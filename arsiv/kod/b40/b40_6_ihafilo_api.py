# -*- coding: utf-8 -*-
"""b40_6_ihafilo_api.py: Mini Iha filo REST API'si.

Kaynaklar: /ihalar, /ihalar/{id}, /ihalar/{id}/gorevler
Veri: sqlite3 (bellekte), Bolum 34'teki gibi tablolar.
"""

import hashlib
import json
import math
import sqlite3
import sys
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import jsonschema

from b40_4_kova import KovaSinirlayici

# Test anahtarlari: yalnizca bu bolumun yerel demosu icin.
# Gercek sistemde anahtarlar yapilandirmadan okunur (Bolum 32).
# anahtar -> (kullanici, kova kapasitesi, jeton/saniye)
ANAHTARLAR = {
    "k-ali": ("ali", 60, 10.0),
    "k-ayse": ("ayse", 60, 10.0),
    "k-hiz": ("hiz", 5, 0.5),  # hiz siniri icin dar kova
}
KOVALAR = {}  # kullanici -> KovaSinirlayici
GUNLUK = []  # her yanit icin bir JSON satiri

IHA_SEMA = {
    "type": "object",
    "required": ["ad", "tip"],
    "additionalProperties": False,
    "properties": {
        "ad": {
            "type": "string",
            "minLength": 2,
            "maxLength": 32,
            "pattern": "^[A-Za-z0-9-]+$",
        },
        "tip": {"enum": ["sabit_kanat", "dortrotor"]},
        "durum": {"enum": ["hazir", "ucuyor", "bakimda"]},
    },
}
GOREV_SEMA = {
    "type": "object",
    "required": ["hedef", "irtifa_m"],
    "additionalProperties": False,
    "properties": {
        "hedef": {"type": "string", "minLength": 1, "maxLength": 64},
        "irtifa_m": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5000,
        },
    },
}


