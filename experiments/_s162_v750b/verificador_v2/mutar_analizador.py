# -*- coding: utf-8 -*-
"""VB2: mutaciones al ANALIZADOR corridas contra la batería adaptada del autor (mutaciones_regla_s6_v2.py).

Preguntas del instrumento. (1) Si el analizador tuviera una decisión rota, ¿la batería v2 lo vería? Se muta una línea de la
regla o de los controles y se compara la salida completa de la batería con la de línea base: una mutación «sobrevive» si
la salida no cambia (la batería no la ve) y «cae» si cambia. (2) Si la batería estuviera muerta (no corre), todas las
mutaciones darían «sin dato» y el script sale 1. Control positivo: la mutación M0 (rompe el parseo del analizador) tiene
que caer; la de línea base contra sí misma tiene que dar IGUAL.
Uso: python mutar_analizador.py --arbol <arbol> --trabajo <carpeta temporal>
"""
import argparse, shutil, subprocess, sys, re
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--arbol", required=True); ap.add_argument("--trabajo", required=True)
a = ap.parse_args()
src = Path(a.arbol).resolve(); W = Path(a.trabajo).resolve()
T = W / "arbol"
if T.exists():
    shutil.rmtree(T)
shutil.copytree(src, T, ignore=shutil.ignore_patterns("*.json", "data", "ref"))
AN = T / "experiments/_s162_v750b/analizar_v750b.py"
orig = AN.read_text(encoding="utf-8")
BAT = T / "experiments/_s162_v750b/mutaciones_regla_s6_v2.py"


def bateria(nombre):
    d = W / nombre
    if d.exists():
        shutil.rmtree(d)
    o = subprocess.run([sys.executable, str(BAT), "--arbol", str(T), "--dest", str(d)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    txt = o.stdout
    return re.sub(r"\n+", "\n", txt), o.returncode

MUT = {
 "M0 rompe sintaxis": ('FRONTERA_OCR = "2026-06-13"', 'FRONTERA_OCR = "2026-06-13" +'),
 "M1 quita P1 en O con tabla sola (§6.1 segunda condición)": (' and ver[(b, "O", "tabla")][0] == 0]', ']'),
 "M2 quita el filtro de la tabla en §6.2": ('\n             and ver[(b, "TO", "tabla")][1] in ("GANA", "EMPATE", "SIN SUSTRATO")]', ']'),
 "M3 §6.3 admite BLOQUEA": ('("EMPATE", "SIN SUSTRATO"))]', '("EMPATE", "SIN SUSTRATO", "BLOQUEA"))]'),
 "M4 orden de PREF invertido": ('PREF = ("B4", "B2", "B5", "B1", "B3")', 'PREF = ("B3", "B1", "B5", "B2", "B4")'),
 "M5 frontera OCR 2026-07-01": ('FRONTERA_OCR = "2026-06-13"', 'FRONTERA_OCR = "2026-07-01"'),
 "M6 signo de c invertido": ('c = err(b) - err(ref)', 'c = err(ref) - err(b)'),
 "M7 canal decide = siempre todo": ('canal = "tabla" if o["hora_utc"] < FRONTERA_OCR else "todo"', 'canal = "todo"'),
 "M8 ancla del record = centro": ('return tuple(obj[i].get("pos_crater") or (C, C))', 'return (C, C)'),
 "M9 cobertura ignora protegidas SIN DATO": ('and not prot_sin\n', '\n'),
 "M10 compuerta ignora K = producción": ('c_nulo == 0 and k_ok and cob_ok', 'c_nulo == 0 and cob_ok'),
 "M11 compuerta ignora control positivo": ('and len(pcc) >= 1', ''),
 "M12 compuerta ignora control negativo": ('neg_ctrl[0] == "SIN SUSTRATO" and neg_ctrl[2] == 0 and ', ''),
 "M13 tope de SIN DATO 50 %": ('MAX_SIN_DATO = 0.02', 'MAX_SIN_DATO = 0.5'),
 "M14 P1 nunca cuenta": ('if e == "prot" and not pb:', 'if e == "prot" and not pb and False:'),
 "M15 B4 invertido": ('return "B1" if volcan in VOL_SENS else "B0"', 'return "B0" if volcan in VOL_SENS else "B1"'),
 "M16 bloque = sólo la noche": ('sumas[(o["hora_utc"][:10], o["volcan"])] += c', 'sumas[o["hora_utc"][:10]] += c'),
 "M17 bloques de c = 0 también cuentan": ('            if c:\n                sumas', '            if True:\n                sumas'),
 "M18 K distinta no sale de los brazos": ('oks = [i for i in oks if i not in set(k_dist)]', 'pass'),
 "M19 el desempate §6.2 elige el de MAYOR E": ('elegido = min(ganan, key=lambda b: ver[(b, "TO", "decide")][2])', 'elegido = max(ganan, key=lambda b: ver[(b, "TO", "decide")][2])'),
 "M20 elegible exige P1 sólo en T": ('ver[(b, "TO", "decide")][0] == 0', 'ver[(b, "T", "decide")][0] == 0'),
 "M21 §6.2 usa canal todo en vez de decide": ('ver[(b, "TO", "decide")][1] == "GANA"', 'ver[(b, "TO", "todo")][1] == "GANA"'),
 "M22 §6.3 sin B1 como candidato": ('(b == "B1" or ver', '(ver'),
}
base, rc0 = bateria("base")
if rc0 != 0 or "== E7" not in base:
    print("SIN DATO: la batería de línea base no corrió", rc0); sys.exit(1)
igual0, _ = bateria("base2")
print("control: línea base contra sí misma:", "IGUAL" if igual0 == base else "DISTINTA (la batería no es determinista)")
res = {}
for nom, (v, n) in MUT.items():
    if orig.count(v) != 1:
        print(f"{nom}: SIN DATO (la cadena aparece {orig.count(v)} veces)"); res[nom] = "SIN DATO"; continue
    AN.write_text(orig.replace(v, n), encoding="utf-8")
    t, rc = bateria("m")
    AN.write_text(orig, encoding="utf-8")
    est = "IGUAL (la batería NO la ve)" if t == base else "CAE (la batería la ve)"
    res[nom] = est
    print(f"{nom}: {est}", flush=True)
AN.write_text(orig, encoding="utf-8")
print("resumen: caen", sum(v.startswith('CAE') for v in res.values()), "sobreviven", sum(v.startswith('IGUAL') for v in res.values()),
      "sin dato", sum(v == 'SIN DATO' for v in res.values()))
