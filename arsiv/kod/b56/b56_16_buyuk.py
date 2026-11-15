import os, time, tempfile
import numpy as np
import pandas as pd
import pyarrow
from ihadata import uret

df, _ = uret(56)
df = pd.concat([df] * 20, ignore_index=True)     # ~1,15 M satir
print("satir:", len(df), " pyarrow:", pyarrow.__version__)
klasor = tempfile.mkdtemp(prefix="b56_")
csv_y = os.path.join(klasor, "u.csv")
pq_y = os.path.join(klasor, "u.parquet")
t0 = time.perf_counter(); df.to_csv(csv_y, index=False)
print("CSV yazma  %.2f s  %6.1f MB" % (time.perf_counter() - t0,
      os.path.getsize(csv_y) / 1e6))
t0 = time.perf_counter(); df.to_parquet(pq_y, index=False)
print("Parquet yaz %.2f s  %6.1f MB" % (time.perf_counter() - t0,
      os.path.getsize(pq_y) / 1e6))
t0 = time.perf_counter(); pd.read_csv(csv_y)
print("CSV oku    %.2f s" % (time.perf_counter() - t0))
t0 = time.perf_counter(); pd.read_parquet(pq_y)
print("Parquet oku %.2f s" % (time.perf_counter() - t0))
toplam = 0; parca = 0
for c in pd.read_csv(csv_y, chunksize=200_000):
    toplam += len(c); parca += 1
print("chunk ile okunan satir:", toplam, " parca sayisi:", parca)
