#!/bin/bash

echo "============================================="
echo "🚀 PolyMusic 强制拉新部署脚本启动..."
echo "============================================="

echo "[1/4] 正在拉取 Github 最新代码..."
git pull origin master

echo "[2/4] 清理旧数据，防止新版数据格式兼容问题..."
rm -f data/polymusic.db
echo "数据库已重置！"

echo "[3/4] 停止并移除正在运行的旧容器..."
docker-compose down

echo "[4/4] 重新构建镜像并启动容器..."
docker-compose up -d --build

echo "============================================="
echo "✅ 部署完成！"
echo "你可以使用以下命令查看日志："
echo "   docker logs -f polymusic_app"
echo "============================================="
