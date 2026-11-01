# Cuenta veredictos de la matriz Coppola 2016a contra el .m de VIIRS 750 (matriz escrita a mano, ver INFORME.md).
import csv, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = list(csv.DictReader(open("matriz_c16_vs_codigo.csv", encoding="utf-8"), delimiter=";"))
c = collections.Counter(r["veredicto"] for r in rows)
print("filas:", len(rows), dict(c))
hab = [r for r in rows if r["veredicto"] != "CALLA"]
print("donde el paper habla:", len(hab), "IGUAL", sum(r["veredicto"]=="IGUAL" for r in hab), "DISTINTO", sum(r["veredicto"]=="DISTINTO" for r in hab))
print("DISTINTOS:"); [print("  paso", r["paso"], r["aspecto"]) for r in hab if r["veredicto"]=="DISTINTO"]
