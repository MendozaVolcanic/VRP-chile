# VE2: A104/A119 sobre la lista (solo JSON de objetivos). Tasa con que K publica (pub_prod) por tramo y clase, y cuantas
# alertas del marco son solo-OCR por tramo. P1: ve si pooling T+O1+O2 mezcla regimenes; control: n por celda.
import sys, collections, json
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
V = R/"experiments/_s162_v375"
sys.path.insert(0, str(V/"e_adenda2")); sys.path.insert(0, str(V)); sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"scripts"))
import leer_posicion_v375e as L
import evaluar as E
obj = L.objetivos(V/"e_adenda2/objetivos_run_far_v375.json")
def tr(o): return E.tramo(o["hora_utc"])
t = collections.defaultdict(lambda: [0, 0])
for o in obj.values():
    if o.get("lote") in ("CTLF",): continue
    k = (o["clase"], tr(o)); t[k][0] += 1; t[k][1] += bool(o.get("pub_prod"))
print("clase, tramo -> n, K publica (pub_prod)")
for k in sorted(t): print("  ", k, t[k], f"{t[k][1]/t[k][0]:.2f}")
print("alertas (pos_prot, pos_bajo) por tramo y fuente:")
c = collections.Counter()
for o in obj.values():
    if o.get("clase") in ("pos_prot", "pos_bajo"): c[(o["clase"], tr(o), "tabla" if o.get("alerta_tabla") else "solo_OCR")] += 1
for k in sorted(c): print("  ", k, c[k])
print("far_tabla por tramo (n):", {k: v for k, v in collections.Counter(tr(o) for o in obj.values() if o.get("clase")=="far_tabla").items()})
# sensor de las far_tabla por tramo
print("far_tabla por sensor:", collections.Counter(o["sensor"] for o in obj.values() if o.get("clase")=="far_tabla"))
