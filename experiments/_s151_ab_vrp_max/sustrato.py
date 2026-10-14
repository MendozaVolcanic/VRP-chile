# -*- coding: utf-8 -*-
"""Sustrato del A/B `vrp_max` contra `vent_anchored` (tarea 1.4 del loop), sobre los datos ya en disco.

EL FENOMENO. En el recuadro de 25 km de un volcan puede haber mas de una fuente de calor de noche: el crater y,
por ejemplo, un incendio, un salar que guarda calor o un campo geotermal. MIROVA informa UNA por pasada; segun
la decision de Nicolas (2026-10-09) la de mayor energia. Nuestra replica elige el cumulo pegado al crater
(`vent_anchored`). Las dos reglas dan lo mismo cuando no hay calor lejano, o cuando el lejano es mas debil que
el del crater. Divergen solo en las pasadas con un cumulo lejano MAS FUERTE que el del crater.

EL MECANISMO. `pipeline/clustering.py::cluster_hotspots` ya tiene la estrategia "vrp_max"; se usa cuando
`ENABLE_VENT_ANCHORED_CLUSTERING` es False. Pero la seleccion no es el ultimo paso: si el Test 1 dispara en el
crater y el pixel mas energetico de la escena esta lejos, la Regla D (`resolve_test1_source_priority`, primera
rama) le da la fuente al Test 1 y reemplaza el cumulo por el del crater, y el ancla honesta
(`pipeline/anchor.py::resolve_honest_anchor`) pone la posicion en el crater. En esas pasadas apagar el flag no
cambia nada. Y el tablero (`mirovaEqVrp`) no publica un cumulo fuera del `inner_radius`: si `vrp_max` elige el
lejano, la pasada queda en silencio en el tablero.

QUE CUENTA. Para cada pasada nocturna de los 11 Tier A (2026-03-01 a 2026-10-09) que hoy publica, si apagar el
flag podria silenciarla, con tres grados:
  * seguro:   el pixel lejano mas energetico pesa mas que la suma de los pixeles del crater (el cumulo lejano
              gana por cualquier forma de agrupar);
  * estimado: agrupando los pixeles guardados por cercania (umbral validado por el control C1), el cumulo de
              mayor energia queda fuera del inner_radius; se confirma con el predicado del tablero (node);
  * posible:  la suma de los pixeles lejanos pesa mas que el pixel mas energetico del crater (techo).
  Aparte: las protegidas por la Regla D (no cambian con el flag; si con el cambio de codigo prerequisito) y las
  no observables (el record solo guarda los pixeles del Test 1 o llego al tope de 100 pixeles).
Y el universo de la tarea: las 359 filas FALSO_POSITIVO nocturnas de la tabla (VERIFICADOR_DATOS D2).

CONTROLES (pueden fallar):
  C1 reproduccion: la regla `vent_anchored` reconstruida desde `anomaly_pixels` debe reproducir el
     `primary_cluster` guardado (centroide a 20 m y mismo numero de pixeles) en al menos 90 % de los records
     reconstruibles. Si no, el "estimado" no vale y solo se informan las cotas.
  C2 enriquecimiento: si los cumulos lejanos de nuestras escenas son los objetos que MIROVA lista lejos, la
     tasa de "seguro" en far_ref tiene que superar a la de neg_limpio. Si no la supera, el sustrato mide calor
     lejano que MIROVA no ve y la prediccion del A/B cambia de signo.
  C3 sintetico: un record con un cumulo lejano mas fuerte tiene que dar "seguro"; uno sin lejano, "sin_lejano";
     uno con Test 1 y pixel maximo lejano, "regla_D". Si falla, el script aborta.
  C4 identidad del predicado: los casos del guard S139 (`bp.control_identidad_predicado`).

Uso: python experiments/_s151_ab_vrp_max/sustrato.py   (lee data/mirova_equivalent y el snapshot de la referencia)
Salida: sustrato_salida.txt y sustrato_salida.json en esta carpeta.
"""
from __future__ import annotations

import collections
import copy
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comun as C  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402

