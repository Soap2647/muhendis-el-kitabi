from typing import NamedTuple, Optional

GERILIM_AGIRLIGI = 0.92
SICAKLIK_AGIRLIGI = 0.08
KRITIK_SKOR = 85.0


class Kayit(NamedTuple):
    zaman: float
    gerilim: float
    sicaklik: float
    aktif: int


def kayit_oku(ham) -> Optional[Kayit]:
    zaman, gerilim, sicaklik, aktif = ham
    if zaman is None or gerilim is None or sicaklik is None:
        return None
    return Kayit(zaman, gerilim, sicaklik, aktif)


def kayit_uygun_mu(kayit: Kayit, esik: float) -> bool:
    return kayit.aktif == 1 and kayit.gerilim >= esik


def skor_hesapla(kayit: Kayit) -> float:
    return (kayit.gerilim * GERILIM_AGIRLIGI
            + kayit.sicaklik * SICAKLIK_AGIRLIGI)


def kritik_skorlar(ham_kayitlar, esik):
    sonuc = []
    for ham in ham_kayitlar:
        kayit = kayit_oku(ham)
        if kayit is None or not kayit_uygun_mu(kayit, esik):
            continue
        skor = skor_hesapla(kayit)
        if skor > KRITIK_SKOR:
            sonuc.append((kayit.zaman, skor))
    return sonuc


def kritik_ozet(ham_kayitlar, esik, mod):
    kritikler = kritik_skorlar(ham_kayitlar, esik)
    if not kritikler:
        return None
    if mod == "ortalama":
        toplam = 0.0
        for _, skor in kritikler:
            toplam = toplam + skor
        return toplam / len(kritikler)
    if mod == "liste":
        return kritikler
    raise ValueError(mod)
