# -*- coding: utf-8 -*-
"""Bolum 43 - 'Bare-Metal C' diyagramlari.

Olcum sekli (boyut) engine/veri/b43_boyut.csv dosyasini okur.
Diger sekiller bolumdeki kesin degerlerden cizilir (bellek haritasi,
vektor tablosu, bit-band formulu, yazmac adresleri).
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = "DejaVu Sans Mono"
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b43_%s.png" % ad)


def _tuval(w, h, xl=14, yl=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _metin(ax, x, y, s, fs=9.5, renk=INK, mono=False, ha="left"):
    kw = dict(fontsize=fs, color=renk, ha=ha, va="center")
    if mono:
        kw["family"] = MONO
    ax.text(x, y, s, **kw)


# 1. Mikrodenetleyici blok diyagrami --------------------------------- #
def mcu_blok():
    fig, ax = _tuval(9.6, 5.4)
    _box(ax, 0.3, 5.6, 3.0, 1.9, "Cortex-M4\nçekirdeği\n(yazmaçlar, ALU)",
         FILL[0], EDGE[0], fs=9.5)
    _box(ax, 4.3, 5.9, 4.6, 1.1, "Bus matrisi (AHB)", FILL[2], EDGE[2],
         fs=9.5)
    _box(ax, 10.6, 5.6, 3.1, 1.9, "Flash\nkod ve sabitler",
         FILL[1], EDGE[1], fs=9.5)
    _box(ax, 10.6, 3.2, 3.1, 1.9, "SRAM\nveri ve yığın", FILL[1],
         EDGE[1], fs=9.5)
    _box(ax, 4.3, 3.2, 4.6, 1.9, "Çevre birimleri\nGPIO, USART, "
         "timer, ADC", FILL[0], EDGE[0], fs=9.5)
    _box(ax, 0.3, 3.2, 3.0, 1.9, "Hata ayıklama\nSWD / JTAG", FILL[3],
         EDGE[3], fs=9.5)
    _box(ax, 4.3, 0.6, 4.6, 1.6, "DMA\n(CPU'suz bellek aktarımı)",
         FILL[4], EDGE[4], fs=9.5)
    _box(ax, 0.3, 0.6, 3.0, 1.6, "Saat ağacı (RCC)\nkapılı saat",
         FILL[2], EDGE[2], fs=9.5)
    _arrow(ax, 3.3, 6.55, 4.3, 6.45)
    _arrow(ax, 8.9, 6.45, 10.6, 6.45)
    _arrow(ax, 8.9, 6.2, 10.6, 4.4)
    _arrow(ax, 6.6, 5.9, 6.6, 5.1)
    _arrow(ax, 1.8, 3.2, 1.8, 5.6, col=MUTED, style="<|-|>", lw=1.1)
    _arrow(ax, 3.3, 1.4, 4.3, 3.6, col=MUTED, style="-|>", lw=1.1)
    _arrow(ax, 1.8, 2.2, 1.8, 3.2, col=MUTED, style="-|>", lw=1.1)
    _metin(ax, 0.3, 0.25, "Saat ağacı çevre birimlerini besler; "
           "kullanılmayan birimin saati kapatılabilir.", fs=8.6,
           renk=MUTED)
    return _save(fig, _yol("mcu_blok"))


# 2. Cortex-M bellek haritasi ----------------------------------------- #
def bellek_haritasi():
    fig, ax = _tuval(9.6, 6.0, xl=14, yl=10)
    bolgeler = [
        ("0xE0000000 - 0xFFFFFFFF", "Sistem (PPB): NVIC, SysTick, SCB",
         FILL[4], EDGE[4]),
        ("0xA0000000 - 0xDFFFFFFF", "Harici aygıtlar", FILL[3], EDGE[3]),
        ("0x60000000 - 0x9FFFFFFF", "Harici RAM", FILL[3], EDGE[3]),
        ("0x42000000 - 0x43FFFFFF", "Çevre birimi bit-band takma adresi",
         FILL[2], EDGE[2]),
        ("0x40000000 - 0x5FFFFFFF", "Çevre birimleri (APB1, APB2, AHB)",
         FILL[0], EDGE[0]),
        ("0x22000000 - 0x23FFFFFF", "SRAM bit-band takma adresi",
         FILL[2], EDGE[2]),
        ("0x20000000 - 0x3FFFFFFF", "SRAM (veri, yığın)", FILL[1],
         EDGE[1]),
        ("0x00000000 - 0x1FFFFFFF", "Kod (flash, 0x08000000'da)",
         FILL[1], EDGE[1]),
    ]
    y = 9.1
    for adr, ad, f, e in bolgeler:
        _metin(ax, 0.2, y, adr, fs=8.6, renk=MUTED, mono=True)
        _box(ax, 4.6, y - 0.42, 9.0, 0.84, ad, f, e, fs=9.4)
        y -= 1.05
    _metin(ax, 0.2, 0.35, "ARMv7-M genel bellek haritası. Flash ve SRAM "
           "boyutları üreticiye göre değişir (ör. RM0090).", fs=8.4,
           renk=MUTED)
    return _save(fig, _yol("bellek_haritasi"))


# 3. volatile: derleyicinin dongu uzerindeki karari ------------------- #
def volatile_yolu():
    fig, ax = _tuval(9.6, 5.8)
    _box(ax, 2.6, 6.6, 8.8, 0.9, "C:  while (DURUM_REG == 0u) { }",
         FILL[4], EDGE[4], fs=9.5)
    _metin(ax, 4.7, 5.85, "DURUM_REG: çevre birimi yazmacı", fs=8.5,
           renk=MUTED)
    _arrow(ax, 4.0, 6.6, 3.1, 5.4)
    _arrow(ax, 10.0, 6.6, 10.9, 5.4)
    _box(ax, 0.3, 4.2, 5.6, 0.9, "volatile YOK: okuma bir kez yapılır",
         FILL[3], EDGE[3], fs=9)
    _box(ax, 8.1, 4.2, 5.6, 0.9, "volatile VAR: her yineleme bellekten",
         FILL[1], EDGE[1], fs=9)
    _metin(ax, 0.4, 3.85, "-O2 ile üretilen kod (gerçek çıktı):", fs=8.5,
           renk=MUTED)
    _metin(ax, 8.2, 3.85, "-O2 ile üretilen kod (gerçek çıktı):", fs=8.5,
           renk=MUTED)
    _box(ax, 0.3, 0.9, 5.6, 2.6, "ldr  r3, [r2, #16]\n"
         "cbnz r3, son\n\nb    .        (sonsuz döngü)",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 8.1, 0.9, 5.6, 2.6, "ldr  r3, [r2, #16]\n"
         "cmp  r3, #0\nbeq  döngü\n\nbx   lr", FILL[1], EDGE[1],
         fs=9)
    ax.text(7.0, 0.35, "Aynı C kaynağı, iki farklı makine kodu.",
            fontsize=8.6, ha="center", color=MUTED)
    return _save(fig, _yol("volatile_yolu"))


# 4. Bit-band eslemesi ------------------------------------------------- #
def bit_band():
    fig, ax = _tuval(9.6, 5.9, xl=14, yl=9)
    _metin(ax, 0.3, 8.4, "Çevre birimi yazmacı (ör. GPIOD ODR, 0x40020C14)",
           fs=9.2)
    for i in range(32):
        bit = 31 - i
        x = 0.3 + i * 0.27
        renk = FILL[2] if bit == 12 else FILL[0]
        kenar = ACCENT if bit == 12 else RULE
        ax.add_patch(plt.Rectangle((x, 7.0), 0.25, 0.9, facecolor=renk,
                                   edgecolor=kenar, lw=0.9))
        if bit % 4 == 0:
            ax.text(x + 0.125, 6.7, str(bit), ha="center", fontsize=7,
                    color=MUTED)
    _metin(ax, 0.3, 6.2, "bit 12 (vurgulu): kendi alias adresi var",
           fs=8.6, renk=MUTED)
    _box(ax, 0.3, 4.9, 9.0, 1.0,
         "alias = 0x42000000 + (adres − 0x40000000) × 32 + bit × 4",
         FILL[4], EDGE[4], fs=9.2)
    ornekler = [
        ("bit 0", "0x42418280"),
        ("bit 12", "0x424182B0"),
        ("bit 31", "0x424182FC"),
    ]
    y = 3.7
    for ad, adr in ornekler:
        _box(ax, 0.3, y - 0.38, 2.3, 0.76, ad, FILL[1], EDGE[1], fs=9.2)
        _box(ax, 3.1, y - 0.38, 3.2, 0.76, adr, FILL[0], EDGE[0], fs=9.2)
        y -= 0.95
    _metin(ax, 6.7, 3.7, "Alias'a yazılan tek bit değişir;", fs=8.8,
           renk=MUTED)
    _metin(ax, 6.7, 3.3, "okuma-değiştirme-yazma gerekmez", fs=8.8,
           renk=MUTED)
    _metin(ax, 6.7, 2.9, "(genel bilgi: Cortex-M3/M4'te var,", fs=8.8,
           renk=MUTED)
    _metin(ax, 6.7, 2.5, "ARMv8-M'de yok).", fs=8.8, renk=MUTED)
    return _save(fig, _yol("bit_band"))


# 5. Reset akisi ----------------------------------------------------- #
def reset_akisi():
    fig, ax = _tuval(9.6, 6.6, xl=14, yl=10)
    adimlar = [
        ("Güç açılır veya reset", FILL[4], EDGE[4]),
        ("Donanım: SP ← vektör[0], PC ← vektör[1]", FILL[0], EDGE[0]),
        ("Reset_Handler: .data'yı flash'tan RAM'e kopyala", FILL[1],
         EDGE[1]),
        ("Reset_Handler: .bss'yi sıfırla", FILL[1], EDGE[1]),
        ("CPACR: FPU'yu aç", FILL[2], EDGE[2]),
        ("main()  (uygulama)", FILL[3], EDGE[3]),
    ]
    y = 8.6
    for i, (metin, f, e) in enumerate(adimlar):
        _box(ax, 0.4, y - 0.5, 6.4, 0.9, metin, f, e, fs=9.2)
        if i < len(adimlar) - 1:
            _arrow(ax, 3.6, y - 0.5, 3.6, y - 1.0, lw=1.3)
        y -= 1.4
    _metin(ax, 7.3, 8.6, "Donanım bu iki değeri vektör tablosunun", fs=9)
    _metin(ax, 7.3, 8.2, "ilk iki kelimesinden okur (Şekil 43.5).", fs=9)
    _metin(ax, 7.3, 6.6, "Kopyalama döngüsü, bağlayıcı betiğinin", fs=9)
    _metin(ax, 7.3, 6.2, "_sidata, _sdata, _edata sembollerini kullanır.",
           fs=9)
    _metin(ax, 7.3, 4.6, "main hiçbir zaman dönmez: sonunda", fs=9)
    _metin(ax, 7.3, 4.2, "sonsuz döngü vardır.", fs=9)
    return _save(fig, _yol("reset_akisi"))


# 6. Flash ve RAM yerlesimi (LMA / VMA) ------------------------------ #
def lma_vma():
    fig, ax = _tuval(9.6, 6.2, xl=14, yl=10)
    _metin(ax, 0.4, 9.5, "Flash (0x08000000)", fs=10)
    _metin(ax, 8.6, 9.5, "RAM (0x20000000)", fs=10)
    flash = [
        ("isr_vector (0x08000000)", FILL[4], EDGE[4], 1.1),
        ("text (kod)", FILL[0], EDGE[0], 1.5),
        ("rodata (sabitler)", FILL[0], EDGE[0], 1.0),
        ("data LMA (kaynak kopya)", FILL[2], EDGE[2], 1.1),
    ]
    y = 8.8
    for metin, f, e, h in flash:
        _box(ax, 0.4, y - h, 5.0, h - 0.12, metin, f, e, fs=9)
        y -= h
    ram = [
        ("data VMA (0x20000000)", FILL[2], EDGE[2], 1.1),
        ("bss (sıfırlanmış)", FILL[1], EDGE[1], 1.1),
    ]
    y = 8.8
    for metin, f, e, h in ram:
        _box(ax, 8.6, y - h, 5.0, h - 0.12, metin, f, e, fs=9)
        y -= h
    _box(ax, 8.6, 2.6, 5.0, 2.0, "boş alan", "#ffffff", RULE, fs=9)
    _box(ax, 8.6, 0.6, 5.0, 1.4, "yığın (aşağı büyür)\n"
         "_estack = 0x20020000", FILL[3], EDGE[3], fs=9)
    _arrow(ax, 5.4, 6.9, 8.6, 7.4, col=ACCENT, lw=1.8)
    _metin(ax, 5.8, 7.9, "Reset_Handler", fs=8.6, renk=ACCENT)
    _metin(ax, 5.8, 7.5, "kopyalar", fs=8.6, renk=ACCENT)
    ax.text(7.0, 0.2, "LMA: flash'taki adres.  VMA: çalışırken kullanılan "
            "adres.", fontsize=8.6, ha="center", color=MUTED)
    return _save(fig, _yol("lma_vma"))


# 7. Baglayici bolumleri ---------------------------------------------- #
def baglayici():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=8)
    _box(ax, 0.3, 5.5, 3.6, 1.3, "startup.o\n.isr_vector, .text",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 0.3, 3.7, 3.6, 1.3, "blink.o\n.text, .rodata, .data, .bss",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 5.0, 3.6, 3.4, 2.4, "link.ld\nMEMORY, SECTIONS\n"
         "_sidata, _sdata, _edata", FILL[2], EDGE[2], fs=8.8)
    _arrow(ax, 3.9, 6.1, 5.0, 5.2)
    _arrow(ax, 3.9, 4.3, 5.0, 4.6)
    _box(ax, 9.2, 5.5, 4.5, 1.3, "FLASH (1 MB)\n.isr_vector  .text  .rodata"
         "\n.data (LMA)", FILL[1], EDGE[1], fs=8.6)
    _box(ax, 9.2, 3.7, 4.5, 1.3, "RAM (128 KB)\n.data (VMA)  .bss\n"
         "yığın: _estack", FILL[3], EDGE[3], fs=8.6)
    _arrow(ax, 8.4, 4.8, 9.2, 6.1, col=MUTED, lw=1.1)
    _arrow(ax, 8.4, 4.6, 9.2, 4.3, col=MUTED, lw=1.1)
    _metin(ax, 0.3, 2.6, "Her girdi bölümü, betiğin kuralına göre bir çıktı "
           "bölümüne ve bir", fs=8.6, renk=MUTED)
    _metin(ax, 0.3, 2.2, "bellek bölgesine yerleşir. .data iki adres taşır: "
           "LMA ve VMA.", fs=8.6, renk=MUTED)
    return _save(fig, _yol("baglayici"))


# 8. Vektor tablosu --------------------------------------------------- #
def vektor():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=9)
    satirlar = [
        ("0", "0x20020000", "Başlangıç MSP (yığın tepesi)", FILL[4], EDGE[4]),
        ("1", "0x08000045", "Reset_Handler (bit 0 = 1: Thumb)", FILL[0],
         EDGE[0]),
        ("2", "0x08000041", "NMI", FILL[1], EDGE[1]),
        ("3", "0x08000041", "HardFault", FILL[3], EDGE[3]),
        ("11", "0x08000041", "SVCall", FILL[1], EDGE[1]),
        ("14", "0x08000041", "PendSV", FILL[1], EDGE[1]),
        ("15", "0x08000041", "SysTick", FILL[1], EDGE[1]),
        ("16+", "IRQ girişleri", "MCU'ya özgü kesmeler (Bölüm 44)",
         FILL[2], EDGE[2]),
    ]
    _metin(ax, 0.4, 8.5, "indeks", fs=9, renk=MUTED)
    _metin(ax, 2.2, 8.5, "değer", fs=9, renk=MUTED)
    _metin(ax, 5.2, 8.5, "anlamı", fs=9, renk=MUTED)
    y = 7.9
    for idx, deger, anlam, f, e in satirlar:
        _box(ax, 0.4, y - 0.42, 1.4, 0.8, idx, f, e, fs=9.2)
        _box(ax, 2.0, y - 0.42, 2.8, 0.8, deger, f, e, fs=9.2)
        _box(ax, 5.0, y - 0.42, 8.6, 0.8, anlam, f, e, fs=9.2)
        y -= 0.95
    _metin(ax, 0.4, 0.3, "Değerler startup.c'nin derlenmiş ikilisinden "
           "(objdump -s) alındı.", fs=8.4, renk=MUTED)
    return _save(fig, _yol("vektor"))


# 9. Boyut olcumu (CSV) ---------------------------------------------- #
def boyut():
    with open(os.path.join(VERI, "b43_boyut.csv"), encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    adlar = [s["ad"] for s in satirlar]
    flash = [int(s["text"]) + int(s["data"]) for s in satirlar]
    ram = [int(s["data"]) + int(s["bss"]) for s in satirlar]
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    y = list(range(len(adlar)))[::-1]
    h = 0.36
    ax.barh([v + h / 2 for v in y], flash, height=h, color=EDGE[0],
            label="flash (text + data)")
    ax.barh([v - h / 2 for v in y], ram, height=h, color=EDGE[2],
            label="RAM (data + bss)")
    for yy, fl, rm in zip(y, flash, ram):
        ax.text(fl + 60, yy + h / 2, "%d" % fl, va="center", fontsize=8.5,
                color=INK)
        ax.text(rm + 60, yy - h / 2, "%d" % rm, va="center", fontsize=8.5,
                color=MUTED)
    ax.set_yticks(y)
    ax.set_yticklabels(adlar, fontsize=9)
    ax.set_xlabel("bayt", fontsize=9)
    ax.set_xlim(0, max(flash) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="lower right", fontsize=8.5, frameon=False)
    ax.set_title("Derleme seçeneği ve printf'in bellek maliyeti "
                 "(arm-none-eabi-size)", fontsize=10, loc="left", color=INK)
    fig.tight_layout()
    return _save(fig, _yol("boyut"))


# 10. HAL -> yazmac katmanlari -------------------------------------- #
def katmanlar():
    fig, ax = _tuval(9.6, 6.2, xl=14, yl=10)
    _metin(ax, 0.3, 9.5, "Okuma: HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0)",
           fs=9.2)
    _metin(ax, 7.3, 9.5, "Yazma: HAL_UART_Transmit(&huart1, ...)",
           fs=9.2)
    sol = [
        ("main.c (uygulama kodu)", FILL[4], EDGE[4]),
        ("HAL: (GPIOx->IDR & pin) != 0", FILL[0], EDGE[0]),
        ("Yazmaç: GPIOB->IDR (0x40020410)", FILL[2], EDGE[2]),
        ("Donanım: pin seviyesi", FILL[1], EDGE[1]),
    ]
    sag = [
        ("main.c (uygulama kodu)", FILL[4], EDGE[4]),
        ("HAL: her bayt için TXE bekle,\nDR'ye yaz, TC bekle", FILL[0],
         EDGE[0]),
        ("Yazmaç: USART->SR ve USART->DR", FILL[2], EDGE[2]),
        ("Donanım: seri hat çıkışı", FILL[1], EDGE[1]),
    ]
    for kolon, x in ((sol, 0.3), (sag, 7.3)):
        y = 8.6
        for i, (metin, f, e) in enumerate(kolon):
            _box(ax, x, y - 0.55, 6.3, 1.1, metin, f, e, fs=9)
            if i < len(kolon) - 1:
                _arrow(ax, x + 3.15, y - 0.55, x + 3.15, y - 1.25,
                       lw=1.3)
            y -= 1.9
    ax.text(7.0, 0.3, "Kaynak: STM32F4 HAL v1.8.0 (stm32f4xx_hal_gpio.c, "
            "stm32f4xx_hal_uart.c)", fontsize=8.4, ha="center",
            color=MUTED)
    return _save(fig, _yol("katmanlar"))


if __name__ == "__main__":
    yollar = [mcu_blok(), bellek_haritasi(), volatile_yolu(), bit_band(),
              reset_akisi(), lma_vma(), baglayici(), vektor(), boyut(),
              katmanlar()]
    for y in yollar:
        print("yazildi:", os.path.normpath(y))
