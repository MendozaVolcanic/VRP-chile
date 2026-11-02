"""VS34 V-5b: las dos pruebas viejas ajustadas pueden fallar? Mutaciones en la copia."""
import re
exec(open("v5_mutaciones.py", encoding="utf-8").read().split("# control positivo del instrumento")[0].replace('HECHAS = (', 'HECHAS = ()  #'))
A = ("tests/test_mirova_v375_codigo_s165.py", "tests/test_sombra_codigo_mirova_s167.py")
mut("O1 Lascar x0 +300 m (Tier A) vs caja C13 y esperado", G, "x0: 629801.4", "x0: 630101.4", files=(A[0],), k="caja_de_375")
mut("O2 Lascar sin grilla vs control de la sombra de los 11", G, lambda t: [l for l in t.splitlines(True) if l.lstrip().startswith("Lascar:")][0], "", files=(A[1],), k="tiene_grilla")
mut("O3 grilla_del_volcan inventa una grilla para cualquier nombre (control 'VolcanSinGrilla')", "pipeline/mirova_v750_codigo.py", "    r = _referencias().get(nombre)\n    if r is None:\n        return None\n    n = n_celdas(paso_m)", "    r = _referencias().get(nombre) or _referencias()['Lascar']\n    n = n_celdas(paso_m)", files=(A[1],), k="tiene_grilla")
mut("O4 un volcan de los 34 con inner_radius_km=5 en yaml (filtro de la caja) no cambia la cuenta 11", "volcanoes.yaml", "name: Hudson", "name: Hudson", files=(A[0],), k="caja_de_375")
