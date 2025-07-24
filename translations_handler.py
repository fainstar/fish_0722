"""
翻譯系統模塊 - 處理多語言功能
"""
import json
from pathlib import Path
from flask import g, request, session
from config import config

# 翻譯數據存儲
translations = {}

def load_translations():
    """Load translations from JSON files."""
    lang_dir = Path(__file__).parent / 'translations'
    for lang in config.LANGUAGES:
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

def set_language_context():
    """Set the language for the current request."""
    g.language = session.get('language', request.accept_languages.best_match(config.LANGUAGES.keys()))

def get_template_context():
    """Inject translation function and language info into templates."""
    return dict(
        get_text=get_text, 
        current_language=g.language, 
        languages=config.LANGUAGES
    )

# 初始化翻譯系統
load_translations()
