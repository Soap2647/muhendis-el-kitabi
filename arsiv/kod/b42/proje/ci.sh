#!/usr/bin/env bash
# ci.sh: CI adımlarının yerel sürümü. GitHub Actions da bu betiği
# çağırır.
# Kullanım: ./ci.sh [lint|testler|kapsama|derle|imaj|tum]
set -euo pipefail
cd "$(dirname "$0")"
ESIK=${KAPSAMA_ESIK:-80}

surum() {
  git describe --tags --always --dirty 2>/dev/null || echo surumsuz
}

lint() {
  echo "[lint] C: uyarılar hataya dönüşür"
  gcc -Wall -Wextra -Werror -std=c11 -O2 -c crc32_arac.c \
      -o /dev/null
  echo "[lint] Python: derleme denetimi"
  python3 -W error -m py_compile \
      api/telemetri_api.py api/test_telemetri_api.py
}

testler() {
  echo "[testler] Python birim testleri"
  (cd api && python3 -m unittest -q test_telemetri_api 2>&1 \
     | tail -n 3)
  echo "[testler] C denetim değerleri"
  gcc -O2 -std=c11 crc32_arac.c -o crc32_test
  [ "$(printf '123456789' | ./crc32_test)" = "cbf43926" ]
  [ "$(printf '' | ./crc32_test)" = "00000000" ]
  echo "[testler] tamam"
}

kapsama() {
  echo "[kapsama] gcov ile C satır kapsaması, eşik %$ESIK"
  rm -f crc32_arac.gcda crc32_arac.gcno crc32_arac.o
  # Nesne dosyasını ayrı derlemek .gcda adını kaynağa bağlar
  gcc -O0 --coverage -std=c11 -c crc32_arac.c -o crc32_arac.o
  gcc --coverage crc32_arac.o -o crc32_kapsa
  printf '123456789' | ./crc32_kapsa > /dev/null
  printf '' | ./crc32_kapsa > /dev/null
  oran=$(gcov crc32_arac.c 2>/dev/null \
         | sed -n 's/^Lines executed:\([0-9.]*\)%.*/\1/p' \
         | head -n 1 || true)
  if [ -z "$oran" ]; then
    echo "[kapsama] gcov oranı okunamadı"; exit 1
  fi
  echo "satır kapsaması: %$oran"
  awk -v o="$oran" -v e="$ESIK" \
    'BEGIN { exit !(o + 0 >= e + 0) }' \
    || { echo "[kapsama] BAŞARISIZ"; exit 1; }
}

derle() {
  mkdir -p dist
  gcc -O2 -Wall -Wextra -Werror -std=c11 -static \
      crc32_arac.c -o dist/crc32_arac
  surum > dist/SURUM
  (cd dist && sha256sum crc32_arac SURUM > SHA256SUMS)
  echo "[derle] sürüm: $(cat dist/SURUM)"
  ls -l dist
}

imaj() {
  if command -v docker > /dev/null 2>&1 \
     && docker info > /dev/null 2>&1; then
    docker build -t "crc32-arac:$(surum)" .
  elif [ "${IMAJ_ZORUNLU:-0}" = 1 ]; then
    echo "[imaj] docker yok, IMAJ_ZORUNLU=1: BAŞARISIZ"; exit 1
  else
    echo "[imaj] docker kullanılamıyor: adım yerelde atlandı"
  fi
}

case "${1:-tum}" in
  lint)    lint ;;
  testler) testler ;;
  kapsama) kapsama ;;
  derle)   derle ;;
  imaj)    imaj ;;
  tum)     lint; testler; kapsama; derle; imaj ;;
  *) echo "kullanım: $0 [lint|testler|kapsama|derle|imaj|tum]"
     exit 2 ;;
esac
