# 🐟 Fish Detection System - 魚類檢測系統

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.0-brightgreen.svg)](PROJECT_STRUCTURE.md)

## 📖 專案簡介

基於 AI 深度學習的魚類檢測系統，支援圖片上傳、智能分析、多語言介面。採用 Flask 後端 + 現代化前端設計，提供完整的容器化部署方案。

### ✨ 主要特色
- 🤖 **AI 智能檢測** - 基於 YOLO 的魚類識別技術
- 🌍 **多語言支援** - 繁中🇹🇼 / English🇺🇸 / 日本語🇯🇵 
- 🎨 **現代化 UI** - Morandi 配色系統，響應式設計
- 🐳 **容器化部署** - 完整 Docker 生產環境
- 📊 **完整日誌** - 用戶行為分析和系統監控
- 🔧 **模組化架構** - 清晰的代碼組織和維護性

## 🚀 快速開始

### 💻 本地開發環境

```bash
# 1. 克隆專案
git clone https://github.com/fainstar/fish_0722.git
cd fish_0722

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動應用程式
python src/app_new.py

# 4. 瀏覽器訪問
# http://localhost:5001
```

### 🐳 Docker 部署（推薦）

```bash
# 一鍵部署
./scripts/docker-deploy.sh build
./scripts/docker-deploy.sh run

# 或使用 Docker Compose
cd docker
docker-compose up -d

# 查看運行狀態
docker ps
```

## 📁 專案結構

```
fish_0722/
├── 📱 app.py                    # 舊版應用程式入口點 (已棄用)
├── 📋 requirements.txt          # Python 依賴清單
├── 📄 README.md                # 專案說明文檔
│
├── 📁 src/                     # 🎯 核心源碼目錄
│   ├── app_new.py              # ✨ 新版應用程式入口點
│   ├── app_docker.py           # Docker 生產環境應用
│   ├── config.py               # 本地開發環境配置
│   ├── docker_config.py        # Docker 環境專用配置
│   ├── production_config.py    # 生產環境配置
│   ├── routes.py               # Web 路由處理
│   ├── fish_detector.py        # AI 魚類檢測核心
│   ├── logger.py               # 完整日誌系統
│   ├── translations_handler.py # 多語言國際化支援
│   └── file_utils.py           # 檔案處理工具集
│
├── 📁 docker/                  # 🐳 容器化部署
│   ├── Dockerfile              # 主要 Docker 映像
│   ├── docker-compose.yml      # 服務編排配置
│   └── .dockerignore           # Docker 忽略規則
│
├── 📁 templates/               # 🎨 前端模板
│   ├── base.html               # 基礎模板（導航、多語言）
│   ├── index.html              # 主頁面（上傳介面）
│   ├── result.html             # 檢測結果展示
│   └── logs.html               # 系統日誌查看
│
├── 📁 static/                  # 📦 靜態資源
│   ├── css/                    # 模組化樣式表 (main.css, result.css, logs.css)
│   ├── js/                     # 互動邏輯腳本 (main.js, result.js, logs.js)
│   ├── demo/                   # 示範圖片
│   └── processed/              # AI 處理結果
│
├── 📁 translations/            # 🌍 國際化語言包
│   ├── zh.json                 # 繁體中文
│   ├── en.json                 # English
│   └── ja.json                 # 日本語
│
└── 📁 logs/                    # 📊 系統日誌
    ├── app.log                 # 應用程式運行日誌
    └── user_activity.log       # 用戶行為分析日誌
```

## 🏗️ 架構設計

### 應用程式架構
```
┌─────────────────────────────────┐
│  src/app_new.py (統一入口點)     │
└─────────┬───────────────────────┘
          │
    ┌─────▼─────┐    ┌─────────────┐
    │  本地環境  │    │  Docker環境  │
    │ config.py  │    │docker_config│
    └─────┬─────┘    └─────┬───────┘
          │                │
          └────────┬───────┘
                   │
        ┌──────────▼──────────┐
        │   核心模組群組        │
        │ • routes.py         │
        │ • fish_detector.py  │
        │ • logger.py         │
        │ • translations.py   │
        │ • file_utils.py     │
        └─────────────────────┘
```

