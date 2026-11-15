// ayar.cpp: Builder deseni (C++17, Bolum 22.4)
#include <iostream>
#include <stdexcept>

struct UcusAyar {
    double hiz = 10.0, irtifa = 50.0, batarya = 80.0;
    bool gps = true, kayit = false;
};

class AyarInsaatcisi {
public:
    AyarInsaatcisi& hiz(double v) { a_.hiz = v; return *this; }
    AyarInsaatcisi& irtifa(double v) { a_.irtifa = v; return *this; }
    AyarInsaatcisi& kayit(bool v) { a_.kayit = v; return *this; }

    UcusAyar build() const {
        if (!(a_.hiz > 0 && a_.hiz <= 30))
            throw std::invalid_argument("hiz 0..30 m/s olmali");
        if (!(a_.batarya >= 0 && a_.batarya <= 100))
            throw std::invalid_argument("batarya 0..100 olmali");
        return a_;
    }

private:
    UcusAyar a_;
};

int main() {
    UcusAyar a = AyarInsaatcisi().hiz(12).irtifa(120)
                                 .kayit(true).build();
    std::cout << "hiz=" << a.hiz << " irtifa=" << a.irtifa
              << " kayit=" << a.kayit << "\n";
    try {
        AyarInsaatcisi().hiz(40).build();
    } catch (const std::invalid_argument& e) {
        std::cout << "reddedildi: " << e.what() << "\n";
    }
}
