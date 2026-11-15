// Dizgi testi: std::string ile karsilastirir (tohum 42)
#include <cstdio>
#include <random>
#include <string>
#include <vector>
#include "dizgi.hpp"

int main() {
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> harf(0, 25), secim(0, 2);
    std::vector<Dizgi> d(4);
    std::vector<std::string> r(4);
    long adim = 0;
    for (int it = 0; it < 20000; ++it) {
        int i = static_cast<int>(rng() % 4);
        int j = static_cast<int>(rng() % 4);
        switch (secim(rng)) {
        case 0: {                       // ekle
            char b[4];
            for (int t = 0; t < 3; ++t) b[t] = char('a' + harf(rng));
            b[3] = 0;
            d[i].ekle(b); r[i] += b; break;
        }
        case 1:                         // kopya atama
            d[i] = d[j]; r[i] = r[j]; break;
        case 2:                         // tasima (j bosalir)
            d[i] = std::move(d[j]); r[i] = r[j];
            d[j] = Dizgi(); r[j].clear(); break;
        }
        ++adim;
        for (int k = 0; k < 4; ++k) {
            if (d[k].uzunluk() != r[k].size() ||
                std::strcmp(d[k].c_str(), r[k].c_str()) != 0) {
                std::printf("HATA it=%d k=%d\n", it, k);
                return 1;
            }
        }
    }
    std::printf("%ld islem, 4 dizgi: std::string ile birebir esit\n",
                adim);
    return 0;
}
