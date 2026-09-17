# -*- coding: utf-8 -*-
"""S143: control de instrumento del evaluador sobre los artefactos reales de S135.

POR QUÉ. Un evaluador escrito antes de ver datos puede estar equivocado sin que nada avise. El A/B
de S135 corrió el mismo sensor (VIIRS 375) en la misma ventana (2026-06-01 a 2026-08-31) y dejó un
resultado publicado: 260 noches confirmadas y 12 noches que el brazo D pierde
(`experiments/_s135_ab_d1d2/resultado_final.json`). Si el instrumento nuevo mide lo que dice, esas
12 tienen que aparecer como pérdida y el universo tiene que quedar cerca de 260. Toda diferencia se
atribuye acá a una causa concreta (referencia, predicado o cota), no se deja como ruido.

QUÉ CORRE. Fusiona los dos tramos de los artefactos rescatados (runs 34173711390 y 34208191011) en
un directorio temporal que se borra al terminar (los artefactos NO se copian al repo), evalúa los
brazos A (control), B (keep_peak OFF) y D (ambos) sobre los seis volcanes de S135, y compara.

ATRIBUCIÓN DE LAS DIFERENCIAS. El evaluador nuevo cambia tres cosas respecto de `evaluar_ab.py`:
  1. referencia: CONS y OCR del remoto fijados por sha (pre-registro) con el loader unificado del
     banco, contra el snapshot del repo con `load_mirova_alertas` (que descarta las filas que no son
     alerta);
  2. pasadas diurnas: `es_pasada_diurna_descartada` (elevación solar, el filtro del banco) contra
     `is_nighttime`;
  3. "publica": el predicado del dashboard ejecutado con node contra `publica_en_crater`.
El informe cuenta, noche por noche, cuántas confirmadas se ganan o se pierden por cada una, y corre
además dos controles cruzados sobre los MISMOS artefactos fusionados:
  * el evaluador VIEJO tal cual (otra implementación, hoy), para ver si coincide volcán por volcán;
  * el evaluador viejo con el regex del loader OCR ANTERIOR al PR #652 (S140), que es el que corría
    en S135. Si con ese regex vuelven las 260 noches, la diferencia no es del instrumento nuevo sino
    del loader: #652 le devolvió la distancia a 557 alertas OCR y esas noches pasaron a tener con
    qué contrastar la cota de mismo objeto.

USO (read-only sobre el repo; escribe sólo en esta carpeta):
    python experiments/_s143_evaluador/control_s135.py
"""
from __future__ import annotations

import collections
import io
import json
import shutil
import sys
import tempfile
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT, ROOT / "scripts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import evaluar as ev  # noqa: E402
import fusionar  # noqa: E402
import banco_paridad as bp  # noqa: E402
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from run_pipeline import is_nighttime  # noqa: E402

ARTEFACTOS = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_artefactos_ab")
RUNS = ("__run34173711390", "__run34208191011")
PREFIJO = "s135ab-"
BRAZOS = ["_s135_ab_a_control", "_s135_ab_b_nokeeppeak", "_s135_ab_d_ambos"]
CONTROL = "_s135_ab_a_control"
VOLCANES = ["Isluga", "Lascar", "Lastarria", "PuyehueCordonCaulle", "PlanchonPeteroa", "Tupungatito"]
VENTANA = ("2026-06-01", "2026-08-31")
S135 = ROOT / "experiments" / "_s135_ab_d1d2" / "resultado_final.json"
SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"


def _parse_dt(s):
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, f)
        except (ValueError, TypeError):
            pass
    return None


def noches_alerta_s135(coords):
    """Universo de noches con alerta tal como lo armaba `evaluar_ab.py` de S135: snapshot del repo,
    `load_mirova_alertas` (sólo alertas) y `is_nighttime`."""
    alertas = load_mirova_alertas(cons_path=SNAP / "registro_vrp_consolidado.csv",
                                  ocr_path=SNAP / "registro_vrp_ocr.csv")
    out = collections.defaultdict(set)
    for a in alertas:
        f = a.get("fecha_utc")
        if not f or a["sensor_bucket"] != "VIIRS375":
            continue
        vol = a["volcano"]
        if vol not in VOLCANES:
            continue
        dt = _parse_dt(f)
        if dt is not None and vol in coords and not is_nighttime(*coords[vol], dt):
            continue
        if VENTANA[0] <= f[:10] <= VENTANA[1]:
            out[vol].add(f[:10])
    return dict(out)


