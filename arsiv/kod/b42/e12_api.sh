#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b42
cd proje/api
PORT=18080 APP_VERSION=1.2.0 unshare -r -p -f --mount-proc python3 telemetri_api.py > /tmp/api_pid1.log 2>&1 &
sleep 1.5
HP=$(pgrep -n -f "python3 telemetri_api.py")
echo "\$ python3 istemci.py"
python3 /mnt/c/Users/merty/AppData/Local/Temp/b42/istemci.py
echo "\$ kill -TERM <ana makine PID'i>"
kill -TERM $HP; sleep 2
echo "SIGTERM sonrasi hayatta mi: $(kill -0 $HP 2>/dev/null && echo evet || echo hayir)"
echo "\$ cat /tmp/api_pid1.log"; cat /tmp/api_pid1.log
