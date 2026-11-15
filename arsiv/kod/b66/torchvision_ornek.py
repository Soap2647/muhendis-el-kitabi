# -*- coding: utf-8 -*-
"""Bölüm 66 - gerçek ön eğitimli ağırlıkla transfer
(ÇALIŞTIRILMADI)."""

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet18_Weights

pesler = ResNet18_Weights.DEFAULT  # ImageNet ağırlıkları
on = models.resnet18(weights=pesler)
on_isleme = pesler.transforms()  # ölçek ve normalizasyon

for p in on.parameters():  # gövdeyi dondur
    p.requires_grad_(False)
on.fc = nn.Linear(on.fc.in_features, 4)  # yeni 4 sınıflı baş
