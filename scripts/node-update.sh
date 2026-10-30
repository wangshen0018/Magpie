#!/system/bin/sh
# Magpie daily node updater. The scheduler wakes hourly; this script self-gates:
# no-op before 03:00; from 03:00 on it retries every hour until today's
# subscription file shows up (site publish time is unknown), then runs once.
#
# Flow: fetch daily sing-box subscription -> extract ss nodes -> TCP-probe ->
#       build config (top 8 into urltest) -> validate with a REAL request
#       through the new nodes (separate port, live proxy untouched) -> swap.
# Every failure path keeps the current config and current state.
#
# Manual:  sh node-update.sh --force  (ignores the hour gate + daily flag)
# Why not crond: only crond here writes tabs under another module's dir
# (GGAT_10007) which a module update may wipe. Loop = battguard pattern.

BB=/data/adb/magisk/busybox
SB=/data/adb/srv/bin/sing-box
CURL=/system/bin/curl
D=/data/adb/srv/magpie-proxy
LOG=$D/update.log
FLAG=$D/update.flag
CFG=$D/config.json
PORT=10808
TESTPORT=10809
MAX_NODES=8
GROUP=20
LOCKDIR=$D/update.lockdir

say() { echo "$(date "+%F %T") $*" >> "$LOG"; }

# ---- single-instance lock via mkdir (atomic), stale after 30 min ----
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$LOCKDIR" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 1800 ] && exit 0
  rmdir "$LOCKDIR" 2>/dev/null
  mkdir "$LOCKDIR" 2>/dev/null || exit 0
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

