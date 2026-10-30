#!/system/bin/sh
# Boot autostart for Magpie node updater. New file, does not touch srv.sh.
sleep 45
pgrep -f node-scheduler >/dev/null 2>&1 || \
  nohup sh /data/adb/srv/magpie-proxy/node-scheduler.sh >/dev/null 2>&1 < /dev/null &