# -*- coding: utf-8 -*-
"""P-D: lo que se puede comprobar del medidor mutar_evaluar_f4.py SIN correr la bateria ni el medidor (cupos ocupados).
Se importa el modulo (solo lee evaluar_f4.py) y se examina: (1) clasificar() con entradas sinteticas, control positivo
incluido; (2) cada mutacion aplica exactamente una vez al texto de evaluar_f4.py (si no, 'NO APLICA'); (3) cuantas
mutaciones y controles trae el codigo frente a la salida commiteada; (4) el codigo de salida de resumir() con vivas.
PREGUNTA 1: si clasificar() contara una caida como acierto, (1) lo veria: las entradas con caen != [] no dan ATRAPADA.
PREGUNTA 2: se imprimen conteos con su denominador."""
import importlib.util, sys, re
from pathlib import Path
C = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/experiments/_s166_modd_f4")
spec = importlib.util.spec_from_file_location("mutar_leido", C / "mutar_evaluar_f4.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

print("== 1. clasificar(codigo, fallan, caen)")
for args, debe in (((1, ["E01"], []), "ATRAPADA"), ((1, ["E01"], ["E02"]), "ATRAPADA_CON_CAIDAS"), ((1, [], []), "ROTA"),
                   ((2, [], ["E01"]), "CAE"), ((0, [], []), "VIVA"), ((3, [], []), "ROTA")):
    got = M.clasificar(*args)
    print("   %-28s -> %-20s esperado %-20s %s" % (args, got, debe, "OK" if got == debe else "DISTINTO"))

print("== 2. cada mutacion aplica exactamente una vez a evaluar_f4.py (denominador: %d mutaciones con texto)" % sum(1 for m in M.MUTACIONES if m[1] is not None))
no_aplica = [(n, M.FUENTE.count(v)) for n, v, _ in M.MUTACIONES if v is not None and M.FUENTE.count(v) != 1]
print("   no aplican (nombre, apariciones):", no_aplica)

print("== 3. tamano del medidor del codigo frente a la salida commiteada")
muts = [m[0] for m in M.MUTACIONES if re.match(r"M\d\d", m[0])]
ctrl = [m[0] for m in M.MUTACIONES if not re.match(r"M\d\d", m[0])]
print("   codigo: %d mutaciones M%s..M%s, controles %s" % (len(muts), muts[0][1:3], muts[-1][1:3], ctrl))
sal = (C / "mutar_evaluar_f4_salida.txt").read_text(encoding="utf-8")
en_salida = re.findall(r"^(M\d\d)\w* ", sal, flags=re.M)
print("   salida commiteada: %d mutaciones (%s..%s); lineas de control: %s" % (
    len(en_salida), en_salida[0], en_salida[-1], re.findall(r"^(CONTROL_\w+|IDENTIDAD)\s", sal, flags=re.M)))
print("   mutaciones del codigo que NO estan en la salida:", [n for n in muts if n[:3] not in set(en_salida)])
print("   'ATRAPADA_CON_CAIDAS' aparece en la salida commiteada:", "ATRAPADA_CON_CAIDAS" in sal, "| 'atrapadas con caídas' en su resumen:", "atrapadas con caídas" in sal)

print("== 4. codigo de salida de resumir() con mutaciones vivas / que caen / con caidas / rotas (controles bien)")
res = [("IDENTIDAD", "VIVA", ""), ("CONTROL_CAIDA", "CAE", ""), ("CONTROL_CAIDA_VALUEERROR", "CAE", ""), ("CONTROL_ROTA", "ROTA", ""),
       ("M01_a", "VIVA", ""), ("M02_b", "CAE", ""), ("M03_c", "ATRAPADA_CON_CAIDAS", ""), ("M04_d", "ROTA", ""), ("M05_e", "NO APLICA (0 apariciones)", "")]
txt, cod = M.resumir(res)
print("   codigo de salida:", cod, "| ultima linea:", txt.splitlines()[-1][:160])
res2 = [r if r[0] != "CONTROL_ROTA" else ("CONTROL_ROTA", "VIVA", "") for r in res]
txt2, cod2 = M.resumir(res2)
print("   control positivo (CONTROL_ROTA sale VIVA):", cod2, "|", txt2.splitlines()[-1][:100])
