# -*- coding: utf-8 -*-
"""S143: lee las salidas del probe de las 12 noches y aplica el criterio pre-registrado de README.md.

Escrito ANTES de bajar los artefactos. Ningún umbral se toca después de ver datos.

POR QUÉ ASÍ. "Publica" es el predicado del dashboard ejecutado con node (A97), no uno reconstruido a
mano. "Recupera la noche" exige además que lo publicado sea plausiblemente el mismo objeto que vio
MIROVA: los dos radios desde el `mirova_center` y diferencia <= 0,55 km, la cota de S135
(`experiments/_s135_ab_d1d2/evaluar_ab.py`, misma semántica: si falta la distancia de MIROVA o el
centroide, la noche no se descarta por cota). Sin esa cota, un brazo sin compuerta que publique ruido
en otro punto del disco "recuperaría" la noche (hallazgo 2 del verificador del pre-registro).

USO: python experiments/_s143_probe_12_noches/analizar.py --out <dir con subcarpetas por variante>
Escribe resultado.json y RESULTADO.md en --dest (por defecto, esta carpeta).
"""
import argparse
import collections
import io
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import yaml  # noqa: E402

import banco_paridad as bp  # noqa: E402

VARIANTES = ["control", "s135_d", "s135_d_sin_compuerta_ctx", "literal", "literal_sin_compuerta_ctx",
             "literal_t1_sin_filtro"]
CON_ENVOLTORIO = {"s135_d_sin_compuerta_ctx", "literal_sin_compuerta_ctx"}
REF = ROOT / "experiments" / "_s143_preregistro" / "_dl_referencia"
COTA_KM = 0.55
VENTANA = ("2026-06-01", "2026-08-31")
UMBRAL_RECUPERA = 11  # de 12


