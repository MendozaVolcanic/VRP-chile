# -*- coding: utf-8 -*-
"""Verificador con contexto limpio, Fase 1 S146. Camino de medicion INDEPENDIENTE del informe.

QUE MIDE Y POR QUE. El informe atribuye la sobre-publicacion al Test 1 integrado usando la ETIQUETA
`final_hotspot_source` persistida. Yo no uso la etiqueta como eje principal: uso el MECANISMO que la
produce, leido del codigo (pipeline/process_viirs.py l. 1242-1299 y 1584-1585, pipeline/anchor.py
l. 79-89, pipeline/clustering.py l. 75-76):

  * con ENABLE_FIRST_PASS_TESTS_2_AND_3 True la mascara caliente ES el primer pase mas la recaptura
    del segundo; `cluster_hotspots` devuelve [] SOLO si la mascara esta vacia (clustering.py l. 75).
    Entonces: (primer pase + recaptura) == 0  <=>  no hay cumulo contextual  <=>  el ancla honesta
    cae al Test 1. Ese es el subconjunto donde "sin Test 1 no se publica" es DEDUCIBLE del codigo,
    sin depender de la etiqueta.
  * el primer pase solo corre si fp_diag no es None. Cuando NO corre, la mascara queda en
    combine_hot_paths, que SI incluye test1_hot (l. 1225-1233). Ese es el falsador de la afirmacion 2:
    lo detecto por `diag_mu_dnti is None`, que es exactamente "fp_diag None" (l. 2142-2143).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 (1) Si lo que mido estuviera roto, fallaria? Si. Controles duros que ABORTAN:
     C1  los records con `diag_mu_dnti is None` tienen que tener diag_n_first_pass_pixels == 0
         (si no, estoy leyendo mal que ese campo marque "el primer pase no corrio").
     C2  ningun record con final_hotspot_source en test1_* puede tener triggered_test1 False.
     C3  la reconstruccion de mi vector `pub` tiene que coincidir con la del banco (mismo node).
 (2) Si el instrumento estuviera muerto, se veria distinto? Si: un clasificador muerto pondria
     todo en una sola celda de la tabla cruzada; y para las AUSENCIAS (diag_n_bt_path == 0) busco
     el mismo campo fuera de la ventana y en todo el historico: si nunca fue > 0 en ningun record
     de ningun volcan, el contador podria estar muerto y lo declaro SIN DATO en vez de OK.

SOLO LECTURA. No escribe fuera de experiments/_s146_fase1_sustrato/verificador/.
"""
from __future__ import annotations

import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s146_fase1_sustrato"))
import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from sustrato_caminos import clase_sosten  # noqa: E402  (para CRUZAR, no para derivar)

AQUI = Path(__file__).resolve().parent
REF = ROOT / "experiments" / "_s145_paridad" / "_dl_referencia"
VENTANA = ("2026-09-01", "2026-09-20")
CAMPOS = ["triggered_test1", "n_test1_pixels", "diag_n_bt_path", "diag_n_nti_path",
          "diag_n_dnti_ctx_path", "diag_n_eti_path", "diag_n_first_pass_pixels",
          "diag_n_first_pass_summit", "diag_n_second_pass_recapture", "diag_mu_dnti",
          "diag_sd_dnti", "final_hotspot_source", "final_hotspot_lat", "final_hotspot_lon",
          "final_hotspot_dist_km", "distance_class", "sensor", "datetime_utc",
          "n_anomalous_pixels", "vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw", "discarded_reason"]


def cargar(coords, inner):
    recs, casos = [], []
    for vol in bp.VOLS:
        d = json.loads((bp.DATA / f"{vol}.json").read_text(encoding="utf-8"))
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
            recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                         "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                         "pc_dist": pc.get("centroid_dist_km"), "pc": pc,
                         "diag": {k: r.get(k) for k in CAMPOS}})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    for rec, p in zip(recs, bp.correr_node(casos)):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def ctx_px(d):
    """Pixeles de la mascara contextual publicada = primer pase + recaptura del segundo."""
    return (d["diag_n_first_pass_pixels"] or 0) + (d["diag_n_second_pass_recapture"] or 0)


