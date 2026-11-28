# -*- coding: utf-8 -*-
"""S204: mutaciones del arreglo de tiempo del respaldo LANCE. Cada mutación se aplica en el worktree s204-lance, se
corren las pruebas nuevas y se restaura el archivo (se comprueba el hash al final). Cuenta como atrapada sólo si alguna
prueba falla por AssertionError (no por error de importación ni excepción), lección S202 y S203."""
import hashlib
import io
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = "D:/vrp-trabajo/worktrees/s204-lance"
LR = WT + "/pipeline/lance_respaldo.py"
FE = WT + "/pipeline/fetch.py"
MUT = [
    ("presupuesto nunca corta", LR, "    if _GASTADO[bolsa] >= tope:\n", "    if False:\n"),
    ("no suma el gasto", LR, "        _GASTADO[bolsa] += _reloj() - t0\n", "        _GASTADO[bolsa] += 0\n"),
    ("presupuesto enorme", LR, "PRESUPUESTO_S = 600\n", "PRESUPUESTO_S = 6000\n"),
    ("presupuesto chico", LR, "PRESUPUESTO_S = 600\n", "PRESUPUESTO_S = 60\n"),
    ("bolsa antigua chica", LR, "PRESUPUESTO_ANTIGUO_S = 300\n", "PRESUPUESTO_ANTIGUO_S = 30\n"),
    ("una sola bolsa", LR, ".days <= 1 else \"antiguo\"", ".days <= 1 else \"reciente\""),
    ("no salta el host caído", LR, "    if _se_colgo(ex) and host in _ORDEN and _ORDEN[-1] != host:\n", "    if False:\n"),
    ("ignora el timeout envuelto", LR, " or isinstance(getattr(ex, \"reason\", None), TimeoutError)", ""),
    ("degrada con cualquier error", LR, "    return isinstance(ex, TimeoutError) or", "    return True or"),
    ("conteo no salta el host", LR, "            except _ERRORES_RED as ex:\n                _fallo_host(host, ex)\n                continue\n        if n_lance",
     "            except _ERRORES_RED as ex:\n                continue\n        if n_lance"),
    ("errores no gastan", LR, "    try:\n        with _abrir(url, timeout=timeout) as r:\n            yield r\n    finally:\n        _GASTADO[bolsa] += _reloj() - t0\n",
     "    with _abrir(url, timeout=timeout) as r:\n        yield r\n    _GASTADO[bolsa] += _reloj() - t0\n"),
    ("congelado sin presupuesto", LR, "            with _con_presupuesto(URL_SALUD_CMR, 20) as r:", "            with _abrir(URL_SALUD_CMR, timeout=20) as r:"),
    ("consultar sin presupuesto", LR, "            with _con_presupuesto(url, TIMEOUT_S, bolsa) as r:\n                datos",
     "            with _abrir(url, timeout=TIMEOUT_S) as r:\n                datos"),
    ("conteo CMR sin presupuesto", LR, "        with _con_presupuesto(URL_CMR_GRANULOS + \"?\" + q, TIMEOUT_S, bolsa) as r:",
     "        with _abrir(URL_CMR_GRANULOS + \"?\" + q, timeout=TIMEOUT_S) as r:"),
    ("carpeta sin presupuesto", LR, "                with _con_presupuesto(url, TIMEOUT_S, bolsa) as r:\n                    n_lance",
     "                with _abrir(url, timeout=TIMEOUT_S) as r:\n                    n_lance"),
    ("reiniciar no repone orden", LR, "    _ORDEN[:] = list(HOSTS)\n", ""),
    ("reiniciar no repone gasto", LR, "    _GASTADO.update({\"reciente\": 0.0, \"antiguo\": 0.0})\n", ""),
    ("consultar recorre HOSTS fijo", LR, "    for host in list(_ORDEN):\n        url = \"https://%s/api/v2/content/details?",
     "    for host in HOSTS:\n        url = \"https://%s/api/v2/content/details?"),
    ("sin nrt4 en hosts NASA", FE, "                   \"nrt4.modaps.eosdis.nasa.gov\")", "                   )"),
]
PRUEBAS = ["tests/test_lance_respaldo_tiempo_s204.py", "tests/test_fetch_respaldo_lance_s203.py"]


def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


antes = {p: h(p) for p in (LR, FE)}
atrapadas = 0
for nombre, ruta, a, b in MUT:
    orig = io.open(ruta, encoding="utf-8", newline="").read()
    if "\r\n" in orig:   # el archivo usa CRLF: las mutaciones se escriben con LF
        a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
    assert orig.count(a) == 1, (nombre, orig.count(a))
    try:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig.replace(a, b))
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *PRUEBAS],
                           cwd=WT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    finally:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig)
    salida = r.stdout + r.stderr
    por_asercion = "AssertionError" in salida or "\nE       assert" in salida
    ok = r.returncode != 0 and por_asercion
    atrapadas += ok
    ultima = [l for l in salida.splitlines() if " passed" in l or " failed" in l][-1:]
    print("%-32s %s  %s" % (nombre, "ATRAPADA" if ok else ("CAE SIN ASERCION" if r.returncode else "SOBREVIVE"),
                            ultima[0] if ultima else ""))
print("atrapadas por aserción: %d de %d" % (atrapadas, len(MUT)))
assert {p: h(p) for p in (LR, FE)} == antes, "un archivo no quedó como estaba"
print("archivos restaurados: OK")
