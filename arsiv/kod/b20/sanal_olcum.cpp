// Sanal cagri maliyeti: ayni is, farkli tahmin edilebilirlik
#include <chrono>
#include <cstdio>
#include <random>
#include <vector>

struct Sekil {
    virtual double alan() const = 0;
    virtual ~Sekil() = default;
};
struct Daire : Sekil {
    double r;
    explicit Daire(double x) : r(x) {}
    double alan() const override { return 3.14159 * r * r; }
};
struct Kare : Sekil {
    double a;
    explicit Kare(double x) : a(x) {}
    double alan() const override { return a * a; }
};

// Sanal olmayan: tur etiketi + dal (switch)
struct Etiketli { int tur; double v; };
__attribute__((noinline))
double etiketli_topla(const std::vector<Etiketli>& x) {
    double s = 0;
    for (const auto& e : x)
        s += (e.tur == 0) ? 3.14159 * e.v * e.v : e.v * e.v;
    return s;
}

__attribute__((noinline))
double sanal_topla(const std::vector<Sekil*>& x) {
    double s = 0;
    for (const Sekil* p : x) s += p->alan();   // dolayli cagri
    return s;
}

template <class F>
double sure_ms(F f, double& sonuc) {
    auto t0 = std::chrono::steady_clock::now();
    sonuc = f();
    auto t1 = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::milli>(t1 - t0).count();
}

int main(int argc, char** argv) {
    const std::size_t n = argc > 1 ? std::stoul(argv[1]) : 1u << 20;
    const int tekrar = 50;
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> coin(0, 1);

    // Dagitim 1: hepsi ayni tur (tahmin edilebilir)
    // Dagitim 2: rastgele karisik (dal ve hedef tahmin edilemez)
    struct Durum { const char* ad; bool karisik; };
    Durum durumlar[2] = { {"tek_tur", false}, {"karisik", true} };
    std::printf("n=%zu tekrar=%d\n", n, tekrar);
    std::printf("yontem,dagitim,ms\n");
    for (const Durum& d : durumlar) {
        std::vector<Daire> dz; std::vector<Kare> kz;
        std::vector<Sekil*> pv; std::vector<Etiketli> ev;
        dz.reserve(n); kz.reserve(n);
        for (std::size_t i = 0; i < n; ++i) {
            bool kare = d.karisik ? coin(rng) == 1 : false;
            double v = 1.0 + (i % 7) * 0.5;
            if (kare) kz.emplace_back(v), ev.push_back({1, v});
            else      dz.emplace_back(v), ev.push_back({0, v});
        }
        // Sanal vektor, nesneler hazir olduktan sonra kurulur
        std::size_t di = 0, ki = 0;
        for (std::size_t i = 0; i < n; ++i) {
            bool kare = d.karisik ? ev[i].tur == 1 : false;
            pv.push_back(kare ? static_cast<Sekil*>(&kz[ki++])
                              : static_cast<Sekil*>(&dz[di++]));
        }
        double s1 = 0, s2 = 0, t1 = 0, t2 = 0;
        for (int k = 0; k < tekrar; ++k) {
            t1 += sure_ms([&] { return etiketli_topla(ev); }, s1);
            t2 += sure_ms([&] { return sanal_topla(pv); }, s2);
        }
        std::printf("etiketli,%s,%.3f\n", d.ad, t1 / tekrar);
        std::printf("sanal,%s,%.3f\n", d.ad, t2 / tekrar);
        std::printf("# sonuc_farki=%.9g\n", s1 - s2);
    }
    return 0;
}
