"""S139 VERIFICADOR v4: el objeto D19 que domina la publicacion V375 en negativos, ¿es calor?
Compara la BT del pixel publicado (anomaly_pixel mas cercano al centroide del cumulo de 1 pixel)
con el fondo t_bg_k del record, en NEG_LIMPIO-like (noches sin ninguna alerta nocturna CONS u OCR
del volcan) y en noches con alerta. P1: si el pixel fuera calor real, BT - t_bg seria > 0 casi
siempre; si fuera borde frio (D19 S134), seria < 0 con frecuencia. P2: records sin anomaly_pixels
o sin campo de BT se cuentan como SIN DATO. Ventana 2026-01-10 a 2026-09-07, noche, 11 Tier A."""
import csv, json, sys, io, pathlib, math, statistics as st
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path(__file__).resolve().parents[3]; sys.path.insert(0, str(R))
from pipeline.mirova_csv_loader import normalize_volcano_name
VOLS = ["Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Chaiten","Villarrica","Llaima","Copahue","Isluga","PuyehueCordonCaulle"]
alert = set()
for f in ("latest_consolidado.csv", "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
    for r in csv.DictReader(open(R/f, encoding="utf-8", errors="replace")):
        v = normalize_volcano_name(r.get("Volcan")); t = r.get("Fecha_Satelite_UTC") or ""
        if v and (r.get("Tipo_Registro") or "").startswith("ALERTA") and int(t[11:13] or 12) <= 11:
            alert.add((v, t[:10]))
ej = None; res = defaultdict(list); sd = Counter()
for v in VOLS:
    for r in json.load(open(R/f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
        d = r["datetime_utc"]; s = r["sensor"]
        if not ("2026-01-10" <= d <= "2026-09-07 23:59") or s.startswith("MODIS") or s.endswith("_750"): continue
        sz = r.get("solar_zenith_deg")
        if (sz is not None and sz < 90) or (sz is None and int(d[11:13]) > 11): continue
        pc = r.get("primary_cluster") or {}
        if not (r.get("final_hotspot_source") == "test1_roi" and pc.get("single_pixel_mode") is True and (pc.get("vrp_mw") or 0) > 0): continue
        ap = r.get("anomaly_pixels") or []
        if ej is None and ap: ej = ap[0]; print("ejemplo anomaly_pixel:", ej)
        if not ap or r.get("t_bg_k") is None: sd["sin_pixels_o_tbg"] += 1; continue
        key = next((k for k in ("bt_k","bt","bt_mir_k","t_k","bt_i04_k") if k in ap[0]), None)
        if key is None: sd["sin_campo_bt"] += 1; continue
        la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
        p = min(ap, key=lambda a: (a.get("lat",0)-la)**2 + (a.get("lon",0)-lo)**2)
        grupo = "noche_con_alerta" if (v, d[:10]) in alert else "noche_sin_alerta"
        res[grupo].append((p[key] - r["t_bg_k"], pc.get("centroid_dist_km"), pc.get("vrp_mw")))
print("SIN DATO:", dict(sd))
for g, L in res.items():
    dts = [x[0] for x in L]; dist = [x[1] for x in L if x[1] is not None]
    print(g, "n", len(L), "| BT_pixel - t_bg: mediana %.2f K, frac <0: %.3f" % (st.median(dts), sum(x < 0 for x in dts)/len(dts)),
          "| centroid_dist_km mediana %.2f" % st.median(dist), "| vrp mediana %.3f" % st.median([x[2] for x in L]))
