# VE2: pesos de las clases del marco frente a far_tabla (peso 1). Lee SOLO JSON de objetivos (no artefactos).
# P1: si los pesos estuvieran mal armados, ¿lo veria? Reproduce el armado de analizar(): N/n_ok por (clase, estrato)
# usando la misma construccion de obj que leer_posicion_v375e.objetivos(). P2: el control es que sum(w) por clase = N.
import json, sys, collections
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
V = R/"experiments/_s162_v375"
sys.path.insert(0, str(V/"e_adenda2")); sys.path.insert(0, str(V)); sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"scripts"))
import leer_posicion_v375e as L
obj = L.objetivos(V/"e_adenda2/objetivos_run_far_v375.json")
meta = json.load(open(V/"objetivos_v375_bc.json", encoding="utf-8"))["meta"]["estratos"]
print("lotes:", collections.Counter(o["lote"] for o in obj.values()))
print("clase x lote:", sorted(collections.Counter((o.get("clase"), o["lote"]) for o in obj.values()).items(), key=str))
n_ok = collections.Counter((o["clase"], o["estrato"]) for o in obj.values() if o["lote"] not in ("CTL","CTLF","FAR") and o["clase"] in meta)
tot = collections.defaultdict(list)
for c, est in meta.items():
    for h, v in est.items():
        if n_ok.get((c,h)):
            tot[c].append(v["N"]/n_ok[(c,h)])
        else:
            print("  estrato sin muestra:", c, h, v)
for c, w in tot.items():
    print(c, "n_estratos", len(w), "w min/med/max", round(min(w),2), round(sorted(w)[len(w)//2],2), round(max(w),2))
print("far_tabla: n=", sum(1 for o in obj.values() if o.get('clase')=='far_tabla'), "peso 1")
