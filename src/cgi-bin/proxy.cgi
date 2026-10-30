#!/system/bin/sh
# CGI: 代理开关（sing-box 本地混合端口）
# 入参: a=status|on|off|touch   （默认 status）
# 出参: {"on":bool,"alive":bool,"addr":"...","idle":秒,"outbound":"direct|custom"}
#
# 设计要点：
# - 只接受四个固定动作名，其余一律拒绝，外部输入不进任何 shell 拼接。
# - 端口绑 127.0.0.1，局域网其他设备访问不到。
# - 配置目录在 web 根之外（www/ 内文件会被 httpd 当静态文件下载，含节点密钥）。
# - 状态文件可能与真实进程不同步（进程被杀/崩），status 就地校正后再汇报。
# - 闲置秒数读 $DIR/idle 文件；不用环境变量传，httpd 不保证继承父 shell 的 env。
# - 进程探测必须 O(1)：这台机器有 920 个进程，早先版本每个都 fork 一次 tr，
#   单次 status 耗时 15 秒，前端点开关根本没反应。现在靠 sb.pid + /proc/<pid>/comm。

printf 'Content-Type: application/json\r\n'
printf 'Cache-Control: no-store\r\n'
printf 'X-Content-Type-Options: nosniff\r\n'
printf '\r\n'

A="${QUERY_STRING}"
case "$A" in
  a=*) A="${A#a=}" ;;
  *)   A="status" ;;
esac
A="${A%%&*}"
case "$A" in
  status|on|off|touch) ;;
  *) echo '{"error":"bad action"}'; exit 0 ;;
esac

DIR=""
for d in /data/adb/srv/magpie-proxy /data/adb/magpie-proxy; do
  if [ -f "$d/config.json" ]; then DIR="$d"; break; fi
done
if [ -z "$DIR" ]; then
  echo '{"error":"proxy not set up, run scripts/proxy-setup.sh"}'
  exit 0
fi

SB="${MAGPIE_SB:-/data/adb/srv/bin/sing-box}"
[ -x "$SB" ] || SB=$(command -v sing-box 2>/dev/null)
if [ -z "$SB" ] || [ ! -x "$SB" ]; then
  echo '{"error":"sing-box binary not found"}'
  exit 0
fi

IDLE=""
read -r IDLE < "$DIR/idle" 2>/dev/null
case "$IDLE" in *[!0-9]*|"") IDLE=600 ;; esac

# 端口从配置里读。模式容忍冒号后的空格（setup 写成 "listen_port": 10808）
ADDR="127.0.0.1:10808"
PORTN=$(grep -o 'listen_port[^0-9]*[0-9]*' "$DIR/config.json" 2>/dev/null | head -1 | tr -dc '0-9')
[ -n "$PORTN" ] && ADDR="127.0.0.1:$PORTN"

STATE="$DIR/state"
STAMP="$DIR/lastuse"
SBPID="$DIR/sb.pid"
WDPID="$DIR/watchdog.pid"

# O(1) 存活判定：读 pid 文件 + /proc/<pid>/comm。read 是 shell 内建，不 fork。
alive_of() {
  [ -n "$1" ] || return 1
  NM=""
  read -r NM < "/proc/$1/comm" 2>/dev/null || return 1
  [ "$NM" = "sing-box" ]
}

cur_pid() {
  P=""
  read -r P < "$SBPID" 2>/dev/null
  if alive_of "$P"; then
    printf '%s' "$P"
    return 0
  fi
  return 1
}

# sb.pid 丢失时（比如开机自启已经把代理拉起、或手改过 state）扫一次 /proc。
# 用 read 读 cmdline，全程不 fork。cmdline 里的 NUL 被 read 丢掉，字段会粘成
#   /data/adb/srv/bin/sing-boxrun-D/data/adb/srv/magpie-proxy-c/data/.../config.json
# 所以匹配串按粘连形态写。判据用 -D 的目录而不是 $SB 路径：
# MAGPIE_SB 换了也不影响识别，而这个目录是本服务独有的，不会认错人。
discover_pid() {
  for p in /proc/[0-9]*; do
    Z=""
    read -r Z < "$p/cmdline" 2>/dev/null
    case "$Z" in
      *run-D"$DIR"-c*)
        if alive_of "${p#/proc/}"; then
          printf '%s' "${p#/proc/}" > "$SBPID"
          printf '%s' "${p#/proc/}"
          return 0
        fi
        ;;
    esac
  done
  return 1
}

