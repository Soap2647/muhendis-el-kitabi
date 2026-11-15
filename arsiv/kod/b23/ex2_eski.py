def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is not None:
        gerilim, sicaklik = olcum
        if gerilim is not None:
            if 300.0 <= gerilim <= 420.0:
                if sicaklik is not None:
                    if sicaklik > 60.0:
                        if simdi_s - son_alarm_s >= 60.0:
                            return "KRITIK"
                        return "SESSIZ"
                    if sicaklik > 45.0:
                        return "UYARI"
                    return "NORMAL"
                return "VERI_EKSIK"
            return "GERILIM_HATASI"
        return "VERI_EKSIK"
    return "VERI_YOK"
