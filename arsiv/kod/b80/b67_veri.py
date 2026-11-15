# -*- coding: utf-8 -*-
# b67_veri.py: sentetik sahne ve video ureteci (sabit tohum).
# Siniflar: daire (0), kare (1), ucgen (2). Bunlar sentetik "hava
# hedefleri"dir; gercek bir ucus veri kumesi DEGILDIR. Etiket,
# GORUNUR kisminin kutusu ve piksel maskesidir.
import numpy as np

SINIFLAR = ["daire", "kare", "ucgen"]


def _sekil(sek, s, cx, cy, xx, yy):
    """Tam (ortusmemis) sekil maskesi. Piksel merkezi x+0.5 alinir."""
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    if sek == 0:  # daire, yaricap s/2
        return dx * dx + dy * dy <= (s / 2) ** 2
    if sek == 1:  # kare, kenar s
        return (np.abs(dx) <= s / 2) & (np.abs(dy) <= s / 2)
    # ucgen: tepe yukarida, taban asagida, yukseklik s
    t = (dy + s / 2) / s  # 0 tepe, 1 taban
    return (t >= 0) & (t <= 1) & (np.abs(dx) <= t * s / 2)


def sahne(rng, boyut=96, nmin=0, nmax=5):
    """Bir gri sahne. Donus: img (float32 HxW), nesneler, seg (HxW).
    seg: 0 = arka plan, 1..3 = sinif+1 (gorunur piksel maskesi).
    nesneler: dict listesi (cls, box=[x1,y1,x2,y2) , alan)."""
    W = H = boyut
    olcek = boyut / 96.0
    yy, xx = np.mgrid[0:H, 0:W]
    img = 0.25 + 0.04 * rng.standard_normal((H, W))
    n = int(rng.integers(nmin, nmax + 1))
    adaylar = []
    for _ in range(n):
        s = rng.uniform(8, 24) * olcek
        cx = rng.uniform(s / 2 + 1, W - s / 2 - 1)
        cy = rng.uniform(s / 2 + 1, H - s / 2 - 1)
        sek = int(rng.integers(0, 3))
        par = rng.uniform(0.6, 1.0)
        m = _sekil(sek, s, cx, cy, xx, yy)
        adaylar.append((sek, m, par))
    # Cizim sirasi = katman sirasi: sonra cizilen onceki nesneyi
    # ortusturur.
    gorunur = np.full((H, W), -1, dtype=np.int64)
    for k, (sek, m, par) in enumerate(adaylar):
        gorunur[m] = k
        img[m] = par
    img = np.clip(img + 0.02 * rng.standard_normal((H, W)), 0, 1)
    nesneler, seg = [], np.zeros((H, W), dtype=np.int64)
    for k, (sek, m, par) in enumerate(adaylar):
        mk = gorunur == k
        seg[mk] = sek + 1
        alan = int(mk.sum())
        if alan < 15 * olcek * olcek:  # cok ortulu: kutu etiketi yok
            continue
        ys, xs = np.where(mk)
        box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1,
               int(ys.max()) + 1]
        nesneler.append({"cls": sek, "box": box, "alan": alan})
    return img.astype(np.float32), nesneler, seg


def veri_seti(n, seed, boyut=96, nmin=0, nmax=5):
    """n sahneden X (n,1,H,W), kutu listesi ve maske dizisi uretir."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 1, boyut, boyut), dtype=np.float32)
    Y, S = [], np.zeros((n, boyut, boyut), dtype=np.int64)
    for i in range(n):
        img, nes, seg = sahne(rng, boyut, nmin, nmax)
        X[i, 0] = img
        Y.append(nes)
        S[i] = seg
    return X, Y, S


def video(seed, T=120, W=200, H=200, p_kacir=0.10, n_rast=4):
    """Sabit hizli, gurultulu hareket eden nesneler (takip icin).
    Nesne 0 ve 1 ayni yolda kesisir (kimlik degisimi riski).
    Nesne 2, 60-70. karelerde tamamen ortulur (ardisik kayip).
    Donus: kareler listesi; her kare: gt_id, gt (xyxy), det (xyxy),
    skor, dedektor tespitleri, ve sahte alarm (clutter) kutulari."""
    rng = np.random.default_rng(seed)
    # (x, y, vx, vy, w, h, t_baslangic, t_bitis)
    nes = [
        (20.0, 100.0, 2.0, 0.30, 16, 16, 0, T),
        (180.0, 104.0, -2.0, -0.20, 16, 16, 0, T),
        (30.0, 40.0, 1.0, 0.60, 14, 14, 0, T),
        (170.0, 160.0, -1.2, -0.80, 18, 18, 5, T),
    ]
    for _ in range(n_rast):  # rastgele ek nesneler
        nes.append((rng.uniform(20, 180), rng.uniform(20, 180),
                    rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5),
                    rng.uniform(12, 20), rng.uniform(12, 20),
                    int(rng.integers(0, 40)), T))
    durum = [list(n) for n in nes]
    kareler = []
    for t in range(T):
        gt_id, gt, det, skor = [], [], [], []
        for k, d in enumerate(durum):
            x, y, vx, vy, w, h, t0, t1 = d
            if not (t0 <= t < t1):
                continue
            # kisa surecli ivme gurultusu, sonra sabit hiz
            d[2] += 0.02 * rng.standard_normal()
            d[3] += 0.02 * rng.standard_normal()
            box = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
            gt_id.append(k)
            gt.append(box)
            ortulu = (k == 2 and 60 <= t < 70)
            if ortulu or rng.uniform() < p_kacir:
                pass  # dedektor kacirdi
            else:
                gx = x + rng.normal(0, 1.5)
                gy = y + rng.normal(0, 1.5)
                gw = max(4.0, w + rng.normal(0, 1.0))
                gh = max(4.0, h + rng.normal(0, 1.0))
                det.append([gx - gw / 2, gy - gh / 2,
                            gx + gw / 2, gy + gh / 2])
                # gercek nesneler: cogunlukla yuksek, bazen dusuk skor
                if rng.uniform() < 0.2:
                    skor.append(rng.uniform(0.20, 0.45))
                else:
                    skor.append(rng.uniform(0.55, 0.99))
            d[0] += d[2]
            d[1] += d[3]
        # sahte alarmlar (Poisson, ortalama 1)
        for _ in range(rng.poisson(1.0)):
            cx, cy = rng.uniform(10, W - 10), rng.uniform(10, H - 10)
            s = rng.uniform(12, 20)
            det.append([cx - s / 2, cy - s / 2,
                        cx + s / 2, cy + s / 2])
            skor.append(rng.uniform(0.10, 0.70))
        kareler.append({"gt_id": gt_id, "gt": gt, "det": det,
                        "skor": skor})
    return kareler


if __name__ == "__main__":
    X, Y, S = veri_seti(200, seed=0)
    adet = [len(y) for y in Y]
    print("sahne:", X.shape, "ort. nesne:", round(np.mean(adet), 2))
    print("sinif sayilari:", np.bincount(
        [o["cls"] for y in Y for o in y]).tolist())
    k = video(seed=1)
    print("video kare:", len(k), "ilk kare tespit:", len(k[0]["det"]))
