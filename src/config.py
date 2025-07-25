"""
配置模塊 - 包含應用程式的所有配置設定
"""
import os
import json
from pathlib import Path

# Flask 應用程式配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_local_default_secret_key') # 确保在生产环境中通过环境变量设置此值
    
    # 語言配置
    LANGUAGES = {
        'en': 'English',
        'zh': '中文',
        'ja': '日本語'
    }
    
    # 文件上傳配置
    UPLOAD_FOLDER = 'static/uploads'
    PROCESSED_FOLDER = 'static/processed'
    MAX_PROCESSED_FILES = 20
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_PROCESSED_FILES = 50  # 最多保留50筆處理後的檔案
    
    # 日誌配置
    LOG_DIR = 'logs'
    
    # 管理員配置
    ADMIN_PASSWORD = 'fish_admin_2023'

    # Flask 設定
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = True
    
    def __init__(self):
        # 確保必要的目錄存在
        os.makedirs(self.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        # 載入 API 配置
        self.load_api_config()
    
    def load_api_config(self):
        """載入 API 配置文件"""
        config_path = Path(__file__).parent.parent / 'config' / 'api_config.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.api_config = json.load(f)
            
            # 設定 Roboflow API 相關配置
            roboflow_config = self.api_config.get('roboflow', {})
            self.ROBOFLOW_API_KEY = roboflow_config.get('api_key', '')
            
            # 獲取預設端點
            endpoints = roboflow_config.get('endpoints', {})
            default_endpoint = endpoints.get('detect_count_visualize', {})
            self.ROBOFLOW_API_URL = default_endpoint.get('url', '')
            self.ROBOFLOW_MODEL_ID = default_endpoint.get('model_id', '')
            
            # API 設定
            api_settings = self.api_config.get('api_settings', {})
            self.API_TIMEOUT = api_settings.get('timeout', 30)
            self.API_RETRY_ATTEMPTS = api_settings.get('retry_attempts', 3)
            self.API_RETRY_DELAY = api_settings.get('retry_delay', 1.0)
            
            # 圖片處理設定
            image_config = self.api_config.get('image_processing', {})
            self.IMAGE_MAX_SIZE = image_config.get('max_size', {'width': 1024, 'height': 1024})
            self.IMAGE_QUALITY = image_config.get('quality', 85)
            
        except FileNotFoundError:
            print(f"警告: API 配置文件未找到 {config_path}")
            # 使用預設值
            self.ROBOFLOW_API_KEY = "AXiN0wVj2W4ZXEFJDG13"
            self.ROBOFLOW_API_URL = "https://serverless.roboflow.com/infer/workflows/hw30501/detect-count-and-visualize-2"
            self.ROBOFLOW_MODEL_ID = "hw30501/detect-count-and-visualize-2"
            self.API_TIMEOUT = 30
            self.API_RETRY_ATTEMPTS = 3
            self.API_RETRY_DELAY = 1.0
            self.IMAGE_MAX_SIZE = {'width': 1024, 'height': 1024}
            self.IMAGE_QUALITY = 85
            
        except json.JSONDecodeError as e:
            print(f"錯誤: API 配置文件格式錯誤 {e}")
            # 使用預設值（同上）
    
    def get_api_endpoint(self, endpoint_name='detect_count_visualize'):
        """獲取指定的 API 端點配置"""
        if hasattr(self, 'api_config'):
            endpoints = self.api_config.get('roboflow', {}).get('endpoints', {})
            return endpoints.get(endpoint_name, {})
        return {}
    
    def get_default_parameters(self):
        """獲取預設的 API 參數"""
        if hasattr(self, 'api_config'):
            return self.api_config.get('roboflow', {}).get('default_parameters', {})
        return {'confidence': 0.5, 'overlap': 0.3, 'format': 'json'}
    
    def get_available_models(self):
        """獲取所有可用的模型選項"""
        if hasattr(self, 'api_config'):
            endpoints = self.api_config.get('roboflow', {}).get('endpoints', {})
            models = {}
            for key, config in endpoints.items():
                models[key] = {
                    'name': config.get('name', key),
                    'description': config.get('description', ''),
                    'accuracy': config.get('accuracy', '未知'),
                    'speed': config.get('speed', '未知'),
                    'version': config.get('version', 'v1.0')
                }
            return models
        return {}
    
    def get_model_config(self, model_key='detect_count_visualize'):
        """根據模型鍵值獲取完整的模型配置"""
        if hasattr(self, 'api_config'):
            endpoints = self.api_config.get('roboflow', {}).get('endpoints', {})
            return endpoints.get(model_key, endpoints.get('detect_count_visualize', {}))
        return {}
    
    def set_active_model(self, model_key):
        """設置當前活躍的模型"""
        model_config = self.get_model_config(model_key)
        if model_config:
            self.ROBOFLOW_API_URL = model_config.get('url', '')
            self.ROBOFLOW_MODEL_ID = model_config.get('model_id', '')
            return True
        return False

# 創建配置實例
config = Config()
