"""
Docker 生產環境配置
"""
import os

class DockerConfig:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_docker_default_secret_key') # 确保在生产环境中通过环境变量设置此值
    
    # 語言設定
    LANGUAGES = {
        'zh': '繁體中文',
        'en': 'English', 
        'ja': '日本語'
    }
    
    # 檔案路徑設定
    UPLOAD_FOLDER = '/app/static/uploads'
    PROCESSED_FOLDER = '/app/static/processed'
    
    # 檔案限制
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # 檔案清理設定
    MAX_PROCESSED_FILES = 100
    CLEANUP_INTERVAL_HOURS = 24
    
    # API 設定
    ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY', 'your-roboflow-api-key')
    ROBOFLOW_MODEL_URL = os.environ.get('ROBOFLOW_MODEL_URL', 'https://detect.roboflow.com/your-model')
    
    # 日誌設定
    LOG_DIR = '/app/logs'
    LOG_FILE = '/app/logs/fish_detection.log'
    USER_ACTIVITY_LOG = '/app/logs/user_activity.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 管理員設定
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'fish_admin_2024')
    
    # Flask 設定
    HOST = '0.0.0.0'  # Docker 容器內需要綁定到所有介面
    # 從環境變數讀取配置，提供預設值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    PORT = int(os.environ.get('PORT', 5003))
    
    # 語言配置
    LANGUAGES = ['en', 'zh', 'ja']
    
    DEBUG = False  # 生產環境關閉 debug

# 創建全局配置實例
docker_config = DockerConfig()
