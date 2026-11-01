# -*- coding: utf-8 -*-
"""V3 (verificador S158), hallazgo F3-H1: cúmulos de VIIRS 750 en 0,0 MW por el fondo escalar del anillo.

Pregunta 1 (¿vería el defecto?): sí; cuento records nocturnos con >=1 alertado cuyo cúmulo publicado vale 0,
  y RECOMPUTO por píxel L(bt)-L(t_bg_k) con la Planck del pipeline: si el 0 viniera de otra cosa (tope D9,
  piso, otro fondo) la recomputación no daría <=0 y lo separo.
Pregunta 2 (¿instrumento muerto?): control positivo de reconstrucción: en los píxeles con vrp_mw>0 persistido,
  mi 11,08*dL debe reproducir el vrp_mw persistido (redondeo 4 decimales). Si no, el fondo que reconstruyo no es
  el del pipeline y el conteo no vale.
Además: etiqueta de la referencia MIROVA (banco_paridad, regla SN, snapshot del repo) para saber si esas
  pasadas son alertas de MIROVA (pérdida) o negativos limpios (ocultarlas no cuesta).
Ventana: 2026-03-01 a 2026-10-21; noche = definición del pipeline (es_pasada_diurna_descartada).
Denominador: records VIIRS 750 nocturnos con n_anomalous_pixels>0 de los 11 Tier A.
"""
import sys, io, json, os, collections
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
from pipeline.process_viirs_mod import bt_to_spectral_radiance, M13_LAMBDA
import pipeline.profile as P

VENT = ("2026-03-01", "2026-10-21")
coords = _coords_por_volcan()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, nref = bp.indexar_referencia(filas, coords, VENT, regla_minimas="SN")
K = 0.5625e6 * 19.7 / 1e6  # área nadir 750 m * WOOSTER_COEFF / 1e6 -> MW por unidad de dL
print("perfil V750 fondo vecinos:", P.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750, "| K MW/dL =", K)
recs = []; ctrl = []
for vol in bp.VOLS:
    d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        if bp.bucket(r.get("sensor")) != "VIIRS750":
            continue
        t = r.get("datetime_utc", "")
        if not (VENT[0] <= t[:10] <= VENT[1]):
            continue
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        lat, lon = coords[vol]
        if es_pasada_diurna_descartada("VIIRS750", lat, lon, dt):
            continue
        n = r.get("n_anomalous_pixels") or 0
        if n == 0:
            continue
        pc = r.get("primary_cluster") or {}
        px = r.get("anomaly_pixels") or []
        tbg = r.get("t_bg_k")
        neg = None
        if tbg is not None and px:
            Lb = float(bt_to_spectral_radiance(np.float64(tbg), M13_LAMBDA))
            dl = [float(bt_to_spectral_radiance(np.float64(p["bt_k"]), M13_LAMBDA)) - Lb for p in px]
            neg = all(x <= 0 for x in dl)
            for p, x in zip(px, dl):
                if p["vrp_mw"] > 0:
                    ctrl.append((p["vrp_mw"], K * x))
            dmin = min(p["bt_k"] for p in px) - tbg
            dmax = max(p["bt_k"] for p in px) - tbg
        else:
            dmin = dmax = None
        recs.append({"vol": vol, "b": "VIIRS750", "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                     "pc0": pc and (pc.get("vrp_mw") or 0) <= 0, "has_pc": bool(pc),
                     "summit": r.get("distance_class") == "summit", "neg": neg, "completo": len(px) == n,
                     "capped": bool(pc.get("d9_capped")), "dmax": dmax, "tbg": tbg,
                     "vrp_rec": r.get("vrp_mw") or 0})
bp.etiquetar(recs, por_vb, ns, nv)
c = np.array(ctrl)
rel = np.abs(c[:, 0] - c[:, 1]) / np.maximum(c[:, 0], 1e-4)
print(f"CONTROL reconstrucción: {len(c)} píxeles con vrp>0; |rel err| mediana {np.median(rel):.4f}, p99 {np.percentile(rel,99):.4f}, máx {rel.max():.3f}")
print(f"records V750 nocturnos con alertados: {len(recs)}; sin primary_cluster: {sum(not r['has_pc'] for r in recs)}")
T = collections.defaultdict(collections.Counter)
for r in recs:
    k = r["vol"]
    T[k]["n"] += 1
    T[k]["pc0"] += r["pc0"]
    T[k]["pc0_summit"] += bool(r["pc0"] and r["summit"])
    T[k]["pc0_y_todo_neg"] += bool(r["pc0"] and r["neg"] and r["completo"])
    T[k]["pc0_no_explicado"] += bool(r["pc0"] and not (r["neg"] and r["completo"]))
    if r["pc0"]:
        T[k]["pc0_" + r["lab"]] += 1
    if r["pc0"] and r["summit"]:
        T[k]["pc0s_" + r["lab"]] += 1
    T[k]["lab_" + r["lab"]] += 1
