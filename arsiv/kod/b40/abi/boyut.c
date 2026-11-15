#include <stdio.h>
#include <stddef.h>
#include "olcum.h"
int main(void) {
    printf("sizeof=%zu id@%zu deger@%zu\n", sizeof(struct olcum),
           offsetof(struct olcum, id), offsetof(struct olcum, deger));
#ifdef OLCUM_V2
    printf("durum@%zu\n", offsetof(struct olcum, durum));
#endif
    return 0;
}
