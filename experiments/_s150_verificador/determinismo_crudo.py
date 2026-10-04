# S150 verificador. Determinismo del gemelo contra B a nivel de RECORD CRUDO (no de decision de publicar):
# cuantos records coinciden campo por campo, ignorando marcas de tiempo de proceso. Si B y el gemelo fueran
# el mismo archivo copiado, todo coincidiria incluso esas marcas; se informa aparte.
# Uso: python determinismo_crudo.py B.json GEMELO.json [B.json GEMELO.json ...]
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
args = sys.argv[1:]
for b, g in zip(args[::2], args[1::2]):
    B = {(r.get("sensor"), r.get("datetime_utc")): r for r in json.load(open(b, encoding="utf-8"))["records"]}
    G = {(r.get("sensor"), r.get("datetime_utc")): r for r in json.load(open(g, encoding="utf-8"))["records"]}
    com = set(B) & set(G); dif = collections.Counter(); iguales = 0; tiempos = collections.Counter()
    for k in com:
        kb = set(B[k]) | set(G[k]); d = [f for f in kb if B[k].get(f) != G[k].get(f)]
        proc = [f for f in d if any(s in f.lower() for s in ("processed", "proceso", "created", "updated", "run_", "timestamp", "ingest"))]
        for f in proc: tiempos[f] += 1
        d = [f for f in d if f not in proc]
        if not d: iguales += 1
        for f in d: dif[f] += 1
    print("%s\n   B %d rec | gemelo %d | comunes %d | identicos salvo marcas de proceso %d | campos que difieren %s | marcas de proceso distintas %s"
          % (g.split("salidas")[-1] if "salidas" in g else g[-80:], len(B), len(G), len(com), iguales, dict(dif.most_common(8)), dict(tiempos)))
