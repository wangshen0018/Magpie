#!/system/bin/sh
# 看门狗：代理闲置超时自动关闭。由 proxy.cgi 后台拉起。
# 用法: sh watchdog.sh <部署目录> <闲置秒数>
#
# 闲置判定用 lastuse 的 mtime（搜索 CGI 每次请求都会 touch 它），
# 用 find -mmin 判断，不依赖 stat -c（toybox/busybox 行为不一致）。

DIR="$1"
IDLE="${2:-600}"
case "$IDLE" in *[!0-9]*) IDLE=600 ;; esac
[ "$IDLE" -lt 60 ] && IDLE=60
MIN=$((IDLE / 60))
[ "$MIN" -lt 1 ] && MIN=1
SB="${MAGPIE_SB:-/data/adb/srv/bin/sing-box}"

i=0
while [ "$i" -lt 2880 ]; do        # 最多存活 24 小时，防止孤儿常驻
  sleep 30
  i=$((i+1))
  [ "$(cat "$DIR/state" 2>/dev/null)" = "on" ] || exit 0
  OLD=$(find "$DIR/lastuse" -mmin +"$MIN" -print 2>/dev/null)
  if [ -n "$OLD" ]; then
    for p in /proc/[0-9]*; do
      c=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
      case "$c" in
        *"$SB"*run*|*"sing-box"*run*) kill "${p#/proc/}" 2>/dev/null ;;
      esac
    done
    echo off > "$DIR/state"
    echo "$(date '+%F %T') idle>${IDLE}s, proxy stopped" >> "$DIR/watchdog.log"
    exit 0
  fi
done
