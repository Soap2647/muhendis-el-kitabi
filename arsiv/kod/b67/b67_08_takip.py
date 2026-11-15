# -*- coding: utf-8 -*-
# b67_08_takip.py: tespit-ile-takip (tracking-by-detection).
# Sabit hiz Kalman (kutu durumu), veri iliskilendirme (acgozlu ve
# Macar), iz yasam dongusu, ByteTrack tarzi iki asamali eslestirme,
# MOTA ve kimlik degisimi (IDSW) olcumu. Sentetik videolar.
import os
import itertools
import numpy as np
from scipy.optimize import linear_sum_assignment
from b67_01_iou_nms import iou_matris, xyxy_to_xywh, xywh_to_xyxy
from b67_veri import video

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
F = np.eye(6)
F[0, 4] = F[1, 5] = 1.0          # cx += vx, cy += vy (dt = 1 kare)
H = np.zeros((4, 6))
H[0, 0] = H[1, 1] = H[2, 2] = H[3, 3] = 1.0
Q = np.diag([0.05, 0.05, 0.01, 0.01, 0.05, 0.05])
R = np.diag([2.25, 2.25, 1.0, 1.0]) * 1.5


class Iz:
    """Tek bir iz: Kalman durumu, sayaclar ve kimlik."""

    def __init__(self, kimlik, kutu):
        cx, cy, w, h = xyxy_to_xywh(kutu[None])[0]
        self.id = kimlik
        self.x = np.array([cx, cy, w, h, 0.0, 0.0])
        self.P = np.diag([10.0, 10.0, 10.0, 10.0, 100.0, 100.0])
        self.hits = 1
        self.kacirma = 0          # son ardisik karede eslesmedi mi

    def tahmin(self):
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def guncelle(self, kutu):
        cx, cy, w, h = xyxy_to_xywh(kutu[None])[0]
        z = np.array([cx, cy, w, h])
        y = z - H @ self.x                       # inovasyon
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)      # Kalman kazanci
        self.x = self.x + K @ y
        self.P = (np.eye(6) - K @ H) @ self.P
        self.hits += 1
        self.kacirma = 0

    def kutu(self):
        return xywh_to_xyxy(self.x[None, :4])[0]


def acgozlu_eslestir(maliyet, esik_gecer):
    """Her adimda en yuksek skorlu cifti secer (benzerlik icin)."""
    cift, kul_t, kul_d = [], set(), set()
    pairs = sorted(
        [(maliyet[i, j], i, j) for i in range(maliyet.shape[0])
         for j in range(maliyet.shape[1]) if esik_gecer[i, j]],
        reverse=True)
    for s, i, j in pairs:
        if i in kul_t or j in kul_d:
            continue
        cift.append((i, j))
        kul_t.add(i)
        kul_d.add(j)
    return cift


def macar_eslestir(maliyet, esik_gecer):
    """Toplam maliyeti en az olan tam eslestirme
    (linear_sum_assignment). Gecersiz ciftler cezalandirilir."""
    buyuk = 1e6
    c = np.where(esik_gecer, -maliyet, buyuk)
    satir, sutun = linear_sum_assignment(c)
    return [(i, j) for i, j in zip(satir, sutun) if esik_gecer[i, j]]


class Izleyici:
    """mod:
       'acgozlu_iou' : yalnizca yuksek skorlu tespit, acgozlu IoU
       'macar_iou'   : yalnizca yuksek skorlu tespit, Macar IoU (SORT)
       'macar_mesafe': yalnizca yuksek skorlu tespit, Macar, merkez
       'macar_tum'   : tum tespitler (skor esigi yok), Macar IoU
       'byte'        : yuksek skor + ikinci asama, dusuk skorlu tespit
    """

    def __init__(self, mod, esik_yuksek=0.5, esik_dusuk=0.1,
                 iou_esik=0.3, mesafe_esik=20.0, min_hits=3,
                 max_age=10):
        self.mod = mod
        self.esik_yuksek = esik_yuksek
        self.esik_dusuk = esik_dusuk
        self.iou_esik = iou_esik
        self.mesafe_esik = mesafe_esik
        self.min_hits = min_hits
        self.max_age = max_age
        self.izler = []
        self.sayac = 0

    def _yeni(self, kutu):
        self.sayac += 1
        self.izler.append(Iz(self.sayac, kutu))

    def _esle(self, izler, kutular, metrik, yontem):
        if len(izler) == 0 or len(kutular) == 0:
            return []
        tk = np.array([t.kutu() for t in izler])
        if metrik == "iou":
            iou = iou_matris(tk, kutular)
            gecer = iou >= self.iou_esik
            maliyet = iou
        else:
            ca = tk[:, :2] + (tk[:, 2:] - tk[:, :2]) / 2
            cd = kutular[:, :2] + \
                (kutular[:, 2:] - kutular[:, :2]) / 2
            d = np.linalg.norm(ca[:, None] - cd[None], axis=2)
            gecer = d <= self.mesafe_esik
            maliyet = -d
        if yontem == "acgozlu":
            return acgozlu_eslestir(maliyet, gecer)
        return macar_eslestir(maliyet, gecer)

    def guncelle(self, kutular, skorlar):
        for t in self.izler:
            t.tahmin()
            t.kacirma += 1
        kutular = np.asarray(kutular, float).reshape(-1, 4)
        skorlar = np.asarray(skorlar, float)
        yuksek = np.where(skorlar >= self.esik_yuksek)[0]
        dusuk = np.where((skorlar >= self.esik_dusuk) &
                         (skorlar < self.esik_yuksek))[0]
        if self.mod == "macar_tum":
            asama1 = np.where(skorlar >= self.esik_dusuk)[0]
        else:
            asama1 = yuksek
        yontem = "acgozlu" if self.mod == "acgozlu_iou" else "macar"
        metrik = "mesafe" if self.mod == "macar_mesafe" else "iou"
        eslesen_iz = set()
        eslesen_det = set()
        cift = self._esle(self.izler, kutular[asama1], metrik, yontem)
        for i, j in cift:
            d = asama1[j]
            self.izler[i].guncelle(kutular[d])
            eslesen_iz.add(i)
            eslesen_det.add(d)
        if self.mod == "byte":
            kalan = [i for i in range(len(self.izler))
                     if i not in eslesen_iz]
            cift2 = self._esle([self.izler[i] for i in kalan],
                               kutular[dusuk], "iou", "macar")
            for a, j in cift2:
                i = kalan[a]
                d = dusuk[j]
                self.izler[i].guncelle(kutular[d])
                eslesen_iz.add(i)
        for j in asama1:
            if j not in eslesen_det:
                self._yeni(kutular[j])
        # onaylanmamis iz (hits < min_hits) bir kare bile kacirirsa
        # silinir; onaylanmis iz max_age kareye kadar yasar
        self.izler = [
            t for t in self.izler
            if (t.hits < self.min_hits and t.kacirma == 0)
            or (t.hits >= self.min_hits
                and t.kacirma <= self.max_age)]
        return [(t.id, t.kutu()) for t in self.izler
                if t.hits >= self.min_hits
                and t.kacirma <= self.max_age]


