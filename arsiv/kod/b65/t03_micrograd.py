# t03_micrograd.py: Bölüm 55'teki Deger ile PyTorch gradyanlarını
# karşılaştırır. Aynı ifade, aynı gradyan.
import random, math
import torch
from deger import Deger

# 1) Sabit ifade: f = tanh((a*b + a) / 10)
a = Deger(2.0); b = Deger(3.0)
f = ((a * b + a) / 10).tanh()
f.geri()
print("Deger  : f=%.6f  a.grad=%.6f  b.grad=%.6f"
      % (f.veri, a.grad, b.grad))

ta = torch.tensor(2.0, dtype=torch.float64, requires_grad=True)
tb = torch.tensor(3.0, dtype=torch.float64, requires_grad=True)
tf = torch.tanh((ta * tb + ta) / 10)
tf.backward()
print("torch  : f=%.6f  a.grad=%.6f  b.grad=%.6f"
      % (tf.item(), ta.grad.item(), tb.grad.item()))

# 2) Rastgele ifadeler: 200 tohumlu ağaç, göreli hata ölçümü.
OPS = ["+", "*", "tanh"]


def kur(rng, n_gir, derinlik):
    # Aynı ağacı iki motorda da kurabilmek için bir tarif üretir.
    if derinlik == 0:
        return ("g", rng.randrange(n_gir))
    op = rng.choice(OPS)
    if op == "tanh":
        return (op, kur(rng, n_gir, derinlik - 1))
    return (op, kur(rng, n_gir, derinlik - 1),
            kur(rng, n_gir, derinlik - 1))


def degerle(t, gir):
    if t[0] == "g":
        return gir[t[1]]
    if t[0] == "tanh":
        return degerle(t[1], gir).tanh()
    x, y = degerle(t[1], gir), degerle(t[2], gir)
    return x + y if t[0] == "+" else x * y


def tdegerle(t, gir):
    if t[0] == "g":
        return gir[t[1]]
    if t[0] == "tanh":
        return torch.tanh(tdegerle(t[1], gir))
    x, y = tdegerle(t[1], gir), tdegerle(t[2], gir)
    return x + y if t[0] == "+" else x * y


en_kotu = 0.0
for tohum in range(200):
    rng = random.Random(tohum)
    agac = kur(rng, 3, 4)
    vals = [rng.uniform(-1, 1) for _ in range(3)]
    gir = [Deger(v) for v in vals]
    out = degerle(agac, gir)
    out.geri()
    tg = [torch.tensor(v, dtype=torch.float64, requires_grad=True)
          for v in vals]
    to = tdegerle(agac, tg)
    to.backward()
    for dg, tt in zip(gir, tg):
        # Girdi ifadede hiç kullanılmadıysa gradyan 0'dır.
        ref = 0.0 if tt.grad is None else tt.grad.item()
        hata = abs(dg.grad - ref) / max(1.0, abs(ref))
        en_kotu = max(en_kotu, hata)
print("200 rastgele ifade, en kötü göreli hata: %.3e" % en_kotu)
