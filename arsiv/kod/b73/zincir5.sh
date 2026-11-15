#!/bin/bash
cd "C:/Users/merty/AppData/Local/Temp/b73"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
rm -f zincir5.log
for t in t04_olcum t06_on_gorev t08_clip_olcum; do
  python $t.py > $t.out.txt 2>&1
  echo "$t $?" >> zincir5.log
done
echo BITTI >> zincir5.log
