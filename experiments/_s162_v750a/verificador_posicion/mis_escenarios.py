# -*- coding: utf-8 -*-
"""Verificador de los brazos de posición de V750-A: escenarios PROPIOS (no los E61 a E73 del autor).

Preguntas del instrumento (cada escenario las responde con su control):
 1. Si lo que mido estuviera roto, ¿lo vería? Cada escenario fija una línea de salida que una rotura de UNA línea del
    analizador (mis mutaciones, mutar_propias.py) cambia.
 2. Si el instrumento estuviera muerto, ¿se vería distinto? Se reutiliza `correr` de la batería del autor (corre el
    analizador ENTERO con node), y cada escenario tiene `tiene` (líneas que deben estar) y `no_tiene`.

Uso: python mis_escenarios.py --dest <dir> --evaluador <evaluar_d25.py del tag> [--analizador <ruta>] [--solo W1,W2]
El analizador mutado tiene que vivir en esta carpeta (RAIZ se calcula desde AQUI.parents[1]: ver mutar_propias.py).
"""
import argparse
import sys
from pathlib import Path

AQ = Path(__file__).resolve().parent
sys.path.insert(0, str(AQ.parent))
import probar_evaluar_v750a as PR  # noqa: E402

PR.CRATER["Lastarria"] = [33, 33]     # radio interior de 3 km = 4 celdas EXACTAS de 0,75 km


def px_borde(volcan, celdas, extra_lejos=True):
    """Un alertado débil (M13 1,0) a `celdas` celdas al este del cráter y uno más radiante (2,0) a 27 celdas (20 km)."""
    f, c = PR.CRATER[volcan]
    return [[f, c + celdas, 2, 0.0, 1.0], [f, c + 27, 2, 0.0, 2.0]]


def px_anillo(volcan):
    """Borde de un cuadrado de 8 celdas de radio centrado en el cráter: 8-conexo, centroide EN el cráter (summit para el
    radiante), pero todos sus píxeles a 6 km o más (far para cercano y pico). El más radiante es una esquina."""
    f, c = PR.CRATER[volcan]
    pts = set()
    for k in range(-8, 9):
        pts.update({(f - 8, c + k), (f + 8, c + k), (f + k, c - 8), (f + k, c + 8)})
    px = [[a, b, 2, 0.0, 1.0] for a, b in sorted(pts)]
    px[0][4] = 2.0                     # el pico: una esquina del anillo (a 11,3 celdas)
    return px


def esc(volcan, dias, lab, px, mes, hora="06:00", K=None, P=0.3, mirova_vrp=0.4, tabla=True):
    def f(pb):
        for d in dias:
            pb.pasada(volcan, f"{mes}-{d:02d} {hora}", lab, K=K, P=P, px=px(volcan),
                      mirova_vrp=mirova_vrp if lab == "pos" else None, tabla=tabla)
    return f


def y(*fs):
    def f(pb):
        for g in fs:
            g(pb)
    return f


SEIS = range(1, 7)

ESC = {}

# W1: borde exacto del radio interior. Lastarria, 3 km = 4 celdas exactas: el más cercano a 3,0 km es summit (<=), igual
# que record_cumulo; a 5 celdas (3,75 km) es far. Sólo el brazo cercano cambia (el radiante y el pico miran el de 20 km).
ESC["W1"] = dict(
    pob=lambda: PR.base(extra=y(esc("Lastarria", SEIS, "pos", lambda v: px_borde(v, 4), "2026-05"),
                                esc("Lastarria", range(11, 17), "pos", lambda v: px_borde(v, 5), "2026-05"))), rc=0,
    tiene=[("   §6 bis cambian de publicación contra P (radiante), P-cercano: 6", ["Lastarria 2026-05-01 06:00"]),
           ("   §6 bis cambian de publicación contra P (radiante), P-pico: 0", [])])

# W2: anillo. El centroide del cúmulo del radiante cae EN el cráter (publica); el cercano y el pico quedan a 6 km o más
# (callan). 6 far_ref en el anillo: E_lejana del radiante 6, de los otros dos 0; los dos ganan P2'.
ESC["W2"] = dict(
    pob=lambda: PR.base(extra=esc("Villarrica", SEIS, "far_ref", px_anillo, "2026-09", hora="05:00")), rc=0,
    tiene=[("   §6 bis E + E_lejana P (radiante)", ["E_lejana 6"]),
           ("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -6, bloques 6)", "E_lejana 0"]),
           ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)", "E_lejana 0"]),
           ("   §6 bis pasadas lejanas", ["P (radiante) publica 6", "P-cercano publica 0", "P-pico publica 0"])])

