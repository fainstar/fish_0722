import os
import json
import cv2
import numpy as np
from PIL import Image
import requests
import base64
from io import BytesIO
from pathlib import Path
import shutil
import tempfile
import uuid # <-- 匯入 uuid 模組
import logging
import logging.handlers
from datetime import datetime
from user_agents import parse
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session, g, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'fish_detection_secret_key_2023'

# ========== 日誌系統設定 ==========
# 創建日誌目錄
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    """設置日誌系統"""
    # 創建日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 創建主要應用程式日誌
    app_logger = logging.getLogger('fish_app')
    app_logger.setLevel(logging.INFO)
    
    # 創建用戶活動日誌
    user_logger = logging.getLogger('user_activity')
    user_logger.setLevel(logging.INFO)
    
    # 應用程式日誌文件處理器（每天輪替）
    app_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=30
    )
    app_handler.setFormatter(log_format)
    app_logger.addHandler(app_handler)
    
    # 用戶活動日誌文件處理器（每天輪替）
    user_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, 'user_activity.log'),
        when='midnight',
        interval=1,
        backupCount=30
    )
    user_handler.setFormatter(log_format)
    user_logger.addHandler(user_handler)
    
    # 控制台輸出處理器（可選）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    app_logger.addHandler(console_handler)
    
    return app_logger, user_logger

# 初始化日誌系統
app_logger, user_logger = setup_logging()

def get_client_info(request):
    """獲取客戶端詳細信息"""
    user_agent_string = request.headers.get('User-Agent', '')
    user_agent = parse(user_agent_string)
    
    # 獲取真實IP地址（考慮代理和負載均衡器）
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        ip = request.environ['HTTP_X_REAL_IP']
    else:
        ip = request.environ.get('REMOTE_ADDR', 'Unknown')
    
    client_info = {
        'ip_address': ip,
        'user_agent': user_agent_string,
        'browser': {
            'family': user_agent.browser.family,
            'version': user_agent.browser.version_string
        },
        'os': {
            'family': user_agent.os.family,
            'version': user_agent.os.version_string
        },
        'device': {
            'family': user_agent.device.family,
            'brand': user_agent.device.brand,
            'model': user_agent.device.model
        },
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_bot': user_agent.is_bot,
        'language': request.headers.get('Accept-Language', '').split(',')[0] if request.headers.get('Accept-Language') else 'Unknown',
        'referer': request.headers.get('Referer', 'Direct'),
        'timestamp': datetime.now().isoformat()
    }
    
    return client_info

def log_user_activity(action, details=None, client_info=None):
    """記錄用戶活動"""
    if client_info is None:
        client_info = get_client_info(request)
    
    log_data = {
        'action': action,
        'ip': client_info['ip_address'],
        'browser': f"{client_info['browser']['family']} {client_info['browser']['version']}",
        'os': f"{client_info['os']['family']} {client_info['os']['version']}",
        'device': client_info['device']['family'],
        'is_mobile': client_info['is_mobile'],
        'language': client_info['language'],
        'referer': client_info['referer'],
        'session_id': session.get('session_id', 'No Session'),
        'timestamp': client_info['timestamp']
    }
    
    if details:
        log_data.update(details)
    
    # 格式化日誌訊息
    log_message = f"Action: {action} | IP: {client_info['ip_address']} | " \
                  f"Browser: {client_info['browser']['family']} {client_info['browser']['version']} | " \
                  f"OS: {client_info['os']['family']} | Device: {client_info['device']['family']} | " \
                  f"Mobile: {client_info['is_mobile']} | Language: {client_info['language']}"
    
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        log_message += f" | Details: {detail_str}"
    
    user_logger.info(log_message)
    
    return log_data

@app.before_request
def before_request():
    """在每個請求之前執行"""
    # 設置語言
    g.language = session.get('language', request.accept_languages.best_match(LANGUAGES.keys()))
    
    # 生成或獲取 session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # 記錄頁面訪問
    if request.endpoint:
        client_info = get_client_info(request)
        log_user_activity('page_visit', {
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'args': dict(request.args) if request.args else None
        }, client_info)

# ========== 日誌系統設定結束 ==========

