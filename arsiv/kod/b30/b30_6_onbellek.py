# -*- coding: utf-8 -*-
"""b30_6_onbellek.py: ETag + Cache-Control ile LRU'lu HTTP onbellegi.

Bolum 16'daki LRU fikri (OrderedDict) kapasiteli bir onbellege
uygulanir. Kullanim: python b30_6_onbellek.py SUNUCU:PORT
"""
import http.client
import re
import sys
import time
from collections import OrderedDict


class HTTPOnbellek:
    def __init__(self, kapasite=2):
        self.kapasite = kapasite
        self.veri = OrderedDict()   # yol -> (etag, bitis, govde)
        self.sayac = {"ag": 0, "200": 0, "304": 0, "taze": 0}

    def al(self, sunucu, yol):
        simdi = time.monotonic()
        kayit = self.veri.get(yol)
        if kayit and simdi < kayit[1]:       # taze: aga cikma
            self.veri.move_to_end(yol)
            self.sayac["taze"] += 1
            return kayit[2]
        baslik = {}
        if kayit:                            # bayat: kosullu istek
            baslik["If-None-Match"] = kayit[0]
        conn = http.client.HTTPConnection(sunucu, timeout=5)
        conn.request("GET", yol, headers=baslik)
        r = conn.getresponse()
        govde = r.read()
        conn.close()
        self.sayac["ag"] += 1
        if r.status not in (200, 304):       # 404 onbellege girmez
            return govde
        if r.status == 304:                  # icerik degismemis
            self.sayac["304"] += 1
            etag, govde = kayit[0], kayit[2]
        else:
            self.sayac["200"] += 1
            etag = r.getheader("ETag")
        omur = 0
        m = re.search(r"max-age=(\d+)",
                      r.getheader("Cache-Control", ""))
        if m:
            omur = int(m.group(1))
        self.veri[yol] = (etag, simdi + omur, govde)
        self.veri.move_to_end(yol)
        while len(self.veri) > self.kapasite:   # en eskiyi at
            self.veri.popitem(last=False)
        return govde


if __name__ == "__main__":
    sunucu = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8080"
    oz = HTTPOnbellek(kapasite=2)
    oz.al(sunucu, "/index.html")
    print("1. ilk istek     ", oz.sayac)
    oz.al(sunucu, "/index.html")
    print("2. hemen tekrar  ", oz.sayac)
    e, _, g = oz.veri["/index.html"]
    oz.veri["/index.html"] = (e, 0, g)       # sureyi geriye cek
    oz.al(sunucu, "/index.html")
    print("3. bayat, 304    ", oz.sayac)
    oz.al(sunucu, "/ornek/not.txt")          # onbellek: index, not
    oz.al(sunucu, "/index.html")             # index tazelendi
    oz.al(sunucu, "/uc.txt")                 # 3. kayit: en eski duser
    print("   yollar:", list(oz.veri.keys()))
    oz.al(sunucu, "/ornek/not.txt")          # dusmustu: aga cikar
    print("4. LRU sonrasi   ", oz.sayac)
