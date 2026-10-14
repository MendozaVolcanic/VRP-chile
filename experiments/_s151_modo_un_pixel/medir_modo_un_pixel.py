# -*- coding: utf-8 -*-
"""Tarea 1.8 del loop: que regla de magnitud para cumulos chicos se acerca mas a MIROVA, en reposo y en erupcion.

POR QUE. `pipeline/single_pixel_mode.py` publica el pixel mas caliente cuando el cumulo primario tiene 3 pixeles
o menos y su magnitud de entrada es menor a 5 MW; si no, la suma. Nacio para el reposo (S77: MIROVA informaba un
pixel donde nosotros sumabamos dos o tres marginales). En la erupcion de Nevados de Chillan produce saltos
(AUDIT_S150 C-03: 2,66, 11,08 y 2,49 MW en 54 minutos contra 9,0, 10,0 y 7,06 de MIROVA) y no es monotono.

QUE HACE, sin correr el pipeline (solo records en disco):
  1. Aisla los pixeles de cada cumulo de 1 a 3 pixeles: busca entre `anomaly_pixels` y `discarded_anomaly_pixels`
     el conjunto cuyo promedio simple reproduce el centroide persistido (`pipeline/clustering.py` lo calcula sin
     ponderar). Si no lo encuentra, el record queda NO reconstruible y se cuenta aparte.
  2. CONTROL: la regla actual reconstruida debe reproducir el `pc.vrp_mw` persistido (tolerancia 0,0015 MW, umbral
     de aprobacion 99 %, fijados en DECLARACION.md antes de mirar). Control negativo: la suma no debe reproducirlo.
  3. Recalcula `pc.vrp_mw` bajo las variantes de DECLARACION.md §3 y pasa cada record por el predicado REAL del
     tablero (node, funciones copiadas de frontend/index.html por scripts/banco_paridad.py).
  4. Parea con la referencia unificada de MIROVA (+-2 min, etiquetas de banco_paridad) y mide la razon de
     magnitud por variante, sensor, regimen, tramo A119 y volcan; cuenta publicaciones que cambian, en especial
     las de alertas protegidas (docs/S151_CRITERIO_CLASE_MIROVA.md, lecturas A y B).

Uso:
  python experiments/_s151_modo_un_pixel/medir_modo_un_pixel.py --c0 <ruta al NevadosDeChillan.json del brazo
      _s146_ab_control del run 38560317428, extraido con git archive>
Salidas: resultado.json y salida.txt en esta carpeta.
"""
from __future__ import annotations

import argparse
import collections
import io
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from banco_paridad import (CAMPOS_JS, HTML, VOLS, bucket, correr_node,  # noqa: E402
                           es_alerta, etiquetar, indexar_referencia,
                           inner_desde_html, parear, sha_git)
from clase_mirova import pasadas_protegidas  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

DATA = ROOT / "data" / "mirova_equivalent"
INICIO, INICIO_VIIRS = "2026-03-01", "2026-04-01"
CORTE_OCR = "2026-06-13"
INICIO_ERUPCION = "2026-09-28"
TOL_CONTROL_MW = 0.0015
APROBACION_CONTROL = 0.99
TOL_CENTROIDE = 2e-5
N_BOOT = 2000
UMBRAL_ACTUAL = 5.0
BARRIDO = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, math.inf]
VARIANTES = ["A", "B_off", "B_sum", "C", "D"]

_out = io.StringIO()


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _out.write(s + "\n")


# ------------------------------------------------------------------ reconstruccion del cumulo
def identificar(pc, pix):
    """Pixeles del cumulo cuyo promedio simple reproduce el centroide, o None."""
    n = int(pc.get("n_pixels") or 0)
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None or clon is None or n < 1:
        return None
    pool = [p for p in pix if p.get("lat") is not None and p.get("lon") is not None
            and abs(p["lat"] - clat) < 0.08 and abs(p["lon"] - clon) < 0.1]
    pool.sort(key=lambda p: (p["lat"] - clat) ** 2 + (p["lon"] - clon) ** 2)
    pool = pool[:60]
    for comb in itertools.combinations(pool, n):
        if (abs(sum(p["lat"] for p in comb) / n - clat) < TOL_CENTROIDE
                and abs(sum(p["lon"] for p in comb) / n - clon) < TOL_CENTROIDE):
            return [float(p.get("vrp_mw") or 0.0) for p in comb]
    return None


