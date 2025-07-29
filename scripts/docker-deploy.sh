#!/bin/bash

# 魚類檢測系統 Docker 簡化部署腳本

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 主程序
case "${1:-help}" in
    "build")
        print_info "構建 Docker 映像..."
        docker build -t fish-detection:latest -f docker/Dockerfile .
        print_success "映像構建完成"
        ;;
    "build-prod")
        print_info "構建生產環境 Docker 映像..."
        docker build -t fish-detection:prod -f docker/Dockerfile.prod .
        print_success "生產環境映像構建完成"
        ;;
    "run")
        print_info "運行 Docker 容器..."
        docker run -d -p 5003:5003 --name fish-detection-system fish-detection:latest
        print_success "容器已啟動，訪問: http://localhost:5003"
        ;;
    "stop")
        print_info "停止容器..."
        docker stop fish-detection-system && docker rm fish-detection-system
        print_success "容器已停止"
        ;;
    "push")
        echo "請輸入 Docker Hub 用戶名："
        read username
        docker tag fish-detection:latest $username/fish-detection:latest
        docker push $username/fish-detection:latest
        print_success "映像已推送到 Docker Hub"
        ;;
    "help"|*)
        echo "使用方法: $0 [選項]"
        echo ""
        echo "選項:"
        echo "  build      構建開發環境映像"
        echo "  build-prod 構建生產環境映像"
        echo "  run        運行容器"
        echo "  stop       停止容器"
        echo "  push       推送到 Docker Hub"
        echo "  help       顯示此幫助"
        ;;
esac
