# -*- coding: utf-8 -*-
"""F0b S160, F4-H5 por otro camino: el OSF v2.5 esta truncado en el piso de la Tabla 1 de Coppola 2026 (p. 8, RENDER)?
Mide (1) filas bajo el piso (deberia ser 0 si es filtro duro), (2) densidad en [piso, 1,1 piso) contra [1,1, 1,2) y
[1,2, 1,3): una distribucion truncada tiene el maximo de densidad pegado al piso; (3) control positivo: el mismo
calculo sobre un piso FALSO (0,5 x piso) debe dar filas por debajo > 0 o densidad sin escalon.
Pregunta 2: si el CSV no cargara, n=0 => SIN DATO."""
import sys, io, pandas as pd, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"
h = hashlib.sha256(open(F, "rb").read()).hexdigest(); print("sha256", h[:16])
df = pd.read_csv(F, usecols=["timeUTC", "Dayflag", "Resolution", "VRP"])
print("filas", len(df), df.timeUTC.min(), df.timeUTC.max())
PISO = {(375, 0): 1e4, (750, 0): 5e6, (1000, 0): 1e5, (375, 1): 5e7, (750, 1): 5e7, (1000, 1): 5e7}
for (res, day), p in PISO.items():
    for etiqueta, pp in (("piso Tabla 1", p), ("control piso falso 0,5x", 0.5 * p), ("control piso falso 2x", 2 * p)):
        x = df[(df.Resolution == res) & (df.Dayflag == day)].VRP
        if len(x) == 0:
            print(res, day, "SIN DATO"); continue
        bajo = int((x < pp).sum())
        b = [int(((x >= pp * a) & (x < pp * (a + 0.1))).sum()) for a in (1.0, 1.1, 1.2)]
        print(f"res={res} day={day} {etiqueta:24s} piso={pp:.3g} n={len(x)} bajo_piso={bajo} min={x.min():.6g} "
              f"densidad [1,1.1)={b[0]} [1.1,1.2)={b[1]} [1.2,1.3)={b[2]}")
