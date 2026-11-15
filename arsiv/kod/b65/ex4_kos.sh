#!/bin/bash
# Örnek 4: ex4_dongu ve ex4_ayrik dönüşümlü 3'er koşu; her koşu ayrı kaydedilir.
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"
for k in 1 2 3; do
  python ex4_dongu.py > ex4_kosular/dongu_$k.txt 2>/dev/null
  python ex4_ayrik.py > ex4_kosular/ayrik_$k.txt 2>/dev/null
done
echo BITTI
