# -*- coding: utf-8 -*-
import re

P = "C:/Users/merty/AppData/Local/Temp/b30/bolum30.tpl"
s = open(P, encoding="utf-8").read()

def tek(pat, rep, metin):
    yeni, n = re.subn(pat, lambda m: rep, metin, count=1)
    if n != 1:
        print("UYARI: bulunamadi ->", pat[:60])
    return yeni

s = s.replace("@@KAYNAK 591 612@@", "@@KAYNAK 591 609@@")

# 30.5: DHCP betiginin son blogu
s = tek(r"@@KOD b30_7_dhcp_sema\.py 42 68 python@@",
        "@@KOD b30_7_dhcp_sema.py 42 68 python@@\n\n"
        "Son kısım, örnek paketi kurup ayrıştırır ve alanları yazdırır:\n\n"
        "@@KOD b30_7_dhcp_sema.py 69 75 python@@", s)

# Örnek 3: işaretçi izleyicisinin kodu
s = tek(r"\*\*Adım 6 — Doğrula\.\*\* Programı çalıştır ve izi tabloyla karşılaştır\.",
        "Önce izleyici ve ana programın tamamı aşağıda. `ad_izle`, `ad_coz`'un adım adım yazdırılan sürümüdür; ana program ise `yanit_ayristir` ile tüm yanıtı çözer.\n\n"
        "@@KOD b30_8_isaretci.py 1 34 python@@\n\n"
        "@@KOD b30_8_isaretci.py 35 43 python@@\n\n"
        "**Adım 6 — Doğrula.** Programı çalıştır ve izi tabloyla karşılaştır.", s)

# Örnek 4: önbellek istemcisinin kodu ve sunucu/istemci komutları
s = tek(r"\*\*Adım 6 — Doğrula\.\*\* Önce sunucuyu başlat \(sınırsız çalışsın diye son argüman yok\), sonra istemciyi çalıştır\.",
        "Önbellek istemcisinin tamamı aşağıda. Sunucu tarafı 30.11'de verildi; bu istemci onunla birlikte çalışır.\n\n"
        "@@KOD b30_6_onbellek.py 1 19 python@@\n\n"
        "Sınıfın durumu üç alandan oluşur: kapasite, yol → (ETag, bitiş, gövde) sözlüğü ve bir sayaç sözlüğü. `OrderedDict` sıra da tuttuğu için ilk eleman en eski, son eleman en yeni kullanılandır.\n\n"
        "@@KOD b30_6_onbellek.py 20 55 python@@\n\n"
        "`al` fonksiyonu, taze kopya varsa ağa çıkmadan döner. Değilse koşullu istek gönderir: 304 gelirse önbellekteki gövdeyi kullanır, 200 gelirse yeni gövdeyi saklar. Kapasite aşılınca en eski kayıt atılır.\n\n"
        "@@KOD b30_6_onbellek.py 56 72 python@@\n\n"
        "Ana bölüm aynı istemciyi dört adımlık bir senaryoyla sınar.\n\n"
        "**Adım 6 — Doğrula.** Önce sunucuyu başlat (`python -I b30_4_http_sunucu.py site 8080`), sonra istemciyi çalıştır (`python b30_6_onbellek.py 127.0.0.1:8080`). Sunucu sınırsız çalışsın diye üçüncü argüman verilmedi.", s)

open(P, "w", encoding="utf-8").write(s)
print("tamam")
