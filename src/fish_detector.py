"""
魚類檢測系統模塊 - 處理圖像檢測和AI分析
"""
import os
import cv2
import numpy as np
from PIL import Image
import requests
import base64
from pathlib import Path
from src.config import config

class FishDetectionSystem:
    def __init__(self, api_key=None, endpoint_name='detect_count_visualize', model_key=None):
        self.api_key = api_key or config.ROBOFLOW_API_KEY
        
        # 如果提供了 model_key，使用指定的模型配置
        if model_key:
            model_config = config.get_model_config(model_key)
            self.api_url = model_config.get('url', config.ROBOFLOW_API_URL)
            self.model_id = model_config.get('model_id', config.ROBOFLOW_MODEL_ID)
            self.model_name = model_config.get('name', 'Unknown Model')
            self.model_key = model_key
        else:
            # 使用預設配置
            self.endpoint_config = config.get_api_endpoint(endpoint_name)
            self.api_url = self.endpoint_config.get('url', config.ROBOFLOW_API_URL)
            self.model_id = self.endpoint_config.get('model_id', config.ROBOFLOW_MODEL_ID)
            self.model_name = self.endpoint_config.get('name', 'Default Model')
            self.model_key = endpoint_name
            
        self.timeout = config.API_TIMEOUT
        self.retry_attempts = config.API_RETRY_ATTEMPTS
        self.retry_delay = config.API_RETRY_DELAY
        self.default_params = config.get_default_parameters()
    
    def set_model(self, model_key):
        """動態切換檢測模型"""
        model_config = config.get_model_config(model_key)
        if model_config:
            self.api_url = model_config.get('url', self.api_url)
            self.model_id = model_config.get('model_id', self.model_id)
            self.model_name = model_config.get('name', 'Unknown Model')
            self.model_key = model_key
            return True
        return False
        
    def resize_image(self, image_path, max_size=None):
        """調整圖片大小，確保不超過指定的最大尺寸"""
        if max_size is None:
            max_size = (config.IMAGE_MAX_SIZE['width'], config.IMAGE_MAX_SIZE['height'])
            
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            resized_path = Path(image_path).with_name("resized_" + Path(image_path).name)
            
            # 使用配置中的品質設定
            if img.format == 'JPEG':
                img.save(resized_path, format=img.format, quality=config.IMAGE_QUALITY)
            else:
                img.save(resized_path, format=img.format)
        return resized_path

    def image_to_base64(self, image_path):
        """將圖片轉換為base64字串"""
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

    def detect_fish_api(self, image_path, confidence=None):
        """使用 Roboflow API 進行魚類偵測"""
        headers = {'Content-Type': 'application/json'}
        
        # 使用配置中的預設參數，並允許覆蓋
        params = self.default_params.copy()
        if confidence is not None:
            params['confidence'] = confidence
        
        # 根據API端點類型構建不同的payload格式
        if "127.0.0.1" in self.api_url or "localhost" in self.api_url:
            # 本地API：使用原始圖片，不壓縮
            image_base64 = self.image_to_base64(image_path)
            payload = {
                "image": image_base64,
                "model": self.model_id,  # 添加模型ID參數
                "confidence": confidence if confidence is not None else 0.5,
                "iou_threshold": 0.5  # 添加 IoU 閾值參數
            }
            used_image_path = image_path  # 記錄使用的圖片路徑
        else:
            # Roboflow API：使用調整大小後的圖片
            resized_image_path = self.resize_image(image_path)
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
            # 添加額外參數到 payload
            if params:
                payload.update(params)
            used_image_path = str(resized_image_path)  # 記錄使用的圖片路徑
        
        # 實施重試邏輯
        import time
        print(f"使用 API URL: {self.api_url}")
        print(f"模型名稱: {self.model_name}")
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                response_data = response.json()
                
                # 儲存API回應，包含更多元數據
                response_file = Path(image_path).with_name("response.json")
                metadata = {
                    "api_endpoint": self.api_url,
                    "model_id": self.model_id,
                    "parameters": params,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "attempt": attempt + 1,
                    "response": response_data
                }
                
                with open(response_file, "w", encoding="utf-8") as json_file:
                    import json
                    json.dump(metadata, json_file, indent=2, ensure_ascii=False)
                    
                return response_data, used_image_path
                
            except requests.exceptions.RequestException as e:
                if attempt < self.retry_attempts - 1:
                    print(f"API 調用失敗，第 {attempt + 1} 次重試: {e}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"API 調用最終失敗: {e}")
                    raise e
            print(f"API request error: {e}")
            return None, None

    def load_predictions_from_response(self, response_data):
        """從API回應中提取預測結果"""
        try:
            # 檢查是否為本地API的 /detect/simple 格式
            if 'predictions' in response_data and isinstance(response_data['predictions'], list):
                # 本地API /detect/simple 格式
                # 注意：本地API的 x,y 是左上角坐標，需要轉換為中心點坐標以保持一致性
                converted_predictions = []
                for pred in response_data['predictions']:
                    # 本地API返回的是左上角坐標，但我們的繪製邏輯期望中心點坐標
                    # 所以這裡轉換為中心點坐標格式
                    left_x = pred['x']
                    top_y = pred['y']
                    width = pred['width']
                    height = pred['height']
                    
                    # 轉換為中心點坐標
                    center_x = left_x + width / 2
                    center_y = top_y + height / 2
                    
                    converted_pred = {
                        'class': pred.get('class', 'Fish'),
                        'confidence': pred['confidence'],
                        'x': center_x,  # 中心點 x
                        'y': center_y,  # 中心點 y
                        'width': width,
                        'height': height
                    }
                    converted_predictions.append(converted_pred)
                return converted_predictions
            # 檢查是否為本地API的 /detect 格式
            elif 'detections' in response_data and isinstance(response_data['detections'], list):
                # 本地API /detect 格式 - 轉換為 Roboflow 格式
                converted_predictions = []
                for det in response_data['detections']:
                    bbox = det['bbox']
                    # 從 x1,y1,x2,y2 轉換為中心點和寬高
                    width = bbox['x2'] - bbox['x1']
                    height = bbox['y2'] - bbox['y1']
                    center_x = bbox['x1'] + width / 2
                    center_y = bbox['y1'] + height / 2
                    
                    converted_pred = {
                        'class': det.get('class_name', 'Fish'),
                        'confidence': det['confidence'],
                        'x': center_x,
                        'y': center_y,
                        'width': width,
                        'height': height
                    }
                    converted_predictions.append(converted_pred)
                return converted_predictions
            # Roboflow API格式
            elif 'outputs' in response_data:
                predictions = response_data['outputs'][0]['predictions']['predictions']
                return predictions
            else:
                print(f"Unknown response format: {list(response_data.keys())}")
                print(f"Sample response data: {response_data}")
                return []
        except Exception as e:
            print(f"Error extracting predictions: {str(e)}")
            print(f"Response data structure: {response_data}")
            return []

    def draw_detections(self, image, predictions, confidence_threshold=0.5, original_size=None, api_url=None):
        """在圖片上繪製偵測結果，並根據信賴度使用不同顏色的框。"""
        annotated_image = image.copy()
        current_height, current_width = image.shape[:2]
        
        # 定義莫蘭迪色系 (BGR格式)
        colors = {
            'high_conf': (153, 184, 163),  # 鼠尾草綠 (Sage Green)
            'med_conf': (132, 163, 213),   # 灰橘 (Dusty Orange)
            'low_conf': (137, 137, 195),   # 煙灰粉 (Dusty Rose)
            'text_bg': (80, 80, 80),       # 深灰背景
            'text': (245, 245, 245)      # 米白文字
        }
        
        # 計算縮放比例（只對遠程API需要）
        scale_x = scale_y = 1.0
        is_local_api = api_url and ("127.0.0.1" in api_url or "localhost" in api_url)
        
        print(f"API URL: {api_url}")
        print(f"是否為本地API: {is_local_api}")
        
        if not is_local_api and original_size and len(predictions) > 0:
            # 遠程API：需要座標縮放（因為使用的是調整後的圖片，但座標基於原始圖片）
            first_pred = predictions[0]
            if 'x' in first_pred and first_pred['x'] > current_width:
                # 座標基於原始圖片，需要縮放
                scale_x = current_width / original_size[0]
                scale_y = current_height / original_size[1]
                print(f"遠程API - 座標縮放比例: x={scale_x:.3f}, y={scale_y:.3f}")
                print(f"原始尺寸: {original_size}, 當前尺寸: ({current_width}, {current_height})")
        elif is_local_api:
            print(f"本地API - 使用原始圖片，座標無需縮放")
        
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
                
                # 根據API類型使用不同的座標計算方式
                if is_local_api:
                    # 本地API：我們已經在 load_predictions_from_response 中轉換為中心點坐標
                    # 所以這裡按照中心點坐標處理
                    x1 = int(x_center - width / 2)
                    y1 = int(y_center - height / 2)
                    x2 = int(x_center + width / 2)
                    y2 = int(y_center + height / 2)
                    print(f"本地API座標計算: 中心點({x_center}, {y_center}), 尺寸({width}x{height})")
                    print(f"邊界框: ({x1}, {y1}) 到 ({x2}, {y2})")
                else:
                    # 遠程API使用中心點座標格式
                    x_center_scaled = x_center * scale_x
                    y_center_scaled = y_center * scale_y
                    width_scaled = width * scale_x
                    height_scaled = height * scale_y
                    
                    x1 = int(x_center_scaled - width_scaled / 2)
                    y1 = int(y_center_scaled - height_scaled / 2)
                    x2 = int(x_center_scaled + width_scaled / 2)
                    y2 = int(y_center_scaled + height_scaled / 2)
                    print(f"遠程API座標計算: 中心({x_center_scaled:.1f}, {y_center_scaled:.1f}), 尺寸({width_scaled:.1f}x{height_scaled:.1f})")
                    print(f"邊界框: ({x1}, {y1}) 到 ({x2}, {y2})")
                
                # 確保座標在圖片範圍內
                x1 = max(0, min(x1, current_width - 1))
                y1 = max(0, min(y1, current_height - 1))
                x2 = max(0, min(x2, current_width - 1))
                y2 = max(0, min(y2, current_height - 1))
                
                print(f"裁剪後邊界框: ({x1}, {y1}) 到 ({x2}, {y2})")
                
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
        
        # 獲取原始圖片尺寸
        with Image.open(image_path) as original_img:
            original_size = original_img.size  # (width, height)
        
        response_data, used_image_path = self.detect_fish_api(image_path)
        
        if not response_data:
            return None

        # 根據使用的圖片路徑讀取圖片
        image = cv2.imread(used_image_path)
        if image is None:
            print(f"無法讀取圖片: {used_image_path}")
            return None
        
        print(f"載入的圖片尺寸: {image.shape[:2]} (高度x寬度)")
        print(f"使用的圖片路徑: {used_image_path}")

        predictions = self.load_predictions_from_response(response_data)
        
        # 1. 繪製偵測框，此函式內部已根據 confidence_threshold 進行篩選
        # 返回的 fish_count 和 fish_details 都已是篩選後的結果
        # 傳遞原始尺寸和API URL用於座標縮放判斷
        annotated_image, fish_count, fish_details = self.draw_detections(
            image, predictions, confidence_threshold, original_size, self.api_url
        )
        
        # 2. 再加上統計資訊
        # 直接將篩選後的結果傳入即可
        annotated_image_with_summary = self.add_summary_info(annotated_image, fish_count, fish_details)

        # 儲存最終處理後的圖片
        original_filename = Path(image_path).name
        output_filename = "detected_" + original_filename
        output_path = Path(used_image_path).parent / output_filename
        cv2.imwrite(str(output_path), annotated_image_with_summary)
        
        end_time = cv2.getTickCount()
        process_time = (end_time - start_time) / cv2.getTickFrequency()
        
        # 確定返回的圖片資訊
        if used_image_path == image_path:
            # 使用原始圖片（本地API）
            used_image_name = Path(image_path).name
        else:
            # 使用調整大小的圖片（遠程API）
            used_image_name = Path(used_image_path).name
        
        return {
            "output_image": output_filename,
            "output_image_path": str(output_path),
            "used_image": used_image_name,
            "used_image_path": used_image_path,
            "fish_count": fish_count,
            "fish_details": fish_details,
            "process_time": process_time,
            "confidence": confidence_threshold
        }
