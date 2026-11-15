/* b28_13_fork_tampon.c: fork öncesi tampon ve çift çıktı */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char **argv)
{
    int bosalt = argc > 1 && strcmp(argv[1], "flush") == 0;

    printf("A");                     /* satır sonu yok */
    if (bosalt)
        fflush(stdout);

    pid_t pid = fork();
    printf("B\n");
    if (pid == 0)
        return 0;                    /* çocuk: çıkışta boşaltır */

    wait(NULL);
    return 0;
}
