"""
日誌系統模塊 - 處理所有日誌相關功能
"""
import os
import re
import logging
import logging.handlers
from datetime import datetime
from user_agents import parse
from flask import request, session, g
from src.config import config

# 全局日誌記錄器
app_logger = None

def setup_logging():
    """設置日誌系統"""
    global app_logger
    
    # 如果已經初始化過，直接返回
    if app_logger is not None:
        return app_logger
    
    # 創建日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 創建主要應用程式日誌
    app_logger = logging.getLogger('fish_app')
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False  # 防止向父記錄器傳播
    
    # 清除既有的處理器以防重複
    app_logger.handlers.clear()
    

    
    # 應用程式日誌文件處理器
    app_handler = logging.FileHandler(
        os.path.join(config.LOG_DIR, 'app.log')
    )
    app_handler.setFormatter(log_format)
    app_logger.addHandler(app_handler)
    

    
    # 控制台輸出處理器（可選）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    app_logger.addHandler(console_handler)
    
    return app_logger

def get_app_logger():
    """獲取應用程式日誌記錄器，如果不存在則初始化"""
    global app_logger
    if app_logger is None:
        setup_logging()
    return app_logger



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
    
    app_logger = get_app_logger()
    app_logger.info(log_message)
    
    return log_data

def parse_user_activity_logs(log_type='', date_from='', date_to='', ip_address='', limit=500):
    """解析用戶活動日誌（現在包含所有日誌類型）"""
    logs = []
    log_file = os.path.join(config.LOG_DIR, 'app.log')
    
    if not os.path.exists(log_file):
        return logs
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        lines = lines[-limit:]
        
        for line in reversed(lines):
            try:
                parts = line.strip().split(' - ', 2)
                if len(parts) < 3:
                    continue
                
                timestamp = parts[0]
                level = parts[1]
                message = parts[2]
                
                # 嘗試解析為結構化日誌
                log_data = parse_log_message(message)
                if not log_data:
                    # 如果失敗，則作為通用日誌處理
                    log_data = {'message': message}

                log_data['timestamp'] = timestamp
                log_data['level'] = level
                if 'message' not in log_data:
                    log_data['message'] = message

                # 過濾邏輯
                log_date = timestamp.split(' ')[0]
                if date_from and log_date < date_from:
                    continue
                if date_to and log_date > date_to:
                    continue

                # 對 IP 和日誌類型進行更寬鬆的過濾
                passes_ip_filter = not ip_address or ip_address in log_data.get('ip', '') or ip_address in message
                passes_type_filter = not log_type or log_type in log_data.get('action', '') or log_type in message

                if not (passes_ip_filter and passes_type_filter):
                    continue
                
                logs.append(log_data)
                
            except Exception:
                continue
    
    except Exception as e:
        if app_logger:
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
    """計算日誌統計數據 - 現在能處理統一日誌格式"""
    stats = {
        'total_users': 0,
        'total_uploads': 0,
        'total_fish': 0,
        'avg_processing_time': 0,
        'total_errors': 0
    }
    
    unique_ips = set()
    processing_times = []
    upload_sessions = set()

    for log in logs:
        message = log.get('message', '')
        
        # 統計唯一用戶 (從結構化資料或原始訊息中提取)
        ip = log.get('ip')
        if not ip:
            ip_match = re.search(r'IP: ([\d.]+)', message) or re.search(r'User: ([\d.]+)', message)
            if ip_match:
                ip = ip_match.group(1)
        if ip:
            unique_ips.add(ip)

        # 統計上傳
        # 依賴於 'file_upload' action 或 'API processing successful' 等訊息
        is_upload = False
        if log.get('action') == 'file_upload':
            is_upload = True
        elif 'API processing successful' in message or 'Result page viewed' in message:
            is_upload = True

        if is_upload:
            # 創建一個簡化的會話鍵來避免重複計算
            timestamp = log.get('timestamp', '')
            session_key = f"{ip}_{timestamp[:16]}"
            if session_key not in upload_sessions:
                stats['total_uploads'] += 1
                upload_sessions.add(session_key)

        # 統計魚類數量 (從結構化資料或原始訊息中提取)
        fish_count = 0
        if log.get('details') and 'fish_count' in log['details']:
            try:
                fish_count = int(log['details']['fish_count'])
            except (ValueError, TypeError):
                pass
        else:
            fish_match = re.search(r'Found (\d+) fish', message) or re.search(r'Fish count: (\d+)', message)
            if fish_match:
                try:
                    fish_count = int(fish_match.group(1))
                except (ValueError, TypeError):
                    pass
        stats['total_fish'] += fish_count

        # 統計處理時間 (從結構化資料或原始訊息中提取)
        if log.get('details') and 'processing_time' in log['details']:
            try:
                time_str = str(log['details']['processing_time']).replace('s', '')
                processing_times.append(float(time_str))
            except (ValueError, TypeError):
                pass
        else:
            time_match = re.search(r'Processing time: ([\d.]+)s', message)
            if time_match:
                try:
                    processing_times.append(float(time_match.group(1)))
                except (ValueError, TypeError):
                    pass

        # 統計錯誤
        if log.get('level') == 'ERROR' or 'error' in log.get('action', '').lower():
            stats['total_errors'] += 1

    stats['total_users'] = len(unique_ips)
    if processing_times:
        stats['avg_processing_time'] = sum(processing_times) / len(processing_times)
    
    return stats

