/* fork_agac.c: döngü içinde fork; her sürecin bir printf'i var.
 * Kullanım: ./fork_agac      (tamponlu stdout)
 *           ./fork_agac -u   (stdout tamponsuz) */
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "-u") == 0)
        setvbuf(stdout, NULL, _IONBF, 0);

    for (int i = 0; i < 3; i++) {
        /* her turda süreç sayısı ikiye katlanır */
        fork();
        printf("x\n");
    }
    return 0;
}
