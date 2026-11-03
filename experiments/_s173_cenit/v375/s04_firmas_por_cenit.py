# -*- coding: utf-8 -*-
"""s04 (S173): firmas de pieza en salidas que YA existen, partidas por cenit (Chillán, VIIRS 375). No es ablación.

POR QUÉ. Sin una ablación pieza a pieza, lo que sí se puede leer de los records existentes es la FIRMA que dejaría cada
pieza candidata. Mirando de lado, el píxel de 375 m del barrido cubre más terreno: un domo de potencia fija diluye su
radiancia sobre un píxel más grande.
  - Si la pieza es el REMUESTREO (D17): al interpolar ese píxel grande a celdas fijas de 375 m, la vía reparte el
    exceso sobre más celdas, cada una con la radiancia diluida; la suma recupera la energía. Firma: el número de
    alertados de la vía crece con el cenit más que el de K (npix_via / npix_K sube con z).
  - Si la pieza es el FONDO (D25, la mediana del anillo regional de 5 a 25 km, y el recorte a cero): la firma es un fondo
    de K más tibio que el de la vía que crece con z (t_bg_K - t_bg_via sube con z).
Ninguna firma prueba la pieza; la ablación sí (ver el informe, objetivo 2).

Insumos: s02_v375e_pasadas.csv (vía re-corrida sobre las grillas de los lotes, y K de producción pareado) y s01_k_pasadas.csv
(n_pos = píxeles de K con VRP > 0, pc_n, t_bg del anillo). Además la salida por pasada de la tarea 1.33
(experiments/_s157_magnitud_chillan/a_pasadas_salida.json en origin/main, copiada como _s157_a_pasadas.json): G = S_in/M
(nuestros píxeles dentro del inner sobre MIROVA), G_fondo0 (los mismos píxeles con fondo cero, techo del fondo) y G_area
(con el factor de área del modelo geométrico, techo de D17), partidas por tramo de cenit.
P1: si npix de la vía no se leyera, todos los cocientes serían None (se cuenta n por tramo); control positivo: en el
    tramo nadir la vía y K deben dar fondos parecidos (misma escena, mismo terreno).
P2: Spearman contra cenit con 200 barajados, semilla 173, como en s03.
Uso: python -B s04_firmas_por_cenit.py <s02_v375e_pasadas.csv> <s01_k_pasadas.csv> <_s157_a_pasadas.json> <salida.json>
"""
import csv, json, sys
import importlib.util
from pathlib import Path

VCSV, KCSV, S157, OUT = sys.argv[1:5]
sp = importlib.util.spec_from_file_location("s03", str(Path(__file__).with_name("s03_estratos_cenit.py")))
# reusar spearman/resumen sin ejecutar el main de s03: se copian las funciones necesarias
src = Path(__file__).with_name("s03_estratos_cenit.py").read_text(encoding="utf-8")
ns = {}
exec(src.split("K = [r for r in csv.DictReader")[0].replace("KCSV, VCSV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]", ""), ns)
f, resumen = ns["f"], ns["resumen"]

K = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}
V = list(csv.DictReader(open(VCSV, encoding="utf-8")))
npix, dtbg, filas = [], [], []
for r in V:
    vm = f(r["vrp_M"])
    if not vm or vm <= 0 or r["K_pub"] != "1" or not f(r["via_vrp_rec"]):
        continue
    k = K[(r["sensor"], r["dt"])]
    z = f(r["K_z"])
    nv, nk = f(r["via_npix"]), f(k["n_pos"])
    tv, tk = f(r["via_tbg"]), f(k["t_bg"])
    filas.append({"dt": r["dt"], "sensor": r["sensor"], "z": z, "npix_via": nv, "n_pos_K": nk, "pc_n_K": f(k["pc_n"]),
                  "tbg_via": tv, "tbg_K_anillo": tk})
    if nv and nk:
        npix.append((z, nv / nk, r["sensor"]))
    if tv and tk:
        dtbg.append((z, tk - tv, r["sensor"]))
res = {"n_pasadas": len(filas), "npix_via_sobre_npos_K": resumen(npix, "npix"),
       "tbgK_menos_tbgvia_K": resumen(dtbg, "dtbg"),
       "npix_via_por_tramo": resumen([(x["z"], x["npix_via"], x["sensor"]) for x in filas], "nv"),
       "npos_K_por_tramo": resumen([(x["z"], x["n_pos_K"], x["sensor"]) for x in filas if x["n_pos_K"]], "nk")}

d = json.load(open(S157, encoding="utf-8"))
P = [p for p in d["pasadas"] if p.get("b") == "VIIRS375" and p.get("lab") == "pos" and p.get("M")]
res["s157_meta_ventana"] = {k: d["meta"].get(k) for k in ("desde", "hasta", "ventana", "generado_utc") if k in d["meta"]}
res["s157_n_pos_v375"] = len(P)
for campo in ("R", "G", "G_fondo0", "G_area", "G_area_fondo0", "f_area", "F_rec"):
    res[f"s157_{campo}"] = resumen([(p["cenital"], p[campo], p["sensor"]) for p in P
                                    if p.get(campo) is not None and p.get("cenital") is not None], campo)
res["detalle"] = sorted(filas, key=lambda x: x["z"])
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "detalle"}, indent=1, ensure_ascii=False))
for x in res["detalle"]:
    print(x)
