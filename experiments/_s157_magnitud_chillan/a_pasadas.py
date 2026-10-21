# -*- coding: utf-8 -*-
"""S157, tarea 1.33 (a): por qué la magnitud de Nevados de Chillán con el detector K queda bajo la de MIROVA,
pasada por pasada.

POR QUÉ. Chillán está en erupción desde fines de septiembre de 2026 y, con K, callamos donde MIROVA calla y
publicamos donde MIROVA alerta, pero con menos magnitud (razón ~0,5 y 0,12 en la peor pasada). Antes de
pre-registrar un A/B (D25, fondo por vecinos, o D17, área y remuestreo) hay que saber qué parte del déficit
es de qué. Sin L1B (no hay gránulo en disco y las credenciales locales son el par vencido que ya bloqueó la
cuenta, A71) el script trabaja sólo con lo que el record guarda de cada píxel alertado: su temperatura de
brillo, su VRP y su distancia, más el fondo del anillo y el ángulo de la pasada.

QUÉ MIDE (todo por pasada, sólo lectura):
  R       = D / M: lo que el tablero publica (predicado del tablero ejecutado con node, A97) sobre el VRP de
            MIROVA (consolidado remoto de Mirova-v1; el OCR sólo si la tabla no trae la pasada).
  F_rec   = D / S_in: recorte del tablero. S_in es la suma del VRP de nuestros píxeles alertados dentro del
            inner (5 km en Chillán). Medición pura con nuestros datos (tarea 1.14, §2).
  F_cero  = S_in / S_in_sin_recorte: lo que agrega el recorte a cero del exceso negativo (S26). Mayor o igual
            que 1: el recorte SUBE nuestra magnitud, no la baja.
  G       = S_in / M: lo que queda para selección + fondo + área. No se separa sin el Npix de MIROVA, pero se
            acota con dos techos que no necesitan el L1B:
    techo del fondo   G_fondo0 = S_fondo0 / M con S_fondo0 = suma de k·A·L(bt) de nuestros píxeles con FONDO
                      CERO. Si es menor que 1, ningún fondo, por frío que sea, cierra la brecha con nuestros
                      píxeles: falta selección o área. T_fondo* es la temperatura de fondo uniforme que la
                      cerraría (si existe), para compararla con el anillo.
    factor de área    f_area(cenital): cuánto más grande es el píxel real que el nominal, con el modelo
                      geométrico anclado al ATBD de S131 (brazo B de
                      experiments/_s131_audit/magnitud/02_correccion_area_por_angulo.py). Es el techo de D17:
                      si MIROVA remuestrea conservando energía, su suma equivale a usar el área real.
  saturación        I4 se descarta (NaN) desde 361,27 K, M13 desde 633,5 K y MODIS B22 cae a B21 desde
                    ~331 K (pipeline/process_viirs.py:373, process_viirs_mod.py:182, process_modis.py:327).
                    Un píxel saturado de I4 no aparece en el record: se busca con el testigo de M13 de la misma
                    pasada (energía de VIIRS 750 contra la de VIIRS 375).

Uso:  python -I experiments/_s157_magnitud_chillan/a_pasadas.py --dest <temporal> [--desde 2026-09-18] [--hasta ...]
Salida: a_pasadas_salida.json y a_pasadas_salida.txt junto al script.
"""
import argparse
import io
import json
import math
import os
import sys
from datetime import datetime, timezone
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

VOL = "NevadosDeChillan"
# Constantes del pipeline (leídas de los procesadores, no copiadas a mano: se comprueban abajo).
from pipeline import process_viirs as pv  # noqa: E402
from pipeline import process_viirs_mod as pm  # noqa: E402
try:
    from pipeline import process_modis as pmo  # noqa: E402
    MODIS_K, MODIS_A = pmo.WOOSTER_COEFF, pmo.NADIR_PIXEL_AREA_M2
    B21, B22 = pmo.BAND21_LAMBDA, pmo.BAND22_LAMBDA
except Exception:  # pyhdf roto en Windows: los números son los de process_modis.py:75-87
    MODIS_K, MODIS_A, B21, B22 = 18.9, 1e6, 3.929, 3.959

