"""
翻譯系統模塊 - 處理多語言功能
"""
import json
from pathlib import Path
from flask import g, request, session
from src.config import config

# 翻譯數據存儲
translations = {}

def load_translations():
    """Load translations from JSON files."""
    # 修正翻譯文件路徑 - 翻譯文件在專案根目錄
    lang_dir = Path(__file__).parent.parent / 'translations'
    for lang in config.LANGUAGES:
        filepath = lang_dir / f"{lang}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
        else:
            print(f"Warning: Translation file not found: {filepath}")
            translations[lang] = {}

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

def set_language_context():
    """Set the language for the current request."""
    # 從 session 獲取語言，如果沒有則使用瀏覽器語言偏好，最後預設為中文
    lang = session.get('language')
    if not lang:
        lang = request.accept_languages.best_match(config.LANGUAGES.keys()) or 'zh'
    g.language = lang

def get_template_context():
    """Inject translation function and language info into templates."""
    return dict(
        get_text=get_text, 
        current_language=getattr(g, 'language', 'zh'), 
        languages=config.LANGUAGES
    )

# 初始化翻譯系統
load_translations()
