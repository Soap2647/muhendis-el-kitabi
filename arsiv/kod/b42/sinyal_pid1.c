/* sinyal_pid1.c: PID ad alanında 1 numaralı süreçte SIGTERM.
 * Kullanım: ./sinyal_pid1 yok   (işleyici yok)
 *           ./sinyal_pid1 var   (işleyici var)
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L sinyal_pid1.c */
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t alindi = 0;

static void on_term(int sig)
{
    (void)sig;
    alindi = 1;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc > 1 && strcmp(argv[1], "var") == 0) {
        struct sigaction sa;
        memset(&sa, 0, sizeof sa);
        sa.sa_handler = on_term;
        sigaction(SIGTERM, &sa, NULL);
    }
    printf("pid=%d hazir\n", (int)getpid());
    for (int i = 0; i < 30 && !alindi; i++)
        sleep(1);
    printf("pid=%d %s\n", (int)getpid(),
           alindi ? "SIGTERM yakalandi, temiz cikis"
                  : "30 sn bitti, SIGTERM gelmedi");
    return 0;
}
