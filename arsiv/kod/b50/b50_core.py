# -*- coding: utf-8 -*-
# Bölüm 50 - Optimizasyon: sıfırdan gradyan tabanlı yöntemler.
import numpy as np


def kuad(x):
    """f(x, y) = x^2 + 10 y^2   (kappa = 10)."""
    return x[0] ** 2 + 10 * x[1] ** 2


def kuad_g(x):
    return np.array([2 * x[0], 20 * x[1]])


def kot(x):
    """f(x, y) = x^2 + 100 y^2   (kappa = 100)."""
    return x[0] ** 2 + 100 * x[1] ** 2


def kot_g(x):
    return np.array([2 * x[0], 200 * x[1]])


def rosen(x):
    """Rosenbrock: (1-x)^2 + 100 (y-x^2)^2, minimum (1, 1)."""
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2


def rosen_g(x):
    a = x[1] - x[0] ** 2
    return np.array([-2 * (1 - x[0]) - 400 * x[0] * a, 200 * a])


def gd(g, x0, eta, n):
    x = np.asarray(x0, float).copy()
    yol = [x.copy()]
    for _ in range(n):
        x = x - eta * g(x)
        yol.append(x.copy())
    return np.array(yol)


def momentum(g, x0, eta, n, beta=0.9):
    x = np.asarray(x0, float).copy()
    v = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        v = beta * v + g(x)
        x = x - eta * v
        yol.append(x.copy())
    return np.array(yol)


def nesterov(g, x0, eta, n, beta=0.9):
    x = np.asarray(x0, float).copy()
    v = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        v = beta * v - eta * g(x + beta * v)
        x = x + v
        yol.append(x.copy())
    return np.array(yol)


def adagrad(g, x0, eta, n, eps=1e-8):
    x = np.asarray(x0, float).copy()
    G = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        gr = g(x)
        G += gr * gr
        x = x - eta * gr / (np.sqrt(G) + eps)
        yol.append(x.copy())
    return np.array(yol)


def rmsprop(g, x0, eta, n, rho=0.9, eps=1e-8):
    x = np.asarray(x0, float).copy()
    E = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        gr = g(x)
        E = rho * E + (1 - rho) * gr * gr
        x = x - eta * gr / (np.sqrt(E) + eps)
        yol.append(x.copy())
    return np.array(yol)


def adam(g, x0, eta, n, b1=0.9, b2=0.999, eps=1e-8, wd=0.0):
    x = np.asarray(x0, float).copy()
    m = np.zeros_like(x)
    v = np.zeros_like(x)
    yol = [x.copy()]
    for t in range(1, n + 1):
        gr = g(x)
        m = b1 * m + (1 - b1) * gr
        v = b2 * v + (1 - b2) * gr * gr
        mh = m / (1 - b1 ** t)
        vh = v / (1 - b2 ** t)
        x = x - eta * (mh / (np.sqrt(vh) + eps) + wd * x)
        yol.append(x.copy())
    return np.array(yol)


def yakinsama(f, yol, f_star=0.0):
    """Her adım için f(x_k) - f*; numpy dizisi döndürür."""
    return np.array([f(x) - f_star for x in yol])
