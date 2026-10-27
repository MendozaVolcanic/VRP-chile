# -*- coding: utf-8 -*-
"""S158. Por qué la magnitud publicada de Tupungatito en VIIRS 375 queda en ~0,5x de MIROVA con el detector K,
pasada por pasada, sobre toda la serie K que dejó #883 (records desde 2025-02-15; referencia de la tabla de
MIROVA para Tupungatito desde 2026-02-14, A119).

POR QUÉ: c_noche_audit.py mostró que el 0,266 de #864 baja por dos alertas lejanas mal rotuladas, pero que sin
ellas el déficit sigue (0,45 en la ventana del auto-audit, 0,49 en 101 noches con la tabla). Antes de proponer
una palanca hay que saber qué parte es de qué. Sin L1B el script trabaja con lo que el record guarda de cada
píxel alertado (temperatura de brillo, VRP, distancia), el fondo del anillo y la geometría de la pasada, igual
que experiments/_s157_magnitud_chillan/a_pasadas.py, del que hereda las definiciones.

PAREO: misma pasada (±120 s, banco_paridad), sólo alertas de la TABLA latest.php (CONS) a 7 km o menos del
volcán según la tabla. El OCR queda fuera de la descomposición: en Suomi NPP puede traer la distancia de otra
pasada (b_series_mirova.py) y antes del 2026-06-11 su geometría estaba mal calibrada (A119). Las alertas
sólo-OCR se cuentan aparte.

QUÉ MIDE por pasada (R = D / M):
  D       lo que publica el tablero (predicado de frontend/index.html con node, A97): en VIIRS 375 el núcleo F5.
  F_rec   D / S_in: recorte del tablero. S_in = suma del VRP de nuestros píxeles alertados dentro del inner.
  G       S_in / M: lo que queda para selección + fondo + área.
    fondo     G_fondo0: S con fondo CERO. Si G_fondo0 < 1, ningún fondo cierra la brecha con nuestros píxeles.
              G_fondo_m5 / m10: vecinos 5 / 10 K más fríos que la mediana del anillo (sensibilidad, no D25).
    área      f_area(cenital): modelo geométrico del píxel anclado al ATBD (S131, brazo B). G_area = G·f_area.
    selección n_equiv = M / VRP del píxel más caliente nuestro: cuántos «píxeles nuestros más calientes» hacen
              falta para llegar a MIROVA. C0: S_in y D del detector anterior en el MISMO gránulo (JSON de
              data/mirova_equivalent/ en el commit padre de #883), para separar lo que cambió la selección de K.
  geometría cenital, zona de agregación a bordo (3:1, 2:1, 1:1) y lado del barrido: sin(azimut) > 0,3 este,
            < -0,3 oeste (convención verificada en experiments/_s157_azimut/README.md).

Uso:  python -I d_pasadas.py --dest <temporal> --c0 <Tupungatito.json del commit padre de #883> [--hasta ...]
Salida: d_pasadas_salida.json y d_pasadas_salida.txt junto al script.
"""
import argparse
import io
import json
import math
import os
import statistics as st
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s131_audit" / "magnitud"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

VOL, B = "Tupungatito", "VIIRS375"
LAM, KW, AREA = pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2
_s131 = import_module("02_correccion_area_por_angulo")


def planck(t, lam=LAM):
    if t is None or t <= 0:
        return 0.0
    return C1_PLANCK / (lam ** 5 * (math.exp(C2_PLANCK / (lam * t)) - 1.0))


def vrp_pix(bt, t_bg, clip=True):
    dl = planck(bt) - planck(t_bg)
    return KW * AREA * (max(dl, 0.0) if clip else dl) / 1e6


def zona(z):
    s = _s131.scan_desde_cenital(abs(z))
    return "3:1" if s < _s131.SCAN_3TO2 else ("2:1" if s < _s131.SCAN_2TO1 else "1:1")


