"""S139 eje 1: muestra ampliada (8 imagenes Latest10NTI mas, 80 adquisiciones) imagen vs latest.php.

Horas y VRP transcritos a mano de imagenes bajadas en vivo 2026-09-13 20:00 UTC; CSV remoto
bajado en el mismo minuto. Banner = 'Thermal anomaly' de la cabecera (se refiere a la ultima).
VRP imagen: None = 'NaN', numero = lo dibujado (VIIRS750 trunca a entero).
Instrumento: si la tabla omitiera pasadas se ven AUSENTES; control: hora inventada debe ser AUSENTE.
Uso: python imagen_vs_tabla_ampliado.py <consolidado_remoto.csv>
"""
import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
N = None
IMG = {
    ("Isluga", "VIIRS375", "NONE"): [("2026-09-13 06:30:00", N), ("2026-09-13 05:54:02", .12), ("2026-09-13 05:12:01", .07),
        ("2026-09-12 19:24:00", N), ("2026-09-12 18:48:02", N), ("2026-09-12 18:00:01", N), ("2026-09-12 17:42:00", N),
        ("2026-09-12 06:54:00", N), ("2026-09-12 06:18:02", .21), ("2026-09-12 05:30:01", .09)],
    ("Lastarria", "VIIRS375", "NONE"): [("2026-09-13 06:36:00", .04), ("2026-09-13 06:00:02", .04), ("2026-09-13 05:12:01", N),
        ("2026-09-13 04:54:00", N), ("2026-09-12 19:18:00", N), ("2026-09-12 18:42:02", N), ("2026-09-12 18:00:01", N),
        ("2026-09-12 17:42:00", N), ("2026-09-12 06:54:00", N), ("2026-09-12 06:18:02", N)],
    ("Copahue", "VIIRS375", "VERY LOW"): [("2026-09-13 06:36:00", .28), ("2026-09-13 06:00:02", N), ("2026-09-13 05:18:01", N),
        ("2026-09-13 05:00:00", N), ("2026-09-12 19:36:01", N), ("2026-09-12 19:18:00", N), ("2026-09-12 18:42:02", N),
        ("2026-09-12 17:54:01", N), ("2026-09-12 17:36:00", N), ("2026-09-12 07:00:00", N)],
    ("Chaiten", "VIIRS375", "NONE"): [("2026-09-13 07:00:01", N), ("2026-09-13 06:42:00", N), ("2026-09-13 06:06:02", N),
        ("2026-09-13 05:18:01", .07), ("2026-09-13 05:00:00", N), ("2026-09-13 04:24:02", N), ("2026-09-12 19:36:01", N),
        ("2026-09-12 19:18:00", N), ("2026-09-12 17:54:01", N), ("2026-09-12 07:00:00", N)],
    ("Lascar", "VIIRS", "NONE"): [("2026-09-13 06:36:00", N), ("2026-09-13 06:00:02", N), ("2026-09-13 05:12:01", N),
        ("2026-09-13 04:54:00", N), ("2026-09-12 19:18:00", N), ("2026-09-12 18:42:02", N), ("2026-09-12 18:00:01", N),
        ("2026-09-12 17:42:00", N), ("2026-09-12 06:18:02", N), ("2026-09-12 05:30:01", N)],
    ("Villarrica", "VIIRS", "NONE"): [("2026-09-13 07:00:01", N), ("2026-09-13 06:36:00", N), ("2026-09-13 06:00:02", N),
        ("2026-09-13 05:18:01", N), ("2026-09-13 05:00:00", N), ("2026-09-12 19:36:01", N), ("2026-09-12 19:18:00", N),
        ("2026-09-12 18:42:02", N), ("2026-09-12 17:54:01", N), ("2026-09-12 07:00:00", N)],
    ("Llaima", "VIIRS", "NONE"): [("2026-09-13 07:00:01", N), ("2026-09-13 06:36:00", N), ("2026-09-13 06:00:02", N),
        ("2026-09-13 05:18:01", N), ("2026-09-13 05:00:00", N), ("2026-09-12 19:36:01", N), ("2026-09-12 19:18:00", N),
        ("2026-09-12 18:42:02", N), ("2026-09-12 17:54:01", N), ("2026-09-12 07:00:00", N)],
    ("Puyehue-Cordon Caulle", "VIIRS", "NONE"): [("2026-09-13 07:00:01", N), ("2026-09-13 06:42:00", N), ("2026-09-13 06:00:02", 0),
        ("2026-09-13 05:18:01", 0), ("2026-09-13 05:00:00", N), ("2026-09-12 19:36:01", N), ("2026-09-12 19:18:00", N),
        ("2026-09-12 18:42:02", N), ("2026-09-12 17:54:01", N), ("2026-09-12 07:00:00", N)],
}
c = pd.read_csv(sys.argv[1]); c["t"] = pd.to_datetime(c.Fecha_Satelite_UTC)
rows = []
for (v, s, banner), lst in IMG.items():
    cc = c[(c.Volcan == v) & (c.Sensor == s)]
    for t, vimg in lst + [("2026-09-12 03:33:33", "CTRL")]:
        d = (cc.t - pd.Timestamp(t)).abs(); i = d.idxmin(); ok = d[i] <= pd.Timedelta(seconds=60)
        rows.append(dict(volcan=v, sensor=s, banner=banner, t=t, vrp_img=vimg, en_tabla=ok,
                         vrp_tab=cc.loc[i, "VRP_MW"] if ok else None, dist_tab=cc.loc[i, "Distancia_km"] if ok else None,
                         tipo_tab=cc.loc[i, "Tipo_Registro"] if ok else None))
r = pd.DataFrame(rows)
ctrl = r[r.vrp_img.astype(str) == "CTRL"]; r = r[r.vrp_img.astype(str) != "CTRL"]
print(f"CONTROL: horas inventadas ausentes {int((~ctrl.en_tabla).sum())} de {len(ctrl)}")
print(r.to_string())
r["img_det"] = r.vrp_img.apply(lambda x: "NaN" if x is None else ("detecta" if x > 0 else "0_truncado"))
print("\nausencias por sensor:", r.groupby("sensor").en_tabla.agg(lambda s: f"{(~s).sum()} de {len(s)}").to_dict())
print("ausencias segun lo dibujado:", pd.crosstab(r.img_det, r.en_tabla).to_dict())
print("filas presentes, imagen NaN -> tipo en tabla:", r[(r.img_det == 'NaN') & r.en_tabla].tipo_tab.value_counts().to_dict())
print("filas presentes, imagen con VRP -> tipo:", r[(r.img_det != 'NaN') & r.en_tabla][["volcan", "t", "vrp_img", "vrp_tab", "dist_tab", "tipo_tab", "banner"]].to_string())
