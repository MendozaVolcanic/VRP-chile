# SOSPECHA a probar: la interpolacion 5 km -> 1 km de la geolocalizacion MODIS (zoom con extremos alineados, sin el
# desfase de 2 pixeles del submuestreo) corre los pixeles a lo largo del barrido. Si es asi, el desplazamiento E-O del
# pixel mas caliente de Lascar respecto del crater debe depender del lado del barrido (acimut del sensor) y del angulo.
# Solo lectura sobre los records de produccion.
import json, math, sys, statistics as st
f = sys.argv[1]
vent = (-23.36293, -67.731416)
d = json.load(open(f, encoding="utf-8"))
rows = []
for r in d["records"]:
    if not str(r.get("sensor", "")).startswith("MODIS"):
        continue
    ap = r.get("anomaly_pixels") or []
    if not ap or r.get("sensor_zenith_deg") is None or r.get("sensor_azimuth_deg") is None:
        continue
    p = max(ap, key=lambda x: x.get("bt_k") or 0)
    dn = (p["lat"] - vent[0]) * 111.32; de = (p["lon"] - vent[1]) * 111.32 * math.cos(math.radians(vent[0]))
    if math.hypot(dn, de) > 6:
        continue
    rows.append((r["datetime_utc"], r["sensor"], r["sensor_zenith_deg"], r["sensor_azimuth_deg"], dn, de, r.get("t_max_k")))
print("records con pixel a <6 km del crater:", len(rows))
for lado, cond in (("acimut del sensor al E (0-180)", lambda a: 0 <= a % 360 < 180), ("acimut del sensor al O (180-360)", lambda a: 180 <= a % 360 < 360)):
    for zmin, zmax in ((0, 20), (20, 40), (40, 70)):
        s = [x for x in rows if cond(x[3]) and zmin <= x[2] < zmax]
        if len(s) >= 3:
            print("%-34s zenit %2d-%2d n=%4d  mediana dE %+.2f km  dN %+.2f km" % (lado, zmin, zmax, len(s), st.median(x[5] for x in s), st.median(x[4] for x in s)))
