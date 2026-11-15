# -*- coding: utf-8 -*-
"""Telemetri API'si: Bölüm 40'taki arayüzün bu bölümdeki karşılığı.

Yapılandırma ortamdan okunur (12 faktör). Yalnızca standart
kütüphane. Günlükler stdout'a JSON satırı olarak yazılır.
"""
import json
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SURUM = os.environ.get("APP_VERSION", "gelistirme")
PORT = int(os.environ.get("PORT", "8080"))

durum = {"kapaniyor": False, "kabul": 0}
kilit = threading.Lock()


def gunluk(olay, **alanlar):
    kayit = {"zaman": round(time.time(), 3), "olay": olay}
    kayit.update(alanlar)
    print(json.dumps(kayit, ensure_ascii=False), flush=True)


class Istekci(BaseHTTPRequestHandler):

    def _yanit(self, kod, govde):
        veri = json.dumps(govde, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        tur = "application/json; charset=utf-8"
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        if self.path == "/health":
            self._yanit(200, {"durum": "canli", "surum": SURUM})
        elif self.path == "/hazir":
            if durum["kapaniyor"]:
                self._yanit(503, {"durum": "kapaniyor"})
            else:
                self._yanit(200, {"durum": "hazir"})
        else:
            self._yanit(404, {"hata": "bulunamadi"})

    def do_POST(self):
        if self.path != "/telemetri":
            self._yanit(404, {"hata": "bulunamadi"})
            return
        uzunluk = int(self.headers.get("Content-Length", "0"))
        try:
            veri = json.loads(self.rfile.read(uzunluk))
            sira = int(veri["sira"])
            irtifa = float(veri["irtifa_m"])
        except (ValueError, KeyError, TypeError):
            self._yanit(400, {"hata": "geçersiz gövde"})
            return
        with kilit:
            durum["kabul"] += 1
        gunluk("kabul", sira=sira, irtifa_m=irtifa)
        self._yanit(201, {"kabul": True, "sira": sira})

    def log_message(self, format, *args):
        pass  # erişim satırları kapalı; kendi günlüğümüz var


def sunucu_olustur(port):
    srv = ThreadingHTTPServer(("0.0.0.0", port), Istekci)
    srv.daemon_threads = True
    return srv


def main():
    srv = sunucu_olustur(PORT)

    def kapat(sig, kare):
        durum["kapaniyor"] = True
        gunluk("sinyal", sinyal=signal.Signals(sig).name)
        # shutdown() serve_forever döngüsünü durdurur ve bitmesini
        # bekler. Ana iş parçacığından çağrılırsa kilitlenir; bu
        # yüzden ayrı bir iş parçacığında çağırıyoruz.
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, kapat)
    signal.signal(signal.SIGINT, kapat)
    gunluk("basladi", port=PORT, surum=SURUM)
    srv.serve_forever()
    srv.server_close()
    gunluk("kapandi", kabul=durum["kabul"])


if __name__ == "__main__":
    main()
