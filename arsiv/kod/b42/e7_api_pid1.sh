#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b42/proje/api
PORT=18080 APP_VERSION=1.2.0 unshare -r -p -f --mount-proc python3 telemetri_api.py > /tmp/api_pid1.log 2>&1 &
sleep 1.5
HP=$(pgrep -n -f "python3 telemetri_api.py")
echo "host PID: $HP"
cat > /tmp/istemci.py <<'PY'
import json, urllib.request as u
print("health:", u.urlopen("http://127.0.0.1:18080/health").read().decode())
r = u.Request("http://127.0.0.1:18080/telemetri",
              data=json.dumps({"sira": 3, "irtifa_m": 1234.5}).encode())
print("telemetri:", u.urlopen(r).status)
try:
    u.urlopen(u.Request("http://127.0.0.1:18080/telemetri",
                        data=b'{"sira":"x"}'))
except u.HTTPError as e:
    print("gecersiz govde:", e.code)
PY
python3 /tmp/istemci.py
kill -TERM $HP; sleep 2
echo "SIGTERM sonrası hâlâ çalışıyor mu? $(kill -0 $HP 2>/dev/null && echo evet || echo hayir)"
echo "--- günlük:"; cat /tmp/api_pid1.log