### 技術棧
- **後端**: Flask + Python 3.9+
- **AI 檢測**: YOLO + OpenCV
- **前端**: HTML5 + CSS3 + JavaScript (Vanilla)
- **樣式**: Bootstrap + 自定義 Morandi 配色
- **容器化**: Docker + Docker Compose
- **日誌**: 自建完整日誌系統
- **國際化**: JSON 語言包系統

## 📊 功能特色

### 🎯 核心功能
- **圖片上傳**: 支援多種圖片格式上傳
- **AI 檢測**: 智能魚類識別和標註
- **結果展示**: 直觀的檢測結果和統計
- **歷史記錄**: 完整的操作日誌追蹤

### 🌐 用戶體驗
- **多語言切換**: 即時語言切換，無需重載
- **響應式設計**: 支援桌面/平板/手機
- **現代化 UI**: Morandi 配色，優雅簡潔
- **流暢動畫**: CSS3 過渡效果和互動反饋

### 🔧 管理功能
- **系統監控**: 實時日誌查看和分析
- **用戶行為**: 詳細的使用統計
- **性能追蹤**: 處理時間和資源使用
- **錯誤處理**: 完善的異常捕獲和記錄

## 🐳 Docker 部署指南

### 映像構建
```bash
# 開發環境
docker build -t fish-detection:dev -f docker/Dockerfile .

# 生產環境
docker build -t fish-detection:prod -f docker/Dockerfile.prod .

# 自動化腳本
./scripts/docker-deploy.sh build    # 構建映像
./scripts/docker-deploy.sh run     # 運行容器
./scripts/docker-deploy.sh push    # 推送到倉庫
```

### 建構與推送 Docker 映像檔 (可選)

如果您需要重新建構並推送到您自己的 Docker Hub，請使用以下指令。這主要適用於開發者或需要自訂映像檔的使用者。

```bash
# 建置並推送映像
docker buildx build --platform linux/amd64 -f docker/Dockerfile -t oomaybeoo/fish-front:latest --push .
```

### 容器運行
```bash
# Docker Compose（推薦）
cd docker
docker-compose up -d                # 後台運行
docker-compose logs -f              # 查看日誌
docker-compose down                 # 停止服務

# 直接運行
docker run -d \
  --name fish-detection \
  -p 5001:5001 \
  -v $(pwd)/logs:/app/logs \
  fish-detection:prod
```

### 訪問地址

| 功能 | 地址 | 描述 |
|------|------|------|
| 🏠 主應用 | http://localhost:5001 | 魚類檢測主介面 |
| 📊 日誌查看 | http://localhost:5001/log | 系統運行日誌 |
| 🔧 管理後台 | http://localhost:5001/admin/logs?admin_key=admin123 | 管理員介面 |
| 🌐 語言切換 | http://localhost:5001/set_language/en | 動態語言切換 |

## ✅ 測試

本專案使用 `pytest` 進行單元測試和整合測試，並使用 `pytest-cov` 來計算測試覆蓋率。

### 運行測試

```bash
# 運行所有測試並生成覆蓋率報告
pytest --cov=src
```

### 測試狀態

- ✅ **16/16 個測試案例通過**
- 📊 **總體測試覆蓋率: 48%**

| 模組                     | 測試覆蓋率 |
| ------------------------ | ---------- |
| `src/docker_config.py`     | 100%       |
| `src/production_config.py` | 100%       |
| `src/app_new.py`           | 88%        |
| `src/translations_handler.py` | 87%        |
| `src/file_utils.py`        | 85%        |
| `src/app_docker.py`        | 77%        |
| `src/logger.py`            | 69%        |
| `src/config.py`            | 62%        |

## 🛠️ 開發指南

### 系統要求
- Python 3.9+
- Docker 20.10+
- 8GB+ RAM (AI 模型運行)
- 2GB+ 可用磁碟空間

### 開發環境設置
```bash
# 創建虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安裝開發依賴
pip install -r requirements.txt

# 運行測試
python scripts/test_modules.py

# 系統優化檢查
python tools/system_optimizer.py
```

