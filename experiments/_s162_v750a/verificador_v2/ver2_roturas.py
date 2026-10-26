# -*- coding: utf-8 -*-
"""Segunda vuelta del verificador (V750-A): roturas de una línea propias, en copias `_v2_<id>_evaluar_v750a.py`
que viven en la carpeta del analizador (mismas rutas) y se borran al terminar. Cada rotura corre un subconjunto de
escenarios del autor (--escenarios) y, aparte, los escenarios propios de ver2_casos.py (--casos). Una rotura cuenta
como atrapada sólo si hay una falla por aserción y ninguna caída (rc 1 de la batería; rc 2 es caída).
Uso: python ver2_roturas.py --dest <tmp> --evaluador <evaluar_d25.py> [--solo R1,R2]"""
import argparse
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CARPETA = AQUI.parent
ORIGINAL = CARPETA / "evaluar_v750a.py"
PRUEBAS = CARPETA / "probar_evaluar_v750a.py"
CASOS = AQUI / "ver2_casos.py"

ROTURAS = {
    # (qué rompe, línea vieja, línea nueva, escenarios del autor que deberían atraparla, casos propios que la atrapan)
    "R1": ("L4: los bordes 0,9 y 1,1 quedan FUERA de la banda (§6.2 dice bordes incluidos)",
           "if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):",
           "if rz is None or not (BANDA_RAZON[0] < rz < BANDA_RAZON[1]):",
           "E00,E06,E31,E32,E33,E48", "C1,C2"),
    "R2": ("L18: K = producción deja de aplicarse en la fase sombra",
           "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot",
           "k_ok = (not censo) or (len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot)",
           "E14,E18,E19,E20,E21,E23,E28,E47,E49,E50,E52", "C5,C7"),
    "R3": ("L18: «ninguna protegida» mira sólo la tabla (una protegida sólo del OCR con K distinto no cierra)",
           'k_dist_prot = [nombre(i) for i in k_dist if obj[i].get("protegida")]',
           "k_dist_prot = [nombre(i) for i in k_dist if prot_tabla(obj[i])]",
           "E14,E28,E50,E52", "C4"),
    "R4": ("L18 y §6.1: la pasada con K distinto sale también de la equivalencia del runner (lo que el texto dice)",
           "        for i in oks0:\n            p, o_ = res[i][\"paquete\"][\"P\"], res[i][\"paquete\"][\"O\"]",
           "        for i in oks:\n            p, o_ = res[i][\"paquete\"][\"P\"], res[i][\"paquete\"][\"O\"]",
           "E08,E09,E27,E28", "C10"),
    "R5": ("L4: la razón vacía (ninguna protegida publicada por P) cumple",
           "if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):",
           "if rz is not None and not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):",
           "E00,E01,E06,E31,E44", "C8"),
    "R6": ("L7: la diferencia sin explicar deja de cerrar (el control siempre pasa)",
           'ctrl["placebo (publicación)"] = not pl_dist', 'ctrl["placebo (publicación)"] = True',
           "E00,E30", "C3,C9"),
    "R7": ("L7: t_max ausente cuenta como frío (explicada)",
           '(rec_k(i, "K").get("t_max_k") or 1e9) < TMAX_FILTROS_ARTEFACTO]',
           '(rec_k(i, "K").get("t_max_k") or 0) < TMAX_FILTROS_ARTEFACTO]',
           "E00,E30", "C3"),
    "R8": ("L18: el 1 % se calcula sobre las pasadas que quedan (circular: con pocas, nunca cierra)",
           "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot",
           "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(obj)) and not k_dist_prot",
           "E14,E28,E50,E52", "C5"),
}


def correr(dest, evaluador, nombre):
    que, viejo, nuevo, escs, casos = ROTURAS[nombre]
    copia = CARPETA / f"_v2_{nombre}_evaluar_v750a.py"
    src = ORIGINAL.read_text(encoding="utf-8")
    assert src.count(viejo) == 1, (nombre, src.count(viejo))
    copia.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    out = []
    try:
        for etq, script, sel in (("autor", PRUEBAS, escs), ("propios", CASOS, casos)):
            sal = dest / f"rot_{nombre}_{etq}"
            o = subprocess.run([sys.executable, str(script), "--dest", str(sal), "--analizador", str(copia),
                                "--evaluador", str(evaluador), "--solo", sel], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=7200, cwd=str(CARPETA))
            txt = o.stdout + o.stderr
            linea = next((x for x in txt.splitlines() if x.startswith("== ")), "(sin línea de resumen)")
            fallan = [x.split(" | ")[0] for x in txt.splitlines() if " | FALLA" in x]
            caen = [x.split(" | ")[0] for x in txt.splitlines() if " | CAÍDA" in x]
            est = "CAÍDA" if o.returncode == 2 or caen else ("ATRAPADA" if o.returncode == 1 else "PASA")
            out.append(f"{nombre} [{etq} {sel}] | {est} | rc {o.returncode} | {linea} | fallan {fallan} caen {caen}")
    finally:
        copia.unlink()
    return que, out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    a.dest.mkdir(parents=True, exist_ok=True)
    sel = [x for x in a.solo.split(",") if x] or list(ROTURAS)
    L = []
    for nom in sel:
        que, out = correr(a.dest, a.evaluador, nom)
        L.append(f"{nom}: {que}")
        L += out
        print("\n".join([f"{nom}: {que}"] + out), flush=True)
    (a.dest / "roturas_v2_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
