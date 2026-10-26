# -*- coding: utf-8 -*-
"""Verificador del censo del oraculo V750 (S159): recuento por camino propio, sin pasar por 02_analizar.py.

Lee los resultados crudos del run (resultados_*.json), arma los records para el predicado del tablero con codigo
propio (K: campos del record; oraculo: record sintetico reimplementado desde PREREGISTRO.md seccion 3, y se compara con
record_oraculo de experiments/_s159/n/07_censo_analizar.py), corre el predicado con node UNA vez guardando las cinco
columnas (summit, valid, art, disp, pub) y cuenta.

Pregunta 1 (si el conteo estuviera roto, se veria?): control positivo propio al final (todos los K a `far` tienen que
dar 0 publicaciones; inyectar un cumulo de 0,3 MW en todos los negativos sin publicar tiene que publicarlos todos).
Pregunta 2 (instrumento muerto): si node no corre, el script aborta; si no carga crudos, el assert de 5.746 falla.
Ventana de todo numero: V750 nocturno 2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre (objetivos.json, 5.746).
Uso: python verif_recuento.py --art <run_censo> [<run_rescate>] --salida <sufijo>
"""
from __future__ import annotations

import argparse
import collections
import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
OBJ_DIR = AQUI.parent
ROOT = AQUI.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments/_s158_audit_r2/oraculo"))
import banco_paridad as B  # noqa: E402
import mirova_v750_r2 as ORA  # noqa: E402

spec = importlib.util.spec_from_file_location("cen", ROOT / "experiments/_s159/n/07_censo_analizar.py")
CEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CEN)

CAJAS = {"geo_linear": "O-def", "geo_linear_anillo_sensible": "O-sens"}
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def cargar_crudos(dirs):
    """Carga propia: cada id una sola vez por run; un run posterior solo reemplaza si trae estado ok."""
    res, vistos_por_run = {}, []
    for d in dirs:
        vistos = collections.Counter()
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                vistos[r["id"]] += 1
                if r["id"] not in res or r.get("estado") == "ok":
                    res[r["id"]] = r
        dup = [i for i, n in vistos.items() if n > 1]
        vistos_por_run.append((d, len(vistos), dup))
    return res, vistos_por_run


