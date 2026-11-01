# -*- coding: utf-8 -*-
"""Verificador, R4 (tasa 0,5 % 'del orden' de 0,76 %): los dos numeros tienen denominadores distintos (neg_resto, donde
K publica 0 por definicion, contra TODOS los negativos limpios). Calculo la tasa del port en el mismo denominador que
K (5.132), punto, con las filas congeladas de S159 para neg_pub y 2/390 para neg_resto; y la de K."""
import json, sys
from pathlib import Path
D = Path(sys.argv[1])
F = json.loads((D / "filas_lote_s159_modis_fisica.json").read_text(encoding="utf-8"))["filas"]
npub = [x for x in F if x["c"] == "neg_pub"]
w_port_negpub = sum(x["w"] for x in npub if x["X"]); w_tot_negpub = sum(x["w"] for x in npub)
print(f"neg_pub (K publica, 39 pasadas): filas muestreadas {len(npub)}, peso total {w_tot_negpub:.1f}; el port publica en peso {w_port_negpub:.1f} ({sum(1 for x in npub if x['X'])} de {len(npub)} filas)")
port_todos = (w_port_negpub + 5055 * 2 / 390 + 0) / 5132
print(f"tasa del port en TODOS los negativos limpios (punto): ({w_port_negpub:.1f} + 5055*2/390 + 0)/5132 = {port_todos:.4f} = {100*port_todos:.2f} %")
print(f"tasa de K en todos los negativos limpios: 39/5132 = {39/5132:.4f} = {100*39/5132:.2f} %")
print(f"tasa del port en neg_resto (cruda): 2/390 = {2/390:.4f} = {100*2/390:.2f} %; tasa de K en neg_resto: 0/5093 por definicion del estrato")
