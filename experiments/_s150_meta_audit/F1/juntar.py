"""Junta tanda_*.txt (campos separados por ' | ') en censo.csv. Columnas fijas."""
import glob, csv, io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
COLS = ["fuente","auditoria","tema","recomendacion","tipo","objetivo","estado","evidencia","premisa_caida"]
rows = []
for t in sorted(glob.glob("tanda_*.txt")):
    for n, l in enumerate(open(t, encoding='utf-8'), 1):
        l = l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        p = [x.strip() for x in l.split(" | ")]
        if len(p) != len(COLS): print("MAL FORMADA", t, n, len(p), l[:80]); continue
        rows.append(dict(zip(COLS, p), tanda=t))
with open("censo.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS + ["tanda"]); w.writeheader(); w.writerows(rows)
c = collections.Counter(r["estado"] for r in rows)
print("filas", len(rows), dict(c))
