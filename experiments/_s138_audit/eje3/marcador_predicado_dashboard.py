"""S138 eje 3 - la bateria del Apendice A re-puntuada con el predicado del DASHBOARD.

evaluar_caso (experiments/_s136/conformidad_apendice.py:158-160) cuenta 'publica' cuando
pc.vrp_mw > 0 y el centroide del cumulo esta a <= 5 km del centro. El operador ve otra cosa:
frontend/index.html mirovaEqVrp (l. 1043-1063) devuelve 0 si distance_class != 'summit' o si
pc.centroid_dist_km > innerKm. Este script repite el conteo por caso y por brazo exigiendo
ademas distance_class == 'summit', sobre los MISMOS JSON commiteados (no recalcula nada).
Ventana: las 9 fechas del Apendice A; denominador: pasadas nocturnas MODIS de cada fecha.
"""
import json, glob
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
INNER = 5.0
ORDEN = ["_s136/out_apendice", "_s136/out_apendice_prosa", "_s137/out_apendice_b22", "_s137/out_apendice_b22_prosa",
         "_s137/out_apendice_b22_sincompuerta", "_s137/out_apendice_b22_sincompuerta_prosa",
         "_s137/out_apendice_b22_sincompuerta_fondolocal", "_s137/out_apendice_b22_sincompuerta_fondolocal_prosa"]
def pub_bateria(p):
    return (p.get("vrp_pc_mw") or 0) > 0 and p.get("dist_crater_km") is not None and p["dist_crater_km"] <= INNER
def pub_dashboard(p):
    return pub_bateria(p) and p.get("distance_class") == "summit"
print(f"{'brazo':52s} {'bateria pos/neg':>16s} {'dashboard pos/neg':>18s}   casos que cambian")
for d in ORDEN:
    r = json.load(open(RAIZ / "experiments" / d / "resultado_apendice.json", encoding="utf-8"))
    pb = pn = db = dn = 0; cambian = []
    for c in r:
        pas = c["pasadas"]
        npap = c.get("nti_paper")
        if npap is not None:
            pas = [p for p in pas if isinstance(p["nti_max"], (int, float)) and abs(p["nti_max"] - npap) <= 0.06]
        b = any(pub_bateria(p) for p in pas); dsh = any(pub_dashboard(p) for p in pas)
        pos = c["veredicto_paper"] == "detecta"
        if pos: pb += b; db += dsh
        else: pn += (not b); dn += (not dsh)
        if b != dsh: cambian.append(f"{c['caso']}({'pos' if pos else 'neg'}: bat={'pub' if b else 'no'} dash={'pub' if dsh else 'no'})")
    print(f"{d:52s} {pb}/6 {pn}/3          {db}/6 {dn}/3        " + ", ".join(cambian))
