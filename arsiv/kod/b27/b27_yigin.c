/* b27_yigin.c - kilitsiz (lock-free) Treiber yigini ve ABA.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_yigin.c
 * Kullanim:
 *   ./a.out aba                 (adim adim ABA senaryosu)
 *   ./a.out naive <thread> <r> <pencere>  (etiketsiz head)
 *   ./a.out tagged <thread> <r> <pencere> (etiketli head)
 *   pencere=1: okuma ile CAS arasina sched_yield koyar
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>

#define DUGUM 64
#define NIL 0xFFFFFFFFu
#define PAKET(etiket, idx) (((uint64_t)(etiket) << 32) | (idx))
#define IDX(h) ((uint32_t)(h))
#define ETIKET(h) ((uint32_t)((h) >> 32))

static _Atomic uint32_t sonraki[DUGUM];   /* yiginda bir sonraki */
static _Atomic uint32_t bas_naif;         /* etiketsiz bas */
static _Atomic uint64_t bas_etiketli;     /* etiket + indeks */
/* 1'den fazlaysa cift sahiplik */
static _Atomic int sahiplik[DUGUM];
static _Atomic long cift_sahip;
static int MOD;                           /* 0 naif, 1 etiketli */
/* 1: okuma ile CAS arasina kesinti */
static int PENCERE;

/* ---------- etiketsiz (ABA'ya acik) ---------- */
static void naif_it(uint32_t i)
{
    uint32_t eski = atomic_load(&bas_naif);
    do {
        atomic_store(&sonraki[i], eski);
    } while (!atomic_compare_exchange_weak(&bas_naif, &eski, i));
}

static uint32_t naif_cek(void)
{
    uint32_t eski = atomic_load(&bas_naif);
    for (;;) {
        if (eski == NIL)
            return NIL;
        uint32_t n = atomic_load(&sonraki[eski]);
        if (PENCERE) sched_yield();   /* ABA penceresini genislet */
        if (atomic_compare_exchange_weak(&bas_naif, &eski, n))
            return eski;
    }
}

/* ---------- etiketli (ABA'ya karsi) ---------- */
static void etiketli_it(uint32_t i)
{
    uint64_t eski = atomic_load(&bas_etiketli);
    uint64_t yeni;
    do {
        atomic_store(&sonraki[i], IDX(eski));
        yeni = PAKET(ETIKET(eski) + 1, i);
    } while (!atomic_compare_exchange_weak(&bas_etiketli,
                                           &eski, yeni));
}

static uint32_t etiketli_cek(void)
{
    uint64_t eski = atomic_load(&bas_etiketli);
    for (;;) {
        uint32_t idx = IDX(eski);
        if (idx == NIL)
            return NIL;
        uint32_t n = atomic_load(&sonraki[idx]);
        uint64_t yeni = PAKET(ETIKET(eski) + 1, n);
        if (PENCERE) sched_yield();   /* ABA penceresini genislet */
        if (atomic_compare_exchange_weak(&bas_etiketli, &eski, yeni))
            return idx;
    }
}

/* ---------- ABA senaryosu: adim adim, tek iparcacik ---------- */
/* Burada CAS'i duz degiskenlerle taklit ediyoruz: amac durumu
 * adim adim gostermek; eszamanlilik yok. */
static uint32_t S[3];                     /* A=0, B=1, C=2 */
static uint32_t HEAD;
static const char *AD[3] = {"A", "B", "C"};

static void yaz_durum(const char *etiket)
{
    printf("%-30s head=", etiket);
    if (HEAD == NIL) { printf("NIL"); }
    else { printf("%s", AD[HEAD]); }
    printf("  zincir: ");
    uint32_t c = HEAD;
    int adim = 0;
    while (c != NIL && adim < 3) {
        printf("%s", AD[c]);
        c = S[c];
        if (c != NIL) printf(" -> ");
        adim++;
    }
    if (c != NIL) printf("...(dongu!)");
    printf("\n");
}

