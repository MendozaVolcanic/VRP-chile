# Comprueba la convencion de los acimuts guardados en los records (MODIS y VIIRS), sin suponerla.
# Solo lectura.
#
# POR QUE: todo el estudio depende de saber si `sensor_azimuth_deg` apunta del pixel HACIA el sensor o
# del sensor hacia el pixel. Con una convencion el corrimiento observado va hacia el nadir (lo que
# predice la interpolacion); con la otra va hacia afuera (lo que predice un paralaje sin corregir).
#
# Dos pruebas independientes:
#  1. Acimut solar: se calcula la posicion del Sol (NOAA) en el crater a la hora del record y se compara
#     con `solar_azimuth_deg`. El Data Dictionary C7 (seccion 2.4) agrupa SolarAzimuth y SensorAzimuth
#     como "Sun and satellite bearings" de la misma fuente (MOD03).
#  2. Hora solar local contra el acimut del sensor, sin documentacion: en una misma familia de pasadas
#     nocturnas, el volcan que queda al ESTE de la traza se ve MAS TARDE en hora solar local que el que
#     queda al oeste (la hora local crece hacia el este). Si el acimut es del pixel hacia el sensor, las
#     pasadas con el sensor al este (acimut 0 a 180) tienen el volcan al OESTE de la traza y por lo
#     tanto hora local MENOR.
import datetime as dt
import json
import math
import statistics as st
import sys

import comun

sys.stdout.reconfigure(encoding="utf-8")


def envolver(x):
    return (x + 180) % 360 - 180


def grupo(sensor):
    s = sensor.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    return "V750" if s.endswith("_750") else "V375"


vents = comun.vents()
sol = {}
hora = {}
for vol, (la, lo) in vents.items():
    recs = json.load(open(comun.RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    for r in recs:
        if r.get("solar_azimuth_deg") is None or r.get("sensor_azimuth_deg") is None:
            continue
        t = dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        g = grupo(r["sensor"])
        # MODIS: granulo de 5 min, el record lleva el inicio; VIIRS: granulo de 6 min. Se usa la mitad.
        tm = t + dt.timedelta(minutes=2.5 if g == "MODIS" else 3)
        az, _ = comun.sol_az_zen(tm, la, lo)
        rec = r["solar_azimuth_deg"] % 360
        sol.setdefault(g, []).append((abs(envolver(rec - az)), abs(envolver(rec - az - 180))))
        if (r.get("solar_zenith_deg") or 0) > 100 and (r.get("sensor_zenith_deg") or 0) > 30:
            sat = comun.satelite(r["sensor"])
            lst = (tm.hour + tm.minute / 60 + lo / 15.0) % 24
            lst = lst if lst > 12 else lst + 24      # noche continua: 18 h ... 30 h
            este = 0 <= r["sensor_azimuth_deg"] % 360 < 180
            hora.setdefault((g, sat, "sensor al E" if este else "sensor al O"), []).append(lst)

print("1. Acimut solar del record contra el Sol calculado en el crater (mediana de |diferencia|, grados)")
for g, xs in sorted(sol.items()):
    print("   %-5s n=%5d  convencion pixel->Sol: %6.2f   convencion Sol->pixel: %6.2f"
          % (g, len(xs), st.median(a for a, _ in xs), st.median(b for _, b in xs)))
print()
print("2. Hora solar local (h, 24 = medianoche) de pasadas nocturnas con cenit > 30 deg, por familia de acimut")
for (g, sat, fam), xs in sorted(hora.items()):
    if len(xs) >= 10:
        print("   %-5s %-7s %-12s n=%4d  hora local mediana %5.2f" % (g, sat, fam, len(xs), st.median(xs)))
print("   Si el acimut va del pixel al sensor, 'sensor al E' debe tener hora local MENOR que 'sensor al O'.")
