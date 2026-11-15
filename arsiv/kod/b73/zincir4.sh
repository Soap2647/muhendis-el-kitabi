#!/bin/bash
cd "C:/Users/merty/AppData/Local/Temp/b73"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
rm -f zincir4.log
for t in t03_coll t04_olcum t05_ablasyon t06_on_gorev t07_clip_egit t08_clip_olcum t09_saglamlik t10_kisa_yol; do
  python $t.py > $t.out.txt 2>&1
  echo "$t $?" >> zincir4.log
done
echo BITTI >> zincir4.log
