# rot3.py: 3B donme matrisleri, ortogonallik, homojen donusum
import numpy as np


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


yaw, pitch, roll = np.deg2rad([90.0, 30.0, 10.0])
R = rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)
print("R^T R == I ?", np.allclose(R.T @ R, np.eye(3)))
print("det(R)     =", round(np.linalg.det(R), 9))

# 4x4 homojen donusum: govde -> dunya
t = np.array([100.0, 50.0, 30.0])          # konum (metre)
T = np.eye(4)
T[:3, :3] = R
T[:3, 3] = t
p_govde = np.array([2.0, 0.0, 0.0, 1.0])  # govde x ekseninde 2 m
p_dunya = T @ p_govde
print("dunya koordinati =", np.round(p_dunya[:3], 4))

# ters donusum: dunya -> govde (R^T yeter, tersi gerekmez)
Tt = np.eye(4)
Tt[:3, :3] = R.T
Tt[:3, 3] = -R.T @ t
print("geri donus    =", np.round((Tt @ p_dunya)[:3], 4))
print("ters dogru ?  ", np.allclose(Tt @ p_dunya, p_govde))
