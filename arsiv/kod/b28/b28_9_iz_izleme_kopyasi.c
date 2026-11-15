/* izleme kopyasi: olay dongusunun tur bazli dokumu (kitapta yok) */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/epoll.h>
int main(void){
    enum { N = 1000, TUR = 20, K = 5 };
    int (*bl)[2] = malloc(N * sizeof *bl);
    int ep = epoll_create1(0);
    for (int i = 0; i < N; i++) {
        pipe(bl[i]);
        fcntl(bl[i][0], F_SETFL, O_NONBLOCK);
        struct epoll_event ev = { .events = EPOLLIN, .data.u32 = i };
        epoll_ctl(ep, EPOLL_CTL_ADD, bl[i][0], &ev);
    }
    srand(28);
    struct epoll_event olaylar[64];
    char t[64];
    for (int tur = 0; tur < 4; tur++) {
        printf("tur %d yazilan:", tur);
        for (int k = 0; k < K; k++) {
            int id = rand() % N;
            printf(" %d", id);
            write(bl[id][1], "veri", 4);
        }
        int m = epoll_wait(ep, olaylar, 64, 0);
        printf("\n   epoll_wait=%d hazir:", m);
        for (int i = 0; i < m; i++) {
            int id = (int)olaylar[i].data.u32;
            printf(" %d", id);
            while (read(bl[id][0], t, sizeof t) > 0) ;
        }
        printf("\n");
    }
    return 0;
}
