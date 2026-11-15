GERILIM_ALT, GERILIM_UST = 300.0, 420.0
SICAKLIK_KRITIK, SICAKLIK_UYARI = 60.0, 45.0
SESSIZLIK_SURESI_S = 60.0


def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is None:
        return "VERI_YOK"
    gerilim, sicaklik = olcum
    if gerilim is None:
        return "VERI_EKSIK"
    if not GERILIM_ALT <= gerilim <= GERILIM_UST:
        return "GERILIM_HATASI"
    if sicaklik is None:
        return "VERI_EKSIK"
    if sicaklik > SICAKLIK_KRITIK:
        if simdi_s - son_alarm_s >= SESSIZLIK_SURESI_S:
            return "KRITIK"
        return "SESSIZ"
    if sicaklik > SICAKLIK_UYARI:
        return "UYARI"
    return "NORMAL"
