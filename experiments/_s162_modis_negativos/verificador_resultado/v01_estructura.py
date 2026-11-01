# -*- coding: utf-8 -*-
"""Verificador: estructura de los JSON del run, claves de un record, los dos publicados y dos no evaluables.
Pregunta 1: si el JSON estuviera vacio o roto, esto lo ve (cuenta e imprime). Pregunta 2: si el lector muriera, no
habria salida; imprime conteos explicitos."""
import json, sys, collections
from pathlib import Path
RUN = Path(sys.argv[1])
res = {}
dup = collections.Counter()
por_trozo = {}
for f in sorted(RUN.rglob("resultados_MODIS_*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    por_trozo[f.parent.name] = [(r["id"], r.get("estado")) for r in data]
    for r in data:
        dup[r["id"]] += 1
        res[r["id"]] = r
print("trozos:", {k: len(v) for k, v in por_trozo.items()})
print("ids totales:", sum(len(v) for v in por_trozo.values()), "unicos:", len(res), "duplicados:", [k for k, v in dup.items() if v > 1])
print("estados:", collections.Counter(r.get("estado") for r in res.values()))
print("claves top de un ok:", sorted(res[1000].keys()))
print("claves port:", sorted(res[1000]["port"].keys()))
print("claves port.fisica:", sorted((res[1000]["port"]["fisica"] or {}).keys()))
print("claves K:", sorted((res[1000].get("K") or {}).keys()))
print("claves nativo:", res[1000].get("nativo"))
print("port_estado valores:", collections.Counter(r.get("port_estado") for r in res.values()))
print("motivo_vacio fisica:", collections.Counter(((r.get("port") or {}).get("fisica") or {}).get("motivo_vacio") for r in res.values()))
print("commit/version en el record?:", {k: res[1000][k] for k in res[1000] if any(s in k.lower() for s in ("commit", "sha", "version", "git", "blob"))})
for i in (1120, 1251, 1001, 1205, 1260):
    r = res[i]
    print(f"\n--- id {i} estado={r.get('estado')} port_estado={r.get('port_estado')} nativo={r.get('nativo')}")
    print("  fisica:", json.dumps(r["port"].get("fisica") if r.get("port") else None, ensure_ascii=False)[:1500])
    print("  K keys:", sorted((r.get("K") or {}).keys()), " pc:", ((r.get("K") or {}).get("record") or {}).get("primary_cluster"))
    print("  otros:", {k: r[k] for k in r if k not in ("port", "K", "nativo")})
# no evaluables por trozo (para R3)
print("\nno-ok o escena_invalida por trozo:")
for t, lst in por_trozo.items():
    ne = [(i, e) for i, e in lst if e != "ok"]
    ei = [i for i, e in lst if e == "ok" and ((res[i].get("port") or {}).get("fisica") or {}).get("motivo_vacio") == "escena_invalida"]
    print(" ", t, "n", len(lst), "no_ok", ne, "escena_invalida", ei)
