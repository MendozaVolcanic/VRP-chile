# COPIA S160 F4 de experiments/_s157_lambda_b22/medir_efecto_lambda.py; solo cambia ROOT
# -*- coding: utf-8 -*-
"""S157: cuánto cambia la magnitud MODIS con K si la vuelta a radiancia usa la longitud de onda de la banda
de la que vino cada temperatura, y qué hace eso con la razón contra MIROVA.

POR QUÉ. Con K (enable_modis_b22_primary, D21) la temperatura de brillo MIR de MODIS sale de B22
(Planck invertido con 3,959 µm) y B21 sólo entra donde B22 saturó. Pero la magnitud vuelve a radiancia con
la longitud de onda de B21 (3,929 µm) en `pipeline/process_modis.py` (L_bg_global, hotpix_rad, fondo del
kernel local, diagnóstico). Bajo C0 la ida y la vuelta usaban la misma λ y la radiancia que entraba a la
Ec. 7 de Coppola 2016a (p. 8) era la medida; bajo K ya no lo es. Este script mide cuánto, sin L1B.

CÓMO, sin L1B. El record guarda la magnitud del cúmulo (pc.vrp_mw), el número de píxeles, si la magnitud es
de un solo píxel, y el fondo con que se restó: `t_bg_k` (anillo) o, si actuó el kernel local,
`diag_L_bg_local_w_m2_sr_um` (mediana de la radiancia de fondo local, calculada con λ de B21). Con eso:
  dL_viejo = pc.vrp_mw · 1e6 / (k · A) / n_eff         (exceso de radiancia por píxel, con λ21)
  T_bk     = Planck⁻¹(L_bg, λ21)
  T_pix    = Planck⁻¹(Planck(T_bk, λ21) + dL_viejo, λ21)   (es exactamente bt_mir del píxel)
  dL_nuevo = Planck(T_pix, λ_pix) − Planck(T_bk, λ_fondo)
  F        = dL_nuevo / dL_viejo
con λ_pix = λ22 si T_pix < 331 K (B22 no saturó) y λ21 si no; λ_fondo = λ22 (el fondo nunca satura B22).
n_eff = 1 si la magnitud es de un solo píxel; si es suma de varios se usa el promedio (n_eff = n_pixels) y
se informa el F extremo con n_eff = 1 para acotar el error de esa aproximación.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  P1 (si estuviera roto, lo vería): CONTROL A reproduce `diag_L_bg_w_m2_sr_um` = Planck(t_bg_k, λ21) en cada
     record (si la λ o las constantes estuvieran mal, no coincide). CONTROL B reproduce, píxel por píxel, el
     vrp_mw de anomaly_pixels con 18,9 · A · (Planck(bt, λ21) − Planck(t_bg, λ21)) en los records SIN kernel
     local (si el procesador no hiciera lo que el código dice, no coincide). CONTROL C: con λ_pix = λ_fondo =
     λ21 el método devuelve F = 1 exacto (identidad).
  P2 (instrumento muerto): F se reporta con su distribución completa, no sólo la mediana; un F = 1 en todos
     los records delataría que el instrumento no ve la λ.

Uso:  python -I experiments/_s157_lambda_b22/medir_efecto_lambda.py --dest <temporal>
Salida: medir_efecto_lambda_salida.json y .txt junto al script.
"""
import argparse
import io
import json
import math
import os
import re
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = Path(os.environ["F4_ROOT"]) if os.environ.get("F4_ROOT") else AQUI.parents[1]  # COPIA S160 F4: raiz por variable de entorno
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, detector_de_record, leer_frontera_k  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402
from pipeline.constants import C1, C2  # noqa: E402

# Constantes leídas del procesador como texto (pyhdf no importa en Windows), no copiadas a mano.
_SRC = (ROOT / "pipeline" / "process_modis.py").read_text(encoding="utf-8")


def _const(nombre):
    return float(re.search(rf"^{nombre}\s*=\s*([0-9.e]+)", _SRC, re.M).group(1))


L21, L22 = _const("BAND21_LAMBDA"), _const("BAND22_LAMBDA")
K, A = _const("WOOSTER_COEFF"), _const("NADIR_PIXEL_AREA_M2")
B22_SATURA_K = 331.0  # docstring de merge_mir_bands (process_modis.py): "B22 satura a ~331 K"


def planck(t, lam):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t)) - 1.0))


def inv_planck(L, lam):
    return C2 / (lam * math.log(C1 / (L * lam ** 5) + 1.0))


