#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b42
echo "=== derleme uyarisi yok mu (sinyal)"; gcc -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L sinyal_pid1.c -o sinyal_pid1 && echo "ok"
echo "=== PID1 yok"; unshare -r -p -f --mount-proc ./sinyal_pid1 yok > p1.log 2>&1 &
sleep 1; HP=$(pgrep -n sinyal_pid1); echo "host PID: $HP"; kill -TERM $HP; sleep 2
echo "SIGTERM sonrasi: $(ps -o stat=,comm= -p $HP 2>/dev/null || echo yok)"; cat p1.log; kill -KILL $HP 2>/dev/null; sleep 1
echo "=== PID1 var"; unshare -r -p -f --mount-proc ./sinyal_pid1 var > p2.log 2>&1 &
sleep 1; HP=$(pgrep -n sinyal_pid1); kill -TERM $HP; sleep 2; cat p2.log
echo "=== boyut"; gcc -O2 -Wall -Wextra -std=c11 /mnt/c/Users/merty/AppData/Local/Temp/b42/proje/crc32_arac.c -o crc_dyn && gcc -O2 -Wall -Wextra -std=c11 -static /mnt/c/Users/merty/AppData/Local/Temp/b42/proje/crc32_arac.c -o crc_st && stat -c "%s %n" crc_dyn crc_st && ldd ./crc_dyn
printf "123456789" | ./crc_st
echo "=== simulasyonlar"
python3 katman_onbellek.py > katman_final.txt; python3 uzlastirma.py > uzlastirma_final.txt; python3 dagitim_strateji.py b42_dagitim.csv > dagitim_final.txt
cat uzlastirma_final.txt; cat dagitim_final.txt
