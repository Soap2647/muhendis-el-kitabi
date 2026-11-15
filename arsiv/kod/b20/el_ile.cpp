// El ile kaynak yonetimi: istisna olunca birakma atlanir
#include <cstdio>
#include <stdexcept>

static int acik_kilit = 0;

void islem_el(bool hatali) {
    acik_kilit++;                              // al
    if (hatali)                                // birakmadan cikar
        throw std::runtime_error("hata");
    acik_kilit--;                              // birak
}

int main() {
    try {
        islem_el(true);
    } catch (const std::exception& e) {
        std::printf("yakalandi: %s\n", e.what());
    }
    std::printf("acik kilit = %d\n", acik_kilit);
    return 0;
}
