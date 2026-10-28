# VE2: que protegidas conoce la lista (JSON de objetivos, SIN artefactos de lectura) y cuales son las que el informe del
# verificador de V375-C dice que pierden los 10 brazos. P1: si el veto de la RP quedara determinado por perdidas ajenas a la
# posicion, esta lista lo muestra (control positivo: las 4 protegidas de la adenda §8.1 tienen que aparecer con pub_prod=1).
import json, sys, collections
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
V = R/"experiments/_s162_v375"
sys.path.insert(0, str(V/"e_adenda2")); sys.path.insert(0, str(V)); sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"scripts"))
import leer_posicion_v375e as L
obj = L.objetivos(V/"e_adenda2/objetivos_run_far_v375.json")
prot = [o for o in obj.values() if o.get("clase") == "pos_prot"]
print("pos_prot:", len(prot), "K publica:", sum(bool(o["pub_prod"]) for o in prot), "de tabla:", sum(bool(o.get("alerta_tabla")) for o in prot))
buscadas = [("Tupungatito","2026-08-01 05:00"),("Isluga","2026-09-09 06:06"),("Tupungatito","2026-09-14 06:18"),
            ("Isluga","2026-06-17 05:06"),("Isluga","2026-09-28 05:12"),("Isluga","2026-10-03 05:18"),("Lascar","2026-10-01 05:18"),
            ("Lascar","2026-08-22 05:06"),("Tupungatito","2026-09-28 05:18"),("Tupungatito","2026-09-29 04:54")]
for v,h in buscadas:
    m = [o for o in prot if o["volcan"]==v and o["hora_utc"][:16]==h]
    print(v,h, [(o["lote"], "K" if o["pub_prod"] else "noK", "tabla" if o.get("alerta_tabla") else "solo_OCR", o["sensor"], o.get("mirova_vrp")) for o in m] or "NO ESTA en pos_prot")
print("protegidas sin alerta de la tabla (solo OCR):", sum(1 for o in prot if not o.get("alerta_tabla")), "y K publica", sum(1 for o in prot if not o.get("alerta_tabla") and o["pub_prod"]))
print("por tramo (protegidas):", collections.Counter(o["tramo"] if "tramo" in o else L.E.tramo(o["hora_utc"]) if hasattr(L,'E') else '?' for o in prot))
