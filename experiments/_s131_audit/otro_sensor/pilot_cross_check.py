# -*- coding: utf-8 -*-
"""S131 - piloto de cruce VRP Chile / MIROVA / NHI-v1 (evidencia exogena, otro sensor).

Windows: usar PYTHONIOENCODING=utf-8 o el wrapper de stdout.
Lee (read-only):
  - data/mirova_equivalent/<Vol>.json           (nuestras detecciones)
  - latest_consolidado.csv + mirova_v1_snapshot (ground truth MIROVA, via _s126_lib)
  - experiments/_s131_audit/otro_sensor/nhi_raw/<Vol>.json (NHI-v1, ya descargado del remote)

No escribe nada fuera de experiments/_s131_audit/otro_sensor/.
"""
import io
import sys
import json
import os
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import _s126_lib as lib  # noqa: E402

NHI_DIR = os.path.join(ROOT, "experiments", "_s131_audit", "otro_sensor", "nhi_raw")

# Mapeo nombre-carpeta-json-VRP -> nombre archivo NHI descargado (saneado con tr ' /' '__')
NHI_FILE = {
    "Villarrica": "Villarrica.json",
    "Lascar": "Lascar.json",
    "NevadosDeChillan": "Nevados_de_Chillan.json",
    "Copahue": "Copahue.json",
    "Llaima": "Llaima.json",
    "Chaiten": "Chaiten.json",
    "Isluga": "Isluga.json",
    "Tupungatito": "Tupungatito.json",
    "PlanchonPeteroa": "Planchon-Peteroa.json",
    "PuyehueCordonCaulle": "Puyehue_-_Cordon_Caulle.json",
}

VENTANA = ("2026-02-06", "2026-09-02")


def cargar_nhi(vol):
    """Lista de dicts NHI (todas las pasadas, cualquier fecha)."""
    fn = NHI_FILE.get(vol)
    if not fn:
        return []
    path = os.path.join(NHI_DIR, fn)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def cargar_vrp_chile(vol, ventana):
    """{fecha: {'vrp_max':x, 'detected':bool, 'n_pasadas':n}} usando pc.vrp_mw (A10),
    solo distance_class=='summit' (A61/A62 - lo que se pinta como anomalia real),
    y solo pasadas nocturnas (para comparar contra el mismo universo que MIROVA, A76).
    """
    path = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = defaultdict(lambda: {"vrp_max": 0.0, "detected": False, "n_pasadas": 0})
    for r in d.get("records", []):
        dt = r.get("datetime_utc") or ""
        fecha = dt[:10]
        if not (ventana[0] <= fecha <= ventana[1]):
            continue
        try:
            hh = int(dt[11:13])
        except (ValueError, IndexError):
            hh = 12
        if not (3 <= hh <= 9):
            continue  # night-only, A76
        out[fecha]["n_pasadas"] += 1
        pc = r.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        dc = r.get("distance_class")
        if dc == "summit" and vrp > 0:
            out[fecha]["detected"] = True
            out[fecha]["vrp_max"] = max(out[fecha]["vrp_max"], vrp)
    return dict(out)


def nhi_por_fecha(nhi_list):
    """{fecha: {'alerta':bool, 'px_max':n, 'sensores':set, 'n_pasadas':n}}"""
    out = defaultdict(lambda: {"alerta": False, "px_max": 0, "sensores": set(), "n_pasadas": 0})
    for r in nhi_list:
        f = r.get("fecha")
        if not f:
            continue
        out[f]["n_pasadas"] += 1
        if r.get("alerta"):
            out[f]["alerta"] = True
        out[f]["px_max"] = max(out[f]["px_max"], r.get("pixeles_calientes") or 0)
        out[f]["sensores"].add(r.get("sensor"))
    return dict(out)


def fecha_a_ordinal(fecha):
    import datetime
    return datetime.date.fromisoformat(fecha).toordinal()


def nhi_cercano(nhi_fechas, fecha, tol_dias=2):
    """Devuelve la pasada NHI mas cercana a `fecha` dentro de tol_dias, o None."""
    target = fecha_a_ordinal(fecha)
    mejor = None
    mejor_d = None
    for f, info in nhi_fechas.items():
        d = abs(fecha_a_ordinal(f) - target)
        if d <= tol_dias and (mejor_d is None or d < mejor_d):
            mejor, mejor_d = (f, info), d
    return mejor, (mejor_d if mejor else None)


