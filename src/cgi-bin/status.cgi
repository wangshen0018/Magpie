#!/system/bin/sh
# CGI: 探测两个磁力源站点的连通状态
printf 'Content-Type: application/json\r\n'
printf 'Access-Control-Allow-Origin: *\r\n'
printf 'Cache-Control: no-store\r\n'
printf '\r\n'

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36'

# 改为测搜索接口，但用温和词（避免被反爬）
btsow_code=$(/system/bin/curl -s -o /dev/null -w '%{http_code}' --max-time 1.5 \
  -A "$UA" -X POST -H 'Content-Type: application/json' \
  -d '[{"search":"inception"},1,1]' 'https://btsow.live/bts/data/api/search' 2>/dev/null)

tpb_code=$(/system/bin/curl -s -o /dev/null -w '%{http_code}' --max-time 1.5 \
  -A "$UA" 'https://apibay.org/q.php?q=inception&cat=0' 2>/dev/null)

btsow_ok='false'; tpb_ok='false'
[ "$btsow_code" = "200" ] && btsow_ok='true'
[ "$tpb_code" = "200" ] && tpb_ok='true'

echo "{\"btsow\":{\"ok\":$btsow_ok,\"code\":\"${btsow_code:-timeout}\"},\"tpb\":{\"ok\":$tpb_ok,\"code\":\"${tpb_code:-timeout}\"},\"t\":$(date +%s)}"
exit 0