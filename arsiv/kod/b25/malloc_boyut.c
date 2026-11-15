/* malloc_boyut.c - glibc'nin ayirdigi gercek blok boyutlari.
 * Her istek icin 2 ardisik malloc yapilir. Ikinci adresin
 * birincisinden farki, glibc'nin bu istek icin harcadigi parca
 * boyutudur (baslik dahil). Hicbir blok serbest birakilmaz; bu
 * sayede bloklar ust parcadan (top chunk) sirayla gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 malloc_boyut.c -o mb
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <malloc.h>

int main(void)
{
    size_t istekler[] = { 1, 8, 16, 17, 24, 25, 40, 64, 100, 1000 };
    size_t n = sizeof istekler / sizeof istekler[0];

    printf("istek  kullanilabilir  parca(zincir)\n");
    for (size_t i = 0; i < n; i++) {
        char *a = malloc(istekler[i]);
        char *b = malloc(istekler[i]);
        if (!a || !b) { perror("malloc"); return 1; }
        size_t kull = malloc_usable_size(a);
        size_t parca = (uintptr_t)b - (uintptr_t)a;
        printf("%5zu %12zu %14zu\n", istekler[i], kull, parca);
    }
    return 0;
}
