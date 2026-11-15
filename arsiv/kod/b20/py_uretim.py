# dataclass __init__ kodunu izle: _create_fn'e giden govdeyi yazdir
import dataclasses

orijinal = dataclasses._create_fn

def izle(name, args, body, **kw):
    if name == "__init__":
        print("args :", args)
        for satir in body:
            print("govde:", satir)
    return orijinal(name, args, body, **kw)

dataclasses._create_fn = izle

@dataclasses.dataclass
class Olcum:
    zaman: float
    deger: float = 0.0

@dataclasses.dataclass(frozen=True)
class Sabit:
    kod: int

o = Olcum(1.5)
print(o)
try:
    s = Sabit(7)
    s.kod = 8
except dataclasses.FrozenInstanceError as e:
    print("FrozenInstanceError:", e)
