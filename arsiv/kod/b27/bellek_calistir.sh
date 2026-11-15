#!/bin/bash
# Bellek siralamasi deneyleri: derle ve calistir
C=/mnt/c/Users/merty/AppData/Local/Temp/b27/code
B=/mnt/c/Users/merty/AppData/Local/Temp/b27/bin
cd $B
gcc -O2 -Wall -Wextra -std=c11 -pthread -DMO_S=memory_order_seq_cst -DMO_L=memory_order_seq_cst $C/b27_bellek.c -o bel_sc || exit 1
gcc -O2 -Wall -Wextra -std=c11 -pthread -DMO_S=memory_order_relaxed -DMO_L=memory_order_relaxed $C/b27_bellek.c -o bel_rlx || exit 1
gcc -O2 -Wall -Wextra -std=c11 -pthread -DMO_S=memory_order_release -DMO_L=memory_order_acquire $C/b27_bellek.c -o bel_ra || exit 1
for k in 1 2 3; do echo "== sb relaxed deneme $k"; ./bel_rlx sb 1000000; done
echo "== sb seq_cst"; ./bel_sc sb 1000000
echo "== mp relaxed"; ./bel_rlx mp 1000000
echo "== mp release/acquire"; ./bel_ra mp 1000000
echo "== peterson relaxed"; ./bel_rlx peterson 2000000
echo "== peterson seq_cst"; ./bel_sc peterson 2000000
