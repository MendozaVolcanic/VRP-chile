# -*- coding: utf-8 -*-
"""Verificador de D-45 (S161): comprobaciones propias de prueba_signos_p2 y regla_signos_p2 contra la adenda
ADENDA_SIGNOS_P2.md §2, por un camino distinto del del implementador.

Pregunta 1 (¿veria la rotura?): cada bloque compara la funcion real con una enumeracion propia por bits (no la
convolucion de la funcion) o con una propiedad aritmetica que no depende del codigo; una diferencia se imprime como
FALLA y el script termina con codigo 1.
Pregunta 2 (¿se ve un instrumento muerto?): el control positivo del final altera la funcion (una mutacion en memoria)
y tiene que producir FALLA en la misma comparacion.

Uso: python verif_matematica.py  (desde cualquier carpeta; busca el evaluador por ruta relativa al repositorio)
"""
import collections
import itertools
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

fallas = []


def chequear(nombre, cond, detalle=""):
    print("%-70s %s %s" % (nombre, "OK" if cond else "FALLA", detalle))
    if not cond:
        fallas.append(nombre)


def enum_bits(sumas, neto):
    """Enumeracion propia: itertools.product sobre los signos, sin convolucion."""
    le = ge = dos = 0
    for signos in itertools.product((-1, 1), repeat=len(sumas)):
        t = sum(s * x for s, x in zip(signos, sumas))
        le += t <= neto
        ge += t >= neto
        dos += abs(t) >= abs(neto)
    return le, ge, dos, 2 ** len(sumas)


print("evaluador:", X.__file__)
print("constantes:", X.SEMILLA_P2_SIGNOS, X.N_SORTEOS_P2_SIGNOS, X.MAX_B_EXACTO_P2, X.MAX_B_SIN_SUSTRATO_P2, X.TOPE_P2_DEN)

# ---- 1. exacto contra enumeracion por bits, sumas con ceros y magnitudes desiguales, B de 1 a 14
rng = random.Random(45)
n_ok = 0
for B in range(1, 15):
    for _ in range(6):
        sumas = [rng.choice([-3, -2, -1, 0, 0, 1, 2, 3]) for _ in range(B)]
        neto = sum(sumas)
        pr = X.prueba_signos_p2(sumas, neto)
        le, ge, dos, den = enum_bits(sumas, neto)
        igual = (pr["metodo"] == "exacto" and pr["gana"] == [le, den] and pr["pierde"] == [ge, den]
                 and pr["dos_colas"] == [dos, den] and pr["minimo"] == [1, den])
        n_ok += igual
        if not igual:
            print("   DIFERENCIA", B, sumas, neto, pr, (le, ge, dos, den))
chequear("1. exacto = enumeracion por bits (14 B x 6 conjuntos = 84)", n_ok == 84, "%d de 84" % n_ok)

# ---- 2. B = 20 exacto contra enumeracion por bits (2^20 con numpy, camino distinto de la convolucion)
sumas20 = [3, 1, 0, 1, -2] + [-1] * 9 + [1] * 4 + [1, 0]
neto20 = sum(sumas20)
s = np.asarray(sumas20, dtype=np.int64)
k = np.arange(2 ** 20, dtype=np.int64)
tot = (1 - 2 * ((k[:, None] >> np.arange(20, dtype=np.int64)) & 1)) @ s
pr20 = X.prueba_signos_p2(sumas20, neto20)
chequear("2. B = 20 exacto = bits (2^20)", pr20["metodo"] == "exacto" and pr20["gana"] == [int((tot <= neto20).sum()), 2 ** 20]
         and pr20["pierde"] == [int((tot >= neto20).sum()), 2 ** 20], str(pr20["gana"]))

# ---- 3. B = 21: sorteos reproducidos con un generador propio y los literales de la adenda (162, 10.000, +1)
sumas21 = [-5] + [-1] * 13 + [1] * 7
neto21 = sum(sumas21)
pr21 = X.prueba_signos_p2(sumas21, neto21)
g = np.random.default_rng(162)
S = g.choice((-1, 1), size=(10000, 21))
t21 = S @ np.asarray(sumas21, dtype=np.int64)
m_le = int((t21 <= neto21).sum())
chequear("3a. B = 21 metodo sorteos, semilla 162, 10.000, den 10.001",
         pr21["metodo"] == "sorteos" and pr21["semilla"] == 162 and pr21["n_sorteos"] == 10000 and pr21["gana"][1] == 10001)
