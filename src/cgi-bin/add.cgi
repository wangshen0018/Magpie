#!/system/bin/sh
# CGI: 把磁力推给本机 aria2 RPC
# 入参: h=info_hash（32 或 40 位十六进制）
# 出参: aria2 的原始 JSONRPC 响应；参数不合法时返回 {"error":"..."}
#
# rpc-secret / 端口都从 aria2 配置文件里读，不进前端页面（见 lib/aria2.sh）。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

SELF_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
if [ -f "$SELF_DIR/../../lib/aria2.sh" ]; then
  . "$SELF_DIR/../../lib/aria2.sh"
else
  echo '{"error":"lib/aria2.sh not found, redeploy needed"}'
  exit 0
fi

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

OUT=$(aria2_rpc "aria2.addUri" "[[\"magnet:?xt=urn:btih:${h}\"]]")

if [ -z "$OUT" ]; then
  if [ -z "$MG_CONF" ]; then
    echo '{"error":"aria2 config not found"}'
  else
    echo "{\"error\":\"aria2 rpc no response on port ${MG_PORT}\"}"
  fi
  exit 0
fi

# curl 在某些网络环境下会吐出非 JSON 的错误文本，不能直接透传给前端
if is_json_object "$OUT"; then
  printf '%s' "$OUT"
else
  echo '{"error":"aria2 rpc failed, check rpc port and aria2 service"}'
fi

exit 0
