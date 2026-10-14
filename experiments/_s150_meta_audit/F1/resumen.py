import csv, collections, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
R = list(csv.DictReader(open("censo.csv", encoding="utf-8")))
print("filas", len(R))
orig = collections.Counter("propia" if not r["evidencia"].startswith("[L") else "lote" for r in R)
print("origen", dict(orig))
print("por estado", dict(collections.Counter(r["estado"] for r in R)))
def era(a):
    m = re.search(r"S(\d+)", a or ""); n = int(m.group(1)) if m else 0
    return "S86-S137" if n < 138 else ("S138-S145" if n < 146 else "S146-S150")
t = collections.defaultdict(collections.Counter)
for r in R: t[era(r["auditoria"])][r["estado"]] += 1
for k in sorted(t): print(k, dict(t[k]), sum(t[k].values()))
tipo = collections.defaultdict(collections.Counter)
for r in R:
    if r["estado"] in ("ABANDONADO", "VIGENTE"): tipo[r["tipo"]][r["estado"]] += 1
print("abiertas por tipo", {k: dict(v) for k, v in tipo.items()})
obj = collections.Counter((r["objetivo"], r["estado"]) for r in R if r["estado"] in ("ABANDONADO", "VIGENTE"))
print("abiertas por objetivo", dict(obj))
temas = collections.defaultdict(set)
for r in R: temas[r["tema"].lower()].add(r["estado"])
print("temas distintos", len(temas))
pc = sum(1 for r in R if r["premisa_caida"] not in ("-", "", "ninguna", "no"))
print("filas con premisa caida anotada", pc)
