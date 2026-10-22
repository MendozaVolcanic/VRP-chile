# -*- coding: utf-8 -*-
"""S159 frente N, paso 7: lee el censo (PREREGISTRO_CENSO_N.md) y cuenta lo pre-registrado.

Pregunta 1 (si F estuviera roto, ¿se vería?): el control positivo es que F publique cúmulos de cumbre en 0,0 MW que K
no publica; si F no actuara, los 60 quedarían como K. Pregunta 2 (instrumento muerto): K tiene que reproducir la
publicación y el `pc.vrp_mw` de producción en todas las pasadas ok; las SIN DATO se cuentan aparte.
El oráculo se informa aparte, con el predicado del tablero sobre un record sintético (ver el pre-registro).
Uso: python 07_censo_analizar.py --art <carpeta del run del censo>
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments/_s158_audit_r2/oraculo"))
import banco_paridad as B  # noqa: E402
import mirova_v750_r2 as ORA  # noqa: E402

BRAZOS = ("K", "K2", "C", "F", "FC")
MB_GANADAS_LOTE = 48   # censo de pos_nopub en el lote (03_analizar_salida.txt §8)


def slim(rec):
    s = {k: rec.get(k) for k in B.CAMPOS_JS if k != "anomaly_pixels"}
    s["anomaly_pixels"] = []
    return s


def record_oraculo(o, inner, sensor):
    """Record sintético desde la salida del oráculo, para el predicado del tablero (sin store)."""
    if not o or not o.get("npix"):
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    px = o["pixeles"]
    c = 33
    fr, fc = np.mean([p[0] for p in px]), np.mean([p[1] for p in px])
    dcen = float(np.hypot(fr - c, fc - c) * 0.75)
    Lmax = max(p[4] for p in px)
    tmax = float(ORA.radiancia_a_temperatura(np.array([Lmax]), ORA.LAMBDA_M13)[0])
    v = round(float(o["vrp_mw"]), 3)
    return {"sensor": sensor, "vrp_mw": v, "t_max_k": tmax, "triggered_test1": False,
            "distance_class": "summit" if dcen <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": o["npix"], "centroid_dist_km": round(dcen, 3)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_censo.json").read_text(encoding="utf-8"))}
    res = {}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r["id"] in obj and (r.get("estado") == "ok" or r["id"] not in res):
                    res[r["id"]] = r
    inner = B.inner_desde_html()
    L = []
    pr = lambda *x: (print(*x), L.append(" ".join(str(y) for y in x)))
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res))
    cob = collections.Counter((o["clase"], (res.get(i) or {}).get("estado", "sin_resultado")) for i, o in obj.items())
    pr("  ", dict(sorted(cob.items())))
    ok = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("brazos")
          and all("error" not in (r["brazos"].get(b) or {"error": 1}) for b in BRAZOS)]
    sin = [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"], (res.get(i) or {}).get("estado", "sin_resultado"))
           for i in obj if i not in ok]
    pr("   con cinco brazos ok:", len(ok), "| SIN DATO:", sin)

    casos, idx = [], []
    for i in ok:
        v = obj[i]["volcan"]
        for b in BRAZOS:
            rec = res[i]["brazos"][b].get("record")
            if rec is not None:
                casos.append([slim(rec), inner[v]])
                idx.append((i, b))
        o = (res[i].get("oraculo") or {})
        for n in ("geo_linear", "geo_linear_anillo_sensible"):
            if n in o:
                casos.append([record_oraculo(o[n], inner[v], obj[i]["sensor"]), inner[v]])
                idx.append((i, "O_" + n))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    pub = lambda i, b: P.get((i, b), False)

    # controles
    dpub = [(i, obj[i]["pub_prod"], pub(i, "K")) for i in ok if bool(obj[i]["pub_prod"]) != pub(i, "K")]
    dvrp = []
    for i in ok:
        kv = ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw")
        pv = obj[i].get("pc_vrp")
        if not ((kv is None and pv is None) or (kv is not None and pv is not None and abs(kv - pv) <= 0.001)):
            dvrp.append((i, pv, kv))
    k2 = [i for i in ok if json.dumps(res[i]["brazos"]["K"]["record"], sort_keys=True)
          != json.dumps(res[i]["brazos"]["K2"]["record"], sort_keys=True)]
    det = [i for i in ok if res[i]["brazos"]["F"].get("n_hot") != res[i]["brazos"]["K"].get("n_hot")
           or (((res[i]["brazos"]["F"]["record"] or {}).get("primary_cluster") or {}).get("n_pixels")
               != ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("n_pixels"))]
    dcl = [i for i in ok if (res[i]["brazos"]["F"]["record"] or {}).get("distance_class")
           != (res[i]["brazos"]["K"]["record"] or {}).get("distance_class")]
    pr("== controles: K publica distinto de produccion", dpub, "| pc distinto", dvrp, "| K2 != K", k2,
       "| F cambia la deteccion", det, "| F cambia distance_class", dcl)

    # conteo pre-registrado
    pr("== F en el censo (crudo, sin pesos)")
    for cl in ("cumbre_0mw", "far", "isluga_1012", "reintento_1012"):
        ids = [i for i in ok if obj[i]["clase"] == cl]
        pr(f"   {cl:15s} n={len(ids):3d} " + " ".join(f"{b}={sum(pub(i, b) for i in ids)}" for b in BRAZOS)
           + f" | O_lineal={sum(pub(i, 'O_geo_linear') for i in ids)} O_anillo="
             f"{sum(pub(i, 'O_geo_linear_anillo_sensible') for i in ids)}")
    neg = [i for i in ok if obj[i]["clase"] in ("cumbre_0mw", "far")]
    enc = [i for i in neg if pub(i, "F") and not pub(i, "K")]
    apa = [i for i in neg if pub(i, "K") and not pub(i, "F")]
    isl = [i for i in ok if obj[i]["clase"] == "isluga_1012"]
    gan_isl = sum(1 for i in isl if pub(i, "F") and not pub(i, "K"))
    sin_neg = [x for x in sin if x[3] in ("cumbre_0mw", "far")]
    sin_isl = [x for x in sin if x[3] == "isluga_1012"]
    gan = MB_GANADAS_LOTE + gan_isl
    dE = len(enc) - len(apa) - gan
    # rango por SIN DATO: negativos sin dato encendidos todos o ninguno; Isluga sin dato ganada o no
    dE_hi = dE + len(sin_neg)
    dE_lo = dE - len(sin_isl)
    pr(f"   negativos encendidos por F: {len(enc)} de {len(neg)} medidos (cumbre "
       f"{sum(1 for i in enc if obj[i]['clase'] == 'cumbre_0mw')}, far {sum(1 for i in enc if obj[i]['clase'] == 'far')}); "
       f"apagados {len(apa)}; SIN DATO {len(sin_neg)}")
    pr(f"   alertas bajo 1 MW ganadas: {MB_GANADAS_LOTE} del lote + {gan_isl} de Isluga 10-12 (SIN DATO {len(sin_isl)})")
    pr(f"   dE_F (censo) = {len(enc)} - {len(apa)} - {gan} = {dE}  (rango por SIN DATO {dE_lo} a {dE_hi})")
    negK = 54
    pr(f"   negativos limpios publicados: K {negK} de 5476 ({negK / 5476:.2%}); F {negK + len(enc)} "
       f"({(negK + len(enc)) / 5476:.2%}), hasta {negK + len(enc) + len(sin_neg)} con los SIN DATO")
    for i in enc:
        pc = res[i]["brazos"]["F"]["record"]["primary_cluster"]
        pr(f"     {i} {obj[i]['volcan']} {obj[i]['hora_utc']} {obj[i]['clase']} z {obj[i]['z']} F {pc['vrp_mw']} MW "
           f"{pc['n_pixels']} px a {pc['centroid_dist_km']} km banda "
           f"{[round(x, 3) for x in (res[i]['brazos']['F'].get('F_pc_banda') or [])]} | O {(res[i].get('oraculo') or {}).get('geo_linear', {}).get('npix')} px")
    nf = [i for i in ok if obj[i]["clase"] == "cumbre_0mw" and not pub(i, "F")]
    for i in nf:
        pc = (res[i]["brazos"]["F"]["record"] or {}).get("primary_cluster")
        pr(f"     cumbre que F NO publica: {i} {obj[i]['volcan']} {obj[i]['hora_utc']} F pc {pc} dc "
           f"{res[i]['brazos']['F']['record'].get('distance_class')}")
    # protegidas: reintentos
    for i in obj:
        if obj[i]["clase"] in ("reintento_1012", "isluga_1012"):
            r = res.get(i, {})
            pr(f"   {obj[i]['clase']} {obj[i]['volcan']} {obj[i]['hora_utc']} prot {obj[i]['protegida']} MIROVA "
               f"{obj[i]['mirova_vrp']} estado {r.get('estado')} | " + " ".join(f"{b}={pub(i, b)}" for b in BRAZOS))
    # oráculo aparte
    for n in ("O_geo_linear", "O_geo_linear_anillo_sensible"):
        on = [i for i in neg if pub(i, n)]
        pr(f"== oraculo {n} (predicado del tablero sobre record sintetico): publica {len(on)} de {len(neg)} negativos "
           f"del censo: {[(i, obj[i]['volcan'], obj[i]['hora_utc'], obj[i]['clase']) for i in on]}")
    (AQUI / "07_censo_analizar_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
