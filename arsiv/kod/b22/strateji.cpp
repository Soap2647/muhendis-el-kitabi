// strateji.cpp: derleme zamani ve calisma zamani stratejisi (22.9)
#include <algorithm>
#include <cstddef>
#include <functional>
#include <iostream>
#include <numeric>
#include <vector>

using Pencere = std::vector<double>;
using Strateji = std::function<double(const Pencere&)>;

double ortalama(const Pencere& w) {
    return std::accumulate(w.begin(), w.end(), 0.0) / w.size();
}

double medyan(Pencere w) {               // kopya: siralanacak
    std::sort(w.begin(), w.end());
    return w[w.size() / 2];              // tek uzunlukta pencere
}

Pencere uygula(const Strateji& s, const Pencere& v, std::size_t n) {
    Pencere out;
    for (std::size_t i = 0; i + n <= v.size(); ++i)
        out.push_back(s(Pencere(v.begin() + i, v.begin() + i + n)));
    return out;
}

void yazdir(const char* ad, const Pencere& p) {
    std::cout << ad << " ";
    for (double x : p) std::cout << x << " ";
    std::cout << "\n";
}

int main() {
    Pencere veri{20, 21, 90, 22, 21, 23, 22};   // 90: bozuk olcum
    yazdir("ortalama", uygula(ortalama, veri, 3));
    yazdir("medyan  ", uygula(medyan, veri, 3));

    std::vector<int> sayilar{3, 1, 4, 1, 5};
    std::sort(sayilar.begin(), sayilar.end(), std::greater<int>());
    for (int x : sayilar) std::cout << x << " ";
    std::cout << "\n";
}
