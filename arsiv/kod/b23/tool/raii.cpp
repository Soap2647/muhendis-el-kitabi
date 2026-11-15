#include <cstdio>
#include <memory>
#include <stdexcept>

void kullan(bool hata) {
    auto veri = std::make_unique<double[]>(10);
    veri[0] = 1.0;
    if (hata) throw std::runtime_error("bozuk girdi");
    std::printf("tamam\n");
}

int main() {
    try {
        kullan(false);
        kullan(true);
    } catch (const std::exception& e) {
        std::printf("yakalandi: %s\n", e.what());
    }
    return 0;
}
