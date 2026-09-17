# -*- coding: utf-8 -*-
"""S143: evaluador del A/B D22/D25 (VIIRS 375), escrito y probado ANTES de ver datos del A/B.

POR QUÉ EXISTE. El pre-registro `docs/PREREGISTRO_AB_D22_D25_S143.md` fija tres criterios y el
verificador limpio (`docs/PREREGISTRO_AB_D22_D25_S143_VERIFICADOR.md`, hallazgo 3) encontró que no
había un instrumento que los aplicara: `experiments/_s135_ab_d1d2/evaluar_ab.py` reconstruía el
predicado a mano (A97), tenía radios para seis volcanes, otra partición focal/nevado, pareo a 20 min
y la referencia de un snapshot local. Un evaluador escrito después de mirar resultados deja grados
de libertad que el pre-registro dice no tener. Este lo cierra antes.

EL FENÓMENO QUE MIDE. En un cono nevado, de noche, un foco sub-píxel puede quedar más frío que el
valle que lo rodea. Cada brazo cambia qué reglas deciden si ese foco se ve. El evaluador pregunta
tres cosas en las unidades en que el operador las vive (A91, A94):
  1. ¿el brazo deja de publicar alguna NOCHE que MIROVA alertó y que el control publica con el
     mismo objeto? (cero pérdidas; toda pérdida cuenta, hallazgo 7);
  2. ¿baja la publicación en PASADAS donde MIROVA miró y no vio nada (negativos limpios, A98)?
  3. ¿la magnitud que ve el operador se acerca a la de MIROVA, en las mismas PASADAS?

DECISIONES FIJADAS (cada una es un requisito del verificador; ver README.md):
  * "publica" = predicado del dashboard ejecutado con node desde frontend/index.html
    (`banco_paridad.correr_node`), nunca uno reconstruido (A97). Se guardan también `summit`,
    `valid`, `art` y `disp` para reportar la tasa de artefacto y la tasa previa al display
    (`summit && valid && disp > 0`) en negativos limpios (hallazgo 10, A72).
  * etiquetas `pos` / `neg_limpio` y pasadas diurnas: las de `banco_paridad` sin reescribir.
  * referencia MIROVA: CONS y OCR del remoto MendozaVolcanic/Mirova-v1 bajados por los sha de
    `experiments/_s143_preregistro/denominadores.json` (hallazgo 11), con el loader del banco.
  * mismo objeto (A93): los dos radios desde `mirova_center`; la diferencia de radios es una cota
    INFERIOR de la separación y no debe superar 0,55 km. Se aplica al control Y al brazo
    (hallazgo 2); se reporta además la pérdida sin filtro en el brazo.
  * cobertura pareja simétrica por `(datetime_utc, sensor)` y `product_version` (hallazgo 15).
  * bootstrap percentil 95 % estratificado por volcán, remuestreando noches dentro de cada volcán
    (hallazgo 14), con el margen de pasadas que decide el signo.
  * magnitud decisiva sobre las pasadas `pos` publicadas por AMBOS; n mínimo contado en las `pos`
    del control; una fila MIROVA por pasada, CONS antes que OCR (hallazgo 4).
  * estratos de `scripts/build_c2ab_windows.py:41-42`, siempre con desglose por volcán (hallazgo 13).

Read-only sobre el repo: no toca pipeline/, data/ ni banco_paridad (lo envuelve).

Uso:
    python experiments/_s143_evaluador/evaluar.py --dir <artefactos fusionados> --prefijo s142ab- \\
        --brazos _s142_ab_control _s142_ab_literal ... --control _s142_ab_control \\
        --volcanes Isluga Lascar ... --inicio 2026-06-01 --fin 2026-08-31 --out-json r.json --out-md r.md
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import os
import statistics
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import banco_paridad as bp  # noqa: E402
import build_c2ab_windows as _ventanas  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

PRESUPUESTO_COTA_KM = 0.55  # semidiagonal de la celda de 375 m + residuo por sensor (S135, AUDIT_S128.md:191)
B_DEFECTO = 10000
SEMILLA_DEFECTO = 143
N_MIN_MAGNITUD = 30
TOL_MAGNITUD = 0.05
DENOMINADORES = ROOT / "experiments" / "_s143_preregistro" / "denominadores.json"
DL_REFERENCIA = HERE / "_dl_referencia"
NOMBRES_REF = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv")


# ------------------------------------------------------------------ fuentes del repo
def estrato_de(vol):
    """Partición de `scripts/build_c2ab_windows.py:41-42` (la que manda el spec §5.1)."""
    if vol in _ventanas.FOCAL:
        return "focal"
    if vol in _ventanas.NEVADO:
        return "nevado"
    raise KeyError(f"{vol} no está en FOCAL ni NEVADO de build_c2ab_windows.py")


def radios(vols):
    """inner del dashboard (frontend/index.html, el que usa el predicado) y mirova_center de
    volcanoes.yaml. Se anota también el inner del yaml para ver si las dos fuentes difieren."""
    html = bp.inner_desde_html()
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        yml = {v["name"]: v for v in yaml.safe_load(fh)["volcanoes"]}
    out = {}
    for v in vols:
        if v not in html:
            raise KeyError(f"{v}: sin inner_radius_km en frontend/index.html")
        y = yml.get(v) or {}
        lat, lon = y.get("mirova_center_lat"), y.get("mirova_center_lon")
        if lat is None or lon is None:
            raise KeyError(f"{v}: sin mirova_center en volcanoes.yaml")
        out[v] = {"inner": float(html[v]), "mirova_center": (float(lat), float(lon)),
                  "inner_yaml": y.get("inner_radius_km")}
    return out


def hav(la1, lo1, la2, lo2):
    """Distancia sobre la esfera, en km (misma fórmula que evaluar_ab.py de S135)."""
    rt = 6371.0088
    p = math.radians
    dla, dlo = p(la2 - la1), p(lo2 - lo1)
    a = math.sin(dla / 2) ** 2 + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(dlo / 2) ** 2
    return 2 * rt * math.asin(math.sqrt(a))


# ------------------------------------------------------------------ artefactos y cobertura
def cargar_records(base, prefijo, brazo, vol):
    for cand in (Path(base) / f"{prefijo}{brazo}-{vol}" / f"{vol}.json",
                 Path(base) / brazo / f"{vol}.json"):
        if cand.exists():
            with open(cand, encoding="utf-8") as fh:
                d = json.load(fh)
            return d["records"] if isinstance(d, dict) else d
    return None


def claves_ventana(records, ventana):
    """{(datetime_utc, sensor): product_version} de TODOS los sensores en la ventana."""
    return {(r["datetime_utc"], r["sensor"]): r.get("product_version")
            for r in records if ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]}


def cobertura(claves, control, volcanes):
    """Diferencia simétrica de pasadas y product_version de cada brazo contra el control.

    `claves` = {brazo: {volcán: {(datetime_utc, sensor): product_version}}}. Un volcán es desparejo
    si en algún brazo falta el archivo, hay pasadas de menos o de más, o cambia product_version: sus
    «pérdidas» o «ganancias» serían del experimento, no del algoritmo (S135 chunk 1).
    """
    detalle, desparejos = {}, {}
    for vol in volcanes:
        base = claves.get(control, {}).get(vol)
        detalle[vol] = {}
        for brazo, por_vol in claves.items():
            if brazo == control:
                continue
            k = por_vol.get(vol)
            if base is None or k is None:
                detalle[vol][brazo] = {"archivo_faltante": True}
                desparejos.setdefault(vol, []).append(f"{brazo}: archivo faltante")
                continue
            comunes = base.keys() & k.keys()
            d = {"n_control": len(base), "n_brazo": len(k),
                 "solo_control": len(base.keys() - k.keys()),
                 "solo_brazo": len(k.keys() - base.keys()),
                 "product_version_distinto": sum(1 for c in comunes if base[c] != k[c])}
            detalle[vol][brazo] = d
            if d["solo_control"] or d["solo_brazo"] or d["product_version_distinto"]:
                desparejos.setdefault(vol, []).append(
                    f"{brazo}: solo_control {d['solo_control']}, solo_brazo {d['solo_brazo']}, "
                    f"product_version distinto {d['product_version_distinto']}")
    return detalle, desparejos


# ------------------------------------------------------------------ pasadas con el predicado node
def construir_pasadas(records_por_vol, coords, inner, ventana, buckets=("VIIRS375",)):
    """Misma selección de records y mismos casos que `banco_paridad.cargar_nuestros`, con el
    predicado del dashboard vía node. El test `test_cargador_reproduce_al_banco_de_paridad` vigila
    que no se separen. Una sola llamada a node por invocación."""
    pasadas, casos = [], []
    for vol, records in records_por_vol.items():
        for r in records:
            b = bp.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            if b not in buckets:
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            cen = None
            if pc.get("centroid_lat") is not None and pc.get("centroid_lon") is not None:
                cen = (float(pc["centroid_lat"]), float(pc["centroid_lon"]))
            pasadas.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                            "datetime_utc": r["datetime_utc"], "sensor": r.get("sensor"),
                            "clave": (vol, r["datetime_utc"], r.get("sensor")),
                            "product_version": r.get("product_version"), "cen": cen})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    if len(pred) != len(pasadas):
        raise RuntimeError(f"node devolvió {len(pred)} resultados para {len(pasadas)} pasadas")
    for p, o in zip(pasadas, pred):
        p["summit"], p["valid"], p["art"], p["disp"], p["pub"] = o[0], o[1], o[2], o[3], o[4]
        p["predisp"] = 1 if (o[0] and o[1] and (o[3] or 0) > 0) else 0
    return pasadas


def fila_mirova(filas, dt=None):
    """Una fila MIROVA por pasada: ALERTA con VRP > 0, CONS si existe, si no OCR (hallazgo 4).
    Entre varias de la misma fuente, la más cercana en tiempo."""
    cand = [f for f in filas if bp.es_alerta(f.get("tipo", "")) and (f.get("vrp_mw") or 0) > 0]
    for fuente in ("CONS", "OCR"):
        c = [f for f in cand if f.get("source") == fuente]
        if not c:
            continue
        if dt is None:
            return c[0]

        def lejania(f):
            t = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return abs((t - dt).total_seconds())
        return min(c, key=lejania)
    return None


def anotar_mirova(pasadas, por_vb):
    for p in pasadas:
        f = fila_mirova(bp.parear(por_vb.get((p["vol"], p["b"]), []), p["dt"]), p["dt"])
        p["mir_vrp"] = float(f["vrp_mw"]) if f else None
        p["mir_fuente"] = f["source"] if f else None


def noches_y_distancias(por_vb, noche_sensor, volcanes, bucket="VIIRS375"):
    """Noches con ALERTA nocturna de MIROVA en el sensor y distancias de esas alertas por noche."""
    noches = {v: {n for (vv, b, n), d in noche_sensor.items() if vv == v and b == bucket and d["alerta"]}
              for v in volcanes}
    dist = collections.defaultdict(list)
    for v in volcanes:
        for _, f in por_vb.get((v, bucket), []):
            if bp.es_alerta(f["tipo"]) and f.get("dist_km") is not None:
                dist[(v, f["fecha_utc"][:10])].append(float(f["dist_km"]))
    return noches, dict(dist)


# ------------------------------------------------------------------ criterio 1
def estado_noches(pasadas, noches_alerta, dist_noche, centros, presupuesto=PRESUPUESTO_COTA_KM):
    """Por volcán, sobre las noches con alerta nocturna de MIROVA:
      pub       noches en que se publica algo;
      pub_cota  noches en que se publica un objeto que pasa la cota A93;
      sin_cota  noches de pub_cota aceptadas sin poder calcular la cota (sin distancia o centroide);
      descartadas {noche: cota mínima} cuando se publica pero ningún objeto pasa la cota."""
    vols = set(noches_alerta) | {p["vol"] for p in pasadas}
    out = {v: {"pub_cota": set(), "pub": set(), "descartadas": {}, "sin_cota": set()} for v in vols}
    grupos = collections.defaultdict(list)
    for p in pasadas:
        if p["pub"] and p["noche"] in noches_alerta.get(p["vol"], set()):
            grupos[(p["vol"], p["noche"])].append(p)
    for (v, n), ps in grupos.items():
        e = out[v]
        e["pub"].add(n)
        dm = dist_noche.get((v, n)) or []
        centro = centros[v]
        pasa_con_cota, pasa_sin_cota, cotas = False, False, []
        for p in ps:
            if p.get("cen") is None or not dm:
                pasa_sin_cota = True
                continue
            nuestra = hav(centro[0], centro[1], p["cen"][0], p["cen"][1])
            cota = min(abs(nuestra - x) for x in dm)
            cotas.append(cota)
            if cota <= presupuesto:
                pasa_con_cota = True
        if pasa_con_cota or pasa_sin_cota:
            e["pub_cota"].add(n)
            if not pasa_con_cota:
                e["sin_cota"].add(n)
        else:
            e["descartadas"][n] = round(min(cotas), 3)
    return out


def _lista(pares):
    return [{"volcan": v, "fecha": f} for v, f in sorted(pares)]


def criterio1(est_ctrl, est_brazo, estrato_fn=None):
    """Pérdida = noche confirmada (el control publica con la cota) en que el brazo NO publica un
    objeto que pase la MISMA cota. Toda pérdida cuenta; umbral 0."""
    perd, perd_sf, gan, gan_sf, por_vol = [], [], [], [], {}
    vacio = {"pub_cota": set(), "pub": set()}
    for v in sorted(est_ctrl):
        c, b = est_ctrl[v], est_brazo.get(v, vacio)
        conf = c["pub_cota"]
        pv = {"confirmadas": len(conf),
              "perdidas": sorted(conf - b["pub_cota"]),
              "perdidas_sin_filtro_brazo": sorted(conf - b["pub"]),
              "ganancias": sorted(b["pub_cota"] - conf),
              "ganancias_sin_filtro": sorted(b["pub"] - c["pub"])}
        por_vol[v] = pv
        perd += [(v, f) for f in pv["perdidas"]]
        perd_sf += [(v, f) for f in pv["perdidas_sin_filtro_brazo"]]
        gan += [(v, f) for f in pv["ganancias"]]
        gan_sf += [(v, f) for f in pv["ganancias_sin_filtro"]]
    r = {"perdidas": _lista(perd), "n_perdidas": len(perd),
         "perdidas_sin_filtro_brazo": _lista(perd_sf), "n_perdidas_sin_filtro_brazo": len(perd_sf),
         "ganancias": _lista(gan), "n_ganancias": len(gan),
         "ganancias_sin_filtro": _lista(gan_sf), "n_ganancias_sin_filtro": len(gan_sf),
         "por_volcan": por_vol, "cumple": len(perd) == 0}
    if estrato_fn is not None:
        pe = collections.defaultdict(lambda: {"confirmadas": 0, "perdidas": 0,
                                              "perdidas_sin_filtro_brazo": 0, "ganancias": 0})
        for v, pv in por_vol.items():
            e = pe[estrato_fn(v)]
            e["confirmadas"] += pv["confirmadas"]
            e["perdidas"] += len(pv["perdidas"])
            e["perdidas_sin_filtro_brazo"] += len(pv["perdidas_sin_filtro_brazo"])
            e["ganancias"] += len(pv["ganancias"])
        r["por_estrato"] = dict(pe)
    return r


def resumen_confirmadas(est_ctrl, estrato_fn):
    por_vol = {v: len(e["pub_cota"]) for v, e in sorted(est_ctrl.items())}
    pe = collections.Counter()
    for v, n in por_vol.items():
        pe[estrato_fn(v)] += n
    return {"total": sum(por_vol.values()), "por_volcan": por_vol, "por_estrato": dict(pe),
            "fechas": {v: sorted(e["pub_cota"]) for v, e in sorted(est_ctrl.items())},
            "aceptadas_sin_cota_calculable": {v: sorted(e["sin_cota"]) for v, e in sorted(est_ctrl.items()) if e["sin_cota"]},
            "coincidencias_de_fecha_descartadas": {v: dict(sorted(e["descartadas"].items()))
                                                   for v, e in sorted(est_ctrl.items()) if e["descartadas"]},
            "noches_publicadas_sin_filtro": {v: len(e["pub"]) for v, e in sorted(est_ctrl.items())}}


def seguimiento(estados, lista):
    """Estado de noches puntuales (p. ej. las 12 de S135) en cada brazo."""
    out = []
    for it in lista:
        fila = {"volcan": it["volcan"], "fecha": it["fecha"]}
        for brazo, est in estados.items():
            e = est.get(it["volcan"], {})
            fila[brazo] = {"publica_cota": it["fecha"] in e.get("pub_cota", set()),
                           "publica": it["fecha"] in e.get("pub", set())}
        out.append(fila)
    return out


# ------------------------------------------------------------------ criterio 2
def bootstrap_estratificado(grupos, B=B_DEFECTO, semilla=SEMILLA_DEFECTO):
    """IC percentil 95 % de (Σ pub_brazo − Σ pub_control) / Σ n, remuestreando NOCHES con
    reposición DENTRO de cada volcán. `grupos` = {volcán: [(n, pub_control, pub_brazo) por noche]}."""
    rng = np.random.default_rng(semilla)
    tot_n = np.zeros(B)
    tot_d = np.zeros(B)
    for vol in sorted(grupos):
        arr = np.asarray(grupos[vol], dtype=float)
        k = len(arr)
        if k == 0:
            continue
        sel = arr[rng.integers(0, k, size=(B, k))]
        tot_n += sel[:, :, 0].sum(axis=1)
        tot_d += (sel[:, :, 2] - sel[:, :, 1]).sum(axis=1)
    if not np.all(tot_n > 0):
        return (None, None)
    lo, hi = np.percentile(tot_d / tot_n, [2.5, 97.5])
    return (float(lo), float(hi))


def _bloque2(pares, B, semilla):
    grupos = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
    sb = sc = 0
    for c, b in pares:
        g = grupos[c["vol"]][c["noche"]]
        g[0] += 1
        g[1] += c["pub"]
        g[2] += b["pub"]
        sb += int(b["pub"] and not c["pub"])
        sc += int(c["pub"] and not b["pub"])
    n = len(pares)
    pub_c = sum(c["pub"] for c, _ in pares)
    pub_b = sum(b["pub"] for _, b in pares)
    g2 = {v: [tuple(x) for x in noches.values()] for v, noches in grupos.items()}
    return {"n": n, "n_noches": sum(len(x) for x in g2.values()),
            "pub_control": pub_c, "pub_brazo": pub_b,
            "tasa_control": pub_c / n if n else None, "tasa_brazo": pub_b / n if n else None,
            "dif": (pub_b - pub_c) / n if n else None,
            "ic95": list(bootstrap_estratificado(g2, B, semilla)) if n else [None, None],
            "solo_brazo": sb, "solo_control": sc, "margen_signo": abs(sb - sc)}


def criterio2(pas_ctrl, pas_brazo, estrato_fn, B=B_DEFECTO, semilla=SEMILLA_DEFECTO):
    """Diferencia de tasa de publicación (brazo − control) en negativos limpios, sobre las MISMAS
    pasadas. `margen_signo` = pasadas discordantes netas que deciden el signo (hallazgo 14)."""
    idx = {p["clave"]: p for p in pas_brazo}
    pares = [(c, idx[c["clave"]]) for c in pas_ctrl if c["lab"] == "neg_limpio" and c["clave"] in idx]
    r = {"total": _bloque2(pares, B, semilla), "por_estrato": {}, "por_volcan": {}}
    for est in sorted({estrato_fn(c["vol"]) for c, _ in pares}):
        r["por_estrato"][est] = _bloque2([x for x in pares if estrato_fn(x[0]["vol"]) == est], B, semilla)
    for v in sorted({c["vol"] for c, _ in pares}):
        r["por_volcan"][v] = _bloque2([x for x in pares if x[0]["vol"] == v], B, semilla)
    n = len(pares)

    def tasa(sel, campo):
        return sum(p[campo] for p in sel) / n if n else None
    ctrl_sel, br_sel = [c for c, _ in pares], [b for _, b in pares]
    r["acompanantes_neg_limpio"] = {
        "tasa_art_control": tasa(ctrl_sel, "art"), "tasa_art_brazo": tasa(br_sel, "art"),
        "tasa_predisplay_control": tasa(ctrl_sel, "predisp"),
        "tasa_predisplay_brazo": tasa(br_sel, "predisp"),
        "definicion_predisplay": "summit && valid && disp > 0 (antes de isThermalArtifact)"}
    ac = r["acompanantes_neg_limpio"]
    r["acompanantes_neg_limpio"]["art_sube_en_brazo"] = (
        None if not n else ac["tasa_art_brazo"] > ac["tasa_art_control"])
    hi = r["total"]["ic95"][1]
    r["cumple"] = bool(n and hi is not None and hi < 0
                       and all(e["dif"] <= 0 for e in r["por_estrato"].values() if e["n"]))
    return r


# ------------------------------------------------------------------ criterio 3
def _med(xs):
    return statistics.median(xs) if xs else None


def _bloque3(pos_ctrl, idx_b):
    dec_c, dec_b, inf_c, inf_b = [], [], [], []
    for c in pos_ctrl:
        m = c.get("mir_vrp")
        b = idx_b.get(c["clave"])
        if not m or m <= 0:
            continue
        if c["pub"] and c["disp"] > 0:
            inf_c.append(c["disp"] / m)
        if b is not None and b["pub"] and b["disp"] > 0:
            inf_b.append(b["disp"] / m)
        if b is not None and c["pub"] and b["pub"] and c["disp"] > 0 and b["disp"] > 0:
            dec_c.append(c["disp"] / m)
            dec_b.append(b["disp"] / m)
    mc, mb = _med(dec_c), _med(dec_b)
    return {"n_pos_control": len(pos_ctrl), "n_pares_decisivo": len(dec_c),
            "mediana_control_decisivo": mc, "mediana_brazo_decisivo": mb,
            "dist_a_1_control": abs(mc - 1) if mc is not None else None,
            "dist_a_1_brazo": abs(mb - 1) if mb is not None else None,
            "n_control_informativo": len(inf_c), "mediana_control_informativo": _med(inf_c),
            "n_brazo_informativo": len(inf_b), "mediana_brazo_informativo": _med(inf_b)}


def criterio3(pas_ctrl, pas_brazo, estrato_fn, n_min=N_MIN_MAGNITUD, tol=TOL_MAGNITUD):
    """Razón magnitud del operador (`disp`) / VRP MIROVA en pasadas `pos`. Decide sobre las
    publicadas por AMBOS; los conjuntos de cada brazo se reportan como informativos."""
    idx = {p["clave"]: p for p in pas_brazo}
    pos = [c for c in pas_ctrl if c["lab"] == "pos"]
    r = {"total": _bloque3(pos, idx), "por_estrato": {}, "por_volcan": {}}
    for est in sorted({estrato_fn(c["vol"]) for c in pos}):
        r["por_estrato"][est] = _bloque3([c for c in pos if estrato_fn(c["vol"]) == est], idx)
    peor = []
    for v in sorted({c["vol"] for c in pos}):
        blq = _bloque3([c for c in pos if c["vol"] == v], idx)
        blq["evaluado"] = blq["n_pos_control"] >= n_min
        if blq["evaluado"]:
            blq["empeora_mas_de_tolerancia"] = (
                blq["n_pares_decisivo"] == 0
                or blq["dist_a_1_brazo"] - blq["dist_a_1_control"] > tol + 1e-12)
        else:
            blq["empeora_mas_de_tolerancia"] = None
        if blq["empeora_mas_de_tolerancia"]:
            peor.append(v)
        r["por_volcan"][v] = blq
    t = r["total"]
    r["volcanes_que_empeoran"] = peor
    r["cumple"] = bool(t["n_pares_decisivo"] and t["dist_a_1_brazo"] <= t["dist_a_1_control"] + 1e-12
                       and not peor)
    return r


# ------------------------------------------------------------------ procedencia y referencia
def json_default(o):
    if isinstance(o, set):
        return sorted(o)
    if isinstance(o, tuple):
        return list(o)
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"no serializable: {type(o)}")


def _git(*args):
    o = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return o.stdout.strip() if o.returncode == 0 else None


def procedencia_archivo(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    commit = _git("log", "-1", "--format=%H", "--", rel) or None
    modificado = bool(_git("status", "--porcelain", "--", rel))
    return {"archivo": rel, "commit": commit, "modificado_sin_commit": modificado,
            "blob": _git("hash-object", rel)}


def referencia_por_sha(denominadores=DENOMINADORES, dest=DL_REFERENCIA):
    """Baja CONS y OCR de Mirova-v1 fijados a los sha del pre-registro (cache en _dl_referencia)."""
    with open(denominadores, encoding="utf-8") as fh:
        shas = json.load(fh)["meta"]["referencia"]
    dest.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre in NOMBRES_REF:
        sha = shas[nombre]
        destino = dest / f"{sha[:12]}_{nombre}"
        if not destino.exists() or destino.stat().st_size == 0:
            tmp = destino.with_suffix(".parcial")
            urllib.request.urlretrieve(rmu.URL_RAW.format(sha=sha, nombre=nombre), tmp)
            os.replace(tmp, destino)
        rutas[nombre] = destino
    return rutas, {k: shas[k] for k in NOMBRES_REF}


# ------------------------------------------------------------------ orquestación
def evaluar(a):
    ventana = (a.inicio, a.fin)
    vols = list(a.volcanes)
    brazos = list(a.brazos)
    if a.control not in brazos:
        brazos = [a.control] + brazos
    estratos = {v: estrato_de(v) for v in vols}

    if a.ref_cons and a.ref_ocr:
        cons, ocr = Path(a.ref_cons), Path(a.ref_ocr)
        ref_proc = {"fuente": "archivos locales", "cons": str(cons), "ocr": str(ocr),
                    "blob_cons": bp.sha_git(cons), "blob_ocr": bp.sha_git(ocr)}
    else:
        rutas, shas = referencia_por_sha(Path(a.denominadores))
        cons, ocr = rutas[NOMBRES_REF[0]], rutas[NOMBRES_REF[1]]
        ref_proc = {"fuente": "remoto MendozaVolcanic/Mirova-v1 por sha", "commit_por_archivo": shas,
                    "sha_leido_de": os.path.relpath(a.denominadores, ROOT).replace("\\", "/")}
    ref_proc["respaldo_20260408_blob"] = bp.sha_git(bp.RESPALDO_20260408)

    coords = bp._coords_por_volcan()
    rad = radios(vols)
    inner = {v: rad[v]["inner"] for v in vols}
    centros = {v: rad[v]["mirova_center"] for v in vols}
    filas = bp.cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
    noches_alerta, dist_noche = noches_y_distancias(por_vb, noche_sensor, vols)

    records, claves = {}, {}
    for brazo in brazos:
        records[brazo], claves[brazo] = {}, {}
        for v in vols:
            rs = cargar_records(a.dir, a.prefijo, brazo, v)
            if rs is not None:
                records[brazo][v] = rs
                claves[brazo][v] = claves_ventana(rs, ventana)
    det_cob, desparejos = cobertura(claves, a.control, vols)
    if a.control not in claves or any(v not in claves[a.control] for v in vols):
        for v in vols:
            if v not in claves.get(a.control, {}):
                desparejos.setdefault(v, []).append("control: archivo faltante")
    evaluados = [v for v in vols if v not in desparejos]

    pasadas, estados = {}, {}
    for brazo in brazos:
        ps = construir_pasadas({v: records[brazo][v] for v in evaluados}, coords, inner, ventana)
        bp.etiquetar(ps, por_vb, noche_sensor, noche_volcan)
        anotar_mirova(ps, por_vb)
        pasadas[brazo] = ps
        estados[brazo] = estado_noches(ps, {v: noches_alerta[v] for v in evaluados}, dist_noche,
                                       centros, a.cota_km)

    est_fn = estratos.get
    pc = pasadas[a.control]
    neg_c = [p for p in pc if p["lab"] == "neg_limpio"]
    res = {
        "meta": {"ventana": list(ventana), "brazos": brazos, "control": a.control, "volcanes": vols,
                 "volcanes_evaluados": evaluados, "estratos": estratos,
                 "estratos_fuente": "scripts/build_c2ab_windows.py:41-42",
                 "radios": {v: {"inner_dashboard": rad[v]["inner"], "inner_yaml": rad[v]["inner_yaml"],
                                "mirova_center": list(rad[v]["mirova_center"])} for v in vols},
                 "dir_artefactos": str(a.dir), "prefijo": a.prefijo,
                 "procedencia": {"evaluador": procedencia_archivo(Path(__file__)),
                                 "banco_paridad": procedencia_archivo(ROOT / "scripts" / "banco_paridad.py"),
                                 "sha_index_html": bp.sha_git(bp.HTML), "referencia": ref_proc},
                 "parametros": {"cota_km": a.cota_km, "tol_pareo_s": bp.TOL_S, "B": a.B,
                                "semilla": a.semilla, "n_min_magnitud": a.n_min, "tol_magnitud": a.tol_magnitud},
                 "n_filas_referencia_nocturnas": n_ref,
                 "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "cobertura": {"detalle": det_cob, "excluidos": desparejos,
                      "n_pasadas_v375_nocturnas": {b: collections.Counter(p["vol"] for p in ps)
                                                   for b, ps in pasadas.items()}},
        "noches_confirmadas": resumen_confirmadas(estados[a.control], est_fn),
        "control": {"etiquetas_v375": collections.Counter(p["lab"] for p in pc),
                    "neg_limpio_n": len(neg_c),
                    "neg_limpio_tasa_publica": (sum(p["pub"] for p in neg_c) / len(neg_c)) if neg_c else None,
                    "neg_limpio_tasa_art": (sum(p["art"] for p in neg_c) / len(neg_c)) if neg_c else None,
                    "neg_limpio_tasa_predisplay": (sum(p["predisp"] for p in neg_c) / len(neg_c)) if neg_c else None,
                    "noches_con_alerta_nocturna_v375": {v: len(noches_alerta[v]) for v in evaluados}},
        "brazos": {},
    }
    for brazo in brazos:
        if brazo == a.control:
            continue
        res["brazos"][brazo] = {
            "criterio1": criterio1(estados[a.control], estados[brazo], est_fn),
            "criterio2": criterio2(pc, pasadas[brazo], est_fn, a.B, a.semilla),
            "criterio3": criterio3(pc, pasadas[brazo], est_fn, a.n_min, a.tol_magnitud)}
        b = res["brazos"][brazo]
        b["cumple_1_2_3"] = bool(b["criterio1"]["cumple"] and b["criterio2"]["cumple"]
                                 and b["criterio3"]["cumple"])
    # control del instrumento: el control contra sí mismo no pierde, no gana y no cambia la tasa
    auto1 = criterio1(estados[a.control], estados[a.control])
    auto2 = criterio2(pc, pc, est_fn, B=200, semilla=a.semilla)
    ident = bp.control_identidad_predicado()
    res["controles_instrumento"] = {
        "identidad_predicado_node": ident == ([0, 1, 1, 1, 0], [1, 0]),
        "control_contra_si_mismo": {"perdidas": auto1["n_perdidas"], "ganancias": auto1["n_ganancias"],
                                    "dif_neg_limpio": auto2["total"]["dif"]}}
    if a.seguimiento:
        with open(a.seguimiento, encoding="utf-8") as fh:
            lista = json.load(fh)
        res["seguimiento"] = seguimiento(estados, lista)
    fusion = Path(a.dir) / "fusion_informe.json"
    if fusion.exists():
        with open(fusion, encoding="utf-8") as fh:
            fi = json.load(fh)
        res["meta"]["fusion"] = {"tramos": fi.get("tramos"), "conflictos": len(fi.get("conflictos", [])),
                                 "faltantes": len(fi.get("faltantes", []))}
    return json.loads(json.dumps(res, default=json_default))


# ------------------------------------------------------------------ informe
def _f(x, nd=3):
    if x is None:
        return "sin dato"
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{nd}f}".replace(".", ",")


def _ic(ic):
    return f"[{_f(ic[0])}; {_f(ic[1])}]" if ic and ic[0] is not None else "sin dato"


def informe_markdown(res):
    """Informe generado desde el JSON: ningún número escrito a mano."""
    m = res["meta"]
    L = [f"# Evaluación del A/B: {', '.join(b for b in m['brazos'] if b != m['control'])} contra {m['control']}",
         "",
         f"> Generado por `experiments/_s143_evaluador/evaluar.py` el {m.get('generado_utc', 'sin fecha')}. "
         f"Ventana {m['ventana'][0]} a {m['ventana'][1]}. Todos los números salen del JSON de resultados.",
         ""]
    pr = m.get("procedencia") or {}
    if pr:
        L += ["## Procedencia", "", "```", json.dumps(pr, indent=1, ensure_ascii=False), "```", ""]
    cob = res.get("cobertura") or {}
    L += ["## Cobertura pareja", "",
          f"Volcanes pedidos: {', '.join(m['volcanes'])}. Evaluados: {', '.join(m['volcanes_evaluados']) or 'ninguno'}.", ""]
    if cob.get("excluidos"):
        L.append("Excluidos del veredicto (cobertura despareja o archivo faltante):")
        for v, mot in cob["excluidos"].items():
            L.append(f"- {v}: {'; '.join(mot)}")
        L.append("")
    nc = res.get("noches_confirmadas") or {}
    if nc:
        L += ["## Noches confirmadas (criterio 1)", "",
              f"Total: **{nc['total']}**. Por estrato: "
              + ", ".join(f"{k} {v}" for k, v in sorted(nc.get("por_estrato", {}).items())) + ".", "",
              "| volcán | estrato | confirmadas | publicadas sin filtro | aceptadas sin cota calculable | coincidencias de fecha descartadas |",
              "|---|---|---|---|---|---|"]
        for v, n in nc["por_volcan"].items():
            L.append(f"| {v} | {m['estratos'].get(v, '')} | {n} | {nc.get('noches_publicadas_sin_filtro', {}).get(v, 'sin dato')} | "
                     f"{len(nc.get('aceptadas_sin_cota_calculable', {}).get(v, []))} | "
                     f"{len(nc.get('coincidencias_de_fecha_descartadas', {}).get(v, {}))} |")
        L.append("")
    ctl = res.get("control")
    if ctl:
        L += ["## Línea base del control en negativos limpios", "",
              f"n = {ctl['neg_limpio_n']}; publica {_f(ctl['neg_limpio_tasa_publica'])}; "
              f"artefacto {_f(ctl['neg_limpio_tasa_art'])}; previa al display {_f(ctl['neg_limpio_tasa_predisplay'])}.", ""]
    for brazo, b in (res.get("brazos") or {}).items():
        c1, c2, c3 = b["criterio1"], b["criterio2"], b["criterio3"]
        L += [f"## Brazo {brazo}", ""]
        if "cumple_1_2_3" in b:
            L += [f"Cumple los tres criterios: **{_f(b['cumple_1_2_3'])}**.", ""]
        L += ["### Criterio 1: cero noches perdidas", "",
              f"Pérdidas (misma cota en el brazo): **{c1['n_perdidas']}**; sin filtro en el brazo: "
              f"{c1['n_perdidas_sin_filtro_brazo']}; ganancias: {c1['n_ganancias']} "
              f"(sin filtro {c1['n_ganancias_sin_filtro']}). Cumple: **{_f(c1['cumple'])}**.", "",
              "| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |", "|---|---|---|---|---|"]
        for v, pv in c1["por_volcan"].items():
            L.append(f"| {v} | {pv['confirmadas']} | {len(pv['perdidas'])} | {len(pv['perdidas_sin_filtro_brazo'])} | {len(pv['ganancias'])} |")
        if c1["perdidas"]:
            L += ["", "Noches perdidas: " + ", ".join(f"{p['volcan']} {p['fecha']}" for p in c1["perdidas"]) + "."]
        if c1["perdidas_sin_filtro_brazo"]:
            L += ["", "Perdidas sin filtro en el brazo: " + ", ".join(f"{p['volcan']} {p['fecha']}" for p in c1["perdidas_sin_filtro_brazo"]) + "."]
        L += ["", "### Criterio 2: publicación en negativos limpios (brazo menos control)", "",
              f"Cumple: **{_f(c2['cumple'])}**.", "",
              "| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        filas = [("total", c2["total"])] + [(f"estrato {k}", v) for k, v in c2["por_estrato"].items()] \
            + [(k, v) for k, v in c2["por_volcan"].items()]
        for nom, e in filas:
            L.append(f"| {nom} | {e['n']} | {e['n_noches']} | {_f(e['tasa_control'])} | {_f(e['tasa_brazo'])} | "
                     f"{_f(e['dif'])} | {_ic(e['ic95'])} | {e['solo_brazo']} | {e['solo_control']} | {e['margen_signo']} |")
        ac = c2["acompanantes_neg_limpio"]
        L += ["", f"Acompañantes: artefacto control {_f(ac['tasa_art_control'])}, brazo {_f(ac['tasa_art_brazo'])} "
              f"(sube en el brazo: {_f(ac['art_sube_en_brazo'])}); previa al display control "
              f"{_f(ac['tasa_predisplay_control'])}, brazo {_f(ac['tasa_predisplay_brazo'])}.", "",
              "### Criterio 3: magnitud del operador sobre VRP de MIROVA", "",
              f"Cumple: **{_f(c3['cumple'])}**. Volcanes que empeoran más de la tolerancia: "
              f"{', '.join(c3['volcanes_que_empeoran']) or 'ninguno'}.", "",
              "| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |",
              "|---|---|---|---|---|---|---|---|"]
        filas3 = [("total", c3["total"])] + [(f"estrato {k}", v) for k, v in c3["por_estrato"].items()] \
            + [(k, v) for k, v in c3["por_volcan"].items()]
        for nom, e in filas3:
            L.append(f"| {nom} | {e['n_pos_control']} | {e['n_pares_decisivo']} | {_f(e['mediana_control_decisivo'])} | "
                     f"{_f(e['mediana_brazo_decisivo'])} | {_f(e.get('evaluado')) if 'evaluado' in e else ''} | "
                     f"{e['n_control_informativo']}, {_f(e['mediana_control_informativo'])} | "
                     f"{e['n_brazo_informativo']}, {_f(e['mediana_brazo_informativo'])} |")
        L.append("")
    seg = res.get("seguimiento")
    if seg:
        brs = [k for k in seg[0] if k not in ("volcan", "fecha")]
        L += ["## Seguimiento de noches puntuales", "",
              "Celda: publica con cota / publica sin filtro.", "",
              "| volcán | fecha | " + " | ".join(brs) + " |", "|---|---|" + "---|" * len(brs)]
        for s in seg:
            L.append(f"| {s['volcan']} | {s['fecha']} | " + " | ".join(
                f"{_f(s[b]['publica_cota'])} / {_f(s[b]['publica'])}" for b in brs) + " |")
        L.append("")
    ci = res.get("controles_instrumento")
    if ci:
        L += ["## Controles del instrumento", "", "```", json.dumps(ci, indent=1, ensure_ascii=False), "```", ""]
    # red de seguridad: el proyecto no admite guiones largos ni medios en ningún texto
    return "\n".join(L).replace(chr(8212), ",").replace(chr(8211), ",")


def main(argv=None):
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True, help="artefactos fusionados (salida de fusionar.py)")
    ap.add_argument("--prefijo", default="", help="prefijo de las carpetas, p. ej. 's142ab-'")
    ap.add_argument("--brazos", nargs="+", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--volcanes", nargs="+", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--denominadores", default=str(DENOMINADORES),
                    help="JSON con meta.referencia (sha de CONS y OCR)")
    ap.add_argument("--ref-cons", default=None, help="CSV CONS local (sólo sin red; se anota el blob)")
    ap.add_argument("--ref-ocr", default=None)
    ap.add_argument("--B", type=int, default=B_DEFECTO)
    ap.add_argument("--semilla", type=int, default=SEMILLA_DEFECTO)
    ap.add_argument("--n-min", type=int, default=N_MIN_MAGNITUD)
    ap.add_argument("--tol-magnitud", type=float, default=TOL_MAGNITUD)
    ap.add_argument("--cota-km", type=float, default=PRESUPUESTO_COTA_KM)
    ap.add_argument("--seguimiento", default=None, help="JSON [{volcan, fecha}] de noches a seguir")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", default=None)
    a = ap.parse_args(argv)
    res = evaluar(a)
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(informe_markdown(res), encoding="utf-8")
    print(f"noches confirmadas: {res['noches_confirmadas']['total']} {res['noches_confirmadas']['por_volcan']}")
    for b, r in res["brazos"].items():
        print(f"{b}: perdidas {r['criterio1']['n_perdidas']} (sin filtro {r['criterio1']['n_perdidas_sin_filtro_brazo']}), "
              f"dif neg {r['criterio2']['total']['dif']} IC {r['criterio2']['total']['ic95']}, "
              f"magnitud {r['criterio3']['total']['mediana_control_decisivo']} -> {r['criterio3']['total']['mediana_brazo_decisivo']}")
    print(f"-> {a.out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
