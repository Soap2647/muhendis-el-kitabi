#include <stdio.h>
typedef struct { long pay; long payda; } Kesir;
int main(void) {
    Kesir k = {1, 0};   /* payda sifir: invariant kirildi */
    printf("%ld/%ld\n", k.pay, k.payda);
    return 0;
}
