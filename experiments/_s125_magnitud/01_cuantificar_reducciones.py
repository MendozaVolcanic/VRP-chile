"""S125 — cuantifica cuanto recortan las dos reducciones aguas abajo de Eq.8.

POR QUE: la cadena de MAGNITUD nunca se auditó file:line. El eje 6 de la
auditoría S125 identificó dos reducciones que se aplican SOBRE la suma final
del cluster (no sobre el fondo que las motiva):

  R1 `cluster_focal_vrp_mw` (vrp_regimes.py) — suma solo pixeles contextualmente
     anomalos; si ninguno lo es, colapsa al pixel pico ("degraded").
  R2 `apply_single_pixel_mode` (single_pixel_mode.py) — si vrp<5MW y n<=3,
     reemplaza la SUMA por el MAXIMO per-pixel.

Este script NO transcribe numeros a mano (regla S91): recomputa todo desde los
JSON operacionales y persiste el resultado en 01_resultado.json.

Reporta DISTRIBUCION, no solo mediana (tecnica T3): una mediana de 1.0 puede
ser "sin efecto" o "efectos que se cancelan".
"""
import json, glob, os, statistics as st

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mirova_equivalent")
out = {"por_volcan": {}, "global": {}}

tot = foc = deg = spm = 0
ratios_spm = []          # suma/max en los records que R2 tocó
por_vol_deg = {}

for path in sorted(glob.glob(os.path.join(BASE, "*.json"))):
    vol = os.path.basename(path)[:-5]
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        out["por_volcan"][vol] = {"error": str(e)}
        continue
    recs = d if isinstance(d, list) else d.get("records", [])
    v_tot = v_foc = v_deg = v_spm = 0
    v_ratios = []
    for r in recs:
        pc = r.get("primary_cluster") or {}
        if not pc:
            continue
        v_tot += 1
        # R1: el campo n_focal/degraded lo persiste cluster_focal_vrp_mw
        if pc.get("focal_magnitude") is not None or pc.get("n_focal") is not None:
            v_foc += 1
            if pc.get("focal_degraded") or pc.get("degraded"):
                v_deg += 1
        # R2
        if pc.get("single_pixel_mode") is True:
            v_spm += 1
            pp = pc.get("per_pixel_vrp") or r.get("per_pixel_vrp")
            if pp:
                s, m = float(sum(pp)), float(max(pp))
                if m > 0:
                    v_ratios.append(s / m)
    tot += v_tot; foc += v_foc; deg += v_deg; spm += v_spm
    ratios_spm += v_ratios
    por_vol_deg[vol] = {"records_pc": v_tot, "focal": v_foc,
                        "degraded": v_deg, "single_pixel_mode": v_spm,
                        "pct_degraded": round(100*v_deg/v_foc, 1) if v_foc else None}

def dist(xs):
    if not xs:
        return None
    xs = sorted(xs)
    n = len(xs)
    return {"n": n, "min": round(xs[0], 3), "p25": round(xs[n//4], 3),
            "mediana": round(st.median(xs), 3), "p75": round(xs[3*n//4], 3),
            "p90": round(xs[int(0.9*n)], 3), "max": round(xs[-1], 3),
            "pct_mayor_a_1": round(100*sum(1 for x in xs if x > 1.001)/n, 1)}

out["por_volcan"] = por_vol_deg
out["global"] = {
    "records_con_primary_cluster": tot,
    "records_con_magnitud_focal": foc,
    "records_degradados_a_1px": deg,
    "pct_degradados": round(100*deg/foc, 1) if foc else None,
    "records_single_pixel_mode": spm,
    "pct_single_pixel_mode": round(100*spm/tot, 1) if tot else None,
    "ratio_suma_sobre_max_en_R2": dist(ratios_spm),
}
dest = os.path.join(os.path.dirname(__file__), "01_resultado.json")
json.dump(out, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(out["global"], indent=2, ensure_ascii=False))
print("\n-- top volcanes por % degradado --")
for v, s in sorted(por_vol_deg.items(), key=lambda kv: -(kv[1]["pct_degradado"] if False else (kv[1]["pct_degraded"] or -1)))[:12]:
    if s["focal"]:
        print(f"  {v:<26} focal={s['focal']:>5}  degradados={s['degraded']:>5} ({s['pct_degraded']}%)  spm={s['single_pixel_mode']}")
print("\npersistido en", dest)
