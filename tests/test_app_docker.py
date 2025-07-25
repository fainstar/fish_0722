import os
import sys
import importlib
from unittest.mock import patch, MagicMock

# 將專案根目錄加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_create_app_docker_env(monkeypatch):
    """Test create_app in a simulated Docker environment."""
    # Simulate being in a Docker environment
    monkeypatch.setattr(os.path, 'exists', lambda path: path == '/.dockerenv')
    
    # Reload the module to pick up the mocked environment
    from src import app_docker
    importlib.reload(app_docker)

    app = app_docker.create_app()
    assert app is not None
    # Check if it's using DockerConfig
    assert app.secret_key == 'your_docker_default_secret_key'

def test_create_app_local_env(monkeypatch):
    """Test create_app in a simulated local environment."""
    # Simulate being in a local environment
    monkeypatch.setattr(os.path, 'exists', lambda path: False)

    # Reload the module to pick up the mocked environment
    from src import app_docker
    importlib.reload(app_docker)

    app = app_docker.create_app()
    assert app is not None
    # Check if it's using the default Config
    assert app.secret_key == 'your_local_default_secret_key'

@patch('src.app_docker.setup_logging')
@patch('src.app_docker.create_app')
@patch('src.app_docker.os.makedirs')
def test_main_function(mock_makedirs, mock_create_app, mock_setup_logging):
    """Test the main function of app_docker."""
    # Mock the return values
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    mock_setup_logging.return_value = (MagicMock(), MagicMock())

    from src import app_docker
    # We need to patch app.run to prevent it from actually running
    with patch.object(mock_app, 'run') as mock_run:
        app_docker.main()

    mock_setup_logging.assert_called_once()
    mock_create_app.assert_called_once()
    assert mock_makedirs.call_count == 4
    mock_run.assert_called_once()