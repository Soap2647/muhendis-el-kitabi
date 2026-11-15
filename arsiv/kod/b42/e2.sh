#!/bin/bash
D=/mnt/c/Users/merty/AppData/Local/Temp/b42
cd $D
gcc -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L sinyal_pid1.c -o sinyal_pid1 || exit 1
echo "== E2a: UTS (kendi ad alanında hostname) =="
unshare -r -u sh -c 'hostname konteyner-demo; echo "içeride: $(hostname)"'
echo "dışarıda: $(hostname)"
echo "== E2b: PID 1 SIGTERM (işleyici YOK) =="
unshare -r -p -f --mount-proc ./sinyal_pid1 yok > pid1_yok.log 2>&1 &
sleep 1
# dış kabuktan PID ad alanındaki 1 numaralı süreci bulmak için pid ad alanı içinden kill gerekir:
# ad alanı dışından görünen PID'i bul (en son çocuk olan sinyal_pid1)
HOSTPID=$(pgrep -n sinyal_pid1); echo "host'tan görünen PID: $HOSTPID"
kill -TERM $HOSTPID; sleep 2
echo "SIGTERM sonrası: $(ps -o stat=,comm= -p $HOSTPID 2>/dev/null || echo 'süreç hâlâ var değil')"
cat pid1_yok.log
kill -KILL $HOSTPID 2>/dev/null; sleep 1
echo "== E2c: PID 1 SIGTERM (işleyici VAR) =="
unshare -r -p -f --mount-proc ./sinyal_pid1 var > pid1_var.log 2>&1 &
sleep 1; HOSTPID=$(pgrep -n sinyal_pid1); kill -TERM $HOSTPID; sleep 2
cat pid1_var.log
