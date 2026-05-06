"""S33 R2 — verificación pre-implementación de la hipótesis VRP integrated Eq.1.

Sin descargar granules: usar anomaly_pixels (top-100 ya en JSON) para
simular el cálculo Eq.1 textual y comparar con:
  1. VRP operacional actual (per-pixel sum con clip ≥0).
  2. VRP MIROVA reportado en CSV.

Si la simulación Eq.1 da magnitudes consistentemente más cercanas a MIROVA
que el operacional, R2 confirma. Si NO, refuta la hipótesis antes de
implementar.

Records target (5 casos representativos):
  - Lastarria: worst ratio summit-only (test1 path, magnitud inflada).
  - Villarrica: alto ratio test1 path.
  - Chaiten: alto ratio test1 path.
  - Planchón: alto ratio test1 path.
  - Lascar: control (path BT dominante, NO Test 1 → cambio mínimo esperado).

Caveats:
  - anomaly_pixels tiene cap top-100. Records con >100 pixels Test 1
    (PCC ring) la simulación está incompleta — comparable solo direccional.
  - L_bg local del ring 1-3km no está exportado al JSON. Aproximamos con
    t_bg_k (anillo 5-25km global). Diferencia esperada despreciable salvo
    en volcanes con geotermal crónico cerca cráter (Tupungatito → no en
    nuestro target sample).
  - pixel_area por sensor: nadir aprox (sin corrección zenithal).
"""
from __future__ import annotations
import json, sys, io, math
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
DATA = ROOT / "data" / "mirova_equivalent"

# Constantes Planck (mismas que pipeline/constants.py)
C1 = 1.191042e8     # 2hc^2 (W/m²/sr/μm)
C2 = 14388.0        # hc/k (μm·K)

# Coeficientes Wooster por sensor
WOOSTER = {
    'MODIS': 18.9,        # B21 3.929 μm
    'VIIRS750': 19.7,     # M13 4.05 μm
    'VIIRS375': 18.0,     # I04 3.74 μm
}
LAMBDA = {
    'MODIS': 3.929,
    'VIIRS750': 4.050,
    'VIIRS375': 3.740,
}
PIXEL_AREA_NADIR_M2 = {
    'MODIS': 1_000_000,        # 1 km²
    'VIIRS750': 562_500,       # 750²
    'VIIRS375': 140_625,       # 375²
}

INNER_RADIUS_KM = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}


def planck_L(bt, lam_um):
    """Planck spectral radiance W/m²/sr/μm."""
    return C1 / (lam_um**5 * (np.exp(C2 / (lam_um * bt)) - 1))


def parse_csv_dt(s): return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)

def sensor_match(csv_s, rec_s):
    if csv_s == "MODIS": return rec_s.startswith("MODIS")
    if csv_s == "VIIRS": return rec_s.startswith("VIIRS_") and rec_s.endswith("_750")
    if csv_s == "VIIRS375": return rec_s.startswith("VIIRS_") and not rec_s.endswith("_750")
    return False

def sensor_bucket(rec_s):
    if rec_s.startswith("MODIS"): return "MODIS"
    if rec_s.endswith("_750"): return "VIIRS750"
    if rec_s.startswith("VIIRS_"): return "VIIRS375"
    return None


def vrp_eq1_simulated(record, sensor_b):
    """Simula la fórmula Eq.1 textual desde anomaly_pixels.

    VRP_int = max(0, k · Σ (L_obs - L_bg) · A_pix)

    Sin clip per-pixel. Usa todos los pixels en anomaly_pixels del record
    como proxy de los pixels Test 1 ROI.

    L_bg approximado con planck(t_bg_k) — anillo global 5-25km. En la
    implementación real usaríamos test1_L_bg_local del ring 1-3km, pero
    para verificación direccional t_bg global es razonable.
    """
    aps = record.get('anomaly_pixels') or []
    if not aps:
        return 0.0
    t_bg_k = record.get('t_bg_k')
    if t_bg_k is None:
        return 0.0
    lam = LAMBDA[sensor_b]
    pixel_area = PIXEL_AREA_NADIR_M2[sensor_b]
    k = WOOSTER[sensor_b]
    L_bg = planck_L(t_bg_k, lam)
    # Sumar (L_obs - L_bg) * A_pix sin clip per-pixel
    delta_L_neto_x_area = 0.0
    for p in aps:
        bt = p.get('bt_k')
        if bt is None or bt <= 0:
            continue
        L_obs = planck_L(bt, lam)
        delta_L_neto_x_area += (L_obs - L_bg) * pixel_area
    vrp = k * delta_L_neto_x_area / 1e6  # MW
    return max(0.0, vrp)


