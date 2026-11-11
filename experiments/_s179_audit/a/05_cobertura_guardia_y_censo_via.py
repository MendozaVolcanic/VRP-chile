# -*- coding: utf-8 -*-
"""Censo de records MODIS de produccion desde la vispera del encendido y cobertura de la guardia K, en main 438a60a1e.

Preguntas del instrumento:
1. Si la via estuviera cayendo a K o dejando de escribir, esto lo veria? Si: cuenta por volcan los records MODIS con
   observacion desde 2026-11-02, por marca (`via_codigo_mirova` True, texto, ausente) y por `processed_utc`.
2. Instrumento muerto: imprime el total de records MODIS leidos por volcan en todo el archivo (debe ser miles) y un
   control: records MODIS anteriores al 2026-11-01 con marca True deben ser 0 salvo reemplazos (se listan).
Denominador: records MODIS de los 11 Tier A con datetime_utc >= 2026-11-02 00:00. Ventana hasta el ultimo record del commit.
"""
import io, sys, os, json, collections
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
        "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
ENC = "2026-11-02T20:11:43Z"
def lee(carpeta, vol):
    return json.load(open(os.path.join(BASE, "data", carpeta, vol + ".json"), encoding="utf-8"))["records"]
def dt(r): return datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
tot = collections.Counter(); tabla = {}
viejos_via = []; k_tras_enc = []; sin_guardia = collections.Counter(); con_guardia = collections.Counter()
solo_guardia = []; por_noche = collections.defaultdict(lambda: [0, 0])
campos_via = collections.Counter(); ultimo = ""
for v in VOLS:
    P = [r for r in lee("mirova_equivalent", v) if str(r.get("sensor", "")).startswith("MODIS")]
    G = [r for r in lee("guardia_k_modis", v) if str(r.get("sensor", "")).startswith("MODIS")]
    tot[v] = len(P)
    c = collections.Counter()
    for r in P:
        m = r.get("via_codigo_mirova")
        ultimo = max(ultimo, r["datetime_utc"])
        if r["datetime_utc"] < "2026-11-02 00:00":
            if m is True: viejos_via.append((v, r["sensor"], r["datetime_utc"], r.get("processed_utc")))
            continue
        marca = "via" if m is True else (f"caida:{m}" if isinstance(m, str) else "K_sin_marca")
        c[marca] += 1
        if m is not True and str(r.get("processed_utc", "")) >= ENC:
            k_tras_enc.append((v, r["sensor"], r["datetime_utc"], r.get("processed_utc"), m, r.get("product_type") or r.get("source_product")))
        if m is True:
            for k in r.keys(): campos_via[k] += 1
        par = [g for g in G if g["sensor"] == r["sensor"] and abs((dt(g) - dt(r)).total_seconds()) <= 120]
        noche = r["datetime_utc"][:10]
        por_noche[noche][0] += 1
        if par: con_guardia[v] += 1; por_noche[noche][1] += 1
        else: sin_guardia[v] += 1
    for g in G:
        if g["datetime_utc"] < "2026-11-02 00:00": continue
        if not [r for r in P if r["sensor"] == g["sensor"] and abs((dt(g) - dt(r)).total_seconds()) <= 120]:
            solo_guardia.append((v, g["sensor"], g["datetime_utc"], g.get("processed_utc")))
    tabla[v] = c
print("Ultimo record MODIS de produccion en el commit:", ultimo)
print("Records MODIS por volcan en todo el archivo (control de instrumento vivo):", dict(tot))
print("\nRecords MODIS de produccion con observacion desde 2026-11-02 00:00, por marca:")
suma = collections.Counter()
for v in VOLS:
    print(f"  {v:22s}", dict(tabla[v])); suma.update(tabla[v])
print("  TOTAL", dict(suma))
print("\nRecords MODIS anteriores al 2026-11-02 con marca de la via (control, se espera 0):", len(viejos_via), viejos_via[:5])
print("\nRecords MODIS SIN la via escritos (processed_utc) despues del encendido, observacion desde 2026-11-02:")
for x in k_tras_enc: print("  ", x)
print("  total:", len(k_tras_enc))
print("\nCobertura de la guardia K sobre las pasadas MODIS de produccion (par mismo sensor a +-120 s), por noche UTC:")
for n in sorted(por_noche): print(f"  {n}: produccion {por_noche[n][0]:3d} | con record de la guardia {por_noche[n][1]:3d}")
print("  por volcan con/sin guardia:", {v: (con_guardia[v], sin_guardia[v]) for v in VOLS})
print("\nPasadas que la guardia K registra y produccion no (desde 2026-11-02):", len(solo_guardia))
for x in solo_guardia: print("  ", x)
print("\nCampos presentes en los records de la via (n de", suma["via"], "):")
for k, n in sorted(campos_via.items(), key=lambda x: -x[1]): print(f"   {k}: {n}")
