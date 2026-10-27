"""S165, issue #915, item 3: ¿las magnitudes bajas son pocas noches raras, régimen débil, cenit u otra cosa?

Solo lectura, sobre el mismo árbol de origin/main que detalle_issue915.py (git archive, sha en SHA.txt) y con la
misma regla por noche que el auto-audit (scripts/auto_audit_weekly.py::evaluar_detector, magnitud publicada:
max(pub) de la noche / max VRP de alerta de MIROVA de la noche). Referencia: latest_consolidado.csv (copia de hoy).

Agrega por noche, sobre la pasada nuestra que publica el máximo:
  - r_centro: distancia del centroide del cúmulo al centro de MIROVA (su origen de Distancia_km), y
    sep_min = |r_centro - Distancia_km de MIROVA|: COTA INFERIOR de la separación entre los dos objetos (A93: dos
    radios sin acimut no dan la distancia entre puntos; una cota grande prueba objeto distinto, una chica no prueba
    el mismo).
  - contraste: BT máxima de los píxeles anómalos a <= 1,5 km del centroide menos t_bg_k del record.
Y por celda: Spearman de la razón contra cenit, contra el VRP de MIROVA y contra el contraste.

Centro de MIROVA: volcanoes.yaml (mirova_center_lat/lon) para PCC y Chillán; para Tupungatito, que no lo trae
(S65 lo quitó), el de experiments/_s158_tupungatito/f_espacial_salida.txt (-33.42694, -69.80039).
"""
import importlib
import math
import os
import statistics
import sys

import yaml
from scipy.stats import spearmanr

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "D:/vrp-trabajo/temporales/s165_issue915/main")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)
aw = importlib.import_module("auto_audit_weekly")
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

aw.CONS = os.path.join(ROOT, "latest_consolidado.csv")
win = ("2026-08-27", "2026-10-26")
hoy = aw.datetime.fromisoformat("2026-10-26").date()
print(f"sha main: {open(os.path.join(ROOT, 'SHA.txt')).read().strip()}  consolidado: {aw.CONS}  ventana {win}")

vy = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
vy = vy if isinstance(vy, list) else vy.get("volcanoes", vy)
CENTRO = {v["name"]: (v.get("mirova_center_lat"), v.get("mirova_center_lon")) for v in vy}
CENTRO["Tupungatito"] = (-33.42694, -69.80039)


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


frontera = aw.leer_frontera_k()
vig = aw.detector_vigente(frontera)
alertas = aw.alertas_mirova(cons=aw.CONS, ocr=aw.OCR, historico=aw.HISTORICO)
coords = aw._coords_por_volcan()
filas = cargar_referencia_unificada(aw.CONS, aw.OCR)
mir, inst, _ = aw.noches_mirova_con_instante(aw.aplicar_d9(alertas, aw.REGLA_MINIMAS, filas), coords, win)
mir, _ = aw.partir_por_plataformas(mir, aw.juzga_desde(aw.leer_ceses()[0], hoy))
rpv, _ = aw.cargar_records()
ours = aw.nuestros_por_noche(rpv, win, frontera)["ours"]
idx = {(v, r.get("datetime_utc"), aw.our_bucket(r.get("sensor", ""))): r for v, rs in rpv.items() for r in rs}
ref = {}
for f in filas:
    if bp.es_alerta(f.get("tipo")):
        ref.setdefault((f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]), []).append(f)

CELDAS = ["NevadosDeChillan|MODIS", "NevadosDeChillan|VIIRS375", "NevadosDeChillan|VIIRS750",
          "PuyehueCordonCaulle|VIIRS750", "Tupungatito|VIIRS375"]
for celda in CELDAS:
    vol, s = celda.split("|")
    cen = CENTRO[vol]
    filas_n = []
    for (v, s2, fecha), m in sorted(mir.items()):
        if (v, s2) != (vol, s) or aw.detector_de_noche(fecha, frontera) != vig:
            continue
        o = ours.get((v, s2, fecha))
        if not (o and o["dash"]) or m <= 0:
            continue
        i = max(range(len(o["pub"])), key=lambda j: o["pub"][j])
        r = idx.get((v, o["dt_pub"][i], s2)) or {}
        pc = r.get("primary_cluster") or {}
        c = (pc.get("centroid_lat"), pc.get("centroid_lon"))
        r_c = round(hav(c, cen), 2) if None not in c else None
        fm = ref.get((v, s2, (inst.get((v, s2, fecha)) or "")[:16]), [])
        dm = [f["dist_km"] for f in fm if f.get("dist_km") is not None]
        sep = round(min(abs(r_c - d) for d in dm), 2) if (dm and r_c is not None) else None
        px = [p for p in (r.get("anomaly_pixels") or []) if None not in c and p.get("bt_k")
              and hav((p["lat"], p["lon"]), c) <= 1.5]
        tb = r.get("t_bg_k")
        contr = round(max(p["bt_k"] for p in px) - tb, 2) if (px and tb) else None
        filas_n.append(dict(fecha=fecha, mir=round(m, 3), razon=round(o["pub"][i] / m, 3), z=o["z_pub"][i],
                            r_centro=r_c, dist_mirova=dm, sep_min=sep, contraste=contr,
                            fuentes="+".join(sorted({f["source"] for f in fm}))))
    print("\n" + "-" * 90 + f"\n{celda} (centro MIROVA {cen}), n={len(filas_n)}")
    print("fecha       MIROVA  razon   z      r_centro dist_MIROVA     sep_min  contraste fuente")
    for f in filas_n:
        print(f"{f['fecha']}  {f['mir']:>6}  {f['razon']:>6}  {str(f['z']):<6} {str(f['r_centro']):<8} "
              f"{str(f['dist_mirova']):<15} {str(f['sep_min']):<8} {str(f['contraste']):<9} {f['fuentes']}")
    rz = [f["razon"] for f in filas_n]
    for nombre, clave in (("cenit", "z"), ("VRP MIROVA", "mir"), ("contraste", "contraste")):
        par = [(f[clave], f["razon"]) for f in filas_n if f[clave] is not None]
        if len(par) >= 5:
            rho, p = spearmanr([a for a, _ in par], [b for _, b in par])
            print(f"  Spearman razon vs {nombre}: rho={rho:.3f} p={p:.3f} (n={len(par)})")
    lejos = [f for f in filas_n if f["sep_min"] is not None and f["sep_min"] > 3]
    print(f"  noches con objeto DISTINTO probado (sep_min > 3 km): {len(lejos)} {[f['fecha'] for f in lejos]}")
    resto = [f["razon"] for f in filas_n if f not in lejos]
    if resto:
        print(f"  mediana sin esas noches: {round(statistics.median(resto), 3)} (n={len(resto)}); "
              f"con todas: {round(statistics.median(rz), 3)} (n={len(rz)})")
    con = [f for f in filas_n if f["contraste"] is not None]
    if con:
        print(f"  contraste mediano: {statistics.median([f['contraste'] for f in con])} K; "
              f"VRP MIROVA mediano: {statistics.median([f['mir'] for f in filas_n])} MW")
