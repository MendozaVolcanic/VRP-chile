# -*- coding: utf-8 -*-
"""S146 frente A, paso 5 (solo lectura sobre data/mirova_equivalent):
(a) D24 "invisible hoy": BT MIR maxima de los records MODIS contra la saturacion de banda 21 (~450-500 K).
(b) A84 (CLAUDE.md:993-995): los ctx_cluster de Llaima (artefacto) y Lastarria (real) serian
    indistinguibles en n_pixels (mediana 1, ~83-93 % de un pixel) y VRP (~0,04-0,05 MW). El probe citado
    (scratchpad/probe_ctx_cluster_s117.py) NO existe en el repo; se remide.
 1. Si lo medido estuviera roto, fallaria? (a) PARCIAL: un pixel ya saturado es NaN y no entra en t_max_k,
    asi que esto mide la distancia del corpus al regimen de saturacion, no pixeles perdidos (misma cota que
    declaro S145). (b) SI: si las dos distribuciones difirieran, las medianas y fracciones lo mostrarian.
 2. Instrumento muerto? Se imprime n por grupo y el reparto de final_hotspot_source; n=0 aborta.
"""
import io, json, sys, collections, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TIERA = ["PuyehueCordonCaulle","Villarrica","Lascar","Copahue","NevadosDeChillan","Llaima","Chaiten","PlanchonPeteroa","Lastarria","Isluga","Tupungatito"]
tmax = []; src = collections.Counter(); G = collections.defaultdict(list)
for v in TIERA:
    for r in json.load(open(ROOT / f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
        if r["sensor"].upper().startswith("MODIS") and r.get("t_max_k") is not None: tmax.append((r["t_max_k"], v, r["datetime_utc"]))
        s = r.get("final_hotspot_source"); src[s] += 1
        pc = r.get("primary_cluster")
        if s == "ctx_cluster" and pc and v in ("Llaima", "Lastarria") and not r["sensor"].upper().startswith("MODIS") and not r["sensor"].endswith("_750"):
            G[v].append((pc.get("n_pixels"), pc.get("vrp_mw"), r["datetime_utc"][:7]))
assert tmax, "sin records MODIS"
tmax.sort(reverse=True)
print("(a) MODIS n=", len(tmax), "t_max_k maximo:", tmax[0], "| margen a 450 K:", round(450 - tmax[0][0], 1))
print("reparto final_hotspot_source:", src.most_common(8))
for v, L in G.items():
    assert L
    n = [a for a, _, _ in L if a is not None]; w = [b for _, b, _ in L if b is not None]
    print(f"(b) {v}: VIIRS375 ctx_cluster n={len(L)} | n_pixels mediana={st.median(n)} | un solo pixel={100*sum(1 for a in n if a==1)/len(n):.1f} % | vrp mediana={st.median(w):.3f} MW | p90 vrp={sorted(w)[int(.9*len(w))]:.3f}")
    m = [x for x in L if x[2] in ("2026-05","2026-06")]
    if m:
        n2=[a for a,_,_ in m]; w2=[b for _,b,_ in m]
        print(f"     ventana may-jun 2026 (la que S117 pudo ver): n={len(m)} mediana n_pix={st.median(n2)} un pixel={100*sum(1 for a in n2 if a==1)/len(n2):.1f} % vrp mediana={st.median(w2):.3f}")
