import os
import sys
import importlib
from pathlib import Path
import shutil

# 將專案根目錄加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.production_config import ProductionConfig

def test_production_config_defaults():
    """Test the default values in ProductionConfig."""
    config = ProductionConfig()
    assert config.SECRET_KEY == 'your-super-secret-production-key-change-this'
    assert config.DEBUG is False
    assert config.TESTING is False
    assert config.HOST == '0.0.0.0'
    assert config.PORT == 5000
    assert config.ADMIN_PASSWORD == 'admin123'
    assert config.ROBOFLOW_API_KEY is None

def test_production_config_from_env(monkeypatch):
    """Test that ProductionConfig correctly loads values from environment variables."""
    monkeypatch.setenv('SECRET_KEY', 'prod_secret')
    monkeypatch.setenv('PORT', '8000')
    monkeypatch.setenv('ADMIN_PASSWORD', 'prod_admin')
    monkeypatch.setenv('ROBOFLOW_API_KEY', 'prod_api_key')

    from src import production_config
    importlib.reload(production_config)

    config = production_config.ProductionConfig()

    assert config.SECRET_KEY == 'prod_secret'
    assert config.PORT == 8000
    assert config.ADMIN_PASSWORD == 'prod_admin'
    assert config.ROBOFLOW_API_KEY == 'prod_api_key'

def test_init_directories(tmp_path):
    """Test the init_directories class method."""
    # Use a temporary directory for testing
    upload_dir = tmp_path / 'static' / 'uploads'
    processed_dir = tmp_path / 'static' / 'processed'
    log_dir = tmp_path / 'logs'

    # Monkeypatch the config to use the temp directories
    ProductionConfig.UPLOAD_FOLDER = str(upload_dir)
    ProductionConfig.PROCESSED_FOLDER = str(processed_dir)
    ProductionConfig.LOG_DIR = str(log_dir)

    ProductionConfig.init_directories()

    assert upload_dir.is_dir()
    assert processed_dir.is_dir()
    assert log_dir.is_dir()