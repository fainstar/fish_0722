"""
文件處理工具模塊 - 處理文件上傳、驗證和清理
"""
import os
import shutil
from werkzeug.utils import secure_filename
from config import config
from logger import app_logger

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def clean_processed_folder():
    """保持 processed 資料夾中最多只有 MAX_PROCESSED_FILES 個檔案"""
    try:
        processed_dir = os.path.join(os.getcwd(), config.PROCESSED_FOLDER)
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
        if len(files) > config.MAX_PROCESSED_FILES:
            files_to_delete = files[:-config.MAX_PROCESSED_FILES]  # 保留最新的 MAX_PROCESSED_FILES 個檔案
            for filepath, _ in files_to_delete:
                try:
                    os.remove(filepath)
                    print(f"已刪除舊檔案: {filepath}")
                except OSError as e:
                    print(f"無法刪除檔案 {filepath}: {e}")
                    
    except Exception as e:
        print(f"清理 processed 資料夾時發生錯誤: {e}")

def get_file_size(file):
    """獲取上傳文件的大小"""
    file.seek(0, 2)  # 移動到文件末尾
    size = file.tell()
    file.seek(0)  # 重置到文件開頭
    return size

def save_uploaded_file(file, temp_dir):
    """安全地保存上傳的文件"""
    filename = secure_filename(file.filename)
    filepath = os.path.join(temp_dir, filename)
    file.save(filepath)
    return filepath, filename

def move_processed_files(result, app_root_path):
    """將處理後的文件移動到最終目錄"""
    processed_dir_abs = os.path.join(app_root_path, config.PROCESSED_FOLDER)
    final_output_path = os.path.join(processed_dir_abs, result['output_image'])
    final_resized_path = os.path.join(processed_dir_abs, result['resized_image'])
    
    shutil.move(result['output_image_path'], final_output_path)
    shutil.move(result['resized_image_path'], final_resized_path)
    
    return final_output_path, final_resized_path

def create_sample_image_copy(app_root_path, temp_dir):
    """創建範例圖片副本"""
    sample_image_path = os.path.join(app_root_path, 'static', 'demo', 'A.JPG')
    if not os.path.exists(sample_image_path):
        return None, None, None
    
    filepath = os.path.join(temp_dir, 'A.JPG')
    shutil.copy2(sample_image_path, filepath)
    filename = 'A.JPG'
    file_size = os.path.getsize(sample_image_path)
    
    return filepath, filename, file_size
