#!/system/bin/sh
# 代理首次部署：建目录、生成 sing-box 配置、自检
# 用法: sh scripts/proxy-setup.sh [sing-box路径] [目标目录]
#   默认 /data/adb/srv/bin/sing-box  /data/adb/srv/magpie-proxy
#   环境变量 MAGPIE_PROXY_PORT 改端口（默认 10808）
#
# 安全要点一：配置目录必须在 web 根之外。config.json 里有节点密钥，
#   放进 www/ 会被 busybox httpd 当静态文件直接下载走。
#
# 没有节点也能装：默认生成 direct 出站（纯透传），用来验证整条链路；
#   之后把完整配置写进 config.json 即可切到真实出站。

set -e
SB="${1:-/data/adb/srv/bin/sing-box}"
DIR="${2:-/data/adb/srv/magpie-proxy}"
PORT="${MAGPIE_PROXY_PORT:-10808}"
IDLE="${MAGPIE_PROXY_IDLE:-600}"
SRC=$(cd "$(dirname "$0")/.." && pwd)

[ -x "$SB" ] || { echo "not found sing-box: $SB"; exit 1; }

echo "sing-box: $SB"
echo "conf dir: $DIR"
mkdir -p "$DIR"
chmod 700 "$DIR"

# 端口与闲置秒数必须是纯数字，否则写进 JSON 会坏
case "$PORT" in *[!0-9]*) PORT=10808 ;; esac
case "$IDLE" in *[!0-9]*) IDLE=600 ;; esac

if [ -s "$DIR/config.json" ] && [ "$MAGPIE_KEEP" = "1" ]; then
  echo "keep existing $DIR/config.json"
else
  if [ -s "$DIR/config.json" ]; then
    mv "$DIR/config.json" "$DIR/config.json.prev"
    echo "old config saved as $DIR/config.json.prev"
  fi
  echo "write direct passthrough config (verify pipeline only, does not bypass blocking)"
  cat > "$DIR/config.json" <<EOF
{
  "log": { "level": "info", "timestamp": true, "output": "$DIR/sing-box.log" },
  "inbounds": [
    { "type": "mixed", "tag": "in", "listen": "127.0.0.1", "listen_port": $PORT }
  ],
  "outbounds": [
    { "type": "direct", "tag": "direct" }
  ]
}
EOF
fi
chmod 600 "$DIR/config.json"

# 闲置秒数落盘：proxy.cgi 与 watchdog.sh 都读这个文件。
# 不用环境变量传，busybox httpd 不保证把父 shell 的 env 带给 CGI。
echo "$IDLE" > "$DIR/idle"

cp "$SRC/scripts/watchdog.sh" "$DIR/watchdog.sh"
chmod 700 "$DIR/watchdog.sh"

echo off > "$DIR/state"
touch "$DIR/lastuse"
: > "$DIR/run.out"

echo "===== sing-box config check ====="
"$SB" check -c "$DIR/config.json"
echo "config ok"

echo ""
echo "done. proxy listens on 127.0.0.1:$PORT (loopback only, LAN cannot reach it)."
echo "auto-off after $IDLE s idle; edit $DIR/idle to change."
echo ""
echo "To use a real node: replace $DIR/config.json with a full sing-box config"
echo "(keep the mixed inbound on 127.0.0.1:$PORT, put your node in outbounds),"
echo "then run:  $SB check -c $DIR/config.json"