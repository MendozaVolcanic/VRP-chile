# Pregunta 1: si hubiera un modulo no sellado que influye, ¿se vería? Si, aparece en sys.modules bajo arbol y no esta en los sha. Control positivo: debe listar los 12 sellados.
import sys, importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol").resolve()
sp=importlib.util.spec_from_file_location("S",A/"experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
S=importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
deps,malos=S.cargar_deps(); print("deps",bool(deps),malos)
import banco_paridad as B
from clase_mirova import alerta_protegida
from referencia_mirova_unificada import cargar_referencia_unificada
sellados={str(p.resolve()) for p in list(S.SHA_DEPS)+list(S.SHA_SELLO_LECTOR)}
for n,m in sorted(sys.modules.items()):
    f=getattr(m,"__file__",None)
    if f and str(Path(f).resolve()).startswith(str(A)):
        print(("SELLADO " if str(Path(f).resolve()) in sellados else "NO SELLADO"), n, Path(f).resolve().relative_to(A))
