#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
objdump -d --no-show-raw-insn cerceve | awk '/<faktoriyel>:/,/^$/' > r20.txt
gcc -O0 -Wall -Wextra -std=c11 tabansiz.c -o tab_O0 2>&1 | grep -m1 warning > r21.txt
