# -*- coding: utf-8 -*-
"""S194: dónde se repiten las alertas fuera del cráter (agua, flanco, resto) y qué parte del VRP cae en cada área.

Lee la tabla por píxel que escribe particion.py (--salida, por defecto D:/vrp-trabajo/temporales/s194_areas) y
resumen.json. Agrupa los alertados en casillas de 1 x 1 km (coordenadas locales desde el cráter) y cuenta en cuántas
NOCHES distintas alertó cada casilla.

POR QUÉ por noches y no por pasadas: una misma noche tiene hasta 6 pasadas VIIRS 375 (3 satélites, a veces 2 por
satélite) que ven el mismo objeto; contar pasadas inflaría la recurrencia de un evento de una sola noche (A94).
Recurrente = 3 noches o más (umbral descriptivo, no sellado; sólo ordena la lista).

Uso: python experiments/_s194_areas/recurrencia.py [--salida DIR]   (escribe recurrencia.json y recurrencia_salida.txt)
"""
import argparse
import collections
import csv
import gzip
import json
import math
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
KM_LAT, KM_LON_EQ = 110.574, 111.320
RECURRENTE = 3


def rumbo(x, y):
    ang = (math.degrees(math.atan2(x, y)) + 360) % 360
    return ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int((ang + 22.5) // 45) % 8]


def densidades(vy, salida):
    """Alertados por km² de cada área fuera del cráter, por cada 1000 pasadas nocturnas, en VIIRS 375 (la familia con
    casi todos los alertados fuera del cráter). POR QUÉ: el agua ocupa poca superficie; sin dividir por el área, «pocas
    alertas sobre agua» no dice si el agua alerta más o menos que la tierra (control negativo, A110). El área de cada
    zona se mide dentro del cuadrado de 51 x 51 km centrado en el cráter (aproximación de la grilla)."""
    import numpy as np
    sys.path.insert(0, str(AQUI))
    import particion as P
    conf = yaml.safe_load((RAIZ / "config" / "areas_laboratorio.yaml").read_text(encoding="utf-8"))
    res = json.loads((AQUI / "resumen.json").read_text(encoding="utf-8"))
    cuenta = collections.Counter()
    with gzip.open(Path(salida) / "pixeles.csv.gz", "rt", encoding="utf-8") as f:
        for q in csv.DictReader(f):
            if q["familia"] == "VIIRS375":
                cuenta[(q["volcan"], q["area"])] += 1
    print("Densidad de alertados VIIRS 375 por km² y por 1000 pasadas (área de cada zona dentro de 51 x 51 km):")
    print("  volcan\tkm2_agua\tkm2_flanco\tkm2_resto\tdens_agua\tdens_flanco\tdens_resto\tagua/resto")
    tot = collections.Counter()
    for vol in conf["volcanes"]:
        a = P.Areas(vol, RAIZ, conf, vy[vol])
        # Superficie por conteo sobre una malla de 0,1 km (sin shapely, ver particion.Lago): misma precedencia que la
        # partición; el cráter con la distancia geográfica, no la de la grilla (diferencia menor que media celda).
        paso = 0.1
        g = np.arange(-25.5 + paso / 2, 25.5, paso)
        gx, gy = np.meshgrid(g, g)
        xy = np.column_stack([gx.ravel(), gy.ravel()])
        r = np.hypot(xy[:, 0], xy[:, 1])
        en_agua = np.zeros(len(xy), bool)
        for L in a.lagos:
            b0 = L.bbox
            m = (xy[:, 0] >= b0[0]) & (xy[:, 0] <= b0[2]) & (xy[:, 1] >= b0[1]) & (xy[:, 1] <= b0[3])
            if m.any():
                en_agua[np.nonzero(m)[0][L.contiene_varios(xy[m])]] = True
        crater = r <= a.inner_km
        km_agua = float((en_agua & ~crater).sum()) * paso * paso
        km_flanco = float((~crater & ~en_agua & (r <= a.flanco_km)).sum()) * paso * paso
        km_resto = float((~en_agua & (r > a.flanco_km)).sum()) * paso * paso
        npas = res["volcanes"][vol]["por_familia"].get("VIIRS375", {}).get("pasadas", 0)
        d = {}
        for area, km in (("agua", km_agua), ("flanco", km_flanco), ("resto", km_resto)):
            n = cuenta[(vol, area)]
            tot[area + "_n"] += n
            tot[area + "_km2pas"] += km * npas
            d[area] = 1000 * n / (km * npas) if km and npas else float("nan")
        razon = d["agua"] / d["resto"] if d["resto"] else float("nan")
        print(f"  {vol}\t{km_agua:.1f}\t{km_flanco:.1f}\t{km_resto:.1f}\t{d['agua']:.3f}\t{d['flanco']:.3f}\t"
              f"{d['resto']:.3f}\t{razon:.2f}")
    dg = {a: 1000 * tot[a + "_n"] / tot[a + "_km2pas"] for a in ("agua", "flanco", "resto")}
    print(f"  TODOS\t-\t-\t-\t{dg['agua']:.3f}\t{dg['flanco']:.3f}\t{dg['resto']:.3f}\t{dg['agua'] / dg['resto']:.2f}"
          f"\t(alertados: agua {tot['agua_n']}, flanco {tot['flanco_n']}, resto {tot['resto_n']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="D:/vrp-trabajo/temporales/s194_areas")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    res = json.loads((AQUI / "resumen.json").read_text(encoding="utf-8"))
    casillas = collections.defaultdict(lambda: {"noches": set(), "pasadas": set(), "fam": collections.Counter(),
                                                "max_bt": 0.0, "vrp": 0.0})
    with gzip.open(Path(args.salida) / "pixeles.csv.gz", "rt", encoding="utf-8") as f:
        for q in csv.DictReader(f):
            if q["area"] == "crater":
                continue
            v = vy[q["volcan"]]
            lat0, lon0 = float(v.get("vent_lat", v["lat"])), float(v.get("vent_lon", v["lon"]))
            x = (float(q["lon"]) - lon0) * KM_LON_EQ * math.cos(math.radians(lat0))
            y = (float(q["lat"]) - lat0) * KM_LAT
            k = (q["volcan"], q["area"], round(x), round(y))
            c = casillas[k]
            c["noches"].add(q["noche"])
            c["pasadas"].add((q["sensor"], q["datetime_utc"]))
            c["fam"][q["familia"]] += 1
            c["max_bt"] = max(c["max_bt"], float(q["bt_k"]))
            c["vrp"] += float(q["vrp_px_mw"])
    filas = []
    for (vol, area, x, y), c in casillas.items():
        filas.append({"volcan": vol, "area": area, "x_km": x, "y_km": y, "dist_km": round(math.hypot(x, y), 1),
                      "rumbo": rumbo(x, y), "noches": len(c["noches"]), "pasadas": len(c["pasadas"]),
                      "familias": dict(c["fam"]), "max_bt_k": c["max_bt"], "vrp_mw_suma": round(c["vrp"], 3),
                      "primera": min(c["noches"]), "ultima": max(c["noches"])})
    filas.sort(key=lambda r: (r["volcan"], r["area"], -r["noches"]))
    out = {"recurrente_noches": RECURRENTE, "casillas_recurrentes": [r for r in filas if r["noches"] >= RECURRENTE],
           "por_volcan_area": {}}
    for vol in res["volcanes"]:
        for area in ("agua", "flanco", "resto"):
            fs = [r for r in filas if r["volcan"] == vol and r["area"] == area]
            if fs:
                out["por_volcan_area"][f"{vol}/{area}"] = {
                    "casillas": len(fs), "casillas_recurrentes": sum(r["noches"] >= RECURRENTE for r in fs),
                    "noches_en_casillas_recurrentes": sum(r["noches"] for r in fs if r["noches"] >= RECURRENTE)}
    (AQUI / "recurrencia.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("Fracción del VRP sumado (MW) por área, por volcán y familia (reparto con fondo por partes iguales):")
    for vol, dv in res["volcanes"].items():
        for fam, c in dv["vrp_por_area_mw"].items():
            tot = c.get("total_record", 0.0)
            if tot <= 0:
                continue
            print(f"  {vol}\t{fam}\ttotal {tot:.1f} MW\t" + "\t".join(
                f"{a} {100 * c.get(a, 0.0) / tot:.1f}%" for a in ("crater", "agua", "flanco", "resto")))
    print()
    print(f"Casillas de 1 km fuera del cráter que alertaron en {RECURRENTE} noches o más:")
    for r in out["casillas_recurrentes"]:
        print(f"  {r['volcan']}\t{r['area']}\t{r['dist_km']} km {r['rumbo']}\t({r['x_km']},{r['y_km']})\tnoches "
              f"{r['noches']}\tpasadas {r['pasadas']}\t{r['familias']}\tmaxBT {r['max_bt_k']}\tVRP {r['vrp_mw_suma']}"
              f"\t{r['primera']} a {r['ultima']}")
    print()
    densidades(vy, args.salida)
    print()
    print("Todos los alertados sobre agua (control negativo; lago = índice del polígono en frontend/agua/<Volcan>.geojson):")
    nb = collections.Counter()
    with gzip.open(Path(args.salida) / "pixeles.csv.gz", "rt", encoding="utf-8") as f:
        for q in csv.DictReader(f):
            if q["area"] == "agua":
                nb["total"] += 1
                nb["borde"] += int(q["borde"])
                nb[q["familia"]] += 1
                nb.setdefault("pasadas", set()).add((q["volcan"], q["sensor"], q["datetime_utc"]))
                nb.setdefault("noches", set()).add((q["volcan"], q["noche"]))
                print(f"  {q['volcan']}\t{q['sensor']}\t{q['datetime_utc']}\tlago {q['lago']}\t{q['dist_km']} km\t"
                      f"BT {q['bt_k']} K\tborde {q['borde']}\tpublicada {q['distance_class']}\tVRP_px {q['vrp_px_mw']}")
    print(f"  => alertados sobre agua: {nb['total']} píxeles ({nb['borde']} a menos de media celda de la orilla), "
          f"{len(nb.get('pasadas', ()))} pasadas, {len(nb.get('noches', ()))} noches-volcán; por familia "
          f"MODIS {nb['MODIS']}, VIIRS375 {nb['VIIRS375']}, VIIRS750 {nb['VIIRS750']}")
    print()
    print("Resumen por volcán y área (casillas con alerta, recurrentes, noches en recurrentes):")
    for k, v in out["por_volcan_area"].items():
        print(f"  {k}\t{v['casillas']}\t{v['casillas_recurrentes']}\t{v['noches_en_casillas_recurrentes']}")


if __name__ == "__main__":
    main()
