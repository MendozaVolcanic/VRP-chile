"""VS34 V-4 parte A: geometria. Para cada uno de los 45 volcanes y cada familia (V750 67x67, V375 134x134, MODIS 51x51):
que otros volcanes de volcanoes.yaml caen dentro de SU grilla (cuadrado real de celdas, no el +-25 km del autor) y en
que clase de BOX caen (0 conservadora estricta, 1 anillo conservador, 2 sensible) con la caja que usa la via
(caja_roi 'def' en V750 y MODIS; caja_v375 en V375, centrada en el cráter).
Q1: si un vecino cayera dentro de la grilla, esta medicion lo ve (control positivo: Villarrica contiene a Quetrupillan).
Q2: si el instrumento estuviera muerto (grillas vacias) el conteo seria 0 y el control positivo lo delata.
Usa pipeline.mirova_v750_codigo de la rama (worktree, solo lectura)."""
import sys, os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "D:/vrp-trabajo/worktrees/s172-sombra34")
import numpy as np, yaml
from pyproj import Transformer
from pipeline import mirova_v750_codigo as MV
W = "D:/vrp-trabajo/worktrees/s172-sombra34"
vols = yaml.safe_load(open(f"{W}/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
nrt = set(yaml.safe_load(open(f"{W}/.github/workflows/nrt.yml", encoding="utf-8"))["jobs"]["process"]["strategy"]["matrix"]["volcano"])
FAM = {"VIIRS750": 750.0, "VIIRS375": 375.0, "MODIS": 1000.0}
filas = []
for v in vols:
    for fam, paso in FAM.items():
        cfg = MV.FAMILIAS[fam]
        g = MV.grilla_del_volcan(v["name"], paso_m=paso, clave_roi=cfg["clave_roi"])
        n = g["n"]
        if cfg.get("roi1_half_m") is not None:
            box = MV.caja_v375(g, v["lat"], v["lon"], lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
        else:
            box = MV.caja_roi(g["roi"], n=n, celda_crater=MV.celda_de(g, v["lat"], v["lon"]), lado_sensible=cfg["lado_sensible"],
                              lado_anillo=cfg["lado_anillo"], paso_m=paso)
        box = box.copy(); box[:, [0, -1]] = np.nan; box[[0, -1], :] = np.nan
        t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
        for w in vols:
            if w["name"] == v["name"]: continue
            x, y = t.transform(w["lon"], w["lat"])
            col = (x - g["ul_x"]) // paso; fila = (g["ul_y"] - y) // paso
            if 0 <= fila < n and 0 <= col < n:
                clase = box[int(fila), int(col)]
                d = ((x - g["x0"]) ** 2 + (y - g["y0"]) ** 2) ** 0.5 / 1000
                filas.append((v["name"], fam, w["name"], round(d, 1), "NaN(borde)" if np.isnan(clase) else int(clase)))
print("objetivo | familia | vecino dentro de la grilla | km | clase BOX (0 estricta, 1 anillo, 2 sensible)")
for f in filas: print(" | ".join(map(str, f)))
nombres = {v["name"] for v in vols}
print("\nObjetivos con >=1 vecino dentro de la grilla V750:", len({f[0] for f in filas if f[1] == 'VIIRS750'}),
      "(de los cuales de los 34:", len({f[0] for f in filas if f[1] == 'VIIRS750' and f[0] not in nrt}), ")")
print("Control positivo (Villarrica contiene a Quetrupillan en V750):", any(f[0]=='Villarrica' and f[2]=='Quetrupillan' and f[1]=='VIIRS750' for f in filas))
print("Alguno de los 11 contiene a otro de los 11 en su grilla:", [f for f in filas if f[0] in nrt and f[2] in nrt and f[1]=='VIIRS750'])
print("Vecinos Tier A (los 11) que caen dentro de la grilla de uno de los 34:", sorted({(f[0], f[2]) for f in filas if f[0] not in nrt and f[2] in nrt and f[1]=='VIIRS750'}))
print("Los 34 que caen dentro de la grilla de uno de los 11 (el record de los 11 podria contenerlos):", sorted({(f[0], f[2]) for f in filas if f[0] in nrt and f[2] not in nrt and f[1]=='VIIRS750'}))
print("Clases BOX en que caen los vecinos (V750):", sorted({f[4] for f in filas if f[1]=='VIIRS750'}, key=str), "| V375:", sorted({f[4] for f in filas if f[1]=='VIIRS375'}, key=str), "| MODIS:", sorted({f[4] for f in filas if f[1]=='MODIS'}, key=str))