def hav(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def distancias_mirova():
    """(volcán, noche) -> distancias de las ALERTAS nocturnas V375 de MIROVA."""
    coords = bp._coords_por_volcan()
    filas = bp.cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    out = collections.defaultdict(list)
    for f in filas:
        if f["sensor_bucket"] != "VIIRS375" or not bp.es_alerta(f["tipo"]):
            continue
        noche = f["fecha_utc"][:10]
        if not (VENTANA[0] <= noche <= VENTANA[1]) or f["volcano"] not in coords:
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if bp.es_pasada_diurna_descartada("VIIRS375", *coords[f["volcano"]], dt):
            continue
        if f.get("dist_km") is not None:
            out[(f["volcano"], noche)].append(float(f["dist_km"]))
    return out


def cargar(out_dir):
    filas = {}
    for v in VARIANTES:
        # rglob: `gh run download` deja un subdirectorio por artefacto (uno por volcán), y dentro
        # la carpeta de cada variante. Así el analizador sirve igual con uno o con los cuatro.
        for p in sorted(out_dir.rglob(f"{v}/*.json")):
            x = json.loads(p.read_text(encoding="utf-8"))
            filas[(v, x["volcan"], x["pasada_utc"], x["sensor"])] = x
    return filas


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dest", default=HERE, type=Path)
    a = ap.parse_args(argv)

    pasadas = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    filas = cargar(a.out)
    inner = bp.inner_desde_html()
    cfg = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    centro = {v["name"]: (v.get("mirova_center_lat"), v.get("mirova_center_lon")) for v in cfg["volcanoes"]}
    dist_mir = distancias_mirova()

    # predicado del dashboard con node, una sola llamada
    casos, claves = [], []
    for k, x in filas.items():
        if not x.get("ok"):
            continue
        r = x["record"]
        slim = {c: r.get(c) for c in bp.CAMPOS_JS}
        casos.append([slim, inner[x["volcan"]]])
        claves.append(k)
    pub = {k: bool(p[4]) for k, p in zip(claves, bp.correr_node(casos))} if casos else {}

    def mismo_objeto(k):
        x = filas[k]
        pc = x["record"].get("primary_cluster") or {}
        cm = centro.get(x["volcan"]) or (None, None)
        dm = dist_mir.get((x["volcan"], x["noche"])) or []
        if pc.get("centroid_lat") is None or cm[0] is None or not dm:
            return True, None
        cota = min(abs(hav(cm[0], cm[1], pc["centroid_lat"], pc["centroid_lon"]) - d) for d in dm)
        return cota <= COTA_KM, round(cota, 3)

    res = {"variantes": {}, "control_instrumento": {}}
    noches = sorted({(x["volcan"], x["noche"]) for x in pasadas if x["clase"] == "perdida"})
    for v in VARIANTES:
        ok = [(x["volcan"], x["pasada_utc"], x["sensor"]) for x in pasadas
              if filas.get((v, x["volcan"], x["pasada_utc"], x["sensor"]), {}).get("ok")]
        det_noche = {}
        for vol, noche in noches:
            ps = [x for x in pasadas if x["clase"] == "perdida" and x["volcan"] == vol and x["noche"] == noche]
            estado = {"publica_sin_cota": False, "publica_con_cota": False, "pasadas": []}
            for x in ps:
                k = (v, vol, x["pasada_utc"], x["sensor"])
                if k not in pub:
                    estado["pasadas"].append({"pasada": x["pasada_utc"], "ok": False})
                    continue
                mo, cota = mismo_objeto(k) if pub[k] else (False, None)
                r = filas[k]["record"]
                estado["pasadas"].append({"pasada": x["pasada_utc"], "sensor": x["sensor"], "publica": pub[k],
                                          "mismo_objeto": mo, "cota_km": cota,
                                          "fuente": r.get("final_hotspot_source"),
                                          "n_ctx_path": r.get("diag_n_dnti_ctx_path"),
                                          "llamadas": filas[k].get("llamadas"),
                                          "n_primer_pase": r.get("diag_n_first_pass_pixels"),
                                          "f5": r.get("f5_core_vrp_mw"),
                                          "pc_vrp": (r.get("primary_cluster") or {}).get("vrp_mw")})
                estado["publica_sin_cota"] |= pub[k]
                estado["publica_con_cota"] |= bool(pub[k] and mo)
            det_noche[f"{vol}|{noche}"] = estado
        neg = collections.Counter()
        for x in pasadas:
            if x["clase"].startswith("neg"):
                k = (v, x["volcan"], x["pasada_utc"], x["sensor"])
                neg[f"{x['clase']}_n"] += 1
                neg[f"{x['clase']}_publica"] += int(pub.get(k, False))
        envol = [filas[(v, *c)].get("llamadas_ctx_sin_compuerta", 0) for c in ok]
        # Hallazgo 1 del verificador: quitar la compuerta puede apagar el filtro del Test 1 (por
        # `only_test1_source`), o sea recuperar la noche por el mismo mecanismo que la variante que lo
        # apaga a mano. Sin este conteo las dos causas son indistinguibles en la salida.
        filtro = [(filas[(v, *c)].get("llamadas") or {}).get("filtro_t1", 0) for c in ok]
        res["variantes"][v] = {
            "pasadas_ok": len(ok), "pasadas_total": len(pasadas),
            "noches_recuperadas_con_cota": sum(e["publica_con_cota"] for e in det_noche.values()),
            "noches_recuperadas_sin_cota": sum(e["publica_sin_cota"] for e in det_noche.values()),
            "noches_total": len(noches), "negativos": dict(neg),
            "llamadas_envoltorio_min": min(envol) if envol else None,
            "llamadas_envoltorio_max": max(envol) if envol else None,
            "pasadas_sin_envoltorio": sum(1 for e in envol if e == 0),
            "pasadas_con_filtro_test1": sum(1 for f in filtro if f > 0),
            "flags": next((filas[(v, *c)]["flags"] for c in ok), None),
            "detalle_noches": det_noche,
        }

    V = res["variantes"]
    ci = {
        "1_todas_ok": all(V[v]["pasadas_ok"] == len(pasadas) for v in VARIANTES),
        "2a_control_recupera_11": V["control"]["noches_recuperadas_con_cota"] >= UMBRAL_RECUPERA,
        "2b_s135_d_recupera_max_1": V["s135_d"]["noches_recuperadas_con_cota"] <= 1,
        # El envoltorio sólo puede llamarse en pasadas con bloque contextual; exigirlo en las 61
        # declararía INCONCLUSO todo el probe por una pasada sin ese bloque (hallazgo 5). Se exige que
        # haya corrido en la mayoría y que NUNCA corra en las variantes que no lo declaran.
        "3_envoltorio_coherente": all(
            (V[v]["llamadas_envoltorio_max"] or 0) >= 1 and V[v]["pasadas_sin_envoltorio"] <= 0.1 * len(pasadas)
            if v in CON_ENVOLTORIO else (V[v]["llamadas_envoltorio_max"] or 0) == 0
            for v in VARIANTES if V[v]["pasadas_ok"]),
        "4_control_publica_11_neg_artefacto": V["control"]["negativos"].get("neg_artefacto_publica", 0) >= 11,
    }
    res["control_instrumento"] = ci
    valido = all(ci.values())
    rl = V["literal"]["noches_recuperadas_con_cota"] >= UMBRAL_RECUPERA
    rc = V["literal_sin_compuerta_ctx"]["noches_recuperadas_con_cota"] >= UMBRAL_RECUPERA
    rf = V["literal_t1_sin_filtro"]["noches_recuperadas_con_cota"] >= UMBRAL_RECUPERA
    if not valido:
        lectura = "INCONCLUSO: falla el control de instrumento; no se interpreta"
    elif rl:
        lectura = "literal recupera: los brazos actuales ponen a prueba H1"
    elif rc and rf:
        lectura = "ambas recuperan: comparar costo en negativos; la de menor costo al A/B, la otra como ablacion"
    elif rc:
        lectura = "la compuerta de la mascara contextual es la causa: proponer D22 tambien ahi (codigo, A45)"
    elif rf:
        lectura = "la causa es el filtro contextual del Test 1: proponer brazo con enable_test1_contextual_filter false"
    else:
        lectura = "ninguna recupera: investigar pasada por pasada antes de cualquier A/B"
    res["lectura_pre_registrada"] = lectura
    res["meta"] = {"out": str(a.out), "sha_index_html": bp.sha_git(bp.HTML), "cota_km": COTA_KM,
                   "umbral_recupera": UMBRAL_RECUPERA,
                   "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    a.dest.mkdir(parents=True, exist_ok=True)
    (a.dest / "resultado.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

    lineas = ["# Resultado del probe S143 de las 12 noches", "",
              f"Generado por `analizar.py` desde `resultado.json` ({res['meta']['generado_utc']}). Ningún número escrito a mano.", "",
              f"**Lectura pre-registrada:** {lectura}", "", "## Control de instrumento", ""]
    lineas += [f"- {k}: {'cumple' if val else 'NO cumple'}" for k, val in ci.items()]
    lineas += ["", "## Por variante", "",
               "| variante | pasadas ok | noches recuperadas (con cota) | sin cota | neg_artefacto publicadas | neg_quieta publicadas | pasadas con filtro del Test 1 |",
               "|---|---|---|---|---|---|---|"]
    for v in VARIANTES:
        x = V[v]
        n = x["negativos"]
        lineas.append(f"| {v} | {x['pasadas_ok']} de {x['pasadas_total']} | {x['noches_recuperadas_con_cota']} de {x['noches_total']} "
                      f"| {x['noches_recuperadas_sin_cota']} | {n.get('neg_artefacto_publica', 0)} de {n.get('neg_artefacto_n', 0)} "
                      f"| {n.get('neg_quieta_publica', 0)} de {n.get('neg_quieta_n', 0)} "
                      f"| {x['pasadas_con_filtro_test1']} |")
    lineas += ["", "## Noche por noche (con cota)", "", "| noche | " + " | ".join(VARIANTES) + " |",
               "|---|" + "---|" * len(VARIANTES)]
    for clave in V["control"]["detalle_noches"]:
        lineas.append(f"| {clave} | " + " | ".join(
            "sí" if V[v]["detalle_noches"][clave]["publica_con_cota"] else "no" for v in VARIANTES) + " |")
    (a.dest / "RESULTADO.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(json.dumps({"control_instrumento": ci, "lectura": lectura,
                      "recuperadas": {v: V[v]["noches_recuperadas_con_cota"] for v in VARIANTES}}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
