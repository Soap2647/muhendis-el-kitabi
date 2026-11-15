# -*- coding: utf-8 -*-
import io

BS = chr(92)  # ters egik cizgi, kacis sorunlarindan kacinmak icin

FIX = {
"b32_1_parola.py": {
 2: ['"""b32_1_parola.py: cig etkisi ve tuzlu KDF ile parola saklama.'],
 29: ['    # Tek bit degisince ozetin yarisi degisir (256/2=128)'],
 61: ['        return False                        # kayit guvenilmez'],
 76: ['                  (time.perf_counter() - t)',
      '                  / tekrar["sha256"] * 1000))'],
 82: ['                  (time.perf_counter() - t)',
      '                  / tekrar["pbkdf2"] * 1000))'],
 88: ['                  (time.perf_counter() - t)',
      '                  / tekrar["scrypt"] * 1000))'],
},
"b32_2_hmac_telemetri.py": {
 2: ['"""b32_2_hmac_telemetri.py: Bolum 31 telemetrisine HMAC ekleme.'],
 24: ['ETIKET_BOY = 16                      # HMAC-SHA256, 128 bit'],
 66: ['                "boylam": boylam, "irtifa": irtifa,',
      '                "batarya": batarya}'],
 90: ['    p = paketle(ANAHTAR, 7, 123456, 390000000,',
      '                329000000, 15200, 11980)'],
 106: ['    s = crc_sahtele(c, 10, 0x10)         # enlem alani'],
},
"b32_3_aead_imza.py": {
 5: ['(OpenSSL tabanli) AESGCM, ChaCha20Poly1305 ve Ed25519 kullanilir.'],
 23: ['    """Rastgele 96 bit nonce; cikti = nonce + sifreli + etiket."""'],
 89: ['        dogru(ad + " gidis-donus",',
      '              coz(sinif, k, p, b"baslik") == b"merhaba")'],
},
"b32_4_rastgele.py": {
 2: ['"""b32_4_rastgele.py: random ile secrets farki, etkin guc.'],
 4: ['Bu program kendi jeton uretimimizi olcer: 128 bitlik bir jeton,',
     '16 bitlik bir tohumdan uretilirse etkin guc 128 degil 16 bittir.'],
 22: ['    """YANLIS: random, tohumu bilinen kucuk bir kaynaktan alir."""'],
 32: ['    """Tohum uzayini sirayla tarar; etkin gucu olcer."""'],
 70: ['    dogru("farkli tohum farkli jeton",',
      '          zayif_jeton(7) != zayif_jeton(8))'],
 77: ['    dogru("tohum uzayi kucukse bulunamaz",',
      '          bulunan is None and sayi == 512)'],
},
"b32_5_tls.py": {
 34: ['    ad = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,',
      '                                       "localhost")])'],
 81: ['                pass                # istemci el sikismayi reddetti'],
 126: ['    """Yalnizca okuma: el sikisma, sertifika alanlari, kapanis."""'],
 133: ['        return ", ".join("%s=%s" % (k, v)',
       '                         for grup in seq for k, v in grup)'],
 157: ['    dogru("dogrulama kapaliyken kabul (zafiyet)",',
       '          sonuc["kapali"] is True)'],
},
"b32_canli.py": {
 17: ['IYI = (b"GET /index.html HTTP/1.1' + BS + 'r' + BS + 'nHost: x' + BS + 'r' + BS + 'n"',
      '       b"Connection: close' + BS + 'r' + BS + 'n' + BS + 'r' + BS + 'n")'],
 56: ['                         stdout=subprocess.PIPE,',
      '                         stderr=subprocess.PIPE)'],
},
"b32_fuzz.py": {
 8: ['  http     : Bolum 30 HTTP sunucusunun baglanti isleyicisi'],
 10: ['Beklenen red istisnalari (ValueError, EOFError) sayilmaz.',
      'Diger her istisna bir HATA olarak raporlanir.'],
 14: ['  python b32_fuzz.py ham     # Bolum 30 ozgun sunucusu'],
 72: ['    """Rastgele bir mutasyon uygular; bazen baska tohumdan parca."""'],
 101: ['    Bu demet bos ise hedef istemci girdisinde istisna sizdirmamali."""'],
 220: ['        # Iki surum da calisir; sonuclar tek tabloya yazilir'],
 235: ['    print("surum=%s, yineleme=%d, tohum=%d"',
       '          % (surum, YINELEME, TOHUM))'],
},
"b32_girdi.py": {
 80: ['        print("%-22r %-10s %s" % (t,',
      '                                 "kokte" if naif_kok else "KOKTEN",',
      '                                 durum))'],
},
"b32_http_sag.py": {
 79: ['    sunucuda yapilmaz; yapilirsa denetim ayni tekrarlanmali."""'],
 165: ['        except Exception as e:      # savunma derinligi: katman 4'],
 166: ['            print("baglanti hatasi:", type(e).__name__,',
       '                  file=sys.stderr, flush=True)'],
},
"b32_korumalar.py": {
 3: ['"""b32_korumalar.py: ELF ikilisindeki koruma bayraklarini denetler.'],
 37: ['    sonuc["FORTIFY (__*_chk)"] = bool(',
      '        re.search(r"' + BS + 'b__' + BS + 'w+_chk' + BS + 'b", semb))'],
},
"b32_web.py": {
 2: ['"""b32_web.py: oturum cerezi bayraklari ve CSRF jetonu.'],
 18: ['    c["oturum"]["samesite"] = "Lax"     # capraz site istek yok'],
},
"b32_c1_duzeltilmis.c": {
 1: ['/* b32_c1_duzeltilmis.c: tampon tasmasinin sinirli kopya ile',
     ' * onlenmesi.'],
 11: [' * kapatir. Donus degeri, kesilmis olsaydi yazilacak uzunluk. */'],
},
"b32_c2_hatali.c": {
 1: ['/* b32_c2_hatali.c: serbest birakilmis bellegi kullanma',
     ' * (use-after-free).'],
 2: [' * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra',
     ' *                 -std=c11 b32_c2_hatali.c -o b32_c2_hatali'],
 3: [],
},
"b32_c3_hatali.c": {
 1: ['/* b32_c3_hatali.c: ayni bellegi iki kez serbest birakma',
     ' * (double free).'],
 2: [' * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra',
     ' *                 -std=c11 b32_c3_hatali.c -o b32_c3_hatali'],
 3: [],
},
"b32_c5_duzeltilmis.c": {
 11: ['    printf("%s' + BS + 'n", argv[1]);           /* girdi veri olarak */'],
},
"b32_c5_hatali.c": {
 1: ['/* b32_c5_hatali.c: kullanici girdisi bicim dizesi olarak',
     ' * kullaniliyor.'],
 2: [' * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c5_hatali.c',
     ' *          -o b32_c5_hatali'],
},
"b32_c7_aslr.c": {
 3: [' * Derleme: gcc -O0 -Wall -Wextra -std=c11 b32_c7_aslr.c',
     ' *          -o b32_c7_aslr'],
},
}

for fn, mp in FIX.items():
    with io.open(fn, encoding="utf-8") as f:
        lines = f.read().split("\n")
    out = []
    for i, line in enumerate(lines, 1):
        if i in mp:
            out.extend(mp[i])
        else:
            out.append(line)
    with io.open(fn, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
print("uygulandi")
