# -*- coding: utf-8 -*-
"""Tarea 1.14, parte C: cuanto mueve la magnitud cada palanca ya implementada, con brazos de A/B ya corridos.

POR QUE: la parte A dice cuanto pesa cada factor contra MIROVA, pero no si la palanca que tenemos a mano lo
mueve. Los A/B de S143 (fondo por vecinos D25, keep_peak, compuerta D22), S146 (Test 1 integrado), S147/S148
(conectiva max) y S149 (banda 22 de MODIS) ya produjeron, para las MISMAS pasadas, el record con y sin cada
palanca. Comparar la magnitud publicada de los dos brazos contra la MISMA alerta de MIROVA mide la palanca sin
correr el pipeline. El gemelo de S149 (mismo perfil que el control, otra corrida) es el nulo: tiene que dar 1.

Uso:  python c_palancas_ab.py --ab DIR_RAMAS --s143 DIR_ZIP [--dest DIR_REFERENCIA]
  DIR_RAMAS: carpeta donde se extrajo `git archive origin/s146-ab/<run> experiments/_s146_ab_sin_test1/salidas/<run>`
  DIR_ZIP:   carpeta donde se extrajo experiments/_s143_evaluador/artefactos_fusionados_s143.zip
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(AQUI))

import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402
import comun as C  # noqa: E402
from b_regimen_actual import fila_alerta, MINIMA_V375  # noqa: E402

SAL = "experiments/_s146_ab_sin_test1/salidas"


def comparaciones(ab, s143):
    def rama(run, brazo):
        return {"tipo": "rama", "dir": Path(ab) / SAL / run / brazo}

    def zipb(brazo):
        return {"tipo": "zip", "dir": Path(s143) / "s143_ab", "brazo": brazo}

    out = []
    # nulo: mismo perfil, otra corrida
    out.append(("nulo_gemelo", "2026-03 Lascar", rama("35632736532", "_s146_ab_sin_test1"), rama("35632736532", "_s149_ab_sin_test1_gemelo")))
    # Test 1 integrado (control con Test 1 contra sin Test 1), septiembre, 11 volcanes
    out.append(("quitar_test1", "2026-09-01/20", rama("35521542153", "_s146_ab_control"), rama("35521542153", "_s146_ab_sin_test1")))
    # conectiva max, sobre la base sin Test 1, cinco meses
    for run, mes in (("35599902448", "2026-05"), ("35675490175", "2026-06"), ("35728617326", "2026-07"),
                     ("35759688167", "2026-08"), ("35548121381", "2026-09-01/20")):
        out.append(("conectiva_max", mes, rama(run, "_s146_ab_sin_test1"), rama(run, "_s147_ab_sin_test1_max")))
    # banda 22 en MODIS (Lascar), marzo y junio (junio usa el gemelo como control)
    out.append(("modis_banda22", "2026-03 Lascar", rama("35632736532", "_s146_ab_sin_test1"), rama("35632736532", "_s149_ab_sin_test1_b22")))
    out.append(("modis_banda22_max", "2026-03 Lascar", rama("35632736532", "_s146_ab_sin_test1"), rama("35632736532", "_s149_ab_sin_test1_b22_max")))
    out.append(("modis_banda22", "2026-06 Lascar", rama("35679063864", "_s149_ab_sin_test1_gemelo"), rama("35679063864", "_s149_ab_sin_test1_b22")))
    out.append(("modis_banda22_max", "2026-06 Lascar", rama("35679063864", "_s149_ab_sin_test1_gemelo"), rama("35679063864", "_s149_ab_sin_test1_b22_max")))
    # S143, VIIRS 375, junio a agosto, 9 volcanes
    out.append(("fondo_vecinos_D25", "2026-06/08", zipb("_s142_ab_lit_sin_fondo"), zipb("_s142_ab_literal")))
    out.append(("literal_entero", "2026-06/08", zipb("_s142_ab_control"), zipb("_s142_ab_literal")))
    out.append(("quitar_keep_peak", "2026-06/08", zipb("_s142_ab_lit_keep_peak"), zipb("_s142_ab_literal")))
    out.append(("quitar_compuerta_D22", "2026-06/08", zipb("_s142_ab_lit_con_compuerta"), zipb("_s142_ab_literal")))
    return out


def archivos(spec):
    if spec["tipo"] == "rama":
        return {p.stem: p for p in spec["dir"].glob("*.json")}
    return {p.name.split("-")[-1]: p / f"{p.name.split('-')[-1]}.json"
            for p in spec["dir"].glob(f"s143ab-{spec['brazo']}-*") if p.is_dir()}


def cargar_brazo(spec, coords, inner_html, cache):
    clave = json.dumps({k: str(v) for k, v in spec.items()})
    if clave in cache:
        return cache[clave]
    recs, casos = {}, []
    for vol, path in archivos(spec).items():
        if vol not in C.INNER:
            continue
        for r in json.load(open(path, encoding="utf-8"))["records"]:
            b = C.bucket(r.get("sensor"))
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if b is None or BP.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            k = (vol, r["sensor"], r["datetime_utc"])
            recs[k] = {"vol": vol, "b": b, "dt": dt, "noche_id": f"{vol}|{dt:%Y-%m-%d}", "rec": r}
            slim = {kk: r.get(kk) for kk in BP.CAMPOS_JS if kk != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{kk: p.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append((k, [slim, inner_html[vol]]))
    pred = BP.correr_node([c for _, c in casos]) if casos else []
    for (k, _), p in zip(casos, pred):
        recs[k]["disp"], recs[k]["pub"] = p[3], p[4]
    cache[clave] = recs
    return recs


def medir(A, B, por_vb):
    """Pares de una misma pasada positiva en los dos brazos. Devuelve filas y conteos de publicacion."""
    filas, cuenta, solo_b = [], collections.Counter(), []
    for k, xa in A.items():
        xb = B.get(k)
        if xb is None:
            cuenta["sin_par_en_B"] += 1
            continue
        al = fila_alerta(BP.parear(por_vb.get((xa["vol"], xa["b"]), []), xa["dt"]))
        if al is None:
            continue
        if xa["b"] == "VIIRS375" and al["vrp_mw"] <= MINIMA_V375:
            cuenta[(xa["b"], "minima")] += 1
            continue
        pa, pb = bool(xa["pub"]) and (xa["disp"] or 0) > 0, bool(xb["pub"]) and (xb["disp"] or 0) > 0
        cuenta[(xa["b"], f"pub_A{int(pa)}_B{int(pb)}")] += 1
        if pb and not pa:
            # el brazo B publica donde A no: no hay razon B/A, pero si la magnitud de B contra MIROVA
            solo_b.append({"vol": xa["vol"], "b": xa["b"], "noche_id": xa["noche_id"], "R": xb["disp"] / al["vrp_mw"]})
        if not (pa and pb):
            continue
        f = {"vol": xa["vol"], "b": xa["b"], "noche_id": xa["noche_id"], "V_M": al["vrp_mw"],
             "R_A": xa["disp"] / al["vrp_mw"], "R_B": xb["disp"] / al["vrp_mw"],
             "banda_z": C.banda_z(xa["rec"].get("sensor_zenith_deg")),
             "ln_BA": math.log(xb["disp"] / xa["disp"])}
        for lado, x in (("A", xa), ("B", xb)):
            s_in, n_pos, _, _ = C.pixeles_inner(x["rec"], x["vol"])
            f[f"n_{lado}"] = n_pos
            f[f"ln_rec_{lado}"] = math.log(x["disp"] / s_in) if s_in > 0 else float("nan")
            f[f"ln_G_{lado}"] = math.log(s_in / al["vrp_mw"]) if s_in > 0 else float("nan")
        filas.append(f)
    return filas, cuenta, solo_b


BANDAS = ("0-20", "20-35", "35-50", "50-90")


def _rango_proc(recs):
    """[min, max, n con processed_utc, n] de la hora de proceso de los records de un brazo."""
    ps = sorted((x["rec"].get("processed_utc") or x["rec"].get("first_processed_utc")) for x in recs.values()
                if (x["rec"].get("processed_utc") or x["rec"].get("first_processed_utc")))
    return [ps[0] if ps else None, ps[-1] if ps else None, len(ps), len(recs)]


def por_angulo(filas, semilla=C.SEMILLA, n_boot=1000):
    """Arreglo (c) del verificador de #814: factor B/A por banda de angulo cenital, con IC por noche.

    Dos lecturas: (1) media geometrica de B/A en cada banda; (2) efecto de la banda contra 0-20 con efecto fijo
    por volcan (comun.efecto_cenital), que quita la mezcla de volcanes entre bandas."""
    if len(filas) < 20:
        return None

    def una(sub):
        gmb = {bz: (math.exp(np.mean([f["ln_BA"] for f in sub if f["banda_z"] == bz]))
                    if any(f["banda_z"] == bz for f in sub) else float("nan")) for bz in BANDAS}
        ef = C.efecto_cenital(sub, "ln_BA")
        efb = {bz: (math.exp(ef[bz][0]) if ef.get(bz) and ef[bz][0] is not None else float("nan")) for bz in BANDAS}
        return gmb, efb

    p_gm, p_ef = una(filas)
    por = collections.defaultdict(list)
    for f in filas:
        por[f["noche_id"]].append(f)
    noches = list(por)
    rng = random.Random(semilla)
    bs = [una([f for _ in noches for f in por[noches[rng.randrange(len(noches))]]]) for _ in range(n_boot)]
    out = {}
    for bz in BANDAS:
        g = [b[0][bz] for b in bs]
        e = [b[1][bz] for b in bs]
        out[bz] = {"n": sum(1 for f in filas if f["banda_z"] == bz),
                   "B_sobre_A_gm": [round(p_gm[bz], 4), round(float(np.nanpercentile(g, 2.5)), 4), round(float(np.nanpercentile(g, 97.5)), 4)],
                   "efecto_fijo_volcan_vs_0_20": [round(p_ef[bz], 4), round(float(np.nanpercentile(e, 2.5)), 4),
                                                  round(float(np.nanpercentile(e, 97.5)), 4)]}
    return out


def resumen(filas, semilla=C.SEMILLA, n_boot=C.N_BOOT):
    if len(filas) < 5:
        return None

    def una(sub):
        la = np.array([math.log(f["R_A"]) for f in sub])
        lb = np.array([math.log(f["R_B"]) for f in sub])
        cerr = (lb.mean() - la.mean()) / (-la.mean()) if la.mean() != 0 else float("nan")
        return la.mean(), lb.mean(), cerr

    pa, pb, pc = una(filas)
    por = collections.defaultdict(list)
    for f in filas:
        por[f["noche_id"]].append(f)
    noches = list(por)
    rng = random.Random(semilla)
    bs = [una([f for _ in noches for f in por[noches[rng.randrange(len(noches))]]]) for _ in range(n_boot)]
    q = lambda i, fn=math.exp: [round(float(fn(np.nanpercentile([b[i] for b in bs], 2.5))), 4),
                                round(float(fn(np.nanpercentile([b[i] for b in bs], 97.5))), 4)]
    ratio = [round(math.exp(pb - pa), 4)] + [round(math.exp(np.nanpercentile([b[1] - b[0] for b in bs], x)), 4) for x in (2.5, 97.5)]
    d_rec = np.nanmean([f["ln_rec_B"] - f["ln_rec_A"] for f in filas])
    d_g = np.nanmean([f["ln_G_B"] - f["ln_G_A"] for f in filas])
    return {"n_pasadas": len(filas), "n_noches": len(noches),
            "R_gm_A": [round(math.exp(pa), 4)] + q(0), "R_gm_B": [round(math.exp(pb), 4)] + q(1),
            "factor_B_sobre_A": ratio,
            "frac_deficit_cerrado": [round(float(pc), 4)] + q(2, fn=lambda v: v),
            "factor_por_recorte": round(math.exp(d_rec), 4), "factor_por_G": round(math.exp(d_g), 4),
            "n_pos_mediana_A_B": [float(np.median([f["n_A"] for f in filas])), float(np.median([f["n_B"] for f in filas]))],
            "frac_pasadas_identicas": round(float(np.mean([abs(f["R_B"] / f["R_A"] - 1) < 1e-9 for f in filas])), 4)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ab", required=True)
    ap.add_argument("--s143", required=True)
    ap.add_argument("--dest", default=str(AQUI / "_dl_referencia"))
    a = ap.parse_args(argv)
    info = bajar_remoto(Path(a.dest))
    filas_ref = cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                            Path(info["registro_vrp_ocr.csv"]["path"]))
    coords = BP._coords_por_volcan()
    inner_html = BP.inner_desde_html()
    por_vb, _, _, _ = BP.indexar_referencia(filas_ref, coords, ("2026-03-01", "2026-10-14"))
    out = {"referencia": {"commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                          "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}, "comparaciones": []}
    txt = [json.dumps(out["referencia"])]
    cache = {}
    agrup = collections.defaultdict(list)
    agrup_solo = collections.defaultdict(list)
    for nombre, ventana, sa, sb in comparaciones(a.ab, a.s143):
        A = cargar_brazo(sa, coords, inner_html, cache)
        B = cargar_brazo(sb, coords, inner_html, cache)
        filas, cuenta, solo_b = medir(A, B, por_vb)
        item = {"palanca": nombre, "ventana": ventana, "records_A": len(A), "records_B": len(B),
                "publicacion_en_positivos": {f"{k[0]}|{k[1]}" if isinstance(k, tuple) else k: v for k, v in sorted(cuenta.items(), key=str)},
                "por_sensor": {}, "por_volcan": {}, "solo_B_publica": {},
                # arreglo (b): regimen de CODIGO (cuando se proceso) separado de la ventana de calendario
                "processed_utc_A_B": [_rango_proc(A), _rango_proc(B)]}
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            sb_ = [f for f in solo_b if f["b"] == b]
            if len(sb_) >= 5:
                rep = C.reparto_con_ic(sb_, [])
                item["solo_B_publica"][b] = {"n": rep["n_pasadas"], "R_gm": rep["R_gm"], "R_mediana": round(rep["R_mediana"], 4)}
                txt_solo = f"  solo B publica {b}: {item['solo_B_publica'][b]}"
            else:
                txt_solo = None
            if txt_solo:
                agrup_solo[(nombre, b)] += sb_
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            sub = [f for f in filas if f["b"] == b]
            agrup[(nombre, b)] += sub
            item["por_sensor"][b] = resumen(sub)
            for v in C.VOLS:
                sv = [f for f in sub if f["vol"] == v]
                if len(sv) >= 10:
                    item["por_volcan"][f"{b}|{v}"] = resumen(sv)
        out["comparaciones"].append(item)
        txt.append(f"== {nombre} [{ventana}] records A/B {len(A)}/{len(B)} publicacion {item['publicacion_en_positivos']}")
        for b, v in item["solo_B_publica"].items():
            txt.append(f"  solo B publica {b}: {v}")
        for k, r in list(item["por_sensor"].items()) + list(item["por_volcan"].items()):
            if r:
                txt.append(f"  {k}: n {r['n_pasadas']}/{r['n_noches']} R_A {r['R_gm_A']} R_B {r['R_gm_B']} B/A {r['factor_B_sobre_A']} "
                           f"cierra {r['frac_deficit_cerrado']} (rec {r['factor_por_recorte']}, G {r['factor_por_G']}) n+ {r['n_pos_mediana_A_B']} identicas {r['frac_pasadas_identicas']}")
    out["agrupado"] = {}
    for (nombre, b), sub in agrup.items():
        r = resumen(sub)
        if r:
            if b == "VIIRS375" and nombre in ("fondo_vecinos_D25", "literal_entero", "conectiva_max", "quitar_keep_peak",
                                              "quitar_compuerta_D22"):
                r["por_angulo"] = por_angulo(sub)
                txt.append(f"POR ANGULO {nombre}|{b}: {json.dumps(r['por_angulo'])}")
            out["agrupado"][f"{nombre}|{b}"] = r
            txt.append(f"AGRUPADO {nombre}|{b}: n {r['n_pasadas']} B/A {r['factor_B_sobre_A']} cierra {r['frac_deficit_cerrado']} "
                       f"R_A {r['R_gm_A']} R_B {r['R_gm_B']} (rec {r['factor_por_recorte']}, G {r['factor_por_G']})")
    out["agrupado_solo_B"] = {}
    for (nombre, b), sub in agrup_solo.items():
        rep = C.reparto_con_ic(sub, [])
        out["agrupado_solo_B"][f"{nombre}|{b}"] = {"n": rep["n_pasadas"], "n_noches": rep["n_noches"], "R_gm": rep["R_gm"],
                                                   "R_mediana": round(rep["R_mediana"], 4)}
        txt.append(f"AGRUPADO solo B publica {nombre}|{b}: {out['agrupado_solo_B'][f'{nombre}|{b}']}")
    (AQUI / "c_palancas_ab_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=_js), encoding="utf-8")
    (AQUI / "c_palancas_ab_salida.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


def _js(o):
    return o.item() if hasattr(o, "item") else str(o)


if __name__ == "__main__":
    main()
