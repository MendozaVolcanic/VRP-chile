# -*- coding: utf-8 -*-
"""S135 — ¿de qué tamaño es D19 HOY? El mecanismo medido en el régimen de fondo vigente.

POR QUÉ. Los conteos con que se abrió D19 (Villarrica 245/289 `test1_roi`, mediana 2,80 km del
cráter, 172/245 más fríos que el fondo) son de records grabados ANTES del 2026-08-28 23:00 UTC,
cuando `process_viirs.py` todavía fijaba a mano `CLOUD_BT_THRESHOLD = 260 K` y el fondo global
5-25 km excluía los píxeles más fríos. Desde el PR #535 el umbral sale del perfil
(`cloud_mask_bt_k: 0.0`, D14) y en los nevados el fondo global bajó 6-8 K, con lo que el first
pass dispara varias veces más seguido. El probe del paso 0 mostró que 11 de 12 pasadas que
estaban persistidas como `test1_roi` hoy salen por el path contextual. O sea: **el tamaño de D19
en producción hoy es un número que nadie midió**, y el A/B de `keep_peak` se diseñaría sobre el
tamaño equivocado.

QUÉ MIDE (definiciones heredadas de `experiments/_s134_audit/f3/verif_h1.py` y `verif_h1c.py`,
el verificador con contexto limpio de S134 — no se reinventan acá):

  universo   = records de `data/mirova_equivalent/<vol>.json` con sensor VIIRS de 375 m
               (`VIIRS_*` sin sufijo `_750`). Se reportan DOS denominadores porque el
               etiquetado se movió con el mismo cambio de código que se está midiendo:
                 · TODOS los V375  → denominador ROBUSTO, el que se usa para el veredicto;
                 · sólo `summit`   → el que usó S134, informativo, NO comparable entre
                   regímenes (la fracción summit pasó de ~69 % a ~89 %).
               Todo `test1_roi` es summit (verificado), así que el numerador no cambia:
               cambia sólo con qué se lo divide, y ahí estaba el error de la primera versión.
  ventanas   = VIEJO  [2026-06-01, CORTE)   ·  NUEVO  [CORTE, último record]
               CORTE = 2026-08-28 23:00 UTC (merge del PR #535; #537 del 29-ago fue documentación).
  test1_roi  = `final_hotspot_source == "test1_roi"` (la rama donde `keep_peak` decide).
  1 píxel    = `primary_cluster.n_pixels == 1`.
  distancia  = haversine(`vent_lat/lon` de volcanoes.yaml, `primary_cluster.centroid`).
  corona     = distancia en [2,5 , 3,0] km (el borde del disco de 3 km del Test 1).
  frío       = `bt_k` del píxel del cúmulo (el `anomaly_pixel` más cercano al centroide) menor
               que `t_bg_k` del record. Es el par de campos correcto: `t_max_i04_k` es el máximo
               del ROI de 25 km y da lo contrario.
  MIROVA     = alerta V375 (CONS ∪ OCR, cargador canónico) en la misma fecha UTC, y **sólo
               sobre los records anteriores a la última fecha del CSV de referencia**: más allá
               MIROVA no fue observada, así que un 0 % ahí no significa «no corroboró» sino «no
               hay con qué comparar». El denominador de esa columna se reporta aparte.

  base falso = record summit V375 con cúmulo de 1 píxel, ese píxel más frío que el fondo
               global, y sin alerta de MIROVA esa noche (la definición del pre-registro). Se
               parte en la porción `test1_roi` —lo único que el A/B de `keep_peak` puede
               mover— y el resto (`ctx_cluster`), que ningún brazo toca.

Cada proporción va con su intervalo de Wilson al 95 %: con n de dos dígitos, una proporción sin
intervalo se lee como si fuera precisa y no lo es (A90). Y además va la serie MENSUAL, porque un
cociente antes/después no distingue un cambio de código de la variación estacional si el
«después» cae dentro de la dispersión de los meses previos.

Read-only. Salida: `d19_regimen_vigente.json` + tabla por pantalla.
"""
import io
import json
import math
import os
import statistics as st
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
import yaml  # noqa: E402

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CORTE = "2026-08-28 23:00"
DESDE = "2026-06-01"
TIER_A = ["Villarrica", "Lascar", "Copahue", "Llaima", "NevadosDeChillan", "Isluga",
          "Lastarria", "Chaiten", "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito"]


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p = math.radians
    dla, dlo = p(la2 - la1), p(lo2 - lo1)
    a = math.sin(dla / 2) ** 2 + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def wilson(k, n, z=1.96):
    """Intervalo de Wilson al 95 % para k/n. Con n chico es honesto donde el normal no lo es."""
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (centro - medio), 1), round(100 * (centro + medio), 1)]


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def bloque(recs_todos, cfg, fechas_mirova, fin_gt):
    """Los indicadores de D19. `recs_todos` = TODOS los V375 (no sólo summit)."""
    n_todos = len(recs_todos)
    recs = [r for r in recs_todos if r.get("distance_class") == "summit"]
    n = len(recs)
    src = Counter(r.get("final_hotspot_source") for r in recs)
    tr = [r for r in recs if r.get("final_hotspot_source") == "test1_roi"]
    out = {
        "n_summit": n,
        "fuentes": {str(k): v for k, v in src.most_common()},
        "n_test1_roi": len(tr),
        # --- denominador ROBUSTO (todos los V375): el del veredicto ---
        "n_todos_v375": n_todos,
        "pct_test1_roi_sobre_todos": (round(100 * len(tr) / n_todos, 1) if n_todos else None),
        "ic95_pct_test1_roi_sobre_todos": wilson(len(tr), n_todos),
        "pct_summit_sobre_todos": (round(100 * n / n_todos, 1) if n_todos else None),
        # --- denominador de S134 (sólo summit): informativo, NO comparable entre regímenes ---
        "pct_test1_roi_sobre_summit": (round(100 * len(tr) / n, 1) if n else None),
        "ic95_pct_test1_roi_sobre_summit": wilson(len(tr), n),
        "t_bg_mediana_k": (round(st.median([r["t_bg_k"] for r in recs if r.get("t_bg_k") is not None]), 1)
                           if any(r.get("t_bg_k") is not None for r in recs) else None),
        "pct_first_pass_vacio": (round(100 * sum(1 for r in recs if r.get("diag_n_first_pass_pixels") == 0) / n, 1)
                                 if n else None),
    }
    if not tr:
        out.update(n_1px=0, pct_1px=None, dist_mediana_km=None, pct_en_corona=None,
                   n_frio=0, pct_frio=None, ic95_pct_frio=None, vrp_mediana_mw=None,
                   n_con_ventana_gt=0, pct_con_alerta_mirova=None)
        return out
    npx = [(r.get("primary_cluster") or {}).get("n_pixels") for r in tr]
    n1 = sum(1 for x in npx if x == 1)
    ds, frios, n_frio_den, vrps, con_alerta, n_gt = [], 0, 0, [], 0, 0
    for r in tr:
        pc = r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            ds.append(hav(cfg["vent_lat"], cfg["vent_lon"], pc["centroid_lat"], pc["centroid_lon"]))
        tbg = r.get("t_bg_k")
        ap = r.get("anomaly_pixels") or []
        if ap and tbg is not None and pc.get("centroid_lat") is not None:
            best = min(ap, key=lambda p: hav(pc["centroid_lat"], pc["centroid_lon"], p["lat"], p["lon"]))
            if best.get("bt_k") is not None:
                n_frio_den += 1
                if best["bt_k"] < tbg:
                    frios += 1
        v = r.get("f5_core_vrp_mw")
        if v is None:
            v = pc.get("vrp_mw")
        if v:
            vrps.append(float(v))
        if fin_gt and r["datetime_utc"][:10] <= fin_gt:
            n_gt += 1
            if r["datetime_utc"][:10] in fechas_mirova:
                con_alerta += 1
    # --- población de «nivel base falso» tal como la define el pre-registro, sobre TODOS los
    # summit (no sólo test1_roi): 1 píxel + más frío que el fondo + sin alerta de MIROVA.
    base_total, base_t1 = 0, 0
    for r in recs:
        pc = r.get("primary_cluster") or {}
        if pc.get("n_pixels") != 1 or pc.get("centroid_lat") is None:
            continue
        tbg = r.get("t_bg_k")
        ap = r.get("anomaly_pixels") or []
        if not ap or tbg is None:
            continue
        best = min(ap, key=lambda q: hav(pc["centroid_lat"], pc["centroid_lon"], q["lat"], q["lon"]))
        if best.get("bt_k") is None or best["bt_k"] >= tbg:
            continue
        if r["datetime_utc"][:10] in fechas_mirova:
            continue
        base_total += 1
        if r.get("final_hotspot_source") == "test1_roi":
            base_t1 += 1
    ds.sort()
    out.update(
        base_falso_total=base_total, base_falso_test1_roi=base_t1,
        base_falso_pct_alcanzable=(round(100 * base_t1 / base_total, 1) if base_total else None),
        n_1px=n1, pct_1px=round(100 * n1 / len(tr), 1),
        dist_mediana_km=(round(st.median(ds), 2) if ds else None),
        pct_en_corona=(round(100 * sum(1 for d in ds if 2.5 <= d <= 3.0) / len(ds), 1) if ds else None),
        n_frio=frios, n_frio_denominador=n_frio_den,
        pct_frio=(round(100 * frios / n_frio_den, 1) if n_frio_den else None),
        ic95_pct_frio=wilson(frios, n_frio_den),
        vrp_mediana_mw=(round(st.median(vrps), 3) if vrps else None),
        n_con_ventana_gt=n_gt,
        pct_con_alerta_mirova=(round(100 * con_alerta / n_gt, 1) if n_gt else None),
        ic95_pct_con_alerta=wilson(con_alerta, n_gt),
    )
    return out


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    cfg_all = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    vmap = {v["name"]: v for v in cfg_all["volcanoes"]}
    alertas = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                                  ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
    fechas_mir = {}
    todas_fechas = []
    for a in alertas:
        if a.get("fecha_utc"):
            todas_fechas.append(a["fecha_utc"][:10])
        if a["sensor_bucket"] == "VIIRS375" and a.get("fecha_utc"):
            fechas_mir.setdefault(a["volcano"], set()).add(a["fecha_utc"][:10])
    fin_gt = max(todas_fechas) if todas_fechas else None

    res = {"corte_utc": CORTE, "desde": DESDE, "fin_ground_truth": None,
           "definiciones": __doc__.split("QUÉ MIDE")[1].split("Read-only")[0].strip(),
           "volcanes": {}}
    ult = ""
    print(f"D19 en los dos regímenes de fondo · corte {CORTE} UTC (PR #535)")
    print(f"Ground truth de MIROVA disponible hasta {fin_gt}: la columna MIROVA se calcula sólo\n"
          f"sobre los records hasta esa fecha (n propio), no sobre todos los test1_roi.\n")
    print(f"{'volcán':<21}{'rég':<7}{'n_v375':>6}{'test1_roi/todos':>18}{'1px':>6}{'d_med':>7}"
          f"{'corona':>8}{'frío':>17}{'VRP med':>9}{'MIROVA':>8}{'n_gt':>8}")
    for vol in TIER_A:
        recs_all = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"),
                                  encoding="utf-8"))["records"]
        recs = [r for r in recs_all if es_v375(r) and r.get("datetime_utc", "") >= DESDE]
        if recs:
            ult = max(ult, max(r["datetime_utc"] for r in recs))
        fm = fechas_mir.get(vol, set())
        viejo = [r for r in recs if r["datetime_utc"] < CORTE]
        nuevo = [r for r in recs if r["datetime_utc"] >= CORTE]
        res["volcanes"][vol] = {"viejo": bloque(viejo, vmap[vol], fm, fin_gt),
                                "nuevo": bloque(nuevo, vmap[vol], fm, fin_gt)}
        for tag in ("viejo", "nuevo"):
            b = res["volcanes"][vol][tag]
            ic = b["ic95_pct_test1_roi_sobre_todos"]
            ict = f"{b['pct_test1_roi_sobre_todos']}% [{ic[0]}-{ic[1]}]" if ic else "—"
            icf = (f"{b['pct_frio']}% [{b['ic95_pct_frio'][0]}-{b['ic95_pct_frio'][1]}]"
                   if b.get("ic95_pct_frio") else "—")
            print(f"{vol if tag == 'viejo' else '':<21}{tag:<7}{b['n_todos_v375']:>6}{ict:>18}"
                  f"{(str(b['pct_1px']) + '%') if b['pct_1px'] is not None else '—':>6}"
                  f"{b['dist_mediana_km'] if b['dist_mediana_km'] is not None else '—':>7}"
                  f"{(str(b['pct_en_corona']) + '%') if b['pct_en_corona'] is not None else '—':>8}"
                  f"{icf:>17}{b['vrp_mediana_mw'] if b['vrp_mediana_mw'] is not None else '—':>9}"
                  f"{(str(b['pct_con_alerta_mirova']) + '%') if b.get('pct_con_alerta_mirova') is not None else 's/gt':>8}"
                  f"{'(n=' + str(b.get('n_con_ventana_gt', 0)) + ')':>8}")

    # --- agregado sobre los 11 ---
    agg = {}
    for tag in ("viejo", "nuevo"):
        b = [res["volcanes"][v][tag] for v in TIER_A]
        n_sum = sum(x["n_summit"] for x in b)
        n_tod = sum(x["n_todos_v375"] for x in b)
        n_tr = sum(x["n_test1_roi"] for x in b)
        n_bt = sum(x.get("base_falso_total", 0) for x in b)
        n_b1 = sum(x.get("base_falso_test1_roi", 0) for x in b)
        n_fr = sum(x["n_frio"] for x in b)
        n_fr_den = sum(x.get("n_frio_denominador", 0) for x in b)
        agg[tag] = {
            "n_summit": n_sum, "n_todos_v375": n_tod, "n_test1_roi": n_tr,
            "pct_test1_roi_sobre_todos": (round(100 * n_tr / n_tod, 1) if n_tod else None),
            "ic95_pct_test1_roi_sobre_todos": wilson(n_tr, n_tod),
            "pct_summit_sobre_todos": (round(100 * n_sum / n_tod, 1) if n_tod else None),
            "pct_test1_roi_sobre_summit": (round(100 * n_tr / n_sum, 1) if n_sum else None),
            "base_falso_total": n_bt, "base_falso_test1_roi": n_b1,
            "base_falso_pct_alcanzable": (round(100 * n_b1 / n_bt, 1) if n_bt else None),
            "n_frio": n_fr, "n_frio_denominador": n_fr_den,
            "pct_frio": (round(100 * n_fr / n_fr_den, 1) if n_fr_den else None),
            "ic95_pct_frio": wilson(n_fr, n_fr_den),
        }
    # --- serie MENSUAL sobre el denominador robusto: ¿el valor nuevo se sale de la
    # dispersión de los meses previos, o cae dentro? Sin esto, un antes/después no
    # distingue el cambio de código de la variación estacional.
    from collections import defaultdict as _dd
    men = _dd(lambda: [0, 0])
    for vol in TIER_A:
        for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"),
                                encoding="utf-8"))["records"]:
            if not es_v375(r) or r.get("datetime_utc", "") < DESDE:
                continue
            dt = r["datetime_utc"]
            k = "post-#535" if dt >= CORTE else dt[:7]
            men[k][0] += 1
            if r.get("final_hotspot_source") == "test1_roi":
                men[k][1] += 1
    res["serie_mensual_test1_roi_sobre_todos_v375"] = {
        k: {"n_v375": v[0], "n_test1_roi": v[1],
            "pct": (round(100 * v[1] / v[0], 1) if v[0] else None), "ic95": wilson(v[1], v[0])}
        for k, v in sorted(men.items())}
    # --- noches cat-b por volcán en la ventana del A/B: el denominador del criterio 1 del
    # pre-registro. cat-b = noche con alerta MIROVA V375 que HOY publicamos como summit; se
    # separa la porción que llega por `test1_roi` (la que el A/B puede perder).
    VENT_AB = ("2026-06-01", "2026-08-31")
    catb = {}
    for vol in TIER_A:
        noches, noches_t1 = set(), set()
        for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"),
                                encoding="utf-8"))["records"]:
            if not es_v375(r) or r.get("distance_class") != "summit":
                continue
            d = r["datetime_utc"][:10]
            if not (VENT_AB[0] <= d <= VENT_AB[1]) or d not in fechas_mir.get(vol, set()):
                continue
            noches.add(d)
            if r.get("final_hotspot_source") == "test1_roi":
                noches_t1.add(d)
        catb[vol] = {"noches_catb": len(noches), "por_test1_roi": len(noches_t1),
                     "umbral_10pct_noches": round(0.10 * len(noches), 1)}
    res["noches_catb_ventana_ab"] = {"ventana": list(VENT_AB), "por_volcan": catb}
    print("")
    print(f"  noches cat-b por volcán en la ventana del A/B {VENT_AB[0]}..{VENT_AB[1]}:")
    for vol, c in sorted(catb.items(), key=lambda kv: -kv[1]["noches_catb"]):
        print(f"    {vol:<21}{c['noches_catb']:>4} noches ({c['por_test1_roi']:>3} vía test1_roi)"
              f"   10% = {c['umbral_10pct_noches']} noches")
    res["agregado_11_tier_a"] = agg
    res["ultimo_record"] = ult
    res["fin_ground_truth"] = fin_gt
    print(f"\nAGREGADO 11 Tier A (V375, desde {DESDE}, último record {ult}):")
    for tag in ("viejo", "nuevo"):
        a = agg[tag]
        ic, icf = a["ic95_pct_test1_roi_sobre_todos"], a["ic95_pct_frio"]
        print(f"  {tag:<6} n_V375={a['n_todos_v375']:>5}  summit={a['pct_summit_sobre_todos']}%  "
              f"test1_roi={a['n_test1_roi']:>4} = {a['pct_test1_roi_sobre_todos']}% [{ic[0]}-{ic[1]}] "
              f"(sobre summit daría {a['pct_test1_roi_sobre_summit']}%, NO comparable)")
        print(f"         más fríos que el fondo={a['n_frio']}/{a['n_frio_denominador']} = {a['pct_frio']}% "
              f"[{icf[0] if icf else '—'}-{icf[1] if icf else '—'}]   "
              f"nivel base falso={a['base_falso_total']} de los cuales test1_roi={a['base_falso_test1_roi']} "
              f"({a['base_falso_pct_alcanzable']}% alcanzable por el A/B)")
    print("\n  serie mensual test1_roi / TODOS los V375 (para no confundir código con estación):")
    for k, v in res["serie_mensual_test1_roi_sobre_todos_v375"].items():
        print(f"    {k:<10} {v['n_test1_roi']:>4}/{v['n_v375']:<5} = {v['pct']}% "
              f"[{v['ic95'][0]}-{v['ic95'][1]}]")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d19_regimen_vigente.json"),
              "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print("\n→ d19_regimen_vigente.json")


if __name__ == "__main__":
    main()
