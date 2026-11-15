// dip_cpp.cpp: ISP (kucuk arayuz) ve DIP (kurucu enjeksiyonu), C++17
#include <cstdio>
#include <vector>

// ISP: telemetri hattina yalnizca okuma gerekir; kucuk arayuz
class Okunabilir {
public:
    virtual ~Okunabilir() = default;
    virtual double oku() const = 0;
};

// Depolama soyutlamasi (dusuk seviye ayrintidan bagimsiz)
class Kaydedici {
public:
    virtual ~Kaydedici() = default;
    virtual void yaz(double v) = 0;
};

// Ust seviye politika: somut sensor ve depoyu bilmez
class TelemetriHatti {
public:
    TelemetriHatti(const Okunabilir &kaynak, Kaydedici &hedef)
        : kaynak_(kaynak), hedef_(hedef) {}
    void calistir() { hedef_.yaz(kaynak_.oku() * 2.0); }
private:
    const Okunabilir &kaynak_;   // kurucu enjeksiyonu: referans
    Kaydedici &hedef_;
};

// Gercek donanim surucusu (sahte olmayan)
class TermistorSurucu : public Okunabilir {
public:
    double oku() const override { return 36.6; }
};

// Test sahtesi: deger disaridan verilir
class SahteSensor : public Okunabilir {
public:
    explicit SahteSensor(double d) : deger_(d) {}
    double oku() const override { return deger_; }
private:
    double deger_;
};

// Test icin bellek kaydedicisi
class BellekKaydedici : public Kaydedici {
public:
    void yaz(double v) override { kayit_.push_back(v); }
    std::vector<double> kayit_;
};

int main()
{
    SahteSensor sahte(21.5);
    BellekKaydedici bellek;
    TelemetriHatti h1(sahte, bellek);
    h1.calistir();
    std::printf("sahte: %g\n", bellek.kayit_.at(0));

    TermistorSurucu gercek;
    BellekKaydedici b2;
    TelemetriHatti h2(gercek, b2);
    h2.calistir();
    std::printf("termistor: %g\n", b2.kayit_.at(0));
    return 0;
}
