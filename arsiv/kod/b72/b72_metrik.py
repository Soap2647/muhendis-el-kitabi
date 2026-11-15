# -*- coding: utf-8 -*-
"""Uretken model olcutleri (mini-FID, kesinlik/geri cagirma,
ezberleme). Ozellikler, b72_veri'deki sinif-landiricinin
gizli katmanindan (32 boyut) alinir."""
import numpy as np
import torch
from scipy import linalg
from scipy.spatial.distance import cdist


@torch.no_grad()
def ozellik(model, x):
    t = torch.as_tensor(x, dtype=torch.float32)
    return model.ozellik(t).numpy()


def frechet(f1, f2):
    """Frechet (FID) mesafesi: |m1-m2|^2 + tr(S1+S2-2(S1 S2)^1/2)."""
    m1, m2 = f1.mean(0), f2.mean(0)
    s1 = np.cov(f1, rowvar=False)
    s2 = np.cov(f2, rowvar=False)
    # Tekil kovaryans olabilir (olu ozellik boyutlari): kucuk bir
    # kosegen ekleme standart uygulamadir.
    off = 1e-6 * np.eye(s1.shape[0])
    kok, _ = linalg.sqrtm((s1 + off) @ (s2 + off), disp=False)
    if np.iscomplexobj(kok):
        kok = kok.real
    return float(((m1 - m2) ** 2).sum() + np.trace(s1 + s2 - 2 * kok))


def kesinlik_geri_cagirma(gercek, sahte, k=3):
    """Kynkaanniemi (2019) tarzi kNN tabanli kesinlik ve geri
    cagirma. Her nokta icin k. komsu uzakligi 'yaricap' olur;
    kesinlik: sahte orneklerin gercek topluluk toplarinda oranı."""
    def yaricap(a):
        d = cdist(a, a)
        np.fill_diagonal(d, np.inf)
        return np.sort(d, axis=1)[:, k - 1]

    def kapsama(a, b, ra):
        d = cdist(b, a)
        return float((d <= ra[None, :]).any(axis=1).mean())

    ra = yaricap(gercek)
    rb = yaricap(sahte)
    return kapsama(gercek, sahte, ra), kapsama(sahte, gercek, rb)


def en_yakin(a, b):
    """a'daki her ornegin b icindeki en yakin komsu uzakligi."""
    return cdist(a, b).min(axis=1)


def entropi(etiketler, sinif=10):
    p = np.bincount(etiketler, minlength=sinif) / len(etiketler)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def tam_olcut(x, xtr, clf, xte):
    """Uretilen ornekler x (n, 64, [0,1]) icin tek seferde olcutler.
    Referans: egitim kumesi xtr. Ezber orani: uretilen orneklerin
    egitime en yakin uzakliginin medyani / test orneklerinin egitime
    en yakin uzakliginin medyani (~1: ezber yok; <<1: ezber var)."""
    import b72_veri
    fx = ozellik(clf, x)
    ftr = ozellik(clf, xtr)
    p, r = kesinlik_geri_cagirma(ftr, fx)
    yhat = b72_veri.tahmin(clf, x)
    ezber = float(np.median(en_yakin(x, xtr)) /
                  np.median(en_yakin(xte, xtr)))
    return {"fid": frechet(fx, ftr), "precision": p, "recall": r,
            "entropi": entropi(yhat), "ezber": ezber}
