# -*- coding: utf-8 -*-
"""VERIFICADOR independiente F4 (S134). READ-ONLY.

Reimplementa f(theta) desde cero (sin importar la del auditor) y audita el pareo,
los criterios pre-registrados y la composicion de la cola.
"""
from __future__ import annotations
import io, json, math, os, sys, csv
from collections import defaultdict, Counter
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
sys.path.insert(0, os.path.join(REPO, "experiments"))

out = {}

# ---------- 1. f(theta) REIMPLEMENTADA desde cero ----------
RE = 6371.0


def slant(th_deg, H):
    t = math.radians(th_deg)
    rh = RE + H
    return rh * math.cos(t) - math.sqrt(RE ** 2 - (rh * math.sin(t)) ** 2)


def calib_H(target=25.60 / 11.87):
    lo, hi = 700.0, 1000.0
    for _ in range(300):
        m = (lo + hi) / 2
        if slant(56.063, m) / m > target:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


H = calib_H()


def theta_de_zen(zen, H):
    s = (RE / (RE + H)) * math.sin(math.radians(abs(zen)))
    return min(math.degrees(math.asin(min(1.0, s))), 56.063)


def k_filas(th):
    return 32 if th < 31.589 else (28 if th < 44.680 else 24)


def f_mia(zen, H=H):
    th = theta_de_zen(zen, H)
    r = slant(th, H) / H
    return min(1.0, 32.0 / (k_filas(th) * r)), th, r, k_filas(th)


out["1_f_reimplementada"] = {
    "H_calibrada_km": H,
    "r_en_EOS": slant(56.063, H) / H,
    "objetivo_ATBD_25_60_sobre_11_87": 25.60 / 11.87,
    "tabla": {str(z): dict(zip(("f", "theta", "r", "k"), f_mia(z)))
              for z in (0, 20, 30, 40, 50, 55, 70)},
}


def solape_filas(th):
    return 32 * (slant(th, H) / H) - 32


lo, hi = 0.0, 56.063
for _ in range(200):
    m = (lo + hi) / 2
    if solape_filas(m) < 1.0:
        lo = m
    else:
        hi = m
th_1fila = (lo + hi) / 2
zen_1fila = math.degrees(math.asin(min(1.0, ((RE + H) / RE) * math.sin(math.radians(th_1fila)))))
zen_de_19 = math.degrees(math.asin(min(1.0, ((RE + H) / RE) * math.sin(math.radians(19.0)))))
out["1_tension_S4_19grados"] = {
    "theta_donde_el_solape_supera_1_fila_deg": th_1fila,
    "zenital_equivalente_deg": zen_1fila,
    "ATBD_dice_solape_empieza_a_theta": 19.0,
    "f_en_theta_19": f_mia(zen_de_19)[0],
    "solape_en_filas_a_theta_19": solape_filas(19.0),
}


def f_lineal(zen):
    th = theta_de_zen(zen, H)
    r = 1.0 + (0.80 / 0.371 - 1.0) * (th / 56.063)
    return min(1.0, 32.0 / (k_filas(th) * r))


out["1_modelo_alternativo_r_lineal_en_theta"] = {str(z): f_lineal(z)
                                                 for z in (0, 20, 30, 40, 50, 55, 70)}

# ---------- 2. pareo ----------
from f4_solape_ley_intermedia import cargar_gt, pares_de, _mediana, BINS, VOLCANES  # noqa: E402

gt, n_gt = cargar_gt()
pares, diag = pares_de("_s133_area_geoloc", gt)
pc, _ = pares_de("_s133_area_control", gt)
out["2_diagnostico_geoloc"] = diag
out["2_n_pares"] = len(pares)
out["2_max_dif_f_auditor_vs_mia"] = max(
    abs(p["f_solape"] - f_mia(p["zenital_deg"])[0]) for p in pares)

uso = Counter((p["volcano"], round(p["vrp_mirova_mw"], 6), p["datetime_utc"][:10])
              for p in pares)
out["2_alertas_gt_reusadas"] = {
    "n_pares": len(pares),
    "n_pares_en_claves_repetidas": sum(v for v in uso.values() if v > 1),
    "max_reuso": max(uso.values()),
}

TOL = timedelta(minutes=20)


def _dt(s):
    s = (s or "").replace("T", " ").strip()[:19]
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    return None


usadas, estrictos = set(), []
for vol in VOLCANES:
    ps = sorted([p for p in pares if p["volcano"] == vol], key=lambda p: p["datetime_utc"])
    cand = sorted(gt.get((vol, "v375"), ()))
    for p in ps:
        d = _dt(p["datetime_utc"])
        best = None
        for i, (gd, gv) in enumerate(cand):
            if (vol, i) in usadas:
                continue
            if abs(gd - d) <= TOL and (best is None or abs(gd - d) < best[0]):
                best = (abs(gd - d), i, gv)
        if best:
            usadas.add((vol, best[1]))
            q = dict(p)
            q["vrp_mirova_mw"] = best[2]
            q["razon_x_f"] = p["vrp_ours_mw"] * p["f_solape"] / best[2]
            estrictos.append(q)


