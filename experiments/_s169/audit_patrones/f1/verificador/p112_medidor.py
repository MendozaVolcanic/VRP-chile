# -*- coding: utf-8 -*-
"""VF P1-12: ¿alguna salida del medidor de mutaciones de V750-A en el arbol (commit 01ffd277b) cubre TODAS las
mutaciones del script contra la bateria ENTERA de hoy? Cuenta ids M<n> definidos en mutar_evaluar_v750a.py y escenarios
E<n> en probar_evaluar_v750a.py; por cada salida, que ids M aparecen y con que estado, y cuantos escenarios dice la
cabecera. Pregunta 1: si una salida cubriera todo, saldria con M = todas y bateria = todos. Pregunta 2: control: el
contador de ids tiene que encontrar ids en el script (si diera 0, la regex estaria muerta)."""
import sys, re, pathlib, collections
sys.stdout.reconfigure(encoding="utf-8")
A = pathlib.Path(sys.argv[1])
mut = (A / "mutar_evaluar_v750a.py").read_text(encoding="utf-8")
prob = (A / "probar_evaluar_v750a.py").read_text(encoding="utf-8")
ids_m = sorted({int(x) for x in re.findall(r'["\'(]M(\d+)\b', mut)})
ids_e = sorted({int(x) for x in re.findall(r'\bE(\d+)\b', prob)})
print(f"mutar_evaluar_v750a.py: ids M distintos {len(ids_m)} (min M{min(ids_m)}, max M{max(ids_m)}); huecos {sorted(set(range(1, max(ids_m)+1)) - set(ids_m))}")
print(f"probar_evaluar_v750a.py: ids E distintos {len(ids_e)} (max E{max(ids_e)})")
for f in sorted(A.glob("mutar_evaluar_v750a*salida*.txt")):
    t = f.read_text(encoding="utf-8", errors="replace")
    vistos = collections.Counter()
    estados = {}
    for l in t.splitlines():
        m = re.match(r"\s*(M\d+)\b.*?(atrapada por aserción|NO ATRAPADA|caída|cae|sin efecto)", l)
        if m:
            estados[m.group(1)] = m.group(2)
    cab = [l for l in t.splitlines() if re.search(r"escenario|batería|bateria|identidad|control", l, re.I)][:6]
    print(f"\n== {f.name}: {len(t.splitlines())} lineas; mutaciones con estado {len(estados)}; "
          f"rango {min(estados, key=lambda s:int(s[1:])) if estados else '-'} a {max(estados, key=lambda s:int(s[1:])) if estados else '-'}; "
          f"estados {dict(collections.Counter(estados.values()))}")
    for c in cab: print("   ", c[:220])

print("\n== segunda lectura, formato 'M<n> | ESTADO (tiene que ser X) | ... (N)'")
for f in sorted(A.glob("mutar_evaluar_v750a*salida*.txt")):
    t = f.read_text(encoding="utf-8", errors="replace")
    est = {}
    for l in t.splitlines():
        m = re.match(r"\s*(M\d+)\s*\|\s*([A-ZÁÉÍÓÚ ]+?)\s*\(tiene que ser ([A-ZÁÉÍÓÚ ]+)\)", l)
        if m: est[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    bat = sorted({int(x) for x in re.findall(r"ESCENARIOS COMO SE ESPERA \((\d+)\)|FALLAS \d+ de (\d+)", t) for x in x if x})
    ids = sorted(int(k[1:]) for k in est)
    mal = {k: v for k, v in est.items() if v[0] != v[1]}
    print(f"   {f.name}: mutaciones {len(est)}" + (f" (M{ids[0]} a M{ids[-1]})" if ids else "") +
          f"; tamanos de bateria vistos {bat}; fuera de lo esperado {mal}")
