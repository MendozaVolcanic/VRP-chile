# -*- coding: utf-8 -*-
"""Verificador S142: aplica LITERALMENTE los bloques de codigo del plan sobre una COPIA de pipeline/ y
tests/ en el scratchpad (el repo no se toca), genera el golden ANTES de editar, corre los tests del plan
y mutaciones de control (los tests fallan cuando deberian?).

Uso: python aplicar_plan_en_copia.py <directorio_destino_en_scratchpad>
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEST = Path(sys.argv[1])
if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)
shutil.copytree(REPO / "pipeline", DEST / "pipeline", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(REPO / "tests", DEST / "tests", ignore=shutil.ignore_patterns("__pycache__", "golden*"))
plan = (REPO / "docs/superpowers/plans/2026-09-15-flags-d22-d25.md").read_text(encoding="utf-8")
B = [m.group(2) for m in re.finditer(r"```(python|yaml|bash|markdown)\n(.*?)```", plan, flags=re.S)]
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "VRP_PROFILE": "mirova_equivalent"}


def rd(p):
    return (DEST / p).read_text(encoding="utf-8")


def wr(p, s):
    (DEST / p).write_text(s, encoding="utf-8")


def reemplazar(p, old, new, etiqueta):
    s = rd(p)
    n = s.count(old)
    print(f"[{etiqueta}] ocurrencias del ancla en {p}: {n}", flush=True)
    assert n == 1, etiqueta
    wr(p, s.replace(old, new))


def insertar_despues(p, ancla, bloque, etiqueta):
    s = rd(p)
    n = s.count(ancla)
    print(f"[{etiqueta}] ocurrencias del ancla en {p}: {n}", flush=True)
    assert n == 1, etiqueta
    wr(p, s.replace(ancla, ancla + bloque))


def run(cmd, etiqueta, filtro=True):
    r = subprocess.run(cmd, cwd=str(DEST), env=ENV, capture_output=True, text=True, shell=True,
                       encoding="utf-8", errors="replace")
    print(f"\n===== {etiqueta} (rc={r.returncode}) =====", flush=True)
    lines = (r.stdout + r.stderr).splitlines()
    if filtro:
        keep = [l for l in lines if any(x in l for x in ("PASSED", "FAILED", "ERROR", "passed", "failed", "Error", "assert "))]
    else:
        keep = lines
    print("\n".join(keep[-120:]), flush=True)
    return r


# Tarea 1: arnes + golden con el codigo de hoy
wr("tests/arnes_sintetico_s142.py", B[3])
(DEST / "tests/golden_s142").mkdir()
run("python tests/arnes_sintetico_s142.py --salida tests/golden_s142/apagado.json", "T1 golden", filtro=False)
codigo = B[4].splitlines()[1].split("python -c ", 1)[1].strip()[1:-1]
r = subprocess.run([sys.executable, "-c", codigo], cwd=str(DEST), env=ENV, capture_output=True, text=True)
print("T1 paso 2 salida:", r.stdout.strip(), r.stderr[-300:], flush=True)

# Tarea 2
wr("tests/test_apagado_no_cambia_nada_s142.py", B[7])

# Tarea 3
wr("tests/test_d22_compuerta_bt_s142.py", B[10])
dc = "pipeline/detection_context.py"
reemplazar(dc, '    deti: Optional[np.ndarray] = None,\n) -> np.ndarray:\n    """Contextual dNTI',
           '    deti: Optional[np.ndarray] = None,\n' + B[12] + ') -> np.ndarray:\n    """Contextual dNTI', "T3p3 firma")
reemplazar(dc, B[13], B[14], "T3p3 cuerpo")
reemplazar(dc, '    deti: Optional[np.ndarray] = None,\n) -> np.ndarray:\n    """Dual-ROI',
           '    deti: Optional[np.ndarray] = None,\n' + B[15] + ') -> np.ndarray:\n    """Dual-ROI', "T3p4 firma")
reemplazar(dc, B[16], B[17], "T3p4 kwargs")
reemplazar(dc, "    use_prose_branch: bool = False,\n) -> tuple:",
           "    use_prose_branch: bool = False,\n" + B[18] + ") -> tuple:", "T3p5 firma")
reemplazar(dc, B[19], B[20], "T3p5 cuerpo")

# Tarea 4
wr("tests/test_flags_d22_d25_perfil_s142.py", B[25])
insertar_despues("tests/test_gr2_profile_invariants.py", '    "ENABLE_LOCAL_CLUSTER_MAGNITUDE": False,\n', B[26], "T4p2a")
insertar_despues("tests/test_gr2_profile_invariants.py",
                 '        "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS": "enable_nadir_fixed_pixel_area_viirs",\n', B[27], "T4p2b")
insertar_despues("pipeline/profile.py", '    _p.get("enable_local_cluster_magnitude_viirs375", False))\n', B[29], "T4p4")
y = "pipeline/profiles/mirova_equivalent.yaml"
insertar_despues(y, "  test1_intermediate_bg_ring_km: [1.5, 3.0]\n", B[30], "T4p5a")
insertar_despues(y, "  enable_second_pass_conditioned: false\n", B[31], "T4p5b")
insertar_despues(y, "  enable_local_kernel_bg: true\n", B[32], "T4p5c")