FORCE=0
[ "$1" = "--force" ] && FORCE=1
TODAY=$(date +%Y%m%d)
if [ "$FORCE" != 1 ]; then
  H=$((10#$(date +%H)))
  # 00-02 is too early: the site publishes later, and an unpublished date
  # returns a 200 HTML notice. Retry every hour after 03:00 until we get it.
  [ "$H" -lt 3 ] && exit 0
  [ "$(cat "$FLAG" 2>/dev/null)" = "$TODAY" ] && exit 0
fi

say "run start force=$FORCE"

# ---------- 1. fetch (URL: uploads/<Y>/<M no leading zero>/<Y><mm><dd>.json) ----------
Y=$(date +%Y)
MD=$(date +%m%d)
M10=$((10#$(date +%m)))
got=0
for u in "https://node.v2rayfree.org/uploads/$Y/$M10/$Y$MD.json" \
         "https://node.v2rayfree.org/uploads/$Y/$(date +%m)/$Y$MD.json"; do
  "$CURL" -s --max-time 25 -o "$D/sub.dl" "$u" 2>/dev/null
  # 200 is NOT proof: wrong URL returns a 200 HTML notice page.
  if [ -s "$D/sub.dl" ] && [ "$(head -c 1 "$D/sub.dl")" = "{" ] \
     && grep -q '"outbounds"' "$D/sub.dl" && grep -q '"server":' "$D/sub.dl"; then
    say "sub ok $u ($(wc -c < "$D/sub.dl")B)"
    mv "$D/sub.dl" "$D/sub.json"
    got=1
    break
  fi
  say "sub rejected $u"
done
if [ "$got" != 1 ]; then
  # Deliberately NO flag write here: today's file may not be published yet.
  # An hourly retry is cheap and will pick it up as soon as it appears.
  # (Contrast with the branches below -- once we HAVE the file, its content
  #  is fixed forever, so retrying gains nothing and we do set the flag.)
  rm -f "$D/sub.dl"
  say "today's subscription not available yet, will retry next hour"
  exit 0
fi

# ---------- 2. extract ss nodes from pretty-printed JSON (one key per line) ----------
"$BB" awk '
  function val(t) { sub(/^[^:]*: *"/, "", t); sub(/".*$/, "", t); return t }
  function flush() {
    if (type == "shadowsocks" && srv != "" && port != "" &&
        (meth == "aes-128-gcm" || meth == "aes-256-gcm" || meth == "chacha20-ietf-poly1305" || meth == "aes-128-ctr")) {
      k = srv ":" port
      if (!(k in seen)) { seen[k] = 1; print srv "|" port "|" meth "|" pass }
    }
    type = ""; srv = ""; port = ""; meth = ""; pass = ""
  }
  /"type":/        { flush(); type = val($0) }
  /"server":/      { srv = val($0) }
  /"server_port":/ { t = $0; gsub(/[^0-9]/, "", t); port = t }
  /"method":/      { meth = val($0) }
  /"password":/    { pass = val($0) }
  END              { flush() }
' "$D/sub.json" > "$D/nodes.ss"

N=$(wc -l < "$D/nodes.ss")
say "parsed $N ss nodes"
if [ "$N" -eq 0 ]; then
  echo "$TODAY" > "$FLAG"
  say "nothing usable, keeping config"
  exit 0
fi

# ---------- 3. TCP reachability, parallel batches ----------
: > "$D/nodes.tcp"
i=0
while IFS='|' read -r s p m w; do
  i=$((i + 1))
  (
    if "$BB" nc -v -w 3 -z "$s" "$p" </dev/null >/dev/null 2>&1; then
      echo "$s|$p|$m|$w" >> "$D/nodes.tcp"
    fi
  ) &
  [ $((i % GROUP)) -eq 0 ] && wait
done < "$D/nodes.ss"
wait
RT=$(wc -l < "$D/nodes.tcp")
say "tcp reachable $RT/$N"
if [ "$RT" -eq 0 ]; then
  echo "$TODAY" > "$FLAG"
  say "zero reachable, keeping config"
  exit 0
fi
head -n "$MAX_NODES" "$D/nodes.tcp" > "$D/nodes.pick"
PK=$(wc -l < "$D/nodes.pick")
say "picked $PK"

# ---------- 4. build candidate config ----------
TAGS=""
n=0
while IFS='|' read -r s p m w; do
  n=$((n + 1))
  [ -n "$TAGS" ] && TAGS="$TAGS, "
  TAGS="$TAGS\"u$n\""
done < "$D/nodes.pick"

{
  printf '{\n'
  printf '  "log": { "level": "warning", "timestamp": true, "output": "%s/sing-box.log" },\n' "$D"
  printf '  "inbounds": [\n'
  printf '    { "type": "mixed", "tag": "in", "listen": "127.0.0.1", "listen_port": %s }\n' "$PORT"
  printf '  ],\n'
  printf '  "outbounds": [\n'
  printf '    { "type": "urltest", "tag": "auto", "outbounds": [%s], "url": "https://www.gstatic.com/generate_204", "interval": "10m", "tolerance": 50 },\n' "$TAGS"
  i=0
  while IFS='|' read -r s p m w; do
    i=$((i + 1))
    printf '    { "type": "shadowsocks", "tag": "u%s", "server": "%s", "server_port": %s, "method": "%s", "password": "%s" },\n' "$i" "$s" "$p" "$m" "$w"
  done < "$D/nodes.pick"
  printf '    { "type": "direct", "tag": "direct" }\n'
  printf '  ],\n'
  printf '  "route": { "final": "auto" }\n'
  printf '}\n'
} > "$D/config.new"

if ! "$SB" check -c "$D/config.new" >/dev/null 2>&1; then
  echo "$TODAY" > "$FLAG"
  say "new config failed check, keeping current"
  exit 0
fi

# ---------- 5. validate with real traffic through new nodes ----------
# Separate inbound port so the live proxy keeps serving during the test.
sed "s/\"listen_port\": $PORT/\"listen_port\": $TESTPORT/" "$D/config.new" > "$D/config.test"
nohup "$SB" run -D "$D" -c "$D/config.test" >> "$D/run.out" 2>&1 < /dev/null &
sleep 4
TP=""
for p in /proc/[0-9]*; do
  if [ -r "$p/cmdline" ]; then
    z=""
    read -r z < "$p/cmdline" 2>/dev/null
    case "$z" in *config.test*) TP="${p#/proc/}" ;; esac
  fi
done
CODE=""
if [ -n "$TP" ]; then
  CODE=$("$CURL" -s -o /dev/null -w '%{http_code}' --proxy "http://127.0.0.1:$TESTPORT" --max-time 15 https://www.gstatic.com/generate_204 2>/dev/null)
  kill "$TP" 2>/dev/null
  sleep 1
  [ -d "/proc/$TP" ] && kill -9 "$TP" 2>/dev/null
fi
say "validate gstatic via new nodes: $CODE"
if [ "$CODE" != 204 ] && [ "$CODE" != 200 ]; then
  rm -f "$D/config.test"
  echo "$TODAY" > "$FLAG"
  say "validation failed, keeping current"
  exit 0
fi

# ---------- 6. swap + restart live proxy if it was on ----------
WAS_ON=off
[ "$(cat "$D/state" 2>/dev/null)" = on ] && WAS_ON=on
cp "$CFG" "$D/config.json.prev"
cp "$D/config.new" "$CFG"
chmod 600 "$CFG"
rm -f "$D/config.new" "$D/config.test" "$D/sub.json" "$D/sub.dl" "$D/nodes.ss" "$D/nodes.tcp" "$D/nodes.pick" 2>/dev/null
say "config swapped (was_on=$WAS_ON)"

if [ "$WAS_ON" = on ]; then
  OP=""
  read -r OP < "$D/sb.pid" 2>/dev/null
  NM=""
  [ -n "$OP" ] && read -r NM < "/proc/$OP/comm" 2>/dev/null
  if [ "$NM" = sing-box ]; then
    kill "$OP" 2>/dev/null
    sleep 2
    [ -d "/proc/$OP" ] && kill -9 "$OP" 2>/dev/null
  fi
  nohup "$SB" run -D "$D" -c "$CFG" >> "$D/run.out" 2>&1 < /dev/null &
  NP=""
  j=0
  while [ $j -lt 10 ]; do
    sleep 0.5
    j=$((j + 1))
    NP=""
    for p in /proc/[0-9]*; do
      z=""
      read -r z < "$p/cmdline" 2>/dev/null
      case "$z" in *run-D"$D"-c*) NP="${p#/proc/}" ;; esac
    done
    [ -n "$NP" ] && break
  done
  if [ -n "$NP" ]; then
    printf '%s' "$NP" > "$D/sb.pid"
    say "proxy restarted pid=$NP"
  else
    echo off > "$D/state"
    say "restart failed, state=off (fail-safe: searches go direct)"
  fi
fi

touch "$D/lastuse"
echo "$TODAY" > "$FLAG"
"$BB" tail -n 400 "$LOG" > "$LOG.t" 2>/dev/null && mv "$LOG.t" "$LOG"
say "run done"