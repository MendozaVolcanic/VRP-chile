"""S139 eje 3, medición 02: ¿las filas RUTINA del scraper marcan PASADAS procesadas por MIROVA,
o sólo que el scraper corrió?

Si RUTINA fuera un placeholder por escaneo (no por pasada), sus timestamps no coincidirían con
nuestras pasadas nocturnas del mismo sensor, y la exigencia "al menos un RUTINA esa noche" no
probaría cobertura de la referencia.

Pregunta 1 del instrumento: si RUTINA NO fuera por pasada, ¿lo vería? Sí: fracción de nuestras
pasadas nocturnas con una fila CONS (cualquier Tipo) del mismo sensor a <=20 min, contra la
misma fracción con el reloj de CONS desplazado 6 h (control negativo: debe caer).
Pregunta 2: si el pareo estuviera muerto (nombres de sensor mal mapeados, zona horaria), la
fracción real y la desplazada serían iguales o ambas 0: se imprime SIN DATO si n=0.
Control positivo: las pasadas ALERTA de CONS deben parear con alguna pasada nuestra a <=20 min
en Láscar (sensor dominante).
Ventana: intersección CONS (desde 2026-01-10) y records nuestros; se imprime. Denominadores
impresos. Solo lectura.
"""
import sys, io, json
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
cons = pd.read_csv(ROOT + r"\latest_consolidado.csv")
cons["t"] = pd.to_datetime(cons["Fecha_Satelite_UTC"], errors="coerce")
cons["vol"] = cons["Volcan"].str.replace("-", "").str.replace(" ", "").str.lower()

print("Hora UTC de filas RUTINA (conteo por hora):")
print(cons[cons.Tipo_Registro == "RUTINA"]["t"].dt.hour.value_counts().sort_index().to_string())


def sensor_ours(s):
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS"
    return "VIIRS375"


VOLS = {"Lascar": "lascar", "Llaima": "llaima", "Villarrica": "villarrica", "Isluga": "isluga"}
TOL = pd.Timedelta(minutes=20)
for fn, key in VOLS.items():
    d = json.load(open(f"{ROOT}\\data\\mirova_equivalent\\{fn}.json", encoding="utf-8"))
    recs = pd.DataFrame(d["records"])
    recs["t"] = pd.to_datetime(recs["datetime_utc"], utc=True, errors="coerce").dt.tz_localize(None)
    recs["s"] = recs["sensor"].astype(str).map(sensor_ours)
    recs = recs[recs["t"] >= cons["t"].min()]
    h = recs["t"].dt.hour
    recs = recs[~h.between(11, 21)]  # nocturnas aprox
    c = cons[cons.vol == key]
    print(f"\n== {fn}: pasadas nuestras nocturnas en ventana CONS: {len(recs)}; filas CONS del volcán: {len(c)}")
    if len(recs) == 0 or len(c) == 0:
        print("SIN DATO"); continue
    for s in ("MODIS", "VIIRS", "VIIRS375"):
        ro = recs[recs.s == s].sort_values("t")
        cc = c[c.Sensor == s].sort_values("t")
        if len(ro) == 0 or len(cc) == 0:
            print(f"  {s}: SIN DATO (ours {len(ro)}, cons {len(cc)})"); continue
        res = {}
        for shift_h in (0, 6):
            ct = (cc["t"] + pd.Timedelta(hours=shift_h)).values
            tt = ro["t"].values
            idx = np.searchsorted(ct, tt)
            best = np.full(len(tt), np.timedelta64(10**6, "m"))
            for off in (-1, 0):
                j = np.clip(idx + off, 0, len(ct) - 1)
                dd = np.abs(ct[j] - tt)
                best = np.minimum(best, dd)
            res[shift_h] = float(np.mean(best <= TOL.to_timedelta64()))
        # control positivo: ALERTA CONS -> pasada nuestra
        al = cc[cc.Tipo_Registro == "ALERTA_TERMICA"]
        if len(al):
            tt2 = ro["t"].values
            ok = 0
            for ta in al["t"].values:
                j = np.searchsorted(tt2, ta)
                cand = [abs(tt2[k] - ta) for k in (j - 1, j) if 0 <= k < len(tt2)]
                ok += int(bool(cand) and min(cand) <= TOL.to_timedelta64())
            cp = f"ALERTA con pasada nuestra <=20min: {ok}/{len(al)} (incluye diurnas)"
        else:
            cp = "sin ALERTA"
        print(f"  {s}: n_ours={len(ro)} n_cons={len(cc)} | frac pasadas nuestras con fila CONS <=20min: "
              f"{res[0]:.3f} | reloj CONS +6h (control neg): {res[6]:.3f} | {cp}")
