#!/bin/bash
# 启动磁力搜索服务

set -e

# 配置
PORT=${1:-8080}
TARGET_DIR=${2:-/data/adb/srv/magnet}
HTTPD_BIN="/data/adb/magisk/busybox"

# 检查依赖
echo "检查依赖..."
if [ ! -f "$HTTPD_BIN" ]; then
    echo "错误: busybox 未找到在 $HTTPD_BIN"
    echo "请确保 busybox 已安装"
    exit 1
fi

if [ ! -d "$TARGET_DIR/www" ]; then
    echo "错误: 目标目录不存在: $TARGET_DIR/www"
    echo "请先运行: ./scripts/deploy.sh $TARGET_DIR"
    exit 1
fi

# 检查端口
if netstat -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "警告: 端口 $PORT 已被占用"
    echo "请更换端口或停止现有服务"
    exit 1
fi

# 创建配置文件
HTTPD_CONF="$TARGET_DIR/www/httpd.conf"
cat > "$HTTPD_CONF" << 'EOF'
# busybox httpd 配置
*.cgi:/system/bin/sh
DirectoryIndex index.html
Timeout 30
MaxClients 10
KeepAlive off
EOF

echo "启动服务..."
echo "端口: $PORT"
echo "目录: $TARGET_DIR/www"
echo "配置: $HTTPD_CONF"

# 启动服务
"$HTTPD_BIN" httpd -p "$PORT" -h "$TARGET_DIR/www" -c "$HTTPD_CONF" &

# 等待服务启动
sleep 2

# 检查服务状态
if ps | grep -q "httpd -p $PORT"; then
    echo "✓ 服务启动成功"
    echo "访问: http://localhost:$PORT/"
    echo "PID: $!"
else
    echo "✗ 服务启动失败"
    exit 1
fi

# 保存 PID
echo "$!" > "$TARGET_DIR/www/httpd.pid"

echo ""
echo "停止服务: kill \$(cat $TARGET_DIR/www/httpd.pid)"
echo "查看日志: tail -f /var/log/httpd*.log"