#!/system/bin/sh
# CGI: 探测两个源站的连通状态，供页面状态条使用
# 出参: {"btsow":{"ok":true,"code":"200"},"tpb":{...},"t":时间戳}
#
# 三个探测并行执行，单个 5 秒超时，整体约 5~6 秒返回（前端等 10 秒，留足余量）。
# 超时给短是有意的：apibay 实测经常 28 秒以上，给 8 秒只是让总时长顶到前端上限，
# 结果反而更差（前端 10 秒等满、状态还可能拿不到）。5 秒不应答就当"未知"，符合事实。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

# 本地代理感知：探测必须和实际搜索走同一条路径，否则会出现
# "状态点是红的、但开着代理其实搜得到" 的误导（详见 search.cgi 注释）
for _l in /data/adb/srv/magnet/proxy-lib.sh /data/adb/magnet/proxy-lib.sh; do
  [ -f "$_l" ] && { . "$_l"; break; }
done

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

BTSOW_URL='https://btsow.live/bts/data/api/search'
# 不要带 cat=0：apibay 把它当真实分类，会稳定返回占位记录（见 search.cgi 说明）。
# 这里只看状态码，但用法保持一致，免得留下错误的参考样板。
TPB_URL='https://apibay.org/q.php?q=inception'
YTS_URL='https://yts.gg/api/v2/list_movies.json?query_term=inception&limit=1'

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
  F3="$TMP/.magpie_st_$$_3"

  "$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" > "$F1" 2>/dev/null &
  P1=$!

  "$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
    "$TPB_URL" > "$F2" 2>/dev/null &
  P2=$!

  "$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
    "$YTS_URL" > "$F3" 2>/dev/null &
  P3=$!

  wait $P1
  wait $P2
  wait $P3

  btsow_code=$(cat "$F1" 2>/dev/null)
  tpb_code=$(cat "$F2" 2>/dev/null)
  yts_code=$(cat "$F3" 2>/dev/null)
  rm -f "$F1" "$F2" "$F3"
else
  # 没有可写临时目录时退回串行，超时收短以控制总时长
  btsow_code=$("$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" 2>/dev/null)
  tpb_code=$("$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$TPB_URL" 2>/dev/null)
  yts_code=$("$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$YTS_URL" 2>/dev/null)
fi

btsow_ok='false'
tpb_ok='false'
yts_ok='false'
[ "$btsow_code" = "200" ] && btsow_ok='true'
[ "$tpb_code" = "200" ] && tpb_ok='true'
[ "$yts_code" = "200" ] && yts_ok='true'

# curl 连不上/超时都会输出 "000"，统一成 timeout，前端才能当成"未知"显示灰点。
# 否则 000 会走到非 200 分支被标成红点，实测 apibay 慢的时候必现误报。
[ "$btsow_code" = "000" ] && btsow_code=''
[ "$tpb_code" = "000" ] && tpb_code=''
[ "$yts_code" = "000" ] && yts_code=''

echo "{\"btsow\":{\"ok\":$btsow_ok,\"code\":\"${btsow_code:-timeout}\"},\"tpb\":{\"ok\":$tpb_ok,\"code\":\"${tpb_code:-timeout}\"},\"yts\":{\"ok\":$yts_ok,\"code\":\"${yts_code:-timeout}\"},\"t\":$(date +%s)}"
exit 0
