# -*- coding: utf-8 -*-
"""S157, tarea 1.29. Evaluador del A/B de D25 (fondo por vecinos) sobre K, en VIIRS 375 y 750.

Implementa TAL CUAL las reglas del §5 y §8 d de experiments/_s157_prereg_d25/PREREGISTRO.md (v2). Si una regla
cambia, cambia acá y en el pre-registro en el mismo commit.

QUÉ REUSA, SIN REIMPLEMENTAR NI TOCAR: de experiments/_s151_prereg_fk_11/evaluar_fk.py (F/K, aprobado en #848) la
tabla por pasada (armar_tabla.py: etiquetador de banco_paridad y el predicado del tablero EJECUTADO CON NODE, A97),
la referencia congelada con sus capas, la protección (lecturas A y B) y las etiquetas de D-9. Lo que este archivo
agrega: brazos K, K', D; sólo VIIRS; la métrica de magnitud M por estrato con bootstrap por bloques de noche-volcán y
su calibración; P1b (cruce de 1 MW), P2 por noche (informa), P4 y P5 leídos de los records crudos; el cableado de D25.

POR QUÉ CADA PIEZA (resumen del pre-registro):
  * M decide sólo donde D25 puede actuar: VIIRS 750 en todo el cenit, VIIRS 375 SIN kernel local con cenit <= 40°;
    VIIRS 375 sin kernel con cenit > 40° sólo puede BLOQUEAR (sello del §8 a); los 5 volcanes con kernel local en
    VIIRS 375 ya restan vecinos y sólo informan (verificador H1).
  * El gemelo da la magnitud idéntica (1.14: «1,00 exacto»), así que no sirve de ruido para M (H3): M decide con el
    intervalo del bootstrap por bloques de noche-volcán (las pasadas de una noche no son independientes, H9) y la
    regla se CALIBRA sobre los mismos pares con efectos de tamaño real y signo al azar (nulo que puede fallar).
  * Decide la lectura A con la regla SN de D-9 (MISSION) y con la original; si discrepan, manda la más estricta.
  * D-28 (ADENDA_PLACEBO.md, sellada el 2026-10-21): un MEJORA de M cuenta sólo si D queda además más cerca de MIROVA
    que una ganancia uniforme del mismo tamaño (K×ĝ), porque K queda bajo MIROVA y cualquier ganancia acerca en
    promedio; EMPEORA sigue sobre D contra K; el placebo K×1,2 y K×0,8 informa y no invalida.
  * D-42 (ADENDA_CALIBRACION_P2.md, sellada el 2026-10-22): P2 (D-34) se calibra como M, con el signo sorteado por
    bloque noche-volcán; si la calibración falla, P2 de ese sensor queda INDECIDIBLE. El estrato 203
    (NOTA_ESTRATO_203.md) se informa y no decide.

Uso:
  python evaluar_d25.py --ventana V1 --raiz <run V1> --logs <run V1>/logs --out v1.json
  python evaluar_d25.py --ventana V2 --raiz <V2a> --raiz <V2b> --logs <V2a>/logs --logs <V2b>/logs --ruido-de v1.json --out v2.json
  python evaluar_d25.py --combinar v1.json v2.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E  # noqa: E402  (deja sys.stdout en utf-8; NO se modifica ningún global suyo)

bp, ev, cm = E.bp, E.ev, E.cm

# ---------------------------------------------------------------- lo que el pre-registro fija (§2, §4, §5)
BRAZOS = {"K": "_s157_ab_d25_k_control", "G": "_s157_ab_d25_k_gemelo", "D": "_s157_ab_d25_k_on"}
# Lo que cada brazo DECLARA en su línea FLAGS_BRAZO (resuelto desde pipeline.profile por el workflow).
DECLARADO = {
    "K": {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True,
          "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375": False, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750": False,
          "VRP_BG_NEIGHBOR_MAX_HALF_PX": 3, "SENSOR_MODIS": False},
}
DECLARADO["G"] = dict(DECLARADO["K"])
DECLARADO["D"] = dict(DECLARADO["K"], ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375=True, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750=True)
VENTANAS = {"V1": {"desde": "2026-08-29", "hasta": "2026-10-18", "ref": AQUI / "_congelado_v1", "solo_tabla": False,
                   "brazos": ("K", "G", "D")},
            "V2": {"desde": "2026-04-01", "hasta": "2026-06-12",
                   "ref": RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v2", "solo_tabla": True,
                   "brazos": ("K", "D")}}
SENS = ("VIIRS375", "VIIRS750")
CORTE_CENIT = 40.0                       # el de D17 (nota S141), ELEGIDO (§5, verificador H7)
FRONTERA_K = "2026-09-18"                # desde acá producción es K; antes, el histórico reprocesado con K
# D-29 (Nicolás, 2026-10-21, tasks/LOOP_OBJETIVOS.md §5): «D25 se evalúa sin el 17 al 20 de octubre ni el 13 parcial,
# declarados en el veredicto». POR QUÉ: esos días CMR no entregó los gránulos a los brazos y producción sí los tiene
# (NRT de su momento), y la cobertura compara contra producción. Se excluyen en los tres brazos por igual y en la
# referencia de cobertura; el 13 entero (excluir pasada por pasada dependería de qué le faltó a cada brazo). El 19 y el
# 20 caen fuera de V1 y se listan para que la regla diga lo mismo que la decisión. Sale en la primera línea del veredicto.
DIAS_EXCLUIDOS = {"V1": ("2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"), "V2": ()}
UMBRAL_DETERMINISMO = 0.98               # heredado de S149 a F/K, elegido
MAX_FALTA_COBERTURA = 0.05               # umbral del instrumento, heredado de F/K, elegido
MOV_KM = 0.01                            # P4: el centroide se mueve más de 0,01 km
N_BOOT, SEMILLA = 10000, 157
N_MIN_PARES, N_MIN_NOCHES = 5, 3
N_CALIB, MAX_FALSOS_CALIB = 200, 0.05    # calibración de M: falsos en 5 % o menos de 200
# Calibración de M. "sellada" es el texto del §5: nulo con el signo de log10(D/K) al azar y falsos = MEJORA o EMPEORA
# en 5 % o menos de 200. Medido antes de correr (calibracion_previa_salida.txt) y por el verificador del evaluador
# (verificador_evaluador/INFORME.md, H1 y H5): con ella el control positivo sale INDECIDIBLE, porque el tope (5 %) es el
# nivel nominal de un intervalo de dos colas (una regla perfecta falla 42 % de las veces) y porque ese nulo da EMPEORA
# cuando K ya calza con MIROVA. "simetrica" es la propuesta de la adenda (ADENDA_CALIBRACION.md, decisión de Nicolás):
# nulo con el SIGNO DE d sorteado por bloque (mediana 0 por construcción), cada cola con su tope de 5 %, las dos colas
# donde el estrato decide y sólo EMPEORA donde bloquea; y un MEJORA cuenta sólo si la mediana de d es negativa en al
# menos dos volcanes del estrato con 3 pares o más (H4: cada estrato lo domina un volcán).
# S159 (tarea I2, VB-2 de AUDIT_S158_R2): el default es el que el sello declara vigente. ADENDA_CALIBRACION.md l. 3 a 8:
# «SELLADA por Nicolás el 2026-10-20 (D-27) ... Rige: §2 entero ... y §3 opción A ... El evaluador corre con
# `--calibracion simetrica`.» Hasta S158 el default era "sellada" (la regla del §5 original, reemplazada por ese sello),
# así que un despacho que olvidara el argumento evaluaba con la regla vieja. "sellada" queda disponible por argumento
# para reproducir lo medido antes del sello (calibracion_previa_salida.txt, caso `sellada` de probar_evaluar_d25.py).
CALIB_MODO = "simetrica"
MIN_VOLCANES_MEJORA, MIN_PARES_VOLCAN = 2, 3
MIN_PARES_PODER, MIN_PODER = 20, 0.80    # control positivo de la calibración (informa)
# S159 (tarea I2, R2-8 de AUDIT_S158_R2): placebo de M. POR QUÉ: un brazo que sólo multiplica la magnitud de K por 1,2
# da MEJORA con la calibración simétrica (experiments/_s158_audit_r2/rb/05_placebo_metrica_m.txt y
# experiments/_s159/instrumentos/placebo_real_salida.txt): K queda bajo MIROVA (razón mediana 0,52 a 0,66 en los
# estratos que deciden), así que cualquier ganancia acerca. La primera versión (1438c8fff) lo usó como COMPUERTA (si un
# placebo da MEJORA, el veredicto es INVALIDO), y con los pares reales eso pasaba siempre: D25 salía inválido hiciera lo
# que hiciera. ADENDA_PLACEBO.md, «SELLADA por Nicolás el 2026-10-21 (D-28)» (commit 2629f5a16), lo cambia a
# COMPARADOR (§2): un MEJORA cuenta sólo si D queda además más cerca de MIROVA que K×ĝ, con ĝ la mediana de log10(D/K)
# del estrato, una ganancia uniforme del mismo tamaño que el efecto típico de D. La compuerta se retira (§2.5) y la
# regla sobre K×1,2 y K×0,8 (sin comparador) se sigue INFORMANDO por estrato, para que quede a la vista cuánto de la
# mejora es ganancia.
PLACEBO_GANANCIAS = (1.2, 0.8)
# D-28 §2.3: la nota con que queda NEUTRO un estrato donde d da MEJORA y d′ no (texto de la adenda).
NOTA_COMPARADOR = "sube en promedio, no en los pares correctos (ADENDA_PLACEBO.md, D-28)"
# D-28 §3: la calibración de d′ es la simétrica de D-27 con su propio sorteo (semilla distinta de la de d) y ĝ fijo en
# su estimación puntual («la calibración prueba la regla bajo el nulo, no a ĝ»).
# D-32 (ADENDA_PLACEBO.md §5.3), SELLADO antes del tag. Cita textual de Nicolás (2026-10-21): «Sí: sube las repeticiones
# de la calibración de d′ (por ejemplo a 1.000) y sella esa semilla y ese número antes del tag, para que una sola
# semilla no decida V2 VIIRS 750.» POR QUÉ: con 200 repeticiones, el verificador con contexto limpio
# (experiments/_s159/instrumentos/verificador_comparador/INFORME.md, H2) midió que esta semilla deja V2 VIIRS 750 z<=40
# en 11 falsos MEJORA de 200 contra un tope de 10: la cola binomial fijada por una semilla (con 20 semillas el mismo d′
# falla en 1). Con 1.000 da 31 de 1.000 contra un tope de 50 (calib_dprima_1000_salida.txt). El tope sigue siendo el
# 5 % por cola (MAX_FALSOS_CALIB). La semilla es 160 (SEMILLA + 3, la misma de b4258040c). La calibración de d (D-27)
# no cambia: 200 repeticiones (N_CALIB).
SEMILLA_CALIB_DPRIMA = SEMILLA + 3       # = 160, sellada (D-32)
N_CALIB_DPRIMA = 1000                    # sellado (D-32)
# D-42 (ADENDA_CALIBRACION_P2.md, «SELLADA por Nicolás el 2026-10-22»): P2 se calibra como M. Cita textual: «Sí a D-42
# opción (a): calibra P2 como M en una cuarta adenda sellada, con los candados de V34-03 y V29-01 y verificador limpio
# antes del tag.» POR QUÉ: el verificador de D-34 (verificador_d34/INFORME.md, V34-01) midió que la regla de D-34 sin
# calibrar decide en falso en 24,8 % de los nulos con 3 noches de signo común (con B noches del mismo lado,
# probabilidad 2^(1-B), ningún remuestreo de bloques cruza 0). El nulo: el signo de cada BLOQUE noche-volcán entero se
# sortea (§2.1); a cada sorteo se le aplica la misma regla de D-34 (§2.2); 1.000 sorteos con la semilla 161 (§2.3); tope
# del 5 % en cada cola por separado (§2.4, MAX_FALSOS_CALIB, 50 de 1.000).
SEMILLA_CALIB_P2 = SEMILLA + 4           # = 161, sellada (D-42 §2.3)
N_CALIB_P2 = 1000                        # sellado (D-42 §2.3)
NOTA_CALIB_P2 = "la calibración de P2 falla: con estas noches no se distingue de un nulo (ADENDA_CALIBRACION_P2.md, D-42)"
# D-30, respuesta 1: si d da MEJORA y la calibración de d′ falla, el estrato queda INDECIDIBLE (no se sabe si hay MEJORA).
NOTA_CALIB_DPRIMA = "la calibración de d′ falla: no se sabe si D sube los pares correctos (ADENDA_PLACEBO.md §5, D-30)"
# Detalle numérico, no de la regla: d′ se redondea a 1e-12 en unidades de log10 (un factor de 1 + 2,3e-12). Con D = K×g
# exacto, d′ es 0 en la aritmética pero ±1e-16 en coma flotante, y una mediana de -1e-17 en todas las réplicas daría un
# intervalo «entero bajo 0» sin ningún efecto (D-28 §3 i exige d′ idénticamente 0 para el placebo).
DEC_DPRIMA = 12
# Del más estricto al menos estricto; «manda la más estricta» entre las reglas original y SN (verificador H15).
ORDEN = ("INVALIDO POR INSTRUMENTO", "NO CUMPLE", "INDECIDIBLE", "PENDIENTE DE REPETICION", "DECIDE NICOLAS",
         "SIN EFECTO", "MEJORA", "CUMPLE")
HITO_SNPP = "2026-10-09"                 # A119: hasta acá las filas sólo OCR de Suomi NPP traen distancia de otra pasada


def volcanes_con_kernel():
    """Los volcanes con kernel local en VIIRS 375 (volcanoes.yaml, local_kernel_bg: true). Leído, no copiado."""
    d = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    return {v["name"] for v in (d.get("volcanoes", d) if isinstance(d, dict) else d) if v.get("local_kernel_bg")}


KERNEL = volcanes_con_kernel()


# ---------------------------------------------------------------- estratos de M
# FUENTE ÚNICA del modo de cada estrato (verificador H17: el modo que devolvía estrato() era código muerto).
# 'decide' (las dos direcciones), 'bloquea' (sólo EMPEORA cuenta, sello §8 a) o 'informa'.
ESTRATOS = (("VIIRS750|z<=40", "decide"), ("VIIRS750|z>40", "decide"), ("VIIRS375|sin_kernel|z<=40", "decide"),
            ("VIIRS375|sin_kernel|z>40", "bloquea"), ("VIIRS375|kernel|z<=40", "informa"),
            ("VIIRS375|kernel|z>40", "informa"))
MODO = dict(ESTRATOS)


def estrato(k, z):
    """(nombre, modo) del estrato de M de una pasada; el modo sale de ESTRATOS. Sin cenit, no entra a ningún estrato
    que decida."""
    vol, b = k.split("|")[0], k.split("|")[1]
    if z is None:
        return ("%s|sin_cenit" % b, "informa")
    tramo = "z<=40" if z <= CORTE_CENIT else "z>40"
    if b == "VIIRS750":
        nom = "VIIRS750|%s" % tramo
    else:
        nom = "VIIRS375|%s|%s" % ("kernel" if vol in KERNEL else "sin_kernel", tramo)
    return nom, MODO[nom]


# ---------------------------------------------------------------- bootstrap por bloques
def pesos_bloque(bloques, n_boot=N_BOOT, semilla=SEMILLA):
    """Matriz (n_boot x n_pares) de cuántas veces entra cada par: se remuestrean BLOQUES (noche-volcán) con
    reposición y cada par hereda el conteo de su bloque."""
    uniq = sorted(set(bloques))
    idx = np.array([uniq.index(b) for b in bloques])
    rng = np.random.default_rng(semilla)
    elegidos = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    cuenta = np.zeros((n_boot, len(uniq)), dtype=np.int64)
    np.add.at(cuenta, (np.repeat(np.arange(n_boot), len(uniq)), elegidos.ravel()), 1)
    return cuenta[:, idx]


def pesos_pasada(n, n_boot=N_BOOT, semilla=SEMILLA):
    """Bootstrap por pasada (cada par es su propio bloque). Sólo para la prueba de que la calibración detecta una
    regla mal calibrada; el pre-registro decide con bloques."""
    return pesos_bloque(list(range(n)), n_boot, semilla)


def medianas_ponderadas(d, W):
    """Mediana de cada réplica: d repetido según la fila de W. Exacta (promedio de los dos centrales si el total es
    par), vectorizada sobre las réplicas."""
    o = np.argsort(d)
    ds, Ws = np.asarray(d, dtype=np.float64)[o], W[:, o]
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    lo_r, hi_r = (tot - 1) // 2, tot // 2           # rangos 0-base de los dos centrales
    # índice del primer par cuyo acumulado supera el rango: cuántos acumulados quedan <= rango (vectorizado)
    i_lo = (cs <= lo_r[:, None]).sum(axis=1)
    i_hi = (cs <= hi_r[:, None]).sum(axis=1)
    return (ds[i_lo] + ds[i_hi]) / 2.0


def medianas_ponderadas_filas(Dm, W):
    """Lo mismo que medianas_ponderadas cuando el vector cambia en cada réplica (fila b de Dm con la fila b de W).
    S159, D-28: d′ depende de ĝ y ĝ se recalcula en cada réplica, así que no se puede ordenar una sola vez."""
    Dm = np.asarray(Dm, dtype=np.float64)
    o = np.argsort(Dm, axis=1, kind="stable")
    ds, Ws = np.take_along_axis(Dm, o, axis=1), np.take_along_axis(W, o, axis=1)
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    lo_r, hi_r = (tot - 1) // 2, tot // 2
    i_lo = (cs <= lo_r[:, None]).sum(axis=1)
    i_hi = (cs <= hi_r[:, None]).sum(axis=1)
    filas = np.arange(Dm.shape[0])
    return (ds[filas, i_lo] + ds[filas, i_hi]) / 2.0


def regla_m(d, W):
    """MEJORA si el intervalo al 95 % de la mediana de d queda entero bajo 0; EMPEORA si entero sobre 0."""
    meds = medianas_ponderadas(d, W)
    lo, hi = np.percentile(meds, 2.5), np.percentile(meds, 97.5)
    return ("MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"), float(lo), float(hi)


def d_par(k_mw, d_mw, m_mw):
    return abs(math.log10(d_mw / m_mw)) - abs(math.log10(k_mw / m_mw))


def calibrar(pares, W, bloques, n_rep=N_CALIB, semilla=SEMILLA + 1):
    """Nulo que PUEDE fallar (§5, reemplaza al de K' en lugar de D, H3): a cada par se le cambia D por
    K·10^(±e), con e = |log10(D/K)| observado y el signo al azar; se aplica la regla. El signo se sortea por BLOQUE
    (noche-volcán), no por par: las pasadas de una noche comparten el estado del volcán y de la atmósfera, y un signo por
    par rompería justo la dependencia que el bootstrap por bloques tiene que absorber (con signo por par, la prueba de
    unidad de probar_evaluar_d25.py no distinguía bloques de pasadas). `bloques` es obligatorio: sin él no hay nulo. Devuelve la fracción de
    repeticiones con MEJORA y con EMPEORA (por separado) y, como control positivo, si con el signo fijo hacia MIROVA
    la regla da MEJORA (poder)."""
    rng = np.random.default_rng(semilla)
    K = np.array([p["k"] for p in pares]); M = np.array([p["m"] for p in pares])
    e = np.abs(np.log10(np.array([p["d"] for p in pares]) / K))
    falsos = collections.Counter()
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    for _ in range(n_rep):
        s = rng.choice((-1.0, 1.0), size=len(uniq))[idx]
        dd = np.abs(np.log10(K * 10 ** (s * e) / M)) - np.abs(np.log10(K / M))
        falsos[regla_m(dd, W)[0]] += 1
    hacia = np.sign(np.log10(M / K))
    dd = np.abs(np.log10(K * 10 ** (hacia * np.minimum(e, np.abs(np.log10(M / K)))) / M)) - np.abs(np.log10(K / M))
    poder = regla_m(dd, W)[0] == "MEJORA" if np.any(e > 0) else False
    return falsos["MEJORA"] / n_rep, falsos["EMPEORA"] / n_rep, bool(poder)


def calibrar_simetrico(d, W, bloques, n_rep=N_CALIB, semilla=SEMILLA + 2):
    """Calibración propuesta en ADENDA_CALIBRACION.md (verificador del evaluador, H5): el SIGNO DE d se sortea por
    bloque, así el nulo tiene mediana 0 por construcción y las dos colas se miden por separado. Devuelve (falsos
    MEJORA, falsos EMPEORA, poder), con el poder medido con todos los d hacia MIROVA (-|d|)."""
    rng = np.random.default_rng(semilla)
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    a = np.abs(np.asarray(d, dtype=np.float64))
    falsos = collections.Counter()
    for _ in range(n_rep):
        falsos[regla_m(rng.choice((-1.0, 1.0), size=len(uniq))[idx] * a, W)[0]] += 1
    poder = regla_m(-a, W)[0] == "MEJORA" if np.any(a > 0) else False
    return falsos["MEJORA"] / n_rep, falsos["EMPEORA"] / n_rep, bool(poder)


def comparar_con_ganancia(P, W, bloques):
    """D-28 (ADENDA_PLACEBO.md, sellada por Nicolás el 2026-10-21, commit 2629f5a16), §2 y §3: la regla sellada de D-27
    aplicada a d′ = |log10(D/MIROVA)| − |log10(ĝ·K/MIROVA)|, con ĝ la mediana de log10(D/K) del estrato.

    POR QUÉ. K queda bajo MIROVA en los estratos que deciden, así que cualquier ganancia de magnitud acerca a MIROVA en
    promedio. d′ pregunta otra cosa: si D queda más cerca de MIROVA que una ganancia UNIFORME del mismo tamaño que el
    efecto típico de D, o sea si D sube los pares que debe subir. Para una ganancia uniforme (el placebo) d′ es 0.

    Cómo, sin más elecciones que las de la adenda:
      * ĝ puntual = mediana de log10(D/K) sobre los pares (§2.1). En cada réplica del bootstrap ĝ se recalcula con los
        MISMOS pesos por bloque que la mediana de d′ (§3, primer punto), así la incertidumbre de ĝ entra al intervalo.
      * Regla de D-27 sobre d′: intervalo al 95 % entero bajo 0; calibración simétrica de d′ (signo de d′ sorteado por
        bloque, ĝ fijo en su estimación puntual, §3) con tope de 5 % en la cola de MEJORA, la única que d′ usa (D-30,
        respuesta 2); y mediana de d′ negativa en al menos dos volcanes con 3 pares o más (opción A).
      * ĝ por volcán se informa y no decide (§3, segundo punto).
    Devuelve el detalle; `dprima_da_mejora` es la conjunción de las tres condiciones. Si la calibración falla y d da
    MEJORA, decidir_estrato deja el estrato INDECIDIBLE (D-30, respuesta 1)."""
    K = np.array([p["k"] for p in P], dtype=np.float64)
    Dv = np.array([p["d"] for p in P], dtype=np.float64)
    M = np.array([p["m"] for p in P], dtype=np.float64)
    lK, lD = np.log10(K / M), np.log10(Dv / M)
    g = lD - lK                                        # = log10(D/K)
    g_hat = float(np.median(g))                        # §2.1, estimación puntual
    dp = np.round(np.abs(lD) - np.abs(lK + g_hat), DEC_DPRIMA)
    # §3: ĝ por réplica con los mismos pesos por bloque que la mediana de d′
    g_b = medianas_ponderadas(g, W)
    Dp = np.round(np.abs(lD)[None, :] - np.abs(lK[None, :] + g_b[:, None]), DEC_DPRIMA)
    meds = medianas_ponderadas_filas(Dp, W)
    lo, hi = float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))
    r_p = "MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"
    f_mej, f_emp, poder = calibrar_simetrico(dp, W, bloques, n_rep=N_CALIB_DPRIMA, semilla=SEMILLA_CALIB_DPRIMA)
    # D-30, respuesta 2: d′ sólo se usa para MEJORA, así que sólo se exige la cola de MEJORA (f_emp se informa). Es lo
    # mismo que D-27 hace en el estrato que sólo bloquea: se exige la cola que puede decidir.
    calibrada = f_mej <= MAX_FALSOS_CALIB
    vols_neg, vols_n, g_vol = 0, 0, {}
    for v_ in sorted({p["clave"].split("|")[0] for p in P}):
        sel = np.array([p["clave"].startswith(v_ + "|") for p in P])
        if sel.sum() >= MIN_PARES_VOLCAN:
            vols_n += 1; vols_neg += float(np.median(dp[sel])) < 0
        gv = float(np.median(g[sel]))
        g_vol[v_] = {"n": int(sel.sum()), "log": gv, "factor": float(10 ** gv)}
    return {"g_hat_log": g_hat, "g_hat_factor": float(10 ** g_hat),
            "g_hat_ic95": [float(np.percentile(g_b, 2.5)), float(np.percentile(g_b, 97.5))],
            "g_hat_por_volcan": g_vol, "regla_dprima": r_p, "dprima_mediana": float(np.median(dp)),
            "ic95_dprima": [lo, hi], "dprima_max_abs": float(np.max(np.abs(dp))),
            "falsos_mejora_dprima": f_mej, "falsos_empeora_dprima": f_emp, "calibrada_dprima": calibrada,
            "poder_dprima": poder if len(P) >= MIN_PARES_PODER else None,
            "volcanes_con_dprima_negativa": vols_neg, "volcanes_con_3_pares_dprima": vols_n,
            "dprima_da_mejora": bool(r_p == "MEJORA" and calibrada and vols_neg >= MIN_VOLCANES_MEJORA)}


# ---------------------------------------------------------------- carga
def fusionar(raices, tmp, brazos, vols):
    """V2 llega en dos despachos: junta los records de cada perfil y volcán en un solo directorio."""
    if len(raices) == 1:
        return Path(raices[0])
    dst = tmp / "fusion"
    for n in brazos:
        for v in vols:
            recs = []
            for r in raices:
                p = Path(r) / BRAZOS[n] / (v + ".json")
                if p.exists():
                    recs += json.load(open(p, encoding="utf-8"))["records"]
            if recs:
                (dst / BRAZOS[n]).mkdir(parents=True, exist_ok=True)
                json.dump({"records": recs}, open(dst / BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
    return dst


def filtrar_dias(claves, dias):
    """D-29: saca de un dict o un set las pasadas (clave «volcán|sensor|fecha...») cuya fecha UTC está en `dias`."""
    dias = set(dias)
    if not dias:
        return claves
    if isinstance(claves, dict):
        return {k: v for k, v in claves.items() if k.split("|")[2][:10] not in dias}
    return {k for k in claves if k.split("|")[2][:10] not in dias}


def crudos(raiz, n, vols, desde, hasta):
    """Lo que la tabla no expone, por pasada: versión, Test 1, huella de D25, sensor MODIS, etiqueta, P5."""
    out, modis = {}, 0
    for v in vols:
        p = raiz / BRAZOS[n] / (v + ".json")
        if not p.exists():
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b, t = bp.bucket(r.get("sensor")), r.get("datetime_utc", "")
            if b is None or not (desde <= t[:10] <= hasta):
                continue
            if b == "MODIS":
                modis += 1
                continue
            pc = r.get("primary_cluster") or {}
            out["|".join((v, b, t[:16]))] = {
                "pv": r.get("product_version"), "t1": bool(r.get("triggered_test1")), "con_pc": bool(pc),
                "huella_d25": "diag_bg_vecinos_n_sin_vecinos" in r, "dc": r.get("distance_class"),
                "d9": bool(pc.get("d9_capped")), "un_pixel": pc.get("single_pixel_mode"),
                "descartado": r.get("discarded_reason"), "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km")}
    return out, modis


def claves_cobertura(dirs, vols, desde, hasta):
    """Pasadas VIIRS de la referencia de cobertura: el histórico con K antes de FRONTERA_K y producción desde ahí;
    para un volcán sin histórico en la fecha (Chillán), producción (las pasadas no dependen del detector)."""
    hist, prod = (Path(x) for x in dirs)
    out = collections.defaultdict(set)
    for v in vols:
        fechas_h = set()
        if (hist / (v + ".json")).exists():
            for r in json.load(open(hist / (v + ".json"), encoding="utf-8"))["records"]:
                t, b = r.get("datetime_utc", ""), bp.bucket(r.get("sensor"))
                if b in SENS and desde <= t[:10] <= hasta and t[:10] < FRONTERA_K:
                    out[(v, b)].add("|".join((v, b, t[:16]))); fechas_h.add(t[:10])
        if (prod / (v + ".json")).exists():
            for r in json.load(open(prod / (v + ".json"), encoding="utf-8"))["records"]:
                t, b = r.get("datetime_utc", ""), bp.bucket(r.get("sensor"))
                if b in SENS and desde <= t[:10] <= hasta and (t[:10] >= FRONTERA_K or t[:10] not in fechas_h):
                    out[(v, b)].add("|".join((v, b, t[:16])))
    return out


def flags_leidos(logs, n, vol):
    out = []
    for d in logs:
        p, fl = Path(d) / ("%s_%s.log" % (BRAZOS[n], vol)), None
        if p.exists():
            for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if linea.startswith("FLAGS_BRAZO "):
                    fl = json.loads(linea[len("FLAGS_BRAZO "):]); break
        out.append((Path(d).as_posix(), fl))
    return out


def sin_geometria(claves_, ref, desde, hasta):
    """VRP de la fila ALERTA_SIN_GEOMETRIA_OCR de cada pasada (estrato aparte: en M sólo informa)."""
    cons, ocr, capas = ref
    kw = {"historico_path": capas["historico"], "respaldo_path": capas["respaldo"]} if capas else {}
    filas = ev.cargar_referencia_unificada(Path(cons), Path(ocr), **kw)
    por_vb, *_ = bp.indexar_referencia(filas, bp._coords_por_volcan(), (desde, hasta))
    out = {}
    from datetime import datetime, timezone
    for k in claves_:
        vol, b, t = k.split("|")
        ff = bp.parear(por_vb.get((vol, b), []), datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
        sg = [f["vrp_mw"] for f in ff if bp.es_sin_geometria(f["tipo"]) and f.get("vrp_mw")]
        if sg:
            out[k] = sg[0]
    return out


# ---------------------------------------------------------------- contabilidad con una regla de etiquetas
def es_snpp(k, c, prot):
    """Pasada cuya alerta descansa sólo en el OCR de Suomi NPP ANTES del hito del 2026-10-09 (verificador H14)."""
    return E.ocr_snpp(k, c, prot) and k.split("|")[2][:10] < HITO_SNPP


# ---------------------------------------------------------------- P2 con ruido de muestreo (D-34)
# ADENDA_GEMELO.md, «SELLADA por Nicolás el 2026-10-21 (D-34)». POR QUÉ: en V1 los tres brazos corren en el mismo job,
# en serie sobre la misma CPU, y el gemelo K' sale copia bit a bit de K (0 de 4.610 pasadas distintas,
# experiments/_s159/gemelo_d25/INFORME.md en s159-pruebas, d5b6839b2): el «ruido del gemelo» vale 0 por construcción y
# P2 decidía con una sola pasada neta. Lo que importa es el ruido de MUESTREO: si D publica mejor que K en general o sólo
# en estas noches. Las pasadas de una noche comparten volcán y atmósfera (H9), así que el intervalo es por bloques
# noche-volcán, con la maquinaria y la semilla de M (pesos_bloque, D-27).

def contribuciones_p2(TKD, prot, lect, cfg, s, excluir):
    """Las pasadas discordantes de P2 (error en un brazo y no en el otro) con su aporte al neto. Signo de la definición
    de P2 del pre-registro (§5), que cuenta ERRORES: +1 si el error es sólo de D, -1 si es sólo de K; positivo es malo
    para D. Una alerta Muy Bajo que D publica y K no resta; una publicación de D en un negativo limpio que K no tiene
    suma. La suma de los aportes es la suma de D menos la de K (mismo conjunto que suma_errores)."""
    eK = E.errores_por_pasada(TKD, "control", prot, lect, cfg, s, excluir)
    eD = E.errores_por_pasada(TKD, "brazo", prot, lect, cfg, s, excluir)
    return [{"clave": k, "c": 1 if k in eD else -1, "bloque": "%s|%s" % (k.split("|")[0], k.split("|")[2][:10])}
            for k in sorted(eK ^ eD)]


def regla_p2(sumas, neto):
    """D-34 §5.4 y §5.5 sobre las sumas del bootstrap: GANA si el intervalo al 95 % queda entero bajo 0; PIERDE si queda
    entero sobre 0; si cruza 0 (o lo toca), BLOQUEA cuando el neto puntual es positivo y EMPATE si no. S160 (D-42): la
    misma función decide la pasada observada y cada sorteo de la calibración, así que las dos usan la misma regla."""
    lo, hi = float(np.percentile(sumas, 2.5)), float(np.percentile(sumas, 97.5))
    if hi < 0:
        return "GANA", lo, hi
    if lo > 0:
        return "PIERDE", lo, hi
    elif neto > 0:
        return "BLOQUEA", lo, hi
    return "EMPATE", lo, hi


def calibrar_p2(c, bloques, W, n_rep=N_CALIB_P2, semilla=SEMILLA_CALIB_P2):
    """D-42 §2 (ADENDA_CALIBRACION_P2.md): el nulo de P2. En cada sorteo, el signo de cada BLOQUE noche-volcán entero
    (todas sus contribuciones a la vez) se multiplica por +1 o -1 al azar, y se aplica regla_p2 con la MISMA matriz W
    de D-34 (pesos_bloque con 10.000 remuestreos y semilla 157; depende sólo de los bloques, que el sorteo no cambia).
    POR QUÉ por bloque: bajo el nulo D y K son intercambiables dentro de una noche, y cambiar los brazos de una noche
    invierte todas sus contribuciones a la vez (§2.1; el mismo sorteo que calibrar_simetrico hace para M).
    Devuelve las fracciones de sorteos con GANA, PIERDE y BLOQUEA (falsos GANA, falsos PIERDE, falsos BLOQUEA), y el
    número de sorteos y la semilla que usó de verdad (V42-04: el detalle los declara desde aquí, no desde las constantes)."""
    rng = np.random.default_rng(semilla)
    c = np.asarray(c, dtype=np.float64)
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    S = np.array([rng.choice((-1.0, 1.0), size=len(uniq))[idx] for _ in range(n_rep)])   # un signo por bloque y sorteo
    Wf = np.asarray(W, dtype=np.float64)
    cuenta = collections.Counter()
    for i0 in range(0, n_rep, 100):                     # de a 100 sorteos: 10.000 x 100 sumas en memoria
        C = S[i0:i0 + 100] * c[None, :]
        sumas = Wf @ C.T
        for j in range(C.shape[0]):
            cuenta[regla_p2(sumas[:, j], int(round(C[j].sum())))[0]] += 1
    return cuenta["GANA"] / n_rep, cuenta["PIERDE"] / n_rep, cuenta["BLOQUEA"] / n_rep, int(n_rep), int(semilla)


def decidir_p2_bloques(contrib, ok_ctrl):
    """D-34 §5: GANA si el intervalo al 95 % del neto (bootstrap por bloques noche-volcán) queda entero bajo 0; PIERDE si
    queda entero sobre 0; si cruza 0, BLOQUEA cuando el neto puntual es positivo (en contra de D: bloquea CUMPLE, como un
    EMPEORA en un estrato que sólo bloquea) y EMPATE si no. Con menos pasadas o noches que los mínimos de M, SIN SUSTRATO.
    S160, D-42 §2: después del SIN SUSTRATO y sólo con los controles OK, la regla se calibra (calibrar_p2); si los falsos
    GANA o los falsos PIERDE pasan del 5 %, P2 queda INDECIDIBLE sea cual sea su resultado sin calibrar, que se informa
    al lado (§2.5). BLOQUEA no se calibra: su fracción se informa y no decide (§2.6). Todo va al detalle (§2.7)."""
    c = np.array([x["c"] for x in contrib], dtype=np.float64)
    bl_p2 = [x["bloque"] for x in contrib]
    neto = int(round(c.sum())) if len(c) else 0
    det = {"neto": neto, "n_discordantes": len(c), "noches_discordantes": len(set(bl_p2)), "ic95": None,
           "regla": "D-34: neto de errores (D menos K) con intervalo por bloques noche-volcán; calibrada por D-42",
           # D-42 §2.7: se informa siempre; sin calibración (controles caídos o sin sustrato) los falsos, los sorteos y
           # la semilla quedan en None (V42-04: sorteos y semilla son los que calibrar_p2 usó, no las constantes)
           "resultado_sin_calibrar": None, "calibrada": None, "falsos_gana": None, "falsos_pierde": None,
           "falsos_bloquea": None, "n_sorteos": None, "semilla_calibracion": None,
           "tope_por_cola": MAX_FALSOS_CALIB, "nota_calibracion": ""}
    if not ok_ctrl:
        det["resultado_sin_calibrar"] = "INDECIDIBLE"
        det["nota_calibracion"] = "no se calibra: controles generales caídos"
        return "INDECIDIBLE", det
    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:
        det["resultado_sin_calibrar"] = "SIN SUSTRATO"
        det["nota_calibracion"] = "no se calibra: sin sustrato (D-34 §5.6)"
        return "SIN SUSTRATO", det
    W = pesos_bloque(bl_p2)
    v, lo, hi = regla_p2(W @ c, neto)
    det["ic95"] = [lo, hi]
    f_gana, f_pierde, f_bloquea, n_usados, semilla_usada = calibrar_p2(c, bl_p2, W)
    calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB
    det.update(resultado_sin_calibrar=v, calibrada=bool(calibrada), falsos_gana=f_gana, falsos_pierde=f_pierde,
               falsos_bloquea=f_bloquea, n_sorteos=n_usados, semilla_calibracion=semilla_usada)
    if not calibrada:
        det["nota_calibracion"] = "%s (falsos GANA %.3f, PIERDE %.3f, tope %.2f por cola)" % (
            NOTA_CALIB_P2, f_gana, f_pierde, MAX_FALSOS_CALIB)
        return "INDECIDIBLE", det
    return v, det


def lista_p2(contrib, TKD, R):
    """D-34 §5.7: cada pasada discordante, para diagnosticar; no decide."""
    out = []
    for x in contrib:
        k = x["clave"]
        v = TKD.get(k, {})
        c, b = v.get("control", {}), v.get("brazo", {})
        vol, sensor, hora = k.split("|")
        out.append({"volcan": vol, "sensor": sensor, "hora": hora, "publica_K": bool(c.get("pub")),
                    "publica_D": bool(b.get("pub")), "clase_mirova": c.get("lab", b.get("lab")),
                    "vrp_mirova": c.get("vrp_ref"), "pc_vrp_mw_K": (R.get("K", {}).get(k) or {}).get("pc_vrp"),
                    "pc_vrp_mw_D": (R.get("D", {}).get(k) or {}).get("pc_vrp"), "error_de": "D" if x["c"] > 0 else "K",
                    "contribucion": x["c"]})
    return out


def estrato_203(TKD, prot, R, lect, cfg, excluir, s="VIIRS750"):
    """NOTA_ESTRATO_203.md (5f986a209, declarado antes del tag): SÓLO INFORMA, no entra a P1, P1b, P2, M, global_ventana
    ni combinar. POR QUÉ: la auditoría S160 (hallazgo 203) midió que en K 30 de 97 cúmulos de cumbre de VIIRS 750 quedan
    en 0,0 MW (el exceso sobre el anillo se recorta a cero) y el tablero no publica nada con 0 MW; D25 cambia justo ese
    fondo, así que ahí es donde más puede mover la publicación, en los dos sentidos. Mezclado con el resto se diluye en P2.
    Pasadas de VIIRS 750 cuyo cúmulo de cumbre en K (distance_class summit) tiene pc.vrp_mw 0 o ausente. Totales: recupera
    (alerta que D publica y K no), enciende (negativo limpio que D publica y K no), no cambia (misma publicación) y otros
    cambios (el resto, para que los totales sumen n)."""
    eK = E.errores_por_pasada(TKD, "control", prot, lect, cfg, s, excluir)
    eD = E.errores_por_pasada(TKD, "brazo", prot, lect, cfg, s, excluir)
    pasadas = []
    tot = collections.Counter()
    for k in sorted(TKD):
        v = TKD[k]
        rk = R.get("K", {}).get(k)
        if k.split("|")[1] != s or len(v) != 2 or not rk or rk.get("dc") != "summit" or rk.get("pc_vrp") not in (0, None):
            continue
        c, b = v["control"], v["brazo"]
        clase = ("protegida" if prot.get(k, {}).get(lect) else "alerta" if c["lab"] == "pos" else
                 "negativo limpio" if c["lab"] == "neg_limpio" else "otra")
        vol, _, hora = k.split("|")
        pasadas.append({"volcan": vol, "hora": hora, "clase_mirova": clase, "vrp_mirova": c.get("vrp_ref"),
                        "publica_K": bool(c["pub"]), "publica_D": bool(b["pub"]), "pc_vrp_mw_K": rk.get("pc_vrp"),
                        "pc_vrp_mw_D": (R.get("D", {}).get(k) or {}).get("pc_vrp"),
                        "error_p2_de": "K y D" if k in eK and k in eD else "K" if k in eK else "D" if k in eD else None})
        if bool(c["pub"]) == bool(b["pub"]):
            tot["no_cambia"] += 1
        elif b["pub"] and c["lab"] == "pos":
            tot["recupera_D"] += 1
        elif b["pub"] and c["lab"] == "neg_limpio":
            tot["enciende_D"] += 1
        else:
            tot["otros_cambios"] += 1
    return {"sensor": s, "n": len(pasadas), "recupera_D": tot["recupera_D"], "enciende_D": tot["enciende_D"],
            "no_cambia": tot["no_cambia"], "otros_cambios": tot["otros_cambios"], "pasadas": pasadas,
            "nota": "informa, no decide (NOTA_ESTRATO_203.md)"}


def regla_b_d33(v_a, margen):
    """(b), D-33, nunca adoptada: la regla del gemelo, pero un GANA o PIERDE de una o dos pasadas netas queda pendiente
    de diagnóstico por pasada. D-34 §5.8: se informa para ver si la elección de regla cambia el veredicto."""
    if v_a in ("GANA", "PIERDE") and margen <= 2:
        return "PENDIENTE DE DIAGNOSTICO POR PASADA (%s por %d)" % (v_a, margen)
    return v_a


def decidir_estrato(P, modo, modo_calib, ok_ctrl, comparador=True):
    """La decisión de M de UN estrato con sus pares P (k, d, m, clave, bloque): regla, calibración y opción A.
    S159: extraída sin cambios de contar() para poder correrla también sobre los placebos (evaluar_m).
    S159, D-28: con la calibración simétrica, en los estratos que deciden o bloquean se calcula además el comparador
    (comparar_con_ganancia); un MEJORA cuenta sólo si d′ también da MEJORA, y si no queda NEUTRO con NOTA_COMPARADOR.
    EMPEORA se sigue juzgando sobre d (§2.4). comparador=False es sólo para informar el placebo «sin comparador» (§2.5).
    Con la calibración "sellada" (la del §5 original, para reproducir lo medido antes de D-27) no se aplica: D-28 se
    escribió sobre D-27 y su calibración de d′ es la simétrica."""
    d = np.array([d_par(p["k"], p["d"], p["m"]) for p in P])
    W = pesos_bloque([p["bloque"] for p in P])
    r, lo, hi = regla_m(d, W)
    bl = [p["bloque"] for p in P]
    vols_neg, vols_n = 0, 0
    for v_ in sorted({p["clave"].split("|")[0] for p in P}):
        dv = [x for x, p in zip(d, P) if p["clave"].startswith(v_ + "|")]
        if len(dv) >= MIN_PARES_VOLCAN:
            vols_n += 1; vols_neg += float(np.median(dv)) < 0
    nota = ""
    if modo_calib == "sellada":
        f_mej, f_emp, poder = calibrar(P, W, bl)
        calibrada = f_mej + f_emp <= MAX_FALSOS_CALIB
    else:
        f_mej, f_emp, poder = calibrar_simetrico(d, W, bl)
        calibrada = (f_emp <= MAX_FALSOS_CALIB) if modo == "bloquea" else (f_mej <= MAX_FALSOS_CALIB and f_emp <= MAX_FALSOS_CALIB)
    if modo == "informa":
        r_dec = r                  # no decide: se informa la regla tal cual
    elif not ok_ctrl or not calibrada:
        r_dec = "INDECIDIBLE"
    elif modo == "bloquea" and r == "MEJORA":
        r_dec = "NEUTRO"           # sello §8 a: en este estrato una mejora no cuenta
    elif modo_calib == "simetrica" and r == "MEJORA" and vols_neg < MIN_VOLCANES_MEJORA:
        r_dec, nota = "NEUTRO", "MEJORA sostenida por menos de %d volcanes (adenda, H4)" % MIN_VOLCANES_MEJORA
    else:
        r_dec = r
    detalle = {"n": len(P), "noches": len(set(bl)), "modo": modo, "regla": r, "d_mediana": float(np.median(d)),
               "ic95": [lo, hi], "razon_K": float(np.median([p["k"] / p["m"] for p in P])),
               "razon_D": float(np.median([p["d"] / p["m"] for p in P])),
               "falsos_mejora": f_mej, "falsos_empeora": f_emp, "modo_calibracion": modo_calib,
               "volcanes_con_d_negativa": vols_neg, "volcanes_con_3_pares": vols_n, "nota": nota,
               "calibrada": calibrada, "poder": poder if len(P) >= MIN_PARES_PODER else None}
    # ---- D-28, el comparador (ADENDA_PLACEBO.md §2.3): un MEJORA de d cuenta sólo si d′ también da MEJORA
    if comparador and modo_calib == "simetrica" and modo != "informa":
        detalle.update(comparar_con_ganancia(P, W, bl))
        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:
            # D-30, respuesta 1: como en D-27, un estrato cuya calibración falla no decide; aquí d′ es condición
            # necesaria del MEJORA, así que el estrato queda INDECIDIBLE (y con él la ventana, global_ventana).
            r_dec = "INDECIDIBLE"
            detalle["nota"] = "%s (falsos MEJORA de d′ %.3f, tope %.2f)" % (
                NOTA_CALIB_DPRIMA, detalle["falsos_mejora_dprima"], MAX_FALSOS_CALIB)
        elif r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:
            r_dec = "NEUTRO"
            detalle["nota"] = NOTA_COMPARADOR
    return r_dec, detalle


def evaluar_m(pares, ok_ctrl, modo_calib=CALIB_MODO):
    """M de todos los estratos. `pares`: {estrato: [pares]}. Devuelve (ver, info) con las claves M|<estrato> (ver) y
    M_pares, M_pares_con_magnitud_distinta, M_placebo (info).

    Placebo (S159, R2-8; desde D-28 sólo INFORMA, ADENDA_PLACEBO.md §2.5): para cada estrato que decide o bloquea, la
    regla sellada SIN comparador sobre un brazo D = K×g, con g en PLACEBO_GANANCIAS y los controles dados por buenos (se
    prueba la métrica, no la corrida). Muestra cuánto aprobaría una ganancia cualquiera; no vuelve INVALIDO nada. El
    comparador que sí decide está dentro de decidir_estrato, y ĝ queda en el detalle de cada estrato."""
    ver, info = {}, {}
    # Verificador H8: la huella dice que el flag se leyó, no que D25 actuó. Cuántos pares cambian de magnitud.
    todos = [p for P in pares.values() for p in P]
    info["M_pares_con_magnitud_distinta"] = sum(abs(p["d"] - p["k"]) > 1e-9 for p in todos)
    info["M_pares"] = len(todos)
    info["M_placebo"] = {}
    for nom, modo in ESTRATOS:
        P = pares.get(nom, [])
        bloques = sorted({p["bloque"] for p in P})
        clave = "M|%s" % nom
        if len(P) < N_MIN_PARES or len(bloques) < N_MIN_NOCHES:
            ver[clave], info[clave] = "SIN SUSTRATO", {"n": len(P), "noches": len(bloques), "modo": modo}
            continue
        ver[clave], info[clave] = decidir_estrato(P, modo, modo_calib, ok_ctrl)
        if modo == "informa":
            continue
        info["M_placebo"][nom] = {str(g): decidir_estrato([dict(p, d=p["k"] * g) for p in P], modo, modo_calib, True,
                                                          comparador=False)[0] for g in PLACEBO_GANANCIAS}
    return ver, info


def contar(T, prot, R, cfg, regla, res_ctrl, ruido_frac_de, inner, modo_calib=CALIB_MODO, T_rep=None):
    """Las pruebas P1, P1b, P2 y M con las etiquetas ya fijadas en T (regla 'original' o 'SN')."""
    ver, info = {}, {"regla": regla}
    brazos = cfg["brazos"]
    ok_ctrl = res_ctrl["controles_ok"] and all(res_ctrl["cableado"].values())
    TKD = T[("K", "D")]
    TKG = T.get(("K", "G"))
    excluir = not cfg["solo_tabla"]
    lect = "A"
    # ---- P1 y P1b
    for s in SENS:
        netas, ruidosas, pendientes, snpp, cruces, descartadas, n_pub = [], [], [], [], [], [], 0
        for k, v in TKD.items():
            if len(v) != 2 or k.split("|")[1] != s or not prot[k][lect]:
                continue
            c, b = v["control"], v["brazo"]
            if not c["pub"]:
                continue
            if excluir and es_snpp(k, c, prot):
                snpp.append(k); continue
            n_pub += 1
            if b["pub"] and (c["disp"] or 0) >= 1 > (b["disp"] or 0):
                cruces.append("%s | K %.3f MW -> D %.3f MW | MIROVA %s" % (k, c["disp"], b["disp"], c["vrp_ref"]))
            if b["pub"]:
                continue
            g = TKG.get(k) if TKG else None
            rp = (T_rep or {}).get(k)
            if rp is not None and len(rp) == 2:
                # §4 y F/K §5: con la repetición de los jobs de ese volcán la pérdida se decide ahí
                (netas if rp["control"]["pub"] and not rp["brazo"]["pub"] else descartadas).append(k)
            elif g is not None and len(g) == 2 and g["control"]["pub"] != g["brazo"]["pub"]:
                ruidosas.append(k)
            elif "G" not in brazos:
                pendientes.append(k)
            else:
                netas.append(k)
        v_ = ("INDECIDIBLE" if not ok_ctrl else "VETADO" if netas else "INDECIDIBLE" if ruidosas else
              "PENDIENTE DE REPETICION" if pendientes else "SIN SUSTRATO" if n_pub == 0 else "CUMPLE")
        ver["P1|%s" % s] = v_
        info["P1|%s" % s] = {"protegidas_que_K_publica": n_pub, "netas": netas, "ruidosas": ruidosas,
                             "pendientes": pendientes, "solo_ocr_snpp": snpp, "cruces_1MW": cruces,
                             "descartadas_por_repeticion": descartadas}
        ver["P1b|%s" % s] = "LISTA (decide Nicolas)" if cruces else "SIN CRUCES"
    # ---- P2
    for s in SENS:
        sk = sum(E.suma_errores(TKD, "control", prot, lect, cfg, s, excluir)[:2])
        sd = sum(E.suma_errores(TKD, "brazo", prot, lect, cfg, s, excluir)[:2])
        if TKG is not None:
            ruido = len(E.errores_por_pasada(TKG, "control", prot, lect, cfg, s, excluir)
                        ^ E.errores_por_pasada(TKG, "brazo", prot, lect, cfg, s, excluir))
            info.setdefault("ruido_frac", {})[s] = ruido / sk if sk else 0.0
        elif ruido_frac_de:
            ruido = ruido_frac_de.get(regla, {}).get(s, 0.0) * sk
        else:
            ruido = 0.0
        # (a) la regla del pre-registro §5 (ruido del gemelo), que D-34 retira: se informa, no decide
        v_a = ("INDECIDIBLE" if not ok_ctrl else "GANA" if sd < sk - ruido else "PIERDE" if sd > sk + ruido else "EMPATE")
        # D-34 (ADENDA_GEMELO.md §5): decide el neto de errores con intervalo por bloques noche-volcán
        contrib = contribuciones_p2(TKD, prot, lect, cfg, s, excluir)
        v_, det = decidir_p2_bloques(contrib, ok_ctrl)
        ver["P2|%s" % s] = v_
        noches = {lado: {(k.split("|")[0], k.split("|")[2][:10]) for k in
                         E.errores_por_pasada(TKD, lado, prot, lect, cfg, s, excluir)} for lado in ("control", "brazo")}
        info["P2|%s" % s] = dict(det, suma_K=sk, suma_D=sd, ruido_gemelo=ruido,
                                 neto_igual_a_suma_D_menos_suma_K=(det["neto"] == sd - sk),
                                 regla_a_gemelo=v_a, regla_b_d33=regla_b_d33(v_a, abs(sd - sk)),
                                 discordantes=lista_p2(contrib, TKD, R),
                                 noches_con_error_K=len(noches["control"]), noches_con_error_D=len(noches["brazo"]))
    info["estrato_203"] = estrato_203(TKD, prot, R, lect, cfg, excluir)
    # ---- M
    pares = collections.defaultdict(list)
    salen = collections.Counter()
    for k, v in TKD.items():
        if len(v) != 2:
            continue
        c, b = v["control"], v["brazo"]
        if c["lab"] != "pos" or not c["vrp_ref"] or (excluir and es_snpp(k, c, prot)):
            continue
        if c["pub"] != b["pub"]:
            salen["K publica, D no" if c["pub"] else "D publica, K no"] += 1
            continue
        if not (c["pub"] and (c["disp"] or 0) > 0 and (b["disp"] or 0) > 0):
            continue
        nom, modo = estrato(k, c.get("z"))
        pares[nom].append({"k": c["disp"], "d": b["disp"], "m": c["vrp_ref"], "clave": k,
                           "bloque": "%s|%s" % (k.split("|")[0], k.split("|")[2][:10])})
    info["M_salen"] = dict(salen)
    ver_m, info_m = evaluar_m(pares, ok_ctrl, modo_calib)
    ver.update(ver_m)
    info.update(info_m)
    # M por volcán y Chillán aparte (informa)
    por_vol = collections.defaultdict(list)
    for nom, P in pares.items():
        for p in P:
            por_vol["%s|%s" % (p["clave"].split("|")[0], p["clave"].split("|")[1])].append(p)
    info["M_por_volcan"] = {kv: {"n": len(P), "razon_K": float(np.median([p["k"] / p["m"] for p in P])),
                                 "razon_D": float(np.median([p["d"] / p["m"] for p in P]))} for kv, P in sorted(por_vol.items())}
    return ver, info


def global_ventana(ver, ok_ctrl):
    """§8 d, una ventana. Devuelve (estado, mejora_en_algún_estrato_que_decide, empeora).

    S159, D-28 §2.5 (ADENDA_PLACEBO.md, sellada el 2026-10-21): la compuerta del placebo se retiró; ningún placebo
    vuelve INVALIDO el veredicto. El placebo actúa dentro de M como comparador (decidir_estrato)."""
    if not ok_ctrl:
        return "INDECIDIBLE", False, False
    p1 = [ver["P1|%s" % s] for s in SENS]
    p2 = [ver["P2|%s" % s] for s in SENS]
    m = {nom: ver["M|%s" % nom] for nom, modo in ESTRATOS if modo != "informa"}
    if "VETADO" in p1:
        return "NO CUMPLE (veto)", False, False
    if "PIERDE" in p2:                 # verificador H2: un M INDECIDIBLE no esconde una suma perdida
        return "NO CUMPLE (suma de errores)", False, False
    if "INDECIDIBLE" in p1 + p2 + list(m.values()):
        return "INDECIDIBLE", False, False
    if "PENDIENTE DE REPETICION" in p1:
        return "PENDIENTE DE REPETICION", False, False
    mejora = any(v == "MEJORA" for v in m.values())
    empeora = any(v == "EMPEORA" for v in m.values())
    if mejora and empeora:
        estado = "DECIDE NICOLAS (M mejora en un estrato y empeora en otro)"
    elif empeora:
        # §8 d no tiene fila para «M empeora sin mejora»; el sello §8 a dice que un EMPEORA bloquea CUMPLE, no que sea
        # NO CUMPLE. Sin regla escrita, decide Nicolás (verificador H6).
        estado = "DECIDE NICOLAS (M empeora, sin mejora)"
    elif mejora:
        estado = "MEJORA"
    else:
        estado = "SIN EFECTO"
    # D-34 §5.5 (ADENDA_GEMELO.md): un P2 con neto en contra de D que no alcanza PIERDE bloquea CUMPLE, igual que un
    # EMPEORA en un estrato que sólo bloquea. Desde aquí el tercer valor devuelto quiere decir «bloquea CUMPLE» (M
    # EMPEORA o P2 BLOQUEA), y combinar lo trata así.
    bloq = [s for s in SENS if ver["P2|%s" % s] == "BLOQUEA"]
    if bloq:
        estado = ("DECIDE NICOLAS (P2 con neto en contra de D sin llegar a PIERDE en %s: bloquea CUMPLE, "
                  "ADENDA_GEMELO.md D-34) | M: %s" % (", ".join(bloq), estado))
        empeora = True
    if any(ver["P1b|%s" % s].startswith("LISTA") for s in SENS):
        estado += " | P1b: protegidas que cruzan 1 MW hacia abajo, decide Nicolas"
    return estado, mejora, empeora


def validez_calibracion(calibracion):
    """D-30, respuesta 4 (ADENDA_PLACEBO.md §5): con --calibracion sellada (el §5 original, anterior a D-27) el
    comparador de D-28 no se aplica y ese modo aprobaría un placebo, así que su veredicto no vale para decidir. El JSON
    lo dice en `vale_para_decidir`, y combinar lo arrastra (verificador con contexto limpio, pregunta 5.4)."""
    if calibracion == "simetrica":
        return {"vale_para_decidir": True, "motivo_validez": "calibración simétrica (D-27) con el comparador (D-28)"}
    return {"vale_para_decidir": False,
            "motivo_validez": "NO VALE PARA DECIDIR: calibración %s, anterior a D-27, sin el comparador de D-28; "
                              "sólo para reproducir lo medido antes del sello" % calibracion}


def peor(estados):
    return min(estados, key=lambda e: next((i for i, o in enumerate(ORDEN) if e.startswith(o)), 3))


# ---------------------------------------------------------------- evaluación de una ventana
def evaluar(a):
    cfg = dict(VENTANAS[a.ventana])
    for c in ("desde", "hasta"):
        if getattr(a, c):
            cfg[c] = getattr(a, c)
    if a.ref:
        cfg["ref"] = Path(a.ref)
    if a.brazos:
        cfg["brazos"] = tuple(a.brazos.split(","))
    vols = a.vols.split(",") if a.vols else list(bp.VOLS)
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / ("_tmp_" + a.ventana)
    tmp.mkdir(parents=True, exist_ok=True)
    brazos = cfg["brazos"]
    raiz = fusionar(a.raiz, tmp, brazos, vols)
    faltan = [(n, v) for n in brazos for v in vols if not (raiz / BRAZOS[n] / (v + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos o volcanes: %s. No se evalúa a medias." % faltan[:20])
    res = {"ventana": a.ventana, "desde": cfg["desde"], "hasta": cfg["hasta"], "brazos": list(brazos)}
    excl = DIAS_EXCLUIDOS.get(a.ventana, ())
    res["dias_excluidos"] = list(excl)
    if excl:
        print("== EVALUADO SIN %s (D-29: CMR no sirvió esos días; fuera en los tres brazos y en la cobertura)"
              % ", ".join(excl))
    res["sha256_index_html"] = hashlib.sha256((RAIZ / "frontend" / "index.html").read_bytes()).hexdigest()
    print("== VENTANA %s: %s a %s | volcanes %d | brazos %s | %s | predicado sha256 %s" % (
        a.ventana, cfg["desde"], cfg["hasta"], len(vols), brazos,
        "decide la tabla sola" if cfg["solo_tabla"] else "decide tabla y OCR", res["sha256_index_html"]))
    print("   volcanes con kernel local en VIIRS 375 (volcanoes.yaml):", sorted(KERNEL))
    print("   calibración de M: %s" % ("sellada (§5 original: signo de log D/K al azar, falsos MEJORA o EMPEORA <= 5 %%;"
          " reemplazada por el sello D-27, sólo para reproducir)" if a.calibracion == "sellada" else
          "simétrica con opción A (ADENDA_CALIBRACION.md l. 3 a 8, sello D-27 de Nicolás, vigente)"))
    print("   comparador de M (ADENDA_PLACEBO.md, sello D-28): %s; placebo K x %s informado sin comparador" % (
        "MEJORA sólo si d y d′ (D contra K×ĝ) dan MEJORA, EMPEORA sobre d" if a.calibracion == "simetrica" else
        "no se aplica con la calibración sellada (D-28 se escribió sobre D-27)",
        " y K x ".join(str(g) for g in PLACEBO_GANANCIAS)))
    res["calibracion"] = a.calibracion
    res.update(validez_calibracion(a.calibracion))
    res["placebo"] = {"ganancias_informadas": list(PLACEBO_GANANCIAS), "comparador": a.calibracion == "simetrica"}
    ref = E.archivos_ref(cfg, tmp)
    res["referencia_ok"] = E.referencia_congelada(cfg["ref"], ref[2], False)
    pares = [("K", n) for n in brazos if n != "K"]
    T = {p: E.tabla(raiz / BRAZOS[p[0]], raiz / BRAZOS[p[1]], ref, cfg["desde"], cfg["hasta"], tmp / ("t_%s_%s.json" % p))
         for p in pares}
    T = {p: {k: v for k, v in filtrar_dias(t, excl).items() if k.split("|")[1] in SENS} for p, t in T.items()}
    R, n_modis = {}, {}
    for n in brazos:
        R[n], n_modis[n] = crudos(raiz, n, vols, cfg["desde"], cfg["hasta"])
        R[n] = filtrar_dias(R[n], excl)
    todas = set().union(*[set(t) for t in T.values()])
    prot = E.proteccion(todas, ref, cfg["desde"], cfg["hasta"])

    # ---- 1. cobertura (sólo VIIRS)
    print("\n== 1. COBERTURA (A108), sólo VIIRS 375 y 750")
    claves_ = {n: set(R[n]) for n in brazos}
    mal = []
    for n in brazos:
        d1, d2 = claves_["K"] - claves_[n], claves_[n] - claves_["K"]
        if d1 or d2:
            mal.append("%s: le faltan %d de K y tiene %d que K no" % (n, len(d1), len(d2)))
    protegidas = sorted(k for k in todas if prot[k]["A"])
    sin_rec = {k: [n for n in brazos if k not in claves_[n]] for k in protegidas}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    cob = {vs: filtrar_dias(ks, excl) for vs, ks in
           claves_cobertura(a.cobertura, vols, cfg["desde"], cfg["hasta"]).items()}
    cortos = []
    for (v, s), ks in sorted(cob.items()):
        falta = {k for k in ks if k not in claves_["K"]}
        if len(falta) > MAX_FALTA_COBERTURA * len(ks):
            cortos.append("%s %s: faltan %d de %d" % (v, s, len(falta), len(ks)))
    for x in mal + ["protegidas sin record en algún brazo: %s" % sin_rec] * bool(sin_rec) + cortos:
        print("   " + x)
    res["cobertura_ok"] = not (mal or sin_rec or cortos)
    print("   " + ("cobertura pareja: OK" if res["cobertura_ok"] else "COBERTURA DESPAREJA O CORTA: INDECIDIBLE"))

    # ---- 2. versión de producto
    mezcla = [k for k in protegidas if len({R[n][k]["pv"] for n in brazos if k in R[n]}) > 1]
    res["version_ok"] = not mezcla
    print("\n== 2. VERSIÓN DEL PRODUCTO: protegidas con versión distinta entre brazos %d %s" % (len(mezcla), mezcla[:5]))

    # ---- 3. cableado
    print("\n== 3. CABLEADO (línea FLAGS_BRAZO de cada job y huella en los records)")
    cable = {}
    for n in brazos:
        prob = [] if a.logs else ["sin --logs: no hay con qué probar el cableado"]
        for v in vols:
            for d, fl in flags_leidos(a.logs, n, v):
                if fl is None:
                    prob.append("%s (%s): sin línea FLAGS_BRAZO" % (v, d)); continue
                if fl.get("PROFILE_NAME") != BRAZOS[n] or fl.get("DATA_SUBDIR") != BRAZOS[n]:
                    prob.append("%s: perfil o directorio %s" % (v, fl.get("PROFILE_NAME")))
                for c, val in DECLARADO[n].items():
                    if fl.get(c) != val:
                        prob.append("%s: %s=%s, declarado %s" % (v, c, fl.get(c), val))
        if any(x["t1"] for x in R[n].values()):
            prob.append("records con triggered_test1 (huella de C0)")
        if n_modis[n]:
            prob.append("%d records MODIS (el brazo declara MODIS apagado)" % n_modis[n])
        con_pc = [x for x in R[n].values() if x["con_pc"]]
        huella = sum(x["huella_d25"] for x in con_pc)
        if DECLARADO[n]["ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375"]:
            if con_pc and huella < len(con_pc):
                prob.append("huella de D25 en %d de %d records con cúmulo" % (huella, len(con_pc)))
        elif huella:
            prob.append("%d records con huella de D25 en un brazo sin D25" % huella)
        cable[n] = prob
        print("   %-2s %s" % (n, "OK" if not prob else "ROTO: " + "; ".join(prob[:4]) + (" (y %d más)" % (len(prob) - 4) if len(prob) > 4 else "")))
    res["cableado"] = {n: not p for n, p in cable.items()}

    # ---- 4. determinismo (K' contra K)
    print("\n== 4. DETERMINISMO DE LA PUBLICACIÓN (K' contra K)")
    det_ok = True
    if ("K", "G") in T:
        for s in SENS:
            amb = [v for k, v in T[("K", "G")].items() if k.split("|")[1] == s and len(v) == 2]
            igual = sum(v["control"]["pub"] == v["brazo"]["pub"] for v in amb)
            ok = bool(amb) and igual / len(amb) >= UMBRAL_DETERMINISMO
            det_ok &= ok
            print("   %-8s %5d pasadas, misma decisión %5d | %s" % (s, len(amb), igual, "OK" if ok else "FALLA"))
    else:
        print("   sin gemelo en esta ventana (las pérdidas se confirman repitiendo el job)")
    res["determinismo_ok"] = det_ok
    res["controles_ok"] = res["cobertura_ok"] and res["version_ok"] and det_ok and res["referencia_ok"]
    print("\n== CONTROLES GENERALES:", "OK" if res["controles_ok"] else "FALLAN: ningún veredicto decide")

    # ---- reglas de etiquetas: original y SN (D-9), manda la más estricta
    ruido_de = json.load(open(a.ruido_de, encoding="utf-8"))["ruido_frac"] if a.ruido_de else None
    # repetición dirigida de los jobs de K y D (verificador H7; F/K §5): resuelve las pérdidas PENDIENTES de V2
    T_rep = None
    if a.repeticion:
        rr = Path(a.repeticion)
        T_rep = E.tabla(rr / BRAZOS["K"], rr / BRAZOS["D"], ref, cfg["desde"], cfg["hasta"], tmp / "rep_K_D.json")
        print("   repetición leída de %s: %d pasadas" % (rr, len(T_rep)))
    base = E.etiquetas_regla(sorted(todas), ref, cfg["desde"], cfg["hasta"], "original")
    tabla_lab = {k: x["lab"] for t in T.values() for k, v in t.items() for x in v.values()}
    res["por_regla"], res["ruido_frac"] = {}, {}
    inner = bp.inner_desde_html()
    for regla, modo, umbral in (("original", "original", None), ("SN", "SN", cm.UMBRAL_MINIMA_MW)):
        labs = base if modo == "original" else E.etiquetas_regla(sorted(todas), ref, cfg["desde"], cfg["hasta"], modo, umbral)
        nuevo = {k: (labs[k] if labs[k] != base[k] else tabla_lab.get(k, base[k])) for k in todas}
        Tx = {p: {k: {lado: dict(x, lab=nuevo[k]) for lado, x in v.items()} for k, v in t.items()} for p, t in T.items()}
        ver, info = contar(Tx, prot, R, cfg, regla, res, ruido_de, inner, a.calibracion, T_rep)
        estado, mejora, empeora = global_ventana(ver, res["controles_ok"] and all(res["cableado"].values()))
        res["por_regla"][regla] = {"veredicto": ver, "info": info, "estado": estado, "mejora": mejora, "empeora": empeora}
        res["ruido_frac"][regla] = info.get("ruido_frac", {})
        imprimir(regla, ver, info, estado)
    res["estado"] = peor([res["por_regla"][r]["estado"] for r in res["por_regla"]])
    res["mejora"] = all(res["por_regla"][r]["mejora"] for r in res["por_regla"])
    res["empeora"] = any(res["por_regla"][r]["empeora"] for r in res["por_regla"])
    i_sn = res["por_regla"]["SN"]["info"]
    if "D" in brazos and i_sn["M_pares"] and not i_sn["M_pares_con_magnitud_distinta"]:
        res["estado"] += " | ATENCIÓN: D25 no cambió ninguna magnitud (la huella sólo prueba que el flag se leyó, H8)"

    # ---- P4 y P5 (informan; los cuenta sobre los records crudos de K y D)
    print("\n== P4 Y P5 (informan)")
    mov, etq, d9, sp, desc, filtro = [], [], collections.Counter(), collections.Counter(), [], collections.Counter()
    for k, v in T[("K", "D")].items():
        if len(v) != 2:
            continue
        c, b = v["control"], v["brazo"]
        if c["pub"] and b["pub"] and None not in (c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"]) and \
                ev._hav(c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"]) > MOV_KM:
            mov.append(k)
        rk, rd = R["K"].get(k), R["D"].get(k)
        if rk and rd:
            if rk["dc"] != rd["dc"]:
                etq.append("%s %s->%s" % (k, rk["dc"], rd["dc"]))
            d9[(rk["d9"], rd["d9"])] += 1
            sp[(rk["un_pixel"], rd["un_pixel"])] += 1
            if rk["descartado"] != rd["descartado"]:
                desc.append(k)
            for lado, rr, x in (("K", rk, c), ("D", rd, b)):
                if (rr["pc_vrp"] or 0) > 0 and rr["dc"] == "summit" and rr["pc_dist"] is not None \
                        and rr["pc_dist"] <= inner[k.split("|")[0]] and not x["pub"]:
                    filtro[lado] += 1
    mov_prot = [k for k in mov if prot[k]["A"]]
    res["P4"] = {"movidas": len(mov), "movidas_protegidas": mov_prot, "cambia_distance_class": etq}
    res["P5"] = {"d9_capped_K_D": {"%s->%s" % k: n for k, n in d9.items()},
                 "modo_un_pixel_K_D": {"%s->%s" % k: n for k, n in sp.items()},
                 "discarded_reason_cambia": desc, "apagadas_por_filtro_del_tablero": dict(filtro)}
    print("   P4: cúmulos movidos más de %.2f km %d (protegidas %d: %s) | cambia distance_class %d %s" % (
        MOV_KM, len(mov), len(mov_prot), mov_prot[:5], len(etq), etq[:5]))
    print("   P5:", json.dumps(res["P5"], ensure_ascii=False)[:600])
    if mov_prot:
        res["estado"] += " | auditoría espacial A61 pendiente (P4)"
    if not res["vale_para_decidir"]:
        res["estado"] += " | " + res["motivo_validez"]
    sg = sin_geometria(todas, ref, cfg["desde"], cfg["hasta"])
    res["sin_geometria"] = {k: {"MIROVA": m, "K": T[("K", "D")][k]["control"]["disp"], "D": T[("K", "D")][k]["brazo"]["disp"]}
                            for k, m in sorted(sg.items()) if len(T[("K", "D")].get(k, {})) == 2}
    print("   alertas sin geometría (informan, no deciden): %d" % len(res["sin_geometria"]))
    print("\n== VEREDICTO DE LA VENTANA %s (manda la regla más estricta de original y SN): %s" % (a.ventana, res["estado"]))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


def imprimir(regla, ver, info, estado):
    print("\n== REGLA DE ALERTAS MÍNIMAS: %s" % regla)
    for s in SENS:
        i1, i2 = info["P1|%s" % s], info["P2|%s" % s]
        print("   P1 %-8s %s | protegidas que K publica %d, netas %d, ruidosas %d, pendientes %d, sólo OCR Suomi NPP %d" % (
            s, ver["P1|%s" % s], i1["protegidas_que_K_publica"], len(i1["netas"]), len(i1["ruidosas"]),
            len(i1["pendientes"]), len(i1["solo_ocr_snpp"])))
        for x in i1["netas"] + i1["ruidosas"] + i1["pendientes"]:
            print("      perdida: %s" % x)
        print("   P1b %-8s %s %s" % (s, ver["P1b|%s" % s], i1["cruces_1MW"][:5]))
        print("   P2 %-8s %s (D-34) | neto D menos K %+d, IC95 %s | discordantes %d en %d noches | suma K %d, D %d | "
              "noches con error K %d, D %d" % (
                  s, ver["P2|%s" % s], i2["neto"], i2["ic95"], i2["n_discordantes"], i2["noches_discordantes"],
                  i2["suma_K"], i2["suma_D"], i2["noches_con_error_K"], i2["noches_con_error_D"]))
        print("      calibración D-42: %s | sin calibrar %s | falsos GANA %s PIERDE %s (tope %.2f por cola), BLOQUEA %s "
              "(informa) | %s sorteos, semilla %s%s" % (
                  {True: "OK", False: "FALLA: INDECIDIBLE", None: "no corre"}[i2["calibrada"]], i2["resultado_sin_calibrar"],
                  i2["falsos_gana"], i2["falsos_pierde"], i2["tope_por_cola"], i2["falsos_bloquea"], i2["n_sorteos"],
                  i2["semilla_calibracion"], (" | " + i2["nota_calibracion"]) if i2["nota_calibracion"] else ""))
        print("      informan, no deciden: (a) ruido del gemelo %.1f -> %s | (b) D-33 -> %s" % (
            i2["ruido_gemelo"], i2["regla_a_gemelo"], i2["regla_b_d33"]))
        for x in i2["discordantes"]:
            print("      discordante: %s %s %s | K %s D %s | %s VRP %s | pc.vrp_mw K %s D %s | error de %s" % (
                x["volcan"], x["sensor"], x["hora"], x["publica_K"], x["publica_D"], x["clase_mirova"],
                x["vrp_mirova"], x["pc_vrp_mw_K"], x["pc_vrp_mw_D"], x["error_de"]))
    e203 = info["estrato_203"]
    print("   estrato 203 (VIIRS 750, cumbre de K en 0,0 MW; informa, no decide): %d pasadas | D recupera %d, enciende %d, "
          "no cambia %d, otros cambios %d" % (e203["n"], e203["recupera_D"], e203["enciende_D"], e203["no_cambia"],
                                              e203["otros_cambios"]))
    for x in e203["pasadas"]:
        print("      203: %s %s | %s VRP %s | publica K %s D %s | pc.vrp_mw K %s D %s | error de P2 %s" % (
            x["volcan"], x["hora"], x["clase_mirova"], x["vrp_mirova"], x["publica_K"], x["publica_D"],
            x["pc_vrp_mw_K"], x["pc_vrp_mw_D"], x["error_p2_de"]))
    print("   M (pares que salen: %s)" % info["M_salen"])
    for nom, modo in ESTRATOS:
        x = info["M|%s" % nom]
        if "regla" not in x:
            print("      %-26s %-8s n %d noches %d -> %s" % (nom, modo, x["n"], x["noches"], ver["M|%s" % nom]))
        else:
            print("      %-26s %-8s n %3d noches %3d | razón K %.3f D %.3f | d %+.3f [%+.3f, %+.3f] | nulo MEJORA %.3f EMPEORA %.3f %s | poder %s -> %s" % (
                nom, modo, x["n"], x["noches"], x["razon_K"], x["razon_D"], x["d_mediana"], x["ic95"][0], x["ic95"][1],
                x["falsos_mejora"], x["falsos_empeora"], "OK" if x["calibrada"] else "MAL CALIBRADA", x["poder"], ver["M|%s" % nom]))
            print("         volcanes con d negativa %d de %d con 3 pares o más %s" % (
                x["volcanes_con_d_negativa"], x["volcanes_con_3_pares"], ("| " + x["nota"]) if x["nota"] else ""))
            if "regla_dprima" in x:
                print("         comparador D-28: ĝ x%.3f [x%.3f, x%.3f] | d′ %+.3f [%+.3f, %+.3f] | nulo de d′ MEJORA %.3f EMPEORA %.3f %s | volcanes con d′ negativa %d de %d -> d′ %s" % (
                    x["g_hat_factor"], 10 ** x["g_hat_ic95"][0], 10 ** x["g_hat_ic95"][1], x["dprima_mediana"],
                    x["ic95_dprima"][0], x["ic95_dprima"][1], x["falsos_mejora_dprima"], x["falsos_empeora_dprima"],
                    "OK" if x["calibrada_dprima"] else "MAL CALIBRADA", x["volcanes_con_dprima_negativa"],
                    x["volcanes_con_3_pares_dprima"], x["regla_dprima"]))
                print("         ĝ por volcán (informa, no decide): %s" % ", ".join(
                    "%s x%.3f (n %d)" % (v, g["factor"], g["n"]) for v, g in x["g_hat_por_volcan"].items()))
    print("   pares de M con magnitud distinta entre K y D: %d de %d" % (info["M_pares_con_magnitud_distinta"], info["M_pares"]))
    print("   placebo de M sin comparador (D-28 §2.5, informa, no invalida):")
    for nom, rs in info.get("M_placebo", {}).items():
        print("      %-26s %s" % (nom, ", ".join("K x %s -> %s" % (g, r) for g, r in rs.items())))
    for kv, x in info["M_por_volcan"].items():
        if kv.startswith("NevadosDeChillan|"):
            print("      Chillán %-10s n %d razón K %.3f D %.3f (informa)" % (kv.split("|")[1], x["n"], x["razon_K"], x["razon_D"]))
    print("   estado con la regla %s: %s" % (regla, estado))


def combinar(archivos):
    """§8 d: CUMPLE sólo si ninguna ventana veta ni pierde la suma, M mejora en al menos un estrato que decide EN CADA
    ventana y no empeora en ninguna (H9). Lo demás: el peor estado, o decide Nicolás."""
    rs = [json.load(open(f, encoding="utf-8")) for f in archivos]
    estados = [(r["ventana"], r["estado"]) for r in rs]
    malo = [e for v, e in estados if e.startswith(("INVALIDO", "NO CUMPLE", "INDECIDIBLE", "PENDIENTE"))]
    if malo:
        final = peor(malo)
    elif any(r["empeora"] for r in rs):
        final = "DECIDE NICOLAS (M empeora o P2 bloquea en alguna ventana)"   # D-34 §5.5
    elif all(r["mejora"] for r in rs):
        final = "CUMPLE"
    elif any(r["mejora"] for r in rs):
        final = "DECIDE NICOLAS (M mejora en una sola ventana)"
    else:
        final = "SIN EFECTO (decide Nicolas)"
    if any("P1b" in e for v, e in estados):
        final = ("DECIDE NICOLAS (P1b: protegidas que cruzan 1 MW)" if final == "CUMPLE"
                 else final + " | P1b: protegidas que cruzan 1 MW, decide Nicolas")
    if any("A61" in e for v, e in estados):
        final += " | auditoría espacial A61 pendiente"
    if any(r.get("vale_para_decidir") is False for r in rs):
        final += " | NO VALE PARA DECIDIR: alguna ventana se evaluó con la calibración sellada (D-30)"
    excl = sorted({d for r in rs for d in r.get("dias_excluidos", [])})
    if excl:   # D-29: «declarados en el veredicto», en su primera línea
        final = "EVALUADO SIN %s (D-29) | %s" % (", ".join(excl), final)
    print("== VEREDICTO COMBINADO: %s | por ventana %s" % (final, estados))
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combinar", nargs="+")
    ap.add_argument("--ventana", choices=sorted(VENTANAS))
    ap.add_argument("--raiz", action="append", default=[])
    ap.add_argument("--logs", action="append", default=[])
    ap.add_argument("--out")
    ap.add_argument("--tmp")
    ap.add_argument("--ruido-de", dest="ruido_de")
    ap.add_argument("--calibracion", choices=("sellada", "simetrica"), default=CALIB_MODO,
                    help="calibración de M: 'sellada' es el §5; 'simetrica' es la adenda propuesta (ver CALIB_MODO)")
    ap.add_argument("--repeticion", help="directorio con los jobs repetidos de K y D (resuelve las pérdidas pendientes)")
    ap.add_argument("--cobertura", nargs=2, default=[str(RAIZ / "data" / "_s154_reproc_k_historico"),
                                                     str(RAIZ / "data" / "mirova_equivalent")],
                    help="histórico con K y producción (referencia de cobertura)")
    # sólo para la prueba del evaluador: no cambian ninguna regla
    ap.add_argument("--vols"); ap.add_argument("--desde"); ap.add_argument("--hasta"); ap.add_argument("--ref")
    ap.add_argument("--brazos")
    a = ap.parse_args()
    if a.combinar:
        combinar(a.combinar)
        return 0
    if not (a.ventana and a.raiz and a.out):
        ap.error("--ventana, --raiz y --out son obligatorios")
    return evaluar(a)


if __name__ == "__main__":
    sys.exit(main())
