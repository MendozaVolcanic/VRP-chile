# -*- coding: utf-8 -*-
"""S145: cuanto de lo que publicamos hoy se puede clasificar con los campos que ya estan escritos.

POR QUE. `docs/MISSION.md` declara dos objetivos que comparten un mismo algoritmo de deteccion:
el clon literal de MIROVA NRT y la extension volcanica documentada (publicar la anomalia real que
MIROVA no informa por alcance operacional). Y declara donde vive la distincion: "en el campo
derivado `pc.classification`". Ese nombre no existe en ningun record. Sin esa distincion, el 86 %
de pasadas en que publicamos donde MIROVA miro y no vio nada se lee como defecto cuando puede ser
el producto, y toda metrica de precision queda ininterpretable.

QUE MIDE ESTE SCRIPT, y nada mas. Sobre las pasadas que HOY publica el dashboard, cuantas caen en
cada categoria del marco A54: (a) MIROVA si publico, (b) feature volcanica real no publicada por
MIROVA, (c) geotermal o lacustre no volcanico, (d) artefacto. Y, sobre todo, CUALES de esas cuatro
se pueden separar con los campos persistidos y cuales no. NO propone, NO filtra, NO toca pipeline.

COMO SE DECIDE (a). Por la referencia de MIROVA pareada por pasada, con el etiquetado de
`scripts/banco_paridad.py` (pos / far_ref / neg_limpio / sin_info). "Publicar" es el predicado del
dashboard EJECUTADO con node desde `frontend/index.html` (A97), nunca reconstruido a mano.

COMO SE INTENTA (b), (c) y (d). No hay etiqueta por record para ninguna de las tres: la
clasificacion de S86 se hizo por volcan y a mano, no quedo escrita en el dato. Lo unico que hay son
REGLAS candidatas que sesiones previas propusieron. Asi que en vez de aplicarlas y reportar el
reparto como si fuera medicion, se mide el COSTO de cada regla en el unico estrato con etiqueta
conocida: las pasadas que MIROVA si confirmo, que son reales sin discusion. Una regla que marca
como artefacto a una fraccion apreciable de esas esta refutada como discriminante (A110: un control
se valida midiendo su nulo, no razonandolo). Lo que la regla haga sobre el resto del universo no se
puede verificar y se reporta como tal.

POR VOLCAN SIEMPRE. Una mediana agrupada invierte veredictos (S126): el radio interno va de 3 km
(Lastarria) a 20 km (Puyehue Cordon Caulle) y el regimen termico de cada volcan es distinto.

Fuente de verdad: sustrato_clasificacion.json (regla S91). Ningun numero se escribe a mano.
USO: python experiments/_s145_classification/sustrato_clasificacion.py [--inicio ...] [--fin ...]
"""
import argparse
import collections
import io
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import yaml  # noqa: E402

import banco_paridad as bp  # noqa: E402
from pipeline.store import _haversine_km  # noqa: E402

SALIDA = HERE / "sustrato_clasificacion.json"
INICIO_S145 = "2026-09-01"  # el regimen actual empieza con el PR #571 (2026-08-31); A104
FIN_S145 = "2026-09-20"
FEATURES_YAML = ROOT / "pipeline" / "volcanic_features.yaml"

# Campos que este script necesita ademas de los que `banco_paridad` conserva. Se leen del JSON
# crudo en el mismo recorrido, para no reindexar por clave y arriesgar un pareo equivocado.
EXTRA = ["t_bg_k", "t_max_k", "n_anomalous_pixels", "triggered_test1", "test1_k_observed",
         "diag_nti_max", "nti_max", "diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path",
         "diag_n_eti_path", "n_excluded_water", "discarded_reason", "final_hotspot_dist_km",
         "final_hotspot_source", "f5_core_vrp_mw", "granule", "product_version"]


