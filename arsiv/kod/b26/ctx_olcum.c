/* ctx_olcum.c: sistem çağrısı, bağlam değişimi (boru ping-pong)
 * ve süreç/iş parçacığı oluşturma maliyetini ölçer. Çıktı CSV'dir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread
 * Kullanım: ./ctx_olcum [tekrar]  (varsayılan 5) */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define N_PINGPONG 100000L
#define N_SYSCALL  2000000L
#define N_OLUSTUR  2000L

static double simdi_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

/* Bu çağrıyı yapan iş parçacığını CPU 0'a sabitler. */
static void tek_cpu(void)
{
    cpu_set_t c;
    CPU_ZERO(&c);
    CPU_SET(0, &c);
    sched_setaffinity(0, sizeof c, &c);
}

/* İki boru: ba = ebeveyn->çocuk, bb = çocuk->ebeveyn */
static int ba[2], bb[2];

static void *is_yanki(void *arg)
{
    char c;
    (void)arg;
    for (long i = 0; i < N_PINGPONG; i++) {
        if (read(ba[0], &c, 1) != 1) break;
        if (write(bb[1], &c, 1) != 1) break;
    }
    return NULL;
}

/* Tur başına ortalama süre (ns).
 * Bir tur: 2 bağlam değişimi + 4 sistem çağrısı. */
static double ping_surec(void)
{
    char c = 'x';
    tek_cpu();              /* çocuk fork'tan affinity miras alır */
    if (pipe(ba) < 0 || pipe(bb) < 0) exit(1);
    pid_t pid = fork();
    if (pid == 0) {
        is_yanki(NULL);
        _exit(0);
    }
    double t0 = simdi_ns();
    for (long i = 0; i < N_PINGPONG; i++) {
        if (write(ba[1], &c, 1) != 1) break;
        if (read(bb[0], &c, 1) != 1) break;
    }
    double t1 = simdi_ns();
    waitpid(pid, NULL, 0);
    return (t1 - t0) / N_PINGPONG;
}

static double ping_is(void)
{
    char c = 'x';
    pthread_t t;
    tek_cpu();
    if (pipe(ba) < 0 || pipe(bb) < 0) exit(1);
    pthread_create(&t, NULL, is_yanki, NULL);
    double t0 = simdi_ns();
    for (long i = 0; i < N_PINGPONG; i++) {
        if (write(ba[1], &c, 1) != 1) break;
        if (read(bb[0], &c, 1) != 1) break;
    }
    double t1 = simdi_ns();
    pthread_join(t, NULL);
    return (t1 - t0) / N_PINGPONG;
}

static double syscall_ns(void)
{
    volatile long sonuc = 0;
    double t0 = simdi_ns();
    for (long i = 0; i < N_SYSCALL; i++)
        sonuc += syscall(SYS_getppid);
    /* glibc getppid'i önbelleklemez: her çağrı çekirdeğe gider */
    double t1 = simdi_ns();
    return (t1 - t0) / N_SYSCALL;
}

static void *bos_is(void *arg)
{
    (void)arg;
    return NULL;
}

static double surec_olustur_ns(void)
{
    double t0 = simdi_ns();
    for (long i = 0; i < N_OLUSTUR; i++) {
        pid_t p = fork();
        if (p == 0) _exit(0);
        waitpid(p, NULL, 0);
    }
    return (simdi_ns() - t0) / N_OLUSTUR;
}

static double is_olustur_ns(void)
{
    double t0 = simdi_ns();
    for (long i = 0; i < N_OLUSTUR; i++) {
        pthread_t t;
        pthread_create(&t, NULL, bos_is, NULL);
        pthread_join(t, NULL);
    }
    return (simdi_ns() - t0) / N_OLUSTUR;
}

int main(int argc, char **argv)
{
    int tekrar = (argc > 1) ? atoi(argv[1]) : 5;
    printf("olcum,tekrar,deger_ns\n");
    for (int k = 1; k <= tekrar; k++) {
        printf("syscall_getppid,%d,%.1f\n", k, syscall_ns());
        printf("pingpong_surec_cpu0,%d,%.1f\n", k, ping_surec());
        printf("pingpong_is_cpu0,%d,%.1f\n", k, ping_is());
        printf("olustur_surec,%d,%.1f\n", k, surec_olustur_ns());
        printf("olustur_is,%d,%.1f\n", k, is_olustur_ns());
    }
    return 0;
}
