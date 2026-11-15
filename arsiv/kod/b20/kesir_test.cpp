// Kesir: rastgele islemler + invariant denetimi (tohum 42)
#include <cstdio>
#include <random>
#include "kesir.hpp"

static bool gecerli(const Kesir& k) {
    long g = std::gcd(std::labs(k.pay()), k.payda());
    return k.payda() > 0 && g == 1;
}

int main() {
    std::mt19937 rng(42);
    std::uniform_int_distribution<long> d(-20, 20);
    long sayac = 0;
    for (int i = 0; i < 100000; ++i) {
        long p = d(rng), q = d(rng);
        if (q == 0) { q = 1; }
        Kesir a(p, q), b(d(rng) == 0 ? 1 : d(rng), 3);
        Kesir s = a + b, m = a * b;
        if (!gecerli(s) || !gecerli(m)) {
            std::printf("IHLAL\n");
            return 1;
        }
        if (a == b && !(a < b) && !(b < a)) ++sayac;
    }
    try {
        Kesir hata(1, 0);
        std::printf("olmamali: %ld\n", hata.pay());
    } catch (const std::invalid_argument& e) {
        std::printf("beklenen istisna: %s\n", e.what());
    }
    Kesir x(6, -4);
    std::printf("6/-4 -> %ld/%ld\n", x.pay(), x.payda());
    std::printf("1/2 + 1/3 = %ld/%ld\n",
                (Kesir(1, 2) + Kesir(1, 3)).pay(),
                (Kesir(1, 2) + Kesir(1, 3)).payda());
    std::printf("100000 islem, invariant tutuyor (esit sayac=%ld)\n",
                sayac);
    return 0;
}