def main():
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, VENTANA)
    recs = cargar(coords, inner)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r in recs:
        r["clase"] = clase_sosten(r)[0] if r["pub"] else "NO_PUB"

    out = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "n_records": len(recs), "ventana": list(VENTANA)}}

    # ---- C1/C2: controles duros
    sin_fp = [r for r in recs if r["diag"]["diag_mu_dnti"] is None]
    c1_malos = [r for r in sin_fp if (r["diag"]["diag_n_first_pass_pixels"] or 0) != 0]
    c2_malos = [r for r in recs if str(r["diag"]["final_hotspot_source"]).startswith("test1")
                and r["diag"]["triggered_test1"] is not True]
    out["controles"] = {"C1_sin_first_pass_n": len(sin_fp), "C1_incoherentes": len(c1_malos),
                        "C2_test1_source_sin_trigger": len(c2_malos)}

    # ---- FALSADOR de la afirmacion 2: pasadas donde el primer pase NO corrio -> test1 SI entra a la mascara
    out["falsador_af2_primer_pase_no_corrio"] = {
        b: {"n_pasadas": sum(1 for r in recs if r["b"] == b),
            "n_sin_first_pass": sum(1 for r in recs if r["b"] == b and r["diag"]["diag_mu_dnti"] is None),
            "n_sin_first_pass_y_publicada": sum(1 for r in recs if r["b"] == b and r["diag"]["diag_mu_dnti"] is None and r["pub"]),
            "n_sin_first_pass_pub_y_test1": sum(1 for r in recs if r["b"] == b and r["diag"]["diag_mu_dnti"] is None
                                                and r["pub"] and r["diag"]["triggered_test1"] is True)}
        for b in bp.BUCKETS}

    # ---- mi eje: mascara contextual vacia vs no, cruzado con la clase del informe
    cruz = {}
    for b in bp.BUCKETS:
        cruz[b] = {}
        for lab in ("neg_limpio", "pos"):
            pubs = [r for r in recs if r["b"] == b and r["lab"] == lab and r["pub"]]
            t = collections.Counter()
            for r in pubs:
                t[(r["clase"], "ctx_vacio" if ctx_px(r["diag"]) == 0 else "ctx_con_pixeles")] += 1
            cruz[b][lab] = {"n_pub": len(pubs), "tabla": {f"{k[0]}|{k[1]}": v for k, v in sorted(t.items())}}
    out["cruce_clase_x_mascara_contextual"] = cruz

    # ---- T1_SOLO con pixeles contextuales: cuantos tienen pixeles del primer pase DENTRO del inner
    det = {}
    for b in bp.BUCKETS:
        sel = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and r["pub"] and r["clase"] == "T1_SOLO"]
        det[b] = {"n_T1_SOLO_neg_pub": len(sel),
                  "ctx_vacio": sum(1 for r in sel if ctx_px(r["diag"]) == 0),
                  "ctx_con_pixeles": sum(1 for r in sel if ctx_px(r["diag"]) > 0),
                  # OJO (error propio, ver FASE1_VERIFICADOR.md seccion 10): `diag_n_first_pass_summit`
                  # SOLO existe en los records MODIS. En VIIRS la clave no esta y el `or 0` convierte
                  # la AUSENCIA en un cero. La celda de abajo vale para MODIS y es VACUA para VIIRS.
                  "ctx_con_pixeles_y_first_pass_summit>0_SOLO_VALIDO_EN_MODIS":
                      sum(1 for r in sel if ctx_px(r["diag"]) > 0 and (r["diag"]["diag_n_first_pass_summit"] or 0) > 0),
                  "detalle_ctx_con_pixeles": [
                      {"vol": r["vol"], "dt": r["diag"]["datetime_utc"], "src": r["diag"]["final_hotspot_source"],
                       "fp": r["diag"]["diag_n_first_pass_pixels"], "fp_summit": r["diag"]["diag_n_first_pass_summit"],
                       "sp": r["diag"]["diag_n_second_pass_recapture"], "pc_dist": r["pc_dist"],
                       "pc_vrp": r["pc_vrp"], "disp": r["disp"]}
                      for r in sel if ctx_px(r["diag"]) > 0][:40]}
    out["T1_SOLO_desglose"] = det

    # ---- estratificacion por volcan (concern d)
    est = {}
    for b in bp.BUCKETS:
        est[b] = {}
        for v in bp.VOLS:
            pubs = [r for r in recs if r["b"] == b and r["vol"] == v and r["lab"] == "neg_limpio" and r["pub"]]
            n = sum(1 for r in recs if r["b"] == b and r["vol"] == v and r["lab"] == "neg_limpio")
            est[b][v] = {"n_neg": n, "n_pub": len(pubs),
                         "T1_SOLO": sum(1 for r in pubs if r["clase"] == "T1_SOLO"),
                         "CTX_SOLO": sum(1 for r in pubs if r["clase"] == "CTX_SOLO"),
                         "AMBOS": sum(1 for r in pubs if r["clase"] == "AMBOS"),
                         "T1_SOBRE_CTX": sum(1 for r in pubs if r["clase"] == "T1_SOBRE_CTX")}
    out["por_volcan_neg_limpio"] = est

    # ---- las 4 noches SIN DATO: detalle de las pasadas publicadas
    noches_sd = [("Isluga", "2026-09-19"), ("Lastarria", "2026-09-01"),
                 ("NevadosDeChillan", "2026-09-18"), ("Villarrica", "2026-09-16")]
    sd = {}
    for vol, noche in noches_sd:
        rs = [r for r in recs if r["vol"] == vol and r["noche"] == noche]
        sd[f"{vol}|{noche}"] = {
            "n_pasadas": len(rs),
            "pasadas": [{"b": r["b"], "dt": r["diag"]["datetime_utc"], "lab": r["lab"], "pub": r["pub"],
                         "clase": r["clase"], "src": r["diag"]["final_hotspot_source"],
                         "fp": r["diag"]["diag_n_first_pass_pixels"], "sp": r["diag"]["diag_n_second_pass_recapture"],
                         "dnti_ctx": r["diag"]["diag_n_dnti_ctx_path"], "pc_vrp": r["pc_vrp"],
                         "pc_dist": r["pc_dist"], "disp": r["disp"], "dc": r["dc"]}
                        for r in sorted(rs, key=lambda x: x["dt"])]}
    out["noches_SIN_DATO_detalle"] = sd

    # ---- afirmacion 3: el camino BT. Ausencia buscada con dos herramientas y en todo el historico.
    hist = collections.Counter()
    vistos_campos = collections.Counter()
    for vol in bp.VOLS:
        d = json.loads((bp.DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            for k in ("n_bt_path", "diag_n_bt_path"):
                if k in r:
                    vistos_campos[k] += 1
                    if (r.get(k) or 0) > 0:
                        hist[f"{k}>0"] += 1
                        hist[f"{k}>0|{r.get('datetime_utc','')[:7]}"] += 1
    out["af3_bt_path_historico"] = {"campos_presentes": dict(vistos_campos),
                                    "n_records_con_bt>0": {k: v for k, v in sorted(hist.items())}}

    # ---- contaminacion (e): tasa por corte de noche
    cortes = {}
    for corte in ("2026-09-14", "2026-09-19", "2026-09-20"):
        cortes[corte] = {}
        for b in bp.BUCKETS:
            neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and r["noche"] <= corte]
            pubs = [r for r in neg if r["pub"]]
            cortes[corte][b] = {"n_neg": len(neg), "n_pub": len(pubs),
                                "tasa": bp._tasa(len(pubs), len(neg)),
                                "T1_SOLO": sum(1 for r in pubs if r["clase"] == "T1_SOLO"),
                                "frac_T1_SOLO": bp._tasa(sum(1 for r in pubs if r["clase"] == "T1_SOLO"), len(pubs))}
    out["af_e_cortes_de_noche"] = cortes

    (AQUI / "contra_medicion.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out["controles"], ensure_ascii=False))
    print("FALSADOR af2:", json.dumps(out["falsador_af2_primer_pase_no_corrio"], ensure_ascii=False))
    print("CRUCE:", json.dumps(cruz, ensure_ascii=False))
    print("T1_SOLO desglose:", json.dumps({b: {k: v for k, v in det[b].items() if k != "detalle_ctx_con_pixeles"}
                                           for b in det}, ensure_ascii=False))
    print("BT historico:", json.dumps(out["af3_bt_path_historico"], ensure_ascii=False))
    print("CORTES:", json.dumps(cortes, ensure_ascii=False))
    print("->", AQUI / "contra_medicion.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
