/* test_host.c: host (WSL) birim testleri. Basarisizlikta cikis 1. */
#include <stdio.h>
#include <string.h>
#include "crc16.h"
#include "cobs.h"
#include "telemetri_cerceve.h"
#include "halka.h"
#include "daly.h"

static int hata = 0;
#define KONTROL(kosul, ad)                                  \
    do {                                                    \
        if (kosul) printf("  TAMAM  %s\n", ad);              \
        else { printf("  HATA   %s\n", ad); hata++; }        \
    } while (0)

static uint32_t lcg = 45u;                  /* sabit tohum */
static uint8_t rnd8(void) {
    lcg = lcg * 1664525u + 1013904223u;
    return (uint8_t)(lcg >> 24);
}

static void test_crc(void) {
    const uint8_t v[] = "123456789";
    KONTROL(crc16_ccitt(v, 9) == 0x29B1u, "CRC-16 '123456789' = 0x29B1");
}

static void test_cobs(void) {
    const uint8_t ornek[] = {0x11, 0x22, 0x00, 0x33};
    const uint8_t bek[] = {0x03, 0x11, 0x22, 0x02, 0x33};
    uint8_t k[16], c[16];
    int n = cobs_kodla(ornek, 4, k, sizeof k);
    KONTROL(n == 5 && memcmp(k, bek, 5) == 0, "COBS 11 22 00 33");
    int m = cobs_coz(k, (size_t)n, c, sizeof c);
    KONTROL(m == 4 && memcmp(c, ornek, 4) == 0, "COBS geri cozum");
    /* rastgele gidis-donus, 0 iceren ve 254 sinirli uzunluklar */
    int ok = 1;
    for (int t = 0; t < 3000 && ok; t++) {
        uint8_t g[600], kk[700], cc[600];
        size_t len = (size_t)(rnd8() * 2u + (t % 7));
        for (size_t i = 0; i < len; i++)
            g[i] = (rnd8() < 80) ? 0 : rnd8();
        int a = cobs_kodla(g, len, kk, sizeof kk);
        int b = a < 0 ? -1 : cobs_coz(kk, (size_t)a, cc, sizeof cc);
        if (a < 0 || b != (int)len || memcmp(g, cc, len) != 0)
            ok = 0;
        for (int i = 0; i < a; i++)
            if (kk[i] == 0) ok = 0;
    }
    KONTROL(ok, "COBS 3000 rastgele gidis-donus, sifir yok");
    uint8_t dar[3];
    KONTROL(cobs_kodla(ornek, 4, dar, sizeof dar) == -1,
            "COBS kapasite yetmezse -1");
}

static void test_cerceve(void) {
    tel_yuk_t y = {12, 87, 523, 143, 25, -3, 3300, 'D', 1, 0, 0};
    const uint8_t bek[] = {0x04,0x01,0x07,0x0c,0x05,0x57,0x0b,0x02,
                           0x8f,0x07,0x19,0xfd,0xe4,0x0c,0x44,0x01,
                           0x01,0x03,0xbd,0xcb,0x00};
    uint8_t k[32];
    int n = tel_kodla(&y, 7, k, sizeof k);
    KONTROL(n == 21 && memcmp(k, bek, 21) == 0,
            "cerceve bayt-bayt = Python ciktisi (21 bayt)");
    KONTROL(tel_kodla(&y, 7, k, 10) == -1, "kucuk tampon -> -1");
}

static void test_halka(void) {
    halka_t h;
    uint8_t ref[HALKA_KAPASITE * 4];
    uint32_t rb = 0, rw = 0;
    int ok = 1;
    halka_sifirla(&h);
    for (int i = 0; i < 20000; i++) {
        if (rnd8() & 1) {                   /* yaz */
            int r = halka_yaz(&h, (uint8_t)i);
            int dolu = (rw - rb) >= HALKA_KAPASITE;
            if (dolu != (r == -1)) ok = 0;
            if (!dolu) { ref[rw % sizeof ref] = (uint8_t)i; rw++; }
        } else {                            /* oku */
            uint8_t b = 0;
            int r = halka_oku(&h, &b);
            int bos = (rw == rb);
            if (bos != (r == -1)) ok = 0;
            if (!bos) {
                if (b != ref[rb % sizeof ref]) ok = 0;
                rb++;
            }
        }
    }
    KONTROL(ok, "halka: 20000 rastgele islem, referansla ayni");
}

typedef struct { const uint8_t *v; size_t n, p; int timeout_at; } sahte_t;

static int s_gonder(void *c, const uint8_t *v, uint32_t n) {
    (void)c; (void)v; (void)n; return 0;
}
static int s_al(void *c, uint8_t *b, uint32_t zm) {
    sahte_t *s = (sahte_t *)c; (void)zm;
    if (s->p >= s->n || (int)s->p == s->timeout_at) return -1;
    *b = s->v[s->p++];
    return 0;
}
static void s_temizle(void *c) { (void)c; }

static int dene(const uint8_t *v, size_t n, int tmo, uint8_t komut,
                uint8_t *cevap) {
    sahte_t s = {v, n, 0, tmo};
    daly_io_t io = {&s, s_gonder, s_al, s_temizle};
    return daly_sorgu(&io, komut, cevap);
}

static void makeframe(uint8_t *g, uint8_t komut) {
    uint8_t s = 0;
    g[0] = 0xA5; g[1] = 0x01; g[2] = komut; g[3] = 0x08;
    for (int i = 4; i < 12; i++) g[i] = (uint8_t)(i * 7);
    for (int i = 0; i < 12; i++) s = (uint8_t)(s + g[i]);
    g[12] = s;
}

static void test_daly(void) {
    uint8_t f[13], c[13], buf[64];
    makeframe(f, 0x90);
    KONTROL(dene(f, 13, -1, 0x90, c) == 0, "daly: dogru cerceve -> 0");
    uint8_t gu[20] = {0x11,0x22,0x33,0x44,0x55,0x66,0x77};
    memcpy(buf, gu, 7); memcpy(buf + 7, f, 13);
    KONTROL(dene(buf, 20, -1, 0x90, c) == 0,
            "daly: gurultu sonrasi senkron -> 0");
    uint8_t bz[13]; memcpy(bz, f, 13); bz[12] ^= 1;
    KONTROL(dene(bz, 13, -1, 0x90, c) == -2, "daly: bozuk sagalama -> -2");
    KONTROL(dene(f, 13, -1, 0x92, c) == -2, "daly: komut eslesmiyor -> -2");
    KONTROL(dene(f, 9, -1, 0x90, c) == -1, "daly: yarim cerceve -> -1");
    uint8_t ad[13]; memcpy(ad, f, 13); ad[1] = 0x02;
    KONTROL(dene(ad, 13, -1, 0x90, c) == -2, "daly: adres 0x02 -> -2");
}

int main(void) {
    printf("CRC\n"); test_crc();
    printf("COBS\n"); test_cobs();
    printf("CERCEVE\n"); test_cerceve();
    printf("HALKA\n"); test_halka();
    printf("DALY\n"); test_daly();
    printf("\nSonuc: %s (%d hata)\n", hata ? "BASARISIZ" : "TAMAM", hata);
    return hata ? 1 : 0;
}
