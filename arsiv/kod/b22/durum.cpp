// durum.cpp: IHA ucus modlari, durum nesneleri (C++17, Bolum 22.12)
#include <iostream>
#include <stdexcept>
#include <string>

enum class Olay { KalkisEmri, IrtifaUlasti, InisEmri, PistTemas };

struct Durum;
const Durum& yerde();
const Durum& kalkis();
const Durum& seyir();
const Durum& inis();

struct Durum {                           // soyut durum
    virtual ~Durum() = default;
    virtual const char* ad() const = 0;
    // Gecerli gecis: yeni durum. Gecersiz: nullptr.
    virtual const Durum* gec(Olay) const { return nullptr; }
};

struct Yerde : Durum {
    const char* ad() const override { return "YERDE"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::KalkisEmri ? &kalkis() : nullptr;
    }
};

struct Kalkis : Durum {
    const char* ad() const override { return "KALKIS"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::IrtifaUlasti ? &seyir() : nullptr;
    }
};

struct Seyir : Durum {
    const char* ad() const override { return "SEYIR"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::InisEmri ? &inis() : nullptr;
    }
};

struct Inis : Durum {
    const char* ad() const override { return "INIS"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::PistTemas ? &yerde() : nullptr;
    }
};

const Durum& yerde() { static Yerde s; return s; }
const Durum& kalkis() { static Kalkis s; return s; }
const Durum& seyir() { static Seyir s; return s; }
const Durum& inis() { static Inis s; return s; }

class Ucak {
public:
    void olay(Olay e) {
        const Durum* y = durum_->gec(e);
        if (!y)
            throw std::runtime_error(std::string(durum_->ad()) +
                                     " durumunda olay yok");
        durum_ = y;                      // hata yoksa durum degisir
    }
    const char* ad() const { return durum_->ad(); }
    void durum_ata(const Durum& d) { durum_ = &d; }

private:
    const Durum* durum_ = &yerde();
};

int main() {
    const Durum* durumlar[] = {&yerde(), &kalkis(),
                               &seyir(), &inis()};
    const Olay olaylar[] = {Olay::KalkisEmri, Olay::IrtifaUlasti,
                            Olay::InisEmri, Olay::PistTemas};
    int gecerli = 0, reddedilen = 0;
    for (const Durum* d : durumlar)
        for (Olay e : olaylar) {
            Ucak u;
            u.durum_ata(*d);
            try {
                u.olay(e);
                ++gecerli;
            } catch (const std::runtime_error&) {
                ++reddedilen;
            }
        }
    std::cout << "gecerli: " << gecerli << " reddedilen: "
              << reddedilen << "\n";
    Ucak u;
    u.olay(Olay::KalkisEmri);
    std::cout << "kalkis sonrasi: " << u.ad() << "\n";
    try {
        u.olay(Olay::InisEmri);
    } catch (const std::runtime_error& e) {
        std::cout << "hata: " << e.what() << "\n";
    }
    std::cout << "hata sonrasi durum: " << u.ad() << "\n";
}
