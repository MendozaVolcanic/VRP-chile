# -*- coding: utf-8 -*-
"""V2: pareo B contra F (granulo, version, cenit), transiciones de publicacion, identidad del
cumulo (posicion y magnitud), y que camino de deteccion sostiene lo publicado en cada brazo.

Uso: python v2_pareo_y_caminos.py <dir_salidas_run> <dir_congelado> <fin>
"""
import sys
import collections
import statistics
from verif_base import B, F, cargar_brazo, cargar_ref, etiquetar, hav, zona

D, CONG, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
rb, _ = cargar_brazo(D + "/" + B)
rf, _ = cargar_brazo(D + "/" + F)
filas = cargar_ref(CONG)
lab, por = etiquetar(rb, filas, "2026-09-01", FIN)
comunes = [k for k in lab if k in rf]

print("#### 1. PAREO: mismo granulo en los dos brazos?")
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    ks = [k for k in comunes if k[1] == s]
    g_dist = [k for k in ks if rb[k].get("granule") != rf[k].get("granule")]
    v_dist = [k for k in ks if rb[k].get("product_version") != rf[k].get("product_version")]
    z_dist = [k for k in ks if rb[k].get("sensor_zenith_deg") != rf[k].get("sensor_zenith_deg")]
    tb_dist = [k for k in ks if rb[k].get("t_bg_k") != rf[k].get("t_bg_k")]
    plat = [k for k in ks if rb[k].get("sensor") != rf[k].get("sensor")]
    print(" ", s, "n", len(ks), "| granulo distinto", len(g_dist), "| product_version distinta", len(v_dist),
          "| plataforma distinta", len(plat), "| cenit distinto", len(z_dist), "| t_bg distinto", len(tb_dist))
    print("     versiones B:", dict(collections.Counter(rb[k].get("product_version") for k in ks)),
          " F:", dict(collections.Counter(rf[k].get("product_version") for k in ks)))
    for k in g_dist[:6]:
        print("     ej.", k, rb[k].get("granule"), "->", rf[k].get("granule"),
              "| z", rb[k].get("sensor_zenith_deg"), rf[k].get("sensor_zenith_deg"), "| lab", lab[k],
              "| pub", rb[k]["_pub"], rf[k]["_pub"])
    # cuantas de las con granulo distinto estan en neg o pos
    print("     granulo distinto por etiqueta:", dict(collections.Counter(lab[k] for k in g_dist)))

print("\n#### 2. TRANSICIONES de publicacion B -> F por etiqueta")
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    for L in ("neg", "pos", "far_ref", "sin_info"):
        c = collections.Counter((rb[k]["_pub"], rf[k]["_pub"]) for k in comunes if k[1] == s and lab[k] == L)
        print("  %-9s %-8s 1->1 %4d  1->0 %4d  0->1 %4d  0->0 %4d" % (s, L, c[(1, 1)], c[(1, 0)], c[(0, 1)], c[(0, 0)]))

