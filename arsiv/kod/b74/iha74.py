# -*- coding: utf-8 -*-
"""Bolum 74 - IHA irtifa tutma: PID taban cizgisi, PPO, alan
rastgelelestirme (domain randomization), guvenlik kalkani.

Ayarlar (degistirmeyin, ortam74.IhaIrtifa ile birebir):
  nominal: kutle 1.0, surukleme kd 0.3, itki/agirlik twr 2.0, ruzgar
  1.0
Basari: zemine dusmeme VE son 10 saniyede max|e| <= 1.0 m.
Ayarlama (PID kazancı, eğitim sürümü): tohum 100-109.
Degerlendirme: tohum 3000+ (100 bolum / kontrolcu / alfa); PPO icin 5
egitim tohumu.
"""

import os
import sys
import numpy as np
import torch
from concurrent.futures import ProcessPoolExecutor
from ortam74 import IhaIrtifa
from ppo74 import ppo_egit, acgozlu_eylem, Politika

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
MODEL = "C:/Users/merty/AppData/Local/Temp/b74/model"
NOM = dict(kutle=1.0, kd=0.3, twr=2.0, ruzgar=1.0)
DT, HREF, T = 0.05, 10.0, 400
TOHUMLAR = [0, 1, 2, 3, 4]
RODUL_OLCEK = 0.04
EMAX = 25.0
DR_ARALIK = dict(
    kutle=(0.8, 1.25),
    kd=(0.1, 0.6),
    twr=(1.8, 2.2),
    ruzgar=(0.0, 1.8),
)


def alfa_parametre(alfa):
    """Alan kaymasi: alfa=0 nominal, alfa=1 DR araliginin disinda."""
    return dict(
        kutle=1 + 0.5 * alfa,
        kd=0.3 + 0.5 * alfa,
        twr=2.0 - 0.4 * alfa,
        ruzgar=1.0 + alfa,
    )


def gozlem(env, I):
    e = env.h - env.h_ref
    return np.array(
        [e / 5.0, env.v / 2.0, I / 50.0], dtype=np.float32
    )


class PID:
    def __init__(self, kp, ki, kd, s_h=0.5):
        self.kp, self.ki, self.kd, self.s_h = kp, ki, kd, s_h

    def reset(self):
        self.I = 0.0

    def act(self, env):
        e = env.h - env.h_ref
        self.I = float(np.clip(self.I + e * DT, -20.0, 20.0))
        s = (
            self.s_h
            - self.kp * e
            - self.ki * self.I
            - self.kd * env.v
        )
        return 2.0 * min(max(s, 0.0), 1.0) - 1.0


class PpoKontrol:
    def __init__(self, pol):
        self.pol = pol

    def reset(self):
        self.I = 0.0

    def act(self, env):
        self.I += (env.h - env.h_ref) * DT
        o = gozlem(env, self.I)
        return float(
            np.clip(acgozlu_eylem(self.pol, o, False)[0], -1, 1)
        )


def kalkan(env, s_cmd, h_min=2.0):
    """Tek adimlik ileri bakis: nominal modelle bir sonraki irtifa
    h_min'in altina inecekse itkiyi en az gereken degere kaldir.
    Model uyumsuzlugu kalkanin bilmedigi bir hataya neden olabilir;
    sinirlilik budur."""
    m, kd, twr, g = 1.0, 0.3, 2.0, IhaIrtifa.G
    h, v = env.h, env.v
    s_min = (
        (h_min - h - DT * v + DT * DT * (g + kd * v))
        * m
        / (DT * DT * twr * g)
    )
    s_saf = min(max(max(s_cmd, s_min), 0.0), 1.0)
    return s_saf, s_saf > s_cmd + 1e-12


class IhaWrap:
    """Egitim ortami: PPO arayuzu (reset, step_ppo)."""

    def __init__(self, seed, dr):
        self.seed, self.dr = seed, dr
        self.rng = np.random.default_rng(seed + 555)
        self.env = IhaIrtifa(rng=np.random.default_rng(seed), **NOM)
        self.sayac = 0

    def reset(self):
        self.sayac += 1
        if self.dr:
            p = {
                k: self.rng.uniform(*DR_ARALIK[k]) for k in DR_ARALIK
            }
        else:
            p = NOM
        for k, v in p.items():
            setattr(self.env, k, float(v))
        self.env.reset(seed=self.seed * 100000 + self.sayac)
        self.I = (self.env.h - self.env.h_ref) * DT
        return gozlem(self.env, self.I)

    def step_ppo(self, a):
        u = float(np.clip(a[0], -1.0, 1.0))
        _, _, yere, bitti, s = self.env.step(u)
        self.I += (self.env.h - self.env.h_ref) * DT
        e = self.env.h - self.env.h_ref
        # Egitim odulu: hayatta kalma tabani - sinirli sapma - efor.
        # Yere carpmada taban kazanilmaz (ceza ayrica yok): sinirsiz
        # sapma cezasi yerine tavan (EMAX) kullanilir; bkz. Bolum 74
        # metni.
        r = (
            0.0
            if yere
            else RODUL_OLCEK * (EMAX - min(e * e, EMAX) - 0.1 * s * s)
        )
        return gozlem(self.env, self.I), r, yere, bitti and not yere