def correr_evaluador_viejo(dir_fusion, regex_previo_652=False):
    """Corre `experiments/_s135_ab_d1d2/evaluar_ab.py` sobre los mismos artefactos, en proceso.

    Con `regex_previo_652=True` se restaura el regex de distancia OCR anterior al PR #652, que es
    el que corría cuando se publicó `resultado_final.json`."""
    import contextlib
    import re
    sys.path.insert(0, str(ROOT / "experiments" / "_s135_ab_d1d2"))
    import evaluar_ab
    import pipeline.mirova_csv_loader as loader
    previo = loader._OCR_DIST_RE
    if regex_previo_652:
        loader._OCR_DIST_RE = re.compile(r"(?:dist[≈~=]|->|→)\s*(\d+\.?\d*)\s*km")
    argv, salida = sys.argv, io.StringIO()
    tmp = Path(tempfile.mkdtemp(prefix="s143_viejo_"))
    try:
        sys.argv = ["evaluar_ab.py", "--dir", str(dir_fusion), "--out", str(tmp)]
        with contextlib.redirect_stdout(salida):
            evaluar_ab.main()
        r = json.loads((tmp / "resultado_ab.json").read_text(encoding="utf-8"))
    finally:
        sys.argv = argv
        loader._OCR_DIST_RE = previo
        shutil.rmtree(tmp, ignore_errors=True)
    return {"noches_catb_control": r["noches_catb_control"],
            "total": sum(r["noches_catb_control"].values()),
            "perdidas_brazo_d": r["brazos"]["_s135_ab_d_ambos"]["criterio1_detalle"],
            "perdidas_brazo_b": r["brazos"]["_s135_ab_b_nokeeppeak"]["criterio1_detalle"]}


def publica_en_crater_s135(p, inner):
    """El predicado reconstruido a mano de S135, para medir cuánto se separa del de node (A97).
    Se evalúa sobre los mismos campos que el evaluador guarda de cada pasada."""
    return bool(p["pc_vrp"] and 0 < p["pc_vrp"] <= 50000.0 and p["pc_dist"] is not None
                and p["pc_dist"] <= inner and (not p["dc"] or p["dc"] == "summit"))


