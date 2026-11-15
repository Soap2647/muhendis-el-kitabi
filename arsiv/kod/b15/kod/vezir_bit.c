#include <stdint.h>
#include <stdio.h>

static long cozum = 0;
static long dugum = 0;

/* cols: dolu sutunlar; ld: sol capraz; rd: sag capraz.
   Her bit bir sutun (ya da capraz) konumunu temsil eder. */
static void dene(uint32_t tum, uint32_t cols,
                 uint32_t ld, uint32_t rd) {
    dugum++;
    if (cols == tum) {
        cozum++;
        return;
    }
    uint32_t bos = tum & ~(cols | ld | rd);
    while (bos != 0) {
        uint32_t bit = bos & (0u - bos);   /* en dusuk 1 biti */
        bos ^= bit;
        dene(tum, cols | bit,
             ((ld | bit) << 1) & tum,
             (rd | bit) >> 1);
    }
}

int main(void) {
    printf("N  cozum  dugum\n");
    for (uint32_t n = 1; n <= 10; n++) {
        cozum = 0;
        dugum = 0;
        dene((1u << n) - 1u, 0, 0, 0);
        printf("%2u %6ld %6ld\n", n, cozum, dugum);
    }
    return 0;
}
