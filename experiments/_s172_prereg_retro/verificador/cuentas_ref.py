# -*- coding: utf-8 -*-
"""VPR172 V-4: recalcula los conteos de referencia del borrador con banco_paridad/clase_mirova de origin/main (export_main).
Preg 1 (si lo medido estuviera roto, lo veria): control positivo = el mismo conteo en la ventana de V2/MOD-D (2026-03-01..10-16)
 contra la cifra sellada de MOD-D (50 protegidas MODIS, 42 bajo 1 MW, 5110 negativos limpios) como control de instrumento.
Preg 2 (instrumento muerto): imprime n filas de referencia cargadas por tramo; un 0 con n filas>0 es dato, con n=0 es SIN DATO."""
import sys, os, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts")
os.chdir(EXP)
import banco_paridad as bp
from clase_mirova import alerta_protegida, aplicar_regla_minimas, TIPOS_ALERTA
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
import hashlib
for p in (SNAP_CONS, SNAP_OCR):
    print("sha256", p.name, hashlib.sha256(open(p,'rb').read()).hexdigest())
coords = bp._coords_por_volcan()
filas_all = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
print("filas unificadas", len(filas_all))
filas_cons = [f for f in filas_all if f["source"] == "CONS"]
print("filas CONS", len(filas_cons))
# NOAA21 en la referencia
c = collections.Counter()
for f in filas_all:
    c[(f["sensor_raw"], f["fecha_utc"][:7])] += 1
n21 = sorted(k for k in c if "21" in k[0])
print("sensor_raw con 21:", n21[:6])
first21 = min((f["fecha_utc"] for f in filas_all if "21" in f["sensor_raw"]), default=None)
print("primera fila NOAA21 en la referencia:", first21)
first21c = min((f["fecha_utc"] for f in filas_cons if "21" in f["sensor_raw"]), default=None)
print("primera fila NOAA21 en CONS:", first21c)
first20 = min((f["fecha_utc"] for f in filas_all if "20" in f["sensor_raw"]), default=None)
print("primera NOAA20:", first20, " primera SNPP:", min((f["fecha_utc"] for f in filas_all if "NPP" in f["sensor_raw"].upper() or "Suomi" in f["sensor_raw"]), default=None))
print("sensores raw distintos:", sorted(set(f["sensor_raw"] for f in filas_all))[:20])

TRAMOS = {
 "F26-M(feb,MODIS)": ("2026-02-01","2026-02-28",["MODIS"]),
 "F26-M3(mar,MODIS)": ("2026-03-01","2026-03-31",["MODIS"]),
 "F26-V(feb-mar,VIIRS)": ("2026-02-01","2026-03-31",["VIIRS375","VIIRS750"]),
 "V2-control(03-01..10-16)": ("2026-03-01","2026-10-16",["MODIS","VIIRS375","VIIRS750"]),
 "DM(10-01..10-16)": ("2026-10-01","2026-10-16",["MODIS","VIIRS375","VIIRS750"]),
}
def cuenta(filas, ventana, buckets, regla, desde_tup=None):
    filas2 = filas
    por_vb, ns, nv, n = bp.indexar_referencia(filas2, coords, ventana, regla_minimas=regla)
    out = {}
    for b in buckets:
        pas = {}   # (vol, hora) -> lista filas
        for (vol, bb), lst in por_vb.items():
            if bb != b: continue
            for dt, f in lst:
                if desde_tup and vol=="Tupungatito" and f["fecha_utc"][:10] < desde_tup: continue
                pas.setdefault((vol, f["fecha_utc"][:16]), []).append(f)
        prot = bajo = neg = fp = otros = 0
        prot_vol = collections.Counter(); bajo_vol=collections.Counter(); neg_vol=collections.Counter()
        for k, fs in pas.items():
            al = [f for f in fs if bp.es_alerta(f["tipo"])]
            if al:
                if any(alerta_protegida(f) for f in al): prot += 1; prot_vol[k[0]] += 1
                else: bajo += 1; bajo_vol[k[0]] += 1
            elif any(bp.es_fp(f["tipo"]) for f in fs): fp += 1
            elif all(f["tipo"]=="RUTINA" for f in fs): neg += 1; neg_vol[k[0]]+=1
            else: otros += 1
        out[b] = dict(pasadas=len(pas), protegida=prot, bajo1=bajo, neg_rutina=neg, far_fp=fp, otros=otros,
                      prot_vol=dict(prot_vol), bajo_vol=dict(bajo_vol))
    return out, n
res = {}
for nombre, (d, h, bs) in TRAMOS.items():
    for canal, fl in (("tabla", filas_cons), ("union", filas_all)):
        for regla in ("SN",):
            o, n = cuenta(fl, (d, h), bs, regla, desde_tup="2026-02-23" if nombre.startswith("F26") else None)
            res[f"{nombre}|{canal}|{regla}"] = o
            print(f"\n== {nombre} | canal {canal} | regla {regla} | filas ref nocturnas {n}")
            for b, v in o.items():
                print("  ", b, json.dumps(v, ensure_ascii=False))
json.dump(res, open(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\cuentas_ref_salida.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
