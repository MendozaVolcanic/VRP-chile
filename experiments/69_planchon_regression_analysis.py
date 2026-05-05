"""S32 P2 Driver B post-A/B — Planchón regresión recall -9.7pp.

Driver B redujo recall Planchón 96.8% → 87.1% (3 FNs nuevos). Los demás
volcanes mantuvieron recall idéntico. Planchón es caso especial.

Análisis:
1. Identificar las 3 noches OFF=detección, ON=no-detección.
2. Para cada una: ¿qué reportó MIROVA? VRP, sensor, distancia.
3. ¿Eran detecciones reales sub-pixel (señal débil cortada por filtro)
   o eran TPs marginales que el filtro correctamente eliminó?

Si los 3 son MIROVA<0.1 MW (sub-pixel real) → filtro 5σ es muy agresivo
para Planchón. Considerar 4σ summit.

Si los 3 son MIROVA con n_pixels chico cluster → es señal real cortada.
Considerar 4σ.

Si los 3 son ratio nuestro >>10× pre-fix → eran FPs marginales que el
filter eliminó correctamente, y el "FN" no era detección real nuestra.
"""
from __future__ import annotations
import json, sys, io
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
OFF = ROOT / "data" / "mirova_equivalent_test1pix_disabled"
ON  = ROOT / "data" / "mirova_equivalent_test1pix_filter"

VOLC = 'PlanchonPeteroa'
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

def vrp_summit(rec):
    if not rec: return 0
    pc = rec.get('primary_cluster')
    if not pc: return rec.get('vrp_mw') or 0
    if rec.get('distance_class') and rec.get('distance_class') != 'summit': return 0
    return pc.get('vrp_mw', 0)

# Cargar refs Planchón
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan']=='PlanchonPeteroa']
df = df[df['Tipo_Registro']=='ALERTA_TERMICA']
print(f"# Planchón regresión Driver B — análisis 3 FNs nuevos\n")
print(f"Refs MIROVA Planchón ALERTA_TERMICA 90d: {len(df)}\n")

def load(p):
    out = []
    for r in json.loads((p/f'{VOLC}.json').read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; out.append(r)
    return out
recs_off = load(OFF)
recs_on  = load(ON)

def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=TOL_MIN)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        delta = abs(r['_dt']-ref_dt)
        if delta <= tol and delta < bd: best, bd = r, delta
    return best

# Identificar regresiones: OFF detecta, ON no
print("## Records donde OFF detectó (vrp_summit>0) pero ON no detectó (vrp_summit=0)\n")
print("| Fecha UTC | Sensor MIROVA | MIROVA MW | OFF pc_vrp | OFF n_t1pix | OFF dist_class |")
print("|---|---|---:|---:|---:|---|")
regression_count = 0
for _, row in df.iterrows():
    rec_off = find_match(row['dt'], row['Sensor'], recs_off)
    rec_on = find_match(row['dt'], row['Sensor'], recs_on)
    off_v = vrp_summit(rec_off)
    on_v = vrp_summit(rec_on)
    if off_v > 0 and on_v == 0:
        regression_count += 1
        pc_off = (rec_off or {}).get('primary_cluster') or {}
        print(f"| {row['dt'].strftime('%Y-%m-%d %H:%M')} | {row['Sensor']} | {row['VRP_MW']:.3f} | "
              f"{pc_off.get('vrp_mw','?')} | {rec_off.get('n_test1_pixels','?')} | "
              f"{rec_off.get('distance_class','?')} |")
print(f"\nTotal regresiones OFF→ON: {regression_count}")

# Para cada regresión, datos extra
print("\n## Detalle pixel-level de los records OFF detectados\n")
for _, row in df.iterrows():
    rec_off = find_match(row['dt'], row['Sensor'], recs_off)
    rec_on = find_match(row['dt'], row['Sensor'], recs_on)
    off_v = vrp_summit(rec_off)
    on_v = vrp_summit(rec_on)
    if not (off_v > 0 and on_v == 0): continue
    print(f"### {row['dt'].strftime('%Y-%m-%d %H:%M')} {row['Sensor']} (MIROVA {row['VRP_MW']:.3f} MW)\n")
    print(f"**OFF**: vrp_summit={off_v:.3f}, dist_class={rec_off.get('distance_class')}, "
          f"primary_cluster={rec_off.get('primary_cluster')}, "
          f"triggered_test1={rec_off.get('triggered_test1')}, n_test1_pixels={rec_off.get('n_test1_pixels')}")
    print(f"**ON**: vrp_summit={on_v}, dist_class={rec_on.get('distance_class') if rec_on else 'rec=None'}, "
          f"primary_cluster={(rec_on or {}).get('primary_cluster')}, "
          f"triggered_test1={(rec_on or {}).get('triggered_test1')}, "
          f"n_test1_pixels={(rec_on or {}).get('n_test1_pixels')}")
    # Distribución de pixels OFF para ver si los pixels eran marginales o pico
    aps = (rec_off or {}).get('anomaly_pixels') or []
    if aps:
        vrps = sorted([p.get('vrp_mw',0) for p in aps], reverse=True)
        bts = sorted([p.get('bt_k',0) for p in aps], reverse=True)
        print(f"  OFF anomaly_pixels n={len(aps)}, vrp top5: {[f'{v:.4f}' for v in vrps[:5]]}, "
              f"bt_k top5: {[f'{b:.1f}' for b in bts[:5]]}")
    print()

# Veredicto
print("\n## Veredicto Planchón\n")
print("Si las 3 regresiones tienen MIROVA<0.1 MW y OFF n_test1_pixels grande con vrp pixel chico:")
print("  → señal sub-pixel real cortada por filtro 5σ. Considerar 4σ.")
print("Si las 3 tienen ratio OFF >>5× MIROVA y pc_vrp inflada artificialmente:")
print("  → eran FPs marginales (TPs por coincidencia temporal). Filter es CORRECTO eliminándolos.")
print("Si pixels OFF tienen ΔT >5K consistentemente:")
print("  → eran señal real, considerar relajar threshold.")
