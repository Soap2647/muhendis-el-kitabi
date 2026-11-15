# -*- coding: utf-8 -*-
"""Bolum 48 - Lineer Cebir diyagramlari.

Olcum grafikleri engine/veri/b48_*.csv dosyalarini okur:
  b48_svd.csv    (svd_gorsel.py ciktisi)
  b48_matmul.csv (matmul_hiz.py ciktisi)
Diger sekiller kavramsal ve sayisal olarak yeniden uretilebilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Circle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b48_%s.png" % ad)


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _eksen(ax, lim=2.5):
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axhline(0, color=RULE, lw=0.8, zorder=0)
    ax.axvline(0, color=RULE, lw=0.8, zorder=0)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _ok(ax, v, col=ACCENT, lw=2.0, etiket=None, dx=0.08, dy=0.08):
    ax.annotate("", xy=(v[0], v[1]), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=lw,
                                shrinkA=0, shrinkB=0))
    if etiket:
        ax.text(v[0] + dx, v[1] + dy, etiket, color=col, fontsize=10.5,
                weight="bold")


def _kare():
    return np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]], dtype=float)


def _poligon(ax, M, fill, edge, etiket=None, lim=None):
    p = M @ _kare()
    ax.fill(p[0], p[1], color=fill, alpha=0.85, zorder=2)
    ax.plot(p[0], p[1], color=edge, lw=1.8, zorder=3)


# --------------------------------------------------------------------- #
def nokta_norm(path):
    """2x2: izdusum ve uc norm birim kumesi."""
    fig, axs = plt.subplots(2, 2, figsize=(9.2, 8.6))
    ax = axs[0, 0]
    _eksen(ax, 4.2)
    a = np.array([3.0, 3.0])
    b = np.array([4.0, 0.5])
    _ok(ax, b, col=EDGE[0], lw=2.0, etiket="b", dx=0.1, dy=-0.4)
    _ok(ax, a, col=ACCENT, lw=2.0, etiket="a", dx=0.1, dy=0.1)
    proj = (a @ b) / (b @ b) * b
    ax.plot([a[0], proj[0]], [a[1], proj[1]], "--", color=MUTED, lw=1.2)
    _ok(ax, proj, col=EDGE[1], lw=2.2, etiket="izdüşüm", dx=-1.6, dy=-0.7)
    ax.set_title("(a) Nokta çarpım ve izdüşüm", fontsize=11.5, color=INK)
    ax.text(-3.9, -3.7, "a·b = %.1f ; ‖a‖ cos θ kadar b yönünde"
            % (a @ b), fontsize=9, color=INK)
    # birim kumeler
    th = np.linspace(0, 2 * np.pi, 400)
    kumeler = [
        ("(b) L1: |x|+|y| = 1", None, [(1, 0), (0, 1), (-1, 0), (0, -1)]),
        ("(c) L2: x²+y² = 1", "circle", None),
        ("(d) L∞: max(|x|,|y|) = 1", "square", None),
    ]
    for ax, (baslik, tip, koseler) in zip([axs[0, 1], axs[1, 0], axs[1, 1]],
                                          kumeler):
        _eksen(ax, 1.6)
        if tip is None:
            pts = np.array(koseler + [koseler[0]], dtype=float)
            ax.fill(pts[:, 0], pts[:, 1], color=FILL[0], zorder=1)
            ax.plot(pts[:, 0], pts[:, 1], color=ACCENT, lw=2.0)
        elif tip == "circle":
            ax.plot(np.cos(th), np.sin(th), color=ACCENT, lw=2.0)
            ax.fill(np.cos(th), np.sin(th), color=FILL[0], zorder=1)
        else:
            pts = np.array([(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)],
                           dtype=float)
            ax.fill(pts[:, 0], pts[:, 1], color=FILL[0], zorder=1)
            ax.plot(pts[:, 0], pts[:, 1], color=ACCENT, lw=2.0)
        ax.set_title(baslik, fontsize=11.5, color=INK)
    return _save(fig, _yol("nokta_norm"))


def donusum_det(path):
    """2x2: dondurme, olcekleme, kayma, izdusum; her panelde det."""
    fig, axs = plt.subplots(2, 2, figsize=(9.2, 8.4))
    R = np.array([[0.0, -1.0], [1.0, 0.0]])
    S = np.array([[2.0, 0.0], [0.0, 1.0]])
    K = np.array([[1.0, 1.0], [0.0, 1.0]])
    P = np.array([[1.0, 0.0], [0.0, 0.0]])
    panel = [
        (R, "Döndürme R (90°)", "det = 1 : alan korunur"),
        (S, "Ölçekleme S (x'te 2 kat)", "det = 2 : alan iki katına çıkar"),
        (K, "Kayma K", "det = 1 : alan korunur, şekil eğilir"),
        (P, "İzdüşüm P (x eksenine)", "det = 0 : alan sıfır, boyut düşer"),
    ]
    for ax, (M, baslik, not_) in zip(axs.ravel(), panel):
        _eksen(ax, 2.6)
        ax.plot(_kare()[0], _kare()[1], "--", color=MUTED, lw=1.1,
                zorder=1)
        _poligon(ax, M, FILL[1], EDGE[1])
        ax.set_title(baslik, fontsize=11.5, color=INK)
        ax.text(-2.5, -2.35, not_, fontsize=9, color=INK)
        for e, lb in [(np.array([1, 0]), "e1"), (np.array([0, 1]), "e2")]:
            v = M @ e
            ax.annotate("", xy=v, xytext=(0, 0),
                        arrowprops=dict(arrowstyle="-|>", color=ACCENT,
                                        lw=1.5, shrinkA=0, shrinkB=0))
            ax.text(v[0] + 0.07, v[1] + 0.07, lb + "'",
                    color=ACCENT, fontsize=10)
    fig.text(0.5, 0.005, "Kesikli çizgi: birim kare. Dolu: M ile görüntüsü.",
             ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("donusum_det"))


def bilesim(path):
    """Iki panel: S sonra R (R·S) ve R sonra S (S·R)."""
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 4.6))
    R = np.array([[0.0, -1.0], [1.0, 0.0]])
    S = np.array([[2.0, 0.0], [0.0, 1.0]])
    for ax, (M, baslik, dizi) in zip(axs, [
            (R @ S, "Önce S, sonra R  (R·S)", "S, sonra R"),
            (S @ R, "Önce R, sonra S  (S·R)", "R, sonra S")]):
        _eksen(ax, 2.6)
        ax.plot(_kare()[0], _kare()[1], "--", color=MUTED, lw=1.1,
                zorder=1)
        _poligon(ax, M, FILL[2], EDGE[2])
        ax.set_title(baslik, fontsize=11.5, color=INK)
        ax.text(-2.45, -2.35, "M = [[%d, %d], [%d, %d]]"
                % tuple(M.astype(int).ravel()), fontsize=9.5, color=INK)
        ax.text(-2.45, 2.25, "sıra: " + dizi, fontsize=9.5, color=MUTED)
    return _save(fig, _yol("bilesim"))


def gauss_adimlar(path):
    """2x2: kismi pivotlu Gauss adimlari (ornek2 ile ayni sayilar)."""
    fig, axs = plt.subplots(2, 2, figsize=(9.2, 6.6))
    stages = [
        ("(a) Başlangıç [A | b]",
         [["2", "1", "-1", "8"],
          ["-3", "-1", "2", "-11"],
          ["-2", "1", "2", "-3"]],
         "sütun 1'de en büyük |.| = |-3|: satır 1 ↔ 2"),
        ("(b) k=1 eleme sonrası",
         [["-3", "-1", "2", "-11"],
          ["0", "0.333", "0.333", "0.667"],
          ["0", "1.667", "0.667", "4.333"]],
         "sütun 2'de en büyük |.| = 1.667: satır 2 ↔ 3"),
        ("(c) k=2 eleme sonrası (üst üçgen)",
         [["-3", "-1", "2", "-11"],
          ["0", "1.667", "0.667", "4.333"],
          ["0", "0", "0.200", "-0.200"]],
         "köşegen: -3, 1.667, 0.2 (hepsi sıfırdan farklı)"),
        ("(d) Geri yerine koyma",
         None,
         "z = -1, y = 3, x = 2  (numpy ile aynı)"),
    ]
    for ax, (baslik, M, not_) in zip(axs.ravel(), stages):
        ax.axis("off")
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.set_title(baslik, fontsize=11.5, color=INK, loc="left")
        if M is not None:
            for i, satir in enumerate(M):
                for j, h in enumerate(satir):
                    x = 1.0 + j * 1.55 + (0.5 if j == 3 else 0)
                    y = 4.0 - i * 1.1
                    fill = FILL[0]
                    if j == 3:
                        fill = FILL[2]
                    if (baslik.startswith("(a)") and i == 1 and j == 0) \
                            or (baslik.startswith("(b)") and i == 0 and j == 0) \
                            or (baslik.startswith("(c)") and i == 0 and j == 0):
                        fill = FILL[1]
                    if j < 3 and i > 0 and float(h) == 0:
                        fill = "#ffffff"
                    _box(ax, x, y, 1.3, 0.9, h, fill=fill, edge=EDGE[0],
                         fs=9.5)
        else:
            x_sonuc = ["x = 2", "y = 3", "z = -1"]
            for i, t in enumerate(x_sonuc):
                _box(ax, 2.0 + i * 2.6, 3.2, 2.1, 1.2, t, fill=FILL[1],
                     edge=EDGE[1], fs=12, bold=True)
        ax.text(0.2, 0.5, not_, fontsize=9.5, color=MUTED)
    return _save(fig, _yol("gauss_adimlar"))


def ozvektor(path):
    """Ozvektorler dogrultusunu korur; digerleri doner."""
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 4.8))
    A = np.array([[3.0, 1.0], [1.0, 3.0]])
    v1 = np.array([1.0, 1.0])
    v2 = np.array([1.0, -1.0])
    w = np.array([1.0, 0.0])
    for ax, donum in [(axs[0], None), (axs[1], A)]:
        _eksen(ax, 4.6)
        ax.plot([-4.5, 4.5], [-4.5, 4.5], ":", color=RULE, lw=1.0)
        ax.plot([-4.5, 4.5], [4.5, -4.5], ":", color=RULE, lw=1.0)
        for v, lb, col in [(v1, "v1", ACCENT), (v2, "v2", EDGE[0]),
                           (w, "w", EDGE[1])]:
            vv = v if donum is None else donum @ v
            _ok(ax, vv, col=col, lw=2.0, etiket=lb, dx=0.1, dy=0.1)
        ax.set_title("(a) Başlangıç vektörleri" if donum is None
                     else "(b) A uygulandıktan sonra",
                     fontsize=11, color=INK)
    axs[0].text(-4.3, -4.1, "v1 = (1,1), v2 = (1,-1), w = (1,0)",
                fontsize=9, color=INK)
    axs[1].text(-4.3, -4.1, "A v1 = 4 v1, A v2 = 2 v2; w yön değiştirir",
                fontsize=9, color=INK)
    return _save(fig, _yol("ozvektor"))


def svd_elips(path):
    """2x2: birim cember -> Vt -> Sigma -> U : elips."""
    A = np.array([[2.0, 1.0], [0.0, 1.5]])
    U, s, Vt = np.linalg.svd(A)
    th = np.linspace(0, 2 * np.pi, 300)
    cember = np.vstack([np.cos(th), np.sin(th)])
    fig, axs = plt.subplots(2, 2, figsize=(9.2, 8.6))
    adim = [
        (cember, "(a) Birim çember", "x: birim"),
        (Vt @ cember, "(b) Vᵀ: döndür/yansıt", "dönüş, şekil değişmez"),
        (np.diag(s) @ Vt @ cember, "(c) Σ: eksenlerde ölçekle",
         "σ1 = %.3f, σ2 = %.3f" % (s[0], s[1])),
        (A @ cember, "(d) U: son dönüş = A", "elips, eksenler σ_i u_i"),
    ]
    for ax, (p, baslik, not_) in zip(axs.ravel(), adim):
        _eksen(ax, 3.0)
        ax.fill(p[0], p[1], color=FILL[0], alpha=0.8, zorder=1)
        ax.plot(p[0], p[1], color=ACCENT, lw=1.8, zorder=2)
        ax.set_title(baslik, fontsize=11.5, color=INK)
        ax.text(-2.85, -2.7, not_, fontsize=9.2, color=INK)
    for k, col in [(0, ACCENT), (1, EDGE[0])]:
        v = s[k] * U[:, k]
        axs[1, 1].annotate("", xy=v, xytext=(0, 0),
                           arrowprops=dict(arrowstyle="-|>", color=col,
                                           lw=1.8, shrinkA=0, shrinkB=0))
    return _save(fig, _yol("svd_elips"))


def rankk_gorsel(path):
    """2x2: sentetik gorsel ve k = 2, 8, 16 yaklasimlari."""
    n = 128
    rng = np.random.default_rng(42)
    y, x = np.mgrid[0:n, 0:n] / n
    g = 0.5 * x + 0.3 * y
    g += 0.4 * (((x - 0.6) ** 2 + (y - 0.4) ** 2) < 0.06)
    g += 0.2 * np.sin(18 * np.pi * x) * (y > 0.7)
    g += 0.02 * rng.standard_normal((n, n))
    A = np.clip(g, 0.0, 1.0)
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    fig, axs = plt.subplots(2, 2, figsize=(8.6, 8.6))
    paneller = [("Orijinal (128 × 128)", A)]
    for k in [2, 8, 16]:
        Ak = (U[:, :k] * s[:k]) @ Vt[:k]
        hata = np.linalg.norm(A - Ak) / np.linalg.norm(A)
        paneller.append(("k = %d  (bağıl hata %.3f)" % (k, hata), Ak))
    for ax, (baslik, M) in zip(axs.ravel(), paneller):
        ax.imshow(np.clip(M, 0, 1), cmap="gray", vmin=0, vmax=1)
        ax.set_title(baslik, fontsize=11, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
    return _save(fig, _yol("rankk_gorsel"))


def rankk_hata(path):
    """CSV'den: bagil hata ve sikistirma orani (k'ya gore)."""
    satir = _oku("b48_svd.csv")
    k = np.array([int(r["k"]) for r in satir])
    h = np.array([float(r["bagil_hata"]) for r in satir])
    o = np.array([float(r["oran_yuzde"]) for r in satir])
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 4.2))
    ax = axs[0]
    ax.plot(k, h, "o-", color=ACCENT, lw=1.8)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("k (tekil değer sayısı)", color=INK)
    ax.set_ylabel("‖A − A_k‖_F / ‖A‖_F", color=INK)
    ax.set_title("Bağıl hata", fontsize=11.5, color=INK)
    ax.grid(color=RULE, lw=0.6)
    ax = axs[1]
    ax.plot(k, o, "s-", color=EDGE[0], lw=1.8)
    ax.axhline(100, color=MUTED, ls="--", lw=1.0)
    ax.text(1.1, 88, "100 üstü: orijinalden büyük", color=MUTED, fontsize=9)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("k", color=INK)
    ax.set_ylabel("sıkıştırma oranı (%)", color=INK)
    ax.set_title("Depolama oranı: k(m+n+1)/(mn)", fontsize=11.5, color=INK)
    ax.grid(color=RULE, lw=0.6)
    fig.tight_layout()
    return _save(fig, _yol("rankk_hata"))


def matmul_hiz(path):
    """CSV'den: saf Python ve NumPy matmul sureleri (log-log)."""
    satir = _oku("b48_matmul.csv")
    n = np.array([int(r["n"]) for r in satir])
    tp = np.array([float(r["python_s"]) for r in satir])
    tn = np.array([float(r["numpy_s"]) for r in satir])
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.loglog(n, tp, "o-", color=ACCENT, lw=1.8, label="saf Python üçlü döngü")
    ax.loglog(n, tn, "s-", color=EDGE[0], lw=1.8, label="NumPy (BLAS)")
    for x, a, b in zip(n, tp, tn):
        ax.text(x * 1.05, a * 1.25, "%.0f×" % (a / b), fontsize=9,
                color=INK)
    ax.set_xticks(n)
    ax.set_xticklabels([str(x) for x in n])
    ax.minorticks_off()
    ax.set_xlim(n[0] * 0.8, n[-1] * 1.4)
    ax.set_xlabel("n (matris boyutu, n × n)", color=INK)
    ax.set_ylabel("süre (s, en iyi 3-20 tekrar)", color=INK)
    ax.set_title("Matris çarpımı: Python ve NumPy", fontsize=11.5,
                 color=INK)
    ax.grid(color=RULE, lw=0.6, which="both")
    ax.legend(frameon=False, fontsize=9.5)
    return _save(fig, _yol("matmul_hiz"))


