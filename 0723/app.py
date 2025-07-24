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
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session, g, send_from_directory
from werkzeug.utils import secure_filename

# 獲取當前目錄作為基礎目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
           template_folder=os.path.join(BASE_DIR, 'templates'),
           static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = 'fish_detection_secret_key_2023'

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

def get_text(key):
    """Get translated text for a given key."""
    lang = getattr(g, 'language', 'en')
    return translations.get(lang, {}).get(key, key)

@app.before_request
def before_request():
    """Set the language for the current request."""
    g.language = session.get('language', request.accept_languages.best_match(LANGUAGES.keys()))

@app.context_processor
def inject_get_text():
    """Inject get_text function into templates."""
    return dict(get_text=get_text, current_language=g.language, languages=LANGUAGES)
# -- End Custom Translation --


# 設定上傳檔案的限制
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 確保上傳和處理資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


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
    if language in LANGUAGES:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads from the web form."""
    if 'file' not in request.files:
        flash(get_text('no_file_part'), 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash(get_text('no_selected_file'), 'error')
        return redirect(url_for('index'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        confidence = float(request.form.get('confidence', 0.5))

        try:
            system = FishDetectionSystem()
            result = system.process_image(filepath, confidence)
            
            if result:
                # --- FIX: Use absolute path for destination folder ---
                processed_dir_abs = os.path.join(app.root_path, app.config['PROCESSED_FOLDER'])
                final_output_path = os.path.join(processed_dir_abs, result['output_image'])
                final_resized_path = os.path.join(processed_dir_abs, result['resized_image'])
                
                shutil.move(result['output_image_path'], final_output_path)
                shutil.move(result['resized_image_path'], final_resized_path)

                shutil.rmtree(temp_dir)
                return render_template('result.html', result=result)
            else:
                flash(get_text('processing_error'), 'error')
                shutil.rmtree(temp_dir)
                return redirect(url_for('index'))

        except Exception as e:
            print(f"Error in /upload: {e}")
            flash(get_text('error_occurred').format(error=str(e)), 'error')
            shutil.rmtree(temp_dir)
            return redirect(url_for('index'))
    else:
        flash(get_text('file_type_not_allowed'), 'error')
        return redirect(url_for('index'))

@app.route('/download/<path:filename>')
def download_file(filename):
    """Serve files for download from the processed folder."""
    directory = app.config['PROCESSED_FOLDER']
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        flash(get_text('file_not_found'), 'error')
        return redirect(url_for('index'))

@app.route('/api/upload', methods=['POST'])
def upload_file_api():
    """Handle file uploads via API, store result in cache, and return redirect URL."""
    # 檢查是否使用範例圖片
    use_sample = request.form.get('use_sample')
    
    if use_sample:
        # 使用範例圖片 A.JPG
        sample_image_path = os.path.join(app.root_path, 'static', 'demo', 'A.JPG')
        if not os.path.exists(sample_image_path):
            return jsonify({'error': 'Sample image A.JPG not found'}), 400
        
        # 複製範例圖片到臨時目錄
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, 'A.JPG')
        shutil.copy2(sample_image_path, filepath)
        
    else:
        # 處理上傳的檔案
        if 'file' not in request.files:
            return jsonify({'error': get_text('no_file_uploaded')}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': get_text('no_selected_file')}), 400
            
        if not (file and allowed_file(file.filename)):
            return jsonify({'error': get_text('file_type_not_allowed')}), 400
        
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
    
    confidence = float(request.form.get('confidence', 0.5))

    try:
        system = FishDetectionSystem()
        result = system.process_image(filepath, confidence)
        
        if result:
            # --- FIX: Use absolute path for destination folder ---
            processed_dir_abs = os.path.join(app.root_path, app.config['PROCESSED_FOLDER'])
            final_output_path = os.path.join(processed_dir_abs, result['output_image'])
            final_resized_path = os.path.join(processed_dir_abs, result['resized_image'])
            
            shutil.move(result['output_image_path'], final_output_path)
            shutil.move(result['resized_image_path'], final_resized_path)

            # 產生一個唯一的 ID 來存放這次的結果
            result_id = str(uuid.uuid4())
            RESULTS_CACHE[result_id] = result
            
            # 清理暫存資料夾
            shutil.rmtree(temp_dir)
            
            # 回傳包含專屬 ID 的結果頁面 URL
            result_url = url_for('show_result', result_id=result_id)
            return jsonify({'redirect_url': result_url})
        else:
            shutil.rmtree(temp_dir)
            return jsonify({'error': get_text('image_processing_failed_no_api_response')}), 500

    except Exception as e:
        print(f"Error in /api/upload: {e}")
        shutil.rmtree(temp_dir)
        return jsonify({'error': get_text('error_occurred').format(error=str(e))}), 500

@app.route('/result/<result_id>')
def show_result(result_id):
    """Display the result page by fetching data from the server cache."""
    # 從快取中取出結果，.pop() 會在取出後刪除，避免快取無限增長
    result = RESULTS_CACHE.pop(result_id, None)
    
    if not result:
        flash(get_text('no_result_found'), 'error')
        return redirect(url_for('index'))
    
    return render_template('result.html', result=result)


if __name__ == '__main__':
    load_translations()
    app.run(debug=True, port=5001)
