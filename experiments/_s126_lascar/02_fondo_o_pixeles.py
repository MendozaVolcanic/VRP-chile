# -*- coding: utf-8 -*-
"""S126 — para llegar a MIROVA en Lascar, ?falta fondo mas frio o faltan pixeles?

El script 01 REFUTO la hipotesis del halo geotermal: en Lascar el anillo [1,5-3] km
no esta mas caliente que el fondo global sino mas FRIO (-2,47 K), igual que en los
nevados aunque menos (ellos -7 a -8,5 K). Asi que el sub-reporte de 0,434 no viene
de un fondo inflado.

Quedan dos explicaciones, y son separables con aritmetica sobre lo que ya esta
persistido. La magnitud de un cluster de 1 pixel es

    vrp = A_pix * WOOSTER * (L(bt_pixel) - L_bg) / 1e6

Para reproducir el valor de MIROVA de esa misma noche hace falta:

  (a) FONDO: bajar L_bg hasta que la cuenta de. Se despeja la temperatura de fondo
      necesaria. Si esa temperatura cae por debajo de lo que fisicamente puede
      haber en la escena, el fondo NO puede ser la explicacion.
  (b) PIXELES: sumar mas pixeles al mismo fondo. Se despeja cuantos pixeles
      equivalentes al que tenemos harian falta.

Las dos hipotesis se testean sobre las MISMAS noches y se reportan juntas, asi que
el resultado no depende de cual mire primero.

REFERENCIA FISICA para juzgar (a): el fondo no puede ser mas frio que el pixel mas
frio del ROI esa noche. Como cota practica se usa el minimo bt de los
`anomaly_pixels` del brazo E, que barre el disco de 3 km — es una cota conservadora
(E guarda solo la mitad caliente), asi que si la temperatura NECESARIA queda por
debajo incluso de esa cota, la conclusion es solida.

Persiste en 02_fondo_o_pixeles.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.process_viirs import bt_to_spectral_radiance, I04_LAMBDA, WOOSTER_COEFF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
K = 140625.0 * WOOSTER_COEFF / 1e6
C1, C2 = 1.19104e8, 1.43877e4

VOLS = ["Lascar", "Villarrica", "PlanchonPeteroa", "PuyehueCordonCaulle"]
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}


def rad_a_bt(L, lam=I04_LAMBDA):
    if L <= 0:
        return float("nan")
    return C2 / (lam * math.log1p(C1 / (lam ** 5 * L)))


def L(bt):
    return float(bt_to_spectral_radiance(np.float64(bt), I04_LAMBDA))


def resumen(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), 2),
            "p25": round(xs[len(xs) // 4], 2), "p75": round(xs[3 * len(xs) // 4], 2)}


def mirova():
    out = defaultdict(dict)
    for f in ("latest_consolidado.csv",
              "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            fe = (r.get("Fecha_Satelite_UTC") or "")
            if not (VENTANA[0] <= fe[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(fe[11:13] or 12) <= 9):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v > 0:
                out[vol][fe[:10]] = max(out[vol].get(fe[:10], 0), v)
    return out


def cargar(sub, vol):
    recs = json.load(open(os.path.join(ROOT, "data", sub, vol + ".json"),
                          encoding="utf-8"))["records"]
    out = {}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


mir = mirova()
res = {"ventana": list(VENTANA), "por_volcan": {}}

print("PARA LLEGAR A MIROVA: ?FONDO MAS FRIO O MAS PIXELES?")
print("clusters de 1 pixel, noches con referencia de MIROVA, %s a %s\n" % VENTANA)
print("%-22s %4s %9s %9s %10s %11s %11s %9s" %
      ("volcan", "n", "vrp ours", "vrp MIRO", "ratio", "t_bg usado", "t_bg NECES", "px NECES"))

for vol in VOLS:
    c, e = cargar("_s125_mag_control", vol), cargar("_s125_viirs_e", vol)
    # CONVENCION DEL VEREDICTO (script 09): un par por NOCHE, maximo de los dos
    # lados. Comparar cada pasada individual contra el maximo de MIROVA de esa
    # noche infla el objetivo cuando hay 2-3 pasadas VIIRS375, y con el objetivo
    # inflado la hipotesis "fondo" sale artificialmente imposible. Aca se toma
    # nuestra pasada de MAYOR VRP de cada noche y se la enfrenta al maximo de
    # MIROVA de esa misma noche.
    mejor_por_noche = {}
    for k in sorted(set(c) & set(e)):
        v = (c[k].get("primary_cluster") or {}).get("vrp_mw") or 0
        f = k[0][:10]
        if v > (mejor_por_noche.get(f, (0, None))[0]):
            mejor_por_noche[f] = (v, k)

    filas = []
    for f, (_, k) in sorted(mejor_por_noche.items()):
        r = c[k]
        pc = r.get("primary_cluster") or {}
        ap = r.get("anomaly_pixels") or []
        vm = mir.get(vol, {}).get(f)
        if pc.get("n_pixels") != 1 or len(ap) != 1 or not pc.get("vrp_mw") or not vm:
            continue
        bt = ap[0].get("bt_k")
        if not bt:
            continue
        L_pix = L(bt)
        L_bg = L_pix - pc["vrp_mw"] / K                    # fondo efectivo (exacto)
        # (a) fondo necesario para reproducir a MIROVA con este mismo pixel
        L_bg_nec = L_pix - vm / K
        t_bg_nec = rad_a_bt(L_bg_nec) if L_bg_nec > 0 else float("nan")
        # (b) pixeles equivalentes necesarios con el fondo actual
        px_nec = vm / pc["vrp_mw"]
        # cota fisica: el pixel mas frio que E vio en el disco de 3 km esa noche
        bts_e = [p["bt_k"] for p in (e[k].get("anomaly_pixels") or []) if p.get("bt_k")]
        cota_fria = min(bts_e) if bts_e else None
        filas.append({"bt": bt, "vrp": pc["vrp_mw"], "mirova": vm,
                      "t_bg_usado": rad_a_bt(L_bg), "t_bg_nec": t_bg_nec,
                      "px_nec": px_nec, "cota_fria": cota_fria})
    if len(filas) < 3:
        print("%-22s %4d  (muestra insuficiente)" % (vol, len(filas)))
        continue

    d = {
        "n": len(filas),
        "vrp_ours": resumen([f["vrp"] for f in filas]),
        "vrp_mirova": resumen([f["mirova"] for f in filas]),
        "ratio": resumen([f["vrp"] / f["mirova"] for f in filas]),
        "t_bg_usado_k": resumen([f["t_bg_usado"] for f in filas]),
        "t_bg_necesario_k": resumen([f["t_bg_nec"] for f in filas
                                     if math.isfinite(f["t_bg_nec"])]),
        "pixeles_necesarios": resumen([f["px_nec"] for f in filas]),
        "cota_fria_del_roi_k": resumen([f["cota_fria"] for f in filas if f["cota_fria"]]),
        "pct_donde_el_fondo_necesario_es_IMPOSIBLE": None,
    }
    imposibles = [f for f in filas
                  if f["cota_fria"] and (not math.isfinite(f["t_bg_nec"])
                                         or f["t_bg_nec"] < f["cota_fria"])]
    con_cota = [f for f in filas if f["cota_fria"]]
    if con_cota:
        d["pct_donde_el_fondo_necesario_es_IMPOSIBLE"] = round(
            100 * len(imposibles) / len(con_cota), 1)
    res["por_volcan"][vol] = d
    print("%-22s %4d %9.3f %9.3f %10.3f %11.2f %11s %9.2f"
          % (vol, d["n"], d["vrp_ours"]["mediana"], d["vrp_mirova"]["mediana"],
             d["ratio"]["mediana"], d["t_bg_usado_k"]["mediana"],
             d["t_bg_necesario_k"]["mediana"] if d["t_bg_necesario_k"] else "-",
             d["pixeles_necesarios"]["mediana"]))

print("\n" + "=" * 84)
print("?PUEDE EL FONDO SOLO EXPLICARLO?  (cota fria = pixel mas frio visto en el disco de 3 km)")
for vol, d in res["por_volcan"].items():
    if not d["t_bg_necesario_k"]:
        continue
    nec = d["t_bg_necesario_k"]["mediana"]
    cota = d["cota_fria_del_roi_k"]["mediana"] if d["cota_fria_del_roi_k"] else None
    imp = d["pct_donde_el_fondo_necesario_es_IMPOSIBLE"]
    print("  %-22s fondo necesario %.2f K vs cota fria %s K   imposible en %s%% de las noches"
          % (vol, nec, cota, imp))

print("\nSI EL FONDO NO ALCANZA, LA CUENTA ES DE PIXELES")
for vol, d in res["por_volcan"].items():
    print("  %-22s harian falta %.2f pixeles como el nuestro (hoy sumamos 1)"
          % (vol, d["pixeles_necesarios"]["mediana"]))

dest = os.path.join(os.path.dirname(__file__), "02_fondo_o_pixeles.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
