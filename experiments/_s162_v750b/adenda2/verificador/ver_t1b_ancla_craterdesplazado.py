# -*- coding: utf-8 -*-
"""VAD2-06 / T1b: lector 'radiante' contra analizador sellado B0..B5 sobre los MISMOS resultados, con el cráter corrido
del centro de la grilla (como en Cordón Caulle y Tupungatito) y píxeles alertados que caen summit con una ancla y far con
la otra. Compara canales decide y tabla.
Pregunta 1 (si el lector midiera desde el centro, esto lo vería): sí, la escena cambia de clase según el ancla; el control
positivo es la copia mutada M3 (ancla siempre el centro) con --mutado, que debe dar DISTINTO.
Pregunta 2 (instrumento muerto): se exige que el sellado imprima líneas (n > 0) y que la protegida de la escena se
pierda en alguna caja (P1 > 0), o la comparación no discrimina."""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import Pob, TMP, ADENDA2, V750B, EV, correr, lector, analizador  # noqa: E402

# cráter en (33, 28.5): el píxel (33, 36) está a 3 celdas (2,25 km, summit) del centro y a 7,5 celdas (5,6 km) del cráter:
# far con inner 5 km (Láscar), no con 7 (Tupungatito, que lo haría summit con las dos anclas)
CRATER = (33.0, 28.5)
EN_ANCLA = [(33, 36, 0.9)]
UNO = [(33, 29, 0.9)]


def poblacion():
    p = Pob()
    for n in range(40):
        p.pasada(f"2026-04-{1 + n % 28:02d} {n // 28:02d}:00", "neg_limpio", [], volcan="Tupungatito", crater=CRATER)
    for n in range(3):
        p.pasada(f"2026-05-{1 + n:02d} 05:00", "pos", UNO, 0.4, volcan="Tupungatito", crater=CRATER, dist_mirova=0.8,
                 pub_prod=True)
    for n in range(4):   # control positivo del sellado: B0 pierde protegidas de Cordón Caulle que B1 sí publica
        p.pasada(f"2026-06-{1 + n:02d} 05:00", "pos", {"B0": [], "B1": UNO, "B2": UNO, "B3": UNO, "B5": UNO}, 2.0,
                 volcan="PuyehueCordonCaulle", crater=CRATER, dist_mirova=0.8, pub_prod=True)
    # la escena que discrimina el ancla: summit si se mide desde el centro, far desde el cráter
    p.pasada("2026-07-01 05:00", "pos", EN_ANCLA, 2.0, volcan="Lascar", crater=CRATER, dist_mirova=0.8,
             pub_prod=True, k_pub=True)
    p.pasada("2026-07-02 05:00", "neg_limpio", EN_ANCLA, volcan="Lascar", crater=CRATER, k_pub=False)
    return p


def sellado(txt, canal):
    bl = txt.split(f"== ventana TO, canal {canal}")[1].split("== ventana")[0]
    return {m.group(1): tuple(int(x) for x in m.group(2, 3, 6, 7, 8, 9, 10)) for m in re.finditer(
        r"^   (B\d)\s+prot\s+(\d+) P1\s+(\d+) \| P1b abajo\s+(\d+) arriba\s+(\d+) \| E\s+(\d+) "
        r"\(bajas sin publicar (\d+) de (\d+), neg publicados (\d+) de (\d+)\)", bl, re.M)}


def lect(txt, canal):
    pat = f"canal {canal}); P2"
    bl = txt.split(pat)[1].split("== alertas y negativos limpios")[0] if pat in txt else ""
    return {m.group(1): tuple(int(x) for x in m.group(2, 3, 4, 5, 6, 7, 8)) for m in re.finditer(
        r"^   (B\d) radiante\s+prot\s+(\d+) P1\s+(\d+) \| E\s+(\d+) \(bajas sin publicar (\d+) de (\d+), "
        r"neg publicados (\d+) de (\d+)\)", bl, re.M)}


def main(mutado=None):
    d = TMP / ("t1b_mut" if mutado else "t1b")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    poblacion().escribir(d)
    rca, outa = analizador(d)
    if mutado:
        rc, outl = correr([sys.executable, mutado, "--art", d / "art", "--objetivos", d / "objetivos.json",
                           "--objetivos-supl", d / "supl.json", "--sin-granulo-supl", d / "sin_granulo_supl.json",
                           "--evaluador", EV, "--salida", d / "lector.txt", "--analizador", V750B / "analizar_v750b.py"])
    else:
        rc, outl = lector(d)
    print(f"analizador sellado rc={rca} | lector rc={rc if mutado else 'ver'}")
    print("   compuerta:", [l.strip() for l in outa.splitlines() if "compuerta" in l][:1])
    ok = True
    for canal in ("decide", "tabla"):
        S, L = sellado(outa, canal), lect(outl, canal)
        for c in ("B0", "B1", "B2", "B3", "B4", "B5"):
            igual = S.get(c) is not None and S.get(c) == L.get(c)
            ok &= igual
            print(f"   canal {canal} {c}: sellado {S.get(c)} | radiante {L.get(c)} -> {'IGUAL' if igual else 'DISTINTO'}")
    p1 = sellado(outa, "decide").get("B1", (0, 0))[1]
    print(f"   discrimina: P1 de B1 en el sellado = {p1} (tiene que ser 1: sólo la escena EN_ANCLA se pierde; con el centro como ancla sería 0)")
    print("RESULTADO:", "TODO IGUAL" if ok else "HAY DIFERENCIAS")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
