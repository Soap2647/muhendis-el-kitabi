#!/bin/bash
OUT=/mnt/c/Users/merty/AppData/Local/Temp/b28/cikti
cd /home/merty/b28_work/fsg2 || exit 1
rm -f buyuk.bin
dd if=/dev/urandom of=buyuk.bin bs=1M count=1 status=none
filefrag -v buyuk.bin | sed 's/  */ /g' > $OUT/fs_extent1.txt 2>&1
sync
filefrag -v buyuk.bin | sed 's/  */ /g' > $OUT/fs_extent2.txt 2>&1
echo EXT_DONE
