# -*- coding: utf-8 -*-
"""Frente 4 S155: censo de cierres EXTENDIDO y etiquetado por dependencia del detector K.

Reusa los detectores de experiments/_s145_censo_cierres/censo.py (importados, no copiados:
si alguien rompe aquel, este hereda la rotura y su control lo ve) y agrega:
  - mas documentos (tasks/backlog_*.md y experiments/*/README.md),
  - mas palabras de cierre (inerte, sin efecto, sin beneficio, no aplica...),
  - una etiqueta de DEPENDENCIA de lo que K cambio (Test 1, conectiva, banda MODIS),
  - la sesion mas alta citada en la ventana (proxy de cuando se midio; >=S153 puede ser K).
NO juzga: inventaria para triage manual. No escribe fuera de esta carpeta.

PREGUNTA 1: un cierre redactado sin las palabras clave NO aparece; el censo es un PISO.
Una dependencia de K redactada sin nombrar Test 1 / conectiva / banda tampoco: piso tambien.
PREGUNTA 2: control de instrumento heredado (tres sinteticos) MAS uno propio para la etiqueta
de dependencia: un texto con 'Test 1 integrado' debe salir dep_test1, uno sin nada no.
"""
import io, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "_s145_censo_cierres"))
import censo as C  # noqa: E402

EXTRA_PATRONES = [
    ("inerte", r"\binerte\b|\bsin efecto\b|\bsin beneficio\b|\bno cambia nada\b"),
    ("descartado", r"\bdescartad[oa]s?\b|\bDESCARTAD[OA]\b"),
    ("obsoleta", r"\bOBSOLET[OA]\b"),
]
DEP = [
    ("dep_test1", r"Test ?1|test1|TEST1|keep_peak|ctxpeak|K1\b|integrad[oa] en el ROI"),
    ("dep_conectiva", r"conectiva|\bmin\(|rama OR|prose|`min`|\bbajo `?min`?|\bmax\b"),
    ("dep_banda", r"banda 2[12]|B2[12]\b|b2[12]_primary|D21\b"),
]
def tipos(l):
    t = C.tipos_de_cierre(l)
    t += [n for n, rx in EXTRA_PATRONES if re.search(rx, l)]
    return t
def deps(v):
    return [n for n, rx in DEP if re.search(rx, v)]
def ses_max(v):
    s = [int(x) for x in re.findall(r"\bS(\d{2,3})\b", v)]
    return max(s) if s else None

docs = list(C.DOCS) + [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT/"tasks").glob("backlog_*.md"))]
docs += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT/"experiments").glob("*/README.md"))]

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    filas = []
    for rel in docs:
        p = ROOT / rel
        lin = p.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, l in enumerate(lin):
            t = tipos(l)
            if not t:
                continue
            v = C.contexto(lin, i, antes=2, despues=4)
            filas.append({"archivo": rel, "linea": i+1, "tipos": t, "deps_K": deps(v),
                          "sesion_max": ses_max(v), "respaldos": C.respaldos_citados(v),
                          "texto": l.strip()[:260]})
    ok = (set(tipos("queda CERRADA y no reabrir; inerte")) >= {"cerrada","no_reabrir","inerte"}
          and tipos("El anillo mide 5 a 25 km.") == []
          and "dep_test1" in deps("con el Test 1 integrado encendido") and deps("anillo de 5 km") == []
          and len(filas) > 0)
    conK = [f for f in filas if f["deps_K"]]
    preK = [f for f in conK if (f["sesion_max"] or 0) < 153]
    out = {"control_ok": ok, "docs": docs, "n": len(filas), "n_dep_K": len(conK),
           "n_dep_K_sesion_lt_153": len(preK), "filas": filas}
    (HERE/"censo_k.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print("control_ok", ok, "| docs", len(docs), "| cierres", len(filas), "| con dependencia K", len(conK),
          "| de esos con sesion max < S153", len(preK))
    print("por archivo (con dep K):", Counter(f["archivo"] for f in conK).most_common(12))
    print("por dep:", Counter(d for f in conK for d in f["deps_K"]))
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