cols = ["n", "pc0", "pc0_summit", "pc0_y_todo_neg", "pc0_no_explicado", "pc0s_pos", "pc0s_neg_limpio", "pc0s_sin_info",
        "pc0s_far_ref", "lab_pos"]
print("vol".ljust(20) + " ".join(c_.rjust(16) for c_ in cols))
tot = collections.Counter()
for v in bp.VOLS:
    print(v.ljust(20) + " ".join(str(T[v][c_]).rjust(16) for c_ in cols)); tot.update(T[v])
print("TOTAL".ljust(20) + " ".join(str(tot[c_]).rjust(16) for c_ in cols))
# recall de las alertas de MIROVA V750 que caen en pasadas con nuestro cúmulo en 0 (cumbre)
pos = [r for r in recs if r["lab"] == "pos"]
print(f"\npasadas V750 'pos' (MIROVA alertó) con record nuestro con alertados: {len(pos)}; de ellas cúmulo 0 MW: {sum(r['pc0'] for r in pos)}; cúmulo 0 y summit: {sum(r['pc0'] and r['summit'] for r in pos)}")
for v in bp.VOLS:
    pv = [r for r in pos if r["vol"] == v]
    if pv:
        print(f"   {v}: pos {len(pv)}, cúmulo 0 {sum(r['pc0'] for r in pv)}")
# exceso máximo del alertado sobre el fondo, en los cúmulos 0 de cumbre
dm = np.array([r["dmax"] for r in recs if r["pc0"] and r["summit"] and r["dmax"] is not None])
print(f"\ncúmulos 0 de cumbre: bt_max(alertados) - t_bg: mediana {np.median(dm):.2f} K, p10 {np.percentile(dm,10):.2f}, p90 {np.percentile(dm,90):.2f}, máx {dm.max():.2f} (n={len(dm)})")
print("capped D9 entre cúmulos 0:", sum(r["capped"] for r in recs if r["pc0"]))

# --- Parte 2: unidad del operador (noche de volcán) y magnitud que MIROVA publicó en esas pasadas ---
print("\n=== Parte 2: noches ===")
pub = collections.defaultdict(bool)   # (vol, noche) -> algún record nuestro (cualquier sensor) publicado en cumbre
for vol in bp.VOLS:
    d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        t = r.get("datetime_utc", "")
        if not (VENT[0] <= t[:10] <= VENT[1]):
            continue
        b = bp.bucket(r.get("sensor"))
        if b is None:
            continue
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        lat, lon = coords[vol]
        if es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        pc = r.get("primary_cluster") or {}
        valid = (pc.get("vrp_mw") or 0) > 0 if pc else ((r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1") is True)
        if valid and r.get("distance_class") == "summit":
            pub[(vol, dt.strftime("%Y-%m-%d"))] = True
perd = [r for r in recs if r["lab"] == "pos" and r["pc0"]]
noches = {(r["vol"], r["noche"]) for r in perd}
sin_otro = {k for k in noches if not pub[k]}
print(f"pasadas pos con cúmulo 0: {len(perd)} en {len(noches)} noches de volcán; noches sin NINGUNA otra publicación de cumbre (cualquier sensor): {len(sin_otro)}")
print("   por volcán:", dict(collections.Counter(v for v, _ in sin_otro)))
vr = []
for r in perd:
    fl = bp.parear(por_vb.get((r["vol"], "VIIRS750"), []), r["dt"])
    v = max([f["vrp_mw"] or 0 for f in fl if bp.es_alerta(f["tipo"])] or [0])
    vr.append(v)
vr = np.array(vr)
print(f"VRP de MIROVA en esas {len(vr)} pasadas: mediana {np.median(vr):.3f} MW, p90 {np.percentile(vr,90):.3f}, máx {vr.max():.3f}; >=1 MW (protegidas): {(vr>=1).sum()}")
