"""A5 latente: cuantas filas de alerta descarta el dedup del cargador (CONS gana a OCR por timestamp) con VRP distinto,
y contraejemplo sintetico VRP vacio / dedup."""
import sys, os, csv
from collections import defaultdict
W, REF = sys.argv[1:3]
sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "scripts"))
import scripts.auto_audit_weekly as aa, clase_mirova as cm
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor
cons, ocr = os.path.join(REF, "registro_vrp_consolidado.csv"), os.path.join(REF, "registro_vrp_ocr.csv")
k = defaultdict(list)
for p, s in ((cons, "CONS"), (ocr, "OCR")):
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    print(s, "columnas:", list(rows[0].keys())[:6])
    for r in rows:
        if (r.get("Tipo_Registro") or "").strip() in cm.TIPOS_ALERTA:
            k[(r.get("timestamp"), normalize_volcano_name(r.get("Volcan")), normalize_sensor(r.get("Sensor")))].append((s, r.get("VRP_MW"), r.get("Fecha_Satelite_UTC")))
dup = {kk: v for kk, v in k.items() if len(v) > 1}
print("claves de dedup con >1 fila de alerta:", len(dup))
dif = {kk: v for kk, v in dup.items() if len({x[1] for x in v}) > 1}
print("de ellas con VRP distinto:", len(dif), list(dif.items())[:5])
# contraejemplo sintetico: el cargador ya dedupo y quedo solo la fila CONS de 0,04; la OCR de 1,5 se perdio
al = [{"volcano": "Lascar", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 05:00:00", "vrp_mw": 0.04}]
print("sintetico dedup: aplicar_d9 deja", len(aa.aplicar_d9(al)), "alertas (canon con ambas filas dejaria 1)")
filas = [{"volcano": "Lascar", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 05:00:00", "vrp_mw": v, "tipo": "ALERTA_TERMICA", "source": s}
         for v, s in ((0.04, "CONS"), (1.5, "OCR"))]
print("canon con ambas filas, minimas:", cm.aplicar_regla_minimas(filas, "SN").minimas)
al2 = [{"volcano": "Lascar", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-10-01 05:00:00", "vrp_mw": 0.0}]
print("sintetico VRP vacio (cargador lo vuelve 0.0): aplicar_d9 deja", len(aa.aplicar_d9(al2)),
      "; canon con vrp None:", cm.aplicar_regla_minimas([dict(filas[0], vrp_mw=None)], "SN").minimas)