def vrp_summit_now(record, vol):
    """Replica mirova_eq_vrp con fix S33 (operacional actual)."""
    if not record:
        return 0
    pc = record.get('primary_cluster')
    if not pc:
        return record.get('vrp_mw') or 0
    if record.get('distance_class') and record.get('distance_class') != 'summit':
        return 0
    inner = INNER_RADIUS_KM.get(vol, 10)
    pc_dist = pc.get('centroid_dist_km')
    if pc_dist is not None and pc_dist > inner:
        return 0
    return pc.get('vrp_mw', 0)


# Targets: 5 casos worst ratio post-fix S33 + 1 control Lascar (path BT)
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[df['Tipo_Registro']=='ALERTA_TERMICA']

CSV_TO_OUR = {
    'Lastarria':'Lastarria', 'Villarrica':'Villarrica', 'Chaiten':'Chaiten',
    'PlanchonPeteroa':'PlanchonPeteroa', 'Lascar':'Lascar',
}

print("# R2 — Verificación pre-implementación VRP integrated Eq.1\n")
print(f"Política R2 (S33): NO implementar Eq.1 hasta confirmar dirección\n"
      f"empíricamente desde data ya en disco.\n")

print("| Volcán | Fecha UTC | Sensor | MIROVA MW | VRP actual | VRP Eq.1 sim | "
      "ratio actual | ratio Eq.1 | T1? | path | n_pix |")
print("|---|---|---|---:|---:|---:|---:|---:|:--:|---|---:|")

# Para cada volcán target, encontrar 1-2 worst-ratio records
for csv_v, our_v in CSV_TO_OUR.items():
    sub = df[df['Volcan']==csv_v]
    f = DATA / f"{our_v}.json"
    if not f.exists():
        continue
    raw = json.loads(f.read_text(encoding='utf-8'))
    recs = raw.get('records', [])

    # Compute ratio summit-only para cada referencia MIROVA
    candidates = []
    for _, row in sub.iterrows():
        ref_dt = row['dt']
        tol = timedelta(minutes=60)
        best, bd = None, tol + timedelta(seconds=1)
        for r in recs:
            try: rdt = parse_rec_dt(r['datetime_utc'])
            except: continue
            if not sensor_match(row['Sensor'], r.get('sensor','')): continue
            d = abs(rdt - ref_dt)
            if d <= tol and d < bd:
                best, bd = r, d
        if best is None: continue
        v_now = vrp_summit_now(best, our_v)
        if v_now <= 0: continue
        if row['VRP_MW'] <= 0: continue
        ratio = v_now / row['VRP_MW']
        sb = sensor_bucket(best.get('sensor', ''))
        if sb is None: continue
        v_eq1 = vrp_eq1_simulated(best, sb)
        ratio_eq1 = v_eq1 / row['VRP_MW']
        candidates.append({
            'dt': ref_dt, 'mirova_vrp': row['VRP_MW'], 'sensor': row['Sensor'],
            'v_now': v_now, 'v_eq1': v_eq1,
            'ratio_now': ratio, 'ratio_eq1': ratio_eq1,
            'rec': best,
        })

    # Top 1-2 peor ratio_now por volcán
    candidates.sort(key=lambda c: -c['ratio_now'])
    n_take = 1 if our_v == 'Lascar' else 1  # 1 por volcán para 5 total
    for c in candidates[:n_take]:
        rec = c['rec']
        path = rec.get('final_hotspot_source', 'eruption')
        n_pix = len(rec.get('anomaly_pixels') or [])
        print(f"| {our_v} | {c['dt'].strftime('%Y-%m-%d %H:%M')} | {c['sensor']} | "
              f"{c['mirova_vrp']:.3f} | {c['v_now']:.2f} | {c['v_eq1']:.2f} | "
              f"{c['ratio_now']:.1f} | {c['ratio_eq1']:.1f} | "
              f"{'Y' if rec.get('triggered_test1') else 'N'} | "
              f"{path} | {n_pix} |")

