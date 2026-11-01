"""R3 (censo antes de ponderar), control positivo (c) del frente N de S159.

Pregunta 1 del instrumento: si el estimador ponderado excediera su techo fisico, esta medicion lo ve? Si: compara
`neg_encendidos` ponderado (resumen.json) contra el numero de negativos limpios donde el brazo F PUEDE actuar
(poblacion_completa.json: negativos no publicados por K con algun pixel alertado = clases cumbre_0mw + far), y
contra el censo (07_censo_analizar_salida.txt).
Pregunta 2: si el instrumento estuviera muerto, se veria? Si: el script falla si no encuentra las tres cifras.
"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
N = "experiments/_s159/n/"
res = json.load(open(N + "resumen.json"))
pob = json.load(open(N + "poblacion_completa.json"))
cl = json.load(open(N + "objetivos_censo.json"))
meta=pob["meta"]; print("ventana poblacion:", meta["ventana"], "| regla:", meta.get("regla_minimas"), "| tol:", meta.get("tol_pareo_s"), "| pasadas:", len(pob["pasadas"]))
neg_act=[p for p in pob["pasadas"] if p.get("lab")=="neg_limpio" and p.get("decide") and not p.get("pub_prod") and p.get("dc") in ("summit","far") and (p.get("pc_vrp") is not None)]
print("negativos limpios no publicados con distance_class (pixel alertado) en poblacion_completa:", len(neg_act), "| sin 18 y 19 de octubre:", len([p for p in neg_act if not p["hora_utc"].startswith(("2026-10-18","2026-10-19"))]))
pond = res["F"]["neg_encendidos"]; dE_pond = res["F"]["dE_central"]; ic = res["F"]["ic95_dE"]
print("estimador ponderado F: neg_encendidos = %.2f ; dE = %.2f ; IC95 = %s ; veredicto = %s" % (pond, dE_pond, ic, res["F"]["veredicto"]))
# techo fisico: objetivos del censo por clase
from collections import Counter
clases = Counter(o.get("clase") for o in cl)
techo = clases.get("cumbre_0mw", 0) + clases.get("far", 0)
print("clases del censo:", dict(clases), "| techo fisico (cumbre_0mw + far) =", techo)
txt = open(N + "07_censo_analizar_salida.txt", encoding="utf-8").read()
m = re.search(r"dE_F \(censo\) = (\d+) - (\d+) - (\d+) = (\d+)", txt)
m2 = re.search(r"negativos encendidos por F: (\d+) de (\d+) medidos", txt)
assert m and m2, "no encuentro el censo"
print("censo: encendidos %s de %s medidos ; dE_F(censo) = %s" % (m2.group(1), m2.group(2), m.group(4)))
r3 = "FALLA" if (pond > techo or (techo <= 300 and abs(pond - round(pond)) > 1e-9)) else "OK"
print("R3 del instrumento ponderado: %s (ponderado %.2f %s techo %d; subconjunto contable n=%d y el instrumento pondero)" % (r3, pond, ">" if pond > techo else "<=", techo, techo))
print("control positivo (c): dE ponderado %+.0f contra censo %+d -> %s" % (dE_pond, int(m.group(4)), "ENCONTRADO" if abs(dE_pond-104)<1 and int(m.group(4))==12 else "NO ENCONTRADO"))
