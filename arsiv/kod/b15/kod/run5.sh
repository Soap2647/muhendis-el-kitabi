#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O0 -Wall -Wextra -std=c11 sel.c -o sel_O0 && gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2
for n in 100 300 400 500 1000; do
  ./sel_O0 r $n > s_r0_$n.txt 2>&1; echo "cikis=$?" >> s_r0_$n.txt
  ./sel_O2 r $n > s_r2_$n.txt 2>&1; echo "cikis=$?" >> s_r2_$n.txt
  ./sel_O0 y $n > s_y0_$n.txt 2>&1; echo "cikis=$?" >> s_y0_$n.txt
done
for f in s_*.txt; do echo "== $f: $(tr '\n' ' ' < $f)"; done
