# -*- coding: utf-8 -*-
"""S162 MOD-E (D28, bow tie de MODIS), paso 1 sin red: ¿el port del codigo de MIROVA, que NO quita los pixeles
duplicados del bow tie, reproduce a MIROVA (que si los quita, D28) igual en las pasadas oblicuas que en el nadir?

POR QUE. Hacia el borde del barrido MODIS los barridos de 10 lineas se traslapan (bow tie): el mismo suelo aparece en
la ultima fila de un barrido y en la primera del siguiente. Coppola 2013, 2023 y Aveni 2023 dicen que MIROVA identifica
y elimina esos duplicados antes de remuestrear (catalogo, D28). El port remuestra con todos (griddata lineal sobre los
centros nativos). Si los duplicados pesaran en la magnitud o en la deteccion, la razon port/MIROVA se apartaria de 1
justo donde hay traslape (cenit alto) y no en el nadir. Si es plana, el bow tie no puede ser una pieza grande del
paquete, y la ablacion local real (que necesita el recorte nativo) es una confirmacion, no una busqueda.

Las dos preguntas del instrumento:
1. Si el port fallara sobre 40 grados, ¿se veria? Si: la razon por tramo y el recall por tramo se informan aparte, con
   n; K (produccion) va al lado como control positivo de que el tramo SI separa algo (K cae con el cenit, frente M).
2. Si el insumo estuviera vacio, ¿se veria? Si: imprime n por tramo; una pasada sin resultado del port no entra.
Ventana: la del lote 39712862945 (MODIS 2026-03-01 a 2026-10-21 sin el 17 al 20 de octubre), muestra estratificada de
objetivos_portes.json (rama s159-pruebas). Razon = VRP del port (variante fisica) / VRP de MIROVA de la pasada
(`mirova_vrp`, el de la alerta), en las alertas que el port publica (npix > 0).
Uso: python -I razon_por_cenit.py --art D:/vrp-trabajo/temporales/s159_portes/run_39712862945 --objetivos <json>
"""
import argparse
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

TRAMOS = ((0, 25), (25, 40), (40, 50), (50, 90))


def tramo(z):
    for lo, hi in TRAMOS:
        if lo <= z < hi:
            return "%d-%d" % (lo, hi)
    return "?"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--objetivos", required=True)
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.load(open(a.objetivos, encoding="utf-8"))}
    res = []
    for p in sorted(glob.glob(str(Path(a.art) / "s159-portes-MODIS-*" / "resultados_MODIS_*.json"))):
        res += json.load(open(p, encoding="utf-8"))
    print(f"resultados MODIS leidos: {len(res)}; ok: {sum(r.get('estado') == 'ok' for r in res)}")
    por = {}
    for r in res:
        if r.get("estado") != "ok":
            continue
        o = obj[r["id"]]
        if o["lab"] != "pos" or not o.get("mirova_vrp"):
            continue
        z = (r.get("geometria_centro") or {}).get("sensor_zenith", o["z"])
        t = tramo(z)
        f = r["port"]["fisica"]
        d = por.setdefault(t, {"n_alertas": 0, "port_publica": 0, "razon_port": [], "razon_k": [], "z": []})
        d["n_alertas"] += 1
        d["z"].append(z)
        if f.get("npix", 0) > 0 and f.get("vrp_mw"):
            d["port_publica"] += 1
            d["razon_port"].append(f["vrp_mw"] / o["mirova_vrp"])
        if o.get("pub_prod") and o.get("pc_vrp"):
            d["razon_k"].append(o["pc_vrp"] / o["mirova_vrp"])
    print("tramo  n_alertas  port_publica  razon_port_mediana [n, en banda 0,8-1,25]  razon_K_mediana [n]")
    for t in sorted(por, key=lambda x: int(x.split("-")[0])):
        d = por[t]
        rp, rk = d["razon_port"], d["razon_k"]
        banda = sum(0.8 <= x <= 1.25 for x in rp)
        print(f"{t:>6} {d['n_alertas']:>9} {d['port_publica']:>12}  "
              f"{(st.median(rp) if rp else float('nan')):.3f} [{len(rp)}, {banda}]  "
              f"{(st.median(rk) if rk else float('nan')):.3f} [{len(rk)}]  cenit {min(d['z']):.1f} a {max(d['z']):.1f}")
    # intervalo de la mediana por bootstrap de pasadas (2.000 replicas, semilla 162) y tendencia con el cenit
    import random
    rng = random.Random(162)
    print("IC 95 % de la mediana de la razon del port (bootstrap de pasadas):")
    for t in sorted(por, key=lambda x: int(x.split("-")[0])):
        rp = por[t]["razon_port"]
        if len(rp) >= 3:
            meds = sorted(st.median(rng.choice(rp) for _ in rp) for _ in range(2000))
            por[t]["ic95"] = [round(meds[50], 3), round(meds[1949], 3)]
            print(f"  {t:>6}: {por[t]['ic95']}")
    zs, rs = [], []
    for r in res:
        if r.get("estado") != "ok":
            continue
        o = obj[r["id"]]
        f = r["port"]["fisica"]
        if o["lab"] == "pos" and o.get("mirova_vrp") and f.get("npix", 0) > 0 and f.get("vrp_mw"):
            zs.append((r.get("geometria_centro") or {}).get("sensor_zenith", o["z"]))
            rs.append(f["vrp_mw"] / o["mirova_vrp"])
    def rango(x):
        o = sorted(range(len(x)), key=lambda i: x[i])
        rk = [0] * len(x)
        for k, i in enumerate(o):
            rk[i] = k
        return rk
    rz, rr = rango(zs), rango(rs)
    n = len(zs)
    rho = 1 - 6 * sum((a - b) ** 2 for a, b in zip(rz, rr)) / (n * (n * n - 1))
    perm = 0
    for _ in range(5000):
        q = rr[:]
        rng.shuffle(q)
        perm += abs(1 - 6 * sum((a - b) ** 2 for a, b in zip(rz, q)) / (n * (n * n - 1))) >= abs(rho)
    print(f"Spearman razon del port contra cenit: rho {rho:.3f}, n {n}, p por permutacion (5.000) {perm / 5000:.4f}")
    out = {t: {k: (v if not isinstance(v, list) else [round(x, 4) for x in v]) for k, v in d.items()} for t, d in por.items()}
    out["spearman"] = {"rho": round(rho, 4), "n": n, "p_perm": perm / 5000}
    Path(__file__).with_name("razon_por_cenit.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
