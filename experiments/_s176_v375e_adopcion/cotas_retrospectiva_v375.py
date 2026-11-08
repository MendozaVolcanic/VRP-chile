# -*- coding: utf-8 -*-
"""S176: de dónde salen las cotas de investigación de la regla de reversión de VIIRS 375 (§4.4).

POR QUÉ. La regla pide investigar si la vía pierde más alertas débiles, o enciende más negativos, de lo que cabe esperar. MODIS
fijó sus cotas con los discordantes de su A/B: la tasa se lleva a los 120 días del plazo y la cota es el primer entero con una
falsa alarma baja (D1 y D2 de la regla de MODIS: 8 % y 7 %). VIIRS 375 tiene mucho más flujo y necesita las suyas. No se eligen
mirando los 5 días de noviembre ya vistos (A115): se miden aquí sobre la retrospectiva de V375-B y V375-C, anterior a la
ventana de noviembre, con el brazo C13 (la caja que la vía usa, PD1 de PREREGISTRO_E.md §7) y la regla «cercano» que decide.

Fuente, sin red: el evaluador sellado experiments/_s162_v375/evaluar.py (no se modifica; se ejecuta su texto con una línea
agregada que entrega las filas ya armadas y corta antes de leer resultados) sobre los artefactos de los runs 40116289866 (S162)
y 40131572769 (B2) y el de S159. Ventana O: 2026-06-13 a 2026-10-21, sin el 12, 13 y 17 a 20 de octubre.

Qué mide, por el peso de cada pasada en su estrato:
  (i) alertas Muy Bajo (de MIROVA, sobre 0,05 MW y bajo 1 MW, no protegidas) que K publica y el brazo C13 calla;
  (ii) negativos limpios en que K calla (clase neg_resto) y el brazo C13 publica: es exactamente la sobre-publicación diferencial
       que la vigilancia cuenta (`sobrepublicacion`).
Lo que NO mide: es el port (brazos.py), no la vía de pipeline/; PD3 los declara equivalentes (PREREGISTRO_E.md §3 paso 1). Y el
peso de cada pasada viene de una muestra estratificada: lo de 120 días es una estimación, no una medición.

Uso: python -I experiments/_s176_v375e_adopcion/cotas_retrospectiva_v375.py [carpeta de filas en caché]
"""
import json
import math
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EV = RAIZ / "experiments" / "_s162_v375" / "evaluar.py"
ART162 = r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866"
ART_B2 = r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"
ART159 = r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945"
TEMP = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\nmend\vrp-temporales\s176_guardia_viirs\cotas_v375")
BRAZO = ("C13", "cercano")
PLAZO = 120
FALSA_ALARMA_MAX = 0.08   # la mayor de las aceptadas en MODIS (D1 8 %, D2 7 %)


def filas_del_evaluador():
    """Corre el evaluador sellado hasta tener las filas (con la caché de brazos en una carpeta temporal)."""
    TEMP.mkdir(parents=True, exist_ok=True)
    salida = TEMP / "filas.json"
    if salida.exists():
        return json.loads(salida.read_text(encoding="utf-8"))
    src = EV.read_text(encoding="utf-8")
    ancla = "    filas = armar(obj, res, arms_por_id, inner, pub_k, vk, k_usa_recorrido, pesos)\n"
    assert src.count(ancla) == 1
    src = src.replace(ancla, ancla + "    globals()['_FILAS'] = (filas, obj); raise SystemExit(77)\n")
    g = {"__name__": "__main__", "__file__": str(EV)}
    sys.path.insert(0, str(EV.parent))
    sys.argv = ["evaluar.py", "--art162", ART162, "--art159", ART159, "--objetivos-extra",
                str(EV.parent / "b2" / "objetivos_v375_b2.json"), "--art-extra", ART_B2,
                "--deciden", "S162b", "--neg-pub-de", "S162", "--cache", str(TEMP / "cache_brazos.json"),
                "--salida", str(TEMP / "evaluar_salida.txt"), "--json", str(TEMP / "evaluar.json")]
    try:
        exec(compile(src, str(EV), "exec"), g)
    except SystemExit as e:
        assert e.code == 77, e.code
    filas, obj = g["_FILAS"]
    out = []
    for f in filas:
        pub = f["X"][BRAZO]
        out.append({"hora": f["hora"], "vol": f["vol"], "c": f["c"], "prot": f["prot"], "w": f["w"], "tramo": f["tramo"],
                    "mir": f["mir"], "K": f["K"], "brazo": pub, "part": f["part"],
                    "sat": obj[f["i"]].get("sensor")})
    salida.write_text(json.dumps(out), encoding="utf-8")
    return out


