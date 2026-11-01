# -*- coding: utf-8 -*-
"""F6 M6: ¿Max_Dist del OSF v2.5 cabe en la ventana de 67 x 67 celdas de 750 m que declara el codigo publicado?
El codigo (MIROVA_VIIRS750_hotspot_detection.m) excluye el marco exterior, asi que con el volcan en la celda central
(34 de 67) el desplazamiento maximo por eje es 32 celdas (24 km) y la diagonal 45,25 celdas (33,9 km).
Instrumento: Max_Dist/750 al cuadrado debe ser un entero i^2 + j^2 (pixel en grilla centrada en el volcan). Se
buscan las descomposiciones y se pregunta si alguna cabe con max(|i|,|j|) <= 32.
Pregunta 1: si la grilla no estuviera centrada o no fuera de 750 m, la cuantizacion fallaria en muchas filas (se ve).
Control positivo: el mismo analisis sobre 375 m con celda de 375 m, y sobre 750 m con celda de 700 m (debe fallar).
Denominador: 100.641 filas V750 (2012-2025)."""
import sys, io, math
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
full = pd.read_csv(sys.argv[1])
def decomp(n2):
    out = []
    for i in range(0, int(math.isqrt(n2)) + 1):
        j2 = n2 - i*i
        j = math.isqrt(j2)
        if j*j == j2 and i <= j:
            out.append((i, j))
    return out
for res, cell in [(750, 750.0), (750, 700.0), (375, 375.0)]:
    d = full[full.Resolution == res]
    q = (d.Max_Dist / cell) ** 2
    qi = q.round()
    ok = (q - qi).abs() < 0.02
    print(f"\nres {res} celda {cell}: n={len(d)}  Max_Dist cuantizado a i^2+j^2 (tol 0.02 en celdas^2): {ok.sum()}  "
          f"({100*ok.mean():.2f} %)")
    if cell != res:
        continue
    vals = sorted(set(qi[ok].astype(int)))
    no_rep = [v for v in vals if not decomp(v)]
    print(f"  valores distintos {len(vals)}; sin representacion como suma de dos cuadrados: {len(no_rep)} {no_rep[:10]}")
    if res == 750:
        fuera_caja = [v for v in vals if decomp(v) and min(max(a, b) for a, b in decomp(v)) > 32]
        print("  valores que obligan a max(|i|,|j|) > 32 (fuera de 67x67):", fuera_caja,
              " filas:", int(qi[ok].isin(fuera_caja).sum()))
        print("  radio maximo (celdas):", math.sqrt(max(vals)), " Max_Dist max m:", d.Max_Dist.max())
        top = qi[ok].value_counts().sort_index().tail(12)
        print("  cola de la distribucion (celdas^2: filas):", dict(top))
        # ¿hay pila en el radio 40? contar filas con radio en [38, 40] contra [36, 38)
        rr = np.sqrt(qi[ok])
        print("  filas con radio en [36,38):", int(((rr>=36)&(rr<38)).sum()), " [38,40]:", int(((rr>=38)&(rr<=40)).sum()),
              " (40,45.3]:", int((rr>40).sum()))
