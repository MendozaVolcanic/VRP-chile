# -*- coding: utf-8 -*-
"""Verificador VC: con el flag apagado, ¿el AST de cada archivo A45 es el de b09a7b321 tras quitar SOLO lo marcado como nuevo?
Se quita: (store) `_via_mirova = ...` y `and not _via_mirova`; (viirs_mod) el import del flag, la asignacion
`_via_sin_grilla = False`, el bloque `if ENABLE_V750_CODIGO_MIROVA:` entero y el `if _via_sin_grilla:` final.
Control positivo: si ademas se deja `_via_mirova` en una condicion, tiene que dar DISTINTO."""
import ast, subprocess, sys
R = r"C:\vrp-trabajo\s162-via-mirova"
def git_show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=R, capture_output=True, text=True, encoding="utf-8", check=True).stdout

class Quitar(ast.NodeTransformer):
    def __init__(self, nombres_flag, asign):
        self.nf, self.asign = nombres_flag, asign
    def visit_If(self, n):
        self.generic_visit(n)
        t = n.test
        if isinstance(t, ast.Name) and t.id in self.nf and not n.orelse:
            return None
        return n
    def visit_Assign(self, n):
        if len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in self.asign:
            return None
        return n
    def visit_AnnAssign(self, n):
        if isinstance(n.target, ast.Name) and n.target.id in self.asign:
            return None
        return n
    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.And):
            vals = [v for v in n.values if not (isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not)
                                                and isinstance(v.operand, ast.Name) and v.operand.id == "_via_mirova")]
            if len(vals) == 1:
                return vals[0]
            n.values = vals
        return n
    def visit_ImportFrom(self, n):
        n.names = [a for a in n.names if a.name != "ENABLE_V750_CODIGO_MIROVA"]
        return n if n.names else None

def norm(src, nf, asign):
    t = Quitar(nf, asign).visit(ast.parse(src))
    ast.fix_missing_locations(t)
    return ast.dump(t)

for path, nf, asign in [("pipeline/store.py", set(), {"_via_mirova"}),
                        ("pipeline/process_viirs_mod.py", {"ENABLE_V750_CODIGO_MIROVA", "_via_sin_grilla"}, {"_via_sin_grilla"}),
                        ("pipeline/profile.py", set(), {"ENABLE_V750_CODIGO_MIROVA"})]:
    ant = ast.dump(ast.parse(git_show("b09a7b321", path)))
    nuevo = norm(open(R + "\\" + path, encoding="utf-8").read(), nf, asign)
    # el If del store con `and not _via_mirova` queda como If simple tras visit_BoolOp
    print(path, "AST identico tras quitar lo nuevo:", ant == nuevo)
# control positivo: sin quitar `and not _via_mirova` tiene que dar distinto
src = open(R + "\pipeline\store.py", encoding="utf-8").read()
t = Quitar(set(), {"_via_mirova"}); 
class Sin(Quitar):
    def visit_BoolOp(self, n): self.generic_visit(n); return n
a = ast.parse(src); a = Sin(set(), {"_via_mirova"}).visit(a); ast.fix_missing_locations(a)
print("control (no quitar el `and not`): identico =", ast.dump(a) == ast.dump(ast.parse(git_show("b09a7b321", "pipeline/store.py"))), "(debe ser False)")
