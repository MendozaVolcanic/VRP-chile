# S122 — ¿se puede reconstruir la geometría offline, sin bajar granules?
#
# Los 5.695 records desde jun-2026 no tienen los ángulos (el pipeline recién los
# persiste). Reprocesarlos implicaría re-descargar 1.174 granules Y recalcular el
# VRP con el código de hoy (los valores cambiarían: NO sería aditivo).
#
# Alternativa: calcular los ángulos SOLARES con pura astronomía (fecha + lat/lon),
# sin descargar nada. Este script VALIDA esa vía contra la verdad de terreno: los
# records de Villarrica 2026-07-24 que YA traen el ángulo leído del L1B.
#
# Criterio pre-registrado: si el error mediano < 0.5° y el máximo < 2°, la vía
# offline es válida para los ángulos solares (el sol se mueve 0.25°/min, y el
# record tiene resolución de minuto → ese es el piso de error esperable).
import json
import io
import sys
from pathlib import Path

import numpy as np
from skyfield import almanac  # noqa: F401  (asegura instalación completa)
from skyfield.api import load, wgs84

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

ts = load.timescale()
eph = load("de421.bsp")
sun, earth = eph["sun"], eph["earth"]


def solar_angles(lat, lon, dt_utc):
    """Zenith y azimut solar (grados) en (lat, lon) al instante dt_utc.

    Convención para que sea comparable con el L1B:
      - zenith = 90 - altura (>90 = sol bajo el horizonte, o sea noche)
      - azimut en [-180, 180], 0 = norte, positivo hacia el este
    """
    y, mo, d = int(dt_utc[0:4]), int(dt_utc[5:7]), int(dt_utc[8:10])
    h, mi = int(dt_utc[11:13]), int(dt_utc[14:16])
    t = ts.utc(y, mo, d, h, mi)
    place = earth + wgs84.latlon(lat, lon)
    alt, az, _ = place.at(t).observe(sun).apparent().altaz()
    az_deg = az.degrees
    if az_deg > 180:
        az_deg -= 360.0
    return 90.0 - alt.degrees, az_deg


# --- Verdad de terreno: records que YA tienen el ángulo del L1B ---
truth = []
for vol in ("Villarrica", "Lascar"):
    p = REPO / "data/mirova_equivalent" / f"{vol}.json"
    d = json.load(open(p, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    for r in recs:
        if r.get("solar_zenith_deg") is None:
            continue
        if r.get("final_hotspot_lat") is None:
            continue
        truth.append((vol, r))

print(f"records con geometría L1B (verdad de terreno): {len(truth)}\n")
if not truth:
    print("Sin verdad de terreno todavía — esperar a que el backfill commitee.")
    sys.exit(0)

ez, ea = [], []
print(f'{"sensor":<18}{"L1B zen":>9}{"calc zen":>9}{"Δ":>7}   {"L1B az":>8}{"calc az":>9}{"Δ":>7}')
print("-" * 72)
for vol, r in truth[:14]:
    lat, lon = r["final_hotspot_lat"], r["final_hotspot_lon"]
    z, a = solar_angles(lat, lon, r["datetime_utc"])
    dz = z - r["solar_zenith_deg"]
    da = a - r["solar_azimuth_deg"]
    da = (da + 180) % 360 - 180  # diferencia angular corta
    ez.append(abs(dz))
    ea.append(abs(da))
    print(f'{r["sensor"][:18]:<18}{r["solar_zenith_deg"]:>9.2f}{z:>9.2f}{dz:>7.2f}   '
          f'{r["solar_azimuth_deg"]:>8.2f}{a:>9.2f}{da:>7.2f}')

for vol, r in truth[14:]:
    lat, lon = r["final_hotspot_lat"], r["final_hotspot_lon"]
    z, a = solar_angles(lat, lon, r["datetime_utc"])
    ez.append(abs(z - r["solar_zenith_deg"]))
    da = a - r["solar_azimuth_deg"]
    ea.append(abs((da + 180) % 360 - 180))

print(f"\nERROR sobre {len(ez)} records:")
print(f"  zenith solar : mediana {np.median(ez):.3f}°  p95 {np.percentile(ez,95):.3f}°  max {max(ez):.3f}°")
print(f"  azimut solar : mediana {np.median(ea):.3f}°  p95 {np.percentile(ea,95):.3f}°  max {max(ea):.3f}°")
ok = np.median(ez) < 0.5 and max(ez) < 2.0 and np.median(ea) < 0.5 and max(ea) < 2.0
print(f"\nCriterio pre-registrado (mediana <0.5°, max <2°): {'CUMPLE' if ok else 'NO CUMPLE'}")