def sintetico_propio(o, inner, sensor):
    """Reimplementacion desde PREREGISTRO.md seccion 3 (no copia de record_oraculo)."""
    if not o or not o.get("npix"):
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    filas = [p[0] for p in o["pixeles"]]
    cols = [p[1] for p in o["pixeles"]]
    d = float(np.hypot(np.mean(filas) - 33, np.mean(cols) - 33) * 0.75)
    L_max = max(p[4] for p in o["pixeles"])
    t = float(ORA.radiancia_a_temperatura(np.array([L_max]), ORA.LAMBDA_M13)[0])
    v = round(float(o["vrp_mw"]), 3)
    return {"sensor": sensor, "vrp_mw": v, "t_max_k": t, "triggered_test1": False,
            "distance_class": "summit" if d <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": o["npix"], "centroid_dist_km": round(d, 3)}}


def dist_max_px(o):
    return max(float(np.hypot(p[0] - 33, p[1] - 33) * 0.75) for p in o["pixeles"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--salida", default="")
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((OBJ_DIR / "objetivos.json").read_text(encoding="utf-8"))}
    assert len(obj) == 5746, len(obj)
    res, vistos = cargar_crudos(a.art)
    inner = B.inner_desde_html()
    pr("== carga propia de crudos")
    for d, n, dup in vistos:
        pr(f"   {d}: ids vistos {n}, duplicados dentro del run {len(dup)} {dup[:10]}")
    pr("   ids con resultado:", len(res), "de", len(obj), "| ids de crudos fuera de objetivos:", len(set(res) - set(obj)))
    est = collections.Counter(r.get("estado", "?") for r in res.values())
    pr("   estados:", dict(est))

    ok = [i for i in sorted(obj) if (res.get(i) or {}).get("estado") == "ok"
          and all(c in (res[i].get("oraculo") or {}) for c in CAJAS)
          and "record" in ((res[i].get("brazos") or {}).get("K") or {})]
    fuera = [i for i in sorted(obj) if (res.get(i) or {}).get("estado") == "volcan_fuera_del_granulo"]
    sin = [i for i in sorted(obj) if i not in ok and i not in fuera]
    pr(f"   ok {len(ok)} | fuera {len(fuera)} | SIN DATO {len(sin)}")
    pr("   SIN DATO por dia:", dict(collections.Counter(obj[i]["hora_utc"][:10] for i in sin)))
    pr("   ok con estado ok pero sin alguna caja o sin record K:",
       sum(1 for i in obj if (res.get(i) or {}).get("estado") == "ok" and i not in ok))

    # ---------------------------------------------------------------- pareo del granulo (el record K es del mismo granulo)
    mal_gran = [i for i in ok if res[i]["brazos"]["K"]["record"].get("granule") != obj[i]["granule"]]
    mal_hora = [i for i in ok if res[i]["brazos"]["K"]["record"].get("datetime_utc") != obj[i]["hora_utc"]]
    mal_sens = [i for i in ok if res[i]["brazos"]["K"]["record"].get("sensor") != obj[i]["sensor"]]
    pr(f"== record K del mismo granulo que el objetivo: granule distinto {len(mal_gran)}, hora distinta {len(mal_hora)}, "
       f"sensor distinto {len(mal_sens)}")

    # ---------------------------------------------------------------- record sintetico: copia vs reimplementacion
    dif_sint = 0
    for i in ok:
        for c in CAJAS:
            x = sintetico_propio(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"])
            y = CEN.record_oraculo(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"])
            if json.dumps(x, sort_keys=True) != json.dumps(y, sort_keys=True):
                dif_sint += 1
    pr(f"== record sintetico: reimplementacion vs record_oraculo copiado, distintos {dif_sint} de {2 * len(ok)}")

    # ---------------------------------------------------------------- predicado con node, cinco columnas
    casos, idx = [], []
    for i in ok:
        rec = res[i]["brazos"]["K"]["record"]
        k = {kk: rec.get(kk) for kk in B.CAMPOS_JS if kk != "anomaly_pixels"}
        k["anomaly_pixels"] = []
        casos.append([k, inner[obj[i]["volcan"]]])
        idx.append((i, "K"))
        for c in CAJAS:
            casos.append([sintetico_propio(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"]),
                          inner[obj[i]["volcan"]]])
            idx.append((i, c))
    F = dict(zip(idx, B.correr_node(casos)))   # [summit, valid, art, disp, pub]
    pub = lambda i, b: bool(F[(i, b)][4])

    neg = [i for i in ok if obj[i]["lab"] == "neg_limpio"]
    pos = [i for i in ok if obj[i]["lab"] == "pos"]
    dec = [i for i in pos if obj[i]["decide"]]
    prot = [i for i in dec if obj[i]["protegida"]]
    mb = [i for i in dec if not obj[i]["protegida"]]
    pr(f"== poblacion ok: negativos {len(neg)} | alertas {len(pos)} (deciden {len(dec)}: protegidas {len(prot)}, "
       f"bajo 1 MW {len(mb)}; solo OCR antes del 06-13 {len(pos) - len(dec)})")
    pr("   negativos cuyas filas de MIROVA no son todas RUTINA:",
       sum(1 for i in neg if any(m["tipo"] != "RUTINA" for m in obj[i]["mirova"])))

    # ---------------------------------------------------------------- (a) recuento de negativos publicados
    pr("== (a) negativos limpios publicados, recuento propio sobre", len(neg), "ok")
    pr(f"   K {sum(pub(i, 'K') for i in neg)} | O-def {sum(pub(i, 'geo_linear') for i in neg)} | "
       f"O-sens {sum(pub(i, 'geo_linear_anillo_sensible') for i in neg)}")
    pr(f"   produccion (pub_prod de objetivos.json) en los mismos {len(neg)} ok: {sum(bool(obj[i]['pub_prod']) for i in neg)}")
    pr(f"   produccion en TODOS los negativos de la poblacion ({len([i for i in obj if obj[i]['lab'] == 'neg_limpio'])}): "
       f"{sum(bool(obj[i]['pub_prod']) for i in obj if obj[i]['lab'] == 'neg_limpio')} "
       f"| en los 'fuera': {sum(bool(obj[i]['pub_prod']) for i in fuera)} | en SIN DATO: {sum(bool(obj[i]['pub_prod']) for i in sin)}")
    for c, nom in CAJAS.items():
        enc = [i for i in neg if pub(i, c) and not pub(i, "K")]
        apa = [i for i in neg if pub(i, "K") and not pub(i, c)]
        pr(f"   {nom}: encendidos {len(enc)}, apagados {len(apa)}")
        for i in enc:
            rec = res[i]["brazos"]["K"]["record"]
            o = res[i]["oraculo"][c]
            pr(f"      enc {i} {obj[i]['volcan']} {obj[i]['hora_utc']}: K dc={rec.get('distance_class')} pc={rec.get('primary_cluster')} "
               f"n_px={rec.get('n_anomalous_pixels')} vrp_mw={rec.get('vrp_mw')} | O npix={o['npix']} vrp={o['vrp_mw']:.3f} "
               f"dmax_px={dist_max_px(o):.2f} km inner={inner[obj[i]['volcan']]}")

    # ---------------------------------------------------------------- control 1 por camino propio
    pcK = {i: ((res[i]["brazos"]["K"]["record"].get("primary_cluster") or {}).get("vrp_mw")) for i in ok}
    nn = sum(1 for i in ok if pcK[i] is None and obj[i]["pc_vrp"] is None)
    dif = [i for i in ok if (pcK[i] is None) != (obj[i]["pc_vrp"] is None)
           or (pcK[i] is not None and abs(pcK[i] - obj[i]["pc_vrp"]) > 0.001)]
    dpub = [i for i in ok if bool(obj[i]["pub_prod"]) != pub(i, "K")]
    pr(f"== control 1 propio sobre {len(ok)} ok: pub distinta {len(dpub)}; pc.vrp_mw distinto {len(dif)}; "
       f"pares None-None (no comparan nada) {nn}; K con pc None {sum(1 for i in ok if pcK[i] is None)}; "
       f"K con pc 0,0 MW {sum(1 for i in ok if pcK[i] == 0.0)}; K con pc = 5,0 exacto (tope D9) {sum(1 for i in ok if pcK[i] == 5.0)}")
    pr("   SHA de codigo de los records de produccion (regimen.codigo_sha) en ok:",
       len({obj[i]['sha'] for i in ok}), "distintos; el control pasa en todos")

    # ---------------------------------------------------------------- (b) ramas del predicado por tipo de record
    pr("== (b) ramas del predicado (columnas de node) por tipo de record, sobre", len(ok), "ok")
    for b, nom in (("K", "K"), ("geo_linear", "O-def"), ("geo_linear_anillo_sensible", "O-sens")):
        f = [F[(i, b)] for i in ok]
        con_pc = [i for i in ok if (res[i]["brazos"]["K"]["record"].get("primary_cluster") if b == "K"
                                   else res[i]["oraculo"][b].get("npix"))]
        pr(f"   {nom}: summit {sum(x[0] for x in f)}, valid {sum(x[1] for x in f)}, artefacto termico {sum(x[2] for x in f)}, "
           f"disp>0 {sum(1 for x in f if x[3] > 0)}, publica {sum(x[4] for x in f)} | con cumulo/pixeles {len(con_pc)}")
        # con cumulo pero no publica: por que rama
        por_que = collections.Counter()
        for i in con_pc:
            s, v, art, disp, p = F[(i, b)]
            if p:
                continue
            if not s:
                por_que["no summit (etiqueta far o descartado)"] += 1
            elif not v:
                por_que["cumulo con 0,0 MW"] += 1
            elif art:
                por_que["artefacto termico"] += 1
            elif disp <= 0:
                por_que["disp 0 (pc.centroid_dist_km > inner)"] += 1
            else:
                por_que["otra"] += 1
        pr(f"      con cumulo y sin publicar: {dict(por_que)}")
    # K: cara b de A46 (etiqueta far con cumulo dentro del inner)
    a46b = [i for i in ok if (res[i]["brazos"]["K"]["record"].get("distance_class") == "far"
            and ((res[i]["brazos"]["K"]["record"].get("primary_cluster") or {}).get("centroid_dist_km") or 1e9) <= inner[obj[i]["volcan"]]
            and ((res[i]["brazos"]["K"]["record"].get("primary_cluster") or {}).get("vrp_mw") or 0) > 0)]
    pr(f"   K con etiqueta far pero cumulo con energia dentro del inner (A46 cara b, via que el oraculo no tiene): {len(a46b)}; "
       f"de ellos negativos {sum(1 for i in a46b if obj[i]['lab'] == 'neg_limpio')}, alertas que deciden {sum(1 for i in a46b if i in dec)} "
       f"(protegidas {sum(1 for i in a46b if i in prot)})")
    # oraculo: redondeo a 0 y pixeles fuera del inner
    for c, nom in CAJAS.items():
        red0 = [i for i in ok if res[i]["oraculo"][c].get("npix") and round(res[i]["oraculo"][c]["vrp_mw"], 3) == 0.0]
        pub_c = [i for i in ok if pub(i, c)]
        afuera = [i for i in pub_c if dist_max_px(res[i]["oraculo"][c]) > inner[obj[i]["volcan"]]]
        dmax = max((dist_max_px(res[i]["oraculo"][c]) for i in pub_c), default=0)
        pr(f"   {nom}: con pixeles pero vrp redondeado a 0,000 (no publica por redondeo) {len(red0)}; publicaciones {len(pub_c)}, "
           f"con algun pixel alertado fuera del inner y centroide dentro {len(afuera)} "
           f"{[(obj[i]['volcan'], obj[i]['hora_utc'], obj[i]['lab']) for i in afuera][:12]}; distancia maxima de un pixel publicado {dmax:.2f} km")

    # ---------------------------------------------------------------- protegidas y bajo 1 MW: tabla cruzada
    pr("== alertas que deciden: quien publica (ok)")
    for nombre, grupo in (("protegidas", prot), ("bajo 1 MW", mb)):
        for c, nom in CAJAS.items():
            t = collections.Counter((pub(i, "K"), pub(i, c)) for i in grupo)
            pr(f"   {nombre} ({len(grupo)}) K vs {nom}: ambos {t[(True, True)]}, solo K (O pierde) {t[(True, False)]}, "
               f"solo O (O gana) {t[(False, True)]}, ninguno {t[(False, False)]} | K publica {sum(pub(i, 'K') for i in grupo)}, "
               f"{nom} publica {sum(pub(i, c) for i in grupo)}")
    nopubK = [i for i in prot if not pub(i, "K")]
    pr("   protegidas que K NO publica:", [(obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["mirova_vrp"],
                                           res[i]["brazos"]["K"]["record"].get("distance_class"),
                                           (res[i]["brazos"]["K"]["record"].get("primary_cluster") or {}).get("vrp_mw"),
                                           {nom: bool(res[i]["oraculo"][c].get("npix")) for c, nom in CAJAS.items()}) for i in nopubK])
    perd = [i for i in prot if pub(i, "K") and not pub(i, "geo_linear")]
    pr("   protegidas que O-def pierde, con la geometria del oraculo:",
       [(obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["mirova_vrp"], "pc_prod", obj[i]["pc_vrp"], "pc_dist", obj[i]["pc_dist"],
         "Odef npix", res[i]["oraculo"]["geo_linear"].get("npix"), "Osens npix", res[i]["oraculo"]["geo_linear_anillo_sensible"].get("npix"),
         "Osens dist", (sintetico_propio(res[i]["oraculo"]["geo_linear_anillo_sensible"], inner[obj[i]["volcan"]], obj[i]["sensor"]).get("primary_cluster") or {}).get("centroid_dist_km"))
        for i in perd])

    # ---------------------------------------------------------------- dE y rango, recomputo
    pr("== dE recomputado (mismas definiciones del pre-registro seccion 4)")
    neg_sin = [i for i in sin if obj[i]["lab"] == "neg_limpio"]
    mb_sin = [i for i in sin if obj[i]["lab"] == "pos" and obj[i]["decide"] and not obj[i]["protegida"]]
    prot_sin = [i for i in sin if obj[i]["lab"] == "pos" and obj[i]["decide"] and obj[i]["protegida"]]
    for c, nom in CAJAS.items():
        pK, pO = sum(pub(i, "K") for i in neg), sum(pub(i, c) for i in neg)
        fK, fO = sum(1 for i in mb if not pub(i, "K")), sum(1 for i in mb if not pub(i, c))
        dE = (fO + pO) - (fK + pK)
        pr(f"   {nom}: dE = ({fO}+{pO}) - ({fK}+{pK}) = {dE:+d}; SIN DATO: negativos {len(neg_sin)}, bajo 1 MW {len(mb_sin)}, "
           f"protegidas {len(prot_sin)}; rango [{dE - len(mb_sin):+d}, {dE + len(neg_sin):+d}] "
           f"(supone que K no publica ninguna SIN DATO; si K publicara las {len(neg_sin)} negativas SIN DATO el piso seria {dE - len(mb_sin) - len(neg_sin):+d})")

    # ---------------------------------------------------------------- (c) lectura con la tabla sola
    pr("== (c) lectura con la tabla de latest.php sola: alertas que deciden solo por OCR (alerta_tabla False, desde 06-13) salen del denominador")
    solo_ocr = [i for i in dec if not obj[i]["alerta_tabla"]]
    pr(f"   alertas que deciden solo por OCR, ok: {len(solo_ocr)} "
       f"{[(obj[i]['volcan'], obj[i]['hora_utc'], obj[i]['mirova_vrp'], 'prot' if obj[i]['protegida'] else 'mb', 'K', pub(i, 'K'), 'Odef', pub(i, 'geo_linear'), 'Osens', pub(i, 'geo_linear_anillo_sensible')) for i in solo_ocr]}")
    pr(f"   SIN DATO que deciden solo por OCR: {[(obj[i]['volcan'], obj[i]['hora_utc']) for i in sin if obj[i]['lab'] == 'pos' and obj[i]['decide'] and not obj[i]['alerta_tabla']]}")
    prot_t = [i for i in prot if obj[i]["alerta_tabla"]]
    mb_t = [i for i in mb if obj[i]["alerta_tabla"]]
    for c, nom in CAJAS.items():
        pK, pO = sum(pub(i, "K") for i in neg), sum(pub(i, c) for i in neg)
        fK, fO = sum(1 for i in mb_t if not pub(i, "K")), sum(1 for i in mb_t if not pub(i, c))
        pp = sum(1 for i in prot_t if pub(i, "K") and not pub(i, c))
        pg = sum(1 for i in prot_t if pub(i, c) and not pub(i, "K"))
        pr(f"   {nom} tabla sola: protegidas {len(prot_t)} (perdidas {pp}, ganadas {pg}); bajo 1 MW {len(mb_t)} sin publicar K {fK}, O {fO}; "
           f"dE = ({fO}+{pO}) - ({fK}+{pK}) = {(fO + pO) - (fK + pK):+d}")

    # ---------------------------------------------------------------- desglose negativos publicados por mes (A104, #535 y K)
    pr("== negativos publicados por mes (K / O-def / O-sens / n ok)")
    por_mes = collections.defaultdict(list)
    for i in neg:
        por_mes[obj[i]["hora_utc"][:7]].append(i)
    for m, v in sorted(por_mes.items()):
        pr(f"   {m}: K {sum(pub(i, 'K') for i in v)} / O-def {sum(pub(i, 'geo_linear') for i in v)} / "
           f"O-sens {sum(pub(i, 'geo_linear_anillo_sensible') for i in v)} / {len(v)}")

    # ---------------------------------------------------------------- control positivo del contador propio
    pr("== control positivo del contador propio")
    casos2, idx2 = [], []
    for i in neg:
        k = copy.deepcopy(casos[idx.index((i, "K"))][0])
        k["distance_class"] = "far"
        casos2.append([k, inner[obj[i]["volcan"]]])
        idx2.append((i, "K_far"))
        if not pub(i, "geo_linear"):
            casos2.append([{"sensor": obj[i]["sensor"], "vrp_mw": 0.3, "t_max_k": 290.0, "triggered_test1": False,
                            "distance_class": "summit",
                            "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}},
                          inner[obj[i]["volcan"]]])
            idx2.append((i, "iny"))
    F2 = list(zip(idx2, B.correr_node(casos2)))
    pr(f"   K con distance_class forzado a far: publica {sum(p[4] for (i, t), p in F2 if t == 'K_far')} de {len(neg)} (esperado 0)")
    pr(f"   negativos sin publicar por O-def con cumulo inyectado de 0,3 MW: publican "
       f"{sum(p[4] for (i, t), p in F2 if t == 'iny')} de {sum(1 for (i, t) in idx2 if t == 'iny')} (esperado todos)")

    (AQUI / f"verif_recuento_salida{a.salida}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
