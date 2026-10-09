# -*- coding: utf-8 -*-
"""S150. Patrones de las alertas que F (max) pierde contra las que conserva, con el MISMO instrumento
(filas.json de perdidas_max.py: misma tabla, mismo predicado, misma poblacion de partida = alertas de
MIROVA que B publica). Se compara dentro del tramo debil (MIROVA < 0,10 MW) para no confundir "es mas
debil" con "el umbral subio mas".

  python patrones.py filas.json
"""
import collections, io, json, statistics as st, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = json.load(open(sys.argv[1], encoding="utf-8"))
# Las cinco filas OCR de Suomi NPP con la imagen de otra pasada (docs/S150_IMAGENES_SNPP.md).
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}


def sat(s):
    s = s or ""
    return "SNPP" if "SNPP" in s else "N20" if "NOAA20" in s else "N21" if "NOAA21" in s else s


def mref(r):
    return r["mirova"][0]["vrp_mw"] if r["mirova"] and r["mirova"][0]["vrp_mw"] is not None else None


def q(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "n=0"
    xs.sort(); n = len(xs)
    return "n=%d p25=%.4g med=%.4g p75=%.4g" % (n, xs[n // 4], st.median(xs), xs[(3 * n) // 4])


def auc(pos, neg):
    """P(valor de una perdida > valor de una conservada); 0,5 = no separa."""
    pos = [x for x in pos if x is not None]; neg = [x for x in neg if x is not None]
    if not pos or not neg:
        return None
    s = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return s / (len(pos) * len(neg))


def bloque(titulo, sel):
    L = [r for r in sel if r["perdida"]]; K = [r for r in sel if not r["perdida"]]
    print("\n==", titulo, "| perdidas", len(L), "| conservadas", len(K))
    var = {
        "umbral F dNTI cumbre (mu+5sd)": lambda r: r["B"].get("stat_dnti_s"),
        "umbral F dETI cumbre (mu+5sd)": lambda r: r["B"].get("stat_deti_s"),
        "sd_dNTI": lambda r: r["B"]["diag_sd_dnti"],
        "sd_dETI": lambda r: r["B"]["diag_sd_deti"],
        "sigma BT anillo (K)": lambda r: r["B"]["diag_sigma_bg_k"],
        "cenit (grados)": lambda r: r["B"]["sensor_zenith_deg"],
        "t_bg (K)": lambda r: r["B"]["t_bg_k"],
        "MIROVA VRP (MW)": mref,
        "B pc_vrp (MW)": lambda r: r["B"]["pc_vrp"],
        "B BT max pixel - t_bg (K)": lambda r: (r["B"]["ap_bt_max"] - r["B"]["t_bg_k"]) if r["B"].get("ap_bt_max") and r["B"].get("t_bg_k") else None,
        "B pixeles primer pase": lambda r: r["B"]["diag_n_first_pass_pixels"],
        "B pc n_pixels": lambda r: r["B"]["pc_n"],
        "n pixeles fondo (pool)": lambda r: r["B"]["diag_n_bg_used_first_pass"],
        "nti_max": lambda r: r["B"]["nti_max"],
    }
    for nombre, fn in var.items():
        a = auc([fn(r) for r in L], [fn(r) for r in K])
        print("  %-30s perdidas %-44s | conservadas %-44s | AUC %s" % (nombre, q([fn(r) for r in L]), q([fn(r) for r in K]), "-" if a is None else "%.2f" % a))
    for nombre, fn in (("satelite", lambda r: sat(r["B"]["sensor"])), ("volcan", lambda r: r["vol"]),
                       ("fuente MIROVA", lambda r: "OCR" if r["solo_ocr"] else "tabla"),
                       ("origen en B", lambda r: "solo 2.o pase" if not r["B"]["diag_n_first_pass_pixels"] else "1.er pase"),
                       ("borde (cenit>=50)", lambda r: r["B"]["sensor_zenith_deg"] is not None and r["B"]["sensor_zenith_deg"] >= 50),
                       ("fondo frio (t_bg<260)", lambda r: r["B"]["t_bg_k"] is not None and r["B"]["t_bg_k"] < 260)):
        c = collections.defaultdict(lambda: [0, 0])
        for r in sel:
            c[fn(r)][0 if r["perdida"] else 1] += 1
        print("  %-22s " % nombre + " | ".join("%s: pierde %d de %d (%.0f %%)" % (k, v[0], v[0] + v[1], 100 * v[0] / (v[0] + v[1])) for k, v in sorted(c.items(), key=lambda x: str(x[0]))))


for b in ("VIIRS375",):
    base = [r for r in F if r["b"] == b and r["clave"] not in MALAS]
    bloque(b + ", todas, sin las 5 filas OCR malas", base)
    bloque(b + ", MIROVA < 0,10 MW, sin las 5 malas", [r for r in base if mref(r) is not None and mref(r) < 0.10])
    bloque(b + ", MIROVA < 0,10 MW, solo tabla", [r for r in base if mref(r) is not None and mref(r) < 0.10 and not r["solo_ocr"]])
bloque("VIIRS750, todas", [r for r in F if r["b"] == "VIIRS750"])
