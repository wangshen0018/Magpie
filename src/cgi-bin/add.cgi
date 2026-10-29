#!/system/bin/sh
# CGI: 把磁力推给本机 aria2 RPC（密钥服务端读取，不进前端）
printf 'Content-Type: application/json\r\n'
printf 'Access-Control-Allow-Origin: *\r\n'
printf 'Cache-Control: no-store\r\n'
printf '\r\n'

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

SECRET=$(sed -n 's/^rpc-secret=//p' /data/adb/srv/aria2.conf | tr -d '\r\n')

/system/bin/curl -s --max-time 15 \
  -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"id\":\"magnet\",\"method\":\"aria2.addUri\",\"params\":[\"token:${SECRET}\",[\"magnet:?xt=urn:btih:${h}\"]]}" \
  http://127.0.0.1:6800/jsonrpc 2>/dev/null

echo ""
exit 0
