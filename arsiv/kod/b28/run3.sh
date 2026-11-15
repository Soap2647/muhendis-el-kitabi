#!/bin/bash
set -u
W=/home/merty/b28_work
SRC=/mnt/c/Users/merty/AppData/Local/Temp/b28
OUT=$SRC/cikti
mkdir -p $OUT $W && cd $W && rm -f b28_*.c && cp $SRC/b28_*.c . || exit 1
PROGS="b28_1_temel b28_2_kisa_io b28_3_stdio_fork b28_4_ofset b28_5_atomik b28_6_fsync_olcum b28_7_tampon_olcum b28_8_mmap_olcum b28_9_epoll b28_10_unlink b28_11_append"
for f in $PROGS; do
  gcc -O2 -Wall -Wextra -std=c11 -D_DEFAULT_SOURCE -o $f $f.c 2>$f.warn || echo "FAIL $f"
  [ -s $f.warn ] && { echo "UYARI $f:"; cat $f.warn; }
done
./b28_1_temel > $OUT/t1.txt
./b28_2_kisa_io > $OUT/t2.txt
./b28_3_stdio_fork | cat > $OUT/t3_varsayilan.txt
./b28_3_stdio_fork flush | cat > $OUT/t3_flush.txt
./b28_3_stdio_fork satir | cat > $OUT/t3_satir.txt
./b28_4_ofset > $OUT/t4.txt
./b28_5_atomik yerinde > $OUT/t5_yerinde.txt
./b28_5_atomik atomik > $OUT/t5_atomik.txt
./b28_9_epoll tetik > $OUT/t9_tetik.txt
./b28_9_epoll olay > $OUT/t9_olay.txt
./b28_10_unlink > $OUT/t10.txt
./b28_11_append ekle > $OUT/t11_ekle.txt
./b28_11_append konum > $OUT/t11_konum.txt
./b28_11_append ekle >> $OUT/t11_ekle.txt
./b28_6_fsync_olcum > b28_fsync_ham.csv
dd if=/dev/urandom of=veri.bin bs=1M count=8 status=none 2>/dev/null
./b28_8_mmap_olcum veri.bin > b28_mmap.csv 2> $OUT/t8_sag.txt
./b28_7_tampon_olcum veri.bin > b28_tampon.csv 2> $OUT/t7_sag.txt
echo "n,poll_ns,epoll_ns" > b28_epoll.csv
for n in 10 100 1000 5000 10000; do ./b28_9_epoll olcek $n >> b28_epoll.csv; done
cp -f b28_fsync_ham.csv b28_mmap.csv b28_tampon.csv b28_epoll.csv $SRC/ 2>/dev/null
mkdir -p "/mnt/d/Mevcut Projeler/Kitap/engine/veri" 2>/dev/null
cp -f b28_fsync_ham.csv b28_mmap.csv b28_tampon.csv b28_epoll.csv "/mnt/d/Mevcut Projeler/Kitap/engine/veri/" 2>/dev/null
# sanitizer kontrolu
gcc -O1 -g -fsanitize=address,undefined -std=c11 -D_DEFAULT_SOURCE -o s2 b28_2_kisa_io.c && ./s2 > /dev/null && echo "ASAN t2 OK"
gcc -O1 -g -fsanitize=address,undefined -std=c11 -D_DEFAULT_SOURCE -o s5 b28_5_atomik.c && ./s5 yerinde >/dev/null 2>$OUT/san5.txt; echo "ASAN t5 rc=$?"
gcc -O1 -g -fsanitize=address,undefined -std=c11 -D_DEFAULT_SOURCE -o s11 b28_11_append.c && ./s11 ekle > $OUT/san11.txt 2>&1; echo "ASAN t11 rc=$?"
gcc -O1 -g -fsanitize=address,undefined -std=c11 -D_DEFAULT_SOURCE -o s9 b28_9_epoll.c && ./s9 olay > /dev/null 2>$OUT/san9.txt; echo "ASAN t9 rc=$?"
echo "tum ciktilar: $OUT"
ls -la $OUT
