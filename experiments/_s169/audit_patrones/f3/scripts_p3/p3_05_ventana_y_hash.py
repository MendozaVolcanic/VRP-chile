# -*- coding: utf-8 -*-
"""Bordes de scripts/ventana_sombra.py (CLI real) y control P-A de git hash-object sobre un CSV con CRLF.
P1: los casos de ventana usan el CLI que llama el workflow; control positivo: una ventana invalida SI sale con 2.
P2: si ventana_sombra estuviera muerto (imprimiera siempre lo mismo) los casos diferirian entre si.
Datos: fechas sinteticas; el reloj local NO se usa (se pasa --hoy)."""
import os, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = r"D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol"
def v(*a):
    r = subprocess.run([sys.executable, "-I", ARBOL + "/scripts/ventana_sombra.py", *a], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, r.stdout.strip(), r.stderr.strip()[:80]
casos = [("hoy 11-02", ["--hoy", "2026-11-02"]), ("hoy 11-03", ["--hoy", "2026-11-03"]), ("hoy 11-20", ["--hoy", "2026-11-20"]),
         ("start 11-03 end futuro lejano", ["--hoy", "2026-11-05", "--start", "2026-11-03", "--end", "2027-06-30"]),
         ("start 11-03 end 11-02 (invertida)", ["--hoy", "2026-11-05", "--start", "2026-11-03", "--end", "2026-11-02"]),
         ("start 11-01 (antes de la minima)", ["--hoy", "2026-11-05", "--start", "2026-11-01", "--end", "2026-11-04"]),
         ("start sin end", ["--hoy", "2026-11-05", "--start", "2026-11-04"]),
         ("fecha invalida", ["--hoy", "2026-11-05", "--start", "2026-11-3x", "--end", "2026-11-04"]),
         ("medir sin fechas", ["--hoy", "2026-11-05", "--medir"])]
for n, a in casos:
    print(f"{n:38} -> {v(*a)}")
# P-A: git hash-object de un CSV con CRLF en una copia de trabajo con autocrlf=true
d = tempfile.mkdtemp(prefix="p3_hash_")
run = lambda *a: subprocess.run(["git", *a], cwd=d, capture_output=True, text=True).stdout.strip()
run("init", "-q"); run("config", "core.autocrlf", "true")
open(d + "/ref.csv", "wb").write(b"a,b\r\n1,2\r\n")
print("P-A hash-object (con filtros, como banco_paridad.sha_git):", run("hash-object", "ref.csv"))
print("P-A hash-object --no-filters (bytes del disco)           :", run("hash-object", "--no-filters", "ref.csv"))
print("P-A blob de las mismas lineas en LF (lo que tendria git)  :", subprocess.run(["git", "hash-object", "--stdin"], cwd=d, input=b"a,b\n1,2\n", capture_output=True).stdout.decode().strip())
