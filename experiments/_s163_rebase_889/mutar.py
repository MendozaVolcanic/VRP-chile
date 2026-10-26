# -*- coding: utf-8 -*-
"""S163: control de mutaciones del port de #889 sobre main (copia de experiments/_s159/instrumentos/mutar.py).

Cambios respecto de S159: el grupo i1 apunta al código fusionado con la cobertura por plataforma de #897; el grupo
i2 se retiró (I2 salió de #889 y vive en #890 y en scripts/evaluador_comun.py, #905); se agrega el grupo i3.

Original: control de mutaciones de los arreglos de instrumentos (guía de auditorías §6, A116).

Cada mutación reintroduce el defecto en el archivo real, corre las pruebas indicadas y RESTAURA el archivo (try/finally,
y además se compara el sha256 al terminar). Una mutación cuenta como atrapada sólo si alguna prueba cae por AssertionError
(no por excepción de otro tipo ni por error de colección): se lee la línea corta de pytest (-rf) de cada falla.

Uso: python experiments/_s159/instrumentos/mutar.py <grupo>     (grupo: i1, i3)
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
NADA = "(lambda *a, **k: None)"

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
         'cuentan = any(i.get("cuenta_estricto") for i in incidencias)', "cuentan = False"),
        ("el resumen vuelve a decir completa con incidencias", "scripts/run_pipeline.py",
         "if not fallas and not retiradas and not sin_granulos and not incidencias:",
         "if not fallas and not retiradas and not sin_granulos:"),
        ("sin gránulos pasa a contar en modo estricto (sale con 3 sin juicio)", "pipeline/fetch.py",
         'TIPOS_INCIDENCIA = {"sin_granulos": False,', 'TIPOS_INCIDENCIA = {"sin_granulos": True,'),
        ("reproc_brazos ignora las incidencias", "scripts/reproc_brazos.py",
         'for i in leido.get("incidencias", []):', 'for i in leido.get("incidencias_NO", []):'),
    ],
    "i3": [
        ("banco_paridad vuelve a escribir la ventana como literal", "scripts/banco_paridad.py",
         "TOL_S = VENTANA_S", "TOL_S = 120"),
        ("la ventana cambia en clase_mirova y banco_paridad no la sigue", "scripts/banco_paridad.py",
         "TOL_S = VENTANA_S", "TOL_S = 121"),
    ],
}
PRUEBAS = {"i1": ["tests/test_cobertura_incidencias_s159.py"],
           "i3": ["tests/test_pareo_unico_mirova_s159.py"]}


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
                               env=dict(os.environ, COLUMNS="400", PYTHONIOENCODING="utf-8"))
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