### 代碼規範
- 遵循 PEP 8 Python 代碼風格
- 使用類型提示增強代碼可讀性
- 模組化設計，職責分離
- 完整的錯誤處理和日誌記錄

## 📈 檔案管理

### ✅ 核心使用中檔案
```
🎯 關鍵檔案（正在使用）:
├── src/app_docker.py          ⭐ Docker 主要入口
├── src/routes.py              ⭐ 路由核心
├── src/fish_detector.py       ⭐ AI 檢測引擎
├── src/logger.py              ⭐ 日誌系統
├── src/config.py              ⭐ 配置管理
├── templates/*.html           ⭐ 所有模板
├── static/css/*.css           ⭐ 所有樣式表
└── translations/*.json        ⭐ 多語言檔案
```

### 🧹 維護清理
```bash
# 清理處理結果圖片（保留最近50個）
find static/processed -name "*.jpg" -type f | head -n -50 | xargs rm -f

# 清理系統暫存文件
find . -name ".DS_Store" -delete
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 日誌輪轉（保留最近7天）
find logs -name "*.log" -mtime +7 -delete

# Docker 清理
docker system prune -f
```

## 🔍 故障排除

### 常見問題
1. **模組導入錯誤**: 確認 src/ 目錄在 Python 路徑中
2. **Docker 構建失敗**: 檢查 Dockerfile 中的依賴項
3. **AI 檢測無響應**: 確認 API 金鑰配置正確
4. **多語言顯示異常**: 檢查 translations/ 檔案完整性

### 性能監控
```bash
# 查看容器資源使用
docker stats fish-detection

# 監控處理速度
tail -f logs/fish_detection.log | grep "processing_time"

# 檢查日誌檔案大小
du -sh logs/
```

## 🤝 貢獻指南

1. Fork 專案倉庫
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 開發規範
- 新功能需包含對應測試
- 提交前運行 `python scripts/test_modules.py`
- 更新相關文檔說明
- 遵循現有代碼風格

## 📋 更新日誌

### v2.0 (2025-07-24)
- ✅ 完成 CSS/JS 模組化分離
- ✅ 新增生產環境配置優化
- ✅ 新增系統優化分析工具
- ✅ Docker 容器化配置完善
- ✅ 多語言支援優化（國旗圖示）
- ✅ UI/UX 改進（Morandi 配色系統）
- ✅ 修復 CSS 相容性問題

### v1.0 (2025-07-22)
- 🎯 基礎魚類檢測功能
- 🌐 多語言支援框架
- 📊 日誌系統建立
- 🐳 Docker 基礎配置

## 📄 License

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 👥 作者

**NKUST CSIE** - 國立高雄科技大學 資訊工程系

- 📧 Email: contact@example.com
- 🌐 Website: https://github.com/fainstar/fish_0722
- 📱 Demo: http://your-demo-site.com

---

## ❓ 常見問題 (Q&A)

**Q1: 這個專案是做什麼的？**
A1: 這是一個基於 AI 深度學習的魚類檢測系統，支援圖片上傳並自動識別其中的魚類。

**Q2: 我該如何開始使用？**
A2: 推薦使用 Docker 部署，請參考「🐳 Docker 部署（推薦）」章節。若需本地開發，請遵循「💻 本地開發環境」的步驟。

**Q3: 專案支援哪些圖片格式？**
A3: 支援 `png`, `jpg`, `jpeg` 等常見圖片格式。

**Q4: 測試覆蓋率是多少？**
A4: 目前整體的測試覆蓋率為 48%，詳情請見「✅ 測試」章節。我們仍在持續增加測試案例以提高穩定性。

---

## 🙏 致謝

感謝以下開源專案的支援：
- [Flask](https://flask.palletsprojects.com/) - Web 應用框架
- [OpenCV](https://opencv.org/) - 電腦視覺函式庫
- [Bootstrap](https://getbootstrap.com/) - 前端框架
- [Docker](https://www.docker.com/) - 容器化平台

---

<div align="center">

**🌟 如果這個專案對您有幫助，請給一個 Star! 🌟**

Made with ❤️ by NKUST CSIE Team

</div>
