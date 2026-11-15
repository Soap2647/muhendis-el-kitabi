# -*- coding: utf-8 -*-
import re

P = "C:/Users/merty/AppData/Local/Temp/b30/bolum30.tpl"
s = open(P, encoding="utf-8").read()

pairs = [
    ("Ölçüm ortamı 30.15'te anlatılır.", "Ölçüm ortamı 30.14'te anlatılır."),
    ("Bunu 30.15'te ölçeceğiz.", "Bunu 30.14'te ölçeceğiz."),
    ("DNSSEC'in ona karşı koyma biçimi 30.5'te kısaca anlatılır",
     "DNSSEC'in ona karşı koyma biçimi 30.4'te kısaca anlatılır"),
    ("bunu çerezlerle taşırız (30.9).", "bunu çerezlerle taşırız (30.10)."),
    ("Önbellekteki kopya hâlâ geçerli (30.8)", "Önbellekteki kopya hâlâ geçerli (30.9)"),
    ("(30.10'daki kodda `settimeout(5.0)`)", "(30.11'deki kodda `settimeout(5.0)`)"),
    ("HTTP/2 bu sorunu farklı bir yolla çözer (30.12).",
     "HTTP/2 bu sorunu farklı bir yolla çözer (30.13)."),
    ("Minimal sunucumuz (30.10) her dosya", "Minimal sunucumuz (30.11) her dosya"),
    ("| 3 | 19 | `E` | 14 | ` in\\r\\n\\r\\nchunks.` (14 bayt) | 37 |",
     "| 3 | 19 | `E` | 14 | ` in\\r\\n\\r\\nchunks.` (14 bayt) | 38 |"),
    ("| 4 | not.txt ve index.html yüklendi; uc.txt ile not.txt düştü | 4 | 2 | 1 | 2 |",
     "| 4 | not.txt ve uc.txt ağdan geldi; index taze kaldı | 4 | 3 | 1 | 2 |"),
    ('@@CIKTI cikti/b30_6.txt "python b30_6_onbellek.py 127.0.0.1:8101 (sunucu 8101 portunda)"@@',
     '@@CIKTI cikti/b30_6.txt "python b30_6_onbellek.py 127.0.0.1:8080"@@'),
    ('@@CIKTI cikti/b30_4_curl_raw.txt "curl ile sunucuya beş farklı istek"@@',
     '@@CIKTI cikti/b30_4_curl_raw.txt ""@@'),
    ('@@CIKTI cikti/b30_4_log.txt "sunucunun standart çıktısı"@@',
     '@@CIKTI cikti/b30_4_log.txt ""@@'),
    ('@@CIKTI cikti/wsl_dns.txt "cat /etc/resolv.conf; cat /etc/hosts"@@',
     '@@CIKTI cikti/wsl_dns.txt "grep -v \\"^#\\" /etc/resolv.conf /etc/hosts"@@'),
    ('@@CIKTI cikti/wsl_getent.txt "getent ahosts example.com"@@',
     '@@CIKTI cikti/wsl_getent.txt "getent ahosts example.com | head -3"@@'),
    ("Son iki satır, işletim sisteminin kendi çözümleyicisinin (`getaddrinfo`) verdiği sonuçla aynı adresleri döndürür.",
     "Son satır, işletim sisteminin kendi çözümleyicisinin (`socket.getaddrinfo`) verdiği adres listesiyle birebir aynıdır."),
    ("(makine adı kısaltıldı)", ""),
    ("Sunucuyu iki yolla test ettik. Önce curl ile düz istekler ve hata durumları.",
     "Sunucuyu curl ile test ettik: önce düz istekler ve hata durumları."),
]
for a, b in pairs:
    n = s.count(a)
    if n != 1:
        print("UYARI count=%d: %s" % (n, a[:70]))
    s = s.replace(a, b)

regex = [
    (r"Bu gövde, .*? kelimesini iki parçada taşır\.",
     "Bu gövde üç parçadan oluşur; ilk ikisi Wikipedia kelimesini böler."),
    (r"Açılış yorumundaki örnek, RFC 9112'nin tanımladığı çok parçalı örneğin değişmiş hâlidir\.",
     "Programdaki örnek, HTTP belgelerinde sık anılan Wikipedia in chunks. örneğidir."),
    (r"bir sorguda 50, sonraki sorguda 63 saniye döndü",
     "bir sorguda 63, daha sonraki bir sorguda 50 saniye döndü"),
    (r"Her komut bir TCP bağlantısı açar ve sunucunun sınırlı sayıda bağlantıdan sonra çıkması için son argüman 6 olarak verildi\.",
     "Sunucu altı bağlantıdan sonra kendiliğinden çıkacak şekilde başlatıldı: `python -I b30_4_http_sunucu.py site 8100 6`. Her curl komutu bir bağlantı açar."),
]
for pat, rep in regex:
    s, n = re.subn(pat, rep, s)
    if n != 1:
        print("REGEX UYARI n=%d: %s" % (n, pat[:60]))

# bağımsız "$ ..." satırlarını kaldır (komutlar CIKTI bloklarında yazılır)
satirlar = s.split("\n")
yeni = [l for l in satirlar if not l.startswith("$ ")]
print("kaldirilan $ satiri:", len(satirlar) - len(yeni))
s = "\n".join(yeni)

# ham veri blokları terminal kutusu olsun
s = s.replace("```\nHTTP/1.1 200 OK", "```term\nHTTP/1.1 200 OK")
s = s.replace("```\n4\\r\\nWiki", "```term\n4\\r\\nWiki")
open(P, "w", encoding="utf-8").write(s)
print("tamam")
