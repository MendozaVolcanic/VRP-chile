# -*- coding: utf-8 -*-
"""Mutaciones a mano de la marca «cráter no medido»: cada una se aplica, se corre la prueba y se restaura.
Cuenta como atrapada sólo si pytest falla por una aserción (AssertionError / assert), no por una caída de carga.
Uso: python -B experiments/_s194_mir_perdido/mutar.py <raíz del worktree>"""
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
M = "frontend/crater_no_medido.js"
MUT = [
    ("M1 lee el total (bow-tie incluido) en vez del hueco", M, "entero(d.px_mir_hueco_crater)", "entero(d.px_mir_invalido_crater)"),
    ("M2 sin la marca de saturación", M, "const nSat = entero(d.px_saturados_crater);", "const nSat = 0;"),
    ("M3 sin la marca de barrido sin posición", M, "d.crater_sin_posicion === true;", "false;"),
    ("M4 marca también el bow-tie", M, "return (nMir || nSat || sinPosicion)", "return (nMir || nSat || sinPosicion || entero(d.px_bowtie_crater))"),
    ("M5 acepta valores negativos", M, "Number.isFinite(x) && x > 0) ? Math.round(x) : 0;", "Number.isFinite(x)) ? Math.round(x) : 0;"),
    ("M6 elige la más vieja", M, "if (!best || t > best.t)", "if (!best || t < best.t)"),
    ("M7 sin corte de fecha", M, "if (!(t >= desdeMs)) continue;", ""),
    ("M8 sin filtro de la vista", M, "if (filtro && !filtro(r)) continue;", ""),
    ("M9 cuenta la escena no medida como pasada", M, "if (r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio) continue;", ""),
    ("M10 escribe en el record", M, "const nMir = entero(d.px_mir_hueco_crater);", "const nMir = entero(d.px_mir_hueco_crater); r.marca = 1;"),
    ("M11 singular y plural cruzados", M, 'return n + " " + (n === 1 ? s : p);', 'return n + " " + (n !== 1 ? s : p);'),
    ("M12 index marca aunque no haya marca", "frontend/index.html",
     "  const m = CraterNoMedido.craterNoMedido(r);\n  if (!m) return null;\n", "  const m = CraterNoMedido.craterNoMedido(r) || {nMir: 1, nSat: 0, sinPosicion: false};\n"),
    ("M13 tarjeta exige detección", "frontend/index.html",
     "r => r._diurna !== true && isSensorVisible(r), parseUtcMs);", "r => r._diurna !== true && isSensorVisible(r) && r.vrp_mw > 0, parseUtcMs);"),
    ("M14 tarjeta calla con cualquier detección", "frontend/index.html",
     "if (!lc || (det && det.rec !== lc.rec && det.ts > lc.t)) return null;", "if (!lc || det) return null;"),
    ("M15 tarjeta acepta pasadas de día", "frontend/index.html",
     "r => r._diurna !== true && isSensorVisible(r), parseUtcMs);", "r => isSensorVisible(r), parseUtcMs);"),
    ("M16 tabla con una sola rama", "frontend/index.html",
     '\n          if (i === 2) { const mn = marcaCraterNoMedido("marca-crater-no-medido", r); if (mn) td.appendChild(mn); }   // S194: cráter no medido (C1-102)', ""),
    ("M17 popup sin la marca", "frontend/index.html", "popupAgua + popupCumbre + popupCrater", "popupAgua + popupCumbre"),
    ("M18 mosaico sin cargar el módulo", "frontend/mosaico.html", ' <script src="crater_no_medido.js"></script>', ""),
    ("M19 diario sin el conteo", "frontend/diario.html", "&& CraterNoMedido.craterNoMedido(r)).length", "&& true).length"),
    ("M20 texto con guion largo", M, '"cráter no medido: " + partes.join(", ")', '"cráter no medido" + String.fromCharCode(0x2014) + partes.join(", ")'),
]
atrapadas = 0
for nombre, archivo, viejo, nuevo in MUT:
    p = RAIZ / archivo
    orig = p.read_bytes()
    s = orig.decode("utf-8")
    if s.count(viejo) != 1:
        print(nombre, ": NO SE APLICÓ (", s.count(viejo), "apariciones )")
        continue
    p.write_bytes(s.replace(viejo, nuevo).encode("utf-8"))
    try:
        o = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "tests/test_tablero_crater_no_medido_s194.py"], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    finally:
        p.write_bytes(orig)
    falla = o.returncode != 0
    por_asercion = falla and ("AssertionError" in o.stdout or "assert " in o.stdout)
    atrapadas += por_asercion
    ult = [ln for ln in o.stdout.splitlines() if ln.startswith("FAILED")]
    print(f"{nombre}: {'ATRAPADA' if por_asercion else ('CAE SIN ASERCIÓN' if falla else 'NO ATRAPADA')} {ult[:2]}")
print("atrapadas por aserción:", atrapadas, "de", len(MUT))
