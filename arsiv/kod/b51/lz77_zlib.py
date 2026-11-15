# lz77_zlib.py: LZ77 sözlük kodlamasının sezgisi, DEFLATE = LZ77 +
# Huffman ve sıkıştırılamaz veri (rastgele ve "şifreli benzeri")
# ölçümü.
# Kullanım: python lz77_zlib.py <bolum_18.md yolu>
import hashlib
import random
import sys
import zlib

def lz77_kodla(s, pencere=32, azami=15):
    # Üçlü çıktı: (ofset, uzunluk, sonraki bayt). Kaba kuvvet arama.
    i, cikti = 0, []
    while i < len(s):
        en_uz, en_of = 0, 0
        for j in range(max(0, i - pencere), i):
            k = 0
            # son baytı sonraki için bırak: i+k < len(s)-1
            while (k < azami and i + k < len(s) - 1
                   and s[j + k] == s[i + k]):
                k += 1
            if k > en_uz:
                en_uz, en_of = k, i - j
        cikti.append((en_of, en_uz, s[i + en_uz]))
        i += en_uz + 1
    return cikti

def lz77_coz(uclu):
    # Örtüşen kopyalar bayt bayt yazılır (ofset < uzunluk olabilir).
    cikti = bytearray()
    for of, ul, son in uclu:
        for _ in range(ul):
            cikti.append(cikti[-of])
        cikti.append(son)
    return bytes(cikti)

def sifreli_benzeri(metin, anahtar=b"muhendis-51"):
    # Sayaçlı SHA-256 akışı ile XOR: çıktı rastgeleye yakın görünür.
    # (Gerçek bir şifre DEĞİL; yalnızca sıkıştırılamazlık gösterimi.)
    cikti = bytearray()
    for blok in range(0, len(metin), 32):
        sayac = blok.to_bytes(8, "big")
        ks = hashlib.sha256(anahtar + sayac).digest()
        parca = metin[blok:blok + 32]
        cikti.extend(a ^ b for a, b in zip(parca, ks))
    return bytes(cikti)

def boyut_orani(veri, seviye=9, strateji=zlib.Z_DEFAULT_STRATEGY):
    c = zlib.compressobj(seviye, zlib.DEFLATED, 15, 9, strateji)
    out = c.compress(veri) + c.flush()
    return len(out), len(out) / len(veri)

def main(yol):
    with open(yol, "rb") as f:
        metin = f.read()
    print("abracadabra LZ77 üçlüleri:")
    for u in lz77_kodla(b"abracadabra"):
        print("  ", u)
    ornek = metin[:4000]
    uclu = lz77_kodla(ornek)
    assert lz77_coz(uclu) == ornek
    eslesen = sum(1 for u in uclu if u[1] > 0)
    print("4000 baytlık kesit: %d üçlü, %d tanesi eşleşme içeriyor"
          % (len(uclu), eslesen))
    print("---")
    print("kaynak              bayt   zlib-9  orani  huff-only orani")
    rnd = random.Random(51)
    kaynaklar = [
        ("bolum_18 (metin)", metin),
        ("rastgele 100000", rnd.randbytes(100000)),
        ("sifreli benzeri", sifreli_benzeri(metin)),
    ]
    for ad, veri in kaynaklar:
        b9, o9 = boyut_orani(veri, 9)
        bh, oh = boyut_orani(veri, 9, zlib.Z_HUFFMAN_ONLY)
        print("%-18s %7d %7d  %.4f  %8d   %.4f" % (
            ad, len(veri), b9, o9, bh, oh))
    # Düzey 0: LZ77 ve Huffman yok, yalnızca başlık+saklama
    b0, o0 = boyut_orani(metin, 0)
    print("bolum_18 zlib duzey 0: %d bayt (oran %.4f)" % (b0, o0))


if __name__ == "__main__":
    main(sys.argv[1])