chequear("3b. B = 21 numerador = 1 + m con generador propio", pr21["gana"][0] == 1 + m_le, "%s vs 1+%d" % (pr21["gana"], m_le))
chequear("3c. B = 21 el +1 cuenta: numerador >= 1 aunque m = 0", X.prueba_signos_p2([-1] * 25, -25)["gana"][0] >= 1)
# el orden de las sumas cambia el resultado de los sorteos (no fijado por la adenda; el codigo usa el orden de la clave)
pr21r = X.prueba_signos_p2(list(reversed(sumas21)), neto21)
print("   (informa) B = 21 con las sumas en orden inverso: gana %s contra %s en orden de clave" % (pr21r["gana"], pr21["gana"]))

# ---- 4. aritmetica entera del 5 %: k / 2^B nunca es 1/20 ; (1 + m) / 10.001 nunca es 1/20
chequear("4a. ningun k/2^B vale 1/20 (B 1..30)", all((2 ** B) % 20 != 0 for B in range(1, 31)))
chequear("4b. 10.001 no es multiplo de 20", 10001 % 20 != 0)
# comparacion en enteros contra la de coma flotante en todos los k de B = 5..20: deben coincidir salvo empates (no hay)
dif = 0
for B in range(5, 21):
    den = 2 ** B
    for kk in range(den + 1):
        if (20 * kk <= den) != (kk / den <= 0.05):
            dif += 1
chequear("4c. enteros = flotante en todo k/2^B, B 5..20 (sin empates posibles)", dif == 0, "%d diferencias" % dif)

# ---- 5. regla_signos_p2: tabla de veredictos con fracciones controladas
def pr_de(g, p, den=1000):
    return {"gana": [g, den], "pierde": [p, den], "dos_colas": [0, den], "minimo": [1, den]}
casos = [
    ("B=4 neto -4 p 1/16 -> SIN SUSTRATO", X.regla_signos_p2(-4, 4, pr_de(50, 1000)), "SIN SUSTRATO"),
    ("B=5 neto<0 p=50/1000 (5 % justo) -> GANA", X.regla_signos_p2(-5, 5, pr_de(50, 1000)), "GANA"),
    ("B=5 neto<0 p=51/1000 -> EMPATE", X.regla_signos_p2(-5, 5, pr_de(51, 1000)), "EMPATE"),
    ("B=5 neto>0 p=50/1000 -> PIERDE", X.regla_signos_p2(5, 5, pr_de(1000, 50)), "PIERDE"),
    ("B=5 neto>0 p=51/1000 -> BLOQUEA", X.regla_signos_p2(5, 5, pr_de(1000, 51)), "BLOQUEA"),
    ("B=5 neto=0 -> EMPATE aunque p chico", X.regla_signos_p2(0, 5, pr_de(1, 1)), "EMPATE"),
    ("B=5 neto<0 con p PIERDE chico y GANA grande -> EMPATE (no cruza colas)", X.regla_signos_p2(-5, 5, pr_de(1000, 1)), "EMPATE"),
    ("B=5 neto>0 con p GANA chico -> BLOQUEA (no cruza colas)", X.regla_signos_p2(5, 5, pr_de(1, 1000)), "BLOQUEA"),
    ("B=21 neto<0 p=500/10001 -> GANA (20*500=10000<=10001)", X.regla_signos_p2(-9, 21, pr_de(500, 10001, 10001)), "GANA"),
    ("B=21 neto<0 p=501/10001 -> EMPATE (10020>10001)", X.regla_signos_p2(-9, 21, pr_de(501, 10001, 10001)), "EMPATE"),
]
for nombre, got, esp in casos:
    chequear("5. " + nombre, got == esp, got)

# ---- 6. tasa exacta de falsos por cola, B 5..20, bloques +-1, por mi propia cuenta (binomial) con la regla real
peor = Fraction(0)
tabla = []
for B in range(5, 21):
    den = 2 ** B
    fg = Fraction(0)
    for kpos in range(B + 1):          # kpos bloques +1
        neto = 2 * kpos - B
        pr = X.prueba_signos_p2([1] * B, neto)   # magnitudes 1: el resultado depende solo del neto
        v = X.regla_signos_p2(neto, B, pr)
        if v == "GANA":
            fg += Fraction(math.comb(B, kpos), den)
    tabla.append((B, fg))
    peor = max(peor, fg)
chequear("6. tasa exacta GANA <= 5 % para B 5..20 (bloques +-1)", peor <= Fraction(1, 20), "maxima %s = %.4f %% en B=%d" % (
    peor, 100 * float(peor), [b for b, f in tabla if f == peor][0]))
print("   tabla B: tasa:", ", ".join("%d: %.4f" % (b, float(f)) for b, f in tabla))

# ---- 7. 7 noches del mismo lado deciden; 6 contra 1 no (§7 tercer punto) por decidir_p2_bloques entera
def contrib(por_noche):
    out = []
    for n, cs in enumerate(por_noche):
        dia = "2026-09-%02d" % (n + 1)
        for j, c in enumerate(cs):
            out.append({"clave": "Lascar|VIIRS375|%s 05:%02d" % (dia, j), "c": c, "bloque": "Lascar|%s" % dia})
    return out
