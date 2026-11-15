// gozlemci.cpp: zayif referansli abonelik, weak_ptr (C++17, 22.10)
#include <algorithm>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Gozlemci {
    virtual ~Gozlemci() = default;
    virtual void olay(double deger) = 0;
};

class Konu {
public:
    void abone_ol(const std::shared_ptr<Gozlemci>& g) {
        liste_.push_back(g);                 // weak_ptr'a donusur
    }

    void bildir(double deger) {
        auto kopya = liste_;   // bildirim sirasinda degisebilir
        for (auto& w : kopya)
            if (auto g = w.lock()) g->olay(deger);
        liste_.erase(std::remove_if(liste_.begin(), liste_.end(),
            [](const std::weak_ptr<Gozlemci>& w) {
                return w.expired();
            }), liste_.end());
    }

    std::size_t sayi() const { return liste_.size(); }

private:
    std::vector<std::weak_ptr<Gozlemci>> liste_;
};

class Alarm : public Gozlemci {
public:
    Alarm(std::string ad, double esik) : ad_(ad), esik_(esik) {}
    void olay(double d) override {
        if (d > esik_)
            std::cout << "  ALARM " << ad_ << " " << d << "\n";
    }

private:
    std::string ad_;
    double esik_;
};

int main() {
    Konu k;
    auto kritik = std::make_shared<Alarm>("kritik", 80);
    k.abone_ol(kritik);
    {
        auto gecici = std::make_shared<Alarm>("gecici", 0);
        k.abone_ol(gecici);
        k.bildir(10);                        // gecici alarm verir
    }                                        // gecici burada yok olur
    std::cout << "abone sayisi: " << k.sayi() << "\n";
    k.bildir(85);                            // olu abone temizlenir
    std::cout << "abone sayisi: " << k.sayi() << "\n";
}
