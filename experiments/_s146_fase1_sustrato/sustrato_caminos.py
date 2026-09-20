# -*- coding: utf-8 -*-
"""Fase 1 del plan de paridad S146: que camino de deteccion sostiene la sobre-publicacion y cual
sostiene el recall. SOLO LECTURA: no escribe nada fuera de experiments/_s146_fase1_sustrato/.

QUE HACE. Reutiliza SIN reescribir el banco de paridad (scripts/banco_paridad.py): mismas etiquetas
(pos, neg_limpio, far_ref, sin_info), mismo predicado del dashboard ejecutado con node, misma
referencia que uso S145 (los dos CSV bajados en experiments/_s145_paridad/_dl_referencia, sin red).
Encima agrega, por pasada, la CLASE DE SOSTEN, derivada de como el codigo arma el cumulo publicado
(pipeline/process_viirs.py l. 1299, 1585, 1763-1786, 2085 y pipeline/anchor.py l. 67-89):

  * con ENABLE_FIRST_PASS_TESTS_2_AND_3 = True, la mascara caliente ES el primer pase (Tests 2 y 3
    con compuerta bt > t_bg + 3 K) mas la recaptura del segundo pase (sin compuerta). Los contadores
    diag_n_dnti_ctx_path / diag_n_bt_path / diag_n_nti_path son DIAGNOSTICOS: esos caminos legacy se
    calculan pero NO entran a la mascara (comentario del propio codigo, l. 1237).
  * el Test 1 integrado NO entra a la mascara: compite por la FUENTE del cumulo publicado.
  * `final_hotspot_source` persistido dice quien gano el ancla:
      test1_roi / test1  -> no habia cumulo contextual, o estaba fuera del inner: sin el Test 1 la
                            pasada queda sin cumulo o con clase far, y el dashboard no la publica.
      ctx_cluster / eruption -> hay cumulo contextual. Si el centroide del cumulo publicado es el
                            mismo que el ancla, el cumulo publicado ES el contextual (el Test 1 no
                            aporta). Si difiere, el Test 1 reconstruyo el cumulo encima de uno
                            contextual (regla del cumulo rival debil, < 0,01 MW, o fuente unica).

TRES NIVELES DE EVIDENCIA, separados en la salida:
  N1 participo   : contador > 0 (triggered_test1, diag_n_first_pass_pixels, diag_n_second_pass_recapture,
                   diag_n_dnti_ctx_path, diag_n_bt_path, diag_n_nti_path).
  N2 unico       : los demas en cero.
  N3 dependencia : por la LOGICA del codigo sobre campos persistidos (no por re-ejecucion):
                   T1_SOLO      = sin Test 1 no se publica (deterministico en VIIRS; en MODIS queda
                                  la salvedad del rescate de store.py, se declara).
                   CTX_SOLO     = cumulo contextual y Test 1 no disparo: sin Tests 2 y 3 no se publica.
                   AMBOS        = cumulo contextual publicado y Test 1 disparo: apagar el Test 1 no
                                  cambia la publicacion; apagar el contextual, SIN DATO.
                   T1_SOBRE_CTX = Test 1 reconstruyo el cumulo sobre uno contextual: sin Test 1,
                                  SIN DATO (publicaria solo si el contextual tenia > 0 MW; en el
                                  subcaso rival debil, con menos de 0,01 MW).
                   Lo que NO se puede simular desde lo persistido: quitar la compuerta de 3 K, quitar
                   el segundo pase, cambiar el fondo. Queda SIN DATO y se especifica el probe.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  P1 (si lo que mido estuviera roto, fallaria?): control positivo: con la misma referencia y el
     corte de procesamiento de S145 tengo que reproducir 0,8633 / 0,2138 / 0,1142 y los n 373 / 622 /
     438; el vector `pub` de mi carga debe ser identico al de bp.cargar_nuestros. Control de
     coherencia del clasificador: toda pasada T1_SOBRE_CTX y T1_SOLO debe tener triggered_test1 =
     True; si aparece una con False, el clasificador esta mal y el script ABORTA.
  P2 (si el instrumento estuviera muerto, se veria distinto?): el nulo baraja las etiquetas pos /
     neg_limpio dentro de cada volcan y sensor (1000 veces): si el contraste observado cae dentro del
     nulo, es ruido. Y un clasificador muerto (todo a una clase) daria contraste 0 exacto y una sola
     clase en la tabla: se ve.
"""
from __future__ import annotations

