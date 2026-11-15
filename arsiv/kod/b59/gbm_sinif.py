# gbm_sinif.py -- log-kayipli GBM: benim surum vs sklearn
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss
from gbm import GradyanArtirma, sigmoid

X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
benim = GradyanArtirma(T=100, eta=0.1, derinlik=3, mod="sinif",
                       min_yaprak=5).fit(Xtr, ytr)
p = sigmoid(benim.ham(Xte))
sk = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1,
                                max_depth=3, min_samples_leaf=5,
                                random_state=0).fit(Xtr, ytr)
print("benim:   dogruluk=%.4f  log-kayip=%.4f"
      % (np.mean((p >= 0.5) == yte), log_loss(yte, p)))
p_sk = sk.predict_proba(Xte)[:, 1]
print("sklearn: dogruluk=%.4f  log-kayip=%.4f"
      % (sk.score(Xte, yte), log_loss(yte, p_sk)))
