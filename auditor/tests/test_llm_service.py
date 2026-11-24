import json
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..core.exceptions import LLMError
from ..core.models import FinancialDocument, FinancialLineItem
from ..services.audit_service import AuditService
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService
from ..services.llm_service import LLMAuditService, _to_jsonable

VALID = json.dumps({"findings": [
    {"type": "total_mismatch", "description": "Ingresos suman 1200 pero el total dice 1300",
     "severity": "high", "fix": "Corregir el total"},
]})


def test_parse_response_maps_findings():
    out = LLMAuditService.parse_response(VALID)
    assert out == [{
        "type": "llm_total_mismatch",
        "description": "Ingresos suman 1200 pero el total dice 1300",
        "severity": "high",
        "fix": "Corregir el total",
        "source": "gemini",
    }]


def test_parse_response_empty_findings():
    assert LLMAuditService.parse_response('{"findings": []}') == []


@pytest.mark.parametrize("bad", ["", "no es json", '{"findings": [{"type": "x"}]}',
                                 '{"findings": [{"type":"x","description":"d","severity":"critical","fix":"f"}]}'])
def test_parse_response_invalid_raises(bad):
    with pytest.raises(LLMError):
        LLMAuditService.parse_response(bad)


def test_disabled_service_does_not_call_gemini():
    svc = LLMAuditService(enabled=False)
    with patch.object(LLMAuditService, "areview", new=AsyncMock()) as areview:
        assert svc.review({}, {}, []) == []
        areview.assert_not_called()


def test_to_jsonable_handles_decimal_and_dataclass():
    item = FinancialLineItem(name="Ventas", amount=Decimal("10.50"), category="revenue", period="Q1")
    assert _to_jsonable({"x": [item]}) == {"x": [{"name": "Ventas", "amount": "10.50", "category": "revenue", "period": "Q1"}]}
    json.dumps(_to_jsonable({"x": [item]}))


def _service(llm):
    github = Mock(spec=GitHubService)
    github.retrieve_documents.return_value = {
        "pl": FinancialDocument(content="", doc_type="pl", file_format="markdown"),
        "balance": FinancialDocument(content="", doc_type="balance", file_format="markdown"),
    }
    github.create_or_update_issue.return_value = "https://github.com/o/r/issues/1"
    docs = Mock(spec=DocumentService)
    docs.parse_document.side_effect = [
        {"period": "Q1", "totals": {"Utilidad Neta": Decimal("400")}},
        {"period": "Q1", "totals": {"Total Activos": Decimal("1500"), "Total Pasivos": Decimal("1000"),
                                     "Total Capital Contable": Decimal("500")}},
    ]
    return AuditService(document_service=docs, github_service=github, llm_service=llm), github


def test_audit_merges_gemini_findings_and_creates_issue():
    llm = Mock(spec=LLMAuditService)
    llm.enabled = True
    llm.review.return_value = [{"type": "llm_x", "description": "d", "severity": "medium", "fix": "f", "source": "gemini"}]
    service, github = _service(llm)

    result = service.run_audit("https://github.com/o/r")

    assert result.status == "success" and result.llm_used
    assert [d["type"] for d in result.discrepancies] == ["llm_x"]
    github.create_or_update_issue.assert_called_once()
    llm.review.assert_called_once()


def test_audit_survives_gemini_failure():
    llm = Mock(spec=LLMAuditService)
    llm.enabled = True
    llm.review.side_effect = LLMError("cuota agotada")
    service, _ = _service(llm)

    result = service.run_audit("https://github.com/o/r")

    assert result.status == "success"
    assert not result.llm_used and "cuota" in result.llm_error
