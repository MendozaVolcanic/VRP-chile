# -*- coding: utf-8 -*-
"""COB 09 (S159). (1) Limites horarios del hueco de CMR de oct-2026 (caja de Chile, VNP02IMG std+NRT y MOD021KM): primer y ultimo
granulo servido por dia. (2) Reproduccion de VB-1 sin caja (global) para 2026-10-20: MOD021KM 6.1NRT vs MOD03 6.1NRT y
VNP02MOD_NRT vs VNP03MOD_NRT. Pregunta 1: si el hueco no existiera, la lista de inicios no tendria saltos > 2 h entre
2026-10-17 y 2026-10-21; los tiene (control positivo es el propio salto). Pregunta 2: una lista vacia se imprime como vacia.
Hora de consulta anotada en el encabezado; CMR cambia con el tiempo."""
import sys, io, json, time, datetime, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
print("consulta:", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
def q(sn, ver, t0, t1, bbox=None, ps=2000):
    p = {"short_name": sn, "version": ver, "temporal": f"{t0},{t1}", "page_size": str(ps), "sort_key": "start_date"}
    if bbox: p["bounding_box"] = bbox
    time.sleep(1)
    r = urllib.request.urlopen(urllib.request.Request(BASE + "?" + urllib.parse.urlencode(p), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90)
    return int(r.headers["CMR-Hits"]), [e["time_start"][:16] for e in json.loads(r.read())["feed"]["entry"]]
BB = "-76,-56,-66,-17"
for sn, ver in (("VNP02IMG", "2"), ("VNP02IMG_NRT", "2"), ("MOD021KM", "6.1"), ("MOD021KM", "6.1NRT"), ("VJ102IMG", "2.1"), ("VJ102IMG_NRT", "2.1")):
    n, ts = q(sn, ver, "2026-10-16T00:00:00Z", "2026-10-21T18:00:00Z", BB)
    print(f"\n{sn} v{ver}: {n} granulos 2026-10-16..21 (caja Chile)")
    ts = sorted(ts); prev = None; saltos = []
    for t in ts:
        d = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M")
        if prev and (d - prev).total_seconds() > 3 * 3600:
            saltos.append((prev.strftime("%m-%d %H:%M"), d.strftime("%m-%d %H:%M"), round((d - prev).total_seconds() / 3600, 1)))
        prev = d
    print("  primero:", ts[0] if ts else None, "| ultimo:", ts[-1] if ts else None)
    print("  saltos > 3 h entre granulos consecutivos (desde, hasta, horas):", saltos)
print("\n== VB-1 global (sin caja), 2026-10-20 ==")
for a, av, b, bv in (("MOD021KM", "6.1NRT", "MOD03", "6.1NRT"), ("VNP02MOD_NRT", "2", "VNP03MOD_NRT", "2"), ("MOD021KM", "6.1", "MOD03", "6.1"),
                     ("VNP02IMG_NRT", "2", "VNP03IMG_NRT", "2"), ("VJ102IMG_NRT", "2.1", "VJ103IMG_NRT", "2.1")):
    na, _ = q(a, av, "2026-10-20T00:00:00Z", "2026-10-20T23:59:59Z", None, 1)
    nb, _ = q(b, bv, "2026-10-20T00:00:00Z", "2026-10-20T23:59:59Z", None, 1)
    print(f"  {a} v{av}: {na}  |  {b} v{bv}: {nb}  | L1B - GEO = {na-nb:+d}")
