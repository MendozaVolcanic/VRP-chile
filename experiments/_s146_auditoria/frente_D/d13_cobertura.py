# -*- coding: utf-8 -*-
"""d13: cobertura del frente D. Asigna cada uno de los 89 cierres del censo a una categoria (el MAPA es juicio mio, declarado aca;
los CONTEOS salen del script). Instrumento: (1) un cierre sin categoria cae en 'SIN_ASIGNAR' y el script lo lista: no se pierde nada.
(2) total debe ser 89."""
import io, sys, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
J = json.load(open("d00_cierres_con_cifra.json", encoding="utf-8"))["afirmaciones"]
N = "NO_TOCADO_por_alcance(salidas de A/B o probes que no estan en disco; tiempo)"
R, T, S145, F, H = "REMEDIDO", "TRAZADO_A_FUENTE", "YA_AUDITADO_S145", "CIFRA_ES_PARAMETRO_FISICO_O_CITA(frente C)", "NO_TOCADO_HISTORICO(corpus reprocesado)"
M = {("docs/MIROVA_DIVERGENCES.md", l): c for l, c in {
    289: N, 435: N, 455: F, 515: R, 534: R, 656: N, 1259: R, 1315: F, 1319: F, 1368: R, 1403: T, 1405: N, 1441: T, 1504: R, 1509: R,
    1545: R, 1550: F, 1999: R, 2039: R, 2067: T, 2194: R, 2200: R, 2205: R, 2222: R, 2304: S145, 2353: S145, 2377: S145,
    224: H, 1088: H, 1090: H, 1129: H, 1186: H, 1196: H, 1249: H, 1819: F}.items()}
M.update({("CLAUDE.md", l): c for l, c in {102: F, 112: F, 119: S145, 120: F, 124: F, 324: N, 948: R, 952: R, 953: R, 963: R, 965: R, 967: R, 968: R,
    983: R, 996: N, 1001: N, 1114: N, 1412: F, 1512: N, 1513: R, 1515: R}.items()})
M.update({("docs/MISSION.md", l): c for l, c in {106: R, 107: R, 110: R, 142: R}.items()})
out = Counter(); sin = []; filas = []
for a in J:
    k = (a["archivo"], a["linea_censo"])
    if not a["cifras_en_entorno"]: c = "SIN_CIFRA(fuera del frente D)"
    elif k in M: c = M[k]
    elif a["archivo"].endswith("HYPOTHESIS_LOG.md"): c = H
    else: c = "SIN_ASIGNAR"; sin.append(k)
    out[c] += 1; filas.append((a["archivo"], a["linea_hoy"], ",".join(a["tipos"]), c))
print("total", sum(out.values())); [print(f"{v:3d}  {k}") for k, v in out.most_common()]; print("sin asignar:", sin)
json.dump({"conteo": out, "filas": filas}, open("d13_cobertura.json", "w"), indent=1, ensure_ascii=False)
