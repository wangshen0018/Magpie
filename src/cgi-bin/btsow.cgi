#!/system/bin/sh
# CGI: btsow 搜索代理（原样转发 JSON，字段解析交给前端）
# 前端以 POST 原文发送 UTF-8 关键词
printf 'Content-Type: application/json\r\n'
printf 'Access-Control-Allow-Origin: *\r\n'
printf 'Cache-Control: no-store\r\n'
printf '\r\n'

Q=$(cat)
Q=$(printf '%s' "$Q" | tr -d '\r\n')
Q=$(printf '%s' "$Q" | sed 's/\\/\\\\/g; s/"/\\"/g')

if [ -z "$Q" ]; then
  echo '{"code":200,"data":[]}'
  exit 0
fi

/system/bin/curl -s --max-time 20 \
  -A 'Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Referer: https://btsow.live/' \
  -d "[{\"search\":\"${Q}\"},30,1]" \
  'https://btsow.live/bts/data/api/search' 2>/dev/null

echo ""
exit 0