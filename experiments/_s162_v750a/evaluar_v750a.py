# -*- coding: utf-8 -*-
"""S162 V750-A, analizador pre-registrado (PREREGISTRO_V750A.md §4 a §7): el paquete del código de MIROVA (P) contra K
en VIIRS 750.

POR QUÉ. La adopción del paquete se decide midiendo contra MIROVA en las dos direcciones, con la regla escrita antes de
ver los datos (§6): no perder ninguna protegida que K publica (P1), no equivocarse más que K bajo 1 MW (P2, prueba de
signos por bloque noche-volcán, D-45) y medir la magnitud de MIROVA mejor que K y mejor que una ganancia pareja de K
(M con el comparador d′ de D-28/D-30/D-32 y el placebo K×1,2). Los controles (§7) se imprimen primero y, si caen, no
se imprime ningún veredicto; si la vía no reproduce al oráculo (§6.1), el censo no se mira.

QUÉ REUSA, SIN REIMPLEMENTAR NI COPIAR A MANO:
  * de experiments/_s162_v750b/analizar_v750b.py (sellado, tag s162-v750b-sellado): la carga de artefactos, la partida
    de cada pasada (observada / fuera / sin cráter / SIN DATO), el record del cúmulo 8-conexo del píxel alertado más
    radiante con la distancia medida desde el cráter (record_cumulo), el record de K para el predicado (slim), los
    tramos de cenit, la frontera del OCR y la extracción con ast de la prueba de signos de D-45 con el sha256 del
    evaluador fijado (cargar_signos). Las etiquetas, P2 y el nulo del contador viven dentro del main() de ese archivo y
    no se pueden importar: se copian aquí con la misma lógica y se marca cada copia.
  * de experiments/_s157_prereg_d25/evaluar_d25.py del tag s161-d25-lectura (mismo sha256): M entera, extraída con ast
    (decidir_estrato con su bootstrap por bloques, la calibración simétrica, comparar_con_ganancia con d′ y sus
    constantes selladas), sin importar el resto del evaluador de D25.

Brazos (§3): K (producción, control), Kgemelo (K en otro proceso del mismo runner, nulo), K×1,2 (placebo, se arma aquí
desde K como en evaluar_d25.py: VRP de K por 1,2, el resto igual), Kgeo (diagnóstico de V750-D, sólo informa), P, P-def
y O (salidas del .m sobre la grilla GEO: npix, vrp_mw, píxeles y diagnóstico), P-sinfiltro (el record de P con la
distancia neutralizada, publicado por el mismo predicado).
Brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27): P (radiante, el record de record_cumulo sin tocar),
P-cercano y P-pico. Los tres salen de los MISMOS píxeles de paquete.P: misma detección, mismo VRP, mismo cúmulo; sólo
cambia el punto desde donde se mide la distancia al cráter (pos_crater), y con ella la clase summit o far que decide si el
tablero publica. Cercano = el alertado más cercano al cráter, desempate por (distancia, fila, columna); pico = el de mayor
M13, con el desempate de max(). Es la misma regla de experiments/_s162_v750b/adenda2/leer_posicion_v750b.py (punto y
record_pos), copiada aquí y marcada (punto_pos, rec_pos) para que el medidor de mutaciones la pueda romper. La regla del
§6 bis (elegible, gana, desempate, NINGUNA POSICIÓN ELEGIBLE) se aplica en el censo antes del §6, y el §6 se evalúa
después sobre el brazo elegido como «P». La vara suma E_lejana: las pasadas far_ref en que el brazo publica (P2' = la
prueba de signos de D-45 sobre E + E_lejana por bloque noche-volcán). Las lecturas L20 a L28 de LECTURAS_EVALUAR_V750A.md
fijan lo que el texto deja abierto.

Formato de los artefactos (contrato para el probe o el cálculo local que los produzca):
  objetivos: lista de {id, volcan, hora_utc "AAAA-MM-DD HH:MM", sensor, lab ("pos" | "neg_limpio" | "far_ref" | otro),
    decide, alerta_tabla, protegida, mirova [filas], mirova_vrp, pub_prod, pc_vrp, z (cenit del sensor), pos_crater [f, c]}
    Las pasadas far_ref (MIROVA publicó una fuente lejana: fila FALSO_POSITIVO y ninguna ALERTA, etiqueta de
    banco_paridad) van en la MISMA lista, como la objetivos_run_v750b.json de la adenda 2 de V750-B; sus filas mirova
    traen el tipo FALSO_POSITIVO (tabla) o FALSO_POSITIVO_OCR (OCR) con su dist_km. etiqueta() les da None: no entran a
    P1, P2, M ni E, sólo a E_lejana y a las descriptivas del §6 bis (L20, L21).
  resultados_*.json: lista de {id, estado, dayflag, cobertura {nan_7_crater, nan_crater},
    brazos {K, Kgemelo, [Kgeo], [P en la sombra]: {record}}, paquete {P, Pdef, O: salida del .m}, banda_triangulacion}
  salida del .m: {npix, vrp_mw, pixeles [[fila, col, zona, -, M13]], diag {pasada1, pasada2: {sd_nti, sd_eti,
    u_nti1, u_nti2, u_eti1, u_eti2}, celda_decisiva: {pase, zona, c_nti, c_eti}}}
Las lecturas tomadas donde el pre-registro deja algo abierto están en LECTURAS_EVALUAR_V750A.md.

Régimen de la sombra (S173, VPR939-03; LECTURA LR1): en la fase sombra cada pasada observada se lee con la ROI y el sha
del código con que corrió, tomados del record de P (`diag_codigo_mirova.roi`, `regimen.codigo_sha`). La lectura declara
su brazo de ROI (`--roi-brazo`, el mismo B0 a B5 de V750-B, traducido por volcán con scripts/roi_v750b_a_grillas.py) y,
si quiere, el primer commit de código que acepta (`--sha-desde`, por ascendencia en git). Sin `--roi-brazo` la compuerta
se cierra: ninguna lectura de la sombra mezcla la ROI B0 con la B4 (A104).
Segunda vuelta (S174, VPR945; LECTURA LR2): la sombra no dice CUMPLE antes de las 4 semanas del §4.3 (dice PROVISORIO y
sale 4; el reloj corre sobre las pasadas leídas y, con `--sha-desde`, desde la hora del commit del corte); un volcán que
no está en el mapa de ROI es SIN DATO, no «otra ROI»; con 0 pasadas observadas la compuerta se cierra con su propio
mensaje; `--sha-desde` sólo acepta un sha (completo o abreviado) y se imprime resuelto entero.
Tercera vuelta (S174, VPR945-R2; LECTURA LR3): `--sha-desde` es obligatorio en la sombra; la lectura es una ventana que
empieza en lo más tardío entre el 2026-11-03 (§4.3) y la hora del commit del corte, y sólo entran las pasadas de esa
ventana cuyo código desciende del corte; una pasada de otra ROI con código posterior al corte (la ROI de ese volcán cambió
dentro de lo que se lee) cierra la compuerta; CUMPLE exige 28 días y además 14 noches distintas con datos (noche = fecha
UTC de la pasada, la misma clave del bloque de P2), contados sobre las mismas pasadas que se leen.
Quinta vuelta (S174, VPR945-R4; LECTURA LR3): la ventana es fija y ningún dato mueve el reloj. Inicio = lo más tardío
entre el 2026-11-03 00:00 UTC y la hora del committer del commit de --sha-desde (al minuto); fin = inicio + 28 días (sin
incluir); «ahora» = --ahora o, si no se da, el reloj UTC de la máquina que corre la lectura. Sólo se leen las pasadas de
[inicio, min(fin, ahora)]: las posteriores se cuentan aparte como «fuera de ventana», por volcán. Las 4 semanas son tramos
fijos de 7 días desde el inicio. CUMPLE exige que ahora haya llegado al fin, 5 noches distintas en cada semana y 14 en
total, en el conjunto y en cada volcán cuya ROI difiere de B0; los otros volcanes se imprimen por semana y no deciden.
⚠️ Sexta vuelta (S174, VPR945-R5; decisión de Nicolás del 2026-11-06, A113: el «no deciden» de arriba queda rebajado):
cada volcán de ROI igual a B0 pide 14 noches distintas dentro de la ventana (sin mínimo semanal); cada noche cuenta una
sola vez, en la semana de su primera pasada leída; --ahora acepta ISO con o sin zona y se convierte a UTC.

Uso: python evaluar_v750a.py [--fase censo|sombra] --art <carpetas> --objetivos objetivos_v750a.json
     --evaluador <evaluar_d25.py del tag> [--sin-granulo <archivo>] [--equivalencia-local <salida verde + mutaciones>]
     [--roi-brazo B0..B5] [--sha-desde SHA] [--ahora "AAAA-MM-DD HH:MM[:SS]"] [--leer-con-faltantes MOTIVO]
     [--solo-controles] [--salida <archivo>]
     (en la fase sombra, --roi-brazo y --sha-desde son obligatorios; --ahora es UTC y, si falta, es el reloj de la máquina)
Salida: 0 con veredicto; 3 compuerta cerrada (controles caídos o SIN DATO); 4 sombra PROVISORIA (ahora no llegó al
        fin de la ventana, o falta una semana con sus 5 noches o las 14 noches: no es CUMPLE ni NO CUMPLE); 5 veredicto (o PROVISORIO) leído con
        faltantes (marcado); 6 §6.1 no se cumple (la vía no reproduce al oráculo: no se mira el censo).
"""
from __future__ import annotations

import argparse
import ast
import collections
import copy
import datetime
import functools
import hashlib
import json
import math
import random
import re
import statistics
import subprocess
import sys
import types
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
sys.path.insert(0, str(RAIZ / "experiments/_s162_v750b"))
import banco_paridad as B  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
import analizar_v750b as AB  # noqa: E402
import roi_v750b_a_grillas as RV  # noqa: E402

PAQUETE = ("P", "Pdef", "O")
VENTANAS = ("T", "O")                    # §4.2: T tabla sola hasta el 2026-06-12, O desde el 2026-06-13
CANALES = ("tabla", "todo")              # §6.2: con la tabla sola Y con tabla más OCR
GANANCIA_PLACEBO = 1.2                   # §3, programa §2
TOL_VRP_EQUIV = 1e-6                     # §4.1: VRP a 1e-6 MW en el runner
BANDA_RAZON = (0.9, 1.1)                 # §6.2: mediana de la razón de P en las protegidas
MIN_MUT_LOCAL = 6                        # §6.1: las 6 mutaciones del §4.1 atrapadas (L2, resuelta por D-48: era «5 de 5»)
TMAX_FILTROS_ARTEFACTO = 278.15          # §7 (L7): isCirrusArtifact (<273,15 K) e isDiffuseFieldArtifact (<278,15 K)
TOPE_TABLERO_MW = 50000.0                # §7 (L7, VB-A01): mirovaEqVrp devuelve 0 sobre 50.000 MW (index.html:1182)
MUT_LOCAL = ("k1_y_minimos", "ocho_vecinos", "fondo_sin_halo", "recorte", "fondo_anillo", "remuestreo_vecino")
MIN_CASOS_LOCAL = (1020, 10)             # §4.1: 510 grillas de N con 2 cajas (E1) y los 10 recortes nativos de R2 (E3)
PARES_S1 = (("P", "Pdef"), ("P", "O"), ("Pdef", "O"))   # §5, S-1: los brazos que comparten la detección del .m
VOL_ROI = "PuyehueCordonCaulle"          # §7, control positivo de la ROI
DIAS_MIN_SOMBRA = 28                     # §4.3: la sombra corre «al menos 4 semanas» (S174, VPR945-01, LECTURA LR2)
NOCHES_MIN_SOMBRA = 14                   # S174 (VPR945-R2-01, LECTURA LR3): decisión de Nicolás, «14 noches» distintas
# S174 (VPR945-R4, quinta vuelta, LECTURA LR3; decisión de Nicolás, frase literal «Ventana fija, una vuelta»): la
# ventana de la sombra es fija, [inicio, inicio + 28 días), y se parte en 4 semanas fijas [inicio + 7k, inicio + 7(k+1)).
SEMANAS_SOMBRA = 4
SEMANA = datetime.timedelta(days=7)
# Decisiones de la coordinadora (default reversible, Nicolás no eligió; LR3 las deja pendientes de confirmar):
NOCHES_MIN_SEMANA = 5                    # noches distintas con datos que pide cada una de las 4 semanas
SEMANA_EXIGE_SIN_CAMBIO = False          # False: la exigencia por semana (y las 14) sólo en el conjunto y en los volcanes
                                         # cuya ROI difiere de B0; los que no cambiaron se imprimen y no deciden
                                         # ⚠️ S174 (R5-03, A113): «no deciden» rebajado; piden NOCHES_MIN_SIN_CAMBIO
