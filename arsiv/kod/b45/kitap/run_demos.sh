#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b45/kitap || exit 1
for p in crc cobs halka tel; do
  gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined \
      -o ornek_$p ornek_$p.c crc16.c cobs.c halka.c telemetri_cerceve.c || { echo "DERLEME HATASI $p"; continue; }
  echo "== $p"
  ./ornek_$p
  echo "exit=$?"
done
