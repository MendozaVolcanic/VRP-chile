"""§4.5 de la regla de adopción de K: K sobre el main de hoy contra K del tag de V1, mismos gránulos.

POR QUÉ: V1 y V2 corrieron sobre 402447f3 y 7b74435e; después entraron #785, #821, #822 y #844 (desempate del top-100
MODIS). La regla pide la misma decisión de publicar en cada pasada, salvo diferencias que #844 explique una por una.
Uso: python k_main_contra_tag.py <dir K main> <dir K de la union V1> desde hasta
"""
import collections, importlib.util, json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ui", RAIZ / "experiments" / "_s151_ab_diurno" / "unir_intentos.py")
ui = importlib.util.module_from_spec(spec); spec.loader.exec_module(ui)

main_dir, tag_dir, desde, hasta = sys.argv[1:5]
tot = collections.Counter()
for f in sorted(Path(main_dir).glob("*.json")):
    v = f.stem
    en = lambda r: desde <= (r.get("datetime_utc") or "")[:10] <= hasta
    M = {ui.clave(r): r for r in json.load(open(f, encoding="utf-8"))["records"] if en(r)}
    T = {ui.clave(r): r for r in json.load(open(Path(tag_dir) / f.name, encoding="utf-8"))["records"] if en(r)}
    comunes = sorted(set(M) & set(T))
    print("%s: main %d, tag %d, comunes %d, solo main %d, solo tag %d" % (v, len(M), len(T), len(comunes), len(set(M) - set(T)), len(set(T) - set(M))))
    estados = collections.Counter(); pares = []
    for k in comunes:
        est, det = ui.comparar(T[k], M[k]); estados[est] += 1
        if est != "igual": pares.append((k, est, det))
    malos = set(ui._predicado([(T[k], M[k]) for k, _, _ in pares], v)) if pares else set()
    for j, (k, est, det) in enumerate(pares):
        if est == "distinto" or j in malos:
            print("   %s %s publica distinto=%s campos=%s" % ("|".join(map(str, k)), est, j in malos, (det.get("campos") or det.get("campos_derivados"))))
    print("   estados", dict(estados), "| decisión de publicar distinta:", len(malos))
    tot.update(estados); tot["publica_distinto"] += len(malos)
print("TOTAL", dict(tot))
