# -*- coding: utf-8 -*-
"""S196: datos del visor de radios del edificio (calor conocido por casilla y agua), para que Nicolás fije el radio
del flanco de cada volcán (decisión D-H del 2026-11-23; plan del experimental, ítem P0).

POR QUÉ: P0 quiere que una anomalía térmica conocida y constante (lacolito de Cordón Caulle, lago de lava de
Villarrica, cráter de Láscar) no esconda un foco nuevo en otra parte del edificio. Para eso cada volcán necesita un
borde de edificio («flanco», config/areas_laboratorio.yaml); hoy es 10 km provisional en todos. El radio lo decide la
geología, pero conviene verlo contra dónde ha alertado la vía: qué casillas quedan dentro del flanco, cuáles fuera.

Qué cuenta: los alertados (anomaly_pixels) de los records de la vía «código MIROVA» (via_codigo_mirova: true), sólo
pasadas nocturnas (el mismo criterio que experiments/_s194_areas/particion.py::es_nocturna: dayflag 0 del .m y Sol
bajo el horizonte), desde --desde (por defecto 2026-03-01: la tabla de MIROVA está sana desde marzo, A119, y así la
ventana es la misma para los 11). Cada alertado cae en una casilla de 1 x 1 km en coordenadas locales desde el cráter
(el mismo reparto de experiments/_s194_areas/recurrencia.py, pero incluyendo el cráter). Por casilla se cuentan NOCHES
distintas, no pasadas: una noche tiene hasta 6 pasadas VIIRS 375 que ven el mismo objeto (A94).

Fuentes de records: los 11 Tier A en data/mirova_equivalent/<Volcan>.json; los demás volcanes activos en
data/sombra_34/<Volcan>.json (la sombra corre la vía desde el 2026-11-03, así que su ventana es más corta y se informa).

Centro: get_detection_anchor (el cráter, vent_lat/vent_lon cuando existe), que es el punto desde el que la vía mide
dist_km y desde el que config/areas_laboratorio.yaml aplica radio_flanco_km.

Uso: python experiments/_s196_visor_radios/datos_visor.py [--desde 2026-03-01]
Salidas: experiments/_s196_visor_radios/datos_visor.json (lo que lee el visor) y datos_visor_salida.txt (resumen).
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experiments" / "_s194_areas"))
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from particion import KM_LAT, KM_LON_EQ, Lago, es_nocturna, familia_de, noche_de  # noqa: E402


def anillos_redondeados(geom):
    """Polígonos del GeoJSON con coordenadas a 4 decimales (~10 m) y sin vértices repetidos, para aligerar el HTML."""
    polis = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    out = []
    for anillos in polis:
        pa = []
        for a in anillos:
            r = []
            for lo, la in a:
                p = [round(lo, 4), round(la, 4)]
                if not r or r[-1] != p:
                    r.append(p)
            if len(r) >= 4:
                pa.append(r)
        if pa:
            out.append(pa)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-03-01")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    vols = [v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
            if v.get("active")]
    conf = yaml.safe_load((RAIZ / "config" / "areas_laboratorio.yaml").read_text(encoding="utf-8"))
    salida = {"desde": args.desde, "fuente": "anomaly_pixels de records nocturnos de la vía (via_codigo_mirova)",
              "casilla_km": 1.0, "radio_provisional_km": conf["radio_flanco_km_defecto"], "volcanes": []}
    resumen = []
    for v in vols:
        nombre = v["name"]
        tier_a = v.get("radius_km") == 25
        lat0, lon0 = (float(c) for c in get_detection_anchor(v))
        kx = KM_LON_EQ * math.cos(math.radians(lat0))
        f = RAIZ / "data" / ("mirova_equivalent" if tier_a else "sombra_34") / f"{nombre}.json"
        recs = json.loads(f.read_text(encoding="utf-8"))["records"] if f.exists() else []
        # Agua: polígonos de frontend/agua/<Volcan>.geojson en km locales, para marcar las casillas cuyo centro cae en
        # un lago (la partición los manda al área «agua» antes que al flanco).
        fa = RAIZ / "frontend" / "agua" / f"{nombre}.geojson"
        agua_geo, lagos = [], []
        if fa.exists():
            for feat in json.loads(fa.read_text(encoding="utf-8"))["features"]:
                for anillos in anillos_redondeados(feat["geometry"]):
                    agua_geo.append(anillos)
                    lagos.append(Lago([[((lo - lon0) * kx, (la - lat0) * KM_LAT) for lo, la in a] for a in anillos]))
        noches_pasada, pasadas = set(), 0
        cas = collections.defaultdict(lambda: {"noches": set(), "pasadas": set(), "fam": collections.Counter(),
                                               "max_bt": 0.0})
        ultima = ""
        for r in recs:
            dt = r.get("datetime_utc", "")
            if r.get("via_codigo_mirova") is not True or dt < args.desde or not es_nocturna(r):
                continue
            pasadas += 1
            ultima = max(ultima, dt)
            noche = noche_de(dt)
            noches_pasada.add(noche)
            for q in r.get("anomaly_pixels") or []:
                x = (float(q["lon"]) - lon0) * kx
                y = (float(q["lat"]) - lat0) * KM_LAT
                c = cas[(round(x), round(y))]
                c["noches"].add(noche)
                c["pasadas"].add((r["sensor"], dt))
                c["fam"][familia_de(r["sensor"])] += 1
                c["max_bt"] = max(c["max_bt"], float(q.get("bt_k") or 0.0))
        noches_det = sorted({n for c in cas.values() for n in c["noches"]})
        idx = {n: i for i, n in enumerate(noches_det)}
        casillas = []
        for (x, y), c in sorted(cas.items(), key=lambda kv: -len(kv[1]["noches"])):
            en_agua = any(L.contiene(float(x), float(y)) for L in lagos)
            casillas.append({"x": x, "y": y, "d": round(math.hypot(x, y), 2), "agua": en_agua,
                             "n": [idx[n] for n in sorted(c["noches"])], "pas": len(c["pasadas"]),
                             "fam": dict(c["fam"]), "bt": round(c["max_bt"], 1)})
        cfg = (conf.get("volcanes") or {}).get(nombre) or {}
        inner = v.get("inner_radius_km")
        salida["volcanes"].append({
            "nombre": nombre, "titulo": v.get("display_name", nombre), "tier_a": tier_a,
            "lat": lat0, "lon": lon0, "lat_catalogo": float(v["lat"]), "lon_catalogo": float(v["lon"]),
            "inner_km": float(inner) if inner is not None else None,
            "radio_actual_km": float(cfg["radio_flanco_km"]) if "radio_flanco_km" in cfg else None,
            "en_config": nombre in (conf.get("volcanes") or {}),
            "fuente_records": str(f.relative_to(RAIZ)).replace("\\", "/"),
            "pasadas_nocturnas": pasadas, "noches_con_pasada": len(noches_pasada),
            "primera_noche": min(noches_pasada) if noches_pasada else None,
            "ultima_pasada_utc": ultima or None,
            "noches": noches_det, "casillas": casillas, "agua": agua_geo})
        resumen.append(f"{nombre}\t{'A' if tier_a else '-'}\tpasadas {pasadas}\tnoches {len(noches_pasada)}\t"
                       f"noches con alerta {len(noches_det)}\tcasillas {len(casillas)}\tagua {len(agua_geo)} polígonos\t"
                       f"casillas sobre agua {sum(c['agua'] for c in casillas)}")
    salida["volcanes"].sort(key=lambda d: (not d["tier_a"], -d["lat"]))
    (AQUI / "datos_visor.json").write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")),
                                            encoding="utf-8")
    txt = "\n".join([f"Ventana desde {args.desde} (noche local); casillas de 1 km; sólo pasadas nocturnas de la vía."]
                    + resumen) + "\n"
    (AQUI / "datos_visor_salida.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
