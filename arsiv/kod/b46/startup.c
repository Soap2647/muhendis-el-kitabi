/* startup.c - minimum Cortex-M baslangic kodu (kitap icin). */
#include <stdint.h>

extern int main(void);
extern uint32_t __stack_top;

void _start(void)
{
    main();
    for (;;) { }
}

__attribute__((section(".isr_vector"), used))
const void *const vektor[2] = {
    (void *)&__stack_top,
    (void *)_start,
};
