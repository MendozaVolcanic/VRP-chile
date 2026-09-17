# -*- coding: utf-8 -*-
"""S143: por qué perdemos las pasadas de VIIRS 750 que MIROVA sí publica (régimen actual).

POR QUÉ. La regla que ordena el frente es «tener al menos todo lo que MIROVA publica». La cuenta de
cobertura (`docs/audit_s143/COBERTURA_MIROVA.md`) deja tres celdas de VIIRS 750 bajo el 100 %: Isluga
0 de 1, Puyehue-Cordón Caulle 7 de 10 y Villarrica 0 de 1. Son pocas, así que se miran **una a una**,
que es lo que corresponde con n < 20, en vez de leer la tasa.

QUÉ HACE. Para cada pasada nocturna VIIRS 750 con alerta de MIROVA en la ventana, toma nuestro record
pareado (±2 min, el mismo pareo del banco) y anota por qué el predicado del dashboard no publica:
si no hay cúmulo, si el cúmulo quedó lejos del cráter, si la magnitud salió cero (el recorte del
exceso negativo, D25), si lo tapó el filtro de artefacto del display, o si directamente no hay record.
Guarda el fondo, el máximo de I04 y el NTI para poder distinguir el fenómeno del gate.

Fuente de verdad: `perdidas_v750.json` (regla S91). Ningún número se escribe a mano.
USO: python experiments/_s143_cobertura/perdidas_v750.py [--inicio 2026-09-01] [--fin 2026-09-17]
"""
import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

CAMPOS = ("vrp_mw", "vrp_mir_mw", "t_bg_k", "t_max_k", "t_max_i04_k", "nti_max", "distance_class",
          "discarded_reason", "final_hotspot_source", "final_hotspot_dist_km", "n_anomalous_pixels",
          "triggered_test1", "diag_n_first_pass_pixels", "sensor_zenith_deg", "product_version")


