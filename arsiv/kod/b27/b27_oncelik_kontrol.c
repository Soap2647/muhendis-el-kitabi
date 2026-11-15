/* b27_oncelik_kontrol.c - SCHED_FIFO ve PTHREAD_PRIO_INHERIT izni */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
int main(void)
{
    struct sched_param sp = { .sched_priority = 10 };
    int r = sched_setscheduler(0, SCHED_FIFO, &sp);
    printf("SCHED_FIFO: %s\n", r == 0 ? "izinli" : strerror(errno));
    pthread_mutexattr_t a;
    pthread_mutexattr_init(&a);
    int p = pthread_mutexattr_setprotocol(&a, PTHREAD_PRIO_INHERIT);
    printf("PRIO_INHERIT ayari: %s\n",
           p == 0 ? "tamam" : strerror(p));
    int q;
    pthread_mutexattr_getprotocol(&a, &q);
    printf("protokol degeri = %d (PTHREAD_PRIO_INHERIT=%d)\n", q,
           PTHREAD_PRIO_INHERIT);
    return 0;
}
