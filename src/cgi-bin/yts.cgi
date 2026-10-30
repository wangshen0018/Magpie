#!/system/bin/sh
# CGI: 转发 YTS（电影专用，官方 JSON API）
# 入参: q=关键词（前端已做 URL 编码，这里原样拼进 URL）
# 出参: YTS 原始 JSON（{...}）；失败时返回 {"status":"error","data":{"movies":[]}}
#
# 域名回退：YTS 官方 2026-04-10 起把 API base 迁到 movies-api.accel.li，
# 旧域名 yts.gg 目前仍在服务（实测 2.5 秒返回）。这类站换域名频繁，不硬编码单域名。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

CURL=$(command -v curl 2>/dev/null)
[ -z "$CURL" ] && CURL=/system/bin/curl

for _l in /data/adb/srv/magnet/proxy-lib.sh /data/adb/magnet/proxy-lib.sh; do
  [ -f "$_l" ] && { . "$_l"; break; }
done

q="${QUERY_STRING}"
case "$q" in
  q=*) q="${q#q=}" ;;
  *)   q="" ;;
esac
q="${q%%&*}"

# q 是 URL 编码的，直接拼进 query_term 正好（同一编码层），不能在这里解码。
# 但判空必须解码后判：实测 q=%20 / q=+ / q=%09 这类纯空白输入，YTS 会返回
# 整站列表（movie_count 78129），前端就会显示一堆与关键词无关的条目。
qchk=$(printf '%s' "$q" | sed 's/%20//g; s/%09//g; s/%0[aAdD]//g; s/+/ /g' | tr -d ' \t')
if [ -z "$qchk" ]; then
  echo '{"status":"error","data":{"movies":[]}}'
  exit 0
fi

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

# 完整且成功的 JSON 才算可用：首字符 { 、末字符 } 、含精确的 "status":"ok"
# （不能只通配匹配 ok，标题或 status_message 里出现 OK 会误判）
good_json() {
  case "$1" in \{*) ;; *) return 1 ;; esac
  [ "$(printf '%s' "$1" | tail -c 1)" = "}" ] || return 1
  printf '%s' "$1" | grep -q '"status":"ok"' || return 1
  return 0
}

try_base() {
  # $1=域名 $2=额外 curl 参数（代理开关，可为空）$3=超时秒数
  R=$("$CURL" -sL --max-time "$3" $2 -A "$UA" \
    "https://$1/api/v2/list_movies.json?query_term=${q}&limit=20" 2>/dev/null)
  if good_json "$R"; then
    printf '%s' "$R"
    return 0
  fi
  return 1
}

# 与 search.cgi 相反：**直连优先，代理兜底**。
# 因为 YTS 的国内直连本来就是好的（实测 1.5~2.5 秒、从未失败），
# 先走代理反而白多一跳延迟；代理只在直连两个域名都不通时才派上用场。
#
# 代理死亡也不会拖累这里：urltest 成员全死时 sing-box 立即拒绝连接
# （实测 connection refused、毫秒级），不是慢慢超时。
# 时序预算：直连两跳各 6 秒（YTS 实测 1.5~2.5 秒就回，6 秒很宽），
# 代理两跳各 8 秒。最坏 6+6+8+8=28 秒，与 search.cgi 同口径；
# 前端 srcYTS 相应从 20 秒放宽到 30 秒，否则后端还没跑完前端先放弃。
OUT=""
for base in yts.gg movies-api.accel.li; do
  OUT=$(try_base "$base" "" 6) && break
  OUT=""
done
if [ -z "$OUT" ] && [ -n "$PROXY_OPT" ]; then
  for base in yts.gg movies-api.accel.li; do
    OUT=$(try_base "$base" "$PROXY_OPT" 8) && break
    OUT=""
  done
fi

if [ -z "$OUT" ]; then
  echo '{"status":"error","data":{"movies":[]}}'
  exit 0
fi

printf '%s' "$OUT"
exit 0