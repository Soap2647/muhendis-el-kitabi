# -*- coding: utf-8 -*-
# b67_02_ap.py: TP/FP eslestirme, PR egrisi, AP (11 nokta, 101 nokta,
# tum noktalar) ve mAP@0.5, mAP@[0.5:0.95]. Elle hesaplanmis ornek
# ve sayisal integral ile dogrulama.
import numpy as np
from b67_01_iou_nms import iou_matris
from b67_veri import veri_seti


def eslestir(tahmin, gt, esik):
    """Tek gorsel, tek sinif. tahmin: (K,4) skor sirasina gore azalan.
    Her tahmin, eslesmemis en yuksek IoU'lu gercek kutuyla eslesir
    (IoU >= esik). Eslesme yoksa FP. Her gercek kutu en fazla bir
    kez eslesir."""
    tp = np.zeros(len(tahmin), dtype=bool)
    if len(tahmin) == 0 or len(gt) == 0:
        return tp
    iou = iou_matris(tahmin, gt)
    kullanildi = np.zeros(len(gt), dtype=bool)
    for k in range(len(tahmin)):
        aday = np.where(~kullanildi, iou[k], -1.0)
        j = int(np.argmax(aday))
        if aday[j] >= esik:
            tp[k] = True
            kullanildi[j] = True
    return tp


def pr_egrisi(skor, tp, n_gt):
    """Skora gore azalan sirada kumulatif precision ve recall."""
    sira = np.argsort(-skor, kind="stable")
    tp = tp[sira].astype(np.float64)
    dogru = np.cumsum(tp)
    yanlis = np.cumsum(1 - tp)
    precision = dogru / np.maximum(dogru + yanlis, 1e-12)
    recall = dogru / max(n_gt, 1)
    return precision, recall


def ap_hesapla(skor, tp, n_gt, yontem="tum"):
    """AP. yontem: '11' (VOC2007), '101' (COCO tarzi), 'tum'
    (VOC2010+)."""
    p, r = pr_egrisi(skor, tp, n_gt)
    if len(p) == 0:
        return 0.0
    if yontem in ("11", "101"):
        noktalar = (np.linspace(0, 1, 11) if yontem == "11"
                    else np.linspace(0, 1, 101))
        toplam = 0.0
        for rt in noktalar:
            uygun = p[r >= rt - 1e-9]  # kayan nokta toleransi
            toplam += uygun.max() if uygun.size else 0.0
        return toplam / len(noktalar)
    # tum noktalar: precision zarfi (artan kisim) x recall adimi
    mrec = np.concatenate([[0.0], r, [r[-1]]])
    mpre = np.concatenate([[0.0], p, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    i = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1]))


def map_hesapla(tahminler, gtler, esik, yontem="tum"):
    """tahminler/gtler: gorsel listesi; her biri (kutular, skorlar,
    sinif) ve (kutular, sinif). Donus: (sinif basina AP, ortalama)."""
    siniflar = sorted({int(c) for _, _, cl in tahminler for c in cl} |
                      {int(c) for _, cl in gtler for c in cl})
    aplar = []
    for s in siniflar:
        skor_l, tp_l, ngt = [], [], 0
        for (tk, ts, tc), (gk, gc) in zip(tahminler, gtler):
            mt = tc == s
            mg = gc == s
            ngt += int(mg.sum())
            kutu = tk[mt]
            puan = ts[mt]
            sira = np.argsort(-puan, kind="stable")
            kutu, puan = kutu[sira], puan[sira]
            tp = eslestir(kutu, gk[mg], esik)
            skor_l.append(puan)
            tp_l.append(tp)
        skor = np.concatenate(skor_l) if skor_l else np.zeros(0)
        tp = np.concatenate(tp_l) if tp_l else np.zeros(0, bool)
        aplar.append(ap_hesapla(skor, tp, ngt, yontem))
    return aplar, float(np.mean(aplar))


def el_ile_ornek():
    print("== Elle hesaplanmis ornek (5 tahmin, 4 gercek kutu) ==")
    skor = np.array([0.95, 0.90, 0.85, 0.70, 0.60])
    tp = np.array([1, 0, 1, 1, 0], dtype=bool)
    p, r = pr_egrisi(skor, tp, 4)
    for k in range(5):
        print("tahmin %d: skor=%.2f TP=%d  P=%.4f  R=%.4f"
              % (k + 1, skor[k], tp[k], p[k], r[k]))
    print("AP (11 nokta)   = %.4f" % ap_hesapla(skor, tp, 4, "11"))
    print("AP (tum)        = %.4f" % ap_hesapla(skor, tp, 4, "tum"))
    # Zarfsiz, basamakli toplam (zarf yok): sadece karsilastirma
    basamak = np.sum(np.diff(np.concatenate([[0], r])) * p)
    print("zarfsiz basamak = %.4f  (zarf yok, daha dusuk)" % basamak)


def sayisal_dogrulama():
    print("\n== Sayisal integral dogrulamasi (rastgele, tohum 3) ==")
    rng = np.random.default_rng(3)
    hata = 0.0
    for _ in range(50):
        n = int(rng.integers(5, 60))
        skor = rng.uniform(0, 1, n)
        tp = rng.uniform(0, 1, n) < 0.5
        ngt = int(tp.sum() + rng.integers(0, 10))
        ap = ap_hesapla(skor, tp, ngt, "tum")
        p, r = pr_egrisi(skor, tp, ngt)
        # zarf: her r icin max{P_k : R_k >= r}; sayisal integral
        izgara = np.linspace(0, 1, 100001)[:-1] + 0.5 / 100000
        zarf = np.zeros_like(izgara)
        for k in range(len(r) - 1, -1, -1):
            maske = izgara <= r[k]
            zarf[maske] = np.maximum(zarf[maske], p[k])
        sayi = zarf.mean()
        hata = max(hata, abs(sayi - ap))
    print("maks |AP_adim - AP_integral| = %.2e" % hata)


def coco_tarzi_map(tahminler, gtler):
    esikler = np.arange(0.5, 0.96, 0.05)
    degerler = []
    for e in esikler:
        _, m = map_hesapla(tahminler, gtler, e, "101")
        degerler.append(m)
    return float(np.mean(degerler)), degerler


def gurultu_deneyi():
    print("\n== Kutu gurultusu arttikca mAP (300 gorsel) ==")
    _, Y, _ = veri_seti(300, seed=2024)
    rng = np.random.default_rng(7)
    for sigma in (0.0, 2.0, 5.0):
        tah, gtl = [], []
        for objs in Y:
            gk = np.array([o["box"] for o in objs],
                          float).reshape(-1, 4)
            gc = np.array([o["cls"] for o in objs], int)
            gtl.append((gk, gc))
            kutu = gk + rng.normal(0, sigma, gk.shape)
            puan = rng.uniform(0.5, 1.0, len(gk))
            # her goruntuye 1 sahte kutu (gurultulu) ekle
            sahte = np.array([[5, 5, 20, 20.0]]) + rng.uniform(0, 60)
            kutu = np.vstack([kutu, sahte]) if len(gk) else sahte
            puan = np.concatenate([puan, [0.3]])
            cls = np.concatenate([gc, [0]])
            tah.append((kutu, puan, cls))
        ap5, m5 = map_hesapla(tah, gtl, 0.5, "101")
        m_coco, _ = coco_tarzi_map(tah, gtl)
        print("sigma=%.1f px  mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
              % (sigma, m5, m_coco))


if __name__ == "__main__":
    el_ile_ornek()
    sayisal_dogrulama()
    gurultu_deneyi()
