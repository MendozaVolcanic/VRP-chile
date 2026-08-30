# -*- coding: utf-8 -*-
"""S127 — campos que el pipeline ESCRIBE vs campos que los consumidores LEEN.

POR QUE: las dos direcciones fallan distinto y las dos ya mordieron.

  · LEIDO PERO NUNCA ESCRITO — la peor. En Python y en JS un campo ausente no da
    error: da `None` / `undefined`, que aguas abajo se lee como "cero" o "no hay
    anomalia". Es el modo de falla de A7 (campos que se calculaban y no se
    retornaban) y de la propia regla A7, que S125 tuvo que marcar OBSOLETA porque
    los tres campos que citaba -`std_bg_i04`, `threshold_mir`, `nti_std`- ya no
    existen en ningun record.

  · ESCRITO PERO NUNCA LEIDO — mas barato, pero engorda el schema y da la
    impresion de que algo se esta usando. El caso F47/A46 nacio de dos
    representaciones del mismo concepto donde los gates leian la que no era.

Fuente de lo ESCRITO: los records reales de `data/mirova_equivalent/`, no el codigo
-- asi se ve el schema efectivo y no el pretendido.
Fuente de lo LEIDO: las 3 vistas del frontend, audit_metrics, store y scripts/.

Persiste en 03_escrito_vs_leido.json.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# ── lo ESCRITO: schema efectivo, muestreado de los records reales ──────────────
escritos = collections.Counter()
n_records = 0
for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
    recs = json.load(io.open(f, encoding="utf-8")).get("records", [])
    for r in recs:
        n_records += 1
        for k, v in r.items():
            escritos[k] += 1
            if k == "primary_cluster" and isinstance(v, dict):
                for kk in v:
                    escritos["primary_cluster." + kk] += 1

# ── lo LEIDO: cualquier mencion textual del nombre del campo en un consumidor ──
CONSUMIDORES = (
    glob.glob(os.path.join(ROOT, "frontend", "*.html"))
    + glob.glob(os.path.join(ROOT, "pipeline", "*.py"))
    + glob.glob(os.path.join(ROOT, "scripts", "*.py"))
)
texto_consumidores = {}
for p in CONSUMIDORES:
    texto_consumidores[os.path.relpath(p, ROOT).replace("\\", "/")] = io.open(
        p, encoding="utf-8", errors="replace").read()


def quien_lo_lee(campo):
    hoja = campo.split(".")[-1]
    # se exige el nombre como token, para no matchear subcadenas
    pat = re.compile(r"[\"'\[\.\b]%s[\"'\]\b]" % re.escape(hoja))
    return [n for n, t in texto_consumidores.items() if pat.search(t)]


# ── lo LEIDO pero quizas no escrito: nombres citados entre comillas en el frontend
#    y en audit_metrics que parecen campos de record ─────────────────────────────
CANDIDATOS_LECTURA = set()
for n, t in texto_consumidores.items():
    if not (n.startswith("frontend/") or n.endswith("audit_metrics.py")):
        continue
    for m in re.finditer(r"""(?:r|rec|record|d|pc)(?:\.|\[["'])([a-z][a-z0-9_]{3,})""", t):
        CANDIDATOS_LECTURA.add(m.group(1))
    for m in re.finditer(r"""\.get\(\s*["']([a-z][a-z0-9_]{3,})["']""", t):
        CANDIDATOS_LECTURA.add(m.group(1))

campos_escritos = set(escritos) | {c.split(".")[-1] for c in escritos}
huerfanos_lectura = sorted(c for c in CANDIDATOS_LECTURA if c not in campos_escritos)

print("ESCRITO vs LEIDO — S127")
print("=" * 80)
print("records inspeccionados: %d   campos distintos escritos: %d\n"
      % (n_records, len(escritos)))

print("A) ESCRITOS QUE NINGUN CONSUMIDOR LEE")
print("-" * 80)
sin_lector = []
for campo, n in sorted(escritos.items(), key=lambda kv: -kv[1]):
    lectores = quien_lo_lee(campo)
    if not lectores:
        sin_lector.append({"campo": campo, "records": n})
        print("  %-42s en %6d records" % (campo, n))
if not sin_lector:
    print("  ninguno")

print("\nB) NOMBRES QUE UN CONSUMIDOR PARECE LEER Y NINGUN RECORD ESCRIBE")
print("-" * 80)
print("  (heuristico: `x.campo` / `.get('campo')` en frontend y audit_metrics)")
for c in huerfanos_lectura:
    donde = [n for n, t in texto_consumidores.items()
             if (n.startswith("frontend/") or n.endswith("audit_metrics.py"))
             and re.search(r"""(?:\.|\[["'])%s\b""" % re.escape(c), t)]
    print("  %-42s citado en %s" % (c, ", ".join(os.path.basename(d) for d in donde[:3])))
if not huerfanos_lectura:
    print("  ninguno")

res = {"n_records": n_records,
       "campos_escritos": {k: v for k, v in escritos.items()},
       "escritos_sin_lector": sin_lector,
       "leidos_sin_escritor": huerfanos_lectura}
dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "03_escrito_vs_leido.json")
json.dump(res, io.open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", os.path.relpath(dest, ROOT).replace("\\", "/"))
