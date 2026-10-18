import sys, numpy as np
sys.path.insert(0, "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s151_seleccion_mirova")
import comun_tif as ct
T = "C:/Users/nmend/AppData/Local/Temp/claude/r2_fk/tif/data_tif_Lascar_"
a = ct.leer(T + "20260602_054201_VIIRS375.tif", "VIIRS375")["a"]
b = ct.leer(T + "20260906_054201_VIIRS375.tif", "VIIRS375")["a"]
best = []
for dr in range(-30, 31):
    for dc in range(-45, 46):
        A = a[max(0, dr):a.shape[0] + min(0, dr), max(0, dc):a.shape[1] + min(0, dc)]
        B = b[max(0, -dr):b.shape[0] + min(0, -dr), max(0, -dc):b.shape[1] + min(0, -dc)]
        if A.size < 3000: continue
        m = np.isfinite(A) & np.isfinite(B) & (A > 0) & (B > 0)
        best.append((np.corrcoef(A[m], B[m])[0, 1], dr, dc))
best.sort(reverse=True)
print("mejores desplazamientos (corr, drow, dcol) del 06-02 contra el 09-06:", [(round(c, 3), r, q) for c, r, q in best[:5]])
print("corr a desplazamiento 0:", [round(c, 3) for c, r, q in best if r == 0 and q == 0])
print("corr al desplazamiento del foco (22, 40):", [round(c, 3) for c, r, q in best if (r, q) in ((22, 40), (-22, -40))])