# S174 (VPR945-R5-03, sexta vuelta; decisión de Nicolás del 2026-11-06, «Sí, sexta vuelta»). POR QUÉ: lo que se decide
# es el detector de VIIRS 750 en los once volcanes, y con la exigencia sólo en el conjunto y en los dos cambiados la
# sombra daba CUMPLE con datos de 2 de 11 (el verificador lo reprodujo). Cada volcán de ROI igual a B0 pide este número
# de noches distintas dentro de la ventana; no se le pide el mínimo semanal (los del sur, nublados, dejarían la lectura en
# PROVISORIO sin remedio dentro de la misma ventana).
NOCHES_MIN_SIN_CAMBIO = 14
INICIO_SOMBRA = "2026-11-03 00:00"       # §4.3: «Desde el 2026-11-03 (sin Suomi NPP: otro régimen [...])» (VPR945-R2-03)
POS = ("P", "Pcercano", "Ppico")         # §3 y §6 bis: brazos de posición (P es el radiante, el de hoy)
NOM_POS = {"P": "P (radiante)", "Pcercano": "P-cercano", "Ppico": "P-pico"}
SENSOR_N3, FRONTERA_N3 = "VIIRS_SNPP_750", "2026-10-09"   # §6 ter (N-3, S166): Suomi NPP sólo del OCR, antes del 9-oct

NOMBRES_M = ("N_BOOT", "SEMILLA", "N_MIN_PARES", "N_MIN_NOCHES", "N_CALIB", "MAX_FALSOS_CALIB",
             "MIN_VOLCANES_MEJORA", "MIN_PARES_VOLCAN", "MIN_PARES_PODER", "PLACEBO_GANANCIAS", "NOTA_COMPARADOR",
             "SEMILLA_CALIB_DPRIMA", "N_CALIB_DPRIMA", "NOTA_CALIB_DPRIMA", "DEC_DPRIMA",
             "pesos_bloque", "medianas_ponderadas", "medianas_ponderadas_filas", "regla_m", "d_par", "calibrar",
             "calibrar_simetrico", "comparar_con_ganancia", "decidir_estrato")


def cargar_m(ruta):
    """Extrae de evaluar_d25.py (tag s161-d25-lectura), con ast y en el orden del archivo, el texto literal de M y de
    sus constantes selladas, y lo ejecuta aparte (como AB.cargar_signos con la prueba de signos). Falla si el archivo no
    es el del tag o si falta alguna pieza."""
    crudo = Path(ruta).read_bytes()
    assert hashlib.sha256(crudo).hexdigest() == AB.SHA_EVALUADOR, "evaluar_d25.py no es el del tag s161-d25-lectura"
    src = crudo.decode("utf-8")
    piezas = []
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.FunctionDef):
            nombres = {nodo.name}
        elif isinstance(nodo, ast.Assign):
            nombres = {e.id for t in nodo.targets for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                       if isinstance(e, ast.Name)}
        else:
            continue
        if nombres & set(NOMBRES_M):
            piezas.append((nombres, ast.get_source_segment(src, nodo)))
    faltan = set(NOMBRES_M) - set().union(*(n for n, _ in piezas))
    assert not faltan, f"evaluar_d25.py sin {faltan}"
    m = types.ModuleType("m_d28")
    m.__dict__.update({"collections": collections, "np": np, "math": math})
    exec(compile("\n\n".join(t for _, t in piezas), str(ruta), "exec"), m.__dict__)
    assert (m.N_BOOT, m.SEMILLA, m.SEMILLA_CALIB_DPRIMA, m.N_CALIB_DPRIMA, m.DEC_DPRIMA) == (10000, 157, 160, 1000, 12)
    assert m.PLACEBO_GANANCIAS[0] == GANANCIA_PLACEBO
    return m


# ---------------------------------------------------------------- etiquetas (copia de analizar_v750b.main)
def prot_tabla(o):
    return any(alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS")


def etiqueta(o, canal):
    """'prot', 'baja' (alerta bajo 1 MW que decide), 'neg' o None. Copia literal de la de analizar_v750b.py: canal
    'tabla' (sólo la tabla de MIROVA), 'todo' (tabla más OCR) o 'decide' (tabla sola en T, tabla más OCR en O)."""
    if canal == "decide":
        canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"
    if o["lab"] == "neg_limpio":
        return "neg"
    if o["lab"] != "pos" or not o.get("decide"):
        return None
    if canal == "tabla" and not o.get("alerta_tabla"):
        return None
    p = prot_tabla(o) if canal == "tabla" else o.get("protegida")
    return "prot" if p else "baja"


def es_n3(o):
    """§6 ter (N-3): protegida que existe sólo por el OCR (sin alerta de la tabla), de Suomi NPP y anterior al
    2026-10-09. No veta en el P1 del §6 bis ni en el del §6.2; se lista aparte y su P1 se imprime al lado. La magnitud M,
    E y la sombra (§6.3) no cambian."""
    return (bool(o.get("protegida")) and not o.get("alerta_tabla") and o.get("sensor") == SENSOR_N3
            and o["hora_utc"] < FRONTERA_N3)


def en_ventana(o, v):
    h = o["hora_utc"]
    return v == "TODO" or (v == "T" and h < AB.FRONTERA_OCR) or (v == "O" and h >= AB.FRONTERA_OCR)


# ---------------------------------------------------------------- §6 bis, brazos de posición
def corta(lst, n=20):
    """VP-01 (verificador de posición), como VAD2-11 de V750-B: una lista impresa que se corta lo dice."""
    lst = list(lst)
    return str(lst[:n]) + (f" (y {len(lst) - n} más, cortada a {n})" if len(lst) > n else "")


def etiqueta_lejana(o, canal):
    """§6 bis (LECTURA L20): ¿la pasada es far_ref para el canal? MIROVA vio el calor y lo ubicó lejos del cráter, así
    que publicarla como cumbre es publicar de más. Con la tabla sola cuenta sólo si la fila FALSO_POSITIVO es de la
    tabla (el FALSO_POSITIVO_OCR es etiqueta del scraper, A11); con tabla más OCR, toda far_ref; 'decide' es la tabla
    sola en T y tabla más OCR en O, como etiqueta()."""
    if o.get("lab") != "far_ref":
        return False
    if canal == "decide":
        canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"
    if canal == "tabla":
        return any(str(f.get("tipo", "")).startswith("FALSO_POSITIVO") and f.get("source") == "CONS"
                   for f in o.get("mirova") or [])
    return True


def punto_pos(o, brazo, ancla):
    """(fila, columna) del punto que ubica el record según el brazo de posición (§3). Copia de
    experiments/_s162_v750b/adenda2/leer_posicion_v750b.py::punto (misma regla y mismo desempate; se copia y no se
    importa para que el medidor de mutaciones rompa ESTE archivo): radiante, el centroide del cúmulo 8-conexo del alertado
    de mayor M13 (el de AB.record_cumulo); cercano, el alertado más cercano al ancla, desempate por (distancia, fila,
    columna); pico, el alertado de mayor M13, con el desempate de max() (el primero de la lista, el que siembra el
    cúmulo). `o` es la salida del .m con algún alertado."""
    px = o["pixeles"]
    if brazo == "Pcercano":
        p = min(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))
        return float(p[0]), float(p[1])
    if brazo == "Ppico":
        p = max(px, key=lambda p: p[4])
        return float(p[0]), float(p[1])
    cu = AB.cumulo_del_mas_radiante(px)
    return float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))


# ---------------------------------------------------------------- S-1 (§5, obligatorio, no decide)
def _u(dg, pase, zona, x):
    """Umbral contextual del .m para la celda: zonas 0 y 1 usan u1, la zona 2 usa u2 (.m l. 389-399)."""
    return dg[f"pasada{pase}"][f"u_{x}{2 if zona == 2 else 1}"]


def diag_valido(dg):
    try:
        cd = dg["celda_decisiva"]
        vals = [cd["c_nti"], cd["c_eti"]] + [dg[f"pasada{p}"][k] for p in (1, 2) for k in
                                              ("sd_nti", "sd_eti", "u_nti1", "u_nti2", "u_eti1", "u_eti2")]
        return cd["pase"] in (1, 2) and cd["zona"] in (0, 1, 2) and all(
            v is not None and math.isfinite(v) for v in vals) and all(
            _u(dg, cd["pase"], cd["zona"], x) != 0 for x in ("nti", "eti"))
    except (KeyError, TypeError):
        return False


def margenes(dg):
    """(b) margen de la celda decisiva del cráter contra su umbral: c / u en NTI y en ETI."""
    cd = dg["celda_decisiva"]
    return tuple(cd[f"c_{x}"] / _u(dg, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))


def alerta_celda(dg_celda, dg_umbral):
    """¿La celda decisiva de un brazo alerta con los umbrales de otro? El .m exige los dos tests a la vez (l. 389-399)."""
    cd = dg_celda["celda_decisiva"]
    return all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))


def decidida_por_escena(dA, dB):
    """(c) Con la celda decisiva del cráter QUIETA, el solo cambio de umbral entre los dos brazos (que viene de la media
    y la sd de toda la grilla) cambia su alerta, en una dirección o en la otra."""
    return alerta_celda(dA, dA) != alerta_celda(dA, dB) or alerta_celda(dB, dB) != alerta_celda(dB, dA)


def delta_sd(dA, dB):
    """(a) cambio de sd del contraste NTI y ETI en el primer y el segundo pase, del brazo A al B."""
    return {f"{x}{p}": dB[f"pasada{p}"][f"sd_{x}"] - dA[f"pasada{p}"][f"sd_{x}"] for x in ("nti", "eti") for p in (1, 2)}


@functools.lru_cache(maxsize=None)
def es_ancestro(desde, sha):
    """S173 (VPR939-03): True si el commit `desde` es ancestro de `sha` o el mismo, False si no, None si git no conoce
    alguno de los dos (el sha de la corrida no está en este clon): eso no se adivina, es SIN DATO."""
    o = subprocess.run(["git", "-C", str(RAIZ), "merge-base", "--is-ancestor", desde, sha], capture_output=True)
    return {0: True, 1: False}.get(o.returncode)


def resolver_commit(x):
    """S174 (VPR945-04): el sha completo del commit `x`, o "" si `x` no es un sha (completo o abreviado, 7 caracteres o
    más) de un commit de este clon. POR QUÉ: una referencia móvil (HEAD, origin/main, una rama, `X^{commit}`) cambia de
    significado según el clon y el día, y una lectura sellada con ella no se puede reproducir ni auditar después; por eso
    el texto tecleado tiene que ser el comienzo del sha al que git lo resuelve."""
    o = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "--verify", "--quiet", f"{x}^{{commit}}"],
                       capture_output=True, text=True)
    sha = o.stdout.strip()
    return sha if o.returncode == 0 and len(x) >= 7 and sha.startswith(x) else ""


def fecha_commit(sha):
    """Hora del commit (UTC, "AAAA-MM-DD HH:MM"). En main, con merge squash de GitHub, es la hora del merge: desde ahí
    corre en la sombra el código nuevo."""
    o = subprocess.run(["git", "-C", str(RAIZ), "show", "-s", "--format=%ct", sha], capture_output=True, text=True)
    t = o.stdout.strip()
    if o.returncode != 0 or not t.isdigit():
        return ""                          # S174 (R2): sin la hora no hay ventana; el llamador cierra la compuerta
    return datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")


