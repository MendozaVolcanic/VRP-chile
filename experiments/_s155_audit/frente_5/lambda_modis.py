# -*- coding: utf-8 -*-
"""S155 frente 5: tamano del desajuste de longitud de onda en el VRP de MODIS con la banda 22 primaria (K).
process_modis.py:552-554 arma bt_mir con B22 (3,959 um) donde no satura, y process_modis.py:1034 y 1039 convierten
esa BT de vuelta a radiancia con BAND21_LAMBDA (3,929 um). Se mide cuanto cambia el exceso de radiancia (y por ende el
VRP) entre convertir a 3,929 y a 3,959, sobre los pixeles MODIS de las pasadas pareadas (BT y t_bg del record).
Pregunta 1: si el desajuste no existiera la razon seria 1 exacta. Pregunta 2: control, mismo calculo con BT = t_bg + 0
da 0/0 y se excluye; con BT muy alta la razon tiende a (3,959/3,929)^5 * ... (se imprime el limite numerico)."""
import io, json, os, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import pareo_pasadas as PP  # noqa
import statistics as st
recs = {(r["datetime_utc"][:16], PP.bucket(r["sensor"])): r for r in json.load(open(
    os.path.join(PP.WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]}
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
rz = []
for f in ok:
    if f["b"] != "MODIS":
        continue
    r = recs[(f["t"], f["b"])]
    for p in r["anomaly_pixels"]:
        a = PP.planck(p["bt_k"], PP.BAND21_LAMBDA) - PP.planck(r["t_bg_k"], PP.BAND21_LAMBDA)
        b = PP.planck(p["bt_k"], PP.BAND22_LAMBDA) - PP.planck(r["t_bg_k"], PP.BAND22_LAMBDA)
        if a > 0 and b > 0:
            rz.append(a / b)
print("pixeles MODIS pareados n=%d; razon dL(3,929)/dL(3,959): min %.3f mediana %.3f max %.3f" % (
    len(rz), min(rz), st.median(rz), max(rz)))
print("limite BT=600 K, fondo 270 K: %.3f" % ((PP.planck(600, PP.BAND21_LAMBDA) - PP.planck(270, PP.BAND21_LAMBDA)) /
                                            (PP.planck(600, PP.BAND22_LAMBDA) - PP.planck(270, PP.BAND22_LAMBDA))))
