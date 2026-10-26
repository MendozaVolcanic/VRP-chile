# -*- coding: utf-8 -*-
"""Verificador v3 (tercera vuelta, delta v2 a v3): mide el NULO de la batería sellada `bateria_regla_v750b.py`.

POR QUÉ. La batería dice que comprueba sola 11 escenarios y sale 1 si alguno no coincide. Eso sólo vale si una regla
rota la hace salir 1. Acá se copia el árbol de prueba entero, se rompe a mano UNA línea de `analizar_v750b.py` por
mutación (reemplazo exacto, exigiendo una sola coincidencia), se corre la batería sin tocarla, y se anota si la
atrapó (rc 1) o si sobrevivió (rc 0). Una mutación que sobrevive es una parte de la regla que la batería no mide.

Las dos preguntas del instrumento: (1) si la batería estuviera rota (siempre verde), TODAS las mutaciones
sobrevivirían; el control positivo es M6 (la bandera de pruebas abriendo la cobertura), que la propia batería declaró
haber atrapado en la v3. (2) Si el analizador mutado no corre (SyntaxError), la batería lo registra como SIN DATO en
cada escenario (ROI=None) y los escenarios con veredicto esperado FALLAN: también sale 1, pero por otra razón; por eso
se guarda el stdout entero y se mira la causa, no sólo el rc.

Uso: python mutar_v3.py --arbol <árbol limpio> --dest <carpeta de salida> [--solo M1,M5]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MUTACIONES = {
    # nombre: (qué rompe, texto viejo, texto nuevo, escenario que debería atraparla según la batería)
    "M1": ("no_peor: SIN SUSTRATO siempre es «no peor», sin mirar el neto (vuelve a la v2; VB2-02)",
           'return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO" and neto <= 0)',
           'return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO")',
           "V3"),
    "M2": ("§6.2 ganan: se quita la condición «no peor con la tabla sola»",
           'ver[(b, "TO", "decide")][1] == "GANA" and no_peor(b, "tabla")]',
           'ver[(b, "TO", "decide")][1] == "GANA"]',
           "ninguno conocido"),
    "M3": ("§6.3 cand: se quita «no peor en el canal que decide» (queda sólo la tabla sola)",
           '(b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]',
           '(b == "B1" or no_peor(b, "tabla"))]',
           "ninguno conocido"),
    "M4": ("§6.3 cand: se quita «no peor con la tabla sola» (vuelve a la v2; VB2-01)",
           '(b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]',
           '(b == "B1" or no_peor(b, "decide"))]',
           "V1"),
    "M5": ("VB2-07: las pasadas sin gránulo no se leen (sin_g siempre vacío)",
           'sin_g = json.loads(sg.read_text(encoding="utf-8")) if sg.exists() else []',
           'sin_g = []',
           "ninguno conocido"),
    "M6": ("CONTROL POSITIVO: la cobertura siempre pasa (el defecto que la batería v3 declaró haber atrapado)",
           'cob_pasa = cob_ok or bool(a.leer_con_faltantes)',
           'cob_pasa = True',
           "E3"),
    "M7": ("§6.2: entre los que ganan se elige el de MAYOR E",
           'elegido = min(ganan, key=lambda b: ver[(b, "TO", "decide")][2])',
           'elegido = max(ganan, key=lambda b: ver[(b, "TO", "decide")][2])',
           "E5"),
    "M8": ("control positivo: se quita la exigencia de que B1 publique 3 o más (VB2-06)",
           'and len(pcc) >= 1 and len(pcc_b1) >= 3',
           'and len(pcc) >= 1',
           "V6"),
    "M9": ("cobertura: una protegida SIN DATO ya no frena la lectura (queda sólo el 2 %)",
           'max(1, len(obj) + len(sin_g) - no_obs["fuera"]) and not prot_sin',
           'max(1, len(obj) + len(sin_g) - no_obs["fuera"])',
           "E3 (sólo si el 2 % no la tapa)"),
    "M10": ("compuerta: K = producción deja de cerrar la compuerta",
            'gen_ok = bool(nidx) and c_nulo == 0 and k_ok',
            'gen_ok = bool(nidx) and c_nulo == 0',
            "ninguno conocido"),
    "M11": ("etiqueta: la marca «SIN CENSO» no se escribe en la línea de la ROI",
            'pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo})")',
            'pr(f"== §6 ROI elegida: {elegido} ({motivo})")',
            "todos los que tienen veredicto"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    base = Path(a.arbol)
    nombres = [n for n in MUTACIONES if not a.solo or n in a.solo.split(",")]
    a.dest.mkdir(parents=True, exist_ok=True)
    resumen = []
    for n in nombres:
        desc, viejo, nuevo, atrapa = MUTACIONES[n]
        arbol = a.dest / f"arbol_{n}"
        if arbol.exists():
            shutil.rmtree(arbol)
        shutil.copytree(base, arbol)
        f = arbol / "experiments/_s162_v750b/analizar_v750b.py"
        src = f.read_text(encoding="utf-8")
        assert src.count(viejo) == 1, f"{n}: el texto viejo aparece {src.count(viejo)} veces, no 1"
        f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
        assert f.read_text(encoding="utf-8").count(nuevo) >= 1
        # el analizador mutado tiene que compilar: si no, la batería falla por otra razón (pregunta 2)
        comp = subprocess.run([sys.executable, "-m", "py_compile", str(f)], capture_output=True, text=True)
        assert comp.returncode == 0, f"{n}: el mutante no compila: {comp.stderr}"
        o = subprocess.run([sys.executable, str(arbol / "experiments/_s162_v750b/bateria_regla_v750b.py"),
                            "--arbol", str(arbol), "--dest", str(a.dest / f"bat_{n}")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=str(arbol / "experiments/_s162_v750b"), timeout=1800,
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        txt = o.stdout + o.stderr
        (a.dest / f"bat_{n}_stdout.txt").write_text(txt, encoding="utf-8")
        ultima = [l for l in txt.splitlines() if l.startswith("== BATER")]
        veredicto = "ATRAPADA" if o.returncode == 1 else ("SOBREVIVE" if o.returncode == 0 else f"rc {o.returncode}")
        fila = f"{n} | {veredicto} | esperaba atraparla: {atrapa} | {desc} | {ultima[-1] if ultima else 'SIN LÍNEA FINAL'}"
        print(fila, flush=True)
        resumen.append(fila)
        shutil.rmtree(arbol, ignore_errors=True)
    (a.dest / "resumen_mutaciones.txt").write_text("\n".join(resumen) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