def factor(vrp_mw, n_eff, L_bg21, lam_pix_fn=None, lam_fondo=None):
    """F = dL_nuevo / dL_viejo para un píxel representativo. Devuelve (F, T_pix, T_bk)."""
    dl_viejo = vrp_mw * 1e6 / (K * A) / n_eff
    t_bk = inv_planck(L_bg21, L21)
    t_pix = inv_planck(L_bg21 + dl_viejo, L21)
    lam_p = (L22 if t_pix < B22_SATURA_K else L21) if lam_pix_fn is None else lam_pix_fn(t_pix)
    lam_f = L22 if lam_fondo is None else lam_fondo
    dl_nuevo = max(planck(t_pix, lam_p) - planck(t_bk, lam_f), 0.0)
    return dl_nuevo / dl_viejo, t_pix, t_bk


def cuantiles(xs):
    if not xs:
        return None
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(p * (len(s) - 1) + 0.5))]  # noqa: E731
    return {"n": len(s), "min": round(s[0], 4), "q25": round(q(0.25), 4), "mediana": round(st.median(s), 4),
            "q75": round(q(0.75), 4), "max": round(s[-1], 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--hasta", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    frontera = leer_frontera_k()
    ventana = (frontera, a.hasta)
    out = {"constantes": {"lambda_b21_um": L21, "lambda_b22_um": L22, "k": K, "A_m2": A,
                          "b22_satura_k": B22_SATURA_K},
           "frontera_k": frontera, "ventana": ventana}

    # ---------------- todos los records MODIS con K y cúmulo con magnitud
    ctrl_a, ctrl_b, ctrl_c = [], [], []
    por_rec = {}
    for vol in bp.VOLS:
        with open(bp.DATA / f"{vol}.json", encoding="utf-8") as fh:
            recs = json.load(fh)["records"]
        for r in recs:
            if "MODIS" not in (r.get("sensor") or ""):
                continue
            if not (ventana[0] <= (r.get("datetime_utc") or "")[:10] <= ventana[1]):
                continue
            if detector_de_record(r, frontera) != "K":
                continue
            t_bg = r.get("t_bg_k")
            if t_bg is not None and r.get("diag_L_bg_w_m2_sr_um") is not None:
                ctrl_a.append(abs(planck(t_bg, L21) - r["diag_L_bg_w_m2_sr_um"]) / r["diag_L_bg_w_m2_sr_um"])
            if t_bg is not None and r.get("diag_L_bg_local_w_m2_sr_um") is None:
                for p in (r.get("anomaly_pixels") or []):
                    if p.get("vrp_mw", 0) >= 0.01:
                        esp = K * A * max(planck(p["bt_k"], L21) - planck(t_bg, L21), 0.0) / 1e6
                        ctrl_b.append(abs(esp - p["vrp_mw"]) / p["vrp_mw"])
            pc = r.get("primary_cluster") or {}
            v = pc.get("vrp_mw") or 0.0
            if v <= 0 or t_bg is None:
                continue
            if pc.get("d9_capped"):
                por_rec[(vol, r["sensor"], r["datetime_utc"])] = {"F": 1.0, "F_n1": 1.0, "capado": True,
                                                                  "vrp": v}
                continue
            L_bg = r.get("diag_L_bg_local_w_m2_sr_um") or planck(t_bg, L21)
            n_pix = int(pc.get("n_pixels") or 1)
            n_eff = 1 if (pc.get("single_pixel_mode") or n_pix == 1) else n_pix
            F, t_pix, t_bk = factor(v, n_eff, L_bg)
            F1, _, _ = factor(v, 1, L_bg)
            Fid, _, _ = factor(v, n_eff, L_bg, lam_pix_fn=lambda t: L21, lam_fondo=L21)
            ctrl_c.append(abs(Fid - 1.0))
            por_rec[(vol, r["sensor"], r["datetime_utc"])] = {
                "F": F, "F_n1": F1, "capado": False, "vrp": v, "t_pix": t_pix, "t_bk": t_bk,
                "b21": t_pix >= B22_SATURA_K, "kernel_local": r.get("diag_L_bg_local_w_m2_sr_um") is not None}

    out["controles"] = {
        "A_diag_L_bg_reproducido_err_rel_max": max(ctrl_a) if ctrl_a else None, "A_n": len(ctrl_a),
        "B_vrp_pixel_reproducido_err_rel_mediana": st.median(ctrl_b) if ctrl_b else None,
        "B_vrp_pixel_reproducido_err_rel_p95": sorted(ctrl_b)[int(0.95 * (len(ctrl_b) - 1))] if ctrl_b else None,
        "B_n_pixeles": len(ctrl_b),
        "C_identidad_err_max": max(ctrl_c) if ctrl_c else None, "C_n": len(ctrl_c)}

    vals = [x for x in por_rec.values() if not x["capado"]]
    out["todos_los_records_K"] = {
        "n_con_magnitud": len(por_rec), "n_capados_d9": sum(x["capado"] for x in por_rec.values()),
        "n_pixel_representativo_b21": sum(x["b21"] for x in vals),
        "n_kernel_local": sum(x["kernel_local"] for x in vals),
        "F": cuantiles([x["F"] for x in vals]),
        "F_si_n_eff_1": cuantiles([x["F_n1"] for x in vals]),
        "dif_max_F_por_n_eff": round(max((abs(x["F"] - x["F_n1"]) for x in vals), default=0.0), 5),
        "T_pix_k": cuantiles([x["t_pix"] for x in vals]),
        "T_bk_k": cuantiles([x["t_bk"] for x in vals]),
        "F_por_volcan": {v: cuantiles([x["F"] for k, x in por_rec.items() if k[0] == v and not x["capado"]])
                         for v in bp.VOLS}}

    # ---------------- contra MIROVA: pasadas MODIS con alerta, publicadas por el tablero
    info = bajar_remoto(Path(a.dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    out["procedencia"] = {"commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                          "commit_ocr": info["registro_vrp_ocr.csv"]["sha"],
                          "sha_index_html": bp.sha_git(bp.HTML)}
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
    recs = [r for r in bp.cargar_nuestros(coords, inner, ventana) if r["b"] == "MODIS"]
    bp.etiquetar(recs, por_vb, ns, nv)

    pares = []
    for r in recs:
        if r["lab"] != "pos" or not r.get("pub") or not r.get("sha"):
            continue
        filas_p = [f for f in bp.parear(por_vb.get((r["vol"], "MODIS"), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        cons_p = [f for f in filas_p if f["source"] == "CONS"]
        m = max(((f["vrp_mw"] or 0.0) for f in (cons_p or filas_p)), default=0.0)
        d = r.get("disp")
        key = (r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
        if not m or not d or key not in por_rec:
            continue
        F = por_rec[key]["F"]
        pares.append({"vol": r["vol"], "fecha": key[2], "sensor": r["sensor"], "mirova_mw": m, "nuestro_mw": d,
                      "F": round(F, 5), "razon_antes": d / m, "razon_despues": d * F / m,
                      "fuente_mirova": "CONS" if cons_p else "OCR"})
    import collections
    pv = collections.defaultdict(list)
    for p in pares:
        pv[p["vol"]].append(p)
    out["contra_mirova"] = {
        "n_pasadas": len(pares),
        "razon_antes": cuantiles([p["razon_antes"] for p in pares]),
        "razon_despues": cuantiles([p["razon_despues"] for p in pares]),
        "abs_log_razon_mediana_antes": round(st.median(abs(math.log(p["razon_antes"])) for p in pares), 4) if pares else None,
        "abs_log_razon_mediana_despues": round(st.median(abs(math.log(p["razon_despues"])) for p in pares), 4) if pares else None,
        "por_volcan": {v: {"n": len(ps), "razon_antes": round(st.median(p["razon_antes"] for p in ps), 4),
                           "razon_despues": round(st.median(p["razon_despues"] for p in ps), 4),
                           "F_mediano": round(st.median(p["F"] for p in ps), 4)} for v, ps in sorted(pv.items())},
        "pasadas": pares}

    js = AQUI / "medir_efecto_lambda_salida.json"
    js.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lineas = [f"frontera K {frontera}, ventana {ventana}, constantes {out['constantes']}",
              f"controles {json.dumps(out['controles'])}",
              f"todos los records K con magnitud: {json.dumps({k: v for k, v in out['todos_los_records_K'].items() if k != 'F_por_volcan'})}",
              "F por volcán: " + json.dumps(out["todos_los_records_K"]["F_por_volcan"]),
              f"contra MIROVA: n={len(pares)} antes {out['contra_mirova']['razon_antes']} "
              f"después {out['contra_mirova']['razon_despues']}",
              f"|log razón| mediana antes {out['contra_mirova']['abs_log_razon_mediana_antes']} "
              f"después {out['contra_mirova']['abs_log_razon_mediana_despues']}",
              "por volcán: " + json.dumps(out["contra_mirova"]["por_volcan"]),
              f"procedencia {out['procedencia']}"]
    (AQUI / "medir_efecto_lambda_salida.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
