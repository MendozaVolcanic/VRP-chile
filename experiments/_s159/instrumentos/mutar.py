# -*- coding: utf-8 -*-
"""S159: control de mutaciones de los arreglos de instrumentos (guía de auditorías §6, A116).

Cada mutación reintroduce el defecto en el archivo real, corre las pruebas indicadas y RESTAURA el archivo (try/finally,
y además se compara el sha256 al terminar). Una mutación cuenta como atrapada sólo si alguna prueba cae por AssertionError
(no por excepción de otro tipo ni por error de colección): se lee la línea corta de pytest (-rf) de cada falla.

Uso: python experiments/_s159/instrumentos/mutar.py <grupo>     (grupo: i1, i2)
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
NADA = "(lambda *a, **k: None)"
EV = "experiments/_s157_prereg_d25/evaluar_d25.py"

MUTACIONES = {
    "i1": [
        ("sin_granulos no se registra", "pipeline/fetch.py",
         'registrar_incidencia("sin_granulos"', NADA + '("sin_granulos"'),
        ("sin_granulos se registra aunque la búsqueda haya fallado", "pipeline/fetch.py",
         "                if len(_FALLAS) == n_fallas_antes:\n                    registrar_incidencia(\"sin_granulos\"",
         "                if True:\n                    registrar_incidencia(\"sin_granulos\""),
        ("L1B sin geolocalización en el catálogo no se registra", "pipeline/fetch.py",
         "            if sin_geo and len(_FALLAS) == n_fallas_antes:", "            if False:"),
        ("geolocalización ausente en disco no se registra", "scripts/run_pipeline.py",
         'fetch.registrar_incidencia("sin_geolocalizacion", volcano["name"]',
         NADA + '("sin_geolocalizacion", volcano["name"]'),
        ("día parcial nunca se detecta", "pipeline/fetch.py",
         "    return ahora < inicio + timedelta(days=1, hours=LATENCIA_MINIMA_NRT_H)", "    return False"),
        ("el modo estricto ignora las incidencias", "scripts/run_pipeline.py",
         'cuenta_estricto = bool(fallas) or any(i.get("cuenta_estricto") for i in incidencias)',
         "cuenta_estricto = bool(fallas)"),
        ("el resumen vuelve a decir completa con incidencias", "scripts/run_pipeline.py",
         "    if not fallas and not incidencias:\n        print(\"Cobertura: completa",
         "    if not fallas:\n        print(\"Cobertura: completa"),
        ("sin gránulos pasa a contar en modo estricto (sale con 3 sin juicio)", "pipeline/fetch.py",
         'TIPOS_INCIDENCIA = {"sin_granulos": False,', 'TIPOS_INCIDENCIA = {"sin_granulos": True,'),
        ("reproc_brazos ignora las incidencias", "scripts/reproc_brazos.py",
         'for i in leido.get("incidencias", []):', 'for i in leido.get("incidencias_NO", []):'),
    ],
    "i2": [
        ("el defecto vuelve a ser la calibración original", EV,
         'CALIB_MODO = "simetrica"', 'CALIB_MODO = "sellada"'),
        ("el placebo no se corre (lista de ganancias vacía)", EV,
         "PLACEBO_GANANCIAS = (1.2, 0.8)", "PLACEBO_GANANCIAS = ()"),
        ("el placebo sólo prueba 1,2 (no ve el sesgo hacia arriba)", EV,
         "PLACEBO_GANANCIAS = (1.2, 0.8)", "PLACEBO_GANANCIAS = (1.2,)"),
        ("un placebo que da MEJORA no invalida", EV,
         'if modo != "informa" and r_g == "MEJORA":', 'if False:'),
        ("el veredicto ignora el placebo", EV,
         '    if ver.get("PLACEBO", "OK") != "OK" and', '    if False and'),
        ("combinar no trata INVALIDO como malo", EV,
         'malo = [e for v, e in estados if e.startswith(("INVALIDO", "NO CUMPLE", "INDECIDIBLE", "PENDIENTE"))]',
         'malo = [e for v, e in estados if e.startswith(("NO CUMPLE", "INDECIDIBLE", "PENDIENTE"))]'),
    ],
}
PRUEBAS = {"i1": ["tests/test_cobertura_incidencias_s159.py"],
           "i2": ["tests/test_evaluar_d25_placebo_s159.py"]}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(grupo):
    filas = []
    for nombre, rel, viejo, nuevo in MUTACIONES[grupo]:
        p = RAIZ / rel
        original = p.read_bytes()
        h0 = sha(p)
        texto = original.decode("utf-8")
        if "\r\n" in texto:  # los archivos del repo están en CRLF en este checkout
            viejo, nuevo = viejo.replace("\n", "\r\n"), nuevo.replace("\n", "\r\n")
        if texto.count(viejo) < 1:
            filas.append((nombre, "NO APLICA (texto no encontrado)", ""))
            continue
        try:
            p.write_bytes(texto.replace(viejo, nuevo).encode("utf-8"))
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf"] + PRUEBAS[grupo],
                               cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                               env=dict(os.environ, COLUMNS="400"))
        finally:
            p.write_bytes(original)
        assert sha(p) == h0, "no se restauró %s" % rel
        fallas = [x for x in r.stdout.splitlines() if x.startswith("FAILED")]
        por_asercion = [x for x in fallas if "AssertionError" in x or " - assert " in x]
        estado = ("ATRAPADA por aserción" if por_asercion else
                  "CAE SIN ASERCIÓN" if fallas or r.returncode else "NO ATRAPADA")
        filas.append((nombre, estado, "%d fallas; %s" % (len(fallas), (por_asercion or fallas or [""])[0][:150])))
    for n, e, d in filas:
        print("%-70s %-22s %s" % (n, e, d))
    print("RESUMEN: %d de %d atrapadas por aserción" % (sum(e.startswith("ATRAPADA") for _, e, _ in filas), len(filas)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
