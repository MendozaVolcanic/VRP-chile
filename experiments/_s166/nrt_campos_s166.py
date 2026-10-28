"""S166: records nuevos o reescritos entre dos commits de main, y sus campos.

Pregunta: ¿los records que escribió el NRT con #920-#922 en el código traen los mismos campos que los
escritos antes, por sensor, y ninguno trae via_codigo_mirova? Uso: python nrt_campos_s166.py <antes> <despues>
Se corre desde la raíz del repo (lee con git show, no toca el árbol).
"""
import json
import subprocess
import sys
from collections import Counter, defaultdict

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima",
        "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def cargar(rev, vol):
    out = subprocess.run(["git", "show", f"{rev}:data/mirova_equivalent/{vol}.json"], capture_output=True)
    return json.loads(out.stdout)["records"] if out.returncode == 0 else []


def clave(r):
    return (r.get("sensor"), r.get("datetime_utc"), r.get("granule"))


def campos(r):
    ks = set(r)
    pc = r.get("primary_cluster")
    if isinstance(pc, dict):
        ks |= {"primary_cluster." + k for k in pc}
    return frozenset(ks)


antes, despues = sys.argv[1], sys.argv[2]
tot_nuevos = tot_reesc = 0
via = 0
difs = defaultdict(Counter)
for vol in VOLS:
    a = {clave(r): r for r in cargar(antes, vol)}
    d = cargar(despues, vol)
    # campos de referencia: los records de antes, por sensor (unión e intersección)
    ref = defaultdict(list)
    for r in a.values():
        ref[r.get("sensor")].append(campos(r))
    for r in d:
        k = clave(r)
        if k in a and a[k] == r:
            continue
        nuevo = k not in a
        tot_nuevos += nuevo
        tot_reesc += not nuevo
        s = json.dumps(r)
        if "via_codigo_mirova" in s or "codigo_mirova" in s:
            via += 1
        c = campos(r)
        refs = ref.get(r.get("sensor")) or []
        union = frozenset().union(*refs) if refs else frozenset()
        inter = frozenset.intersection(*refs) if refs else frozenset()
        sobra, falta = c - union, inter - c
        etiqueta = f"{vol} {r.get('sensor')} {r.get('datetime_utc')} {'nuevo' if nuevo else 'reescrito'}"
        print(f"{etiqueta}: campos {len(c)}; fuera de la unión previa {sorted(sobra) or 'ninguno'}; "
              f"faltan de la intersección previa {sorted(falta) or 'ninguno'}")
        if sobra or falta:
            difs[vol][etiqueta] += 1
print(f"== records nuevos {tot_nuevos}, reescritos {tot_reesc}; con 'codigo_mirova' en el texto: {via}; "
      f"con campos distintos a los previos del mismo sensor: {sum(len(v) for v in difs.values())}")
