// fasad.cpp: karmasik altsistemin sade on yuzu (C++17, Bolum 22.8)
#include <iostream>
#include <string>

struct Ayristirici {
    double coz(const std::string& m) const {
        return std::stod(m.substr(m.find(';') + 1));
    }
};

struct Dogrulayici {
    bool gecerli(double d) const { return d >= 0 && d <= 150; }
};

struct Gonderici {
    void yolla(const std::string& p) const {
        std::cout << "yollandi: " << p << "\n";
    }
};

class TelemetriFasad {
public:
    void gonder(const std::string& metin) const {
        double d = ayr_.coz(metin);
        if (!dog_.gecerli(d)) {
            std::cout << "reddedildi\n";
            return;
        }
        gon_.yolla(metin);
    }

private:
    Ayristirici ayr_;
    Dogrulayici dog_;
    Gonderici gon_;
};

int main() {
    TelemetriFasad f;
    f.gonder("ARAC7;23.5");
    f.gonder("ARAC7;999");
}
