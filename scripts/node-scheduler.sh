#!/system/bin/sh
# Hourly wake-up; node-update.sh self-gates (only acts in 03:xx, once/day).
# Deliberately dumb: all logic and locking live in node-update.sh.
while :; do
  sh /data/adb/srv/magpie-proxy/node-update.sh
  sleep 3600
done