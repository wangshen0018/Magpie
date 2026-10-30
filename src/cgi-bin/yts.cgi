#!/system/bin/sh
# CGI: 转发 YTS（电影专用，官方 JSON API）
# 入参: q=关键词（前端已做 URL 编码，这里原样拼进 URL）
# 出参: YTS 原始 JSON（{...}）；失败时返回 {"status":"error","data":{"movies":[]}}
#
# 为什么需要域名回退：YTS 官方 2026-04-10 起把 API base 迁到 movies-api.accel.li，
# 旧域名 yts.gg 目前仍在服务（实测 2.5 秒返回）。这类站换域名很频繁，
# 硬编码单域名迟早变成死源，所以依次尝试，谁先返回完整 JSON 就用谁。

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

# q 是 URL 编码的，直接拼进 YTS 的 query_term 正好（同一编码层），不能在这里解码。
# 但判空必须解码后判：实测 q=%20 / q=+ / q=%09 这类纯空白输入，YTS 会返回
# 整站列表（movie_count 78129），前端就会显示一堆无关条目。
# 所以另取一份副本解码后 trim，只用来判断"是不是真的没输入"。
qchk=$(printf '%s' "$q" | sed 's/%20//g; s/%09//g; s/%0[aAdD]//g; s/+/ /g' | tr -d ' \t')
if [ -z "$qchk" ]; then
  echo '{"status":"error","data":{"movies":[]}}'
  exit 0
fi

# YTS 只有英文电影，中文关键词返回 movie_count 0 属正常（和 apibay 一样），不用拦

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

# 完整且成功的 JSON 才算可用：首字符 { 、末字符 } 、含精确的 "status":"ok"
# （不能只通配匹配 ok，标题或 status_message 里出现 OK 会误判）
good_json() {
  case "$1" in \{*) ;; *) return 1 ;; esac
  [ "$(printf '%s' "$1" | tail -c 1)" = "}" ] || return 1
  printf '%s' "$1" | grep -q '"status":"ok"' || return 1
  return 0
}

OUT=""
# 单个 base 给 9 秒，两个都试最多约 18 秒；前端 srcYTS 要等得更久
for base in yts.gg movies-api.accel.li; do
  R=$("$CURL" -sL --max-time 9 \
    -A "$UA" \
    "https://${base}/api/v2/list_movies.json?query_term=${q}&limit=20" 2>/dev/null)
  if good_json "$R"; then
    OUT="$R"
    break
  fi
done

if [ -z "$OUT" ]; then
  echo '{"status":"error","data":{"movies":[]}}'
  exit 0
fi

printf '%s' "$OUT"
exit 0
