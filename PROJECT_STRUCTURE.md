# 🐟 魚類檢測系統 - 整理後的檔案結構

## 📁 目錄結構

```
fish_0722/
├── 📱 app.py                    # 主應用程式入口點
├── 📋 requirements.txt          # Python 依賴清單
├── 🔧 .gitignore               # Git 忽略檔案
│
├── 📁 src/                     # 原始碼目錄
│   ├── app_new.py              # 本地環境主應用
│   ├── app_docker.py           # Docker 環境主應用
│   ├── config.py               # 應用程式配置
│   ├── docker_config.py        # Docker 專用配置
│   ├── logger.py               # 日誌系統
│   ├── routes.py               # 路由處理
│   ├── translations_handler.py # 多語言處理
│   ├── fish_detector.py        # 魚類檢測核心
│   └── file_utils.py           # 檔案處理工具
│
├── 📁 docker/                  # Docker 相關檔案
│   ├── Dockerfile              # 開發環境容器
│   ├── Dockerfile.prod         # 生產環境容器
│   ├── docker-compose.yml      # 容器編排
│   ├── docker-compose.prod.yml # 生產環境編排
│   └── .dockerignore           # Docker 忽略檔案
│
├── 📁 scripts/                 # 腳本目錄
│   ├── docker-deploy.sh        # Docker 部署腳本
│   └── test_modules.py         # 模組測試腳本
│
├── 📁 docs/                    # 文檔目錄
│   ├── README.md               # 主要說明文檔
│   └── DOCKER_README.md        # Docker 部署指南
│
├── 📁 templates/               # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   └── logs.html
│
├── 📁 static/                  # 靜態資源
│   ├── css/
│   ├── js/
│   ├── uploads/                # 用戶上傳
│   └── processed/              # 處理結果
│
├── 📁 translations/            # 多語言檔案
│   ├── zh.json                 # 繁體中文
│   ├── en.json                 # 英文
│   └── ja.json                 # 日文
│
├── 📁 logs/                    # 日誌檔案
│   ├── fish_detection.log      # 應用程式日誌
│   └── user_activity.log       # 用戶活動日誌
│
└── 📁 data/                    # 資料目錄
    └── output1/                # 輸出檔案
```

## 🚀 快速開始

### 本地運行
```bash
# 安裝依賴
pip install -r requirements.txt

# 運行應用程式
python app.py
```

### Docker 部署
```bash
# 構建映像
./scripts/docker-deploy.sh build

# 運行容器
./scripts/docker-deploy.sh run

# 推送到 Docker Hub
./scripts/docker-deploy.sh push
```

## 📖 核心模組說明

### 🎯 應用程式入口
- `app.py` - 統一入口點，自動處理路徑問題
- `src/app_new.py` - 本地開發環境
- `src/app_docker.py` - Docker 容器環境

### ⚙️ 配置管理
- `src/config.py` - 本地環境配置
- `src/docker_config.py` - Docker 環境配置

### 🔧 核心功能
- `src/fish_detector.py` - AI 魚類檢測
- `src/logger.py` - 完整日誌系統
- `src/routes.py` - Web 路由處理
- `src/translations_handler.py` - 多語言支援
- `src/file_utils.py` - 檔案處理工具

## 🐳 Docker 使用

### 開發環境
```bash
cd docker
docker build -t fish-detection:dev -f Dockerfile ..
docker run -p 5001:5001 fish-detection:dev
```

### 生產環境
```bash
cd docker
docker build -t fish-detection:prod -f Dockerfile.prod ..
docker run -p 5001:5001 fish-detection:prod
```

### Docker Compose
```bash
cd docker
docker-compose up -d
```

## 📊 訪問地址

- **主應用程式**: http://localhost:5001
- **日誌查看**: http://localhost:5001/log
- **管理員介面**: http://localhost:5001/admin/logs?admin_key=your-password

## 🎉 整理完成的優勢

1. **清晰的目錄結構** - 按功能分類組織檔案
2. **模組化設計** - 核心代碼集中在 src/ 目錄
3. **Docker 支援** - 完整的容器化部署方案
4. **文檔齊全** - 詳細的使用說明和部署指南
5. **腳本自動化** - 簡化的部署和管理腳本

現在你的專案結構更加清晰且專業！ 🎯
