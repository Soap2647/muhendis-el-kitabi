// Ornek 3 izi: kopya, tasima ve atama sirasinda dizgiler
#include <cstdio>
#include <utility>
#include "dizgi.hpp"

static void goster(const char* ad, const Dizgi& d) {
    std::printf("%s = \"%s\" (uzunluk %zu)\n",
                ad, d.c_str(), d.uzunluk());
}

int main() {
    Dizgi a("Mert");
    Dizgi b = a;                 // derin kopya
    a.ekle("OS");                // a degisir, b etkilenmez
    goster("a", a);
    goster("b", b);
    Dizgi c = std::move(a);      // tasima: a bosalir
    goster("a", a);
    goster("c", c);
    c = b;                       // kopya atama
    goster("c", c);
    return 0;
}
