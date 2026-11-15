/* b31_2_yapi.c: C struct hizalamasi ve ikili serilestirme tuzagi.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b31_2_yapi.c -o b31_2_yapi
 * Ortam: WSL2 Ubuntu 24.04, x86-64, gcc 13. Sonuclar bu mimaride
 * gecerlidir; baska mimari/derleyicide ofsetler farkli olabilir.
 */
#include <arpa/inet.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Dogal hizalama: derleyici alanlari hizalar, bosluk birakir. */
struct kotu {
    uint8_t tip;
    uint32_t uzunluk;
    uint16_t sira;
};

/* Ayni alanlar, buyukten kucuge siralanmis: bosluk azalir. */
struct iyi {
    uint32_t uzunluk;
    uint16_t sira;
    uint8_t tip;
};

static void hex_yaz(const char *ad, const void *p, size_t n)
{
    const unsigned char *b = p;
    printf("%-22s", ad);
    for (size_t i = 0; i < n; i++) printf(" %02X", b[i]);
    printf("\n");
}

/* Alanlari TELL ofsetlere, ag sirasiyla yaz. Bellek duzeni
 * ve hizalama bu fonksiyonda hic rol oynamaz. */
static size_t paket_yaz(uint8_t *tampon, uint8_t tip,
                        uint32_t uzunluk, uint16_t sira)
{
    tampon[0] = tip;                    /* 1 bayt, sira yok */
    uint32_t un = htonl(uzunluk);
    memcpy(tampon + 1, &un, 4);         /* 4 bayt, ag sirasi */
    uint16_t sn = htons(sira);
    memcpy(tampon + 5, &sn, 2);         /* 2 bayt, ag sirasi */
    return 7;                           /* toplam: dolgu yok */
}

int main(void)
{
    printf("sizeof(struct kotu) = %zu\n", sizeof(struct kotu));
    printf("  ofset tip=%zu uzunluk=%zu sira=%zu\n",
           offsetof(struct kotu, tip), offsetof(struct kotu, uzunluk),
           offsetof(struct kotu, sira));
    printf("sizeof(struct iyi)  = %zu\n", sizeof(struct iyi));
    printf("  ofset uzunluk=%zu sira=%zu tip=%zu\n",
           offsetof(struct iyi, uzunluk), offsetof(struct iyi, sira),
           offsetof(struct iyi, tip));

    /* Dolgu baytlari belirsizdir: once tamamini sifirla. */
    struct kotu k;
    memset(&k, 0, sizeof k);
    k.tip = 2;
    k.uzunluk = 3;
    k.sira = 7;
    hex_yaz("kotu (ham struct)", &k, sizeof k);

    uint8_t p[7];
    size_t n = paket_yaz(p, 2, 3, 7);
    hex_yaz("paket_yaz (ag)", p, n);

    /* Ham struct'i karsi tarafta okuyan bir makine (ayni derleyici,
     * ayni hizalama) bile dolgu yuzunden yanlis ofsetten okur. */
    uint32_t okunan_uzunluk;
    const uint8_t *ham = (const uint8_t *)&k;
    memcpy(&okunan_uzunluk, ham + offsetof(struct kotu, uzunluk), 4);
    printf("ham struct icinde uzunluk (LE bellek): 0x%08X\n",
           okunan_uzunluk);
    uint32_t agdan;
    memcpy(&agdan, p + 1, 4);
    printf("ag baytlarindan uzunluk (ntohl): %u\n", ntohl(agdan));
    return 0;
}