# ---------------------------------------------------------------- carga (copia del banco + extras)
def cargar_extendido(coords, inner, ventana):
    """Igual que bp.cargar_nuestros pero conservando EXTRA y el primary_cluster entero.

    Se copia el recorrido en vez de reusar la funcion porque la del banco descarta los campos que
    esta medicion necesita. El predicado sigue siendo el de node, con los MISMOS `bp.CAMPOS_JS`:
    lo que cambia es que se guarda mas de lo que se le manda a node, nunca menos.
    """
    recs, casos = [], []
    for vol in bp.VOLS:
        with open(bp.DATA / f"{vol}.json", encoding="utf-8") as fh:
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
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                   "sensor": r.get("sensor"), "dc": r.get("distance_class"),
                   "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                   "pc_npix": pc.get("n_pixels"), "pc_lat": pc.get("centroid_lat"),
                   "pc_lon": pc.get("centroid_lon"), "geo_class": pc.get("geo_class"),
                   "tiene_pc": bool(r.get("primary_cluster")),
                   "z": r.get("sensor_zenith_deg")}
            rec.update({k: r.get(k) for k in EXTRA})
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["summit_js"], rec["valid_js"], rec["art_js"] = p[0], p[1], p[2]
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


# ---------------------------------------------------------------- reglas candidatas de artefacto
def _nti(r):
    """nti_max: `diag_nti_max` esta en las 2285 pasadas; `nti_max` solo en 1831 (A89)."""
    v = r.get("diag_nti_max")
    return v if v is not None else r.get("nti_max")


REGLAS = {
    # A80 (S112): nti_max en el piso ~-0.9 = gradiente topografico amplificado por pixel grande.
    # A80 refinada en S116: el piso es COMPARTIDO por lo real y lo artefacto (AUC 0,251).
    "A80_nti_max_en_el_piso": lambda r: (_nti(r) is not None and _nti(r) <= -0.9),
    # Gate t_bg<260 K del diseno S87, REFUTADO por S86 (perdia el Lascar eruptivo del 2026-02-17).
    "S87_t_bg_bajo_260K": lambda r: (r.get("t_bg_k") is not None and r["t_bg_k"] < 260.0),
    # "senal debil = un solo pixel": la intuicion mas comun.
    "cumulo_de_un_pixel": lambda r: (r.get("pc_npix") or 0) <= 1,
    # Camino contextual puro: ningun pixel por umbral de BT (familia del drift D9 / A23).
    # OJO: se reporta pero resulta DEGENERADA en esta ventana (ver `sustrato_de_campos`).
    "sin_camino_BT": lambda r: (r.get("diag_n_bt_path") or 0) == 0,
    # A83 (S116): `test1_k_observed` fue el mejor discriminante fisico hallado (AUC 0,859) y su
    # corte es REGIMEN-DEPENDIENTE (focal ~4-5 K, nevado ~2,8-3,9 K). Se prueba el corte focal.
    "A83_test1_k_menor_4K": lambda r: (r.get("test1_k_observed") is not None
                                       and r["test1_k_observed"] < 4.0),
}


def costo_de_las_reglas(pub_a, pub_resto, por=None):
    """Para cada regla: que fraccion marca en el estrato con etiqueta (a) y en el resto.

    La primera columna es el COSTO medido: lo que la regla destruiria de lo que MIROVA confirmo,
    que es real sin discusion. La segunda NO es una medicion de artefacto: es cuanto se llevaria
    de un universo donde (b), (c) y (d) estan mezcladas y sin etiqueta.
    """
    out = {}
    for nombre, f in REGLAS.items():
        ca = sum(1 for r in pub_a if f(r))
        cr = sum(1 for r in pub_resto if f(r))
        out[nombre] = {
            "n_a": len(pub_a), "marcadas_en_a": ca,
            "frac_de_a_que_destruiria": round(ca / len(pub_a), 4) if pub_a else None,
            "n_resto": len(pub_resto), "marcadas_en_resto": cr,
            "frac_del_resto_que_marca": round(cr / len(pub_resto), 4) if pub_resto else None,
        }
        if por:
            out[nombre]["por_" + por[0]] = {
                k: {"a": [sum(1 for r in va if f(r)), len(va)],
                    "resto": [sum(1 for r in vr if f(r)), len(vr)]}
                for k, (va, vr) in por[1].items()}
    return out


