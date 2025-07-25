# 使用 Python 3.9 作為基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變量
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=src/app_docker.py \
    FLASK_ENV=production \
    DOCKER_CONTAINER=true \
    PYTHONPATH=/app  

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序代碼
COPY . .

# 創建必要的目錄
RUN mkdir -p logs static/uploads static/processed data/output1

# 設置權限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 5001

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# 啟動命令
CMD ["python", "src/app_docker.py"]
