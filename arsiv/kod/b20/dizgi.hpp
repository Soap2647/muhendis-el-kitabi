// Dizgi: kstring.hpp'ye benzer kucuk bir dizgi sinifi (Rule of 5)
#pragma once
#include <cstddef>
#include <cstring>
#include <utility>

class Dizgi {
    char* veri_ = nullptr;   // sahibi oldugumuz bellek
    // uzunluk_ == strlen(veri_): NUL-sonlu, degismez
    std::size_t uzunluk_ = 0;

public:
    Dizgi() = default;

    Dizgi(const char* s)
        : veri_(new char[std::strlen(s) + 1]),
          uzunluk_(std::strlen(s)) {
        std::memcpy(veri_, s, uzunluk_ + 1);
    }

    // Kaynak burada serbest birakilir.
    ~Dizgi() { delete[] veri_; }

    // Kopya kurucu: DERIN kopya (kendi belleğini al)
    Dizgi(const Dizgi& o) : Dizgi(o.c_str()) {}

    // Kopya atama: copy-and-swap (istisna guvenli,
    // oz-atamaya dayanikli)
    Dizgi& operator=(const Dizgi& o) {
        Dizgi kopya(o);
        swap(kopya);
        return *this;
    }

    // Tasima kurucu: kaynagi calar, kaynagi bos birakir
    Dizgi(Dizgi&& o) noexcept
        : veri_(o.veri_), uzunluk_(o.uzunluk_) {
        o.veri_ = nullptr;
        o.uzunluk_ = 0;
    }

    // Tasima atama
    Dizgi& operator=(Dizgi&& o) noexcept {
        Dizgi gecici(std::move(o));
        swap(gecici);
        return *this;
    }

    void swap(Dizgi& o) noexcept {
        std::swap(veri_, o.veri_);
        std::swap(uzunluk_, o.uzunluk_);
    }

    // Sonuna ekle: yeni bellek al, eskiyi birak (guvenli sira)
    void ekle(const char* s) {
        std::size_t n = std::strlen(s);
        char* yeni = new char[uzunluk_ + n + 1];
        if (veri_) std::memcpy(yeni, veri_, uzunluk_);
        std::memcpy(yeni + uzunluk_, s, n + 1);
        delete[] veri_;
        veri_ = yeni;
        uzunluk_ += n;
    }

    const char* c_str() const { return veri_ ? veri_ : ""; }
    std::size_t uzunluk() const { return uzunluk_; }
};