VENTANA = ("2026-03-01", "2026-10-09")
NOMINAL_KM = {"VIIRS375": 0.375, "VIIRS750": 0.75, "MODIS": 1.0}
FACTORES = (1.5, 2.2, 3.0)   # umbral de agrupacion = factor x pixel nominal; C1 elige con los datos
UMBRAL_C1 = 0.90
TOL_CENTRO_KM = 0.02


def agrupar(pix, ancla, thr_km):
    """Union-find por cercania (aproxima la conexidad 8 sin los indices de la grilla)."""
    n = len(pix)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if C.haversine_km(pix[i]["lat"], pix[i]["lon"], pix[j]["lat"], pix[j]["lon"]) <= thr_km:
                par[f(i)] = f(j)
    g = collections.defaultdict(list)
    for i in range(n):
        g[f(i)].append(pix[i])
    out = []
    for ps in g.values():
        la = sum(p["lat"] for p in ps) / len(ps)
        lo = sum(p["lon"] for p in ps) / len(ps)
        out.append({"n_pixels": len(ps), "centroid_lat": la, "centroid_lon": lo,
                    "centroid_dist_km": C.haversine_km(la, lo, ancla[0], ancla[1]),
                    "vrp_mw": sum(p.get("vrp_mw") or 0 for p in ps)})
    return out


def elegir_vent_anchored(cl, inner):
    """Copia de la regla de pipeline/clustering.py (S38 + S43)."""
    rk = [c for c in cl if c["vrp_mw"] > 0] or cl
    return sorted(rk, key=lambda c: (0 if c["centroid_dist_km"] <= inner else 1, c["centroid_dist_km"], -c["vrp_mw"]))[0]


def elegir_vrp_max(cl):
    return sorted(cl, key=lambda c: c["vrp_mw"], reverse=True)[0]


def clasificar(r, ancla, inner, thr_km):
    """Clase de una pasada que hoy publica, para el brazo `prod + vrp_max` (flag apagado, codigo de hoy)."""
    pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
    for p in pix:
        p["_d"] = C.haversine_km(p["lat"], p["lon"], ancla[0], ancla[1])
    lejos = [p for p in pix if p["_d"] > inner]
    cerca = [p for p in pix if p["_d"] <= inner]
    hs = r.get("hotspot_dist_km")
    if r.get("triggered_test1") and hs is not None and hs > inner:
        return "regla_D", None
    if not lejos:
        reconstruido = bool(r.get("triggered_test1")) and pix and max(p["_d"] for p in pix) <= C.TEST1_ROI_KM + 0.5
        oculto = (r.get("n_anomalous_pixels") or 0) > len(pix)
        if (reconstruido and oculto) or len(pix) >= 100:
            return "no_observable", None
        return "sin_lejano", None
    vl = [p.get("vrp_mw") or 0 for p in lejos]
    vc = [p.get("vrp_mw") or 0 for p in cerca]
    seguro = max(vl) > sum(vc)
    posible = sum(vl) > (max(vc) if vc else 0.0)
    cl = agrupar(pix, ancla, thr_km)
    mx = elegir_vrp_max(cl)
    estimado = mx["centroid_dist_km"] > inner
    if seguro:
        return "seguro", mx
    if estimado:
        return "estimado", mx
    if posible:
        return "posible", None
    return "lejano_debil", None


def simular(r, mx):
    """Record del brazo vrp_max: el cumulo lejano reemplaza al primario (magnitud = suma por pixel)."""
    s = copy.deepcopy(r)
    s["primary_cluster"] = {"n_pixels": mx["n_pixels"], "vrp_mw": round(mx["vrp_mw"], 3),
                            "centroid_lat": round(mx["centroid_lat"], 5), "centroid_lon": round(mx["centroid_lon"], 5),
                            "centroid_dist_km": round(mx["centroid_dist_km"], 3)}
    s["distance_class"] = "summit" if r.get("triggered_test1") else "far"
    s["f5_core_vrp_mw"] = None
    return s


