"""S157 issue #865: compara campo por campo el record de produccion (K) y el de la sombra (C0)
de Puyehue-Cordon Caulle, VIIRS 750 NOAA-21, 2026-10-10 05:54 UTC. Solo lectura."""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = sys.argv[1] if len(sys.argv) > 1 else "."
VOL, SENSOR, DT = "PuyehueCordonCaulle", sys.argv[2] if len(sys.argv) > 2 else "VIIRS_NOAA21_750", "2026-10-10 05:54"

def buscar(sub):
    d = json.load(open(f"{RAIZ}/data/{sub}/{VOL}.json", encoding="utf-8"))
    hits = [r for r in d["records"] if r.get("sensor") == SENSOR and r.get("datetime_utc") == DT]
    assert len(hits) == 1, (sub, len(hits))
    return hits[0]

k, c0 = buscar("mirova_equivalent"), buscar("experimental_v2")
claves = sorted(set(k) | set(c0))
print(f"{'campo':40s} {'K (produccion)':>28s} {'C0 (sombra)':>28s}")
for c in claves:
    if c in ("anomaly_pixels",):
        continue
    a, b = k.get(c, "<falta>"), c0.get(c, "<falta>")
    if c == "primary_cluster":
        a = {x: y for x, y in (a or {}).items() if not isinstance(y, list)} if isinstance(a, dict) else a
        b = {x: y for x, y in (b or {}).items() if not isinstance(y, list)} if isinstance(b, dict) else b
    marca = "" if a == b else "  <==="
    print(f"{c:40s} {str(a)[:60]:>28s} {str(b)[:60]:>28s}{marca}")
print("\nanomaly_pixels K:", len(k.get("anomaly_pixels") or []), " C0:", len(c0.get("anomaly_pixels") or []))
for p in (c0.get("anomaly_pixels") or [])[:40]:
    print("  C0 px", p)
for p in (k.get("anomaly_pixels") or [])[:40]:
    print("  K  px", p)
