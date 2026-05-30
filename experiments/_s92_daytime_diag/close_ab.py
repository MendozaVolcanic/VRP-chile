"""S92 — cierre A/B diurno NdC mayo. Fuente de verdad reproducible (§0.5).
Completa lo que analyze_ab.py no cubre: conteo de diurnas con señal + cruce OCR
(no solo CONS) + qué pasó en las fechas con TIF MODIS diurno.
"""
import json
import sys
import urllib.request
import csv
import io
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.audit_metrics import mirova_eq_vrp       # noqa: E402
from pipeline.store import _solar_elevation            # noqa: E402

VOL = "NevadosDeChillan"
OCR_URL = ("https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/"
           "monitoreo_satelital/registro_vrp_ocr.csv")
START, END = "2026-05-08", "2026-05-21 23:59"


def elev(r):
    try:
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
    except (ValueError, KeyError):
        return None
    lat = r.get("final_hotspot_lat") or r.get("hotspot_lat")
    lon = r.get("final_hotspot_lon") or r.get("hotspot_lon")
    if lat is None or lon is None:
        return None
    return _solar_elevation(lat, lon, dt)


def load(prof):
    p = ROOT / f"data/_daytime_modis_{prof}/{VOL}.json"
    recs = json.load(open(p, encoding="utf-8"))["records"]
    return [r for r in recs if START <= str(r.get("datetime_utc", "")) <= END]


def main():
    en = load("enabled")
    di = load("disabled")
    en_modis = [r for r in en if str(r.get("sensor", "")).startswith("MODIS")]
    di_modis = [r for r in di if str(r.get("sensor", "")).startswith("MODIS")]

    # diurnas (elev>0) en enabled
    diurnas = [(r, elev(r)) for r in en_modis if (elev(r) is not None and elev(r) > 0)]
    diurnas_sig = [(r, e) for r, e in diurnas if mirova_eq_vrp(r, VOL) > 0]
    print(f"=== A/B NdC mayo 08-21 — composición MODIS ===")
    print(f"enabled MODIS={len(en_modis)}  disabled MODIS={len(di_modis)}  "
          f"(+{len(en_modis)-len(di_modis)} = pasadas diurnas bajadas por --no-night-filter)")
    print(f"enabled MODIS DIURNAS (elev>0): {len(diurnas)}  |  con señal (meq>0): {len(diurnas_sig)}")
    print(f"\n=== Las {len(diurnas)} pasadas MODIS diurnas y su detección ===")
    for r, e in sorted(diurnas, key=lambda x: x[0]["datetime_utc"]):
        meq = mirova_eq_vrp(r, VOL)
        flag = "  <<< SEÑAL" if meq > 0 else ""
        print(f"  {r['datetime_utc']} {r['sensor']:12} elev={e:+5.1f}°  "
              f"meq={meq:7.2f}  t_max={r.get('t_max_k')}{flag}")

    # cruce OCR
    print(f"\n=== MIROVA OCR NdC mayo 08-21 (ALERTAS, todas las horas) ===")
    try:
        raw = urllib.request.urlopen(OCR_URL, timeout=30).read().decode("utf-8", "replace")
        rows = list(csv.DictReader(io.StringIO(raw)))
        hit = 0
        for r in rows:
            v = (r.get("Volcan", "") or "").strip()
            if "hillan" not in v.lower():
                continue
            ts = (r.get("Fecha_Satelite_UTC", "") or "").strip()
            if not (START <= ts <= END):
                continue
            tipo = r.get("Tipo_Registro", "") or ""
            if not tipo.startswith("ALERTA"):
                continue
            hit += 1
            # diurno?
            try:
                dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
                el = _solar_elevation(-36.86, -71.38, dt)
                dn = "DÍA" if el > 0 else "noc"
            except Exception:
                dn = "?"
            print(f"  {ts[:16]} {dn} VRP={r.get('VRP_MW')} dist={r.get('Distancia_km')} "
                  f"{r.get('Sensor')} {tipo}")
        if not hit:
            print("  (0 ALERTAS OCR NdC en la ventana)")
    except Exception as e:  # noqa: BLE001
        print(f"  (OCR no disponible: {e})")


if __name__ == "__main__":
    main()
