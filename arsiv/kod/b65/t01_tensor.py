# t01_tensor.py: dtype, cihaz, şekil, stride, view ve yayınlama.
import torch

x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
print("shape:", tuple(x.shape), "dtype:", x.dtype)
print("device:", x.device, "stride:", x.stride())
print("offset:", x.storage_offset())
print("storage bayt:", x.untyped_storage().nbytes())

ptr = x.untyped_storage().data_ptr()
y = x.t()                      # transpose: veri kopyalanmaz
print("\ny = x.t()  shape:", tuple(y.shape), "stride:", y.stride())
print("aynı storage:", y.untyped_storage().data_ptr() == ptr)
print("y.is_contiguous():", y.is_contiguous())
try:
    y.view(-1)
except RuntimeError as e:
    print("view hatası:", str(e)[:44], "...")
r = y.reshape(-1)              # reshape: gerekirse kopyalar
print("reshape(-1) aynı storage:",
      r.untyped_storage().data_ptr() == ptr)
c = y.contiguous()
print("contiguous stride:", c.stride(),
      "aynı storage:", c.untyped_storage().data_ptr() == ptr)

z = x[1:, ::2]                 # dilimleme: offset ve stride değişir
print("\nx[1:, ::2] shape:", tuple(z.shape), "stride:", z.stride(),
      "offset:", z.storage_offset())

a = torch.zeros(3, 1)
b = torch.arange(4.0)
print("\nyayın (3,1)+(4,) ->", tuple((a + b).shape))
print(a + b)

print("\nfinfo:")
for dt in (torch.float16, torch.bfloat16, torch.float32):
    f = torch.finfo(dt)
    print(f"{str(dt):15s} max={f.max:.4e} eps={f.eps:.4e} "
          f"bit={f.bits}")
