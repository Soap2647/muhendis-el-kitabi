# -*- coding: utf-8 -*-
# katman_onbellek.py: Dockerfile önbellek anahtarının MODELİ.
# Gerçek Docker kodu değildir; kuralı gösterir:
#   anahtar_i = sha256(anahtar_(i-1) | talimat | COPY özeti)
# Bir anahtar üst katmana bağlı olduğundan, bir talimat
# yeniden çalışınca altındaki tüm talimatlar da çalışır.
import hashlib
import pathlib
import tempfile

A_DOCKERFILE = [
    "FROM gcc:13",
    "WORKDIR /src",
    "COPY . .",
    "RUN apt-get install -y make",
    "RUN make",
]
B_DOCKERFILE = [
    "FROM gcc:13",
    "WORKDIR /src",
    "COPY deps.txt .",
    "RUN apt-get install -y make",
    "COPY . .",
    "RUN make",
]


def sha(metin):
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()[:10]


def dosya_ozeti(baglam, yol):
    """COPY için: dosya adlarından ve baytlarından özet."""
    kok = pathlib.Path(baglam) / yol
    # Sıralama açık anahtarla yapılır. Path sıralaması Windows'ta
    # büyük-küçük harf duyarsız, Linux'ta duyarlıdır; özet değişirdi.
    if kok.is_file():
        dosyalar = [kok]
    else:
        dosyalar = sorted(
            kok.rglob("*"),
            key=lambda f: f.relative_to(baglam).as_posix())
    h = hashlib.sha256()
    for f in dosyalar:
        if f.is_file():
            h.update(str(f.relative_to(baglam)).encode("utf-8"))
            h.update(f.read_bytes())
    return h.hexdigest()[:10]


def derle(talimatlar, baglam, onbellek):
    """Her talimat için anahtar üretir: önbellekte varsa CACHED,
    yoksa REBUILT. Anahtarlar ortak önbelleğe eklenir."""
    anahtar = "kok"
    satirlar = []
    for tal in talimatlar:
        kom = tal.split()[0]
        girdi = ""
        if kom == "COPY":
            girdi = dosya_ozeti(baglam, tal.split()[1])
        anahtar = sha(anahtar + "|" + tal + "|" + girdi)
        durum = "CACHED" if anahtar in onbellek else "REBUILT"
        onbellek.add(anahtar)
        satirlar.append((tal, durum, anahtar))
    return satirlar


def yaz_dosya(yol, metin):
    # write_text Windows'ta satır sonunu değiştirir. Baytları doğrudan
    # yazarak özetin her işletim sisteminde aynı kalmasını sağlarız.
    yol.write_bytes(metin.encode("utf-8"))


def yaz(baslik, satirlar):
    print(baslik)
    for tal, durum, anahtar in satirlar:
        print("  %-28s %-8s %s" % (tal, durum, anahtar))


def ana():
    with tempfile.TemporaryDirectory() as baglam:
        p = pathlib.Path(baglam)
        yaz_dosya(p / "deps.txt", "make\n")
        yaz_dosya(p / "Makefile", "all:\n\tgcc crc32_arac.c\n")
        yaz_dosya(p / "crc32_arac.c", "int main(void){return 0;}\n")
        onbellek = set()
        yaz("A ilk derleme:", derle(A_DOCKERFILE, baglam, onbellek))
        yaz("B ilk derleme:", derle(B_DOCKERFILE, baglam, onbellek))
        # Yalnızca kaynak kodu değişir
        yaz_dosya(p / "crc32_arac.c", "int main(void){return 1;}\n")
        a = derle(A_DOCKERFILE, baglam, onbellek)
        yaz("A kaynak değişti:", a)
        b = derle(B_DOCKERFILE, baglam, onbellek)
        yaz("B kaynak değişti:", b)


if __name__ == "__main__":
    ana()
