# -*- coding: utf-8 -*-
"""Pregunta 3: en las pasadas con alerta de MIROVA, que detecta nuestro pipeline, como lo etiqueta, que cumulo elige y
si el tablero lo publica (predicado de frontend/index.html ejecutado con node, A97, via scripts/banco_paridad).
Cuenta cuantas alertas (y protegidas) se pierden o se ganan SOLO por geometria (etiqueta far, radio interno, eleccion
de cumulo) y no por deteccion.

Clasificacion de cada pasada nuestra pareada (misma volcan y sensor, +-120 s) con una alerta de MIROVA:
  publicada            : predicado del tablero = 1.
  perdida_geometria    : hay energia detectada (algun pixel anomalo con vrp > 0, o pc.vrp > 0) pero el predicado da 0 por
                         distance_class far, por pc.centroid_dist_km > inner, o por que el cumulo elegido tiene 0 MW
                         mientras otro pixel si tiene energia (eleccion de cumulo). Se desglosa el motivo.
  perdida_deteccion    : ningun pixel anomalo y ningun cumulo con energia (no es geometria).
  perdida_artefacto    : el predicado la apaga por isThermalArtifact (cirrus / campo difuso).
Y en negativos limpios (MIROVA miro y todas sus filas son RUTINA): cuantas publicamos y DONDE (distancia y rumbo del
cumulo al vent y al centro del TIF).

Fuentes: records de origin/main db0dfe847 (data/ de esta carpeta), referencia unificada local (CONS 2026-10-14, OCR
2026-10-18), regla D-9 SN (minimas de VIIRS 375 <= 0,05 MW cuentan como negativo... en banco_paridad van al estrato
"minima"; aqui se informan aparte y NO entran como alerta), lectura A de protegidas.
Las dos preguntas del instrumento:
  P1: control_identidad_predicado() de banco_paridad debe dar lo que fija tests/test_evaluador_ab_s143.py:603 ([0,1,1,1,0] y [1,0]).
  P2: una pasada con alerta y sin record nuestro va a "sin_record" (no se cuenta como perdida ni como nada).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import median

import comun as C

sys.path.insert(0, str(C.ROOT))
sys.path.insert(0, str(C.ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

SAL = C.AQUI / "03_pareo_geometria_salida.txt"
CSV = C.AQUI / "03_pareo_geometria_pasadas.csv"
JS = C.AQUI / "03_pareo_geometria.json"
VENTANA = ("2026-01-10", "2026-10-21")
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def main():
    ident = BP.control_identidad_predicado()
    # valor esperado = el del guard del repo tests/test_evaluador_ab_s143.py:603 (leido en la sesion), no uno supuesto
    p("P1 control de identidad del predicado:", ident, "OK" if ident == ([0, 1, 1, 1, 0], [1, 0]) else "FALLA")
    coords = {v: (C.GEO[v]["lat"], C.GEO[v]["lon"]) for v in C.VOLS}
    inner = {v: C.GEO[v]["inner_km"] for v in C.VOLS}
    html_inner = BP.inner_desde_html()
    for v in C.VOLS:
        assert html_inner[v] == inner[v], (v, html_inner[v], inner[v])
    p("inner del tablero (frontend/index.html) = volcanoes.yaml:", {v: inner[v] for v in C.VOLS})
    filas = [f for f in cargar_referencia_unificada() if f["volcano"] in C.VOLS]
    por_vb, noche_sensor, noche_volcan, nref = BP.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    p(f"referencia nocturna indexada: {nref} filas en {VENTANA}")
    # nuestros records
    recs, casos = [], []
    ap_por_rec = {}
    for v in C.VOLS:
        d = json.load(open(C.DATA / f"{v}.json", encoding="utf-8"))
        for r in d["records"]:
            b = C.bucket(r.get("sensor"))
            if b is None or not (VENTANA[0] <= r.get("datetime_utc", "")[:10] <= VENTANA[1]):
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if BP.es_pasada_diurna_descartada(b, *coords[v], dt):
                continue
            pc = r.get("primary_cluster") or {}
            ap = r.get("anomaly_pixels") or []
            vent, tc = C.GEO[v]["vent"], C.GEO[v]["tif_centro"]
            rec = {"vol": v, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "hora": r["datetime_utc"],
                   "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                   "pc_n": pc.get("n_pixels"), "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"),
                   "n_ap": len(ap), "ap_vrp_pos": sum(1 for x in ap if (x.get("vrp_mw") or 0) > 0),
                   "ap_min_dvent": min([C.hav_km(x["lat"], x["lon"], *vent) for x in ap if x.get("lat") is not None], default=None),
                   "n_anom": r.get("n_anomalous_pixels"), "vrp_mw": r.get("vrp_mw"), "t1": r.get("triggered_test1"),
                   "fhs": r.get("final_hotspot_source"), "fh_dist": r.get("final_hotspot_dist_km"),
                   "disc": r.get("discarded_reason"), "a46": r.get("diag_a46_relabel"), "z": r.get("sensor_zenith_deg"),
                   "t_max": r.get("t_max_k"), "f5": r.get("f5_core_vrp_mw"), "regimen": (r.get("regimen") or {}).get("perfil")}
            if rec["pc_lat"] is not None:
                rec["pc_dvent"] = C.hav_km(rec["pc_lat"], rec["pc_lon"], *vent)
                rec["pc_rvent"] = C.rumbo_deg(vent[0], vent[1], rec["pc_lat"], rec["pc_lon"])
                rec["pc_dtif"] = C.hav_km(rec["pc_lat"], rec["pc_lon"], *tc)
                rec["pc_rtif"] = C.rumbo_deg(tc[0], tc[1], rec["pc_lat"], rec["pc_lon"])
            else:
                rec["pc_dvent"] = rec["pc_rvent"] = rec["pc_dtif"] = rec["pc_rtif"] = None
            recs.append(rec)
            ap_por_rec[id(rec)] = ap
            slim = {k: r.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: x.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for x in ap]
            casos.append([slim, inner[v]])
    pred = BP.correr_node(casos)
    for rec, pr in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = pr
    BP.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for rec in recs:
        fl = BP.parear(por_vb.get((rec["vol"], rec["b"]), []), rec["dt"])
        al = [f for f in fl if BP.es_alerta(f["tipo"])]
        rec["mir_vrp"] = max((f["vrp_mw"] or 0) for f in al) if al else None
        rec["mir_dist"] = next((f["dist_km"] for f in al if f["dist_km"] is not None), None) if al else None
        rec["mir_src"] = "+".join(sorted(set(f["source"] for f in al))) if al else ""
        rec["mir_tabla"] = any(f["source"] == "CONS" for f in al)
        rec["protegida"] = bool(al) and rec["mir_vrp"] >= C.PROTEGIDA_MW
        rec["tramo"] = C.tramo_a119(rec["hora"], "CONS" if rec["mir_tabla"] else "OCR") if al else ""
        # motivo cuando no publica. "Cerca" = algun pixel anomalo con vrp > 0 a <= inner del vent, o pc con vrp > 0 a <= inner:
        # si toda la energia detectada esta fuera del inner, MIROVA no vio ESO (su Distancia_km esta dentro), asi que es
        # perdida de deteccion con un foco lejano de distractor, no geometria.
        vent = C.GEO[rec["vol"]]["vent"]
        ap_cerca = [x for x in ap_por_rec[id(rec)] if x.get("lat") is not None and C.hav_km(x["lat"], x["lon"], *vent) <= inner[rec["vol"]]]
        rec["ap_cerca_n"] = len(ap_cerca)
        rec["ap_cerca_vrp_pos"] = sum(1 for x in ap_cerca if (x.get("vrp_mw") or 0) > 0)
        rec["ap_cerca_vrp_max"] = max([(x.get("vrp_mw") or 0) for x in ap_cerca], default=None)
        pc_cerca = (rec["pc_vrp"] or 0) > 0 and rec["pc_dvent"] is not None and rec["pc_dvent"] <= inner[rec["vol"]]
        hay_energia = (rec["pc_vrp"] or 0) > 0 or rec["ap_vrp_pos"] > 0
        if rec["pub"]:
            rec["clase"] = "publicada"
        elif rec["art"]:
            rec["clase"] = "perdida_artefacto"
        elif not hay_energia and rec["ap_cerca_n"] == 0:
            rec["clase"] = "perdida_deteccion"
        elif rec["ap_cerca_n"] > 0 and rec["ap_cerca_vrp_pos"] == 0 and not pc_cerca:
            rec["clase"] = "perdida_geometria:pixel_cerca_en_0MW"   # detecto el crater pero su exceso quedo en 0 MW
        elif not pc_cerca and rec["ap_cerca_vrp_pos"] == 0:
            rec["clase"] = "perdida_deteccion:foco_lejano"          # energia solo fuera del inner
        elif (rec["pc_vrp"] or 0) <= 0 or not pc_cerca:
            rec["clase"] = "perdida_geometria:cumulo_elegido_lejos_o_0MW"  # hay pixel con energia cerca y el cumulo elegido es otro
        elif rec["dc"] == "far":
            rec["clase"] = "perdida_geometria:far"
        elif rec["pc_dist"] is not None and rec["pc_dist"] > inner[rec["vol"]]:
            rec["clase"] = "perdida_geometria:pc_fuera_inner"
        elif rec["dc"] is None:
            rec["clase"] = "perdida_geometria:sin_clase"
        else:
            rec["clase"] = "perdida_otro"
    sin_record = BP.alertas_sin_record(por_vb, recs)
    # ---------------- salida
    cols = ["vol", "b", "hora", "lab", "clase", "ap_cerca_n", "ap_cerca_vrp_pos", "ap_cerca_vrp_max", "protegida", "mir_vrp", "mir_dist", "mir_src", "tramo", "pub", "dc", "pc_vrp",
            "pc_n", "pc_dist", "pc_lat", "pc_lon", "mir_tabla", "pc_dvent", "pc_rvent", "pc_dtif", "pc_rtif", "n_ap", "ap_vrp_pos", "ap_min_dvent", "fhs",
            "fh_dist", "disc", "a46", "z", "t_max", "f5", "regimen"]
    lines = [",".join(cols)]
    for r in recs:
        lines.append(",".join("" if r.get(c) is None else (f"{r[c]:.2f}" if isinstance(r[c], float) else str(r[c])) for c in cols))
    CSV.write_text("\n".join(lines), encoding="utf-8")
    res = {}
    for v in C.VOLS:
        p(f"\n==== {v} (inner {inner[v]:g} km; vent a {C.hav_km(*C.GEO[v]['tif_centro'], *C.GEO[v]['vent']):.2f} km del centro del TIF)")
        res[v] = {}
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            R = [r for r in recs if r["vol"] == v and r["b"] == b]
            if not R:
                p(f"  {b}: SIN DATO")
                continue
            labs = Counter(r["lab"] for r in R)
            p(f"  -- {b}: {len(R)} pasadas nocturnas nuestras; etiquetas {dict(labs)}")
            pos = [r for r in R if r["lab"] == "pos"]
            cl = Counter(r["clase"] for r in pos)
            prot = [r for r in pos if r["protegida"]]
            clp = Counter(r["clase"] for r in prot)
            tab = [r for r in pos if r["mir_tabla"]]
            clt = Counter(r["clase"] for r in tab)
            p(f"     alertas pareadas {len(pos)}: {dict(cl)}")
            p(f"       solo tabla (CONS) {len(tab)}: {dict(clt)}")
            p(f"       protegidas {len(prot)}: {dict(clp)}")
            for t in sorted(set(r["tramo"] for r in pos)):
                p(f"       tramo {t}: {dict(Counter(r['clase'] for r in pos if r['tramo']==t))}")
            geo = [r for r in pos if r["clase"].startswith("perdida_geometria")]
            if geo:
                for r in geo:
                    r["ap_detalle"] = [(round(C.hav_km(x["lat"], x["lon"], *C.GEO[r["vol"]]["vent"]), 2), C.octante(C.rumbo_deg(*C.GEO[r["vol"]]["vent"], x["lat"], x["lon"])), x.get("vrp_mw"), x.get("bt_k")) for x in ap_por_rec[id(r)] if x.get("lat") is not None]
                p(f"     perdidas por geometria {len(geo)}: dc {dict(Counter(r['dc'] for r in geo))}; pc_dvent p50 "
                  f"{median([r['pc_dvent'] for r in geo if r['pc_dvent'] is not None] or [float('nan')]):.2f} km; "
                  f"octante pc desde vent {dict(Counter(C.octante(r['pc_rvent']) for r in geo if r['pc_rvent'] is not None))}; "
                  f"ap_min_dvent p50 {median([r['ap_min_dvent'] for r in geo if r['ap_min_dvent'] is not None] or [float('nan')]):.2f} km")
                for r in geo[:12]:
                    p(f"        {r['hora']} MIROVA {r['mir_vrp']} MW @{r['mir_dist']} km [{r['mir_src']}] | {r['clase']} dc={r['dc']} "
                      f"pc {r['pc_vrp']} MW n={r['pc_n']} d_vent {r['pc_dvent'] and round(r['pc_dvent'],2)} {r['pc_rvent'] and C.octante(r['pc_rvent'])} "
                      f"pc_dist {r['pc_dist']} | ap n={r['n_ap']} fhs={r['fhs']} a46={r['a46']} t_bg? t_max {r['t_max']} | pixeles (d_vent, oct, vrp, bt): {r['ap_detalle']}")
            pubpos = [r for r in pos if r["pub"]]
            if pubpos:
                dv = [r["pc_dvent"] for r in pubpos if r["pc_dvent"] is not None]
                dtf = [r["pc_dtif"] for r in pubpos if r["pc_dtif"] is not None]
                p(f"     publicadas con alerta {len(pubpos)}: pc a vent p50 {median(dv):.2f} km, octante desde vent "
                  f"{dict(Counter(C.octante(r['pc_rvent']) for r in pubpos if r['pc_rvent'] is not None).most_common(4))}; "
                  f"pc al centro TIF p50 {median(dtf):.2f} km; MIROVA Distancia_km p50 {median([r['mir_dist'] for r in pubpos if r['mir_dist'] is not None] or [float('nan')]):.2f}")
            neg = [r for r in R if r["lab"] == "neg_limpio"]
            pubneg = [r for r in neg if r["pub"]]
            p(f"     negativos limpios {len(neg)}: publicamos {len(pubneg)} ({100*len(pubneg)/len(neg) if neg else float('nan'):.1f} %)")
            if pubneg:
                dv = [r["pc_dvent"] for r in pubneg if r["pc_dvent"] is not None]
                p(f"       donde: pc a vent p50 {median(dv):.2f} km, <=1,5 km {100*sum(d<=1.5 for d in dv)/len(dv):.0f}%, octante desde vent "
                  f"{dict(Counter(C.octante(r['pc_rvent']) for r in pubneg if r['pc_rvent'] is not None).most_common(5))}; "
                  f"pc a centro TIF p50 {median([r['pc_dtif'] for r in pubneg if r['pc_dtif'] is not None]):.2f} km; "
                  f"dentro de caja 2,63 del centro TIF {100*sum(r['pc_dtif']<=C.CAJA_KM for r in pubneg if r['pc_dtif'] is not None)/len(dv):.0f}%, "
                  f"dentro del anillo 7,88 {100*sum(r['pc_dtif']<=C.ANILLO_KM for r in pubneg if r['pc_dtif'] is not None)/len(dv):.0f}%")
            # far_ref: MIROVA vio un foco lejano
            fr = [r for r in R if r["lab"] == "far_ref"]
            if fr:
                p(f"     far_ref (FALSO_POSITIVO de MIROVA) {len(fr)}: publicamos {sum(r['pub'] for r in fr)}; con energia detectada "
                  f"{sum(1 for r in fr if (r['pc_vrp'] or 0) > 0 or r['ap_vrp_pos'] > 0)}")
            mi = [r for r in R if r["lab"] == "minima"]
            if mi:
                p(f"     minimas SN (VIIRS 375 <= 0,05 MW, no deciden) {len(mi)}: publicamos {sum(r['pub'] for r in mi)}")
            res[v][b] = {"n": len(R), "labs": dict(labs), "pos": dict(cl), "pos_tabla": dict(clt), "protegidas": dict(clp),
                         "neg": len(neg), "neg_pub": len(pubneg)}
    try:
        p("\nalertas de MIROVA sin record nuestro (alertas_sin_record):", len(sin_record) if hasattr(sin_record, "__len__") else sin_record)
        c = Counter()
        for x in (sin_record if isinstance(sin_record, list) else []):
            k = x[0] if isinstance(x, (list, tuple)) else (x.get("vol"), x.get("b")) if isinstance(x, dict) else "?"
            c[str(k)] += 1
        p("  por volcan/sensor:", dict(c))
    except Exception as e:  # noqa: BLE001
        p("alertas_sin_record no legible:", type(e).__name__, e)
    JS.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    SAL.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
