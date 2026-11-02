"""S173 (decisión 3 de tasks/BLOQUE_ARRANQUE_S173.md §b, aprobada por Nicolás el 2026-11-02): separa en la lectura de
la sombra de los 34 las pasadas cuyo calor puede ser del volcán vecino.

POR QUÉ (fenómeno). La vía «código MIROVA» mira una grilla de 51 x 51 km alrededor de cada volcán y suma todos los
píxeles alertados de la grilla, también los de fuera de la caja sensible (D32). En 13 de los 34 hay otro volcán de
volcanoes.yaml dentro de esa grilla (experiments/_s172_sombra34/vecinos.yaml, que tests/test_sombra_34_s172.py
recalcula con la geometría de la vía). Si el vecino tiene calor (el lago de lava de Villarrica visto desde
Quetrupillán, el domo de Chaitén desde Michinmahuida), ese calor aparece como del volcán nuevo, con su magnitud y su
posición, y sin etiqueta: los 34 no tienen inner_radius_km y el record sale con `distance_class: null`. Mezclar esas
pasadas con las del volcán propio haría que la sombra juzgue al detector con calor ajeno.

QUÉ HACE. Para cada record, toma las posiciones que escribe pipeline/mirova_v750_codigo.py::procesar_grilla: cada
`anomaly_pixels[].lat/lon` (los alertados; en la vía pipeline/store.py no los filtra) y
`primary_cluster.centroid_lat/lon` (el cúmulo publicado), y mide la distancia geodésica (WGS84) a cada vecino. Si
alguna queda a menos de UMBRAL_KM (4 km) de un vecino, el record lleva la marca
`cerca_de_vecino = {"vecino": <nombre>, "km": <distancia mínima>}` (el vecino más cercano). La marca vive sólo en la
lectura: no se escribe en data/.

La posición del vecino es `vent_lat/vent_lon` de volcanoes.yaml cuando existe (el cráter de los Tier A, por ejemplo
el de Villarrica, a 0,85 km del punto nominal) y `lat/lon` cuando no.

LO QUE NO HACE. No cambia la detección ni la grilla: la zona excluida alrededor del vecino en la grilla toca pipeline/
y pide A45; queda como trabajo previo a PUBLICAR Quetrupillán, Michinmahuida, AntillancaCasablanca y Callaqui (los
cuatro con vecino Tier A). Una pasada marcada no se descarta: se cuenta aparte.

Uso: python scripts/vecinos_sombra_34.py [--dir data/sombra_34] [--vecinos experiments/_s172_sombra34/vecinos.yaml]
     imprime, por volcán con vecino, cuántas pasadas de la vía hay y cuántas quedan cerca de un vecino.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VECINOS_YAML = ROOT / "experiments" / "_s172_sombra34" / "vecinos.yaml"
VOLCANES_YAML = ROOT / "volcanoes.yaml"
UMBRAL_KM = 4.0


def _posicion(v):
    """(lat, lon) del volcán: el cráter (vent) si volcanoes.yaml lo trae, si no el punto nominal."""
    if v.get("vent_lat") is not None and v.get("vent_lon") is not None:
        return float(v["vent_lat"]), float(v["vent_lon"])
    return float(v["lat"]), float(v["lon"])


def cargar_vecinos(ruta_vecinos=VECINOS_YAML, ruta_volcanes=VOLCANES_YAML):
    """{volcán de los 34: {vecino: (lat, lon)}}, sólo los volcanes que tienen algún vecino en su grilla.

    Lanza si un archivo no se lee o si un vecino no está en volcanoes.yaml: una lista de vecinos que no se puede
    armar no puede terminar en «ningún vecino» (sería un vigilante ciego que da verde)."""
    tabla = yaml.safe_load(Path(ruta_vecinos).read_text(encoding="utf-8"))["volcanes"]
    vols = {v["name"]: v for v in yaml.safe_load(Path(ruta_volcanes).read_text(encoding="utf-8"))["volcanoes"]}
    out = {}
    for nombre, lista in tabla.items():
        out[nombre] = {e["vecino"]: _posicion(vols[e["vecino"]]) for e in lista}
    return out


def _geod():
    from pyproj import Geod
    return Geod(ellps="WGS84")


def _puntos(rec):
    """Posiciones (lat, lon) de los alertados y del cúmulo publicado del record."""
    pts = []
    for p in rec.get("anomaly_pixels") or []:
        if isinstance(p, dict):
            pts.append((p.get("lat"), p.get("lon")))
    pc = rec.get("primary_cluster")
    if isinstance(pc, dict):
        pts.append((pc.get("centroid_lat"), pc.get("centroid_lon")))
    out = []
    for la, lo in pts:
        try:
            la, lo = float(la), float(lo)
        except (TypeError, ValueError):
            continue
        if math.isfinite(la) and math.isfinite(lo):
            out.append((la, lo))
    return out


def marca_vecino(rec, vecinos, umbral_km=UMBRAL_KM, geod=None):
    """{"vecino", "km"} del vecino más cercano si algún alertado o el cúmulo queda a menos de `umbral_km` de él;
    None si no (o si el volcán no tiene vecinos: `vecinos` vacío o None)."""
    if not vecinos:
        return None
    pts = _puntos(rec)
    if not pts:
        return None
    geod = geod or _geod()
    mejor = None
    for nombre, (vla, vlo) in vecinos.items():
        for la, lo in pts:
            _, _, d_m = geod.inv(lo, la, vlo, vla)
            km = d_m / 1000.0
            if mejor is None or km < mejor[1]:
                mejor = (nombre, km)
    if mejor is None or not mejor[1] < umbral_km:
        return None
    return {"vecino": mejor[0], "km": round(mejor[1], 2)}


def separar(registros, vecinos, umbral_km=UMBRAL_KM):
    """(propias, cerca_de_vecino): las pasadas sin marca y las marcadas. A cada marcada se le agrega, en una COPIA,
    la clave `cerca_de_vecino`; el record original no se toca."""
    propias, cerca = [], []
    geod = _geod() if vecinos else None
    for r in registros:
        m = marca_vecino(r, vecinos, umbral_km, geod) if vecinos else None
        if m is None:
            propias.append(r)
        else:
            cerca.append({**r, "cerca_de_vecino": m})
    return propias, cerca


def linea_resumen(registros_via, vecinos, umbral_km=UMBRAL_KM):
    """Una línea para el informe: pasadas de la vía cerca de un vecino, aparte de las propias. None si el volcán no
    tiene vecinos (el informe de un volcán sin vecino no cambia)."""
    if not vecinos:
        return None
    propias, cerca = separar(registros_via, vecinos, umbral_km)
    por_vecino = {}
    for r in cerca:
        m = r["cerca_de_vecino"]
        n, km = por_vecino.get(m["vecino"], (0, None))
        por_vecino[m["vecino"]] = (n + 1, m["km"] if km is None else min(km, m["km"]))
    detalle = "; ".join(f"{v}: {n}, mínimo {km:g} km" for v, (n, km) in sorted(por_vecino.items()))
    return (f"Vecinos en la grilla ({', '.join(sorted(vecinos))}): {len(cerca)} de {len(registros_via)} pasadas de "
            f"la vía con un alertado o el cúmulo a menos de {umbral_km:g} km de un vecino, aparte; propias: "
            f"{len(propias)}" + (f" [{detalle}]" if detalle else ""))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "data" / "sombra_34"))
    ap.add_argument("--vecinos", default=str(VECINOS_YAML))
    ap.add_argument("--umbral-km", type=float, default=UMBRAL_KM)
    a = ap.parse_args(argv)
    tabla = cargar_vecinos(a.vecinos)
    for volcan in sorted(tabla):
        p = Path(a.dir) / f"{volcan}.json"
        if not p.exists():
            print(f"{volcan}: sin archivo")
            continue
        regs = [r for r in (json.loads(p.read_text(encoding="utf-8")).get("records") or [])
                if isinstance(r, dict) and r.get("via_codigo_mirova") is True]
        print(f"{volcan}: {linea_resumen(regs, tabla[volcan], a.umbral_km)}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
