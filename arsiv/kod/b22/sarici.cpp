// sarici.cpp: nesne dekoratorleri zinciri (C++17, Bolum 22.7)
#include <iostream>
#include <memory>
#include <stdexcept>

struct Okuyucu {
    virtual ~Okuyucu() = default;
    virtual double oku() = 0;
};

struct Ham : Okuyucu {
    int cagri = 0;
    double oku() override {
        ++cagri;
        if (cagri == 2) throw std::runtime_error("gecici hata");
        return 20.0 + cagri;
    }
};

struct Onbellek : Okuyucu {
    std::unique_ptr<Okuyucu> ic;
    bool var = false;
    double son = 0.0;
    explicit Onbellek(std::unique_ptr<Okuyucu> i)
        : ic(std::move(i)) {}
    double oku() override {
        if (!var) { son = ic->oku(); var = true; }
        return son;
    }
};

struct Yeniden : Okuyucu {
    std::unique_ptr<Okuyucu> ic;
    int deneme;
    Yeniden(std::unique_ptr<Okuyucu> i, int d)
        : ic(std::move(i)), deneme(d) {}
    double oku() override {
        for (int i = 0;; ++i) {
            try {
                return ic->oku();
            } catch (const std::runtime_error&) {
                if (i == deneme - 1) throw;
            }
        }
    }
};

int main() {
    auto ham = std::make_unique<Ham>();
    Ham* h = ham.get();                 // sayaci okumak icin
    Yeniden y(std::move(ham), 3);
    std::cout << "1. yeniden: " << y.oku()
              << " ham cagri: " << h->cagri << "\n";
    std::cout << "2. yeniden: " << y.oku()
              << " ham cagri: " << h->cagri << "\n";

    Onbellek z(std::make_unique<Yeniden>(std::make_unique<Ham>(), 3));
    std::cout << "onbellek: " << z.oku() << " " << z.oku() << "\n";
}
