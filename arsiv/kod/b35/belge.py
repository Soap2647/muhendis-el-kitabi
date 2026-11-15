# -*- coding: utf-8 -*-
"""Belge modeli: gömme ile sorgu ve şema evrimi (Bölüm 35.9).
SQLite JSON1 fonksiyonları (json_extract, json_each) kullanılır.
Bu makinedeki SQLite sürümü: sqlite3.sqlite_version."""
import json
import sqlite3


def kur():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE musteri (id INTEGER PRIMARY KEY, "
              "veri TEXT)")
    belgeler = [
        {"ad": "Ali", "sehir": "Ankara", "siparisler": [
            {"no": 1, "tutar": 250.0, "urun": "sensör"},
            {"no": 2, "tutar": 1200.0, "urun": "kart"}]},
        {"ad": "Ayşe", "telefon": "0555", "siparisler": [
            {"no": 3, "tutar": 80.0, "urun": "kablo"}]},
        {"ad": "Mert", "sehir": "İzmir", "siparisler": []},
        {"ad": "Can", "sehir": "Ankara", "siparisler": [
            {"no": 4, "tutar": 80.0, "urun": "kablo"}]},
    ]
    for i, b in enumerate(belgeler, 1):
        c.execute("INSERT INTO musteri VALUES (?, ?)",
                  (i, json.dumps(b, ensure_ascii=False)))
    return c


if __name__ == "__main__":
    print("SQLite sürümü:", sqlite3.sqlite_version)
    c = kur()
    print("\n-- 1. Alan okuma (şema yok, yol ifadesi var)")
    for ad, sehir in c.execute(
            "SELECT json_extract(veri,'$.ad'), "
            "json_extract(veri,'$.sehir') FROM musteri ORDER BY id"):
        print("%-6s sehir=%s" % (ad, sehir))
    print("\n-- 2. Tutarı 1000'i aşan siparişi olan müşteriler")
    for (ad,) in c.execute(
            "SELECT json_extract(m.veri,'$.ad') FROM musteri m, "
            "json_each(m.veri,'$.siparisler') s "
            "WHERE json_extract(s.value,'$.tutar') > 1000"):
        print(ad)
    print("\n-- 3. Şema evrimi: eksik alan NULL döner, hata vermez")
    for ad, tel in c.execute(
            "SELECT json_extract(veri,'$.ad'), "
            "json_extract(veri,'$.telefon') FROM musteri "
            "ORDER BY id"):
        print("%-6s telefon=%s" % (ad, tel))
    print("\n-- 4. Gömülü veride aynı ürünü içeren belge "
          "sayısı")
    n = c.execute("SELECT COUNT(*) FROM musteri m, "
                  "json_each(m.veri,'$.siparisler') s WHERE "
                  "json_extract(s.value,'$.urun') = "
                  "'kablo'").fetchone()[0]
    print("'kablo' geçen sipariş sayısı:", n)
    print("Ürün adı değişirse güncellenecek belge (gömülü): "
          "%d" % n)
    print("Aynı ürün ayrı bir 'urun' tablosunda olsaydı: "
          "1 satır")
