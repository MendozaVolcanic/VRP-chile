# -*- coding: utf-8 -*-
"""S150. Sobre la imagen de MIROVA (tif_contraste.json): ¿que separa mejor lo que MIROVA alerto de lo
que MIROVA callo (residual), un contraste NORMALIZADO por la sigma de la escena (z, como mu + C2*sigma)
o un exceso ABSOLUTO (dNTI aproximado contra el piso C1)? Si MIROVA decidiera por el estadistico de la
escena, z deberia separar mejor; si decidiera por el piso fijo, el absoluto.
Se informa tambien el estrato debil (MIROVA < 0,10 MW), que es donde `max` pierde.

  python tif_que_separa.py tif_contraste.json
"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = json.load(open(sys.argv[1], encoding="utf-8"))


def auc(pos, neg):
    pos = [x for x in pos if x is not None]; neg = [x for x in neg if x is not None]
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg)), len(pos), len(neg)


neg = [m for m in R if m["grupo"].startswith("residual")]
for nombre, pos in (("todas las alertas con TIF", [m for m in R if not m["grupo"].startswith("residual")]),
                    ("alertas < 0,10 MW", [m for m in R if not m["grupo"].startswith("residual") and m["mirova_mw"] is not None and m["mirova_mw"] < 0.10]),
                    ("solo las perdidas por F", [m for m in R if m["grupo"] == "perdida por F"])):
    print("==", nombre)
    for var in ("z_ventana", "z_ventana_robusto", "dL_ventana", "dnti_proxy_mirova"):
        a, n1, n0 = auc([m.get(var) for m in pos], [m.get(var) for m in neg])
        print("   %-20s AUC alerta contra residual %.3f (n %d contra %d)" % (var, a, n1, n0))
    # umbral que dejaria pasar todas las perdidas: cuantos residuales pasarian
for var in ("z_ventana", "dnti_proxy_mirova"):
    perd = sorted(m[var] for m in R if m["grupo"] == "perdida por F" and m.get(var) is not None)
    for corte in perd[:3]:
        print("corte %s >= %.4f: residual que pasa %d de %d | conservadas debiles que pasan %d de %d" % (
            var, corte, sum((m.get(var) or -9) >= corte for m in neg), len(neg),
            sum((m.get(var) or -9) >= corte for m in R if m["grupo"] == "conservada por F" and (m["mirova_mw"] or 9) < 0.10),
            sum(1 for m in R if m["grupo"] == "conservada por F" and (m["mirova_mw"] or 9) < 0.10)))