def hora_dt(h):
    """S174 (VPR945-R4): «AAAA-MM-DD HH:MM» (o con «:SS») a datetime UTC sin zona, para comparar con la ventana fija."""
    return datetime.datetime.fromisoformat(h.strip().replace("T", " "))


def arg_ahora(x):
    """--ahora: fecha ISO, con o sin zona («AAAA-MM-DD HH:MM[:SS]», con «T» o espacio, y «Z» o «±HH:MM»). Sin zona se lee
    como UTC. S174 (VPR945-R5-01). POR QUÉ: un workflow que pase `date -u -Iseconds` trae la zona, y comparar una fecha
    con zona contra las de la ventana (sin zona) tumbaba el lector con TypeError. Una zona distinta de UTC se convierte a
    UTC, no se ignora (ignorarla corre «ahora» tantas horas como la zona); el resultado queda sin zona, como el resto.
    S174 (VPR945-R6-01): la conversión va dentro del try y también se captura OverflowError. POR QUÉ: una fecha con zona
    que al pasarla a UTC sale del rango de datetime (año 9999 con zona negativa, año 1 con zona positiva) tumbaba el
    lector con traceback (salida 1) en vez de dar el error de argparse (salida 2) de una fecha que no se puede leer."""
    try:
        t = hora_dt(x)
        if t.tzinfo is not None:
            t = t.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except (ValueError, OverflowError):
        raise argparse.ArgumentTypeError(f"--ahora {x!r} no es una fecha ISO «AAAA-MM-DD HH:MM[:SS]» (UTC, o con zona "
                                         "«Z» o «±HH:MM»)")
    return t


def semanas_noches(horas, t_ini):
    """S174 (VPR945-R4, LECTURA LR3): (noches distintas en cada una de las 4 semanas fijas, noches distintas en total) de
    unas horas UTC. Semana k = [inicio + 7k días, inicio + 7(k+1) días); noche = fecha UTC de la pasada. POR QUÉ: en
    cuatro rondas el reloj y el reparto se anclaron a la primera y la última pasada, y una pasada suelta en una punta (o
    con fecha futura) los movía; con tramos fijos desde el inicio de la ventana ningún dato los mueve. Una fecha con
    pasadas a los dos lados del borde de una semana cuenta en las dos (tiene datos en las dos). Una hora fuera de las 4
    semanas no cuenta (la ventana ya las sacó de la lectura).
    ⚠️ S174 (VPR945-R5-02, sexta vuelta; decisión de Nicolás del 2026-11-06, A113: rebaja la frase «cuenta en las dos»
    de arriba, que se conserva): cada noche cuenta una sola vez, en la semana de su primera pasada dentro de las 4
    semanas. POR QUÉ: contada en las dos, una semana con 4 noches propias llegaba a 5 con la noche de la frontera (el
    verificador lo reprodujo); así el total es siempre la suma de las semanas. La definición de noche no cambia."""
    semana_de = {}
    for h in sorted(horas, key=hora_dt):
        k = (hora_dt(h) - t_ini) // SEMANA
        if 0 <= k < SEMANAS_SOMBRA:
            semana_de.setdefault(h[:10], k)
    c = [0] * SEMANAS_SOMBRA
    for k in semana_de.values():
        c[k] += 1
    return c, len(semana_de)


def faltan_noches(ns, n):
    """S174 (VPR945-R4): True si alguna de las 4 semanas tiene menos de NOCHES_MIN_SEMANA noches o el total no llega a
    NOCHES_MIN_SOMBRA (con 5 por semana el total es 20 o más y la de 14 se cumple sola; queda explícita por si el umbral
    por semana cambia). S174 (VPR945-R5-05): la regla de 14 de los volcanes cambiados y del conjunto es redundante con 5
    por semana (4 × 5 = 20) y ninguna prueba puede hacerla caer sola mientras el umbral semanal sea 4 o más (A116); se
    deja, sin quitarla, por si ese umbral baja de 4."""
    return min(ns) < NOCHES_MIN_SEMANA or n < NOCHES_MIN_SOMBRA


