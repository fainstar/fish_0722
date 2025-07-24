"""
生產環境專用配置文件
移除所有除錯輸出，優化性能設置
"""
import os
from pathlib import Path

class ProductionConfig:
    """生產環境配置類"""
    
    # 基本應用配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-production-key-change-this')
    DEBUG = False
    TESTING = False
    
    # 網路配置
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # 檔案上傳配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    PROCESSED_FOLDER = 'static/processed'
    
    # 清理配置
    MAX_PROCESSED_FILES = 50  # 限制處理過的檔案數量
    CLEANUP_INTERVAL = 3600   # 1小時清理一次
    
    # 語言配置
    LANGUAGES = {
        'zh': '繁體中文',
        'en': 'English', 
        'ja': '日本語'
    }
    DEFAULT_LANGUAGE = 'zh'
    
    # 日誌配置
    LOG_DIR = 'logs'
    LOG_LEVEL = 'INFO'  # 生產環境只記錄重要資訊
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 管理員配置
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # 性能優化配置
    ENABLE_STATIC_FILE_CACHE = True
    STATIC_FILE_CACHE_TIMEOUT = 3600  # 1小時
    
    # 安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API配置（從環境變數讀取）
    ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY')
    ROBOFLOW_MODEL_URL = os.environ.get('ROBOFLOW_MODEL_URL')
    
    @classmethod
    def init_directories(cls):
        """初始化必要目錄"""
        for directory in [cls.UPLOAD_FOLDER, cls.PROCESSED_FOLDER, cls.LOG_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

# 創建配置實例
production_config = ProductionConfig()