# Tarea 5
wr("tests/test_d25_fondo_vecinos_s142.py", B[36])
reemplazar("pipeline/vrp_regimes.py", "    return t_bks\n\n\ndef cluster_corona_background(",
           "    return t_bks\n\n\n" + B[38] + "\n\ndef cluster_corona_background(", "T5p3")
reemplazar("pipeline/vrp_regimes.py", B[40], B[41], "T5p5")

# Tarea 6
wr("tests/test_d22_compuerta_bt_s142.py", rd("tests/test_d22_compuerta_bt_s142.py") + "\n\n" + B[44])
wr("tests/test_d25_fondo_vecinos_s142.py", rd("tests/test_d25_fondo_vecinos_s142.py") + "\n\n" + B[45])
pv = "pipeline/process_viirs.py"
insertar_despues(pv, "                               select_test1_effective_lbg)\n", B[47], "T6p4")
insertar_despues(pv, "    return sum_cluster_vrp(per_pixel), False, per_pixel\n", B[48], "T6p5")
insertar_despues(pv, "    diag_L_bg_local = None  # S140 T7: sólo si actúa el kernel local\n", B[49], "T6p6")
for a, b, e in ((50, 51, "T6p7 dual"), (52, 53, "T6p7 ctx"), (54, 55, "T6p7 eti"), (56, 57, "T6p7 fp"),
                (58, 59, "T6p8"), (60, 61, "T6p9a"), (62, 63, "T6p9b")):
    reemplazar(pv, B[a], B[b], e)
s = rd(pv)
i = s.rfind("\n    return record")
wr(pv, s[:i] + "\n" + B[64].rstrip("\n") + s[i:])
wr("pipeline/profiles/_s142_verif_flags_nuevos.yaml", B[65])
for idx, nombre in zip(range(71, 77), ["_s142_ab_control", "_s142_ab_literal", "_s142_ab_lit_sin_fondo",
                                        "_s142_ab_lit_con_compuerta", "_s142_ab_lit_sp_suelto", "_s142_ab_lit_keep_peak"]):
    assert f"profile: {nombre}" in B[idx], nombre
    wr(f"pipeline/profiles/{nombre}.yaml", B[idx])
print("py_compile rc:", subprocess.run([sys.executable, "-m", "py_compile", pv, dc, "pipeline/vrp_regimes.py",
                                        "pipeline/profile.py"], cwd=str(DEST)).returncode, flush=True)
print("lineas compute_test1_nti / FLAG_DNS:", [(n + 1, l.strip()[:50]) for n, l in enumerate(rd(pv).splitlines())
                                               if "compute_test1_nti" in l or l.startswith("FLAG_DNS")], flush=True)

T = ("tests/test_apagado_no_cambia_nada_s142.py tests/test_d22_compuerta_bt_s142.py tests/test_d25_fondo_vecinos_s142.py "
     "tests/test_flags_d22_d25_perfil_s142.py tests/test_gr2_profile_invariants.py tests/test_fondo_persistido_s140.py "
     "tests/test_second_pass_conditioned_s135.py tests/test_local_kernel_background.py tests/test_corona_eq6_viirs_s126.py "
     "tests/test_corona_single_pixel_coherencia_s127.py")
run(f"python -m pytest -p no:cacheprovider -rA -q {T}", "TESTS DEL PLAN SOBRE LA COPIA")


def mutar(p, old, new, etiqueta, cmd):
    s0 = rd(p)
    n = s0.count(old)
    print(f"\n[{etiqueta}] ocurrencias a mutar: {n}", flush=True)
    assert n >= 1, etiqueta
    wr(p, s0.replace(old, new))
    try:
        return run(cmd, "MUTACION " + etiqueta)
    finally:
        wr(p, s0)


mutar(dc, "    apply_bt_gate: bool = True,", "    apply_bt_gate: bool = False,",
      "M1 default apply_bt_gate=False en los 3 helpers (MODIS y V750 pierden la compuerta)",
      "python -m pytest -p no:cacheprovider -rA -q tests/test_apagado_no_cambia_nada_s142.py")
mutar(pv, "                if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:\n                    L_bg, _n_sin",
      "                if True:\n                    L_bg, _n_sin",
      "M2 fondo por vecinos siempre activo en el bloque contextual",
      "python -m pytest -p no:cacheprovider -rA -q tests/test_apagado_no_cambia_nada_s142.py::test_perfil_operacional_reproduce_el_golden_bit_a_bit")
mutar(pv, "            _t1_Lbg = effective_L_bg\n",
      "            _t1_Lbg = effective_L_bg * 0.5\n",
      "M3 fondo del Test 1 alterado con flag OFF (los dos bloques)",
      "python -m pytest -p no:cacheprovider -rA -q tests/test_apagado_no_cambia_nada_s142.py::test_perfil_operacional_reproduce_el_golden_bit_a_bit")
mutar(pv, "apply_bt_gate=not ENABLE_TESTS_23_NO_BT_GATE_VIIRS375,  # D22 (S142)\n                    )\n                else:",
      "apply_bt_gate=True,  # D22 (S142)\n                    )\n                else:",
      "M4 la llamada dual-ROI V375 ignora el flag D22",
      "python -m pytest -p no:cacheprovider -rA -q tests/test_d22_compuerta_bt_s142.py")
