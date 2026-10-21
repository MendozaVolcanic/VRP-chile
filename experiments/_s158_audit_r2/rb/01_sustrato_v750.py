"""Sustrato en producción (data/mirova_equivalent, 11 Tier A):
(a) Counter de sensores (A48) para no clasificar a ciegas;
(b) para VIIRS 750 (sufijo _750): cuántos records tienen primer pase = 0 y recaptura del segundo
    pase > 0 (detección que existe SÓLO por el segundo pase, que no lleva compuerta de BT), y cuántos
    tienen recaptura > 0 en general; ventana: todo el corpus y además desde 2026-09-18 (datos con K);
(c) records por día y sensor para Chaitén y NdC entre 2026-10-10 y 2026-10-20 (para la afirmación 4).
Pregunta 1: si el segundo pase no corriera nunca, diag_n_second_pass_recapture sería 0 en todos;
el control positivo es que haya records con recaptura > 0. Pregunta 2: si el campo no existiera el
script lo cuenta como 'sin campo' aparte, no como 0."""
import sys, io, json, glob, os
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\data\mirova_equivalent"
TIER_A = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
sens = Counter(); tot = 0
v750 = []
por_dia = defaultdict(Counter)
for v in TIER_A:
    with open(os.path.join(D, v + ".json"), encoding="utf-8") as fh:
        d = json.load(fh)
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    for r in recs:
        tot += 1; s = r.get("sensor"); sens[s] += 1
        if s and s.endswith("_750"):
            v750.append((v, r))
        if v in ("Chaiten", "NevadosDeChillan"):
            dt = (r.get("datetime_utc") or "")[:10]
            if "2026-10-10" <= dt <= "2026-10-20":
                por_dia[(v, dt)][s] += 1
print("records totales 11 Tier A:", tot)
print("Counter sensores:", dict(sens))
print("\nVIIRS 750: n =", len(v750))
fechas = sorted((r.get("datetime_utc") or "") for _, r in v750)
print("  ventana datetime_utc:", fechas[0], "..", fechas[-1])
def resumen(items, titulo):
    n = len(items); sin = 0; fp0_rec = 0; rec_pos = 0; fp_pos = 0; anom_pos = 0; fp0_rec_anom = 0
    por_vol = Counter(); por_vol_n = Counter()
    for v, r in items:
        por_vol_n[v] += 1
        if "diag_n_second_pass_recapture" not in r or "diag_n_first_pass_pixels" not in r:
            sin += 1; continue
        fp = r["diag_n_first_pass_pixels"] or 0; sp = r["diag_n_second_pass_recapture"] or 0
        na = r.get("n_anomalous_pixels") or 0
        if fp > 0: fp_pos += 1
        if sp > 0: rec_pos += 1
        if na > 0: anom_pos += 1
        if fp == 0 and sp > 0:
            fp0_rec += 1; por_vol[v] += 1
            if na > 0: fp0_rec_anom += 1
    print(f"\n{titulo}: n={n} sin_campo={sin}")
    print(f"  primer pase > 0: {fp_pos}  |  recaptura > 0: {rec_pos}  |  n_anomalous_pixels > 0: {anom_pos}")
    print(f"  primer pase = 0 Y recaptura > 0 (detección solo del segundo pase): {fp0_rec} ({100*fp0_rec/max(1,n-sin):.1f} % de los con campo); de ellos con n_anomalous_pixels>0: {fp0_rec_anom}")
    print("  por volcán (fp=0 & rec>0 / n):", {v: f"{por_vol[v]}/{por_vol_n[v]}" for v in TIER_A})
resumen(v750, "VIIRS 750, todo el corpus")
resumen([(v, r) for v, r in v750 if (r.get("datetime_utc") or "") >= "2026-09-18"], "VIIRS 750, desde 2026-09-18 (datos con K)")
# distribución de recaptura cuando fp=0
c = Counter()
for v, r in v750:
    if r.get("diag_n_first_pass_pixels", None) == 0 and (r.get("diag_n_second_pass_recapture") or 0) > 0:
        c[r["diag_n_second_pass_recapture"]] += 1
print("\n  histograma de n_second_pass_recapture cuando primer pase = 0:", dict(sorted(c.items())[:15]))
# y sumas de pixeles: cuanto del total de pixeles alertados viene del segundo pase
sfp = sum((r.get("diag_n_first_pass_pixels") or 0) for _, r in v750); ssp = sum((r.get("diag_n_second_pass_recapture") or 0) for _, r in v750)
print(f"  píxeles: suma primer pase={sfp}, suma recaptura={ssp}, fracción recaptura={ssp/max(1,sfp+ssp):.3f}")
print("\nRecords por día y sensor, Chaitén y NdC, 2026-10-10..2026-10-20 (producción):")
for k in sorted(por_dia): print("  ", k, dict(por_dia[k]))
for v in ("Chaiten", "NevadosDeChillan"):
    for dt in ("2026-10-12", "2026-10-13", "2026-10-18"):
        if (v, dt) not in por_dia: print(f"   {v} {dt}: SIN RECORDS en producción")
