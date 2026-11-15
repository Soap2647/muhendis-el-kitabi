# -*- coding: utf-8 -*-
# b67_03_anchor.py: anchor kutulari, kutu ofset kodlama/cozme ve
# hucre-anchor hedef atamasi. Iki kodlama: Faster R-CNN tarzi
# (log-olcek) ve YOLO tarzi (sigmoid ile hucre ici ofset).
import numpy as np
from b67_01_iou_nms import iou_matris

S = 8                                  # hucre boyu (piksel), stride
ANCHORS = np.array([[10.0, 10.0],      # (genislik, yukseklik)
                    [20.0, 20.0]])


def frcnn_kodla(kutu, capa):
    """Gercek kutu ve anchor (cx,cy,w,h): ofset ve log-olcek."""
    tx = (kutu[:, 0] - capa[:, 0]) / capa[:, 2]
    ty = (kutu[:, 1] - capa[:, 1]) / capa[:, 3]
    tw = np.log(kutu[:, 2] / capa[:, 2])
    th = np.log(kutu[:, 3] / capa[:, 3])
    return np.stack([tx, ty, tw, th], 1)


def frcnn_coz(t, capa):
    """Ters donusum: ofsetleri kutuya geri cevirir."""
    cx = capa[:, 0] + t[:, 0] * capa[:, 2]
    cy = capa[:, 1] + t[:, 1] * capa[:, 3]
    w = capa[:, 2] * np.exp(t[:, 2])
    h = capa[:, 3] * np.exp(t[:, 3])
    return np.stack([cx, cy, w, h], 1)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def yolo_coz(ham, hucre, aw):
    """ham: (N,4) ham ag cikisi (tx,ty,tw,th); hucre: (N,2) hucre
    indisleri (gx,gy); aw: (N,2) anchor (w,h). Donus: cx,cy,w,h."""
    cx = (hucre[:, 0] + sigmoid(ham[:, 0])) * S
    cy = (hucre[:, 1] + sigmoid(ham[:, 1])) * S
    w = aw[:, 0] * np.exp(ham[:, 2])
    h = aw[:, 1] * np.exp(ham[:, 3])
    return np.stack([cx, cy, w, h], 1)


def yolo_kodla(kutu_cxcywh, hucre, aw):
    """Yolo_coz'un tersi: ham ag ciktisi hedefi (logit ve log)."""
    ox = kutu_cxcywh[:, 0] / S - hucre[:, 0]
    oy = kutu_cxcywh[:, 1] / S - hucre[:, 1]
    ox, oy = np.clip(ox, 1e-6, 1 - 1e-6), np.clip(oy, 1e-6, 1 - 1e-6)
    tx = np.log(ox / (1 - ox))
    ty = np.log(oy / (1 - oy))
    tw = np.log(kutu_cxcywh[:, 2] / aw[:, 0])
    th = np.log(kutu_cxcywh[:, 3] / aw[:, 1])
    return np.stack([tx, ty, tw, th], 1)


def sekil_iou(w, h, aw, ah):
    """Ortak merkezde iki kutunun IoU'su (yalnizca boyuta bakar)."""
    inter = np.minimum(w, aw) * np.minimum(h, ah)
    return inter / (w * h + aw * ah - inter)