def main():
    mirova_gt, diurnas = lib.cargar_mirova(VENTANA, solo_nocturnas=True)
    print(f"MIROVA cargado: {sum(len(v) for v in mirova_gt.values())} pares (fecha,bucket) "
          f"en ventana {VENTANA}, {diurnas} diurnas descartadas (A76).\n")

    volcanes_piloto = ["Lascar", "Villarrica", "NevadosDeChillan", "Copahue", "Llaima"]

    resumen_global = {}

    for vol in volcanes_piloto:
        nhi_raw = cargar_nhi(vol)
        nhi_fechas = nhi_por_fecha(nhi_raw)
        vrp_chile = cargar_vrp_chile(vol, VENTANA)
        gt = mirova_gt.get(vol, {})
        # fechas MIROVA (cualquier bucket) en la ventana
        fechas_mirova = sorted({k[0] for k in gt.keys()})

        print(f"=== {vol} ===")
        print(f"  NHI: {len(nhi_raw)} pasadas totales (archivo), {len(nhi_fechas)} fechas unicas; "
              f"rango archivo: {min(nhi_fechas) if nhi_fechas else '-'} a "
              f"{max(nhi_fechas) if nhi_fechas else '-'}")
        print(f"  VRP Chile: {len(vrp_chile)} noches con >=1 pasada nocturna en ventana; "
              f"{sum(1 for v in vrp_chile.values() if v['detected'])} noches con deteccion summit")
        print(f"  MIROVA: {len(fechas_mirova)} noches-fecha distintas con ALERTA en ventana "
              f"(cualquier bucket)")

        # --- Caso A: FN respecto de MIROVA (MIROVA detecto, nosotros NO esa noche) ---
        fn_dates = [f for f in fechas_mirova if not vrp_chile.get(f, {}).get("detected")]
        # --- Caso B: deteccion nuestra SIN respaldo MIROVA esa noche (posible FP) ---
        fp_dates = [f for f, v in vrp_chile.items() if v["detected"] and f not in fechas_mirova]

        print(f"  FN vs MIROVA (n={len(fn_dates)}): fechas donde MIROVA marco ALERTA y "
              f"nuestro summit=0 esa noche")
        print(f"  deteccion-sin-MIROVA (n={len(fp_dates)}): fechas donde marcamos summit "
              f"y MIROVA no tiene ALERTA esa noche")

        def clasificar(dates, tol=2):
            cnt = {"nhi_alerta": 0, "nhi_sin_alerta_con_pasada": 0, "sin_pasada_nhi": 0}
            detalle = []
            for f in dates:
                match, d = nhi_cercano(nhi_fechas, f, tol_dias=tol)
                if match is None:
                    cnt["sin_pasada_nhi"] += 1
                    detalle.append((f, None, None, None))
                    continue
                fnhi, info = match
                if info["alerta"]:
                    cnt["nhi_alerta"] += 1
                else:
                    cnt["nhi_sin_alerta_con_pasada"] += 1
                detalle.append((f, fnhi, d, info["alerta"]))
            return cnt, detalle

        cnt_fn, det_fn = clasificar(fn_dates)
        cnt_fp, det_fp = clasificar(fp_dates)

        print(f"  -> de los FN vs MIROVA (n={len(fn_dates)}), NHI (tol +-2d) dice: "
              f"alerta={cnt_fn['nhi_alerta']}, sin_alerta_con_pasada={cnt_fn['nhi_sin_alerta_con_pasada']}, "
              f"sin_pasada_cercana={cnt_fn['sin_pasada_nhi']}")
        print(f"  -> de deteccion-sin-MIROVA (n={len(fp_dates)}), NHI (tol +-2d) dice: "
              f"alerta={cnt_fp['nhi_alerta']}, sin_alerta_con_pasada={cnt_fp['nhi_sin_alerta_con_pasada']}, "
              f"sin_pasada_cercana={cnt_fp['sin_pasada_nhi']}")

        if det_fn:
            print("  detalle FN (fecha_mirova, fecha_nhi_mas_cercana, delta_dias, nhi_alerta):")
            for row in det_fn[:20]:
                print(f"    {row}")
        if det_fp:
            print("  detalle deteccion-sin-MIROVA (fecha_ours, fecha_nhi_mas_cercana, delta_dias, nhi_alerta):")
            for row in det_fp[:20]:
                print(f"    {row}")

        resumen_global[vol] = {
            "n_fn": len(fn_dates), "cnt_fn": cnt_fn,
            "n_fp": len(fp_dates), "cnt_fp": cnt_fp,
            "n_nhi_fechas": len(nhi_fechas),
        }
        print()

    out_path = os.path.join(ROOT, "experiments", "_s131_audit", "otro_sensor", "resumen_piloto.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resumen_global, f, indent=2, ensure_ascii=False)
    print(f"Resumen escrito en {out_path}")


if __name__ == "__main__":
    main()
