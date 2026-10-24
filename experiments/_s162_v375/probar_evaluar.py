# -*- coding: utf-8 -*-
"""Pruebas del evaluador de V375-B y V375-C, sin red y sin datos del runner.

1. La prueba de signos llevada a sumas reales (evaluar.prueba_signos y regla_signos) da lo MISMO que la función sellada
   de D-45 (experiments/_s157_prereg_d25/evaluar_d25.py en el tag s161-d25-lectura, leída con git show, no copiada) en
   2.000 juegos de sumas enteras, exacto (B <= 20) y por sorteos (B > 20).
2. Casos sintéticos con respuesta conocida, cada uno con su caso que tiene que fallar:
   a. nulo: un brazo idéntico a la referencia da 0 bloques discordantes y SIN SUSTRATO;
   b. un brazo que pierde 10 alertas bajo 1 MW en 10 noches distintas da P2 PIERDE (p = 1/1024); con 3 noches, SIN
      SUSTRATO; con 6 noches y 5 contra 1 en pérdidas, no llega (BLOQUEA);
   c. silencio: 0 de 445 en neg_resto con peso parejo da la Wilson cruda (~0,85 %) y, con N = 3.323 y neg_pub censo,
      el veredicto SILENCIO ACOTADO BAJO K contra 3,85 %; si el brazo publica 40 de 445, ENCIENDE DE MAS;
   d. cota honesta (verificador de S159 V-1): con 0 de 45 en neg_resto y N = 3.348, un ΔE puntual negativo no puede
      salir GANA: la cota superior lo deja NO RESUELTO;
   e. la elección por volcán se hace sólo con la ventana T (un brazo que es mejor en O pero peor en T no se elige);
   f. el peso importa: con pesos distintos la tasa ponderada no es la cruda.
3. Una mutación que el evaluador tiene que atrapar: si err() contara las protegidas como errores bajo 1 MW, el caso b
   cambiaría (la prueba lo detecta comparando contra la cuenta a mano).
Uso: python -I probar_evaluar.py
"""
from __future__ import annotations

import collections
import io
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import evaluar as EV  # noqa: E402

TAG = "s161-d25-lectura"
RUTA = "experiments/_s157_prereg_d25/evaluar_d25.py"


def sellada():
    """Las dos funciones de D-45 tal como están en el tag, ejecutadas en un espacio propio."""
    src = subprocess.run(["git", "show", f"{TAG}:{RUTA}"], cwd=RAIZ, capture_output=True, text=True,
                         encoding="utf-8").stdout
    assert "def prueba_signos_p2" in src, "no pude leer la función sellada del tag"
    ns = {"np": np, "collections": collections, "N_SORTEOS_P2_SIGNOS": 10000, "SEMILLA_P2_SIGNOS": 162,
          "MAX_B_EXACTO_P2": 20, "MAX_B_SIN_SUSTRATO_P2": 4, "TOPE_P2_DEN": 20}
    for nombre in ("prueba_signos_p2", "regla_signos_p2"):
        i = src.index(f"def {nombre}(")
        j = src.index("\ndef ", i + 1)
        exec(src[i:j], ns)  # noqa: S102
    return ns["prueba_signos_p2"], ns["regla_signos_p2"]


def prueba_1():
    ps, rs = sellada()
    rng = np.random.default_rng(7)
    n = 0
    for _ in range(2000):
        Bn = int(rng.integers(0, 26))
        s = [int(x) for x in rng.integers(-3, 4, Bn)]
        neto = sum(s)
        a, b = ps(s, neto), EV.prueba_signos(s, float(neto))
        if Bn <= 20:
            assert a["gana"] == b["gana"] and a["pierde"] == b["pierde"] and a["dos_colas"] == b["dos_colas"], (s, a, b)
        else:   # por sorteos: misma semilla, mismos signos (int contra float, las sumas coinciden)
            assert a["gana"] == b["gana"] and a["pierde"] == b["pierde"], (Bn, a, b)
        assert rs(neto, Bn, a) == EV.regla_signos(float(neto), Bn, b), (s, rs(neto, Bn, a))
        n += 1
    print(f"1. prueba de signos = función sellada de D-45 ({TAG}) en {n} de {n} juegos")


