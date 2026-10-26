"""S163 D-39: pasos del ocr_workflow.yml que reescriben registro_vrp_ocr.csv sin red, en el brazo dado:
guardar_ocr sin eventos nuevos (reorden y columnas), backfill_horas_utc, [reparar_mojibake si existe], reconciliar_latest, merger_maestro."""
import os, sys, runpy, subprocess
brazo = sys.argv[1]; os.chdir(brazo); sys.path.insert(0, brazo)
import pandas as pd, scraper_ocr
df = pd.read_csv(scraper_ocr.DB_OCR)
scraper_ocr.guardar_ocr(df, [], scraper_ocr.DB_OCR); print('guardar_ocr sin eventos: ok')
pasos = [['backfill_horas_utc.py', 'monitoreo_satelital/registro_vrp_ocr.csv']]
if os.path.exists('reparar_mojibake.py'): pasos.append(['reparar_mojibake.py', 'monitoreo_satelital/registro_vrp_ocr.csv'])
pasos += [['reconciliar_latest.py'], ['merger_maestro.py']]
for p in pasos:
    r = subprocess.run([sys.executable] + p, capture_output=True, text=True)
    print(p[0], 'exit', r.returncode, '|', (r.stdout.strip().splitlines() or [''])[-1][:150], r.stderr[-300:])
