"""Muestra encabezados y lineas candidatas (con contexto) de un informe. Uso: python ver.py archivo [ctx]"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
PAT = re.compile(r"(recomend|recommend|acci[oó]n|pendiente|pr[oó]xim|siguiente paso|abiert|propuest|propong|"
  r"sugier|sugerenc|backlog|follow|a futuro|por hacer|deber[ií]a|hay que|habr[ií]a que|conviene|falta|queda|"
  r"seguimiento|correcci|decisi|arreglo|fix|tarea|plan\b|medir|S\d{2,3}\+|SIN VERIFICAR|no aplicad|redactad|espera)", re.I)
f = sys.argv[1]; ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 1
L = open(f, encoding='utf-8', errors='replace').read().splitlines()
keep = set()
for i, l in enumerate(L):
    if l.startswith('#'): keep.add(i)
    elif PAT.search(l):
        for j in range(max(0, i-ctx), min(len(L), i+ctx+1)): keep.add(j)
prev = -2
print(f"### {f} ({len(L)} lineas, mostradas {len(keep)})")
for i in sorted(keep):
    if i != prev + 1: print("  ...")
    print(f"{i+1}: {L[i][:260]}")
    prev = i
