#include <stdio.h>
#include <stdint.h>

/* a*b mod m: 64 bitlik çarpım taşarsa sonuç yanlış olur. */
static uint64_t carp_kaba(uint64_t a, uint64_t b, uint64_t m)
{
    return (a * b) % m;
}

/* 128 bitlik ara sonuçla doğru çarpım (GCC/Clang uzantısı). */
static uint64_t carp_dogru(uint64_t a, uint64_t b, uint64_t m)
{
    return (uint64_t)(((unsigned __int128)a * b) % m);
}

int main(void)
{
    uint64_t m = 1000000000039ULL;   /* yaklaşık 10^12 */
    uint64_t a = 999999999989ULL;

    printf("kaba  : %llu\n", (unsigned long long)carp_kaba(a, a, m));
    printf("dogru : %llu\n", (unsigned long long)carp_dogru(a, a, m));
    printf("sizeof(long) = %zu\n", sizeof(long));
    return 0;
}
