# -*- coding: utf-8 -*-
"""S168, candado de MOD-D fase 4, §4: ¿LAADS sirve HOY cada L1B y cada MxD03 de las pasadas del tramo E?

POR QUÉ. CMR puede listar entradas que dan 404 al bajarlas (commit 798400dec, S159) y una fila del listado cambió en una
hora (VF4-07). Por eso el pre-registro define «sirve» como una petición HEAD a la URL de descarga del L1B y a la de su
MxD03 que responde 200, para cada volcán y pasada nocturna del día. Un día con un solo archivo sin 200 se excluye
entero (poblacion_f4.py --head) y sus pasadas de MIROVA quedan sin pareja (N-04).

QUÉ HACE. Lee `e_candidatas` de poblacion_f4.json (todas las pasadas de E con sus URL, antes de excluir nada), hace
UNA petición HEAD por URL distinta, siguiendo redirecciones, SIN reintentos (un reintento contra la cuenta puede
bloquearla, A71; un fallo transitorio excluye el día, que es el lado conservador), y escribe head_e.json.

Modo de autenticación (uno de los dos, explícito):
  --publico     sin credenciales. Medido el 2026-10-29 21:05 UTC: la URL de LAADS en la nube
                (data.laadsdaac.earthdatacloud.nasa.gov) responde 303 a una URL firmada de CloudFront y ésta 200 con el
                tamaño del archivo, sin pedir autenticación. Si algún día pide autenticación (401, 403, o la redirección
                va a urs.earthdata.nasa.gov) el status queda distinto de 200 y el control positivo falla: hay que
                correrlo en el workflow con token.
  --con-token   envía «Authorization: Bearer $EARTHDATA_TOKEN» (la variable del NRT); si viene vacía sale al
                instante, sin hacer ninguna petición. Nunca usuario y clave (A71).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si LAADS no sirviera un archivo, ¿se vería? Sí: control negativo, un nombre inexistente bajo el mismo prefijo, tiene
   que dar distinto de 200. Si diera 200, el HEAD no mide existencia y la comprobación no vale.
2. Si el HEAD estuviera roto o pidiera credenciales, ¿se vería? Sí: control positivo, un L1B del censo que el censo
   bajó, tiene que dar 200. Si no, la comprobación no vale (poblacion_f4.py se niega a aplicarla).

Uso: python head_e.py (--publico | --con-token) [--poblacion poblacion_f4.json] [--salida head_e.json]
     [--tramo C --salida head_c.json]   (informa: los archivos del censo que LAADS sigue sirviendo, para la identidad)
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
POSITIVO = ("https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/MOD021KM/"
            "MOD021KM.A2026060.0135.061.2026060131721.hdf")          # L1B del censo (Chaitén y otros, 2026-03-01 01:35)
NEGATIVO = ("https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/MOD021KM/"
            "MOD021KM.A2026060.0135.061.2026060000000.hdf")          # mismo gránulo, fecha de producción inexistente
TIMEOUT_S = 60


def head(url, token):
    """Una sola petición HEAD (con sus redirecciones). Devuelve status final, host final sin la consulta, tamaño."""
    h = {"Authorization": f"Bearer {token}"} if token else {}
    t0 = time.time()
    try:
        r = requests.head(url, headers=h, allow_redirects=True, timeout=TIMEOUT_S)
        final = r.url.split("?")[0]
        return {"status": r.status_code, "saltos": [x.status_code for x in r.history],
                "host_final": final.split("/")[2] if "//" in final else final,
                "pide_urs": any("urs.earthdata.nasa.gov" in (x.headers.get("location") or "") for x in r.history)
                or "urs.earthdata.nasa.gov" in final,
                "bytes": int(r.headers["content-length"]) if r.headers.get("content-length", "").isdigit() else None,
                "error": None, "s": round(time.time() - t0, 2)}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "saltos": [], "host_final": None, "pide_urs": False, "bytes": None,
                "error": f"{type(e).__name__}: {e}"[:200], "s": round(time.time() - t0, 2)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--publico", action="store_true")
    m.add_argument("--con-token", action="store_true")
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion_f4.json"))
    ap.add_argument("--tramo", default="E", choices=("E", "C"))
    ap.add_argument("--salida", default=None)
    ap.add_argument("--hilos", type=int, default=4)
    a = ap.parse_args()
    token = None
    if a.con_token:
        token = os.environ.get("EARTHDATA_TOKEN", "").strip()
        if not token:
            sys.exit("EARTHDATA_TOKEN vacío: sin token no se hace ninguna petición (A71)")
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    pas = pob["e_candidatas"] if a.tramo == "E" else [p for p in pob["pasadas"] if p["tramo"] == "C"]
    urls = sorted({u for p in pas for u in (p.get("url_l1b"), p.get("url_geo")) if u})
    sin_url = [(p["vol"], p["dt"]) for p in pas if not p.get("url_l1b") or not p.get("url_geo")]
    print(f"head_e.py tramo {a.tramo}: {len(pas)} pasadas, {len(urls)} URL distintas, {len(sin_url)} pasadas sin URL; "
          f"modo {'token' if token else 'publico'}", flush=True)
    t0 = time.time()
    ctl = {}
    for nom, u, quiere200 in (("positivo", POSITIVO, True), ("negativo", NEGATIVO, False)):
        r = head(u, token)
        ok = (r["status"] == 200) if quiere200 else (r["status"] is not None and r["status"] != 200)
        ctl[nom] = {"estado": "OK" if ok else "FALLA", "url": u, **r}
        print(f"control {nom}: {r['status']} saltos {r['saltos']} host {r['host_final']} bytes {r['bytes']} "
              f"pide_urs {r['pide_urs']} -> {ctl[nom]['estado']}", flush=True)
    res = {}
    with ThreadPoolExecutor(max_workers=a.hilos) as ex:
        for u, r in zip(urls, ex.map(lambda x: head(x, token), urls)):
            res[u] = r
    st = collections.Counter(r["status"] for r in res.values())
    print(f"status: {dict(st)} | pide_urs {sum(r['pide_urs'] for r in res.values())} | {time.time() - t0:.0f} s")
    dias = collections.defaultdict(lambda: {"pasadas": 0, "fallan": []})
    for p in pas:
        d = dias[p["dt"][:10]]
        d["pasadas"] += 1
        for lado, u in (("L1B", p.get("url_l1b")), ("MxD03", p.get("url_geo"))):
            s = res[u]["status"] if u else None
            if s != 200:
                d["fallan"].append({"vol": p["vol"], "dt": p["dt"], "archivo": lado, "url": u, "status": s})
    for d, v in sorted(dias.items()):
        print(f"  {d}: {v['pasadas']} pasadas, {len(v['fallan'])} archivos sin 200 -> "
              f"{'SIRVE' if not v['fallan'] else 'NO SIRVE'}", flush=True)
    malos = [(u, r["status"], r["error"]) for u, r in res.items() if r["status"] != 200]
    for x in malos[:30]:
        print("  sin 200:", x)
    out = {"tramo": a.tramo, "modo": "token" if token else "publico",
           "hora_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
           "poblacion": a.poblacion, "controles": ctl, "urls": res,
           "dias": {d: {"pasadas": v["pasadas"], "sirve": not v["fallan"], "fallan": v["fallan"]}
                    for d, v in sorted(dias.items())},
           "n_urls": len(urls), "n_200": st.get(200, 0)}
    salida = a.salida or str(AQUI / ("head_e.json" if a.tramo == "E" else "head_c.json"))
    Path(salida).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print("escrito", salida)
    sys.exit(0 if all(c["estado"] == "OK" for c in ctl.values()) else 2)


if __name__ == "__main__":
    main()
