# -*- coding: utf-8 -*-
"""S159, censo del oráculo, estrato aparte «reprocesadas del 2026-10-12» (adenda del pre-registro, §8).

POR QUÉ. NASA reprocesó el 2026-10-19 los gránulos de SNPP y NOAA-21 del 12 (experiments/_s159/laads_rescate/INFORME.md
H1): LAADS borró los originales, pero CMR sigue entregando la entrada vieja, cuyo enlace da 404. Por eso el censo (y
el frente N) dejan SIN DATO las pasadas de esos gránulos, entre ellas la protegida de Chillán 05:18. Aquí se bajan los
archivos NUEVOS listando el directorio del día en LAADS y tomando el que tiene el mismo AYYYYDDD.HHMM, con el
EARTHDATA_TOKEN como Bearer (A71: nunca el par usuario y clave). Después se procesan con el mismo probe del censo.

Lo que NO vale aquí: el control «K = producción», porque producción procesó el archivo original y éste es otro.
Pregunta 1: si la bajada trajera el archivo equivocado, el volcán quedaría fuera o el tag no calzaría (se verifica el
tag del nombre). Pregunta 2: si no baja, la pasada queda con estado de error, nunca como «no publica».
Uso: python probe_rescate.py --objetivos objetivos.json --out out
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import probe_censo as PC  # noqa: E402

PN = PC.PN
BASE = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData"
COL = {"VNP": "5200", "VJ1": "5201", "VJ2": "5201"}
GRANULOS = ("VJ202MOD.A2026285.0512", "VJ202MOD.A2026285.0518", "VNP02MOD.A2026285.0548", "VNP02MOD.A2026285.0554")


def _get(url, **kw):
    h = {"Authorization": "Bearer " + os.environ["EARTHDATA_TOKEN"].strip()}
    for n in range(4):
        try:
            r = requests.get(url, headers=h, timeout=120, **kw)
            if r.status_code == 200:
                return r
            print(f"   GET {url} -> {r.status_code}", flush=True)
        except requests.RequestException as e:  # ReadTimeout y cortes: reintentar
            print(f"   GET {url} fallo {type(e).__name__}", flush=True)
        time.sleep(15 * (n + 1))
    return None


def listar(pref, tipo, anio, dia):
    url = f"{BASE}/{COL[pref]}/{pref}{tipo}MOD/{anio}/{dia}.json"
    r = _get(url)
    if r is None:
        return []
    d = r.json()
    filas = d.get("content", d) if isinstance(d, dict) else d
    return [f["name"] for f in filas if isinstance(f, dict) and "name" in f]


def bajar_laads(nombre_viejo, destino):
    """nombre_viejo: el del record (CMR). Devuelve (l1b, geo) nuevos o (None, motivo)."""
    pref, tag = nombre_viejo[:3], ".".join(nombre_viejo.split(".")[1:3])   # A2026285.0518
    anio, dia = tag[1:5], tag[5:8]
    destino.mkdir(parents=True, exist_ok=True)
    out = []
    for tipo in ("02", "03"):
        nom = [n for n in listar(pref, tipo, anio, dia) if f".{tag}." in n and n.endswith(".nc")]
        if len(nom) != 1:
            return None, f"laads_{tipo}_candidatos_{len(nom)}"
        url = f"{BASE}/{COL[pref]}/{pref}{tipo}MOD/{anio}/{dia}/{nom[0]}"
        r = _get(url, stream=False)
        if r is None:
            return None, f"laads_{tipo}_descarga_fallo"
        p = destino / nom[0]
        p.write_bytes(r.content)
        print(f"   bajado {nom[0]} ({len(r.content) / 1e6:.1f} MB)", flush=True)
        out.append(p)
    return (out[0], out[1]), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos.json"))
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    PN.prueba_sin_red()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 1
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    destino = Path(os.environ.get("VRP_TMP_DIR", "/tmp/vrp_tmp")) / "granulos"
    objs = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    grupos = {}
    for o in objs:
        if o["granule"] and o["granule"].startswith(GRANULOS):
            grupos.setdefault(o["granule"], []).append(o)
    print("granulos:", {k: len(v) for k, v in grupos.items()}, flush=True)
    PN.bajar_con_reintentos = lambda nombre, dest, intentos=3: bajar_laads(nombre, dest)   # sólo la bajada cambia
    resultados, faltan = [], 0
    for k in sorted(grupos):
        print(f"== {k} ({len(grupos[k])} pasadas)", flush=True)
        rs = PC.procesar_granulo(grupos[k], destino)
        for r in rs:
            r["rescate"] = True
            if r.get("estado") not in ("ok", "volcan_fuera_del_granulo"):
                faltan += 1
            od = (r.get("oraculo") or {}).get("geo_linear", {})
            osn = (r.get("oraculo") or {}).get("geo_linear_anillo_sensible", {})
            kpc = ((((r.get("brazos") or {}).get("K") or {}).get("record") or {}).get("primary_cluster") or {}).get("vrp_mw")
            print(f"   {r['id']} {r['volcan']} {r['hora_utc']} estado={r.get('estado')} archivos={r.get('archivos')} "
                  f"O={od.get('npix')}px {od.get('vrp_mw')} Os={osn.get('npix')}px {osn.get('vrp_mw')} | K pc {kpc}",
                  flush=True)
            resultados.append(r)
    (outdir / "resultados_rescate.json").write_text(json.dumps(resultados, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {len(resultados)}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
