#!/bin/bash
set -e
cd /mnt/c/Users/merty/AppData/Local/Temp/b42
R=/tmp/b42ov/rootfs; rm -rf $R; mkdir -p $R/bin $R/lib
cp /bin/sh $R/bin/
for lib in $(ldd /bin/sh | grep -o '/[^ ]*'); do mkdir -p $R$(dirname $lib); cp -L $lib $R$lib; done
gcc -O2 -Wall -Wextra -std=c11 -static proje/crc32_arac.c -o crc_st
cp crc_st $R/bin/crc
unshare -r -m chroot $R /bin/sh -c 'echo "konum: $PWD"; for f in /*; do echo "  $f"; done; printf "123456789" | /bin/crc'
unshare -r -m chroot $R /bin/sh -c 'if [ -d /home ]; then echo var; else echo yok; fi'
