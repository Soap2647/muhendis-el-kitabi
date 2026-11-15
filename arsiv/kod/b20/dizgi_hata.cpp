// Sigh kopya: Rule of 5'i bozan bilincli hata (kopya ctor yok)
#include <cstdio>
#include <cstring>

class Dizgi {
    char* veri_;
public:
    Dizgi(const char* s) : veri_(new char[std::strlen(s) + 1]) {
        std::strcpy(veri_, s);
    }
    ~Dizgi() { delete[] veri_; }
    const char* c_str() const { return veri_; }
};

int main() {
    Dizgi a("MertOS");
    Dizgi b = a;                 // derleyicinin uretti: sigh kopya
    std::printf("%s %s\n", a.c_str(), b.c_str());
    return 0;                    // iki yikici ayni bloku free eder
}
