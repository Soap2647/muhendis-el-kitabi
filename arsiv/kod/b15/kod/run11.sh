#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
( timeout 2 ./tab_O2 5 ) > r11.txt 2>/dev/null; echo "O2 cikis=$?" >> r11.txt
( timeout 2 ./tab_O0 5 ) > r12.txt 2>/dev/null; echo "O0 cikis=$?" >> r12.txt
( ./tab_O0 5 ) > r13.txt 2>/dev/null; echo "O0 direkt cikis=$?" >> r13.txt
