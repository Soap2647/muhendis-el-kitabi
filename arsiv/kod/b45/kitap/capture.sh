#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b45/kitap || exit 1
for p in crc cobs halka tel; do
  ./ornek_$p > out/ornek_$p.txt
done