def fila(c, vol, dia, w=1.0, h="h", tramo="T", X=False, K=False, mir=0.5, V=0.5, prot=False):
    a = ("A", "cercano")
    r = ("M14", "cercano")
    return {"i": None, "lote": "S162", "c": c, "h": h, "w": w, "vol": vol, "hora": f"2026-05-{dia:02d} 05:00",
            "tramo": tramo, "z": 20.0, "bloque": f"{vol}|2026-05-{dia:02d}", "prot": prot, "mir": mir, "tabla": True,
            "part": False, "K": K, "VK": None, "X": {a: X, r: K}, "V": {a: V if X else 0.0, r: V if K else 0.0},
            "npix": {a: int(X), r: int(K)}}


def prueba_2():
    A, R = ("A", "cercano"), ("M14", "cercano")
    # a. nulo
    f = [fila("pos_bajo", "V", d, X=True, K=True) for d in range(1, 11)]
    for x in f:
        x["X"][A] = x["X"][R]
    p = EV.p2(f, A, R)
    assert p["B"] == 0 and p["veredicto"] == "SIN SUSTRATO", p
    # b. pierde 10 noches
    f = [fila("pos_bajo", "V", d, X=False, K=True) for d in range(1, 11)]
    p = EV.p2(f, A, R)
    assert p["veredicto"] == "PIERDE" and p["p"]["pierde"] == [1, 1024] and abs(p["neto"] - 10) < 1e-9, p
    p3 = EV.p2(f[:3], A, R)
    assert p3["veredicto"] == "SIN SUSTRATO", p3
    f6 = [fila("pos_bajo", "V", d, X=False, K=True) for d in range(1, 6)] + [fila("pos_bajo", "V", 6, X=True, K=False)]
    p6 = EV.p2(f6, A, R)
    assert p6["veredicto"] == "BLOQUEA" and p6["p"]["pierde"] == [7, 64], p6
    # mutación: las protegidas no son errores bajo 1 MW
    fm = f + [fila("pos_prot", "V", d, X=False, K=True, prot=True, mir=2.0) for d in range(11, 16)]
    assert abs(EV.p2(fm, A, R)["neto"] - 10) < 1e-9, "una protegida entró a P2"
    print("2a-b. nulo SIN SUSTRATO; 10 noches PIERDE p 1/1024; 3 noches SIN SUSTRATO; 5 contra 1 BLOQUEA; "
          "protegidas fuera de P2")
    # c. silencio
    N_neg = {"neg_pub": 133, "neg_resto": 3323}
    tk = 133 / 3456
    base = [fila("neg_pub", "V", 1 + d % 28, X=d < 7, K=True) for d in range(133)]   # apaga 126 de 133, como S159
    resto = [fila("neg_resto", "V", 1 + d % 28, w=3323 / 445) for d in range(445)]
    l = EV.lecturas(base + resto, A, np.random.default_rng(1), N_neg, tk)
    hi = l["silencio"]["neg_resto"]["ic_kish"][1]
    assert abs(hi - EV.wilson(0, 445)[1]) < 1e-12 and 0.0080 < hi < 0.0090, hi
    assert l["silencio"]["veredicto"] == "SILENCIO ACOTADO BAJO K", l["silencio"]
    for x in resto[:40]:
        x["X"][A] = True
        x["V"][A] = 0.1
    l2 = EV.lecturas(base + resto, A, np.random.default_rng(1), N_neg, tk)
    assert l2["silencio"]["veredicto"] == "ENCIENDE DE MAS", l2["silencio"]
    print(f"2c. silencio: 0 de 445 -> Wilson {hi:.4f}, SILENCIO ACOTADO BAJO K; 40 de 445 -> ENCIENDE DE MAS")
    # d. cota honesta con 0 de 45 y N = 3.348: K publica 20 negativos de 134 que el brazo apaga (ΔE puntual -134)
    N2 = {"neg_pub": 134, "neg_resto": 3348}
    pub = [fila("neg_pub", "V", 1 + d % 28, w=134 / 20, K=True, X=False) for d in range(20)]
    rs = [fila("neg_resto", "W", 1 + d % 28, w=3348 / 45) for d in range(45)]
    l3 = EV.lecturas(pub + rs, A, np.random.default_rng(1), N2, 134 / 3482)
    m = l3["MISSION_K"]
    assert m["dE"] < -100 and m["cota_honesta_sup"] > 0 and m["veredicto"] == "NO RESUELTO", m
    print(f"2d. cota honesta: ΔE {m['dE']:+.0f}, IC bootstrap {m['ic_boot'][1]:+.0f}, cota {m['cota_honesta_sup']:+.0f}"
          f" -> {m['veredicto']}")
    # e. elección por volcán sólo con T
    T = [fila("pos_bajo", "V", d, tramo="T", X=False, K=True) for d in range(1, 6)]
    O = [fila("pos_bajo", "V", d, tramo="O1", X=True, K=False) for d in range(10, 20)]
    el = EV.elegir_por_volcan(T + O, [A, R], None)
    assert el["V"] == R, el
    print("2e. elección por volcán: el brazo mejor en O y peor en T no se elige")
    # f. el peso
    g = [fila("neg_resto", "V", 1, w=10.0, X=True)] + [fila("neg_resto", "V", 2, w=1.0) for _ in range(9)]
    p, ic, ne = EV.tasa_ponderada(g, lambda x: x["X"][A])
    assert abs(p - 10 / 19) < 1e-12 and ne < 10, (p, ne)
    print(f"2f. ponderada {p:.3f} (cruda 0,100), n efectivo {ne:.2f}")


