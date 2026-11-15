#!/bin/bash
# E1: ad alanı kimlikleri, host ile kullanıcı ad alanı + PID ad alanı karşılaştırması
echo "== host (WSL) ad alanları =="
for n in pid mnt uts ipc net user cgroup; do printf "%-7s %s\n" $n "$(readlink /proc/$$/ns/$n)"; done
echo "== unshare -r -p -f --mount-proc =="
unshare -r -p -f --mount-proc bash -c '
  echo "uid=$(id -u) (dışarıdan: $(id -un))"
  echo "PID ad alanı içinde: $$ ; ps:"
  ps -e -o pid,ppid,comm | head -5
  for n in pid mnt uts user; do printf "%-7s %s\n" $n "$(readlink /proc/$$/ns/$n)"; done
  echo "--- UTS: hostname değiştir (yalnız içeride)"
  unshare -u hostname konteyner-demo 2>/dev/null || true
  echo "içeride: $(hostname)"
'
echo "host hostname: $(hostname)"
echo "== /proc/self/cgroup =="; cat /proc/self/cgroup
