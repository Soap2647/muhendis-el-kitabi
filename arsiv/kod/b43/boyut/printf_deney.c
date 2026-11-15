/* printf_deney.c - printf'in boyut maliyetini olcmek icin */
#include <stdio.h>
#include <stdint.h>

volatile uint32_t sonuc;

int main(void)
{
    printf("menzil=%u km\n", (unsigned)sonuc);
    return 0;
}
