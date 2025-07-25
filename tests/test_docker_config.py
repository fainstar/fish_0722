import os
import sys

# 將專案根目錄加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.docker_config import DockerConfig

def test_docker_config_defaults():
    """Test the default values in DockerConfig."""
    config = DockerConfig()
    assert config.SECRET_KEY == 'your_docker_default_secret_key'
    assert config.ROBOFLOW_API_KEY == 'your-roboflow-api-key'
    assert config.ADMIN_PASSWORD == 'fish_admin_2024'
    assert config.HOST == '0.0.0.0'
    assert config.PORT == 5001
    assert config.DEBUG is False
    assert config.UPLOAD_FOLDER == '/app/static/uploads'
    assert config.PROCESSED_FOLDER == '/app/static/processed'
    assert config.LOG_DIR == '/app/logs'

import importlib

def test_docker_config_from_env(monkeypatch):
    """Test that DockerConfig correctly loads values from environment variables."""
    monkeypatch.setenv('SECRET_KEY', 'env_secret')
    monkeypatch.setenv('ROBOFLOW_API_KEY', 'env_api_key')
    monkeypatch.setenv('ADMIN_PASSWORD', 'env_admin')
    monkeypatch.setenv('PORT', '8080')

    # Reload the module to apply the new environment variables
    from src import docker_config
    importlib.reload(docker_config)

    config = docker_config.DockerConfig()

    assert config.SECRET_KEY == 'env_secret'
    assert config.ROBOFLOW_API_KEY == 'env_api_key'
    assert config.ADMIN_PASSWORD == 'env_admin'
    assert config.PORT == 8080