# Análisis agregado
print("\n## Análisis agregado: simulación Eq.1 vs actual sobre records test1\n")
all_pairs = []
for csv_v, our_v in CSV_TO_OUR.items():
    sub = df[df['Volcan']==csv_v]
    f = DATA / f"{our_v}.json"
    if not f.exists(): continue
    raw = json.loads(f.read_text(encoding='utf-8'))
    recs = raw.get('records', [])
    for _, row in sub.iterrows():
        ref_dt = row['dt']
        tol = timedelta(minutes=60)
        best, bd = None, tol + timedelta(seconds=1)
        for r in recs:
            try: rdt = parse_rec_dt(r['datetime_utc'])
            except: continue
            if not sensor_match(row['Sensor'], r.get('sensor','')): continue
            d = abs(rdt - ref_dt)
            if d <= tol and d < bd:
                best, bd = r, d
        if best is None: continue
        # SOLO records donde final_hotspot_source='test1'
        if best.get('final_hotspot_source') != 'test1': continue
        v_now = vrp_summit_now(best, our_v)
        if v_now <= 0: continue
        if row['VRP_MW'] <= 0: continue
        sb = sensor_bucket(best.get('sensor', ''))
        if sb is None: continue
        v_eq1 = vrp_eq1_simulated(best, sb)
        all_pairs.append({
            'volcan': our_v, 'mirova': row['VRP_MW'],
            'v_now': v_now, 'v_eq1': v_eq1,
            'ratio_now': v_now/row['VRP_MW'], 'ratio_eq1': v_eq1/row['VRP_MW'],
        })

if all_pairs:
    df_pairs = pd.DataFrame(all_pairs)
    print(f"Records con final_hotspot_source='test1' analizados: {len(df_pairs)}\n")
    print(f"Ratio mediano actual:    {df_pairs['ratio_now'].median():.2f}x")
    print(f"Ratio mediano Eq.1 sim:  {df_pairs['ratio_eq1'].median():.2f}x")
    pct_lower = (df_pairs['ratio_eq1'] < df_pairs['ratio_now']).mean() * 100
    print(f"Records donde Eq.1 < actual: {pct_lower:.0f}%")
    avg_reduction = (1 - df_pairs['ratio_eq1'] / df_pairs['ratio_now']).median() * 100
    print(f"Reducción mediana de ratio: {avg_reduction:.0f}%")
    print(f"\nPor volcán:\n")
    for v, g in df_pairs.groupby('volcan'):
        print(f"  {v}: n={len(g)}, ratio actual={g['ratio_now'].median():.2f}, "
              f"Eq.1={g['ratio_eq1'].median():.2f}")

# Veredicto R2
print(f"\n## Veredicto R2\n")
if all_pairs:
    df_pairs = pd.DataFrame(all_pairs)
    median_now = df_pairs['ratio_now'].median()
    median_eq1 = df_pairs['ratio_eq1'].median()
    if median_eq1 < median_now * 0.6:
        print(f"R2 CONFIRMA dirección — Eq.1 reduce ratio mediano "
              f"{median_now:.2f}x → {median_eq1:.2f}x (-{(1-median_eq1/median_now)*100:.0f}%).")
        print(f"Implementar y A/B test.")
    elif median_eq1 < median_now * 0.8:
        print(f"R2 PARCIAL — Eq.1 reduce moderadamente "
              f"{median_now:.2f}x → {median_eq1:.2f}x.")
        print(f"Implementar pero esperar A/B con criterios estrictos.")
    else:
        print(f"R2 REFUTA — Eq.1 NO reduce ratio significativamente "
              f"{median_now:.2f}x → {median_eq1:.2f}x.")
        print(f"NO implementar. Buscar otra hipótesis.")