# ---------------------------------------------------------------- permanencia del sitio publicado
def permanencia(pub, recs):
    """Cuan fijo es el lugar que publicamos, por volcan y sensor.

    POR QUE: un sitio que publica casi todas las noches SIEMPRE en el mismo punto es, o una fuente
    volcanica cronica (categoria b, real), o terreno tibio estable (categoria d, artefacto A69).
    Justo el par que ningun campo separa (A83). Medirlo hace concreta la indistinguibilidad, y de
    paso dice si lo que el operador ve es un estado de base o un evento.
    """
    out = {}
    # A90: un conteo de noches sin su denominador no es una afirmacion. El denominador es cuantas
    # noches ese volcan tuvo al menos una pasada nocturna de ese sensor en la ventana.
    noches_con_pasada = {k: len({r["noche"] for r in v})
                         for k, v in _agrupar(recs, lambda r: (r["vol"], r["b"])).items()}
    for (vol, b), grp in sorted(_agrupar(pub, lambda r: (r["vol"], r["b"])).items()):
        pts = [(r["pc_lat"], r["pc_lon"]) for r in grp if r["pc_lat"] is not None]
        disp = None
        if len(pts) >= 3:
            mlat = statistics.median(p[0] for p in pts)
            mlon = statistics.median(p[1] for p in pts)
            disp = round(statistics.median(_haversine_km(p[0], p[1], mlat, mlon) for p in pts), 3)
        out[f"{vol}|{b}"] = {
            "n_publicadas": len(grp),
            "n_pasadas_nocturnas": len(_agrupar(recs, lambda r: (r["vol"], r["b"]))[(vol, b)]),
            "n_noches_publicadas": len({r["noche"] for r in grp}),
            "n_noches_con_pasada": noches_con_pasada[(vol, b)],
            "mediana_dist_crater_km": (round(statistics.median(
                r["pc_dist"] for r in grp if r["pc_dist"] is not None), 3)
                if any(r["pc_dist"] is not None for r in grp) else None),
            "dispersion_mediana_del_centroide_km": disp,
        }
    return out


# ---------------------------------------------------------------- sustrato: que campo varia
CANDIDATOS = ["t_bg_k", "t_max_k", "n_anomalous_pixels", "test1_k_observed", "diag_nti_max",
              "diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path", "diag_n_eti_path",
              "pc_vrp", "pc_npix", "pc_dist", "geo_class", "dc", "triggered_test1",
              "f5_core_vrp_mw", "n_excluded_water", "final_hotspot_source"]


def sustrato_de_campos(pub, pub_a, pool):
    """Por campo: cuanto esta poblado sobre lo PUBLICADO, cuanto varia, y cuanto separa.

    POR QUE ESTE ORDEN. Un campo que no esta escrito no puede clasificar nada; uno que esta escrito
    pero vale siempre lo mismo sobre el conjunto donde se hace la pregunta, tampoco (es el caso de
    `geo_class`, que existe y esta poblado, pero sobre lo publicado vale `summit` siempre porque
    publicar EXIGE ser summit). Recien despues tiene sentido preguntar cuanto separa.

    El AUC que se informa es (a) contra el pool, que NO es (b) contra (d): es la unica etiqueta que
    existe. Sirve como COTA: un campo que ni siquiera separa lo que MIROVA confirmo de lo que no,
    menos va a separar una feature real de un artefacto dentro del pool (A83). Que separe bien
    tampoco alcanza, porque el pool sigue mezclado.
    """
    out = {}
    for c in CANDIDATOS:
        vals = [r.get(c) for r in pub]
        pres = [v for v in vals if v is not None]
        distintos = len(set(map(str, pres)))
        fila = {"n_publicadas": len(pub), "n_con_valor": len(pres), "n_valores_distintos": distintos,
                "constante_sobre_lo_publicado": distintos <= 1}
        num_a = [r[c] for r in pub_a if isinstance(r.get(c), (int, float)) and not isinstance(r.get(c), bool)]
        num_p = [r[c] for r in pool if isinstance(r.get(c), (int, float)) and not isinstance(r.get(c), bool)]
        fila["auc_a_vs_pool_global"] = (round(bp.auc(num_a, num_p), 3)
                                        if num_a and num_p and distintos > 1 else None)
        porv = {}
        for v in bp.VOLS:
            na = [r[c] for r in pub_a if r["vol"] == v and isinstance(r.get(c), (int, float))
                  and not isinstance(r.get(c), bool)]
            np_ = [r[c] for r in pool if r["vol"] == v and isinstance(r.get(c), (int, float))
                   and not isinstance(r.get(c), bool)]
            if len(na) >= bp.N_MIN_AUC and len(np_) >= bp.N_MIN_AUC:
                porv[v] = round(bp.auc(na, np_), 3)
        fila["auc_a_vs_pool_por_volcan"] = porv
        out[c] = fila
    return out


