# t05_module.py: nn.Module ağacı, state_dict, buffer ve hook.
import torch
import torch.nn as nn

torch.manual_seed(0)


class Ag(nn.Module):
    def __init__(self):
        super().__init__()
        self.ust = nn.Sequential(
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.5),
        )
        self.cikis = nn.Linear(32, 10)

    def forward(self, x):
        return self.cikis(self.ust(x))


ag = Ag()
print("modül ağacı (ad, sınıf):")
for ad, m in ag.named_modules():
    print(f"  {ad or '(kök)':12s} {type(m).__name__}")
print("\nparametreler:")
for ad, p in ag.named_parameters():
    print(f"  {ad:22s} {str(tuple(p.shape)):12s}")
print("buffer'lar:")
for ad, _ in ag.named_buffers():
    print("  ", ad)
print("state_dict anahtarları:")
for k in ag.state_dict():
    print("  ", k)
print("toplam parametre:",
      sum(p.numel() for p in ag.parameters()))

ag.train()
print("\ntrain modu: dropout =", ag.ust[3].training,
      " bn =", ag.ust[1].training)
ag.eval()
print("eval modu : dropout =", ag.ust[3].training,
      " bn =", ag.ust[1].training)

# Hook: ileri geçişte aktivasyonun ortalama ve std değerini topla.
izler = {}


def ileri_hook(ad):
    def kanca(modul, girdi, cikti):
        izler[ad] = (cikti.mean().item(), cikti.std().item())
    return kanca


kanca = ag.ust[2].register_forward_hook(ileri_hook("relu"))
ag.train()
ag(torch.randn(64, 64))
print("\nrelu aktivasyonu (train):",
      {k: tuple(round(v, 4) for v in t) for k, t in izler.items()})
kanca.remove()
