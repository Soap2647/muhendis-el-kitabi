// ocp_indirim.cpp: if zinciri ve polimorfizm (C++17)
#include <cstdio>
#include <memory>
#include <vector>

struct Musteri {
    bool ogrenci;
    bool bayram;
    bool sadakat;   // 'sonradan eklenen' alan
};

// ONCE: her yeni kural bu govdeyi degistirmeyi gerektirir
double indirim_once(double t, const Musteri &m)
{
    if (m.ogrenci) t *= 0.80;
    if (m.bayram) t *= 0.90;
    if (m.sadakat) t *= 0.95;
    return t;
}

// SONRA: kural = sinif. Yeni kural = yeni sinif + listeye ekleme
class IndirimKurali {
public:
    virtual ~IndirimKurali() = default;
    virtual double uygula(double t, const Musteri &m) const = 0;
};

class OgrenciIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.ogrenci ? t * 0.80 : t; }
};

class BayramIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.bayram ? t * 0.90 : t; }
};

class SadakatIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.sadakat ? t * 0.95 : t; }
};

double toplam(
    const std::vector<std::unique_ptr<IndirimKurali>> &kurallar,
    double t, const Musteri &m)
{
    for (const auto &k : kurallar)
        t = k->uygula(t, m);
    return t;
}

int main()
{
    std::vector<std::unique_ptr<IndirimKurali>> kurallar;
    kurallar.push_back(std::make_unique<OgrenciIndirimi>());
    kurallar.push_back(std::make_unique<BayramIndirimi>());
    kurallar.push_back(std::make_unique<SadakatIndirimi>());

    const Musteri ms[] = {{false, false, false}, {true, false, false},
                          {true, true, true}};
    for (const Musteri &m : ms) {
        double a = indirim_once(100.0, m);
        double b = toplam(kurallar, 100.0, m);
        std::printf("once=%.4f sonra=%.4f esit=%d\n", a, b, a == b);
    }
    return 0;
}
