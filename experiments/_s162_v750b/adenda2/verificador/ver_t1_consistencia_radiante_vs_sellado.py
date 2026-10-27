# -*- coding: utf-8 -*-
"""VAD2-01/T1: las filas 'radiante' del lector de posicion deberian ser las filas B0..B5 del analizador sellado sobre los
MISMOS resultados (es lo que el texto da a entender: radiante = record_cumulo del analizador, sin tocar).
Dos poblaciones: (A) sin pasadas con K distinto de produccion; (B) la misma mas una pasada con K != produccion.
Pregunta 1: si el lector estuviera roto, esta comparacion lo veria? Si: compara numeros de dos programas distintos.
Pregunta 2: instrumento muerto? Se comprueba que ambas salidas traen lineas (n > 0) y que A y B difieren en el sellado."""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import *

UNO = [(33, 34, 0.9)]
LEJOS = [(33, 34, 0.9), (33, 50, 5.0)]


def poblacion(con_kdist):
    p = Pob()
    for n in range(150):   # >100 pasadas: una sola con K distinto queda bajo el 1 % del sec.7 (compuerta abierta)
        p.pasada(f"2026-04-{1 + n % 28:02d} {n // 28:02d}:00", "neg_limpio", [])
    for n in range(3):
        p.pasada(f"2026-05-{1 + n:02d} 05:00", "pos", UNO, 0.4, dist_mirova=0.8, pub_prod=True)
    for n in range(4):   # PCC protegidas: B0 no ve nada, el resto si (abre el control positivo del sellado)
        p.pasada(f"2026-06-{1 + n:02d} 05:00", "pos", {"B0": [], "B1": UNO, "B2": UNO, "B3": UNO, "B5": UNO}, 2.0,
                 volcan="PuyehueCordonCaulle", dist_mirova=0.8, pub_prod=True)
    # una alerta protegida cuyo cumulo radiante cae lejos: radiante la pierde en todas las cajas
    p.pasada("2026-07-01 05:00", "pos", LEJOS, 2.0, dist_mirova=0.8, pub_prod=True)
    if con_kdist:
        # produccion publica, K del probe no: el analizador sellado la saca de TODOS los brazos (sec.7)
        p.pasada("2026-07-02 05:00", "pos", UNO, 0.4, dist_mirova=0.8, pub_prod=True, k_pub=False)
    return p


def lineas_sellado(txt, canal="decide", v="TO"):
    bloque = txt.split(f"== ventana {v}, canal {canal}")[1].split("== ventana")[0]
    out = {}
    for m in re.finditer(r"^   (B\d|K)\s+prot\s+(\d+) P1\s+(\d+) \| P1b abajo\s+(\d+) arriba\s+(\d+) \| E\s+(\d+) "
                         r"\(bajas sin publicar (\d+) de (\d+), neg publicados (\d+) de (\d+)\)", bloque, re.M):
        out[m.group(1)] = tuple(int(x) for x in (m.group(2), m.group(3), m.group(6), m.group(7), m.group(8), m.group(9), m.group(10)))
    return out


def lineas_lector(txt, canal="decide"):
    bloque = txt.split(f"canal {canal}); P2")[1].split("== alertas y negativos limpios")[0] if f"canal {canal}); P2" in txt else ""
    out = {}
    for m in re.finditer(r"^   (B\d) radiante\s+prot\s+(\d+) P1\s+(\d+) \| E\s+(\d+) \(bajas sin publicar (\d+) de (\d+), "
                         r"neg publicados (\d+) de (\d+)\)", bloque, re.M):
        out[m.group(1)] = tuple(int(x) for x in (m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7), m.group(8)))
    return out


for nombre, kd in (("A_sin_Kdistinto", False), ("B_con_Kdistinto", True)):
    d = TMP / "t1" / nombre
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    p = poblacion(kd)
    p.escribir(d)
    rca, outa = analizador(d)
    rcl, outl = lector(d)
    print(f"== {nombre}: analizador sellado rc={rca}, lector rc={rcl}")
    ctl = [l for l in outa.splitlines() if "K = producción" in l or "compuerta" in l]
    print("   ", *ctl, sep="\n    ")
    S = lineas_sellado(outa)
    # sellado: tupla (prot, P1, E, E_baja, n_baja, E_neg, n_neg) por caja; B4 = B0 aqui (Lascar)
    L = lineas_lector(outl)
    print("   lineas sellado:", len(S), "lineas lector radiante:", len(L))
    for c in ("B0", "B1", "B2", "B3", "B4", "B5"):
        s, l = S.get(c), L.get(c)
        marca = "IGUAL" if s == l else "DISTINTO"
        print(f"   {c}: sellado {s} | lector radiante {l} -> {marca}")
