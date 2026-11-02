# Control positivo de S0 (Q1): si un archivo sellado del checkout cambia, S0 cae. Se simula cambiando el sello esperado.
import importlib.util, os, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("LS", "D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS)
os.environ["VRP_PROFILE"] = "mirova_equivalent"
k = next(p for p in LS.SHA_SELLO_LECTOR if p.name == "mirova_equivalent.yaml")
LS.SHA_SELLO_LECTOR[k] = "0" * 64
d, malos = LS.cargar_deps()
print("S0 con el sello de mirova_equivalent.yaml alterado:", "NO CAE (malo)" if d else f"cae: {list(malos)}")
os.environ["VRP_PROFILE"] = "sombra_codigo_mirova"
d, malos = LS.cargar_deps()
print("S0 con VRP_PROFILE=sombra_codigo_mirova:", "NO CAE (malo)" if d else f"cae: {malos}")
