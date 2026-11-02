# -*- coding: utf-8 -*-
"""S173 F2 (b): ¿A, B o #932 cambian el régimen (S8) o el sello (S0) del lector re-sellado de V375-E?

Usa las funciones del propio lector, tal como están en el tag s172-v375e-lector-resellado (fc3912cb2): se carga la copia
extraída con `git show` (lector_fc3912cb2.py, mismo contenido) y se llama `cambio_significativo(ruta, viejo, nuevo)` con
los textos reales de cada archivo de RUTAS_REGIMEN que cambia entre main (a3c5a9b49) y cada combinación (árboles de
git merge-tree, ver sim_merges_salida.txt). Es la misma función que el lector aplica a cada codigo_sha de los records.

Pregunta 1 (si lo medido estuviera roto, ¿se vería?): si A, B o #932 tocaran algo que el lector cuenta como régimen, la
  lista «significativos» no saldría vacía. Control positivo: una mutación de mirova_equivalent.yaml en una clave que NO
  está en CLAVES_PERFIL_OTRO_SENSOR (anomaly_k) y una entrada de un Tier A en grillas_mirova.yaml (x0) tienen que dar
  True; y una mutación sólo en enable_modis_codigo_mirova y una entrada nueva de un volcán fuera de los 11, False.
Pregunta 2 (instrumento muerto): si git no resolviera los árboles o el filtro de rutas no encontrara nada, se imprime
  el número de archivos candidatos; un 0 candidatos en una combinación que sí cambia pipeline/ sería sospechoso.
S0: compara el sha256 LF de los archivos del sello contra el árbol de cada combinación, para mostrar qué pasaría si el
  lector se corriera desde main y no desde el checkout de su tag.
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parent
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
spec = importlib.util.spec_from_file_location("lector", F / "lector_fc3912cb2.py")
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

ARBOLES = {"main (a3c5a9b49)": "a3c5a9b49",
           "A": "9af3a621b8a130f69cea1bb22c597436d18210b4",
           "A+B": "dc36546d11f7bf623fa97229e431f730af0b64c9",
           "A+#932": "255163095061da6407652965c21bef80c0417a05",
           "A+B+#932": "a4ce2182a4ecc19b155abadac666be0f518e2111",
           "tag lector fc3912cb2": "fc3912cb2"}


def git(*a):
    p = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, p.stdout


def show(rev, ruta):
    rc, out = git("show", f"{rev}:{ruta}")
    return out if rc == 0 else None


def main():
    print(f"lector cargado: RUTAS_REGIMEN={L.RUTAS_REGIMEN}")
    print(f"PERFILES_REGIMEN={L.PERFILES_REGIMEN}; VOLCANES_GRILLA_REGIMEN={len(L.VOLCANES_GRILLA_REGIMEN)}")
    base = "a3c5a9b49"
    for nom, rev in ARBOLES.items():
        if rev == base:
            continue
        rc, out = git("diff", "--name-only", base, rev, "--", *L.RUTAS_REGIMEN)
        cands = [x for x in out.splitlines() if x.strip()]
        sig = [r for r in cands if L.cambio_significativo(r, show(base, r), show(rev, r))]
        print(f"\n== {nom}: {len(cands)} archivos de RUTAS_REGIMEN cambian contra main; significativos para S8: {sig}")
        for r in cands:
            print(f"   {r}: {'SIGNIFICATIVO' if r in sig else 'no cuenta'}")
    # controles positivos y negativos con textos reales
    me = show(base, "pipeline/profiles/mirova_equivalent.yaml")
    gr = show("28183712a", "pipeline/grillas_mirova.yaml")
    gr_main = show(base, "pipeline/grillas_mirova.yaml")
    ctl = {
        "POS perfil: anomaly_k cambiado": L.cambio_significativo("pipeline/profiles/mirova_equivalent.yaml", me,
                                                                  me.replace("thresholds:", "thresholds:\n  anomaly_k: 99.0", 1)),
        "NEG perfil: sólo enable_modis_codigo_mirova": L.cambio_significativo(
            "pipeline/profiles/mirova_equivalent.yaml", me,
            me.replace("thresholds:", "thresholds:\n  enable_modis_codigo_mirova: true", 1)),
        "POS grilla: x0 de Lascar +1 m": None,
        "NEG grilla: las 34 de #932 agregadas": L.cambio_significativo("pipeline/grillas_mirova.yaml", gr_main, gr),
        "POS .py: una línea de código en process_modis.py": L.cambio_significativo(
            "pipeline/process_modis.py", show(base, "pipeline/process_modis.py"),
            show(base, "pipeline/process_modis.py") + "\nX_CONTROL = 1\n"),
        "NEG .py: un comentario en process_modis.py": L.cambio_significativo(
            "pipeline/process_modis.py", show(base, "pipeline/process_modis.py"),
            show(base, "pipeline/process_modis.py") + "\n# comentario de control\n"),
    }
    import re
    m = re.search(r"(  Lascar:\s*\{[^}]*x0: )([0-9.]+)", gr_main)
    if m:
        mut = gr_main[:m.start(2)] + str(float(m.group(2)) + 1) + gr_main[m.end(2):]
        ctl["POS grilla: x0 de Lascar +1 m"] = L.cambio_significativo("pipeline/grillas_mirova.yaml", gr_main, mut)
    print("\n== controles (POS debe dar True, NEG debe dar False)")
    for k, v in ctl.items():
        print(f"   {k}: {v}")
    # S0: sha256 LF de los archivos del sello en cada árbol
    print("\n== S0: sha256 LF de los 16 archivos del sello, por árbol (OK = igual al sellado)")
    sello = {**{str(p.relative_to(L.RAIZ)).replace('\\', '/'): h for p, h in L.SHA_DEPS.items()},
             **{str(p.relative_to(L.RAIZ)).replace('\\', '/'): h for p, h in L.SHA_SELLO_LECTOR.items()}}
    for nom, rev in ARBOLES.items():
        malos = []
        for ruta, h in sello.items():
            t = show(rev, ruta)
            if t is None:
                malos.append(f"{ruta} (no existe)")
                continue
            if hashlib.sha256(t.replace("\r\n", "\n").encode("utf-8")).hexdigest() != h:
                malos.append(ruta)
        print(f"   {nom}: {16 - len(malos)} de 16 OK; distintos: {malos}")


if __name__ == "__main__":
    main()
