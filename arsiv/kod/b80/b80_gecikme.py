# -*- coding: utf-8 -*-
# b80_gecikme.py: kare basina gecikme (CPU, ONNX Runtime), asama
# dokumu (on isleme, cikarim, son isleme, takip, guvence) ve bellek /
# MAC hesabi. Olcum CPU'da yapilir; Cortex-M ya da Jetson olculmedi.
import os
import time
import numpy as np
import onnx
from b80_veri import video, NOMINAL
from b80_onnx import ort_oturum, ham_to_cikti, ONNX32, ONNX8
from b67_04_yolo_mini import decode
from b67_08_takip import Izleyici

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISINMA, OLCUM = 30, 300
ASAMALAR = ["on_isleme", "cikarim", "son_isleme", "takip", "guvence"]


def olc(yol, threads, kareler):
    sess = ort_oturum(yol, threads)
    ad = sess.get_inputs()[0].name
    iz = Izleyici("acgozlu_iou")
    zaman = {a: [] for a in ASAMALAR}
    for t in range(ISINMA + OLCUM):
        img = kareler[t % len(kareler)]["img"]
        t0 = time.perf_counter()
        kare_u8 = (img * 255).astype(np.uint8)  # sensor ciktisi
        x = kare_u8.astype(np.float32).reshape(1, 1, 96, 96) / 255.0
        t1 = time.perf_counter()
        ham = sess.run(None, {ad: x})[0]
        t2 = time.perf_counter()
        kut, skor, _ = decode(ham_to_cikti(ham))[0]
        t3 = time.perf_counter()
        iz.guncelle(kut, skor)
        t4 = time.perf_counter()
        _ = [s < 0.6 for s in skor]  # guvence kurali
        t5 = time.perf_counter()
        if t >= ISINMA:
            for a, (p, q) in zip(
                ASAMALAR,
                [(t0, t1), (t1, t2), (t2, t3), (t3, t4), (t4, t5)],
            ):
                zaman[a].append((q - p) * 1000.0)
    return {a: np.array(v) for a, v in zaman.items()}


def conv_mac(h, w, cin, cout, k=3):
    return h * w * cin * cout * k * k


def mac_tablosu(boyut):
    """Bolum 67/75'in 4 konvolusyonu + 1x1 bas. Adim 2,2,2,1."""
    katman = [(1, 16, 2), (16, 32, 2), (32, 64, 2), (64, 64, 1)]
    h = boyut
    toplam, cikis_bayt = 0, []
    for cin, cout, adim in katman:
        h = h // adim
        toplam += conv_mac(h, h, cin, cout)
        cikis_bayt.append(cout * h * h)  # int8: 1 bayt / eleman
    toplam += h * h * 64 * 16  # 1x1 bas
    return toplam, cikis_bayt


def main():
    kareler = video(300, kus=1)
    satirlar = []
    print(
        "%-10s %-6s %-12s %8s %8s"
        % ("is_parcacigi", "model", "asama", "p50_ms", "p95_ms")
    )
    for threads in (4, 1):
        for ad, yol in [("int8", ONNX8), ("fp32", ONNX32)]:
            z = olc(yol, threads, kareler)
            toplam = sum(z[a] for a in ASAMALAR)
            for a in ASAMALAR + ["toplam"]:
                v = toplam if a == "toplam" else z[a]
                p50, p95 = np.percentile(v, 50), np.percentile(v, 95)
                satirlar.append((threads, ad, a, p50, p95))
                print(
                    "%-10d %-6s %-12s %8.3f %8.3f"
                    % (threads, ad, a, p50, p95)
                )
    with open(
        os.path.join(VERI, "b80_gecikme.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("threads,model,asama,p50_ms,p95_ms\n")
        for s in satirlar:
            f.write("%d,%s,%s,%.3f,%.3f\n" % s)
    # Bilesen cubugu: int8, 4 thread, p50 degerleri
    with open(
        os.path.join(VERI, "b80_gecikme_bilesen.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("senaryo,asama,p50_ms\n")
        for s in satirlar:
            if s[1] == "int8" and s[2] != "toplam":
                f.write("%d_thread,%s,%.3f\n" % (s[0], s[2], s[3]))
    # Olcek senaryosu: ayni ag 640x640 girdide (yalnizca cikarim
    # suresi; bu boyutta egitilmedi, dogruluk yok)
    nl = chr(10)
    rng = np.random.default_rng(0)
    x640 = rng.random((1, 1, 640, 640), dtype=np.float32)
    with open(
        os.path.join(VERI, "b80_gecikme_640.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("threads,girdi,p50_ms,p95_ms" + nl)
        for threads in (4, 1):
            sess = ort_oturum(ONNX8, threads)
            ad = sess.get_inputs()[0].name
            zs = []
            for t in range(10 + 60):
                t0 = time.perf_counter()
                sess.run(None, {ad: x640})
                if t >= 10:
                    zs.append((time.perf_counter() - t0) * 1000.0)
            zs = np.array(zs)
            p50, p95 = np.percentile(zs, 50), np.percentile(zs, 95)
            print(
                "640x640 int8 %d thread: cikarim p50=%.2f ms "
                "p95=%.2f ms" % (threads, p50, p95)
            )
            f.write("%d,640,%.3f,%.3f" % (threads, p50, p95) + nl)
    # Bellek ve MAC: Cortex-M sinifi icin 96x96 ve 640x640 girdi
    m = onnx.load(ONNX8)
    flash = sum(
        int(np.prod(t.dims))
        * (
            4
            if t.data_type == 1
            else 1 if t.data_type in (2, 3) else 4
        )
        for t in m.graph.initializer
    )
    print(
        "\nint8 model agirlik ve sabitler (yaklasik): %d bayt" % flash
    )
    for boyut in (96, 640):
        mac, cikislar = mac_tablosu(boyut)
        print(
            "girdi %dx%d: MAC = %.1f milyon, en buyuk ara tampon "
            "= %d bayt" % (boyut, boyut, mac / 1e6, max(cikislar))
        )
    with open(
        os.path.join(VERI, "b80_bellek.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("girdi,mac,en_buyuk_ara_bayt,agirlik_bayt\n")
        for boyut in (96, 640):
            mac, cikislar = mac_tablosu(boyut)
            f.write(
                "%d,%d,%d,%d\n" % (boyut, mac, max(cikislar), flash)
            )


if __name__ == "__main__":
    main()