static void aba_senaryosu(void)
{
    S[0] = 1; S[1] = 2; S[2] = NIL; HEAD = 0;   /* A -> B -> C */
    yaz_durum("baslangic:");

    uint32_t t1_eski = HEAD;                    /* T1: eski = A */
    uint32_t t1_sonraki = S[t1_eski];           /* T1: sonraki = B */
    printf("T1 eski=%s, sonraki=%s okudu, duraklatildi\n",
           AD[t1_eski], AD[t1_sonraki]);

    HEAD = S[HEAD]; /* T2 pop: A cikar, head = B */
    HEAD = S[HEAD]; /* T2 pop: B cikar, head = C */
    S[0] = HEAD; HEAD = 0;                      /* T2 push: A geri */
    yaz_durum("T2 A,B cikardi, A geri koydu:");

    if (HEAD == t1_eski) {                      /* T1 CAS(head,A,B) */
        HEAD = t1_sonraki;
        printf("T1 CAS basarili (head hala A!) -> head = B\n");
    }
    yaz_durum("T1 CAS sonrasi:");
    printf("A artik zincirde degil: sizdi.\n");

    S[1] = HEAD;                        /* T2 B'yi geri iter */
    HEAD = 1;
    yaz_durum("T2 B'yi geri itti:");
}

/* ---------- stres ---------- */
static int R;
static int TH;

static uint64_t xorshift(uint64_t *s)
{
    uint64_t x = *s;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    return *s = x;
}

static void *isci(void *p)
{
    uint64_t rng = 0x9E3779B97F4A7C15ull ^ (uintptr_t)p;
    for (int r = 0; r < R; r++) {
        uint32_t i = (MOD == 0) ? naif_cek() : etiketli_cek();
        if (i == NIL) continue;
        if (atomic_fetch_add(&sahiplik[i], 1) != 0)
            atomic_fetch_add(&cift_sahip, 1);
        int bekle = (int)(xorshift(&rng) % 64);
        for (int k = 0; k < bekle; k++)
            sched_yield();
        atomic_fetch_sub(&sahiplik[i], 1);
        if (MOD == 0) naif_it(i); else etiketli_it(i);
    }
    return NULL;
}

static void stres(void)
{
    /* bas bos olmali: sifir degeri 0 numarali dugume isaret eder */
    atomic_store(&bas_naif, NIL);
    atomic_store(&bas_etiketli, PAKET(0, NIL));
    for (uint32_t i = 0; i < DUGUM; i++) {
        if (MOD == 0) naif_it(DUGUM - 1 - i);
        else etiketli_it(DUGUM - 1 - i);
    }
    pthread_t th[32];
    for (long i = 0; i < TH; i++)
        pthread_create(&th[i], NULL, isci, (void *)(i + 1));
    for (int i = 0; i < TH; i++)
        pthread_join(th[i], NULL);

    /* yigini bosalt; dongu ya da fazla eleman varsa bozulmus */
    int say = 0, dongu = 0;
    uint32_t c = (MOD == 0) ? bas_naif : IDX(bas_etiketli);
    while (c != NIL) {
        if (++say > DUGUM) { dongu = 1; break; }
        c = atomic_load(&sonraki[c]);
    }
    printf("%s thread=%d r=%d\n", MOD ? "etiketli" : "naif",
           TH, R);
    printf("cift sahiplik: %ld\n", atomic_load(&cift_sahip));
    if (dongu)
        printf("yigin: DONGU VAR (bozuldu)\n");
    else
        printf("yigin uzunlugu: %d (beklenen %d)\n", say, DUGUM);
}

int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "aba")) {
        aba_senaryosu();
        return 0;
    }
    if (argc < 5) return 1;
    MOD = !strcmp(argv[1], "tagged");
    TH = atoi(argv[2]);
    R = atoi(argv[3]);
    PENCERE = atoi(argv[4]);
    stres();
    return 0;
}
