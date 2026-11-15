#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O2 -Wall -Wextra -std=c11 tabansiz.c -o tab_O2 2>/dev/null
timeout 3 ./tab_O2 5; echo "cikis=$?"
gcc -O2 -std=c11 tabansiz.c -o tab_O2b 2>/dev/null
timeout 3 ./tab_O2b 5; echo "cikis=$?"
objdump -d --no-show-raw-insn tab_O2 | awk '/<faktoriyel>:/,/^$/' | head -30
