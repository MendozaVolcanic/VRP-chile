# -*- coding: utf-8 -*-
"""S149. UN solo script para las predicciones del pre-registro de la conectiva en otra ventana, sobre
la tabla que arma armar_tabla.py. Existe porque el evaluador no calcula P2, P5 ni P6 y el script de
S148 que daba P2 estaba atado a su tabla de septiembre (verificador del pre-registro, H5).
Probado sobre septiembre: tiene que devolver lo ya publicado en docs/S148_RESULTADO_AB_CONECTIVA.md y
docs/S149_COSTO_OCULTO_MAX.md (ver medir_predicciones_septiembre_salida.txt).

  python medir_predicciones.py tabla.json [SENSOR]
"""
import json, math, random, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = json.load(open(sys.argv[1], encoding="utf-8")); SENSOR = sys.argv[2] if len(sys.argv) > 2 else "VIIRS375"
UMBRAL_P1, UMBRAL_P2, MIN_ZONA, FRAC_P4, MW_P4 = 0.18, 1.3, 10, (118, 141), 0.5
rows = []
for k, v in T["pasadas"].items():
    vol, b, dt = k.split("|")
    if b == SENSOR and len(v) == 2:
        c, f = v["control"], v["brazo"]
        rows.append(dict(vol=vol, dt=dt, lab=c["lab"], pB=c["pub"], pF=f["pub"], z=c["z"], ref=c["vrp_ref"], plat=c.get("plataforma"),
                         rut=c["rutina_pasada"], nal=c["noche_con_alerta_sensor"], solo_ocr=c.get("alerta_solo_ocr", False)))
print("ventana", T["ventana"], "| sensor", SENSOR, "| pasadas en ambos brazos:", len(rows))
def zona(z): return None if z is None else ("nadir" if z < 36 else ("medio" if z < 52 else "borde"))
neg = [r for r in rows if r["lab"] == "neg_limpio"]; pos = [r for r in rows if r["lab"] == "pos"]
tB = sum(r["pB"] for r in neg) / len(neg) if neg else float("nan"); tF = sum(r["pF"] for r in neg) / len(neg) if neg else float("nan")
print("\nP1. publicacion en negativos limpios (n %d): control %.1f %% | brazo %.1f %%" % (len(neg), 100 * tB, 100 * tF))
if not neg or tB <= UMBRAL_P1: print("    INDECIDIBLE: el control ya publica %.0f %% o menos, el umbral se cumpliria sin que el brazo haga nada (H7)" % (100 * UMBRAL_P1))
else: print("    %s (umbral: brazo en %.0f %% o menos)" % ("CUMPLE" if tF <= UMBRAL_P1 else "FALLA", 100 * UMBRAL_P1))
print("\nP2. razon de la tasa falsa borde sobre nadir")
tz = {}
for zn in ("nadir", "medio", "borde"):
    s = [r for r in neg if zona(r["z"]) == zn]; tz[zn] = (sum(r["pB"] for r in s), sum(r["pF"] for r in s), len(s))
    print("    %-6s n %3d | control %3d | brazo %3d" % (zn, len(s), tz[zn][0], tz[zn][1]))
nB, nF, nn = tz["nadir"]; bB, bF, bn = tz["borde"]
if min(nn, bn) < MIN_ZONA: print("    INDECIDIBLE: menos de %d negativos limpios en nadir o en borde (H9)" % MIN_ZONA)
else:
    piso = 1.0 / nn   # si el nadir del brazo publica 0, la razon se calcula contra una publicacion (H9)
    rB = (bB / bn) / max(nB / nn, piso); rF = (bF / bn) / max(nF / nn, piso)
    print("    razon control %.2f | brazo %.2f | %s (umbral %.1f o menos)" % (rB, rF, "CUMPLE" if rF <= UMBRAL_P2 else "FALLA", UMBRAL_P2))
print("\nP4. recall por pasada")
nBp = sum(r["pB"] for r in pos); nFp = sum(1 for r in pos if r["pB"] and r["pF"]); piso4 = math.ceil(nBp * FRAC_P4[0] / FRAC_P4[1])
perd = [r for r in pos if r["pB"] and not r["pF"]]
graves = [r for r in perd if (r["ref"] or 0) >= MW_P4]
print("    positivas %d | publica el control %d | de esas conserva el brazo %d | piso ceil(n_B x 118/141) = %d | perdidas con %.1f MW o mas: %d | %s" % (
    len(pos), nBp, nFp, piso4, MW_P4, len(graves), "CUMPLE" if nFp >= piso4 and not graves else "FALLA"))
