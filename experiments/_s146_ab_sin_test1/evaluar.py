# -*- coding: utf-8 -*-
"""Evaluador del A/B S146 "sin el Test 1 integrado en el ROI".

QUE HACE. Carga los JSON de cada brazo, los etiqueta contra la referencia de MIROVA con el mismo
codigo del banco de paridad (scripts/banco_paridad.py), aplica el predicado literal de publicacion
del dashboard EJECUTADO CON NODE desde frontend/index.html (nunca portado a Python, A97) y aplica
los criterios congelados en parametros.json. El veredicto es ADOPTAR, NO ADOPTAR o INDECIDIBLE.

QUE NO HACE. No decide el flip: eso es el ciclo A45 (tag defensivo y confirmacion de Nicolas).
No baja nada de la red: la referencia son dos CSV en disco, pasados por --cons y --ocr.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 (1) Si lo que mide estuviera roto, fallaria? Si, por tres vias independientes:
     - control positivo del brazo de control: sus records tienen que reproducir los de produccion
       campo por campo, y su tasa de publicacion en negativos limpios tiene que caer dentro de la
       banda pre-registrada. Si no, el veredicto es INDECIDIBLE y no se interpreta nada;
     - control del cargador: el vector de publicacion que produce este archivo sobre el directorio
       de produccion tiene que ser IDENTICO al de banco_paridad.cargar_nuestros (--control-cargador);
     - control de identidad del predicado: los 7 casos del guard de S139, ejecutados con node.
 (2) Si el instrumento estuviera muerto (por ejemplo, si leyera siempre el mismo directorio, o si
     el veredicto no dependiera de los datos), se veria distinto? Si: un brazo IDENTICO al control
     tiene que dar "sin cambio" y NO ADOPTAR, y un brazo que pierde una noche con magnitud grande
     tiene que dar NO ADOPTAR. Los tres casos estan en sintetico.py y su salida cruda en README.md.

USO
  python experiments/_s146_ab_sin_test1/evaluar.py \
      --control data/_s146_ab_control \
      --brazo   data/_s146_ab_sin_test1 \
      --brazo   data/_s146_ab_sin_prioridad_debil \
      --cons <ruta>/registro_vrp_consolidado.csv --ocr <ruta>/registro_vrp_ocr.csv \
      --out experiments/_s146_ab_sin_test1/resultado.json
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

PARAMETROS = AQUI / "parametros.json"
# S147 (verificador, H6): insumos congelados antes del despacho. Ver congelar_produccion.py.
CONGELADO = AQUI / "_congelado"


# --------------------------------------------------------------------------------------
# Carga
# --------------------------------------------------------------------------------------
def cargar_brazo(data_dir, coords, inner, ventana):
    """Igual que banco_paridad.cargar_nuestros pero leyendo `data_dir` y guardando ademas la
    posicion del cumulo publicado, la fuente del ancla y el disparo del Test 1.

    El predicado de publicacion NO se reimplementa: se llama a bp.correr_node, que evalua las
    funciones del propio frontend/index.html con node.
    """
    data_dir = Path(data_dir)
    recs, casos = [], []
    for vol in bp.VOLS:
        p = data_dir / f"{vol}.json"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            recs.append({
                "vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                "pc_dist": pc.get("centroid_dist_km"), "pc_lat": pc.get("centroid_lat"),
                "pc_lon": pc.get("centroid_lon"), "z": r.get("sensor_zenith_deg"),
                "fuente": r.get("final_hotspot_source"),
                "plataforma": r.get("sensor"),  # I-03: MIROVA no lista las pasadas al azar
                "t1": bool(r.get("triggered_test1")),
                "n_px": r.get("n_anomalous_pixels") or 0,
                "granule": r.get("granule"),
            })
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for q in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, q in zip(recs, pred):
        rec["disp"], rec["pub"] = q[3], q[4]
    return recs


def clave(r):
    return (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))


def anotar_vrp_mirova(recs, por_vb):
    """VRP que MIROVA publico en esa pasada (CONS antes que OCR). Solo para las `pos`."""
    for r in recs:
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        alertas = [f for f in filas if bp.es_alerta(f["tipo"])]
        alertas.sort(key=lambda f: (f["source"] != "CONS",))
        r["vrp_ref"] = alertas[0]["vrp_mw"] if alertas else None


# --------------------------------------------------------------------------------------
# Metricas
# --------------------------------------------------------------------------------------
def _tasa(a, n):
    return round(a / n, 4) if n else None


def metricas(recs):
    """Todo lo que el pre-registro mide, en las unidades del operador."""
    out = {"por_sensor": {}, "por_volcan_sensor": {}, "noche_volcan": {}, "noche_sensor": {}}
    for b in bp.BUCKETS:
        sel = [r for r in recs if r["b"] == b]
        neg = [r for r in sel if r["lab"] == "neg_limpio"]
        pos = [r for r in sel if r["lab"] == "pos"]
        out["por_sensor"][b] = {
            "n_pasadas": len(sel),
            "n_neg_limpio": len(neg), "n_neg_pub": sum(r["pub"] for r in neg),
            "tasa_pub_neg": _tasa(sum(r["pub"] for r in neg), len(neg)),
            "n_pos": len(pos), "n_pos_pub": sum(r["pub"] for r in pos),
            "recall_pasada_pos": _tasa(sum(r["pub"] for r in pos), len(pos)),
        }
    for (vol, b), sel in _agrupar(recs, lambda r: (r["vol"], r["b"])).items():
        neg = [r for r in sel if r["lab"] == "neg_limpio"]
        pos = [r for r in sel if r["lab"] == "pos"]
        out["por_volcan_sensor"][f"{vol}|{b}"] = {
            "n_neg_limpio": len(neg), "n_neg_pub": sum(r["pub"] for r in neg),
            "tasa_pub_neg": _tasa(sum(r["pub"] for r in neg), len(neg)),
            "n_pos": len(pos), "n_pos_pub": sum(r["pub"] for r in pos),
        }
    # Unidad 1: la noche del volcan con CUALQUIER sensor.
    noches = _agrupar([r for r in recs], lambda r: (r["vol"], r["noche"]))
    pub, tot = {}, {}
    for k, sel in noches.items():
        if any(r["lab"] == "pos" for r in sel):
            tot[k] = True
            pub[k] = any(r["pub"] for r in sel)
    out["noche_volcan"] = {"n_pos": len(tot), "publicadas": sum(pub.values()),
                           "detalle": {f"{v}|{d}": bool(pub[(v, d)]) for (v, d) in sorted(tot)}}
    # Unidad 2: la noche del SENSOR en que MIROVA alerto (el verificador de la Fase 1 la pidio:
    # sin ella, una perdida en VIIRS 750 desaparece por agregacion).
    ns = _agrupar(recs, lambda r: (r["vol"], r["b"], r["noche"]))
    pub2, tot2 = {}, {}
    for k, sel in ns.items():
        if any(r["lab"] == "pos" for r in sel):
            tot2[k] = True
            pub2[k] = any(r["pub"] for r in sel)
    out["noche_sensor"] = {"n_pos": len(tot2), "publicadas": sum(pub2.values()),
                           "detalle": {f"{v}|{b}|{d}": bool(pub2[(v, b, d)]) for (v, b, d) in sorted(tot2)}}
    # Unidad 3, la que DECIDE: la PASADA en que MIROVA alerto, por sensor. Es la unica vara de
    # recall con poder medido (I-01 y poder_recall.py: las dos unidades de noche las alcanza el
    # azar casi siempre; esta no).
    out["pasada_pos"] = {}
    for b in bp.BUCKETS:
        sub = [r for r in recs if r["b"] == b and r["lab"] == "pos"]
        out["pasada_pos"][b] = {"n": len(sub), "publicadas": sum(r["pub"] for r in sub),
                                "recall": _tasa(sum(r["pub"] for r in sub), len(sub))}
    # I-02: "publicamos" cuenta apariciones, no energia. La mitad de lo que publicamos en
    # negativos limpios esta bajo 0,041 MW y MIROVA casi nunca alerta bajo 0,02 MW. Se informa
    # estratificado por magnitud publicada; NO es piso ni criterio de adopcion.
    out["neg_por_magnitud"] = {}
    for b in bp.BUCKETS:
        neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio"]
        d = {}
        for nombre, lo, hi in (("lt0.02", 0.0, 0.02), ("0.02a0.05", 0.02, 0.05),
                               ("ge0.05", 0.05, float("inf"))):
            pubs = [r for r in neg if r["pub"] and lo <= (r["disp"] or 0) < hi]
            d[nombre] = len(pubs)
        d["n_neg"] = len(neg)
        d["n_pub"] = sum(r["pub"] for r in neg)
        out["neg_por_magnitud"][b] = d
    # I-03: por plataforma. De SNPP MIROVA lista menos de la mitad de las pasadas, asi que el
    # denominador esta enriquecido en pasadas de buena geometria.
    out["neg_por_plataforma"] = {}
    for p, sel in _agrupar([r for r in recs if r["lab"] == "neg_limpio"],
                           lambda r: r["plataforma"]).items():
        out["neg_por_plataforma"][str(p)] = {"n": len(sel), "pub": sum(r["pub"] for r in sel),
                                             "tasa": _tasa(sum(r["pub"] for r in sel), len(sel))}
    # I-04: en MODIS, la mayoria de lo publicado en negativos es de un solo volcan.
    out["modis_sin_pcc"] = {}
    neg = [r for r in recs if r["b"] == "MODIS" and r["lab"] == "neg_limpio"
           and r["vol"] != "PuyehueCordonCaulle"]
    out["modis_sin_pcc"] = {"n": len(neg), "pub": sum(r["pub"] for r in neg),
                            "tasa": _tasa(sum(r["pub"] for r in neg), len(neg))}
    return out


def _agrupar(xs, f):
    d = collections.defaultdict(list)
    for x in xs:
        d[f(x)].append(x)
    return d


def razon_magnitud(recs, n_min):
    """Mediana de (magnitud que ve el operador) / (VRP de MIROVA) en pasadas `pos` publicadas.

    La magnitud del operador es `disp`, que es lo que devuelve mirovaEqVrpDisplay del dashboard:
    ya resuelve el nucleo F5 en VIIRS 375 y pc.vrp_mw en los otros dos (A10, matiz S132). No se
    recalcula aca.
    """
    out = {}
    for k, sel in _agrupar([r for r in recs if r["lab"] == "pos" and r["pub"]
                            and r.get("vrp_ref")], lambda r: (r["vol"], r["b"])).items():
        razones = [r["disp"] / r["vrp_ref"] for r in sel if r["vrp_ref"]]
        if len(razones) >= n_min:
            out[f"{k[0]}|{k[1]}"] = {"n": len(razones), "mediana": round(statistics.median(razones), 4)}
    for b in bp.BUCKETS:
        sel = [r for r in recs if r["b"] == b and r["lab"] == "pos" and r["pub"] and r.get("vrp_ref")]
        razones = [r["disp"] / r["vrp_ref"] for r in sel if r["vrp_ref"]]
        if len(razones) >= n_min:
            out[f"TODOS|{b}"] = {"n": len(razones), "mediana": round(statistics.median(razones), 4)}
    return out


def razon_magnitud_pareada(ctrl, brazo, n_min):
    """S147 (verificador, H4): la razon de magnitud, PAREADA sobre las pasadas que los DOS publican.

    POR QUE. La version sin parear calcula la mediana del control sobre lo que publica el control y
    la del brazo sobre lo que publica el brazo, que es un subconjunto. Con eso, un brazo que deja
    de publicar el 20 % de menor magnitud mueve la mediana hasta 0,23 SIN que cambie ni un vatio de
    las que sobreviven, o sea mas del doble del umbral de 0,10: el criterio se dispara por la
    seleccion, no por una degradacion. `posicion_cumulo` de este mismo archivo ya paraba bien, asi
    que la inconsistencia era interna.

    Devuelve por estrato: la mediana del control y la del brazo sobre EL MISMO conjunto de pasadas,
    mas el conteo de pasadas que el brazo dejo de publicar (que se informa aparte y lo juzga C1).
    """
    ic = {clave(r): r for r in ctrl}
    comunes = []
    for r in brazo:
        c = ic.get(clave(r))
        if c is None or not (c["pub"] and r["pub"]):
            continue
        if c["lab"] != "pos" or not c.get("vrp_ref") or not r.get("vrp_ref"):
            continue
        comunes.append((c, r))
    out = {}

    def _mete(nombre, sel):
        if len(sel) < n_min:
            return
        rc = [c["disp"] / c["vrp_ref"] for c, _ in sel]
        rb = [r["disp"] / r["vrp_ref"] for _, r in sel]
        out[nombre] = {"n": len(sel),
                       "mediana_control": round(statistics.median(rc), 4),
                       "mediana_brazo": round(statistics.median(rb), 4)}

    for k, sel in _agrupar(comunes, lambda cr: (cr[1]["vol"], cr[1]["b"])).items():
        _mete(f"{k[0]}|{k[1]}", sel)
    for b in bp.BUCKETS:
        _mete(f"TODOS|{b}", [cr for cr in comunes if cr[1]["b"] == b])
    return out


def ganancias_publicacion(ctrl, brazo):
    """S147 (verificador, H10): el mecanismo es BIDIRECCIONAL y el pre-registro solo medía la baja.

    Apagar el Test 1 tambien apaga el recomputo de magnitud gateado por source == 'test1'. Cuando
    ese recomputo da 0, TAPA la publicacion; apagarlo devuelve el cumulo contextual, que puede
    traer magnitud mayor que cero. Medido en el control de la ventana: 38 pasadas de VIIRS 750 y 3
    de MODIS tienen el Test 1 disparando y publicacion 0, y 3 de las de VIIRS 750 son POSITIVAS.
    O sea que el brazo puede SUBIR el recall y a la vez subir la publicacion en negativos.

    Sin esto, C6 diria 'la atribucion del mecanismo queda refutada' cuando lo que paso es un
    segundo mecanismo, conocido y declarado, que ningun criterio contemplaba.
    """
    ic = {clave(r): r for r in ctrl}
    out = {b: {"pos": [], "neg_limpio": [], "far_ref": [], "sin_info": []} for b in bp.BUCKETS}
    for r in brazo:
        c = ic.get(clave(r))
        if c is None or c["pub"] or not r["pub"]:
            continue
        lab = c["lab"]
        if lab in out[r["b"]]:
            out[r["b"]][lab].append("|".join(clave(r)))
    return {b: {lab: {"n": len(v), "pasadas": v[:20]} for lab, v in d.items()}
            for b, d in out.items()}


def posicion_cumulo(ctrl, brazo):
    """Cuanto se mueve el cumulo publicado. Distancias al crater, y separacion entre el punto del
    control y el del brazo en las pasadas que los dos publican. Una diferencia de radios NO es una
    distancia entre puntos (A93, A107): por eso se informan las dos cosas."""
    ic = {clave(r): r for r in ctrl}
    pares, movidos = [], []
    for r in brazo:
        c = ic.get(clave(r))
        if c is None or not (c["pub"] and r["pub"]):
            continue
        if None in (c.get("pc_lat"), c.get("pc_lon"), r.get("pc_lat"), r.get("pc_lon")):
            continue
        d = _hav(c["pc_lat"], c["pc_lon"], r["pc_lat"], r["pc_lon"])
        pares.append(d)
        if d > 0.5:
            movidos.append({"pasada": "|".join(clave(r)), "km": round(d, 3),
                            "fuente_control": c.get("fuente"), "fuente_brazo": r.get("fuente")})
    return {"n_pares_publicados_por_ambos": len(pares),
            "mediana_separacion_km": round(statistics.median(pares), 3) if pares else None,
            "p90_separacion_km": round(sorted(pares)[int(0.9 * (len(pares) - 1))], 3) if pares else None,
            "n_movidos_mas_de_500_m": len(movidos), "movidos": movidos[:40]}


def _hav(lat1, lon1, lat2, lon2):
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


# --------------------------------------------------------------------------------------
# Controles
# --------------------------------------------------------------------------------------
def cobertura(ctrl, brazo):
    kc, kb = {clave(r) for r in ctrl}, {clave(r) for r in brazo}
    faltan = sorted(kc - kb)
    sobran = sorted(kb - kc)
    por_vol = collections.Counter(k[0] for k in faltan)
    return {"n_control": len(kc), "n_brazo": len(kb), "n_faltan": len(faltan),
            "n_sobran": len(sobran), "faltan_por_volcan": dict(por_vol),
            "faltan": ["|".join(k) for k in faltan[:60]],
            "sobran": ["|".join(k) for k in sobran[:60]],
            "pareja": not faltan}


def nulo_estructural(ctrl, brazo):
    """Pasadas donde el control no tiene NINGUN pixel anomalo y TAMPOCO PUBLICA: de la nada no
    puede salir una publicacion. Si el brazo publica ahi, el brazo (o el evaluador) esta inventando.

    ⚠️ S147, ARREGLO DE INSTRUMENTO. La version original exigia solo `n_px == 0` en el control, sin
    mirar si el control publicaba. Medido sobre el brazo C: de 1.132 pasadas con 0 pixeles anomalos
    en el control, el control PUBLICA en 392, y el brazo publica exactamente esas mismas 392, sin
    inventar ni una. O sea que el criterio acusaba de invencion un comportamiento conocido y
    documentado: un record con 0 `anomaly_pixels` puede publicar igual por el camino del Test 1,
    que arma su propio cumulo (D30). El brazo C salia INDECIDIBLE por eso.

    Y el defecto es peor que un falso rojo, porque tambien daba un falso VERDE: el brazo B pasaba
    este criterio con 0 publicadas, pero no porque no inventara nada, sino porque apaga justamente
    el camino que hace que esas 392 publiquen. O sea que el unico brazo al que el nulo "le
    funcionaba" era aquel para el que la pregunta no aplicaba. Es el modo de falla de A110: un
    control que no se cancela por construccion, y cuyo nulo nadie habia medido.

    El predicado correcto es el diferencial: el brazo publica donde el control NO publica y ademas
    no hay pixeles. Con eso, el brazo C da 0, que es lo que corresponde.
    """
    ic = {clave(r): r for r in ctrl}

    def _base(r):
        c = ic.get(clave(r))
        return c is not None and (c["n_px"] or 0) == 0 and not c["pub"]

    inventadas = [r for r in brazo if _base(r) and r["pub"]]
    base = [r for r in brazo if _base(r)]
    # Se informa tambien el conteo viejo, para que se vea por que cambio el veredicto.
    viejo = [r for r in brazo
             if (c := ic.get(clave(r))) is not None and (c["n_px"] or 0) == 0 and r["pub"]]
    return {"n_pasadas_sin_pixeles_y_sin_publicar_en_control": len(base),
            "n_publicadas_por_el_brazo": len(inventadas),
            "diag_predicado_viejo_sin_mirar_si_el_control_publica": len(viejo),
            "ejemplos": ["|".join(clave(r)) for r in inventadas[:20]]}


def nulo_barajado(ctrl, brazo, n_iter, semilla):
    """Nulo por etiquetas barajadas DENTRO de cada volcan y sensor (Simpson, V-03).

    Estadistico observado = (caida de la tasa de publicacion entre los negativos limpios) menos
    (caida entre los positivos). Si el brazo apagara publicaciones al azar, las dos caidas serian
    iguales y el contraste caeria dentro del intervalo del nulo.
    """
    ic = {clave(r): r for r in ctrl}
    pares = [(c, r) for r in brazo if (c := ic.get(clave(r))) is not None
             and c["lab"] in ("pos", "neg_limpio")]
    if not pares:
        return {"observado": None, "nota": "sin pares"}

    def contraste(etiquetas):
        neg = [(c, r) for (c, r), lab in zip(pares, etiquetas) if lab == "neg_limpio"]
        pos = [(c, r) for (c, r), lab in zip(pares, etiquetas) if lab == "pos"]
        if not neg or not pos:
            return None
        dn = (sum(r["pub"] for _, r in neg) - sum(c["pub"] for c, _ in neg)) / len(neg)
        dp = (sum(r["pub"] for _, r in pos) - sum(c["pub"] for c, _ in pos)) / len(pos)
        return dn - dp

    obs = contraste([c["lab"] for c, _ in pares])
    rnd = random.Random(semilla)
    grupos = _agrupar(list(range(len(pares))), lambda i: (pares[i][0]["vol"], pares[i][0]["b"]))
    nulos = []
    for _ in range(n_iter):
        etiquetas = [None] * len(pares)
        for idxs in grupos.values():
            labs = [pares[i][0]["lab"] for i in idxs]
            rnd.shuffle(labs)
            for i, lab in zip(idxs, labs):
                etiquetas[i] = lab
        v = contraste(etiquetas)
        if v is not None:
            nulos.append(v)
    nulos.sort()
    lo = nulos[int(0.025 * (len(nulos) - 1))] if nulos else None
    hi = nulos[int(0.975 * (len(nulos) - 1))] if nulos else None
    return {"observado": round(obs, 4) if obs is not None else None,
            "nulo_media": round(sum(nulos) / len(nulos), 4) if nulos else None,
            "nulo_p2.5": round(lo, 4) if lo is not None else None,
            "nulo_p97.5": round(hi, 4) if hi is not None else None,
            "fuera_del_nulo": bool(obs is not None and lo is not None and (obs < lo or obs > hi))}


def control_positivo_control(ctrl, produccion, par):
    """El brazo de control reprocesado debe reproducir produccion. Dos comprobaciones:
    (a) campo por campo sobre los campos que deciden publicacion; (b) la tasa de publicacion en
    negativos limpios dentro de la banda pre-registrada por sensor."""
    ip = {clave(r): r for r in produccion}
    comunes = [r for r in ctrl if clave(r) in ip]
    campos = ["pub", "disp", "dc", "pc_vrp", "pc_dist", "t1", "fuente"]
    difs = collections.Counter()
    ejemplos = collections.defaultdict(list)
    for r in comunes:
        p = ip[clave(r)]
        for c in campos:
            a, b = r.get(c), p.get(c)
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > 1e-6:
                    difs[c] += 1
                    ejemplos[c].append("|".join(clave(r)))
            elif a != b:
                difs[c] += 1
                ejemplos[c].append("|".join(clave(r)))
    n = len(comunes)
    frac_pub_igual = round(1 - difs["pub"] / n, 4) if n else None
    bandas = {}
    ok_banda = True
    m = metricas(ctrl)
    for b, (lo, hi) in par["banda_control_tasa_pub_neg"].items():
        t = m["por_sensor"][b]["tasa_pub_neg"]
        dentro = t is not None and lo <= t <= hi
        bandas[b] = {"tasa": t, "banda": [lo, hi], "dentro": dentro}
        ok_banda = ok_banda and dentro
    # S147 (verificador, H3): la COBERTURA DEL CONTROL contra produccion. Hasta S147 esto
    # comparaba solo la INTERSECCION, asi que un control al que le faltaba el 30 % de las pasadas
    # daba fraccion identica 1,0 y bandas dentro de rango (son tasas, no conteos) y pasaba. Y el
    # control es la referencia de C1, C3, C4, C5 y del propio C0: si el corte de red de NASA le
    # pega a EL, ningun otro criterio se entera, porque C0 solo falla cuando al BRAZO le faltan.
    faltan_ctrl = sorted(set(ip) - {clave(r) for r in ctrl})
    frac_cobertura = round(n / len(produccion), 4) if produccion else None
    ok_cobertura = (frac_cobertura is not None
                    and frac_cobertura >= par["min_fraccion_cobertura_control"])
    return {"n_pasadas_comparadas": n, "n_pasadas_produccion": len(produccion),
            "n_pasadas_control": len(ctrl),
            "n_faltan_al_control_contra_produccion": len(faltan_ctrl),
            "faltan_al_control": ["|".join(k) for k in faltan_ctrl[:60]],
            "faltan_al_control_por_volcan": dict(collections.Counter(k[0] for k in faltan_ctrl)),
            "fraccion_cobertura_control": frac_cobertura,
            "cobertura_control_ok": bool(ok_cobertura),
            "diferencias_por_campo": dict(difs),
            "fraccion_publicacion_identica": frac_pub_igual,
            "ejemplos": {k: v[:10] for k, v in ejemplos.items()},
            "bandas_tasa_pub_neg": bandas,
            "cumple": bool(n > 0 and frac_pub_igual is not None
                           and frac_pub_igual >= par["min_fraccion_publicacion_identica"]
                           and ok_banda and ok_cobertura)}


# --------------------------------------------------------------------------------------
# Criterios y veredicto
# --------------------------------------------------------------------------------------
def perdidas(mc, mb, unidad, vrp_por_noche):
    """Noches que el control publica y el brazo no, con la magnitud que publico MIROVA."""
    out = []
    dc, db = mc[unidad]["detalle"], mb[unidad]["detalle"]
    for k, v in sorted(dc.items()):
        if v and not db.get(k, False):
            out.append({"noche": k, "vrp_mirova_mw": vrp_por_noche.get(k)})
    return out


def perdidas_pasada(ctrl, brazo):
    """Pasadas con ALERTA de MIROVA que el control publica y el brazo no, una por una."""
    ib = {clave(r): r for r in brazo}
    out = []
    for c in ctrl:
        if c["lab"] != "pos" or not c["pub"]:
            continue
        b = ib.get(clave(c))
        if b is not None and not b["pub"]:
            out.append({"pasada": "|".join(clave(c)), "vol": c["vol"], "sensor": c["b"],
                        "plataforma": c["plataforma"], "noche": c["noche"],
                        "vrp_mirova_mw": c.get("vrp_ref"),
                        "magnitud_control_mw": c.get("disp"),
                        "fuente_control": c.get("fuente")})
    return sorted(out, key=lambda p: -(p["vrp_mirova_mw"] or 0))


def vrp_por_noche(recs, unidad):
    d = {}
    for r in recs:
        if r["lab"] != "pos" or not r.get("vrp_ref"):
            continue
        k = f"{r['vol']}|{r['noche']}" if unidad == "noche_volcan" else f"{r['vol']}|{r['b']}|{r['noche']}"
        d[k] = max(d.get(k, 0.0), float(r["vrp_ref"]))
    return d


def evaluar_brazo(nombre, ctrl, brazo, par):
    mc, mb = metricas(ctrl), metricas(brazo)
    cob = cobertura(ctrl, brazo)
    res = {
        "brazo": nombre,
        "cobertura": cob,
        "metricas_control": mc, "metricas_brazo": mb,
        "perdidas_noche_volcan": perdidas(mc, mb, "noche_volcan", vrp_por_noche(ctrl, "noche_volcan")),
        "perdidas_noche_sensor": perdidas(mc, mb, "noche_sensor", vrp_por_noche(ctrl, "noche_sensor")),
        "razon_magnitud_control": razon_magnitud(ctrl, par["n_min_magnitud"]),
        "razon_magnitud_brazo": razon_magnitud(brazo, par["n_min_magnitud"]),
        "posicion": posicion_cumulo(ctrl, brazo),
        "nulo_estructural": nulo_estructural(ctrl, brazo),
        "nulo_barajado": nulo_barajado(ctrl, brazo, par["n_barajados"], par["semilla"]),
    }
    c = {}
    # C0 cobertura pareja (se mira ANTES del veredicto, A108).
    c["C0_cobertura_pareja"] = cob["pareja"]
    # C1 recall POR PASADA del sensor que alerto. Es la unica vara de recall con poder medido
    # (I-01 y poder_recall.py). Dos condiciones: ninguna pasada perdida que MIROVA publico con
    # 0,5 MW o mas (cualquier sensor), y piso de recall por sensor.
    res["pasadas_perdidas"] = perdidas_pasada(ctrl, brazo)
    grandes = [p for p in res["pasadas_perdidas"]
               if (p["vrp_mirova_mw"] or 0) >= par["max_vrp_fn_aceptable_mw"]]
    res["pasadas_perdidas_grandes"] = grandes
    # S147, verificador con contexto limpio (H1 y H2): el piso se compara en CONTEO, no en tasa
    # redondeada. Antes el piso de VIIRS 750 era 0.667 y `_tasa` redondea 12/18 a 0.6667, asi que
    # `0.6667 >= 0.667` daba False: el umbral RECHAZABA justo el valor que el pre-registro decia
    # aceptar, y el brazo salia NO ADOPTAR por un error de redondeo en la tercera cifra. Con
    # conteos no hay redondeo posible. La tasa se sigue informando, pero no decide.
    pisos = par["min_pasadas_positivas_publicadas"]
    det1 = {}
    ok1 = not grandes
    for b, piso in pisos.items():
        pb = mb["pasada_pos"][b]["publicadas"]
        pc_ = mc["pasada_pos"][b]["publicadas"]
        cumple = pb >= piso
        det1[b] = {"control_publicadas": pc_, "brazo_publicadas": pb, "piso_conteo": piso,
                   "cumple": cumple, "n": mb["pasada_pos"][b]["n"],
                   "recall_control": mc["pasada_pos"][b]["recall"],
                   "recall_brazo": mb["pasada_pos"][b]["recall"],
                   "perdidas_contra_control": pc_ - pb}
        ok1 = ok1 and cumple
    c["C1_recall_pasada"] = bool(ok1)
    res["C1_detalle"] = det1
    # C2 ninguna NOCHE perdida fuera de la lista pre-identificada por la Fase 1. Esta vara no
    # tiene poder por si sola (el azar la cumple), asi que NO sirve para certificar que el brazo
    # es bueno; sirve para lo contrario, que es barato y si informa: una perdida que la Fase 1 no
    # predijo significa que hay un mecanismo que no entendemos.
    pv = res["perdidas_noche_volcan"]
    ps = res["perdidas_noche_sensor"]
    esperadas = set(par["perdidas_esperadas_noche_volcan"])
    esperadas_s = set(par["perdidas_esperadas_noche_sensor"])
    c["C2_noches_dentro_de_lo_previsto"] = bool(
        all(p["noche"] in esperadas for p in pv)
        and all(p["noche"] in esperadas_s for p in ps)
        and len(pv) <= par["max_noches_perdidas_volcan"]
        and len(ps) <= par["max_noches_perdidas_sensor"])
    # C3 baja la publicacion en negativos limpios (solo los sensores con poder).
    # S147 (verificador, H5): dos formas. La de TECHO por tasa absoluta sirve cuando el brazo
    # puede mover mucho (brazo B). Para un brazo que apaga una rama chica, un techo absoluto
    # exige que la prediccion se cumpla entera y puede dejar margen CERO en un sensor: ahi el
    # criterio es un PISO DE PASADAS APAGADAS en la subclase, que es lo que ese brazo puede mover.
    detalle = {}
    ok3 = True
    if "min_pasadas_apagadas_neg" in par:
        for b, minimo in par["min_pasadas_apagadas_neg"].items():
            pb = mb["por_sensor"][b]["n_neg_pub"]
            pc_ = mc["por_sensor"][b]["n_neg_pub"]
            apagadas = pc_ - pb
            cumple = apagadas >= minimo
            detalle[b] = {"control_publicadas_neg": pc_, "brazo_publicadas_neg": pb,
                          "apagadas": apagadas, "minimo_apagadas": minimo, "cumple": cumple,
                          "tasa_control": mc["por_sensor"][b]["tasa_pub_neg"],
                          "tasa_brazo": mb["por_sensor"][b]["tasa_pub_neg"]}
            ok3 = ok3 and cumple
    else:
        for b, techo in par["techo_tasa_pub_neg"].items():
            t = mb["por_sensor"][b]["tasa_pub_neg"]
            tc = mc["por_sensor"][b]["tasa_pub_neg"]
            cumple = t is not None and t <= techo
            detalle[b] = {"control": tc, "brazo": t, "techo": techo, "cumple": cumple,
                          "caida_pp": round(100 * (tc - t), 2) if (t is not None and tc is not None) else None}
            ok3 = ok3 and cumple
    c["C3_publicacion_negativos"] = ok3
    res["C3_detalle"] = detalle
    # C4 la magnitud no se aleja de 1 en ningun estrato con n suficiente. S147 (verificador, H4):
    # PAREADO sobre las pasadas que los dos publican. La version sin parear medía la seleccion, no
    # la degradacion: un brazo que deja de publicar el 20 % mas chico movia la mediana 0,23, mas
    # del doble del umbral, sin cambiar ni un vatio de lo que sobrevive. La version sin parear se
    # sigue guardando en el informe, pero NO decide.
    res["razon_magnitud_pareada"] = razon_magnitud_pareada(ctrl, brazo, par["n_min_magnitud"])
    peor, ok4 = None, True
    for k, v in res["razon_magnitud_pareada"].items():
        empeora = abs(v["mediana_brazo"] - 1) - abs(v["mediana_control"] - 1)
        if peor is None or empeora > peor[1]:
            peor = (k, round(empeora, 4))
        if empeora > par["max_empeora_magnitud"]:
            ok4 = False
    c["C4_magnitud"] = ok4
    res["C4_peor_estrato"] = peor
    res["C4_estratos_sin_muestra"] = sorted(
        set(res["razon_magnitud_control"]) - set(res["razon_magnitud_pareada"]))
    # C5 el nulo estructural: de la nada no sale una publicacion.
    c["C5_nulo_estructural"] = res["nulo_estructural"]["n_publicadas_por_el_brazo"] == 0
    # C6 el orden por sensor que predice el mecanismo de F-01 (escrito antes de correr).
    caidas = {b: (detalle[b].get("caida_pp") if b in detalle else None) for b in bp.BUCKETS}
    for b in bp.BUCKETS:
        if caidas[b] is None:
            tc, t = mc["por_sensor"][b]["tasa_pub_neg"], mb["por_sensor"][b]["tasa_pub_neg"]
            caidas[b] = round(100 * (tc - t), 2) if (t is not None and tc is not None) else None
    orden = (caidas["VIIRS375"] is not None and caidas["VIIRS750"] is not None
             and caidas["MODIS"] is not None
             and caidas["VIIRS375"] >= caidas["VIIRS750"] >= caidas["MODIS"])
    c["C6_orden_por_sensor_V375_V750_MODIS"] = bool(orden)
    res["C6_caidas_pp"] = caidas
    # C7 (S147, verificador H11): el cumulo publicado no se muda. Se calculaba y no decidia. En un
    # proyecto donde A61 nacio porque dos auditorias completas se perdieron el eje espacial, y
    # donde el operador mira un mapa, ese es el eje que menos conviene dejar sin criterio.
    c["C7_posicion_estable"] = bool(
        res["posicion"]["n_movidos_mas_de_500_m"] <= par["max_cumulos_movidos_500m"])
    # C8 (S147, verificador H11): el contraste entre positivos y negativos queda FUERA del nulo de
    # etiquetas barajadas. Un brazo que apaga publicaciones al azar da las dos caidas iguales y
    # cae dentro del nulo; hasta ahora eso salia ADOPTAR igual.
    c["C8_fuera_del_nulo_barajado"] = bool(res["nulo_barajado"].get("fuera_del_nulo"))
    # Informativo, no decide: las pasadas que el brazo publica y el control NO (H10). El mecanismo
    # es bidireccional y hasta S147 ningun criterio lo miraba.
    res["ganancias_publicacion"] = ganancias_publicacion(ctrl, brazo)
    res["criterios"] = c
    return res


def veredicto(res, ctrl_ok, par):
    c = res["criterios"]
    if not ctrl_ok:
        return "INDECIDIBLE", "el control positivo del brazo de control no se cumple"
    if not c["C0_cobertura_pareja"]:
        return "INDECIDIBLE", ("cobertura despareja: faltan %d pasadas (%s). Repetir el job y "
                               "volver a evaluar" % (res["cobertura"]["n_faltan"],
                                                     res["cobertura"]["faltan_por_volcan"]))
    if not c["C5_nulo_estructural"]:
        return "INDECIDIBLE", "el brazo publica en pasadas sin ningun pixel anomalo: el nulo falla"
    decisorios = [k for k in par["criterios_decisorios"]]
    fallan = [k for k in decisorios if not c.get(k)]
    # C6 no decide: es la prediccion por sensor que escribimos antes de correr (F-01). Si falla,
    # el beneficio de paridad puede ser real igual, pero la atribucion del mecanismo queda
    # refutada y eso tiene que salir en el titular, no en una nota al pie.
    aviso = "" if c.get("C6_orden_por_sensor_V375_V750_MODIS") else \
        " | AVISO: falla C6, el orden por sensor no es el que predice F-01: la atribucion del " \
        "mecanismo queda refutada y el verificador tiene que mirarlo antes de proponer nada"
    if not fallan:
        return "ADOPTAR", "cumple " + ", ".join(decisorios) + aviso
    return "NO ADOPTAR", "falla " + ", ".join(fallan) + aviso


# --------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True, help="directorio de JSON del brazo de control")
    ap.add_argument("--brazo", action="append", default=[], help="directorio de un brazo (repetible)")
    # S147 (verificador, H6): los tres insumos que NO son los brazos estan CONGELADOS en
    # _congelado/, generados por congelar_produccion.py antes de despachar. El cron NRT escribe
    # data/mirova_equivalent cada dos horas y el scraper sigue trayendo filas de MIROVA: entre dos
    # corridas del mismo banco con horas de diferencia el corpus paso de 2.360 a 2.386 records y
    # una vara de recall cambio de clasificacion por el borde de su corte. Los techos de C3 son
    # tasas absolutas calibradas sobre denominadores fijos: si el denominador se mueve, un brazo
    # puede cruzar un techo sin que el flag tenga nada que ver (A90).
    ap.add_argument("--produccion", default=str(CONGELADO / "produccion_ventana.json"),
                    help="JSON congelado (o directorio) de produccion para el control positivo; "
                         "'no' lo salta")
    ap.add_argument("--cons", default=str(CONGELADO / "registro_vrp_consolidado.csv"))
    ap.add_argument("--ocr", default=str(CONGELADO / "registro_vrp_ocr.csv"))
    ap.add_argument("--parametros", default=str(PARAMETROS))
    ap.add_argument("--poder", default=str(AQUI / "poder_recall.json"),
                    help="salida de poder_recall.py: el nulo medido de cada vara de recall")
    ap.add_argument("--out", default=str(AQUI / "resultado.json"))
    ap.add_argument("--control-cargador", action="store_true",
                    help="comprueba que este cargador da el mismo vector de publicacion que banco_paridad")
    a = ap.parse_args(argv)

    par = json.loads(Path(a.parametros).read_text(encoding="utf-8"))
    ventana = (par["ventana"][0], par["ventana"][1])
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    identidad = bp.control_identidad_predicado()
    # S147 (verificador, H8): el valor se guardaba en `meta` y NUNCA se comparaba, asi que el
    # control no podia fallar. Si alguien toca isValidDetection en frontend/index.html entre el
    # pre-registro y la evaluacion, el A/B mide con otro predicado que el que calibro los
    # umbrales, y el informe diria igual que el control se corrio. Es el modo de falla de A110:
    # un control que pasa en verde sobre un instrumento cambiado. El esperado es el mismo que
    # pineaba el evaluador de S143 (experiments/_s143_evaluador/evaluar.py).
    esperado = ([0, 1, 1, 1, 0], [1, 0])
    identidad_ok = (list(identidad[0]), list(identidad[1])) == (esperado[0], esperado[1])

    filas = cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)

    def preparar(d):
        recs = cargar_brazo(d, coords, inner, ventana)
        bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        anotar_vrp_mirova(recs, por_vb)
        return recs

    ctrl = preparar(a.control)

    salida = {"meta": {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana": list(ventana), "parametros": par,
        "sha_index_html": bp.sha_git(bp.HTML),
        "n_filas_referencia_nocturnas": n_ref,
        # El poder de cada vara de recall se midio ANTES de fijar los umbrales, sobre los
        # records de produccion, con poder_recall.py. Se incrusta aca para que el veredicto y
        # la prueba de que la vara discrimina viajen juntos (I-01).
        "poder_de_las_varas": (json.loads(Path(a.poder).read_text(encoding="utf-8"))["varas"]
                               if Path(a.poder).exists() else "NO MEDIDO: correr poder_recall.py"),
        "control_identidad_predicado": {"guard_s139": identidad[0],
                                        "publica_no_publica": identidad[1],
                                        "esperado": [esperado[0], esperado[1]],
                                        "coincide": bool(identidad_ok)},
        "volcanes": bp.VOLS}}

    if a.control_cargador:
        viejo_data = bp.DATA
        bp.DATA = Path(a.control)
        try:
            ref_recs = bp.cargar_nuestros(coords, inner, ventana)
        finally:
            bp.DATA = viejo_data
        mio = {clave(r): r["pub"] for r in ctrl}
        suyo = {(r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M")): r["pub"] for r in ref_recs}
        salida["meta"]["control_cargador"] = {
            "n_mio": len(mio), "n_banco": len(suyo),
            "identico": mio == suyo,
            "discrepancias": [("|".join(k)) for k in sorted(set(mio) | set(suyo))
                              if mio.get(k) != suyo.get(k)][:20]}

    if a.produccion and a.produccion != "no" and Path(a.produccion).exists():
        # S147 (H6): la produccion congelada viene como JSON ya cargado y etiquetado, con el
        # predicado del operador ya evaluado con node. Un directorio se sigue aceptando, pero
        # entonces se lee el corpus VIVO y eso es lo que H6 dice que no hay que hacer.
        if Path(a.produccion).is_file():
            crudo = json.loads(Path(a.produccion).read_text(encoding="utf-8"))
            prod = []
            for s in crudo["records"]:
                r = dict(s)
                r["dt"] = datetime.strptime(s["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                prod.append(r)
            salida["meta"]["produccion_congelada"] = crudo["manifiesto"]
        else:
            prod = preparar(a.produccion)
            salida["meta"]["produccion_congelada"] = "NO: se leyo el corpus vivo (ver H6)"
        salida["control_positivo"] = control_positivo_control(ctrl, prod, par)
        ctrl_ok = salida["control_positivo"]["cumple"]
    else:
        salida["control_positivo"] = {"cumple": False, "nota": "no se comparo contra produccion"}
        ctrl_ok = False
    # S147 (verificador, H8): el predicado del operador tiene que ser el MISMO que calibro los
    # umbrales. Si cambio, todo el A/B midio otra cosa y el veredicto es INDECIDIBLE.
    if not identidad_ok:
        ctrl_ok = False
        salida["control_positivo"]["nota_identidad"] = (
            "el predicado de frontend/index.html cambio respecto del pre-registro: "
            f"{identidad} contra el esperado {esperado}")

    salida["brazos"] = []
    for d in a.brazo:
        b = preparar(d)
        nombre = Path(d).name
        # Cada brazo mide una palanca de tamano distinto, asi que sus umbrales estan
        # pre-registrados por separado en par["por_brazo"]. Lo que NO cambia por brazo es la
        # forma del criterio ni los controles.
        par_b = dict(par)
        par_b.update(par.get("por_brazo", {}).get(nombre, {}))
        res = evaluar_brazo(nombre, ctrl, b, par_b)
        res["parametros_del_brazo"] = par.get("por_brazo", {}).get(nombre, {})
        res["veredicto"], res["razon"] = veredicto(res, ctrl_ok, par_b)
        salida["brazos"].append(res)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    print("ventana %s a %s | referencia nocturna %d filas | sha index.html %s"
          % (ventana[0], ventana[1], n_ref, salida["meta"]["sha_index_html"][:10]))
    cp = salida["control_positivo"]
    print("control positivo del control: cumple=%s | %s" % (cp.get("cumple"), json.dumps(
        {k: cp.get(k) for k in ("n_pasadas_comparadas", "fraccion_publicacion_identica",
                                "diferencias_por_campo")}, ensure_ascii=False)))
    if "control_cargador" in salida["meta"]:
        print("control del cargador contra banco_paridad: identico=%s"
              % salida["meta"]["control_cargador"]["identico"])
    for res in salida["brazos"]:
        print("\n=== %s -> %s (%s)" % (res["brazo"], res["veredicto"], res["razon"]))
        print("  cobertura: control %d, brazo %d, faltan %d (pareja=%s)"
              % (res["cobertura"]["n_control"], res["cobertura"]["n_brazo"],
                 res["cobertura"]["n_faltan"], res["cobertura"]["pareja"]))
        print("  publicacion en negativos limpios:", json.dumps(res["C3_detalle"], ensure_ascii=False))
        print("  caidas pp por sensor:", res["C6_caidas_pp"])
        print("  recall por PASADA (la vara que decide):", json.dumps(res["C1_detalle"], ensure_ascii=False))
        print("  pasadas perdidas: %d, de ellas con 0,5 MW o mas de MIROVA: %d"
              % (len(res["pasadas_perdidas"]), len(res["pasadas_perdidas_grandes"])))
        for q in res["pasadas_perdidas"][:15]:
            print("     - %s | MIROVA %s MW | nuestro control %s MW | fuente %s"
                  % (q["pasada"], q["vrp_mirova_mw"], q["magnitud_control_mw"], q["fuente_control"]))
        print("  noches perdidas (volcan, vara SIN poder): %d %s"
              % (len(res["perdidas_noche_volcan"]), res["perdidas_noche_volcan"]))
        print("  noches perdidas (sensor, vara SIN poder): %d %s"
              % (len(res["perdidas_noche_sensor"]), res["perdidas_noche_sensor"]))
        print("  negativos publicados por magnitud (I-02):",
              json.dumps(res["metricas_brazo"]["neg_por_magnitud"], ensure_ascii=False))
        print("  MODIS sin Cordon Caulle (I-04): control %s brazo %s"
              % (json.dumps(res["metricas_control"]["modis_sin_pcc"], ensure_ascii=False),
                 json.dumps(res["metricas_brazo"]["modis_sin_pcc"], ensure_ascii=False)))
        print("  negativos por plataforma (I-03):",
              json.dumps(res["metricas_brazo"]["neg_por_plataforma"], ensure_ascii=False))
        print("  nulo estructural:", res["nulo_estructural"]["n_publicadas_por_el_brazo"],
              "publicadas de", res["nulo_estructural"]["n_pasadas_sin_pixeles_y_sin_publicar_en_control"],
              "| nulo barajado:", json.dumps(res["nulo_barajado"], ensure_ascii=False))
        print("  criterios:", json.dumps(res["criterios"], ensure_ascii=False))
    print("\n->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
