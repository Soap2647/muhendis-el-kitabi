#!/bin/bash
D=/mnt/c/Users/merty/AppData/Local/Temp/b42; cd $D
gcc -O2 -Wall -Wextra -std=c11 crc32_arac.c -o crc32_dinamik || exit 1
gcc -O2 -Wall -Wextra -std=c11 -static crc32_arac.c -o crc32_statik || exit 1
echo "== bağımlılıklar (dinamik) =="; ldd ./crc32_dinamik
echo "== boyutlar (bayt) =="; stat -c "%s %n" crc32_dinamik crc32_statik
printf "merhaba dunya" | ./crc32_dinamik
printf "merhaba dunya" | ./crc32_statik
printf "123456789" | ./crc32_dinamik
echo "== python zlib ile çapraz doğrulama =="
python3 -c "import zlib;print('%08x'%zlib.crc32(b'merhaba dunya'), '%08x'%zlib.crc32(b'123456789'))"
echo "== chroot minik rootfs (yerleşik komutlarla) =="
R=/tmp/b42ov/rootfs
cp crc32_statik $R/bin/crc
unshare -r -m chroot $R /bin/sh -c 'echo "konum: $PWD"; for f in /*; do echo "  $f"; done; printf "123456789" | /bin/crc'
echo "== host /home görünür mü? =="
unshare -r -m chroot $R /bin/sh -c 'if [ -d /home ]; then echo var; else echo yok; fi'