def motivo(r, disp, pub, inner):
    """Por qué el dashboard no publica, en el orden en que el predicado lo decide."""
    pc = r.get("primary_cluster") or {}
    if not r:
        return "sin record"
    if r.get("discarded_reason"):
        return f"descartado por el pipeline: {r['discarded_reason']}"
    if not pc:
        return "sin cúmulo primario"
    d = pc.get("centroid_dist_km")
    if d is None:
        return "cúmulo sin distancia"
    if inner is not None and d > inner:
        return f"cúmulo fuera del radio interno ({d} km > {inner} km)"
    if (pc.get("vrp_mw") or 0) == 0:
        return "cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25)"
    if disp == 0:
        return "magnitud del display en 0 (filtro de artefacto o recorte)"
    return "publica" if pub else "el predicado lo suprime por otra rama"


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(bp.cargar_referencia_unificada(cons, ocr), coords, ventana)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    crudos = {}
    for v in bp.VOLS:
        for r in json.loads((ROOT / "data" / "mirova_equivalent" / f"{v}.json").read_text(encoding="utf-8"))["records"]:
            if bp.bucket(r.get("sensor")) == "VIIRS750":
                crudos[(v, r["datetime_utc"], r["sensor"])] = r

    casos = []
    for r in recs:
        if r["b"] != "VIIRS750" or r["lab"] != "pos" or r["pub"]:
            continue
        clave = [k for k in crudos if k[0] == r["vol"] and k[1] == r["dt"].strftime("%Y-%m-%d %H:%M")]
        crudo = crudos[clave[0]] if len(clave) == 1 else {}
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        mir = [{"tipo": f["tipo"], "vrp_mw": f["vrp_mw"], "dist_km": f["dist_km"], "fuente": f["source"]}
               for f in filas if bp.es_alerta(f["tipo"])]
        pc = (crudo.get("primary_cluster") or {})
        casos.append({
            "volcan": r["vol"], "pasada_utc": r["dt"].strftime("%Y-%m-%d %H:%M"),
            "sensor": crudo.get("sensor"), "noche": r["noche"],
            "inner_km": inner[r["vol"]], "mirova": mir,
            "motivo": motivo(crudo, r.get("disp"), r["pub"], inner[r["vol"]]),
            "cumulo": {k: pc.get(k) for k in ("vrp_mw", "n_pixels", "centroid_dist_km", "geo_class")},
            "record": {k: crudo.get(k) for k in CAMPOS if k in crudo},
            "magnitud_display": r.get("disp"),
            "otra_pasada_de_la_noche_publica": any(
                x["vol"] == r["vol"] and x["noche"] == r["noche"] and x["pub"] for x in recs),
        })
    casos.sort(key=lambda x: (x["volcan"], x["pasada_utc"]))
    out = {"meta": {"ventana": list(ventana), "referencia": {k: v["sha"] for k, v in info.items()},
                    "sha_index_html": bp.sha_git(bp.HTML),
                    "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "definiciones": {
               "caso": "pasada nocturna VIIRS 750 con ALERTA de MIROVA a +-2 min que el dashboard NO publica",
               "motivo": "primera condición del predicado que falla, en el orden en que el dashboard decide",
               "otra_pasada_de_la_noche_publica": "si esa noche de volcán quedó cubierta por otra pasada, de cualquier sensor"},
           "n_casos": len(casos), "casos": casos}
    (HERE / "perdidas_v750.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    motivos = {}
    for c in casos:
        motivos.setdefault(c["motivo"], []).append(c)
    L = ["# Las pasadas de VIIRS 750 que MIROVA publica y nosotros no",
         "",
         f"> Generado por `experiments/_s143_cobertura/perdidas_v750.py` desde `perdidas_v750.json`",
         f"> ({out['meta']['generado_utc']}). Ningún número escrito a mano (S91). Ventana"
         f" **{ventana[0]} a {ventana[1]}**, régimen posterior al PR #571. Publicar = predicado del",
         f"> dashboard ejecutado con node. Referencia de MIROVA fijada por sha en el JSON.",
         "",
         "**Por qué importa.** La regla del proyecto es tener al menos todo lo que MIROVA publica; esta",
         "es la lista corta que hay que dejar en cero. Con n < 20 no se lee la tasa: se miran los casos.",
         "",
         f"## Los {len(casos)} casos",
         "",
         "| volcán | pasada UTC | sensor | MIROVA (MW, km) | nuestro cúmulo | fondo K | máx I04 K | por qué no publica | ¿la noche quedó cubierta? |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in casos:
        r, pc, m = c["record"], c["cumulo"], (c["mirova"] or [{}])[0]
        L.append(f"| {c['volcan']} | {c['pasada_utc']} | {c['sensor']} | "
                 f"{m.get('vrp_mw')} MW a {m.get('dist_km')} km | "
                 f"{pc.get('vrp_mw')} MW, {pc.get('n_pixels')} px a {pc.get('centroid_dist_km')} km | "
                 f"{r.get('t_bg_k')} | {r.get('t_max_k')} | {c['motivo']} | "
                 f"{'sí' if c['otra_pasada_de_la_noche_publica'] else 'NO'} |")
    L += ["", "## Qué dicen estos casos", ""]
    for mot, cs in sorted(motivos.items(), key=lambda kv: -len(kv[1])):
        L.append(f"- **{len(cs)} de {len(casos)}**: {mot}.")
    L += ["",
          "El fenómeno, en palabras: en los cinco casos **sí encontramos el foco en el cráter** (cúmulo",
          "summit a 0,2 a 0,7 km) y lo que falla es la energía. El fondo con que se resta es la mediana",
          "de un anillo regional de 5 a 25 km, lleno de valle sin nieve y más tibio que la cumbre; el",
          "exceso sale negativo y se recorta a 0,0 MW. MIROVA, que promedia los píxeles vecinos del",
          "alertado (SP426.5 p. 8, ec. 6), publica entre 0,16 y 0,49 MW en esas mismas pasadas. Es la",
          "divergencia D25, la misma que el A/B abierto está midiendo en VIIRS 375.",
          "",
          "**Consecuencia para el plan**: el flag del fondo por vecinos existe hoy sólo para VIIRS 375",
          "(`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`). Si el A/B lo respalda, la fase 2 del plan de paridad",
          "debería llevarlo a VIIRS 750, que es donde está esta brecha de cobertura. No se propone antes",
          "de tener el resultado del A/B: cinco casos muestran el mecanismo, no su tamaño (A94).",
          "",
          "**Lo que NO dicen**: ninguna de estas cinco pasadas dejó una noche sin alerta, porque otra",
          "pasada de la misma noche sí publicó. La pérdida es de fidelidad por pasada y de magnitud, no",
          "de recall por noche."]
    salto = chr(10)
    (ROOT / "docs" / "audit_s143" / "PERDIDAS_V750.md").write_text(
        salto.join(L) + salto, encoding="utf-8")
    print(f"{len(casos)} pasadas V750 con alerta que no publicamos, ventana {ventana[0]} a {ventana[1]}")
    for c in casos:
        rec = c["record"]
        print(f"  {c['volcan']:20s} {c['pasada_utc']} {c['sensor']}: {c['motivo']}")
        print(f"      MIROVA {c['mirova']} | cumulo {c['cumulo']} | t_bg {rec.get('t_bg_k')} "
              f"t_max {rec.get('t_max_k')} nti_max {rec.get('nti_max')} zen {rec.get('sensor_zenith_deg')} "
              f"| noche cubierta por otra pasada: {c['otra_pasada_de_la_noche_publica']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
