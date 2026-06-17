"""S112 Parte B (Test1-lowmag) — audit A/B con criterio PRE-REGISTRADO (A66, A10, A62).

Objetivo: elegir el brazo de cuantificacion que reproduce la magnitud "Muy Bajo" de las
ALERTAS VIIRS375 de la reactivacion de Nevados de Chillan (MIROVA 0.02-0.49, mediana 0.06)
SIN inflar las noches RUTINA, estratificado por los 3 nevados lbg_global_compatible
(NdC/Lascar/Lastarria) donde el riesgo de inflacion se concentra.

REGLAS:
  - Cruce SIEMPRE con pc.vrp_mw (primary_cluster), NO record.vrp_mw (A10).
  - VIIRS375 = sensor VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21 (sin _750; A48).
  - Cruce vs MIROVA = veredicto (A62): el PASS mecanico no basta.

CRITERIO PRE-REGISTRADO (endurecido tras review adversarial S112):
  ALERTA: para cada ALERTA VIIRS375 NdC NOCTURNA (elevacion solar<=0, igual que el
    pipeline) que DETECTAMOS (triggered_test1=True), error = |log10(max(ours_pc, FLOOR)/
    mirova_vrp)|. Reportamos MEDIANA y MAXIMO. Las ALERTAS con t1=False = FN de DETECCION
    (Parte C), se cuentan como recall perdido (n_detect) y se reportan aparte.
  RUTINA (inflacion): por (vol, brazo), contar las PASADAS RUTINA NOCTURNAS (MIROVA
    VIIRS375 no-ALERTA) donde nuestro pc.vrp_mw >= RUTINA_FLOOR. Estratificado por
    NdC/Lascar/Lastarria (match por-pasada +-MATCH_MIN, no por-fecha — recupera las
    sub-pasadas de Lascar/Lastarria).
  GANADOR: brazo que cumple TODO (gates pre-registrados):
    (1) banda ABSOLUTA: mediana err|log| <= ABS_MED_MAX (=0.3, ~factor 2 de MIROVA);
    (2) sin outlier peligroso: MAX err|log| <= ABS_MAX_MAX (=0.7, ~factor 5) -> ninguna
        ALERTA sobre/sub-disparada >5x (atrapa la falsa "HIGH" de varios MW);
    (3) recall: n_detect >= n_detect del baseline Q2 (no perder eventos, FN es el peor error);
    (4) no inflar: inflacion RUTINA (suma 3 nevados) <= baseline Q2;
    (5) mejorar vs baseline: mediana err <= baseline Q2.
    Entre los que cumplen, gana el de menor mediana err. Si NINGUNO -> NO adoptar,
    documentar (la senal puede estar bajo el limite de nuestra cuantificacion Wooster).
"""
import csv, io, json, math, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.store import _solar_elevation  # criterio noche/dia identico al pipeline

CONS = ROOT / "experiments" / "_s111_d11" / "mirova_fresh" / "cons.csv"
PROFILES = [
    "_t1lm_q0_control", "_t1lm_q2_global", "_t1lm_q3_ring24", "_t1lm_q3_ring35",
    "_t1lm_q3_ring15", "_t1lm_q4_te700", "_t1lm_q4_te1000", "_t1lm_q5_ntilocal",
    "_t1lm_q6_spatialcore",
]
BASELINE = "_t1lm_q2_global"
VOLS = {"Nevados de Chillan": "NevadosDeChillan", "Lascar": "Lascar",
        "Lastarria": "Lastarria", "Villarrica": "Villarrica"}
# coords vent (volcanoes.yaml) para elevacion solar / clasificacion noche
VOL_COORDS = {"Nevados de Chillan": (-36.863, -71.377), "Lascar": (-23.37, -67.73),
              "Lastarria": (-25.168, -68.507), "Villarrica": (-39.42, -71.93)}
VIIRS375 = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}
MATCH_MIN = 12.0       # tolerancia de match de pasada (min); pasadas legitimas del MISMO
                       # satelite estan >90min apart, 18min => satelite distinto
