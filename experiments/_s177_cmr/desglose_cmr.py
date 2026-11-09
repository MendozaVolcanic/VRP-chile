"""S177: desglose del corte de CMR del 2026-11-08 por producto, flujo y tiempo de respuesta.

POR QUE: contar fallas por hora no separa "NASA estuvo lenta para todos" de "nuestra carga la satura". El tiempo de
respuesta de las consultas EXITOSAS del NRT (que no falla) mide el estado de CMR sin depender de quien fallo.
Uso: python experiments/_s177_cmr/desglose_cmr.py C:/Users/nmend/vrp-temporales/s177_cmr
"""
import collections, io, json, re, statistics as st, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
out = sys.argv[1]
RE_OK = re.compile(r"\[(\w+)\] \S+ v\S+ (\S+)\.\.(\S+) n=(\d+) elapsed=([\d.]+)s")
RE_P = re.compile(r"\[(\w+)\]")
ok = collections.defaultdict(list); err = collections.Counter()
for l in open(f"{out}/eventos.jsonl", encoding="utf-8"):
    e = json.loads(l)
    if e["ev"] == "SEARCH_VENTANA":
        m = RE_OK.search(e["txt"])
        if m: ok[(e["ts"][:13], e["wf"][:14], m.group(1))].append(float(m.group(5)))
    elif e["ev"] in ("SEARCH_VENTANA_ERR", "SEARCH_CMR_TIMEOUT"):
        m = RE_P.search(e["txt"]); err[(e["ts"][:13], e["wf"][:14], m.group(1) if m else "?")] += 1
def resumen(filtro, titulo):
    print("\n##", titulo)
    agg = collections.defaultdict(lambda: [[], 0])
    for k, v in ok.items():
        g = filtro(k)
        if g: agg[g][0] += v
    for k, v in err.items():
        g = filtro(k)
        if g: agg[g][1] += v
    for g in sorted(agg):
        v, n = agg[g]
        q = sorted(v)
        print(g, "ok", len(v), "err", n, "med", round(st.median(q), 1) if q else None,
              "p95", round(q[int(.95 * (len(q) - 1))], 1) if q else None, "max", q[-1] if q else None)
def diar(k): return k[0][:10]
resumen(lambda k: (k[0][:10], k[1]) if k[0] >= "2026-11-05" else None, "por dia y flujo")
resumen(lambda k: (k[0], k[1]) if "2026-11-08T17" <= k[0] <= "2026-11-09T04" else None, "por hora y flujo, 11-08 tarde")
resumen(lambda k: (k[1], k[2]) if "2026-11-08T19" <= k[0] <= "2026-11-08T23" else None, "19 a 23 UTC por flujo y producto")
resumen(lambda k: ("NRT", k[0]) if k[1].startswith("nrt") and "2026-11-08T12" <= k[0] <= "2026-11-09T04" else None, "NRT por hora: tiempo de consultas exitosas")
