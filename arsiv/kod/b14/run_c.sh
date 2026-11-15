#!/bin/bash
# Kullanım: run_c.sh <dosya.c> [argümanlar...]
# Derler (-O2 -Wall -Wextra -std=c11) ve çalıştırır; sonra ASan+UBSan ile de.
SRC=/mnt/c/Users/merty/AppData/Local/Temp/b14/src
BIN=/tmp/b14bin
mkdir -p "$BIN"
f="$1"; shift
base=$(basename "$f" .c)
echo "### $base: -O2 -Wall -Wextra -std=c11"
gcc -O2 -Wall -Wextra -std=c11 "$SRC/$f" -o "$BIN/$base" && "$BIN/$base" "$@"
echo "exit=$?"
echo "### $base: -fsanitize=address,undefined"
gcc -g -O1 -Wall -Wextra -std=c11 -fsanitize=address,undefined "$SRC/$f" -o "$BIN/${base}_san" && "$BIN/${base}_san" "$@"
echo "exit=$?"
