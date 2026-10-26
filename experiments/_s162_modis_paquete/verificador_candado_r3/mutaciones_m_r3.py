# Verificador r3: mutaciones sobre copia en memoria de m_con_regla_matlab.py; cual de ellas atrapa probar()
import sys, traceback
from pathlib import Path
P = Path(r"C:/vrp-trabajo/s162-modd/experiments/_s162_modis_paquete/m_con_regla_matlab.py")
src0 = P.read_text(encoding="utf-8")
MUT = {
 "sin_mutar": (None, None),
 "k_siempre_3": ("k = 3 if n <= 4 else (5 if n <= 30 else 7)", "k = 3"),
 "k_5_en_vez_de_7": ("(5 if n <= 30 else 7)", "(5 if n <= 30 else 5)"),
 "corte_30_a_20": ("(5 if n <= 30 else 7)", "(5 if n <= 20 else 7)"),
 "corte_4_a_2": ("k = 3 if n <= 4 else", "k = 3 if n <= 2 else"),
 "coef_mal": ("COEF_MODIS = 1.89e7 * 1.0 / 1e6", "COEF_MODIS = 1.89e7 * 1.0 / 1e6 * 1.001"),
 "regla_es_el_port": ("return DP.rellenar(enm, \"xy_fila_col\")[0]", "import mirova_port as MPX\n    return MPX.ORA._fillmissing2_lineal(enm)"),
 "regla_marco_col_fila_solo_en_regla": ("return DP.rellenar(enm, \"xy_fila_col\")[0]", "return DP.rellenar(enm, \"xy_col_fila\")[0]"),
 "mascara_traspuesta": ("m[int(q[0]), int(q[1])] = True", "m[int(q[1]), int(q[0])] = True"),
 "umbral_distintas_0": ("assert distintas >= 5", "assert distintas >= 0"),
 "pares_sin_filtro_pub_k": ("or not (EP._pub(f, \"K\") == 1 and EP._pub(f, \"PM\") == 1)", "or False"),
}
import os
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
for nombre, (a, b) in MUT.items():
    src = src0
    if a is not None:
        if src.count(a) != 1:
            print(nombre, "SUSTITUCION INVALIDA (%d)" % src.count(a)); continue
        src = src.replace(a, b)
    g = {"__file__": str(P), "__name__": "mut"}
    try:
        exec(compile(src, str(P), "exec"), g)
        if nombre == "mascara_traspuesta" or nombre == "pares_sin_filtro_pub_k":
            print(nombre, "probar() PASA (la mutacion esta fuera de probar)" if g["probar"]() is not None else "?")
        else:
            r = g["probar"]()
            print(nombre, "probar() PASA", r)
    except AssertionError as e:
        print(nombre, "ATRAPADA por aserción:", str(e)[:90])
    except Exception as e:
        print(nombre, "CAE por excepcion", type(e).__name__, str(e)[:90])
