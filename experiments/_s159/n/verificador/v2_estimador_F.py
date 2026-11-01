# -*- coding: utf-8 -*-
"""Verificador S159 N, paso 2: el estimador de dE de F (afirmacion 1) mirado por dentro.

Que se pregunta: los 6 negativos que F enciende, en que estratos caen, con que peso, que magnitud y de que pase
salen; cuanto pesa cada uno en dE; si dE sigue > 0 quitando el evento mas pesado o los dos; cuantos eventos hacen
falta para que dE cruce 0; y una cota inferior que no depende del bootstrap (Poisson exacta por estrato).
P1: si el estimador estuviera mal ponderado, la suma de pesos por estrato no daria el tamano del estrato en la
poblacion (se compara con poblacion_completa.json). P2: si no hubiera eventos, dE seria -48 (las alertas ganadas,
censo); el resultado distinto de -48 es el efecto de los eventos, no del instrumento.
Ventana: pasadas VIIRS 750 nocturnas 2026-04-01 a 2026-10-21 sin 10-18/10-19 (objetivos_n.json).
"""
import collections, io, json, math, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; N = AQUI.parent
obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
V = json.load(open(AQUI / "v1_pub.json")); P = {tuple([int(k.split("|")[0]), k.split("|")[1]]): v for k, v in V["P"].items()}
ok = set(V["ok"])
res = {}
for f in sorted((N / "run_39682867040").glob("*resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
pub = lambda i, b: P.get((i, b), False)
# 1. pesos por estrato contra la poblacion
pob = json.loads((N / "poblacion_completa.json").read_text(encoding="utf-8"))
print("poblacion_completa: tipo", type(pob).__name__, "n", len(pob))
est = lambda o: f"{o['volcan']}|{o['estrato_z']}"
neg_sel = [i for i, o in obj.items() if o["clase"] == "neg_resto" and o["peso"] > 0]
Wsum = collections.defaultdict(float); n_s = collections.Counter(); n_ok = collections.Counter(); W_ok = collections.defaultdict(float)
for i in neg_sel:
    Wsum[est(obj[i])] += obj[i]["peso"]; n_s[est(obj[i])] += 1
    if i in ok:
        n_ok[est(obj[i])] += 1; W_ok[est(obj[i])] += obj[i]["peso"]
print("neg_resto: suma de pesos de la muestra", round(sum(Wsum.values()), 1), "| en pasadas ok", round(sum(W_ok.values()), 1))
# 2. los eventos
ev = [i for i in ok if obj[i]["lab"] == "neg_limpio" and pub(i, "F") and not pub(i, "K")]
print("\nnegativos encendidos por F:", len(ev))
for i in ev:
    o, r = obj[i], res[i]; k = r["brazos"]["K"]; f = r["brazos"]["F"]
    kpc = (k["record"] or {}).get("primary_cluster") or {}; fpc = (f["record"] or {}).get("primary_cluster") or {}
    og = (r.get("oraculo") or {}); gl = og.get("geo_linear") or {}; an = og.get("geo_linear_anillo_sensible") or {}
    print(f"  id {i} {o['volcan']} {o['hora_utc']} {o['estrato_z']} peso {o['peso']:.2f} (estrato n={n_s[est(o)]}, "
          f"N~{Wsum[est(o)]:.0f}) | K pc {kpc.get('n_pixels')}px {kpc.get('vrp_mw')} dc {(k['record'] or {}).get('distance_class')} "
          f"| F pc {fpc.get('n_pixels')}px {fpc.get('vrp_mw')} banda {[round(x,3) for x in f.get('F_pc_banda') or []]} "
          f"primer_pase {f.get('pc_pix_primer_pase')} | O geo_lin {gl.get('npix')}px n_abs {gl.get('n_abs')} n_p1 {gl.get('n_p1')} "
          f"n_p2 {gl.get('n_p2')} | O anillo {an.get('npix')}px | MIROVA filas {[ (m['tipo'], m['vrp_mw']) for m in o['mirova']]}")
# 3. dE y sensibilidad
mb_gan = sum(obj[i]["peso"] for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"] and not obj[i]["protegida"]
             and pub(i, "F") and not pub(i, "K"))
mb_per = sum(obj[i]["peso"] for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"] and not obj[i]["protegida"]
             and pub(i, "K") and not pub(i, "F"))
enc = sum(obj[i]["peso"] for i in ev)
print(f"\nalertas bajo 1 MW ganadas {mb_gan:.1f}, perdidas {mb_per:.1f}; negativos encendidos {enc:.1f}; dE = {enc - mb_gan + mb_per:.1f}")
ws = sorted((obj[i]["peso"] for i in ev), reverse=True)
for q in range(0, len(ws) + 1):
    print(f"  quitando los {q} eventos mas pesados: dE = {sum(ws[q:]) - mb_gan + mb_per:.1f}")
# eventos minimos para cruzar 0 con el peso medio de neg_resto
wm = sum(W_ok.values()) / sum(n_ok.values())
print(f"peso medio de neg_resto {wm:.1f}; eventos para cruzar 0: {mb_gan / wm:.2f}")
# 4. cota Poisson exacta (sobre el total de eventos, con el peso de cada estrato): cota inferior 95 % unilateral y bilateral
def poisson_lo(k, a):
    # cota inferior exacta: chi2_{2k, a}/2
    from scipy.stats import chi2
    return 0.0 if k == 0 else chi2.ppf(a, 2 * k) / 2
for a, nom in ((0.05, "unilateral 95"), (0.025, "bilateral 95")):
    lo = poisson_lo(len(ev), a)
    # escala: cada evento con el peso medio de los eventos observados y con el peso minimo de neg_resto
    wmin = min(obj[i]["peso"] for i in neg_sel)
    print(f"Poisson {nom}: eventos >= {lo:.2f}; x peso medio de los eventos {enc/len(ev):.1f} -> {lo*enc/len(ev):.1f}; "
          f"x peso medio neg_resto {wm:.1f} -> {lo*wm:.1f}; x peso minimo {wmin:.1f} -> {lo*wmin:.1f} (dE cruza 0 bajo {mb_gan:.0f})")