def caminos(pub_a, pool):
    """La unica informacion de CAMINO que queda viva: Test 1 y dNTI contextual."""
    def tab(xs):
        return dict(collections.Counter(
            f"test1={bool(r.get('triggered_test1'))}|dnti_ctx={(r.get('diag_n_dnti_ctx_path') or 0) > 0}"
            for r in xs))
    return {"a": tab(pub_a), "pool": tab(pool)}


def _inventario_geo_class():
    """geo_class sobre TODA la historia de los 45 volcanes, no solo la ventana.

    Sirve para una sola afirmacion del informe: cuantas veces en la vida del proyecto el campo
    llego a valer "extension". El denominador va al lado (A90).
    """
    c = collections.Counter()
    ext = []
    for f in sorted(bp.DATA.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d.get("records", []):
            pc = r.get("primary_cluster") or {}
            c[str(pc.get("geo_class"))] += 1
            if pc.get("geo_class") == "extension":
                ext.append(f"{f.stem}|{r.get('datetime_utc')}|{r.get('sensor')}")
    return {"n_records_todos_los_volcanes": sum(c.values()), "reparto": dict(c),
            "n_con_geo_class": sum(v for k, v in c.items() if k != "None"),
            "extension_una_por_una": ext}


def _agrupar(xs, clave):
    d = collections.defaultdict(list)
    for x in xs:
        d[clave(x)].append(x)
    return d


# ---------------------------------------------------------------- catalogo de features (b)
def cerca_de_feature(r, features):
    """Unico campo que hoy sostiene la categoria (b) por si solo: distancia a feature catalogada."""
    for f in features.get(r["vol"], []):
        if r["pc_lat"] is None:
            return False
        if _haversine_km(r["pc_lat"], r["pc_lon"], f["lat"], f["lon"]) <= f.get("ext_km", 2.0):
            return True
    return False


# ---------------------------------------------------------------- reparto principal
def reparto(recs, features, noches_alerta_volcan):
    """Las pasadas PUBLICADAS, repartidas por lo que la referencia permite afirmar."""
    pub = [r for r in recs if r["pub"]]
    filas = {}
    for r in pub:
        if r["lab"] == "pos":
            cat = "a_mirova_publico_esa_pasada"
        elif (r["vol"], r["noche"]) in noches_alerta_volcan:
            cat = "a_probable_misma_noche_otra_pasada"
        elif r["lab"] == "far_ref":
            cat = "sin_informacion_mirova_vio_fuera_del_limite"
        else:
            cat = "bcd_indistinguible"
        r["cat"] = cat
    for clave, grp in sorted(_agrupar(pub, lambda r: (r["vol"], r["b"])).items()):
        filas[f"{clave[0]}|{clave[1]}"] = dict(collections.Counter(r["cat"] for r in grp))
    total = dict(collections.Counter(r["cat"] for r in pub))
    por_sensor = {b: dict(collections.Counter(r["cat"] for r in pub if r["b"] == b))
                  for b in bp.BUCKETS}
    por_volcan = {v: dict(collections.Counter(r["cat"] for r in pub if r["vol"] == v))
                  for v in bp.VOLS}
    # El unico apoyo POSITIVO de (b) que existe en el dato: geo_class=extension, o cercania a una
    # feature catalogada. Se cuenta sobre el pool indistinguible.
    pool = [r for r in pub if r["cat"] == "bcd_indistinguible"]
    apoyo_b = {
        "n_pool": len(pool),
        "geo_class_extension": sum(1 for r in pool if r["geo_class"] == "extension"),
        "cerca_de_feature_catalogada": sum(1 for r in pool if cerca_de_feature(r, features)),
        "geo_class_reparto": dict(collections.Counter(str(r["geo_class"]) for r in pool)),
        "sin_primary_cluster": sum(1 for r in pool if not r["tiene_pc"]),
    }
    return pub, pool, {"total": total, "por_sensor": por_sensor, "por_volcan": por_volcan,
                       "por_volcan_y_sensor": filas, "apoyo_positivo_de_b": apoyo_b}


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inicio", default=INICIO_S145)
    ap.add_argument("--fin", default=FIN_S145)
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    filas_ref = bp.cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas_ref, coords, ventana)

    # A110 / P2 del instrumento: antes de leer nada, el predicado tiene que ser el del dashboard.
    identidad = bp.control_identidad_predicado()
    ok_identidad = (identidad == ([0, 1, 1, 1, 0], [1, 0]))

    recs = cargar_extendido(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    # P1: el cargador de este script es una copia del recorrido del banco. Si divergio, los totales
    # no coinciden y todo lo de abajo mide otra cosa. Se compara contra el banco corrido de verdad.
    del_banco = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(del_banco, por_vb, ns, nv)
    control_copia = {
        "n_records": [len(recs), len(del_banco)],
        "n_publicadas": [sum(r["pub"] for r in recs), sum(r["pub"] for r in del_banco)],
        "etiquetas": [dict(collections.Counter(r["lab"] for r in recs)),
                      dict(collections.Counter(r["lab"] for r in del_banco))],
    }
    control_copia["coincide"] = (control_copia["n_records"][0] == control_copia["n_records"][1]
                                 and control_copia["n_publicadas"][0] == control_copia["n_publicadas"][1]
                                 and control_copia["etiquetas"][0] == control_copia["etiquetas"][1])

    features = yaml.safe_load(FEATURES_YAML.read_text(encoding="utf-8")) or {}
    noches_alerta_volcan = {k for k, v in nv.items() if v["alerta"]}

    pub, pool, rep = reparto(recs, features, noches_alerta_volcan)
    pub_a = [r for r in pub if r["cat"].startswith("a_")]

    por_sensor_reglas = {b: ([r for r in pub_a if r["b"] == b], [r for r in pool if r["b"] == b])
                         for b in bp.BUCKETS}
    por_volcan_reglas = {v: ([r for r in pub_a if r["vol"] == v], [r for r in pool if r["vol"] == v])
                         for v in bp.VOLS}

    out = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana": {"inicio": a.inicio, "fin": a.fin,
                    "por_que": "el regimen actual empieza con el PR #571 (2026-08-31); "
                               "una ventana que lo cruce mezcla dos regimenes (A104)"},
        "procedencia": {"referencia": {k: v["sha"] for k, v in info.items()},
                        "sha_index_html": bp.sha_git(bp.HTML),
                        "sha_store_py": bp.sha_git(ROOT / "pipeline" / "store.py"),
                        "sha_volcanic_features_yaml": bp.sha_git(FEATURES_YAML),
                        "inner_radius_km": inner},
        "controles": {
            "identidad_predicado_node": identidad,
            "identidad_predicado_ok": ok_identidad,
            "copia_del_cargador_coincide_con_banco": control_copia,
        },
        "definiciones": {
            "publicada": "predicado del dashboard de frontend/index.html ejecutado con node (A97): "
                         "isSummitDetection && isValidDetection && !isThermalArtifact && display>0",
            "a_mirova_publico_esa_pasada": "etiqueta `pos` del banco: fila ALERTA de MIROVA "
                                           "(consolidado u OCR) nocturna a +-2 min de esa pasada",
            "a_probable_misma_noche_otra_pasada": "no hay ALERTA en esa pasada pero SI en la misma "
                                                  "noche de ese volcan, en cualquier sensor: el "
                                                  "evento es el mismo, la pasada no es un extra",
            "bcd_indistinguible": "publicamos, MIROVA no alerto ni esa pasada ni esa noche. "
                                  "Aca viven (b), (c) y (d) MEZCLADAS: no hay etiqueta por record",
            "pool": "el conjunto bcd_indistinguible, que es sobre el que se prueban las reglas",
        },
        "cobertura": {
            "n_records_nocturnos": len(recs),
            "n_publicadas": len(pub),
            "n_filas_referencia_nocturnas": n_ref,
            "etiquetas_del_banco_sobre_todos": dict(collections.Counter(r["lab"] for r in recs)),
            "no_publicadas_por_artefacto_termico_del_frontend": sum(
                1 for r in recs if r["art_js"]),
            "no_publicadas_por_artefacto_por_volcan": dict(collections.Counter(
                r["vol"] for r in recs if r["art_js"])),
        },
        "reparto": rep,
        "reglas_candidatas_de_artefacto": {
            "que_es_esto": "NO es un reparto de (d). Es el costo medido de cada regla sobre el "
                           "unico estrato con etiqueta conocida (las pasadas que MIROVA confirmo, "
                           "reales sin discusion). Una regla que destruye una fraccion apreciable "
                           "de esas esta refutada como discriminante (A110).",
            "global": costo_de_las_reglas(pub_a, pool),
            "por_sensor": costo_de_las_reglas(pub_a, pool, ("sensor", por_sensor_reglas)),
            "por_volcan": costo_de_las_reglas(pub_a, pool, ("volcan", por_volcan_reglas)),
        },
        # Las fracciones que cita el informe se calculan ACA, no a mano (S91).
        "titulares": {
            "frac_publicadas_de_las_nocturnas": round(len(pub) / len(recs), 4),
            "frac_publicadas_atribuibles_a_mirova": round(len(pub_a) / len(pub), 4),
            "frac_publicadas_en_el_pool_bcd": round(len(pool) / len(pub), 4),
            "frac_del_pool_con_apoyo_positivo_de_b": round(
                rep["apoyo_positivo_de_b"]["cerca_de_feature_catalogada"] / len(pool), 4),
            "n_volcanes_sin_una_sola_pasada_atribuible_a_mirova": sum(
                1 for v in bp.VOLS if not any(r["vol"] == v for r in pub_a)),
            "volcanes_sin_una_sola_pasada_atribuible_a_mirova": [
                v for v in bp.VOLS if not any(r["vol"] == v for r in pub_a)],
            "n_pares_volcan_sensor_que_publican_todas_las_noches": None,  # se llena abajo
        },
        # Los agregados que el informe pone en tablas. Van acá para que ninguna suma se haga a
        # mano al escribirlo (S91): una suma de columnas tambien es un numero transcrito.
        "tablas_del_informe": {
            "por_sensor": {b: {"publicadas": sum(1 for r in pub if r["b"] == b),
                               "a": sum(1 for r in pub_a if r["b"] == b),
                               "fuera_de_limite": sum(1 for r in pub if r["b"] == b and r["cat"].startswith("sin_info")),
                               "pool": sum(1 for r in pool if r["b"] == b)} for b in bp.BUCKETS},
            "por_volcan": {v: {"inner_radius_km": inner[v],
                               "publicadas": sum(1 for r in pub if r["vol"] == v),
                               "a": sum(1 for r in pub_a if r["vol"] == v),
                               "pool": sum(1 for r in pool if r["vol"] == v)} for v in bp.VOLS},
            "n_noches_de_la_ventana": len({r["noche"] for r in recs}),
        },
        # Como quedaria repartido lo publicado bajo la clasificacion que propone el informe: los
        # cuatro valores salen del eje de referencia, que es el unico con etiqueta (§5.2).
        "reparto_bajo_la_propuesta": dict(collections.Counter(
            ("mirova_confirmed" if r["cat"] == "a_mirova_publico_esa_pasada" else
             "mirova_same_night" if r["cat"] == "a_probable_misma_noche_otra_pasada" else
             "mirova_saw_outside" if r["cat"].startswith("sin_info") else
             "mirova_silent" if r["lab"] == "neg_limpio" else "no_reference")
            for r in pub)),
        "inventario_historico_geo_class": _inventario_geo_class(),
        "sustrato_de_campos": sustrato_de_campos(pub, pub_a, pool),
        "caminos_de_deteccion": caminos(pub_a, pool),
        "permanencia_del_sitio_publicado": permanencia(pub, recs),
        "catalogo_volcanic_features": {
            "volcanes_con_entrada": sorted(features.keys()),
            "n_features": sum(len(v) for v in features.values()),
            "de_11_tier_a": len([v for v in features if v in bp.VOLS]),
        },
    }
    perm = out["permanencia_del_sitio_publicado"]
    out["titulares"]["n_pares_volcan_sensor_que_publican_todas_las_noches"] = sum(
        1 for v in perm.values() if v["n_noches_publicadas"] == v["n_noches_con_pasada"])
    out["titulares"]["n_pares_volcan_sensor"] = len(perm)
    out["titulares"]["viirs375_publica_todas_las_noches_en_n_volcanes"] = sum(
        1 for k, v in perm.items()
        if k.endswith("|VIIRS375") and v["n_noches_publicadas"] == v["n_noches_con_pasada"])
    SALIDA.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"escrito {SALIDA}")
    print(f"ventana {a.inicio} a {a.fin} | identidad del predicado ok: {ok_identidad} | "
          f"copia del cargador coincide: {control_copia['coincide']}")
    print(f"\n{len(pub)} pasadas publicadas de {len(recs)} nocturnas. Reparto: {rep['total']}")
    print(f"\napoyo positivo de (b) en el pool: {rep['apoyo_positivo_de_b']}")
    print(f"\n{'volcan':<22}{'sensor':>10}{'publ':>7}{'a':>6}{'a_noche':>9}{'pool':>7}")
    for k, v in sorted(rep["por_volcan_y_sensor"].items()):
        vol, b = k.split("|")
        n = sum(v.values())
        print(f"{vol:<22}{b:>10}{n:>7}{v.get('a_mirova_publico_esa_pasada', 0):>6}"
              f"{v.get('a_probable_misma_noche_otra_pasada', 0):>9}"
              f"{v.get('bcd_indistinguible', 0):>7}")
    print(f"\n{'campo':<26}{'con valor':>11}{'distintos':>11}{'AUC a vs pool':>15}")
    for c, v in out["sustrato_de_campos"].items():
        print(f"{c:<26}{v['n_con_valor']:>7}/{len(pub):<4}{v['n_valores_distintos']:>11}"
              f"{(v['auc_a_vs_pool_global'] if v['auc_a_vs_pool_global'] is not None else float('nan')):>15.3f}")
    print(f"\ncaminos: {out['caminos_de_deteccion']}")
    print(f"\n{'regla candidata':<32}{'destruye de (a)':>17}{'marca del pool':>17}")
    for nombre, v in out["reglas_candidatas_de_artefacto"]["global"].items():
        print(f"{nombre:<32}{v['marcadas_en_a']:>7}/{v['n_a']:<9}"
              f"{v['marcadas_en_resto']:>7}/{v['n_resto']:<9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
