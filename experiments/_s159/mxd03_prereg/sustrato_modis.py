"""S159, pre-registro de MxD03: con qué detector están escritos hoy los records MODIS, y cuánto sustrato hay por
tramo de cenit y lado del barrido, contra la referencia de MIROVA.

Lee `data/mirova_equivalent/<volcan>.json` de un commit (por defecto origin/main) con `git show`, nunca del
checkout local (regla 5 del mapa del workspace). Sólo MODIS (`sensor` empieza con MODIS), sólo noche
(no hay records diurnos MODIS en producción; se cuenta igual por si acaso con `solar_zenith_deg`).

Qué imprime:
1. Por mes de observación: n records MODIS, campo `regimen`, y el `processed_utc` mínimo y máximo, para ver si todo
   el tramo está escrito con K (adopción 2026-10-18 09:57:30 UTC; histórico K desde 2025-02-15 según
   `frontend/cambio_detector.js`).
2. Por tramo de cenit del record (<=25, 25-40, 40-50, >50) y lado del barrido (regla de S151 validada 85 de 85 en
   el probe M: Aqua con acimut > 0 o Terra con acimut < 0 = lado del frame 0): n records, n `summit`,
   n con cúmulo dentro de inner.

Las dos preguntas del instrumento:
1. Si los records no tuvieran cenit o acimut, ¿se vería? Sí: cuenta los que no lo traen (`sin_geom`).
2. Si el `git show` devolviera un archivo vacío, ¿se vería distinto? Sí: imprime records totales por volcán, y
   el control positivo es Láscar, que tiene que tener miles de records MODIS.

Uso: python sustrato_modis.py [--ref origin/main] [--desde 2026-03-01] [--hasta 2026-10-16]
"""
import collections
import json
import subprocess
import sys

ONCE = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima",
        "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
REPO = r"C:\vrp-trabajo\s159-pruebas"


def arg(n, d):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def tramo(z):
    if z is None:
        return "sin_geom"
    return "<=25" if z <= 25 else ("25-40" if z <= 40 else ("40-50" if z <= 50 else ">50"))


def lado(sensor, az):
    if az is None:
        return "?"
    aqua = "AQUA" in sensor
    return "f0" if (aqua and az > 0) or (not aqua and az < 0) else "otro"


def main():
    ref = arg("--ref", "origin/main")
    desde, hasta = arg("--desde", "2025-02-15"), arg("--hasta", "2026-10-21")
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", ref], capture_output=True, text=True).stdout.strip()
    print(f"ref {ref} = {sha}; ventana de observación {desde} a {hasta} (inclusive)")
    por_mes = collections.defaultdict(lambda: {"n": 0, "reg": collections.Counter(), "pmin": "9", "pmax": "0"})
    tab = collections.defaultdict(lambda: collections.Counter())
    for v in ONCE:
        txt = subprocess.run(["git", "-C", REPO, "show", f"{ref}:data/mirova_equivalent/{v}.json"],
                             capture_output=True, text=True, encoding="utf-8").stdout
        d = json.loads(txt)
        recs = d["records"] if isinstance(d, dict) else d
        modis = [r for r in recs if str(r.get("sensor", "")).startswith("MODIS")]
        en = [r for r in modis if desde <= str(r.get("datetime_utc", ""))[:10] <= hasta]
        print(f"  {v}: records {len(recs)}, MODIS {len(modis)}, MODIS en ventana {len(en)}")
        for r in en:
            mes = r["datetime_utc"][:7]
            m = por_mes[mes]
            m["n"] += 1
            m["reg"][str(r.get("regimen"))] += 1
            p = str(r.get("processed_utc") or "")
            if p:
                m["pmin"] = min(m["pmin"], p)
                m["pmax"] = max(m["pmax"], p)
            z = r.get("sensor_zenith_deg")
            k = (tramo(z), lado(r.get("sensor", ""), r.get("sensor_azimuth_deg")))
            tab[k]["n"] += 1
            pc = r.get("primary_cluster") or {}
            if r.get("distance_class") == "summit":
                tab[k]["summit"] += 1
            if pc and (pc.get("vrp_mw") or 0) > 0:
                tab[k]["pc_vrp>0"] += 1
    print("\nPor mes de observación (MODIS, 11 Tier A):")
    for mes in sorted(por_mes):
        m = por_mes[mes]
        print(f"  {mes}: n {m['n']:5d} | regimen {dict(m['reg'])} | processed_utc {m['pmin'][:16]} a {m['pmax'][:16]}")
    print("\nPor tramo de cenit y lado (MODIS, 11 Tier A, ventana):")
    for k in sorted(tab):
        print(f"  {k[0]:>8} {k[1]:>5}: {dict(tab[k])}")


if __name__ == "__main__":
    main()
