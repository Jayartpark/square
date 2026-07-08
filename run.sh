#!/bin/bash

# VisionCraft 一键启动脚本
# 用法: ./run.sh [port]

PORT=${1:-8000}
HOST="0.0.0.0"

echo "🚀 正在启动 VisionCraft..."
echo "----------------------------------------"

# 1. 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 2. 检查并安装依赖
if [ ! -f "requirements.txt" ]; then
    echo "⚠️ 警告: 未找到 requirements.txt，跳过依赖安装"
else
    echo "📦 检查依赖..."
    pip3 install -q -r requirements.txt
    echo "✅ 依赖检查完成"
fi

# 3. 启动服务
echo "----------------------------------------"
echo "🌐 服务地址: http://localhost:$PORT"
echo "📚 API 文档: http://localhost:$PORT/docs"
echo "----------------------------------------"
echo "按 Ctrl+C 停止服务"
echo ""

cd backend
python3 -m uvicorn main:app --host $HOST --port $PORT --reload
