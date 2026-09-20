# -*- coding: utf-8 -*-
"""Frente G: arma docs/audit_s146/FRENTE_G_INVENTARIO_DE_CAMINOS.md desde la plantilla + la tabla generada.
Unico archivo que escribe fuera de esta carpeta (el entregable pedido)."""
import json, os, re, collections
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, "..", "..", ".."))
inv = json.load(open(os.path.join(here, "inventario.json"), encoding="utf-8"))
P = json.load(open(os.path.join(here, "perfil_efectivo.json"), encoding="utf-8"))
t = open(os.path.join(here, "plantilla_informe.md"), encoding="utf-8").read()
tabla = open(os.path.join(here, "tabla_inventario.md"), encoding="utf-8").read()
dep = inv["atributos_dependientes"]; n_dep = sum(len(v) for v in dep.values())
dep_md = "\n".join(f"  - {k}: " + ", ".join(f"`{a}` = {json.dumps(v, ensure_ascii=False)}" for a, v in d.items()) for k, d in dep.items())
cnt = collections.Counter(r["origen"] for r in inv["filas"])
t = (t.replace("{{TABLA}}", tabla).replace("{{DEPENDIENTES}}", dep_md)
       .replace("{{N_ATTR}}", str(len(P))).replace("{{N_DEP}}", str(n_dep)).replace("{{N_CITADOS}}", str(len(P) - n_dep))
       .replace("{{N_FILAS}}", str(len(inv["filas"]))).replace("{{CONTEO}}", "; ".join(f"{k}: {v}" for k, v in cnt.most_common())))
for a in re.findall(r"\{\{([A-Z0-9_]+)\}\}", t): t = t.replace("{{" + a + "}}", json.dumps(P[a]))
assert "{{" not in t
assert "\u2014" not in t and "\u2013" not in t, "hay guiones largos o medios"
open(os.path.join(root, "docs", "audit_s146", "FRENTE_G_INVENTARIO_DE_CAMINOS.md"), "w", encoding="utf-8").write(t)
print("ok", len(t), "caracteres;", cnt)
