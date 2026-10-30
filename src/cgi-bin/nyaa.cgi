#!/system/bin/sh
# CGI: 转发 nyaa.si 搜索（转成 JSON 给前端）
# 入参: q=关键词（URL 编码，原样拼进 Nyaa 的 query，不解码）
# 出参: {"data":[{"hash":"..","name":"..","size":字节,"seeders":n,"leechers":n}]}
#
# 为什么必须走代理：nyaa.si 国内直连实测 12 秒超时（code=000），
# 经代理 3.3~3.7 秒稳定返回 75 条。这是本项目第一个"只在代理下可用"的源。
#
# 为什么把 HTML 转成 JSON 而不是丢给前端：Nyaa 没有可用 JSON API
# （/api/v1/search 实测 404），只能解析页面；解析不该让前端扛。
#
# 为什么用文件而不是 shell 变量接 curl 输出：
# 实测中文结果的页面 133768 字节，用 HTML=$(curl ...) 捕获后内容会丢，
# 而 curl -o 写文件再解析完全正常（same URL, same proxy）。所以走临时文件。

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
  q=*) q="${q#q=}" ;;    # Nyaa 的 q 参数是 URL 编码的，前端已编码，原样用
  *)   q="" ;;
esac
q="${q%%&*}"

# 判空必须解码后判：实测 q=%20（纯空格）会让 Nyaa 忽略关键词、返回整站
# current 页（"out of 1000"），前端就会显示一堆无关条目。YTS 踩过同一个坑。
# 注意：只用于判空，真正请求仍用编码原值（同一编码层）。
qchk=$(printf '%s' "$q" | sed 's/%20//g; s/%09//g; s/%0[aAdD]//g; s/+/ /g' | tr -d ' \t')
if [ -z "$qchk" ]; then
  echo '{"data":[]}'
  exit 0
fi

UA='Mozilla/5.0 (Linux; Android 13; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
URL="https://nyaa.si/?q=${q}&c=0_0&f=0"

# 临时文件（本机 /data/local/tmp 可写；没有就退回 /cache）
TMP=""
for d in /data/local/tmp /cache /tmp; do
  if [ -d "$d" ] && [ -w "$d" ]; then TMP="$d"; break; fi
done
[ -z "$TMP" ] && { echo '{"data":[]}'; exit 0; }
F="$TMP/.nyaa_$$.html"
trap 'rm -f "$F"' EXIT

# 代理优先（直连必死），16 秒；失败再给直连 8 秒碰运气。总预算 24 秒，前端 26 秒。
# --compressed 实测有效：页面 109612 -> 14474 字节，耗时 3.7~4.5s -> 2.3~2.5s。
# 走代理时链路质量一般，省下 87% 传输量对响应时间影响明显。
ok=0
if [ -n "$PROXY_OPT" ]; then
  "$CURL" -sL --compressed --max-time 16 $PROXY_OPT -A "$UA" -o "$F" "$URL" 2>/dev/null
  grep -q '<tr class=' "$F" 2>/dev/null && ok=1
fi
if [ "$ok" != 1 ]; then
  "$CURL" -sL --compressed --max-time 8 -A "$UA" -o "$F" "$URL" 2>/dev/null
  grep -q '<tr class=' "$F" 2>/dev/null && ok=1
fi
[ "$ok" != 1 ] && { echo '{"data":[]}'; exit 0; }

# 以 </tr> 为记录分隔逐条解析。页面结构（实测）：
#   <a href="/view/NNN" title="标题">     <- 标题（HTML 转义过，&amp; 等要还原）
#   <a href="magnet:?xt=urn:btih:HASH&... <- 磁力，hash 取 btih 后 40 位
#   <td class="text-center">364.9 MiB</td> <- size（带单位）
#   <td class="text-center" data-timestamp="..">日期</td>
#   <td class="text-center">106</td>       <- seeders
#   <td class="text-center">2</td>         <- leechers
# 日期格带 data-timestamp，所以不能按"第几个 text-center"编号，
# 而是：带单位的当 size，纯数字的按出现顺序当前两个是 seeds/leech。
awk '
  BEGIN { RS = "</tr>"; ORS = ""; first = 1; print "{\"data\":[" }
  !/<tr class=/ { next }
  {
    line = $0
    hash = ""
    if (match(line, /urn:btih:[0-9a-fA-F]+/)) {
      hash = substr(line, RSTART + 9, RLENGTH - 9)
      hash = tolower(hash)
    }
    name = ""
    if (match(line, /<a href="\/view\/[0-9]+" title="[^"]*"/)) {
      s = substr(line, RSTART, RLENGTH)
      sub(/^.*title="/, "", s)
      sub(/"$/, "", s)
      name = s
    }
    size = 0; seeds = 0; leech = 0; nums = 0
    rest = line
    while (match(rest, /<td class="text-center"[^>]*>[^<]*<\/td>/)) {
      cell = substr(rest, RSTART, RLENGTH)
      rest = substr(rest, RSTART + RLENGTH)
      sub(/^<td[^>]*>/, "", cell)
      sub(/<\/td>$/, "", cell)
      gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", cell)
      if (cell ~ /^[0-9.]+ [KMGTP]i?B$/) {
        v = cell; sub(/ .*/, "", v); u = cell; sub(/^[0-9.]+ /, "", u)
        v = v + 0
        if (u ~ /^Ki?B$/)      v = v * 1024
        else if (u ~ /^Mi?B$/) v = v * 1048576
        else if (u ~ /^Gi?B$/) v = v * 1073741824
        else if (u ~ /^Ti?B$/) v = v * 1099511627776
        size = int(v)
      } else if (cell ~ /^[0-9]+$/) {
        nums++
        if (nums == 1) seeds = cell + 0
        else if (nums == 2) leech = cell + 0
      }
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
      printf "{\"hash\":\"%s\",\"name\":\"%s\",\"size\":%d,\"seeders\":%d,\"leechers\":%d}", \
             hash, name, size, seeds, leech
    }
  }
  END { print "]}" }
' "$F"

exit 0
