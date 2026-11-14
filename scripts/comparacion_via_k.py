#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · comparacion_via_k.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Mostrar, por sensor, volcán y noche, cuánto se parecen a MIROVA el detector de producción (la vía
#                 «código MIROVA») y el anterior (K, hoy de guardia). Alimenta la pestaña «Vía, K y MIROVA» de
#                 frontend/comparacion.html. No decide nada: informa.
# Lógica        : Evalúa cada pasada con el predicado del tablero (node sobre frontend/index.html, vía
#                 scripts/banco_paridad.py), la etiqueta contra MIROVA (alerta, negativo limpio, fuera de límite, sin
#                 información) y cuenta aciertos, silencios y falsas alarmas por noche-satélite, sólo en pasadas que los
#                 dos detectores procesaron.
# Modelo/método : Conteo determinista. NO es caja negra (punto 5.5 Res.372).
# Datos entrada : Records JSON de data/mirova_equivalent y de las guardias K; caché de la historia de K (tag
#                 pre-s180-reemplazo-historia); registros públicos de MIROVA (Mirova-v1). SIN datos personales.
# Variables     : Alerta protegida (1 MW o más, lectura A), D-9 modo SN (VIIRS 375 hasta 0,05 MW no es alerta), pareo
#                 de 120 s, pasada nocturna.
# Limitaciones  : Sólo juzga noches que MIROVA miró. La historia de la vía es un reproceso (S181); la de K se evaluó una
#                 vez y avisa si el predicado del tablero cambió después.
# Refs/datos    : experiments/_s183_comparacion/PROPUESTA.md; plan docs/superpowers/plans/2026-11-14-comparacion-via-k-mirova.md.
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md.
# ════════════════════════════════════════════════════════════════════
"""Comparación diaria vía «código MIROVA» contra K contra MIROVA (S183).

POR QUÉ. Nicolás quiere asegurarse de que la vía nueva es la más fiable. Las vigilancias de las guardias sólo buscan una
cosa (alertas protegidas que la vía calla y K publica); esto mide el parecido completo con la misma vara para los dos
detectores. Se compara noche-satélite por noche-satélite y sólo donde los dos tienen record: una diferencia de cobertura no
es una diferencia de detección (se informa aparte, como «sin par»).

FUENTES DE K. Antes de la adopción de cada sensor (MODIS 2026-11-02, VIIRS 2026-11-11), la historia de K del tag
pre-s180-reemplazo-historia, evaluada una vez con `--construir-cache-k` (el tag pesa 176 MB y no se baja cada día en
Actions). Desde la adopción, la guardia (data/guardia_k_modis, data/guardia_k_viirs).

Uso diario: python scripts/comparacion_via_k.py --cons C.csv --ocr O.csv
Caché:      python scripts/comparacion_via_k.py --construir-cache-k <carpeta con los 11 JSON del tag>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import shutil
import statistics
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402
from clase_mirova import MODO_MINIMAS, alerta_protegida  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, bajar_remoto, cargar_referencia_unificada  # noqa: E402

SENSORES = ("MODIS", "VIIRS375", "VIIRS750")
# Encendido de la vía en producción (PR #934 MODIS; #974 y #983 VIIRS). Desde ese día K es la guardia.
ADOPCION = {"MODIS": "2026-11-02", "VIIRS375": "2026-11-11", "VIIRS750": "2026-11-11"}
INICIO = "2026-03-01"           # tabla de MIROVA sana desde marzo (A119)
PROD = ROOT / "data" / "mirova_equivalent"
GUARDIA_MODIS = ROOT / "data" / "guardia_k_modis"
GUARDIA_VIIRS = ROOT / "data" / "guardia_k_viirs"
CACHE_K = ROOT / "data" / "audit_continuous" / "comparacion_k_historia_cache.json"
SALIDA = ROOT / "data" / "audit_continuous" / "comparacion_via_k.json"
TAG_K = "pre-s180-reemplazo-historia"
CAMPOS_CACHE = ["vol", "b", "sensor", "dt", "disp", "pub", "dc", "d_mc"]
CAMPOS_NOCHE = ["vol", "sat", "b", "noche", "lab_tabla", "lab_comb", "prot_tabla", "prot_comb", "vrp_mirova",
                "via_pub", "via_vrp", "via_dc", "via_dmc", "k_pub", "k_vrp", "k_dc", "k_dmc", "k_fuente"]
# Los que lee frontend/comparacion.html (guard: tests/test_comparacion_via_k_s183.py).
CAMPOS_USADOS_POR_LA_PAGINA = ["vol", "sat", "b", "noche", "lab_tabla", "lab_comb", "prot_tabla", "prot_comb",
                               "vrp_mirova", "via_pub", "via_vrp", "via_dc", "via_dmc", "k_pub", "k_vrp", "k_dc",
                               "k_dmc", "k_fuente"]


def _dia_antes(fecha):
    return (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")


def ventanas(hoy):
    """Las ventanas de la página, por sensor: (inicio, fin) en fecha UTC. V183-03: la historia llega hasta el día antes
    de la adopción de cada sensor y la adopción parte ese día, así cada día cae en una ventana y con una sola fuente de K
    (historia del tag antes, guardia desde), la misma que usa la franja."""
    return {"historia": {b: (INICIO, _dia_antes(ADOPCION[b])) for b in SENSORES},
            "adopcion": {b: (ADOPCION[b], hoy) for b in SENSORES}}


def sha_predicado(html, cambio_detector_js):
    """sha256 de lo que decide si una pasada se publica: las constantes y funciones que banco_paridad extrae de
    frontend/index.html para node, más frontend/cambio_detector.js, que ese mismo código carga. V183-01: el sha de todo
    index.html cambiaba con un texto de la página (un modal) y el aviso de «predicado cambió» quedaba encendido sin
    motivo. La lista de nombres se lee de banco_paridad._JS para no tener dos listas."""
    consts = re.findall(r"constante\('(\w+)'\)", bp._JS)
    funcs = re.findall(r"'(\w+)'", bp._JS[bp._JS.index("concat(") : bp._JS.index("].map(extraer)")])
    partes = []
    for c in consts:
        m = re.search(r"const " + c + r"\s*=\s*([^;]+);", html)
        partes.append(m.group(0) if m else "SIN " + c)
    for f in funcs:
        i = html.find("function " + f + "(")
        if i < 0:
            partes.append("SIN " + f)
            continue
        j, d = html.index("{", i), 0
        for k in range(j, len(html)):
            d += {"{": 1, "}": -1}.get(html[k], 0)
            if d == 0:
                partes.append(html[i:k + 1])
                break
    partes.append(cambio_detector_js)
    return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()


def sha_predicado_actual():
    cd = bp.HTML.parent / "cambio_detector.js"
    return sha_predicado(bp.HTML.read_text(encoding="utf-8"), cd.read_text(encoding="utf-8") if cd.exists() else "")


# ------------------------------------------------------------------ cuentas
def agregar_noches(pasadas):
    """Pasadas -> noche-satélite (volcán, satélite, fecha UTC). pos si alguna pasada tiene alerta de MIROVA; neg si hay un
    negativo limpio y ninguna pos ni far_ref; el resto no se juzga. Publica si alguna pasada publica."""
    g = collections.defaultdict(list)
    for r in pasadas:
        g[(r["vol"], r["sensor"], r["noche"])].append(r)
    out = {}
    for k, lst in g.items():
        labs = {r["lab"] for r in lst}
        if "pos" in labs:
            lab = "pos"
        elif "neg_limpio" in labs and "far_ref" not in labs:
            lab = "neg"
        else:
            continue
        rep = max(lst, key=lambda r: (r["pub"], r["disp"] or 0))
        out[k] = {"lab": lab, "pub": max(r["pub"] for r in lst), "prot": any(r["protegida"] for r in lst),
                  "vrp_mirova": max((r["vrp_mirova"] for r in lst if r["vrp_mirova"] is not None), default=None),
                  "vrp_nuestro": max((r["disp"] for r in lst if r["pub"]), default=None),
                  "dc": rep["dc"], "d_mc": rep["d_mc"]}
    return out


def _tasa(a, n):
    return round(a / n, 4) if n else None


def metricas(noches, pasadas):
    """TP, FN, FP, TN por noche-satélite; protegidas; cociente nuestro/MIROVA por pasada pos publicada."""
    c = collections.Counter()
    for e in noches.values():
        if e["lab"] == "pos":
            c["TP" if e["pub"] else "FN"] += 1
            if e["prot"]:
                c["prot_TP" if e["pub"] else "prot_FN"] += 1
        else:
            c["FP" if e["pub"] else "TN"] += 1
    ratios = [r["disp"] / r["vrp_mirova"] for r in pasadas
              if r["lab"] == "pos" and r["pub"] and r["vrp_mirova"] and r["disp"] is not None]
    tp, fn, fp, tn = c["TP"], c["FN"], c["FP"], c["TN"]
    return {"TP": tp, "FN": fn, "FP": fp, "TN": tn, "recall": _tasa(tp, tp + fn), "precision": _tasa(tp, tp + fp),
            "protegidas": c["prot_TP"] + c["prot_FN"], "protegidas_perdidas": c["prot_FN"],
            "mediana_cociente": round(statistics.median(ratios), 3) if ratios else None, "n_cociente": len(ratios),
            "cuartiles_cociente": ([round(q, 3) for q in statistics.quantiles(ratios, n=4)]
                                   if len(ratios) > 1 else None)}


def _sin_par(a, otro, b):
    xs = [a[x] for x in a if a[x]["b"] == b and x not in otro]
    return {"n": len(xs), "pos": sum(r["lab"] == "pos" for r in xs),
            "pos_publica": sum(r["pub"] for r in xs if r["lab"] == "pos"),
            "protegidas": sum(bool(r["protegida"]) for r in xs),
            "protegidas_publica": sum(r["pub"] for r in xs if r["protegida"])}


def comparar(via, k, b, por_volcan=True):
    """`via` y `k`: {(volcán, satélite, instante): pasada etiquetada}. Sólo cuentan las claves comunes del sensor `b`."""
    claves = sorted(x for x in via.keys() & k.keys() if via[x]["b"] == b)
    pv, pk = [via[x] for x in claves], [k[x] for x in claves]
    res = {"n_pasadas_pareadas": len(claves), "via": metricas(agregar_noches(pv), pv),
           "k": metricas(agregar_noches(pk), pk), "sin_par_via": _sin_par(via, k, b), "sin_par_k": _sin_par(k, via, b)}
    disc = []
    for x in claves:
        a, z = via[x], k[x]
        if a["lab"] == "pos" and a["protegida"] and a["pub"] != z["pub"]:
            disc.append({"vol": x[0], "sat": x[1], "dt": x[2].strftime("%Y-%m-%d %H:%M"), "vrp_mirova": a["vrp_mirova"],
                         "via_pub": a["pub"], "via_vrp": a["disp"], "via_dc": a["dc"], "via_dmc": a["d_mc"],
                         "k_pub": z["pub"], "k_vrp": z["disp"], "k_dc": z["dc"], "k_dmc": z["d_mc"]})
    res["protegidas_discordantes"] = disc
    if por_volcan:
        res["por_volcan"] = {}
        for vol in bp.VOLS:
            cv_ = [x for x in claves if x[0] == vol]
            if cv_:
                a_, z_ = [via[x] for x in cv_], [k[x] for x in cv_]
                res["por_volcan"][vol] = {"via": metricas(agregar_noches(a_), a_),
                                          "k": metricas(agregar_noches(z_), z_)}
    return res


# ------------------------------------------------------------------ evaluación y etiquetado
def filtrar_records_k(records):
    """K puro (sin la clave `via_codigo_mirova`) desde INICIO y anterior al día de la adopción de su sensor."""
    out = []
    for r in records:
        b = bp.bucket(r.get("sensor"))
        d = (r.get("datetime_utc") or "")[:10]
        if b is None or "via_codigo_mirova" in r or not (INICIO <= d < ADOPCION[b]):
            continue
        out.append(r)
    return out


def evaluar(data_dir, coords, inner, ventana):
    """Pasadas nocturnas de una carpeta con los 11 JSON, con lo que el tablero muestra (disp) y si publica (pub)."""
    return bp.cargar_nuestros(coords, inner, ventana, data=data_dir)


def construir_cache_k(carpeta_tag, out, hoy):
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    tmp = Path(tempfile.mkdtemp(prefix="s183_cache_"))
    try:
        for vol in bp.VOLS:
            d = json.loads((Path(carpeta_tag) / f"{vol}.json").read_text(encoding="utf-8"))
            (tmp / f"{vol}.json").write_text(json.dumps({"records": filtrar_records_k(d.get("records", []))}),
                                             encoding="utf-8")
        pas = evaluar(tmp, coords, inner, (INICIO, hoy))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    filas = [[p["vol"], p["b"], p["sensor"], p["dt"].strftime("%Y-%m-%d %H:%M"), p["disp"], p["pub"], p["dc"], p["d_mc"]]
             for p in pas]
    meta = {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tag": TAG_K,
            "sha_index_html": bp.sha_git(bp.HTML), "sha_predicado": sha_predicado_actual(), "n": len(filas), "inicio": INICIO, "adopcion": ADOPCION,
            "nota": "K puro del tag, evaluado con el predicado del tablero de ese sha; sólo pasadas nocturnas"}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps({"meta": meta, "campos": CAMPOS_CACHE, "filas": filas}, separators=(",", ":")),
                         encoding="utf-8")
    return meta


def cargar_cache_k(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    campos = d.get("campos", CAMPOS_CACHE)
    out = []
    for f in d.get("filas", d.get("pasadas", [])):
        r = dict(zip(campos, f))
        r["dt"] = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        r["noche"] = r["dt"].strftime("%Y-%m-%d")
        r["vol"], r["b"] = r["vol"], r["b"]
        out.append(r)
    return out, d.get("meta", {})


def avisos_cache(meta_cache, sha_actual):
    s = meta_cache.get("sha_predicado")
    if s == sha_actual:
        return []
    return [f"El criterio de publicación del tablero cambió desde que se evaluó la historia de K (predicado {s} en el "
            f"caché, {sha_actual} hoy): la columna K de la historia usa el criterio anterior. Reconstruir el caché con "
            f"--construir-cache-k."]


def etiquetar(pasadas, ref):
    """Copia etiquetada de las pasadas contra una referencia indexada (banco_paridad.indexar_referencia)."""
    por_vb, ns, nv, _ = ref
    out = [dict(p) for p in pasadas]
    bp.etiquetar(out, por_vb, ns, nv)
    for r in out:
        al = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        tab = [f["vrp_mw"] for f in al if f["source"] == "CONS" and f["vrp_mw"] is not None]
        todos = [f["vrp_mw"] for f in al if f["vrp_mw"] is not None]
        r["vrp_mirova"] = max(tab) if tab else (max(todos) if todos else None)
        r["protegida"] = r["lab"] == "pos" and any(alerta_protegida(f) for f in al)
    return out


def _indice(pasadas, b, ini, fin):
    return {(p["vol"], p["sensor"], p["dt"]): p for p in pasadas if p["b"] == b and ini <= p["noche"] <= fin}


def serie_k(historia, guardia):
    """K continuo para la franja: la historia antes del día de la adopción de cada sensor, la guardia desde ese día. Sin
    este corte, una noche entre el inicio de la guardia y la adopción tendría dos K y se contaría dos veces."""
    return ([p for p in historia if p["noche"] < ADOPCION[p["b"]]]
            + [p for p in guardia if p["noche"] >= ADOPCION[p["b"]]])


def filas_noches(series, hoy):
    """Una fila por noche-satélite con algo que mirar: alerta de MIROVA en alguna referencia o algún detector publica.
    `series[ref] = (via_etiquetadas, k_etiquetadas)`, con K ya armado (historia antes de la adopción, guardia desde)."""
    nv = {ref: agregar_noches(v) for ref, (v, _) in series.items()}
    nk = {ref: agregar_noches(k) for ref, (_, k) in series.items()}
    claves = set()
    for ref in series:
        claves |= nv[ref].keys() | nk[ref].keys()
    filas = []
    for key in sorted(claves, key=lambda x: (x[2], x[0], x[1])):
        vol, sat, noche = key
        if not (INICIO <= noche <= hoy):
            continue
        b = bp.bucket(sat)
        lab = {ref: (nv[ref].get(key) or nk[ref].get(key) or {}).get("lab") for ref in series}
        prot = {ref: int(bool((nv[ref].get(key) or nk[ref].get(key) or {}).get("prot"))) for ref in series}
        v, k = nv["combinado"].get(key) or nv["tabla"].get(key), nk["combinado"].get(key) or nk["tabla"].get(key)
        if not ("pos" in lab.values() or (v and v["pub"]) or (k and k["pub"])):
            continue
        vm = [(nv[r].get(key) or nk[r].get(key) or {}).get("vrp_mirova") for r in ("tabla", "combinado")]
        filas.append([vol, sat, b, noche, lab.get("tabla"), lab.get("combinado"), prot.get("tabla"),
                      prot.get("combinado"), next((x for x in vm if x is not None), None),
                      v["pub"] if v else None, v["vrp_nuestro"] if v else None, v["dc"] if v else None,
                      v["d_mc"] if v else None, k["pub"] if k else None, k["vrp_nuestro"] if k else None,
                      k["dc"] if k else None, k["d_mc"] if k else None,
                      ("historia" if noche < ADOPCION[b] else "guardia") if k else None])
    return {"campos": CAMPOS_NOCHE, "filas": filas}


# ------------------------------------------------------------------ principal
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prod", default=str(PROD))
    ap.add_argument("--guardia-modis", default=str(GUARDIA_MODIS))
    ap.add_argument("--guardia-viirs", default=str(GUARDIA_VIIRS))
    ap.add_argument("--cache-k", default=str(CACHE_K))
    ap.add_argument("--construir-cache-k", metavar="CARPETA_TAG")
    ap.add_argument("--cons", help="consolidado de Mirova-v1 (por defecto el snapshot del repo)")
    ap.add_argument("--ocr")
    ap.add_argument("--remoto", metavar="CARPETA", help="bajar consolidado y OCR del remoto de Mirova-v1")
    ap.add_argument("--sin-capas-historicas", action="store_true", help="sin respaldo ni filas recuperadas (pruebas)")
    ap.add_argument("--hoy", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--out", default=str(SALIDA))
    a = ap.parse_args(argv)

    if a.construir_cache_k:
        meta = construir_cache_k(a.construir_cache_k, a.cache_k, a.hoy)
        print("caché de K:", meta)
        return 0

    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    sha = bp.sha_git(bp.HTML)
    sha_pred = sha_predicado_actual()
    cons, ocr, proc = Path(a.cons or SNAP_CONS), Path(a.ocr or SNAP_OCR), {"fuente": "archivo"}
    if a.remoto:
        info = bajar_remoto(Path(a.remoto))
        cons, ocr = Path(info["registro_vrp_consolidado.csv"]["path"]), Path(info["registro_vrp_ocr.csv"]["path"])
        proc = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    elif a.cons is None:
        proc = {"fuente": "snapshot"}
    capas = {"respaldo_path": None, "historico_path": None} if a.sin_capas_historicas else {}
    filas_ref = cargar_referencia_unificada(cons, ocr, **capas)
    refs = {"tabla": [f for f in filas_ref if f["source"] == "CONS"], "combinado": filas_ref}
    total = (INICIO, a.hoy)

    via = evaluar(a.prod, coords, inner, total)
    guardia = ([p for p in evaluar(a.guardia_modis, coords, inner, total) if p["b"] == "MODIS"]
               + [p for p in evaluar(a.guardia_viirs, coords, inner, total) if p["b"] != "MODIS"])
    hist, meta_cache = cargar_cache_k(a.cache_k)
    vents = ventanas(a.hoy)

    resultados, series = {}, {}
    for nombre, fil in refs.items():
        idx = bp.indexar_referencia(fil, coords, total, regla_minimas=MODO_MINIMAS)
        v_l, g_l, h_l = etiquetar(via, idx), etiquetar(guardia, idx), etiquetar(hist, idx)
        for vent, por_b in vents.items():
            for b, (ini, fin) in por_b.items():
                k_l = h_l if vent == "historia" else g_l
                resultados[f"{nombre}|{vent}|{b}"] = comparar(_indice(v_l, b, ini, fin), _indice(k_l, b, ini, fin), b)
        series[nombre] = (v_l, serie_k(h_l, g_l))

    ult_tabla = max((f["fecha_utc"] for f in refs["tabla"]), default=None)
    guardia_hasta = max((p["noche"] for p in guardia), default=None)
    salida = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "hoy": a.hoy,
                       "sha_index_html": sha, "sha_predicado": sha_pred, "referencia": proc, "regla_minimas": MODO_MINIMAS, "adopcion": ADOPCION,
                       "ventanas": vents, "ultima_fila_tabla_mirova": ult_tabla, "guardia_hasta": guardia_hasta,
                       "cache_k": {k: meta_cache.get(k) for k in ("tag", "sha_predicado", "generado_utc", "n")},
                       "avisos": avisos_cache(meta_cache, sha_pred)},
              "resultados": resultados, "noches": filas_noches(series, a.hoy)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for clave in sorted(resultados):
        if clave.startswith("tabla|"):
            r = resultados[clave]
            print(f"{clave:28s} pares {r['n_pasadas_pareadas']:6d} | vía rec {r['via']['recall']} prec "
                  f"{r['via']['precision']} prot -{r['via']['protegidas_perdidas']} | K rec {r['k']['recall']} prec "
                  f"{r['k']['precision']} prot -{r['k']['protegidas_perdidas']}")
    print(f"noches {len(salida['noches']['filas'])} | avisos {salida['meta']['avisos']} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