def veritabani_kur():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""
        CREATE TABLE iha (
            id INTEGER PRIMARY KEY,
            sahip TEXT NOT NULL,
            ad TEXT NOT NULL,
            tip TEXT NOT NULL,
            durum TEXT NOT NULL,
            UNIQUE (sahip, ad)
        );
        CREATE TABLE gorev (
            id INTEGER PRIMARY KEY,
            iha_id INTEGER NOT NULL REFERENCES iha(id),
            hedef TEXT NOT NULL,
            irtifa_m INTEGER NOT NULL
        );
        CREATE TABLE idem (
            sahip TEXT NOT NULL,
            anahtar TEXT NOT NULL,
            ozet TEXT NOT NULL,
            konum TEXT NOT NULL,
            govde TEXT NOT NULL,
            PRIMARY KEY (sahip, anahtar)
        );
    """)
    return db


DB = veritabani_kur()


class Red(Exception):
    """Isleyiciyi erken bitirir; tasidigi sonuc yanit olarak gider."""

    def __init__(self, sonuc):
        super().__init__()
        self.sonuc = sonuc


def ok(durum, nesne=None, ek=None):
    return (durum, nesne, ek or {}, "application/json")


def hata(durum, baslik, ayrinti, ek=None, tip="about:blank", **alan):
    nesne = {
        "type": tip,
        "title": baslik,
        "status": durum,
        "detail": ayrinti,
    }
    nesne.update(alan)
    return (durum, nesne, ek or {}, "application/problem+json")


def izinli_degil(allow):
    return hata(
        405,
        "Yontem izinli degil",
        "desteklenmez",
        ek={"Allow": allow},
    )


def ozet(nesne):
    """Kanonik JSON'un parmak izi: ETag ve idempotentlik icin."""
    kanon = json.dumps(
        nesne,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(kanon.encode("utf-8")).hexdigest()[:16]


def etag(nesne):
    return '"%s"' % ozet(nesne)


def imlec_kodla(son_id):
    ham = json.dumps({"son": son_id}).encode("utf-8")
    return urlsafe_b64encode(ham).decode("ascii")


def imlec_coz(imlec):
    return json.loads(urlsafe_b64decode(imlec))["son"]


def govde_al(ham):
    try:
        nesne = json.loads(ham.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Red(hata(400, "Hatali JSON", str(e)))
    if not isinstance(nesne, dict):
        raise Red(
            hata(
                422,
                "Dogrulama hatasi",
                "nesne bekleniyordu",
                tip="/hatalar/dogrulama",
            )
        )
    return nesne


def dogrula(sema, nesne):
    hatalar = []
    for e in jsonschema.Draft202012Validator(sema).iter_errors(nesne):
        yol = "/".join(str(p) for p in e.path) or "(kok)"
        hatalar.append({"alan": yol, "mesaj": e.message})
    return sorted(hatalar, key=lambda h: (h["alan"], h["mesaj"]))


def dogrulama_hatasi(hatalar):
    return hata(
        422,
        "Dogrulama hatasi",
        "%d alan" % len(hatalar),
        tip="/hatalar/dogrulama",
        hatalar=hatalar,
    )


def iha_getir(kul, iha_id):
    """Sahiplik filtresi: baskasinin kaydi 'yok' gibi davranir."""
    satir = DB.execute(
        "SELECT ad, tip, durum FROM iha WHERE id = ? AND sahip = ?",
        (iha_id, kul),
    ).fetchone()
    if satir is None:
        return None
    return {
        "id": iha_id,
        "ad": satir[0],
        "tip": satir[1],
        "durum": satir[2],
    }


def ihalari_listele(kul, sorgu):
    try:
        boyut = min(int(sorgu.get("limit", ["2"])[0]), 50)
        imlec = sorgu.get("imlec", [None])[0]
        son = imlec_coz(imlec) if imlec else 0
    except (ValueError, KeyError, json.JSONDecodeError):
        return hata(400, "Gecersiz sorgu", "imlec ya da limit")
    rows = DB.execute(
        "SELECT id, ad, tip, durum FROM iha "
        "WHERE sahip = ? AND id > ? ORDER BY id ASC LIMIT ?",
        (kul, son, boyut + 1),
    ).fetchall()  # bir fazla: devam var mi?
    veri = [
        {
            "id": r[0],
            "ad": r[1],
            "tip": r[2],
            "durum": r[3],
            "href": "/ihalar/%d" % r[0],
        }
        for r in rows[:boyut]
    ]
    sonraki = None
    if len(rows) > boyut:
        sonraki = imlec_kodla(rows[boyut - 1][0])
    return ok(200, {"veri": veri, "sonraki_imlec": sonraki})


def ihalari_olustur(kul, govde, anahtar):
    hatalar = dogrula(IHA_SEMA, govde)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    ozeti = ozet(govde)
    if anahtar:
        eski = DB.execute(
            "SELECT ozet, konum, govde FROM idem "
            "WHERE sahip = ? AND anahtar = ?",
            (kul, anahtar),
        ).fetchone()
        if eski is not None:
            if eski[0] != ozeti:
                return hata(
                    422,
                    "Idempotency-Key yeniden kullanildi",
                    "farkli govde",
                )
            return ok(
                201,
                json.loads(eski[2]),
                ek={
                    "Location": eski[1],
                    "Idempotent-Replayed": "true",
                },
            )
    try:
        cur = DB.execute(
            "INSERT INTO iha (sahip, ad, tip, durum) "
            "VALUES (?, ?, ?, ?)",
            (
                kul,
                govde["ad"],
                govde["tip"],
                govde.get("durum", "hazir"),
            ),
        )
    except sqlite3.IntegrityError:
        return hata(409, "Cakisma", "bu ad zaten kayitli")
    nesne = iha_getir(kul, cur.lastrowid)
    konum = "/ihalar/%d" % nesne["id"]
    if anahtar:
        DB.execute(
            "INSERT INTO idem VALUES (?, ?, ?, ?, ?)",
            (kul, anahtar, ozeti, konum, json.dumps(nesne)),
        )
    DB.commit()
    return ok(201, nesne, ek={"Location": konum, "ETag": etag(nesne)})


def iha_goster(kul, iha_id):
    nesne = iha_getir(kul, iha_id)
    if nesne is None:
        return hata(404, "Bulunamadi", "iha yok")
    return ok(200, nesne, ek={"ETag": etag(nesne)})


def iha_guncelle(kul, iha_id, if_match, govde, kismi):
    mevcut = iha_getir(kul, iha_id)
    if mevcut is None:
        return hata(404, "Bulunamadi", "iha yok")
    if if_match is None:
        return hata(428, "Onkosul gerekli", "If-Match basligi yok")
    if if_match != etag(mevcut):
        return hata(
            412,
            "Onkosul basarisiz",
            "kayit degismis; once GET ile yeniden okuyun",
            ek={"ETag": etag(mevcut)},
        )
    if kismi:  # PATCH: yalnizca gonderilen alanlar
        yeni = {
            "ad": mevcut["ad"],
            "tip": mevcut["tip"],
            "durum": mevcut["durum"],
        }
        yeni.update(govde)
    else:  # PUT: tam nesne, eksik durum varsayilan
        yeni = {"durum": "hazir", **govde}
    hatalar = dogrula(IHA_SEMA, yeni)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    try:
        DB.execute(
            "UPDATE iha SET ad = ?, tip = ?, durum = ? "
            "WHERE id = ? AND sahip = ?",
            (yeni["ad"], yeni["tip"], yeni["durum"], iha_id, kul),
        )
    except sqlite3.IntegrityError:
        return hata(409, "Cakisma", "bu ad zaten kayitli")
    DB.commit()
    nesne = iha_getir(kul, iha_id)
    return ok(200, nesne, ek={"ETag": etag(nesne)})


def iha_sil(kul, iha_id, if_match):
    mevcut = iha_getir(kul, iha_id)
    if mevcut is None:
        return hata(404, "Bulunamadi", "iha yok")
    if if_match is None:
        return hata(428, "Onkosul gerekli", "If-Match basligi yok")
    if if_match != etag(mevcut):
        return hata(
            412,
            "Onkosul basarisiz",
            "kayit degismis",
            ek={"ETag": etag(mevcut)},
        )
    DB.execute("DELETE FROM gorev WHERE iha_id = ?", (iha_id,))
    DB.execute(
        "DELETE FROM iha WHERE id = ? AND sahip = ?", (iha_id, kul)
    )
    DB.commit()
    return ok(204)


def gorevleri_listele(kul, iha_id):
    if iha_getir(kul, iha_id) is None:
        return hata(404, "Bulunamadi", "iha yok")
    rows = DB.execute(
        "SELECT id, hedef, irtifa_m FROM gorev "
        "WHERE iha_id = ? ORDER BY id",
        (iha_id,),
    ).fetchall()
    veri = [
        {"id": r[0], "hedef": r[1], "irtifa_m": r[2]} for r in rows
    ]
    return ok(200, {"veri": veri})


def gorev_olustur(kul, iha_id, govde):
    if iha_getir(kul, iha_id) is None:
        return hata(404, "Bulunamadi", "iha yok")
    hatalar = dogrula(GOREV_SEMA, govde)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    cur = DB.execute(
        "INSERT INTO gorev (iha_id, hedef, irtifa_m) "
        "VALUES (?, ?, ?)",
        (iha_id, govde["hedef"], govde["irtifa_m"]),
    )
    DB.commit()
    konum = "/ihalar/%d/gorevler/%d" % (iha_id, cur.lastrowid)
    return ok(
        201, {"id": cur.lastrowid, **govde}, ek={"Location": konum}
    )


class Istek(BaseHTTPRequestHandler):
    server_version = "IHAFilo/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # varsayilan stderr logunu kapat

    def do_GET(self):
        self._isle()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    def _isle(self):
        self.istek_id = (
            self.headers.get("X-Request-ID") or uuid.uuid4().hex
        )
        uz = int(self.headers.get("Content-Length") or 0)
        if uz > 4096:
            self.close_connection = True  # govdeyi okumadan kapat
            return self._gonder(
                hata(413, "Govde cok buyuk", "en fazla 4096 bayt")
            )
        ham = self.rfile.read(uz) if uz else b""
        try:
            sonuc = self._yonlendir(ham)
        except Red as r:
            sonuc = r.sonuc
        self._gonder(sonuc)

    def _yonlendir(self, ham):
        kayit = ANAHTARLAR.get(self.headers.get("X-Api-Key") or "")
        if kayit is None:
            return hata(
                401,
                "Kimlik dogrulanamadi",
                "gecerli X-Api-Key gerekli",
                ek={"WWW-Authenticate": 'ApiKey realm="ihafilo"'},
            )
        kul, kapasite, hiz = kayit
        kova = KOVALAR.setdefault(kul, KovaSinirlayici(kapasite, hiz))
        izin, bekle = kova.izin_ver(time.monotonic())
        if not izin:
            return hata(
                429,
                "Cok fazla istek",
                "hiz siniri asildi",
                ek={"Retry-After": str(math.ceil(bekle))},
            )
        yol = urlparse(self.path)
        p = [s for s in yol.path.split("/") if s]
        q = parse_qs(yol.query)
        m = self.command
        if p == ["ihalar"]:
            if m == "GET":
                return ihalari_listele(kul, q)
            if m == "POST":
                return ihalari_olustur(
                    kul,
                    govde_al(ham),
                    self.headers.get("Idempotency-Key"),
                )
            return izinli_degil("GET, POST")
        if len(p) == 2 and p[0] == "ihalar" and p[1].isdigit():
            i = int(p[1])
            if m == "GET":
                return iha_goster(kul, i)
            if m in ("PUT", "PATCH"):
                return iha_guncelle(
                    kul,
                    i,
                    self.headers.get("If-Match"),
                    govde_al(ham),
                    m == "PATCH",
                )
            if m == "DELETE":
                return iha_sil(kul, i, self.headers.get("If-Match"))
            return izinli_degil("GET, PUT, PATCH, DELETE")
        if (
            len(p) == 3
            and p[0] == "ihalar"
            and p[1].isdigit()
            and p[2] == "gorevler"
        ):
            i = int(p[1])
            if m == "GET":
                return gorevleri_listele(kul, i)
            if m == "POST":
                return gorev_olustur(kul, i, govde_al(ham))
            return izinli_degil("GET, POST")
        return hata(
            404, "Bulunamadi", "yol tanimli degil: %s" % yol.path
        )

    def _gonder(self, sonuc):
        durum, nesne, ek, tur = sonuc
        govde = b""
        if nesne is not None:
            govde = json.dumps(nesne, ensure_ascii=False).encode(
                "utf-8"
            )
        self.send_response(durum)
        if govde:
            self.send_header("Content-Type", tur + "; charset=utf-8")
        if durum != 204:  # RFC 9110: 204'te Content-Length yok
            self.send_header("Content-Length", str(len(govde)))
        self.send_header("X-Request-ID", self.istek_id)
        for ad, deger in ek.items():
            self.send_header(ad, deger)
        self.end_headers()
        if govde:
            self.wfile.write(govde)
        GUNLUK.append(
            json.dumps(
                {
                    "olay": "istek",
                    "yontem": self.command,
                    "yol": self.path,
                    "durum": durum,
                    "istek_id": self.istek_id,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    HTTPServer(("127.0.0.1", port), Istek).serve_forever()
