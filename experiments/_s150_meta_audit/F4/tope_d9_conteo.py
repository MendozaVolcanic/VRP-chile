"""F4 (meta-auditoria S150): el tope D9 de 5 MW, contado sobre el corpus de hoy.

Afirmacion bajo prueba: CLAUDE.md A23 (l. 357 y 363) dice que el tope "ya esta adoptado y funciona"
y "0 records sobre 5 MW"; MISSION.md l. 105 y CLAUDE.md l. 1785 dicen que el tope "se confirma".
AUDIT_S150 §2 y AUDITOR_C C-01 dicen que recorto magnitudes reales de la erupcion de NdC.

Preguntas del instrumento:
1. Si el tope recortara magnitudes, se veria: cuento records con primary_cluster.d9_capped y
   pc.vrp_mw == 5.0 exacto. NO mide cuanto se recorto (el record no guarda el valor previo,
   AUDITOR_C C-01): un conteo no distingue un recorte de erupcion de uno de cirrus.
2. Si el instrumento estuviera muerto (clave mal escrita) daria 0 en todo; el control positivo es
   que d9_capped > 0 en el corpus (si sale 0 en todos, el instrumento no ve la clave).
Ventana: todo el corpus data/mirova_equivalent/*.json; desglose desde 2026-09-28 (erupcion NdC).
"""
import glob, io, json, os, sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent/"
tot = Counter()
for f in sorted(glob.glob(BASE + "*.json")):
    v = os.path.basename(f)[:-5]
    try:
        recs = json.load(open(f, encoding="utf-8"))["records"]
    except Exception as e:
        print("no se pudo leer", v, e); continue
    for r in recs:
        pc = r.get("primary_cluster") or {}
        tot["records"] += 1
        if pc.get("d9_capped"):
            tot["capped"] += 1
            if pc.get("vrp_mw") == 5.0:
                tot["capped_5.0"] += 1
                key = (v, r.get("sensor", "")[:5], r.get("distance_class"))
                tot[("c",) + key] += 1
                if r.get("datetime_utc", "") >= "2026-09-28":
                    tot[("erup",) + key] += 1
            if (pc.get("vrp_mw") or 0) > 5.0:
                tot["capped_mayor_5"] += 1
print("records", tot["records"], "| d9_capped", tot["capped"], "| capped con 5.0 exacto", tot["capped_5.0"],
      "| capped con >5", tot["capped_mayor_5"])
print("\npor volcan/sensor/clase (todo el corpus):")
for k, n in sorted(((k, n) for k, n in tot.items() if isinstance(k, tuple) and k[0] == "c"), key=lambda x: -x[1])[:15]:
    print(" ", k[1:], n)
print("\ndesde 2026-09-28:")
for k, n in sorted(((k, n) for k, n in tot.items() if isinstance(k, tuple) and k[0] == "erup"), key=lambda x: -x[1]):
    print(" ", k[1:], n)
