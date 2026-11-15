#!/bin/bash
set -e
B=/tmp/b42ov; rm -rf $B; mkdir -p $B/lower $B/upper $B/work $B/merged
echo "altta bir dosya" > $B/lower/alt.txt
mkdir -p $B/lower/etc && echo "alt-etc" > $B/lower/etc/ayar.conf
unshare -r -m sh -c "
  mount -t overlay overlay -o lowerdir=$B/lower,upperdir=$B/upper,workdir=$B/work $B/merged || { echo 'mount basarisiz'; exit 1; }
  echo '== birleşik görünüm (merged) =='; find $B/merged -type f | sort
  echo 'yeni dosya' > $B/merged/yeni.txt
  echo 'degisti' > $B/merged/etc/ayar.conf
  rm $B/merged/alt.txt 2>/dev/null || echo 'alt.txt silinemedi (whiteout bekleniyor)'
  echo '== upper (yalnız değişiklikler) =='; find $B/upper | sort
  echo '== upper içindeki özel dosya türleri (whiteout = 0/0 karakter aygıtı) =='
  ls -l $B/upper | head -5
" 2>&1 | grep -v "screen size"
echo "== lower dokunulmadı mı? =="; cat $B/lower/etc/ayar.conf; ls $B/lower
echo "== kök dosya sistemi: chroot ile minik rootfs =="
R=$B/rootfs; rm -rf $R; mkdir -p $R/bin $R/lib
cp /bin/sh $R/bin/
for lib in $(ldd /bin/sh | grep -o '/[^ ]*'); do mkdir -p $R$(dirname $lib); cp -L $lib $R$lib; done
ls -la $R/bin/sh
unshare -r -m chroot $R /bin/sh -c 'echo "kök içinde: $(ls /)"; echo "/ altındaki dosyalar:"; ls -R / 2>/dev/null | head -3' 2>&1 | grep -v "screen size"