def resumen(ps, campo="razon_x_f"):
    r = {}
    for b in BINS:
        xs = [p[campo] for p in ps if p["bin"] == b]
        r[b] = {"n": len(xs), "med": _mediana(xs)}
    xs = [p[campo] for p in ps]
    r["cola_frac"] = sum(1 for x in xs if x > 2) / float(len(xs)) if xs else None
    r["n_total"] = len(xs)
    return r


out["2_pareo_1a1_estricto"] = resumen(estrictos)
out["2_pareo_del_auditor"] = resumen(pares)


# ---------- 3. C2, el criterio que el informe no evalua ----------
def c2(ps, campo):
    d = {}
    for v in VOLCANES:
        xs = [p[campo] for p in ps if p["volcano"] == v]
        m = _mediana(xs)
        d[v] = {"n": len(xs), "med": m, "evaluable": len(xs) >= 15,
                "en_banda": (0.90 <= m <= 1.10) if m else None}
    d["_n_en_banda"] = sum(1 for v in VOLCANES if d[v]["en_banda"])
    d["_n_en_banda_y_evaluable"] = sum(1 for v in VOLCANES
                                       if d[v]["en_banda"] and d[v]["evaluable"])
    return d


out["3_C2_ley_intermedia"] = c2(pares, "razon_x_f")
out["3_C2_geoloc_sin_f"] = c2(pares, "razon")
out["3_C2_control"] = c2(pc, "razon")

# ---------- 4. la cola ----------
vals = sorted(p["vrp_mirova_mw"] for p in pares)
out["4_gt_pequenos"] = {
    "min": vals[0], "mediana": _mediana(vals),
    "n_menores_0_5": sum(1 for v in vals if v < 0.5),
    "valores_distintos_bajo_0_5": len(set(round(v, 6) for v in vals if v < 0.5)),
    "los_10_mas_chicos": vals[:10],
    "los_5_valores_mas_frecuentes": Counter(round(v, 3) for v in vals).most_common(5),
    "n_con_2_decimales_o_menos": sum(1 for v in vals
                                     if abs(v * 100 - round(v * 100)) < 1e-9),
}
tail = [p for p in pares if p["razon_x_f"] > 2]
nott = [p for p in pares if p["razon_x_f"] <= 2]


def frac_fb(ps):
    return sum(1 for p in ps if "fallback" in p["fuente_magnitud"]) / float(len(ps)) if ps else None


out["4_fallback_A46"] = {"en_cola": frac_fb(tail), "fuera_cola": frac_fb(nott),
                         "n_cola": len(tail), "n_fuera": len(nott)}


def cola_por_tramo(ps, campo):
    d = defaultdict(lambda: [0, 0])
    for p in ps:
        t = ("<0.5" if p["vrp_mirova_mw"] < 0.5
             else ("0.5-2" if p["vrp_mirova_mw"] < 2 else ">=2"))
        d[t][0] += 1
        if p[campo] > 2:
            d[t][1] += 1
    return {k: {"n": v[0], "cola": v[1], "frac": v[1] / float(v[0])}
            for k, v in sorted(d.items())}


out["4_cola_por_tramo_ley_intermedia"] = cola_por_tramo(pares, "razon_x_f")
out["4_cola_por_tramo_control"] = cola_por_tramo(pc, "razon")
out["4_cola_por_tramo_geoloc_sin_f"] = cola_por_tramo(pares, "razon")
out["4_cola_por_bin_ley_intermedia"] = {
    b: {"n": sum(1 for p in pares if p["bin"] == b),
        "cola": sum(1 for p in pares if p["bin"] == b and p["razon_x_f"] > 2)}
    for b in BINS}

# ---------- 5. ground truth ----------
snap = os.path.join(REPO, "data", "mirova_reference", "mirova_v1_snapshot",
                    "registro_vrp_consolidado.csv")
live = os.path.join(REPO, "latest_consolidado.csv")


def filas(p):
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in csv.DictReader(fh))


out["5_ground_truth"] = {
    "live_latest_consolidado_filas": filas(live),
    "snapshot_consolidado_filas": filas(snap),
    "el_script_usa": "latest_consolidado.csv (VIVO) + snapshot OCR",
    "n_filas_alerta_nocturnas_cargadas": n_gt,
}

# ---------- 6. H4 ----------
p_lascar = os.path.expanduser("~/ab_area/s133area-_s133_area_geoloc-Lascar/Lascar.json")
d0 = json.load(io.open(p_lascar, encoding="utf-8"))
recs = d0["records"] if isinstance(d0, dict) else d0
ks = sorted(set(k for r in recs for k in r.keys()))
out["6_H4_claves"] = {
    "claves_con_area_o_pix": [k for k in ks if "area" in k.lower() or "pix" in k.lower()],
    "n_claves_distintas": len(ks),
    "tiene_f5_core_vrp_mw": "f5_core_vrp_mw" in ks,
    "n_records": len(recs),
}

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with io.open(os.path.join(HERE, "verif_resultados.json"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps(out, indent=1, ensure_ascii=False, default=str))
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
