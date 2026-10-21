# -*- coding: utf-8 -*-
"""F6 M9: ¿el rechazo por sun-glint < 12 grados del codigo publicado se ve en el OSF v2.5?
Fenomeno: con el sol reflejado especularmente hacia el satelite, el MIR sube sin calor; el codigo rechaza la escena
entera si el angulo de glint < 12 (MIROVA_VIIRS750_hotspot_detection.m, seccion 1).
Instrumento: sol calculado con el algoritmo NOAA (Meeus simplificado) desde timeUTC (minuto de inicio del granulo,
error hasta ~6 min = ~1,5 grados de sol) y la cumbre; glint con la formula de run_example.m y el SatZen/SatAzi del OSF.
Validacion del instrumento: el ejemplo de Etna (sun_zen 115,90, sun_azi 31,89 en el .mat) debe salir a < 1 grado.
Pregunta 1 (control positivo / nulo): se baraja SatAzi entre filas diurnas (conserva cenit y sol). Si el rechazo no
existiera, la fraccion real con glint < 12 deberia parecerse a la barajada. Si el instrumento estuviera muerto (sol
mal calculado) la validacion de Etna fallaria.
Denominador: filas V750 Dayflag = 1 (17.859), OSF v2.5 2012-2025."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def sol(t, lat, lon):
    """Zenit y azimut solar (grados, azimut horario desde el norte). Algoritmo NOAA."""
    jd = t.map(pd.Timestamp.to_julian_date).to_numpy() if hasattr(t, "map") else np.array([t.to_julian_date()])
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    Mr = np.radians(M)
    C = (np.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T)) + np.sin(2 * Mr) * (0.019993 - 0.000101 * T)
         + np.sin(3 * Mr) * 0.000289)
    lam = L0 + C - 0.00569 - 0.00478 * np.sin(np.radians(125.04 - 1934.136 * T))
    eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * np.cos(np.radians(125.04 - 1934.136 * T))
    dec = np.degrees(np.arcsin(np.sin(np.radians(eps)) * np.sin(np.radians(lam))))
    y = np.tan(np.radians(eps / 2)) ** 2
    L0r = np.radians(L0)
    eqt = 4 * np.degrees(y * np.sin(2 * L0r) - 2 * e * np.sin(Mr) + 4 * e * y * np.sin(Mr) * np.cos(2 * L0r)
                         - 0.5 * y * y * np.sin(4 * L0r) - 1.25 * e * e * np.sin(2 * Mr))
    frac = (jd + 0.5) % 1.0
    tst = (frac * 1440 + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    latr, decr, har = np.radians(lat), np.radians(dec), np.radians(ha)
    cz = np.sin(latr) * np.sin(decr) + np.cos(latr) * np.cos(decr) * np.cos(har)
    zen = np.degrees(np.arccos(np.clip(cz, -1, 1)))
    az = np.degrees(np.arctan2(np.sin(har), np.cos(har) * np.sin(latr) - np.tan(decr) * np.cos(latr))) + 180
    return zen, az % 360

def glint(sat_zen, sun_zen, sat_azi, sun_azi):
    c = (np.cos(np.radians(sat_zen)) * np.cos(np.radians(sun_zen))
         - np.sin(np.radians(sat_zen)) * np.sin(np.radians(sun_zen)) * np.cos(np.radians(sun_azi - sat_azi)))
    return np.degrees(np.arccos(np.clip(c, -1, 1)))

z, a = sol(pd.Series([pd.Timestamp("2023-05-19 00:54")]), 37.734, 15.004)
print(f"validacion Etna 2023-05-19 00:54: sun_zen {z[0]:.2f} (mat 115.90), sun_azi {a[0]:.2f} (mat 31.89)")
d = pd.read_pickle(sys.argv[1])
for flag in (1, 0):
    s = d[d.Dayflag == flag].copy()
    zen, az = sol(s.t, s.Volc_LAT.to_numpy(), s.Volc_LON.to_numpy())
    g = glint(s.SatZen.to_numpy(), zen, s.SatAzi.to_numpy(), az)
    rng = np.random.default_rng(0)
    gb = [glint(s.SatZen.to_numpy(), zen, rng.permutation(s.SatAzi.to_numpy()), az) for _ in range(20)]
    gb = np.concatenate(gb)
    print(f"\nDayflag {flag}: n={len(s)}  sol zenit mediana {np.median(zen):.1f}  (min {zen.min():.1f}, max {zen.max():.1f})")
    for c in (6, 10, 12, 14, 18):
        print(f"  glint < {c:2d}: real {int((g < c).sum()):5d} ({100*(g < c).mean():.3f} %)   barajado {100*(gb < c).mean():.3f} %")
    if flag == 1:
        low = s.assign(glint=g, sun_zen=zen)[g < 14].sort_values("glint")
        print("  filas reales con glint < 14 (primeras 10):")
        print(low[["timeUTC","Volc_Name","SatZen","SatAzi","sun_zen","glint","VRP"]].head(10).to_string())
