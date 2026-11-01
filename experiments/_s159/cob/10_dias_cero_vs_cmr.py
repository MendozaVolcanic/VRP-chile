# -*- coding: utf-8 -*-
"""COB 10 (S159). Los dias con 0 records de una plataforma (de 05_huecos_historicos.txt) contra CMR: granulos L1B de ESA plataforma
en la caja de Chile (lon -76..-66, lat -56..-17) en la ventana nocturna 00:00-10:00 UTC del dia, Standard y NRT (cabecera CMR-Hits).
Si CMR tiene granulos nocturnos y nosotros 0 records => hueco NUESTRO (candidato a falla de produccion). Si CMR tiene 0 => hueco de NASA/CMR.
Control positivo: dias vecinos con records (dia-1 y dia+1) deben tener CMR > 0. Pregunta 2: un 0 de CMR por falla de consulta
se distingue porque los controles vecinos tambien darian 0 (se imprimen). Plataforma -> (std, nrt) segun fetch.py:187-225."""
import sys, io, json, time, datetime, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
BB = "-76,-56,-66,-17"
PL = {"MODIS_TERRA": [("MOD021KM", "6.1"), ("MOD021KM", "6.1NRT")], "MODIS_AQUA": [("MYD021KM", "6.1"), ("MYD021KM", "6.1NRT")],
      "VIIRS_SNPP": [("VNP02IMG", "2"), ("VNP02IMG_NRT", "2")], "VIIRS_NOAA21": [("VJ202IMG", "2.1"), ("VJ202IMG_NRT", "2.1")],
      "VIIRS_NOAA20": [("VJ102IMG", "2.1"), ("VJ102IMG_NRT", "2.1")]}
def d(s): return datetime.date.fromisoformat(s)
CASOS = {"MODIS_TERRA": ["2025-06-03", "2025-07-15", "2026-02-22", "2026-03-27", "2026-06-02", "2026-09-28", "2026-10-02", "2026-10-10"],
         "MODIS_AQUA": ["2025-11-16", "2026-07-21"], "VIIRS_NOAA21": ["2025-09-18", "2026-10-13"],
         "VIIRS_SNPP": ["2025-11-12", "2026-03-10", "2026-03-11", "2026-03-12", "2026-04-28", "2026-04-29", "2026-04-30", "2026-06-01", "2026-06-02",
                        "2026-07-11", "2026-07-12", "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-10-13", "2026-10-20"]}
last = [0.0]
def hits(sn, ver, dia):
    t0 = f"{dia}T00:00:00Z"; t1 = f"{dia}T10:00:00Z"
    p = {"short_name": sn, "version": ver, "temporal": f"{t0},{t1}", "bounding_box": BB, "page_size": "1"}
    w = 1 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    for i in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(BASE + "?" + urllib.parse.urlencode(p), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90)
            n = int(r.headers["CMR-Hits"]); break
        except Exception:
            if i == 3: raise
            time.sleep(3 * (i + 1))
    last[0] = time.time(); return n
print("plataforma     dia         CMR std  CMR nrt | vecino dia-1 (std,nrt) | vecino dia+1 (std,nrt)   [granulos L1B nocturnos 00-10 UTC, caja Chile]")
for pl, dias in CASOS.items():
    for dia in dias:
        a = [hits(sn, v, dia) for sn, v in PL[pl]]
        dm = (d(dia) - datetime.timedelta(days=1)).isoformat(); dp = (d(dia) + datetime.timedelta(days=1)).isoformat()
        b = [hits(sn, v, dm) for sn, v in PL[pl]]; c = [hits(sn, v, dp) for sn, v in PL[pl]]
        veredicto = "NASA/CMR sin granulos (no es nuestro)" if sum(a) == 0 else "CMR TIENE granulos: hueco NUESTRO"
        print(f"{pl:13s} {dia}  {a[0]:5d} {a[1]:7d} | {b[0]:3d},{b[1]:3d} | {c[0]:3d},{c[1]:3d}  -> {veredicto}", flush=True)
