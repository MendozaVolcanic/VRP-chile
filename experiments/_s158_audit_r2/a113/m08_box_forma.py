# M08: forma exacta de BOX==1 y BOX==2 en la matriz de ejemplo (dimension en km a 750 m).
# Pregunta 1: si BOX==1 no fuera el rectangulo menos la caja central, la comparacion celda a celda daria False.
# Pregunta 2: se imprime el conteo de celdas de cada mascara reconstruida, que no puede ser 0 si se leyo bien.
import scipy.io as sio, numpy as np
S = sio.loadmat(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_d17_diseno\osf_codigo_mirova\Example\VIIRS750_example.mat")
B = S["BOX"]
rect = np.zeros_like(B, bool); rect[22:43, 24:43] = True
caja = np.zeros_like(B, bool); caja[30:37, 30:37] = True
print("BOX==2 es la caja 7x7 filas 30-36 cols 30-36:", np.array_equal(B==2, caja), int(caja.sum()))
print("BOX==1 es rectangulo filas 22-42 x cols 24-42 menos la caja:", np.array_equal(B==1, rect & ~caja), int((rect&~caja).sum()))
print("caja de cumbre: 7 x 0,75 =", 7*0.75, "km; ROI1 rectangulo:", 21*0.75, "x", 19*0.75, "km; ventana:", 67*0.75, "km")
