# -*- coding: utf-8 -*-
"""A5: ejecuta criterios_sombra y control_s7 del lector del tag con entradas sinteticas. No llama a main(), no lee
ninguna lectura de la sombra. Uso: python v_a5.py <ruta_leer_sombra_v375e.py>"""
import importlib.util
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
spec = importlib.util.spec_from_file_location("lector_tag", sys.argv[1])
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
print("CLASES_DECIDEN", M.CLASES_DECIDEN, "| UMBRAL_COBERTURA", M.UMBRAL_COBERTURA)

SS = "SIN SUSTRATO"
SIL = "SIN SUSTRATO (faltan negativos de alguna clase)"   # el literal que pone leer_brazo cuando no hay negativos
casos = [
    ("p2k y silencio SIN SUSTRATO, p2l SIN SUSTRATO", dict(p2k=SS, silencio=SIL, p2l=SS)),
    ("p2k y silencio SIN SUSTRATO, p2l EMPATE", dict(p2k=SS, silencio=SIL, p2l="EMPATE")),
    ("p2k y silencio SIN SUSTRATO, p2l PIERDE (control)", dict(p2k=SS, silencio=SIL, p2l="PIERDE")),
    ("p2k PIERDE (control)", dict(p2k="PIERDE", silencio=SIL, p2l=SS)),
    ("silencio ENCIENDE DE MAS (control)", dict(p2k=SS, silencio="ENCIENDE DE MAS", p2l=SS)),
]
for nombre, k in casos:
    c = M.criterios_sombra([], k["p2k"], k["silencio"], k["p2l"], M.CUMPLE, False, M.CUMPLE, regimen_ok=True)
    print(f"criterios_sombra [{nombre}] -> b={c['b']} estado={c['estado']}")
c = M.criterios_sombra([], SS, SIL, SS, M.CUMPLE, False, M.CUMPLE, regimen_ok=False)
print("criterios_sombra [todo SIN SUSTRATO, regimen_ok=False] -> b=", c["b"], "estado=", c["estado"])


def pob(clases):
    out, i = [], 0
    for cl, n in clases.items():
        for _ in range(n):
            out.append({"clase": cl, "volcan": "X", "hora_utc": f"h{i}", "id": i})
            i += 1
    return out


p = pob({"pos_prot": 10, "pos_bajo": 5, "far_tabla": 3})          # negativos con n 0
arms = {o["id"] for o in p}
ok, por = M.control_s7(p, arms)
print("control_s7 negativos n=0, resto con dato completo -> pasa =", ok, "| n por clase", {k: v["n"] for k, v in por.items()})
p2 = pob({"pos_prot": 10, "neg_pub": 10, "neg_resto": 10})
arms2 = {o["id"] for o in p2 if not (o["clase"] == "neg_pub" and o["id"] % 2 == 0)}
ok2, por2 = M.control_s7(p2, arms2)
print("control_s7 control: neg_pub 50 % sin dato -> pasa =", ok2, "| sin_dato", {k: v["sin_dato"] for k, v in por2.items()})
ok3, _ = M.control_s7([], set())
print("control_s7 poblacion vacia -> pasa =", ok3)
p4 = pob({"far_tabla": 1})
ok4, _ = M.control_s7(p4, {o["id"] for o in p4})
print("control_s7 solo 1 far_tabla, sin protegidas ni negativos -> pasa =", ok4)
