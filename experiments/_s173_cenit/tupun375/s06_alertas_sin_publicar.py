# -*- coding: utf-8 -*-
"""s06 (S173 tupun375): alertas de MIROVA (U, D-9 SN) en Tupungatito VIIRS 375 que K no publica, con cenit, fuente de la
referencia y lo que dice el record K (clase, t_bg, t_max, n de píxeles con VRP > 0).
POR QUÉ: si el fondo de anillo con recorte borra el foco diluido, las alertas perdidas deberían concentrarse en cenit
alto con K summit y 0 píxeles con VRP > 0; si son fuentes lejanas, K las marca far.
P1: el conteo debe coincidir con n_alerta_sin_publicar de s01_k_resumen.json (11). P2: si el CSV no se leyera, 0 filas.
Uso: python -B s06_alertas_sin_publicar.py s01_k_pasadas.csv"""
import csv, json, sys
R = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")) if r["b"] == "VIIRS375"]
sel = [r for r in R if r["vrp_M"] and float(r["vrp_M"]) > 0 and not (r["pub"] == "1" and r["disp"] and float(r["disp"]) > 0)]
print("n", len(sel), "(s01 dice", json.load(open("s01_k_resumen.json", encoding="utf-8"))["por_sensor"]["VIIRS375"]["n_alerta_sin_publicar"], ")")
for r in sorted(sel, key=lambda r: float(r["z"])):
    sosp = r["src_M"] == "OCR" and r["sensor"] == "VIIRS_SNPP" and r["dt"][:10] < "2026-10-09"
    print(r["dt"], r["sensor"], "z", r["z"], "M", r["vrp_M"], r["src_M"], "dist_M", r["dist_M"], "| K pub", r["pub"], "disp", r["disp"],
          "dc", r["dc"], "pc_dist", r["pc_dist"], "n_pos", r["n_pos"], "t_bg", r["t_bg"], "t_max", r["t_max"], "fhs", r["fhs"], "SOSPECHOSA" if sosp else "")