def olc_bolum(kontrol, params, seed, shield=False, kayit=False):
    """Tek bolum: basari, RMS, IAE, efor, kalkan mudahale sayisi."""
    env = IhaIrtifa(rng=np.random.default_rng(seed), **params)
    env.reset(seed=seed)
    kontrol.reset()
    es, ss, ws, hs = [], [], [], []
    mudahale, yere = 0, False
    while True:
        u = kontrol.act(env)
        if shield:
            s_saf, m = kalkan(env, (u + 1) / 2)
            mudahale += int(m)
            u = 2 * s_saf - 1
        if kayit:
            ws.append(env.ruzgar_at(env.adim * DT))
            hs.append(env.h)
        _, r, yere, bitti, s = env.step(u)
        es.append(env.h - env.h_ref)
        ss.append(s)
        if bitti:
            break
    es, ss = np.array(es), np.array(ss)
    son = es[-200:]
    basari = (
        (not yere) and (len(es) >= T) and np.max(np.abs(son)) <= 1.0
    )
    out = dict(
        basari=bool(basari),
        yere=bool(yere),
        rms=float(np.sqrt(np.mean(son**2))) if not yere else np.nan,
        iae=float(np.mean(np.abs(es[100:]))) if not yere else np.nan,
        efor=float(np.mean(ss**2)),
        mudahale=mudahale,
    )
    if kayit:
        out["traj"] = (np.array(hs), np.array(ws), es, ss)
    return out


def ozet(sonuclar):
    basari = np.mean([r["basari"] for r in sonuclar])
    yere = np.mean([r["yere"] for r in sonuclar])
    iae = np.nanmean([r["iae"] for r in sonuclar])
    efor = np.mean([r["efor"] for r in sonuclar])
    mud = np.mean([r["mudahale"] for r in sonuclar])
    return basari, yere, iae, efor, mud


def egri_ol(pol):
    """Egitim sirasinda: nominal 10 bolumde basari orani."""
    ks = PpoKontrol(pol)
    return float(
        np.mean(
            [
                olc_bolum(ks, NOM, 4000 + i)["basari"]
                for i in range(10)
            ]
        )
    )


def egit(args):
    dr, tohum = args
    torch.set_num_threads(1)
    pol, egri = ppo_egit(
        lambda sd: IhaWrap(sd, dr),
        3,
        1,
        False,
        200000,
        tohum,
        eval_fn=egri_ol,
        eval_her=20000,
    )
    os.makedirs(MODEL, exist_ok=True)
    ad = "dr" if dr else "nom"
    torch.save(
        pol.state_dict(),
        os.path.join(MODEL, "%s_%d.pt" % (ad, tohum)),
    )
    return dr, tohum, egri


def pid_ayarla():
    """Kazanc izgarasi; amac: tohum 100-109 (nominal) uzerinde
    ortalama maliyet = e^2 + 0.1 s^2 + 1000 * dusme orani."""
    en_iyi, en_j = None, np.inf
    for kp in (0.05, 0.1, 0.2, 0.4):
        for ki in (0.0, 0.01, 0.02, 0.05):
            for kd in (0.1, 0.2, 0.4, 0.8):
                pid = PID(kp, ki, kd)
                J = []
                for i in range(10):
                    env = IhaIrtifa(
                        rng=np.random.default_rng(100 + i), **NOM
                    )
                    env.reset(seed=100 + i)
                    pid.reset()
                    e2, s2, dus = [], [], 0
                    while True:
                        u = pid.act(env)
                        _, _, yere, bitti, s = env.step(u)
                        e2.append((env.h - env.h_ref) ** 2)
                        s2.append(s * s)
                        if bitti:
                            dus = int(yere)
                            break
                    J.append(
                        np.mean(e2) + 0.1 * np.mean(s2) + 1000 * dus
                    )
                j = float(np.mean(J))
                if j < en_j:
                    en_j, en_iyi = j, (kp, ki, kd)
    return en_iyi, en_j


