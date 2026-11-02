# -*- coding: utf-8 -*-
"""s05 (S172, auditoria Chillan): dos controles cruzados del instrumento.

(a) Mis razones K por pasada de MODIS (s02) contra las razon_k de la lectura del A/B de MOD-D (resultado_f4.json, clave
    chillan.pares): si mi pareo o mi magnitud publicada estuvieran rotos, no coincidirian pasada a pasada.
(b) El criterio "dash" del auto-audit (reconstruido en Python: 0 < pc.vrp_mw <= CAP, pc.centroid_dist_km <= inner,
    distance_class in {summit, None}) contra el predicado del tablero ejecutado con node (s02, columna pub), sobre las
    mismas pasadas nocturnas de Chillan. A97 dice que "publica" es el de node; si difieren, el auto-audit mide otra cosa.
P1: control positivo de (a): se compara tambien contra razon_b (brazo V), que debe NO coincidir con K.
P2: si el archivo de MOD-D no se leyera, n_comparados = 0 y se imprime SIN DATO, no OK.
Uso: python -B s05_controles_cruzados.py <pasadas.csv> <resultado_f4.json> <salida.txt>
"""
import csv, json, sys

PAS, F4, OUT = sys.argv[1:4]
R = list(csv.DictReader(open(PAS, encoding="utf-8")))
f4 = json.load(open(F4, encoding="utf-8"))
lines = []
mod = {r["dt"]: r for r in R if r["b"] == "MODIS" and r["pub"] == "1" and r["vrp_M"] not in ("", "None")}
n, ok, okb = 0, 0, 0
for p in f4.get("chillan", {}).get("pares", []):
    r = mod.get(p["dt"])
    if r is None:
        lines.append(f"(a) {p['dt']} sin par en s02")
        continue
    mia = float(r["disp"]) / float(r["vrp_M"])
    n += 1
    ok += abs(mia - p["razon_k"]) < 1e-3
    okb += abs(mia - p["razon_b"]) < 1e-3
    lines.append(f"(a) {p['dt']} mia {mia:.4f} | MOD-D razon_k {p['razon_k']:.4f} | razon_b {p['razon_b']:.4f}")
lines.append(f"(a) comparados {n}; coinciden con razon_k {ok}; con razon_b (control, debe ser ~0) {okb}"
             + ("" if n else "  -> SIN DATO"))
CAP = 50000.0
inner = 5.0
dif = []
for r in R:
    try:
        v = float(r["pc_vrp"]) if r["pc_vrp"] not in ("", "None") else 0.0
        d = float(r["pc_dist"]) if r["pc_dist"] not in ("", "None") else None
    except ValueError:
        v, d = 0.0, None
    dash = (0 < v <= CAP) and (d is not None and d <= inner) and (r["dc"] in ("", "None", "summit"))
    if dash != (r["pub"] == "1"):
        dif.append((r["b"], r["dt"], r["dc"], r["pc_vrp"], r["pc_dist"], r["pub"], r["disp"]))
lines.append(f"(b) pasadas nocturnas {len(R)}; dash del auto-audit != pub de node en {len(dif)}")
for x in dif[:40]:
    lines.append(f"(b)   {x}")
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
