# 🐳 魚類檢測系統 Docker 部署指南

這是魚類檢測系統的 Docker 容器化版本，提供完整的部署和管理解決方案。

## 📋 系統需求

- Docker Engine 20.10.0+
- Docker Compose 2.0.0+
- 至少 2GB 可用記憶體
- 至少 5GB 可用磁碟空間

## 🚀 快速開始

### 1. 克隆專案（如果尚未完成）
```bash
git clone <repository-url>
cd fish_0722
```

### 2. 環境變數設定（可選）
創建 `.env` 文件來自訂配置：
```bash
# 管理員設定
ADMIN_PASSWORD=your-secure-admin-password

# 其他設定
SECRET_KEY=your-secret-key
PORT=5001
```

### 3. 使用部署腳本（推薦）
```bash
# 構建並啟動服務
./scripts/docker-deploy.sh build
./scripts/docker-deploy.sh run
```

### 4. 手動部署（替代方案）
```bash
# 構建 Docker 映像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看狀態
docker-compose ps
```

## 🎯 訪問應用程式

服務啟動後，可以通過以下地址訪問：

- **主應用程式**: http://localhost:5001
- **日誌查看**: http://localhost:5001/log
- **管理員介面**: http://localhost:5001/admin/logs?admin_key=fish_admin_2024

## 🛠️ 管理命令

### 使用部署腳本管理服務

```bash
# 構建映像
./scripts/docker-deploy.sh build

# 運行容器
./scripts/docker-deploy.sh run

# 推送映像
./scripts/docker-deploy.sh push

# 停止服務
./scripts/docker-deploy.sh stop

# 查看日誌
./scripts/docker-deploy.sh logs
```

### 使用 Docker Compose 管理

```bash
# 啟動服務
docker-compose up -d

# 停止服務
docker-compose down

# 查看日誌
docker-compose logs -f

# 重啟特定服務
docker-compose restart fish-detection

# 查看運行狀態
docker-compose ps

# 進入容器
docker-compose exec fish-detection bash
```

## 📁 數據持久化

系統自動將以下目錄掛載到主機，確保數據持久化：

- `./logs` - 系統日誌文件
- `./static/uploads` - 用戶上傳的圖片
- `./static/processed` - 處理後的圖片
- `./data` - 其他數據文件

## 🔧 配置說明

### Docker 環境變量

| 變量名 | 默認值 | 說明 |
|--------|--------|------|

| `ADMIN_PASSWORD` | `fish_admin_2024` | 管理員密碼 |
| `SECRET_KEY` | `docker-fish-detection-2024-secure-key` | Flask 密鑰 |
| `PORT` | `5001` | 應用程式端口 |

### 自訂配置

1. **修改端口映射**：
   編輯 `docker-compose.yml` 中的 `ports` 設定
   ```yaml
   ports:
     - "8080:5001"  # 將應用程式映射到主機 8080 端口
   ```

2. **調整資源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

3. **添加環境變量**：
   ```yaml
   environment:
     - CUSTOM_VAR=custom_value
   ```

## 📊 監控和日誌

### 查看容器狀態
```bash
docker-compose ps
docker stats fish-detection-system
```

### 查看應用程式日誌
```bash
# 實時日誌
docker-compose logs -f fish-detection

# 最近 100 行日誌
docker-compose logs --tail=100 fish-detection
```

### 訪問內部日誌文件
```bash
# 進入容器
docker-compose exec fish-detection bash

# 查看日誌文件
tail -f /app/logs/fish_detection.log
tail -f /app/logs/user_activity.log
```

## 🔒 安全考量

1. **修改默認密碼**：
   ```bash
   # 設置環境變量
   export ADMIN_PASSWORD=your-secure-password
   ```

2. **使用 HTTPS**：
   建議在生產環境中使用反向代理（如 Nginx）提供 HTTPS

3. **網路安全**：
   ```yaml
   # 限制容器網路訪問
   networks:
     fish-detection-network:
       driver: bridge
       internal: true  # 限制外部訪問
   ```

## 🚨 故障排除

### 常見問題

1. **容器無法啟動**
   ```bash
   # 查看詳細錯誤
   docker-compose logs fish-detection
   
   # 檢查映像是否構建成功
   docker images | grep fish
   ```

2. **端口衝突**
   ```bash
   # 檢查端口使用情況
   lsof -i :5001
   
   # 修改端口映射
   # 編輯 docker-compose.yml 中的 ports 設定
   ```

3. **權限問題**
   ```bash
   # 修復目錄權限
   sudo chown -R $(whoami):$(whoami) logs static data
   ```

4. **記憶體不足**
   ```bash
   # 檢查系統資源
   docker system df
   docker system prune  # 清理未使用的資源
   ```

### 除錯模式

啟用除錯模式來獲取更多信息：
```bash
# 修改 docker-compose.yml
environment:
  - FLASK_ENV=development
  - FLASK_DEBUG=1
```

## 📈 效能優化

1. **映像大小優化**：
   - 使用多階段構建
   - 清理不必要的文件

2. **運行時優化**：
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
       reservations:
         memory: 512M
   ```

3. **日誌輪替**：
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "100m"
       max-file: "3"
   ```

## 🔄 更新和維護

### 更新和維護

### 更新應用程式
```bash
# 停止服務
./scripts/docker-deploy.sh stop

# 拉取最新代碼
git pull

# 重新構建並啟動
./scripts/docker-deploy.sh build
./scripts/docker-deploy.sh run
```

## 📞 支援

如遇到問題，請：

1. 查看日誌文件確認錯誤信息
2. 檢查 GitHub Issues
3. 聯繫開發團隊

---

**🎉 享受使用 Docker 版本的魚類檢測系統！**
