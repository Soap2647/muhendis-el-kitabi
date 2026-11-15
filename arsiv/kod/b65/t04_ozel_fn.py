# t04_ozel_fn.py: özel autograd Function ve gradcheck.
import torch


class Softplus(torch.autograd.Function):
    # softplus(x) = log(1 + e^x), sayısal olarak kararlı biçimde.
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        # max(x,0) + log(1 + e^{-|x|}): e^x hiç hesaplanmaz.
        return x.clamp_min(0) + torch.log1p(torch.exp(-x.abs()))

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        return grad_out * torch.sigmoid(x)


def naif(x):
    return torch.log1p(torch.exp(x))


x = torch.tensor([-100.0, 0.0, 100.0], requires_grad=True)
ileri = Softplus.apply(x).tolist()
print("kararlı ileri :", [f"{v:.6g}" for v in ileri])
print("naif ileri    :", naif(x).detach().tolist())
Softplus.apply(x).sum().backward()
print("kararlı grad  :", x.grad.tolist())
x.grad = None
naif(x).sum().backward()
print("naif grad      :", x.grad.tolist())

xd = torch.linspace(-5, 5, 9, dtype=torch.float64, requires_grad=True)
ok = torch.autograd.gradcheck(Softplus.apply, (xd,))
print("\ngradcheck (float64, 9 nokta):", ok)

# İkinci dereceden türev: f = x^3, f' = 3x^2, f'' = 6x (x = 3).
y = torch.tensor(3.0, requires_grad=True)
d1, = torch.autograd.grad(y ** 3, y, create_graph=True)
d2, = torch.autograd.grad(d1, y)
print("f'(3) = %.1f, f''(3) = %.1f" % (d1.item(), d2.item()))
