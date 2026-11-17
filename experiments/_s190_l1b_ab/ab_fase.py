# FICHA (SDA, CPLT 372): driver de solo lectura del A/B de fase de grilla en VIIRS 750 (PREREGISTRO.md). Baja cada L1B y
# su GEO a un temporal, corre la vía con 4 esquinas de grilla y borra el gránulo. No es detección de producción; no
# escribe en data/, no commitea, no hace push.
"""Uso (desde la raíz del repo, con EARTHDATA_TOKEN en el entorno; lo corre .github/workflows/probe-s185-l1b.yml con
probe=s190):
    python experiments/_s190_l1b_ab/ab_fase.py --parte K --partes N --out out [--tmp DIR] [--solo M]

Reparte los gránulos del manifiesto en N partes (por orden de nombre, gránulo k va a la parte k % N); en cada gránulo
corre todas las pasadas (volcanes) que lo usan. Escribe out/s190_parte<K>.json. Sale con 2 si falta alguna pasada (S141).
"""
import argparse
import json
import os
import shutil
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline import mirova_v750_codigo as MV  # noqa: E402

# Brazos (PREREGISTRO.md §3): corrimiento de la esquina de la grilla en celdas (este, norte).
BRAZOS = {"A": (0.0, 0.0), "B": (0.0, 0.5), "C": (0.5, 0.5), "Z": (0.5, 0.0)}
PRODUCTOS = {"VJ1": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"), "VJ2": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO"),
             "VNP": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO")}
SENSOR = {"VJ1": "VIIRS_NOAA20_750", "VJ2": "VIIRS_NOAA21_750", "VNP": "VIIRS_SNPP_750"}


def sello(nombre):
    """'VJ102MOD.A2026062.0548.021.2026062122629.nc' -> 'A2026062.0548'."""
    return ".".join(nombre.split(".")[1:3])


def grilla_corrida(g, de, dn):
    """Esquina corrida `de` celdas al este y `dn` al norte (calcular_vrp_granulo recalcula celda del cráter y caja)."""
    g2 = dict(g)
    g2["ul_x"] = g["ul_x"] + de * g["paso"]
    g2["ul_y"] = g["ul_y"] + dn * g["paso"]
    return g2


def correr_brazos(rad, lat, lon, ang, p):
    """Los 4 brazos de una pasada `p` del manifiesto: {brazo: {n_pix, vrp_mw, celda_decisiva}} o {"estado": ...}."""
    g0 = MV.grilla_del_volcan(p["volcan"])
    sensor = SENSOR[p["l1b"][:3]]
    out = {}
    for b, (de, dn) in BRAZOS.items():
        rec = MV.calcular_vrp_granulo(rad, lat, lon, ang, p["volcan"], p["vent"][0], p["vent"][1], p["inner_km"], sensor,
                                      grilla=grilla_corrida(g0, de, dn))
        if rec is None:
            out[b] = {"estado": "sin_record"}
            continue
        cd = ((rec.get("diag_codigo_mirova") or {}).get("s1") or {}).get("celda_decisiva")
        out[b] = {"n_pix": rec["n_anomalous_pixels"], "vrp_mw": rec["vrp_mw"], "celda_decisiva": cd}
    return out


def reproduce(brazo_a, ref):
    """V1 del pre-registro: mismo n_pix, misma celda decisiva y margen a 1e-3 que el record publicado."""
    cd, cp = (brazo_a or {}).get("celda_decisiva"), ref.get("publicado_celda_decisiva")
    if not cd or not cp or brazo_a.get("n_pix") is None:
        return False
    return (brazo_a["n_pix"] == ref.get("publicado_n_pix") and (cd["fila"], cd["col"]) == (cp["fila"], cp["col"])
            and abs(cd["margen"] - cp["margen"]) < 1e-3)


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def bajar(clave, nombre_l1b, lat, lon, destino, exacto=True):
    """Busca en CMR (pipeline.fetch, la ruta del NRT) el gránulo de la misma pasada y lo baja. (ruta, nota) o (None, motivo).
    Con exacto=True prefiere el nombre del record publicado; si ya no está (reproceso), toma el de la misma pasada y lo anota."""
    from pipeline.fetch import download_granules, search_granules
    st = sello(nombre_l1b)
    dt = datetime.strptime(st[1:], "%Y%j.%H%M")
    grs = [g for g in search_granules(clave, lat, lon, 25, dt) if st in gname(g)]
    elegidos = ([g for g in grs if gname(g) == nombre_l1b] if exacto else []) or grs
    if not elegidos:
        return None, f"sin gránulo {clave} {st}"
    got = [Path(x) for x in download_granules(elegidos[:1], destino) if st in Path(x).name]
    if not got:
        return None, f"descarga fallida {clave} {st}"
    return got[0], (None if (not exacto or got[0].name == nombre_l1b) else f"reprocesado: {got[0].name}")


