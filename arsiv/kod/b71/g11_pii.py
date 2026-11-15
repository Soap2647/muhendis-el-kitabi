# -*- coding: utf-8 -*-
"""Bolum 71 - Desen tabanli PII maskeleme: sifirdan, olculu."""

import re

TC_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
EPOSTA_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
TEL_RE = re.compile(
    r"(?:\+90|0)?\s?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}"
)
IBAN_RE = re.compile(r"\bTR\d{24}\b")


def tc_gecerli(s):
    """TC kimlik no denetim basamaklari.

    10. ve 11. basamak kontrolu."""
    d = [int(c) for c in s]
    d10 = (
        (d[0] + d[2] + d[4] + d[6] + d[8]) * 7
        - (d[1] + d[3] + d[5] + d[7])
    ) % 10
    d11 = sum(d[:10]) % 10
    return d[9] == d10 and d[10] == d11


def maskele(metin):
    """Dondurur: (maskeli metin, bulunan tur listesi)."""
    bulunan = []

    def tc(m):
        if tc_gecerli(m.group(0)):
            bulunan.append("TC")
            return "[TC]"
        return m.group(0)

    metin = TC_RE.sub(tc, metin)
    for ad, desen in [
        ("EPOSTA", EPOSTA_RE),
        ("IBAN", IBAN_RE),
        ("TEL", TEL_RE),
    ]:

        def degistir(m, ad=ad):
            bulunan.append(ad)
            return "[" + ad + "]"

        metin = desen.sub(degistir, metin)
    return metin, bulunan


def tc_uret(baz):
    """Gecerli bir TC kimlik no'su uretir (sinama icin)."""
    d = [int(c) for c in baz]
    d10 = (
        (d[0] + d[2] + d[4] + d[6] + d[8]) * 7
        - (d[1] + d[3] + d[5] + d[7])
    ) % 10
    d.append(d10)
    d.append(sum(d) % 10)
    return "".join(str(x) for x in d)


if __name__ == "__main__":
    print(
        "gecerli TC ornegi:",
        tc_uret("123456789"),
        tc_gecerli(tc_uret("123456789")),
    )
    # (metin, beklenen_maskeli_tur_kumesi)
    ornek = [
        ("Adım: Ali Veli, TC: " + tc_uret("512345678") + ".", {"TC"}),
        ("Rapor 12345678901 numaralı kayda aittir.", set()),
        ("İletişim: ali.veli@ornek.com", {"EPOSTA"}),
        ("Telefon 0532 123 45 67 olarak kaydedildi.", {"TEL"}),
        ("Hesap TR" + "1" * 24 + " üzerinden ödendi.", {"IBAN"}),
        ("Sıcaklık 36 derece, nem %45.", set()),
        ("Sayı 2024123456789 bir seri numarasıdır.", set()),
        (
            "Kullanıcı " + tc_uret("623456789") + " ve "
            "mail: test@firma.com.tr",
            {"TC", "EPOSTA"},
        ),
    ]
    tp = fp = fn = 0
    for metin, bekl in ornek:
        cikti, bul = maskele(metin)
        kume = set(bul)
        tp += len(kume & bekl)
        fp += len(kume - bekl)
        fn += len(bekl - kume)
        print("%-46s -> %s" % (cikti[:46], sorted(kume)))
    print(
        "kesinlik=%.3f duyarlilik=%.3f (tur-bazli, %d ornek)"
        % (tp / (tp + fp), tp / (tp + fn), len(ornek))
    )
