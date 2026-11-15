// Nesne dilimleme (slicing): Tureyen degerle Taban'a kopyalanirsa
#include <cstdio>

struct Taban {
    int kimlik = 1;
    virtual const char* ad() const { return "Taban"; }
    virtual ~Taban() = default;
};

struct Tureyen : Taban {
    int ek = 99;                  // Taban'da olmayan uye
    const char* ad() const override { return "Tureyen"; }
};

void goster_deger(Taban t) {      // deger ile alir: dilimlenir
    std::printf("deger  : %s kimlik=%d\n", t.ad(), t.kimlik);
}
void goster_ref(const Taban& t) { // referans ile alir: dilimlenmez
    std::printf("referans: %s kimlik=%d\n", t.ad(), t.kimlik);
}

int main() {
    Tureyen t;
    t.kimlik = 7;
    // Taban kopyasi: ad() Taban'i dondurur
    goster_deger(t);
    goster_ref(t);                // gercek tur: Tureyen
    Taban kopya = t;              // ayni dilimleme, atama ile
    std::printf("atama  : %s\n", kopya.ad());
    std::printf("sizeof(Taban)=%zu sizeof(Tureyen)=%zu\n",
                sizeof(Taban), sizeof(Tureyen));
    return 0;
}
