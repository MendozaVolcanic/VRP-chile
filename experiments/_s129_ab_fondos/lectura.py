# -*- coding: utf-8 -*-
"""Lectura del A/B de los dos fondos autorreferentes (S129).

Escrita ANTES del reproceso (A16). Concentra las decisiones metodológicas que,
re-escritas a mano en cada veredicto, es donde aparecen los errores: emparejar
sobre la INTERSECCIÓN de pasadas, un par por NOCHE con el máximo de ambos lados,
y `pc.vrp_mw` nunca `record.vrp_mw` (A10).

Las cuatro firmas están definidas en `docs/s129/PREREGISTRO_AB_FONDOS.md` y no se
tocan después de ver resultados. F2 (conteo de detecciones) y F3 (brecha por
régimen) son las que ATRIBUYEN: el brazo del pool debe moverlas y el del fondo de
magnitud no.
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "experiments"))
from _s126_lib import bucket                                   # noqa: E402

BUCK = "v375"


def _noches(recs):
    """{fecha: (vrp_max, delta_t, umbral)} — un registro por noche, el mayor VRP."""
    out = {}
    for r in recs:
        if bucket(r.get("sensor")) != BUCK:
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        f = r.get("datetime_utc", "")[:10]
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        tmax = r.get("t_max_i04_k") or r.get("t_max_k")
        tbg = r.get("t_bg_k")
        dt = (tmax - tbg) if (tmax is not None and tbg is not None) else None
        if f not in out or v > out[f][0]:
            out[f] = (v, dt, r.get("diag_eff_threshold_k"))
    return out


def pares_intersectados(brazo, mirova, pasadas=None):
    """[{vol, fecha, nuestro, mirova, ratio, delta_t}] sobre las noches comunes.

    `pasadas` es el conjunto de fechas presentes en TODOS los brazos. Sin él, un
    brazo que procesó más granules parece 'detectar más' cuando lo único que pasa
    es que miró más veces.
    """
    pares = []
    for vol, recs in brazo.items():
        for f, (v, dt, _thr) in _noches(recs).items():
            if pasadas is not None and f not in pasadas:
                continue
            if v <= 0:
                continue
            m = (mirova.get(vol) or {}).get((f, BUCK))
            pares.append({"vol": vol, "fecha": f, "nuestro": v,
                          "mirova": m, "ratio": (v / m) if m else None,
                          "delta_t": dt})
    return pares


def brecha_por_regimen(pares):
    """F3 — ratio del tercil DÉBIL menos el del tercil FUERTE de delta_t.

    El mecanismo del pool (GAP #A) infla el umbral y hace perder los píxeles
    marginales del borde del clúster. Steffke & Harris 2011 p.1134 mide que eso
    cuesta el 12 % de la potencia en una anomalía intensa y el 50 % en una débil,
    así que encender ese flag debería ACHICAR esta brecha. El fondo de la magnitud
    no tiene por qué tocarla.
    """
    con = [p for p in pares if p.get("delta_t") is not None
           and p.get("ratio") is not None]
    if len(con) < 6:
        return {"debil": None, "fuerte": None, "brecha": None, "n": len(con)}
    con.sort(key=lambda p: p["delta_t"])
    t = len(con) // 3
    debil = round(st.median([p["ratio"] for p in con[:t]]), 3)
    fuerte = round(st.median([p["ratio"] for p in con[-t:]]), 3)
    return {"debil": debil, "fuerte": fuerte,
            "brecha": round(debil - fuerte, 3), "n": len(con)}


def firmas_de_brazo(brazo, mirova, pasadas=None):
    """Las cuatro firmas del pre-registro para un brazo."""
    pares = pares_intersectados(brazo, mirova, pasadas)
    ratios = [p["ratio"] for p in pares if p["ratio"] is not None]
    umbrales = [thr for recs in brazo.values()
                for (_v, _dt, thr) in _noches(recs).values() if thr is not None]
    return {
        "ratio_mediano": round(st.median(ratios), 3) if ratios else None,
        "n_detecciones": sum(1 for recs in brazo.values()
                             for (v, _dt, _t) in _noches(recs).values() if v > 0),
        "regimen": brecha_por_regimen(pares),
        "umbral_mediano": round(st.median(umbrales), 3) if umbrales else None,
        "n_pares": len(ratios),
    }
