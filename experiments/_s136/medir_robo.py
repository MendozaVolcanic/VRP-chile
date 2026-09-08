"""S136 - la cara OCULTA de A46: separa geometricamente el robo legitimo del artefacto?

PREGUNTA. S113 dejo un "fix candidato": promover a summit los cumulos crateriana genuinos que hoy
quedan etiquetados `far` porque un objeto lejano le robo el final_hotspot. Lo dejo pendiente porque
requiere distinguir el caso LEGITIMO (Lascar: el Salar de Atacama a 18-24 km roba el hotspot y
esconde un cumulo crateriano real que MIROVA confirma) del ARTEFACTO (NdC: gradiente topografico
A69 sub-pixel). Y A83 declara agotado el discriminante FISICO per-record.

Esta medicion prueba una via que A83 NO cubrio: la GEOMETRICA. Si en los casos legitimos el
final_hotspot esta lejisimos (fuera de plausibilidad volcanica) y en los artefactos esta cerca,
entonces la distancia del hotspot robado separa, sin necesidad de un discriminante fisico.

READ-ONLY. Reporta con denominador y ventana (A90).
"""
import os, sys, json, statistics as st
from collections import defaultdict
ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import yaml
from pipeline.mirova_csv_loader import load_mirova_alertas

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
vc = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
inner = {v["name"]: float(v.get("inner_radius_km") or 5.0) for v in vc["volcanoes"]}
TIER_A = ["Villarrica","Lascar","Isluga","NevadosDeChillan","Llaima","Chaiten","Copahue",
          "Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]

al = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                         ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
mir = defaultdict(set)
for a in al:
    f = a.get("fecha_utc")
    if f: mir[a["volcano"]].add(f[:10])

print("Records OCULTOS por la etiqueta: distance_class='far' pero el cumulo primario esta")
print("DENTRO del inner_radius con VRP>0. El dashboard filtra por summit -> no se publican.\n")
print(f"{'volcan':20s} {'ocultos':>8s} {'conf.MIR':>9s} {'dist hotspot robado (km)':>26s} {'dist cumulo':>12s}")
print(f"{'':20s} {'':>8s} {'':>9s} {'p25   mediana   p75':>26s} {'mediana':>12s}")
print("-"*82)
tot = defaultdict(list)
for vol in TIER_A:
    p = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding="utf-8")); recs = d.get("records", d)
    inn = inner.get(vol, 5.0)
    oc = []
    for r in recs:
        pc = r.get("primary_cluster") or {}
        cd, vrp = pc.get("centroid_dist_km"), pc.get("vrp_mw") or 0
        if r.get("distance_class") != "far" or cd is None or vrp <= 0 or cd > inn:
            continue
        fh = r.get("final_hotspot_dist_km")
        if fh is None: continue
        conf = (r.get("datetime_utc","")[:10] in mir[vol])
        oc.append((fh, cd, conf, r.get("sensor",""), r.get("datetime_utc","")[:10]))
    if not oc: continue
    fhs = sorted(x[0] for x in oc)
    q = lambda p: fhs[min(len(fhs)-1, int(p*len(fhs)))]
    nconf = sum(1 for x in oc if x[2])
    print(f"{vol:20s} {len(oc):8d} {100*nconf/len(oc):8.0f}% "
          f"{q(.25):8.1f} {st.median(fhs):8.1f} {q(.75):8.1f} "
          f"{st.median([x[1] for x in oc]):11.2f}")
    tot[vol] = oc

print("\n" + "="*82)
print("SEPARACION GEOMETRICA: el hotspot robado esta LEJOS (robo claro) o CERCA (ambiguo)?")
print("="*82)
for corte in (10.0, 15.0, 18.0):
    print(f"\n  con corte 'hotspot robado a mas de {corte:.0f} km' => robo claro:")
    for vol in sorted(tot, key=lambda v: -len(tot[v]))[:11]:
        oc = tot[vol]
        claro = [x for x in oc if x[0] > corte]
        cc = sum(1 for x in claro if x[2])
        print(f"    {vol:20s} {len(claro):5d} de {len(oc):5d} ({100*len(claro)/len(oc):3.0f}%)"
              f"  de esos, MIROVA confirma {100*cc/len(claro) if claro else 0:3.0f}%")