v7, d7 = X.decidir_p2_bloques(contrib([[+1]] * 7), True)
v61, d61 = X.decidir_p2_bloques(contrib([[+1]] * 6 + [[-1]]), True)
chequear("7a. 7 noches +1 -> PIERDE p=1/128", v7 == "PIERDE" and d7["p_pierde_fraccion"] == [1, 128])
chequear("7b. 6 contra 1 -> BLOQUEA p=8/128", v61 == "BLOQUEA" and d61["p_pierde_fraccion"] == [8, 128])
v7n, d7n = X.decidir_p2_bloques(contrib([[-1]] * 7), True)
chequear("7c. 7 noches -1 -> GANA", v7n == "GANA")
# 6 contra 1 con magnitudes desiguales SI puede decidir (el contrario chico): 6 noches de +2 y una de -1
v62, d62 = X.decidir_p2_bloques(contrib([[+1, +1]] * 6 + [[-1]]), True)
print("   (informa) 6 noches de +2 contra 1 de -1: %s p_pierde %s" % (v62, d62["p_pierde_fraccion"]))

# ---- 8. INDECIDIBLE solo con controles caidos; SIN SUSTRATO con B <= 4 aun con neto grande
v_c, d_c = X.decidir_p2_bloques(contrib([[+1]] * 12), False)
chequear("8a. controles caidos -> INDECIDIBLE", v_c == "INDECIDIBLE" and d_c["B"] == 12)
v_s, d_s = X.decidir_p2_bloques(contrib([[+1] * 30] * 4), True)
chequear("8b. 4 noches de 30 errores de D -> SIN SUSTRATO (no bloquea)", v_s == "SIN SUSTRATO" and d_s["neto"] == 120)
v_0, d_0 = X.decidir_p2_bloques([], True)
chequear("8c. sin discordantes -> SIN SUSTRATO, B 0, sin excepcion", v_0 == "SIN SUSTRATO" and d_0["B"] == 0, str(d_0.get("p_gana_fraccion")))

# ---- 9. B cuenta bloques de suma 0 y el neto es la suma de las sumas
v_b, d_b = X.decidir_p2_bloques(contrib([[-1]] * 4 + [[+1, -1]]), True)
chequear("9. B=5 con un bloque de suma 0; neto -4; EMPATE (p 2/32)", d_b["B"] == 5 and d_b["neto"] == -4 and v_b == "EMPATE"
         and d_b["p_gana_fraccion"] == [2, 32])

# ---- 10. D-46, punto 3: con las tasas esperadas por celda (resumen_signos.txt) y 40 semillas, P(al menos una de las
# 16 celdas-cola >= 3 de 40, o sea sobre el 5 %)
tasas = [0.011, 0.011, 0.017, 0.033, 0.018, 0.025, 0.032, 0.025]   # 8 celdas (punto x sensor), igual por cola
def p_ge3(p, n=40):
    return 1 - sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(3))
p_alguna = 1 - math.prod((1 - p_ge3(p)) ** 2 for p in tasas)
print("   D-46 punto 3: P(alguna de 16 celdas-cola sobre 5 %%) = %.3f (NOTA_D46 dice 0,67)" % p_alguna)
print("   D-46 punto 2: P(X >= 3 de 40 | p = 0,032) = %.4f (NOTA_D46 dice 0,136)" % p_ge3(0.032))
# Wilson de 8/320 y 4/320 y 3/40
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)
print("   Wilson 8/320 = [%.1f, %.1f]; 4/320 = [%.1f, %.1f]; 3/40 = [%.1f, %.1f]" % (wilson(8, 320) + wilson(4, 320) + wilson(3, 40)))

# ---- 11. control positivo del instrumento: una mutacion en memoria (cola de GANA con >=) tiene que dar FALLA en 1.
import types
src_ok = X.prueba_signos_p2
def mutada(sumas, neto, **kw):
    r = src_ok(sumas, neto, **kw)
    r = dict(r); r["gana"] = r["pierde"]
    return r
X.prueba_signos_p2 = mutada
le, ge, dos, den = enum_bits([-2, -1, 1, 0, -1], -3)
prm = X.prueba_signos_p2([-2, -1, 1, 0, -1], -3)
X.prueba_signos_p2 = src_ok
chequear("11. CONTROL POSITIVO: la mutacion en memoria se detecta (debe decir FALLA)", prm["gana"] == [le, den], "esperado FALLA")
if fallas == ["11. CONTROL POSITIVO: la mutacion en memoria se detecta (debe decir FALLA)"]:
    print("\nRESULTADO: todas las comprobaciones OK y el control positivo falla como debe")
    sys.exit(0)
print("\nRESULTADO: FALLAS", fallas)
sys.exit(1)
