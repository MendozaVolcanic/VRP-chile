"""La frescura es por volcan, no por sensor: si la sombra pierde un sensor entero, nadie avisa.
Uso: python sensor_muerto.py <raiz> <ref>"""
import os, sys
from collections import defaultdict
raiz, ref = sys.argv[1:3]
sys.path.insert(0, raiz); sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.vigilancia_sombra as vs
vs.aa.CONS = os.path.join(ref, "registro_vrp_consolidado.csv"); vs.aa.OCR = os.path.join(ref, "registro_vrp_ocr.csv")
hoy = "2026-10-19"; win = (vs.aa.leer_frontera_k(), hoy)
filas, prod, sombra = vs.cargar_insumos(win)
ult = defaultdict(str)
for r in sombra: ult[(r["vol"], r["b"])] = max(ult[(r["vol"], r["b"])], r["noche"])
print("ultima noche de la sombra por sensor:", {b: sorted({v for (vv, bb), v in ult.items() if bb == b}) for b in ("MODIS", "VIIRS375", "VIIRS750")})
sin_modis = [r for r in sombra if r["b"] != "MODIS"]
pas = vs.pasadas_de_alerta(filas, prod, sin_modis, win)
d = vs.disparadores(pas, prod, hoy, "2026-10-02 00:00:00")
print("sombra sin MODIS: avisos =", vs.avisos_sombra(sin_modis, hoy), "| protegidas MODIS con sombra =",
      sum(p["protegida"] and p["sensor"] == "MODIS" and p["sombra_pub"] is not None for p in pas),
      "| protegidas MODIS en la ventana =", sum(p["protegida"] and p["sensor"] == "MODIS" for p in pas))
