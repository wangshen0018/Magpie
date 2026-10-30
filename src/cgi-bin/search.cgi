#!/system/bin/sh
# CGI: 转发 apibay（Pirate Bay 官方 JSON API）搜索
# 入参: q=关键词（前端已做 URL 编码，这里原样拼进 URL）
# 出参: apibay 原始 JSON 数组；失败时返回 []

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

# ---- 本地代理感知：库在 web 根外（.sh 会被 httpd 当静态文件下载，不能放 www/）----
# 库只在"开关为 on 且配置里有真实节点"时才给 PROXY_OPT 赋值；direct 透传不注入。
# 注意使用处 $PROXY_OPT 一律不加引号：加引号时空值会留下一个空参数，
# curl 报 "option : blank argument" 直接失败（实测过）。
for _l in /data/adb/srv/magnet/proxy-lib.sh /data/adb/magnet/proxy-lib.sh; do
  [ -f "$_l" ] && { . "$_l"; break; }
done

q="${QUERY_STRING}"
case "$q" in
  q=*) q="${q#q=}" ;;
  *)   q="" ;;
esac
q="${q%%&*}"

if [ -z "$q" ]; then
  echo '[]'
  exit 0
fi

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

# 注意：不要带 cat=0。apibay 现在把 cat=0 当成一个真实的分类，实测稳定返回
# "No results returned"；不带 cat（或 cat=）才是全站搜索。
URL="https://apibay.org/q.php?q=${q}"

# 代理开着但 urltest 成员全死时，sing-box 不回退直连而是拒绝连接
# （实测日志 connection refused、curl 秒回 000）。sing-box 1.14 的 route.final
# 只接受单个 tag（文档 "Default outbound tag"，实测写数组 check 直接 FAIL），
# 所以回退只能放在调用层做。
#
# apibay 的策略是"代理优先"：它的直连本来就不通，先赌代理 15 秒，
# 拿不到再退回直连 13 秒碰运气，总预算 ~28 秒，前端 srcTPB 留 30 秒。
# 判"拿到"的标准：完整闭合的 JSON 数组。apibay 搜不到时返回的是
# [{"id":"0","name":"No results returned",...}] —— 那同样是合法响应，
# 说明代理通了，绝不能再退回直连白等 13 秒。
OUT=""
if [ -n "$PROXY_OPT" ]; then
  OUT=$("$CURL" -s --max-time 15 $PROXY_OPT -A "$UA" "$URL" 2>/dev/null)
fi
case "$OUT" in
  \[*\]) : ;;                      # 完整数组（含占位空结果），代理成功，不再重试
  *) OUT=$("$CURL" -s --max-time 13 -A "$UA" "$URL" 2>/dev/null) ;;
esac

# 拿不到东西或返回的不是完整 JSON 数组，一律给空数组，前端不用处理异常
case "$OUT" in
  *"No results returned"*) echo '[]' ;;
  \[*\]) printf '%s' "$OUT" ;;
  *)   echo '[]' ;;
esac

exit 0