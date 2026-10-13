"""Convierte filas de un lote_L*.csv (subagente) a formato tanda, marcando el origen.
Uso: python importar_lote.py lote_L4.csv tanda_07.txt [excluir_substr ...]"""
import csv, sys
src, dst, excl = sys.argv[1], sys.argv[2], sys.argv[3:]
n = 0
with open(dst, "w", encoding="utf-8") as out:
    out.write(f"# importado de {src} (subagente); muestreo propio en progreso.txt\n")
    for r in csv.DictReader(open(src, encoding="utf-8")):
        if any(e in r["fuente"] for e in excl): continue
        f = lambda k: (r.get(k) or "-").replace(" | ", " / ").replace("\n", " ").strip() or "-"
        out.write(" | ".join([f("fuente"), f("auditoria"), f("tema"), f("recomendacion"), f("tipo"), f("objetivo"),
                              f("estado"), "[" + src.split('.')[0].replace('lote_','') + "] " + f("evidencia"), f("premisa_caida")]) + "\n")
        n += 1
print(n, "filas ->", dst)
