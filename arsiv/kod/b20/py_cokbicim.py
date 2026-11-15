# Python'da cok bicimlilik: abc.ABC, Protocol ve duck typing
from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass, field

class Surucu(ABC):
    @abstractmethod
    def oku(self) -> int: ...
    def tani(self) -> str:             # somut ortak davranis
        return "surucu:" + type(self).__name__

class KlavyeSurucusu(Surucu):
    def oku(self) -> int:
        return 0x1C

try:
    Surucu()
except TypeError as e:
    print("TypeError:", e)
print(KlavyeSurucusu().tani(), KlavyeSurucusu().oku())

class Okunabilir(Protocol):            # yapisal: miras sart degil
    def oku(self) -> int: ...

class EskiSensor:                      # Surucu'den turemiyor
    def oku(self) -> int:
        return 42

def olc(kaynak: Okunabilir) -> int:
    return kaynak.oku() * 2

print(olc(EskiSensor()), olc(KlavyeSurucusu()))

@dataclass(order=True)
class Olcum:
    zaman: float
    deger: float
    etiketler: list = field(default_factory=list, compare=False)

o1 = Olcum(1.0, 5.0)
o2 = Olcum(1.0, 5.0)
print(o1 == o2, o1 < Olcum(2.0, 0.0))
print(o1)
