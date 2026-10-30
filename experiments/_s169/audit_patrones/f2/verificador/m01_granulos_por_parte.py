"""P2-01, medición propia. Pregunta 1: si el breaker pegado no existiera, ¿esta medición lo vería? No mide el breaker;
mide el tamaño de lo que quedaría expuesto (gránulos por parte, archivos únicos, NRT vs estándar) y el presupuesto de
tiempo. Pregunta 2: si el JSON no se leyera, n=0 y se ve. Control positivo: la suma de pasadas debe dar n_pasadas total.
Denominador: poblacion_f4.json del árbol 743e89c48."""
import json, collections, sys
P = "D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/experiments/_s166_modd_f4/poblacion_f4.json"
pob = json.load(open(P, encoding="utf-8"))
pas = pob["pasadas"]
print("claves top:", sorted(pob.keys()))
print("n_pasadas", len(pas), "n_partes", len(pob.get("partes") or []))
def clave(p): return p.get("clave") or ".".join(str(p.get("l1b") or "").split(".")[:3])
nrt = sum(1 for p in pas if ".NRT." in str(p.get("l1b")))
print("pasadas con L1B NRT:", nrt, "sin l1b:", sum(1 for p in pas if not p.get("l1b")), "sin geo:", sum(1 for p in pas if not p.get("geo")))
TIMEOUT = 240*60
for i, part in enumerate(pob["partes"]):
    cl = set(part)
    sel = [p for p in pas if clave(p) in cl]
    archivos = {(p.get("l1b"), p.get("geo")) for p in sel}
    n_arch = len(archivos)
    # peor caso: breaker tripea en el primer grupo; cada grupo cuesta 2 x (20+40+60+80) = 400 s de sueño
    grupos_cubiertos = TIMEOUT // 400
    # pasadas por grupo, en el orden del arnés (sorted por clave)
    orden = sorted(archivos, key=lambda a: str(a[0]))
    porg = collections.Counter((p.get("l1b"), p.get("geo")) for p in sel)
    pas_sin_fila = sum(porg[a] for a in sorted(porg, key=lambda a: [clave({'l1b':a[0]})])[grupos_cubiertos:])
    print(f"parte {i:2d}: pasadas {len(sel):4d} grupos(l1b,geo) {n_arch:4d}  peor caso pasadas sin fila tras 240 min: {pas_sin_fila}")
