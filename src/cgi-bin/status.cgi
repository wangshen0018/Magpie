#!/system/bin/sh
# CGI: 探测三个源站的连通状态，供页面状态条使用
# 出参: {"btsow":{"ok":bool,"code":"200|timeout|..."},"tpb":{...},"yts":{...},"t":时间戳}
#
# 语义很重要：状态点表达的是「用户此刻能不能从这一源搜到结果」，
# 不是「代理这条路通不通」。所以代理开着时，apibay / YTS 会同时探代理和
# 直连两条路，任一 200 就算通——否则会出现「点显示红的、但其实搜得到」的
# 自相矛盾（实测踩过：节点死光时搜索自动退回直连能出结果，状态点却报红）。
# btsow 永远直连，因为 btsow.cgi 本身就不注入代理。
#
# 三个源并行探测，单个 5 秒超时，整体约 5~6 秒（前端等 10 秒）。
# 5 秒不应答就当"未知"（灰点）：apibay 实测经常 28 秒以上不返回，
# 等更久只会顶到前端上限、状态反而更差。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

# 代理感知库：决定 $PROXY_OPT 是否有值（开关 on + 配置有真实节点才注入）
for _l in /data/adb/srv/magnet/proxy-lib.sh /data/adb/magnet/proxy-lib.sh; do
  [ -f "$_l" ] && { . "$_l"; break; }
done

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

BTSOW_URL='https://btsow.live/bts/data/api/search'
# 不要带 cat=0：apibay 把它当真实分类，会稳定返回占位记录（见 search.cgi）
TPB_URL='https://apibay.org/q.php?q=inception'
YTS_URL='https://yts.gg/api/v2/list_movies.json?query_term=inception&limit=1'
# Nyaa 只在代理下可用（直连实测 12 秒超时），所以它只探代理那条路；
# 代理没开时它必然是灰的，这是事实，不该谎报绿点。
NYAA_URL='https://nyaa.si/?q=naruto&c=0_0&f=0'

# 找一个可写的临时目录用于收集并行结果
TMP=""
for d in "$TMPDIR" /data/local/tmp /cache /tmp; do
  if [ -n "$d" ] && [ -d "$d" ] && [ -w "$d" ]; then
    TMP="$d"
    break
  fi
done

btsow_code=""
tpb_code=""
yts_code=""

if [ -n "$TMP" ]; then
  B="$TMP/.magpie_st_$$"

  # btsow：只探直连（与 btsow.cgi 的实际行为一致）
  "$CURL" -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" > "$B.1" 2>/dev/null &

  if [ -n "$PROXY_OPT" ]; then
    # 代理开着：两条路都探（.2p/.3p 走代理，.2d/.3d 直连）
    "$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$TPB_URL" > "$B.2p" 2>/dev/null &
    "$CURL" -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$TPB_URL" > "$B.2d" 2>/dev/null &
    "$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$YTS_URL" > "$B.3p" 2>/dev/null &
    "$CURL" -sL -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$YTS_URL" > "$B.3d" 2>/dev/null &
    # Nyaa 只探代理：它直连必死，探直连只会白等 5 秒
    "$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 6 -A "$UA" \
      "$NYAA_URL" > "$B.4" 2>/dev/null &
  else
    "$CURL" -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$TPB_URL" > "$B.2d" 2>/dev/null &
    "$CURL" -sL -o /dev/null -w '%{http_code}' --max-time 5 -A "$UA" \
      "$YTS_URL" > "$B.3d" 2>/dev/null &
    # 代理没开：Nyaa 直接标灰，不去探（探了也是 12 秒超时，白占 5 秒预算）
    echo "000" > "$B.4" 2>/dev/null &
  fi

  wait

  btsow_code=$(cat "$B.1" 2>/dev/null)
  tpb_code=$(cat "$B.2d" 2>/dev/null)
  yts_code=$(cat "$B.3d" 2>/dev/null)
  nyaa_code=$(cat "$B.4" 2>/dev/null)
  # 代理那条路只要也拿到 200，就覆盖成 200（任一通即算通）
  if [ -n "$PROXY_OPT" ]; then
    [ "$(cat "$B.2p" 2>/dev/null)" = "200" ] && tpb_code=200
    [ "$(cat "$B.3p" 2>/dev/null)" = "200" ] && yts_code=200
  fi
  rm -f "$B.1" "$B.2p" "$B.2d" "$B.3p" "$B.3d" "$B.4"
else
  # 没有可写临时目录时退回串行，超时收短以控制总时长
  btsow_code=$("$CURL" -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" -X POST \
    -H 'Content-Type: application/json' -H 'Referer: https://btsow.live/' \
    -d '[{"search":"inception"},1,1]' "$BTSOW_URL" 2>/dev/null)
  tpb_code=$("$CURL" $PROXY_OPT -s -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$TPB_URL" 2>/dev/null)
  yts_code=$("$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$YTS_URL" 2>/dev/null)
  nyaa_code=$("$CURL" $PROXY_OPT -sL -o /dev/null -w '%{http_code}' --max-time 3 -A "$UA" \
    "$NYAA_URL" 2>/dev/null)
fi

btsow_ok='false'
tpb_ok='false'
yts_ok='false'
nyaa_ok='false'
[ "$btsow_code" = "200" ] && btsow_ok='true'
[ "$tpb_code" = "200" ] && tpb_ok='true'
[ "$yts_code" = "200" ] && yts_ok='true'
[ "$nyaa_code" = "200" ] && nyaa_ok='true'

# curl 连不上/超时都会输出 "000"，统一成 timeout，前端才能当成"未知"显示灰点。
# 否则 000 会走到非 200 分支被标成红点，实测 apibay 慢的时候必现误报。
[ "$btsow_code" = "000" ] && btsow_code=''
[ "$tpb_code" = "000" ] && tpb_code=''
[ "$yts_code" = "000" ] && yts_code=''
[ "$nyaa_code" = "000" ] && nyaa_code=''

echo "{\"btsow\":{\"ok\":$btsow_ok,\"code\":\"${btsow_code:-timeout}\"},\"tpb\":{\"ok\":$tpb_ok,\"code\":\"${tpb_code:-timeout}\"},\"yts\":{\"ok\":$yts_ok,\"code\":\"${yts_code:-timeout}\"},\"nyaa\":{\"ok\":$nyaa_ok,\"code\":\"${nyaa_code:-timeout}\"},\"t\":$(date +%s)}"
exit 0
