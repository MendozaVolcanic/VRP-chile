# -*- coding: utf-8 -*-
"""F4-11: con la banda 22 primaria, la BT del pixel viene de la banda 22 (lambda 3,959) pero el VRP la vuelve
radiancia con lambda 3,929 (process_modis.py:1036-1062). ¿Cuanto sesga el exceso de radiancia dL?
Se compara dL(l21) contra dL(l22) para pares (T_bg, T_hot) tipicos, y sobre los records K de MODIS con cumulo
(t_bg_k y la BT de los pixeles anomalos persistidos). P1: con T_hot = T_bg ambos dan 0; con l21 = l22 el
cociente da 1 (control). P2: records sin pixeles se excluyen y se cuentan."""
import io, json, sys, math, collections, statistics
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 1.4387752e4  # W um^4 m^-2 sr^-1, um K (constantes de Planck en las unidades del repo)
B = lambda l, T: C1 / (l ** 5 * (math.exp(C2 / (l * T)) - 1))
l21, l22 = 3.929, 3.959
print("control l21=l21:", (B(l21, 280) - B(l21, 260)) / (B(l21, 280) - B(l21, 260)))
for tb in (240, 260, 275):
    for dt in (2, 5, 10, 30, 100):
        th = tb + dt
        print(f"T_bg {tb} T_hot {th}: dL(l21)/dL(l22) = {(B(l21, th) - B(l21, tb)) / (B(l22, th) - B(l22, tb)):.4f}")
ROOT = Path(__file__).resolve().parents[3]
rat = []; n_sin = 0
for vol in ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima",
            "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]:
    for r in json.loads((ROOT / "data/mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))["records"]:
        if not (r.get("sensor") or "").startswith("MODIS") or (r.get("processed_utc") or "") < "2026-10-18T09:57:30Z": continue
        px = [p for p in (r.get("anomaly_pixels") or []) if p.get("bt_k")]
        tb = r.get("t_bg_k")
        if not px or not tb: n_sin += 1; continue
        num = sum(max(B(l21, p["bt_k"]) - B(l21, tb), 0) for p in px)
        den = sum(max(B(l22, p["bt_k"]) - B(l22, tb), 0) for p in px)
        if den > 0: rat.append(num / den)
print("records MODIS K con pixeles:", len(rat), "sin pixeles/t_bg:", n_sin)
if rat: print("cociente dL(l21)/dL(l22) mediana", round(statistics.median(rat), 4), "min", round(min(rat), 4), "max", round(max(rat), 4))
