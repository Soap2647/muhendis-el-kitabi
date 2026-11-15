/* harness.c -- girdi.txt ornekleri icin agac_tahmin */
#include <stdio.h>
#include <stdint.h>

uint8_t agac_tahmin(const float x[3]);

int main(void) {
    float x[3];
    while (scanf("%f %f %f", &x[0], &x[1], &x[2]) == 3) {
        printf("%u\n", (unsigned)agac_tahmin(x));
    }
    return 0;
}
