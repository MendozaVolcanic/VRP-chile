# Pregunta 1: ¿ve esta medicion que un CRASH dentro de una seccion cuenta como 'aserción fallida'? Si: usa la misma seccion() y chk() de la bateria.
# Pregunta 2: control positivo = una aserción de valor falsa (chk False) debe dar el mismo resultado final (exit 1) que el crash.
import sys, importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol/experiments/_s168/v375e_sombra")
sp=importlib.util.spec_from_file_location("P",A/"probar_sombra.py"); P=importlib.util.module_from_spec(sp); sp.loader.exec_module(P)
with P.seccion("crash simulado de un mutante"):
    raise KeyError("clave ausente por mutacion")
print("RES tras crash:", P.RES, "-> exit batería =", 0 if all(P.RES) else 1)
P.RES.clear()
P.chk("aserción de valor falsa", False)
print("RES tras aserción falsa:", P.RES, "-> exit batería =", 0 if all(P.RES) else 1)
