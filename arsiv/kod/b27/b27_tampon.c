/* b27_tampon.c - sinirli tampon: mutex + iki condvar, ve semafor.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_tampon.c
 * Sahte uyanma deneyi icin: -DIF_HATASI ekle (if ile bekleme).
 * Kullanim:
 *   ./a.out kv <uretici> <tuketici> <adet>   (condvar)
 *   ./a.out sem <uretici> <tuketici> <adet>  (semafor)
 *   ./a.out sahte                            (sahte uyanma)
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define KAPASITE 16

typedef struct {
    int veri[KAPASITE];
    int bas;                 /* okunacak indeks */
    int kuyruk;              /* yazilacak indeks */
    int sayi;                /* dolu hucre sayisi */
    pthread_mutex_t kilit;
    pthread_cond_t bos_degil;   /* tuketici bekler */
    pthread_cond_t dolu_degil;  /* uretici bekler */
} Tampon;

static void tampon_baslat(Tampon *t)
{
    t->bas = t->kuyruk = t->sayi = 0;
    pthread_mutex_init(&t->kilit, NULL);
    pthread_cond_init(&t->bos_degil, NULL);
    pthread_cond_init(&t->dolu_degil, NULL);
}

static void tampon_koy(Tampon *t, int x)
{
    pthread_mutex_lock(&t->kilit);
    while (t->sayi == KAPASITE)            /* while: sahte uyanma */
        pthread_cond_wait(&t->dolu_degil, &t->kilit);
    t->veri[t->kuyruk] = x;
    t->kuyruk = (t->kuyruk + 1) % KAPASITE;
    t->sayi++;
    pthread_cond_signal(&t->bos_degil);
    pthread_mutex_unlock(&t->kilit);
}

static int tampon_al(Tampon *t)
{
    pthread_mutex_lock(&t->kilit);
    while (t->sayi == 0)
        pthread_cond_wait(&t->bos_degil, &t->kilit);
    int x = t->veri[t->bas];
    t->bas = (t->bas + 1) % KAPASITE;
    t->sayi--;
    pthread_cond_signal(&t->dolu_degil);
    pthread_mutex_unlock(&t->kilit);
    return x;
}

/* ---------- semafor surumu ---------- */
typedef struct {
    int veri[KAPASITE];
    int bas, kuyruk;
    pthread_mutex_t kilit;
    sem_t bos;               /* kac bos hucre var */
    sem_t dolu;              /* kac dolu hucre var */
} SemTampon;

static void semtampon_baslat(SemTampon *t)
{
    t->bas = t->kuyruk = 0;
    pthread_mutex_init(&t->kilit, NULL);
    sem_init(&t->bos, 0, KAPASITE);
    sem_init(&t->dolu, 0, 0);
}

static void semtampon_koy(SemTampon *t, int x)
{
    sem_wait(&t->bos);                     /* P(bos) */
    pthread_mutex_lock(&t->kilit);
    t->veri[t->kuyruk] = x;
    t->kuyruk = (t->kuyruk + 1) % KAPASITE;
    pthread_mutex_unlock(&t->kilit);
    sem_post(&t->dolu);                    /* V(dolu) */
}

static int semtampon_al(SemTampon *t)
{
    sem_wait(&t->dolu);
    pthread_mutex_lock(&t->kilit);
    int x = t->veri[t->bas];
    t->bas = (t->bas + 1) % KAPASITE;
    pthread_mutex_unlock(&t->kilit);
    sem_post(&t->bos);
    return x;
}

/* ---------- test: P uretici, C tuketici ---------- */
static Tampon kv;
static SemTampon sm;
static int MOD;                           /* 0 kv, 1 sem */
static int M;                             /* uretici basina adet */
static int P, C;

typedef struct {
    long toplam;
    long adet;
} Sonuc;

static void *uretici(void *p)
{
    long id = (long)p;
    for (int i = 0; i < M; i++) {
        int deger = (int)(id * M + i);     /* benzersiz deger */
        if (MOD == 0) tampon_koy(&kv, deger);
        else semtampon_koy(&sm, deger);
    }
    return NULL;
}

static void *tuketici(void *p)
{
    Sonuc *s = p;
    for (;;) {
        int x = (MOD == 0) ? tampon_al(&kv) : semtampon_al(&sm);
        if (x < 0) break;                  /* zehirli hap: dur */
        s->toplam += x;
        s->adet++;
    }
    return NULL;
}

