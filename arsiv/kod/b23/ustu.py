def kullanici_bul(kimlik):
    if kimlik != 1:
        raise KeyError(kimlik)
    return "Ayse"


def ad_getir(kimlik):
    try:
        return kullanici_bul(kimlik).upper()
    except KeyError as hata:
        raise ValueError("kimlik %d yok" % kimlik) from hata


print(ad_getir(1))
try:
    ad_getir(7)
except ValueError as e:
    print("hata:", e, "| neden:", repr(e.__cause__))