def hedefle(kutular, siniflar, G):
    """Gercek kutulari (xyxy, piksel) G x G hucreye ve en iyi anchor'a
    atar. Donus: pozitif maske (G,G,A), hedef kutu (G,G,A,4) [ham],
    sinif (G,G,A) ve cakisma sayisi (ayni hucre+anchor'a iki kutu)."""
    A = len(ANCHORS)
    poz = np.zeros((G, G, A), bool)
    hedef = np.zeros((G, G, A, 4))
    sinif = np.zeros((G, G, A), int)
    cakisma = 0
    for (x1, y1, x2, y2), c in zip(kutular, siniflar):
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = x2 - x1, y2 - y1
        gx, gy = int(cx // S), int(cy // S)
        gx, gy = min(gx, G - 1), min(gy, G - 1)
        a = int(np.argmax(sekil_iou(w, h, ANCHORS[:, 0],
                                    ANCHORS[:, 1])))
        if poz[gy, gx, a]:
            cakisma += 1
        poz[gy, gx, a] = True
        kut = np.array([[cx, cy, w, h]])
        hucre = np.array([[gx, gy]], float)
        hedef[gy, gx, a] = yolo_kodla(kut, hucre, ANCHORS[a:a + 1])[0]
        sinif[gy, gx, a] = c
    return poz, hedef, sinif, cakisma


def testler():
    rng = np.random.default_rng(0)
    print("== Anchor tablosu: sekil IoU'su (ortak merkez) ==")
    ornek = np.array([[8, 8], [12, 12], [16, 24], [24, 24.0]])
    for w, h in ornek:
        v = sekil_iou(w, h, ANCHORS[:, 0], ANCHORS[:, 1])
        print("kutu %4.0fx%-4.0f  IoU(a1)=%.3f  IoU(a2)=%.3f  -> %d"
              % (w, h, v[0], v[1], int(np.argmax(v)) + 1))
    print("\n== Faster R-CNN kodlama gidis-donus (tohum 0) ==")
    capa = np.column_stack([rng.uniform(20, 70, 500),
                            rng.uniform(20, 70, 500),
                            rng.uniform(6, 30, 500),
                            rng.uniform(6, 30, 500)])
    kutu = capa + rng.normal(0, 1.0, capa.shape) * capa[:, 2:3]
    kutu[:, 2:] = np.abs(kutu[:, 2:]) + 1e-3
    geri = frcnn_coz(frcnn_kodla(kutu, capa), capa)
    print("maks |fark| = %.2e" % np.abs(geri - kutu).max())
    print("\n== YOLO tarzi kodlama gidis-donus ==")
    hucre = rng.integers(0, 12, (500, 2)).astype(float)
    kutu_c = np.column_stack([(hucre[:, 0] + rng.uniform(0.01, 0.99,
                              500)) * S, (hucre[:, 1] + rng.uniform(
                              0.01, 0.99, 500)) * S,
                              rng.uniform(6, 30, 500),
                              rng.uniform(6, 30, 500)])
    aw = ANCHORS[rng.integers(0, 2, 500)]
    geri = yolo_coz(yolo_kodla(kutu_c, hucre, aw), hucre, aw)
    print("maks |fark| = %.2e" % np.abs(geri - kutu_c).max())
    print("\n== Hedef atamasi: gorsel basina pozitif ve cakisma ==")
    from b67_veri import veri_seti
    _, Y, _ = veri_seti(300, seed=0)
    pozlar, cakismalar = [], 0
    for objs in Y:
        kut = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        cls = np.array([o["cls"] for o in objs], int)
        poz, _, _, c = hedefle(kut, cls, 12)
        pozlar.append(int(poz.sum()))
        cakismalar += c
    print("ort. pozitif/gorsel = %.2f, nesne = %d, cakisma = %d"
          % (np.mean(pozlar), sum(len(y) for y in Y), cakismalar))
    print("\n== Atama dogrulamasi: en iyi anchor brute force ile ==")
    hata = 0
    for objs in Y[:100]:
        for o in objs:
            x1, y1, x2, y2 = o["box"]
            kut = np.array([[x1, y1, x2, y2]], float)
            w, h = x2 - x1, y2 - y1
            ref = iou_matris(
                np.array([[-w / 2, -h / 2, w / 2, h / 2]], float),
                np.column_stack([-ANCHORS / 2, ANCHORS / 2]))
            beklenen = int(np.argmax(ref[0]))
            poz, _, _, _ = hedefle(kut, [o["cls"]], 12)
            a = int(np.argmax(poz.any(axis=(0, 1))))
            hata += int(a != beklenen)
    print("yanlis anchor atamasi: %d" % hata)


if __name__ == "__main__":
    testler()
