# Verificador S172: igualdad de Python entre escalares YAML (1 == 1.0 == True). Q1: si el comparador distinguiera tipos,
# el caso 'cambia de tipo' marcaria; el control positivo (valor distinto) marca siempre. Q2: instrumento muerto -> sin salida.
import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("LS", "D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS)
ME = "pipeline/profiles/mirova_equivalent.yaml"
for nom, a, b in (("1 -> true", "thresholds:\n  x: 1\n", "thresholds:\n  x: true\n"),
                  ("0 -> false", "thresholds:\n  x: 0\n", "thresholds:\n  x: false\n"),
                  ("5 -> 5.0", "thresholds:\n  x: 5\n", "thresholds:\n  x: 5.0\n"),
                  ("1 -> 'true' (str)", "thresholds:\n  x: 1\n", "thresholds:\n  x: 'true'\n"),
                  ("CONTROL 1 -> 2", "thresholds:\n  x: 1\n", "thresholds:\n  x: 2\n")):
    print(f"{nom:20} marca={LS.cambio_significativo(ME, a, b)}")
