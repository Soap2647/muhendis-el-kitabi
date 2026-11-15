# -*- coding: utf-8 -*-
"""Bolum 74 - PPO, sifirdan (PyTorch 2.6.0, CPU).

Kirpilmis vekil amac (clip), GAE (lambda), birden cok epoch mini-
batch,
entropi bonusu, deger kaybi. Ayrik eylemde Categorical, surekli
eylemde
durumdan bagimsiz log_std ile Gauss politikasi (eylem [-1,1]'e
kirpilir).
"""

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical, Normal


def mlp(giris, cikis):
    return nn.Sequential(
        nn.Linear(giris, 64),
        nn.Tanh(),
        nn.Linear(64, 64),
        nn.Tanh(),
        nn.Linear(64, cikis),
    )


class Politika(nn.Module):
    def __init__(self, obs_dim, act_dim, ayrik):
        super().__init__()
        self.ayrik = ayrik
        self.aktor = mlp(obs_dim, act_dim)
        self.elestirmen = mlp(obs_dim, 1)
        if not ayrik:
            self.log_std = nn.Parameter(torch.full((act_dim,), -0.5))

    def dagilim(self, s):
        mu = self.aktor(s)
        if self.ayrik:
            return Categorical(logits=mu)
        return Normal(mu, self.log_std.exp())

    def deger(self, s):
        return self.elestirmen(s).squeeze(-1)


def gae(r, v, v_son, term, done, gamma, lam):
    """Genellestirilmis avantaj kestirimi.
    delta_t = r_t + gamma (1 - term_t) V(s_{t+1}) - V(s_t)
    A_t = delta_t + gamma lam (1 - done_t) A_{t+1}"""
    T = len(r)
    adv = np.zeros(T, dtype=np.float32)
    son = 0.0
    for t in reversed(range(T)):
        delta = r[t] + gamma * (1.0 - term[t]) * v_son[t] - v[t]
        son = delta + gamma * lam * (1.0 - done[t]) * son
        adv[t] = son
    return adv, adv + v


def ppo_egit(
    ortam_fn,
    obs_dim,
    act_dim,
    ayrik,
    toplam_adim,
    seed,
    eval_fn=None,
    eval_her=10000,
    T=1024,
    K=4,
    mb=64,
    lr=3e-4,
    gamma=0.99,
    lam=0.95,
    eps=0.2,
    c_v=0.5,
    c_ent=0.0,
    kirp=0.5,
):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    pol = Politika(obs_dim, act_dim, ayrik)
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    env = ortam_fn(seed)
    s = env.reset()
    adim, egri = 0, []
    while adim < toplam_adim:
        obs, nxt, acts, logps, rews, vals = [], [], [], [], [], []
        terms, dones = [], []
        for _ in range(T):
            st = torch.as_tensor(s, dtype=torch.float32)
            with torch.no_grad():
                d = pol.dagilim(st)
                a = d.sample()
                lp = d.log_prob(a)
                if not ayrik:
                    lp = lp.sum()
            ev = a.item() if ayrik else a.numpy()
            s2, r, term, trunc = env.step_ppo(ev)
            obs.append(s)
            nxt.append(s2)
            acts.append(a.numpy())
            logps.append(float(lp))
            rews.append(r)
            terms.append(float(term))
            dones.append(float(term or trunc))
            adim += 1
            s = s2
            if term or trunc:
                s = env.reset()
        O = torch.as_tensor(np.array(obs), dtype=torch.float32)
        N = torch.as_tensor(np.array(nxt), dtype=torch.float32)
        with torch.no_grad():
            V = pol.deger(O).numpy()
            Vn = pol.deger(N).numpy()
        adv, ret = gae(
            np.array(rews, np.float32),
            V,
            Vn,
            np.array(terms),
            np.array(dones),
            gamma,
            lam,
        )
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        A = torch.as_tensor(np.array(acts))
        LP = torch.as_tensor(np.array(logps), dtype=torch.float32)
        ADV = torch.as_tensor(adv)
        RET = torch.as_tensor(ret)
        for _ in range(K):
            idx = rng.permutation(T)
            for j in range(0, T, mb):
                b = idx[j : j + mb]
                d = pol.dagilim(O[b])
                if ayrik:
                    lp = d.log_prob(A[b].long())
                else:
                    lp = d.log_prob(A[b]).sum(-1)
                oran = torch.exp(lp - LP[b])
                s1 = oran * ADV[b]
                s2_ = torch.clamp(oran, 1 - eps, 1 + eps) * ADV[b]
                kayip_pi = -torch.min(s1, s2_).mean()
                kayip_v = (pol.deger(O[b]) - RET[b]).pow(2).mean()
                ent = d.entropy()
                ent = ent if ayrik else ent.sum(-1)
                kayip = kayip_pi + c_v * kayip_v - c_ent * ent.mean()
                opt.zero_grad()
                kayip.backward()
                nn.utils.clip_grad_norm_(pol.parameters(), kirp)
                opt.step()
        if eval_fn is not None and (adim // eval_her) > (
            (adim - T) // eval_her
        ):
            egri.append((adim, eval_fn(pol)))
    return pol, egri


def acgozlu_eylem(pol, s, ayrik):
    with torch.no_grad():
        st = torch.as_tensor(s, dtype=torch.float32)
        mu = pol.aktor(st)
        if ayrik:
            return int(mu.argmax())
        return np.clip(mu.numpy(), -1.0, 1.0)
