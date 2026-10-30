# Deriva m4_muestra.py de la copia del nulo del autor: temporales dentro de mi CARPETA, subconjunto de mutaciones por nombre
# (argv[2:]; vacio = todas) y mutaciones propias Y1..Y8 sobre la logica de T1. No modifica el original.
src = open("m4_mutaciones_r3_copia.py", encoding="utf-8").read()
src = src.replace('BASE = "D:/vrp-trabajo/temporales/s169_vigilancia"', 'BASE = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/medidas/nulo"')
src = src.replace('if os.path.exists(DST):\n    shutil.rmtree(DST)', 'os.makedirs(BASE, exist_ok=True)\nif os.path.exists(DST):\n    shutil.rmtree(DST)')
extra = r'''
 # mutaciones propias del verificador R3 sobre T1
 ("Y1 el ultimo dia (fin) no se juzga", RS, "for i in range((b - a).days + 1)]", "for i in range((b - a).days)]"),
 ("Y2 el primer dia no se juzga", RS, "return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]", "return [(a + timedelta(days=i + 1)).isoformat() for i in range((b - a).days)]"),
 ("Y3 cualquier incidencia vale como prueba", RS, 'if i.get("tipo") == "sin_granulos" and i.get("fecha") == dia}', 'if i.get("fecha") == dia}'),
 ("Y4 un record de otro sensor cubre el dia", RS, "if (d, s) in hay:", "if any((d, x) in hay for x in sensores):"),
 ("Y6 corrida muerta: basta un K nuevo", RS, 'via_nuevos = sum(1 for r in nuevos if r.get("via_codigo_mirova") is True)', "via_nuevos = len(nuevos)"),
 ("Y7 SNPP vivo no exigido", RS, "if p not in vacias:\n            return None", "if p not in vacias and not p.startswith('VIIRS_SNPP'):\n            return None"),
 ("Y8 catalogo vacio solo con tres sensores", RS, 'or {"VIIRS750", "VIIRS375"} <= set(sin_pasada_d)', "or False"),
 ("Y9 retirada cuenta como vacia aunque cese sea posterior", RS, "if cese is not None and inicio_dia is not None and inicio_dia >= cese:", "if cese is not None and inicio_dia is not None:"),
'''
i = src.index("\n]\n\n\ndef correr")
src = src[:i] + extra.rstrip("\n") + src[i:]
src = src.replace("for nombre, f, a, b in MUT:\n    orig = None", 'SEL = sys.argv[2:]\nfor nombre, f, a, b in MUT:\n    if SEL and nombre != "ninguna" and not any(nombre.startswith(x) for x in SEL):\n        continue\n    orig = None')
open("m4_muestra.py", "w", encoding="utf-8").write(src)
print("ok")