def prueba_3():
    """decidir() y repesar(): con C13 y C14 idénticos y mejores que M14 en 10 noches, sin perder protegidas de M14, el
    global es C13 (desempate por caja más chica); si C13 pierde una protegida que M14 publica, el global es C14; y el
    peso del subconjunto es N_h / n_h del subconjunto."""
    R, C13, C14 = ("M14", "cercano"), ("C13", "cercano"), ("C14", "cercano")
    def f(c, d, ok, prot=False):
        x = fila(c, "V", d, h="V|z<=40", tramo="T" if d < 6 else "O1", X=ok, K=True, prot=prot, mir=2.0 if prot else 0.5)
        x["X"] = {R: (not ok) if c == "pos_bajo" else True, C13: True, C14: True}
        x["V"] = {k: 0.5 for k in x["X"]}
        return x
    filas = [f("pos_bajo", d, True) for d in range(1, 11)] + [f("pos_prot", d, True, prot=True) for d in range(11, 14)]
    for x in filas[:10]:
        x["X"][R] = False
    meta = {"pos_bajo": {"V|z<=40": {"N": 100}}, "pos_prot": {"V|z<=40": {"N": 3}},
            "neg_pub": {}, "neg_resto": {}}
    fr = EV.repesar(filas, meta)
    assert abs(fr[0]["w"] - 10.0) < 1e-12 and abs(fr[-1]["w"] - 1.0) < 1e-12, (fr[0]["w"], fr[-1]["w"])
    N_neg = {"neg_pub": 1, "neg_resto": 1}
    d = EV.decidir(fr, N_neg, 0.5, np.random.default_rng(1), [R, C13, C14], R,
                   {"recall_bajo": 1.0, "recall_prot": 1.0}, "prueba")
    assert d["global"] == "C13" and d["candidatos"] == ["C13", "C14"], d["global"]
    assert d["valida_en_O"] == "VALIDA EN O", d["valida_en_O"]
    # si en O el compuesto es igual a M14, la validación no puede salir VALIDA (corrección del verificador)
    fo = [dict(x, X=dict(x["X"]), V=dict(x["V"])) for x in fr]
    for x in fo:
        if x["tramo"] != "T":
            x["X"][C13] = x["X"][C14] = x["X"][R]
    d3 = EV.decidir(fo, N_neg, 0.5, np.random.default_rng(1), [R, C13, C14], R,
                    {"recall_bajo": 1.0, "recall_prot": 1.0}, "prueba")
    assert d3["valida_en_O"] == "SIN SUSTRATO EN O", d3["valida_en_O"]
    fr[-1]["X"][C13] = False
    d2 = EV.decidir(fr, N_neg, 0.5, np.random.default_rng(1), [R, C13, C14], R,
                    {"recall_bajo": 1.0, "recall_prot": 1.0}, "prueba")
    assert d2["global"] == "C14", d2["global"]
    print("3. decidir: desempate a la caja más chica; validar en O exige GANA; una protegida perdida respecto de M14 saca al brazo; repesar ok")


def main():
    prueba_1()
    prueba_2()
    prueba_3()
    print("PRUEBAS DEL EVALUADOR OK")


if __name__ == "__main__":
    main()
