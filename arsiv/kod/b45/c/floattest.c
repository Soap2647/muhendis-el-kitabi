#include <stdio.h>
#include <stdint.h>
int main(void) {
    char b[32];
    float v = 52.3f;
    snprintf(b, sizeof b, "%.1f", (double)v);
    return b[0];
}
