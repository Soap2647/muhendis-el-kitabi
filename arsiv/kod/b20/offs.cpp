// Tureyen icinde ek uyesinin yerlesimi (Itanium ABI, tail padding)
#include <cstdio>

struct Taban {
    int kimlik = 1;
    virtual ~Taban() = default;
};

struct Tureyen : Taban {
    int ek = 99;
};

int main() {
    Tureyen t;
    const char* b = reinterpret_cast<const char*>(&t);
    std::printf("kimlik ofset=%td\n",
        reinterpret_cast<const char*>(&t.kimlik) - b);
    std::printf("ek ofset=%td\n",
        reinterpret_cast<const char*>(&t.ek) - b);
    std::printf("sizeof(Tureyen)=%zu\n", sizeof(Tureyen));
    return 0;
}
