#!/bin/bash
# E6: katman arşivinin tekrarlanabilirliği (içerik adresi)
D=/tmp/b42tar; rm -rf $D; mkdir -p $D/src/app
printf 'int main(void){return 0;}\n' > $D/src/app/main.c
printf 'bin\n' > $D/src/app/.gitignore
cd $D/src
echo "== 1) normalleştirilmiş arşiv =="
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -cf $D/a1.tar .
sha256sum $D/a1.tar | cut -c1-16
sleep 1; touch app/main.c   # yalnız zaman damgası değişir
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -cf $D/a2.tar .
echo "zaman damgası değişti, normalleştirilmiş özet:"; sha256sum $D/a2.tar | cut -c1-16
echo "== 2) normalleştirilmemiş arşiv =="
tar -cf $D/b1.tar . ; sleep 1; touch app/main.c; tar -cf $D/b2.tar .
echo "b1: $(sha256sum $D/b1.tar | cut -c1-16)"
echo "b2: $(sha256sum $D/b2.tar | cut -c1-16)"
echo "== 3) içerik değişince özet değişir =="
printf 'int main(void){return 1;}\n' > app/main.c
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -cf $D/a3.tar .
sha256sum $D/a3.tar | cut -c1-16
echo "== 4) arşiv içeriği (normalleştirilmiş) =="
tar -tvf $D/a1.tar
