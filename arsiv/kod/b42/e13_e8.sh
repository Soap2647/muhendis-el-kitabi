#!/bin/bash
unshare -r -p -f --mount-proc python3 -c 'import time,os; print("pid", os.getpid(), flush=True); time.sleep(3); print("bitti", flush=True)' > /tmp/e13.log 2>&1 &
sleep 1; HP=$(pgrep -n -f "time.sleep")
echo "\$ kill -TERM <ana makine PID'i>"; kill -TERM $HP; sleep 1
echo "SIGTERM sonrasi hayatta mi: $(kill -0 $HP 2>/dev/null && echo evet || echo hayir)"
sleep 3; echo "\$ cat /tmp/e13.log"; cat /tmp/e13.log