def control_c1(xs, ancla, inner):
    """Reproduccion de primary_cluster con la regla vent_anchored, por factor y sensor."""
    res = {}
    for fac in FACTORES:
        c = collections.Counter()
        for x in xs:
            r = x["rec"]
            pc = r.get("primary_cluster")
            pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
            if not pc or not pix or len(pix) >= 100 or pc.get("centroid_lat") is None:
                continue
            thr = fac * NOMINAL_KM[x["b"]]
            ch = elegir_vent_anchored(agrupar(pix, ancla[x["vol"]], thr), inner[x["vol"]])
            ok = (C.haversine_km(ch["centroid_lat"], ch["centroid_lon"], pc["centroid_lat"], pc["centroid_lon"]) <= TOL_CENTRO_KM
                  and ch["n_pixels"] == pc.get("n_pixels"))
            c[(x["b"], "n")] += 1
            c[(x["b"], "ok")] += int(ok)
        res[fac] = {b: (c[(b, "ok")], c[(b, "n")]) for b in C.BUCKETS}
    return res


def control_c3(ancla_ej=(-23.36, -67.73), inner=5.0):
    p_cr = {"lat": -23.36, "lon": -67.73, "vrp_mw": 0.2}
    p_lj = {"lat": -23.36, "lon": -67.53, "vrp_mw": 1.5}  # ~20 km al este
    casos = {
        "seguro": {"anomaly_pixels": [dict(p_lj), dict(p_cr)], "hotspot_dist_km": 20.4, "triggered_test1": False,
                   "n_anomalous_pixels": 2},
        "sin_lejano": {"anomaly_pixels": [dict(p_cr)], "hotspot_dist_km": 0.0, "triggered_test1": False,
                       "n_anomalous_pixels": 1},
        "regla_D": {"anomaly_pixels": [dict(p_cr)], "hotspot_dist_km": 20.4, "triggered_test1": True,
                    "n_anomalous_pixels": 30},
    }
    for esperado, r in casos.items():
        got, _ = clasificar(r, ancla_ej, inner, 0.6)
        if got != esperado:
            raise SystemExit(f"C3 FALLA: esperaba {esperado}, dio {got}")
    return "ok (seguro, sin_lejano, regla_D)"


