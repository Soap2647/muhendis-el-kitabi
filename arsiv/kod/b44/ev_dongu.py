# -*- coding: utf-8 -*-
"""EV Dashboard ana dongusunun en kotu sure analizi (main.c).

HAL_UART_Transmit (100 ms) ve HAL_UART_Receive (200 ms) zaman asimli
cagrilardir; HAL_Delay(200) dongunun sonunda gelir. Dongu periyodu
= govde suresi + 200 ms. Sabit 200 ms periyot DEGILDIR.
"""
# (cagri, zaman asimi ms): Daly x3 (T+R), Kelly (T+R), RPi (T)
CAGRILAR = [
    ("Daly 1 (T)", 100), ("Daly 1 (R)", 200),
    ("Daly 2 (T)", 100), ("Daly 2 (R)", 200),
    ("Daly 3 (T)", 100), ("Daly 3 (R)", 200),
    ("Kelly (T)", 100), ("Kelly (R)", 200),
    ("RPi (T)", 100),
]
GECIKME_MS = 200


def uart_suresi_ms(bayt, baud):
    """8N1 cerceve: bayt basina 10 bit (genel bilgi)."""
    return bayt * 10 / baud * 1000.0


if __name__ == "__main__":
    govde = sum(z for _, z in CAGRILAR)
    print("En kotu govde suresi    : %d ms" % govde)
    print("En kotu dongu periyodu  : %d ms" % (govde + GECIKME_MS))
    print("13 bayt @115200 baud    : %.3f ms"
          % uart_suresi_ms(13, 115200))
    print("13 bayt @9600 baud      : %.3f ms"
          % uart_suresi_ms(13, 9600))
    f_hclk = 168_000_000
    load = f_hclk // 1000 - 1
    print("SysTick LOAD (1 ms)     : %d" % load)
    print("LOAD siniri (2^24 - 1)  : %d" % (2 ** 24 - 1))
    print("gercek tick suresi      : %.6f ms"
          % ((load + 1) / f_hclk * 1000))
    for pr, rl in ((4, 1249), (6, 4095)):
        t = 4 * 2 ** pr * (rl + 1) / 32000
        print("IWDG PR=%d RL=%d        : %.3f s" % (pr, rl, t))
