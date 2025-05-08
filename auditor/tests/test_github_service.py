import pytest
from unittest.mock import Mock, patch
from github import Github
from github.ContentFile import ContentFile

from ..core.models import FinancialDocument
from ..core.exceptions import GitHubError, ConfigurationError
from ..services.github_service import GitHubService

@pytest.fixture
def mock_github():
    """Fixture con un mock de GitHub."""
    with patch('github.Github') as mock:
        yield mock

@pytest.fixture
def mock_repo():
    """Fixture con un mock de repositorio."""
    repo = Mock()
    content1 = Mock(spec=ContentFile)
    content1.name = 'pl.md'
    content1.path = 'pl.md'
    content1.type = 'file'
    content1.decoded_content = b'IyBQJkwKUGVyaW9kbzogMjAyNC1RMQoKIyMgSW5ncmVzb3MKfCBDb25jZXB0byB8IE1vbnRvIHwKfC0tLS0tLS0tLS18LS0tLS0tLS18CnwgVmVudGFzICAgfCAkMTAwMCB8CnwgT3Ryb3MgICAgfCAkMjAwICB8Cg=='
    
    content2 = Mock(spec=ContentFile)
    content2.name = 'balance.md'
    content2.path = 'balance.md'
    content2.type = 'file'
    content2.decoded_content = b'IyBCYWxhbmNlIEdlbmVyYWwKUGVyaW9kbzogMjAyNC1RMQoKIyMgQWN0aXZvcwp8IENvbmNlcHRvIHwgTW9udG8gfAp8LS0tLS0tLS0tfC0tLS0tLS18CnwgRWZlY3Rpdm8gfCAkMTAwMCB8CnwgQ3VlbnRhcyAgfCAkNTAwICB8Cg=='
    
    contents = [content1, content2]
    repo.get_contents.return_value = contents
    repo.get_contents.side_effect = lambda path, ref=None: next((c for c in contents if c.path == path), contents)
    return repo

@pytest.fixture
def github_service():
    """Fixture con un servicio de GitHub."""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        return GitHubService()

def test_init_without_token():
    """Prueba la inicialización sin token de GitHub."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ConfigurationError):
            GitHubService()

def test_retrieve_documents(github_service, mock_github, mock_repo):
    """Prueba la recuperación de documentos."""
    mock_github.return_value.get_repo.return_value = mock_repo
    github_service.github_client = mock_github.return_value
    
    docs = github_service.retrieve_documents('https://github.com/owner/repo')
    
    assert 'pl' in docs
    assert 'balance' in docs
    assert docs['pl'].doc_type == 'pl'
    assert docs['balance'].doc_type == 'balance'

def test_retrieve_documents_no_files(github_service, mock_github, mock_repo):
    """Prueba la recuperación cuando no hay archivos."""
    empty_repo = Mock()
    empty_repo.get_contents.return_value = []
    empty_repo.get_contents.side_effect = lambda path, ref=None: []
    mock_github.return_value.get_repo.return_value = empty_repo
    github_service.github_client = mock_github.return_value
    
    with pytest.raises(GitHubError):
        github_service.retrieve_documents('https://github.com/owner/repo')

def test_create_issue(github_service, mock_github, mock_repo):
    """Prueba la creación de un issue."""
    mock_github.return_value.get_repo.return_value = mock_repo
    mock_repo.get_issues.return_value = []
    mock_repo.create_issue.return_value.html_url = 'https://github.com/owner/repo/issues/1'
    github_service.github_client = mock_github.return_value
    
    issue_url = github_service.create_or_update_issue(
        [{
            'type': 'test',
            'description': 'Test discrepancy',
            'severity': 'high',
            'fix': 'Test fix'
        }],
        'https://github.com/owner/repo'
    )
    
    assert issue_url == 'https://github.com/owner/repo/issues/1'
    assert mock_repo.create_issue.called

def test_update_existing_issue(github_service, mock_github, mock_repo):
    """Prueba la actualización de un issue existente."""
    existing_issue = Mock()
    existing_issue.title = "Auditoría Financiera: 1 discrepancias encontradas"
    existing_issue.html_url = 'https://github.com/owner/repo/issues/1'
    mock_repo.get_issues.return_value = [existing_issue]
    mock_github.return_value.get_repo.return_value = mock_repo
    github_service.github_client = mock_github.return_value
    
    issue_url = github_service.create_or_update_issue(
        [{
            'type': 'test',
            'description': 'Test discrepancy',
            'severity': 'high',
            'fix': 'Test fix'
        }],
        'https://github.com/owner/repo'
    )
    
    assert issue_url == 'https://github.com/owner/repo/issues/1'
    assert existing_issue.edit.called
    assert not mock_repo.create_issue.called

def test_invalid_repo_url():
    """Prueba el manejo de URLs de repositorio inválidas."""
    service = GitHubService()
    with pytest.raises(GitHubError):
        service.retrieve_documents('invalid-url') 