#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
./cerceve > c1.txt 2>&1; echo "cikis=$?" >> c1.txt
./derin_O0 100000 > c2.txt 2>&1; echo "cikis=$?" >> c2.txt
./derin_O0 10000 > c3.txt 2>&1; echo "cikis=$?" >> c3.txt
./kuyruk_O0 k 10000000 > c4.txt 2>&1; echo "cikis=$?" >> c4.txt
./kuyruk_O0 k 100000 > c5.txt 2>&1; echo "cikis=$?" >> c5.txt
./derin 1000000 > c6.txt 2>&1; echo "cikis=$?" >> c6.txt
for f in c1 c2 c3 c4 c5 c6; do echo "== $f"; cat $f.txt; done
