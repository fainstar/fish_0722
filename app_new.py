"""
Fish Detection System - 主應用程式文件
重構後的模組化架構
"""
import uuid
from flask import Flask, g, session, request
from datetime import datetime

# 導入自定義模塊
from config import config
from logger import setup_logging, app_logger, log_user_activity, get_client_info
from translations_handler import set_language_context, get_template_context, load_translations
from file_utils import clean_processed_folder
from routes import register_routes

# 創建Flask應用
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 配置應用
app.config['PROCESSED_FOLDER'] = config.PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['LANGUAGES'] = config.LANGUAGES

# 初始化日誌系統
app_logger, user_logger = setup_logging()

@app.before_request
def before_request():
    """在每個請求之前執行"""
    # 設置語言
    set_language_context()
    
    # 生成或獲取 session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # 記錄頁面訪問
    if request.endpoint and request.endpoint != 'static':
        client_info = get_client_info(request)
        log_user_activity('page_visit', {
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'args': dict(request.args) if request.args else None
        }, client_info)

@app.context_processor
def inject_template_context():
    """注入模板上下文"""
    return get_template_context()

# 註冊所有路由
register_routes(app)

if __name__ == '__main__':
    # 載入翻譯
    load_translations()
    
    # 啟動時清理 processed 資料夾
    clean_processed_folder()
    
    # 記錄應用啟動
    app_logger.info("Fish Detection System started - Modular architecture")
    
    # 運行應用
    app.run(debug=True, port=5001)
