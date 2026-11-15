# -*- coding: utf-8 -*-
"""Bölüm 70 - Küçük GPT'yi sıfırdan ön-eğitmek (dil modelleme).

Kullanım:
  python g05_gpt.py --seed 0 --tag ana --save 1
  python g05_gpt.py --seed 0 --d 64 --L 2 --frac 0.25 --tag olcek
Veri: tok_egitim.npy (eğitim), tok_dogrulama.npy (en iyi noktayı
seçmek
için), tok_test.npy (yalnızca son raporlama). Pencereler bloklardır:
her blok ctx+1 tokendir; hedef, girdinin bir kaydırılmış hâlidir.
"""

import argparse, csv, math, os, time
import numpy as np
import torch
from gpt_b70 import MiniGPT, parametre_say

K = os.path.dirname(os.path.abspath(__file__))
V = 2149


def bloklar(dizi, ctx):
    n = len(dizi) // (ctx + 1)
    return torch.tensor(
        dizi[: n * (ctx + 1)].reshape(n, ctx + 1), dtype=torch.long
    )


def degerlendir(model, veri, cihaz, ctx):
    model.eval()
    toplam, sayi = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(veri), 64):
            b = veri[i : i + 64].to(cihaz)
            x, y = b[:, :-1], b[:, 1:]
            with torch.autocast(
                cihaz.type, enabled=cihaz.type == "cuda"
            ):
                _, kayip = model(x, y)
            toplam += kayip.item() * y.numel()
            sayi += y.numel()
    model.train()
    return math.exp(toplam / sayi)


def egit(
    seed=0,
    d=128,
    L=4,
    bas=4,
    ctx=128,
    steps=3000,
    frac=1.0,
    lr=1e-3,
    batch=32,
    tag="ana",
    save=False,
    log=True,
):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    cihaz = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    tr = np.load(os.path.join(K, "tok_egitim.npy")).astype(np.int64)
    va = np.load(os.path.join(K, "tok_dogrulama.npy")).astype(
        np.int64
    )
    te = np.load(os.path.join(K, "tok_test.npy")).astype(np.int64)
    B_tr = bloklar(tr, ctx)
    # Veri ölçeği: rastgele bir blok alt kümesi (sabit tohumla)
    secim = rng.choice(
        len(B_tr), size=int(frac * len(B_tr)), replace=False
    )
    B_tr = B_tr[torch.as_tensor(secim)]
    B_va, B_te = bloklar(va, ctx), bloklar(te, ctx)

    model = MiniGPT(V, ctx=ctx, d=d, L=L, bas=bas, dusme=0.1).to(
        cihaz
    )
    dec = [p for p in model.parameters() if p.dim() >= 2]
    nodec = [p for p in model.parameters() if p.dim() < 2]
    opt = torch.optim.AdamW(
        [
            {"params": dec, "weight_decay": 0.1},
            {"params": nodec, "weight_decay": 0.0},
        ],
        lr=lr,
        betas=(0.9, 0.95),
    )
    isinma = 200

    def takvim(adim):
        if adim < isinma:
            return lr * (adim + 1) / isinma
        ilerleme = (adim - isinma) / max(1, steps - isinma)
        return lr * (
            0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * ilerleme))
        )

    amp = cihaz.type == "cuda"
    olcekleyici = torch.amp.GradScaler("cuda", enabled=amp)
    en_iyi = (float("inf"), None, 0)
    kayitlar = []
    t0 = time.time()
    kayip_top = 0.0
    for adim in range(steps):
        for g in opt.param_groups:
            g["lr"] = takvim(adim)
        sec = torch.randint(len(B_tr), (batch,))
        b = B_tr[sec].to(cihaz)
        x, y = b[:, :-1], b[:, 1:]
        with torch.autocast(cihaz.type, enabled=amp):
            _, kayip = model(x, y)
        opt.zero_grad(set_to_none=True)
        olcekleyici.scale(kayip).backward()
        olcekleyici.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        olcekleyici.step(opt)
        olcekleyici.update()
        kayip_top += kayip.item()
        if (adim + 1) % 250 == 0 or adim == steps - 1:
            vp = degerlendir(model, B_va, cihaz, ctx)
            egitim_loss = (
                kayip_top / 250
                if (adim + 1) % 250 == 0
                else kayip_top / ((adim % 250) + 1)
            )
            kayitlar.append((adim + 1, egitim_loss, vp))
            if log:
                print(
                    "adım %5d  eğitim kayıp=%.4f  doğrulama "
                    "ppl=%.2f  (%.0f sn)"
                    % (adim + 1, egitim_loss, vp, time.time() - t0)
                )
            kayip_top = 0.0
            if vp < en_iyi[0]:
                en_iyi = (
                    vp,
                    {
                        k: v.detach().clone()
                        for k, v in model.state_dict().items()
                    },
                    adim + 1,
                )
    sure = time.time() - t0
    model.load_state_dict(en_iyi[1])
    test_ppl = degerlendir(model, B_te, cihaz, ctx)
    sonuc = {
        "seed": seed,
        "d": d,
        "L": L,
        "frac": frac,
        "parametre": parametre_say(model),
        "en_iyi_adim": en_iyi[2],
        "dogrulama_ppl": en_iyi[0],
        "test_ppl": test_ppl,
        "sure_sn": sure,
        "adim_basi_ms": 1000 * sure / steps,
        "cihaz": str(cihaz),
        "egri": kayitlar,
        "model": model,
    }
    if save:
        torch.save(
            {
                "state": en_iyi[1],
                "d": d,
                "L": L,
                "bas": bas,
                "ctx": ctx,
            },
            os.path.join(K, "gpt_%s_%d.pt" % (tag, seed)),
        )
    with open(
        os.path.join(K, "egri_%s_%d.csv" % (tag, seed)),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        cw = csv.writer(f)
        cw.writerow(["adim", "egitim_kayip", "dogrulama_ppl"])
        cw.writerows(kayitlar)
    return sonuc


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--d", type=int, default=128)
    p.add_argument("--L", type=int, default=4)
    p.add_argument("--bas", type=int, default=4)
    p.add_argument("--steps", type=int, default=3000)
    p.add_argument("--frac", type=float, default=1.0)
    p.add_argument("--tag", type=str, default="ana")
    p.add_argument("--save", type=int, default=0)
    a = p.parse_args()
    s = egit(
        seed=a.seed,
        d=a.d,
        L=a.L,
        bas=a.bas,
        steps=a.steps,
        frac=a.frac,
        tag=a.tag,
        save=bool(a.save),
    )
    print(
        "parametre=%d  en iyi adım=%d  doğrulama ppl=%.2f  "
        "test ppl=%.2f  "
        "süre=%.0f sn  adım başı=%.1f ms  cihaz=%s"
        % (
            s["parametre"],
            s["en_iyi_adim"],
            s["dogrulama_ppl"],
            s["test_ppl"],
            s["sure_sn"],
            s["adim_basi_ms"],
            s["cihaz"],
        )
    )