def leer_equivalencia_local(ruta):
    """§6.1, parte local: la salida de equivalencia_v750a.py contra el módulo real (VERDE) y su corrida --mutaciones."""
    if not ruta or not Path(ruta).exists():
        return False, "salida de la prueba local AUSENTE (SIN DATO)"
    lin = Path(ruta).read_text(encoding="utf-8").splitlines()
    casos = [tuple(int(n) for n in re.findall(r"E1 (\d+) casos, E3 (\d+) recortes", x)[0])
             for x in lin if x.startswith("VERDE:") and re.search(r"E1 \d+ casos, E3 \d+ recortes", x)]
    verde = (any(c[0] >= MIN_CASOS_LOCAL[0] and c[1] >= MIN_CASOS_LOCAL[1] for c in casos)
             and not any(x.startswith("ROJA") for x in lin))
    todas = any(x.strip() == "mutaciones: TODAS COMO SE ESPERA" for x in lin)
    n_atr = sum("atrapada por aserción" in x for x in lin)
    # VB-A06: las seis del §4.1 por nombre, no sólo seis líneas cualesquiera
    nombradas = [m for m in MUT_LOCAL
                 if any(re.search(rf"mutación {m}\s+atrapada por aserción", x) for x in lin)]
    caida = any("control_que_se_cae" in x and "caída" in x for x in lin)
    ok = verde and todas and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL) and caida
    return ok, (f"prueba local: verde con los casos del §4.1 {verde} {casos}, mutaciones todas como se espera {todas}, atrapadas {n_atr} "
                f"(mínimo {MIN_MUT_LOCAL}; las seis del §4.1 por nombre: {len(nombradas)} de {len(MUT_LOCAL)}), control caído {caida}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=("censo", "sombra"), default="censo")
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura (sha256 fijado)")
    ap.add_argument("--sin-granulo", default=str(AQUI / "sin_granulo_v750a.json"))
    ap.add_argument("--equivalencia-local", default="",
                    help="salida de equivalencia_v750a.py contra el módulo real y con --mutaciones (§6.1)")
    ap.add_argument("--leer-con-faltantes", default="",
                    help="MOTIVO de la decisión de leer con cobertura insuficiente; veredicto marcado y salida 5")
    ap.add_argument("--solo-controles", action="store_true")
    ap.add_argument("--roi-brazo", choices=("B0", "B1", "B2", "B3", "B4", "B5"), default="",
                    help="fase sombra: brazo de ROI de V750-B que se lee (obligatorio en la sombra; VPR939-03)")
    ap.add_argument("--sha-desde", default="",
                    help="fase sombra: sólo pasadas cuyo regimen.codigo_sha desciende de este commit (incluido)")
    ap.add_argument("--ahora", type=arg_ahora, default=None,
                    help="fase sombra: fecha de referencia en UTC, «AAAA-MM-DD HH:MM[:SS]» (las pruebas la fijan); si "
                         "falta, el reloj UTC de la máquina que corre la lectura (S174, VPR945-R4)")
    ap.add_argument("--salida", default=str(AQUI / "evaluar_v750a_salida.txt"))
    a = ap.parse_args(argv)
    EV = AB.cargar_signos(a.evaluador)
    EM = cargar_m(a.evaluador)
    censo = a.fase == "censo"
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    res = AB.cargar(a.art)
    inner = B.inner_desde_html()
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    def salir(cod):
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
        return cod

    def nombre(i):
        return f"{obj[i]['volcan']} {obj[i]['hora_utc']}"

    pr(f"== V750-A, fase {a.fase}")
    # ---------------------------------------------------------------- régimen de la sombra (S173, VPR939-03, LECTURA LR1)
    # POR QUÉ. El 2026-11-05 03:23 UTC #939 (58edb9788) cambió la ROI de la vía de VIIRS 750 en Cordón Caulle y
    # Tupungatito de def (B0) a sens (B4): la caja sensible, donde el código de MIROVA usa el umbral bajo, pasa a cubrir
    # el cráter. La sombra escribe con el sha de main de cada corrida, así que puede traer pasadas de los dos detectores, y
    # una pasada vieja metida en el denominador nuevo decide la lectura nueva (A104; con la mezcla del escenario ER1 el
    # lector de antes daba NO CUMPLE por una pasada de la ROI vieja). La ROI se lee del record, no de la fecha (S155: la
    # marca va en los datos): `diag_codigo_mirova.roi` es la caja con que corrió, `regimen.codigo_sha` el código.
    sin_regimen, fuera_regimen, sin_mapa = {}, {}, {}
    corte, fecha_corte, ventana_desde, cambia, esperada = "", "", "", [], {}
    # S174 (VPR945-R4, LECTURA LR3): «ahora» es la fecha de referencia de la ventana fija. Sin --ahora es el reloj UTC
    # de la máquina que corre la lectura (en Actions, el del runner); las pruebas lo fijan para ser deterministas.
    t_ahora = a.ahora or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)
    origen_ahora = "--ahora" if a.ahora else "reloj de esta máquina, UTC"
    if not censo:
        reg = {}
        for i in obj:
            r = res.get(i) or {}
            if AB.partida(r) != "observada":
                continue
            rp = ((r.get("brazos") or {}).get("P") or {}).get("record")
            if not isinstance(rp, dict):
                continue                       # falta_brazo la marca SIN DATO más abajo
            roi = (rp.get("diag_codigo_mirova") or {}).get("roi")
            sha = (rp.get("regimen") or {}).get("codigo_sha")
            if not roi or not sha:
                sin_regimen[i] = "sin_regimen"  # sin la marca no se sabe con qué ROI corrió: SIN DATO, no se adivina
                continue
            reg[i] = (roi, str(sha))
        tabla_reg = collections.defaultdict(list)
        for i, (roi, sha) in reg.items():
            tabla_reg[(obj[i]["volcan"], roi, sha[:9])].append(obj[i]["hora_utc"])
        pr("== régimen de la sombra (VPR939-03): pasadas observadas por volcán, ROI del record de P y codigo_sha")
        for (v, roi, sha), hs in sorted(tabla_reg.items(), key=lambda kv: tuple(map(str, kv[0]))):
            pr(f"   {v} {roi} {sha}: {len(hs)} ({min(hs)} a {max(hs)})")
        dos_roi = sorted(v for v in {k[0] for k in tabla_reg} if len({k[1] for k in tabla_reg if k[0] == v}) > 1)
        if not a.roi_brazo:
            pr(f"== régimen de la sombra: SIN --roi-brazo, compuerta cerrada (la lectura declara la ROI que lee; "
               f"volcanes con dos ROI en los datos: {dos_roi or 'ninguno'})")
            return salir(3)
        if not a.sha_desde:
            # S174 (VPR945-R2-02, decisión de la coordinadora, reversible). POR QUÉ: sin corte, las pasadas del código
            # viejo en los volcanes que no cambiaron ponen en marcha el reloj de las 4 semanas aunque el detector nuevo
            # de Cordón Caulle y Tupungatito lleve una sola noche (el verificador lo reprodujo: 28,1 de 28 días, CUMPLE).
            pr("== régimen de la sombra: SIN --sha-desde, compuerta cerrada (la lectura declara el commit desde el que "
               "lee: el que puso en la sombra el código y la ROI que se evalúan; sin él, las pasadas de otro código "
               "ponen en marcha el reloj de las 4 semanas)")
            return salir(3)
        corte = resolver_commit(a.sha_desde)
        if not corte:
            pr(f"== régimen de la sombra: --sha-desde {a.sha_desde} no es el sha (completo o abreviado) de un commit de "
               "este clon, compuerta cerrada (una referencia como HEAD u origin/main cambia según el clon y el día)")
            return salir(3)
        fecha_corte = fecha_commit(corte)
        if not fecha_corte:
            pr(f"== régimen de la sombra: no se pudo leer la hora del commit {corte} (git show), compuerta cerrada")
            return salir(3)
        # S174 (VPR945-R2-03, LECTURA LR3). POR QUÉ: la sombra empieza el 2026-11-03 (§4.3: antes es otro régimen de
        # plataformas, con Suomi NPP) y el código del corte no corrió antes de su commit; una noche anterior procesada con
        # el código nuevo es un reproceso, no sombra. La ventana es una sola para la lectura, el reloj y las noches.
        ventana_desde = max(INICIO_SOMBRA, fecha_corte)
        # S174 (VPR945-R4, LECTURA LR3; Nicolás: «Ventana fija, una vuelta»). POR QUÉ: en cuatro rondas el reloj de 28
        # días y el reparto de noches se anclaron a la primera y la última pasada leída, y una pasada suelta en una punta
        # (o con fecha futura) los movía; cada parche cerró una variante y abrió otra. La ventana se fija antes de mirar
        # los datos: fin = inicio + 28 días (sin incluir), y sólo se lee hasta min(fin, ahora). Lo posterior no entra a
        # la lectura y se cuenta aparte, por volcán.
        t_ini = hora_dt(ventana_desde)
        t_fin = t_ini + datetime.timedelta(days=DIAS_MIN_SOMBRA)
        t_lim = min(t_fin, t_ahora)

        def en_lectura(h):
            t = hora_dt(h)
            return t < t_fin and t <= t_ahora
        esperada = RV.roi_por_volcan(a.roi_brazo)
        # S174 (VPR945-R3-01, LECTURA LR3). POR QUÉ: la sombra existe para ver el detector nuevo justo donde la ROI
        # cambió (con B4, la caja del cráter de Cordón Caulle y Tupungatito). Si sus pasadas faltan, o salen como «otra
        # ROI» con código viejo, el reloj y las noches de los otros nueve volcanes daban CUMPLE con esos dos en una noche
        # (el verificador lo reprodujo). Los volcanes cuya ROI difiere de B0 se derivan del mapa, no se escriben a mano.
        cambia = sorted(v for v, t in esperada.items() if t != RV.roi_por_volcan("B0").get(v))
        for i, (roi, sha) in reg.items():
            if obj[i]["volcan"] not in esperada:
                # S174 (VPR945-02): un volcán que no está en el mapa de ROI (otro nombre, uno de los 34) no tiene ROI
                # esperada; descartarlo como «otra ROI» lo sacaba en silencio del denominador con sus protegidas.
                sin_mapa[i] = "volcan_sin_roi"
            elif roi != esperada.get(obj[i]["volcan"]):
                fuera_regimen[i] = "otra ROI"
            elif corte:
                anc = es_ancestro(corte, sha)
                if anc is None:
                    sin_regimen[i] = "sha_desconocido"
                elif not anc:
                    fuera_regimen[i] = "anterior al corte"
        # la ventana, después de la ROI y del código (que dicen más del régimen) y para todas las pasadas, observadas o no
        for i in obj:
            if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde:
                fuera_regimen[i] = ("anterior al inicio de la sombra" if obj[i]["hora_utc"] < INICIO_SOMBRA
                                    else "anterior a la hora del corte")
            elif i not in fuera_regimen and not en_lectura(obj[i]["hora_utc"]):
                fuera_regimen[i] = "fuera de ventana"   # S174 (VPR945-R4): posterior al fin o a ahora (fecha futura)

        def por_vol(motivo):
            return dict(collections.Counter(obj[i]["volcan"] for i, m in fuera_regimen.items() if m == motivo))

        n_fuera = collections.Counter(fuera_regimen.values())
        dentro = sum(1 for i in reg if i not in fuera_regimen and i not in sin_regimen and i not in sin_mapa)
        pr(f"== régimen de la sombra: brazo {a.roi_brazo}"
           + (f", desde {corte} (commit del {fecha_corte} UTC)" if corte else "")
           + f": dentro {dentro}, fuera por otra ROI {n_fuera['otra ROI']} {por_vol('otra ROI')}, anteriores al "
           f"corte {n_fuera['anterior al corte']} {por_vol('anterior al corte')}; ventana desde {ventana_desde} UTC: "
           f"anteriores al inicio de la sombra {n_fuera['anterior al inicio de la sombra']}, anteriores a la hora del "
           f"corte {n_fuera['anterior a la hora del corte']}; fuera de ventana (posteriores a "
           f"{t_lim:%Y-%m-%d %H:%M:%S}) {n_fuera['fuera de ventana']} {por_vol('fuera de ventana')}")
        pr(f"== ventana fija de la sombra (§4.3, LECTURA LR3): inicio {t_ini:%Y-%m-%d %H:%M} UTC, fin "
           f"{t_fin:%Y-%m-%d %H:%M} UTC (inicio + {DIAS_MIN_SOMBRA} días, sin incluir), {SEMANAS_SOMBRA} semanas fijas "
           f"desde {', '.join(f'{t_ini + k * SEMANA:%m-%d %H:%M}' for k in range(SEMANAS_SOMBRA))}; ahora "
           f"{t_ahora:%Y-%m-%d %H:%M:%S} UTC ({origen_ahora}); se lee hasta {t_lim:%Y-%m-%d %H:%M:%S} UTC")
        pr("   protegidas fuera de esta lectura (se leen con su propio brazo, no aquí):",
           [f"{nombre(i)} ({m})" for i, m in fuera_regimen.items() if obj[i].get("protegida")] or "ninguna")
        # S174 (VPR945-R2-02, LECTURA LR3). POR QUÉ: el corte tiene que aislar UN régimen en cada volcán. Si una pasada de
        # otra ROI trae código posterior al corte (o un sha que git no conoce y no se puede descartar), la ROI de ese
        # volcán cambió dentro de lo que se lee: el reloj y las noches de la lectura serían los de los otros volcanes, no
        # los suyos (con el corte viejo c3aea8a3e y B4, las pasadas def de los nueve volcanes que no cambiaron hacían
        # correr el reloj aunque Cordón Caulle y Tupungatito llevaran una noche con sens).
        # S174 (VPR945-R4): sólo dentro de lo que se lee; una ROI nueva después del fin de la ventana no la toca
        roi_cambia = sorted({obj[i]["volcan"] for i, m in fuera_regimen.items() if m == "otra ROI"
                             and obj[i]["hora_utc"] >= ventana_desde and es_ancestro(corte, reg[i][1]) is not False
                             and en_lectura(obj[i]["hora_utc"])})
        if roi_cambia:
            pr(f"== régimen de la sombra: el corte {corte[:9]} no aísla el brazo {a.roi_brazo}: hay pasadas de otra ROI "
               f"con código posterior al corte (o sha desconocido) en {roi_cambia}; la ROI de esos volcanes cambió dentro "
               "de lo que se lee y el reloj no sería el suyo. Usa como --sha-desde el commit que puso esta ROI (B4: el "
               "merge de #939, 58edb9788); compuerta cerrada")
            return salir(3)
        obj = {i: o for i, o in obj.items() if i not in fuera_regimen}
    # ---------------------------------------------------------------- cobertura (copia de analizar_v750b, §4.2)
    req_brazos = ("K", "Kgemelo") if censo else ("K", "P")

    def falta_brazo(r):
        br = r.get("brazos") or {}
        if any(not isinstance(br.get(x), dict) or "record" not in br[x] for x in req_brazos):
            return True
        return censo and not set(PAQUETE) <= set(r.get("paquete") or {})

    part = {i: AB.partida(res.get(i) or {}) for i in obj}
    motivo_sin = {}
    for i in obj:
        r = res.get(i) or {}
        if part[i] is None:
            motivo_sin[i] = str(r.get("estado") or "sin_estado")[:40]
        elif part[i] == "observada" and r.get("dayflag") != 0:
            motivo_sin[i] = "diurna"
        elif part[i] == "observada" and falta_brazo(r):
            motivo_sin[i] = "falta_brazo"      # una pasada «ok» incompleta es SIN DATO, no desaparece en silencio
        elif part[i] == "observada" and i in sin_regimen:
            motivo_sin[i] = sin_regimen[i]     # S173: sin ROI o sha legibles no se sabe qué detector la produjo
        elif part[i] == "observada" and i in sin_mapa:
            motivo_sin[i] = sin_mapa[i]        # S174 (VPR945-02): el brazo no dice qué ROI esperar en ese volcán
    sin = list(motivo_sin)
    no_obs = collections.Counter(part[i] for i in obj if part[i] in ("fuera", "sin_crater"))
    oks0 = [i for i in obj if part[i] == "observada" and i not in motivo_sin]
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res))
    pr(f"   observadas: {len(oks0)} | no observadas (fuera del denominador): {dict(no_obs)} | SIN DATO: {len(sin)}")
    pr("   SIN DATO por motivo:", dict(collections.Counter(motivo_sin.values())))
    prot_sin = [nombre(i) for i in sin if obj[i].get("protegida")]
    sg = Path(a.sin_granulo)
    sha_obj = hashlib.sha256(Path(a.objetivos).read_bytes()).hexdigest()
    sg_ok, sin_g = False, []
    if sg.exists():
        dsg = json.loads(sg.read_text(encoding="utf-8"))
        sg_ok = isinstance(dsg, dict) and dsg.get("objetivos_sha256") == sha_obj
        sin_g = dsg.get("pasadas", []) if sg_ok else []
    if not censo:   # S174 (VPR945-R2-03, R4): la misma ventana que la lectura, por las dos puntas; sin hora no se descarta
        sin_g = [x for x in sin_g if not x.get("hora_utc") or (x["hora_utc"] >= ventana_desde
                                                               and en_lectura(x["hora_utc"]))]
    pr(f"   pasadas sin gránulo (del generador): {len(sin_g)}"
       + ("" if sg_ok else f" | ARCHIVO {'AUSENTE' if not sg.exists() else 'DE OTRA LISTA DE OBJETIVOS'}: SIN DATO"))
    prot_sin += [f"{x['volcan']} {x['hora_utc']}" for x in sin_g if x.get("protegida")]
    pr("   protegidas no observadas (fuera del denominador):",
       [nombre(i) for i in obj if part[i] in ("fuera", "sin_crater") and obj[i].get("protegida")] or "ninguna")
    pr("   protegidas SIN DATO (falla de cobertura, no de brazo):", prot_sin or "ninguna")
    den_cob = max(1, len(obj) + len(sin_g) - no_obs["fuera"] - no_obs["sin_crater"])
    cob_ok = sg_ok and len(sin) + len(sin_g) <= AB.MAX_SIN_DATO * den_cob and not prot_sin
    if not oks0:
        # S174 (VPR945-03): sin ninguna pasada observada no hay nada que medir. Antes decía «cobertura: SUFICIENTE» y
        # cerraba por «control nulo FALLA», dos mensajes falsos (el nulo no tuvo con qué probarse).
        pr(f"== cobertura: SIN PASADAS OBSERVADAS en esta lectura (observadas 0, SIN DATO {len(sin)}"
           + (f"; brazo {a.roi_brazo}" + (f", desde {corte}" if corte else "") if not censo else "")
           + "): no hay nada que medir, compuerta cerrada")
        pr("== sin veredicto: ninguna pasada observada que leer")
        return salir(3)
    pr("== cobertura:", "SUFICIENTE" if cob_ok else
       f"INSUFICIENTE (más de {AB.MAX_SIN_DATO:.0%} sin procesar o una protegida): relanzar con SOLO las faltantes")

    # ---------------------------------------------------------------- publicación con node (A97)
    def anc(i):
        return tuple(obj[i].get("pos_crater") or (AB.C, AB.C))

    def rec_k(i, b):
        return AB.slim(res[i]["brazos"][b]["record"])

    def rec_paq(i, b):
        return AB.record_cumulo(res[i]["paquete"][b], inner[obj[i]["volcan"]], obj[i]["sensor"], anc(i))

    def rec_p(i):
        return rec_paq(i, "P") if censo else rec_k(i, "P")

    def rec_pos(i, b):
        """§3 y §6 bis: el record de P (AB.record_cumulo, sin tocar) con la distancia al cráter, y con ella la clase
        summit o far, medida desde el punto del brazo; el VRP, el cúmulo y el resto del record quedan iguales. Copia de
        leer_posicion_v750b.py::record_pos; el ancla es pos_crater, como la distancia del radiante (VB-07)."""
        r = rec_paq(i, "P")
        if b == "P" or not r.get("primary_cluster"):
            return r
        ancla = anc(i)
        f, c = punto_pos(res[i]["paquete"]["P"], b, ancla)
        d = float(np.hypot(f - ancla[0], c - ancla[1]) * 0.75)
        rp = copy.deepcopy(r)            # rp y no r: M28 del medidor rompe la línea de P-sinfiltro por su texto
        rp["distance_class"] = "summit" if d <= inner[obj[i]["volcan"]] else "far"
        rp["primary_cluster"]["centroid_dist_km"] = round(d, 3)
        return rp

    def rec_sinfiltro(i):
        """P-sinfiltro (§3): el record de P con la distancia neutralizada; el resto del predicado, igual."""
        r = rec_paq(i, "P")
        if r.get("primary_cluster"):
            r["distance_class"] = "summit"
            r["primary_cluster"]["centroid_dist_km"] = 0.0
        return r

    def rec_kx12(i):
        """Placebo (§3, como evaluar_d25.py): K con su VRP multiplicado por 1,2; la publicación no tendría que cambiar."""
        r = copy.deepcopy(rec_k(i, "K"))
        for k in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw"):
            if r.get(k) is not None:
                r[k] = r[k] * GANANCIA_PLACEBO
        if r.get("primary_cluster") and r["primary_cluster"].get("vrp_mw") is not None:
            r["primary_cluster"]["vrp_mw"] = r["primary_cluster"]["vrp_mw"] * GANANCIA_PLACEBO
        return r

    casos, idx = [], []

    def caso(i, b, r):
        casos.append([r, inner[obj[i]["volcan"]]])
        idx.append((i, b))

    for i in oks0:
        caso(i, "K", rec_k(i, "K"))
        caso(i, "P", rec_p(i))
        if censo:
            caso(i, "Kgemelo", rec_k(i, "Kgemelo"))
            caso(i, "Kx12", rec_kx12(i))
            caso(i, "Pdef", rec_paq(i, "Pdef"))
            caso(i, "O", rec_paq(i, "O"))
            caso(i, "Psinfiltro", rec_sinfiltro(i))
            for b in POS[1:]:                         # §6 bis: los brazos de posición, por el mismo predicado
                caso(i, b, rec_pos(i, b))
            if isinstance((res[i].get("brazos") or {}).get("Kgeo"), dict) and "record" in res[i]["brazos"]["Kgeo"]:
                caso(i, "Kgeo", rec_k(i, "Kgeo"))
    PUB = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))} if casos else {}

    def pub(i, b):
        return PUB.get((i, b), False)

    def vrp(i, b):
        if b in ("K", "Kgemelo", "Kgeo") or (b == "P" and not censo):
            rec = res[i]["brazos"][b]["record"] or {}
            return (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        if b == "Kx12":
            return GANANCIA_PLACEBO * vrp(i, "K")
        # P-sinfiltro y los brazos de posición tienen el VRP de P (sólo cambia la distancia del record)
        return res[i]["paquete"]["P" if b in ("Psinfiltro",) + POS else b].get("vrp_mw") or 0.0

    # ---------------------------------------------------------------- controles (§7)
    # nulo del contador (copia de analizar_v750b): perturbar records publicados de P y publicar un negativo
    nulo, nidx = [], []
    for i in oks0:
        if pub(i, "P"):
            base = rec_p(i)
            a0 = copy.deepcopy(base)
            if a0.get("primary_cluster"):
                a0["primary_cluster"]["vrp_mw"] = 0.0
            a0["vrp_mw"] = 0.0
            b0 = copy.deepcopy(base)
            b0["distance_class"] = "far"
            for rr in (a0, b0):
                nulo.append([rr, inner[obj[i]["volcan"]]])
                nidx.append(False)
    rng = random.Random(162)
    neg_no = [i for i in oks0 if obj[i]["lab"] == "neg_limpio" and not pub(i, "P")]
    for i in rng.sample(neg_no, min(50, len(neg_no))):
        rr = {"sensor": obj[i]["sensor"], "vrp_mw": 0.3, "t_max_k": 290.0, "triggered_test1": False,
              "distance_class": "summit", "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}}
        nulo.append([rr, inner[obj[i]["volcan"]]])
        nidx.append(True)
    NP = [bool(p[4]) for p in B.correr_node(nulo)] if nulo else []
    c_nulo = sum(1 for esperado, p in zip(nidx, NP) if p != esperado)
    nulo_ok = bool(nidx) and c_nulo == 0
    pr(f"== control nulo del contador: {len(nidx)} perturbaciones; las que no dan lo esperado: {c_nulo} "
       f"(tiene que ser 0, con al menos una perturbación): {'OK' if nulo_ok else 'FALLA'}")
    # K = producción (copia de analizar_v750b)
    k_dist = sorted({i for i in oks0 if bool(obj[i].get("pub_prod")) != pub(i, "K")}
                    | {i for i in oks0 if abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 0.001})
    k_dist_prot = [nombre(i) for i in k_dist if obj[i].get("protegida")]
    # §7 (L18, resuelta por D-48): la tolerancia de V750-B, mismo probe y misma población. Hasta 1 % de pasadas con K
    # distinto de producción y ninguna protegida; esas pasadas salen de TODOS los brazos y se listan (las diferencias
    # de máquina entre runners existen: S152, argsort inestable según la CPU)
    k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot
    pr(f"== control K = producción: distintas {len(k_dist)} de {len(oks0)} (protegidas {k_dist_prot or 'ninguna'}): "
       f"{'OK' if k_ok else 'FALLA'}; lista {[nombre(i) for i in k_dist]}")
    oks = [i for i in oks0 if i not in set(k_dist)]   # §7: salen de todos los brazos y se listan arriba

    def p2(b, ref, v, canal, lejana=False):
        """Copia de analizar_v750b.p2: e = 1 si la pasada es un error bajo 1 MW; c = e(b) - e(ref) por bloque
        (noche UTC, volcán); prueba de signos de D-45. lejana=True es la P2' del §6 bis: las pasadas far_ref del canal
        suman al mismo bloque como error cuando el brazo publica (E + E_lejana)."""
        sumas = collections.defaultdict(int)
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if lejana and etiqueta_lejana(o, canal):   # §6 bis: publicar lo que MIROVA ubicó lejos es error, como un negativo
                e = "neg"
            if e not in ("baja", "neg") or not en_ventana(o, v):
                continue
            err = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))  # noqa: E731
            c = err(b) - err(ref)
            if c:
                sumas[(o["hora_utc"][:10], o["volcan"])] += c
        s = [sumas[k] for k in sorted(sumas)]
        neto = sum(s)
        prr = EV.prueba_signos_p2(s, neto)
        return EV.regla_signos_p2(neto, len(s), prr), neto, len(s), prr

    def m_pares(b, v, canal):
        """M (§5): alertas que deciden publicadas por K y por el brazo, con VRP de los dos y de MIROVA (LECTURA L4)."""
        out = []
        for i in oks:
            o = obj[i]
            if etiqueta(o, canal) not in ("prot", "baja") or not en_ventana(o, v):
                continue
            if not (pub(i, "K") and pub(i, b)):
                continue
            k, d, m = vrp(i, "K"), vrp(i, b), o.get("mirova_vrp") or 0.0
            if k > 0 and d > 0 and m > 0:
                out.append({"k": k, "d": d, "m": m, "clave": f"{o['volcan']}|{o['hora_utc']}",
                            "bloque": f"{o['hora_utc'][:10]}|{o['volcan']}"})
        return out

    def decidir_m(P_, comparador=True):
        """decidir_estrato de evaluar_d25.py con el mismo piso de sustrato que su evaluar_m."""
        if len(P_) < EM.N_MIN_PARES or len({p["bloque"] for p in P_}) < EM.N_MIN_NOCHES:
            return "SIN SUSTRATO", {"n": len(P_)}
        return EM.decidir_estrato(P_, "decide", "simetrica", True, comparador=comparador)

    ctrl = {"nulo del contador": nulo_ok, "K = producción": k_ok}
    if censo:
        # placebo, publicación (L7, resuelta por D-48): el predicado del tablero mira la magnitud sólo en sus dos
        # filtros de artefacto (isCirrusArtifact e isDiffuseFieldArtifact), y los dos exigen t_max del record bajo
        # 278,15 K. Una diferencia K contra K×1,2 con t_max frío la explican esos filtros: se lista y no cierra. Una
        # con t_max tibio o sin t_max no la explica nada conocido y cierra la compuerta
        # VB-A01: y el tope de 50.000 MW de mirovaEqVrp, que tampoco es un defecto del paquete
        pl_todas = [i for i in oks if pub(i, "Kx12") != pub(i, "K")]
        pl_frio = [i for i in pl_todas if (rec_k(i, "K").get("t_max_k") or 1e9) < TMAX_FILTROS_ARTEFACTO
                   or vrp(i, "K") <= TOPE_TABLERO_MW < vrp(i, "K") * GANANCIA_PLACEBO]
        pl_dist = [nombre(i) for i in pl_todas if i not in set(pl_frio)]
        ctrl["placebo (publicación)"] = not pl_dist
        pr(f"== control placebo K×1,2 (publicación): distintas de K {len(pl_todas)} de {len(oks)}; explicadas por los "
           f"filtros de artefacto del tablero (t_max bajo {TMAX_FILTROS_ARTEFACTO} K) o su tope de {TOPE_TABLERO_MW:.0f} MW {len(pl_frio)} "
           f"{[nombre(i) for i in pl_frio][:10]}; sin explicar {len(pl_dist)} {pl_dist[:10]}: "
           f"{'OK' if not pl_dist else 'FALLA'}")
        # placebo, M con el comparador: d′ es 0 para una ganancia pareja, así que M no lo puede dar por mejor
        # VP-03 (LECTURA L28): sobre los pares de LOS TRES brazos de posición, porque el brazo que decide el §6 se elige
        # después de esta compuerta; así el placebo cubre los pares de cualquiera que se elija
        pl_m = {}
        for v in VENTANAS:
            for canal in CANALES:
                for b in POS:
                    pl_m[f"{NOM_POS[b]} {v}/{canal}"] = decidir_m([dict(p, d=p["k"] * GANANCIA_PLACEBO)
                                                                   for p in m_pares(b, v, canal)])[0]
        ctrl["placebo (M con comparador)"] = all(r != "MEJORA" for r in pl_m.values())
        pr(f"== control placebo K×1,2 (M con comparador, tiene que no dar MEJORA): {pl_m}: "
           f"{'OK' if ctrl['placebo (M con comparador)'] else 'FALLA'}")
        # nulo: K contra su gemelo
        g_reg, g_neto, g_nb, _ = p2("Kgemelo", "K", "TODO", "decide")
        g_m = decidir_m(m_pares("Kgemelo", "TODO", "decide"))[0]
        ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO") and g_m in ("NEUTRO", "SIN SUSTRATO")
        pr(f"== control nulo K contra K gemelo: P2 {g_reg} (neto {g_neto}, bloques {g_nb}), M {g_m} (tiene que ser "
           f"P2 EMPATE o SIN SUSTRATO y M sin separación): {'OK' if ctrl['nulo K contra K gemelo'] else 'FALLA'}")
        # control positivo de la ROI: P-def pierde una protegida de Cordón Caulle que P publica (LECTURA L6)
        roi = [nombre(i) for i in oks if obj[i]["volcan"] == VOL_ROI and etiqueta(obj[i], "decide") == "prot"
               and pub(i, "P") and not pub(i, "Pdef")]
        ctrl["positivo de la ROI"] = len(roi) >= 1
        pr(f"== control positivo de la ROI: protegidas de Cordón Caulle que P publica y P-def pierde {len(roi)} {roi[:10]} "
           f"(1 o más): {'OK' if roi else 'FALLA'}")
    else:
        pr("== fase sombra: los controles que necesitan P-def, O, el gemelo o el placebo no aplican (LECTURA L9)")
        # S173 (programa por sensor §12.8 punto 2): K y la vía difieren justo en las pasadas oblicuas, y un total que
        # mezcla los dos tramos puede esconderlo. Corte informativo en 30° de cenit del sensor; no decide nada.
        pr("== sombra por cenit del sensor (informa, no decide; §12.8 punto 2), canal que decide:")
        for nom_z, f_z in (("bajo 30°", lambda z: z < 30), ("sobre 30°", lambda z: z >= 30)):
            ids = [i for i in oks0 if obj[i].get("z") is not None and f_z(obj[i]["z"])]
            prz = [i for i in ids if etiqueta(obj[i], "decide") == "prot"]
            pr(f"   {nom_z}: observadas {len(ids)} | protegidas {len(prz)} | K publica {sum(pub(i, 'K') for i in ids)}"
               f" | P publica {sum(pub(i, 'P') for i in ids)} | protegidas que K publica y P no "
               f"{sum(1 for i in prz if pub(i, 'K') and not pub(i, 'P'))}")
        sin_z = [i for i in oks0 if obj[i].get("z") is None]
        if sin_z:
            pr(f"   sin cenit: {len(sin_z)}")
        # S174 (VPR945-01, LECTURA LR2). POR QUÉ: §4.3 pide que la sombra corra «al menos 4 semanas»: dos noches ven unas
        # pocas pasadas de un volcán, una estación y unos ángulos, y un CUMPLE con eso no confirma nada. El reloj corre
        # sobre las pasadas observadas que esta lectura lee (no sobre las de otra ROI, las de antes del corte o de la
        # ventana, las SIN DATO ni las no observadas).
        # S174 (VPR945-R2-01 y R2-03, LECTURA LR3). POR QUÉ: el lapso entre la primera y la última pasada no es cobertura
        # (3 noches con una suelta a 30 días daban COMPLETA); Nicolás pide además «14 noches» distintas con datos. Noche
        # = fecha UTC de la pasada (hora_utc[:10]), la misma clave del bloque de P2 (noche UTC, volcán): las pasadas
        # nocturnas de VIIRS 750 sobre Chile caen de madrugada en UTC, así que una noche local es una sola fecha UTC
        # mientras ninguna pasada leída cruce las 00:00 UTC. S174 (VPR945-R3-05): eso no se escribe con una cifra que
        # envejece; la línea «horas UTC de las pasadas leídas» lo mide en cada lectura. Reloj, noches y lectura usan las
        # mismas pasadas (oks0, ya dentro de la ventana del corte); los días se muestran truncados al décimo, para que
        # 27,99 no se lea «28,0».
        # S174 (VPR945-R3-02, R3-01): ⚠️ S174 (VPR945-R4, quinta vuelta, A113): el reparto de 7 y 7 por mitad del lapso y
        # el reloj medido entre la primera y la última pasada leída quedan retirados; el texto de LR3 los conserva.
        # S174 (VPR945-R4, LECTURA LR3). POR QUÉ: con la ventana fija los días son de calendario, de su inicio a
        # min(ahora, fin), y no dependen de ninguna pasada; las noches se cuentan en 4 semanas fijas desde el inicio.
        # CUMPLE exige que ahora haya llegado al fin, NOCHES_MIN_SEMANA noches en cada semana y NOCHES_MIN_SOMBRA en total,
        # en el conjunto y en cada volcán cuya ROI difiere de B0 (`cambia`), contadas sobre sus pasadas leídas (oks0); un
        # volcán cambiado sin pasadas tiene 0 noches. Los otros volcanes se imprimen y no deciden (SEMANA_EXIGE_SIN_CAMBIO).
        # ⚠️ S174 (R5-03, A113): ese «no deciden» queda rebajado: piden NOCHES_MIN_SIN_CAMBIO noches en total (abajo).
        horas = sorted(obj[i]["hora_utc"] for i in oks0) or ["(ninguna)"]
        dias = max(0.0, (t_lim - t_ini).total_seconds() / 86400)
        # S177 (VPR964-03, LECTURA LR4): las noches se cuentan sobre `oks`, no sobre `oks0`: una pasada con K distinto de
        # producción sale de todos los brazos (L18), así que su noche no la leyó nadie y no puede completar la sombra.
        noches_sem, noches = semanas_noches([obj[i]["hora_utc"] for i in oks], t_ini)
        por_v = {v: semanas_noches([obj[i]["hora_utc"] for i in oks if obj[i]["volcan"] == v], t_ini) for v in esperada}
        exigidos = [v for v in esperada if v in cambia or SEMANA_EXIGE_SIN_CAMBIO]
        vol_falta = [v for v in sorted(exigidos) if faltan_noches(*por_v[v])]
        # S174 (VPR945-R5-03, decisión de Nicolás del 2026-11-06): los volcanes de ROI igual a B0 (con B4, los nueve)
        # piden NOCHES_MIN_SIN_CAMBIO noches en la ventana, sin mínimo semanal; uno sin pasadas tiene 0 y deja PROVISORIO
        sin_cambio = [v for v in sorted(esperada) if v not in exigidos]
        vol_pocas = [v for v in sin_cambio if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]
        ahora_ok = t_ahora >= t_fin
        noches_ok = not faltan_noches(noches_sem, noches)
        dur_ok = ahora_ok and noches_ok and not vol_falta and not vol_pocas
        dias_txt = f"{math.floor(dias * 10) / 10:.1f}"

        def sem_txt(ns, n):
            return ", ".join(str(x) for x in ns) + f" ({n})"

        hh = sorted(h[11:16] for h in horas) if oks0 else ["-"]
        pr(f"   horas UTC de las pasadas leídas: de {hh[0]} a {hh[-1]} (una noche es una fecha UTC mientras ninguna "
           "cruce las 00:00 UTC)")
        pr(f"== noches por semana y volcán (brazo {a.roi_brazo}; semanas fijas desde {t_ini:%Y-%m-%d %H:%M} UTC; ROI "
           f"distinta de B0 en {cambia or 'ninguno'}, cada uno pide {NOCHES_MIN_SEMANA} por semana y "
           f"{NOCHES_MIN_SOMBRA} en total; los demás, sin cambio, piden {NOCHES_MIN_SIN_CAMBIO} en total y por semana "
           f"informan): "
           + ", ".join(f"{v} {sem_txt(ns, n)}" + (" decide, faltan" if v in vol_falta else " decide, completas"
                                                   if v in exigidos else " sin cambio, faltan" if v in vol_pocas
                                                   else " sin cambio, completas")
                       for v, (ns, n) in sorted(por_v.items())))
        pr(f"== duración de la sombra (§4.3, ventana fija de {DIAS_MIN_SOMBRA} días en {SEMANAS_SOMBRA} semanas, "
           f"{NOCHES_MIN_SEMANA} noches distintas por semana y {NOCHES_MIN_SOMBRA} en total): primera {horas[0]}, última "
           f"{horas[-1]}; días de calendario desde el inicio {dias_txt} de {DIAS_MIN_SOMBRA} "
           f"{'(completos)' if ahora_ok else '(faltan: ahora es anterior al fin)'}; noches del conjunto por semana "
           f"{sem_txt(noches_sem, noches)} {'(completas)' if noches_ok else '(faltan)'}; volcanes con ROI cambiada sin "
           f"sus noches {vol_falta or 'ninguno'}; volcanes sin cambio de ROI con menos de {NOCHES_MIN_SIN_CAMBIO} "
           f"noches {vol_pocas or 'ninguno'}: {'COMPLETA' if dur_ok else 'INCOMPLETA'}")
    aviso, rc_final = "", 0
    if not cob_ok and a.leer_con_faltantes:
        aviso, rc_final = f"[LEÍDO CON FALTANTES: {a.leer_con_faltantes}]", 5
    todo_ok = all(ctrl.values()) and (cob_ok or bool(a.leer_con_faltantes))
    pr("== compuerta del veredicto (controles de §7 y cobertura):", "ABIERTA" if todo_ok else "CERRADA",
       {k: v for k, v in ctrl.items() if not v} or "", aviso)
    if a.solo_controles or not todo_ok:
        pr("== sin veredicto:", "--solo-controles" if a.solo_controles else "controles caídos o SIN DATO")
        return salir(0 if (a.solo_controles and todo_ok) else 3)

    # ---------------------------------------------------------------- §6.1 equivalencia (censo)
    if censo:
        dist, banda = [], []
        for i in oks0:
            p, o_ = res[i]["paquete"]["P"], res[i]["paquete"]["O"]
            mp = sorted((x[0], x[1]) for x in p.get("pixeles") or [])
            mo = sorted((x[0], x[1]) for x in o_.get("pixeles") or [])
            if mp != mo or abs((p.get("vrp_mw") or 0.0) - (o_.get("vrp_mw") or 0.0)) > TOL_VRP_EQUIV:
                (banda if res[i].get("banda_triangulacion") else dist).append(i)

        def etq_eq(i):
            dP, dO = res[i]["paquete"]["P"].get("diag"), res[i]["paquete"]["O"].get("diag")
            if not (diag_valido(dP) and diag_valido(dO)):
                return nombre(i) + " (S-1 SIN DATO)"
            return nombre(i) + (" (decidida por la escena, no por el cráter: bloquea igual)"
                                if decidida_por_escena(dP, dO) else "")
        local_ok, local_txt = leer_equivalencia_local(a.equivalencia_local)
        pr("   P distinto de O dentro de la banda de triangulación (se listan aparte):", [nombre(i) for i in banda]
           or "ninguna")
        if dist or not local_ok:
            pr(f"== §6.1 equivalencia: NO SE CUMPLE (runner: {len(dist)} pasadas distintas fuera de la banda "
               f"{[etq_eq(i) for i in dist][:20]}; local: {local_txt}): se arregla la vía y se repite §4.1; "
               "el censo no se mira")
            return salir(6)
        pr(f"== §6.1 equivalencia: CUMPLE (runner: 0 pasadas distintas fuera de la banda de {len(oks0)}; {local_txt})")

    # ---------------------------------------------------------------- S-1, diagnóstico de la sigma de escena
    s1_prot, s1_sin_diag_prot, s1_filas = set(), set(), []
    if censo:
        for A, Bb in PARES_S1:
            con, sd_ = [], []
            for i in oks0:
                dA, dB = res[i]["paquete"][A].get("diag"), res[i]["paquete"][Bb].get("diag")
                if diag_valido(dA) and diag_valido(dB):
                    con.append(i)
                    sd_.append(delta_sd(dA, dB))
            for i in con:
                dA, dB = res[i]["paquete"][A]["diag"], res[i]["paquete"][Bb]["diag"]
                s1_filas.append({"par": f"{A}|{Bb}", "pasada": nombre(i), "id": i, "volcan": obj[i]["volcan"],
                                 "cenit": AB.tramo_z(obj[i].get("z")), "protegida": etiqueta(obj[i], "decide") == "prot",
                                 "delta_sd": delta_sd(dA, dB), "margen_A_nti_eti": list(margenes(dA)),
                                 "margen_B_nti_eti": list(margenes(dB)), "publica": [pub(i, A), pub(i, Bb)],
                                 "decidida_por_escena": decidida_por_escena(dA, dB)})
            cambia = [i for i in oks0 if pub(i, A) != pub(i, Bb)]
            esc = [i for i in cambia if i in set(con) and decidida_por_escena(res[i]["paquete"][A]["diag"],
                                                                             res[i]["paquete"][Bb]["diag"])]
            for i in cambia:
                if etiqueta(obj[i], "decide") == "prot":
                    if i in esc:
                        s1_prot.add(nombre(i))
                    elif i not in set(con):
                        s1_sin_diag_prot.add(nombre(i))
            partes = []
            for k in ("nti1", "eti1", "nti2", "eti2"):
                vals = [x[k] for x in sd_]
                partes.append(f"Δsd {k} mediana {statistics.median(vals):.4f} máx {max(abs(v) for v in vals):.4f}"
                              if vals else f"Δsd {k} SIN DATO")

            def entrada(i):
                mA = margenes(res[i]["paquete"][A]["diag"])
                mB = margenes(res[i]["paquete"][Bb]["diag"])
                return f"{nombre(i)} ({A} c/u {mA[0]:.2f}/{mA[1]:.2f}, {Bb} c/u {mB[0]:.2f}/{mB[1]:.2f})"
            pr(f"== S-1 par ({A}, {Bb}): pasadas con diagnóstico {len(con)} (SIN DATO {len(oks0) - len(con)}) | "
               + " | ".join(partes) + f" | publicación distinta {len(cambia)} | decididas por la escena {len(esc)}: "
               + str([entrada(i) for i in esc]))
            pr(f"   S-1 ({A}, {Bb}) decididas por la escena, por volcán "
               f"{dict(collections.Counter(obj[i]['volcan'] for i in esc))} y por cenit "
               f"{dict(collections.Counter(AB.tramo_z(obj[i].get('z')) for i in esc))}")

        f_s1 = Path(a.salida).with_name(Path(a.salida).stem + "_s1_por_pasada.json")
        f_s1.write_text(json.dumps(s1_filas, ensure_ascii=False, indent=1), encoding="utf-8")
        pr(f"== S-1 por pasada (a), (b) y (c) de §5: {len(s1_filas)} filas en {f_s1}")

    # ---------------------------------------------------------------- métricas por ventana y canal
    def metricas(b, v, canal, n3=False):
        """P1 (§6.2): protegidas que K publica y el brazo no; P1_nadie: las que ni K ni el brazo publican (se
        listan). P1b y E como analizar_v750b. n3=True (§6 ter, sólo en el §6 bis y el §6.2): las de la clase N-3 van a
        P1_n3 en vez de P1 y no vetan; P1 + P1_n3 es el P1 que las cuenta todas."""
        m = collections.Counter()
        nadie = []
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if e is None or not en_ventana(o, v):
                continue
            pb, vb = pub(i, b), vrp(i, b)
            m[f"n_{e}"] += 1
            if e == "prot" and not pb and pub(i, "K"):
                m["P1_n3" if n3 and es_n3(o) else "P1"] += 1
            if e == "prot" and not pb and not pub(i, "K"):
                nadie.append(nombre(i))
            if e == "prot" and pb and vb < 1.0:
                m["P1b_abajo"] += 1
            if e in ("baja", "neg") and pb and vb >= 1.0:
                m["P1b_arriba"] += 1
            if e == "baja" and not pb:
                m["E_baja"] += 1
            if e == "neg" and pb:
                m["E_neg"] += 1
        m["E"] = m["E_baja"] + m["E_neg"]
        return m, nadie

    def razon_prot(b, v, canal, exigir_k=False):
        """§6.2 (L4, resuelta por D-48): mediana de brazo/MIROVA en las protegidas que el brazo publica, con VRP del
        brazo y de MIROVA mayores que 0, publique K o no: la calibración es de P, y una P que publica al doble donde K
        calla tiene que fallar. exigir_k=True sólo informa (el subconjunto que publican K y el brazo)."""
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks
                    if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b)
                    and (pub(i, "K") and vrp(i, "K") > 0 or not exigir_k)
                    and obj[i].get("mirova_vrp") and vrp(i, b) > 0)
        return (statistics.median(rz) if rz else None), len(rz)

    # ---------------------------------------------------------------- §6 bis, regla de posición (antes del §6)
    def e_lejana(b, v, canal):
        """§6 bis: pasadas far_ref del canal en que el brazo publica (MIROVA vio el calor y lo ubicó lejos)."""
        return sum(1 for i in oks if etiqueta_lejana(obj[i], canal) and en_ventana(obj[i], v) and pub(i, b))

    def no_peor(reg, neto):
        """§6 bis: GANA o EMPATE, o SIN SUSTRATO con el neto en 0 o a favor (BLOQUEA y PIERDE son peor; L22)."""
        return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO" and neto <= 0)

    PE, eleccion = "P", "P"
    if censo:
        # §6 ter (N-3): las protegidas de la clase se listan por nombre con los brazos que las publican, y por brazo el
        # P1 que veta (sin ellas) al lado del que las cuenta todas, en T y O con tabla más OCR (con la tabla sola no son
        # protegidas: no tienen alerta de la tabla)
        n3_l = [i for i in oks if es_n3(obj[i]) and etiqueta(obj[i], "todo") == "prot"]
        pr("== §6 ter N-3 (protegidas sólo del OCR de Suomi NPP anteriores al 2026-10-09; no vetan, se informan): "
           + (corta([f"{nombre(i)} ({'/'.join(NOM_POS.get(b, b) for b in ('K',) + POS if pub(i, b)) or 'nadie'})"
                     for i in n3_l]) if n3_l else "ninguna"))
        pr("   §6 ter P1 por brazo, T y O, tabla más OCR, el que veta (contándolas todas): " + " | ".join(
            f"{NOM_POS[b]} {sum(metricas(b, v, 'todo', n3=True)[0]['P1'] for v in VENTANAS)} (contándolas "
            f"{sum(metricas(b, v, 'todo')[0]['P1'] for v in VENTANAS)})" for b in POS))
        # elegible: P1 = 0 en T y en O, con la tabla sola y con tabla más OCR (la condición de P1 del §6.2)
        eleg = {b: all(metricas(b, v, canal, n3=True)[0]["P1"] == 0 for v in VENTANAS for canal in CANALES)
                for b in POS}
        # P2' contra P (radiante), sobre T ∪ O, con el canal que decide y con la tabla sola (L21)
        p2d = {b: p2(b, "P", "TODO", "decide", lejana=True) for b in POS[1:]}
        p2t = {b: p2(b, "P", "TODO", "tabla", lejana=True) for b in POS[1:]}
        e_tot = {b: (metricas(b, "TODO", "decide")[0]["E"], e_lejana(b, "TODO", "decide")) for b in POS}

        def menor(cands):
            """Menor E + E_lejana; a igual valor, P-pico (S165: la distancia de MIROVA calza mejor con el pico)."""
            return min(cands, key=lambda b: (sum(e_tot[b]), b != "Ppico"))

        def desempate(cands):
            if len(cands) < 2:
                return ""
            iguales = len({sum(e_tot[b]) for b in cands}) == 1
            return "; ganan los dos: " + ("a igual valor, P-pico" if iguales else "el de menor E + E_lejana")

        gan = [b for b in POS[1:] if eleg[b] and p2d[b][0] == "GANA" and no_peor(*p2t[b][:2])]
        if gan:
            eleccion = menor(gan)
            motivo = "gana contra P en P2' con el canal que decide y no es peor con la tabla sola" + desempate(gan)
        elif eleg["P"]:
            eleccion = "P"
            motivo = ("ninguno gana y P es elegible: es lo que hace hoy la vía y lo que midió el censo; a igual "
                      "desempeño no se cambia sin evidencia")
        else:
            np_ = [b for b in POS[1:] if eleg[b] and no_peor(*p2d[b][:2]) and no_peor(*p2t[b][:2])]
            if np_:
                eleccion = menor(np_)
                motivo = ("P no es elegible; es el elegible que no es peor que P en P2' con el canal que decide ni con "
                          "la tabla sola" + desempate(np_).replace("ganan", "califican"))
            else:
                eleccion = None
                motivo = "P no es elegible y ningún elegible deja de ser peor que P en P2'; P no se adopta"
        PE = eleccion or "P"
        pr("== §6 bis elegibles (P1 = 0 en T y O, con la tabla sola y con tabla más OCR): "
           + " | ".join(f"{NOM_POS[b]} {'sí' if eleg[b] else 'no'}" for b in POS))
        for b in POS:
            et = f"E + E_lejana {sum(e_tot[b])} (E {e_tot[b][0]}, E_lejana {e_tot[b][1]})"
            if b == "P":
                pr(f"   §6 bis E + E_lejana {NOM_POS[b]}: {et}")
                continue
            (rd, nd, bd, _), (rt, nt, bt, _) = p2d[b], p2t[b]
            pr(f"   §6 bis P2' {NOM_POS[b]} contra P (radiante), T y O: canal que decide {rd} (neto {nd}, bloques {bd}) "
               f"| tabla sola {rt} (neto {nt}, bloques {bt}) | {et}")
        pr(f"== §6 bis posición elegida: {NOM_POS[eleccion] if eleccion else 'NINGUNA POSICIÓN ELEGIBLE'} ({motivo})")
        pr("   §6 bis multiplicidad: dos contrastes contra P, cada uno al 5 % de una cola, sin corregir; la probabilidad "
           "de que alguno gane sólo por azar es mayor que 5 %")
        # descriptivas, no deciden
        far_obj = [i for i in obj if obj[i].get("lab") == "far_ref"]
        far = [i for i in oks if obj[i].get("lab") == "far_ref"]
        pr(f"== §6 bis vara lejana: far_ref en los objetivos {len(far_obj)}, observadas {len(far)}"
           + ("" if far else ": SIN DATO (sin pasadas far_ref observadas, E_lejana vale 0 y la regla se lee igual)"))
        for b in POS[1:]:
            lst = [f"{nombre(i)} ({etiqueta(obj[i], 'decide') or obj[i]['lab']}, {'publica' if pub(i, b) else 'calla'})"
                   for i in oks if pub(i, b) != pub(i, "P")]
            pr(f"   §6 bis cambian de publicación contra P (radiante), {NOM_POS[b]}: {len(lst)} {corta(lst) if lst else 'ninguna'}")
        if far:
            con_alert = sum(bool((res[i]["paquete"]["P"] or {}).get("npix")) for i in far)
            pr(f"   §6 bis pasadas lejanas: con algún alertado {con_alert} de {len(far)}"
               + (" (sin alertados: un cero de E_lejana no dice nada)" if not con_alert else "") + " | "
               + " | ".join(f"{NOM_POS[b]} publica {sum(pub(i, b) for i in far)}" for b in POS) + " | lista "
               + corta([f"{nombre(i)} ({'/'.join(NOM_POS[b] for b in POS if pub(i, b))})" for i in far
                        if any(pub(i, b) for b in POS)]))
        pr("== §6 bis distancia de cada brazo desde la celda central de la grilla contra la Distancia_km de MIROVA "
           "(diferencia de RADIOS, A93: cota inferior de la separación; OCR sólo desde el 2026-06-13, A119; |delta| "
           "mediana, fracción a 1 km o menos, n)")
        for grupo, lab_, tipo_ in (("alertas con distancia", "pos", "ALERTA"), ("far_ref", "far_ref", "FALSO_POSITIVO")):
            partes = []
            for b in POS:
                dd = []
                for i in oks:
                    o, pq = obj[i], res[i]["paquete"]["P"]
                    if o["lab"] != lab_ or not pq.get("npix") or pq.get("vrp_mw") is None:
                        continue
                    ref = next((f["dist_km"] for f in o.get("mirova") or [] if f.get("dist_km") is not None
                                and str(f.get("tipo", "")).startswith(tipo_)
                                and (f.get("source") == "CONS" or o["hora_utc"] >= AB.FRONTERA_OCR)), None)
                    if ref is None:
                        continue
                    fp, cp = punto_pos(pq, b, anc(i))
                    dd.append(abs(float(np.hypot(fp - AB.C, cp - AB.C) * 0.75) - float(ref)))
                partes.append(f"{NOM_POS[b]} {statistics.median(dd):.2f} km, {sum(x <= 1 for x in dd) / len(dd):.2f}, "
                              f"n={len(dd)}" if dd else f"{NOM_POS[b]} -")
            pr(f"   §6 bis distancia desde la celda central contra MIROVA, {grupo}: " + " | ".join(partes))
    else:
        pr("== §6 bis: no aplica en la sombra (LECTURA L26): la posición elegida en el censo es la del record del perfil "
           "sombra")
    nom_pe = NOM_POS[PE] + ("" if eleccion else ", NINGUNA POSICIÓN ELEGIBLE: se informa")

    if censo:
        fallas, nadie_tot = [], set()
        if eleccion is None:
            fallas.append(("TODO", "decide", "§6 bis: NINGUNA POSICIÓN ELEGIBLE"))
        for v in VENTANAS:
            for canal in CANALES:
                m, nadie = metricas(PE, v, canal, n3=True)
                nadie_tot.update(nadie)
                reg, neto, nb, prr = p2(PE, "K", v, canal)
                rz, nrz = razon_prot(PE, v, canal)
                Pm = m_pares(PE, v, canal)
                rm, det = decidir_m(Pm)
                motivos = []
                if m["P1"]:
                    motivos.append(f"P1 {m['P1']}")
                if reg not in ("GANA", "EMPATE"):
                    motivos.append(f"P2 {reg}")
                if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):
                    motivos.append(f"M razón {'sin protegidas' if rz is None else f'{rz:.3f}'}")
                if rm != "MEJORA":
                    motivos.append(f"M comparador {rm}")
                fallas += [(v, canal, x) for x in motivos]
                rz_txt = "-" if rz is None else f"{rz:.3f}"
                pr(f"== §6.2 ventana {v}, canal {canal} (posición {nom_pe}): P1 {m['P1']} (de {m['n_prot']} protegidas; "
                   f"contando las N-3 {m['P1'] + m['P1_n3']}) | P1b abajo "
                   f"{m['P1b_abajo']} arriba {m['P1b_arriba']} | P2 contra K {reg} (neto {neto}, bloques {nb}, p gana "
                   f"{prr['gana']}, pierde {prr['pierde']}) | M razón en protegidas {rz_txt} (n {nrz}) | M comparador "
                   f"{rm} (pares {len(Pm)}, ĝ {det.get('g_hat_factor', '-')}, d′ {det.get('regla_dprima', '-')}, "
                   f"nota «{det.get('nota', '')}») -> {'cumple' if not motivos else 'no cumple: ' + '; '.join(motivos)}")
                rz2, n2 = razon_prot(PE, v, canal, exigir_k=True)
                pr(f"   razón en protegidas que publican K y P (informa, no decide): "
                   f"{'-' if rz2 is None else f'{rz2:.3f}'} (n {n2})")
                pl = decidir_m([dict(p, d=p["k"] * GANANCIA_PLACEBO) for p in Pm], comparador=False)[0]
                pr(f"   placebo K×1,2 SIN comparador (informa, como evaluar_d25.py): {pl}")
        pr("   protegidas que ni K ni P publican (se listan, no vetan):", sorted(nadie_tot) or "ninguna")
        if not fallas:
            ver = ("== §6 censo: CUMPLE §6.1, §6.2 y §6.4 en T y O, con la tabla sola y con tabla más OCR; falta la "
                   "sombra (§6.3) para proponer P a Nicolás (A45)")
        elif all(v == "O" and x.startswith("P2") for v, _c, x in fallas):
            ver = ("== §6 censo: INFORMAR POR CANAL ANTES DE DECIDIR (falla sólo P2 en la ventana O: "
                   + "; ".join(f"{v}/{c}: {x}" for v, c, x in fallas) + ")")
        else:
            ver = "== §6 censo: NO CUMPLE (" + "; ".join(f"{v}/{c}: {x}" for v, c, x in fallas) + ")"
        ver += f" [posición del record: {NOM_POS[eleccion] if eleccion else 'NINGUNA POSICIÓN ELEGIBLE'}]"   # §6 bis
        pr(ver + (" " + aviso if aviso else ""))
        pr("   S-1 al lado del veredicto: protegidas decididas por la escena, no por el cráter:",
           sorted(s1_prot) or "ninguna", "| protegidas con publicación distinta y S-1 SIN DATO:",
           sorted(s1_sin_diag_prot) or "ninguna")
    else:
        motivos, regs, sin_sus, n_prot = [], {}, True, 0
        for canal in CANALES:
            m, nadie = metricas("P", "TODO", canal)
            reg, neto, nb, _ = p2("P", "K", "TODO", canal)
            regs[canal] = reg
            n_prot += m["n_prot"]
            sin_sus = sin_sus and reg == "SIN SUSTRATO"
            if m["P1"]:
                motivos.append(f"{canal}: P1 {m['P1']}")
            if reg == "PIERDE":
                motivos.append(f"{canal}: P2 PIERDE (neto {neto}, bloques {nb})")
            pr(f"== §6.3 canal {canal}: P1 {m['P1']} (de {m['n_prot']}) | P2 contra K {reg} (neto {neto}, bloques {nb}) "
               f"| protegidas que ni K ni P publican {nadie or 'ninguna'}")
        # S174 (LECTURA LR2): antes de las 4 semanas sólo el veto de P1 es definitivo (una protegida perdida sigue
        # perdida con más noches); un P2 que hoy PIERDE puede no perder con más bloques, y un CUMPLE no vale aún.
        dur_txt = (f"; ventana {t_ini:%Y-%m-%d %H:%M} a {t_fin:%Y-%m-%d %H:%M} UTC, {dias_txt} de {DIAS_MIN_SOMBRA} días, "
                   f"semanas {sem_txt(noches_sem, noches)}"
                   + "".join(f", {v} {sem_txt(*por_v[v])}" for v in sorted(exigidos))
                   + (f"; sin cambio de ROI, {NOCHES_MIN_SIN_CAMBIO} noches o más cada uno: "
                      + ", ".join(f"{v} {por_v[v][1]}" for v in sin_cambio) if sin_cambio and not vol_pocas else ""))
        p1_veta = any(": P1 " in x for x in motivos)
        if motivos and (dur_ok or p1_veta):
            pr("== §6.3 sombra: NO CUMPLE (" + "; ".join(motivos) + dur_txt + ")" + (" " + aviso if aviso else ""))
        elif dur_ok:
            pr(f"== §6.3 sombra: CUMPLE (P1 = 0; P2 tabla {regs['tabla']}, todo {regs['todo']}"
               + ("; con 4 bloques o menos la sombra sólo veta" if sin_sus else "")
               + ("; SIN PROTEGIDAS: P1 no pudo vetar" if not n_prot else "") + dur_txt + ")"
               + (" " + aviso if aviso else ""))
        else:
            rc_final = rc_final or 4
            pr(f"== §6.3 sombra: PROVISORIO ({dias_txt} de {DIAS_MIN_SOMBRA} días de la ventana "
               f"{t_ini:%Y-%m-%d %H:%M} a {t_fin:%Y-%m-%d %H:%M} UTC"
               + ("" if ahora_ok else " (ahora es anterior al fin)")
               + f", semanas {sem_txt(noches_sem, noches)}"
               + (f"; volcanes con ROI cambiada sin sus noches: "
                  + ", ".join(f"{v} {sem_txt(*por_v[v])}" for v in vol_falta) if vol_falta else "")
               + (f"; volcanes sin cambio de ROI con menos de {NOCHES_MIN_SIN_CAMBIO} noches: "
                  + ", ".join(f"{v} {por_v[v][1]}" for v in vol_pocas) if vol_pocas else "")
               + f"; el §4.3 pide 4 semanas, Nicolás 14 noches (también en cada volcán sin cambio de ROI) y la "
               f"coordinadora {NOCHES_MIN_SEMANA} por semana): hoy "
               + ("; ".join(motivos) if motivos else f"P1 = 0; P2 tabla {regs['tabla']}, todo {regs['todo']}")
               + ("; SIN PROTEGIDAS" if not n_prot else "")
               + "; no es CUMPLE ni NO CUMPLE hasta que pase el fin, cada semana tenga sus noches y cada volcán sin cambio "
               f"de ROI sus {NOCHES_MIN_SIN_CAMBIO}" + (" " + aviso if aviso else ""))

    # ---------------------------------------------------------------- informativo
    brazos_inf = ("K", "P") + (("Pdef", "Psinfiltro", "Kgeo") + POS[1:] if censo else ())
    pr("\n== brazos, ventana T y O juntas, canal que decide (informa)")
    for b in brazos_inf:
        if not any((i, b) in PUB for i in oks):
            pr(f"   {b}: sin datos")
            continue
        m, _ = metricas(b, "TODO", "decide")
        lin = (f"   {b:10s} prot {m['n_prot']} P1 {m['P1']} | E {m['E']} (bajas sin publicar {m['E_baja']} de "
               f"{m['n_baja']}, neg publicados {m['E_neg']} de {m['n_neg']})")
        if b != "K":
            reg, neto, nb, _ = p2(b, "K", "TODO", "decide")
            lin += f" | P2 contra K {reg} (neto {neto}, bloques {nb})"
        pr(lin)
    if censo:
        reg, neto, nb, _ = p2("Psinfiltro", PE, "TODO", "decide")
        pr(f"== P-sinfiltro contra P ({nom_pe}; §9.5 del programa, informa; predicción §8: empata o pierde): P2 {reg} "
           f"(neto {neto}, bloques {nb})")
    pr("\n== razón brazo/MIROVA en alertas que deciden publicadas (mediana [q1, q3] n)")
    for b in brazos_inf:
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks if etiqueta(obj[i], "decide") in ("prot", "baja")
                    and pub(i, b) and obj[i].get("mirova_vrp") and vrp(i, b) > 0)
        n = len(rz)
        pr(f"   {b}: " + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}" if n else "-"))
    pr("== curva por cenit: VRP más oblicua sobre menos oblicua de la misma noche y volcán (mediana, n; MIROVA al lado)")
    for b in brazos_inf:
        por = collections.defaultdict(list)
        for i in oks:
            o = obj[i]
            if (etiqueta(o, "decide") in ("prot", "baja") and pub(i, b) and vrp(i, b) > 0 and o.get("mirova_vrp")
                    and o.get("z") is not None):
                por[(o["hora_utc"][:10], o["volcan"])].append(i)
        rb, rm_ = [], []
        for ids in por.values():
            hi, lo = max(ids, key=lambda i: obj[i]["z"]), min(ids, key=lambda i: obj[i]["z"])
            if obj[hi]["z"] > obj[lo]["z"]:
                rb.append(vrp(hi, b) / vrp(lo, b))
                rm_.append(obj[hi]["mirova_vrp"] / obj[lo]["mirova_vrp"])
        pr(f"   {b}: " + (f"brazo {statistics.median(rb):.3f} | MIROVA {statistics.median(rm_):.3f} | n {len(rb)}"
                          if rb else "-"))
    pr("== por volcán y por tramo de 10° de cenit, canal que decide: protegidas publicadas, bajas publicadas, "
       "negativos publicados")
    for clave, f in (("volcán", lambda o: o["volcan"]), ("cenit", lambda o: AB.tramo_z(o.get("z")))):
        for b in brazos_inf:
            t = collections.Counter()
            for i in oks:
                e = etiqueta(obj[i], "decide")
                if e and (i, b) in PUB:
                    g = f(obj[i])
                    t[(g, e)] += 1
                    t[(g, e + "_pub")] += pub(i, b)
            grupos = sorted({g for g, _ in t})
            pr(f"   {clave} {b}: " + " | ".join(
                f"{g} prot {t[(g, 'prot_pub')]}/{t[(g, 'prot')]} baja {t[(g, 'baja_pub')]}/{t[(g, 'baja')]} "
                f"neg {t[(g, 'neg_pub')]}/{t[(g, 'neg')]}" for g in grupos))
    if aviso:
        pr(f"== {aviso}: el veredicto de arriba lleva esta marca")
    return salir(rc_final)


if __name__ == "__main__":
    sys.exit(main())
