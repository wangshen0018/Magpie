#!/system/bin/sh
# CGI: 探测两个源站的连通状态，供页面状态条使用
# 出参: {"btsow":{"ok":true,"code":"200"},"tpb":{...},"t":时间戳}
#
# 两个探测并行执行，单个 8 秒超时，整体约 8 秒内返回（前端等 10 秒）。
# 串行的话最坏要 16 秒，前端早断了，状态条会一直是红的。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

BTSOW_URL='https://btsow.live/bts/data/api/search'
TPB_URL='https://apibay.org/q.php?q=inception&cat=0'

# 找一个可写的临时目录用于收集并行结果
TMP=""
for d in "$TMPDIR" /data/local/tmp /cache /tmp; do
  if [ -n "$d" ] && [ -d "$d" ] && [ -w "$d" ]; then
    TMP="$d"
    break
  fi
done

if [ -n "$TMP" ]; then
  F1="$TMP/.magpie_st_$$_1"
  F2="$TMP/.magpie_st_$$_2"

  "$CURL" -s -o /dev/null -w '%{http_code}' --max-time 8 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" > "$F1" 2>/dev/null &
  P1=$!

  "$CURL" -s -o /dev/null -w '%{http_code}' --max-time 8 -A "$UA" \
    "$TPB_URL" > "$F2" 2>/dev/null &
  P2=$!

  wait $P1
  wait $P2

  btsow_code=$(cat "$F1" 2>/dev/null)
  tpb_code=$(cat "$F2" 2>/dev/null)
  rm -f "$F1" "$F2"
else
  # 没有可写临时目录时退回串行，超时收短以控制总时长
  btsow_code=$("$CURL" -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" 2>/dev/null)
  tpb_code=$("$CURL" -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$TPB_URL" 2>/dev/null)
fi

btsow_ok='false'
tpb_ok='false'
[ "$btsow_code" = "200" ] && btsow_ok='true'
[ "$tpb_code" = "200" ] && tpb_ok='true'

echo "{\"btsow\":{\"ok\":$btsow_ok,\"code\":\"${btsow_code:-timeout}\"},\"tpb\":{\"ok\":$tpb_ok,\"code\":\"${tpb_code:-timeout}\"},\"t\":$(date +%s)}"
exit 0
