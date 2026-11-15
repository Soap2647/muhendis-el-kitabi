# t02_autograd.py: requires_grad, grad_fn, birikim, no_grad, detach.
import torch

a = torch.tensor(2.0, requires_grad=True)
b = torch.tensor(3.0, requires_grad=True)
c = a * b + a
f = torch.tanh(c / 10)
print("f =", round(f.item(), 6))
print("f.grad_fn:", type(f.grad_fn).__name__)
print("f.grad_fn.next_functions:")
print("  ", [type(n).__name__ for n, _ in f.grad_fn.next_functions])
print("c.grad_fn:", type(c.grad_fn).__name__)
print("a.is_leaf:", a.is_leaf, " c.is_leaf:", c.is_leaf)

f.backward()
print("\nbirinci geçiş: a.grad =", round(a.grad.item(), 6),
      " b.grad =", round(b.grad.item(), 6))

# Birikim: zero_grad olmadan ikinci backward gradyanı toplar.
(a * b).sum().backward()
print("ikinci geçiş (sıfırlamadan): a.grad =",
      round(a.grad.item(), 6))
a.grad = None
b.grad = None
(a * b).sum().backward()
print("sıfırlandıktan sonra:        a.grad =", a.grad.item())

# Yaprak olmayan tensör: grad varsayılan olarak doldurulmaz.
u = a * 2
(u ** 2).sum().backward()
print("\nyaprak olmayan u.is_leaf:", u.is_leaf)
u2 = a * 2
u2.retain_grad()
(u2 ** 2).sum().backward()
print("retain_grad sonrası u2.grad:", u2.grad.item())

# no_grad ve detach: gradyan izi kesilir.
with torch.no_grad():
    d = a * b
print("\nno_grad içinde requires_grad:", d.requires_grad)
e = (a * b).detach()
print("detach requires_grad:", e.requires_grad)

# In-place çatışması: geri adımın ihtiyaç duyduğu çıktı değişti.
p = torch.tensor([1.0, 2.0], requires_grad=True)
q = p.sigmoid()
q.add_(1.0)
try:
    q.sum().backward()
except RuntimeError as err:
    print("\nin-place hatası:", str(err)[:44], "...")
