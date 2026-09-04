# -*- coding: utf-8 -*-
"""S133 — evidencia para decidir ENABLE_MODIS_B22_PRIMARY (READ-ONLY sobre pipeline/).

Mide, sobre los records MODIS ya persistidos en data/mirova_equivalent/:

  (1) SUSTRATO: con qué frecuencia B22 habría saturado, que es el UNICO caso donde el
      comportamiento actual del repo (B21 primaria) y la regla del paper (B22 primaria,
      B21 sólo si B22 saturó) coinciden. Fuera de ese caso las dos reglas difieren.

      LIMITACION DECLARADA: NO hay ningún campo per-banda persistido en el schema (no
      existen bt_21, bt_22, rad_21, rad_22, ni un flag de saturación). Lo que SI existe
      es `bt_k` por píxel de anomalía y `t_max_k` por record, y hoy ambos vienen de B21
      (porque merge_mir_bands con el flag OFF devuelve B21 salvo NaN). Se usa como PROXY
      el techo de saturación de B22 (~331 K, spec del sensor citada en
      tests/test_b22_primaria_modis_s132.py, NO medida de nuestros datos): un píxel con
      BT21 por encima de ese techo es un píxel donde B22 estaba saturada. El proxy es
      un LIMITE INFERIOR del fondo (los píxeles de fondo jamás llegan ahí) y una
      estimación razonable en el núcleo caliente. No es una medición directa.

  (2) LINEA BASE de diag_sigma_bg_k en MODIS: agregado, por volcán y serie mensual.
      Es la métrica que AUDIT_S131 propuso vigilar. Se espera que BAJE al pasar a la
      banda menos ruidosa (NEdT 0,017 K de B22 contra 0,183 K de B21).

Salida: experiments/_s133/b22_evidencia.json. Ningún número se transcribe a mano (S91).
"""
import json
import os
import statistics
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "data", "mirova_equivalent")
OUT = os.path.join(REPO, "experiments", "_s133", "b22_evidencia.json")

# Techo de saturación de B22 en BT (spec del sensor; ver docstring). Se barren varios
# valores porque el número exacto depende de la fuente y no queremos colgar la
# conclusión de un solo umbral.
TECHOS_B22_K = [325.0, 331.0, 335.0]

TIER_A = [
    "Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica",
    "Chaiten", "Copahue", "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle",
]


