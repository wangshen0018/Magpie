#!/system/bin/sh
# CGI: 把磁力推给本机 aria2 RPC
# 入参: h=info_hash（32 或 40 位十六进制）
# 出参: aria2 的原始 JSONRPC 响应；参数不合法时返回 {"error":"..."}
#
# rpc-secret / 端口都从 aria2 配置文件里读，不进前端页面。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

h="${QUERY_STRING}"
case "$h" in
  h=*) h="${h#h=}" ;;
  *)   h="" ;;
esac
h="${h%%&*}"

if [ -z "$h" ]; then
  echo '{"error":"missing hash"}'
  exit 0
fi

# 只接受十六进制，长度 32 或 40，其余一律拒绝
case "$h" in
  *[!0-9a-fA-F]*)
    echo '{"error":"bad hash"}'
    exit 0
    ;;
esac

HLEN=${#h}
if [ "$HLEN" -ne 32 ] && [ "$HLEN" -ne 40 ]; then
  echo '{"error":"bad hash length"}'
  exit 0
fi

# 找 aria2 配置文件：优先 ARIA2_CONF 环境变量，其次常见路径
# 都找不到时按默认端口 6800、无密钥去试，能连上就当成功（有人不写配置文件）
CONF=""
for c in "$ARIA2_CONF" \
         /data/adb/srv/aria2.conf \
         /data/adb/aria2/aria2.conf \
         /data/adb/modules/aria2/aria2.conf \
         /sdcard/aria2/aria2.conf \
         "$HOME/.aria2/aria2.conf"; do
  if [ -n "$c" ] && [ -f "$c" ]; then
    CONF="$c"
    break
  fi
done

SECRET=""
PORT="6800"

if [ -n "$CONF" ]; then
  SECRET=$(sed -n 's/^[[:space:]]*rpc-secret[[:space:]]*=[[:space:]]*//p' "$CONF" | tr -d '\r\n')
  P=$(sed -n 's/^[[:space:]]*rpc-listen-port[[:space:]]*=[[:space:]]*//p' "$CONF" | tr -d '\r\n')
  [ -n "$P" ] && PORT="$P"
fi

MAGNET="magnet:?xt=urn:btih:${h}"

# 没配 secret 时不能带 "token:" 前缀，否则 aria2 直接鉴权失败
if [ -n "$SECRET" ]; then
  PARAMS="[\"token:${SECRET}\",[\"${MAGNET}\"]]"
else
  PARAMS="[[\"${MAGNET}\"]]"
fi

OUT=$("$CURL" -s --max-time 15 \
  -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"id\":\"magpie\",\"method\":\"aria2.addUri\",\"params\":${PARAMS}}" \
  "http://127.0.0.1:${PORT}/jsonrpc" 2>/dev/null)

if [ -z "$OUT" ]; then
  if [ -z "$CONF" ]; then
    echo '{"error":"aria2 config not found"}'
  else
    echo "{\"error\":\"aria2 rpc no response on port ${PORT}\"}"
  fi
  exit 0
fi

# curl 在某些网络环境下会吐出非 JSON 的错误文本，不能直接透传给前端
case "$OUT" in
  \{*) printf '%s' "$OUT" ;;
  *)   echo '{"error":"aria2 rpc failed, check rpc port and aria2 service"}' ;;
esac

exit 0
