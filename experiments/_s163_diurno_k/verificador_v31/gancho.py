import sys, os
RAIZ = os.path.normcase(os.path.abspath(sys.argv[1])) + os.sep
vistos = set()
def hook(ev, args):
    if ev == "open":
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            try:
                p = os.path.normcase(os.path.abspath(os.fsdecode(p)))
            except Exception:
                return
            if p.startswith(RAIZ) and "__pycache__" not in p and "verificador" not in p:
                vistos.add(p[len(RAIZ):].replace(os.sep, "/"))
sys.addaudithook(hook)
sys.path.insert(0, os.path.join(sys.argv[1], "experiments", "_s163_diurno_k"))
sys.path.insert(0, os.path.join(sys.argv[1], "scripts"))
sys.path.insert(0, sys.argv[1])
import pytest
pytest.main(["-q", "-p", "no:cacheprovider", os.path.join(sys.argv[1], "experiments/_s163_diurno_k/test_evaluar_diurno_k.py")])
import importlib
for m in ("nulo_estructural", "sustrato_k", "congelar_referencia"):
    try:
        importlib.import_module(m)
    except BaseException as e:
        print("import", m, "->", repr(e)[:100])
sel = [x for x in open(os.path.join(sys.argv[1], "experiments/_s163_diurno_k/objetivos_sha256.txt")) if not x.startswith("#") and x.strip()]
sel = {x.split()[1] for x in sel}
print("ABIERTOS Y NO SELLADOS:")
for v in sorted(vistos - sel):
    print("  ", v)
print("SELLADOS NO ABIERTOS:")
for v in sorted(sel - vistos):
    print("  ", v)
print("MODULOS CARGADOS DEL REPO NO SELLADOS:")
mods = set()
for n, m in list(sys.modules.items()):
    f = getattr(m, "__file__", None)
    if f:
        p = os.path.normcase(os.path.abspath(f))
        if p.startswith(RAIZ) and "verificador" not in p:
            mods.add(p[len(RAIZ):].replace(os.sep, "/"))
for v in sorted(mods - sel):
    print("  ", v)
print("SELLADOS NO CARGADOS NI ABIERTOS:", sorted(sel - vistos - mods))
