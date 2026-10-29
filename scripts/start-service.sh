#!/system/bin/sh
# 启动服务：sh scripts/start-service.sh [端口] [部署目录]
# 默认端口 8080，默认部署目录 /data/adb/srv/magnet
#
# 前置条件：已运行过 scripts/deploy.sh（httpd.conf 由 deploy.sh 复制过去）

PORT=${1:-8080}
TARGET=${2:-/data/adb/srv/magnet}
WWW="$TARGET/www"
CONF="$WWW/httpd.conf"

# 找 busybox：优先 PATH，其次 Magisk / 系统常见位置
BB=""
for p in "$(command -v busybox 2>/dev/null)" \
         /data/adb/magisk/busybox \
         /data/adb/ksu/bin/busybox \
         /system/xbin/busybox \
         /system/bin/busybox; do
  if [ -n "$p" ] && [ -x "$p" ]; then
    BB="$p"
    break
  fi
done

if [ -z "$BB" ]; then
  echo "未找到 busybox。请先安装 busybox（Magisk 模块或系统自带）。"
  exit 1
fi

if [ ! -f "$CONF" ]; then
  echo "缺少配置文件: $CONF"
  echo "请先运行: sh scripts/deploy.sh $TARGET"
  exit 1
fi

# 端口占用检查（有 netstat 才查，没有就跳过）
if command -v netstat >/dev/null 2>&1; then
  if netstat -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "端口 $PORT 已被占用，换一个端口或先停掉已有服务。"
    exit 1
  fi
fi

echo "busybox: $BB"
echo "端口:    $PORT"
echo "目录:    $WWW"
echo "配置:    $CONF"

"$BB" httpd -p "$PORT" -h "$WWW" -c "$CONF" -t 60
RC=$?

if [ "$RC" -ne 0 ]; then
  echo "启动失败（退出码 $RC）。"
  exit "$RC"
fi

echo "已启动，访问 http://本机IP:$PORT/"
echo "停止：pkill -f 'httpd -p $PORT'"
