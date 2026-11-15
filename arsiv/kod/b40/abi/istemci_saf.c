/* istemci_saf.c: Boyut kontrolu YOK. Yalnizca ASan ile sinanir. */
#include <stdio.h>
#include "olcum.h"

int main(void)
{
    struct olcum o = {7, 0.0};
    olcum_guncelle(&o, 42.0);
    printf("id=%d deger=%.1f\n", o.id, o.deger);
    return 0;
}
