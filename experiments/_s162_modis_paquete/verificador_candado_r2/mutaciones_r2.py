# -*- coding: utf-8 -*-
"""Mutaciones propias de la segunda vuelta (sobre copia, fuera del candado), con el mismo criterio S156 que
mutar_evaluar_paquete.py: atrapada = al menos una prueba FALLA por asercion. Se corren contra la bateria del candado
(probar_evaluar_paquete.py) y contra las pruebas extra de esta vuelta (pruebas_extra_r2.py).
Uso: python -I -B mutaciones_r2.py [nombres...]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CANDADO = AQUI.parent
FUENTE = CANDADO / "evaluar_paquete.py"

MUTACIONES = {
    # la regla (b) evaluada ANTES del veto de P1 (un P1 veto + protegida fuera daria DECIDE NICOLAS, no NO CANDIDATO)
    "m1_prot_antes_que_p1": (
        '    if b["p1"]["estado"] == "VETADO":\n        return "NO CANDIDATO"\n',
        '    if [p for p in res["controles"]["cobertura"].get("protegidas_fuera_del_denominador", []) if p.get("k_publica")]:\n'
        '        return "DECIDE NICOLÁS"\n    if b["p1"]["estado"] == "VETADO":\n        return "NO CANDIDATO"\n'),
    # la lista de "protegidas fuera" toma toda etiqueta (bajo1 y negativos con K publicando mandarian a DECIDE)
    "m2_fuera_toda_etiqueta": (
        'if not f["_evaluable"] and f.get("lab") == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]',
        'if not f["_evaluable"] and f["_motivo"] in MOTIVOS_SELLADOS]'),
    # la procedencia deja de exigir el commit del tag
    "m4_procedencia_sin_commit": (
        'ok_commit = bool(commit_esperado) and len(commits) == 1 and str(commits[0]).startswith(commit_esperado)',
        'ok_commit = len(commits) == 1'),
    # el evaluador deja de comprobar el manifiesto
    "m5_manifiesto_ignorado": (
        '    ext["manifiesto"] = MC.comprobar()',
        '    ext["manifiesto"] = {"estado": "OK"}'),
}


def correr(script, modulo, salida_json):
    env = dict(os.environ, MODD_RAIZ=str(CANDADO.parents[1]), VRP_PROFILE="mirova_equivalent")
    args = [sys.executable, "-I", "-B", str(script), "--modulo", str(modulo)]
    if salida_json is not None:
        args += ["--json", str(salida_json)]
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    res = None
    if salida_json is not None and Path(salida_json).exists():
        res = json.loads(Path(salida_json).read_text(encoding="utf-8"))
    return res, p.stdout, p.returncode


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    solo = set(sys.argv[1:])
    src = FUENTE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for nombre, (viejo, nuevo) in MUTACIONES.items():
            if solo and nombre not in solo:
                continue
            assert src.count(viejo) == 1, "%s: el texto aparece %d veces" % (nombre, src.count(viejo))
            mut = td / ("mut_" + nombre)
            mut.mkdir()
            for a in ("evaluar_d25_ded217af4.py", "grillas.json"):
                shutil.copy2(CANDADO / a, mut / a)
            (mut / "evaluar_paquete.py").write_text(src.replace(viejo, nuevo), encoding="utf-8")
            # contra la bateria del candado
            r, _out, _rc = correr(CANDADO / "probar_evaluar_paquete.py", mut / "evaluar_paquete.py", mut / "r.json")
            fallan = [k for k, v in (r or {}).items() if v == "falla"]
            caen = [k for k, v in (r or {}).items() if v == "cae"]
            bat = ("ATRAPADA por " + ", ".join(fallan[:4])) if fallan else ("CAE %s" % caen if caen else "VIVA")
            # contra las pruebas extra de esta vuelta
            _r2, out2, rc2 = correr(AQUI / "pruebas_extra_r2.py", mut / "evaluar_paquete.py", None)
            fallan2 = [l.split()[1].rstrip(":") for l in out2.splitlines() if l.strip().startswith("FALLA ")]
            caen2 = [l.split()[1].rstrip(":") for l in out2.splitlines() if l.strip().startswith("CAE ")]
            ext = ("ATRAPADA por " + ", ".join(fallan2[:4])) if fallan2 else ("CAE %s" % caen2 if caen2 else "VIVA")
            print("  %-28s bateria del candado: %-60s | extra r2: %s" % (nombre, bat, ext), flush=True)


if __name__ == "__main__":
    main()
