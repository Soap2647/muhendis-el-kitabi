#!/bin/bash
# Cortex-M4 derleme, boyut ve komut sayimi.
PLG="/c/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins"
PKG="com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32"
PKG="$PKG.13.3.rel1.win32_1.0.0.202411081344"
TB="$PLG/$PKG/tools/bin"
CC="$TB/arm-none-eabi-gcc.exe"
SZ="$TB/arm-none-eabi-size.exe"
OD="$TB/arm-none-eabi-objdump.exe"
BAYRAK="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard"
BAYRAK="$BAYRAK -mfpu=fpv4-sp-d16 -Os"
BAYRAK="$BAYRAK -ffp-contract=off -fno-math-errno"
BAYRAK="$BAYRAK -ffunction-sections -fdata-sections"
BAYRAK="$BAYRAK -Wall -Wextra -std=c11"
cd "$(dirname "$0")"
for v in 0 1; do
  echo "=== TM_KULLAN_DSP=$v ==="
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -S -o tinyml_dsp$v.s tinyml.c
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -c -o tinyml_dsp$v.o tinyml.c
  echo "-- tinyml.o:"
  "$SZ" tinyml_dsp$v.o
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -nostartfiles -nostdlib \
     -T ld_m4.ld -Wl,--gc-sections -o fw_dsp$v.elf \
     startup.c mcu_main.c tinyml.c -lm -lgcc
  echo "-- firmware (fw_dsp$v.elf):"
  "$SZ" fw_dsp$v.elf
  "$OD" -d tinyml_dsp$v.o > dis_dsp$v.txt
  echo "-- komut sayimi (tinyml.o, disassembly):"
  for m in smlad smlabb mla ldrsb ldr; do
    n=$(grep -cE "\s$m(\.[wn])?\s" dis_dsp$v.txt)
    printf "  %-8s %s\n" "$m" "$n"
  done
done
