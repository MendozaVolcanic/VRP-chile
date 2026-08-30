# -*- coding: utf-8 -*-
"""S127 — inventario de afirmaciones que el codigo hace sobre su propio estado.

POR QUE: S126 encontro doce casos donde algo afirmaba una cosa sobre el sistema y era
falso — el comentario del PR #535 decia "no-op" y apago la mascara de nube en
produccion; el docstring de single_pixel_mode dice "Volcanes NO afectados ... Lascar" y
esta activo en 110/110 records de Lascar. Los dos costaron sesiones.

No se puede verificar automaticamente si una afirmacion es cierta. Si se puede LISTARLAS
todas para revisarlas de a una, que es lo que nunca se hizo. Este barrido es el
inventario; la verificacion de cada linea es manual y va al informe.

Plan: docs/superpowers/plans/2026-08-30-auditoria-s127.md, Fase 1 Task 1.
Persiste en 01_afirmaciones_de_estado.json.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# Frases que afirman estado del sistema. Cada clase costo al menos un incidente real.
PATRONES = [
    (r"\bno[- ]?op\b", "afirma que algo no tiene efecto"),
    (r"NO afectad|no afecta a", "afirma que algo no aplica a cierto caso"),
    (r"\bremovid|se removio|ya no (se )?(usa|aplica|corre|existe)",
     "afirma que algo se quito"),
    (r"codigo muerto|dead code|nunca (se )?(llama|corre|dispara|usa)",
     "afirma que algo no corre"),
    (r"s[oó]lo (afecta|aplica|toca|corre|se usa)", "acota el alcance de algo"),
    (r"por defecto (est[aá] |queda )?(OFF|apagad)|flag-?off default",
     "afirma un default"),
    (r"id[eé]ntico|byte a byte|no cambia (nada|el resultado|el comportamiento)",
     "afirma equivalencia"),
    (r"(ya|siempre) (est[aá]|esta) (garantizad|cubiert|resuelt)",
     "afirma que algo ya esta resuelto"),
]
EXT = (".py", ".yaml", ".yml")
SALTAR = ("/.git/", "/_archive/", "/node_modules/", "/__pycache__/",
          "/experiments/", "/data/")

# El barrido mira lineas de COMENTARIO o de docstring. Heuristica deliberadamente
# amplia: preferimos revisar de mas a que se escape una afirmacion falsa.
ES_PROSA = re.compile(r"^\s*#|^\s*\"\"\"|^\s*'''|#\s|\"\"\"|'''")


def barrer():
    out = []
    for base, dirs, files in os.walk(ROOT):
        rel = base.replace("\\", "/") + "/"
        if any(s in rel for s in SALTAR):
            dirs[:] = []
            continue
        for f in sorted(files):
            if not f.endswith(EXT):
                continue
            p = os.path.join(base, f)
            try:
                lineas = io.open(p, encoding="utf-8",
                                 errors="replace").read().splitlines()
            except OSError:
                continue
            for n, linea in enumerate(lineas, 1):
                if not ES_PROSA.search(linea):
                    continue
                for pat, clase in PATRONES:
                    if re.search(pat, linea, re.I):
                        out.append({
                            "archivo": os.path.relpath(p, ROOT).replace("\\", "/"),
                            "linea": n,
                            "clase": clase,
                            "texto": linea.strip()[:180],
                        })
                        break
    return out


hallazgos = barrer()

# Los de `pipeline/` y `.github/` son los que pueden costar una sesion: ahi una
# afirmacion falsa dirige una decision operacional. El resto es contexto.
CRITICO = ("pipeline/", ".github/")
criticos = [h for h in hallazgos if h["archivo"].startswith(CRITICO)]

print("AFIRMACIONES DE ESTADO — inventario S127")
print("=" * 78)
print("total: %d   en pipeline/ y .github/: %d\n" % (len(hallazgos), len(criticos)))

por_clase = {}
for h in hallazgos:
    por_clase.setdefault(h["clase"], []).append(h)
print("%-46s %8s %10s" % ("clase de afirmacion", "total", "criticos"))
for clase in sorted(por_clase, key=lambda c: -len(por_clase[c])):
    ncrit = sum(1 for h in por_clase[clase] if h["archivo"].startswith(CRITICO))
    print("%-46s %8d %10d" % (clase[:46], len(por_clase[clase]), ncrit))

print("\n" + "-" * 78)
print("A REVISAR UNA POR UNA (pipeline/ y .github/):\n")
for h in criticos:
    print("  %s:%d" % (h["archivo"], h["linea"]))
    print("      [%s] %s" % (h["clase"], h["texto"]))

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "01_afirmaciones_de_estado.json")
json.dump({"total": len(hallazgos), "criticos": len(criticos),
           "por_clase": {c: len(v) for c, v in por_clase.items()},
           "hallazgos": hallazgos},
          io.open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", os.path.relpath(dest, ROOT).replace("\\", "/"))