SENSOR = {
    "VIIRS375": {"lam": pv.I04_LAMBDA, "k": pv.WOOSTER_COEFF, "A": pv.NADIR_PIXEL_AREA_M2, "techo": 361.77},
    "VIIRS750": {"lam": pm.M13_LAMBDA, "k": pm.WOOSTER_COEFF, "A": pm.NADIR_PIXEL_AREA_M2, "techo": 634.0},
    # MODIS: el VRP vuelve a radiancia con la longitud de onda de B21 SIEMPRE (process_modis.py:1036 y :1040),
    # aunque con K la temperatura del píxel venga de B22 (D21, merge_mir_bands). Se reproduce lo que hace el
    # procesador; la diferencia con la longitud de onda de B22 se informa aparte (f_lambda_modis).
    "MODIS": {"lam": B21, "k": MODIS_K, "A": MODIS_A, "techo": None},
}
B22_SATURA_K = 331.0   # process_modis.py:327, "B22 satura a ~331 K"; sobre eso el píxel trae B21


def planck(t, lam):
    if t is None or t <= 0:
        return 0.0
    return C1_PLANCK / (lam ** 5 * (math.exp(C2_PLANCK / (lam * t)) - 1.0))


def lam_pixel(b, bt):
    return SENSOR[b]["lam"]


def f_lambda_modis(bts, t_bg):
    """Suma con la longitud de onda de B22 (la de la temperatura bajo K, si B22 no saturó) sobre la del procesador."""
    s = SENSOR["MODIS"]
    con_b21 = sum(max(planck(bt, B21) - planck(t_bg, B21), 0.0) for bt in bts)
    con_b22 = sum(max(planck(bt, B22 if bt < B22_SATURA_K else B21) - planck(t_bg, B22), 0.0) for bt in bts)
    return con_b22 / con_b21 if con_b21 > 0 else None


def vrp_pix(b, bt, t_bg, clip=True):
    s = SENSOR[b]
    lam = lam_pixel(b, bt)
    dl = planck(bt, lam) - planck(t_bg, lam)
    if clip:
        dl = max(dl, 0.0)
    return s["k"] * s["A"] * dl / 1e6


def t_fondo_que_cierra(b, bts, objetivo_mw):
    """Fondo uniforme T* con suma k·A·(L(bt) - L(T*)) = objetivo, sin recorte. None si ni con fondo 0 alcanza."""
    s = SENSOR[b]
    techo = sum(s["k"] * s["A"] * planck(bt, lam_pixel(b, bt)) / 1e6 for bt in bts)
    if techo < objetivo_mw or not bts:
        return None
    lo, hi = 1.0, max(bts)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        v = sum(vrp_pix(b, bt, mid, clip=False) for bt in bts)
        if v > objetivo_mw:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---- factor de área: modelo geométrico anclado al ATBD (S131, brazo B) ----
from importlib import import_module  # noqa: E402
_s131 = import_module("02_correccion_area_por_angulo")


def f_area(b, z):
    if z is None:
        return None
    if b in ("VIIRS375", "VIIRS750"):
        return _s131.f_modelo(z)
    # MODIS: mismo modelo de esfera sin agregación a bordo (h = 705 km). Es un MODELO, no el ATBD de MODIS.
    R, H = 6371.0, 705.0
    tz = min(abs(z), 65.0)
    ts = math.degrees(math.asin(R * math.sin(math.radians(tz)) / (R + H)))
    gam = math.radians(tz - ts)
    slant = math.sqrt(R ** 2 + (R + H) ** 2 - 2 * R * (R + H) * math.cos(gam))
    g_track = slant / H
    return g_track * (g_track / math.cos(math.radians(tz)))


def zona_agregacion(b, z):
    """Zona de agregación a bordo de VIIRS por ángulo de barrido (ATBD 423-ATBD-002 §2.2, vía S131): 3:1 hasta
    31,589°, 2:1 hasta 44,680°, 1:1 después. Es lo único que separa el área del píxel de cualquier otro efecto
    del ángulo sin L1B (verificador S157, H3): al pasar de 2:1 a 1:1 el área CAE aunque el ángulo siga subiendo."""
    if b not in ("VIIRS375", "VIIRS750") or z is None:
        return None
    s = _s131.scan_desde_cenital(abs(z))
    return "3:1" if s < _s131.SCAN_3TO2 else ("2:1" if s < _s131.SCAN_2TO1 else "1:1")