# W3: elegible mira también tabla más OCR. Una protegida SÓLO del OCR (Láscar, O) que K y el radiante publican (anillo) y
# que el cercano y el pico pierden: con la tabla sola nadie la ve (P1 = 0), con tabla más OCR P1 = 1. Más 6 bajas
# «cerca y lejos» de la tabla que el cercano gana: sin la mirada del OCR el cercano sería elegido.
def _prot_ocr_anillo(pb):
    pb.pasada("Lascar", "2026-09-01 06:00", "pos", K=1.2, P=3.0, mirova_vrp=3.0, px=px_anillo("Lascar"), tabla=False)


ESC["W3"] = dict(
    pob=lambda: PR.base(extra=y(_prot_ocr_anillo,
                                esc("Lascar", range(10, 16), "pos", PR.px_cerca_lejos, "2026-09"))), rc=0,
    tiene=[("== §6 bis elegibles", ["P (radiante) sí", "P-cercano no", "P-pico no"]),
           ("   §6 bis P2' P-cercano", ["canal que decide GANA"]),
           ("== §6 bis posición elegida: P (radiante)", [])])

# W4: E_lejana con la tabla sola excluye las FALSO_POSITIVO_OCR. En O: 12 bajas SÓLO del OCR que el cercano gana
# (invisibles a la tabla sola) y 4 far_ref SÓLO del OCR que el cercano publica de más. El canal que decide en O es
# tabla más OCR: -12 + 4 en 16 bloques = GANA. La tabla sola no ve nada: SIN SUSTRATO con neto 0, que no es peor. Si la
# tabla sola contara el FALSO_POSITIVO_OCR, sería SIN SUSTRATO con neto +4 y el cercano no se elegiría.
ESC["W4"] = dict(
    pob=lambda: PR.base(extra=y(esc("Villarrica", range(1, 13), "pos", PR.px_cerca_lejos, "2026-09", tabla=False),
                                esc("Lascar", range(15, 19), "far_ref", PR.px_cerca_lejos, "2026-09", hora="05:00",
                                    tabla=False))), rc=0,
    tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -8, bloques 16)",
                                      "tabla sola SIN SUSTRATO (neto 0, bloques 0)"]),
           ("== §6 bis posición elegida: P-cercano", ["gana contra P"])])

# W5: el desempate cuenta E_lejana. Ganan los dos. «línea» (14 bajas): cercano y pico en el cráter. «cerca y lejos»
# (4 bajas): sólo el cercano. 6 far_ref «cerca y lejos»: el cercano las publica (E_lejana 6), el pico no. Cercano:
# E = base - 18, E_lejana 6, suma base - 12; pico: base - 14, suma base - 14. Gana el de menor suma: P-pico. Sólo con E
# (sin E_lejana) ganaría el cercano.
ESC["W5"] = dict(
    pob=lambda: PR.base(extra=y(esc("Lascar", range(1, 15), "pos", PR.px_linea, "2026-05"),
                                esc("Villarrica", range(1, 5), "pos", PR.px_cerca_lejos, "2026-05"),
                                esc("Villarrica", range(11, 17), "far_ref", PR.px_cerca_lejos, "2026-09", hora="05:00"))),
    rc=0,
    tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA"]),
           ("   §6 bis P2' P-pico", ["canal que decide GANA"]),
           ("== §6 bis posición elegida: P-pico", ["ganan los dos", "menor E + E_lejana"])])

# W6: distancia descriptiva de las far_ref (L27): sólo cuenta la fila FALSO_POSITIVO de la tabla, o del OCR desde el
# 2026-06-13. 3 de la tabla en abril, 2 sólo del OCR en abril (no entran) y 2 sólo del OCR en septiembre (entran): n = 5.
ESC["W6"] = dict(
    pob=lambda: PR.base(extra=y(esc("Lascar", (1, 2, 3), "far_ref", PR.px_cerca_lejos, "2026-04", hora="05:00"),
                                esc("Lascar", (4, 5), "far_ref", PR.px_cerca_lejos, "2026-04", hora="05:00", tabla=False),
                                esc("Lascar", (4, 5), "far_ref", PR.px_cerca_lejos, "2026-09", hora="05:00",
                                    tabla=False))), rc=0,
    tiene=[("   §6 bis distancia desde la celda central contra MIROVA, far_ref", ["n=5"])],
    no_contiene=[("   §6 bis distancia desde la celda central contra MIROVA, far_ref", "n=7")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--analizador", default=str(AQ.parent / "evaluar_v750a.py"))
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    sel = [x for x in a.solo.split(",") if x] or list(ESC)
    for nom in sel:
        est, det = PR.correr(nom, ESC[nom], Path(a.analizador), Path(a.evaluador), a.dest)
        print(f"{nom} | {est}" + (" | " + " ; ".join(det) if det else ""), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
