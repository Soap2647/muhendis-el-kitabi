#include "minitest.h"
#include "tarih.h"

int main(void) {
    CHECK(artik_yil_mi(2024));
    CHECK(!artik_yil_mi(1900));
    CHECK(artik_yil_mi(2000));
    CHECK(gecerli_tarih(2024, 2, 29));
    CHECK(!gecerli_tarih(2023, 2, 29));
    CHECK(!gecerli_tarih(2024, 13, 1));
    CHECK(!gecerli_tarih(2024, 4, 31));
    CHECK_EQ(gun_sayisi(2023, 2), 28);
    CHECK_EQ(gun_sayisi(2024, 4), 30);
    CHECK_EQ(gun_sayisi(2024, 13), -1);
    MT_SONUC();
}
