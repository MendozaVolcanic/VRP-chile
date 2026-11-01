# -*- coding: utf-8 -*-
"""Regla NLC (negativo limpio con crater), S159. Biblioteca comun de medir.py; no cambia ninguna etiqueta del banco.

POR QUE. Cuando el ROI cae entre dos granulos de la misma orbita, MIROVA lista uno solo (casi siempre el del sur) y
no ve el crater si quedo en el otro. Su fila RUTINA ahi es «no mire», no «no vi». La regla (INFORME.md §0) saca esas
pasadas de los negativos limpios usando diag_n_bg_anillo como indicador de en que granulo esta el crater.
"""
import collections
import json
from datetime import timedelta
from pathlib import Path

PASO = {"MODIS": timedelta(minutes=5), "VIIRS375": timedelta(minutes=6), "VIIRS750": timedelta(minutes=6)}
MISMO_GRANULO_S = 120   # el pareo del banco: una fila a +-120 s es del mismo granulo


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    return "VIIRS375" if s.startswith("VIIRS") else None


def indice_anillo(data_dir, vols):
    """(vol, sensor, 'YYYY-MM-DD HH:MM') -> nbg, y cadenas: clave -> clave del companero (solo cadenas de dos)."""
    from datetime import datetime
    nbg, por = {}, collections.defaultdict(dict)
    for vol in vols:
        recs = json.load(open(Path(data_dir) / f"{vol}.json", encoding="utf-8"))["records"]
        for r in recs:
            k = (vol, r["sensor"], r["datetime_utc"][:16])
            nbg[k] = r.get("diag_n_bg_anillo")
            por[(vol, r["sensor"])][datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")] = k
    comp, largos = {}, collections.Counter()
    for (vol, s), d in por.items():
        p = PASO[bucket(s)]
        ts = sorted(d)
        cad, cur = [], [ts[0]]
        for t in ts[1:]:
            if t - cur[-1] == p:
                cur.append(t)
            else:
                cad.append(cur); cur = [t]
        cad.append(cur)
        for c in cad:
            largos[len(c)] += 1
            if len(c) == 2:
                comp[d[c[0]]] = d[c[1]]
                comp[d[c[1]]] = d[c[0]]
    return nbg, comp, largos


def fraccion(k, nbg, comp):
    """f del record k en su cadena de dos; None si esta solo; 'indet' si el anillo total es 0 o falta."""
    q = comp.get(k)
    if q is None:
        return None
    a, b = nbg.get(k), nbg.get(q)
    if a is None or b is None or (a + b) == 0:
        return "indet"
    return a / (a + b)


def crater_en_granulo_mirova(k, filas_dt, t_rec, nbg, comp, corte=0.5):
    """Regla NLC para un record k etiquetado neg_limpio. filas_dt: datetimes de las filas de MIROVA pareadas.

    Devuelve (bool se_queda, motivo).
    """
    mismo = [t for t in filas_dt if abs((t - t_rec).total_seconds()) <= MISMO_GRANULO_S]
    if mismo:
        f = fraccion(k, nbg, comp)
        if f is None:
            return True, "solo"
        if f == "indet":
            return True, "indet"
        return (f >= corte), ("partida_con_crater" if f >= corte else "partida_sin_crater")
    # regla 2: MIROVA listo el granulo vecino
    q = comp.get(k)
    if q is None:
        return False, "vecino_que_no_tenemos"
    f = fraccion(q, nbg, comp)
    if f == "indet":
        return True, "indet"
    return (f >= corte), ("vecino_con_crater" if f >= corte else "vecino_sin_crater")
