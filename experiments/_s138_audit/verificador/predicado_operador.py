"""VERIFICADOR S138 (discrepancia c): re-puntua los 8 brazos de la bateria del Apendice A con el
predicado que usa el dashboard, escrito desde frontend/index.html y no desde el script de ningun eje.

mirovaEqVrp (frontend/index.html:1043-1064): devuelve 0 si distance_class existe y no es "summit";
0 si primary_cluster.centroid_dist_km > innerKm; si no, pc.vrp_mw. isValidDetection (l.1466-1470)
exige vrp > 0 (o triggered_test1). La bateria (conformidad_apendice.py:158-160) no mira
distance_class: publica = vrp_pc_mw > 0 y dist_crater_km <= 5.

DOS PREGUNTAS. (1) Si un brazo cambiara de veredicto, se veria: el control de identidad reproduce
los 6/6 y 0/3 commiteados con el predicado de la bateria. (2) Si el instrumento estuviera muerto,
todos los brazos darian lo mismo; dan distinto. Control adicional: un predicado que exija
distance_class == "imposible" tiene que dar 0/6 en los ocho brazos.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
INNER = 5.0
BRAZOS = [
    ("_s136/out_apendice (B21 min = produccion)", "_s136/out_apendice"),
    ("_s136/out_apendice_prosa", "_s136/out_apendice_prosa"),
    ("_s137/out_apendice_b22", "_s137/out_apendice_b22"),
    ("_s137/out_apendice_b22_prosa", "_s137/out_apendice_b22_prosa"),
    ("_s137/out_apendice_b22_sincompuerta", "_s137/out_apendice_b22_sincompuerta"),
    ("_s137/out_apendice_b22_sincompuerta_prosa", "_s137/out_apendice_b22_sincompuerta_prosa"),
    ("_s137/..._sincompuerta_fondolocal", "_s137/out_apendice_b22_sincompuerta_fondolocal"),
    ("_s137/..._sincompuerta_fondolocal_prosa", "_s137/out_apendice_b22_sincompuerta_fondolocal_prosa"),
]


def pub_bateria(p):
    v = p.get("vrp_pc_mw")
    d = p.get("dist_crater_km")
    return v is not None and v > 0 and d is not None and d <= INNER


def pub_dashboard(p, clase_exigida="summit"):
    dc = p.get("distance_class")
    if dc is not None and dc != clase_exigida:
        return False
    return pub_bateria(p)


def contar(dirrel, pub):
    casos = json.loads((RAIZ / "experiments" / dirrel.lstrip("_") if False else RAIZ / ("experiments/" + dirrel) / "resultado_apendice.json").read_text(encoding="utf-8"))
    pos_ok = neg_ok = npos = nneg = 0
    detalle = []
    for c in casos:
        publica = any(pub(p) for p in c["pasadas"])
        if c["veredicto_paper"] == "detecta":
            npos += 1
            pos_ok += publica
            detalle.append((c["caso"], "pos", publica))
        else:
            nneg += 1
            neg_ok += (not publica)
            detalle.append((c["caso"], "neg", publica))
    return pos_ok, npos, neg_ok, nneg, detalle


if __name__ == "__main__":
    print(f"{'brazo':45s} {'bateria':>10s} {'dashboard':>10s}   casos que cambian")
    for nom, d in BRAZOS:
        b = contar(d, pub_bateria)
        s = contar(d, pub_dashboard)
        camb = [f"{x[0]}({x[1]})" for x, y in zip(b[4], s[4]) if x[2] != y[2]]
        print(f"{nom:45s} {b[0]}/{b[1]} {b[2]}/{b[3]:<4d} {s[0]}/{s[1]} {s[2]}/{s[3]:<4d}  {', '.join(camb)}")
    print("\nCONTROL NEGATIVO (exigir distance_class == 'imposible'):")
    for nom, d in BRAZOS[:3]:
        s = contar(d, lambda p: pub_dashboard(p, "imposible"))
        print(f"  {nom:45s} {s[0]}/{s[1]} {s[2]}/{s[3]}")
    print("\nDISTRIBUCION de distance_class en el brazo de produccion:")
    casos = json.loads((RAIZ / "experiments" / "_s136" / "out_apendice" / "resultado_apendice.json").read_text(encoding="utf-8"))
    from collections import Counter
    cc = Counter(p.get("distance_class") for c in casos for p in c["pasadas"])
    print("  todas las pasadas:", dict(cc))
    cc2 = Counter(p.get("distance_class") for c in casos for p in c["pasadas"] if pub_bateria(p))
    print("  solo las que la bateria cuenta como publicadas:", dict(cc2), "total", sum(cc2.values()))
    print("\nTOPE D9 (diag_n_nti_path == 0 y vrp == 5.0) en el brazo de produccion:")
    for c in casos:
        for p in c["pasadas"]:
            if p.get("vrp_pc_mw") == 5.0:
                print(f"  {c['caso']} {p['inicio']} vrp={p['vrp_pc_mw']} npx={p['n_pixels_pc']} "
                      f"nti_path={p['diag_n_nti_path']} dist={round(p['dist_crater_km'],2)} clase={p['distance_class']}")
