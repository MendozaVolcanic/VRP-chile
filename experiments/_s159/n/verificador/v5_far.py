# -*- coding: utf-8 -*-
"""Verificador S159 N, paso 5: puede F encender un negativo cuyo record de K es 'far'? (cota del estimador de v3).
Cuenta en la muestra las pasadas con K far y que dc/publicacion da F; y cuantas far hay en la poblacion.
P1: si F nunca cambiara distance_class, el conteo de cambios seria 0 y la cota de 60 elegibles valdria; si cambia,
la cota sube. Ventana: la de objetivos_n.json."""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; N = AQUI.parent
obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
V = json.load(open(AQUI / "v1_pub.json")); P = {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in V["P"].items()}
ok = set(V["ok"])
res = {}
for f in sorted((N / "run_39682867040").glob("*resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
dc = lambda i, b: (res[i]["brazos"][b]["record"] or {}).get("distance_class")
c = collections.Counter((obj[i]["clase"], dc(i, "K"), dc(i, "F"), P.get((i, "F"))) for i in ok if dc(i, "K") == "far")
print("pasadas con K far (clase, dc K, dc F, F publica):", dict(c))
print("cambios de distance_class K->F en todo el lote:", collections.Counter((dc(i, "K"), dc(i, "F")) for i in ok if dc(i, "K") != dc(i, "F")))
pob = [p for p in json.loads((N / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"] if p["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
print("negativos far no publicados en la poblacion:", sum(1 for p in pob if p["lab"] == "neg_limpio" and not p["pub_prod"] and p.get("dc") == "far"))
print("negativos sin cumulo: n_px distribucion:", collections.Counter(p.get("n_px") for p in pob if p["lab"] == "neg_limpio" and p.get("dc") is None))
