# dfa.py: DFA (beşli tanım) ve 3'e bölünebilirlik
import random


class DFA:
    """(Q, Sigma, delta, q0, F) beşlisi."""

    def __init__(self, Q, Sigma, delta, q0, F):
        self.Q, self.Sigma = set(Q), set(Sigma)
        self.delta = dict(delta)       # (durum, harf) -> durum
        self.q0, self.F = q0, set(F)

    def calistir(self, w):
        """w'nun izini (durum listesi) döndürür."""
        iz = [self.q0]
        for c in w:
            iz.append(self.delta[(iz[-1], c)])
        return iz

    def kabul(self, w):
        return self.calistir(w)[-1] in self.F


def uc_bolunebilirlik():
    """Durum = şimdiye kadarki değerin mod 3'ü."""
    delta = {(r, b): (2 * r + int(b)) % 3
             for r in range(3) for b in "01"}
    return DFA(range(3), "01", delta, 0, {0})


def dogrula(seed=36):
    m = uc_bolunebilirlik()
    sayac = 0
    for uz in range(13):               # tüm dizgiler, |w| <= 12
        for bits in range(2 ** uz):
            w = format(bits, "0%db" % uz) if uz else ""
            beklenen = (int(w, 2) if w else 0) % 3 == 0
            assert m.kabul(w) == beklenen, w
            sayac += 1
    rng = random.Random(seed)          # rastgele uzun dizgiler
    for _ in range(2000):
        n = rng.randint(13, 80)
        w = "".join(rng.choice("01") for _ in range(n))
        assert m.kabul(w) == (int(w, 2) % 3 == 0), w
        sayac += 1
    return sayac


if __name__ == "__main__":
    m = uc_bolunebilirlik()
    for w in ["1011", "1001", ""]:
        print(repr(w), m.calistir(w),
              "kabul" if m.kabul(w) else "red")
    print("sinanan dizge:", dogrula())
