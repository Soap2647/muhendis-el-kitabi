#!/bin/bash
# Bolum 75 tum deneyleri sirayla (tek seferde tek betik, 4 thread).
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"
for b in b75_nicemleme.py b75_aykiri.py b75_budama.py b75_damitma.py \
         b75_onnx.py b75_olcum.py b75_mimari.py; do
  echo "=== $b"; python -W ignore "$b" > "log_${b%.py}.txt" 2>/dev/null
  echo "  cikis=$?"
done
