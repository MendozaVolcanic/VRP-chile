"""S136 - que rama de los Tests 2/3 gobierna la deteccion: el piso absoluto o el contraste?

EL PAPER (sp426_5.txt:317-329) define Test 2 como  dNTI > C1  OR  dNTI > mu + C2*sigma,
y el codigo lo implementa como  dNTI > min(C1, mu + C2*sigma)  — equivalente exacto.
De ahi sale el diagnostico sin instrumentar nada: la rama que MANDA es la del umbral menor.

  si  mu + C2*sigma < C1  -> manda el CONTRASTE (la escena es homogenea; el umbral se adapta)
  si  C1 < mu + C2*sigma  -> manda el PISO ABSOLUTO C1 (la escena es variable y el piso la corta)

Importa porque la bateria del Apendice A mostro que la sobre-deteccion la produce el primer pase
contextual con los umbrales del paper puestos. Si el piso C1 es el que dispara, el frente es el
piso; si es el contraste, el frente es el pool sobre el que se calculan mu y sigma.

READ-ONLY sobre los records ya en disco. Reporta con denominador (A90).
"""
import os, sys, json, statistics as st
ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT)
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import pipeline.profile as P

C1S, C2S = P.DNTI_CONTEXTUAL_C1_SUMMIT, P.C2_DNTI_SUMMIT_NIGHT
C1E, C2E = P.DNTI_CONTEXTUAL_C1_SCENE, P.C2_DNTI_SCENE_NIGHT
print(f"Tabla 1 del paper, noche:  cumbre C1={C1S} C2={C2S}   escena C1={C1E} C2={C2E}\n")
TIER_A = ["Villarrica","Lascar","Isluga","NevadosDeChillan","Llaima","Chaiten","Copahue",
          "Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]

def bucket(s):
    if not s: return None
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS"): return "V750" if s.endswith("_750") else "V375"
    return None

agg = {}
for vol in TIER_A:
    p = os.path.join(ROOT,"data","mirova_equivalent",f"{vol}.json")
    if not os.path.exists(p): continue
    d = json.load(open(p,encoding="utf-8")); recs = d.get("records", d)
    for r in recs:
        b = bucket(r.get("sensor"))
        mu, sd = r.get("diag_mu_dnti"), r.get("diag_sd_dnti")
        if b is None or not isinstance(mu,(int,float)) or not isinstance(sd,(int,float)):
            continue
        est_s, est_e = mu + C2S*sd, mu + C2E*sd
        k = agg.setdefault(b, {"n":0,"piso_s":0,"piso_e":0,"est_s":[],"sd":[]})
        k["n"] += 1
        k["piso_s"] += (C1S < est_s)      # manda el piso en la cumbre
        k["piso_e"] += (C1E < est_e)      # manda el piso en la escena
        k["est_s"].append(est_s); k["sd"].append(sd)

print(f"{'sensor':8s} {'records':>8s} {'manda PISO en cumbre':>21s} {'manda PISO en escena':>21s}"
      f" {'mediana mu+5sd':>15s} {'mediana sd':>11s}")
print("-"*90)
for b in ("MODIS","V375","V750"):
    k = agg.get(b)
    if not k: continue
    print(f"{b:8s} {k['n']:8d} {k['piso_s']:9d} ({100*k['piso_s']/k['n']:5.1f}%) "
          f"{k['piso_e']:12d} ({100*k['piso_e']/k['n']:5.1f}%) "
          f"{st.median(k['est_s']):15.5f} {st.median(k['sd']):11.5f}")
print("\nInterpretacion: 'manda el PISO' = el umbral efectivo es C1, o sea el contraste con la")
print("escena quedo MAS ALTO que el piso y el piso es el que deja pasar pixeles. Si esa fraccion")
print("es alta, la deteccion la gobierna un numero fijo y no la variabilidad de cada escena.")
