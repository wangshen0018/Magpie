#!/system/bin/sh
# CGI: 查 aria2 当前下载情况，供页面底部进度条使用
# 入参: 无
# 出参: {"active":{aria2原始响应},"waiting":{...},"stopped":{...}}
#
# 为什么原样转发 aria2 的响应而不在这里解析：
#   sh 里拆嵌套 JSON 只能用 sed，字段一多就脆。前端的 JSON.parse 本来就会解析，
#   这里只做三件事——补齐 token、拼接成一个合法 JSON、失败时降级成空数组。
#
# 字段只取需要的几个，避免大任务的 files 列表把响应撑到几百 KB。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

SELF_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
if [ -f "$SELF_DIR/../../lib/aria2.sh" ]; then
  . "$SELF_DIR/../../lib/aria2.sh"
else
  echo '{"error":"lib/aria2.sh not found, redeploy needed"}'
  exit 0
fi

# 通用的任务字段。bittorrent 里带 info.name（种子里写的名字，比文件名靠谱）；
# files 里的 path 当兜底；totalLength/completedLength 用来算进度。
KEYS='["gid","status","totalLength","completedLength","downloadSpeed","errorCode","files","bittorrent"]'

# 第一个请求兼作存活探测：aria2 没起时立刻返回，不再试后面两个（否则要等三个超时）
ACT=$(aria2_rpc "aria2.tellActive" "[${KEYS}]")
if [ -z "$ACT" ] || ! is_json_object "$ACT"; then
  if [ -z "$MG_CONF" ]; then
    echo '{"error":"aria2 config not found"}'
  else
    echo "{\"error\":\"aria2 rpc no response on port ${MG_PORT}\"}"
  fi
  exit 0
fi

# 这两个失败就降级成空列表，不影响整体返回（下载进度缺等待队列也能用）
WAI=$(aria2_rpc "aria2.tellWaiting" "[0,30,${KEYS}]")
is_json_object "$WAI" || WAI='{"result":[]}'

STP=$(aria2_rpc "aria2.tellStopped" "[0,20,${KEYS}]")
is_json_object "$STP" || STP='{"result":[]}'

printf '{"active":%s,"waiting":%s,"stopped":%s}' "$ACT" "$WAI" "$STP"
exit 0
