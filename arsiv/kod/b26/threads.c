/* threads.c: iş parçacıkları ile süreç kaynaklarının
 * karşılaştırılması.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread threads.c */
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

/* veri bölümünde; tüm iş parçacıkları görür */
int global_sayi = 42;

static void *is(void *arg)
{
    int yerel = 7;           /* kendi yığınında yaşar */
    printf("%s: pid=%d tid=%ld global=%p yerel=%p\n",
           (const char *)arg, (int)getpid(),
           (long)syscall(SYS_gettid),
           (void *)&global_sayi, (void *)&yerel);
    return NULL;
}

int main(void)
{
    pthread_attr_t attr;
    size_t yigin;
    pthread_attr_init(&attr);
    pthread_attr_getstacksize(&attr, &yigin);
    printf("varsayılan iş parçacığı yığını: %zu KB\n",
           yigin / 1024);
    pthread_attr_destroy(&attr);

    printf("ana: pid=%d tid=%ld\n",
           (int)getpid(), (long)syscall(SYS_gettid));

    pthread_t a, b;
    pthread_create(&a, NULL, is, "A");
    pthread_create(&b, NULL, is, "B");
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    return 0;
}
