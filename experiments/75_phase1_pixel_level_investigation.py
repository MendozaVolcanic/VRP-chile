"""S33 C — investigación pixel-level Phase 1 destrucción recall.

Pregunta científica: cuando Phase 1 (filtro 5σ summit pixel-level Test 1)
destruye la detección summit en Lastarria/Villarrica/Planchón, los pixels
Test 1 que el filtro elimina son:

  (a) Ruido térmico — background tibio, BT marginal sobre bg, sin actividad.
      → Phase 1 hace lo correcto (suprimir falsos), recall caído es
        artefacto de bug S33 que inflaba los TPs.
  (b) Señal real sub-pixel — fumarolas peri-cráter dispersas con BT poco
      arriba bg pero NTI alto.
      → Phase 1 destruye señal real, revertir.

Análisis: comparar records (filter_OFF detectó / filter_ON perdió)
con métrica corregida S33. Para cada uno:
- Distribución pixels Test 1 OFF (BT, vrp_pixel).
- Cuántos sobreviven 5σ summit threshold.
- ¿NTI alto compensa BT bajo? (firma fumarola sub-pixel).
- ¿BT distribución uniforme bg-tibio? (firma ruido).
"""
from __future__ import annotations
import json, sys, io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
OFF = ROOT / "data" / "mirova_equivalent_test1pix_disabled"
ON  = ROOT / "data" / "mirova_equivalent_test1pix_filter"

INNER_RADIUS_KM = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}

VOLCS_FOCO = ['Lastarria', 'Villarrica', 'PlanchonPeteroa']  # peor regresión
END_DT = datetime(2026,4,29,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)
TOL_MIN = 60


