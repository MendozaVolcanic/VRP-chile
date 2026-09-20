# -*- coding: utf-8 -*-
"""V-01b: que definicion de 'confirmado' reproduce ~96,7 % sobre la poblacion S113 (05-01..06-18, t_bg<262, path-D dominante, summit, pc>0)?
(1) roto? imprime n y cada variante. (2) muerto? la variante ALERTA estricta y la RUTINA-incluida deben diferir (si dan igual, el pareo no discrimina)."""
import io, sys, datetime as dt
from collections import Counter
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); REF = referencia(); w = ("2026-05-01", "2026-06-18")
su = []
for v in VOLS:
    for r in D[v]:
        f = r["datetime_utc"][:10]
        if not (w[0] <= f <= w[1]): continue
        pc = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        d = r.get("diag_n_dnti_ctx_path") or 0; o = sum(r.get(k) or 0 for k in ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
        if pc > 0 and r.get("t_bg_k") is not None and r["t_bg_k"] < 262 and d > o and r.get("distance_class") == "summit":
            su.append((v, r["datetime_utc"], bucket(r["sensor"]), pc))
n = len(su); print("poblacion", n, "por volcan", Counter(x[0] for x in su), "por sensor", Counter(x[2] for x in su))
byvol = {}
for f in REF: byvol.setdefault(f["vol"], []).append(f)
def t(s): return dt.datetime.fromisoformat(s[:16] if len(s) >= 16 else s)
for nombre, tipos in (("ALERTA", {"ALERTA_TERMICA"}), ("ALERTA+OCR", {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR"}), ("cualquier fila (incl. RUTINA)", None)):
    for tol in (10, 30, 120, 720):
        for mismo_sensor in (True, False):
            k = 0
            for v, d0, b, _ in su:
                T = t(d0)
                if any((tipos is None or f["tipo"] in tipos) and (not mismo_sensor or f["b"] == b) and abs((t(f["dt"]) - T).total_seconds()) <= tol * 60 for f in byvol.get(v, [])): k += 1
            print(f"{nombre:32s} tol={tol:4d}min mismo_sensor={mismo_sensor}: {k}/{n} = {100*k/n:.1f}%")
# alertas de MIROVA alguna vez en la ventana por volcan (tasa base): un volcan con alerta casi todas las noches 'confirma' cualquier cosa
for v in sorted({x[0] for x in su}):
    dias = {f["fecha"] for f in byvol.get(v, []) if f["tipo"] in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR") and w[0] <= f["fecha"] <= w[1]}
    print("tasa base", v, "dias con alerta MIROVA en ventana:", len(dias), "de 49")
