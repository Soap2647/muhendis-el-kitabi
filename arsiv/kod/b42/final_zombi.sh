#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b42
echo "--- zombi (PID 1 Python toplamaz):"
unshare -r -p -f --mount-proc python3 zombi_snippet.py
echo "--- tek tikte tersi: bir sh orneği"
echo "--- e8 (işleyicisiz Python PID 1):"
unshare -r -p -f --mount-proc python3 -c 'import time,os; print("pid", os.getpid(), flush=True); time.sleep(3); print("bitti", flush=True)' > /tmp/e8b.log 2>&1 &
sleep 1; HP=$(pgrep -n -f "time.sleep"); kill -TERM $HP; sleep 1
echo "SIGTERM sonrasi hayatta mi: $(kill -0 $HP 2>/dev/null && echo evet || echo hayir)"; sleep 3; cat /tmp/e8b.log
