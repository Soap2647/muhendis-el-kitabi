# -*- coding: utf-8 -*-
# saglik.py: HEALTHCHECK için. Çıkış kodu 0 sağlıklı, 1 sağlıksız.
import sys
import urllib.request

URL = "http://127.0.0.1:8080/health"
try:
    r = urllib.request.urlopen(URL, timeout=1)
    sys.exit(0 if r.status == 200 else 1)
except OSError:
    sys.exit(1)
