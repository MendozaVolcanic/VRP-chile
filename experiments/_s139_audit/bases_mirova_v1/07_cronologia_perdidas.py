"""07: cuando desaparecieron del remoto las filas que las copias viejas tienen
(06-A), y cuanto valen las distancias de las notas OCR anteriores a V29.

Entrada: --historico DIR con cons_YYYY-MM-DD.csv bajados del remoto a distintos
commits (ver la celda de descarga en el informe) y --remoto DIR con el vigente.
"""
import glob
import os
import sys

import pandas as pd

from comun import LLAVE, LOCAL_MIROVA, REPO, dir_remoto, encabezado, leer
from pipeline_loader_shim import parse_ocr_distance  # noqa: E402  (copia local del regex del loader)

D = dir_remoto(sys.argv)
H = sys.argv[sys.argv.index("--historico") + 1] if "--historico" in sys.argv else os.path.join(D, "..", "historico")
cons = leer(f"{D}/registro_vrp_consolidado.csv")
ocr = leer(f"{D}/registro_vrp_ocr.csv")
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 300)

encabezado(
    "CRONOLOGIA DE LAS FILAS PERDIDAS Y DISTANCIAS OCR PRE-V29",
    "si nada se hubiera perdido, cada version historica contendria el 100 % de las llaves de la copia del 08-abr; si se perdio de una vez, habria un escalon; si es progresivo, una pendiente",
    "cada version imprime cuantas de las llaves buscadas contiene (n/244); un archivo ilegible se reporta como error, no como 0",
    "la copia del 08-abr contra si misma debe dar 244/244 presentes",
)


def llaves(df):
    return set(zip(df["timestamp"].astype("int64"), df["Volcan"], df["Sensor"]))


kr = llaves(cons)
b = leer(os.path.join(LOCAL_MIROVA, "registro_vrp_consolidado al 08042026.csv"))
b.loc[b["Volcan"] == "Peteroa", "Volcan"] = "PlanchonPeteroa"
perdidas = b[[k not in kr for k in zip(b["timestamp"].astype("int64"), b["Volcan"], b["Sensor"])]]
kp = llaves(perdidas)
print(f"llaves de la copia del 08-abr ausentes en el remoto de hoy: {len(kp)}")
print(f"CONTROL: presentes en la propia copia del 08-abr: {len(kp & llaves(b))}/{len(kp)}")
print("\nversion historica del remoto -> cuantas de esas llaves seguian presentes (y filas totales)")
for f in sorted(glob.glob(os.path.join(H, "cons_*.csv"))):
    try:
        v = leer(f)
    except Exception as e:  # noqa: BLE001
        print(f"  {os.path.basename(f)}: ERROR {e}"); continue
    v.loc[v["Volcan"] == "Peteroa", "Volcan"] = "PlanchonPeteroa"
    kv = llaves(v)
    pres = kp & kv
    por_tipo = perdidas[[k in kv for k in zip(perdidas["timestamp"].astype("int64"), perdidas["Volcan"], perdidas["Sensor"])]]["Tipo_Registro"].value_counts().to_dict()
    print(f"  {os.path.basename(f)}: filas {len(v):6d}, max {v['dt'].max()} -> presentes {len(pres):3d}/{len(kp)}  {por_tipo}")

# ausencias por fecha de la fila: se van las mas viejas primero?
print("\nlas 244 por semana de la fecha del satelite:")
print(perdidas.groupby(perdidas["dt"].dt.to_period("W"))["Tipo_Registro"].count())
print("\nlas 244: posicion que ocupaban en la copia del 08-abr (ordenada por timestamp desc, fila 0 = mas nueva)")
b_sorted = b.sort_values("timestamp", ascending=False).reset_index(drop=True)
pos = b_sorted.index[[k in kp for k in zip(b_sorted["timestamp"].astype("int64"), b_sorted["Volcan"], b_sorted["Sensor"])]]
print("  min/mediana/max:", int(pos.min()), int(pd.Series(pos).median()), int(pos.max()), "de", len(b_sorted))
# hay huecos de dias enteros por volcan/sensor en el remoto que las copias viejas si tienen?
print("\nde las 244, cuantas son la UNICA fila de su (volcan, sensor, noche) en la copia del 08-abr (o sea la noche entera se pierde):")
b_n = b[b["noche"]].groupby(["Volcan", "Sensor", "noche_id"]).size()
u = 0
for _, r in perdidas[perdidas["noche"]].iterrows():
    if b_n.get((r["Volcan"], r["Sensor"], r["noche_id"]), 0) == 1:
        u += 1
print("  ", u, "de", int(perdidas["noche"].sum()), "nocturnas")

print("\n=== distancia de la NOTA OCR (parse del loader de VRP Chile) contra Distancia_km de latest.php, en las llaves compartidas, por mes ===")
oa = ocr[ocr["Tipo_Registro"] == "ALERTA_TERMICA_OCR"].set_index(LLAVE)
ca = cons.set_index(LLAVE)
com = oa.index.intersection(ca.index)
t = pd.DataFrame({"mes": oa.loc[com, "mes"], "d_nota": [parse_ocr_distance(n) for n in oa.loc[com, "Nota_Validacion"]],
                  "d_col": oa.loc[com, "Distancia_km"].values, "d_php": ca.loc[com, "Distancia_km"].values,
                  "Version_OCR": oa.loc[com, "Version_OCR"].values})
t["d_loader"] = [c if c > 0 else n for c, n in zip(t["d_col"], t["d_nota"])]
t["ratio"] = t["d_loader"] / t["d_php"].where(t["d_php"] > 0)
g = t.groupby("mes").agg(n=("d_php", "size"), con_nota=("d_nota", lambda s: s.notna().sum()),
                          col_medida=("d_col", lambda s: (s > 0).sum()),
                          ratio_mediana=("ratio", "median"), abs_err_mediana_km=("d_loader", lambda s: float("nan")))
g["abs_err_mediana_km"] = t.assign(e=(t["d_loader"] - t["d_php"]).abs()).groupby("mes")["e"].median()
print(g.round(2))
print("\nratio mediana por Version_OCR:", t.groupby("Version_OCR")["ratio"].median().round(2).to_dict())
