#!/system/bin/sh
# 部署脚本：把 src/ 下的页面与 CGI 复制到目标目录
# 用法：sh scripts/deploy.sh [目标目录]
# 默认目标目录：/data/adb/srv/magnet
#
# 说明：脚本用自身位置推算仓库根目录，所以在任何目录下执行都可以。

set -e

TARGET=${1:-/data/adb/srv/magnet}
WWW="$TARGET/www"
SRC=$(cd "$(dirname "$0")/.." && pwd)

echo "源目录: $SRC"
echo "目标目录: $TARGET"

mkdir -p "$WWW/cgi-bin"

cp "$SRC/src/index.html" "$WWW/index.html"
cp "$SRC"/src/cgi-bin/*.cgi "$WWW/cgi-bin/"
cp "$SRC/static/httpd.conf" "$WWW/httpd.conf"

# 开机自启（/data/adb/service.d/srv.sh）读的是 TARGET 根目录那份 httpd.conf，
# 而 start-service.sh 读的是 www 下那份。两份都写，避免以后只改一边导致行为不一致。
cp "$SRC/static/httpd.conf" "$TARGET/httpd.conf" 2>/dev/null || true

chmod 755 "$WWW/cgi-bin/"*.cgi
chmod 644 "$WWW/index.html" "$WWW/httpd.conf"

# 部署后自检：少一个文件就报错，避免出现"启动后 404 或读不到配置"
MISS=0
for f in index.html httpd.conf cgi-bin/search.cgi cgi-bin/btsow.cgi cgi-bin/add.cgi cgi-bin/status.cgi; do
  if [ ! -f "$WWW/$f" ]; then
    echo "缺失: $WWW/$f"
    MISS=1
  fi
done

if [ "$MISS" -ne 0 ]; then
  echo "部署未完成，请检查上面的缺失项"
  exit 1
fi

echo "文件检查通过"

cat <<EOF

部署完成，启动服务：

  sh $SRC/scripts/start-service.sh 8080 $TARGET

手动启动（等价）：

  busybox httpd -p 8080 -h $WWW -c $WWW/httpd.conf

EOF