get_pid() {
  cur_pid && return 0
  discover_pid
}

is_on() { S=""; read -r S < "$STATE" 2>/dev/null; [ "$S" = "on" ]; }

do_stop() {
  P=$(get_pid)
  if [ -n "$P" ]; then
    kill "$P" 2>/dev/null
    sleep 1
    # 复查仍然活着才升级成 kill -9，避免对已退出的 PID 动手
    alive_of "$P" && kill -9 "$P" 2>/dev/null
  fi
  rm -f "$SBPID"
  echo off > "$STATE"
  # 不 kill watchdog：setsid 会 fork，$! 记下的不是 watchdog 本体，
  # 那个 PID 可能已被回收并分给无关进程，照它 kill 就是杀错别的程序。
  # watchdog 每 30 秒读一次 state，见到 off 会自己退出（见 watchdog.sh）。
  rm -f "$WDPID"
}

spawn() {
  # $@ 是要后台放的命令。必须 < /dev/null：否则继承 httpd 给 CGI 的请求 stdin，
  # httpd 会等这条管道关闭，本次请求就没有响应。
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup "$@" < /dev/null &
  else
    nohup "$@" < /dev/null &
  fi
}

do_start() {
  if ! "$SB" check -c "$DIR/config.json" >/dev/null 2>&1; then
    echo '{"error":"config invalid, run sing-box check manually"}'
    return 1
  fi
  : >> "$DIR/run.out"
  touch "$STAMP"
  # 注意：setsid 会 fork，$! 拿到的不是 sing-box 的 PID，所以之后靠 discover_pid 找
  spawn "$SB" run -D "$DIR" -c "$DIR/config.json" >> "$DIR/run.out" 2>&1
  I=0
  P=""
  while [ "$I" -lt 10 ]; do
    sleep 0.5
    I=$((I+1))
    rm -f "$SBPID"
    P=$(discover_pid)
    [ -n "$P" ] && break
  done
  if [ -z "$P" ]; then
    echo off > "$STATE"
    T=$(tail -3 "$DIR/run.out" 2>/dev/null | tr '\n' ' ' | cut -c1-200)
    printf '{"error":"sing-box failed to start","detail":"%s"}\n' "$T"
    return 1
  fi
  echo on > "$STATE"
  if [ -x "$DIR/watchdog.sh" ]; then
    # 不记录 watchdog 的 PID：setsid 会 fork，$! 不是 watchdog 本体，
    # 记下这个号既没用又可能指向后来复用的无关进程。
    spawn sh "$DIR/watchdog.sh" "$DIR" "$IDLE" >> "$DIR/watchdog.log" 2>&1
  fi
  return 0
}

case "$A" in
  touch)
    # 搜索请求续命，防止用着用着被看门狗关掉
    is_on && touch "$STAMP"
    echo '{"ok":true}'
    exit 0
    ;;
  on)
    if [ -n "$(get_pid)" ]; then
      echo on > "$STATE"; touch "$STAMP"
    else
      do_start || exit 0
    fi
    ;;
  off)
    do_stop
    ;;
esac

# 汇报真实状态，顺带校正 state 与进程不一致
P=$(get_pid)
if is_on; then
  if [ -z "$P" ]; then
    ON=false; ALIVE=false; echo off > "$STATE"
  else
    ON=true; ALIVE=true
  fi
else
  ON=false
  [ -n "$P" ] && ALIVE=true || ALIVE=false
fi

# 有没有节点：只看 outbounds 数组的第一个 type（默认出站）。
# 不能用 grep 全文找 "direct" —— 配置末尾常有备用的 direct 出站，
# urltest 主配置会被误报成 direct（实测踩过，页面因此错显"透传"）。
# 判据与 proxy-lib.sh 保持一致：urltest 等任何非 direct/block 都算有节点。
OUT="direct"
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
        *) OUT="custom" ;;
      esac
      ;;
  esac
done < "$DIR/config.json"

echo "{\"on\":$ON,\"alive\":$ALIVE,\"addr\":\"$ADDR\",\"idle\":$IDLE,\"outbound\":\"$OUT\"}"
exit 0