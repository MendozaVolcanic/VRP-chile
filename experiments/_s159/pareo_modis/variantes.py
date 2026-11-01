# -*- coding: utf-8 -*-
"""Tres pareos para el banco de paridad y el auto-audit, como parches EN MEMORIA sobre un espejo de main.

No edita ningun archivo de scripts/: importa banco_paridad y auto_audit_weekly del espejo (--raiz) y
reemplaza funciones del modulo ya cargado.

  hoy     : sin cambios (TOL 120 s).
  ancha   : tolerancia 390 s en todo pareo por pasada (banco_paridad.parear, alertas_sin_record,
            auto_audit_weekly.TOL_PASADA_S). Cubre el granulo vecino de MODIS (5 min) y de VIIRS (6 min).
            Defecto conocido: si tenemos los dos granulos de la misma orbita, los dos records quedan
            etiquetados con la misma fila de MIROVA (doble conteo de una pasada fisica).
  orbita  : la unidad es la PASADA FISICA: records del mismo volcan y la misma plataforma en granulos
            consecutivos (diferencia exacta de 5 min MODIS, 6 min VIIRS) se juntan en una cadena; la
            cadena publica si publica cualquiera de sus records (lo que ve el operador: dos puntos de la
            misma pasada) y se etiqueta con las filas de MIROVA a 120 s de cualquiera de sus horas, o, si
            no hay ninguna, con las del granulo vecino de sus extremos. Un solo record por cadena entra
            al banco. Para las alertas protegidas y la "misma pasada" de la magnitud equivale a 390 s,
            porque una cadena nunca pasa de dos granulos (verificado en medir_pareo).

clase_mirova.VENTANA_S (regla D-9 de alertas minimas) NO se toca en ninguna variante: compara filas de
MIROVA entre si y MIROVA lista los dos granulos de una orbita solo 12 veces en 12.780 pasadas MODIS.
"""
import bisect
import collections
import os
import sys
from datetime import timedelta
from pathlib import Path

TOL_ANCHA = 390


def paso_min(sensor_o_bucket):
    s = sensor_o_bucket or ""
    return 5 if s.startswith("MODIS") else 6


def cargar(raiz):
    raiz = Path(raiz)
    sys.path.insert(0, str(raiz))
    sys.path.insert(0, str(raiz / "scripts"))
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import banco_paridad as bp
    import auto_audit_weekly as aaw
    assert str(bp.ROOT).replace("\\", "/").lower() == str(raiz).replace("\\", "/").lower(), (bp.ROOT, raiz)
    return bp, aaw


def _parear_original(lista, t, tol):
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
    out = []
    while i < len(lista) and lista[i][0] <= t + timedelta(seconds=tol):
        out.append(lista[i][1])
        i += 1
    return out


def aplicar(bp, aaw, variante, registro=None):
    """Parchea los modulos. `registro` (dict) recibe las cadenas colapsadas para inspeccion."""
    if variante == "hoy":
        return
    if variante == "ancha":
        def parear(lista, t, tol=TOL_ANCHA):
            return _parear_original(lista, t, tol)
        bp.parear = parear
        bp.TOL_S = TOL_ANCHA
        aaw.TOL_PASADA_S = TOL_ANCHA
        return
    if variante != "orbita":
        raise ValueError(variante)
    aaw.TOL_PASADA_S = TOL_ANCHA
    cadenas = {}                     # (vol, b, dt_representante) -> (horas de la cadena, paso)
    original_cargar = bp.cargar_nuestros

    def cargar_nuestros(*args, **kw):
        recs = original_cargar(*args, **kw)
        grupos = collections.defaultdict(list)
        for r in recs:
            grupos[(r["vol"], r["b"], r.get("sensor"))].append(r)
        out = []
        for (vol, b, sensor), lista in grupos.items():
            lista.sort(key=lambda r: r["dt"])
            p = timedelta(minutes=paso_min(sensor))
            actual = [lista[0]]
            bloques = []
            for r in lista[1:]:
                if r["dt"] - actual[-1]["dt"] == p:
                    actual.append(r)
                else:
                    bloques.append(actual)
                    actual = [r]
            bloques.append(actual)
            for bl in bloques:
                rep = dict(bl[0])
                rep["pub"] = max(x["pub"] for x in bl)
                rep["disp"] = max(x["disp"] for x in bl)
                rep["n_cadena"] = len(bl)
                rep["horas_cadena"] = [x["dt"] for x in bl]
                rep["pub_por_hora"] = [x["pub"] for x in bl]
                cadenas[(vol, b, rep["dt"])] = ([x["dt"] for x in bl], p)
                out.append(rep)
        if registro is not None:
            registro["n_records"] = len(recs)
            registro["n_cadenas"] = len(out)
            registro["largo"] = collections.Counter(r["n_cadena"] for r in out)
        return out

    def etiquetar(recs, por_vb, noche_sensor, noche_volcan):
        # la lista de referencia no sabe de que (vol, b) es: se la paso por cierre, record a record
        for r in recs:
            lista = por_vb.get((r["vol"], r["b"]), [])
            horas, p = cadenas.get((r["vol"], r["b"], r["dt"]), ([r["dt"]], timedelta(0)))
            filas = []
            for h in horas:
                filas += _parear_original(lista, h, 120)
            if not filas and p:
                filas = (_parear_original(lista, horas[0] - p, 120)
                         + _parear_original(lista, horas[-1] + p, 120))
            r["_filas_orbita"] = filas
        original_parear = bp.parear
        try:
            filas_de = {id(r): r["_filas_orbita"] for r in recs}
            cola = list(recs)
            idx = {"i": 0}

            def parear(lista, t, tol=120):
                r = cola[idx["i"]]
                idx["i"] += 1
                assert r["dt"] == t, (r["dt"], t)
                return filas_de[id(r)]
            bp.parear = parear
            original_etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        finally:
            bp.parear = original_parear

    original_etiquetar = bp.etiquetar
    bp.cargar_nuestros = cargar_nuestros
    bp.etiquetar = etiquetar

    original_sin_record = bp.alertas_sin_record

    def alertas_sin_record(por_vb, recs):
        # una alerta en el granulo vecino de una cadena SI tiene record (es la misma pasada)
        expandidos = []
        for r in recs:
            horas, p = cadenas.get((r["vol"], r["b"], r["dt"]), ([r["dt"]], timedelta(0)))
            for h in [horas[0] - p] + horas + [horas[-1] + p]:
                expandidos.append(dict(r, dt=h))
        return original_sin_record(por_vb, expandidos)
    bp.alertas_sin_record = alertas_sin_record
