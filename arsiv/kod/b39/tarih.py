"""Gregoryen takvimde tarih doğrulayıcı (Bölüm 39, Örnek 1)."""

AY_GUN_SAYISI = [31, 28, 31, 30, 31, 30,
                 31, 31, 30, 31, 30, 31]


def artik_yil_mi(yil):
    """400'e bölünen yıllar ve 4'e bölünüp 100'e bölünmeyenler."""
    return yil % 4 == 0 and (yil % 100 != 0 or yil % 400 == 0)


def gun_sayisi(yil, ay):
    """Ayın gün sayısı. Ay 1..12 aralığında olmalıdır."""
    if ay == 2 and artik_yil_mi(yil):
        return 29
    return AY_GUN_SAYISI[ay - 1]


def gecerli_tarih(yil, ay, gun):
    """Üçlünün gerçek bir Gregoryen tarihi olup olmadığını söyler."""
    if not 1 <= ay <= 12:
        return False
    return 1 <= gun <= gun_sayisi(yil, ay)
