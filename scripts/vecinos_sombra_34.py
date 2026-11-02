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
alguna queda a menos del radio de ese vecino, el record lleva la marca
`cerca_de_vecino = {"vecino": <nombre>, "km": <distancia mínima>}` (el vecino más cercano). La marca vive sólo en la
lectura: no se escribe en data/.

La posición del vecino son dos puntos: el cráter (`vent_lat/vent_lon` de volcanoes.yaml, cuando existe; el de
Villarrica está a 0,85 km del punto nominal) y el punto nominal (`lat/lon`). El radio es UMBRAL_KM (4 km, la decisión
de Nicolás) o el `inner_radius_km` del vecino si es mayor (los Tier A lo traen de los KML de MIROVA: es la zona que
MIROVA misma da por cumbre de ese volcán). POR QUÉ el radio del vecino (V935-01 del verificador del PR #935): el calor
de Puyehue-Cordón Caulle que cae en la grilla de AntillancaCasablanca es el del lacolito del Cordón Caulle, a unos 7 km
del cráter (A20, A68), y el cráter queda fuera de esa grilla; con 4 km desde el cráter no se marcaba casi ninguno de los
cúmulos de producción de PCC que caen ahí (38 de 39 en MODIS, 99 de 102 en VIIRS 375, 40 de 40 en VIIRS 750 sin marca).

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


def _radio(v):
    """Radio en km alrededor del vecino: UMBRAL_KM o su inner_radius_km si es mayor."""
    try:
        r = float(v.get("inner_radius_km") or 0.0)
    except (TypeError, ValueError):
        r = 0.0
    return max(UMBRAL_KM, r)


def _vecino(v):
    """{"puntos": [cráter si existe, punto nominal], "radio_km": ...} de un volcán de volcanoes.yaml."""
    puntos = [_posicion(v)]
    nominal = (float(v["lat"]), float(v["lon"]))
    if nominal not in puntos:
        puntos.append(nominal)
    return {"puntos": puntos, "radio_km": _radio(v)}


def cargar_vecinos(ruta_vecinos=VECINOS_YAML, ruta_volcanes=VOLCANES_YAML):
    """{volcán de los 34: {vecino: {"puntos": [...], "radio_km": r}}}, sólo los volcanes con algún vecino en su grilla.

    Lanza si un archivo no se lee o si un vecino no está en volcanoes.yaml: una lista de vecinos que no se puede
    armar no puede terminar en «ningún vecino» (sería un vigilante ciego que da verde)."""
    tabla = yaml.safe_load(Path(ruta_vecinos).read_text(encoding="utf-8"))["volcanes"]
    vols = {v["name"]: v for v in yaml.safe_load(Path(ruta_volcanes).read_text(encoding="utf-8"))["volcanoes"]}
    out = {}
    for nombre, lista in tabla.items():
        out[nombre] = {e["vecino"]: _vecino(vols[e["vecino"]]) for e in lista}
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


def marca_vecino(rec, vecinos, umbral_km=None, geod=None):
    """{"vecino", "km", "radio_km"} del vecino con la distancia mínima entre los que tienen algún alertado o el cúmulo
    dentro de su radio (`umbral_km` lo reemplaza para todos si se da); None si ninguno (o si el volcán no tiene
    vecinos: `vecinos` vacío o None). "km" se redondea hacia abajo a 0,01 km para que el informe nunca diga «mínimo
    4 km» de una marca de menos de 4 km (V935-05)."""
    if not vecinos:
        return None
    pts = _puntos(rec)
    if not pts:
        return None
    geod = geod or _geod()
    mejor = None
    for nombre, vec in vecinos.items():
        radio = float(umbral_km) if umbral_km is not None else float(vec["radio_km"])
        for vla, vlo in vec["puntos"]:
            for la, lo in pts:
                _, _, d_m = geod.inv(lo, la, vlo, vla)
                km = d_m / 1000.0
                if km < radio and (mejor is None or km < mejor[1]):
                    mejor = (nombre, km, radio)
    if mejor is None:
        return None
    return {"vecino": mejor[0], "km": math.floor(mejor[1] * 100.0) / 100.0, "radio_km": mejor[2]}


def separar(registros, vecinos, umbral_km=None):
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


def linea_resumen(registros_via, vecinos, umbral_km=None):
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
    radios = ", ".join(f"{v} {float(umbral_km) if umbral_km is not None else vecinos[v]['radio_km']:g} km"
                       for v in sorted(vecinos))
    return (f"Vecinos en la grilla ({radios}): {len(cerca)} de {len(registros_via)} pasadas de "
            f"la vía con un alertado o el cúmulo dentro del radio de un vecino, aparte; propias: "
            f"{len(propias)}" + (f" [{detalle}]" if detalle else ""))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "data" / "sombra_34"))
    ap.add_argument("--vecinos", default=str(VECINOS_YAML))
    ap.add_argument("--umbral-km", type=float, default=None)
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
