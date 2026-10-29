#!/system/bin/sh
# CGI: 搜索 apibay，输出 JSON
printf 'Content-Type: application/json\r\n'
printf 'Access-Control-Allow-Origin: *\r\n'
printf 'Cache-Control: no-store\r\n'
printf '\r\n'

q="${QUERY_STRING}"
case "$q" in
  q=*) q="${q#q=}" ;;
  *)   q="" ;;
esac

if [ -z "$q" ]; then
  echo '[]'
  exit 0
fi

# 去掉可能出现的额外参数，只保留 q
q="${q%%&*}"

/system/bin/curl -s --max-time 12 \
  -A 'Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36' \
  "https://apibay.org/q.php?q=${q}&cat=0" 2>/dev/null

exit 0
