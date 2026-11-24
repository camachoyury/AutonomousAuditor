import hashlib
import hmac
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

import app as api

client = TestClient(api.app)
RESULT = {"status": "success", "discrepancies": [], "issue_url": None, "llm_used": False,
          "llm_error": None, "error_message": None}


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cret")
    r = client.post("/webhook/github", content=b"{}", headers={"X-Hub-Signature-256": "sha256=bad"})
    assert r.status_code == 401


def test_webhook_rejects_when_secret_not_configured(monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    body = b"{}"
    r = client.post("/webhook/github", content=body, headers={"X-Hub-Signature-256": _sign(body, "")})
    assert r.status_code == 401


def test_webhook_push_to_default_branch_triggers_audit(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cret")
    body = json.dumps({"ref": "refs/heads/main", "repository": {"html_url": "https://github.com/o/r", "default_branch": "main"}}).encode()
    with patch.object(api, "audit_financial_documents", return_value=RESULT) as audit:
        r = client.post("/webhook/github", content=body, headers={"X-Hub-Signature-256": _sign(body, "s3cret")})
    assert r.status_code == 202
    audit.assert_called_once_with("https://github.com/o/r", "main")


def test_webhook_ignores_other_branches(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cret")
    body = json.dumps({"ref": "refs/heads/dev", "repository": {"html_url": "https://github.com/o/r", "default_branch": "main"}}).encode()
    r = client.post("/webhook/github", content=body, headers={"X-Hub-Signature-256": _sign(body, "s3cret")})
    assert r.json()["status"] == "skipped"


def test_audit_requires_api_key(monkeypatch):
    monkeypatch.setenv("AUDIT_API_KEY", "k")
    assert client.post("/audit", params={"repo_url": "https://github.com/o/r"}).status_code == 401
    monkeypatch.delenv("AUDIT_API_KEY")
    assert client.post("/audit", params={"repo_url": "https://github.com/o/r"}, headers={"X-API-Key": "k"}).status_code == 503


def test_audit_runs_with_valid_key(monkeypatch):
    monkeypatch.setenv("AUDIT_API_KEY", "k")
    with patch.object(api, "audit_financial_documents", return_value=RESULT):
        r = client.post("/audit", params={"repo_url": "https://github.com/o/r"}, headers={"X-API-Key": "k"})
    assert r.status_code == 200 and r.json()["status"] == "success"