def mota(cikti, kareler):
    """CLEAR MOT tarzi: IoU >= 0.5 ile kare basina Macar eslestirmesi.
    Donus: MOTA, FN, FP, IDSW ve eslesen GT -> iz kimligi kaydi."""
    fn = fp = idsw = toplam = 0
    son = {}
    kayit = []
    for (izler, kare) in zip(cikti, kareler):
        gk = np.array(kare["gt"], float).reshape(-1, 4)
        gid = kare["gt_id"]
        toplam += len(gk)
        if len(izler) == 0 or len(gk) == 0:
            fn += len(gk)
            fp += len(izler)
            kayit.append({})
            continue
        ik = np.array([b for _, b in izler])
        iid = [i for i, _ in izler]
        iou = iou_matris(gk, ik)
        gecer = iou >= 0.5
        c = np.where(gecer, -iou, 1e6)
        satir, sutun = linear_sum_assignment(c)
        eslesmis = {}
        for r, s in zip(satir, sutun):
            if gecer[r, s]:
                eslesmis[r] = iid[s]
        fn += len(gk) - len(eslesmis)
        fp += len(izler) - len(eslesmis)
        for r, tid in eslesmis.items():
            g = gid[r]
            if g in son and son[g] != tid:
                idsw += 1
            son[g] = tid
        kayit.append({gid[r]: t for r, t in eslesmis.items()})
    mota_d = 1 - (fn + fp + idsw) / max(toplam, 1)
    return mota_d, fn, fp, idsw, kayit


def macar_kontrol(n_deneme=300):
    """Macar cozumu kaba kuvvet (permütasyon) ile ayni toplam maliyeti
    veriyor mu?"""
    rng = np.random.default_rng(5)
    uyusan = 0
    for _ in range(n_deneme):
        m = rng.uniform(0, 1, (4, 4))
        s, t = linear_sum_assignment(m)
        en_iyi = min(sum(m[i, p[i]] for i in range(4))
                     for p in itertools.permutations(range(4)))
        uyusan += int(abs(m[s, t].sum() - en_iyi) < 1e-12)
    print("Macar = kaba kuvvet (4x4, %d deneme): %d uyumlu"
          % (n_deneme, uyusan))


def acgozlu_ornek():
    """Acgozlu eslestirmenin Macar'dan kotu oldugu bir durum."""
    # satir: iz, sutun: tespit
    m = np.array([[0.9, 0.8], [0.85, 0.1]])
    gecer = np.ones((2, 2), bool)
    print("acgozlu toplam =", round(sum(
        m[i, j] for i, j in acgozlu_eslestir(m, gecer)), 3),
        "| Macar toplam =", round(sum(
        m[i, j] for i, j in macar_eslestir(m, gecer)), 3))


MODLAR = ["acgozlu_iou", "macar_iou", "macar_mesafe", "macar_tum",
          "byte"]


def degerlendir(sayi=20):
    sonuc = {m: [] for m in MODLAR}
    for seed in range(100, 100 + sayi):
        kareler = video(seed)
        for mod in MODLAR:
            izci = Izleyici(mod)
            cikti = []
            for k in kareler:
                cikti.append(izci.guncelle(k["det"], k["skor"]))
            sonuc[mod].append(mota(cikti, kareler)[:4])
    return sonuc


if __name__ == "__main__":
    macar_kontrol()
    acgozlu_ornek()
    print("\n== Iz ilişkilendirme karşılaştırması (20 video) ==")
    sonuc = degerlendir(20)
    satirlar = ["yontem,mota_ort,mota_ss,idsw_ort,fn_ort,fp_ort"]
    for mod in MODLAR:
        a = np.array(sonuc[mod], float)
        print("%-13s MOTA=%.3f +- %.3f  IDSW=%.1f  FN=%.1f  FP=%.1f"
              % (mod, a[:, 0].mean(), a[:, 0].std(ddof=1),
                 a[:, 3].mean(), a[:, 1].mean(), a[:, 2].mean()))
        satirlar.append("%s,%.4f,%.4f,%.2f,%.2f,%.2f" % (
            mod, a[:, 0].mean(), a[:, 0].std(ddof=1),
            a[:, 3].mean(), a[:, 1].mean(), a[:, 2].mean()))
    with open(os.path.join(VERI, "b67_takip_karsilastirma.csv"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
