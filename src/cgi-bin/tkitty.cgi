#!/system/bin/sh
# CGI: 转发 TorrentKitty 搜索
# 入参: q=关键词（URL 编码，原样拼进路径）
# 出参: {"data":[{"hash":"..","name":"..","size":字节,"seeders":null,"leechers":null,"date":".."}]}
#
# 只在代理下可用：直连实测 12 秒超时（同 Nyaa）。
# 无 JSON API，解析 HTML。页面结构（实测很规整，一条一行）：
#   <tr><td class="name">标题</td>
#       <td class="size">223.04 kb</td>
#       <td class="date">2026-07-20</td>
#       <td class="action"><a href="/information/HASH" ...>
#                              <a href="magnet:?xt=urn:btih:HASH&dn=...">
# 注意：它**不提供 seeders/leechers**，那几个字段只能给 null（前端会显示日期）。
# size 单位是小写 "kb/mb/gb"，按 1024 进制换算。

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

if [ -z "$q" ]; then
  echo '{"data":[]}'
  exit 0
fi

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
URL="https://www.torrentkitty.tv/search/${q}/"

# 临时文件而非变量：与 nyaa 同样理由，多字节大响应用 $(...) 捕获不可靠
TMP=""
for d in /data/local/tmp /cache /tmp; do
  if [ -d "$d" ] && [ -w "$d" ]; then TMP="$d"; break; fi
done
[ -z "$TMP" ] && { echo '{"data":[]}'; exit 0; }
F="$TMP/.tk_$$.html"
trap 'rm -f "$F"' EXIT

# 代理优先 16 秒，失败直连 8 秒兜底。实测代理下 2.6 秒出页面（--compressed 后）。
ok=0
if [ -n "$PROXY_OPT" ]; then
  "$CURL" -sL --compressed --max-time 16 $PROXY_OPT -A "$UA" -o "$F" "$URL" 2>/dev/null
  grep -q 'class="name"' "$F" 2>/dev/null && ok=1
fi
if [ "$ok" != 1 ]; then
  "$CURL" -sL --compressed --max-time 8 -A "$UA" -o "$F" "$URL" 2>/dev/null
  grep -q 'class="name"' "$F" 2>/dev/null && ok=1
fi
[ "$ok" != 1 ] && { echo '{"data":[]}'; exit 0; }

# 以 </tr> 切记录；只处理同时含 class="name" 与 magnet 的行（表头行会被自然跳过）
awk '
  BEGIN { RS = "</tr>"; ORS = ""; first = 1; print "{\"data\":[" }
  !/class="name"/ { next }
  {
    line = $0
    if (line !~ /magnet:\?xt=urn:btih:/) next

    hash = ""
    if (match(line, /urn:btih:[0-9A-Fa-f]+/)) {
      hash = substr(line, RSTART + 9, RLENGTH - 9)
      hash = tolower(hash)
    }

    name = ""
    if (match(line, /<td class="name">[^<]*<\/td>/)) {
      s = substr(line, RSTART, RLENGTH)
      sub(/^<td class="name">/, "", s)
      sub(/<\/td>$/, "", s)
      name = s
    }

    size = 0
    if (match(line, /<td class="size">[^<]*<\/td>/)) {
      s = substr(line, RSTART, RLENGTH)
      sub(/^<td class="size">/, "", s)
      sub(/<\/td>$/, "", s)
      # 形如 "223.04 kb" / "1.2 gb"
      if (match(s, /[0-9.]+/)) {
        v = substr(s, RSTART, RLENGTH) + 0
        u = tolower(s)
        if (u ~ /kb/)      size = int(v * 1024)
        else if (u ~ /mb/) size = int(v * 1048576)
        else if (u ~ /gb/) size = int(v * 1073741824)
        else if (u ~ /tb/) size = int(v * 1099511627776)
        else               size = int(v)
      }
    }

    date = ""
    if (match(line, /<td class="date">[^<]*<\/td>/)) {
      s = substr(line, RSTART, RLENGTH)
      sub(/^<td class="date">/, "", s)
      sub(/<\/td>$/, "", s)
      date = s
    }

    if (hash != "") {
      gsub(/&amp;/, "\\&", name)
      gsub(/&quot;/, "\"", name)
      gsub(/&lt;/, "<", name)
      gsub(/&gt;/, ">", name)
      gsub(/\\/, "\\\\", name)
      gsub(/"/, "\\\"", name)
      if (!first) print ","
      first = 0
      printf "{\"hash\":\"%s\",\"name\":\"%s\",\"size\":%d,\"seeders\":null,\"leechers\":null,\"date\":\"%s\"}", \
             hash, name, size, date
    }
  }
  END { print "]}" }
' "$F"

exit 0
