// adaptor.cpp: eski surucuyu yeni arayuze uyarlamak (C++17, 22.6)
#include <iostream>
#include <vector>

struct Sicaklik {                       // hedef arayuz
    virtual ~Sicaklik() = default;
    virtual double celsius() const = 0;
};

struct EskiSurucu {                // uyarlanan: ADC (0..4095)
    std::vector<int> degerler;
    int adc_oku(int kanal) const { return degerler[kanal]; }
};

class Uyarlayici : public Sicaklik {    // adapter
public:
    Uyarlayici(const EskiSurucu& e, int kanal) : e_(e), k_(kanal) {}

    double celsius() const override {
        double gerilim = e_.adc_oku(k_) / 4095.0 * 3.3;
        return gerilim / 0.010;         // 10 mV/derece varsayimi
    }

private:
    const EskiSurucu& e_;
    int k_;
};

void yazdir(const Sicaklik& s) {
    std::cout << s.celsius() << " C\n";
}

int main() {
    EskiSurucu e{{1024, 2048, 3000}};
    for (int k = 0; k < 3; ++k)
        yazdir(Uyarlayici(e, k));
}
