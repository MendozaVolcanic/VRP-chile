# -*- coding: utf-8 -*-
"""S128 Fase 2 · sonda P3 — CUANTO PIERDE `latest.php`. Cierra D2, que nunca se midio.

El fenomeno. Nuestro ground truth es un CSV que un scraper arma leyendo la pagina
`latest.php` de mirovaweb cada 5 minutos. Esa pagina muestra las ultimas pasadas;
si dos pasadas caen entre dos lecturas del scraper, la del medio se pierde para
siempre. Hace 127 sesiones que toda metrica de recall se corrige mentalmente con la
creencia "el CSV cubre ~70 % de VIIRS" — un numero que **nunca se midio**, porque
no habia denominador: no se sabia cuantas pasadas hubo en realidad.

El archivo de TIF SI da el denominador. Cada GeoTIFF es una pasada que MIROVA
proceso y publico, con su timestamp. Comparar el conjunto de pasadas del archivo
contra el conjunto de filas del CSV mide la perdida directamente.

Limite honesto, que va en el resultado: el archivo tambien es un poller (cada ~1 h),
asi que si MIROVA sobrescribio su imagen "Last" dos veces entre dos capturas, el
archivo tambien perdio esa pasada. Una pasada que perdieron LOS DOS no entra en
ninguno de los dos terminos, asi que lo medido es una **cota SUPERIOR** de la
cobertura real del CSV: el CSV puede perder mas de lo que este numero dice, nunca
menos.

Read-only. Escribe solo su JSON.
"""
import collections
import csv
import datetime as dt
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
ARCH = os.path.join(os.path.dirname(ROOT), "mirova-tif-archive")
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import ALIAS                                    # noqa: E402

ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}
SEN_TIF = {"MODIS": "modis", "VIIRS750": "v750", "VIIRS375": "v375"}
SEN_CSV = {"MODIS": "modis", "VIIRS": "v750", "VIIRS375": "v375"}
TOL_MIN = 30

# ── 1. El DENOMINADOR: las pasadas que MIROVA publico (archivo de TIF) ──────
pasadas = set()
for r in csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8")):
    vol = ALIAS_TIF.get(r["volcano"], r["volcano"])
    m = re.search(r"(\d{8})_(\d{6})", os.path.basename(r["tif_path"]))
    if not m:
        continue
    pasadas.add((vol, SEN_TIF[r["sensor"]],
                 dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")))
pasadas = sorted(pasadas)
if not pasadas:
    raise SystemExit("sin pasadas")
V0, V1 = min(p[2] for p in pasadas), max(p[2] for p in pasadas)

# ── 2. El NUMERADOR: las filas del CSV en la misma ventana ────────────────
filas = collections.defaultdict(list)
tipos = collections.Counter()
for r in csv.DictReader(open(os.path.join(ROOT, "latest_consolidado.csv"),
                             encoding="utf-8", errors="replace")):
    nom = (r.get("Volcan") or "").strip()
    vol = next((v for v, al in ALIAS.items() if nom in al), None)
    b = SEN_CSV.get((r.get("Sensor") or "").strip().upper())
    f = (r.get("Fecha_Satelite_UTC") or "").strip()
    if vol is None or b is None or len(f) < 16:
        continue
    try:
        t = dt.datetime.fromisoformat(f[:19].replace("Z", ""))
    except ValueError:
        continue
    if not (V0 - dt.timedelta(hours=2) <= t <= V1 + dt.timedelta(hours=2)):
        continue
    filas[(vol, b)].append((t, r.get("Tipo_Registro") or "", r.get("VRP_MW") or ""))
    tipos[r.get("Tipo_Registro") or ""] += 1

# ── 3. El cruce, pasada a pasada ─────────────────────────────────────────
det = []
for vol, b, t in pasadas:
    cand = filas.get((vol, b), [])
    dmin = min((abs((c[0] - t).total_seconds()) / 60.0 for c in cand), default=None)
    hit = dmin is not None and dmin <= TOL_MIN
    tipo = None
    if hit:
        tipo = min(cand, key=lambda c: abs((c[0] - t).total_seconds()))[1]
    det.append({"vol": vol, "sensor": b, "ts": t.isoformat(),
                "en_csv": hit, "delta_min": round(dmin, 1) if dmin is not None else None,
                "tipo": tipo})

# ── 4. Estratificado por SENSOR y por VOLCAN (regla S126) ────────────────
def cobertura(sel):
    n = len(sel)
    h = sum(1 for d in sel if d["en_csv"])
    return {"pasadas_archivo": n, "en_csv": h, "perdidas": n - h,
            "cobertura_pct": round(100.0 * h / n, 1) if n else None}


por_sensor = {s: cobertura([d for d in det if d["sensor"] == s])
              for s in sorted({d["sensor"] for d in det})}
por_volcan = {v: cobertura([d for d in det if d["vol"] == v])
              for v in sorted({d["vol"] for d in det})}
por_vs = {f"{v}|{s}": cobertura([d for d in det if d["vol"] == v and d["sensor"] == s])
          for v in sorted({d["vol"] for d in det})
          for s in sorted({d["sensor"] for d in det})}

R = {"_meta": {
        "ventana": [V0.isoformat(), V1.isoformat()],
        "tolerancia_min": TOL_MIN,
        "denominador": "pasadas unicas del archivo de TIF (volcan, sensor, timestamp)",
        "numerador": "filas de latest_consolidado.csv que emparejan dentro de la tolerancia",
        "limite": "el archivo tambien es un poller (~1 h): la cobertura medida es una "
                  "COTA SUPERIOR de la del CSV. El CSV puede perder mas, nunca menos.",
        "tipos_de_registro_en_ventana": dict(tipos)},
     "global": cobertura(det), "por_sensor": por_sensor, "por_volcan": por_volcan,
     "por_volcan_sensor": por_vs, "detalle": det}
out = os.path.join(AQUI, "03_cobertura_csv.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("escrito:", out)

print("\nventana:", V0, "->", V1)
print("tipos de registro del CSV en la ventana:", dict(tipos))
print("\nGLOBAL:", json.dumps(R["global"], ensure_ascii=False))
print("\n%-10s %10s %8s %10s %11s" % ("sensor", "archivo", "en_csv", "perdidas", "cobertura%"))
for s, c in por_sensor.items():
    print("%-10s %10d %8d %10d %10s%%" % (s, c["pasadas_archivo"], c["en_csv"],
                                          c["perdidas"], c["cobertura_pct"]))
print("\n%-22s %10s %8s %10s %11s" % ("volcan", "archivo", "en_csv", "perdidas", "cobertura%"))
for v, c in por_volcan.items():
    print("%-22s %10d %8d %10d %10s%%" % (v, c["pasadas_archivo"], c["en_csv"],
                                          c["perdidas"], c["cobertura_pct"]))
print("\nPor volcan x sensor (cobertura %):")
sens = sorted({d["sensor"] for d in det})
print("%-22s" % "volcan" + "".join("%12s" % s for s in sens))
for v in sorted({d["vol"] for d in det}):
    print("%-22s" % v + "".join("%12s" % por_vs[f"{v}|{s}"]["cobertura_pct"] for s in sens))
