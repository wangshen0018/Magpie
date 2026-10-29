#!/system/bin/sh
# CGI: 转发 btsow 搜索（原样返回 JSON，字段解析交给前端）
# 入参: POST 正文为 UTF-8 原文关键词（前端用 text/plain 发）
# 出参: btsow 原始 JSON；失败时返回 {"code":200,"data":[]}

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

Q=$(cat)
# 丢掉换行/制表/空字节，避免把 JSON 拼坏
Q=$(printf '%s' "$Q" | tr -d '\000\r\n\t')
# 掐掉首尾空格：btsow 收到纯空格会返回整站最新列表，必须当空搜索处理
Q=$(printf '%s' "$Q" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
# 限长 200 字节，防止异常输入
Q=$(printf '%s' "$Q" | cut -c1-200)

if [ -z "$Q" ]; then
  echo '{"code":200,"data":[]}'
  exit 0
fi

# 转义反斜杠与双引号：顺序必须是先反斜杠、后引号
Q=$(printf '%s' "$Q" | sed 's/\\/\\\\/g; s/"/\\"/g')

OUT=$("$CURL" -s --max-time 15 \
  -A 'Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Referer: https://btsow.live/' \
  -d "[{\"search\":\"${Q}\"},30,1]" \
  'https://btsow.live/bts/data/api/search' 2>/dev/null)

# curl 超时会返回半截内容，校验首尾是不是完整的 {...}，否则前端 JSON.parse 会报错
case "$OUT" in
  \{*\}) printf '%s' "$OUT" ;;
  *)     echo '{"code":200,"data":[]}' ;;
esac

exit 0