# 伺服器端暫存處理結果的地方
RESULTS_CACHE = {}

# Language configuration
LANGUAGES = {
    'en': 'English',
    'zh': '中文',
    'ja': '日本語'
}
app.config['LANGUAGES'] = LANGUAGES
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations' # Can be removed, but let's keep for now

# -- Custom Translation Implementation --
translations = {}

def load_translations():
    """Load translations from JSON files."""
    lang_dir = Path(__file__).parent / 'translations'
    for lang in LANGUAGES:
        filepath = lang_dir / f"{lang}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)

def get_text(key, **kwargs):
    """Get translated text for a given key with optional formatting."""
    lang = getattr(g, 'language', 'en')
    text = translations.get(lang, {}).get(key, key)
    
    # 如果有格式化參數，則進行格式化
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            # 如果格式化失敗，返回原始文本
            pass
    
    return text

@app.context_processor
def inject_get_text():
    """Inject get_text function into templates."""
    return dict(get_text=get_text, current_language=g.language, languages=LANGUAGES)
# -- End Custom Translation --


# 設定上傳檔案的限制
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_PROCESSED_FILES = 50  # 最多保留50筆處理後的檔案

# 確保處理資料夾存在
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def clean_processed_folder():
    """保持 processed 資料夾中最多只有 MAX_PROCESSED_FILES 個檔案"""
    try:
        processed_dir = os.path.join(app.root_path, PROCESSED_FOLDER)
        if not os.path.exists(processed_dir):
            return
            
        # 獲取所有檔案並按修改時間排序（最舊的在前）
        files = []
        for filename in os.listdir(processed_dir):
            filepath = os.path.join(processed_dir, filename)
            if os.path.isfile(filepath):
                files.append((filepath, os.path.getmtime(filepath)))
        
        # 按修改時間排序
        files.sort(key=lambda x: x[1])
        
        # 如果檔案數量超過限制，刪除最舊的檔案
        if len(files) > MAX_PROCESSED_FILES:
            files_to_delete = files[:-MAX_PROCESSED_FILES]  # 保留最新的 MAX_PROCESSED_FILES 個檔案
            for filepath, _ in files_to_delete:
                try:
                    os.remove(filepath)
                    print(f"已刪除舊檔案: {filepath}")
                except OSError as e:
                    print(f"無法刪除檔案 {filepath}: {e}")
                    
    except Exception as e:
        print(f"清理 processed 資料夾時發生錯誤: {e}")


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class FishDetectionSystem:
    def __init__(self, api_key="AXiN0wVj2W4ZXEFJDG13"):
        self.api_key = api_key
        self.api_url = "https://serverless.roboflow.com/infer/workflows/hw30501/detect-count-and-visualize-2"
        
    def resize_image(self, image_path, max_size=(2048, 2048)):
        """調整圖片大小，確保不超過指定的最大尺寸"""
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            resized_path = Path(image_path).with_name("resized_" + Path(image_path).name)
            img.save(resized_path, format=img.format)
        return resized_path

    def image_to_base64(self, image_path):
        """將圖片轉換為base64字串"""
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

    def detect_fish_api(self, image_path):
        """使用 Roboflow API 進行魚類偵測"""
        headers = {'Content-Type': 'application/json'}
        
        # 調整圖片大小
        resized_image_path = self.resize_image(image_path)
        
        # 將圖片轉換為base64
        image_base64 = self.image_to_base64(resized_image_path)
        
        payload = {
            "api_key": self.api_key,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": image_base64
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            
            # 儲存API回應
            response_file = Path(image_path).with_name("response.json")
            with open(response_file, "w", encoding="utf-8") as json_file:
                json.dump(response_data, json_file, indent=2, ensure_ascii=False)
                
            return response_data, str(resized_image_path)
            
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return None, None

    def load_predictions_from_response(self, response_data):
        """從API回應中提取預測結果"""
        try:
            predictions = response_data['outputs'][0]['predictions']['predictions']
            return predictions
        except Exception as e:
            print(f"Error extracting predictions: {str(e)}")
            return []

    def draw_detections(self, image, predictions, confidence_threshold=0.5):
        """在圖片上繪製偵測結果，並根據信賴度使用不同顏色的框。"""
        annotated_image = image.copy()
        
        # 定義莫蘭迪色系 (BGR格式)
        colors = {
            'high_conf': (153, 184, 163),  # 鼠尾草綠 (Sage Green)
            'med_conf': (132, 163, 213),   # 灰橘 (Dusty Orange)
            'low_conf': (137, 137, 195),   # 煙灰粉 (Dusty Rose)
            'text_bg': (80, 80, 80),       # 深灰背景
            'text': (245, 245, 245)      # 米白文字
        }
        
        # 這裡將只儲存高於信賴度閾值的魚
        fish_details_above_threshold = []
        
        for pred in predictions:
            confidence = pred['confidence']
            # 核心邏輯：只處理高於或等於信賴度閾值的預測
            if confidence >= confidence_threshold:
                
                # 根據信賴度選擇顏色
                if confidence >= 0.8:
                    box_color = colors['high_conf']
                elif confidence >= 0.6:
                    box_color = colors['med_conf']
                else:
                    box_color = colors['low_conf']

                x_center, y_center, width, height = pred['x'], pred['y'], pred['width'], pred['height']
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                # 繪製邊界框
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), box_color, 2)
                
                # 繪製信心度
                confidence_text = f"{confidence:.2f}"
                text_size, _ = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                text_x = x1
                text_y = y1 - 10 if y1 - 10 > 10 else y1 + 20
                
                # 繪製文字背景
                cv2.rectangle(annotated_image, (text_x, text_y - text_size[1] - 5), (text_x + text_size[0] + 5, text_y + 5), box_color, -1)
                # 繪製文字
                cv2.putText(annotated_image, confidence_text, (text_x + 2, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors['text'], 1, cv2.LINE_AA)

                # 將符合條件的魚加入列表
                fish_details_above_threshold.append({
                    'box': [x1, y1, x2, y2],
                    'confidence': confidence
                })
        
        # 返回的計數和詳情列表現在已是篩選後的結果
        return annotated_image, len(fish_details_above_threshold), fish_details_above_threshold

    def add_summary_info(self, image, fish_count, fish_details):
        """在圖片上添加統計資訊"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 根據信心度統計數量
        # 注意：傳入的 fish_details 已經是篩選過的，所以這裡的統計是基於篩選後的結果
        high_conf_count = sum(1 for f in fish_details if f['confidence'] >= 0.8)
        medium_conf_count = sum(1 for f in fish_details if 0.6 <= f['confidence'] < 0.8)
        low_conf_count = sum(1 for f in fish_details if f['confidence'] < 0.6)

        # 主要標題
        title = f"Total Fish Detected: {fish_count}"
        title_scale = 1.0
        title_thickness = 2
        
        # 詳細統計
        stats_lines = [
            f"High Confidence (>0.8): {high_conf_count}",
            f"Medium Confidence (0.6-0.8): {medium_conf_count}",
            f"Low Confidence (<0.6): {low_conf_count}"
        ]
        
        stats_scale = 0.7
        stats_thickness = 1
        
        # 計算文字位置（右上角）
        (title_w, title_h), _ = cv2.getTextSize(title, font, title_scale, title_thickness)
        
        # 計算統計資訊的最大寬度
        max_stats_w = 0
        stats_h = 0
        for line in stats_lines:
            (w, h), _ = cv2.getTextSize(line, font, stats_scale, stats_thickness)
            max_stats_w = max(max_stats_w, w)
            stats_h += h + 10 # 增加行距
        
        # 計算背景框尺寸
        bg_width = max(title_w, max_stats_w) + 40 # 增加寬度
        bg_height = title_h + stats_h + 30 # 增加高度
        
        # 位置設定
        bg_x = image.shape[1] - bg_width - 10
        bg_y = 10
        
        # 創建一個半透明的莫蘭迪灰背景
        overlay = image.copy()
        alpha = 0.6 # 透明度
        # 使用莫蘭迪色系的深灰色作為背景
        morandi_bg_color = (80, 80, 80) # BGR
        cv2.rectangle(overlay, 
                     (bg_x, bg_y), 
                     (bg_x + bg_width, bg_y + bg_height), 
                     morandi_bg_color, -1)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

        # 繪製標題
        title_x = bg_x + (bg_width - title_w) // 2
        title_y = bg_y + title_h + 15
        cv2.putText(image, title, (title_x, title_y), 
                   font, title_scale, (255, 255, 255), title_thickness, cv2.LINE_AA)
        
        # 繪製分隔線
        cv2.line(image, (bg_x + 10, title_y + 10), (bg_x + bg_width - 10, title_y + 10), (255, 255, 255), 1)

        # 繪製統計資訊
        current_y = title_y + 40
        for i, line in enumerate(stats_lines):
            # 根據信心等級設定莫蘭迪顏色
            if i == 0:
                color = (153, 184, 163) # 高 - 鼠尾草綠
            elif i == 1:
                color = (132, 163, 213) # 中 - 灰橘
            else:
                color = (137, 137, 195) # 低 - 煙灰粉
            
            cv2.putText(image, line, (bg_x + 20, current_y), 
                       font, stats_scale, color, stats_thickness, cv2.LINE_AA)
            current_y += 25
        
        return image

    def process_image(self, image_path, confidence_threshold=0.5):
        """處理單張圖片，包括偵測和繪製"""
        start_time = cv2.getTickCount()
        
        response_data, resized_image_path = self.detect_fish_api(image_path)
        
        if not response_data:
            return None

        # 從調整大小後的圖片路徑讀取圖片
        image = cv2.imread(resized_image_path)
        if image is None:
            print(f"無法讀取圖片: {resized_image_path}")
            return None

        predictions = self.load_predictions_from_response(response_data)
        
        # 1. 繪製偵測框，此函式內部已根據 confidence_threshold 進行篩選
        # 返回的 fish_count 和 fish_details 都已是篩選後的結果
        annotated_image, fish_count, fish_details = self.draw_detections(image, predictions, confidence_threshold)
        
        # 2. 再加上統計資訊
        # 直接將篩選後的結果傳入即可
        annotated_image_with_summary = self.add_summary_info(annotated_image, fish_count, fish_details)

        # 儲存最終處理後的圖片
        original_filename = Path(image_path).name
        output_filename = "detected_" + original_filename
        output_path = Path(resized_image_path).parent / output_filename
        cv2.imwrite(str(output_path), annotated_image_with_summary)
        
        end_time = cv2.getTickCount()
        process_time = (end_time - start_time) / cv2.getTickFrequency()
        
        return {
            "output_image": output_filename,
            "output_image_path": str(output_path),
            "resized_image": Path(resized_image_path).name,
            "resized_image_path": resized_image_path,
            "fish_count": fish_count,
            "fish_details": fish_details,
            "process_time": process_time,
            "confidence": confidence_threshold
        }

@app.route('/set_language/<language>')
def set_language(language=None):
    """Set the user's language preference."""
    client_info = get_client_info(request)
    
    if language in LANGUAGES:
        session['language'] = language
        log_user_activity('language_change', {
            'new_language': language,
            'old_language': session.get('language', 'default'),
            'available_languages': list(LANGUAGES.keys())
        }, client_info)
        app_logger.info(f"Language changed to {language} for user {client_info['ip_address']}")
    else:
        log_user_activity('invalid_language_attempt', {
            'attempted_language': language,
            'available_languages': list(LANGUAGES.keys())
        }, client_info)
        app_logger.warning(f"Invalid language change attempt: {language} from {client_info['ip_address']}")
    
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    """Render the main upload page."""
    client_info = get_client_info(request)
    log_user_activity('home_page_visit', {
        'user_language': g.language,
        'session_duration': 'new_session' if 'session_start' not in session else 'returning'
    }, client_info)
    
    if 'session_start' not in session:
        session['session_start'] = datetime.now().isoformat()
        app_logger.info(f"New user session started for {client_info['ip_address']}")
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads from the web form."""
    client_info = get_client_info(request)
    
    if 'file' not in request.files:
        log_user_activity('upload_error', {
            'error_type': 'no_file_part',
            'form_data': dict(request.form)
        }, client_info)
        flash(get_text('no_file_part'), 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        log_user_activity('upload_error', {
            'error_type': 'no_selected_file',
            'form_data': dict(request.form)
        }, client_info)
        flash(get_text('no_selected_file'), 'error')
        return redirect(url_for('index'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_size = len(file.read())
        file.seek(0)  # 重置文件指針
        
        log_user_activity('file_upload_start', {
            'filename': filename,
            'original_filename': file.filename,
            'file_size_bytes': file_size,
            'file_type': file.content_type,
            'confidence': request.form.get('confidence', 0.5)
        }, client_info)
        
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        confidence = float(request.form.get('confidence', 0.5))

        try:
            system = FishDetectionSystem()
            start_time = datetime.now()
            result = system.process_image(filepath, confidence)
            process_time = (datetime.now() - start_time).total_seconds()
            
            if result:
                # --- FIX: Use absolute path for destination folder ---
                processed_dir_abs = os.path.join(app.root_path, app.config['PROCESSED_FOLDER'])
                final_output_path = os.path.join(processed_dir_abs, result['output_image'])
                final_resized_path = os.path.join(processed_dir_abs, result['resized_image'])
                
                shutil.move(result['output_image_path'], final_output_path)
                shutil.move(result['resized_image_path'], final_resized_path)

                # 清理 processed 資料夾，保持檔案數量限制
                clean_processed_folder()

                # 記錄成功的處理結果
                log_user_activity('file_processing_success', {
                    'filename': filename,
                    'fish_count': result['fish_count'],
                    'confidence_threshold': confidence,
                    'processing_time_seconds': process_time,
                    'output_image': result['output_image'],
                    'file_size_bytes': file_size
                }, client_info)
                
                app_logger.info(f"File processed successfully: {filename} - Found {result['fish_count']} fish - User: {client_info['ip_address']}")

                shutil.rmtree(temp_dir)
                return render_template('result.html', result=result)
            else:
                log_user_activity('file_processing_failed', {
                    'filename': filename,
                    'error_type': 'no_api_response',
                    'confidence_threshold': confidence,
                    'processing_time_seconds': process_time
                }, client_info)
                
                app_logger.error(f"File processing failed (no API response): {filename} - User: {client_info['ip_address']}")
                flash(get_text('processing_error'), 'error')
                shutil.rmtree(temp_dir)
                return redirect(url_for('index'))

        except Exception as e:
            log_user_activity('file_processing_error', {
                'filename': filename,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'confidence_threshold': confidence
            }, client_info)
            
            app_logger.error(f"File processing error: {filename} - {str(e)} - User: {client_info['ip_address']}")
            print(f"Error in /upload: {e}")
            flash(get_text('error_occurred').format(error=str(e)), 'error')
            shutil.rmtree(temp_dir)
            return redirect(url_for('index'))
    else:
        log_user_activity('upload_error', {
            'error_type': 'file_type_not_allowed',
            'filename': file.filename if file else 'unknown',
            'file_type': file.content_type if file else 'unknown'
        }, client_info)
        
        app_logger.warning(f"File type not allowed: {file.filename if file else 'unknown'} - User: {client_info['ip_address']}")
        flash(get_text('file_type_not_allowed'), 'error')
        return redirect(url_for('index'))

@app.route('/download/<path:filename>')
def download_file(filename):
    """Serve files for download from the processed folder."""
    client_info = get_client_info(request)
    directory = app.config['PROCESSED_FOLDER']
    try:
        log_user_activity('file_download', {
            'filename': filename,
            'download_type': 'processed_image'
        }, client_info)
        
        app_logger.info(f"File download: {filename} - User: {client_info['ip_address']}")
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        log_user_activity('download_error', {
            'filename': filename,
            'error_type': 'file_not_found'
        }, client_info)
        
        app_logger.error(f"Download failed - file not found: {filename} - User: {client_info['ip_address']}")
        flash(get_text('file_not_found'), 'error')
        return redirect(url_for('index'))

@app.route('/api/upload', methods=['POST'])
def upload_file_api():
    """Handle file uploads via API, store result in cache, and return redirect URL."""
    client_info = get_client_info(request)
    
    # 檢查是否使用範例圖片
    use_sample = request.form.get('use_sample')
    
    if use_sample:
        log_user_activity('sample_image_usage', {
            'sample_image': 'A.JPG',
            'confidence': request.form.get('confidence', 0.5)
        }, client_info)
        
        # 使用範例圖片 A.JPG
        sample_image_path = os.path.join(app.root_path, 'static', 'demo', 'A.JPG')
        if not os.path.exists(sample_image_path):
            log_user_activity('api_error', {
                'error_type': 'sample_image_not_found',
                'sample_image': 'A.JPG'
            }, client_info)
            return jsonify({'error': 'Sample image A.JPG not found'}), 400
        
        # 複製範例圖片到臨時目錄
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, 'A.JPG')
        shutil.copy2(sample_image_path, filepath)
        filename = 'A.JPG'
        file_size = os.path.getsize(sample_image_path)
        
    else:
        # 處理上傳的檔案
        if 'file' not in request.files:
            log_user_activity('api_error', {
                'error_type': 'no_file_in_request',
                'form_data': dict(request.form)
            }, client_info)
            return jsonify({'error': get_text('no_file_uploaded')}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            log_user_activity('api_error', {
                'error_type': 'no_selected_file',
                'form_data': dict(request.form)
            }, client_info)
            return jsonify({'error': get_text('no_selected_file')}), 400
            
        if not (file and allowed_file(file.filename)):
            log_user_activity('api_error', {
                'error_type': 'file_type_not_allowed',
                'filename': file.filename,
                'file_type': file.content_type if file else 'unknown'
            }, client_info)
            return jsonify({'error': get_text('file_type_not_allowed')}), 400
        
        filename = secure_filename(file.filename)
        file_size = len(file.read())
        file.seek(0)  # 重置文件指針
        
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        log_user_activity('api_file_upload_start', {
            'filename': filename,
            'original_filename': file.filename,
            'file_size_bytes': file_size,
            'file_type': file.content_type,
            'confidence': request.form.get('confidence', 0.5)
        }, client_info)
    
    confidence = float(request.form.get('confidence', 0.5))

    try:
        system = FishDetectionSystem()
        start_time = datetime.now()
        result = system.process_image(filepath, confidence)
        process_time = (datetime.now() - start_time).total_seconds()
        
        if result:
            # --- FIX: Use absolute path for destination folder ---
            processed_dir_abs = os.path.join(app.root_path, app.config['PROCESSED_FOLDER'])
            final_output_path = os.path.join(processed_dir_abs, result['output_image'])
            final_resized_path = os.path.join(processed_dir_abs, result['resized_image'])
            
            shutil.move(result['output_image_path'], final_output_path)
            shutil.move(result['resized_image_path'], final_resized_path)

            # 清理 processed 資料夾，保持檔案數量限制
            clean_processed_folder()

            # 產生一個唯一的 ID 來存放這次的結果
            result_id = str(uuid.uuid4())
            RESULTS_CACHE[result_id] = result
            
            # 記錄成功的API處理結果
            log_user_activity('api_processing_success', {
                'filename': filename,
                'fish_count': result['fish_count'],
                'confidence_threshold': confidence,
                'processing_time_seconds': process_time,
                'output_image': result['output_image'],
                'file_size_bytes': file_size,
                'result_id': result_id,
                'use_sample': bool(use_sample)
            }, client_info)
            
            app_logger.info(f"API processing successful: {filename} - Found {result['fish_count']} fish - User: {client_info['ip_address']}")
            
            # 清理暫存資料夾
            shutil.rmtree(temp_dir)
            
            # 回傳包含專屬 ID 的結果頁面 URL
            result_url = url_for('show_result', result_id=result_id)
            return jsonify({'redirect_url': result_url})
        else:
            log_user_activity('api_processing_failed', {
                'filename': filename,
                'error_type': 'no_api_response',
                'confidence_threshold': confidence,
                'processing_time_seconds': process_time,
                'use_sample': bool(use_sample)
            }, client_info)
            
            app_logger.error(f"API processing failed (no API response): {filename} - User: {client_info['ip_address']}")
            shutil.rmtree(temp_dir)
            return jsonify({'error': get_text('image_processing_failed_no_api_response')}), 500

    except Exception as e:
        log_user_activity('api_processing_error', {
            'filename': filename,
            'error_message': str(e),
            'error_type': type(e).__name__,
            'confidence_threshold': confidence,
            'use_sample': bool(use_sample)
        }, client_info)
        
        app_logger.error(f"API processing error: {filename} - {str(e)} - User: {client_info['ip_address']}")
        print(f"Error in /api/upload: {e}")
        shutil.rmtree(temp_dir)
        return jsonify({'error': get_text('error_occurred').format(error=str(e))}), 500

@app.route('/result/<result_id>')
def show_result(result_id):
    """Display the result page by fetching data from the server cache."""
    client_info = get_client_info(request)
    
    # 從快取中取出結果，.pop() 會在取出後刪除，避免快取無限增長
    result = RESULTS_CACHE.pop(result_id, None)
    
    if not result:
        log_user_activity('result_page_error', {
            'result_id': result_id,
            'error_type': 'result_not_found_in_cache'
        }, client_info)
        
        app_logger.warning(f"Result not found in cache: {result_id} - User: {client_info['ip_address']}")
        flash(get_text('no_result_found'), 'error')
        return redirect(url_for('index'))
    
    log_user_activity('result_page_view', {
        'result_id': result_id,
        'fish_count': result.get('fish_count', 0),
        'output_image': result.get('output_image', 'unknown'),
        'confidence': result.get('confidence', 0.5)
    }, client_info)
    
    app_logger.info(f"Result page viewed: {result_id} - Fish count: {result.get('fish_count', 0)} - User: {client_info['ip_address']}")
    
    return render_template('result.html', result=result)

@app.route('/log')
def log_viewer():
    """簡化的日誌查看頁面 - 不需要管理員密碼"""
    client_info = get_client_info(request)
    
    log_user_activity('log_page_access', {
        'access_method': 'simple_route'
    }, client_info)
    
    # 獲取篩選參數
    log_type = request.args.get('log_type', '')
    date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    ip_address = request.args.get('ip_address', '')
    
    # 讀取用戶活動日誌
    logs = parse_user_activity_logs(log_type, date_from, date_to, ip_address)
    
    # 計算統計數據
    stats = calculate_log_statistics(logs)
    
    return render_template('logs.html', 
                         logs=logs, 
                         stats=stats, 
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/admin/logs')
def admin_logs():
    """管理員日誌查看頁面"""
    client_info = get_client_info(request)
    
    # 簡單的管理員驗證 (可以根據需要改為更安全的驗證方式)
    admin_password = request.args.get('admin_key')
    if admin_password != 'fish_admin_2023':
        log_user_activity('admin_access_denied', {
            'attempted_password': admin_password or 'none',
            'page': 'logs'
        }, client_info)
        return "Access denied. Invalid admin key.", 403
    
    log_user_activity('admin_page_access', {
        'admin_page': 'logs'
    }, client_info)
    
    # 獲取篩選參數
    log_type = request.args.get('log_type', '')
    date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    ip_address = request.args.get('ip_address', '')
    
    # 讀取用戶活動日誌
    logs = parse_user_activity_logs(log_type, date_from, date_to, ip_address)
    
    # 計算統計數據
    stats = calculate_log_statistics(logs)
    
    return render_template('logs.html', 
                         logs=logs, 
                         stats=stats, 
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/admin/clear-logs', methods=['POST'])
def admin_clear_logs():
    """清除日誌文件"""
    client_info = get_client_info(request)
    
    # 簡單的管理員驗證
    admin_password = request.headers.get('X-Admin-Key') or request.form.get('admin_key')
    if admin_password != 'fish_admin_2023':
        log_user_activity('admin_access_denied', {
            'attempted_password': admin_password or 'none',
            'action': 'clear_logs'
        }, client_info)
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        # 清除用戶活動日誌
        user_log_file = os.path.join(LOG_DIR, 'user_activity.log')
        if os.path.exists(user_log_file):
            open(user_log_file, 'w').close()
        
        log_user_activity('admin_logs_cleared', {
            'admin_action': 'clear_all_logs'
        }, client_info)
        
        app_logger.info(f"Logs cleared by admin from {client_info['ip_address']}")
        
        return jsonify({'success': True})
    except Exception as e:
        app_logger.error(f"Error clearing logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_user_activity_logs(log_type='', date_from='', date_to='', ip_address='', limit=500):
    """解析用戶活動日誌"""
    logs = []
    log_file = os.path.join(LOG_DIR, 'user_activity.log')
    
    if not os.path.exists(log_file):
        return logs
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 只讀取最新的 limit 行
        lines = lines[-limit:]
        
        for line in reversed(lines):  # 最新的在前
            try:
                # 解析日誌行
                parts = line.strip().split(' - ', 2)
                if len(parts) < 3:
                    continue
                
                timestamp = parts[0]
                level = parts[1]
                message = parts[2]
                
                # 解析消息內容
                log_data = parse_log_message(message)
                if not log_data:
                    continue
                
                # 應用篩選條件
                if log_type and log_type not in log_data.get('action', ''):
                    continue
                
                if ip_address and ip_address not in log_data.get('ip', ''):
                    continue
                
                # 日期篩選
                log_date = timestamp.split(' ')[0]
                if date_from and log_date < date_from:
                    continue
                if date_to and log_date > date_to:
                    continue
                
                log_data['timestamp'] = timestamp
                log_data['level'] = level
                logs.append(log_data)
                
            except Exception as e:
                continue  # 跳過解析失敗的行
    
    except Exception as e:
        app_logger.error(f"Error reading log file: {str(e)}")
    
    return logs

def parse_log_message(message):
    """解析日誌消息"""
    try:
        # 提取主要欄位
        data = {}
        parts = message.split(' | ')
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'Action':
                    data['action'] = value
                elif key == 'IP':
                    data['ip'] = value
                elif key == 'Browser':
                    data['browser'] = value
                elif key == 'OS':
                    data['os'] = value
                elif key == 'Device':
                    data['device'] = value
                elif key == 'Mobile':
                    data['is_mobile'] = value.lower() == 'true'
                elif key == 'Language':
                    data['language'] = value
                elif key == 'Details':
                    # 嘗試解析詳細信息
                    details = {}
                    detail_parts = value.split(' | ')
                    for detail in detail_parts:
                        if ':' in detail:
                            detail_key, detail_value = detail.split(':', 1)
                            details[detail_key.strip()] = detail_value.strip()
                    data['details'] = details
        
        return data if data else None
    except Exception:
        return None

def calculate_log_statistics(logs):
    """計算日誌統計數據"""
    stats = {
        'total_users': 0,
        'total_uploads': 0,
        'total_fish': 0,
        'avg_processing_time': 0,
        'total_errors': 0
    }
    
    unique_ips = set()
    processing_times = []
    
    for log in logs:
        # 統計唯一用戶
        if log.get('ip'):
            unique_ips.add(log['ip'])
        
        # 統計上傳
        if 'upload' in log.get('action', '').lower():
            stats['total_uploads'] += 1
        
        # 統計魚類檢測數量
        if log.get('details') and 'fish_count' in log['details']:
            try:
                fish_count = int(log['details']['fish_count'])
                stats['total_fish'] += fish_count
            except ValueError:
                pass
        
        # 統計處理時間
        if log.get('details') and 'processing_time_seconds' in log['details']:
            try:
                time_seconds = float(log['details']['processing_time_seconds'])
                processing_times.append(time_seconds)
            except ValueError:
                pass
        
        # 統計錯誤
        if 'error' in log.get('action', '').lower():
            stats['total_errors'] += 1
    
    stats['total_users'] = len(unique_ips)
    if processing_times:
        stats['avg_processing_time'] = sum(processing_times) / len(processing_times)
    
    return stats


if __name__ == '__main__':
    load_translations()
    # 啟動時清理 processed 資料夾
    clean_processed_folder()
    app_logger.info("Fish Detection System started")
    app.run(debug=True, port=5001)