def p_mayor(lam, c):
    """P(Poisson(lam) > c)."""
    term, cdf = math.exp(-lam), 0.0
    for k in range(c + 1):
        cdf += term
        term *= lam / (k + 1)
    return 1 - cdf


def cota(lam):
    c = 0
    while p_mayor(lam, c) > FALSA_ALARMA_MAX:
        c += 1
    return c


def main():
    filas = filas_del_evaluador()
    excluidos = 6                                  # 12, 13 y 17 a 20 de octubre (EXCLUIDOS de evaluar.py)
    dias_o = (__import__("datetime").date(2026, 10, 21) - __import__("datetime").date(2026, 6, 13)).days + 1 - excluidos
    print(f"filas del evaluador: {len(filas)}; ventana O: {dias_o} días (2026-06-13 a 2026-10-21 sin 6 días excluidos)")
    for nombre, cond in (("con las tres plataformas (Suomi NPP incluido)", lambda f: True),
                         ("sólo NOAA-20 y NOAA-21 (el régimen desde el 2026-11-02)", lambda f: "SNPP" not in (f["sat"] or ""))):
        o = [f for f in filas if f["tramo"] in ("O1", "O2") and cond(f)]
        mb_base = [f for f in o if f["c"] == "pos_bajo" and not f["prot"] and f["mir"] > 0.05]
        mb = [f for f in mb_base if f["K"] and not f["brazo"]]
        neg_base = [f for f in o if f["c"] == "neg_resto"]
        neg = [f for f in neg_base if f["brazo"]]
        wmb, wneg = sum(f["w"] for f in mb), sum(f["w"] for f in neg)
        lam_mb, lam_neg = wmb * PLAZO / dias_o, wneg * PLAZO / dias_o
        print(f"\n== {nombre}")
        print(f"  (i) Muy Bajo que K publica y C13 calla: crudo {len(mb)} de {len(mb_base)}; ponderado {wmb:.1f}; "
              f"lambda {PLAZO} d = {lam_mb:.2f}; cota con falsa alarma <= {FALSA_ALARMA_MAX}: {cota(lam_mb)} "
              f"(falsa alarma {p_mayor(lam_mb, cota(lam_mb)):.3f})")
        print(f"  (ii) neg_resto que C13 publica y K calla: crudo {len(neg)} de {len(neg_base)}; ponderado {wneg:.1f}; "
              f"lambda {PLAZO} d = {lam_neg:.2f}; cota con falsa alarma <= {FALSA_ALARMA_MAX}: {cota(lam_neg)} "
              f"(falsa alarma {p_mayor(lam_neg, cota(lam_neg)):.3f})")
        print(f"  detalle (i), hasta 15: {[(f['vol'], f['hora'], f['mir']) for f in mb[:15]]}")
        print(f"  detalle (ii), hasta 15: {[(f['vol'], f['hora'], round(f['w'], 2)) for f in neg[:15]]}")
    # Control del instrumento (A110): un brazo que calla todo no puede dar pérdidas cero, y K contra K da cero.
    o = [f for f in filas if f["tramo"] in ("O1", "O2")]
    print("\ncontrol: K contra K, Muy Bajo que K publica y K calla:",
          sum(1 for f in o if f["c"] == "pos_bajo" and f["K"] and not f["K"]), "(tiene que ser 0)")
    print("control: un brazo que nunca publica perdería, de Muy Bajo que K publica:",
          sum(1 for f in o if f["c"] == "pos_bajo" and not f["prot"] and f["mir"] > 0.05 and f["K"]), "(tiene que ser mayor que 0)")


if __name__ == "__main__":
    main()
