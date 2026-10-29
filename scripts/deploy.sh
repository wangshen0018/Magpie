#!/bin/bash
# 磁力搜索一键部署脚本
# 用法: ./deploy.sh [target_dir]

set -e

TARGET_DIR=${1:-/data/adb/srv/magnet}
echo "部署到: $TARGET_DIR"

# 创建目录结构
mkdir -p $TARGET_DIR/www
mkdir -p $TARGET_DIR/www/cgi-bin

# 复制文件
cp src/index.html $TARGET_DIR/www/
cp src/cgi-bin/*.cgi $TARGET_DIR/www/cgi-bin/
chmod +x $TARGET_DIR/www/cgi-bin/*.cgi

# 启动服务（如果使用 busybox httpd）
echo "手动启动服务："
echo "busybox httpd -p 8080 -h $TARGET_DIR/www -c $TARGET_DIR/www/httpd.conf"

echo "部署完成！"