def parse_app_logs(date_from='', date_to='', limit=200):
    """解析應用程式日誌"""
    logs = []
    log_file = os.path.join(config.LOG_DIR, 'app.log')
    
    if not os.path.exists(log_file):
        return logs
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 只讀取最新的 limit 行
        lines = lines[-limit:]
        
        for line in reversed(lines):  # 最新的在前
            try:
                # 解析日誌行: 2025-07-24 12:21:22 - INFO - API processing successful: A.JPG - Found 74 fish - User: 127.0.0.1
                parts = line.strip().split(' - ', 2)
                if len(parts) < 3:
                    continue
                
                timestamp = parts[0]
                level = parts[1]
                message = parts[2]
                
                # 日期篩選
                log_date = timestamp.split(' ')[0]
                if date_from and log_date < date_from:
                    continue
                if date_to and log_date > date_to:
                    continue
                
                # 解析消息內容以提取更多信息
                log_data = {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'type': 'app_log'
                }
                
                # 嘗試從消息中提取結構化信息
                if 'API processing successful' in message:
                    log_data['action'] = 'api_processing'
                    log_data['status'] = 'success'
                elif 'Result page viewed' in message:
                    log_data['action'] = 'result_view'
                    log_data['status'] = 'info'
                elif 'Language changed' in message:
                    log_data['action'] = 'language_change'
                    log_data['status'] = 'info'
                elif 'Fish Detection System started' in message:
                    log_data['action'] = 'system_start'
                    log_data['status'] = 'info'
                elif 'New user session started' in message:
                    log_data['action'] = 'new_session'
                    log_data['status'] = 'info'
                else:
                    log_data['action'] = 'general'
                    log_data['status'] = level.lower()
                
                logs.append(log_data)
                
            except Exception as e:
                continue  # 跳過解析失敗的行
    
    except Exception as e:
        if app_logger:
            app_logger.error(f"Error reading app log file: {str(e)}")
    
    return logs

def get_combined_logs(log_type='', date_from='', date_to='', ip_address='', limit=300):
    """獲取合併的日誌數據"""
    # 現在所有日誌都在 app.log 中，我們直接解析它
    all_logs = parse_user_activity_logs(log_type, date_from, date_to, ip_address, limit)

    # 按時間排序（最新的在前）
    try:
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except:
        pass

    return all_logs
