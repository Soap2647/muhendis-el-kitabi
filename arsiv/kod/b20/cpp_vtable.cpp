// C++ ayni islemi derleyiciye yaptirir: virtual
#include <cstdio>
#include <cstddef>

class Sekil {
public:
    virtual double alan() const = 0;     // saf sanal (soyut)
    virtual void yazdir() const = 0;
    virtual ~Sekil() = default;          // sanal yikici
};

class Daire : public Sekil {
    double r_;
public:
    explicit Daire(double r) : r_(r) {}
    double alan() const override {
        return 3.14159265358979 * r_ * r_;
    }
    void yazdir() const override {
        std::printf("Daire r=%.1f\n", r_);
    }
};

class Dikdortgen : public Sekil {
    double a_, b_;
public:
    Dikdortgen(double a, double b) : a_(a), b_(b) {}
    double alan() const override { return a_ * b_; }
    void yazdir() const override {
        std::printf("Dikdortgen %.1fx%.1f\n", a_, b_);
    }
};

int main() {
    Daire d(2.0);
    Dikdortgen k(3.0, 4.0);
    Sekil *liste[2] = { &d, &k };
    double toplam = 0.0;
    for (Sekil *s : liste) {
        s->yazdir();
        toplam += s->alan();
    }
    std::printf("toplam alan = %.3f\n", toplam);
    std::printf("sizeof(Sekil)=%zu sizeof(Daire)=%zu\n",
                sizeof(Sekil), sizeof(Daire));
    return 0;
}
