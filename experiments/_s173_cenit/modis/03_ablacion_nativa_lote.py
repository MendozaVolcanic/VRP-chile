# -*- coding: utf-8 -*-
"""03 (S173): ablación por pieza de la vía MOD-D sobre los recortes NATIVOS del lote 40120713181 (S162 MOD-E), que
sí permiten quitar el remuestreo (D17) y cambiar la geolocalización en Windows, sin pyhdf.

POR QUE: 02 sólo puede cambiar lo que pasa después del remuestreo. Para saber si quitar el remuestreo (D17) hunde la
razón en las pasadas oblicuas hay que correr la vía sobre los píxeles nativos. El lote trae, por pasada, el recorte
nativo (B21, B22, B31, lat/lon del MxD03 y de la grilla de 5 km, cenit por píxel), el dayflag y el sun-glint de la
vía, y el record de K. Son 403 pasadas MODIS de 11 volcanes; sólo 3 son alertas de Chillán (todas sobre 50° de cenit) y 8
son alertas de Láscar (2 a 41°). No es la población de Chillán: es la única con nativos en disco.

P1: control V0 (las funciones de pipeline/mirova_v750_codigo.py sobre el recorte) contra el port `fisica` del lote
    (npix y VRP); X2 dobla la magnitud; NAT tiene que cambiar algo en las pasadas oblicuas (si no, el remuestreo no
    actúa y no hay nada que atribuir).
P2: un brazo que no se aplicara daría V0; se cuenta cuántas pasadas cambian. Pasada sin detección = VRP 0, contada.
Uso: python -B 03_ablacion_nativa_lote.py <raiz copia main> [<carpeta del lote>]
"""
import glob
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1]).resolve()
RUN = Path(sys.argv[2] if len(sys.argv) > 2 else r"C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181")
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import yaml  # noqa: E402
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.process_modis import merge_mir_bands  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
import banco_paridad as bp  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


exec(open(AQUI / "_estadistica.py", encoding="utf-8").read())

obj = {o["id"]: o for o in json.load(open(AQUI / "objetivos_neg_resto_modis.json", encoding="utf-8"))
       if o["b"] == "MODIS" and o["clase"] in ("neg_resto", "control_s159")}
