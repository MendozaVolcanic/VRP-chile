# FICHA (SDA, CPLT 372): driver de solo lectura. Baja gránulos L1B a un temporal, los mide con analisis.py y los borra.
# No es detección de producción; no escribe en data/, no commitea, no hace push.
"""Uso (desde la raíz del repo, con EARTHDATA_TOKEN en el entorno; lo corre .github/workflows/probe-s185-l1b.yml):
    python experiments/_s185_l1b/bajar_y_medir.py --caso tup|chi --out out [--tmp DIR] [--solo N]

Por cada pasada del manifiesto: busca el gránulo L1B y su GEO en CMR (pipeline.fetch.search_granules, misma ruta que el NRT),
los baja con download_granules, corre analisis.analizar_tup o analizar_chi, guarda un recorte chico (npz, +-12 km del cráter)
y BORRA el gránulo. Escribe out/<caso>_resultados.json y out/recortes_<caso>/*.npz. Sale con 2 si falta alguna pasada (S141).
Si el nombre exacto del gránulo ya no existe (reproceso), usa el que tenga la misma fecha y hora y lo anota en `nota_granulo`.
"""
import argparse
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for p in (ROOT, AQUI):
    sys.path.insert(0, str(p))
import numpy as np  # noqa: E402

VOLCAN = {"tup": {"nombre": "Tupungatito", "lat": -33.4, "lon": -69.8, "radio": 25},
          "chi": {"nombre": "NevadosDeChillan", "lat": -36.863, "lon": -71.377, "radio": 25}}
# clave de producto de pipeline.fetch por prefijo del nombre y por caso (V750 usa los M-band, V375 los I-band)
PRODUCTOS = {"tup": {"VJ1": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"), "VJ2": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO"),
                     "VNP": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO")},
             "chi": {"VJ1": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"), "VJ2": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
                     "VNP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO")}}


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def sello(nombre):
    """'VJ102MOD.A2026062.0548.021.2026062122629.nc' -> 'A2026062.0548' (día juliano y hora de la pasada)."""
    return ".".join(nombre.split(".")[1:3])


def bajar_uno(caso, clave, nombre, destino):
    """Descarga el gránulo `nombre` (o, si ya no existe, el de la misma pasada) y devuelve (ruta, nota) o (None, motivo)."""
    from pipeline.fetch import download_granules, search_granules
    v = VOLCAN[caso]
    st = sello(nombre)
    dt = datetime.strptime(st[1:], "%Y%j.%H%M")
    grs = [g for g in search_granules(clave, v["lat"], v["lon"], v["radio"], dt) if st in gname(g)]
    exactos = [g for g in grs if gname(g) == nombre]
    elegidos = exactos or grs
    if not elegidos:
        return None, f"sin gránulo {clave} {st}"
    got = [Path(p) for p in download_granules(elegidos[:1], destino) if st in Path(p).name]
    if not got:
        return None, f"descarga fallida {clave} {st}"
    nota = None if got[0].name == nombre else f"reprocesado: {got[0].name} en lugar de {nombre}"
    return got[0], nota


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)   # no se reemplaza sys.stdout: rompería la captura de pytest
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", choices=("tup", "chi"), required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=os.environ.get("VRP_TMP_DIR", str(ROOT / "granulos_tmp")))
    ap.add_argument("--solo", type=int, default=0, help="solo las primeras N pasadas (prueba)")
    a = ap.parse_args()
    if not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 2
    from pipeline.fetch import auth
    import analisis as AN
    auth()
    man = [m for m in json.load(open(AQUI / "manifiesto_s185.json", encoding="utf-8")) if m["proyecto"] == a.caso]
    if a.solo:
        man = man[:a.solo]
    out = Path(a.out)
    (out / f"recortes_{a.caso}").mkdir(parents=True, exist_ok=True)
    tmp = Path(a.tmp) / a.caso
    res, faltan = [], 0
    for m in man:
        print("\n== %s | %s | %s" % (m["rol"], m["rotulo"], m["l1b"]), flush=True)
        item = {"rol": m["rol"], "rotulo": m["rotulo"], "gran_pedido": m["l1b"], "ok": False}
        try:
            k1, k2 = PRODUCTOS[a.caso][m["l1b"][:3]]
            tmp.mkdir(parents=True, exist_ok=True)
            rl, nota = bajar_uno(a.caso, k1, m["l1b"], tmp)
            if rl is None:
                raise RuntimeError(nota)
            rg, nota_g = bajar_uno(a.caso, k2, m["geo"], tmp)
            if rg is None:
                raise RuntimeError(nota_g)
            item["nota_granulo"] = nota
            item["nota_geo"] = nota_g
            item["mb_descargados"] = round((rl.stat().st_size + rg.stat().st_size) / 1e6, 1)
            if a.caso == "tup":
                rad = AN.MV.leer_radiancia_l1b(rl)
                lat, lon, ang = AN.MV.leer_geo_l1b(rg)
                item.update(AN.analizar_tup(rl.name, rad, lat, lon, ang, m["ref"]))
                np.savez_compressed(out / f"recortes_{a.caso}" / (rl.stem + ".npz"), **AN.recorte_tup(rad, lat, lon, ang))
            else:
                rad = AN.MV.leer_radiancia_l1b(rl, bandas=AN.MV.FAMILIAS["VIIRS375"]["bandas"])
                lat, lon, ang = AN.MV.leer_geo_l1b(rg)
                flags, altura = AN.leer_banderas(rl), AN.leer_altura(rg)
                item.update(AN.analizar_chi(rl.name, rad, lat, lon, ang, flags, altura, m["ref"]))
                np.savez_compressed(out / f"recortes_{a.caso}" / (rl.stem + ".npz"), **AN.recorte_chi(rad, lat, lon, ang, flags, altura))
            item["ok"] = True
            item["ref"] = m["ref"]
            print("  reproduce_publicado:", item.get("reproduce_publicado"), "| variantes:",
                  {k: (v.get("razon_mirova") if a.caso == "chi" else (v.get("celda_decisiva") or {}).get("margen"))
                   for k, v in item["variantes"].items()}, flush=True)
        except Exception as e:  # una pasada que falla no tumba las demás, pero el código de salida lo dice
            item["error"] = "%s: %s" % (type(e).__name__, e)
            print("  FALLA:", item["error"])
            traceback.print_exc()
            faltan += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)   # nunca se acumulan L1B: se borran al usarlos
        res.append(item)
        json.dump(res, open(out / f"{a.caso}_resultados.json", "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
    print("\npasadas medidas: %d de %d" % (len(res) - faltan, len(res)))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