def ml_harita(path):
    """ML'de lineer cebir haritasi: kutular ve oklar."""
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    _box(ax, 0.3, 5.9, 2.9, 1.2, "Veri matrisi X\n(n örnek × d özellik)",
         fill=FILL[0], edge=EDGE[0], fs=9.5, bold=True)
    _box(ax, 4.0, 5.9, 3.2, 1.2, "Afin dönüşüm\nXW + b", fill=FILL[1],
         edge=EDGE[1], fs=9.5, bold=True)
    _box(ax, 7.9, 5.9, 2.9, 1.2, "Doğrusal olmayan σ\n(ReLU, tanh)",
         fill=FILL[2], edge=EDGE[2], fs=9.5, bold=True)
    _box(ax, 11.3, 5.9, 2.5, 1.2, "Katman çıktısı\n(Bölüm 63)", fill=FILL[4],
         edge=EDGE[4], fs=9.5, bold=True)
    _arrow(ax, 3.2, 6.5, 4.0, 6.5, col=ACCENT)
    _arrow(ax, 7.2, 6.5, 7.9, 6.5, col=ACCENT)
    _arrow(ax, 10.8, 6.5, 11.3, 6.5, col=ACCENT)
    _box(ax, 0.3, 3.4, 3.4, 1.4, "Dikkat: softmax(QKᵀ/√d)V\n(Bölüm 69)",
         fill=FILL[3], edge=EDGE[3], fs=9.2)
    _box(ax, 4.3, 3.4, 3.4, 1.4, "Gömme: one-hot × E\n(Bölüm 70)",
         fill=FILL[1], edge=EDGE[1], fs=9.2)
    _box(ax, 8.3, 3.4, 2.9, 1.4, "PCA: X = UΣVᵀ\n(Bölüm 61)",
         fill=FILL[0], edge=EDGE[0], fs=9.2)
    _box(ax, 0.3, 0.6, 3.4, 1.4, "LoRA: W + BA, düşük rank\n(Bölüm 70)",
         fill=FILL[4], edge=EDGE[4], fs=9.2)
    _box(ax, 4.3, 0.6, 3.4, 1.4, "Gradyan: Jacobian\nzincir kuralı (Bölüm 55)",
         fill=FILL[2], edge=EDGE[2], fs=9.2)
    _box(ax, 8.3, 0.6, 3.4, 1.4, "En küçük kareler:\nQR / SVD (Bölüm 58)",
         fill=FILL[3], edge=EDGE[3], fs=9.2)
    _box(ax, 11.6, 3.4, 2.2, 1.4, "Kosinüs\nbenzerliği\n(Bölüm 70)",
         fill=FILL[1], edge=EDGE[1], fs=8.8)
    ax.text(7.0, 2.4, "Tensörler (batch, kanal, yükseklik, genişlik) bu "
            "matrislerin genelleşmesidir", ha="center", fontsize=9.2,
            color=MUTED)
    return _save(fig, _yol("ml_harita"))


def main():
    yollar = [nokta_norm(None), donusum_det(None), bilesim(None),
              gauss_adimlar(None), ozvektor(None), svd_elips(None),
              rankk_gorsel(None), rankk_hata(None), matmul_hiz(None),
              ml_harita(None)]
    for p in yollar:
        print(os.path.normpath(p))


if __name__ == "__main__":
    main()
