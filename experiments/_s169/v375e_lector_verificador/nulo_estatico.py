# Pregunta 1: si el nulo estuviera mal armado, ¿esta medicion lo veria? Si para (i) unicidad de cada texto y (ii) cuenta; NO para si el criterio de atrapada es correcto (eso lo ve (iii)).
# Pregunta 2: si 'comprobar_unicas' estuviera muerta devolveria [] igual: control positivo = una mutacion falsa debe salir en la lista.
import sys, importlib.util, io
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol/experiments/_s168/v375e_sombra")
sp=importlib.util.spec_from_file_location("M",A/"mutar_sombra.py"); M=importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
print("n mutaciones:", len(M.MUTACIONES), "ids unicos:", len({m[0] for m in M.MUTACIONES}))
print("textos no unicos:", M.comprobar_unicas())
M.MUTACIONES.append(("FALSA","texto_que_no_existe_xyz","a"))
print("control positivo (debe listar FALSA):", M.comprobar_unicas())
M.MUTACIONES.pop()
# (iii) como clasifica: miro el codigo de correr()
import inspect; print(inspect.getsource(M.correr))
# ¿hay mutaciones cuyo reemplazo deja el texto igual (no-op)?
print("no-op:", [m[0] for m in M.MUTACIONES if m[1]==m[2]])
# conjuntos de ids por regla nueva
ids=[m[0] for m in M.MUTACIONES]; print(ids)
