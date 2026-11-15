#!/bin/bash
# b53 nihai olcum kosusu: tum C olcumleri, ciktilar sonuc/ altina
cd "$(dirname "$0")"
mkdir -p sonuc
gcc -O2 -std=c11 -Wall -Wextra -fopenmp b53_olcek.c -o olcek
gcc -O2 -std=c11 -Wall -Wextra -fopenmp b53_bant.c -o bant
gcc -O2 -std=c11 -Wall -Wextra -fopenmp b53_histogram.c -o hist
gcc -O2 -std=c11 -Wall -Wextra b53_toplam.c -o toplam
gcc -O2 -std=c11 -Wall -Wextra -fopenmp b53_zamanlama.c -o zamanlama
gcc -O2 -std=c11 -Wall -Wextra -fopenmp b53_mergesort.c -o msort
gcc -O2 -std=c11 -Wall -Wextra -pthread -fopenmp b53_pthread.c -o pth
./olcek guclu 0.0  > sonuc/amdahl_s000.csv
./olcek guclu 0.10 > sonuc/amdahl_s010.csv
./olcek zayif 0.10 > sonuc/gustafson_s010.csv
./bant > sonuc/bant.csv
./hist 8 > sonuc/histogram_p8.txt
./toplam > sonuc/toplam.txt
./zamanlama 8 > sonuc/zamanlama_p8.txt
cp b53_gantt.csv sonuc/gantt_p8.csv
./msort 8 > sonuc/msort_p8.txt
./pth 8 > sonuc/pth_p8.txt
echo KOSU_TAMAM
cat /proc/loadavg
