# Mutaciones propias (V-A1) sobre una COPIA fuera del worktree: lo que las 18 pruebas no vigilan.
import sys, subprocess, pathlib, shutil
copia = pathlib.Path(sys.argv[1]); f = copia/"experiments/_s163_diurno_k/dias_excluidos_nasa.py"
orig = f.read_text(encoding="utf-8")
M = [
 ("M1 main decide con la regla (b)", "    excluir = dias_a_excluir(dict(vacios), con_records)\n    excluir_b = dias_a_excluir_b(dict(vacios), faltas)",
  "    excluir_b = dias_a_excluir_b(dict(vacios), faltas)\n    excluir = excluir_b"),
 ("M2 sin paginacion de CMR", "        if len(e) < 2000:\n            break\n        pagina += 1", "        break"),
 ("M3 dia CMR con [:9]", 'dias[g["time_start"][:10]] += 1', 'dias[g["time_start"][:9]] += 1'),
 ("M4 caja distinta", 'CAJA = "-72.5,-39.5,-67.5,-23.0"', 'CAJA = "-72.5,-39.5,-67.5,-33.0"'),
 ("M5 version de VNP02IMG", '"VNP02IMG": "2",', '"VNP02IMG": "9",'),
 ("M6 solo se consulta la banda I", "    for s, prods in PRODUCTOS.items():\n        for prod, ver in prods.items():\n            for _, d0, d1 in ventanas:",
  "    for s, prods in list(PRODUCTOS.items())[:1]:\n        for prod, ver in prods.items():\n            for _, d0, d1 in ventanas:"),
 ("M7 CMR dia = hasta T00 (pierde el ultimo dia)", '"temporal": "%sT00:00:00Z,%sT23:59:59Z" % (desde, hasta)', '"temporal": "%sT00:00:00Z,%sT00:00:00Z" % (desde, hasta)'),
 ("M8 error de CMR = 0 gran.", "        e = json.load(urllib.request.urlopen(CMR + \"?\" + q, timeout=60))[\"feed\"][\"entry\"]",
  "        try:\n            e = json.load(urllib.request.urlopen(CMR + \"?\" + q, timeout=60))[\"feed\"][\"entry\"]\n        except Exception:\n            e = []"),
 ("M9 ventanas de W2 a W6 incluyen todas (sk.VENTANAS)", "x[:3] for x in sk.VENTANAS if x[0] in sk.DECIDEN", "x[:3] for x in sk.VENTANAS"),
 ("M10 control por defecto = brazo", 'default="_s154_ab_diurno_k_control"', 'default="_s154_ab_diurno_k_on"'),
]
for nombre, viejo, nuevo in M:
    assert orig.count(viejo) == 1, (nombre, orig.count(viejo))
    f.write_text(orig.replace(viejo, nuevo), encoding="utf-8")
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "experiments/_s163_diurno_k/test_dias_excluidos_nasa.py"],
                       cwd=copia, capture_output=True, text=True)
    ult = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-200:]
    print("%-55s -> %s | %s" % (nombre, "ATRAPADA" if p.returncode else "SOBREVIVE", ult))
f.write_text(orig, encoding="utf-8")
