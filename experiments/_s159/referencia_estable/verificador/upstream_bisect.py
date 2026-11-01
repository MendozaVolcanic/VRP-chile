# -*- coding: utf-8 -*-
"""Verificador S159: la perdida de filas de la tabla, ¿es del CSV de Mirova-v1 (upstream) o de nuestra copia?

Pregunta 1 (si lo medido estuviera roto, ¿lo veria?): si la fila sigue en upstream y solo nuestra copia
la perdio, el upstream la mostraria presente despues de nuestra baja. Pregunta 2 (instrumento muerto):
cada descarga reporta n de lineas y busca una fila control que si debe estar (la ultima pasada conocida
antes de la ventana); si la descarga fallara, n=0 y control=False, distinto de "fila ausente".
Uso: python -I upstream_bisect.py <since> <until> <patron1> [<patron2> ...]
"""
import json, subprocess, sys, urllib.request, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = "MendozaVolcanic/Mirova-v1"; P = "monitoreo_satelital/registro_vrp_consolidado.csv"
since, until, *pats = sys.argv[1:]
out = subprocess.run(["gh", "api", f"repos/{REPO}/commits?path={P}&since={since}&until={until}&per_page=100",
                      "--jq", ".[] | [.sha, .commit.committer.date] | @tsv"], capture_output=True, text=True).stdout
cs = [l.split("\t") for l in out.strip().splitlines()][::-1]
cache = {}
def get(sha):
    if sha not in cache:
        t = urllib.request.urlopen(f"https://raw.githubusercontent.com/{REPO}/{sha}/{P}", timeout=60).read().decode("utf-8", "replace")
        cache[sha] = t
    return cache[sha]
def estado(sha):
    t = get(sha); lines = t.splitlines()
    return len(lines), [any(all(x in l for x in p.split("&")) for l in lines) for p in pats]
lo, hi = 0, len(cs) - 1
s0, s1 = estado(cs[lo][0]), estado(cs[hi][0])
print("commits", len(cs), "primero", cs[lo], s0, "ultimo", cs[hi], s1)
# bisect sobre el primer patron (presente en lo, ausente en hi)
if s0[1][0] and not s1[1][0]:
    while hi - lo > 1:
        m = (lo + hi) // 2
        s = estado(cs[m][0]); print("  ", cs[m], s)
        if s[1][0]: lo = m
        else: hi = m
    print("PERDIDA UPSTREAM entre", cs[lo], estado(cs[lo][0]), "y", cs[hi], estado(cs[hi][0]))
