#!/bin/bash
# Bolum 75 MCU hatti: konakta bit-tam test ve Cortex-M4 boyutu.
set -e
cd "$(dirname "$0")"
TB="/c/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins"
TB="$TB/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32"
TB="$TB.13.3.rel1.win32_1.0.0.202411081344/tools/bin"
BAY="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16"
BAY="$BAY -Os -ffp-contract=off -ffunction-sections -fdata-sections"
BAY="$BAY -Wall -Wextra -std=c11"
echo "== konak (WSL gcc, ASan+UBSan) =="
wsl bash -lc "cd /mnt/c/Users/merty/AppData/Local/Temp/b75/mcu && \
gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined \
mlp_int8.c test_host.c -o test_host && ./test_host"
echo "== Cortex-M4 (arm-none-eabi-gcc 13.3.1) =="
"$TB/arm-none-eabi-gcc.exe" $BAY -c mlp_int8.c -o mlp_int8.o
"$TB/arm-none-eabi-size.exe" -A mlp_int8.o