def sha(path):
    try:
        return subprocess.run(["git", "log", "-1", "--format=%H", "--", str(path)], cwd=C.ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return None


def main():
    out = io.StringIO()

    def P(*a):
        print(*a)
        print(*a, file=out)

    coords = C._coords_por_volcan()
    ancla, inner_yaml, inner_html = C.anclas_y_inner()
    if inner_yaml != inner_html:
        raise SystemExit(f"inner_radius distinto entre volcanoes.yaml y frontend: {inner_yaml} {inner_html}")
    inner = inner_yaml
    P("== C3 sintetico:", control_c3())
    ident = C.bp.control_identidad_predicado()
    P("== C4 identidad del predicado (guard S139):", ident)

    filas = cargar_referencia_unificada()
    P(f"referencia: snapshot CONS {sha(SNAP_CONS)[:10]} OCR {sha(SNAP_OCR)[:10]}; {len(filas)} filas")

    # ---------------------------------------------------------------- universo de la tarea (D2)
    univ = [f for f in filas if f["tipo"] == "FALSO_POSITIVO" and f["source"] == "CONS" and f["origen"] == "principal"
            and VENTANA[0] <= f["fecha_utc"][:10] <= VENTANA[1] and (f["vrp_mw"] or 0) > 0
            and int(f["fecha_utc"][11:13]) < 12]
    P(f"\n== 1. Universo: FALSO_POSITIVO de la tabla, nocturnas (hora UTC < 12), {VENTANA[0]} a {VENTANA[1]}: {len(univ)}"
      " (VERIFICADOR_DATOS D2: 359)")
    P("   por sensor:", dict(collections.Counter(f["sensor_bucket"] for f in univ)))
    P("   distancia de MIROVA > 25 km (fuera de nuestro disco de 25 km):",
      sum(1 for f in univ if (f["dist_km"] or 0) > 25.0))

    recs = C.cargar_records(C.ROOT / "data" / "mirova_equivalent", VENTANA, coords)
    P(f"\nrecords de los 11 Tier A en la ventana: {len(recs)} (nocturnos segun el filtro del pipeline: "
      f"{sum(x['noche_ok'] for x in recs)})")
    pub = C.predicado(recs, inner_html)
    for x, p in zip(recs, pub):
        x["pub"] = p

    # factor de agrupacion: el que mejor reproduce primary_cluster (C1)
    noct = [x for x in recs if x["noche_ok"]]
    c1 = control_c1(noct, ancla, inner)
    P("\n== C1 reproduccion de primary_cluster con vent_anchored reconstruido (ok / n), por factor x pixel nominal:")
    for fac, d in c1.items():
        P(f"   factor {fac}: " + ", ".join(f"{b} {v[0]}/{v[1]} = {v[0] / max(v[1], 1):.3f}" for b, v in d.items()))
    # Se juzga POR SENSOR (como se mide el criterio). Version 1 de este script lo juzgaba en total y fallaba
    # (0,667) porque MODIS y VIIRS 750 no se reconstruyen por cercania: su pixel fuera del nadir se estira
    # varios km y la vecindad de la grilla no es una distancia. Cambio hecho DESPUES de ver la salida; dicho.
    mejor, mejor_tasa, c1_pasa = {}, {}, {}
    for b in C.BUCKETS:
        fac = max(FACTORES, key=lambda f: c1[f][b][0] / max(c1[f][b][1], 1))
        mejor[b], mejor_tasa[b] = fac, c1[fac][b][0] / max(c1[fac][b][1], 1)
        c1_pasa[b] = mejor_tasa[b] >= UMBRAL_C1
        P(f"   {b}: factor {fac}, {mejor_tasa[b]:.3f}; umbral {UMBRAL_C1}: "
          f"{'PASA, vale el estimado' if c1_pasa[b] else 'FALLA, el estimado se pasa a la cota posible'}")

    # ---------------------------------------------------------------- clasificacion de las pasadas que publican
    for x in recs:
        if not x["pub"]:
            x["clase"] = "no_publica"
            continue
        thr = mejor[x["b"]] * NOMINAL_KM[x["b"]]
        x["clase"], x["_mx"] = clasificar(x["rec"], ancla[x["vol"]], inner[x["vol"]], thr)
        if x["clase"] == "estimado" and not c1_pasa[x["b"]]:
            x["clase"], x["_mx"] = "posible", None
    cand = [x for x in recs if x.get("clase") in ("seguro", "estimado")]
    sims = [{"vol": x["vol"], "sim": simular(x["rec"], x["_mx"])} for x in cand]
    pub_sim = C.predicado(sims, inner_html, campo="sim") if sims else []
    for x, p in zip(cand, pub_sim):
        x["pub_sim"] = p
    no_silencia = sum(1 for x in cand if x["pub_sim"])
    P(f"\npasadas que publican y que el brazo vrp_max reemplazaria por un cumulo lejano: {len(cand)}; "
      f"el predicado del tablero las sigue publicando en {no_silencia} (debe ser 0)")

    # ---------------------------------------------------------------- etiquetas y techo en el criterio
    C.etiquetar(noct, filas, coords, VENTANA)
    P("\n== 2. Las 359: que hay en nuestra pasada pareada (+-2 min, mismo volcan y sensor)")
    idx = collections.defaultdict(list)
    for x in recs:
        idx[(x["vol"], x["b"])].append(x)
    cat = collections.Counter()
    from datetime import datetime, timezone
    for f in univ:
        t = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        ms = [x for x in idx[(f["volcano"], f["sensor_bucket"])] if abs((x["dt"] - t).total_seconds()) <= 120]
        if not ms:
            cat["sin_record_nuestro"] += 1
            continue
        x = ms[0]
        if not x["pub"]:
            pc = x["rec"].get("primary_cluster") or {}
            cat["no_publica_" + ("cumulo_lejano" if (pc.get("centroid_dist_km") or 0) > inner[x["vol"]] and (pc.get("vrp_mw") or 0) > 0
                                 else "sin_cumulo_con_energia")] += 1
        else:
            cat["publica_" + x["clase"]] += 1
    for k, v in sorted(cat.items()):
        P(f"   {k:40s} {v}")

    P("\n== 3. Pasadas nocturnas que hoy publican, por etiqueta y clase (todas las fechas de la ventana)")
    tab = collections.Counter()
    for x in noct:
        if x["pub"]:
            tab[(x["lab"], x["clase"])] += 1
    clases = ["seguro", "estimado", "posible", "lejano_debil", "regla_D", "no_observable", "sin_lejano"]
    P("   etiqueta     | " + " | ".join(f"{c[:9]:>9s}" for c in clases))
    for lab in ("pos", "far_ref", "neg_limpio", "sin_info"):
        P(f"   {lab:12s} | " + " | ".join(f"{tab[(lab, c)]:9d}" for c in clases))

    # C2 (version 2, cambiada DESPUES de ver la salida de la version 1): la version 1 usaba solo la clase
    # "seguro" y "pasaba" con 1 de 247 contra 4 de 4.288, una diferencia de un evento, sin poder (S146). Aca
    # "lejano domina" = el pixel o el cumulo mas energetico de la escena esta fuera del inner (seguro,
    # estimado o regla_D), y el nulo se MIDE barajando las etiquetas dentro de cada volcan y sensor (A110).
    DOM = ("seguro", "estimado", "regla_D")
    pubn = [x for x in noct if x["pub"] and x["lab"] in ("far_ref", "neg_limpio")]

    def razon(labs):
        a = [x["clase"] in DOM for x, l in zip(pubn, labs) if l == "far_ref"]
        b = [x["clase"] in DOM for x, l in zip(pubn, labs) if l == "neg_limpio"]
        ta, tb = sum(a) / max(len(a), 1), sum(b) / max(len(b), 1)
        return ta, tb, (ta / tb if tb else float("inf")), len(a), len(b), sum(a), sum(b)
    ta, tb, rz, na, nb, ka, kb = razon([x["lab"] for x in pubn])
    import random
    rng = random.Random(14)
    grupos = collections.defaultdict(list)
    for i, x in enumerate(pubn):
        grupos[(x["vol"], x["b"])].append(i)
    nulos = []
    for _ in range(200):
        labs = [x["lab"] for x in pubn]
        for ids in grupos.values():
            v = [labs[i] for i in ids]
            rng.shuffle(v)
            for i, l in zip(ids, v):
                labs[i] = l
        nulos.append(razon(labs)[2])
    nulos.sort()
    p95 = nulos[int(0.95 * len(nulos))]
    c2_pasa = na >= 30 and rz > p95
    P(f"\n== C2 enriquecimiento: 'lejano domina' entre las que publican: far_ref {ka}/{na} = {ta:.3f}, "
      f"neg_limpio {kb}/{nb} = {tb:.3f}, razon {rz:.2f}; nulo barajado (200, dentro de volcan y sensor): "
      f"mediana {nulos[100]:.2f}, p95 {p95:.2f}: {'PASA' if c2_pasa else 'FALLA'}")
    pos_dom = [x for x in noct if x["pub"] and x["lab"] == "pos"]
    P(f"   en positivas (MIROVA informo el crater): {sum(x['clase'] in DOM for x in pos_dom)}/{len(pos_dom)}")

    P("\n== 2b. Distancia al objeto en far_ref donde nuestro pixel mas energetico esta lejos (A93: diferencia de")
    P("   RADIOS, cota inferior de la separacion; sin acimut no identifica el objeto)")
    for ref in ("crater", "catalogo"):
        difs = []
        for x in noct:
            r = x["rec"]
            if x["lab"] != "far_ref" or x["clase"] not in DOM or x["dist_ref"] is None or r.get("hotspot_lat") is None:
                continue
            a = ancla[x["vol"]] if ref == "crater" else coords[x["vol"]]
            difs.append(abs(C.haversine_km(r["hotspot_lat"], r["hotspot_lon"], a[0], a[1]) - x["dist_ref"]))
        difs.sort()
        if difs:
            P(f"   desde el {ref:9s}: n {len(difs)}, mediana |r_nuestro - r_MIROVA| {difs[len(difs) // 2]:.2f} km, "
              f"a 2 km o menos {sum(d <= 2 for d in difs)}")

    P("\n== 4. Techo en el criterio de victoria, por sensor y tramo A119 (solo pasadas que DECIDEN; brazo prod + vrp_max)")
    P("   perdidas = pos que hoy publican y quedarian en silencio; ganancias = neg_limpio que hoy publican y callarian")
    P("   cada celda: seguro / seguro+estimado / techo (seguro+estimado+posible+no_observable)")
    grados = {"s": ("seguro",), "e": ("seguro", "estimado"), "t": ("seguro", "estimado", "posible", "no_observable")}
    res = {}
    for b in C.BUCKETS:
        for tn, *_ in C.TRAMOS:
            sel = [x for x in noct if x["b"] == b and x["tramo"] == tn and x["pub"] and x["decide"]]
            if not sel:
                continue
            fila = {}
            for g, cl in grados.items():
                fila[g] = {
                    "veto_A": sum(1 for x in sel if x["lab"] == "pos" and x["prot_A"] and x["clase"] in cl),
                    "perd_muybajo": sum(1 for x in sel if x["lab"] == "pos" and not x["prot_A"] and x["clase"] in cl),
                    "gan_neg": sum(1 for x in sel if x["lab"] == "neg_limpio" and x["clase"] in cl),
                    "veto_B_extra": sum(1 for x in sel if x["lab"] == "far_ref" and x["prot_B"] and x["clase"] in cl),
                }
            fila["n_pos_pub"] = sum(1 for x in sel if x["lab"] == "pos")
            fila["n_neg_pub"] = sum(1 for x in sel if x["lab"] == "neg_limpio")
            res[f"{b}|{tn}"] = fila
            P(f"   {b:8s} {tn:15s} pos publ {fila['n_pos_pub']:4d} neg publ {fila['n_neg_pub']:4d} | "
              + " ; ".join(f"{k} {fila['s'][k]}/{fila['e'][k]}/{fila['t'][k]}" for k in ("veto_A", "perd_muybajo", "gan_neg", "veto_B_extra")))
    solo_ocr = [x for x in noct if x["pub"] and x["lab"] == "pos" and not x["decide"] and x["clase"] in grados["t"]]
    P(f"   positivas solo OCR antes del 2026-06-13 (no deciden, A119) en el techo: {len(solo_ocr)}")

    P("\n== 5. Las que el flag no alcanza (Regla D) pero el cambio de codigo prerequisito si, por etiqueta")
    rd = collections.Counter((x["b"], x["lab"]) for x in noct if x["pub"] and x["clase"] == "regla_D")
    for k, v in sorted(rd.items()):
        P(f"   {k[0]:8s} {k[1]:12s} {v}")
    rd_prot = sum(1 for x in noct if x["pub"] and x["clase"] == "regla_D" and x["lab"] == "pos" and x["prot_A"])
    P(f"   de ellas, pos protegidas (lectura A): {rd_prot}")
    P("   por sensor y tramo, solo las que deciden: pos protegidas A / pos Muy Bajo / neg_limpio / far_ref protegidas B")
    rd_tr = {}
    for b in C.BUCKETS:
        for tn, *_ in C.TRAMOS:
            sel = [x for x in noct if x["b"] == b and x["tramo"] == tn and x["pub"] and x["decide"] and x["clase"] == "regla_D"]
            if not sel:
                continue
            f4 = (sum(x["lab"] == "pos" and x["prot_A"] for x in sel), sum(x["lab"] == "pos" and not x["prot_A"] for x in sel),
                  sum(x["lab"] == "neg_limpio" for x in sel), sum(x["lab"] == "far_ref" and x["prot_B"] for x in sel))
            rd_tr[f"{b}|{tn}"] = f4
            P(f"   {b:8s} {tn:15s} {f4[0]:4d} / {f4[1]:4d} / {f4[2]:4d} / {f4[3]:4d}")

    P("\n== 6. Por volcan: pasadas que publican con clase seguro o estimado (todas las etiquetas)")
    pv = collections.Counter(x["vol"] for x in noct if x["pub"] and x["clase"] in ("seguro", "estimado"))
    for v in C.VOLS:
        P(f"   {v:22s} {pv[v]}")

    P("\n== 7. Ventana propuesta del A/B (tramo T3, 2026-08-29 a 2026-10-08): base de las predicciones")
    t3 = [x for x in noct if x["tramo"] == "T3_ago29_oct08"]
    for b in C.BUCKETS:
        s = [x for x in t3 if x["b"] == b]
        dec = [x for x in s if x["decide"]]
        P(f"   {b:8s} pasadas {len(s):5d}; deciden: pos {sum(x['lab'] == 'pos' for x in dec)} "
          f"(protegidas A {sum(x['lab'] == 'pos' and x['prot_A'] for x in dec)}, publicadas "
          f"{sum(x['lab'] == 'pos' and x['prot_A'] and x['pub'] for x in dec)}), "
          f"neg_limpio {sum(x['lab'] == 'neg_limpio' for x in dec)} (publicados {sum(x['lab'] == 'neg_limpio' and x['pub'] for x in dec)}), "
          f"far_ref {sum(x['lab'] == 'far_ref' for x in s)} (protegidas B {sum(x['lab'] == 'far_ref' and x['prot_B'] for x in s)})")
    cambia_A1 = {g: sum(1 for x in t3 if x["pub"] and x["clase"] in cl) for g, cl in grados.items()}
    cambia_A2 = sum(1 for x in t3 if x["pub"] and x["clase"] == "regla_D")
    for b in C.BUCKETS:
        s = [x for x in t3 if x["b"] == b and x["pub"]]
        P(f"   {b:8s} publicadas {len(s):5d}: A1 seguro {sum(x['clase'] == 'seguro' for x in s)}, "
          f"seguro+estimado {sum(x['clase'] in grados['e'] for x in s)}, techo {sum(x['clase'] in grados['t'] for x in s)}; "
          f"solo A2 (regla_D) {sum(x['clase'] == 'regla_D' for x in s)}")
    P(f"   pasadas publicadas que el brazo A1 podria silenciar (todas las etiquetas): seguro {cambia_A1['s']}, "
      f"seguro+estimado {cambia_A1['e']}, techo {cambia_A1['t']}")
    P(f"   pasadas publicadas que solo el brazo A2 alcanza (regla_D): {cambia_A2}")
    # R4 base: far_ref donde el cumulo publicado ya esta lejos y su radio cae a 2 km del de MIROVA
    fr = [x for x in t3 if x["lab"] == "far_ref"]
    r4 = sum(1 for x in fr if (x["rec"].get("primary_cluster") or {}).get("centroid_dist_km") is not None
             and x["dist_ref"] is not None and x["rec"]["primary_cluster"]["centroid_dist_km"] > inner[x["vol"]]
             and abs(x["rec"]["primary_cluster"]["centroid_dist_km"] - x["dist_ref"]) <= 2.0)
    dom_fr = sum(1 for x in fr if x["clase"] in DOM)
    P(f"   R4 en produccion (far_ref con cumulo lejano a 2 km de radio del de MIROVA): {r4}/{len(fr)}; "
      f"far_ref con lejano dominante (lo que A2 podria mover): {dom_fr}/{len(fr)}")

    resumen = {"t3": {"cambia_A1": cambia_A1, "cambia_A2_regla_D": cambia_A2, "r4_produccion": [r4, len(fr)],
                      "far_ref_dominante": [dom_fr, len(fr)]},
               "ventana": VENTANA, "n_universo": len(univ), "c1": {str(k): v for k, v in c1.items()},
               "c1_factor": mejor, "c1_tasa": {b: round(v, 4) for b, v in mejor_tasa.items()}, "c1_pasa": c1_pasa,
               "c2": {"far_ref": [ka, na], "neg_limpio": [kb, nb], "razon": round(rz, 3), "nulo_p95": round(p95, 3),
                      "nulo_mediana": round(nulos[100], 3), "pasa": c2_pasa},
               "universo_categorias": dict(cat), "techo": res, "candidatas_siguen_publicando": no_silencia,
               "regla_D_por_sensor_etiqueta": {f"{k[0]}|{k[1]}": v for k, v in rd.items()},
               "regla_D_por_sensor_tramo_decide": rd_tr,
               "por_volcan": dict(pv), "identidad_predicado": ident}
    (HERE / "sustrato_salida.txt").write_text(out.getvalue(), encoding="utf-8")
    (HERE / "sustrato_salida.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
