"""En records nocturnos de la vía (data/mirova_equivalent, desde 2026-03-01, 10 volcanes de la zona A): ¿cuántas
veces manda el término mu + s·sd sobre el piso en la región sensible, para s = 5 y s = 1? Si el piso (0,003) manda
casi siempre ya con s = 5, bajar s no cambia nada. Lee mu y sd del diagnóstico s1 de cada pase. Sólo lectura."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(sys.argv[1])
ZONA = ["Lascar", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "Chaiten", "Lastarria"]
PISO = 0.003
cuenta = {}
for v in ZONA:
    d = json.loads((RAIZ / "data" / "mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    for r in recs:
        if str(r.get("datetime_utc", "")) < "2026-03-01" or not r.get("via_codigo_mirova"):
            continue
        dg = r.get("diag_codigo_mirova") or {}
        if dg.get("dayflag") != 0:
            continue
        p = (dg.get("s1") or {}).get("pasada1")
        if not p or p.get("sd_nti") is None or p.get("mu_nti") is None:
            continue
        fam = r.get("sensor", "?").split("_")[0] + ("_750" if r.get("sensor", "").endswith("750") else "")
        c = cuenta.setdefault(fam, {"n": 0, "nti_s5": 0, "nti_s1": 0, "eti_s5": 0, "eti_s1": 0, "ambos_s5": 0,
                                    "ambos_s1": 0})
        c["n"] += 1
        mn, sn = p["mu_nti"], p["sd_nti"]
        me, se = p.get("mu_eti"), p.get("sd_eti")
        n5, n1 = mn + 5 * sn > PISO, mn + 1 * sn > PISO
        e5 = me is not None and se is not None and me + 5 * se > PISO
        e1 = me is not None and se is not None and me + 1 * se > PISO
        c["nti_s5"] += n5; c["nti_s1"] += n1; c["eti_s5"] += e5; c["eti_s1"] += e1
        c["ambos_s5"] += (n5 or e5); c["ambos_s1"] += (n1 or e1)
print("familia: n pases1 nocturnos; cuántos con mu+s*sd > piso en NTI, en ETI, y en alguno, para s=5 y s=1")
for f, c in sorted(cuenta.items()):
    print(f, c)
