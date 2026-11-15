/* b32_c4_hatali.c: tamsayi tasmasi, yanlis malloc boyutu.
 * int n*4 hesabi tasar; malloc kucuk bir blok verir; dongu
 * ayrilan bellegin disina yazar.
 * Derleme: gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra \
 *          -std=c11 b32_c4_hatali.c -o b32_c4_hatali
 */
#include <stdio.h>
#include <stdlib.h>

static int *dizi_olustur(int n)
{
    int bayt = n * (int)sizeof(int);     /* int tasmasi (UB) */
    int *d = malloc((size_t)bayt);
    if (d == NULL)
        return NULL;
    for (int i = 0; i < n; i++)
        d[i] = i;                        /* ayrilan alanin disina */
    return d;
}

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    int n = atoi(argv[1]);
    int *d = dizi_olustur(n);
    if (d == NULL)
        return 1;
    printf("d[0]=%d\n", d[0]);
    free(d);
    return 0;
}
