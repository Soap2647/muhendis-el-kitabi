/* b32_c4_duzeltilmis.c: boyut hesabi tasma denetimli yapilir.
 * __builtin_mul_overflow tasma olursa 1 dondurur (GCC ve Clang).
 * Derleme: gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra \
 *          -std=c11 b32_c4_duzeltilmis.c -o b32_c4_duzeltilmis
 */
#include <stdio.h>
#include <stdlib.h>

static int *dizi_olustur(size_t n)
{
    size_t bayt;
    if (__builtin_mul_overflow(n, sizeof(int), &bayt))
        return NULL;                     /* hesap tasti: reddet */
    int *d = malloc(bayt);
    if (d == NULL)
        return NULL;
    for (size_t i = 0; i < n; i++)
        d[i] = (int)i;
    return d;
}

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    char *son;
    unsigned long v = strtoul(argv[1], &son, 10);
    if (*son != '\0' || v == 0)
        return 2;
    int *d = dizi_olustur((size_t)v);
    if (d == NULL) {
        fprintf(stderr, "boyut kabul edilemez\n");
        return 1;
    }
    printf("d[0]=%d\n", d[0]);
    free(d);
    return 0;
}
