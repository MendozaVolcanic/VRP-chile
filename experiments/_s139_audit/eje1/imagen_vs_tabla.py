"""S139 eje 1: las 10 adquisiciones que MIROVA dibuja en Latest10NTI, estan todas en el consolidado?

Horas transcritas de las 4 imagenes Latest10NTI descargadas en vivo el 2026-09-13 ~19:54 UTC
(Villarrica MODIS/VIIRS375, Lascar MODIS/VIIRS375). Se buscan en el CSV remoto de Mirova-v1
bajado el mismo dia (~19:50 UTC).
Pregunta 1: si latest.php omitiera pasadas, aparecerian horas de imagen sin fila. Pregunta 2:
control positivo, una hora inventada (03:33:33) debe salir como ausente; si el loader no leyera
nada todas saldrian ausentes (se reporta el denominador).
Uso: python imagen_vs_tabla.py <consolidado_remoto.csv>
"""
import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IMG = {
    ("Villarrica", "MODIS"): ["2026-09-13 12:35:00", "2026-09-13 08:40:00", "2026-09-13 01:30:00", "2026-09-12 21:35:00",
                              "2026-09-12 13:35:00", "2026-09-12 08:00:00", "2026-09-12 02:30:00", "2026-09-11 21:00:00",
                              "2026-09-11 12:55:00", "2026-09-11 07:20:00"],
    ("Villarrica", "VIIRS375"): ["2026-09-13 07:00:01", "2026-09-13 06:36:00", "2026-09-13 06:00:02", "2026-09-13 05:18:01",
                                 "2026-09-13 05:00:00", "2026-09-12 19:36:01", "2026-09-12 19:18:00", "2026-09-12 18:42:02",
                                 "2026-09-12 17:54:01", "2026-09-12 07:00:00"],
    ("Lascar", "VIIRS375"): ["2026-09-13 06:36:00", "2026-09-13 06:00:02", "2026-09-13 05:12:01", "2026-09-13 04:54:00",
                             "2026-09-12 19:18:00", "2026-09-12 18:42:02", "2026-09-12 18:00:01", "2026-09-12 17:42:00",
                             "2026-09-12 06:18:02", "2026-09-12 05:30:01"],
    ("Lascar", "MODIS"): ["2026-09-13 12:30:00", "2026-09-13 08:35:00", "2026-09-13 01:35:00", "2026-09-12 20:00:00",
                          "2026-09-12 13:30:00", "2026-09-12 07:55:00", "2026-09-12 00:55:00", "2026-09-11 21:00:00",
                          "2026-09-11 12:50:00", "2026-09-11 07:20:00"],
}

c = pd.read_csv(sys.argv[1])
c["t"] = pd.to_datetime(c.Fecha_Satelite_UTC)
tot = pres = 0
for (v, s), times in IMG.items():
    cc = c[(c.Volcan == v) & (c.Sensor == s)]
    print(f"\n{v} {s}: filas CONS del par={len(cc)}")
    for t in times + ["2026-09-12 03:33:33"]:
        tt = pd.Timestamp(t)
        d = (cc.t - tt).abs()
        i = d.idxmin()
        ok = d[i] <= pd.Timedelta(seconds=60)
        ctrl = t.endswith("03:33:33")
        if not ctrl:
            tot += 1; pres += ok
        print(f"   {'CTRL ' if ctrl else ''}{t}: {'EN TABLA' if ok else 'AUSENTE'}  (fila mas cercana {cc.loc[i,'Fecha_Satelite_UTC']} "
              f"VRP={cc.loc[i,'VRP_MW']} {cc.loc[i,'Tipo_Registro']})")
print(f"\nadquisiciones de imagen presentes en el consolidado: {pres} de {tot}")

# otros conteos pedidos
a = c[c.Tipo_Registro == "ALERTA_TERMICA"]
print(f"\nALERTA_TERMICA CONS: n={len(a)}; VRP<0.1 MW: {int((a.VRP_MW < 0.1).sum())}; VRP<0.05: {int((a.VRP_MW < 0.05).sum())}; min={a.VRP_MW.min()}")
