#!/bin/bash
set -u
OUT=/mnt/c/Users/merty/AppData/Local/Temp/b28/cikti
W=/home/merty/b28_work/fsg2
rm -rf $W && mkdir -p $W && cd $W || exit 1
{ df -i . | tail -1; stat -f -c 'blok=%S toplam=%b bos=%f' .; } > $OUT/fs_df.txt 2>&1
{ printf 'merhaba dunya\n' > a.txt; stat a.txt; } > $OUT/fs_stat.txt 2>&1
{ mkdir dizin && touch dizin/x dizin/y && ls -i dizin; } > $OUT/fs_dizin.txt 2>&1
{ ln a.txt b.txt; ln -s a.txt s.txt; ls -li a.txt b.txt s.txt; } > $OUT/fs_baglar.txt 2>&1
{ rm a.txt; cat b.txt; stat -c '%h' b.txt; rm b.txt; cat s.txt; } > $OUT/fs_baglar2.txt 2>&1
{ dd if=/dev/urandom of=buyuk.bin bs=1M count=1 status=none; filefrag -v buyuk.bin; } > $OUT/fs_extent1.txt 2>&1
{ sync; filefrag -v buyuk.bin; } > $OUT/fs_extent2.txt 2>&1
{ grep ' / ' /proc/mounts; } > $OUT/fs_baglama.txt 2>&1
{ ls -l /dev/null /dev/sdd /dev/tty; } > $OUT/fs_dev.txt 2>&1
cd $OUT && cat t5_yerinde.txt t5_atomik.txt > t5_birlikte.txt
echo FS_DONE
