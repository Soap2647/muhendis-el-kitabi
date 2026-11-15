# -*- coding: utf-8 -*-
"""b40_7_istemci.py: API'yi gercek HTTP istekleriyle sinar.

Sunucu ayni surecte bir is parcacigi olarak, 127.0.0.1 uzerinde,
gecici bir portta calisir. Her adim bir HTTP istegidir (urllib).
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import b40_6_ihafilo_api as api

TABAN = ""
SAYAC = [0]


def istek(
    yontem, yol, anahtar="k-ali", govde=None, ham=None, ek=None
):
    basliklar = {"X-Api-Key": anahtar} if anahtar else {}
    SAYAC[0] += 1
    basliklar["X-Request-ID"] = "t%03d" % SAYAC[0]
    veri = ham
    if govde is not None:
        veri = json.dumps(govde).encode("utf-8")
    if veri is not None:
        basliklar["Content-Type"] = "application/json"
    basliklar.update(ek or {})
    req = urllib.request.Request(
        TABAN + yol, data=veri, method=yontem, headers=basliklar
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return (
                r.status,
                {k.lower(): v for k, v in r.headers.items()},
                r.read(),
            )
    except urllib.error.HTTPError as e:
        return (
            e.code,
            {k.lower(): v for k, v in e.headers.items()},
            e.read(),
        )


def goster(ad, sonuc):
    durum, basl, govde = sonuc
    print("%-28s %d" % (ad, durum))
    ilgili = []
    for alan, ad_ in (
        ("location", "Location"),
        ("etag", "ETag"),
        ("retry-after", "Retry-After"),
        ("allow", "Allow"),
        ("www-authenticate", "WWW-Authenticate"),
        ("idempotent-replayed", "Idempotent-Replayed"),
    ):
        if alan in basl:
            ilgili.append("%s=%s" % (ad_, basl[alan]))
    if ilgili:
        print("      " + " ".join(ilgili))
    if durum >= 400 and govde:
        p = json.loads(govde)
        print("      %s: %s" % (p["title"], p["detail"]))
        for h in p.get("hatalar", []):
            print("      - %s: %s" % (h["alan"], h["mesaj"]))


def json_al(sonuc):
    return json.loads(sonuc[2]) if sonuc[2] else None


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 0), api.Istek)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    TABAN = "http://127.0.0.1:%d" % srv.server_address[1]

    print("1. Idempotent olusturma")
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "ALFA-1", "tip": "sabit_kanat"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST /ihalar", s)
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "ALFA-1", "tip": "sabit_kanat"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST /ihalar (ayni anahtar)", s)
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "BETA-2", "tip": "dortrotor"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST (anahtar, farkli govde)", s)
    print(
        "   kayit sayisi:",
        len(api.DB.execute("SELECT * FROM iha").fetchall()),
    )

    print("2. Girdi hatalari")
    goster(
        "POST gecersiz alanlar",
        istek(
            "POST", "/ihalar", govde={"ad": "X", "tip": "helikopter"}
        ),
    )
    goster(
        "POST bozuk JSON", istek("POST", "/ihalar", ham=b'{"ad": ')
    )
    goster(
        "POST ayni ad (409)",
        istek(
            "POST",
            "/ihalar",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ),
    )

    print("3. Kosullu guncelleme (ETag)")
    s = istek("GET", "/ihalar/1")
    goster("GET /ihalar/1", s)
    e1 = s[1]["etag"]
    goster(
        "PUT If-Match yok",
        istek(
            "PUT",
            "/ihalar/1",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ),
    )
    goster(
        "PUT yanlis If-Match",
        istek(
            "PUT",
            "/ihalar/1",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
            ek={"If-Match": '"0000000000000000"'},
        ),
    )
    s = istek(
        "PUT",
        "/ihalar/1",
        govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ek={"If-Match": e1},
    )
    goster("PUT dogru If-Match", s)
    e2 = s[1]["etag"]
    goster(
        "PATCH eski ETag",
        istek(
            "PATCH",
            "/ihalar/1",
            govde={"durum": "ucuyor"},
            ek={"If-Match": e1},
        ),
    )
    goster(
        "PATCH guncel ETag",
        istek(
            "PATCH",
            "/ihalar/1",
            govde={"durum": "ucuyor"},
            ek={"If-Match": e2},
        ),
    )
    e3 = istek("GET", "/ihalar/1")[1]["etag"]

    print("4. Sahiplik: ayse, ali'nin kaydina erisemez")
    goster(
        "GET /ihalar/1 (ayse)", istek("GET", "/ihalar/1", "k-ayse")
    )
    goster(
        "DELETE /ihalar/1 (ayse)",
        istek("DELETE", "/ihalar/1", "k-ayse", ek={"If-Match": e3}),
    )

    print("5. Imlecli sayfalama (limit=2)")
    for ad in ("BRAVO-3", "CHARLIE-4", "DELTA-5"):
        istek(
            "POST", "/ihalar", govde={"ad": ad, "tip": "sabit_kanat"}
        )
    s = istek("GET", "/ihalar?limit=2")
    sayfa1 = json_al(s)
    print("   sayfa 1:", [v["ad"] for v in sayfa1["veri"]])
    s = istek(
        "GET", "/ihalar?limit=2&imlec=" + sayfa1["sonraki_imlec"]
    )
    sayfa2 = json_al(s)
    print(
        "   sayfa 2:",
        [v["ad"] for v in sayfa2["veri"]],
        "sonraki:",
        sayfa2["sonraki_imlec"],
    )

    print("6. Alt kaynak ve yontem")
    s = istek(
        "POST",
        "/ihalar/1/gorevler",
        govde={"hedef": "sinir-hatti-A", "irtifa_m": 120},
    )
    goster("POST /ihalar/1/gorevler", s)
    goster(
        "GET  /ihalar/1/gorevler", istek("GET", "/ihalar/1/gorevler")
    )
    goster(
        "PUT  /ihalar (koleksiyon)", istek("PUT", "/ihalar", govde={})
    )
    goster(
        "POST 5000 bayt govde",
        istek("POST", "/ihalar", ham=b"x" * 5000),
    )

    print("7. Hiz siniri (kapasite 5, 0,5 jeton/s)")
    for _ in range(7):
        s = istek("GET", "/ihalar", "k-hiz")
        goster("GET /ihalar (hiz)", s)

    print("8. Kimliksiz istek ve silme")
    goster(
        "GET /ihalar (anahtarsiz)",
        istek("GET", "/ihalar", anahtar=None),
    )
    goster(
        "DELETE /ihalar/1 (ali)",
        istek("DELETE", "/ihalar/1", ek={"If-Match": e3}),
    )
    goster("GET /ihalar/1 (silindi)", istek("GET", "/ihalar/1"))

    srv.shutdown()
    print("9. Gunluk son satirlar")
    for satir in api.GUNLUK[-2:]:
        k = json.loads(satir)
        print(
            "  %s %s -> %d (istek_id=%s)"
            % (k["yontem"], k["yol"], k["durum"], k["istek_id"])
        )
