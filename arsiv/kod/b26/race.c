/* race.c: iki iş parçacığı aynı sayacı kilitsiz artırır.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 -pthread race.c
 * Kayıp sayısı her çalıştırmada değişebilir:
 * bu bir yarış koşuludur. */
#include <pthread.h>
#include <stdio.h>

#define N 10000000L

static long sayac = 0;       /* iki iş parçacığı da yazar */

static void *artir(void *arg)
{
    (void)arg;
    for (long i = 0; i < N; i++)
        sayac++;             /* oku, artır, yaz: bölünemez */
    return NULL;
}

int main(void)
{
    pthread_t a, b;
    if (pthread_create(&a, NULL, artir, NULL) != 0 ||
        pthread_create(&b, NULL, artir, NULL) != 0) {
        fprintf(stderr, "pthread_create başarısız\n");
        return 1;
    }
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    printf("beklenen=%ld gerçekleşen=%ld kayıp=%ld\n",
           2 * N, sayac, 2 * N - sayac);
    return 0;
}
