# Verificador S156: pruebas de mutacion de scripts/vigilancia_sombra.py contra tests/test_vigilancia_sombra_s156.py,
# en una COPIA fuera del worktree. Clasifica: ATRAPADA (falla por AssertionError), CAIDA (excepcion que no es
# aserto, o error de coleccion: NO cuenta como atrapada), SOBREVIVE (la suite pasa). Control nulo: sin mutacion
# la suite pasa (si no pasa, el instrumento esta roto).
# Uso: python v5_mutaciones.py <worktree> <dir_copia>
import os, re, shutil, subprocess, sys
from pathlib import Path

W = Path(sys.argv[1]); BASE = Path(sys.argv[2])
if BASE.exists():
    shutil.rmtree(BASE)
for d in ("scripts", "pipeline"):
    shutil.copytree(W / d, BASE / d, ignore=shutil.ignore_patterns("__pycache__"))
(BASE / "frontend").mkdir(parents=True)
for f in ("cambio_detector.js", "index.html"):
    shutil.copy2(W / "frontend" / f, BASE / "frontend" / f)
shutil.copy2(W / "volcanoes.yaml", BASE / "volcanoes.yaml")
(BASE / "tests").mkdir()
shutil.copy2(W / "tests" / "test_vigilancia_sombra_s156.py", BASE / "tests" / "test_vigilancia_sombra_s156.py")
(BASE / "experiments" / "_s153_fk_v2").mkdir(parents=True)
shutil.copy2(W / "experiments" / "_s153_fk_v2" / "v1.log", BASE / "experiments" / "_s153_fk_v2" / "v1.log")
for p in ("pipeline/profiles",):
    pass
SRC = BASE / "scripts" / "vigilancia_sombra.py"
ORIG = SRC.read_text(encoding="utf-8")

MUT = [
    ("M0_nulo_sin_mutacion", None, None),
    ("M1_reversion_no_exige_protegida", 'reversion = [p for p in calla if p["protegida"]]', 'reversion = list(calla)'),
    ("M2_calla_acepta_prod_sin_record", 'p["sombra_pub"] is True and p["prod_pub"] is False', 'p["sombra_pub"] is True and not p["prod_pub"]'),
    ("M3_tolerancia_3600s", 'TOL_S = cm.VENTANA_S', 'TOL_S = 3600'),
    ("M4_publica_all_en_vez_de_any", 'any(r["pub"] for r in cands)', 'all(r["pub"] for r in cands)'),
    ("M5_sin_regla_D9", 'cm.aplicar_regla_minimas(filas, "SN").filas', 'cm.aplicar_regla_minimas(filas, "original").filas'),
    ("M6_muy_bajo_incluye_protegidas", 'if p["protegida"] or p["prod_pub"] is None', 'if p["prod_pub"] is None'),
    ("M7_negativos_todas_las_etiquetas", 'r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"', 'r["b"] == "VIIRS375"'),
    ("M8_cota_MODIS_cambiada", '"MODIS": {"V1": (3, 4), "V2": (5, 26)}', '"MODIS": {"V1": (0, 4), "V2": (1, 26)}'),
    ("M9_cota_V750_cambiada", '"VIIRS750": {"V1": (14, 30), "V2": (26, 75)}', '"VIIRS750": {"V1": (4, 30), "V2": (4, 75)}'),
    ("M10_sombra_detenida_umbral_10", 'MAX_DIAS_SOMBRA_SIN_DATOS = 3', 'MAX_DIAS_SOMBRA_SIN_DATOS = 10'),
    ("M11_cumplida_solo_por_dias", 'vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)', 'bool(vence and hoy >= vence)'),
    ("M12_ventana_no_filtra", 'and win[0] <= f["fecha_utc"][:10] <= win[1]', ''),
    ("M13_persistencia_largo_4", 'def _corridas(fechas, largo=3):', 'def _corridas(fechas, largo=4):'),
    ("M14_diurnas_no_se_saltan", '        if diurna(b, vol, dt):\n            continue\n', ''),
    ("M15_muy_bajo_cota_con_hi", '"dispara": lo > cota}', '"dispara": hi > cota}'),
    ("M16_cumplida_vistas_cuenta_None", 'p["protegida"] and p["sombra_pub"] is not None)', 'p["protegida"])'),
    ("M17_protegidas_umbral_mayor", '"protegida": any(cm.alerta_protegida(f) for f in fs)', '"protegida": any(cm.alerta_protegida(f, umbral=2.5) for f in fs)'),
]


def correr(nombre, viejo, nuevo):
    src = ORIG
    if viejo is not None:
        n = src.count(viejo)
        if n != 1:
            return nombre, "MUTACION_NO_APLICABLE (%d coincidencias)" % n, ""
        src = src.replace(viejo, nuevo)
    SRC.write_text(src, encoding="utf-8")
    for c in BASE.rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRP_PROFILE="mirova_equivalent")
    o = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", "tests/test_vigilancia_sombra_s156.py"],
                       cwd=BASE, capture_output=True, text=True, env=env, timeout=600)
    out = o.stdout + o.stderr
    if o.returncode == 0:
        res = "SOBREVIVE"
    else:
        lineas = [l for l in out.splitlines() if re.search(r"\.py:\d+: ", l)]
        excs = [l.split(": ", 1)[1][:90] for l in lineas]
        fallas = re.findall(r"^FAILED (\S+)", out, re.M)
        if fallas and excs and all(e.startswith("AssertionError") or e.startswith("assert") for e in excs):
            res = "ATRAPADA %s | %s" % ([f.split("::")[-1] for f in fallas], excs)
        else:
            res = "CAIDA/NO_ASERTO %s | %s" % ([f.split("::")[-1] for f in fallas], excs or out[-300:].replace(chr(10), " "))
    return nombre, res, out[-200:]


for m in MUT:
    nombre, res, cola = correr(*m)
    print("%-40s %s" % (nombre, res))
SRC.write_text(ORIG, encoding="utf-8")
