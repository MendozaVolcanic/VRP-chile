# -*- coding: utf-8 -*-
"""Auditoría S169 (frente V750), P-D sobre la rama de la ROI.
Pregunta 1: si el script roi_v750b_a_grillas.py estuviera roto, ¿lo vería tests/test_roi_v750b_variantes_s169.py?
  -> se rompe UNA cosa por vez en una copia y se corre la prueba; ATRAPADA = falla por AssertionError y ninguna
     excepción distinta; CAIDA = falla con otra excepción; NO ATRAPADA = la prueba sigue verde.
Pregunta 2: si el instrumento estuviera muerto, ¿se vería distinto? Control IDENTIDAD (sin mutar: verde) y CONTROL_CAIDA
  (lanza ValueError: tiene que salir CAIDA, no ATRAPADA).
Denominador: 21 pruebas de la rama 3c5c494b9, sobre pipeline/mirova_v750_codigo.py de main 443da8649.
Procesos livianos: un pytest a la vez (~1 s cada uno).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent / "roi_run"
PY = sys.executable
SCRIPT = "scripts/roi_v750b_a_grillas.py"

MUT = {
    "IDENTIDAD": (None, None),
    "m1_B2_a_sens": ('"B2": "crater"', '"B2": "sens"'),
    "m2_B4_sin_Tupungatito": ('SENSIBLES_B4 = ("PuyehueCordonCaulle", "Tupungatito")', 'SENSIBLES_B4 = ("PuyehueCordonCaulle",)'),
    "m3_B3_a_def": ('"B3": "inner"', '"B3": "def"'),
    "m4_B5_a_sens": ('"B5": "corona"', '"B5": "sens"'),
    "m5_sin_comentario": ('texto = texto.replace(COMENTARIO_VIEJO, COMENTARIO_NUEVO)', 'pass'),
    "m6_dry_run_escribe": ('if a.escribir and nuevo != viejo:', 'if nuevo != viejo:'),
    "m7_escribe_viejo": ('YAML.write_text(nuevo, encoding="utf-8", newline="")', 'YAML.write_text(viejo, encoding="utf-8", newline="")'),
    "m8_newline_crlf": ('YAML.write_text(nuevo, encoding="utf-8", newline="")', 'YAML.write_text(nuevo, encoding="utf-8")'),
    "m9_regex_acepta_varios": ('if n != 1:', 'if n < 1:'),
    "m10_choices_sin_B5": ('choices=("B0", "B1", "B2", "B3", "B4", "B5")', 'choices=("B0", "B1", "B2", "B3", "B4")'),
    "CONTROL_CAIDA": ('    roi = roi_por_volcan(brazo)\n', '    raise ValueError("mutacion de control")\n'),
}


def correr(nombre, viejo, nuevo):
    d = BASE.parent / f"roi_mut_{nombre}"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(BASE, d, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    if viejo is not None:
        p = d / SCRIPT
        src = p.read_text(encoding="utf-8")
        assert src.count(viejo) == 1, (nombre, src.count(viejo))
        p.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    o = subprocess.run([PY, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rN", "--tb=line",
                        "tests/test_roi_v750b_variantes_s169.py"], cwd=str(d), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    txt = o.stdout + o.stderr
    # --tb=line: una línea por falla, "ruta:linea: Tipo: mensaje" (o "E   Tipo" si pytest la corta)
    lin = [x for x in txt.splitlines() if re.match(r"^.*\.py:\d+: \w+", x)]
    tipos = [re.match(r"^.*\.py:\d+: (\w+)", x).group(1) for x in lin]
    fallas = tipos
    no_assert = [t for t in tipos if t not in ("AssertionError", "assert")]
    m_fail = re.search(r"(\d+) failed", txt)
    n_fail = int(m_fail.group(1)) if m_fail else 0
    # control del clasificador: tiene que haber una línea por cada falla; si no, SIN DATO
    if n_fail != len(tipos):
        no_assert = ["SIN DATO: %d fallas, %d líneas parseadas" % (n_fail, len(tipos))]
    if o.returncode == 0:
        est = "NO ATRAPADA (prueba verde)"
    elif no_assert:
        est = f"CAIDA ({len(no_assert)} fallas con excepción distinta de AssertionError)"
    else:
        est = f"ATRAPADA por aserción ({len(fallas)} fallas)"
    shutil.rmtree(d)
    return est, (txt.strip().splitlines() or [""])[-1]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for n, (v, nu) in MUT.items():
        est, ult = correr(n, v, nu)
        print(f"{n:26s} | {est} | {ult}", flush=True)


if __name__ == "__main__":
    main()