def variantes_de(pc):
    """Valores de pc.vrp_mw por variante para un cumulo, mas el estado de la reconstruccion.

    Devuelve (estado, dict). estado: 'n>3' | 'n1' | 'ident' | 'no_ident'. Un valor None = desconocido.
    Las variantes `_lo` y `_hi` son los dos extremos cuando la magnitud focal no dice que pixeles entraron.
    """
    n = int(pc.get("n_pixels") or 0)
    pers = float(pc.get("vrp_mw") or 0.0)
    todos = {v: pers for v in VARIANTES}
    todos.update({"T%s" % t: pers for t in BARRIDO})
    if n > 3:
        return "n>3", todos, None
    if n <= 1:
        return "n1", todos, None
    vr = pc.get("_vrps")
    if vr is None:
        return "no_ident", {k: None for k in todos}, None
    pico, suma = max(vr), sum(vr)
    spm = pc.get("single_pixel_mode") is True
    capado = pc.get("d9_capped") is True
    focal = pc.get("focal_magnitude") is True
    degradado = pc.get("focal_degraded") is True
    if capado:
        return "ident", todos, (pico, suma)
    if not spm:
        pres = [pers]                      # el modo no actuo: lo persistido ES la entrada
    elif not focal:
        pres = [suma]
    elif degradado:
        pres = [pico]
    else:
        pres = [pico, suma]                # foco sin decir que pixeles: los dos extremos
        if suma >= UMBRAL_ACTUAL:
            pres = [pico]                  # el modo actuo, asi que la entrada era < 5: la suma no pudo ser

    def una(pre):
        o = {"A": pico if pre < UMBRAL_ACTUAL else pre, "B_off": pre, "C": pico if pre < 1.0 else pre}
        o["B_sum"] = suma
        o["D"] = pico if pico < 1.0 else suma
        if focal and suma > UMBRAL_ACTUAL:  # el tope D9 pudo actuar sobre la suma y el record no lo dice
            o["B_sum"] = None
            if o["D"] == suma:
                o["D"] = None
        for t in BARRIDO:
            o["T%s" % t] = pico if pre < t else pre
        return {k: (None if v is None else round(v, 3)) for k, v in o.items()}

    vals = [una(p) for p in pres]
    if len(vals) == 1:
        return "ident", vals[0], (pico, suma)
    out = {}
    for k in vals[0]:
        a, b = vals[0][k], vals[1][k]
        out[k] = a if a == b else ("AMBIGUO", a, b)
    return "ident", out, (pico, suma)


