# -*- coding: utf-8 -*-
"""Ayudante de consulta publica a CMR (sin credenciales; A71). Pausa de 1 s entre consultas, cache en disco."""
from __future__ import annotations
import json, time, hashlib, urllib.parse, urllib.request
from pathlib import Path

CACHE = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob\_cache_cmr2")
CACHE.mkdir(exist_ok=True)
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
_last = [0.0]

# Short names y versiones: copia de pipeline/fetch.py:187-225 (PRODUCTS), leidos a mano el 2026-10-21.
PRODUCTOS = {
    # sensor nuestro -> (L1B std [(sn, versiones)], L1B nrt, GEO std, GEO nrt)
    "MODIS_TERRA":      ([("MOD021KM", ["6.1"])], [("MOD021KM", ["6.1NRT"])], [("MOD03", ["6.1"])], [("MOD03", ["6.1NRT"])]),
    "MODIS_AQUA":       ([("MYD021KM", ["6.1"])], [("MYD021KM", ["6.1NRT"])], [("MYD03", ["6.1"])], [("MYD03", ["6.1NRT"])]),
    "VIIRS_SNPP":       ([("VNP02IMG", ["2"])], [("VNP02IMG_NRT", ["2"])], [("VNP03IMG", ["2"])], [("VNP03IMG_NRT", ["2"])]),
    "VIIRS_NOAA20":     ([("VJ102IMG", ["2.1", "2", "1"])], [("VJ102IMG_NRT", ["2.1", "2"])], [("VJ103IMG", ["2.1", "2", "1"])], [("VJ103IMG_NRT", ["2.1", "2"])]),
    "VIIRS_NOAA21":     ([("VJ202IMG", ["2.1"])], [("VJ202IMG_NRT", ["2.1"])], [("VJ203IMG", ["2.1"])], [("VJ203IMG_NRT", ["2.1"])]),
    "VIIRS_SNPP_750":   ([("VNP02MOD", ["2"])], [("VNP02MOD_NRT", ["2"])], [("VNP03MOD", ["2"])], [("VNP03MOD_NRT", ["2"])]),
    "VIIRS_NOAA20_750": ([("VJ102MOD", ["2.1", "2", "1"])], [("VJ102MOD_NRT", ["2.1", "2"])], [("VJ103MOD", ["2.1", "2", "1"])], [("VJ103MOD_NRT", ["2.1", "2"])]),
    "VIIRS_NOAA21_750": ([("VJ202MOD", ["2.1"])], [("VJ202MOD_NRT", ["2.1"])], [("VJ203MOD", ["2.1"])], [("VJ203MOD_NRT", ["2.1"])]),
}


def _pagina(short_name, version, t0, t1, bbox, page_size, page_num):
    q = {"short_name": short_name, "temporal": f"{t0},{t1}", "page_size": str(page_size), "page_num": str(page_num),
         "sort_key": "start_date"}
    if version:
        q["version"] = version
    if bbox:
        q["bounding_box"] = ",".join(f"{x:.5f}" for x in bbox)
    url = BASE + "?" + urllib.parse.urlencode(q)
    h = hashlib.sha1(url.encode()).hexdigest()
    f = CACHE / f"{h}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))["g"]
    espera = 1.0 - (time.time() - _last[0])
    if espera > 0:
        time.sleep(espera)
    for intento in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90) as r:
                d = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:  # noqa: BLE001
            if intento == 3:
                raise
            time.sleep(3 * (intento + 1))
    _last[0] = time.time()
    g = [dict(pid=e.get("producer_granule_id"), t0=e.get("time_start"), t1=e.get("time_end"), dn=e.get("day_night_flag"),
              cid=e.get("collection_concept_id"), upd=e.get("updated"), id=e.get("id")) for e in d["feed"]["entry"]]
    f.write_text(json.dumps({"url": url, "g": g}), encoding="utf-8")
    return g


def consulta(short_name, version, t0, t1, bbox, page_size=2000):
    """t0/t1 ISO 'YYYY-MM-DDTHH:MM:SSZ'. bbox = (lon_min, lat_min, lon_max, lat_max) como en earthaccess/CMR. Pagina."""
    out, n = [], 1
    while True:
        g = _pagina(short_name, version, t0, t1, bbox, page_size, n)
        out += g
        if len(g) < page_size:
            return out
        n += 1


def catalogo(sensor, kind, t0, t1, bbox, nrt=None):
    """Todos los granulos (std y nrt, todas las versiones) de un producto en [t0,t1] sobre bbox.
    Devuelve dict inicio(ISO minuto) -> lista de (pid, tipo, short_name, version, dn)."""
    std_l1b, nrt_l1b, std_geo, nrt_geo = PRODUCTOS[sensor]
    pasos = []
    if kind == "l1b":
        pasos += [("std", sn, v) for sn, vs in std_l1b for v in vs]
        if nrt is not False:
            pasos += [("nrt", sn, v) for sn, vs in nrt_l1b for v in vs]
    else:
        pasos += [("std", sn, v) for sn, vs in std_geo for v in vs]
        if nrt is not False:
            pasos += [("nrt", sn, v) for sn, vs in nrt_geo for v in vs]
    out = {}
    for tipo, sn, v in pasos:
        for g in consulta(sn, v, t0, t1, bbox):
            k = g["t0"][:16]
            out.setdefault(k, []).append((g["pid"], tipo, sn, v, g["dn"], g["upd"]))
    return out