def zbin(z):
    return "<30" if z < 30 else ("30-50" if z < 50 else ">=50")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="temporal donde bajar la referencia de Mirova-v1")
    ap.add_argument("--desde", default="2026-09-18")   # DATOS_K_DESDE_UTC de frontend/cambio_detector.js
    ap.add_argument("--hasta", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    ventana = (a.desde, a.hasta)

    info = bajar_remoto(Path(a.dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    proc = {"commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
            "commit_ocr": info["registro_vrp_ocr.csv"]["sha"],
            "sha_index_html": bp.sha_git(bp.HTML),
            "sha_json": bp.sha_git(bp.DATA / f"{VOL}.json")}

    bp.VOLS = [VOL]
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    with open(bp.DATA / f"{VOL}.json", encoding="utf-8") as fh:
        crudos = {(r["sensor"], r["datetime_utc"]): r for r in json.load(fh)["records"]}

    filas_out, conteo = [], {"pos": 0, "pos_K": 0, "pos_K_pub": 0, "pos_K_no_pub": [], "sin_geometria_K_pub": 0}
    reproduccion = []
    for r in sorted(recs, key=lambda x: (x["dt"], x["b"])):
        # Verificador S157 H10: las alertas «sin geometría» (MIROVA vio calor en ESTA pasada pero el OCR no
        # sabe dónde) no sirven para detección, pero su VRP es de la pasada y sí sirve para magnitud. Van como
        # estrato APARTE (campo lab): no entran a los estratos ni al testigo, que son sólo de "pos".
        if r["lab"] not in ("pos", "sin_geometria"):
            continue
        es_pos = r["lab"] == "pos"
        if es_pos:
            conteo["pos"] += 1
        if not r.get("sha"):
            continue
        if es_pos:
            conteo["pos_K"] += 1
        crudo = crudos[(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))]
        ref = bp.parear(por_vb.get((VOL, r["b"]), []), r["dt"])
        alertas = [f for f in ref if (bp.es_alerta(f["tipo"]) if es_pos else bp.es_sin_geometria(f["tipo"]))]
        cons_al = [f for f in alertas if f["source"] == "CONS" and f["vrp_mw"]]
        usar = cons_al or [f for f in alertas if f["vrp_mw"]]
        if not r["pub"]:
            if es_pos:
                conteo["pos_K_no_pub"].append(f'{r["dt"]:%Y-%m-%d %H:%M} {r["b"]}')
            continue
        if not usar:
            continue
        conteo["pos_K_pub" if es_pos else "sin_geometria_K_pub"] += 1
        M = max(f["vrp_mw"] for f in usar)
        fuente = usar[0]["source"]
        b, z = r["b"], crudo.get("sensor_zenith_deg")
        t_bg = crudo.get("t_bg_k")
        pix = crudo.get("anomaly_pixels") or []
        dentro = [p for p in pix if p["dist_km"] is not None and p["dist_km"] <= inner[VOL]]
        # control: el VRP del píxel se reproduce con la fórmula del procesador (fondo del anillo, recorte a 0)
        for p in dentro:
            rec_v = vrp_pix(b, p["bt_k"], t_bg)
            reproduccion.append(abs(rec_v - p["vrp_mw"]) <= max(0.002, 0.005 * p["vrp_mw"]))
        bts = [p["bt_k"] for p in dentro]
        S_in = sum(p["vrp_mw"] for p in dentro)
        S_in_nc = sum(vrp_pix(b, bt, t_bg, clip=False) for bt in bts)
        S_f0 = sum(vrp_pix(b, bt, 0.0, clip=False) for bt in bts)
        n_cero = sum(1 for p in dentro if p["vrp_mw"] == 0)
        D = r["disp"]
        fa = f_area(b, z)
        tstar = t_fondo_que_cierra(b, bts, M)
        tstar_area = t_fondo_que_cierra(b, bts, M / fa) if fa else None
        techo = SENSOR[b]["techo"]
        filas_out.append({
            "pasada": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "b": b, "lab": r["lab"],
            "zona_agregacion": zona_agregacion(b, z),
            "cenital": z, "banda_cenital": zbin(z) if z is not None else None,
            "M": M, "fuente": fuente, "D": D, "R": D / M,
            "n_alertados": len(pix), "n_dentro": len(dentro), "n_recortados_a_cero": n_cero,
            "S_todos": sum(p["vrp_mw"] for p in pix), "S_in": S_in, "S_in_sin_recorte": S_in_nc,
            "F_rec": D / S_in if S_in else None,
            "F_cero": S_in / S_in_nc if S_in_nc > 0 else None,
            "G": S_in / M, "G_fondo0": S_f0 / M,
            # sensibilidad al fondo (D25 sin medir): vecinos 5 y 10 K más fríos que la mediana del anillo
            "G_fondo_m5": sum(vrp_pix(b, bt, t_bg - 5.0) for bt in bts) / M,
            "G_fondo_m10": sum(vrp_pix(b, bt, t_bg - 10.0) for bt in bts) / M,
            "f_area": fa, "G_area": (S_in / M) * fa if fa else None,
            "G_area_fondo0": (S_f0 / M) * fa if fa else None,
            "t_bg_anillo": t_bg, "t_max": max(bts) if bts else None,
            "T_fondo_cierra": tstar, "T_fondo_cierra_con_area": tstar_area,
            "dT_fondo_cierra": (t_bg - tstar) if tstar else None,
            "dT_fondo_cierra_con_area": (t_bg - tstar_area) if tstar_area else None,
            "sigma_bg": crudo.get("diag_sigma_bg_k"), "test1": crudo.get("triggered_test1"),
            "pc_n": (crudo.get("primary_cluster") or {}).get("n_pixels"),
            "pc_un_pixel": (crudo.get("primary_cluster") or {}).get("single_pixel_mode"),
            "f5": crudo.get("f5_core_vrp_mw"),
            "cerca_del_techo": bool(techo and bts and max(bts) >= techo - 5.0),
            "modis_b21": bool(b == "MODIS" and bts and max(bts) >= B22_SATURA_K),
            "f_lambda_modis": f_lambda_modis(bts, t_bg) if b == "MODIS" else None,
            "granulo": crudo.get("granule"), "version": crudo.get("product_version"),
            "codigo_sha": (crudo.get("regimen") or {}).get("codigo_sha"),
        })

    sin_geo = [f for f in filas_out if f["lab"] == "sin_geometria"]
    filas_out = [f for f in filas_out if f["lab"] == "pos"]

    # testigo de saturación de I4: misma pasada en VIIRS 750 (energía de M13 contra la de I4, cada una con el recorte a cero del procesador)
    por_pasada = {}
    for f in filas_out:
        por_pasada.setdefault(f["pasada"][:16] + f["sensor"].replace("_750", ""), {})[f["b"]] = f
    testigo = []
    for k, d in sorted(por_pasada.items()):
        if "VIIRS375" in d and "VIIRS750" in d:
            testigo.append({"pasada": k, "S375": d["VIIRS375"]["S_in"], "S750": d["VIIRS750"]["S_in"],
                            "S750_sobre_S375": d["VIIRS750"]["S_in"] / d["VIIRS375"]["S_in"],
                            "M375": d["VIIRS375"]["M"], "M750": d["VIIRS750"]["M"]})

    # estratos: sensor x banda de cenit, medianas (n chico: se informa n y no se afirma nada con n < 5)
    import statistics as st
    estratos = []
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        for zb in ("<30", "30-50", ">=50"):
            g = [f for f in filas_out if f["b"] == b and f["banda_cenital"] == zb]
            if not g:
                continue
            med = lambda k: st.median([f[k] for f in g if f[k] is not None]) if any(f[k] is not None for f in g) else None  # noqa: E731
            estratos.append({"b": b, "banda": zb, "n": len(g), "cenital": med("cenital"), "R": med("R"),
                             "F_rec": med("F_rec"), "G": med("G"), "G_fondo_m5": med("G_fondo_m5"),
                             "G_fondo_m10": med("G_fondo_m10"), "G_fondo0": med("G_fondo0"),
                             "f_area": med("f_area"), "G_area": med("G_area"),
                             # alza que daría cada palanca, mediana POR PASADA (no cociente de medianas)
                             "alza_fondo_m10": st.median([f["G_fondo_m10"] / f["G"] for f in g]),
                             "alza_fondo0": st.median([f["G_fondo0"] / f["G"] for f in g]),
                             "deficit_recorte": st.median([-math.log(f["F_rec"]) for f in g if f["F_rec"]]),
                             "deficit_G": st.median([-math.log(f["G"]) for f in g]),
                             "n_fondo0_no_cierra": sum(1 for f in g if f["G_fondo0"] < 1),
                             "n_area_cierra": sum(1 for f in g if f["G_area"] is not None and f["G_area"] >= 1)})
    # testigo de saturación: nuestra razón 750/375 contra la de MIROVA en la misma pasada
    if len(testigo) >= 3:
        xs = [math.log(t["S750_sobre_S375"]) for t in testigo]
        ys = [math.log(t["M750"] / t["M375"]) for t in testigo]
        mx, my = st.mean(xs), st.mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        rho = cov / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    else:
        rho = None

    # Verificador S157 H6: el catálogo (D17, nota S141) pide reportar la magnitud también con cenit <= 40°.
    def resumen(g):
        if not g:
            return None
        return {"n": len(g), "cenital": st.median([f["cenital"] for f in g]), "f_area": st.median([f["f_area"] for f in g]),
                "G": st.median([f["G"] for f in g]), "G_area": st.median([f["G_area"] for f in g]),
                "R": st.median([f["R"] for f in g])}
    corte40 = {b_: {"<=40": resumen([f for f in filas_out if f["b"] == b_ and f["cenital"] <= 40]),
                    ">40": resumen([f for f in filas_out if f["b"] == b_ and f["cenital"] > 40])}
               for b_ in ("VIIRS375", "VIIRS750", "MODIS")}
    # Verificador S157 H3: contraste por zona de agregación en las pasadas de 40 a 62° de cenital. Si el déficit
    # fuera área, la zona 2:1 (píxel más grande) tendría G MÁS BAJO que la 1:1 de cenital mayor.
    zonas = {}
    for etiqueta, base in (("pos", filas_out), ("pos+sin_geometria", filas_out + sin_geo)):
        for b_ in ("VIIRS375", "VIIRS750"):
            for zn in ("2:1", "1:1"):
                zonas[f"{etiqueta}|{b_}|{zn}"] = resumen([f for f in base if f["b"] == b_ and 40 <= f["cenital"] <= 62
                                                          and f["zona_agregacion"] == zn])

    out = {"meta": {"ventana": list(ventana), "volcan": VOL, "inner_km": inner[VOL], "procedencia": proc,
                    "conteo": conteo,
                    "control_reproduccion_pixel": {"n": len(reproduccion), "ok": sum(reproduccion)},
                    "testigo_corr_log_750_375_nuestro_vs_mirova": rho,
                    "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "estratos": estratos, "corte_40": corte40, "zonas_agregacion": zonas,
           "pasadas": filas_out, "sin_geometria": sin_geo, "testigo_saturacion_i4": testigo}
    (AQUI / "a_pasadas_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    L = []
    P = L.append
    P(f"Chillán, ventana {ventana[0]} a {ventana[1]}, inner {inner[VOL]} km. Referencia: {json.dumps(proc)}")
    P(f"pasadas con alerta de MIROVA (nocturnas, ±2 min): {conteo['pos']}; con K: {conteo['pos_K']}; "
      f"publicadas por el tablero: {conteo['pos_K_pub']}; no publicadas: {conteo['pos_K_no_pub']}")
    P(f"control: VRP por píxel reproducido con la fórmula del procesador en {sum(reproduccion)} de {len(reproduccion)}")
    P("")
    P("pasada            sensor    cen   M     D     R    | n  ncero S_in  F_rec F_cero G    | G_f0  f_area G_area | "
      "t_bg  t_max  T*    dT*  T*area dT*area")
    for f in filas_out:
        fmt = lambda v, s="%5.2f": (s % v) if v is not None else "  -  "  # noqa: E731
        P("%s  %-8s %5.1f %5.2f %5.2f %4.2f | %2d %2d %5.2f %5s %5s %4.2f | %5s %5s %5s | %5.1f %5.1f %5s %5s %5s %5s" % (
            f["pasada"], f["b"], f["cenital"], f["M"], f["D"], f["R"], f["n_dentro"], f["n_recortados_a_cero"],
            f["S_in"], fmt(f["F_rec"]), fmt(f["F_cero"]), f["G"], fmt(f["G_fondo0"]), fmt(f["f_area"]),
            fmt(f["G_area"]), f["t_bg_anillo"], f["t_max"] or float("nan"), fmt(f["T_fondo_cierra"], "%5.1f"),
            fmt(f["dT_fondo_cierra"], "%5.1f"), fmt(f["T_fondo_cierra_con_area"], "%5.1f"),
            fmt(f["dT_fondo_cierra_con_area"], "%5.1f")))
    P("")
    P("estratos (medianas): sensor banda n | cenital R F_rec G | G-5K G-10K G_f0 | f_area G_area | "
      "n(G_f0<1) n(G_area>=1) | alza fondo-10K, alza fondo0 | -ln F_rec, -ln G")
    for e in estratos:
        P("  %-8s %-6s %2d | %5.1f %4.2f %4.2f %4.2f | %4.2f %4.2f %4.2f | %4.2f %4.2f | %2d %2d | %4.2f %4.2f | %4.2f %4.2f" % (
            e["b"], e["banda"], e["n"], e["cenital"], e["R"], e["F_rec"], e["G"], e["G_fondo_m5"],
            e["G_fondo_m10"], e["G_fondo0"], e["f_area"], e["G_area"], e["n_fondo0_no_cierra"], e["n_area_cierra"],
            e["alza_fondo_m10"], e["alza_fondo0"], e["deficit_recorte"], e["deficit_G"]))
    P("")
    fr = lambda d: ("n %2d  cenital %4.1f  f_area %4.2f  R %4.2f  G %4.2f  G_area %4.2f" % (  # noqa: E731
        d["n"], d["cenital"], d["f_area"], d["R"], d["G"], d["G_area"])) if d else "sin pasadas"
    P("corte de D17 (nota S141): cenital <= 40 contra > 40 (medianas)")
    for b_, d in corte40.items():
        P(f"  {b_:8s} <=40: {fr(d['<=40'])}")
        P(f"  {b_:8s}  >40: {fr(d['>40'])}")
    P("")
    P("contraste por zona de agregación, cenital 40 a 62 (si fuera área: G de 2:1 < G de 1:1)")
    for k, d in zonas.items():
        P(f"  {k:32s} {fr(d)}")
    P("")
    P(f"estrato aparte, alertas sin geometría publicadas con K: {len(sin_geo)}")
    for f in sin_geo:
        P("  %s  %-8s %5.1f  zona %-4s M %5.2f  D %5.2f  R %4.2f  G %4.2f  f_area %4.2f  G_area %4.2f" % (
            f["pasada"], f["b"], f["cenital"], f["zona_agregacion"] or "-", f["M"], f["D"], f["R"], f["G"],
            f["f_area"], f["G_area"]))
    P("")
    P(f"testigo de saturación: correlación (log) entre nuestra razón 750/375 y la de MIROVA, misma pasada: "
      f"{rho if rho is None else round(rho, 3)} (n {len(testigo)})")
    P("testigo de saturación de I4 (S_in de VIIRS 750 sobre S_in de VIIRS 375 en la misma pasada):")
    for t in testigo:
        P("  %s  S375 %.2f  S750 %.2f  razón %.2f  (MIROVA 375 %.2f, 750 %.2f)" % (
            t["pasada"], t["S375"], t["S750"], t["S750_sobre_S375"], t["M375"], t["M750"]))
    txt = "\n".join(L)
    (AQUI / "a_pasadas_salida.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