ALERTA_FLOOR = 1e-4
RUTINA_FLOOR = 0.01    # MW
ABS_MED_MAX = 0.3      # mediana err|log| (~factor 2)
ABS_MAX_MAX = 0.7      # max err|log| (~factor 5)


def parse_dt(s):
    s = str(s).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s[:19] if len(s) >= 19 else s, fmt)
        except ValueError:
            continue
    return None


def is_night(vol_mirova, dt):
    lat, lon = VOL_COORDS[vol_mirova]
    return _solar_elevation(lat, lon, dt) <= 0.0


def load_mirova():
    """-> {vol: {'alerta':[(dt,vrp)], 'rutina':[dt]}} VIIRS375 NOCTURNAS."""
    out = {v: {"alerta": [], "rutina": []} for v in VOLS}
    with open(CONS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") not in VOLS or row.get("Sensor") != "VIIRS375":
                continue
            dt = parse_dt(row.get("Fecha_Satelite_UTC"))
            if dt is None:
                continue
            try:
                vrp = float(row.get("VRP_MW") or 0.0)
            except ValueError:
                vrp = 0.0
            v = row["Volcan"]
            night = is_night(v, dt)
            if row.get("Tipo_Registro") == "ALERTA_TERMICA" and vrp > 0:
                out[v]["alerta"].append((dt, vrp, night))
            elif night:  # RUTINA: solo pasadas nocturnas (procesamos night-only)
                out[v]["rutina"].append(dt)
    return out


def load_ours(profile, volfile):
    p = ROOT / "data" / profile / f"{volfile}.json"
    if not p.exists():
        return None
    doc = json.loads(p.read_text(encoding="utf-8"))
    recs = doc["records"] if isinstance(doc, dict) else doc
    out = []
    for r in recs:
        if r.get("sensor", "") not in VIIRS375:
            continue
        dt = parse_dt(r.get("datetime_utc") or r.get("timestamp_utc") or "")
        if dt is None:
            continue
        pc = r.get("primary_cluster") or {}
        out.append({"dt": dt, "t1": bool(r.get("triggered_test1")),
                    "pc_vrp": float(pc.get("vrp_mw") or 0.0)})
    return out


def match_pass(ours, dt):
    cands = [o for o in ours if abs((o["dt"] - dt).total_seconds()) / 60.0 <= MATCH_MIN]
    if not cands:
        return None, 0
    best = min(cands, key=lambda o: abs((o["dt"] - dt).total_seconds()))
    return best, len(cands)


def audit():
    mirova = load_mirova()
    print("=== Ground truth MIROVA VIIRS375 nocturno (CONS fresco) ===", flush=True)
    for v in VOLS:
        aln = [a for a in mirova[v]["alerta"] if a[2]]
        print(f"  {v:22s} ALERTAS_noct={len(aln)} RUTINA_pasadas_noct={len(mirova[v]['rutina'])}",
              flush=True)

    summary = {}
    base_q2 = {}
    for prof in PROFILES:
        ndc = load_ours(prof, "NevadosDeChillan")
        if ndc is None:
            print(f"\n[{prof}] SIN DATA (correr gather primero)", flush=True)
            continue
        errs, rows, n_fn, ambiguous = [], [], 0, 0
        for (dt, vrp, night) in sorted(mirova["Nevados de Chillan"]["alerta"]):
            if not night:
                rows.append((dt, vrp, "DIURNA(skip)", None, None)); continue
            m, ncand = match_pass(ndc, dt)
            if ncand > 1:
                ambiguous += 1
            if m is None:
                rows.append((dt, vrp, "sin-pasada", None, None)); continue
            if not m["t1"]:
                n_fn += 1
                rows.append((dt, vrp, "FN-deteccion(t1=F)", m["pc_vrp"], None)); continue
            err = abs(math.log10(max(m["pc_vrp"], ALERTA_FLOOR) / vrp))
            errs.append(err)
            rows.append((dt, vrp, "DETECTADA", m["pc_vrp"], round(err, 2)))
        med_err = (sorted(errs)[len(errs) // 2] if errs else None)
        max_err = (max(errs) if errs else None)
        # RUTINA inflation por-pasada estratificada
        infl = {}
        for vname, vfile in [("Nevados de Chillan", "NevadosDeChillan"),
                             ("Lascar", "Lascar"), ("Lastarria", "Lastarria")]:
            ours = load_ours(prof, vfile)
            if ours is None:
                infl[vfile] = None; continue
            c = 0
            for dt in mirova[vname]["rutina"]:
                m, _ = match_pass(ours, dt)
                if m is not None and m["pc_vrp"] >= RUTINA_FLOOR:
                    c += 1
            infl[vfile] = c
        infl_total = sum(x for x in infl.values() if x is not None)
        summary[prof] = {"med_err": med_err, "max_err": max_err, "n_detect": len(errs),
                         "n_fn": n_fn, "infl": infl, "infl_total": infl_total,
                         "ambiguous": ambiguous}
        if prof == BASELINE:
            base_q2 = summary[prof]
        print(f"\n=== {prof} ===", flush=True)
        for (dt, vrp, status, ours_vrp, err) in rows:
            ov = f"{ours_vrp:.3f}" if ours_vrp is not None else "  -  "
            es = f" err|log|={err}" if err is not None else ""
            print(f"  {dt}  MIROVA={vrp:.2f}  ours_pc={ov}  {status}{es}", flush=True)
        me = f"{med_err:.2f}" if med_err is not None else "n/a"
        mx = f"{max_err:.2f}" if max_err is not None else "n/a"
        print(f"  -> det={len(errs)} FN={n_fn} ambiguos={ambiguous} | med_err={me} max_err={mx}",
              flush=True)
        print(f"  -> inflacion RUTINA (pasadas>={RUTINA_FLOOR}MW): "
              f"NdC={infl.get('NevadosDeChillan')} Lascar={infl.get('Lascar')} "
              f"Lastarria={infl.get('Lastarria')} TOTAL={infl_total}", flush=True)

    # --- VEREDICTO ---
    print("\n" + "=" * 64, flush=True)
    print("VEREDICTO (criterio pre-registrado A66/A10/A62, endurecido S112)", flush=True)
    if not base_q2:
        print("  baseline Q2 SIN DATA — no se puede emitir veredicto", flush=True)
    else:
        print(f"  baseline {BASELINE}: med_err={base_q2['med_err']} "
              f"max_err={base_q2['max_err']} n_detect={base_q2['n_detect']} "
              f"infl={base_q2['infl_total']}", flush=True)
        winners = []
        for prof, s in summary.items():
            if prof in ("_t1lm_q0_control", BASELINE) or s["med_err"] is None:
                continue
            g_band = s["med_err"] <= ABS_MED_MAX
            g_outlier = (s["max_err"] is not None) and (s["max_err"] <= ABS_MAX_MAX)
            g_recall = s["n_detect"] >= base_q2["n_detect"]
            g_infl = s["infl_total"] <= base_q2["infl_total"]
            g_beat = (base_q2["med_err"] is None) or (s["med_err"] <= base_q2["med_err"])
            ok = g_band and g_outlier and g_recall and g_infl and g_beat
            fails = [n for n, g in [("banda", g_band), ("outlier", g_outlier),
                     ("recall", g_recall), ("infla", g_infl), ("nomejora", g_beat)] if not g]
            tag = "OK" if ok else "FALLA:" + ",".join(fails)
            print(f"  {prof:22s} med={s['med_err']:.2f} max={s['max_err']:.2f} "
                  f"det={s['n_detect']} infl={s['infl_total']} -> {tag}", flush=True)
            if ok:
                winners.append((s["med_err"], prof))
        if winners:
            w = sorted(winners)[0]
            print(f"\n  GANADOR: {w[1]} (med_err={w[0]:.2f}) — cumple banda+outlier+"
                  f"recall+no-infla+mejora", flush=True)
        else:
            print("\n  NINGUN brazo cumple TODOS los gates -> NO adoptar / documentar "
                  "(senal posiblemente bajo el limite de la cuantificacion Wooster)",
                  flush=True)
    out = ROOT / "experiments" / "_s112_test1_lowmag" / "t1lm_ab_audit.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResumen -> {out}", flush=True)


if __name__ == "__main__":
    audit()
