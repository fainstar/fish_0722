#!/usr/bin/env python3
"""
Docker 環境專用啟動腳本
"""
import os
import sys
from flask import Flask, session, request, g

# 獲取專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 檢查是否在 Docker 環境中
if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
    # 使用 Docker 配置
    from src.docker_config import docker_config as config
    print("🐳 Running in Docker environment")
else:
    # 使用原始配置
    from src.config import config
    print("💻 Running in local environment")

from src.logger import setup_logging, get_app_logger
from src.translations_handler import set_language_context, get_template_context
from src.routes import register_routes

def create_app():
    """創建 Flask 應用程式"""
    app = Flask(__name__, 
               template_folder=os.path.join(BASE_DIR, 'templates'),
               static_folder=os.path.join(BASE_DIR, 'static'))
    app.secret_key = config.SECRET_KEY
    print(f"DEBUG: Flask app secret_key is set to: {app.secret_key}") # Add this line for debugging
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
     # 💡 進入 app context 再設置 jinja template 的 global context
    with app.app_context():
        app.jinja_env.globals.update(get_template_context())

    # 在每個請求前設置語言上下文
    @app.before_request
    def before_request():
        set_language_context()
    
    # 註冊所有路由
    register_routes(app)
    
    return app

def main():
    """主函數"""
    # 初始化日誌系統
    app_logger, user_logger = setup_logging()
    
    # 確保必要目錄存在
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.PROCESSED_FOLDER, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs('data/output1', exist_ok=True)
    
    # 創建應用程式
    app = create_app()
    
    # 記錄啟動信息
    if app_logger:
        if os.path.exists('/.dockerenv'):
            app_logger.info("🐳 Fish Detection System started in Docker container")
        else:
            app_logger.info("💻 Fish Detection System started locally")
    
    try:
        # 啟動應用程式
        print(f"🚀 Fish Detection System starting on {config.HOST}:{config.PORT}")
        print(f"📱 Access the application at: http://localhost:{config.PORT}")
        print(f"📊 View logs at: http://localhost:{config.PORT}/log")
        print(f"🔧 Admin access: http://localhost:{config.PORT}/admin/logs?admin_key={config.ADMIN_PASSWORD}")
        
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n🛑 Fish Detection System stopped")
        if app_logger:
            app_logger.info("Fish Detection System stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        if app_logger:
            app_logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