print("\n#### 3. IDENTIDAD DEL CUMULO en las que publican los dos brazos (V375 y V750)")
for s in ("VIIRS375", "VIIRS750"):
    for L in ("pos", "neg"):
        ks = [k for k in comunes if k[1] == s and lab[k] == L and rb[k]["_pub"] and rf[k]["_pub"]]
        des, raz, razpc = [], [], []
        for k in ks:
            a, b = rb[k]["primary_cluster"], rf[k]["primary_cluster"]
            des.append(hav(a["centroid_lat"], a["centroid_lon"], b["centroid_lat"], b["centroid_lon"]))
            raz.append(rf[k]["_disp"] / rb[k]["_disp"])
            razpc.append(b["vrp_mw"] / a["vrp_mw"])
        if not ks:
            continue
        print("  %s %s n=%d | desplazamiento km: mediana %.3f, max %.3f, >0.5 km: %d, >1 km: %d" %
              (s, L, len(ks), statistics.median(des), max(des), sum(d > 0.5 for d in des), sum(d > 1 for d in des)))
        print("      razon magnitud publicada F/B: mediana %.3f, p10 %.3f, p90 %.3f, min %.3f, max %.3f | identica (1.000): %d | F<B: %d | F>B: %d" %
              (statistics.median(raz), sorted(raz)[len(raz) // 10], sorted(raz)[9 * len(raz) // 10], min(raz), max(raz),
               sum(abs(x - 1) < 1e-9 for x in raz), sum(x < 1 - 1e-9 for x in raz), sum(x > 1 + 1e-9 for x in raz)))
        print("      razon pc.vrp_mw F/B: mediana %.3f | n_pixels cumulo B mediana %s, F mediana %s" %
              (statistics.median(razpc), statistics.median(rb[k]["primary_cluster"]["n_pixels"] for k in ks),
               statistics.median(rf[k]["primary_cluster"]["n_pixels"] for k in ks)))
        print("      suma magnitud publicada: B %.3f MW, F %.3f MW" % (sum(rb[k]["_disp"] for k in ks), sum(rf[k]["_disp"] for k in ks)))
        movidos = [(k, d) for k, d in zip(ks, des) if d > 0.5]
        for k, d in movidos[:10]:
            print("      movido", k, "%.2f km" % d, "B dist", rb[k]["primary_cluster"]["centroid_dist_km"],
                  "F dist", rf[k]["primary_cluster"]["centroid_dist_km"], "disp", rb[k]["_disp"], rf[k]["_disp"])

print("\n#### 4. MAGNITUD contra MIROVA en positivas V375 publicadas por los dos")
ks = [k for k in comunes if k[1] == "VIIRS375" and lab[k] == "pos" and rb[k]["_pub"] and rf[k]["_pub"]]
from datetime import datetime
rbm, rfm = [], []
for k in ks:
    t = datetime.strptime(k[2], "%Y-%m-%d %H:%M")
    fs = [f for f in por[(k[0], k[1])] if abs((f["dt"] - t).total_seconds()) <= 120 and f["tipo"].startswith("ALERTA") and (f["vrp"] or 0) > 0]
    if fs:
        m = max(f["vrp"] for f in fs)
        rbm.append(rb[k]["_disp"] / m)
        rfm.append(rf[k]["_disp"] / m)
print("  n=%d | mediana nuestra/MIROVA: B %.3f, F %.3f" % (len(rbm), statistics.median(rbm), statistics.median(rfm)))

print("\n#### 5. CAMINOS: pasadas con pixeles del primer pase, por brazo y etiqueta")
CAMPOS = ["diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "n_dnti_ctx_path", "diag_n_eti_path",
          "n_bt_path", "n_nti_path", "n_nti_rel_path", "n_vent_pixels", "n_test1_pixels"]
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    print(" ", s)
    for L in ("pos", "neg", "far_ref", "sin_info"):
        ks = [k for k in comunes if k[1] == s and lab[k] == L]
        for nombre, recs in (("B", rb), ("F", rf)):
            fp = sum(1 for k in ks if (recs[k].get("diag_n_first_pass_pixels") or 0) > 0)
            an = sum(1 for k in ks if (recs[k].get("n_anomalous_pixels") or 0) > 0)
            print("    %-8s %s n=%4d | con primer pase>0: %4d | con n_anomalous_pixels>0: %4d | publica %4d" %
                  (L, nombre, len(ks), fp, an, sum(recs[k]["_pub"] for k in ks)))

print("\n#### 6. Que sostiene lo PUBLICADO en F (positivas y negativas, V375 y V750)")
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    for L in ("pos", "neg"):
        ks = [k for k in comunes if k[1] == s and lab[k] == L and rf[k]["_pub"]]
        if not ks:
            continue
        print("  %s %s publicadas en F: %d" % (s, L, len(ks)))
        for c in CAMPOS:
            print("      %-30s >0 en %4d | mediana %s" % (c, sum((rf[k].get(c) or 0) > 0 for k in ks),
                                                         statistics.median((rf[k].get(c) or 0) for k in ks)))
        print("      final_hotspot_source:", dict(collections.Counter(rf[k].get("final_hotspot_source") for k in ks)))
        print("      triggered_test1:", dict(collections.Counter(bool(rf[k].get("triggered_test1")) for k in ks)))
        sinfp = [k for k in ks if (rf[k].get("diag_n_first_pass_pixels") or 0) == 0]
        print("      publicadas en F SIN ningun pixel del primer pase:", len(sinfp))
        for k in sinfp[:8]:
            r = rf[k]
            print("         ", k, {c: r.get(c) for c in CAMPOS if (r.get(c) or 0) > 0}, r.get("final_hotspot_source"), "disp", r["_disp"])

print("\n#### 7. Las negativas V375 que sobreviven en F, una por una")
for k in [k for k in comunes if k[1] == "VIIRS375" and lab[k] == "neg" and rf[k]["_pub"]]:
    a, b = rb[k], rf[k]
    print("  ", k, "z %.1f %s t_bg %.1f | B pub %d disp %s dist %s | F disp %s dist %s npx %s fp %s" %
          (b["sensor_zenith_deg"], zona(b["sensor_zenith_deg"]), b["t_bg_k"], a["_pub"], a["_disp"],
           (a.get("primary_cluster") or {}).get("centroid_dist_km"), b["_disp"],
           b["primary_cluster"]["centroid_dist_km"], b["primary_cluster"]["n_pixels"], b.get("diag_n_first_pass_pixels")))

print("\n#### 8. Las positivas perdidas (B publica, F no) y ganadas, todos los sensores")
for k in comunes:
    if lab[k] == "pos" and rb[k]["_pub"] != rf[k]["_pub"]:
        t = datetime.strptime(k[2], "%Y-%m-%d %H:%M")
        m = [f["vrp"] for f in por[(k[0], k[1])] if abs((f["dt"] - t).total_seconds()) <= 120 and f["tipo"].startswith("ALERTA")]
        print("  ", k, "B pub", rb[k]["_pub"], rb[k]["_disp"], "-> F pub", rf[k]["_pub"], rf[k]["_disp"], "| MIROVA", m)
print("  positivas V375 que NINGUN brazo publica:")
for k in comunes:
    if k[1] == "VIIRS375" and lab[k] == "pos" and not rb[k]["_pub"] and not rf[k]["_pub"]:
        print("    ", k, "dc B", rb[k].get("distance_class"), "F", rf[k].get("distance_class"))

print("\n#### 9. Umbral efectivo en F: mu + C2 sigma contra C1 (dNTI), V375, por zona, en negativas")
for z in ("nadir", "medio", "borde"):
    ks = [k for k in comunes if k[1] == "VIIRS375" and lab[k] == "neg" and rf[k].get("sensor_zenith_deg") is not None
          and zona(rf[k]["sensor_zenith_deg"]) == z and rf[k].get("diag_sd_dnti") is not None]
    th = [rf[k]["diag_mu_dnti"] + 5 * rf[k]["diag_sd_dnti"] for k in ks]
    print("   %-6s n=%3d | mediana mu+5sigma dNTI %.4f | fraccion con mu+5sigma > 0.003: %.2f" %
          (z, len(ks), statistics.median(th), sum(x > 0.003 for x in th) / len(th)))