def partir(pasadas, parte, partes):
    grupos = defaultdict(list)
    for p in pasadas:
        grupos[p["l1b"]].append(p)
    return {g: grupos[g] for i, g in enumerate(sorted(grupos)) if i % partes == parte}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", type=int, required=True)
    ap.add_argument("--partes", type=int, required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=os.environ.get("VRP_TMP_DIR", str(ROOT / "granulos_tmp")))
    ap.add_argument("--solo", type=int, default=0, help="solo los primeros M gránulos de la parte (prueba)")
    a = ap.parse_args()
    if not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 2
    from pipeline.fetch import auth
    auth()
    man = json.load(open(AQUI / "manifiesto_s190.json", encoding="utf-8"))["pasadas"]
    grupos = partir(man, a.parte, a.partes)
    if a.solo:
        grupos = dict(list(grupos.items())[:a.solo])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    salida = out / f"s190_parte{a.parte}.json"
    tmp = Path(a.tmp) / f"s190_{a.parte}"
    res, faltan = [], 0
    for gran, ps in grupos.items():
        print("\n== %s (%d pasadas: %s)" % (gran, len(ps), ", ".join(p["volcan"] for p in ps)), flush=True)
        try:
            k1, k2 = PRODUCTOS[gran[:3]]
            tmp.mkdir(parents=True, exist_ok=True)
            v0 = ps[0]["vent"]
            rl, nota = bajar(k1, gran, v0[0], v0[1], tmp)
            if rl is None:
                raise RuntimeError(nota)
            rg, nota_g = bajar(k2, gran, v0[0], v0[1], tmp, exacto=False)
            if rg is None:
                raise RuntimeError(nota_g)
            rad = MV.leer_radiancia_l1b(rl)
            lat, lon, ang = MV.leer_geo_l1b(rg)
            for p in ps:
                item = {k: p[k] for k in ("volcan", "dt", "l1b", "cat", "estrato", "rol", "ref")}
                item.update({"gran_usado": rl.name, "geo_usado": rg.name, "nota_granulo": nota})
                try:
                    item["brazos"] = correr_brazos(rad, lat, lon, ang, p)
                    item["reproduce"] = reproduce(item["brazos"].get("A"), p["ref"])
                    item["ok"] = True
                    print("  %s %s %s reproduce=%s n_pix=%s" % (p["volcan"], p["cat"], p["estrato"], item["reproduce"],
                          {b: v.get("n_pix") for b, v in item["brazos"].items()}), flush=True)
                except Exception as e:
                    item.update({"ok": False, "error": "%s: %s" % (type(e).__name__, e)})
                    traceback.print_exc()
                    faltan += 1
                res.append(item)
        except Exception as e:  # el gránulo falla: todas sus pasadas faltan, pero las demás siguen
            print("  FALLA:", type(e).__name__, e)
            traceback.print_exc()
            for p in ps:
                res.append({k: p[k] for k in ("volcan", "dt", "l1b", "cat", "estrato", "rol")} |
                           {"ok": False, "error": "%s: %s" % (type(e).__name__, e)})
                faltan += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)   # nunca se acumulan L1B
        json.dump(res, open(salida, "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
    print("\npasadas medidas: %d de %d" % (len(res) - faltan, len(res)))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