res = {}
for f in sorted(RUN.glob("s162-negmodis-MODIS-*/resultados_MODIS_*.json")):
    for r in json.load(open(f, encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r


def evaluable(r):
    """Criterio de experiments/_s162_modis_bowtie/real/comun.py::evaluable (el del lector del lote)."""
    if not r or r.get("estado") != "ok" or not r.get("port"):
        return False
    f = r["port"].get("fisica") or {}
    if f.get("motivo_vacio") in ("escena_invalida", "sunglint"):
        return False
    return r.get("port_estado") != "grilla_incompleta"


vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ids = [i for i in sorted(obj) if evaluable(res.get(i))]
pr(f"== lote {RUN}: objetivos MODIS {len(obj)}, evaluables {len(ids)}")
out = {}
t0 = time.time()
for i in ids:
    o, r = obj[i], res[i]
    h = list(RUN.glob(f"s162-negmodis-MODIS-*/nativo_{i:04d}.npz"))
    if len(h) != 1:
        continue
    n = np.load(h[0])
    v = vols[o["volcan"]]
    g = MV.grilla_del_volcan(o["volcan"], paso_m=1000.0, clave_roi="roi_modis")
    rad = {"MIR": merge_mir_bands(n["b21"], n["b22"], True), "TIR": n["b31"]}
    vent = get_detection_anchor(v)
    b = PZ.correr_brazos(rad, n["lat_mxd03"].astype(np.float64), n["lon_mxd03"].astype(np.float64),
                         n["lat_5km"].astype(np.float64), n["lon_5km"].astype(np.float64), g, vent,
                         (v["lat"], v["lon"]), v.get("inner_radius_km"), o.get("sensor") or r.get("sensor", "MODIS"),
                         int(r["dayflag"]), float(r["sunglint"]), n["sensor_zenith"].astype(np.float64))
    kr = (r.get("K") or {}).get("record") or {}
    out[i] = {"volcan": o["volcan"], "hora": o["hora_utc"], "z": o["z"], "protegida": bool(o.get("protegida")),
              "clase": o["clase"], "mirova": o.get("mirova_vrp"), "port_npix": r["port"]["fisica"]["npix"],
              "port_vrp": r["port"]["fisica"]["vrp_mw"], "K_pc_vrp": (kr.get("primary_cluster") or {}).get("vrp_mw"),
              "K_dc": kr.get("distance_class"), "brazos": b}
pr(f"   corridas {len(out)} pasadas en {time.time() - t0:.0f} s")

# publicación de los brazos con record (grilla), predicado del tablero con node
inner = bp.inner_desde_html()
casos, idx = [], []
for i, e in out.items():
    for bn, br in e["brazos"].items():
        if "_record" not in br:
            continue
        rec = dict(br["_record"])
        slim = {k: rec.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                  for q in (rec.get("anomaly_pixels") or [])]
        casos.append([slim, inner[e["volcan"]]])
        idx.append((i, bn))
for (i, bn), p in zip(idx, bp.correr_node(casos)):
    out[i]["brazos"][bn]["publica"] = int(p[4])
for e in out.values():
    for br in e["brazos"].values():
        br.pop("_record", None)

pr("\n== controles")
v0 = [(e["brazos"]["V0"]["npix"], e["port_npix"], e["brazos"]["V0"]["vrp_mw"] or 0, round(e["port_vrp"] or 0, 3))
      for e in out.values()]
pr(f"  V0 (pipeline sobre el recorte) = port fisica del lote en npix: {sum(a == b for a, b, _, _ in v0)} de {len(v0)}; "
   f"en VRP a 1e-3: {sum(abs(c - d) <= 0.001 for _, _, c, d in v0)} de {len(v0)}")
det = [i for i, e in out.items() if e["brazos"]["V0"]["npix"]]
pr(f"  V0 detecta en {len(det)} pasadas")
pr(f"  X2 = 2 x V0 en {sum(abs(out[i]['brazos']['X2']['vrp_mw'] - 2 * out[i]['brazos']['V0']['vrp_mw']) <= 0.0015 for i in det)} de {len(det)}")
for bn in PZ.BRAZOS[1:]:
    ch = sum(abs((e["brazos"][bn]["vrp_mw"] or 0) - (e["brazos"]["V0"]["vrp_mw"] or 0)) > 0.0005
             or e["brazos"][bn]["npix"] != e["brazos"]["V0"]["npix"] for e in out.values())
    pr(f"  {bn}: npix o VRP distinto de V0 en {ch} de {len(out)}")
pr("  publicación (predicado del tablero) en neg_resto y en protegidas, brazos con record:")
for bn in ("V0", "FA", "FSH", "SC", "FA_SC", "RN", "G5"):
    nr = sum(e["brazos"][bn].get("publica", 0) for e in out.values() if e["clase"] == "neg_resto")
    pp = sum(e["brazos"][bn].get("publica", 0) for e in out.values() if e["protegida"])
    pr(f"     {bn:6s} neg_resto {nr} de {sum(e['clase'] == 'neg_resto' for e in out.values())}; protegidas {pp} de "
       f"{sum(e['protegida'] for e in out.values())}")

pr("\n== pasadas donde V0, NAT o K detectan (VRP MW; razón brazo/V0 entre paréntesis)")
cols = ["V0", "FA", "RN", "G5", "NAT", "NAT_AREA"]
pr(f"  {'id':>5s} {'volcan':18s} {'hora':16s} {'z':>5s} {'M':>6s} {'K':>6s} " + " ".join(f"{c:>14s}" for c in cols))
sel = [i for i, e in out.items() if e["brazos"]["V0"]["npix"] or e["brazos"]["NAT"]["npix"] or (e["K_pc_vrp"] or 0) > 0]
for i in sorted(sel, key=lambda i: out[i]["z"]):
    e = out[i]
    base = e["brazos"]["V0"]["vrp_mw"] or 0
    cc = []
    for c in cols:
        x = e["brazos"][c]["vrp_mw"] or 0
        cc.append(f"{x:7.3f}({(x / base) if base else float('nan'):5.2f})")
    pr(f"  {i:5d} {e['volcan']:18s} {e['hora']:16s} {e['z']:5.1f} {e['mirova'] or 0:6.2f} {e['K_pc_vrp'] or 0:6.3f} "
       + " ".join(cc) + ("  PROT" if e["protegida"] else ""))

pr("\n== protegidas (alertas de MIROVA >= 1 MW del lote): razón contra MIROVA por brazo, Spearman con el cenit")
prot = [e for e in out.values() if e["protegida"]]
zz = [e["z"] for e in prot]
resumen = {}
for bn in ("K",) + PZ.BRAZOS:
    rr = [((e["K_pc_vrp"] or 0) if bn == "K" else (e["brazos"][bn]["vrp_mw"] or 0)) / e["mirova"] for e in prot]
    rho, lo, hi = con_barajado(zz, rr)
    a = [x for x, z in zip(rr, zz) if z < 30]
    c = [x for x, z in zip(rr, zz) if z >= 30]
    resumen[bn] = {"spearman": rho, "barajado": [lo, hi], "z<30": {"n": len(a), "mediana": med(a)},
                   "z>=30": {"n": len(c), "mediana": med(c)}}
    pr(f"  {bn:8s} Spearman {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]  z<30 n {len(a)} mediana {med(a)}  z>=30 n {len(c)} "
       f"mediana {med(c)}")
pr("  (las 3 protegidas sobre 50° son las 3 de Chillán; el cenit está confundido con el volcán)")
json.dump({"pasadas": out, "resumen_protegidas": resumen}, open(AQUI / "03_salida.json", "w", encoding="utf-8"),
          indent=1, ensure_ascii=False, default=str)
(AQUI / "03_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
