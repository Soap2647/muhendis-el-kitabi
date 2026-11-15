# ex_dogrula.py: Çözümlü Örnek 1-3 için sayısal doğrulama.
import torch

# Örnek 1: permute ve dilimleme adresleri.
x = torch.arange(24).reshape(2, 3, 4)
y = x.permute(2, 0, 1)
print("x stride:", x.stride())
print("y = x.permute(2,0,1): shape", tuple(y.shape),
      "stride", y.stride())
print("y[3,1,2] =", y[3, 1, 2].item(),
      " x[1,2,3] =", x[1, 2, 3].item())
z = x[:, 1, ::2]
print("z = x[:,1,::2]: shape", tuple(z.shape),
      "stride", z.stride(), "offset", z.storage_offset())
print("z[1,1] =", z[1, 1].item(),
      " x[1,1,2] =", x[1, 1, 2].item())
print("y.is_contiguous():", y.is_contiguous())

# Örnek 2: f(x,y) = y^2 * ln(x) noktasında (2, 3).
xa = torch.tensor(2.0, dtype=torch.float64, requires_grad=True)
ya = torch.tensor(3.0, dtype=torch.float64, requires_grad=True)
f = torch.log(xa) * ya ** 2
f.backward()
print("\nf =", f.item(), " df/dx =", xa.grad.item(),
      " df/dy =", ya.grad.item())
print("elle: df/dx = y^2/x =", 9 / 2,
      " df/dy = 2y ln x =",
      6 * torch.log(torch.tensor(2.0)).item())
print("grad_fn:", type(f.grad_fn).__name__,
      [type(n).__name__ for n, _ in f.grad_fn.next_functions])

# Örnek 3: eşit olmayan mikro-batch 6 + 4 (N = 10).
torch.manual_seed(0)
lin = torch.nn.Linear(3, 2).double()
X = torch.randn(10, 3, dtype=torch.float64)
Y = torch.randint(0, 2, (10,))
ce_sum = torch.nn.CrossEntropyLoss(reduction="sum")
ce_mean = torch.nn.CrossEntropyLoss()


def gradyan(fn):
    lin.zero_grad()
    fn().backward()
    return lin.weight.grad.clone(), lin.bias.grad.clone()


def fark(a, b):
    return max((p - q).abs().max().item() for p, q in zip(a, b))


ref = gradyan(lambda: ce_mean(lin(X), Y))
lin.zero_grad()
for a, b in [(0, 6), (6, 10)]:
    (ce_sum(lin(X[a:b]), Y[a:b]) / 10).backward()
dogru = (lin.weight.grad.clone(), lin.bias.grad.clone())
lin.zero_grad()
for a, b in [(0, 6), (6, 10)]:
    (ce_mean(lin(X[a:b]), Y[a:b]) / 2).backward()
yanlis = (lin.weight.grad.clone(), lin.bias.grad.clone())
print("\neşit olmayan batch doğru:", fark(ref, dogru))
print("eşit olmayan batch yanlış (ortalama/2):", fark(ref, yanlis))