def parse_csv_dt(s): return datetime.strptime(s.strip(),"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)
def sensor_match(ref, rec):
    if ref == "MODIS": return rec.startswith("MODIS")
    if ref == "VIIRS": return rec.startswith("VIIRS_") and rec.endswith("_750")
    if ref == "VIIRS375": return rec.startswith("VIIRS_") and not rec.endswith("_750")
    return False

def vrp_summit_fixed(rec, volc):
    """mirovaEqVrp con fix S33 (validación pc.centroid_dist_km)."""
    if not rec: return 0
    pc = rec.get('primary_cluster')
    if not pc: return rec.get('vrp_mw') or 0
    if rec.get('distance_class') and rec.get('distance_class') != 'summit': return 0
    inner = INNER_RADIUS_KM.get(volc, 10)
    pc_dist = pc.get('centroid_dist_km')
    if pc_dist is not None and pc_dist > inner: return 0
    return pc.get('vrp_mw', 0)


# Cargar refs MIROVA
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Tipo_Registro']=='ALERTA_TERMICA']

print("# C — Investigación pixel-level Phase 1 destrucción recall\n")

CSV_TO_OUR = {'Lastarria':'Lastarria', 'Villarrica':'Villarrica', 'PlanchonPeteroa':'PlanchonPeteroa'}

def load_recs(p, vol):
    f = p / f'{vol}.json'
    if not f.exists(): return []
    out = []
    for r in json.loads(f.read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; out.append(r)
    return out

def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=TOL_MIN)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        d = abs(r['_dt']-ref_dt)
        if d <= tol and d < bd: best, bd = r, d
    return best


for vol in VOLCS_FOCO:
    csv_v = vol  # mismo nombre
    print(f"\n{'='*80}")
    print(f"## {vol}\n")
    sub = df[df['Volcan']==csv_v]
    recs_off = load_recs(OFF, vol)
    recs_on  = load_recs(ON, vol)

    # Identificar records donde OFF detectó summit pero ON no
    regression_recs = []
    for _, row in sub.iterrows():
        rec_off = find_match(row['dt'], row['Sensor'], recs_off)
        rec_on  = find_match(row['dt'], row['Sensor'], recs_on)
        off_v = vrp_summit_fixed(rec_off, vol)
        on_v  = vrp_summit_fixed(rec_on, vol)
        if off_v > 0 and on_v == 0:
            regression_recs.append((row, rec_off, rec_on))

    print(f"Refs MIROVA: {len(sub)}, regresiones OFF→ON: {len(regression_recs)}\n")

    if not regression_recs:
        print("(sin regresiones)\n")
        continue

    # Para cada regresión, analizar pixels
    print("### Análisis pixel por record (sample top 5)\n")
    print("| Fecha | Sensor | MIROVA MW | OFF pc_vrp | OFF pc_n | OFF pc_dist | n_anom | n_t1 | t_bg | std_bg | t_max | nti_max |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    cases_a, cases_b, cases_indet = 0, 0, 0
    for row, rec_off, rec_on in regression_recs:
        pc = rec_off.get('primary_cluster') or {}
        ap = rec_off.get('anomaly_pixels') or []
        # Solo pixels cercanos al cluster centroid (proxy de pixels Test 1 cluster)
        cent_lat, cent_lon = pc.get('centroid_lat'), pc.get('centroid_lon')
        if cent_lat is None: continue

        bts = [p.get('bt_k', 0) for p in ap]
        if not bts: continue
        t_max = max(bts)
        n_anom = len(ap)
        n_t1 = rec_off.get('n_test1_pixels', 0)
        t_bg = rec_off.get('t_bg_k', 0)
        std_bg = rec_off.get('diag_sigma_bg_k', 0)
        nti_max = rec_off.get('nti_max', 0)

        # Threshold 5σ summit (Coppola 2016a)
        sigma_thr = max(5.0, 5.0 * std_bg)  # max(floor 5K, 5σ)
        t_threshold_5sigma = t_bg + sigma_thr

        # Cuántos pixels anomaly_pixels superan ese threshold
        pixels_pass_5sigma = sum(1 for b in bts if b >= t_threshold_5sigma)
        delta_t_max = t_max - t_bg

        # Clasificación heurística:
        # - Si t_max >> t_threshold_5sigma (10+ K margin) → señal real fuerte (b ★)
        # - Si delta_t_max < threshold y muchos pixels marginalmente arriba bg → ruido (a)
        # - Si NTI alto (-0.85+) con BT marginal → fumarola sub-pixel (b)

        # Heurística simple
        if delta_t_max > sigma_thr * 1.5:
            classification = "b★"  # señal fuerte
            cases_b += 1
        elif (nti_max is not None and nti_max > -0.85) and delta_t_max < sigma_thr:
            classification = "b☆"  # NTI alto compensa BT bajo
            cases_b += 1
        elif delta_t_max > 5 and pixels_pass_5sigma >= 1:
            classification = "b?"  # algunos pixels sí pasan
            cases_b += 1
        elif delta_t_max < 3 or pixels_pass_5sigma == 0:
            classification = "a"  # ruido bg-tibio
            cases_a += 1
        else:
            classification = "?"
            cases_indet += 1

        if cases_b + cases_a + cases_indet <= 5:
            nti_str = f"{nti_max:.3f}" if nti_max is not None else "NA"
            print(f"| {row['dt'].strftime('%Y-%m-%d %H:%M')} | {row['Sensor']} | {row['VRP_MW']:.3f} | "
                  f"{pc.get('vrp_mw',0):.2f} | {pc.get('n_pixels','?')} | "
                  f"{pc.get('centroid_dist_km','?')} | {n_anom} | {n_t1} | "
                  f"{t_bg:.2f} | {std_bg:.2f} | {t_max:.2f} | "
                  f"{nti_str} | {classification} |")

    print(f"\n### Veredicto {vol}\n")
    print(f"- Regresiones totales: {len(regression_recs)}")
    print(f"- **Caso (a) ruido bg-tibio**: {cases_a} ({cases_a/max(1,len(regression_recs))*100:.0f}%)")
    print(f"- **Caso (b) señal real**: {cases_b} ({cases_b/max(1,len(regression_recs))*100:.0f}%)")
    print(f"- Indeterminado: {cases_indet}")
    if cases_a > cases_b * 2:
        print(f"  → Phase 1 hace lo correcto en {vol}; recall caído refleja eliminación falsos.")
    elif cases_b > cases_a * 2:
        print(f"  → Phase 1 destruye señal real en {vol}; revertir.")
    else:
        print(f"  → Mixto en {vol}; decisión depende de otros volcanes.")

print("\n\n## Veredicto global\n")
print("Si caso (a) domina en los 3 volcanes → Phase 1 es correcto, recall caído es artefacto.")
print("Si caso (b) domina → Phase 1 destruye señal real, revertir.")
print("Si mixto → decisión basada en preferencia recall vs ratio.")
