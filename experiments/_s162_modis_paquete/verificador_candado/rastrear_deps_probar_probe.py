# Verificador: corre probar_probe_paquete.main() y lista los paquetes de terceros que quedaron importados,
# para cotejar con el `pip install` del job `prueba` del workflow (numpy scipy pyyaml pyproj).
import runpy, sys, sysconfig, os
from pathlib import Path
AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI))
sys.argv = [str(AQUI / "probar_probe_paquete.py")]
rc = 0
try:
    runpy.run_path(str(AQUI / "probar_probe_paquete.py"), run_name="__main__")
except SystemExit as e:
    rc = e.code
stdlib = set(sys.stdlib_module_names)
top = {m.split(".")[0] for m in sys.modules}
terceros = sorted(t for t in top if t not in stdlib and not t.startswith("_")
                  and getattr(sys.modules.get(t), "__file__", None)
                  and "site-packages" in (sys.modules[t].__file__ or ""))
print("TERCEROS IMPORTADOS:", terceros)
sys.exit(rc)