# ------------------------------------------------------------------ records
def cargar(fuente, rutas, coords, inner, desde, hasta):
    recs = []
    for vol, ruta in rutas:
        with open(ruta, encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            dia = (r.get("datetime_utc") or "")[:10]
            if b is None or not (desde <= dia <= hasta):
                continue
            if b != "MODIS" and dia < INICIO_VIIRS:
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster")
            slim = {k: r.get(k) for k in CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            rec = {"fuente": fuente, "vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                   "sensor": r.get("sensor"), "slim": slim,
                   "regimen": "erupcion" if (vol == "NevadosDeChillan" and dia >= INICIO_ERUPCION) else "reposo",
                   "tramo": "mar-jun12" if dia < CORTE_OCR else "jun13-oct",
                   "estado": "sin_pc", "vals": None}
            if pc:
                n = int(pc.get("n_pixels") or 0)
                pcx = dict(pc)
                if 2 <= n <= 3:
                    pix = (r.get("anomaly_pixels") or []) + (r.get("discarded_anomaly_pixels") or [])
                    pcx["_vrps"] = identificar(pc, pix)
                rec["estado"], rec["vals"], rec["pico_suma"] = variantes_de(pcx)
                rec["spm"] = pc.get("single_pixel_mode")
                rec["n_px"] = n
                rec["pers"] = float(pc.get("vrp_mw") or 0.0)
                rec["marcas"] = {k: pc.get(k) for k in ("focal_magnitude", "focal_degraded", "d9_capped")}
            recs.append(rec)
    return recs


# ------------------------------------------------------------------ predicado del tablero
def predicado(recs, clave):
    """Corre node sobre los records cuya variante difiere de lo persistido; el resto hereda la base."""
    casos, idx = [], []
    for i, r in enumerate(recs):
        if r["vals"] is None:
            continue
        v = r["vals"].get(clave)
        for k, vv in (("lo", v[1]), ("hi", v[2])) if isinstance(v, tuple) else (("", v),):
            if vv is None or abs(vv - r["pers"]) < 1e-9:
                continue
            s = dict(r["slim"])
            s["primary_cluster"] = dict(s["primary_cluster"], vrp_mw=vv)
            casos.append([s, r["inner"]])
            idx.append((i, k))
    res = correr_node(casos) if casos else []
    out = {}
    for (i, k), p in zip(idx, res):
        out[(i, k)] = (p[4], p[3] if p[4] else 0.0)
    return out


def magnitud(r, clave, nodo, extremo):
    """(publica, magnitud publicada) de la variante; None si desconocida."""
    v = r["vals"].get(clave) if r["vals"] is not None else 0
    if r["vals"] is None:
        return r["pub"], r["mag"]
    if isinstance(v, tuple):
        v = v[1] if extremo == "lo" else v[2]
        k = extremo
    else:
        k = ""
    if v is None:
        return None
    if abs(v - r["pers"]) < 1e-9:
        return r["pub"], r["mag"]
    return nodo[(r["_i"], k)]


# ------------------------------------------------------------------ estadistica
def boot_mediana(vals, grupos, rng):
    vals, grupos = np.asarray(vals, float), np.asarray(grupos)
    if len(vals) == 0:
        return None
    u = np.unique(grupos)
    por = {g: vals[grupos == g] for g in u}
    meds = []
    for _ in range(N_BOOT):
        s = rng.choice(u, size=len(u), replace=True)
        meds.append(np.median(np.concatenate([por[g] for g in s])))
    return [round(float(np.percentile(meds, 2.5)), 3), round(float(np.percentile(meds, 97.5)), 3)]


def boot_media(vals, grupos, rng):
    vals, grupos = np.asarray(vals, float), np.asarray(grupos)
    if len(vals) == 0:
        return None
    u = np.unique(grupos)
    sumas = np.array([vals[grupos == g].sum() for g in u])
    cuentas = np.array([(grupos == g).sum() for g in u])
    ms = []
    for _ in range(N_BOOT):
        s = rng.integers(0, len(u), len(u))
        ms.append(sumas[s].sum() / cuentas[s].sum())
    return [round(float(np.percentile(ms, 2.5)), 4), round(float(np.percentile(ms, 97.5)), 4)]


def resumen_razon(pares, rng, con_ic=True):
    if not pares:
        return {"n": 0}
    rz = np.array([p[0] for p in pares])
    g = [p[1] for p in pares]
    lg = np.abs(np.log10(rz))
    return {"n": len(rz), "n_noches": len(set(g)), "mediana": round(float(np.median(rz)), 3),
            "ic95_mediana": boot_mediana(rz, g, rng) if con_ic else None,
            "p25": round(float(np.percentile(rz, 25)), 3), "p75": round(float(np.percentile(rz, 75)), 3),
            "frac_bajo_0_5": round(float(np.mean(rz < 0.5)), 3), "frac_sobre_2": round(float(np.mean(rz > 2)), 3),
            "mediana_abs_log10": round(float(np.median(lg)), 3)}


# ------------------------------------------------------------------ main
def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--c0", required=True, help="NevadosDeChillan.json del brazo _s146_ab_control (run 38560317428)")
    ap.add_argument("--hasta", default="2026-10-14")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(20261014)

    coords, inner = _coords_por_volcan(), inner_desde_html()
    filas = cargar_referencia_unificada()
    por_vb, noche_sensor, noche_volcan, n_ref = indexar_referencia(filas, coords, (INICIO, a.hasta))
    prot = {"A": pasadas_protegidas(filas, lectura="A"), "B": pasadas_protegidas(filas, lectura="B")}

    fuentes = {
        "prod": cargar("prod", [(v, DATA / f"{v}.json") for v in VOLS], coords, inner, INICIO, a.hasta),
        "c0": cargar("c0", [("NevadosDeChillan", Path(a.c0))], coords, inner, INICIO, a.hasta),
    }
    say("TAREA 1.8: modo de un solo pixel contra MIROVA (records en disco, sin correr el pipeline)")
    say("referencia: filas %d, ultima %s | index.html sha %s | c0 %s" % (
        len(filas), max(f["fecha_utc"] for f in filas), sha_git(HTML), a.c0.replace("\\", "/").split("/salidas/")[-1]))

    resultado = {"meta": {"ventana": [INICIO, a.hasta], "inicio_viirs": INICIO_VIIRS, "corte_ocr": CORTE_OCR,
                          "inicio_erupcion": INICIO_ERUPCION, "tol_control_mw": TOL_CONTROL_MW,
                          "aprobacion_control": APROBACION_CONTROL, "n_boot": N_BOOT,
                          "sha_index_html": sha_git(HTML)}}

    for nombre, recs in fuentes.items():
        say("\n" + "=" * 100)
        say("FUENTE %s: %d records nocturnos en ventana" % (nombre, len(recs)))
        for i, r in enumerate(recs):
            r["_i"] = i
            r["inner"] = inner[r["vol"]]
        etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        # base: lo persistido, con el predicado del tablero
        base = correr_node([[r["slim"], r["inner"]] for r in recs])
        for r, p in zip(recs, base):
            r["pub"], r["mag"] = p[4], (p[3] if p[4] else 0.0)
        res = {"estados": {}, "control": {}, "variantes": {}}

        # ---------------- reconstruccion y control
        est = collections.Counter((r["b"], r["estado"]) for r in recs)
        res["estados"] = {"%s|%s" % k: v for k, v in sorted(est.items())}
        say("\n1. RECONSTRUCCION (cumulos de 2 a 3 pixeles; n1 y n>3 no cambian con ninguna variante)")
        for b in ("MODIS", "VIIRS375", "VIIRS750"):
            say("  %-9s ident %5d | no_ident %5d | n1 %6d | n>3 %6d | sin cumulo %6d" % (
                b, est[(b, "ident")], est[(b, "no_ident")], est[(b, "n1")], est[(b, "n>3")], est[(b, "sin_pc")]))
        ctl = [r for r in recs if r["estado"] == "ident" and r.get("spm") is True]
        ok_max = [r for r in ctl if abs(round(r["pico_suma"][0], 3) - r["pers"]) <= TOL_CONTROL_MW]
        ok_suma = [r for r in ctl if abs(round(r["pico_suma"][1], 3) - r["pers"]) <= TOL_CONTROL_MW]
        no_spm = [r for r in recs if r["estado"] == "ident" and r.get("spm") is False
                  and not r["marcas"].get("d9_capped") and not r["marcas"].get("focal_magnitude")]
        ok_nospm = [r for r in no_spm if abs(round(r["pico_suma"][1], 3) - r["pers"]) <= TOL_CONTROL_MW]
        frac = len(ok_max) / len(ctl) if ctl else None
        _ok_ids = {id(r) for r in ok_max}
        fallas = [r for r in ctl if id(r) not in _ok_ids]
        res["control"] = {
            "n_modo_activo_multipixel_ident": len(ctl), "reproduce_con_max": len(ok_max),
            "fraccion": round(frac, 5) if frac is not None else None,
            "PASA": bool(frac is not None and frac >= APROBACION_CONTROL),
            "negativo_reproduce_con_suma": len(ok_suma),
            "sin_modo_no_focal_no_capado_ident": len(no_spm), "sin_modo_reproduce_con_suma": len(ok_nospm),
            "fallas": [{"vol": r["vol"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"],
                        "pers": r["pers"], "pico": round(r["pico_suma"][0], 4), "suma": round(r["pico_suma"][1], 4),
                        **r["marcas"]} for r in fallas],
        }
        say("\n2. CONTROL de la reconstruccion (tolerancia %.4f MW, aprueba con >= %.0f %%)" % (
            TOL_CONTROL_MW, 100 * APROBACION_CONTROL))
        say("  modo activo, 2-3 px, identificados: %d | reproduce pc.vrp_mw con el pico: %d (%.3f %%) -> %s" % (
            len(ctl), len(ok_max), 100 * (frac or 0), "PASA" if res["control"]["PASA"] else "FALLA"))
        say("  control negativo, la SUMA reproduce pc.vrp_mw en: %d de %d (debe ser minoria)" % (len(ok_suma), len(ctl)))
        say("  sin modo, sin foco ni tope, identificados: %d | la suma reproduce: %d" % (len(no_spm), len(ok_nospm)))
        for f in res["control"]["fallas"][:12]:
            say("    falla:", json.dumps(f, ensure_ascii=False))

        # ---------------- variantes por el predicado
        claves = VARIANTES[1:] + ["T%s" % t for t in BARRIDO]
        nodos = {k: predicado(recs, k) for k in claves}

        def mag_var(r, k, ext):
            if k == "A":
                return r["pub"], r["mag"]
            return magnitud(r, k, nodos[k], ext)

        # pares con alerta y fuente de la referencia
        for r in recs:
            r["ref_vrp"] = None
            if r["lab"] != "pos":
                continue
            fl = [f for f in parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if es_alerta(f["tipo"])]
            cons = [f for f in fl if f["source"] == "CONS" and (f["vrp_mw"] or 0) > 0]
            ocr = [f for f in fl if f["source"] == "OCR" and (f["vrp_mw"] or 0) > 0]
            src = cons or ocr
            if src:
                r["ref_vrp"] = max(f["vrp_mw"] for f in src)
                r["ref_src"] = "CONS" if cons else "OCR"
            claves_p = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]) for f in fl}
            r["prot_A"] = bool(claves_p & prot["A"])
            r["prot_B"] = bool(claves_p & prot["B"])

        def decide(r):
            # tramo A119: antes del 13-jun decide la tabla; las alertas solo del OCR van aparte
            return r["ref_vrp"] is not None and not (r["tramo"] == "mar-jun12" and r["ref_src"] == "OCR")

        pares_base = [r for r in recs if r["lab"] == "pos" and r["ref_vrp"] is not None]
        say("\n3. PARES con alerta de MIROVA: %d (deciden %d; solo OCR antes del 13-jun, aparte: %d)" % (
            len(pares_base), sum(decide(r) for r in pares_base), sum(not decide(r) for r in pares_base)))

        cambios_pub = {}
        for k in VARIANTES[1:] + ["T%s" % t for t in BARRIDO]:
            for ext in ("lo", "hi"):
                c = collections.Counter()
                for r in recs:
                    mv = mag_var(r, k, ext)
                    if mv is None:
                        c["desconocido"] += 1
                        continue
                    if mv[0] != r["pub"]:
                        c["cambia_%s_%s" % (r["lab"], "a_publica" if mv[0] else "a_calla")] += 1
                        if r["lab"] == "pos" and r.get("prot_A"):
                            c["protegida_A"] += 1
                        if r["lab"] == "pos" and r.get("prot_B"):
                            c["protegida_B"] += 1
                cambios_pub["%s|%s" % (k, ext)] = dict(c)
        res["cambios_publicacion"] = cambios_pub
        say("\n4. PUBLICACIONES que cambian contra la regla actual (predicado del tablero, todos los records)")
        for k in VARIANTES[1:]:
            say("  %-6s lo %s | hi %s" % (k, cambios_pub[k + "|lo"], cambios_pub[k + "|hi"]))
        say("  alertas protegidas que cambian de publicacion (lectura A / B), todas las variantes y extremos: %d / %d" % (
            sum(v.get("protegida_A", 0) for v in cambios_pub.values()),
            sum(v.get("protegida_B", 0) for v in cambios_pub.values())))
        pb = collections.Counter((r["b"], r["estado"], bool(r["pub"])) for r in recs if r["lab"] == "pos")
        res["pares_por_estado"] = {"%s|%s|%s" % k: v for k, v in sorted(pb.items())}
        say("  pasadas con alerta por sensor, estado del cumulo y si publicamos: %s" % res["pares_por_estado"])
        nd = collections.Counter((r["b"], r["estado"], r["slim"].get("distance_class"))
                                 for r in recs if r["lab"] == "pos" and not r["pub"])
        res["no_publicadas_por_etiqueta"] = {"%s|%s|%s" % k: v for k, v in sorted(nd.items(), key=str)}
        say("  pasadas con alerta que NO publicamos, por etiqueta de distancia: %s" % res["no_publicadas_por_etiqueta"])

        # ---------------- razon de magnitud
        def razones(k, ext, filtro):
            out = []
            for r in pares_base:
                if not decide(r) or not filtro(r):
                    continue
                mv = mag_var(r, k, ext)
                if mv is None or not mv[0] or mv[1] <= 0 or not r["pub"]:
                    continue
                out.append((mv[1] / r["ref_vrp"], "%s|%s" % (r["vol"], r["noche"]), r))
            return out

        def comunes(ext, filtro):
            """Pares donde TODAS las variantes son conocidas y publican: comparacion pareada justa."""
            sel = []
            for r in pares_base:
                if not decide(r) or not filtro(r) or not r["pub"]:
                    continue
                ok = True
                for k in VARIANTES:
                    mv = mag_var(r, k, ext)
                    if mv is None or not mv[0] or mv[1] <= 0:
                        ok = False
                        break
                if ok:
                    sel.append(r)
            return sel

        for r in pares_base:
            r["afectado"] = any(
                (mv := mag_var(r, k, "lo")) is not None and abs(mv[1] - r["mag"]) > 1e-9 for k in VARIANTES[1:])
        estratos = {"todo": lambda r: True,
                    "solo_afectados": lambda r: r["afectado"],
                    "solo_afectados|reposo": lambda r: r["afectado"] and r["regimen"] == "reposo",
                    "solo_afectados|erupcion": lambda r: r["afectado"] and r["regimen"] == "erupcion"}
        for reg in ("reposo", "erupcion"):
            estratos[reg] = (lambda reg: lambda r: r["regimen"] == reg)(reg)
            for b in ("MODIS", "VIIRS375", "VIIRS750"):
                estratos["%s|%s" % (reg, b)] = (lambda reg, b: lambda r: r["regimen"] == reg and r["b"] == b)(reg, b)
                for t in ("mar-jun12", "jun13-oct"):
                    estratos["%s|%s|%s" % (reg, b, t)] = (
                        lambda reg, b, t: lambda r: r["regimen"] == reg and r["b"] == b and r["tramo"] == t)(reg, b, t)
        for v in VOLS:
            for b in ("MODIS", "VIIRS375", "VIIRS750"):
                estratos["vol|%s|%s" % (v, b)] = (lambda v, b: lambda r: r["vol"] == v and r["b"] == b
                                                   and r["regimen"] == "reposo")(v, b)

        tabla = {}
        for ext in ("lo", "hi"):
            for nom, filt in estratos.items():
                sel = comunes(ext, filt)
                if not sel:
                    continue
                fila = {"n_pares": len(sel),
                        "n_afectados": sum(1 for r in sel if any(
                            abs(mag_var(r, k, ext)[1] - r["mag"]) > 1e-9 for k in VARIANTES[1:]))}
                g = ["%s|%s" % (r["vol"], r["noche"]) for r in sel]
                logA = np.array([abs(math.log10(r["mag"] / r["ref_vrp"])) for r in sel])
                for k in VARIANTES + ["T%s" % t for t in BARRIDO]:
                    rz = []
                    for r in sel:
                        mv = mag_var(r, k, ext)
                        rz.append(None if (mv is None or not mv[0] or mv[1] <= 0) else mv[1] / r["ref_vrp"])
                    if any(x is None for x in rz):
                        continue
                    con_ic = k in VARIANTES and not nom.startswith("vol|")
                    s = resumen_razon(list(zip(rz, g)), rng, con_ic)
                    if k != "A":
                        d = np.abs(np.log10(np.array(rz))) - logA
                        s["dif_media_abs_log10_vs_A"] = round(float(d.mean()), 4)
                        s["ic95_dif"] = boot_media(d, g, rng) if con_ic else None
                    fila[k] = s
                tabla["%s|%s" % (nom, ext)] = fila
        res["razon"] = tabla

        say("\n5. RAZON nuestra/MIROVA por variante (pares comunes; mediana [IC95] | |log10| mediana | dif. pareada vs A [IC95])")
        for nom in list(estratos):
            if nom.startswith("vol|"):
                continue
            for ext in ("lo", "hi"):
                f = tabla.get("%s|%s" % (nom, ext))
                if not f:
                    continue
                def _punto(fx):
                    return json.dumps({k: {c: v for c, v in (fx.get(k) or {}).items() if not c.startswith("ic95")}
                                       for k in VARIANTES}, sort_keys=True)
                if ext == "hi" and _punto(f) == _punto(tabla.get("%s|lo" % nom, {})):
                    say("  [%s hi] igual al extremo lo en todas las variantes" % nom)
                    continue
                say("  [%s %s] pares %d, afectados por alguna variante %d" % (nom, ext, f["n_pares"], f["n_afectados"]))
                for k in VARIANTES:
                    s = f.get(k)
                    if not s:
                        continue
                    say("     %-6s med %6.3f %-16s p25-p75 %5.3f-%-6.3f <0,5 %4.2f >2 %4.2f |log| %5.3f %s" % (
                        k, s["mediana"], s["ic95_mediana"], s["p25"], s["p75"], s["frac_bajo_0_5"],
                        s["frac_sobre_2"], s["mediana_abs_log10"],
                        "" if k == "A" else "dif %+.4f %s" % (s["dif_media_abs_log10_vs_A"], s["ic95_dif"])))
        say("\n   REGLA DE DECISION (DECLARACION.md §4), por variante y extremo:")
        veredictos = {}
        for k in VARIANTES[1:]:
            for ext in ("lo", "hi"):
                motivos = []
                for reg in ("reposo", "erupcion"):
                    f = tabla.get("%s|%s" % (reg, ext), {}).get(k)
                    if not f or f.get("ic95_dif") is None:
                        motivos.append("%s sin dato" % reg)
                        continue
                    lo_, hi_ = f["ic95_dif"]
                    n = tabla["%s|%s" % (reg, ext)]["n_pares"]
                    if reg == "erupcion" and n < 10:
                        if lo_ > 0:
                            motivos.append("erupcion empeora (n<10)")
                    elif not hi_ < 0:
                        motivos.append("%s IC [%s, %s] no queda bajo 0" % (reg, lo_, hi_))
                for reg in ("reposo", "erupcion"):
                    for b in ("MODIS", "VIIRS375", "VIIRS750"):
                        fs = tabla.get("%s|%s|%s" % (reg, b, ext), {})
                        f = fs.get(k)
                        if f and fs["n_pares"] >= 10 and f.get("ic95_dif") and f["ic95_dif"][0] > 0:
                            motivos.append("%s|%s empeora" % (reg, b))
                cp = cambios_pub.get("%s|%s" % (k, ext), {})
                if cp.get("protegida_A") or cp.get("protegida_B"):
                    motivos.append("cambia una alerta protegida")
                veredictos["%s|%s" % (k, ext)] = {"gana": not motivos, "motivos": motivos}
                say("     %-6s %s: %s" % (k, ext, "GANA CON CLARIDAD" if not motivos else "no gana: " + "; ".join(motivos)))
        res["veredictos"] = veredictos

        say("\n   por volcan (reposo, extremo lo; sensor: n pares, mediana A / B_sum / C / D)")
        for v in VOLS:
            partes = []
            for b in ("MODIS", "VIIRS375", "VIIRS750"):
                f = tabla.get("vol|%s|%s|lo" % (v, b))
                if f and f.get("A"):
                    partes.append("%s n%d %.2f/%.2f/%.2f/%.2f" % (b, f["n_pares"], f["A"]["mediana"], f["B_sum"]["mediana"],
                                                              f["C"]["mediana"], f["D"]["mediana"]))
            say("   %-20s %s" % (v, " | ".join(partes)))

        say("\n6. BARRIDO descriptivo del umbral (sobre la entrada del modo), extremo lo: mediana |log10 razon|")
        for nom in ("reposo|MODIS", "reposo|VIIRS750", "erupcion|MODIS", "erupcion|VIIRS750", "erupcion|VIIRS375"):
            f = tabla.get("%s|lo" % nom)
            if f:
                say("   %-18s n %4d  " % (nom, f["n_pares"]) + "  ".join(
                    "T%s:%.3f" % (t, f["T%s" % t]["mediana_abs_log10"]) for t in BARRIDO if f.get("T%s" % t)))

        # ---------------- negativos limpios
        say("\n7. NEGATIVOS LIMPIOS: publicaciones y magnitud publicada (mediana / suma, MW)")
        negs = {}
        for b in ("MODIS", "VIIRS375", "VIIRS750"):
            for reg in ("reposo", "erupcion"):
                sel = [r for r in recs if r["lab"] == "neg_limpio" and r["b"] == b and r["regimen"] == reg]
                if not sel:
                    continue
                # records con alguna variante desconocida (cumulo de 2-3 px no identificado) fuera de TODAS
                conoc = [r for r in sel if all(mag_var(r, k, e) is not None for k in VARIANTES for e in ("lo", "hi"))]
                fila = {"n": len(sel), "n_excluidos_no_reconstruibles": len(sel) - len(conoc)}
                for k in VARIANTES:
                    for ext in ("lo", "hi"):
                        ms = [mag_var(r, k, ext) for r in conoc]
                        pubm = [m[1] for m in ms if m[0]]
                        fila["%s|%s" % (k, ext)] = {"publica": len(pubm),
                                                    "mediana": round(float(np.median(pubm)), 4) if pubm else None,
                                                    "suma": round(float(sum(pubm)), 3)}
                negs["%s|%s" % (reg, b)] = fila
                say("   %-18s n %5d (excl. %d)  " % ("%s|%s" % (reg, b), len(conoc), len(sel) - len(conoc)) + "  ".join(
                    "%s:%s/%s/%s" % (k, fila.get(k + "|lo", {}).get("publica"), fila.get(k + "|lo", {}).get("mediana"),
                                     fila.get(k + "|lo", {}).get("suma")) for k in VARIANTES))
        res["negativos_limpios"] = negs

        # ---------------- casos de Chillan en erupcion
        say("\n8. CHILLAN EN ERUPCION, pares MODIS y VIIRS 750 (MIROVA | A | B_off | B_sum | C | D; n px; marcas)")
        casos = []
        for r in sorted(pares_base, key=lambda r: r["dt"]):
            if r["regimen"] != "erupcion" or r["b"] == "VIIRS375":
                continue
            fila = {"dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "mirova": r["ref_vrp"],
                    "fuente_ref": r["ref_src"], "n_px": r.get("n_px"), "estado": r["estado"], "decide": decide(r)}
            for k in VARIANTES:
                mv = mag_var(r, k, "lo")
                fila[k] = None if mv is None else (round(mv[1], 3) if mv[0] else 0.0)
            fila.update(r.get("marcas") or {})
            casos.append(fila)
            say("   %s %-17s %6.2f %-4s | %s | %s | %s | %s | %s | n%s %s %s" % (
                fila["dt"], fila["sensor"], fila["mirova"], fila["fuente_ref"], fila["A"], fila["B_off"],
                fila["B_sum"], fila["C"], fila["D"], fila["n_px"], fila["estado"],
                {k: v for k, v in (r.get("marcas") or {}).items() if v}))
        res["casos_chillan_erupcion"] = casos
        resultado[nombre] = res

    (AQUI / "resultado.json").write_text(json.dumps(resultado, indent=1, ensure_ascii=False, default=str),
                                         encoding="utf-8")
    (AQUI / "salida.txt").write_text(_out.getvalue(), encoding="utf-8")
    say("\nlisto -> resultado.json, salida.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
