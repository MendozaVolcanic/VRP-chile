"""S157: identidad de granulos contra el CMR REAL: ventana contra consulta por dia, producto por producto.

POR QUE. Las pruebas de tests/test_busqueda_ventana_s157.py usan un CMR simulado que aplica la regla de traslape que
nosotros creemos que aplica CMR. Si CMR aplicara otra (bordes, orden, versiones), las pruebas pasarian igual. Este
script pregunta al CMR de verdad: para cada uno de los 16 productos y cada dia, la lista de GranuleUR (y su orden)
que devuelve fetch.search_granules por el camino de hoy (una consulta por dia) contra la que devuelve con la
ventana configurada. La busqueda de CMR es publica: no autentica ni toca credenciales.

Cada consulta por dia se reintenta hasta 4 veces (CMR anda lento); si igual falla, ese dia queda SIN DATO y no se
cuenta como coincidencia ni como diferencia.

Uso:
  python experiments/_s157_busqueda_ventana/identidad_cmr.py --volcan NevadosDeChillan --inicio 2026-07-18 \
      --fin 2026-07-27 --salida experiments/_s157_busqueda_ventana/identidad_chillan.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import yaml  # noqa: E402

from pipeline import fetch  # noqa: E402

PLATAFORMAS = [
    ("MODIS_TERRA", "MODIS_TERRA_L1B", "MODIS_TERRA_GEO"), ("MODIS_AQUA", "MODIS_AQUA_L1B", "MODIS_AQUA_GEO"),
    ("VIIRS_SNPP", "VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"), ("VIIRS_NOAA20", "VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
    ("VIIRS_NOAA21", "VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
    ("VIIRS_SNPP_750", "VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
    ("VIIRS_NOAA20_750", "VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
    ("VIIRS_NOAA21_750", "VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO"),
]


def _urs(lista):
    return [g["umm"]["GranuleUR"] for g in lista]


def _por_dia(producto, lat, lon, r, d):
    for k in range(4):
        try:
            return _urs(fetch.search_granules(producto, lat, lon, r, d))
        except Exception as e:  # noqa: BLE001 - CMR lento o caido: se reintenta y si no, SIN DATO
            print(f"  reintento {k} {producto} {d:%Y-%m-%d}: {type(e).__name__}: {str(e)[:80]}", flush=True)
            time.sleep(15 * (k + 1))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcan", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))
    v = next(x for x in cfg["volcanoes"] if x["name"] == a.volcan)
    lat, lon, r = v["lat"], v["lon"], v.get("radius_km", 30)
    d, fin = datetime.strptime(a.inicio, "%Y-%m-%d"), datetime.strptime(a.fin, "%Y-%m-%d")
    dias = []
    while d <= fin:
        dias.append(d)
        d += timedelta(days=1)
    # el cortacircuito convertiria un timeout en [] y eso pareceria una diferencia: aca se reintenta
    fetch.ENABLE_CMR_SEARCH_BREAKER = False
    fetch._VENTANA_ESPERAS_S = [0, 20, 60]
    productos = [p for _, l1b, geo in PLATAFORMAS for p in (l1b, geo)]
    out = {"volcan": a.volcan, "inicio": a.inicio, "fin": a.fin, "productos": {}}
    t0 = time.time()
    tot = {"dias_comparados": 0, "iguales": 0, "distintos": 0, "sin_dato": 0, "dias_por_dia_en_ventana": 0,
           "granulos": 0, "consultas_ventana": 0, "consultas_por_dia": 0}
    orig_search = fetch.earthaccess.search_data

    def contar(*args, **kw):
        t = kw.get("temporal")
        if t and t[0] != t[1]:
            tot["consultas_ventana"] += 1
        else:
            tot["consultas_por_dia"] += 1
        return orig_search(*args, **kw)

    fetch.earthaccess.search_data = contar
    for producto in productos:
        fetch.reiniciar_ventana()
        hoy = {x.strftime("%Y-%m-%d"): _por_dia(producto, lat, lon, r, x) for x in dias}
        fetch.reiniciar_ventana()
        fetch.configurar_ventana(dias)
        ven = {}
        for x in dias:
            ven[x.strftime("%Y-%m-%d")] = _por_dia(producto, lat, lon, r, x)
        usada = bool(fetch._VENTANA_CACHE) and not fetch._VENTANA_APAGADA
        nulos = sum(1 for por in fetch._VENTANA_CACHE.values() for vv in por.values() if vv is None)
        tot["dias_por_dia_en_ventana"] += nulos
        dif = []
        for k in hoy:
            if hoy[k] is None or ven[k] is None:
                tot["sin_dato"] += 1
                continue
            tot["dias_comparados"] += 1
            tot["granulos"] += len(hoy[k])
            if hoy[k] == ven[k]:
                tot["iguales"] += 1
            else:
                tot["distintos"] += 1
                dif.append({"dia": k, "por_dia": hoy[k], "ventana": ven[k]})
        out["productos"][producto] = {"ventana_usada": usada, "dias_por_dia_dentro_de_la_ventana": nulos,
                                      "diferencias": dif, "granulos_por_dia": {k: hoy[k] for k in hoy}}
        print(f"{producto}: ventana_usada={usada} diferencias={len(dif)} "
              f"granulos={sum(len(x or []) for x in hoy.values())} t={time.time()-t0:.0f}s", flush=True)
    out["totales"] = tot
    Path(a.salida).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(tot))
    return 0 if tot["distintos"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
