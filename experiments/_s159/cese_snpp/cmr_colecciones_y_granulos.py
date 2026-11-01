"""S159 cese SNPP: estado de colecciones y granulos en CMR publico (sin credenciales).

Pregunta 1 del instrumento: si una coleccion hubiera dejado de producir, el ultimo granulo
sobre Chile seria viejo y el conteo de los ultimos dias daria 0; la medicion lo ve.
Pregunta 2: si CMR no respondiera, el script imprime ERROR, no 0 (SIN DATO != 0).
Control positivo: VJ102IMG_NRT y VJ202IMG_NRT (plataformas vivas) deben dar > 0.
Control negativo del instrumento: una coleccion inexistente (MYD021KM_NRT v61, el error
de S133) debe dar 0 colecciones, que es lo que el pipeline ve como "no hay dato".
Ventana: granulos con inicio en [hoy-3 d, hoy] UTC, bbox Chile volcanico -76,-46,-66,-17.
"""
import json, time, urllib.request, urllib.parse, sys, io
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CMR = "https://cmr.earthdata.nasa.gov/search"
BBOX = "-76,-46,-66,-17"
HOY = datetime.now(timezone.utc)
INI = (HOY - timedelta(days=3)).strftime("%Y-%m-%dT00:00:00Z")
FIN = HOY.strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "vrp-chile-audit-s159"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.headers, json.loads(r.read().decode())


def colecciones(short_name):
    url = f"{CMR}/collections.umm_json?short_name={urllib.parse.quote(short_name)}&page_size=50"
    _, d = get(url)
    out = []
    for it in d.get("items", []):
        u = it["umm"]
        te = (u.get("TemporalExtents") or [{}])[0].get("RangeDateTimes") or [{}]
        out.append({"version": u.get("Version"), "progress": u.get("CollectionProgress"),
                    "fin_temporal": te[-1].get("EndingDateTime"),
                    "concept": it["meta"]["concept-id"], "proveedor": it["meta"]["provider-id"]})
    return out


def granulos(short_name, version):
    q = {"short_name": short_name, "version": version, "bounding_box": BBOX,
         "temporal": f"{INI},{FIN}", "page_size": 1, "sort_key": "-start_date"}
    h, d = get(f"{CMR}/granules.json?" + urllib.parse.urlencode(q))
    e = d["feed"]["entry"]
    return int(h.get("CMR-Hits", -1)), (e[0]["time_start"] if e else None)


NOMBRES = ["VNP02IMG", "VNP02IMG_NRT", "VNP03IMG_NRT", "VNP02MOD_NRT", "VNP03MOD_NRT",
           "VJ102IMG_NRT", "VJ202IMG_NRT", "VJ202MOD_NRT", "VJ102MOD_NRT",
           "MOD021KM", "MYD021KM", "MOD03", "MYD03", "MYD021KM_NRT"]

print(f"hora servidor local UTC {HOY:%Y-%m-%d %H:%M}Z ; ventana granulos {INI}..{FIN}")
for n in NOMBRES:
    try:
        cols = colecciones(n)
    except Exception as e:
        print(f"{n}: ERROR colecciones {type(e).__name__}: {e}")
        continue
    if not cols:
        print(f"{n}: 0 colecciones (no existe en CMR)")
    for c in cols:
        try:
            hits, ult = granulos(n, c["version"])
        except Exception as e:
            hits, ult = f"ERROR {type(e).__name__}", None
        print(f"{n} v{c['version']} [{c['proveedor']}] progress={c['progress']} fin_temporal={c['fin_temporal']}"
              f" | granulos Chile 3 d={hits} ultimo={ult}")
        time.sleep(1.5)
    time.sleep(1.5)
