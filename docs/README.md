# 🐟 魚類檢測系統 (Fish Detection System)

一個基於 AI 的魚類檢測和分析系統，支援多語言介面和完整的用戶活動記錄功能。

## 📋 功能特色

### 🔍 AI 魚類檢測
- 使用 Roboflow API 進行準確的魚類檢測
- 支援批量圖片處理
- 自動標註檢測結果
- 支援多種圖片格式 (JPG, JPEG, PNG)

### 🌐 多語言支援
- 支援繁體中文、英文、日文介面
- 動態語言切換
- 完整的國際化支援

### 📊 完整記錄系統
- 用戶操作記錄
- 設備資訊追蹤 (瀏覽器、作業系統、裝置類型)
- IP 地址記錄
- 檔案上傳歷史
- 管理員日誌查看介面

### 📁 檔案管理
- 自動檔案清理
- 處理結果保存
- 檔案大小限制
- 安全檔案驗證

## 🏗️ 系統架構

### 模組化設計
系統採用模組化架構，便於維護和擴展：

```
fish_0722/
├── app_new.py              # 主應用程式
├── config.py               # 配置管理
├── logger.py               # 日誌系統
├── translations_handler.py # 翻譯處理
├── fish_detector.py        # 魚類檢測模組
├── file_utils.py          # 檔案工具
├── routes.py              # 路由管理
├── templates/             # HTML 模板
├── static/               # 靜態資源
├── data/                 # 資料目錄
└── translations/         # 翻譯檔案
```

### 核心模組說明

#### 🔧 config.py
- 集中管理所有配置參數
- API 金鑰配置
- 檔案上傳限制
- 語言設定

#### 📝 logger.py
- 用戶活動追蹤
- 設備資訊檢測
- 日誌輪替管理
- 統計資料分析

#### 🌍 translations_handler.py
- 多語言支援
- 動態語言切換
- 模板上下文注入

#### 🤖 fish_detector.py
- AI 檢測核心
- Roboflow API 整合
- 圖片處理和標註

## 🚀 安裝和設定

### 系統需求
```bash
Python 3.8+
Flask 2.0+
```

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd fish_0722
```

2. **安裝相依套件**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
在 `config.py` 中設定：
```python
ROBOFLOW_API_KEY = "your-api-key-here"
SECRET_KEY = "your-secret-key"
ADMIN_PASSWORD = "your-admin-password"
```

4. **創建必要目錄**
```bash
mkdir -p static/uploads
mkdir -p static/processed
mkdir -p data/output1
mkdir -p logs
```

5. **啟動應用程式**
```bash
python app_new.py
```

應用程式將在 `http://127.0.0.1:5001` 啟動

## 📖 使用指南

### 基本使用流程

1. **上傳圖片**
   - 訪問主頁 `http://127.0.0.1:5001`
   - 選擇要檢測的魚類圖片
   - 點擊上傳按鈕

2. **查看結果**
   - 系統自動進行 AI 檢測
   - 顯示標註後的圖片
   - 提供檢測統計資訊

3. **語言切換**
   - 使用頁面上的語言選擇器
   - 支援即時切換語言

### 管理功能

#### 查看日誌
- **一般用戶**: `http://127.0.0.1:5001/log`
- **管理員**: `http://127.0.0.1:5001/admin/logs`

#### 系統統計
管理員介面提供：
- 用戶活動統計
- 檔案處理記錄
- 系統使用情況
- 錯誤日誌分析

## 🔧 配置說明

### 主要配置參數

```python
# 語言設定
LANGUAGES = {
    'zh': '繁體中文',
    'en': 'English', 
    'ja': '日本語'
}

# 檔案上傳限制
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# API 設定
ROBOFLOW_API_KEY = "your-roboflow-api-key"
ROBOFLOW_MODEL_URL = "your-model-endpoint"

# 日誌設定
LOG_FILE = 'logs/fish_detection.log'
USER_ACTIVITY_LOG = 'logs/user_activity.log'
```

### 翻譯檔案
在 `translations/` 目錄下：
- `zh.json`: 繁體中文翻譯
- `en.json`: 英文翻譯
- `ja.json`: 日文翻譯

## 🛠️ 開發指南

### 新增功能模組

1. **創建新模組檔案**
```python
# new_module.py
from config import config
from logger import log_user_activity

def new_function():
    # 實作新功能
    pass
```

2. **在路由中註冊**
```python
# routes.py
from new_module import new_function

@app.route('/new-endpoint')
def new_route():
    return new_function()
```

### 新增翻譯

1. **在翻譯檔案中加入新的鍵值**
```json
{
  "new_text": "新的文字內容"
}
```

2. **在模板中使用**
```html
{{ get_text('new_text') }}
```

### 測試模組

執行測試腳本驗證系統：
```bash
python test_modules.py
```

## 📊 系統監控

### 日誌系統
- **應用程式日誌**: 記錄系統運行狀況
- **用戶活動日誌**: 追蹤用戶操作
- **錯誤日誌**: 記錄系統錯誤

### 效能監控
- 檔案處理時間記錄
- API 回應時間追蹤
- 系統資源使用情況

## 🔒 安全性

### 檔案安全
- 檔案類型驗證
- 檔案大小限制
- 惡意檔案檢查

### 用戶隱私
- IP 地址記錄加密
- 用戶資料匿名化
- 自動資料清理

## 🐛 疑難排解

### 常見問題

**Q: 無法上傳檔案**
A: 檢查檔案格式是否支援，確認檔案大小未超過限制

**Q: API 檢測失敗**
A: 確認 Roboflow API 金鑰是否正確設定

**Q: 語言切換無效**
A: 檢查翻譯檔案是否存在且格式正確

**Q: 日誌無法查看**
A: 確認日誌檔案權限和路徑設定

### 除錯模式
啟用除錯模式：
```python
app.run(debug=True, host='127.0.0.1', port=5001)
```

## 📝 更新日誌

### v2.0.0 (2024-07-24)
- ✨ 實作模組化架構重構
- ✨ 新增完整的用戶活動記錄系統
- ✨ 新增管理員日誌查看介面
- ✅ 優化檔案處理效能
- 🐛 修復多語言切換問題

### v1.0.0 (2024-07-22)
- 🎉 初版發布
- ✨ 基礎魚類檢測功能
- ✨ 多語言支援
- ✨ 檔案上傳處理

## 👥 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 授權

此專案採用 MIT 授權條款。

## 📞 聯絡資訊

如有問題或建議，請聯繫開發團隊。

---

**🚀 感謝使用魚類檢測系統！**
