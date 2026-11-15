// RAII: kurucuda edin, yikicida birak. Yikici sirasi: LIFO
#include <cstdio>
#include <stdexcept>
#include <string>
#include <utility>

static int acik_kilit = 0;             // kilit durumunu simule eder

class Kilit {
    std::string ad_;
public:
    explicit Kilit(std::string ad) : ad_(std::move(ad)) {
        ++acik_kilit;
        std::printf("  al    %s\n", ad_.c_str());
    }
    ~Kilit() {
        --acik_kilit;
        std::printf("  birak %s\n", ad_.c_str());
    }
    // iki kez birakma olmasin
    Kilit(const Kilit&) = delete;
    Kilit& operator=(const Kilit&) = delete;
};

class Dosya {
    std::FILE* f_;
public:
    Dosya(const char* yol, const char* kip)
        : f_(std::fopen(yol, kip)) {
        if (!f_) throw std::runtime_error("dosya acilamadi");
        std::printf("  ac    %s\n", yol);
    }
    ~Dosya() {
        if (f_) { std::fclose(f_); std::printf("  kapat\n"); }
    }
    Dosya(const Dosya&) = delete;
    Dosya& operator=(const Dosya&) = delete;
    Dosya(Dosya&& o) noexcept : f_(o.f_) { o.f_ = nullptr; }
    void yaz(const char* s) { std::fputs(s, f_); }
};

void islem(bool hatali) {
    Kilit a("kilit-A");
    Dosya d("raii_cikti.txt", "w");
    Kilit b("kilit-B");
    d.yaz("merhaba\n");
    if (hatali) throw std::runtime_error("islem basarisiz");
    std::printf("  is bitti\n");
}

int main() {
    std::printf("-- basarili:\n");
    islem(false);
    std::printf("-- istisnali:\n");
    try {
        islem(true);
    } catch (const std::exception& e) {
        std::printf("  yakalandi: %s\n", e.what());
    }
    std::printf("acik kilit = %d\n", acik_kilit);
    return 0;
}
