# -*- coding: utf-8 -*-
import json
import threading
import unittest
import urllib.error
import urllib.request

import telemetri_api as api


class ApiTest(unittest.TestCase):

    def setUp(self):
        api.durum.update(kapaniyor=False, kabul=0)
        # 0 numaralı port: işletim sistemi boş bir port seçer
        self.srv = api.sunucu_olustur(0)
        port = self.srv.server_address[1]
        self.taban = "http://127.0.0.1:%d" % port
        sunucu = threading.Thread(target=self.srv.serve_forever,
                                  daemon=True)
        sunucu.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def istek(self, yol, govde=None):
        veri = None if govde is None else json.dumps(govde).encode()
        req = urllib.request.Request(self.taban + yol, data=veri)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_saglik(self):
        kod, govde = self.istek("/health")
        self.assertEqual((kod, govde["durum"]), (200, "canli"))

    def test_telemetri_kabul(self):
        yuk = {"sira": 7, "irtifa_m": 120.5}
        kod, _ = self.istek("/telemetri", yuk)
        self.assertEqual(kod, 201)
        self.assertEqual(api.durum["kabul"], 1)

    def test_gecersiz_govde(self):
        kod, _ = self.istek("/telemetri", {"sira": "yok"})
        self.assertEqual(kod, 400)
        self.assertEqual(api.durum["kabul"], 0)

    def test_kapanirken_hazir_degil(self):
        api.durum["kapaniyor"] = True
        kod, govde = self.istek("/hazir")
        self.assertEqual((kod, govde["durum"]), (503, "kapaniyor"))

    def test_bilinmeyen_yol(self):
        kod, _ = self.istek("/yok")
        self.assertEqual(kod, 404)


if __name__ == "__main__":
    unittest.main()
