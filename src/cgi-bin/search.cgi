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

OUT=$("$CURL" -s --max-time 12 \
  -A 'Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36' \
  "https://apibay.org/q.php?q=${q}&cat=0" 2>/dev/null)

# 拿不到东西或返回的不是完整 JSON 数组，一律给空数组，前端不用处理异常
# 注意三点：
# 1. apibay 搜不到时会返回一条 info_hash 全 0 的 "No results returned" 占位记录，前端过滤不全容易当成真结果
# 2. curl 超时会返回半截内容，必须校验首尾是不是完整的 [...]，否则前端 JSON.parse 直接报错
case "$OUT" in
  *"No results returned"*) echo '[]' ;;
  \[*\]) printf '%s' "$OUT" ;;
  *)   echo '[]' ;;
esac

exit 0
