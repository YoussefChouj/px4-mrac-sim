# stiffer LQR K sets on the xyc_gains.h model (al 0.367879, b 0.585759, D 0.885604, dt 0.02); default Q diag(4,1,0.1,0.5) R 1
import numpy as np
from scipy.linalg import solve_discrete_are
al, b, D, dt = 0.367879, 0.585759, 0.885604, 0.02
A = np.array([[1, dt, 0, 0], [0, 1 - dt * D, dt, 0], [0, 0, al, 0], [dt, 0, 0, 1]]); B = np.array([[0], [0], [b], [0]])
def K(Q, R):
    P = solve_discrete_are(A, B, Q, np.array([[R]])); return np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)[0]
for name, q, R in [('default', [4, 1, .1, .5], 1), ('R0.25', [4, 1, .1, .5], .25), ('R0.1', [4, 1, .1, .5], .1),
                   ('qp16', [16, 2, .1, 2], 1), ('qp36', [36, 4, .1, 4], 1), ('qp64', [64, 6, .1, 6], 1), ('qp100', [100, 9, .1, 9], 1)]:
    k = K(np.diag(q), R); ev = np.linalg.eigvals(A - B @ k[None, :]); s = np.log(ev.astype(complex)) / dt
    wn = np.abs(s); zeta = -s.real / np.maximum(wn, 1e-9)
    print(f'{name:8s} K {np.round(k,3)}  slow poles wn {np.round(np.sort(wn)[:3],2)} zeta {np.round(zeta[np.argsort(wn)][:3],2)}')
