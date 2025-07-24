"""
配置模塊 - 包含應用程式的所有配置設定
"""
import os
from pathlib import Path

# Flask 應用程式配置
class Config:
    SECRET_KEY = 'fish_detection_secret_key_2023'
    
    # 語言配置
    LANGUAGES = {
        'en': 'English',
        'zh': '中文',
        'ja': '日本語'
    }
    
    # 文件上傳配置
    PROCESSED_FOLDER = 'static/processed'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_PROCESSED_FILES = 50  # 最多保留50筆處理後的檔案
    
    # 日誌配置
    LOG_DIR = 'logs'
    
    # API 配置
    ROBOFLOW_API_KEY = "AXiN0wVj2W4ZXEFJDG13"
    ROBOFLOW_API_URL = "https://serverless.roboflow.com/infer/workflows/hw30501/detect-count-and-visualize-2"
    
    # 管理員配置
    ADMIN_PASSWORD = 'fish_admin_2023'
    
    def __init__(self):
        # 確保必要的目錄存在
        os.makedirs(self.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)

# 創建配置實例
config = Config()
