# -*- coding: utf-8 -*-
"""Evaluador pre-registrado de la zona A del laboratorio (MEJ-5), S194, paso 2 del plan S190.

ESCRITO ANTES DE TENER DATOS DEL LABORATORIO. El criterio que aplica está sellado en
`experiments/_s194_lab_zona_a/PREREGISTRO.md` (valores de Nicolás, D5 del 2026-11-17). Este archivo no se edita
después del sello sin un pre-registro nuevo: la prueba `tests/test_lab_zona_a_preregistro_s194.py` compara su
sha256 (con fin de línea normalizado) con el que declara el pre-registro.

POR QUÉ existe. La zona A baja la línea de detección de MIROVA sólo dentro del cráter (círculo de `inner_radius_km`).
Lo que aparezca de más no se puede juzgar contra MIROVA (A115: todo lo nuevo contaría como falso positivo). Se juzga
contra NHI (SWIR de Sentinel 2 y Landsat, repo NHI-v1) y contra la persistencia, con el nulo medido (S131: en 4 de 5
volcanes la tasa de alerta NHI en noches con detección propia fue igual a la basal, 20 a 49 %).

QUÉ HACE, en cuatro piezas que son funciones puras (las prueba el archivo de pruebas con datos sintéticos):
  1. `clasificar_noches`: cada noche de volcán (fecha UTC de las pasadas nocturnas) en S (sólo laboratorio publica),
     N (ninguno), A (ambos), P (sólo producción), con «publica» = predicado del tablero ejecutado con node
     (`banco_paridad.correr_node`, nunca portado). Una noche con distinta cobertura entre perfiles no entra.
  2. `parear_nhi` y `prueba_permutacion`: cada escena NHI a una noche (D, después D+1, después D-1), y la diferencia
     de tasa de alerta NHI entre S y N con permutación dentro del volcán, estratificada por nubosidad de la escena.
  3. `control_desplazado`: lo mismo con las fechas NHI corridas +15 y -15 días; tiene que dar nulo.
  4. `persistencia`: fracción de detecciones extra a <= 1 km de una detección del laboratorio de las 3 noches previas,
     contra posiciones sorteadas al azar dentro de la zona A.
Y `elegir_valor`, la regla del paso 3 para elegir el multiplicador de sigma de la zona A sobre negativos limpios.

Uso (cuando existan los datos del paso 4; hoy sale con error a propósito si falta la carpeta del laboratorio):
  python experiments/_s194_lab_zona_a/evaluar.py evaluar --lab data/laboratorio_v1 --nhi-dir <carpeta> --out r.json
  python experiments/_s194_lab_zona_a/evaluar.py calibrar --barrido 5.0=<dir> --barrido 4.5=<dir> ... --out c.json
  python experiments/_s194_lab_zona_a/evaluar.py poder        (tabla de exceso mínimo detectable, sin datos)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

# ------------------------------------------------------------------------------------------------ valores sellados
# D5 (Nicolás, 2026-11-17): 30 %, 4 de 9, p < 0,05, control de 15 días, SIN PODER bajo 10. El resto son las
# definiciones operables del PREREGISTRO.md, fijadas en el mismo commit.
VENTANA_INICIO = "2026-02-15"              # medición contra NHI (plan S190 §6, «Ventana»)
VENTANA_CALIBRACION_INICIO = "2026-03-01"  # calibración sobre negativos limpios: A119, la tabla de MIROVA sana desde marzo
VOLCANES_NHI = ("Lascar", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima",
                "Villarrica", "Copahue", "Chaiten")               # los 9 con serie NHI, sin Cordón Caulle
VOLCANES_FUERA = ("PuyehueCordonCaulle",)                          # D6
VOLCANES_ZONA_A = VOLCANES_NHI + ("Lastarria",)                    # calibración y persistencia (no necesitan NHI)
NOMBRE_NHI = {"PlanchonPeteroa": "Planchon-Peteroa", "NevadosDeChillan": "Nevados de Chillan",
              "PuyehueCordonCaulle": "Puyehue - Cordon Caulle"}
ALFA = 0.05
MIN_VOLCANES_CUMPLE = 4
N_MIN_NOCHES = 10              # por grupo (S y N) y por volcán; bajo esto el volcán no vota (SIN PODER)
N_PERMUTACIONES = 10000
SEMILLA = 194
ORDEN_PAREO_DIAS = (0, 1, -1)  # la escena del día D se parea con la noche D; si no hay, D+1; si no, D-1
CORTES_NUBE = (20.0, 50.0)     # estratos de nubosidad de la escena NHI, en %: <=20, (20, 50], >50
DESPLAZAMIENTOS_CONTROL = (15, -15)
MAX_VOLCANES_SIG_CONTROL = 1   # el control es nulo si en cada desplazamiento a lo más 1 volcán da exceso con p < ALFA
TOL_PAREO_S = 120              # pareo de pasadas entre perfiles (clase_mirova.VENTANA_S)
MAX_FRAC_COBERTURA_DESIGUAL = 0.05
RADIO_PERSIST_KM = 1.0
NOCHES_PREVIAS = 3
N_SORTEOS_PERSIST = 2000
N_MIN_EXTRAS = 10
TASA_OBJETIVO = 0.30           # tasa de publicación por pasada en negativos limpios, zona A, cada sensor
GRILLA_S = (5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0)  # 5.0 = s2 nocturno de producción (control del barrido)
N_MIN_NEG_SENSOR = 30
SENSORES = ("MODIS", "VIIRS375", "VIIRS750")
# Unidad de la tasa objetivo. D5 aprobó «por pasada» y es la que rige. «noche» (noche de volcán, tres sensores juntos)
# queda implementada y probada pero APAGADA: es la alternativa de la pregunta 1 del PR para Nicolás (debilidad 1 del
# PREREGISTRO). Cambiar esta constante es un re-sello (nuevo sha256), antes de correr el barrido.
UNIDAD_TASA = "pasada"
CLAVES_UNIDAD = {"pasada": SENSORES, "noche": ("NOCHE",)}

CUMPLE, NO_CUMPLE, SIN_PODER, INVALIDO = "CUMPLE", "NO CUMPLE", "SIN PODER", "INVALIDO POR INSTRUMENTO"
CLASES = ("S", "N", "A", "P")


# ------------------------------------------------------------------------------------------------ 1. noches
def _noche(dt):
    return dt.strftime("%Y-%m-%d")


def _clave_pasada(p):
    return (p["sensor"], p["dt"])


def _parear_pasadas(lab, prod, tol_s=TOL_PAREO_S):
    """Empareja cada pasada del laboratorio con la de producción del mismo sensor a <= tol_s. Devuelve (pares,
    sin_par_lab, sin_par_prod)."""
    libres = list(prod)
    pares, solo_lab = [], []
    for a in sorted(lab, key=_clave_pasada):
        j = next((i for i, b in enumerate(libres) if b["sensor"] == a["sensor"]
                  and abs((b["dt"] - a["dt"]).total_seconds()) <= tol_s), None)
        if j is None:
            solo_lab.append(a)
        else:
            pares.append((a, libres.pop(j)))
    return pares, solo_lab, libres


def clasificar_noches(pasadas_lab, pasadas_prod):
    """{(vol, noche): {"clase": S|N|A|P|None, "cobertura_igual": bool, "pares": [(lab, prod)]}}.

    Cada pasada es {vol, sensor, dt, pub, invalida, lat, lon}. Cobertura igual: toda pasada de un perfil tiene par en
    el otro y la escena es inválida en los dos o en ninguno. Una noche sin ninguna pasada válida queda con clase None
    (no observada). Publica = alguna pasada válida con pub."""
    por = collections.defaultdict(lambda: ([], []))
    for p in pasadas_lab:
        por[(p["vol"], _noche(p["dt"]))][0].append(p)
    for p in pasadas_prod:
        por[(p["vol"], _noche(p["dt"]))][1].append(p)
    out = {}
    for k, (lab, prod) in por.items():
        pares, solo_lab, solo_prod = _parear_pasadas(lab, prod)
        igual = not solo_lab and not solo_prod and all(bool(a["invalida"]) == bool(b["invalida"]) for a, b in pares)
        validos = [(a, b) for a, b in pares if not a["invalida"] and not b["invalida"]]
        clase = None
        if igual and validos:
            pl = any(a["pub"] for a, _ in validos)
            pp = any(b["pub"] for _, b in validos)
            clase = "A" if (pl and pp) else "S" if pl else "P" if pp else "N"
        out[k] = {"clase": clase, "cobertura_igual": igual, "pares": validos}
    return out


# ------------------------------------------------------------------------------------------------ 2. NHI
def estrato_nube(cc):
    if cc is None:
        return 2   # sin dato de nubes: al estrato más nublado (no puede pasar por escena despejada)
    return 0 if cc <= CORTES_NUBE[0] else 1 if cc <= CORTES_NUBE[1] else 2


def parear_nhi(escenas, noches_vol, inicio=VENTANA_INICIO, fin=None, desplazamiento_dias=0):
    """Unidades de la prueba para un volcán: {noche: {"alerta": bool, "nube": float|None, "clase": S|N}}.

    `escenas`: filas de nhi_timeseries.json ({fecha, alerta, cloud_cover, sensor}). La escena (con su fecha corrida
    `desplazamiento_dias`, para el control) se parea con la primera noche de ORDEN_PAREO_DIAS que esté observada
    (clase no nula). Las clases A y P también consumen la escena, para que no salte a la noche vecina sólo porque la
    suya tuvo otra clase. Varias escenas en la misma noche: alerta = alguna; nube = la menor (la vista más limpia).
    Sólo entran a la prueba las noches de clase S o N. Filtros: fecha (ya corrida) dentro de la ventana, `alerta` no nula."""
    unidades = {}
    for e in escenas:
        if e.get("alerta") is None or not e.get("fecha"):
            continue
        d = date.fromisoformat(e["fecha"][:10]) + timedelta(days=desplazamiento_dias)
        if d.isoformat() < inicio or (fin is not None and d.isoformat() > fin):
            continue
        for k in ORDEN_PAREO_DIAS:
            n = (d + timedelta(days=k)).isoformat()
            info = noches_vol.get(n)
            if info is not None and info["clase"] is not None:
                if info["clase"] in ("S", "N"):
                    u = unidades.setdefault(n, {"alerta": False, "nube": None, "clase": info["clase"]})
                    u["alerta"] = u["alerta"] or bool(e["alerta"])
                    cc = e.get("cloud_cover")
                    if cc is not None and (u["nube"] is None or cc < u["nube"]):
                        u["nube"] = float(cc)
                break
    return unidades


def prueba_permutacion(unidades, n_perm=N_PERMUTACIONES, semilla=SEMILLA):
    """Exceso = tasa de alerta NHI en S menos en N; p de una cola (exceso positivo), permutando las etiquetas S/N
    dentro de cada estrato de nubosidad. p = (1 + #{T* >= T}) / (1 + n_perm)."""
    u = list(unidades.values())
    y = np.array([1.0 if x["alerta"] else 0.0 for x in u])
    g = np.array([x["clase"] == "S" for x in u])
    est = np.array([estrato_nube(x["nube"]) for x in u])
    n_s, n_n = int(g.sum()), int((~g).sum())
    res = {"n_S": n_s, "n_N": n_n, "alertas_S": int(y[g].sum()), "alertas_N": int(y[~g].sum()),
           "exceso": None, "p": None}
    if n_s == 0 or n_n == 0:
        return res
    obs = y[g].mean() - y[~g].mean()
    rng = np.random.default_rng(semilla)
    gp = np.empty((n_perm, len(u)), dtype=bool)
    for s in np.unique(est):
        idx = np.flatnonzero(est == s)
        orden = np.argsort(rng.random((n_perm, len(idx))), axis=1)
        gp[:, idx] = g[idx][orden]
    suma_s = (gp * y).sum(axis=1)
    t = suma_s / n_s - (y.sum() - suma_s) / n_n
    res["exceso"] = round(float(obs), 6)
    res["p"] = float((1 + np.sum(t >= obs - 1e-12)) / (1 + n_perm))
    return res


def voto_volcan(r):
    if r["n_S"] < N_MIN_NOCHES or r["n_N"] < N_MIN_NOCHES:
        return SIN_PODER
    return "exceso" if (r["exceso"] is not None and r["exceso"] > 0 and r["p"] < ALFA) else "sin exceso"


def medir_nhi(noches, nhi, volcanes=VOLCANES_NHI, fin=None, desplazamiento_dias=0, n_perm=N_PERMUTACIONES):
    out = {}
    for vol in volcanes:
        nv = {n: info for (v, n), info in noches.items() if v == vol}
        uni = parear_nhi(nhi.get(vol, []), nv, fin=fin, desplazamiento_dias=desplazamiento_dias)
        r = prueba_permutacion(uni, n_perm=n_perm)
        r["voto"] = voto_volcan(r)
        out[vol] = r
    return out


# ------------------------------------------------------------------------------------------------ 3. control
def control_desplazado(noches, nhi, fin=None, n_perm=N_PERMUTACIONES):
    """El mismo cálculo con las fechas NHI corridas. Nulo si en cada desplazamiento a lo más
    MAX_VOLCANES_SIG_CONTROL volcanes (con poder) dan exceso con p < ALFA."""
    out = {"desplazamientos": {}, "nulo": True}
    for dd in DESPLAZAMIENTOS_CONTROL:
        m = medir_nhi(noches, nhi, fin=fin, desplazamiento_dias=dd, n_perm=n_perm)
        n_sig = sum(r["voto"] == "exceso" for r in m.values())
        out["desplazamientos"][str(dd)] = {"n_volcanes_exceso": n_sig, "por_volcan": m}
        if n_sig > MAX_VOLCANES_SIG_CONTROL:
            out["nulo"] = False
    return out


# ------------------------------------------------------------------------------------------------ 4. persistencia
def _hav_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _detecciones(noches, volcanes):
    """(extras, publicadas_lab). Extra: pasada válida que el laboratorio publica y producción no, en una noche con
    cobertura igual. Publicadas del laboratorio: toda pasada válida del laboratorio con pub, por (vol, noche)."""
    extras, pub = [], collections.defaultdict(list)
    for (vol, n), info in noches.items():
        if vol not in volcanes or not info["cobertura_igual"]:
            continue
        for a, b in info["pares"]:
            if a["pub"] and a.get("lat") is not None:
                pub[(vol, n)].append((a["lat"], a["lon"]))
                if not b["pub"]:
                    extras.append({"vol": vol, "noche": n, "lat": a["lat"], "lon": a["lon"]})
    return extras, pub


def _previas(pub, vol, noche):
    d = date.fromisoformat(noche)
    pts = [pt for k in range(1, NOCHES_PREVIAS + 1) for pt in pub.get((vol, (d - timedelta(days=k)).isoformat()), [])]
    return np.array(pts, dtype=float).reshape(-1, 2)


def _sorteo_disco(rng, lat0, lon0, r_km, n):
    r = r_km * np.sqrt(rng.random(n))
    th = 2 * np.pi * rng.random(n)
    return lat0 + r * np.cos(th) / 111.32, lon0 + r * np.sin(th) / (111.32 * math.cos(math.radians(lat0)))


def persistencia(noches, anclas, volcanes=VOLCANES_ZONA_A, n_sorteos=N_SORTEOS_PERSIST, semilla=SEMILLA):
    """`anclas`: {vol: (lat, lon, inner_km)}. Fracción de extras a <= RADIO_PERSIST_KM de una detección publicada del
    laboratorio en las NOCHES_PREVIAS noches anteriores, contra la misma fracción con la posición de cada extra
    sorteada uniforme (por área) en el disco de la zona A de su volcán; las detecciones previas quedan reales.
    p = (1 + #{f* >= f}) / (1 + n_sorteos); supera si p < ALFA y hay al menos N_MIN_EXTRAS extras."""
    extras, pub = _detecciones(noches, volcanes)
    res = {"n_extras": len(extras), "frac_obs": None, "frac_sorteo_media": None, "p": None, "supera": False,
           "sin_poder": len(extras) < N_MIN_EXTRAS}
    if not extras:
        return res
    rng = np.random.default_rng(semilla)
    hits_obs, hits = 0, np.zeros(n_sorteos)
    for e in extras:
        pv = _previas(pub, e["vol"], e["noche"])
        lat0, lon0, rk = anclas[e["vol"]]
        la, lo = _sorteo_disco(rng, lat0, lon0, rk, n_sorteos)   # se sortea siempre: la secuencia no depende de pv
        if not len(pv):
            continue
        hits_obs += bool(np.min(_hav_km(e["lat"], e["lon"], pv[:, 0], pv[:, 1])) <= RADIO_PERSIST_KM)
        d = _hav_km(la[:, None], lo[:, None], pv[None, :, 0], pv[None, :, 1]).min(axis=1)
        hits += d <= RADIO_PERSIST_KM
    obs, sorteo = hits_obs / len(extras), hits / len(extras)
    p = float((1 + np.sum(sorteo >= obs - 1e-12)) / (1 + n_sorteos))
    res.update(frac_obs=round(obs, 6), frac_sorteo_media=round(float(sorteo.mean()), 6), p=p,
               supera=bool(p < ALFA and not res["sin_poder"]))
    return res


def persistencia_temporal(noches, volcanes=VOLCANES_ZONA_A, n_sorteos=N_SORTEOS_PERSIST, semilla=SEMILLA):
    """INFORMATIVA, no vota (PREREGISTRO, debilidad 5): cada extra toma la posición de una detección publicada del
    laboratorio del mismo volcán en otra noche lejana (|Δ| > NOCHES_PREVIAS + 3 días). Separa la recurrencia en el
    tiempo de la mera concentración espacial en un punto fijo (un píxel tibio de siempre también «persiste»)."""
    extras, pub = _detecciones(noches, volcanes)
    if not extras:
        return {"n_extras": 0, "frac_obs": None, "frac_sorteo_media": None, "p": None}
    pool = collections.defaultdict(list)
    for (vol, n), pts in pub.items():
        for pt in pts:
            pool[vol].append((date.fromisoformat(n), pt))
    rng = np.random.default_rng(semilla + 1)
    hits_obs, hits = 0, np.zeros(n_sorteos)
    for e in extras:
        pv = _previas(pub, e["vol"], e["noche"])
        d0 = date.fromisoformat(e["noche"])
        cand = np.array([pt for (d, pt) in pool[e["vol"]] if abs((d - d0).days) > NOCHES_PREVIAS + 3],
                        dtype=float).reshape(-1, 2)
        if not len(pv) or not len(cand):
            continue
        hits_obs += bool(np.min(_hav_km(e["lat"], e["lon"], pv[:, 0], pv[:, 1])) <= RADIO_PERSIST_KM)
        hit_c = _hav_km(cand[:, None, 0], cand[:, None, 1], pv[None, :, 0], pv[None, :, 1]).min(axis=1) <= RADIO_PERSIST_KM
        hits += hit_c[rng.integers(len(cand), size=n_sorteos)]
    obs, sorteo = hits_obs / len(extras), hits / len(extras)
    return {"n_extras": len(extras), "frac_obs": round(obs, 6), "frac_sorteo_media": round(float(sorteo.mean()), 6),
            "p": float((1 + np.sum(sorteo >= obs - 1e-12)) / (1 + n_sorteos))}


# ------------------------------------------------------------------------------------------------ veredicto
def veredicto(noches, nhi, anclas, fin=None, n_perm=N_PERMUTACIONES, n_sorteos=N_SORTEOS_PERSIST):
    """Orden: instrumento (cobertura), control, poder, exceso y persistencia."""
    cob = {}
    for vol in VOLCANES_ZONA_A:
        ks = [info for (v, _), info in noches.items() if v == vol]
        des = sum(not i["cobertura_igual"] for i in ks)
        cob[vol] = {"noches": len(ks), "desiguales": des, "frac": round(des / len(ks), 6) if ks else None}
    clases = {vol: dict(collections.Counter(i["clase"] for (v, _), i in noches.items() if v == vol))
              for vol in VOLCANES_ZONA_A}
    nhi_res = medir_nhi(noches, nhi, fin=fin, n_perm=n_perm)
    ctrl = control_desplazado(noches, nhi, fin=fin, n_perm=n_perm)
    pers = persistencia(noches, anclas, n_sorteos=n_sorteos)
    pers_t = persistencia_temporal(noches, n_sorteos=n_sorteos)
    con_poder = [v for v, r in nhi_res.items() if r["voto"] != SIN_PODER]
    con_exceso = [v for v, r in nhi_res.items() if r["voto"] == "exceso"]
    motivos = []
    if any(c["frac"] is not None and c["frac"] > MAX_FRAC_COBERTURA_DESIGUAL for c in cob.values()):
        v = INVALIDO
        motivos.append("cobertura desigual entre laboratorio y producción sobre %.0f %% de las noches en algún volcán"
                       % (100 * MAX_FRAC_COBERTURA_DESIGUAL))
    elif not ctrl["nulo"]:
        v = INVALIDO
        motivos.append("el control con fechas NHI corridas no dio nulo: el instrumento mide algo que no es la noche")
    elif len(con_poder) < MIN_VOLCANES_CUMPLE:
        v = SIN_PODER
        motivos.append("sólo %d volcanes con poder; hacen falta %d para poder cumplir" % (len(con_poder),
                                                                                     MIN_VOLCANES_CUMPLE))
    elif len(con_exceso) >= MIN_VOLCANES_CUMPLE and pers["supera"]:
        v = CUMPLE
    elif len(con_exceso) >= MIN_VOLCANES_CUMPLE and pers["sin_poder"]:
        v = SIN_PODER
        motivos.append("exceso NHI suficiente pero menos de %d detecciones extra para la persistencia" % N_MIN_EXTRAS)
    else:
        v = NO_CUMPLE
        if len(con_exceso) < MIN_VOLCANES_CUMPLE:
            motivos.append("exceso NHI con p < %.2f en %d volcanes (hacen falta %d)" % (ALFA, len(con_exceso),
                                                                                    MIN_VOLCANES_CUMPLE))
        if not pers["supera"]:
            motivos.append("la persistencia no supera al sorteo dentro de la zona A")
    return {"veredicto": v, "motivos": motivos, "volcanes_con_poder": con_poder, "volcanes_con_exceso": con_exceso,
            "nhi": nhi_res, "control": ctrl, "persistencia": pers, "persistencia_temporal_informativa": pers_t,
            "cobertura": cob, "clases_por_volcan": clases}


# ------------------------------------------------------------------------------------------------ calibración
def elegir_valor(tasas, unidad=None):
    """Regla del paso 3. `tasas`: {s: {clave: (n_pub, n_neg)}} con s en GRILLA_S y clave cada sensor (unidad pasada)
    o "NOCHE" (unidad noche), medidas con el predicado del tablero sobre negativos limpios (`tasas_barrido`) de
    VOLCANES_ZONA_A desde VENTANA_CALIBRACION_INICIO. Devuelve {"estado", "valor", "detalle"}: el menor s cuya tasa no
    supera TASA_OBJETIVO en ninguna clave de la unidad (por defecto UNIDAD_TASA)."""
    claves = CLAVES_UNIDAD[unidad or UNIDAD_TASA]
    falta = [s for s in GRILLA_S if s not in tasas]
    if falta:
        return {"estado": INVALIDO, "valor": None, "detalle": "faltan brazos del barrido: %s" % falta}
    for sen in claves:
        if any(tasas[s][sen][1] < N_MIN_NEG_SENSOR for s in GRILLA_S):
            return {"estado": SIN_PODER, "valor": None,
                    "detalle": "%s con menos de %d negativos limpios en algún brazo" % (sen, N_MIN_NEG_SENSOR)}
        r = [tasas[s][sen][0] / tasas[s][sen][1] for s in GRILLA_S]
        if any(r[i + 1] < r[i] for i in range(len(r) - 1)):
            return {"estado": INVALIDO, "valor": None,
                    "detalle": "%s: la tasa baja al bajar s (no monótona): %s" % (sen, [round(x, 4) for x in r])}

    def ok(s):   # entero, sin coma flotante: n_pub / n_neg <= 0,30  <=>  10 n_pub <= 3 n_neg
        return all(10 * tasas[s][sen][0] <= round(10 * TASA_OBJETIVO) * tasas[s][sen][1] for sen in claves)

    if not ok(GRILLA_S[0]):
        return {"estado": "SIN VALOR", "valor": None,
                "detalle": "producción (s = %.1f) ya supera la tasa objetivo en algún sensor" % GRILLA_S[0]}
    elegido = GRILLA_S[0]
    for s in GRILLA_S[1:]:
        if not ok(s):
            break
        elegido = s
    det = "menor s de la grilla que cumple" + (" (el piso de la grilla: el barrido no alcanzó la tasa objetivo)"
                                               if elegido == GRILLA_S[-1] else "")
    return {"estado": "ELEGIDO" if elegido != GRILLA_S[0] else "SIN EXTENSION", "valor": elegido, "detalle": det}


def control_barrido(tasas, tasas_prod):
    """El brazo s = GRILLA_S[0] (el s2 de producción) tiene que dar exactamente las cuentas de producción. Si no, la
    implementación de la zona A cambia algo más que el multiplicador (geometría, fondo, ancla: S147 §5) y el barrido
    no vale."""
    return tasas.get(GRILLA_S[0]) == tasas_prod


# ------------------------------------------------------------------------------------------------ poder (sin datos)
def p_hipergeometrica(k, n_s, n_n, a_n):
    """P(X >= k) con X ~ hipergeométrica: n_s+n_n noches, k+a_n alertas, n_s en S (permutación exacta sin estratos)."""
    tot, alt = n_s + n_n, k + a_n
    den = math.comb(tot, n_s)
    return sum(math.comb(alt, x) * math.comb(tot - alt, n_s - x) for x in range(k, min(alt, n_s) + 1)) / den


def minimo_detectable(n_s, n_n, p0):
    """Menor número de alertas NHI en S (de n_s) que da p < ALFA si N tiene la tasa basal p0."""
    a_n = round(p0 * n_n)
    for k in range(n_s + 1):
        if p_hipergeometrica(k, n_s, n_n, a_n) < ALFA:
            return k
    return None


def prob_al_menos(k, n, a):
    return sum(math.comb(n, i) * a ** i * (1 - a) ** (n - i) for i in range(k, n + 1))


# ------------------------------------------------------------------------------------------------ carga real
def _volcanes_yaml():
    import yaml
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        return {v["name"]: v for v in yaml.safe_load(fh)["volcanoes"]}


def anclas_reales():
    sys.path.insert(0, str(ROOT))
    from pipeline.geo_utils import get_detection_anchor
    vy = _volcanes_yaml()
    out = {}
    for vol in VOLCANES_ZONA_A:
        lat, lon = get_detection_anchor(vy[vol])
        out[vol] = (float(lat), float(lon), float(vy[vol]["inner_radius_km"]))
    return out


def cargar_pasadas(directorio, inicio, fin):
    """Pasadas nocturnas de los JSON por volcán con el predicado del tablero (node, banco_paridad)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    recs, casos = [], []
    for vol in VOLCANES_ZONA_A:
        ruta = Path(directorio) / ("%s.json" % vol)
        if not ruta.exists():
            raise FileNotFoundError("falta %s: sin datos del laboratorio no hay medición (paso 4)" % ruta)
        for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b is None or not (inicio <= t[:10] <= fin):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if bp.es_pasada_diurna_descartada(b, *coords[vol], dt):
                continue
            recs.append({"vol": vol, "sensor": r.get("sensor"), "dt": dt, "invalida": bp.es_escena_invalida(r),
                         "lat": r.get("final_hotspot_lat"), "lon": r.get("final_hotspot_lon")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["pub"] = bool(p[4])
    return recs


def cargar_nhi(directorio):
    """Lee <dir>/<Volcan>.json (copias de docs/nhi_data/<carpeta>/nhi_timeseries.json de NHI-v1)."""
    out = {}
    for vol in VOLCANES_NHI:
        ruta = Path(directorio) / ("%s.json" % vol)
        if not ruta.exists():
            raise FileNotFoundError("falta la serie NHI de %s (%s)" % (vol, ruta))
        out[vol] = [x for x in json.loads(ruta.read_text(encoding="utf-8")) if isinstance(x, dict)]
    return out


def bajar_nhi(directorio):
    """Baja las 9 series del remoto (raw.githubusercontent, rama main) a `directorio` (datos no confiables: sólo se
    leen como JSON)."""
    from urllib.parse import quote
    from urllib.request import urlopen
    Path(directorio).mkdir(parents=True, exist_ok=True)
    for vol in VOLCANES_NHI:
        url = ("https://raw.githubusercontent.com/MendozaVolcanic/NHI-v1/main/docs/nhi_data/%s/nhi_timeseries.json"
               % quote(NOMBRE_NHI.get(vol, vol)))
        (Path(directorio) / ("%s.json" % vol)).write_bytes(urlopen(url, timeout=60).read())


def tasas_barrido(brazos, fin, dest):
    """{s: {sensor | "NOCHE": (n_pub, n_neg)}} sobre negativos limpios con el etiquetador del banco (sin escenas
    inválidas). Por sensor: pasadas `neg_limpio` y cuántas publica el tablero. NOCHE: noches de volcán (tres sensores)
    con alguna pasada `neg_limpio` y ninguna `pos` ni `far_ref` (la misma noche negativa del banco) y cuántas tienen
    alguna pasada publicada. La referencia de MIROVA se baja fresca del remoto, como el banco (el snapshot del repo se
    refresca sólo los domingos)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    ventana = (VENTANA_CALIBRACION_INICIO, fin)
    info = bp.bajar_remoto(Path(dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    filas = bp.cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    out = {}
    for s, d in brazos.items():
        recs = [r for r in bp.cargar_nuestros(coords, inner, ventana, data=d, excluir_escenas_invalidas=True)
                if r["vol"] in VOLCANES_ZONA_A]
        bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        out[s] = {sen: (sum(1 for r in recs if r["b"] == sen and r["lab"] == "neg_limpio" and r["pub"]),
                        sum(1 for r in recs if r["b"] == sen and r["lab"] == "neg_limpio")) for sen in SENSORES}
        noches = collections.defaultdict(list)
        for r in recs:
            noches[(r["vol"], r["noche"])].append(r)
        neg = [v for v in noches.values() if any(r["lab"] == "neg_limpio" for r in v)
               and not any(r["lab"] in ("pos", "far_ref") for r in v)]
        out[s]["NOCHE"] = (sum(1 for v in neg if any(r["pub"] for r in v)), len(neg))
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluar")
    e.add_argument("--lab", required=True)
    e.add_argument("--prod", default=str(ROOT / "data" / "mirova_equivalent"))
    e.add_argument("--nhi-dir", required=True)
    e.add_argument("--bajar-nhi", action="store_true")
    e.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    e.add_argument("--out", required=True)
    c = sub.add_parser("calibrar")
    c.add_argument("--barrido", action="append", required=True, help="s=carpeta de records del brazo")
    c.add_argument("--prod", default=str(ROOT / "data" / "mirova_equivalent"))
    c.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    c.add_argument("--dest", required=True, help="carpeta temporal para la referencia de MIROVA")
    c.add_argument("--out", required=True)
    sub.add_parser("poder")
    a = ap.parse_args(argv)
    if a.cmd == "poder":
        print("exceso mínimo detectable (p < %.2f, una cola, permutación exacta sin estratos)" % ALFA)
        print("n_S  n_N  basal  alertas_minimas_en_S  tasa_minima_en_S")
        for n_s in (10, 20, 40):
            for p0 in (0.07, 0.15, 0.35):
                k = minimo_detectable(n_s, 80, p0)
                print("%3d  %3d  %5.2f  %20s  %16s" % (n_s, 80, p0, k, "-" if k is None else "%.2f" % (k / n_s)))
        print("P(>= %d de 9 volcanes con p < %.2f | nulo) <= %.5f" % (MIN_VOLCANES_CUMPLE, ALFA,
                                                                   prob_al_menos(MIN_VOLCANES_CUMPLE, 9, ALFA)))
        print("P(control falla en un desplazamiento | nulo) <= %.4f (>= %d de 9)" % (
            prob_al_menos(MAX_VOLCANES_SIG_CONTROL + 1, 9, ALFA), MAX_VOLCANES_SIG_CONTROL + 1))
        return 0
    if a.cmd == "calibrar":
        brazos = {float(x.split("=", 1)[0]): x.split("=", 1)[1] for x in a.barrido}
        tasas = tasas_barrido(brazos, a.fin, a.dest)
        tasas_prod = tasas_barrido({"prod": a.prod}, a.fin, a.dest)["prod"]
        res = elegir_valor(tasas)
        if not control_barrido(tasas, tasas_prod):
            res = {"estado": INVALIDO, "valor": None,
                   "detalle": "el brazo s = %.1f no reproduce a producción: %s contra %s"
                              % (GRILLA_S[0], tasas.get(GRILLA_S[0]), tasas_prod)}
        res["tasas_produccion"] = tasas_prod
        res["tasas"] = {str(s): v for s, v in tasas.items()}
        Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({k: res[k] for k in ("estado", "valor", "detalle")}, ensure_ascii=False))
        return 0
    if a.bajar_nhi:
        bajar_nhi(a.nhi_dir)
    noches = clasificar_noches(cargar_pasadas(a.lab, VENTANA_INICIO, a.fin),
                               cargar_pasadas(a.prod, VENTANA_INICIO, a.fin))
    res = veredicto(noches, cargar_nhi(a.nhi_dir), anclas_reales(), fin=a.fin)
    res["meta"] = {"lab": a.lab, "prod": a.prod, "ventana": [VENTANA_INICIO, a.fin],
                   "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(res["veredicto"], "|", "; ".join(res["motivos"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
