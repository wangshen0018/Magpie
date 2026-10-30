#!/system/bin/sh
# 部署脚本：把 src/ 下的页面与 CGI 复制到目标目录
# 用法：sh scripts/deploy.sh [目标目录]
# 默认目标目录：/data/adb/srv/magnet
#
# 说明：脚本用自身位置推算仓库根目录，所以在任何目录下执行都可以。

set -e

TARGET=${1:-/data/adb/srv/magnet}
WWW="$TARGET/www"
LIB="$TARGET/lib"
SRC=$(cd "$(dirname "$0")/.." && pwd)

echo "源目录: $SRC"
echo "目标目录: $TARGET"

mkdir -p "$WWW/cgi-bin" "$LIB"

cp "$SRC/src/index.html" "$WWW/index.html"
cp "$SRC"/src/cgi-bin/*.cgi "$WWW/cgi-bin/"
cp "$SRC/static/httpd.conf" "$WWW/httpd.conf"

# aria2 配置读取的公共库。故意放在 www 之外：httpd 的根目录是 www，
# 放里面就能被浏览器当静态文件直接下载走源码。
cp "$SRC/src/lib/aria2.sh" "$LIB/aria2.sh"

# 代理判断库同样放在 web 根之外：www/ 里的 .sh 会被 httpd 当静态文件原样下载。
# （.cgi 有 *.cgi 映射会被执行，.sh 没有，等于源码泄露。）
cp "$SRC/scripts/proxy-lib.sh" "$TARGET/proxy-lib.sh" 2>/dev/null || true
chmod 644 "$TARGET/proxy-lib.sh" 2>/dev/null || true

# 开机自启（/data/adb/service.d/srv.sh）读的是 TARGET 根目录那份 httpd.conf，
# 而 start-service.sh 读的是 www 下那份。两份都写，避免以后只改一边导致行为不一致。
cp "$SRC/static/httpd.conf" "$TARGET/httpd.conf" 2>/dev/null || true

chmod 755 "$WWW/cgi-bin/"*.cgi
chmod 644 "$WWW/index.html" "$WWW/httpd.conf" "$LIB/aria2.sh"

# 部署后自检：少一个文件就报错，避免出现"启动后 404 或读不到配置"
MISS=0
for f in index.html httpd.conf cgi-bin/search.cgi cgi-bin/btsow.cgi cgi-bin/yts.cgi cgi-bin/nyaa.cgi cgi-bin/tkitty.cgi cgi-bin/proxy.cgi cgi-bin/add.cgi cgi-bin/list.cgi cgi-bin/status.cgi; do
  if [ ! -f "$WWW/$f" ]; then
    echo "缺失: $WWW/$f"
    MISS=1
  fi
done
if [ ! -f "$LIB/aria2.sh" ]; then
  echo "缺失: $LIB/aria2.sh"
  MISS=1
fi
[ -f "$TARGET/proxy-lib.sh" ] || { echo "缺失: $TARGET/proxy-lib.sh"; MISS=1; }

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
