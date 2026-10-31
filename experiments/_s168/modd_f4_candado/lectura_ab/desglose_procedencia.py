# -*- coding: utf-8 -*-
"""S170: desglose completo del control de procedencia de la lectura del A/B (resultado_f4.json sólo lista 30 de los
malos). Repite externos_f4.procedencia con los mismos insumos que leer_f4 y cuenta por motivo. Sólo informa.
Uso: python desglose_procedencia.py <carpeta del artefacto> <tag>"""
import sys
from collections import Counter
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments/_s166_modd_f4"))
sys.stdout.reconfigure(encoding="utf-8")
import evaluar_f4 as E  # noqa: E402
import externos_f4 as X  # noqa: E402
art, tag = sys.argv[1], sys.argv[2]
_f, cab = E.cargar(art)
commit_tag = X.git("rev-parse", f"{tag}^{{commit}}", raiz=RAIZ).strip()
p = X.procedencia(cab, art, commit_tag, tag, X.sha_archivo(RAIZ / X.REL_EVALUAR), X.sha_archivo(RAIZ / X.REL_PROBE))
print("tag", tag, "commit", commit_tag[:9], "| cabeceras", len(cab), "| malos", p["n_malos"])
print("por motivo:", dict(Counter(m["motivo"] for m in X.procedencia(cab, art, commit_tag, tag,
      X.sha_archivo(RAIZ / X.REL_EVALUAR), X.sha_archivo(RAIZ / X.REL_PROBE))["malos"])) if p["n_malos"] <= 30 else "")
print("commits de las cabeceras:", dict(Counter(c.get("commit") for c in cab)))
print("tags de las cabeceras:", dict(Counter(c.get("tag") for c in cab)))
print("sha256_evaluar_f4 de las cabeceras:", dict(Counter(c.get("sha256_evaluar_f4") for c in cab)), "| lectura", p["sha256_evaluar_f4_lectura"])
print("sha256_probe_f4 de las cabeceras:", dict(Counter(c.get("sha256_probe_f4") for c in cab)), "| lectura", p["sha256_probe_f4_lectura"])
print("procedencia_*.txt:", len(list(Path(art).glob("**/procedencia_*.txt"))))
