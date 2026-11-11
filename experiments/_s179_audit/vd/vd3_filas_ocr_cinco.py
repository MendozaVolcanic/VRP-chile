# -*- coding: utf-8 -*-
"""VD3 (verificador frente D, S179). Las 5 protegidas VIIRS 375 que la vía (posición radiante) calla y K publica:
¿qué dice la fila de MIROVA que las hace protegidas? Imprime, de la copia del OCR de 438a60a1e (sha256 7e54155a...) y de
la tabla (latest_consolidado.csv, sha256 40b1b928...), toda fila de ese volcán a +-180 s, con distancia, nota,
versión del OCR y la distancia aproximada complementaria (Mirova-v1#25).
Pregunta 1: si las 5 tuvieran fila de la tabla, ¿lo vería? Sí, busca también en la tabla. Pregunta 2: si el lector
estuviera muerto, imprimiría 0 filas; cada caso imprime cuántas encontró (control: las 5 deben tener al menos 1 fila OCR).
Uso: python vd3_filas_ocr_cinco.py <latest_consolidado.csv> <registro_vrp_ocr.csv>
"""
import sys, io, csv
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CASOS = [("Isluga", "2026-03-20 05:06"), ("Isluga", "2026-03-24 05:30"), ("Lascar", "2026-03-15 05:00"),
         ("Isluga", "2026-10-03 05:18"), ("Lascar", "2026-10-01 05:18")]
def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
cons = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
ocr = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
kc = [k for k in cons[0] if "fecha" in k.lower() and "sat" in k.lower()] or [k for k in cons[0] if "fecha" in k.lower()]
print("columnas de fecha de la tabla:", kc[:3])
for vol, m in CASOS:
    print(f"\n=== {vol} {m} UTC ===")
    n_ocr = 0
    for r in ocr:
        if r["Volcan"] == vol and r["Sensor"] == "VIIRS375" and abs((t(r["Fecha_Satelite_UTC"]) - t(m)).total_seconds()) <= 180:
            n_ocr += 1
            print("  OCR:", {k: r.get(k) for k in ("Fecha_Satelite_UTC", "VRP_MW", "Distancia_km", "Tipo_Registro", "Nota_Validacion",
                                                  "Version_OCR", "Distancia_aprox_km", "Distancia_aprox_min_km",
                                                  "Distancia_aprox_max_km", "Distancia_aprox_metodo")})
    n_tab = 0
    for r in cons:
        f = r.get(kc[0]) or ""
        if (r.get("Volcan") or r.get("volcan") or "") .replace(" ", "") in (vol, "Láscar" if vol == "Lascar" else vol) and f[:10] == m[:10]:
            try:
                d = abs((t(f) - t(m)).total_seconds())
            except ValueError:
                continue
            if d <= 180:
                n_tab += 1
                print("  TABLA:", dict(list(r.items())[:12]))
    print(f"  filas OCR {n_ocr}, filas de la tabla a +-180 s {n_tab}")