if __name__ == "__main__":
    (kp, ki, kd), j = pid_ayarla()
    print(
        "PID kazanclari (tohum 100-109): "
        "kp=%.2f ki=%.2f kd=%.2f J=%.4f"
        % (kp, ki, kd, j)
    )
    PIDK = PID(kp, ki, kd)

    with ProcessPoolExecutor(max_workers=5) as ex:
        isler = [(d, t) for d in (False, True) for t in TOHUMLAR]
        egitim = list(ex.map(egit, isler))
    print("PPO egitimi tamam (10 kosu)")

    pol_nom, pol_dr = {}, {}
    for dr, t, _ in egitim:
        p = Politika(3, 1, False)
        p.load_state_dict(
            torch.load(
                os.path.join(
                    MODEL, "%s_%d.pt" % ("dr" if dr else "nom", t)
                ),
                weights_only=True,
            )
        )
        (pol_dr if dr else pol_nom)[t] = p

    # Alan kaymasi taramasi: basari orani (5 egitim tohumu x 100
    # bolum)
    satirlar = ["alfa,kontrolcu,ort,sd"]
    tablo = {}
    for alfa in (0.0, 0.25, 0.5, 0.75, 1.0):
        prm = alfa_parametre(alfa)
        seeds = range(3000, 3100)
        b = [olc_bolum(PIDK, prm, s)["basari"] for s in seeds]
        tablo[(alfa, "PID")] = (np.mean(b), 0.0)
        satirlar.append("%.2f,PID,%.3f,0.000" % (alfa, np.mean(b)))
        for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
            vals = []
            for t in TOHUMLAR:
                kon = PpoKontrol(bank[t])
                vals.append(
                    np.mean(
                        [
                            olc_bolum(kon, prm, s)["basari"]
                            for s in seeds
                        ]
                    )
                )
            vals = np.array(vals)
            tablo[(alfa, ad)] = (vals.mean(), vals.std(ddof=1))
            satirlar.append(
                "%.2f,%s,%.3f,%.3f"
                % (alfa, ad, vals.mean(), vals.std(ddof=1))
            )
    with open(
        os.path.join(VERI, "b74_iha_dr.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print("alfa   PID          PPO-nom       PPO-DR     (basari, sd)")
    for alfa in (0.0, 0.25, 0.5, 0.75, 1.0):
        print(
            "%.2f  " % alfa
            + "  ".join(
                "%.2f(%.2f)" % tablo[(alfa, k)]
                for k in ("PID", "PPO-nom", "PPO-DR")
            )
        )

    # Ayrinti tablosu: nominal ve alfa=1 (efor, IAE, dusme)
    for alfa in (0.0, 1.0):
        prm = alfa_parametre(alfa)
        seeds = range(3000, 3100)
        r = ozet([olc_bolum(PIDK, prm, s) for s in seeds])
        print(
            "alfa=%.1f PID: basari=%.2f dusme=%.2f IAE=%.3f efor=%.3f"
            % (alfa, r[0], r[1], r[2], r[3])
        )
        for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
            rr = [
                ozet(
                    [
                        olc_bolum(PpoKontrol(bank[t]), prm, s)
                        for s in seeds
                    ]
                )
                for t in TOHUMLAR
            ]
            rr = np.array(rr)
            print(
                "alfa=%.1f %s: basari=%.2f dusme=%.2f "
                "IAE=%.3f efor=%.3f"
                % (
                    alfa,
                    ad,
                    rr[:, 0].mean(),
                    rr[:, 1].mean(),
                    rr[:, 2].mean(),
                    rr[:, 3].mean(),
                )
            )

    # Guvenlik kalkani: alfa=1.0, nominal ve DR, kalkan var/yok
    prm = alfa_parametre(1.0)
    seeds = range(3000, 3100)
    for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
        for kal in (False, True):
            rr = np.array(
                [
                    ozet(
                        [
                            olc_bolum(
                                PpoKontrol(bank[t]),
                                prm,
                                s,
                                shield=kal,
                            )
                            for s in seeds
                        ]
                    )
                    for t in TOHUMLAR
                ]
            )
            print(
                "kalkan=%s %s (a=1): dusme=%.3f basari=%.3f "
                "mudahale=%.1f"
                % (
                    kal,
                    ad,
                    rr[:, 1].mean(),
                    rr[:, 0].mean(),
                    rr[:, 4].mean(),
                )
            )

    # Yorunge: kutle +20%, ruzgar x1.5 (DR araligi icinde), tohum 3000
    prm = dict(kutle=1.2, kd=0.3, twr=2.0, ruzgar=1.5)
    yol = {
        "PID": olc_bolum(PIDK, prm, 3001, kayit=True)["traj"],
        "PPO-DR": olc_bolum(
            PpoKontrol(pol_dr[0]), prm, 3001, kayit=True
        )["traj"],
        "PPO-nom": olc_bolum(
            PpoKontrol(pol_nom[0]), prm, 3001, kayit=True
        )["traj"],
    }
    n = len(yol["PID"][2])
    sat = ["t,referans,ruzgar,pid_h,dr_h,nom_h,pid_s,dr_s,nom_s"]
    for i in range(n):
        sat.append(
            "%.2f,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                i * DT,
                HREF,
                yol["PID"][1][i],
                yol["PID"][0][i],
                yol["PPO-DR"][0][i],
                yol["PPO-nom"][0][i],
                (yol["PID"][3][i]),
                yol["PPO-DR"][3][i],
                yol["PPO-nom"][3][i],
            )
        )
    with open(
        os.path.join(VERI, "b74_iha_yorunge.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(sat) + "\n")
    for k, v in yol.items():
        e = v[2]
        print(
            "yorunge %-7s max|e|=%.2f (t>=5s: %.2f)  efor=%.3f"
            % (
                k,
                np.max(np.abs(e)),
                np.max(np.abs(e[100:])),
                np.mean(v[3] ** 2),
            )
        )
    print("PID kazanclari:", (kp, ki, kd))
