import json
import urllib.request as u

TABAN = "http://127.0.0.1:18080"
print("health:", u.urlopen(TABAN + "/health").read().decode())
yuk = json.dumps({"sira": 3, "irtifa_m": 1234.5}).encode()
r = u.Request(TABAN + "/telemetri", data=yuk)
print("telemetri:", u.urlopen(r).status)
try:
    u.urlopen(u.Request(TABAN + "/telemetri", data=b'{"sira":"x"}'))
except u.HTTPError as e:
    print("gecersiz govde:", e.code)
