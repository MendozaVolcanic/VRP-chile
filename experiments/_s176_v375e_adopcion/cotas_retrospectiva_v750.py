# -*- coding: utf-8 -*-
"""S176: de dónde salen las cotas de investigación de la regla de reversión de VIIRS 750 (§4.4).

POR QUÉ. El mismo método que para VIIRS 375 (cotas_retrospectiva_v375.py): la tasa de la retrospectiva, llevada a los 120 días
del plazo, y la cota con falsa alarma de 8 % o menos. No se miran los 5 días de noviembre (A115). Fuente, sin red: el analizador
sellado de V750-B (experiments/_s162_v750b/analizar_v750b.py, tag s162-v750b-sellado) sobre los artefactos de los runs
41615021658 y 41693265163, leídos el 2026-11-03; la población termina antes de la ventana P. El brazo B4 es la ROI que la vía usa
(`pipeline/grillas_mirova.yaml`, #939). El analizador no se modifica: se ejecuta su texto con un bloque agregado antes de sus
controles, que cuenta las discordancias de B4 contra K y corta.

Qué mide, en el canal que decide y en la ventana O (desde el 2026-06-13), sin y con Suomi NPP:
  (i) alertas bajo 1 MW que K publica y B4 calla; (ii) negativos limpios que B4 publica y K calla.

Uso: python -I experiments/_s176_v375e_adopcion/cotas_retrospectiva_v750.py
"""
import glob
import math
import sys
from pathlib import Path

ARBOL = Path(r"D:\vrp-trabajo\temporales\v750b_r4_20261103\arbol")
AN = ARBOL / "experiments" / "_s162_v750b" / "analizar_v750b.py"
TEMP = Path(r"D:\vrp-trabajo\temporales\v750b_r4_20261103")
PLAZO = 120
FALSA_ALARMA_MAX = 0.08


def p_mayor(lam, c):
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


BLOQUE = r'''
    import collections as _c, datetime as _d
    _orden = sorted(obj[i]["hora_utc"] for i in oks if obj[i]["hora_utc"] >= FRONTERA_OCR)
    print("== ventana O (canal que decide):", _orden[0], "a", _orden[-1], "pasadas", len(_orden))
    for _nombre, _cond in (("con Suomi NPP", lambda o: True), ("sin Suomi NPP", lambda o: "SNPP" not in o.get("sensor", ""))):
        _mb, _nb, _ng, _ngb, _lista_mb, _lista_n = 0, 0, 0, 0, [], []
        for i in oks:
            o = obj[i]
            e = etiqueta(o, "decide")
            if e is None or not ventana(o, "O") or not _cond(o):
                continue
            if e == "baja" and (o.get("mirova_vrp") or 0) > 0.05:
                _nb += 1
                if pub(i, "K") and not pub(i, "B4"):
                    _mb += 1; _lista_mb.append((o["volcan"], o["hora_utc"], o.get("mirova_vrp")))
            if e == "neg":
                _ng += 1
                if pub(i, "B4") and not pub(i, "K"):
                    _ngb += 1; _lista_n.append((o["volcan"], o["hora_utc"]))
        print(f"== {_nombre}: (i) bajas (sobre 0,05 MW) que K publica y B4 calla: {_mb} de {_nb}; (ii) negativos limpios que B4 publica y K calla: {_ngb} de {_ng}")
        print("   lista (i), hasta 15:", _lista_mb[:15])
        print("   lista (ii), hasta 15:", _lista_n[:15])
        globals().setdefault("_RES", {})[_nombre] = (_mb, _ngb)
    globals()["_ORDEN"] = _orden
    raise SystemExit(77)
'''


def main():
    src = AN.read_text(encoding="utf-8")
    ancla = "    # controles del instrumento de la ROI, DENTRO de la compuerta"
    assert src.count(ancla) == 1
    src = src.replace(ancla, BLOQUE + ancla)
    arts = sorted(glob.glob(str(TEMP / "sep" / "sellado" / "*")))
    sys.argv = ["analizar_v750b.py", "--art", *arts, "--objetivos", str(ARBOL / "experiments" / "_s162_v750b" / "objetivos_v750b.json"),
                "--sin-granulo", str(ARBOL / "experiments" / "_s162_v750b" / "sin_granulo_v750b.json"),
                "--evaluador", r"D:\vrp-trabajo\temporales\evaluar_d25_s161.py",
                "--censo-art", r"D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252",
                "--censo-objetivos", str(TEMP / "objetivos_censo_s159.json"),
                "--salida", str(TEMP / "nada_s176.txt")]
    g = {"__name__": "__main__", "__file__": str(AN)}
    sys.path.insert(0, str(AN.parent))
    try:
        exec(compile(src, str(AN), "exec"), g)
    except SystemExit as e:
        assert e.code == 77, e.code
    orden = g["_ORDEN"]
    from datetime import date
    ini, fin = date.fromisoformat(orden[0][:10]), date.fromisoformat(orden[-1][:10])
    dias = (fin - ini).days + 1
    print(f"días de la ventana O entre la primera y la última pasada: {dias}")
    for nombre, (mb, n) in g["_RES"].items():
        lmb, ln = mb * PLAZO / dias, n * PLAZO / dias
        print(f"{nombre}: lambda {PLAZO} d (i) {lmb:.2f} -> cota {cota(lmb)} (falsa alarma {p_mayor(lmb, cota(lmb)):.3f}); "
              f"(ii) {ln:.2f} -> cota {cota(ln)} (falsa alarma {p_mayor(ln, cota(ln)):.3f})")


if __name__ == "__main__":
    main()
