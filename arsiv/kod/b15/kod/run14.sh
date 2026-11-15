#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
objdump -d --no-show-raw-insn derin_O0 | awk '/<derin>:/,/^$/' | head -8 > r33.txt
