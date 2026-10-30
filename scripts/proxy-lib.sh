#!/system/bin/sh
# 共享：判断"本地代理是否已就绪且值得走"。由搜索类 CGI source。
# 结果写进全局 PROXY_OPT（使用处**不要加引号**，空值时靠词分割自然消失；
#   加引号会留下一个空参数，curl 会把它当 URL，实测报 "option : blank argument"）。
#
# 只有在同时满足三个条件时才注入 --proxy：
#   1) state = on        2) sb.pid 指向的进程真的活着   3) 配置里有真实节点（proxy/direct 都不算）
# 第 3 条是重点：direct 出站只是透传，不解决封锁，却白白多绕一跳。
# 实测 YTS 直连 1~2 秒，经 direct 代理 12.8 秒。所以未接节点时必须走直连。
#
# 全程用 shell 内建（read / case），只在取端口时 fork 一次 grep。
# 早先版本每个进程 fork 一次 tr，单次请求 15 秒，别再犯。

MAGPIE_PROXY=""
PROXY_OPT=""

for _d in /data/adb/srv/magpie-proxy /data/adb/magpie-proxy; do
  [ -f "$_d/config.json" ] && { MAGPIE_PROXY="$_d"; break; }
done

if [ -n "$MAGPIE_PROXY" ]; then
  _s=""
  _p=""
  _c=""
  read -r _s < "$MAGPIE_PROXY/state" 2>/dev/null
  if [ "$_s" = "on" ]; then
    read -r _p < "$MAGPIE_PROXY/sb.pid" 2>/dev/null
    if [ -n "$_p" ]; then
      read -r _c < "/proc/$_p/comm" 2>/dev/null
      if [ "$_c" = "sing-box" ]; then
        # 看配置里有没有真实节点出站。两个坑都踩过：
        #  1) 正向枚举协议名会漏（sing-box 合法类型很多，而且 "proxy" 根本不是类型名，
        #     上一版写了它，实测 sing-box 直接报 unknown outbound type: proxy）。
        #     改成反向：outbounds 区段里出现任何 "type" 且不是 direct/block，就算有节点。
        #  2) 必须限定只看 outbounds 区段。inbounds 里那个 mixed 入站也带 "type"，
        #     不加区段判断会把 direct 配置误判成"已接节点"。
        # 用内建 read 逐行扫描，不 fork。
        # 只看 outbounds 数组的**第一个** type —— 那才是默认出站，决定流量去哪。
        # 见到就定论并停止扫描，否则后面 dns/route 段落里的 "type":"https" 会误判。
        _node=""
        _in=0
        _seen=0
        while IFS= read -r _line || [ -n "$_line" ]; do
          [ "$_seen" = 1 ] && break
          case "$_line" in
            *'"outbounds"'*) _in=1; continue ;;
            *'"inbounds"'*)  _in=0; continue ;;
          esac
          [ "$_in" = 1 ] || continue
          case "$_line" in
            *'"type"'*)
              _seen=1
              case "$_line" in
                *'"type": "direct"'*|*'"type":"direct"'*) ;;
                *'"type": "block"'*|*'"type":"block"'*)   ;;
                *) _node=1 ;;
              esac
              ;;
          esac
        done < "$MAGPIE_PROXY/config.json"
        if [ -n "$_node" ]; then
          _port=$(grep -o 'listen_port[^0-9]*[0-9]*' "$MAGPIE_PROXY/config.json" 2>/dev/null | head -1 | tr -dc '0-9')
          [ -n "$_port" ] || _port=10808
          PROXY_OPT="--proxy http://127.0.0.1:$_port"
          # 续命：搜索活动算"使用中"，别让看门狗把正在用的代理关掉
          touch "$MAGPIE_PROXY/lastuse" 2>/dev/null
        fi
      fi
    fi
  fi
fi