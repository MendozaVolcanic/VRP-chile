"""F3 (S160): cuántas veces la copia horaria de la referencia (latest_consolidado.csv) ENCOGIÓ y el
sync la aceptó igual.

Por qué: sync-mirova-csv.yml compara el archivo nuevo con `cmp` y lo reemplaza entero; el canal OCR
exige que el archivo no se encoja (l. 110 a 112 del yml) y el consolidado NO tiene esa defensa.
Un CSV que pierde filas se propaga a data/mirova/<Vol>.json y al tablero sin aviso.

Pregunta 1: si el sync aceptara copias encogidas, aquí aparecerían commits con menos líneas que el
anterior. Pregunta 2: si el instrumento estuviera muerto (git show fallando), n sería None y se
imprime como tal, no como 0. Control positivo: la historia del repo trae encogimientos ya medidos por
S159 (0c8848ff9 el 2026-10-18 con 630 bajas netas), así que al menos ese tiene que aparecer.

Uso: python -I medir_encogimientos_consolidado.py <repo> <lista_commits.txt> > salida.txt
Lee sólo con `git show` (no checkout, no pull). Ventana: la de los commits listados.
"""
import subprocess
import sys

repo, lista = sys.argv[1], sys.argv[2]
commits = []
with open(lista, encoding="utf-8") as fh:
    for line in fh:
        sha, fecha = line.split()
        commits.append((sha, fecha))
commits.reverse()  # más viejo primero

filas = []
for sha, fecha in commits:
    r = subprocess.run(["git", "-C", repo, "show", f"{sha}:latest_consolidado.csv"],
                       capture_output=True)
    n = None if r.returncode else r.stdout.count(b"\n")
    filas.append((sha, fecha, n))

prev = None
enc = []
print(f"commits que tocan latest_consolidado.csv: {len(filas)}; ventana {filas[0][1]} a {filas[-1][1]}")
for sha, fecha, n in filas:
    if n is None:
        print(f"SIN DATO {sha} {fecha}: git show falló")
        continue
    if prev is not None and n < prev[2]:
        enc.append((sha, fecha, prev[2], n, prev[2] - n))
    prev = (sha, fecha, n)
print(f"encogimientos aceptados por el sync: {len(enc)}")
for sha, fecha, antes, despues, d in enc:
    print(f"  {sha} {fecha}: {antes} -> {despues} lineas (-{d})")
print(f"primera copia: {filas[0][2]} lineas; ultima: {filas[-1][2]} lineas")
