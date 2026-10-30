# -*- coding: utf-8 -*-
"""VF P1-02: tabla de verdad de la compuerta del analizador sellado (texto literal de analizar_v750b.py, desde
'aviso, rc_final = "", 0' hasta 'todo_ok = ...', ejecutado aparte con las variables de entrada fijadas).
Pregunta 1: si la compuerta dejara pasar un censo FALLADO con --leer-con-faltantes, esta tabla lo veria (fila 4).
Pregunta 2: control: la fila 'bandera de pruebas + censo pedido y fallado' tiene que salir CERRADA (VB3-06); si saliera
ABIERTA la extraccion estaria mal. Y la fila 'todo OK sin banderas' tiene que salir ABIERTA."""
import sys, types, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ruta = sys.argv[1]
src = open(ruta, encoding="utf-8").read().replace("\r\n", "\n")
print("analizador", ruta, "sha256 LF", hashlib.sha256(src.encode()).hexdigest())
ini = src.index('    aviso, rc_final = "", 0\n'); fin = src.index("    todo_ok = gen_ok and ctrl_roi and cob_pasa and censo_pasa\n")
fin = src.index("\n", fin) + 1
bloque = "\n".join(l[4:] for l in src[ini:fin].splitlines())
print("lineas del bloque:", src[:ini].count("\n") + 1, "a", src[:fin].count("\n"))
print(bloque); print("----")
def corre(cob_ok, censo_ok, censo_art, omitido, lcf):
    a = types.SimpleNamespace(leer_con_faltantes=lcf, censo_omitido_solo_pruebas=omitido,
                              censo_art=["x"] if censo_art else [], censo_objetivos="o.json" if censo_art else "")
    ns = dict(a=a, cob_ok=cob_ok, censo_ok=censo_ok, nidx=[True], c_nulo=0, k_ok=True, ctrl_roi=True)
    exec(bloque, ns)
    return ("ABIERTA" if ns["todo_ok"] else "CERRADA"), ns["rc_final"], ns["aviso"]
filas = [("todo OK, sin banderas (control: ABIERTA)", True, True, True, False, ""),
         ("censo corrio y FALLO, sin banderas", True, False, True, False, ""),
         ("bandera de pruebas + censo corrido y fallado (control VB3-06: CERRADA)", True, False, True, True, ""),
         ("cobertura OK, censo corrio y FALLO, --leer-con-faltantes", True, False, True, False, "motivo X"),
         ("cobertura INSUF, censo corrio y FALLO, --leer-con-faltantes (motivo de cobertura)", False, False, True, False, "faltan 3 pasadas"),
         ("censo AUSENTE (no se pudo correr), --leer-con-faltantes (lo que permite el texto)", True, False, False, False, "censo no corre")]
for t, *x in filas:
    print(f"{t:95s} -> {corre(*x)}")
