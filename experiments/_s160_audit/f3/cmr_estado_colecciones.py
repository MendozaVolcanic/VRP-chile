"""F3 (S160): estado en CMR de cada colección que pide pipeline/fetch.py PRODUCTS (sin autenticación).

Para cada short_name que pide el pipeline: qué VERSIONES existen hoy en CMR (sin filtrar por versión),
CollectionProgress y EndingDateTime de la colección, y cuántos gránulos sobre Chile en las últimas 48 h
en la versión que el pipeline pide. Así se ve (a) si una colección que pedimos ya tiene fecha de fin,
(b) si existe una versión más nueva que el pipeline no pide (NOAA-21 sólo pide «2.1»), (c) si hay
Colección 7 NRT de MODIS.

Pregunta 1: una colección cesada tendría EndingDateTime, CollectionProgress distinto de ACTIVE o 0
gránulos recientes. Pregunta 2: un error de red imprime ERROR en la fila, no 0. Control positivo:
MYD021KM_NRT (nombre inexistente, S133) debe dar 0 colecciones; VJ202IMG_NRT 2.1 debe dar gránulos.
Presupuesto: menos de 40 consultas (tope 150). Ventana: gránulos con inicio en las últimas 48 h a la
hora de la consulta; bbox -76,-46,-66,-17.

Uso: python -I cmr_estado_colecciones.py > salida.txt
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CMR = "https://cmr.earthdata.nasa.gov/search/"
BBOX = "-76,-46,-66,-17"
AHORA = datetime.now(timezone.utc)
DESDE = AHORA - timedelta(hours=48)
N = 0


def get(path, params, headers_wanted=()):
    global N
    N += 1
    url = CMR + path + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": "vrp-chile-f3-audit", "Client-Id": "vrp-chile-f3"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        hdr = {h: r.headers.get(h) for h in headers_wanted}
    return json.loads(body) if body else {}, hdr


# (short_name, version que pide el pipeline, plataforma)
PEDIDAS = [
    ("MOD021KM", ["6.1", "6.1NRT"], "Terra"), ("MOD03", ["6.1", "6.1NRT"], "Terra"),
    ("MYD021KM", ["6.1", "6.1NRT"], "Aqua"), ("MYD03", ["6.1", "6.1NRT"], "Aqua"),
    ("VNP02IMG", ["2"], "Suomi NPP"), ("VNP02IMG_NRT", ["2"], "Suomi NPP"),
    ("VNP02MOD", ["2"], "Suomi NPP"), ("VNP02MOD_NRT", ["2"], "Suomi NPP"),
    ("VJ102IMG", ["2.1", "2", "1"], "NOAA-20"), ("VJ102IMG_NRT", ["2.1", "2"], "NOAA-20"),
    ("VJ102MOD", ["2.1", "2", "1"], "NOAA-20"), ("VJ102MOD_NRT", ["2.1", "2"], "NOAA-20"),
    ("VJ202IMG", ["2.1"], "NOAA-21"), ("VJ202IMG_NRT", ["2.1"], "NOAA-21"),
    ("VJ202MOD", ["2.1"], "NOAA-21"), ("VJ202MOD_NRT", ["2.1"], "NOAA-21"),
    ("MYD021KM_NRT", ["61"], "control: nombre inexistente (S133)"),
]
print(f"hora de consulta {AHORA.isoformat(timespec='seconds')}; ventana gránulos {DESDE.isoformat(timespec='seconds')} a ahora; bbox {BBOX}")
print("short_name | plataforma | versiones en CMR (progress, fin) | versión pedida -> gránulos 48 h")
for sn, vers, plat in PEDIDAS:
    try:
        col, _ = get("collections.umm_json", {"short_name": sn, "page_size": 20})
        items = col.get("items", [])
        desc = []
        for it in items:
            u = it["umm"]
            v = u.get("Version")
            prog = u.get("CollectionProgress")
            fin = None
            for te in u.get("TemporalExtents", []):
                for rd in te.get("RangeDateTimes", []):
                    fin = rd.get("EndingDateTime") or fin
                if te.get("EndsAtPresentFlag"):
                    fin = "presente"
            prov = it.get("meta", {}).get("provider-id")
            desc.append(f"v{v}@{prov}({prog},{fin})")
        gr = []
        for v in vers:
            try:
                _, h = get("granules.json", {"short_name": sn, "version": v, "bounding_box": BBOX,
                                             "temporal": f"{DESDE.isoformat(timespec='seconds')},{AHORA.isoformat(timespec='seconds')}",
                                             "page_size": 0}, headers_wanted=("CMR-Hits",))
                gr.append(f"v{v}:{h.get('CMR-Hits')}")
            except Exception as e:
                gr.append(f"v{v}:ERROR {type(e).__name__}")
        print(f"{sn} | {plat} | {len(items)} col: {' '.join(desc) or '-'} | {' '.join(gr)}")
    except Exception as e:
        print(f"{sn} | {plat} | ERROR {type(e).__name__}: {str(e)[:80]}")
print(f"consultas a CMR: {N}")
