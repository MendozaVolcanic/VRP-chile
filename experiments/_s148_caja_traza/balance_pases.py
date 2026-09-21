"""S148 - balance primer pase / segundo pase entre el control B y el brazo G, todos los records.

FENOMENO. Si la caja actua en el primer pase y el segundo pase (que sigue usando el circulo) la
deshace, lo que el primer pase pierde en G lo tiene que ganar el segundo, pixel por pixel, y el
total de pixeles anomalos casi no se mueve. Esto lo cuenta sobre TODOS los records pareados por
granulo (sin filtro de etiqueta ni de publicacion), por sensor.

Ademas, cota de lo que un segundo pase con caja podria apagar entre los 51: pasadas donde en B
todos los pixeles eran del primer pase (recaptura 0) y en G el primer pase quedo en 0. Esos
pixeles fallaron el umbral estricto con seguridad; hoy vuelven solo por el segundo pase.

Datos: copia local de trabajo prelim_s148 (no esta en git), ventana 2026-09-01 a 2026-09-17.
Uso: PYTHONIOENCODING=utf-8 python experiments/_s148_caja_traza/balance_pases.py
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "experiments" / "_s147_lectura" / "experiments" / "_s146_ab_sin_test1" / "salidas" / "prelim_s148"
CONTROL, BRAZO = "_s146_ab_sin_test1", "_s147_ab_sin_test1_caja"
V = ("2026-09-01", "2026-09-17")


def bucket(s):
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


tot = defaultdict(lambda: defaultdict(int))
for f in sorted((D / CONTROL).glob("*.json")):
    A = {r["granule"]: r for r in json.load(open(f, encoding="utf-8"))["records"]}
    B = {r["granule"]: r for r in json.load(open(D / BRAZO / f.name, encoding="utf-8"))["records"]}
    for g, ra in A.items():
        rb = B.get(g)
        if rb is None or not (V[0] <= ra.get("datetime_utc", "")[:10] <= V[1]):
            continue
        t = tot[bucket(ra["sensor"])]
        fa, fb = ra.get("diag_n_first_pass_pixels") or 0, rb.get("diag_n_first_pass_pixels") or 0
        sa, sb = ra.get("diag_n_second_pass_recapture") or 0, rb.get("diag_n_second_pass_recapture") or 0
        na, nb = ra.get("n_anomalous_pixels") or 0, rb.get("n_anomalous_pixels") or 0
        t["records"] += 1
        t["fp_B"] += fa; t["fp_G"] += fb
        t["sp_B"] += sa; t["sp_G"] += sb
        t["anom_B"] += na; t["anom_G"] += nb
        t["records donde cambia el 1er pase"] += int(fa != fb)
        t["  de esos, el 2do pase compensa exacto"] += int(fa != fb and fa - fb == sb - sa)
        t["  de esos, n_anomalous identico"] += int(fa != fb and na == nb)
        t["records donde cambia n_anomalous"] += int(na != nb)
for s, t in sorted(tot.items()):
    print(f"\n== {s} ==")
    for k, v in t.items():
        print(f"  {k}: {v}")
