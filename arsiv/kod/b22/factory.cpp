// factory.cpp: kayit tablosu ile sensor fabrikasi (C++17, Bolum 22.3)
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>

struct Sensor {
    virtual ~Sensor() = default;
    virtual double oku() const = 0;
};

struct Termistor : Sensor {
    double oku() const override { return 23.5; }
};

struct Nem : Sensor {
    double oku() const override { return 61.0; }
};

using Uretici = std::function<std::unique_ptr<Sensor>()>;

// Tablo bir fonksiyonun yerel statik degiskeninde (Bolum 22.5'te
// bu tercihi sorgulayacagiz).
std::map<std::string, Uretici>& kayit() {
    static std::map<std::string, Uretici> tablo;
    return tablo;
}

template <typename T>
struct Kaydedici {
    explicit Kaydedici(const std::string& ad) {
        kayit()[ad] = [] { return std::make_unique<T>(); };
    }
};

std::unique_ptr<Sensor> sensor_olustur(const std::string& ad) {
    auto it = kayit().find(ad);
    if (it == kayit().end())
        throw std::runtime_error("bilinmeyen sensor: " + ad);
    return it->second();
}

static Kaydedici<Termistor> k1("termistor");
static Kaydedici<Nem> k2("nem");

int main() {
    for (const char* ad : {"termistor", "nem"}) {
        auto s = sensor_olustur(ad);
        std::cout << ad << " " << s->oku() << "\n";
    }
    try {
        sensor_olustur("basinc");
    } catch (const std::runtime_error& e) {
        std::cout << "hata: " << e.what() << "\n";
    }
}
