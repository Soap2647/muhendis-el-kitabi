import random
from abc import ABC, abstractmethod


class Olcekleyici(ABC):
    @abstractmethod
    def donustur(self, ham: float) -> float: ...


class Sicaklik(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return ham * 0.1 - 40.0


class Basinc(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return ham * 0.01


class Nem(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return min(max(ham, 0.0), 100.0)


def olc_kosul(tip, ham):
    if tip == "sicaklik":
        return ham * 0.1 - 40.0
    elif tip == "basinc":
        return ham * 0.01
    elif tip == "nem":
        return min(max(ham, 0.0), 100.0)
    raise ValueError(tip)


SINIFLAR = {"sicaklik": Sicaklik(), "basinc": Basinc(), "nem": Nem()}

if __name__ == "__main__":
    rng = random.Random(42)
    uyusmayan = 0
    for _ in range(10000):
        tip = rng.choice(["sicaklik", "basinc", "nem"])
        ham = rng.uniform(-500.0, 150000.0)
        if SINIFLAR[tip].donustur(ham) != olc_kosul(tip, ham):
            uyusmayan += 1
    print("uyusmayan:", uyusmayan)
