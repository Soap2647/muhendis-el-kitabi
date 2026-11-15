/* uretici_tuketici.c: ebeveyn 1..10 sayılarını bir boruya
 * yazar, çocuk okuyup toplar. Boru EOF'u, yazma ucu
 * kapanınca gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int boru[2];
    if (pipe(boru) < 0) {
        perror("pipe");
        return 1;
    }
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {                  /* TÜKETİCİ */
        close(boru[1]);     /* yazma ucu bu süreçte gereksiz */
        int x, toplam = 0;
        while (read(boru[0], &x, sizeof x)
               == (ssize_t)sizeof x) {
            printf("aldı: %d\n", x);
            toplam += x;
        }                   /* read 0 dönünce EOF */
        printf("toplam=%d\n", toplam);
        close(boru[0]);
        return 0;
    }

    close(boru[0]);         /* okuma ucu bu süreçte gereksiz */
    for (int i = 1; i <= 10; i++) {
        if (write(boru[1], &i, sizeof i)
            != (ssize_t)sizeof i) {
            perror("write");
            break;
        }
    }
    close(boru[1]);         /* EOF'u tetikler */
    waitpid(pid, NULL, 0);
    return 0;
}
