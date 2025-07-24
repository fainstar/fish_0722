"""
Fish Detection System - 主應用程式文件
重構後的模組化架構
"""
import uuid
import os
from flask import Flask, g, session, request
from datetime import datetime

# 獲取專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 導入自定義模塊
from src.config import config
from src.logger import setup_logging, get_app_logger, log_user_activity, get_client_info
from src.translations_handler import set_language_context, get_template_context, load_translations
from src.file_utils import clean_processed_folder
from src.routes import register_routes

# 創建Flask應用，指定正確的模板和靜態檔案路徑
app = Flask(__name__, 
           template_folder=os.path.join(BASE_DIR, 'templates'),
           static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = config.SECRET_KEY

# 配置應用
app.config['PROCESSED_FOLDER'] = config.PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['LANGUAGES'] = config.LANGUAGES

# 確保必要的目錄存在
processed_dir = os.path.join(BASE_DIR, config.PROCESSED_FOLDER)
uploads_dir = os.path.join(BASE_DIR, 'static', 'uploads')
demo_dir = os.path.join(BASE_DIR, 'static', 'demo')

os.makedirs(processed_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(demo_dir, exist_ok=True)

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

def main():
    """主函數 - 啟動應用程式"""
    # 載入翻譯
    load_translations()
    
    # 啟動時清理 processed 資料夾
    clean_processed_folder()
    
    # 記錄應用啟動
    get_app_logger().info("Fish Detection System started - Modular architecture")
    
    # 運行應用
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    main()
