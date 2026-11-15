// komut.cpp: GoF Command, geri al / yinele yigini (C++17, 22.11)
#include <cstddef>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Metin {                           // alici (receiver)
    std::string s;
};

struct Komut {                           // Command arayuzu
    virtual ~Komut() = default;
    virtual void calistir() = 0;
    virtual void geri_al() = 0;
};

class Ekle : public Komut {
public:
    Ekle(Metin& m, std::string y) : m_(m), y_(std::move(y)) {}
    void calistir() override { m_.s += y_; }
    void geri_al() override { m_.s.resize(m_.s.size() - y_.size()); }

private:
    Metin& m_;
    std::string y_;
};

class Sil : public Komut {
public:
    Sil(Metin& m, std::size_t k) : m_(m), k_(k) {}
    void calistir() override {
        silinen_ = m_.s.substr(m_.s.size() - k_);
        m_.s.resize(m_.s.size() - k_);
    }
    void geri_al() override { m_.s += silinen_; }

private:
    Metin& m_;
    std::size_t k_;
    std::string silinen_;
};

class Editor {
public:
    void yap(std::unique_ptr<Komut> k) {
        k->calistir();
        geri_.push_back(std::move(k));
        ileri_.clear();   // yeni komut ileri yigini siler
    }

    bool geri() {
        if (geri_.empty()) return false;
        auto k = std::move(geri_.back());
        geri_.pop_back();
        k->geri_al();
        ileri_.push_back(std::move(k));
        return true;
    }

    bool yinele() {
        if (ileri_.empty()) return false;
        auto k = std::move(ileri_.back());
        ileri_.pop_back();
        k->calistir();
        geri_.push_back(std::move(k));
        return true;
    }

    Metin& metin() { return m_; }
    std::size_t geri_sayi() const { return geri_.size(); }
    std::size_t ileri_sayi() const { return ileri_.size(); }

private:
    Metin m_;
    std::vector<std::unique_ptr<Komut>> geri_, ileri_;
};

void goster(const char* ad, Editor& e) {
    std::cout << ad << " metin=\"" << e.metin().s << "\" geri="
              << e.geri_sayi() << " ileri=" << e.ileri_sayi() << "\n";
}

int main() {
    Editor e;
    e.yap(std::make_unique<Ekle>(e.metin(), "Merhaba"));
    goster("ekle", e);
    e.yap(std::make_unique<Ekle>(e.metin(), " dunya"));
    e.yap(std::make_unique<Sil>(e.metin(), 5));
    goster("sil5", e);
    e.geri();
    goster("geri", e);
    e.geri();
    goster("geri", e);
    e.yinele();
    goster("yinele", e);
    e.yap(std::make_unique<Ekle>(e.metin(), "!"));
    goster("ekle!", e);
    bool y = e.yinele();
    std::cout << "yinele: " << (y ? "evet" : "hayir") << "\n";
}