def banda(z):
    return "<30" if z < 30 else ("30-50" if z < 50 else ">=50")


def lado(az):
    if az is None:
        return None
    s = math.sin(math.radians(az))
    return "este" if s > 0.3 else ("oeste" if s < -0.3 else None)


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def resumir(g):
    if not g:
        return None
    return {"n": len(g), "cenital": med([f["cenital"] for f in g]), "R": med([f["R"] for f in g]),
            "F_rec": med([f["F_rec"] for f in g]), "G": med([f["G"] for f in g]),
            "G_fondo_m10": med([f["G_fondo_m10"] for f in g]), "G_fondo0": med([f["G_fondo0"] for f in g]),
            "f_area": med([f["f_area"] for f in g]), "G_area": med([f["G_area"] for f in g]),
            "n_pix": med([f["n_dentro"] for f in g]), "n_equiv": med([f["n_equiv"] for f in g]),
            "dT": med([f["dT"] for f in g]), "M": med([f["M"] for f in g]), "D": med([f["D"] for f in g]),
            "n_G_fondo0_bajo_1": sum(1 for f in g if f["G_fondo0"] is not None and f["G_fondo0"] < 1),
            "R_C0": med([f["R_C0"] for f in g]), "n_con_C0": sum(1 for f in g if f["R_C0"] is not None)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--c0", required=True, help="Tupungatito.json del commit padre de #883 (detector C0)")
    ap.add_argument("--desde", default="2026-02-14")
    ap.add_argument("--hasta", default="2026-10-20")
    a = ap.parse_args()
    ventana = (a.desde, a.hasta)

    info = bajar_remoto(Path(a.dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    proc = {"commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
            "commit_ocr": info["registro_vrp_ocr.csv"]["sha"],
            "sha_index_html": bp.sha_git(bp.HTML), "sha_json": bp.sha_git(bp.DATA / f"{VOL}.json")}

    bp.VOLS = [VOL]
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()[VOL]
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
    recs = [r for r in bp.cargar_nuestros(coords, {VOL: inner}, ventana) if r["b"] == B]
    bp.etiquetar(recs, por_vb, ns, nv)

    with open(bp.DATA / f"{VOL}.json", encoding="utf-8") as fh:
        crudos = {(r["sensor"], r["datetime_utc"]): r for r in json.load(fh)["records"]}
    with open(a.c0, encoding="utf-8") as fh:
        c0 = {(r["sensor"], r["datetime_utc"]): r for r in json.load(fh)["records"]
              if not (r.get("regimen") or {}).get("codigo_sha")}

    # el predicado del tablero también para los records C0 del mismo gránulo
    casos_c0, claves_c0 = [], []
    for r in recs:
        k = (r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
        if k in c0:
            rc = c0[k]
            slim = {kk: rc.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
            if rc.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{kk: p.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (rc.get("anomaly_pixels") or [])]
            casos_c0.append([slim, inner]); claves_c0.append(k)
    pred_c0 = dict(zip(claves_c0, (p[3] for p in bp.correr_node(casos_c0)))) if casos_c0 else {}

    conteo = {"pos": 0, "pos_cons_cerca": 0, "pos_solo_ocr": 0, "pos_cons_lejos": 0, "pub": 0, "no_pub": []}
    filas_out, repro = [], []
    for r in sorted(recs, key=lambda x: x["dt"]):
        if r["lab"] != "pos" or not r.get("sha"):
            continue
        conteo["pos"] += 1
        ref = bp.parear(por_vb.get((VOL, B), []), r["dt"])
        al = [f for f in ref if bp.es_alerta(f["tipo"]) and f["vrp_mw"]]
        cons_al = [f for f in al if f["source"] == "CONS"]
        if not cons_al:
            conteo["pos_solo_ocr"] += 1
            continue
        cerca = [f for f in cons_al if f["dist_km"] is not None and f["dist_km"] <= inner]
        if not cerca:
            conteo["pos_cons_lejos"] += 1
            continue
        conteo["pos_cons_cerca"] += 1
        clave = r["dt"].strftime("%Y-%m-%d %H:%M")
        crudo = crudos[(r["sensor"], clave)]
        if not r["pub"]:
            _pc = crudo.get("primary_cluster") or {}
            _px = [p for p in (crudo.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= inner]
            conteo["no_pub"].append(f"{clave} {r['sensor']} M={max(f['vrp_mw'] for f in cerca)} "
                                    f"dc={crudo.get('distance_class')} pc_dist={_pc.get('centroid_dist_km')} "
                                    f"pc_vrp={_pc.get('vrp_mw')} t_max_dentro={max((p['bt_k'] for p in _px), default=None)} "
                                    f"t_bg={crudo.get('t_bg_k')}")
            continue
        conteo["pub"] += 1
        M = max(f["vrp_mw"] for f in cerca)
        z, az, t_bg = crudo.get("sensor_zenith_deg"), crudo.get("sensor_azimuth_deg"), crudo.get("t_bg_k")
        pix = crudo.get("anomaly_pixels") or []
        dentro = [p for p in pix if p.get("dist_km") is not None and p["dist_km"] <= inner]
        for p in dentro:
            repro.append(abs(vrp_pix(p["bt_k"], t_bg) - p["vrp_mw"]) <= max(0.002, 0.005 * p["vrp_mw"]))
        bts = [p["bt_k"] for p in dentro]
        S_in = sum(p["vrp_mw"] for p in dentro)
        S_f0 = sum(vrp_pix(bt, 0.0, clip=False) for bt in bts)
        D = r["disp"]
        fa = _s131.f_modelo(z) if z is not None else None
        vmax = max((p["vrp_mw"] for p in dentro), default=0.0)
        rc = c0.get((r["sensor"], clave))
        S_in_c0 = D_c0 = t_bg_c0 = None
        perdidos, ganados, pc0 = [], [], []
        if rc is not None:
            pc0 = [p for p in (rc.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= inner]
            S_in_c0 = sum(p["vrp_mw"] for p in pc0)
            D_c0 = pred_c0.get((r["sensor"], clave))
            t_bg_c0 = rc.get("t_bg_k")
            # mismo gránulo: un píxel es el mismo si su lat/lon coincide a 1e-4° (~10 m)
            llk = {(round(p["lat"], 4), round(p["lon"], 4)) for p in dentro}
            ll0 = {(round(p["lat"], 4), round(p["lon"], 4)) for p in pc0}
            perdidos = [p for p in pc0 if (round(p["lat"], 4), round(p["lon"], 4)) not in llk]
            ganados = [p for p in dentro if (round(p["lat"], 4), round(p["lon"], 4)) not in ll0]
        filas_out.append({
            "pasada": clave, "sensor": r["sensor"], "cenital": z, "banda": banda(z), "zona": zona(z),
            "azimut": az, "lado": lado(az), "M": M, "dist_M_tabla": max(f["dist_km"] for f in cerca),
            "D": D, "R": D / M, "n_alertados": len(pix), "n_dentro": len(dentro),
            "S_in": S_in, "F_rec": D / S_in if S_in else None, "G": S_in / M,
            "G_fondo0": S_f0 / M if bts else None,
            "G_fondo_m5": sum(vrp_pix(bt, t_bg - 5) for bt in bts) / M if bts else None,
            "G_fondo_m10": sum(vrp_pix(bt, t_bg - 10) for bt in bts) / M if bts else None,
            "f_area": fa, "G_area": (S_in / M) * fa if fa else None,
            "n_equiv": M / vmax if vmax > 0 else None,
            "t_bg": t_bg, "t_max": max(bts) if bts else None, "dT": (max(bts) - t_bg) if bts else None,
            "pc_dist": (crudo.get("primary_cluster") or {}).get("centroid_dist_km"),
            "pc_n": (crudo.get("primary_cluster") or {}).get("n_pixels"),
            "f5": crudo.get("f5_core_vrp_mw"), "sigma_bg": crudo.get("diag_sigma_bg_k"),
            "S_in_C0": S_in_c0, "D_C0": D_c0, "R_C0": (D_c0 / M) if D_c0 else None,
            "n_dentro_C0": len(pc0) if rc is not None else None,
            "D_sobre_D_C0": (D / D_c0) if D_c0 else None,
            "t_bg_C0": t_bg_c0, "G_C0": (S_in_c0 / M) if S_in_c0 is not None else None,
            "fuente_C0": rc.get("final_hotspot_source") if rc is not None else None,
            "n_perdidos_por_K": len(perdidos) if rc is not None else None,
            "n_ganados_por_K": len(ganados) if rc is not None else None,
            "VRP_perdido_por_K": sum(p["vrp_mw"] for p in perdidos) if rc is not None else None,
            "dT_perdidos": [round(p["bt_k"] - t_bg_c0, 2) for p in perdidos] if rc is not None and t_bg_c0 else None,
            "dT_mantenidos": [round(p["bt_k"] - t_bg, 2) for p in dentro],
        })

    estr = {}
    estr["todas"] = resumir(filas_out)
    for k in ("<30", "30-50", ">=50"):
        estr[f"cenital {k}"] = resumir([f for f in filas_out if f["banda"] == k])
    for k in ("este", "oeste"):
        estr[f"lado {k}"] = resumir([f for f in filas_out if f["lado"] == k])
        for zb in ("<30", "30-50", ">=50"):
            estr[f"lado {k} · cenital {zb}"] = resumir([f for f in filas_out if f["lado"] == k and f["banda"] == zb])
    for k in ("3:1", "2:1", "1:1"):
        estr[f"zona {k}"] = resumir([f for f in filas_out if f["zona"] == k])
    for k in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"):
        estr[f"plataforma {k}"] = resumir([f for f in filas_out if f["sensor"] == k])
    estr["antes 2026-06-13"] = resumir([f for f in filas_out if f["pasada"] < "2026-06-13"])
    estr["desde 2026-06-13"] = resumir([f for f in filas_out if f["pasada"] >= "2026-06-13"])
    for k in (1, 2):
        estr[f"{k} píxel dentro"] = resumir([f for f in filas_out if f["n_dentro"] == k])
    estr["3+ píxeles dentro"] = resumir([f for f in filas_out if f["n_dentro"] >= 3])

    # K contra C0 en el MISMO gránulo: cuánto de la magnitud cambió la selección de K
    con = [f for f in filas_out if f["D_C0"]]
    kc0 = {"n": len(con), "mediana_D_sobre_D_C0": med([f["D_sobre_D_C0"] for f in con]),
           "mediana_n_dentro_K": med([f["n_dentro"] for f in con]), "mediana_n_dentro_C0": med([f["n_dentro_C0"] for f in con]),
           "pasadas_con_perdidos": sum(1 for f in con if f["n_perdidos_por_K"]),
           "pasadas_con_ganados": sum(1 for f in con if f["n_ganados_por_K"]),
           "pasadas_D_igual": sum(1 for f in con if abs(f["D_sobre_D_C0"] - 1) < 0.01),
           "t_bg_igual": sum(1 for f in con if f["t_bg_C0"] is not None and abs(f["t_bg_C0"] - f["t_bg"]) < 0.01),
           "dT_perdidos_mediana": med([d for f in con for d in (f["dT_perdidos"] or [])]),
           "n_perdidos": sum(len(f["dT_perdidos"] or []) for f in con),
           "dT_mantenidos_mediana": med([d for f in con for d in f["dT_mantenidos"]]),
           "por_banda": {zb: med([f["D_sobre_D_C0"] for f in con if f["banda"] == zb]) for zb in ("<30", "30-50", ">=50")},
           "G_C0_mediana": med([f["G_C0"] for f in con]), "G_K_mediana_mismas": med([f["G"] for f in con]),
           "R_C0_mediana": med([f["R_C0"] for f in con]), "R_K_mediana_mismas": med([f["R"] for f in con]),
           # el Test 1 integrado de C0 restaba un fondo LOCAL (anillo de 1 a 3 km, e_fondo_local.py); K lo apagó (D30)
           "por_fuente_C0": {fu: {"n": sum(1 for f in con if f["fuente_C0"] == fu),
                                  "D_sobre_D_C0": med([f["D_sobre_D_C0"] for f in con if f["fuente_C0"] == fu]),
                                  "R_C0": med([f["R_C0"] for f in con if f["fuente_C0"] == fu]),
                                  "R_K": med([f["R"] for f in con if f["fuente_C0"] == fu])}
                             for fu in sorted({f["fuente_C0"] for f in con}, key=str)},
           "por_regimen_535": {nom: {"n": len(g), "D_sobre_D_C0": med([f["D_sobre_D_C0"] for f in g]),
                                     "t_bg_K_menos_C0": med([f["t_bg"] - f["t_bg_C0"] for f in g if f["t_bg_C0"]])}
                               for nom, g in (("antes de #535 (2026-08-28 23 UTC)", [f for f in con if f["pasada"] < "2026-08-28 23"]),
                                              ("desde #535", [f for f in con if f["pasada"] >= "2026-08-28 23"]))}}

    # efecto del lado dentro de cada banda de cenit (diferencia de medianas de log10), peso nE·nO/(nE+nO)
    def efecto(campo):
        num = den = 0.0
        for zb in ("<30", "30-50", ">=50"):
            e = [math.log10(f[campo]) for f in filas_out if f["banda"] == zb and f["lado"] == "este" and f[campo]]
            o = [math.log10(f[campo]) for f in filas_out if f["banda"] == zb and f["lado"] == "oeste" and f[campo]]
            if len(e) >= 3 and len(o) >= 3:
                w = len(e) * len(o) / (len(e) + len(o))
                num += w * (st.median(e) - st.median(o)); den += w
        return 10 ** (num / den) if den else None
    import random
    rnd = random.Random(158)

    def nulo(campo, n=2000):
        """Sortea el lado dentro de cada banda de cenit; IC95 del factor este/oeste bajo azar."""
        orig = [f["lado"] for f in filas_out]
        vals = []
        for _ in range(n):
            for zb in ("<30", "30-50", ">=50"):
                idx = [i for i, f in enumerate(filas_out) if f["banda"] == zb and orig[i] is not None]
                lados = [orig[i] for i in idx]
                rnd.shuffle(lados)
                for i, l_ in zip(idx, lados):
                    filas_out[i]["lado"] = l_
            vals.append(efecto(campo))
        for i, f in enumerate(filas_out):
            f["lado"] = orig[i]
        vals = sorted(v for v in vals if v is not None)
        obs = efecto(campo)
        p = (sum(1 for v in vals if abs(math.log10(v)) >= abs(math.log10(obs))) + 1) / (len(vals) + 1) if obs else None
        return {"factor_este_oeste": obs, "ic95_nulo": [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]],
                "p_dos_colas": p}
    lado_efecto = {c: nulo(c) for c in ("R", "M", "D", "G", "G_fondo0", "n_dentro", "dT")}

    out = {"meta": {"ventana": list(ventana), "volcan": VOL, "sensor": B, "inner_km": inner, "procedencia": proc,
                    "conteo": conteo, "control_reproduccion_pixel": {"n": len(repro), "ok": sum(repro)},
                    "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "estratos": estr, "efecto_lado": lado_efecto, "K_contra_C0": kc0, "pasadas": filas_out}
    (AQUI / "d_pasadas_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    L = []
    P = L.append
    P(f"{VOL} {B}, ventana {ventana[0]} a {ventana[1]}, inner {inner} km. Referencia: {json.dumps(proc)}")
    P(f"pasadas K con alerta (scraper): {conteo['pos']}; con alerta de la tabla a <= {inner} km: "
      f"{conteo['pos_cons_cerca']} (publicadas {conteo['pub']}); sólo OCR: {conteo['pos_solo_ocr']}; "
      f"tabla lejos: {conteo['pos_cons_lejos']}")
    P(f"no publicadas con alerta de tabla cerca: {conteo['no_pub']}")
    P(f"control: VRP por píxel reproducido con la fórmula del procesador en {sum(repro)} de {len(repro)}")
    P("")
    hdr = ("estrato                         n  cen   R    F_rec  G    G-10K G_f0  f_area G_area npix n_equiv "
           "dT    M     D     G_f0<1 R_C0 (n)")
    P(hdr)
    for k, e in estr.items():
        if not e:
            P(f"{k:30s}  sin pasadas"); continue
        f2 = lambda v, s="%5.2f": (s % v) if v is not None else "  -  "  # noqa: E731
        P("%-30s %3d %4.0f %s %s %s %s %s %s %s %4.1f %s %s %s %s %3d    %s (%d)" % (
            k, e["n"], e["cenital"], f2(e["R"]), f2(e["F_rec"]), f2(e["G"]), f2(e["G_fondo_m10"]),
            f2(e["G_fondo0"]), f2(e["f_area"]), f2(e["G_area"]), e["n_pix"], f2(e["n_equiv"], "%5.1f"),
            f2(e["dT"], "%5.1f"), f2(e["M"], "%5.3f"), f2(e["D"], "%5.3f"), e["n_G_fondo0_bajo_1"],
            f2(e["R_C0"]), e["n_con_C0"]))
    P("")
    P("K contra C0 en el mismo gránulo (pasadas publicadas por los dos):")
    for k_, v_ in kc0.items():
        P(f"  {k_}: {v_}")
    P("")
    P("efecto del lado (este/oeste) dentro de cada banda de cenit, con nulo por sorteo del lado (2000):")
    for c, v in lado_efecto.items():
        if v["factor_este_oeste"] is None:
            P(f"  {c:9s} sin poder"); continue
        P(f"  {c:9s} factor {v['factor_este_oeste']:.3f}  IC95 nulo [{v['ic95_nulo'][0]:.3f}, "
          f"{v['ic95_nulo'][1]:.3f}]  p {v['p_dos_colas']:.4f}")
    P("")
    P("pasada            sensor        cen  lado  zona M     D     R    | n S_in  F_rec G    G_f0 f_area G_area n_eq | "
      "t_bg  t_max dT   | R_C0 nC0")
    for f in filas_out:
        f2 = lambda v, s="%5.2f": (s % v) if v is not None else "  -  "  # noqa: E731
        P("%s  %-13s %4.1f %-5s %-4s %5.3f %5.3f %4.2f | %d %5.3f %s %4.2f %s %s %s %s | %5.1f %5.1f %4.1f | %s %s" % (
            f["pasada"], f["sensor"], f["cenital"], f["lado"] or "-", f["zona"], f["M"], f["D"], f["R"],
            f["n_dentro"], f["S_in"], f2(f["F_rec"]), f["G"], f2(f["G_fondo0"]), f2(f["f_area"]),
            f2(f["G_area"]), f2(f["n_equiv"], "%4.1f"), f["t_bg"], f["t_max"] or float("nan"),
            f["dT"] or float("nan"), f2(f["R_C0"]), f["n_dentro_C0"] if f["n_dentro_C0"] is not None else "-"))
    txt = "\n".join(L)
    (AQUI / "d_pasadas_salida.txt").write_text(txt + "\n", encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
