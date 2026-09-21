# -*- coding: utf-8 -*-
"""S149, frente D. Abre por dentro los 44 pares VIIRS 375 donde la magnitud publicada cambia al
apagar el Test 1 (salida de d1: d1_pares_magnitud.json). Pregunta: el cambio es de DETECCION (otro
objeto, otro lugar) o solo del NUMERO (el mismo cumulo con menos pixeles sumados)?

Instrumento: lee los records crudos de los dos brazos y compara primary_cluster (n_pixels, vrp_mw,
centroide), n_anomalous_pixels, f5_core_vrp_mw y el conteo de pixeles por camino si existe.
1. Si estuviera roto (no pareara bien), n de pares != 44: se imprime.
2. Control positivo: en los 91 pares donde la magnitud NO cambia, n_pixels del cumulo debe ser igual
   en casi todos; si tambien difiriera ahi, la comparacion de pixeles no explicaria nada.
Uso: python d2_magnitud_por_dentro.py DIR_SALIDAS
"""
import sys, io, json, statistics, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; D = Path(sys.argv[1])
pares = json.load(open(AQUI / "d1_pares_magnitud.json", encoding="utf-8"))
idx = {}
for brazo in ("_s146_ab_control", "_s146_ab_sin_test1"):
    for p in (D / brazo).glob("*.json"):
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            s = r.get("sensor") or ""
            if s.startswith("VIIRS") and not s.endswith("_750"):
                idx[(brazo, p.stem, r["datetime_utc"][:16])] = r


def px_cluster(r):
    pc = r.get("primary_cluster") or {}
    return pc.get("n_pixels"), pc.get("vrp_mw"), r.get("n_anomalous_pixels"), r.get("f5_core_vrp_mw"), r.get("f5_core_n_pixels")


campos_diag = None
for nombre, sel in (("CAMBIA la magnitud", [f for f in pares if abs(f["dc"] - f["db"]) >= 1e-9]),
                    ("NO cambia (control positivo)", [f for f in pares if abs(f["dc"] - f["db"]) < 1e-9])):
    print("\n==", nombre, "| pares", len(sel))
    dn, dnan, menos, mas, igual, falt = [], [], 0, 0, 0, 0
    for f in sel:
        c = idx.get(("_s146_ab_control", f["vol"], f["dt"])); b = idx.get(("_s146_ab_sin_test1", f["vol"], f["dt"]))
        if c is None or b is None: falt += 1; continue
        nc, vc, ac, fc, fnc = px_cluster(c); nb, vb, ab, fb, fnb = px_cluster(b)
        if nc is None or nb is None: falt += 1; continue
        dn.append(nb - nc); dnan.append((ab or 0) - (ac or 0))
        menos += nb < nc; mas += nb > nc; igual += nb == nc
    print("   sin parear en crudo:", falt)
    print("   pixeles del cumulo primario, brazo menos control: menos %d | igual %d | mas %d | mediana %s" % (menos, igual, mas, statistics.median(dn) if dn else None))
    print("   n_anomalous_pixels de la escena, brazo menos control: mediana %s | min %s | max %s" % (
        statistics.median(dnan) if dnan else None, min(dnan) if dnan else None, max(dnan) if dnan else None))

# detalle de los que cambian: razon brazo/control de la magnitud y de los pixeles
print("\n== detalle de los que cambian (ordenado por razon de magnitud brazo/control)")
print("%-20s %-16s %7s %8s %8s %6s %6s %7s %s" % ("volcan", "pasada", "MIROVA", "control", "brazo", "npx_c", "npx_b", "mov_km", "diag_test1 en control"))
filas = []
for f in pares:
    if abs(f["dc"] - f["db"]) < 1e-9: continue
    c = idx[("_s146_ab_control", f["vol"], f["dt"])]; b = idx[("_s146_ab_sin_test1", f["vol"], f["dt"])]
    filas.append((f["db"] / f["dc"], f, c, b))
for q, f, c, b in sorted(filas, key=lambda t: t[0]):
    pc_c = c.get("primary_cluster") or {}; pc_b = b.get("primary_cluster") or {}
    print("%-20s %-16s %7.3f %8.3f %8.3f %6s %6s %7.2f t1=%s n_t1=%s" % (f["vol"], f["dt"], f["ref"], f["dc"], f["db"], pc_c.get("n_pixels"), pc_b.get("n_pixels"),
          f["mov"] or 0, c.get("triggered_test1"), c.get("diag_n_test1_pixels", c.get("test1_n_pixels"))))
# que campos de diagnostico del Test 1 existen en el record del control
ej = filas[0][2]
print("\ncampos del record que nombran test1:", sorted(k for k in ej if "test1" in k.lower()))
print("campos de primary_cluster:", sorted((ej.get("primary_cluster") or {}).keys()))
# a que lado de 1 queda cada brazo
ab_c = sum(1 for q, f, c, b in filas if f["dc"] / f["ref"] < 1); ab_b = sum(1 for q, f, c, b in filas if f["db"] / f["ref"] < 1)
acerca = sum(1 for q, f, c, b in filas if abs(f["db"] / f["ref"] - 1) < abs(f["dc"] / f["ref"] - 1))
print("\nde los %d que cambian: control bajo MIROVA en %d, brazo bajo MIROVA en %d | el brazo queda MAS CERCA de MIROVA en %d y mas lejos en %d" % (
    len(filas), ab_c, ab_b, acerca, len(filas) - acerca))
