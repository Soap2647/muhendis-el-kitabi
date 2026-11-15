ESIK = 3.6


def satir_ayristir(satir):
    cihaz, zaman, deger, birim = satir.split(";")
    if not zaman.isdigit():
        raise ValueError("zaman")
    deger = float(deger)
    if birim == "mV":
        deger = deger / 1000.0
    elif birim != "V":
        raise ValueError("birim")
    return cihaz, deger


def rapor_uret(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        try:
            cihaz, deger = satir_ayristir(satir)
        except ValueError:
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = {"min": deger, "max": deger,
                               "toplam": 0.0, "adet": 0}
        c = cihazlar[cihaz]
        c["min"] = min(c["min"], deger)
        c["max"] = max(c["max"], deger)
        c["toplam"] += deger
        c["adet"] += 1
    cikti = ["CIHAZ       ADET      MIN      MAX    ORT  DURUM"]
    for ad in sorted(cihazlar):
        c = cihazlar[ad]
        ort = c["toplam"] / c["adet"]
        durum = "UYARI" if c["max"] > ESIK else "TAMAM"
        cikti.append("%-10s %5d %8.3f %8.3f %6.3f  %s"
                     % (ad, c["adet"], c["min"], c["max"], ort, durum))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