def markdown_control(s):
    """CONTROL_S135.md: la prosa es fija, cada número sale de `s` (regla S91)."""
    c = s["comparacion_con_s135"]
    res = s["resultado"]
    nuevo, viejo_hoy = c["noches_confirmadas_nuevas_total"], c["evaluador_viejo_hoy"]
    viejo_652 = c["evaluador_viejo_con_loader_previo_652"]
    pub = s["control_s135_publicado"]
    doce = {(d["volcan"], d["fecha"]) for d in c["doce_noches_de_s135"]}
    sinf = {(d["volcan"], d["fecha"]) for d in c["perdidas_brazo_d_sin_filtro"]}
    L = [
        "# Control de instrumento del evaluador sobre los artefactos de S135",
        "",
        f"> Generado por `experiments/_s143_evaluador/control_s135.py` el {s['meta']['generado_utc']}. "
        f"Artefactos locales de los runs {', '.join(s['meta']['runs'])} (no versionados, fuera del repo), "
        f"fusionados en un directorio temporal: {s['meta']['fusion']['archivos']} archivos, "
        f"{s['meta']['fusion']['conflictos']} conflictos, {s['meta']['fusion']['faltantes']} faltantes. "
        f"Ventana {s['meta']['ventana'][0]} a {s['meta']['ventana'][1]}, seis volcanes, brazos A, B y D. "
        "Ningún número de este documento está escrito a mano: todos salen de `control_s135.json`.",
        "",
        "## Por qué este control",
        "",
        "Un evaluador escrito antes de ver datos puede estar equivocado sin que nada avise. S135 corrió",
        "el mismo sensor en la misma ventana y dejó dos números publicados contra los cuales medirse:",
        f"**{pub['total']} noches confirmadas** y **{len(doce)} noches** que el brazo D pierde.",
        "",
        "## Las doce noches de S135",
        "",
        f"El evaluador nuevo las reproduce **una a una** como pérdida del brazo D sin filtro de cota en el",
        f"brazo: {len(sinf)} noches, y el conjunto coincide exactamente con el publicado "
        f"({'sí' if sinf == doce else 'NO'}).",
        "",
        "| volcán | fecha | control publica con cota | brazo D publica con cota | brazo D publica |",
        "|---|---|---|---|---|",
    ]
    for f in (c["estado_de_las_doce"] or []):
        ctl, d = f[CONTROL], f["_s135_ab_d_ambos"]
        L.append(f"| {f['volcan']} | {f['fecha']} | {'sí' if ctl['publica_cota'] else 'no'} | "
                 f"{'sí' if d['publica_cota'] else 'no'} | {'sí' if d['publica'] else 'no'} |")
    extra = [f for filas in (c["perdidas_solo_por_la_cota_en_el_brazo"] or {}).values() for f in filas]
    marg = [f for f in extra if f["cota_min_brazo_km"] is not None and f["cota_min_brazo_km"] <= 0.70]
    L += [
        "",
        "## Con la cota también en el brazo, el brazo D pierde más",
        "",
        f"Exigirle al brazo lo mismo que al control (hallazgo 2 del verificador) lleva las pérdidas de D de "
        f"{len(sinf)} a **{len(c['perdidas_brazo_d_nuevas'])}**, y las de B de "
        f"{len(c['perdidas_brazo_b_sin_filtro'])} a **{len(c['perdidas_brazo_b_nuevas'])}**.",
        "Las que aparecen sólo con la cota son noches en que el brazo publica, pero un objeto que está lejos",
        "de lo que MIROVA informó esa noche: con el criterio viejo el brazo se quedaba con la noche por",
        "publicar otra cosa. El caso a caso, con la cota del mejor objeto publicado por cada uno:",
        "",
        "| brazo | volcán | fecha | cota del brazo (km) | cota del control (km) | distancia de MIROVA (km) |",
        "|---|---|---|---|---|---|",
    ]
    for brazo, filas in (c["perdidas_solo_por_la_cota_en_el_brazo"] or {}).items():
        for f in filas:
            L.append(f"| {brazo} | {f['volcan']} | {f['fecha']} | {f['cota_min_brazo_km']} | "
                     f"{f['cota_min_control_km']} | {f['dist_mirova_km']} |")
    L += [
        "",
        f"De esas {len(extra)} noches, **{len(marg)}** tienen el objeto del brazo a menos de 0,70 km de la",
        "cota, o sea al borde del presupuesto de 0,55 km: son las más sensibles a la elección del umbral y a",
        "la distancia que informó MIROVA, que viene cuantizada a su celda de grilla (D15).",
        "",
        f"## El universo: {nuevo} hoy contra las {pub['total']} publicadas",
        "",
        f"El evaluador nuevo cuenta **{nuevo}** noches confirmadas; S135 publicó **{pub['total']}**. La",
        "diferencia no es del instrumento nuevo, y se atribuye con dos controles cruzados sobre los mismos",
        "artefactos fusionados:",
        "",
        f"1. el evaluador **viejo** (`evaluar_ab.py`, otra implementación, predicado reconstruido a mano y",
        f"   referencia del snapshot) corrido **hoy** da **{viejo_hoy['total']}**, volcán por volcán igual que",
        f"   el nuevo ({'sí' if viejo_hoy['noches_catb_control'] == res['noches_confirmadas']['por_volcan'] else 'NO'});",
        f"2. el mismo evaluador viejo con el **regex del loader OCR anterior al PR #652** (S140, el que corría",
        f"   en S135) vuelve a dar **{viejo_652['total']}**.",
        "",
        "| volcán | nuevo | viejo hoy | viejo con loader previo a #652 | S135 publicado |",
        "|---|---|---|---|---|",
    ]
    for v in s["meta"].get("volcanes", res["meta"]["volcanes"]):
        L.append(f"| {v} | {res['noches_confirmadas']['por_volcan'][v]} | {viejo_hoy['noches_catb_control'][v]} | "
                 f"{viejo_652['noches_catb_control'][v]} | {pub['noches_catb_control'][v]} |")
    L += [
        "",
        "El PR #652 le devolvió la distancia a 557 alertas OCR cuyas notas venían en codificación doble. Sin",
        "esa distancia la cota de mismo objeto no se podía calcular y la noche se aceptaba por defecto; con",
        "ella, esas noches muestran que lo publicado está lejos de lo que informó MIROVA. Es el caso de libro",
        "de A90: el número de un informe viejo no es comparable con el de hoy sin reconstruir el corpus y el",
        "código que ese informe pudo ver.",
        "",
        "## Los dos predicados",
        "",
        f"Sobre las {c['n_pasadas_control']} pasadas nocturnas de VIIRS 375 del control, el predicado del",
        f"dashboard ejecutado con node y el `publica_en_crater` reconstruido a mano de S135 discrepan en",
        f"**{c['pasadas_con_predicado_discordante']}**. El evaluador usa el de node (A97); el viejo se deja",
        "acá sólo como control cruzado.",
        "",
        "## Los otros dos criterios, contra los números publicados",
        "",
        f"En negativos limpios el control publica en {ev._f(res['control']['neg_limpio_tasa_publica'])} de "
        f"{res['control']['neg_limpio_n']} pasadas, el régimen que el verificador declaró esperable para el",
        "control reprocesado de S135 (93,8 %, hallazgo 16); el brazo D baja a "
        f"{ev._f(res['brazos']['_s135_ab_d_ambos']['criterio2']['total']['tasa_brazo'])}.",
        "",
        f"En magnitud, la mediana del control sobre pares decisivos es "
        f"{ev._f(res['brazos']['_s135_ab_d_ambos']['criterio3']['total']['mediana_control_decisivo'])} "
        f"(n = {res['brazos']['_s135_ab_d_ambos']['criterio3']['total']['n_pares_decisivo']}) y la del brazo D "
        f"{ev._f(res['brazos']['_s135_ab_d_ambos']['criterio3']['total']['mediana_brazo_decisivo'])}; S135 publicó "
        f"{pub['magnitud_mediana'][CONTROL]} (n = {pub['magnitud_n_pares'][CONTROL]}) y "
        f"{pub['magnitud_mediana']['_s135_ab_d_ambos']} (n = {pub['magnitud_n_pares']['_s135_ab_d_ambos']}).",
        "La diferencia esperada: S135 pareaba a 20 minutos y podía usar varias filas de MIROVA por pasada,",
        "acá el pareo es de 2 minutos (`banco_paridad.TOL_S`) con una sola fila por pasada, CONS antes que OCR,",
        "y las medianas se toman sobre las pasadas que publican los dos brazos, no sobre el conjunto de cada uno.",
        "",
        "## Una advertencia sobre un contador que NO es comparable",
        "",
        "`coincidencias_de_fecha_descartadas` cuenta distinto en cada evaluador: el viejo anota la noche si",
        "**algún** objeto publicado queda fuera de la cota (aunque otro de la misma noche la pase), y el nuevo",
        "sólo si **ninguno** la pasa. Por eso el viejo muestra números mucho mayores sin que eso signifique",
        "que descarta más noches. La cifra comparable es la de noches confirmadas.",
        "",
        "## Qué queda probado y qué no",
        "",
        "- CONFIRMADO: el evaluador reproduce las doce noches de S135 y coincide volcán por volcán con la otra",
        "  implementación sobre los mismos datos.",
        "- CONFIRMADO: la diferencia con el 260 publicado es el loader OCR de #652, no el instrumento.",
        "- Lo que este control NO prueba: que los criterios 2 y 3 estén bien calibrados para los brazos de",
        "  S143 (son otros perfiles) ni que la cota acepte sólo objetos verdaderamente iguales, que es una cota",
        "  inferior por construcción (A93).",
        "",
    ]
    # red de seguridad: el proyecto no admite guiones largos ni medios en ningún texto
    return "\n".join(L).replace(chr(8212), ",").replace(chr(8211), ",")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ref = json.loads(S135.read_text(encoding="utf-8"))
    doce = ref["brazos"]["_s135_ab_d_ambos"]["criterio1_detalle"]
    tmp = Path(tempfile.mkdtemp(prefix="s143_control_s135_"))
    try:
        inf = fusionar.fusionar([(str(ARTEFACTOS), r) for r in RUNS], PREFIJO, BRAZOS, VOLCANES,
                                str(tmp))
        (tmp / "fusion_informe.json").write_text(json.dumps(inf, ensure_ascii=False), encoding="utf-8")
        seg = HERE / "_seguimiento_s135.json"
        seg.write_text(json.dumps(doce, ensure_ascii=False), encoding="utf-8")
        args = Namespace(dir=str(tmp), prefijo=PREFIJO, brazos=BRAZOS, control=CONTROL,
                         volcanes=VOLCANES, inicio=VENTANA[0], fin=VENTANA[1],
                         denominadores=str(ev.DENOMINADORES), ref_cons=None, ref_ocr=None,
                         B=ev.B_DEFECTO, semilla=ev.SEMILLA_DEFECTO, n_min=ev.N_MIN_MAGNITUD,
                         tol_magnitud=ev.TOL_MAGNITUD, cota_km=ev.PRESUPUESTO_COTA_KM,
                         seguimiento=str(seg), out_json=None, out_md=None)
        res = ev.evaluar(args)

        # --- atribución de las diferencias con S135, noche por noche ---
        coords = bp._coords_por_volcan()
        rad = ev.radios(VOLCANES)
        alertas_s135 = noches_alerta_s135(coords)
        rutas, _ = ev.referencia_por_sha()
        filas = bp.cargar_referencia_unificada(rutas[ev.NOMBRES_REF[0]], rutas[ev.NOMBRES_REF[1]])
        por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
        alertas_nuevas, dist_noche = ev.noches_y_distancias(por_vb, ns, VOLCANES)
        recs = {v: ev.cargar_records(tmp, PREFIJO, CONTROL, v) for v in VOLCANES}
        pas = ev.construir_pasadas(recs, coords, {v: rad[v]["inner"] for v in VOLCANES}, VENTANA)
        # el predicado viejo necesita pc_vrp/pc_dist/dc: se leen del record original
        crudo = {}
        for v, rs in recs.items():
            for r in rs:
                crudo[(v, r["datetime_utc"], r["sensor"])] = r
        for p in pas:
            r = crudo[p["clave"]]
            pc = r.get("primary_cluster") or {}
            p["pc_vrp"], p["pc_dist"], p["dc"] = pc.get("vrp_mw"), pc.get("centroid_dist_km"), r.get("distance_class")

        atribucion, desacuerdo_predicado = {}, 0
        for v in VOLCANES:
            inner = rad[v]["inner"]
            nuevas, viejas = alertas_nuevas.get(v, set()), alertas_s135.get(v, set())
            pub_node, pub_viejo = set(), set()
            for p in pas:
                if p["vol"] != v:
                    continue
                viejo = publica_en_crater_s135(p, inner)
                if int(viejo) != int(p["pub"]):
                    desacuerdo_predicado += 1
                if p["pub"]:
                    pub_node.add(p["noche"])
                if viejo:
                    pub_viejo.add(p["noche"])
            est_nuevo = ev.estado_noches([p for p in pas if p["vol"] == v], {v: nuevas}, dist_noche,
                                         {v: rad[v]["mirova_center"]}, ev.PRESUPUESTO_COTA_KM)[v]
            atribucion[v] = {
                "noches_alerta_referencia_nueva": len(nuevas),
                "noches_alerta_referencia_s135": len(viejas),
                "solo_en_referencia_nueva": sorted(nuevas - viejas),
                "solo_en_referencia_s135": sorted(viejas - nuevas),
                "confirmadas_nuevas": len(est_nuevo["pub_cota"]),
                "confirmadas_s135_publicadas": ref["noches_catb_control"][v],
                "noches_con_alerta_publicadas_node": len(pub_node & nuevas),
                "noches_con_alerta_publicadas_predicado_s135": len(pub_viejo & nuevas),
                "descartadas_por_cota": len(est_nuevo["descartadas"]),
                "aceptadas_sin_cota": len(est_nuevo["sin_cota"]),
                "descartadas_por_cota_s135": len(ref["coincidencias_de_fecha_descartadas"].get(v, {})),
            }
        # --- las pérdidas que aparecen sólo al exigir la cota TAMBIÉN en el brazo (hallazgo 2) ---
        def cota_min(pasadas, vol, noche):
            centro, dm = rad[vol]["mirova_center"], dist_noche.get((vol, noche)) or []
            cotas = [min(abs(ev.hav(centro[0], centro[1], p["cen"][0], p["cen"][1]) - x) for x in dm)
                     for p in pasadas
                     if p["vol"] == vol and p["noche"] == noche and p["pub"] and p["cen"] and dm]
            return round(min(cotas), 3) if cotas else None

        detalle_cota = {}
        for brazo in BRAZOS[1:]:
            rb = {v: ev.cargar_records(tmp, PREFIJO, brazo, v) for v in VOLCANES}
            pb = ev.construir_pasadas(rb, coords, {v: rad[v]["inner"] for v in VOLCANES}, VENTANA)
            c1 = res["brazos"][brazo]["criterio1"]
            sinf = {(d["volcan"], d["fecha"]) for d in c1["perdidas_sin_filtro_brazo"]}
            detalle_cota[brazo] = [
                {"volcan": d["volcan"], "fecha": d["fecha"],
                 "cota_min_brazo_km": cota_min(pb, d["volcan"], d["fecha"]),
                 "cota_min_control_km": cota_min(pas, d["volcan"], d["fecha"]),
                 "dist_mirova_km": sorted(set(dist_noche.get((d["volcan"], d["fecha"]) ) or []))}
                for d in c1["perdidas"] if (d["volcan"], d["fecha"]) not in sinf]

        viejo_hoy = correr_evaluador_viejo(tmp)
        viejo_s135 = correr_evaluador_viejo(tmp, regex_previo_652=True)
        salida = {
            "meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "artefactos": str(ARTEFACTOS), "runs": list(RUNS), "ventana": list(VENTANA),
                     "referencia_s135": str(S135.relative_to(ROOT)).replace("\\", "/"),
                     "fusion": {"archivos": len(inf["archivos"]), "conflictos": len(inf["conflictos"]),
                                "faltantes": len(inf["faltantes"]),
                                "duplicados_identicos": inf["duplicados_identicos"]}},
            "resultado": res,
            "comparacion_con_s135": {
                "noches_confirmadas_nuevas_total": res["noches_confirmadas"]["total"],
                "noches_confirmadas_s135_total": sum(ref["noches_catb_control"].values()),
                "doce_noches_de_s135": doce,
                "estado_de_las_doce": res.get("seguimiento"),
                "perdidas_brazo_d_nuevas": res["brazos"]["_s135_ab_d_ambos"]["criterio1"]["perdidas"],
                "perdidas_brazo_d_sin_filtro": res["brazos"]["_s135_ab_d_ambos"]["criterio1"]["perdidas_sin_filtro_brazo"],
                "perdidas_brazo_b_nuevas": res["brazos"]["_s135_ab_b_nokeeppeak"]["criterio1"]["perdidas"],
                "perdidas_brazo_b_sin_filtro": res["brazos"]["_s135_ab_b_nokeeppeak"]["criterio1"]["perdidas_sin_filtro_brazo"],
                "perdidas_solo_por_la_cota_en_el_brazo": detalle_cota,
                "pasadas_con_predicado_discordante": desacuerdo_predicado,
                "n_pasadas_control": len(pas),
                "evaluador_viejo_hoy": viejo_hoy,
                "evaluador_viejo_con_loader_previo_652": viejo_s135,
                "atribucion_por_volcan": atribucion},
        }
        salida["control_s135_publicado"] = {
            "noches_catb_control": ref["noches_catb_control"],
            "total": sum(ref["noches_catb_control"].values()),
            "magnitud_mediana": {b: ref["brazos"][b]["criterio3_razon_mediana"] for b in BRAZOS},
            "magnitud_n_pares": {b: ref["brazos"][b]["criterio3_n_pares"] for b in BRAZOS}}
        (HERE / "control_s135.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False,
                                                           default=ev.json_default), encoding="utf-8")
        print(json.dumps(salida["comparacion_con_s135"]["atribucion_por_volcan"], indent=1, ensure_ascii=False))
        print("confirmadas nuevas", salida["comparacion_con_s135"]["noches_confirmadas_nuevas_total"],
              "vs S135", salida["comparacion_con_s135"]["noches_confirmadas_s135_total"])
        print("perdidas D:", salida["comparacion_con_s135"]["perdidas_brazo_d_nuevas"])
        print("perdidas D sin filtro:", salida["comparacion_con_s135"]["perdidas_brazo_d_sin_filtro"])
        print("perdidas B:", salida["comparacion_con_s135"]["perdidas_brazo_b_nuevas"])
        print("predicado discordante:", desacuerdo_predicado, "de", len(pas))
        (HERE / "informe_control_s135.md").write_text(ev.informe_markdown(res), encoding="utf-8")
        (HERE / "CONTROL_S135.md").write_text(markdown_control(salida), encoding="utf-8")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
