"""A7: mutaciones del auto-audit en la COPIA (ci_copia), y si las pruebas las atrapan.

Cada mutacion: reemplazo exacto (debe aparecer 1 vez), corre las pruebas del auto-audit, restaura.
Control: la copia sin mutar debe pasar (nulo del instrumento).
"""
import os, subprocess, sys, shutil
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ci_copia")
AA = os.path.join(C, "scripts", "auto_audit_weekly.py")
BP = os.path.join(C, "scripts", "banco_paridad.py")
TESTS = ["tests/test_auto_audit_por_detector_s156.py", "tests/test_auto_audit_ventana_regimen_s142.py",
         "tests/test_auto_audit_historial_falsas_s153.py", "tests/test_auto_audit_falsas_s139.py",
         "tests/test_auto_audit_cobertura_s150.py", "tests/test_auto_audit_union_historica_s151.py",
         "tests/test_audit_ratio_band_s124.py", "tests/test_audit_solar_filter_s124.py",
         "tests/test_banco_paridad_s139.py", "tests/test_regla_minimas_d9_s151.py"]

MUT = [
    ("M1 falsas mezclan detectores", AA, 'vig = [r for r in recs if r["det"] == vigente]', 'vig = list(recs)'),
    ("M2 main no agrega flags de protegidas", AA, "flags.extend(flags_protegidas(protegidas, vigente))", "pass"),
    ("M3 noche con records de otro detector", AA,
     '                fuera[f"{d_rec} en noche {d_noche}"] += 1\n                continue',
     '                fuera[f"{d_rec} en noche {d_noche}"] += 1'),
    ("M4 protegida publicada solo si TODAS sus pasadas publican", AA,
     'else "publicada" if any(r["pub"] for r in cand)', 'else "publicada" if all(r["pub"] for r in cand)'),
    ("M5 flags de protegidas de cualquier detector", AA,
     'if p["detector"] != vigente or p["estado"] != "sin_publicar":', 'if p["estado"] != "sin_publicar":'),
    ("M6 main juzga con C0", AA, "ev = por_detector[vigente]", 'ev = por_detector.get("C0", por_detector[vigente])'),
    ("M7 banco sin la marca sha", BP, '"sha": (r.get("regimen") or {}).get("codigo_sha")', '"sha": None'),
    ("M8 main sin D-9 en el recall", AA, "mir, n_diurnas_excluidas = noches_mirova(aplicar_d9(alertas, REGLA_MINIMAS), coords, win)",
     "mir, n_diurnas_excluidas = noches_mirova(alertas, coords, win)"),
    ("M9 pareo de protegidas a 0 s", AA, "abs((r[\"dt\"] - dt).total_seconds()) <= TOL_PASADA_S",
     "abs((r[\"dt\"] - dt).total_seconds()) <= 0"),
    ("M10 frontera ignorada (todo C0)", AA, "    frontera = leer_frontera_k()\n", "    frontera = None\n"),
    ("M11 protegidas sin_record leidas como sin_publicar", AA,
     'estado = ("sin_record" if not cand else', 'estado = ("sin_publicar" if not cand else'),
    ("M12 error del banco no degrada", AA,
     '        cobertura_avisos.append(f"no se pudieron evaluar las alertas protegidas (banco de paridad): {error_banco}")',
     '        pass'),
]


def correr():
    o = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", *TESTS],
                       cwd=C, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    ult = [l for l in o.stdout.splitlines() if " passed" in l or " failed" in l or "error" in l.lower()]
    fallas = [l for l in o.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")]
    return o.returncode, (ult[-1] if ult else o.stdout[-300:]), fallas


rc, res, _ = correr()
print("CONTROL sin mutar:", rc, res)
for nombre, path, a, b in MUT:
    src = open(path, encoding="utf-8").read()
    n = src.count(a)
    if n != 1:
        print(nombre, ": NO APLICADA (coincidencias=%d)" % n)
        continue
    shutil.copy(path, path + ".bak")
    open(path, "w", encoding="utf-8").write(src.replace(a, b))
    try:
        rc, res, fallas = correr()
    finally:
        shutil.move(path + ".bak", path)
    print(f"{nombre}: {'ATRAPADA' if rc else 'NO ATRAPADA'} | {res} | {[f[:110] for f in fallas[:3]]}")
rc, res, _ = correr()
print("CONTROL tras restaurar:", rc, res)
