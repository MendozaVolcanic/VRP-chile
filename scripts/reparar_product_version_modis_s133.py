# -*- coding: utf-8 -*-
"""
S133 - Reetiqueta como "nrt" los records MODIS que entraron por LANCE y se guardaron
como "standard" por el bug del detector.

FICHA SDA - no toca ninguna magnitud ni ninguna clasificacion: sólo corrige el campo de
PROCEDENCIA del dato. No altera la deteccion.

POR QUE IMPORTA UNA ETIQUETA. `store.py` reemplaza un record por su version definitiva
SOLO cuando el guardado dice "nrt" y el nuevo dice "standard" (append_record, la rama
`is_upgrade`). Un granule de LANCE mal etiquetado "standard" nunca dispara esa condicion:
se queda con la calibracion provisional para siempre, y en silencio. Reprocesar NO lo
arregla, porque el reproceso produciria "nrt" contra un "standard" ya guardado y la rama
de upgrade no aplica en ese sentido.

QUE HACE, y como evita adivinar. Para cada record MODIS sospechoso pregunta al catalogo
de NASA (CMR) si existe el granule ESTANDAR de esa pasada. Si no existe, el record solo
pudo venir de LANCE y se reetiqueta. Si existe, se deja como esta. No se infiere por
fecha ni por sensor: se verifica uno por uno.

USO:
    python scripts/reparar_product_version_modis_s133.py            # informe, no escribe
    python scripts/reparar_product_version_modis_s133.py --aplicar  # escribe
"""
import argparse
import datetime as dt
import glob
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLECCION = {"MODIS_TERRA": "MOD021KM", "MODIS_AQUA": "MYD021KM"}


def _volcan_latlon():
    """Coordenadas desde volcanoes.yaml, para acotar la consulta a la escena real."""
    import yaml
    with io.open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    out = {}
    if isinstance(vols, dict):
        for k, v in vols.items():
            out[k] = (v.get("lat"), v.get("lon"))
    else:
        for v in vols:
            out[v["name"]] = (v.get("lat"), v.get("lon"))
    return out


def hay_granule_estandar(coleccion, cuando, lat, lon, margen_min=10):
    """True si el CMR tiene el granule ESTANDAR de esa pasada sobre ese punto."""
    t = dt.datetime.fromisoformat(cuando.replace("Z", "+00:00"))
    d0 = (t - dt.timedelta(minutes=margen_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
    d1 = (t + dt.timedelta(minutes=margen_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.urlencode({
        "short_name": coleccion, "version": "6.1", "temporal": "%s,%s" % (d0, d1),
        "bounding_box": "%f,%f,%f,%f" % (lon - 0.4, lat - 0.4, lon + 0.4, lat + 0.4),
        "page_size": 5})
    try:
        with urllib.request.urlopen(CMR + "?" + q, timeout=30) as r:
            return len(json.load(r).get("feed", {}).get("entry", [])) > 0
    except Exception as e:
        # Sin respuesta NO se decide: se conserva el record tal como esta. Un error de
        # red no puede convertirse en una reescritura de datos.
        print("   [red] %s %s: %s -> se deja intacto" % (coleccion, cuando, e))
        return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aplicar", action="store_true", help="escribir los cambios")
    ap.add_argument("--desde", default="2026-09-01", help="fecha minima a revisar")
    a = ap.parse_args()

    coords = _volcan_latlon()
    cambios, revisados = [], 0
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "data", "mirova_equivalent",
                                              "*.json"))):
        vol = os.path.splitext(os.path.basename(ruta))[0]
        if vol not in coords or coords[vol][0] is None:
            continue
        lat, lon = coords[vol]
        with io.open(ruta, encoding="utf-8") as fh:
            doc = json.load(fh)
        recs = doc["records"] if isinstance(doc, dict) and "records" in doc else doc
        if not isinstance(recs, list):
            continue
        tocado = False
        for r in recs:
            if not isinstance(r, dict):
                continue
            sensor = str(r.get("sensor") or "")
            ts = str(r.get("datetime_utc") or "")
            if sensor not in COLECCION or ts[:10] < a.desde:
                continue
            if r.get("product_version") != "standard":
                continue
            revisados += 1
            if hay_granule_estandar(COLECCION[sensor], ts, lat, lon):
                continue
            cambios.append((vol, ts[:16], sensor))
            if a.aplicar:
                r["product_version"] = "nrt"
                tocado = True
            time.sleep(0.3)
        if tocado:
            # EL FORMATO TIENE QUE SER EXACTAMENTE EL DE store.py:213
            # (`json.dump(store, f, indent=2)`, con el ensure_ascii por defecto y sin
            # newline final). El primer intento de S133 escribió con `indent=1` y
            # `ensure_ascii=False`: reformateó los diez archivos enteros y produjo un
            # diff de 9,2 millones de líneas para cambiar diez palabras. Un diff así no
            # es sólo ruido — vuelve irrevisable el cambio real y puede romper a
            # cualquiera que compare bytes. Se revirtió con `git checkout -- data/`.
            tmp = ruta + ".tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2)
            os.replace(tmp, ruta)

    print()
    print("revisados: %d  |  a reetiquetar como nrt: %d" % (revisados, len(cambios)))
    for c in cambios:
        print("   %-22s %s %s" % c)
    if cambios and not a.aplicar:
        print("\n(informe solamente; volver a correr con --aplicar para escribir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