import collections
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

AQUI = Path(__file__).resolve().parent
REF = ROOT / "experiments" / "_s145_paridad" / "_dl_referencia"
BANCO_S145 = ROOT / "experiments" / "_s145_paridad" / "banco_s145.json"
VENTANA = ("2026-09-01", "2026-09-20")
CORTE_S145 = "2026-09-20T04:55:46Z"  # generado_utc del banco S145
N_NULO = 1000
DIAG = ["triggered_test1", "n_test1_pixels", "test1_k_observed", "diag_n_bt_path", "diag_n_nti_path",
        "diag_n_dnti_ctx_path", "diag_n_eti_path", "diag_n_first_pass_pixels",
        "diag_n_first_pass_summit", "diag_n_second_pass_recapture", "t_bg_k", "diag_sigma_bg_k",
        "final_hotspot_source", "final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km",
        "hotspot_dist_km", "distance_class", "processed_utc", "sensor", "datetime_utc",
        "n_anomalous_pixels", "f5_core_vrp_mw", "discarded_reason"]


def cargar(coords, inner):
    """Copia del bucle de bp.cargar_nuestros que ademas conserva los diagnosticos del record."""
    recs, casos = [], []
    for vol in bp.VOLS:
        with open(bp.DATA / f"{vol}.json", encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            if b is None or not (VENTANA[0] <= r.get("datetime_utc", "")[:10] <= VENTANA[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                   "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                   "pc_dist": pc.get("centroid_dist_km"), "z": r.get("sensor_zenith_deg"),
                   "pc": pc, "diag": {k: r.get(k) for k in DIAG}}
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def clase_sosten(r):
    """Clase de sosten de una pasada PUBLICADA. Devuelve (clase, subclase)."""
    d, pc = r["diag"], r["pc"]
    src = d["final_hotspot_source"]
    t1 = d["triggered_test1"] is True
    if src in ("test1_roi", "test1", "test1_nti_peak"):
        return "T1_SOLO", src
    if src in ("eruption", "eruption_loose"):
        # cascada LEGACY (MODIS, ancla honesta apagada): "eruption" significa que el Test 1 NO gano
        # la fuente, asi que el cumulo publicado es el contextual. Aca final_hotspot es el pixel mas
        # caliente suelto y no el centroide, por eso la igualdad de centroides no aplica (medido:
        # 436 de 440 "eruption" de MODIS difieren sin que el Test 1 haya disparado).
        return ("AMBOS" if t1 else "CTX_SOLO"), src
    if src == "cluster_rescue":
        # store.py reescribio la fuente: no se sabe quien armo el cumulo -> SIN DATO
        return "RESCATE_SIN_DATO", src
    if src == "ctx_cluster":
        mismo = (pc.get("centroid_lat") is not None and d["final_hotspot_lat"] is not None
                 and abs(pc["centroid_lat"] - d["final_hotspot_lat"]) < 1e-5
                 and abs(pc["centroid_lon"] - d["final_hotspot_lon"]) < 1e-5)
        if mismo:
            return ("AMBOS" if t1 else "CTX_SOLO"), src
        sub = ("fuente_unica" if (d["diag_n_dnti_ctx_path"] or 0) == 0 and (d["diag_n_nti_path"] or 0) == 0
               else "rival_debil_lt_0.01MW")
        return "T1_SOBRE_CTX", f"{src}|{sub}"
    return "OTRO", str(src)


def frio(t):
    if t is None:
        return "t_bg?"
    return "lt262" if t < 262 else ("262-270" if t < 270 else "ge270")


def tabla(recs, filtro):
    """Conteos por etiqueta y clase para las pasadas que cumplen filtro."""
    out = {}
    for lab in ("neg_limpio", "pos", "far_ref", "sin_info"):
        sel = [r for r in recs if r["lab"] == lab and filtro(r)]
        pubs = [r for r in sel if r["pub"]]
        c = collections.Counter(r["clase"] for r in pubs)
        out[lab] = {"n": len(sel), "n_pub": len(pubs), "clases_pub": dict(sorted(c.items()))}
    return out


def noches(recs, filtro_sensor):
    """Noches de volcan pos (def. del banco) y que pasa si se apaga el Test 1 / el contextual."""
    nn = collections.defaultdict(list)
    for r in recs:
        if filtro_sensor(r):
            nn[(r["vol"], r["noche"])].append(r)
    res = collections.Counter()
    lista_t1 = []
    for (vol, noche), rs in sorted(nn.items()):
        if not any(r["lab"] == "pos" for r in rs):
            continue
        res["n_noches_pos"] += 1
        pubs = [r for r in rs if r["pub"]]
        if not pubs:
            res["no_publicada_hoy"] += 1
            continue
        res["publicada_hoy"] += 1
        cl = collections.Counter(r["clase"] for r in pubs)
        # sin Test 1: sobreviven seguro CTX_SOLO y AMBOS; T1_SOBRE_CTX es SIN DATO; T1_SOLO cae
        seguro = cl["CTX_SOLO"] + cl["AMBOS"]
        if seguro > 0:
            res["sinT1_sigue_publicada"] += 1
        elif cl["T1_SOBRE_CTX"] > 0:
            res["sinT1_SIN_DATO"] += 1
            lista_t1.append([vol, noche, "SIN_DATO", dict(cl)])
        else:
            res["sinT1_se_pierde"] += 1
            lista_t1.append([vol, noche, "SE_PIERDE", dict(cl)])
        # sin contextual: sobreviven seguro T1_SOLO (no dependen del cumulo contextual)
        if cl["T1_SOLO"] > 0:
            res["sinCTX_sigue_publicada"] += 1
        elif cl["AMBOS"] + cl["T1_SOBRE_CTX"] > 0:
            res["sinCTX_SIN_DATO"] += 1
        else:
            res["sinCTX_se_pierde"] += 1
    return dict(res), lista_t1


def contraste(recs_lab, clase):
    """frac(clase | neg_limpio publicada) - frac(clase | pos publicada)."""
    a = [r for r in recs_lab if r["lab_x"] == "neg_limpio"]
    b = [r for r in recs_lab if r["lab_x"] == "pos"]
    if not a or not b:
        return None
    fa = sum(1 for r in a if r["clase"] == clase) / len(a)
    fb = sum(1 for r in b if r["clase"] == clase) / len(b)
    return fa - fb


def nulo(recs, bsens, clase, rng):
    """Baraja pos/neg_limpio dentro de cada volcan (sensor fijo) entre las pasadas PUBLICADAS."""
    sel = [dict(r, lab_x=r["lab"]) for r in recs
           if r["b"] == bsens and r["pub"] and r["lab"] in ("pos", "neg_limpio")]
    obs = contraste(sel, clase)
    if obs is None:
        return None
    por_vol = collections.defaultdict(list)
    for r in sel:
        por_vol[r["vol"]].append(r)
    vals = []
    for _ in range(N_NULO):
        for rs in por_vol.values():
            labs = [r["lab"] for r in rs]
            rng.shuffle(labs)
            for r, l in zip(rs, labs):
                r["lab_x"] = l
        vals.append(contraste(sel, clase))
    vals.sort()
    return {"observado": round(obs, 4), "nulo_media": round(sum(vals) / len(vals), 4),
            "nulo_p2.5": round(vals[int(0.025 * N_NULO)], 4), "nulo_p97.5": round(vals[int(0.975 * N_NULO)], 4),
            "n_neg_pub": sum(1 for r in sel if r["lab"] == "neg_limpio"),
            "n_pos_pub": sum(1 for r in sel if r["lab"] == "pos"),
            "fuera_del_nulo": bool(obs < vals[int(0.025 * N_NULO)] or obs > vals[int(0.975 * N_NULO)])}


def main():
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    identidad = bp.control_identidad_predicado()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, VENTANA)
    ult = {s: max((f["fecha_utc"] for f in filas if f["source"] == s), default=None) for s in ("CONS", "OCR")}

    recs = cargar(coords, inner)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    # ---- control positivo 1: mi carga == carga del banco (mismo pub, mismo orden)
    recs_bp = bp.cargar_nuestros(coords, inner, VENTANA)
    igual_pub = [r["pub"] for r in recs] == [r["pub"] for r in recs_bp] and len(recs) == len(recs_bp)

    # ---- control positivo 2: reproducir S145 con el corte de procesamiento de S145
    s145 = json.loads(BANCO_S145.read_text(encoding="utf-8"))
    def tasas(sel):
        o = {}
        for b in bp.BUCKETS:
            neg = [r for r in sel if r["b"] == b and r["lab"] == "neg_limpio"]
            o[b] = {"n_neg_limpio": len(neg), "tasa_pub_neg": round(sum(r["pub"] for r in neg) / len(neg), 4) if neg else None,
                    "n_pos": sum(1 for r in sel if r["b"] == b and r["lab"] == "pos")}
        return o
    al_corte = [r for r in recs if (r["diag"]["processed_utc"] or "") <= CORTE_S145]
    ctrl = {"identidad_predicado": identidad == ([0, 1, 1, 1, 0], [1, 0]), "pub_identico_a_bp": igual_pub,
            "s145_publicado": {b: {k: s145["por_sensor"][b]["pasada"][k] for k in ("n_neg_limpio", "tasa_pub_neg", "n_pos")} for b in bp.BUCKETS},
            "hoy_todo": tasas(recs), "hoy_con_corte_processed_utc_s145": tasas(al_corte),
            "n_records_hoy": len(recs), "n_records_al_corte": len(al_corte), "n_records_s145": s145["meta"]["n_records_nocturnos"]}

    # ---- clases
    for r in recs:
        r["clase"], r["sub"] = clase_sosten(r) if r["pub"] else ("NO_PUB", "")
        r["provisorio"] = ult["OCR"] is not None and r["noche"] > ult["OCR"][:10]
    malos = [r for r in recs if r["clase"] in ("T1_SOLO", "T1_SOBRE_CTX") and r["diag"]["triggered_test1"] is not True]
    # control del instrumento "igualdad de centroides": sin Test 1 no puede haber reconstruccion, asi
    # que entre las ctx_cluster con triggered_test1 False la igualdad tiene que dar SIEMPRE True.
    sin_t1 = [r for r in recs if r["diag"]["final_hotspot_source"] == "ctx_cluster" and r["diag"]["triggered_test1"] is not True and r["pc"]]
    ctrl["control_centroides_ctx_sin_t1"] = {"n": len(sin_t1), "n_centroide_distinto": sum(
        1 for r in sin_t1 if not (abs(r["pc"]["centroid_lat"] - r["diag"]["final_hotspot_lat"]) < 1e-5
                                  and abs(r["pc"]["centroid_lon"] - r["diag"]["final_hotspot_lon"]) < 1e-5))}
    ctrl["coherencia_clasificador_T1_sin_trigger"] = len(malos)
    ctrl["ejemplos_incoherentes"] = [[r["vol"], r["b"], r["diag"]["datetime_utc"], r["clase"], r["sub"]] for r in malos[:10]]

    res = {"meta": {"ventana": list(VENTANA), "ultima_fila_ref": ult, "n_filas_ref_nocturnas": n_ref,
                    "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
                    "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "sha_index_html": bp.sha_git(bp.HTML)},
           "controles": ctrl}

    # ---- N1/N2: participacion por contadores, entre publicadas, por sensor y etiqueta
    cont = {}
    for b in bp.BUCKETS:
        cont[b] = {}
        for lab in ("neg_limpio", "pos"):
            pubs = [r for r in recs if r["b"] == b and r["lab"] == lab and r["pub"]]
            c = collections.Counter()
            for r in pubs:
                d = r["diag"]
                t1 = d["triggered_test1"] is True
                fp = (d["diag_n_first_pass_pixels"] or 0) > 0
                sp = (d["diag_n_second_pass_recapture"] or 0) > 0
                c["N1_test1"] += t1; c["N1_primer_pase"] += fp; c["N1_segundo_pase"] += sp
                c["N1_dnti_ctx_diag"] += (d["diag_n_dnti_ctx_path"] or 0) > 0
                c["N1_bt_path"] += (d["diag_n_bt_path"] or 0) > 0
                c["N1_nti_path"] += (d["diag_n_nti_path"] or 0) > 0
                c["N2_solo_test1"] += t1 and not fp and not sp
                c["N2_solo_primer_pase"] += fp and not t1 and not sp
                c["N2_solo_segundo_pase"] += sp and not t1 and not fp
                c["N2_solo_contextual(1o+2o)"] += (fp or sp) and not t1
                c["ninguno_de_los_tres"] += not (t1 or fp or sp)
            cont[b][lab] = {"n_pub": len(pubs), **dict(c)}
    res["N1_N2_contadores"] = cont

    # ---- N3: clases de sosten por sensor (todo / definitivo / provisorio) y por volcan
    res["N3_por_sensor"] = {b: {"todo": tabla(recs, lambda r, b=b: r["b"] == b),
                                "definitivo_hasta_ultimo_OCR": tabla(recs, lambda r, b=b: r["b"] == b and not r["provisorio"]),
                                "provisorio_post_OCR": tabla(recs, lambda r, b=b: r["b"] == b and r["provisorio"]),
                                "sensibilidad_noche_hasta_2026-09-14": tabla(recs, lambda r, b=b: r["b"] == b and r["noche"] <= "2026-09-14")}
                            for b in bp.BUCKETS}
    res["N3_por_volcan"] = {b: {v: tabla(recs, lambda r, b=b, v=v: r["b"] == b and r["vol"] == v) for v in bp.VOLS}
                            for b in bp.BUCKETS}
    res["subclases_pub"] = {b: {lab: dict(collections.Counter(f'{r["clase"]}|{r["sub"]}' for r in recs
                                                              if r["b"] == b and r["lab"] == lab and r["pub"]))
                                for lab in ("neg_limpio", "pos")} for b in bp.BUCKETS}

    # ---- contrafactual "sin Test 1 integrado" (cotas: T1_SOBRE_CTX y RESCATE son SIN DATO)
    cf = {}
    for b in bp.BUCKETS:
        for corte, f in (("todo", lambda r: True), ("hasta_2026-09-14", lambda r: r["noche"] <= "2026-09-14")):
            o = {}
            for lab in ("neg_limpio", "pos"):
                sel = [r for r in recs if r["b"] == b and r["lab"] == lab and f(r)]
                c = collections.Counter(r["clase"] for r in sel if r["pub"])
                n = len(sel)
                seguro = c["CTX_SOLO"] + c["AMBOS"]
                duda = c["T1_SOBRE_CTX"] + c["RESCATE_SIN_DATO"] + c["OTRO"]
                o[lab] = {"n": n, "pub_hoy": sum(c.values()), "tasa_hoy": bp._tasa(sum(c.values()), n),
                          "T1_SOLO": c["T1_SOLO"], "frac_T1_SOLO_de_lo_publicado": bp._tasa(c["T1_SOLO"], sum(c.values())),
                          "sinT1_pub_min": seguro, "sinT1_pub_max": seguro + duda,
                          "sinT1_tasa_min": bp._tasa(seguro, n), "sinT1_tasa_max": bp._tasa(seguro + duda, n),
                          "sinCTX_pub_seguro(T1_SOLO)": c["T1_SOLO"], "CTX_SOLO": c["CTX_SOLO"],
                          "frac_CTX_SOLO_de_lo_publicado": bp._tasa(c["CTX_SOLO"], sum(c.values()))}
            cf.setdefault(b, {})[corte] = o
    res["contrafactual_sin_test1"] = cf
    res["frac_T1_SOLO_por_volcan"] = {b: {v: {lab: (lambda pubs: {"n_pub": len(pubs), "T1_SOLO": sum(1 for r in pubs if r["clase"] == "T1_SOLO"),
                                                                     "CTX_SOLO": sum(1 for r in pubs if r["clase"] == "CTX_SOLO")})(
                                              [r for r in recs if r["b"] == b and r["vol"] == v and r["lab"] == lab and r["pub"]])
                                              for lab in ("neg_limpio", "pos")} for v in bp.VOLS} for b in bp.BUCKETS}
    # ---- sustrato de los caminos legacy sobre TODAS las pasadas nocturnas de la ventana
    res["sustrato_caminos_legacy_todas_las_pasadas"] = {b: {
        "n": sum(1 for r in recs if r["b"] == b),
        "diag_n_bt_path>0": sum(1 for r in recs if r["b"] == b and (r["diag"]["diag_n_bt_path"] or 0) > 0),
        "diag_n_nti_path>0": sum(1 for r in recs if r["b"] == b and (r["diag"]["diag_n_nti_path"] or 0) > 0),
        "diag_n_eti_path>0": sum(1 for r in recs if r["b"] == b and (r["diag"]["diag_n_eti_path"] or 0) > 0),
        "triggered_test1": sum(1 for r in recs if r["b"] == b and r["diag"]["triggered_test1"] is True),
        "d9_capped": sum(1 for r in recs if r["b"] == b and r["pc"].get("d9_capped")),
        "d9_capped_y_publicada": sum(1 for r in recs if r["b"] == b and r["pc"].get("d9_capped") and r["pub"])} for b in bp.BUCKETS}

    # ---- recall por NOCHE
    res["noches_recall"] = {}
    for b in bp.BUCKETS + [None]:
        r_, lista = noches(recs, (lambda r, b=b: b is None or r["b"] == b))
        res["noches_recall"][b or "CUALQUIERA"] = {"resumen": r_, "noches_que_dependen_de_T1": lista}
    res["noches_recall_por_volcan_CUALQUIERA"] = {v: noches(recs, lambda r, v=v: r["vol"] == v)[0] for v in bp.VOLS}

    # ---- nulo
    rng = random.Random(146)
    res["nulo_barajado_dentro_de_volcan"] = {b: {cl: nulo(recs, b, cl, rng) for cl in ("T1_SOLO", "CTX_SOLO", "AMBOS", "T1_SOBRE_CTX")}
                                             for b in bp.BUCKETS}

    # ---- fondo frio (Fase 3)
    ff = {}
    for b in bp.BUCKETS:
        ff[b] = {}
        for lab in ("neg_limpio", "pos"):
            sel = [r for r in recs if r["b"] == b and r["lab"] == lab]
            o = {}
            for k in ("lt262", "262-270", "ge270", "t_bg?"):
                s2 = [r for r in sel if frio(r["diag"]["t_bg_k"]) == k]
                pubs = [r for r in s2 if r["pub"]]
                o[k] = {"n": len(s2), "n_pub": len(pubs),
                        "clases_pub": dict(collections.Counter(r["clase"] for r in pubs)),
                        "d9_capped_pub": sum(1 for r in pubs if r["pc"].get("d9_capped")),
                        "pub_por_volcan": dict(collections.Counter(r["vol"] for r in pubs))}
            ff[b][lab] = o
    res["fondo_frio"] = ff

    # ---- magnitud publicada por clase (mediana), para saber de que tamano es lo que sostiene cada camino
    def med(xs):
        xs = sorted(xs)
        return round(xs[len(xs) // 2], 4) if xs else None
    res["mediana_disp_mw"] = {b: {lab: {cl: {"n": len(v), "mediana": med(v)} for cl, v in
                                        ((cl, [r["disp"] for r in recs if r["b"] == b and r["lab"] == lab and r["clase"] == cl])
                                         for cl in ("T1_SOLO", "CTX_SOLO", "AMBOS", "T1_SOBRE_CTX"))}
                                  for lab in ("neg_limpio", "pos")} for b in bp.BUCKETS}

    out = AQUI / "resultados_sustrato.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("CONTROLES", json.dumps(ctrl, ensure_ascii=False, indent=1))
    if malos:
        print("ABORTO: clasificador incoherente"); return 2
    print("META", json.dumps(res["meta"], ensure_ascii=False))
    for b in bp.BUCKETS:
        print("==", b)
        for corte in ("todo", "definitivo_hasta_ultimo_OCR", "provisorio_post_OCR"):
            t = res["N3_por_sensor"][b][corte]
            print("  ", corte, {k: t[k] for k in ("neg_limpio", "pos")})
        print("   noches:", res["noches_recall"][b]["resumen"])
        print("   nulo:", res["nulo_barajado_dentro_de_volcan"][b])
    print("CONTRAFACTUAL sin Test 1:", json.dumps(res["contrafactual_sin_test1"], ensure_ascii=False))
    print("SUSTRATO legacy:", json.dumps(res["sustrato_caminos_legacy_todas_las_pasadas"], ensure_ascii=False))
    print("== CUALQUIERA noches:", res["noches_recall"]["CUALQUIERA"])
    print("->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