for r in perd: print("       perdida: %-20s %s | MIROVA %.3f MW | %s%s" % (r["vol"], r["dt"], r["ref"] or 0, r["plat"], " | alerta solo por OCR" if r["solo_ocr"] else ""))
sin_ocr = [r for r in pos if not r["solo_ocr"]]
print("    lo mismo con la tabla de MIROVA sola, sin OCR (H10): positivas %d | control %d | brazo conserva %d" % (len(sin_ocr), sum(r["pB"] for r in sin_ocr), sum(1 for r in sin_ocr if r["pB"] and r["pF"])))
print("\nP5. pasadas que MIROVA lista con VRP 0 en noche con alerta del sensor")
e = [r for r in rows if r["lab"] == "sin_info" and r["rut"] and r["nal"]]
if e:
    a, b_ = sum(r["pB"] for r in e), sum(r["pF"] for r in e)
    # El umbral NO es un numero fijo: un apagado parejo, sin ninguna selectividad, ya baja la razon. El
    # brazo apaga una fraccion f de TODO lo que publica el control; un apagado parejo dejaria la razon
    # de este estrato en 1 - f. P5 se cumple si el brazo recorta este estrato MAS que eso. (La primera
    # version fijaba 0,50 y en septiembre el apagado parejo daba 0,47: la cumplia el azar.)
    pubs = [r for r in rows if r["pB"]]; parejo = sum(r["pF"] for r in pubs) / len(pubs)
    razon = b_ / a if a else float("nan")
    print("    n %d | control %d (%.1f %%) | brazo %d (%.1f %%) | razon brazo sobre control %.2f | un apagado parejo daria %.2f | %s" % (
        len(e), a, 100 * a / len(e), b_, 100 * b_ / len(e), razon, parejo, "CUMPLE" if a >= 20 and razon < parejo else ("sin sustrato (menos de 20 publicadas por el control)" if a < 20 else "FALLA")))
    for pl, n in sorted(collections.Counter(r["plat"] for r in e).items(), key=lambda x: -x[1]): print("       %s: %d" % (pl, n))
    for nom, sel in (("negativos limpios", neg), ("este estrato", e), ("positivas", pos)):
        k = sum(r["pB"] for r in sel); print("       supervivencia de lo que publica el control en %-18s %3d de %3d (%.0f %%)" % (nom + ":", sum(1 for r in sel if r["pB"] and r["pF"]), k, 100 * sum(1 for r in sel if r["pB"] and r["pF"]) / k if k else 0))
else: print("    sin sustrato")
print("\nP6 (informativa, sin poder para decidir: H6). Villarrica y Nevados de Chillan, positivas una por una")
for r in sorted(pos, key=lambda r: (r["vol"], r["dt"])):
    if r["vol"] in ("Villarrica", "NevadosDeChillan"): print("    %-18s %s | MIROVA %.3f MW | control %d | brazo %d" % (r["vol"], r["dt"], r["ref"] or 0, r["pB"], r["pF"]))
print("\nC8b. selectividad a una cola (misma definicion que evaluar.selectividad_supervivencia)")
def c8b(nombre, pp):
    def est(labs):
        p = [r["pF"] for r, l in zip(pp, labs) if l == "pos"]; n = [r["pF"] for r, l in zip(pp, labs) if l == "neg_limpio"]
        return sum(p) / len(p) - sum(n) / len(n)
    if not (any(r["lab"] == "pos" for r in pp) and any(r["lab"] == "neg_limpio" for r in pp)):
        print("    %-34s sin sustrato" % nombre); return
    obs = est([r["lab"] for r in pp]); rnd = random.Random(149); g = collections.defaultdict(list)
    for i, r in enumerate(pp): g[r["vol"]].append(i)
    nul = []
    for _ in range(1000):
        labs = [None] * len(pp)
        for idx in g.values():
            ls = [pp[i]["lab"] for i in idx]; rnd.shuffle(ls)
            for i, l in zip(idx, ls): labs[i] = l
        nul.append(est(labs))
    nul.sort(); hi = nul[int(.975 * 999)]
    print("    %-34s observado %+.4f | p97,5 del nulo %+.4f | %s" % (nombre, obs, hi, "CUMPLE" if obs > hi else "FALLA"))
base = [r for r in rows if r["lab"] in ("pos", "neg_limpio") and r["pB"]]
c8b("con tabla y OCR:", base)
# A119: en ventanas que empiezan antes del 2026-06-13 DECIDE esta, porque el OCR estaba mal calibrado
c8b("con la tabla sola (sin OCR):", [r for r in base if not (r["lab"] == "pos" and r["solo_ocr"])])
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "scripts"))
import calidad_referencia_mirova as cal
print()
print("Que etiqueta DECIDE en esta ventana (A119):", cal.etiqueta_que_decide(T["ventana"][0]))
cal.avisar(T["ventana"][0], T["ventana"][1], archivo=sys.stdout)
