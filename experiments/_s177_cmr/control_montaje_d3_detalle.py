"""S177: coberturas finales de D3 y detalle de pasadas que solo una rama tiene. Sin VRP ni detecciones (candado 11)."""
import collections, json, pathlib, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path("C:/Users/nmend/vrp-temporales")
tot = collections.Counter(); via0 = collections.Counter(); inc = collections.Counter()
for d in sorted((R/"s177_d3").glob("log-*")):
    for c in (d/"cobertura").glob("*.json"):
        j = json.loads(c.read_text(encoding="utf-8"))
        tot["archivos"] += 1; tot["fallas"] += len(j["fallas"]) if hasattr(j["fallas"], "__len__") else j["fallas"]
        tot["sin_granulos"] += len(j["sin_granulos"]) if hasattr(j["sin_granulos"], "__len__") else j["sin_granulos"]
        tot["n_incidencias"] += j["n_incidencias"]; tot["retiradas"] += len(j["retiradas"]) if hasattr(j["retiradas"], "__len__") else j["retiradas"]
        if j["fallas"]: print("FALLA", c, str(j["fallas"])[:300])
    t = (d/"controles_via.txt").read_text(encoding="utf-8")
    for m in re.finditer(r"(\w+): (\d+)/(\d+) de la via \(([\d.]+)%\)", t):
        via0["todo_cero" if m[2] == "0" else "con_via"] += 1
print(dict(tot), dict(via0))
def pas(raiz):
    o = collections.defaultdict(set)
    for d in sorted((R/raiz).glob("trozo-*")):
        js = list(d.glob("*.json"))
        for r in json.loads(js[0].read_text(encoding="utf-8"))["records"]:
            o[js[0].stem].add((r["datetime_utc"], r["sensor"]))
    return o
d3, d2 = pas("s177_d3"), pas("s177_d2")
pares = collections.Counter(); ej = []
for v in sorted(d3):
    dias = {x[0][:10] for x in d3[v]}
    sub = {x for x in d2.get(v, set()) if x[0][:10] in dias}
    for t, s in sorted(sub-d3[v]):
        # misma pasada en K con otra hora a menos de 5 min?
        cerca = [x for x in d3[v] if x[1] == s and x[0][:13] == t[:13]]
        pares["solo_via_con_pasada_K_misma_hora_sensor" if cerca else "solo_via_sin_K_en_esa_hora"] += 1
        ej.append((v, t, s, [c[0] for c in cerca][:2]))
print(dict(pares))
for e in ej[:32]: print(e)
