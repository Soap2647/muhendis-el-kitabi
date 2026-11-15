# -*- coding: utf-8 -*-
"""Bölüm 41.3 - Kapasite tahmini (back-of-the-envelope).
Varsayımlar metinde açıkça yazılmıştır. Ölçüm değil, hesaptır.
"""

# --- 1) Genel şablon: kullanıcı tabanlı istek tahmini ---------------
kullanici_gun = 10_000_000  # günlük aktif kullanıcı (varsayım)
istek_kullanici_gun = 20  # kullanıcı başına günlük istek
gun_saniye = 86400
ortalama = kullanici_gun * istek_kullanici_gun / gun_saniye
tepe_katsayi = 3  # ortalamanın kaç katı tepe (varsayım)
print("Ortalama istek/s : %.0f" % ortalama)
print("Tepe istek/s     : %.0f" % (ortalama * tepe_katsayi))

#@@
# --- 2) İHA filosu telemetrisi -------------------------------------
ARAC = 40  # filodaki İHA sayısı (varsayım)
HZ = 100  # her araçtan saniyede paket
PAKET = 256  # bayt: başlık + ölçümler + CRC (varsayım)
SIKISMA = 5  # ham/sıkıştırılmış oran (varsayım: 5:1)

paket_s = ARAC * HZ
bayt_s = paket_s * PAKET
print()
print("İHA filosu telemetrisi")
print("Paket/s (filo)        : %d" % paket_s)
print(
    "Ham bayt/s            : %d (%.3f MB/s)" % (bayt_s, bayt_s / 1e6)
)
print("Ham bit/s             : %.2f Mbit/s" % (bayt_s * 8 / 1e6))
print("Tepe (2x) bit/s       : %.2f Mbit/s" % (2 * bayt_s * 8 / 1e6))
gun_ham = bayt_s * gun_saniye
print("Ham depolama / gün    : %.1f GB" % (gun_ham / 1e9))
print("Sıkıştırılmış / gün   : %.1f GB" % (gun_ham / SIKISMA / 1e9))
print(
    "Sıkıştırılmış / yıl   : %.1f TB"
    % (gun_ham / SIKISMA * 365 / 1e12)
)
print(
    "Tek bir paket başına  : %.1f us (4000 paket/s için pay)"
    % (1e6 / paket_s)
)

#@@
# --- 3) Gecikme bütçesi (Bölüm 25 ve 35 sayıları) -------------------
DRAM_NS = 120  # Bölüm 25.4 ölçümü, 110-130 ns
NVME_US = 100  # genel bilgi
AG_MS = 0.5  # genel bilgi, aynı veri merkezi
print()
print("Bir paketin yol üzerindeki kabaca maliyeti:")
print("  bellek (DRAM)       : %d ns" % DRAM_NS)
print("  NVMe diske yazma    : %d us" % NVME_US)
print("  ağ turu (aynı DC)   : %.1f ms" % AG_MS)
print(
    "Tek bağlantıda sıralı (her paket bir tur) en fazla: %d paket/s"
    % (1000 / AG_MS)
)
print(
    "Filo gereksinimi                        : %d paket/s" % paket_s
)
print(
    "Bağlantı sayısı (en az, tur başına)     : %d"
    % (paket_s / (1000 / AG_MS))
)
