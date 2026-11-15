// Kesir: degismez (invariant) koruyan sinif. Degismez:
//   payda_ > 0  ve  gcd(|pay_|, payda_) == 1  (her zaman)
#pragma once
#include <cstdlib>
#include <numeric>
#include <stdexcept>

class Kesir {
    long pay_;
    long payda_;

    void normalize() {
        if (payda_ < 0) { pay_ = -pay_; payda_ = -payda_; }
        long g = std::gcd(std::labs(pay_), payda_);
        if (g > 1) { pay_ /= g; payda_ /= g; }
    }

public:
    Kesir(long p, long q = 1) : pay_(p), payda_(q) {
        if (q == 0) throw std::invalid_argument("payda sifir");
        normalize();   // kurucu invariant'i kurar
    }

    long pay() const { return pay_; }
    long payda() const { return payda_; }

    Kesir operator+(const Kesir& o) const {
        return Kesir(pay_ * o.payda_ + o.pay_ * payda_,
                     payda_ * o.payda_);
    }
    Kesir operator*(const Kesir& o) const {
        return Kesir(pay_ * o.pay_, payda_ * o.payda_);
    }
    bool operator==(const Kesir& o) const {
        // normalize sayesinde karsilastirma yeter
        return pay_ == o.pay_ && payda_ == o.payda_;
    }
    bool operator<(const Kesir& o) const {
        return pay_ * o.payda_ < o.pay_ * payda_;   // payda > 0
    }
};
