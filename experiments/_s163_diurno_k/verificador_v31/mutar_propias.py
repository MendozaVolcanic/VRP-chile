# Mutaciones propias del verificador v3.1, SOLO en una copia (git archive) fuera del worktree.
import sys, subprocess, pathlib, os
copia = pathlib.Path(sys.argv[1])
ev = copia / "experiments/_s163_diurno_k/evaluar_diurno_k.py"
orig = ev.read_bytes().decode("utf-8").replace(chr(13) + chr(10), chr(10))
M = [
 ("N1 juzgar_i6 sin el argumento gana", 'juzgar_i6(res_a, det_a["B"], falsos, gana)', 'juzgar_i6(res_a, det_a["B"], falsos)'),
 ("N2 gana cuenta GANA o PIERDE", 'gana += res_c == "GANA"', 'gana += res_c in ("GANA", "PIERDE")'),
 ("N3 reclasifica tambien las nocturnas", " and es_dia_vol(p.volcano, p.instante)) else p for p in pas]", ") else p for p in pas]"),
 ("N4 sin filtro de sensor", "p.fuente == \"CONS\" and p.sensor_bucket in SENSORES_DIA\n", "p.fuente == \"CONS\"\n"),
 ("N5 sin filtro de fuente CONS", "p.estado == \"fp\" and p.fuente == \"CONS\" and", "p.estado == \"fp\" and"),
 ("N6 reclasifica siempre (tambien en el principal)", "    if otra_como_negativo:\n        # Verificador v3, V3-1", "    if True:\n        # Verificador v3, V3-1"),
 ("N7 reclasifica a otro estado", 'p._replace(estado="rutina")', 'p._replace(estado="otro")'),
 ("N8 tope GANA con >=", "if gana_c > MAX_GANA_C:", "if gana_c >= MAX_GANA_C:"),
 ("N9 tope GANA en 4 pero compara con MAX_FALSOS_C", "if gana_c > MAX_GANA_C:", "if gana_c > MAX_FALSOS_C:"),
 ("N10 gana_c por defecto alto", "def juzgar_i6(res_a, bloques_a, falsos_c, gana_c=0):", "def juzgar_i6(res_a, bloques_a, falsos_c, gana_c=99):"),
 ("N11 FP de MODIS tambien (quitar es_dia pero sin sensor)", " and p.sensor_bucket in SENSORES_DIA\n", " and p.sensor_bucket in (\"VIIRS375\", \"VIIRS750\", \"MODIS\")\n"),
 ("N12 compuerta_i6 devuelve c_gana en falsos", '"c_gana": gana', '"c_gana": falsos'),
]
for nom, v, n in M:
    assert orig.count(v) == 1, (nom, orig.count(v))
    ev.write_bytes(orig.replace(v, n).encode("utf-8"))
    r = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x",
                        str(copia / "experiments/_s163_diurno_k/test_evaluar_diurno_k.py")],
                       capture_output=True, text=True, cwd=str(copia), env=dict(os.environ, PYTHONPATH=""))
    ult = [l for l in r.stdout.splitlines() if l.strip()][-1] if r.stdout.strip() else r.stderr[-200:]
    print("%-58s rc=%d | %s" % (nom, r.returncode, ult[:110]), flush=True)
ev.write_bytes(orig.encode("utf-8"))
