/* b27_kilitlenme.c - kilitlenme (deadlock): uretim, tespit, onlem.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_kilitlenme.c
 * Kullanim:
 *   ./a.out banka-bozuk
 *   ./a.out banka-sirali
 *   ./a.out filozof-bozuk
 *   ./a.out filozof-sirali
 *   ./a.out filozof-trylock
 * Tespit: 1 saniye icinde kilit alinamazsa "zaman asimi" yazilir ve
 * program 3 koduyla cikar. Zaman asimi kanit degil, suphedir.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define ZAMAN_ASIMI_SN 1
#define N 5

static void uyku_ms(long ms)
{
    struct timespec t = { ms / 1000, (ms % 1000) * 1000000L };
    nanosleep(&t, NULL);
}

static void uyku_us(long us)
{
    struct timespec t = { us / 1000000L, (us % 1000000L) * 1000L };
    nanosleep(&t, NULL);
}

/* Kilidi zaman asimiyla al; asilirsa kilitlenme suphesi raporla. */
static void kilitle(pthread_mutex_t *m, const char *ad)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += ZAMAN_ASIMI_SN;
    if (pthread_mutex_timedlock(m, &ts) == ETIMEDOUT) {
        printf("ZAMAN ASIMI: %s kilidi %d sn alinamadi\n",
               ad, ZAMAN_ASIMI_SN);
        printf("-> kilitlenme suphesi (cikis kodu 3)\n");
        fflush(stdout);
        _exit(3);
    }
}

/* ---------- banka havalesi ---------- */
typedef struct {
    pthread_mutex_t kilit;
    long bakiye;
    int id;
} Hesap;

static Hesap h[2];
static int SIRALI;
static long TUR;

static void havale(Hesap *a, Hesap *b, long miktar)
{
    Hesap *ilk = a, *ikinci = b;
    /* sirali: kilitleri her zaman kimlik sirasiyla al */
    if (SIRALI && b->id < a->id) {
        ilk = b;
        ikinci = a;
    }
    kilitle(&ilk->kilit, ilk->id ? "hesap B" : "hesap A");
    uyku_ms(1);             /* ara sicaklik: penceyi genis tut */
    kilitle(&ikinci->kilit, ikinci->id ? "hesap B" : "hesap A");
    a->bakiye -= miktar;
    b->bakiye += miktar;
    pthread_mutex_unlock(&ikinci->kilit);
    pthread_mutex_unlock(&ilk->kilit);
}

static void *banka_t1(void *p)
{
    (void)p;
    for (long i = 0; i < TUR; i++)
        havale(&h[0], &h[1], 1);      /* A -> B */
    return NULL;
}

static void *banka_t2(void *p)
{
    (void)p;
    for (long i = 0; i < TUR; i++)
        havale(&h[1], &h[0], 1);      /* B -> A */
    return NULL;
}

static void banka(int sirali)
{
    SIRALI = sirali;
    TUR = 200;
    for (int i = 0; i < 2; i++) {
        pthread_mutex_init(&h[i].kilit, NULL);
        h[i].bakiye = 1000;
        h[i].id = i;
    }
    pthread_t a, b;
    pthread_create(&a, NULL, banka_t1, NULL);
    pthread_create(&b, NULL, banka_t2, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    long toplam = h[0].bakiye + h[1].bakiye;
    printf("kilitlenme yok; toplam bakiye = %ld (beklenen 2000)\n",
           toplam);
}

/* ---------- yemek yiyen filozoflar ---------- */
static pthread_mutex_t cat[N];
static long yemek[N];
/* MODF: 0 bozuk, 1 sirali, 2 trylock */
static int MODF;
static long FTUR;

static void *filozof(void *p)
{
    int i = (int)(long)p;
    int sol = i, sag = (i + 1) % N;
    unsigned tohum = 17u + (unsigned)i;
    for (long t = 0; t < FTUR; t++) {
        if (MODF == 0) {
            kilitle(&cat[sol], "catal (sol)");
            uyku_ms(1);               /* herkes solu almis olsun */
            kilitle(&cat[sag], "catal (sag)");
        } else if (MODF == 1) {
            int a = sol < sag ? sol : sag;
            int b = sol < sag ? sag : sol;
            kilitle(&cat[a], "catal (kucuk)");
            uyku_ms(1);
            kilitle(&cat[b], "catal (buyuk)");
        } else {
            for (;;) {
                kilitle(&cat[sol], "catal (sol)");
                if (pthread_mutex_trylock(&cat[sag]) == 0)
                    break;
                pthread_mutex_unlock(&cat[sol]);
                /* rastgele geri cekilme */
                uyku_us(rand_r(&tohum) % 500);
            }
        }
        yemek[i]++;                   /* yemek */
        pthread_mutex_unlock(&cat[sag]);
        pthread_mutex_unlock(&cat[sol]);
    }
    return NULL;
}

static void filozoflar(int mod)
{
    MODF = mod;
    FTUR = 50;
    for (int i = 0; i < N; i++)
        pthread_mutex_init(&cat[i], NULL);
    pthread_t th[N];
    for (long i = 0; i < N; i++)
        pthread_create(&th[i], NULL, filozof, (void *)i);
    for (int i = 0; i < N; i++)
        pthread_join(th[i], NULL);
    long toplam = 0;
    for (int i = 0; i < N; i++)
        toplam += yemek[i];
    printf("kilitlenme yok; toplam yemek = %ld (beklenen %ld)\n",
           toplam, (long)N * FTUR);
}

int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "banka-bozuk")) banka(0);
    else if (!strcmp(argv[1], "banka-sirali")) banka(1);
    else if (!strcmp(argv[1], "filozof-bozuk")) filozoflar(0);
    else if (!strcmp(argv[1], "filozof-sirali")) filozoflar(1);
    else if (!strcmp(argv[1], "filozof-trylock")) filozoflar(2);
    else { fprintf(stderr, "bilinmeyen mod\n"); return 1; }
    return 0;
}
