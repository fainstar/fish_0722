"""
路由模塊 - 包含所有Web路由處理
"""
import os
import tempfile
import shutil
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session, g

from src.config import config
from src.logger import get_client_info, log_user_activity, get_app_logger, parse_user_activity_logs, calculate_log_statistics, get_combined_logs
from src.translations_handler import get_text
from src.fish_detector import FishDetectionSystem
from src.file_utils import allowed_file, clean_processed_folder, get_file_size, save_uploaded_file, move_processed_files, create_sample_image_copy

# 伺服器端暫存處理結果的地方
RESULTS_CACHE = {}

def register_routes(app):
    """註冊所有路由到Flask應用"""
    
    @app.route('/set_language/<language>')
    def set_language(language=None):
        """Set the user's language preference."""
        client_info = get_client_info(request)
        
        if language in config.LANGUAGES:
            session['language'] = language
            log_user_activity('language_change', {
                'new_language': language,
                'old_language': session.get('language', 'default'),
                'available_languages': list(config.LANGUAGES.keys())
            }, client_info)
            get_app_logger().info(f"Language changed to {language} for user {client_info['ip_address']}")
        else:
            log_user_activity('invalid_language_attempt', {
                'attempted_language': language,
                'available_languages': list(config.LANGUAGES.keys())
            }, client_info)
            get_app_logger().warning(f"Invalid language change attempt: {language} from {client_info['ip_address']}")
        
        return redirect(request.referrer or url_for('index'))

    @app.route('/')
    def index():
        """Render the main upload page."""
        client_info = get_client_info(request)
        log_user_activity('home_page_visit', {
            'user_language': getattr(g, 'language', 'en'),
            'session_duration': 'new_session' if 'session_start' not in session else 'returning'
        }, client_info)
        
        if 'session_start' not in session:
            session['session_start'] = datetime.now().isoformat()
            get_app_logger().info(f"New user session started for {client_info['ip_address']}")
        
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
            file_size = get_file_size(file)
            
            log_user_activity('file_upload_start', {
                'filename': file.filename,
                'original_filename': file.filename,
                'file_size_bytes': file_size,
                'file_type': file.content_type,
                'confidence': request.form.get('confidence', 0.5)
            }, client_info)
            
            temp_dir = tempfile.mkdtemp()
            filepath, filename = save_uploaded_file(file, temp_dir)
            
            confidence = float(request.form.get('confidence', 0.5))

            try:
                system = FishDetectionSystem()
                start_time = datetime.now()
                result = system.process_image(filepath, confidence)
                process_time = (datetime.now() - start_time).total_seconds()
                
                if result:
                    move_processed_files(result, app.root_path)
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
                    
                    get_app_logger().info(f"File processed successfully: {filename} - Found {result['fish_count']} fish - Processing time: {process_time:.2f}s - User: {client_info['ip_address']}")

                    shutil.rmtree(temp_dir)
                    return render_template('result.html', result=result)
                else:
                    log_user_activity('file_processing_failed', {
                        'filename': filename,
                        'error_type': 'no_api_response',
                        'confidence_threshold': confidence,
                        'processing_time_seconds': process_time
                    }, client_info)
                    
                    get_app_logger().error(f"File processing failed (no API response): {filename} - User: {client_info['ip_address']}")
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
                
                get_app_logger().error(f"File processing error: {filename} - {str(e)} - User: {client_info['ip_address']}")
                flash(get_text('error_occurred').format(error=str(e)), 'error')
                shutil.rmtree(temp_dir)
                return redirect(url_for('index'))
        else:
            log_user_activity('upload_error', {
                'error_type': 'file_type_not_allowed',
                'filename': file.filename if file else 'unknown',
                'file_type': file.content_type if file else 'unknown'
            }, client_info)
            
            get_app_logger().warning(f"File type not allowed: {file.filename if file else 'unknown'} - User: {client_info['ip_address']}")
            flash(get_text('file_type_not_allowed'), 'error')
            return redirect(url_for('index'))

    @app.route('/download/<path:filename>')
    def download_file(filename):
        """Serve files for download from the processed folder."""
        client_info = get_client_info(request)
        directory = config.PROCESSED_FOLDER
        try:
            log_user_activity('file_download', {
                'filename': filename,
                'download_type': 'processed_image'
            }, client_info)
            
            get_app_logger().info(f"File download: {filename} - User: {client_info['ip_address']}")
            return send_from_directory(directory, filename, as_attachment=True)
        except FileNotFoundError:
            log_user_activity('download_error', {
                'filename': filename,
                'error_type': 'file_not_found'
            }, client_info)
            
            get_app_logger().error(f"Download failed - file not found: {filename} - User: {client_info['ip_address']}")
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
            
            temp_dir = tempfile.mkdtemp()
            filepath, filename, file_size = create_sample_image_copy(app.root_path, temp_dir)
            
            if not filepath:
                log_user_activity('api_error', {
                    'error_type': 'sample_image_not_found',
                    'sample_image': 'A.JPG'
                }, client_info)
                return jsonify({'error': 'Sample image A.JPG not found'}), 400
            
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
            
            file_size = get_file_size(file)
            temp_dir = tempfile.mkdtemp()
            filepath, filename = save_uploaded_file(file, temp_dir)
            
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
                move_processed_files(result, app.root_path)
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
                
                get_app_logger().info(f"API processing successful: {filename} - Found {result['fish_count']} fish - Processing time: {process_time:.2f}s - User: {client_info['ip_address']}")
                
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
                
                get_app_logger().error(f"API processing failed (no API response): {filename} - User: {client_info['ip_address']}")
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
            
            get_app_logger().error(f"API processing error: {filename} - {str(e)} - User: {client_info['ip_address']}")
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
            
            get_app_logger().warning(f"Result not found in cache: {result_id} - User: {client_info['ip_address']}")
            flash(get_text('no_result_found'), 'error')
            return redirect(url_for('index'))
        
        log_user_activity('result_page_view', {
            'result_id': result_id,
            'fish_count': result.get('fish_count', 0),
            'output_image': result.get('output_image', 'unknown'),
            'confidence': result.get('confidence', 0.5)
        }, client_info)
        
        get_app_logger().info(f"Result page viewed: {result_id} - Fish count: {result.get('fish_count', 0)} - User: {client_info['ip_address']}")
        
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
        
        # 讀取合併的日誌
        logs = get_combined_logs(log_type, date_from, date_to, ip_address)
        
        # 計算統計數據（使用合併的日誌，包含應用程式日誌中的魚類檢測數據）
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
        if admin_password != config.ADMIN_PASSWORD:
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
        
        # 讀取合併的日誌
        logs = get_combined_logs(log_type, date_from, date_to, ip_address)
        
        # 計算統計數據（使用合併的日誌，包含應用程式日誌中的魚類檢測數據）
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
        if admin_password != config.ADMIN_PASSWORD:
            log_user_activity('admin_access_denied', {
                'attempted_password': admin_password or 'none',
                'action': 'clear_logs'
            }, client_info)
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        try:
            # 清除用戶活動日誌
            user_log_file = os.path.join(config.LOG_DIR, 'user_activity.log')
            if os.path.exists(user_log_file):
                open(user_log_file, 'w').close()
            
            log_user_activity('admin_logs_cleared', {
                'admin_action': 'clear_all_logs'
            }, client_info)
            
            get_app_logger().info(f"Logs cleared by admin from {client_info['ip_address']}")
            
            return jsonify({'success': True})
        except Exception as e:
            get_app_logger().error(f"Error clearing logs: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
