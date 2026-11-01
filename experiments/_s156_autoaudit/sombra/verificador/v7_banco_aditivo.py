# Verificador S156: cargar_nuestros(coords, inner, win) del commit es identico al del padre (0026eb816^)
# sobre la misma ventana (records, campos y predicado). Uso: python v7_banco_aditivo.py <worktree> <dir_padre>
import json, os, sys, subprocess, importlib.util
W, P = sys.argv[1], sys.argv[2]
sys.path.append(W)
def cargar(root, tag):
    sys.path[:0] = [root, os.path.join(root, "scripts")]
    for m in [k for k in list(sys.modules) if k in ("banco_paridad", "auto_audit_weekly", "clase_mirova", "referencia_mirova_unificada", "calidad_referencia_mirova") or k.startswith("pipeline")]:
        del sys.modules[m]
    spec = importlib.util.spec_from_file_location("bp_" + tag, os.path.join(root, "scripts", "banco_paridad.py"))
    bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)
    bp.DATA = __import__("pathlib").Path(W) / "data" / "mirova_equivalent"
    bp.HTML = __import__("pathlib").Path(W) / "frontend" / "index.html"
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
    recs = bp.cargar_nuestros(coords, inner, ("2026-09-18", "2026-10-19"))
    del sys.path[:2]
    return [{k: (str(v) if k == "dt" else v) for k, v in r.items()} for r in recs]
a = cargar(W, "nuevo"); b = cargar(P, "padre")
print("n nuevo", len(a), "n padre", len(b), "identicos:", a == b)
print("claves nuevo", sorted(a[0]), "\nclaves padre", sorted(b[0]))