def cargar(vol):
    p = os.path.join(DATA, vol + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def q(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
    return round(s[i], 4)


def resumen(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "mediana": round(statistics.median(vals), 4),
        "media": round(statistics.fmean(vals), 4),
        "p10": q(vals, 0.10), "p90": q(vals, 0.90),
        "min": round(min(vals), 4), "max": round(max(vals), 4),
    }


def main():
    vols_encontrados, vols_faltantes = [], []
    por_volcan = {}
    agregado_sigma, fechas = [], []
    sigma_mensual = defaultdict(list)
    tot_rec = tot_rec_con_px = 0
    tot_px = 0
    px_sobre = {t: 0 for t in TECHOS_B22_K}
    rec_sobre_tmax = {t: 0 for t in TECHOS_B22_K}
    rec_sobre_px = {t: 0 for t in TECHOS_B22_K}
    tmax_all = []

    for vol in TIER_A:
        recs = cargar(vol)
        if recs is None:
            vols_faltantes.append(vol)
            continue
        vols_encontrados.append(vol)
        m = [r for r in recs if "MODIS" in str(r.get("sensor", ""))]
        sig_v, tmax_v = [], []
        px_v = 0
        px_sobre_v = {t: 0 for t in TECHOS_B22_K}
        rec_sobre_v = {t: 0 for t in TECHOS_B22_K}
        f_v = []
        for r in m:
            tot_rec += 1
            dt = r.get("datetime_utc")
            if dt:
                f_v.append(dt)
                fechas.append(dt)
            s = r.get("diag_sigma_bg_k")
            if isinstance(s, (int, float)):
                sig_v.append(float(s))
                agregado_sigma.append(float(s))
                if dt:
                    sigma_mensual[dt[:7]].append(float(s))
            tm = r.get("t_max_k")
            if isinstance(tm, (int, float)):
                tmax_v.append(float(tm))
                tmax_all.append(float(tm))
                for t in TECHOS_B22_K:
                    if tm > t:
                        rec_sobre_tmax[t] += 1
            px = r.get("anomaly_pixels") or []
            if px:
                tot_rec_con_px += 1
            bts = [p.get("bt_k") for p in px if isinstance(p.get("bt_k"), (int, float))]
            px_v += len(bts)
            tot_px += len(bts)
            for t in TECHOS_B22_K:
                c = sum(1 for b in bts if b > t)
                px_sobre[t] += c
                px_sobre_v[t] += c
                if c:
                    rec_sobre_px[t] += 1
                    rec_sobre_v[t] += 1

        por_volcan[vol] = {
            "n_records_modis": len(m),
            "ventana": {"desde": min(f_v) if f_v else None, "hasta": max(f_v) if f_v else None},
            "sigma_bg_k": resumen(sig_v),
            "t_max_k": resumen(tmax_v),
            "n_px_anomalia": px_v,
            "px_sobre_techo_b22": {str(t): px_sobre_v[t] for t in TECHOS_B22_K},
            "records_con_px_sobre_techo_b22": {str(t): rec_sobre_v[t] for t in TECHOS_B22_K},
            "pct_records_con_px_sobre_331K": (
                round(100.0 * rec_sobre_v[331.0] / len(m), 3) if m else None),
        }

    mensual = {k: {"n": len(v), "mediana_sigma_bg_k": round(statistics.median(v), 4)}
               for k, v in sorted(sigma_mensual.items())}

    out = {
        "_que_es": "Evidencia S133 para ENABLE_MODIS_B22_PRIMARY. READ-ONLY sobre data/.",
        "_flag_hoy": False,
        "_fuente": "data/mirova_equivalent/*.json (11 Tier A)",
        "_limitacion_sustrato": (
            "No existe campo per-banda ni flag de saturación en el schema. La saturación "
            "de B22 NO es medible directamente con lo persistido. Se reporta el PROXY "
            "bt_k > techo(B22), con bt_k proveniente de B21 (flag OFF)."),
        "volcanes_encontrados": vols_encontrados,
        "volcanes_faltantes": vols_faltantes,
        "ventana_global": {"desde": min(fechas) if fechas else None,
                           "hasta": max(fechas) if fechas else None},
        "denominadores": {
            "n_records_modis": tot_rec,
            "n_records_modis_con_anomaly_pixels": tot_rec_con_px,
            "n_pixeles_anomalia_con_bt": tot_px,
            "n_records_con_sigma_bg_k": len(agregado_sigma),
            "n_records_con_t_max_k": len(tmax_all),
        },
        "sustrato_saturacion_b22_PROXY": {
            "techos_K": TECHOS_B22_K,
            "px_anomalia_sobre_techo": {str(t): px_sobre[t] for t in TECHOS_B22_K},
            "pct_px_anomalia_sobre_techo": {
                str(t): (round(100.0 * px_sobre[t] / tot_px, 4) if tot_px else None)
                for t in TECHOS_B22_K},
            "records_con_al_menos_1_px_sobre_techo": {str(t): rec_sobre_px[t] for t in TECHOS_B22_K},
            "pct_records_con_al_menos_1_px_sobre_techo": {
                str(t): (round(100.0 * rec_sobre_px[t] / tot_rec, 4) if tot_rec else None)
                for t in TECHOS_B22_K},
            "records_con_t_max_sobre_techo": {str(t): rec_sobre_tmax[t] for t in TECHOS_B22_K},
            "t_max_k_global": resumen(tmax_all),
        },
        "linea_base_sigma_bg_k": {
            "agregado": resumen(agregado_sigma),
            "mensual": mensual,
        },
        "por_volcan": por_volcan,
        # ¿Cuánto margen tiene el mecanismo que S131 propuso vigilar? El σ del anillo de
        # fondo mide la heterogeneidad del TERRENO más el ruido del SENSOR, sumados en
        # cuadratura. Si el σ observado está muy por encima del NEdT, el término del
        # sensor es despreciable y cambiar de banda no puede bajarlo de forma medible.
        "margen_del_mecanismo": {
            "nedt_b21_k": 0.183,
            "nedt_b22_k": 0.017,
            "_fuente_nedt": "spec del sensor, citada en tests/test_b22_primaria_modis_s132.py",
            "sigma_bg_k_minimo_observado": (round(min(agregado_sigma), 4)
                                            if agregado_sigma else None),
            "sigma_bg_k_p10": q(agregado_sigma, 0.10),
            "razon_sigma_min_sobre_nedt_b21": (round(min(agregado_sigma) / 0.183, 2)
                                               if agregado_sigma else None),
            "sigma_esperado_si_solo_cambia_el_ruido_del_sensor": (
                # sqrt(sigma^2 - nedt21^2 + nedt22^2) sobre la mediana observada
                round((statistics.median(agregado_sigma) ** 2 - 0.183 ** 2 + 0.017 ** 2) ** 0.5, 4)
                if agregado_sigma else None),
            "delta_esperado_k": (
                round(statistics.median(agregado_sigma)
                      - (statistics.median(agregado_sigma) ** 2 - 0.183 ** 2 + 0.017 ** 2) ** 0.5, 6)
                if agregado_sigma else None),
        },
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("escrito:", OUT)
    print("records MODIS:", tot_rec, "| px anomalia:", tot_px)
    print("sigma_bg_k agregado:", out["linea_base_sigma_bg_k"]["agregado"])
    print("px sobre 331K:", px_sobre[331.0], "->",
          out["sustrato_saturacion_b22_PROXY"]["pct_px_anomalia_sobre_techo"]["331.0"], "%")
    print("records con >=1 px sobre 331K:", rec_sobre_px[331.0])
    print("t_max_k global:", out["sustrato_saturacion_b22_PROXY"]["t_max_k_global"])


if __name__ == "__main__":
    main()