static void sonuc_yaz(Sonuc *top, long beklenen_adet,
                       long beklenen_top)
{
    int tam = (top->adet == beklenen_adet) &&
              (top->toplam == beklenen_top);
    printf("alinan adet=%ld (beklenen %ld)\n",
           top->adet, beklenen_adet);
    printf("toplam     =%ld (beklenen %ld)\n",
           top->toplam, beklenen_top);
    printf("sonuc: %s\n", tam ? "DOGRU" : "HATA");
}

static int dogrulama_calistir(int mod, int p, int c, int m)
{
    MOD = mod; P = p; C = c; M = m;
    if (MOD == 0) tampon_baslat(&kv);
    else semtampon_baslat(&sm);

    pthread_t up[32], tp[32];
    static Sonuc son[32];
    memset(son, 0, sizeof son);
    for (long i = 0; i < P; i++)
        pthread_create(&up[i], NULL, uretici, (void *)i);
    for (long i = 0; i < C; i++)
        pthread_create(&tp[i], NULL, tuketici, &son[i]);
    for (int i = 0; i < P; i++)
        pthread_join(up[i], NULL);
    /* uretici bitti: C tuketiciyi durdurmak icin C zehirli hap */
    for (int i = 0; i < C; i++) {
        if (MOD == 0) tampon_koy(&kv, -1);
        else semtampon_koy(&sm, -1);
    }
    for (int i = 0; i < C; i++)
        pthread_join(tp[i], NULL);

    Sonuc top;
    memset(&top, 0, sizeof top);
    for (int i = 0; i < C; i++) {
        top.toplam += son[i].toplam;
        top.adet += son[i].adet;
    }
    long beklenen_top = 0;
    for (long id = 0; id < P; id++)
        for (long i = 0; i < M; i++)
            beklenen_top += id * M + i;
    sonuc_yaz(&top, (long)P * M, beklenen_top);
    return top.adet == (long)P * M && top.toplam == beklenen_top;
}

/* ---------- sahte uyanma: if ile bekleyen tuketici ---------- */
static void uyku_ms(long ms)
{
    struct timespec t = { ms / 1000, (ms % 1000) * 1000000L };
    nanosleep(&t, NULL);
}

static Tampon st;
/* tuketici kilit altinda isaretler */
static int bekliyor;
static int hata_sayisi;

static void *sahte_tuketici(void *p)
{
    (void)p;
    pthread_mutex_lock(&st.kilit);
    bekliyor = 1;
#ifdef IF_HATASI
    if (st.sayi == 0)                     /* yanlis: if */
        pthread_cond_wait(&st.bos_degil, &st.kilit);
    if (st.sayi == 0) {                   /* uyandi ama tampon bos */
        hata_sayisi++;
        printf("HATA: uyandi ama tampon BOS (sahte uyanma)\n");
        pthread_mutex_unlock(&st.kilit);
        return NULL;
    }
#else
    while (st.sayi == 0)                  /* dogru: while */
        pthread_cond_wait(&st.bos_degil, &st.kilit);
#endif
    int x = st.veri[st.bas];
    st.bas = (st.bas + 1) % KAPASITE;
    st.sayi--;
    printf("tuketici aldi: %d\n", x);
    pthread_mutex_unlock(&st.kilit);
    return NULL;
}

static void sahte_deney(void)
{
    tampon_baslat(&st);
    bekliyor = 0;
    pthread_t t;
    pthread_create(&t, NULL, sahte_tuketici, NULL);
    /* tuketici beklemeye gecene kadar bekle */
    for (;;) {
        pthread_mutex_lock(&st.kilit);
        int b = bekliyor;
        pthread_mutex_unlock(&st.kilit);
        if (b) break;
        uyku_ms(1);
    }
    uyku_ms(20);                        /* cond_wait'e tam otursun */
    /* 1) veri yok, ama sinyal var: sahte uyanma */
    pthread_mutex_lock(&st.kilit);
    pthread_cond_broadcast(&st.bos_degil);
    pthread_mutex_unlock(&st.kilit);
    uyku_ms(50);
    /* 2) simdi gercek veri koy ve sinyal ver */
    pthread_mutex_lock(&st.kilit);
    st.veri[st.kuyruk] = 7;
    st.kuyruk = (st.kuyruk + 1) % KAPASITE;
    st.sayi++;
    pthread_cond_signal(&st.bos_degil);
    pthread_mutex_unlock(&st.kilit);
    pthread_join(t, NULL);
    printf("hata sayisi = %d\n", hata_sayisi);
}

int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "sahte")) {
        sahte_deney();
        return 0;
    }
    if (argc < 5) return 1;
    int mod = !strcmp(argv[1], "sem");
    int ok = dogrulama_calistir(mod, atoi(argv[2]), atoi(argv[3]),
                                atoi(argv[4]));
    return ok ? 0 : 2;
}
