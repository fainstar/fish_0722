#!/usr/bin/env python3
"""
魚類檢測系統 - 主應用程式入口點
"""
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 導入並運行應用程式
if __name__ == '__main__':
    from app_new import main
    main()