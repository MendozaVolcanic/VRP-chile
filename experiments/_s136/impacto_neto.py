"""S136 - impacto NETO de la etiqueta `far`, contado en NOCHES y no en records (A93).

Un record oculto no es una alerta perdida: si OTRA pasada de la misma noche se publica como
summit, el operador ve el volcan encendido igual. Lo que se pierde de verdad son las noches
ENTERAMENTE ocultas: MIROVA publico, nosotros tenemos un cumulo crateriano, y NINGUN record de
esa noche llega al dashboard.

S113 midio 84 noches asi, 73 de ellas de NdC (artefacto A69, que NO hay que destapar). Esto lo
remide con la data de hoy, que casi triplico el corpus desde entonces (A90: el corpus crece
hacia atras por backfill, asi que el numero de S113 no es comparable sin reconstruir su ventana).
READ-ONLY.
"""
import os, sys, json
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
al = load_mirova_alertas(cons_path=os.path.join(SNAP,"registro_vrp_consolidado.csv"),
                         ocr_path=os.path.join(SNAP,"registro_vrp_ocr.csv"))
mir = defaultdict(set); fin = ""
for a in al:
    f = a.get("fecha_utc")
    if f: mir[a["volcano"]].add(f[:10]); fin = max(fin, f[:10])

print(f"Ventana: toda la serie en disco; ground truth hasta {fin}\n")
print(f"{'volcan':20s} {'noches MIR':>10s} {'publica':>8s} {'OCULTA':>7s} {'sin nada':>9s}  recall hoy -> si se promoviera")
print("-"*100)
T = [0,0,0,0]
for vol in TIER_A:
    p = os.path.join(ROOT,"data","mirova_equivalent",f"{vol}.json")
    if not os.path.exists(p): continue
    d = json.load(open(p,encoding="utf-8")); recs = d.get("records", d)
    inn = inner.get(vol,5.0)
    pub, ocu = defaultdict(bool), defaultdict(bool)
    for r in recs:
        f = (r.get("datetime_utc") or "")[:10]
        if not f or f > fin: continue
        pc = r.get("primary_cluster") or {}
        cd, vrp = pc.get("centroid_dist_km"), pc.get("vrp_mw") or 0
        if vrp <= 0 or cd is None: continue
        if r.get("distance_class") == "summit" and cd <= inn:
            pub[f] = True
        elif r.get("distance_class") == "far" and cd <= inn:
            ocu[f] = True
    noches = sorted(n for n in mir[vol] if n <= fin)
    n_pub = sum(1 for n in noches if pub[n])
    n_ocu = sum(1 for n in noches if (not pub[n]) and ocu[n])     # ENTERAMENTE oculta
    n_nada = len(noches) - n_pub - n_ocu
    r0 = 100*n_pub/len(noches) if noches else 0
    r1 = 100*(n_pub+n_ocu)/len(noches) if noches else 0
    T[0]+=len(noches); T[1]+=n_pub; T[2]+=n_ocu; T[3]+=n_nada
    print(f"{vol:20s} {len(noches):10d} {n_pub:8d} {n_ocu:7d} {n_nada:9d}  "
          f"{r0:5.1f}% -> {r1:5.1f}%   (+{r1-r0:.1f} pp)")
print("-"*100)
print(f"{'TOTAL':20s} {T[0]:10d} {T[1]:8d} {T[2]:7d} {T[3]:9d}  "
      f"{100*T[1]/T[0]:5.1f}% -> {100*(T[1]+T[2])/T[0]:5.1f}%   (+{100*T[2]/T[0]:.1f} pp)")
print("\n'OCULTA' = MIROVA publico, tenemos cumulo crateriano, y NINGUN record de la noche llega")
print("al dashboard. Es el impacto neto real de la etiqueta. 'sin nada' = no tenemos nada esa")
print("noche (ni oculto): no lo arregla la etiqueta.")
