# -*- coding: utf-8 -*-
import warnings
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
warnings.filterwarnings("ignore")
VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
G = np.random.default_rng(61).normal(size=(500, 50))
km_ham = KMeans(n_clusters=8, n_init=10, random_state=61).fit(G)
print("ham gurultu siluet(k=8) = %.4f" % silhouette_score(
    G, km_ham.labels_))
for p in [5, 15, 30, 50]:
    ts = TSNE(n_components=2, perplexity=p, init="pca",
              learning_rate="auto", random_state=61)
    Y = ts.fit_transform(G)
    km = KMeans(n_clusters=8, n_init=10, random_state=61).fit(Y)
    lab = km.labels_
    print("perp=%2d KL=%.4f siluet(k=8)=%.4f" % (
        p, ts.kl_divergence_, silhouette_score(Y, lab)))
    yol = VERI + "b61_tsne_gurultu_p%d.csv"
    np.savetxt(yol % p, Y, delimiter=",", header="x,y",
               comments="", fmt="%.5f")

# Etiketli gurultu gomulmesi (sekil icin): p=30 ve k=8 etiketleri
Y = TSNE(n_components=2, perplexity=30, init="pca",
         learning_rate="auto", random_state=61).fit_transform(G)
lab = KMeans(n_clusters=8, n_init=10, random_state=61).fit(Y).labels_
with open(VERI + "b61_tsne_gurultu_etiket.csv", "w") as f:
    f.write("x,y,kume\n")
    for (a, b), c in zip(Y, lab):
        f.write("%.5f,%.5f,%d\n" % (a, b, c))
print("etiketli CSV yazildi, siluet=%.4f" % silhouette_score(Y, lab))
