# -*- coding: utf-8 -*-
"""H3: pasadas que publican en el brazo F (max) sin ningun pixel del primer pase.

Mide, sin correr el pipeline, con lo que cada record persiste (anomaly_pixels.bt_k, t_bg_k,
diag_n_first_pass_pixels, diag_n_second_pass_recapture):
  0. control del instrumento: en pasadas con primer pase > 0 y recaptura = 0, TODOS los pixeles
     deben cumplir bt_k > t_bg_k + 3 (la compuerta del primer pase). Si no, el instrumento no sirve.
  1. en las pasadas con primer pase = 0: que fraccion de pixeles NO cumple la compuerta.
  2. cuantas de esas ya eran primer pase = 0 en el brazo B (min): propio de max o venia de antes.
  3. credibilidad fisica: magnitud contra MIROVA, distancia al crater, volcan, zona, fondo.
  4. cuantas negativas limpias (y demas etiquetas) publican por ese camino, V375 y V750.
"""
import sys
import collections
import statistics as st
from base import cargar, mirova_mw, BT_GATE_K, zona

rb, rf, lab, por, comunes = cargar(sys.argv)


def fp(r):
    return r.get("diag_n_first_pass_pixels") or 0


def sp(r):
    return r.get("diag_n_second_pass_recapture") or 0


def exceso(r):
    """bt_k - t_bg_k de cada pixel persistido del record."""
    return [round(p["bt_k"] - r["t_bg_k"], 2) for p in (r.get("anomaly_pixels") or [])]


def cuart(q):
    q = sorted(q)
    return q[0], q[len(q) // 4], st.median(q), q[3 * len(q) // 4], q[-1]


print("#### 0. CONTROL DEL INSTRUMENTO: pasadas con primer pase>0 y recaptura=0 (todo pixel vino del primer pase)")
for s in ("VIIRS375", "VIIRS750"):
    for nombre, recs in (("B", rb), ("F", rf)):
        ks = [k for k in comunes if k[1] == s and fp(recs[k]) > 0 and sp(recs[k]) == 0
              and (recs[k].get("n_nti_path") or 0) == 0 and recs[k].get("t_bg_k") is not None
              and len(recs[k].get("anomaly_pixels") or []) == (recs[k].get("n_anomalous_pixels") or 0)]
        ex = [e for k in ks for e in exceso(recs[k])]
        print("  %s %s pasadas %d | pixeles %d | con bt<=t_bg+3: %d | exceso minimo %.2f K" %
              (s, nombre, len(ks), len(ex), sum(e <= BT_GATE_K for e in ex), min(ex) if ex else float("nan")))

print("\n#### 1. PASADAS CON PRIMER PASE = 0 y algun pixel: los pixeles cumplen la compuerta de BT?")
for s in ("VIIRS375", "VIIRS750"):
    for nombre, recs in (("B", rb), ("F", rf)):
        ks = [k for k in comunes if k[1] == s and fp(recs[k]) == 0 and (recs[k].get("n_anomalous_pixels") or 0) > 0
              and recs[k].get("t_bg_k") is not None]
        ex = [e for k in ks for e in exceso(recs[k])]
        n_alguno = sum(any(e > BT_GATE_K for e in exceso(recs[k])) for k in ks)
        print("  %s %s pasadas %d | pixeles %d | bt<=t_bg+3: %d (%.1f %%) | pasadas con ALGUN pixel sobre la compuerta: %d" %
              (s, nombre, len(ks), len(ex), sum(e <= BT_GATE_K for e in ex),
               100.0 * sum(e <= BT_GATE_K for e in ex) / max(1, len(ex)), n_alguno))
        if ex:
            print("       exceso bt-t_bg: min %.2f | p25 %.2f | mediana %.2f | p75 %.2f | max %.2f" % cuart(ex))
        npath = collections.Counter()
        for k in ks:
            for c in ("n_bt_path", "n_nti_path", "n_nti_rel_path", "n_vent_pixels", "n_test1_pixels", "diag_n_eti_path"):
                if (recs[k].get(c) or 0) > 0:
                    npath[c] += 1
        print("       otros caminos con pixeles en esas pasadas:", dict(npath))

print("\n#### 1b. En pasadas CON primer pase y CON recaptura: los pixeles bajo la compuerta caben en la recaptura?")
for s in ("VIIRS375", "VIIRS750"):
    for nombre, recs in (("B", rb), ("F", rf)):
        ks = [k for k in comunes if k[1] == s and fp(recs[k]) > 0 and sp(recs[k]) > 0 and recs[k].get("t_bg_k") is not None
              and len(recs[k].get("anomaly_pixels") or []) == (recs[k].get("n_anomalous_pixels") or 0)]
        mas = sum(1 for k in ks if sum(e <= BT_GATE_K for e in exceso(recs[k])) > sp(recs[k]))
        bajo = sum(sum(e <= BT_GATE_K for e in exceso(recs[k])) for k in ks)
        rec = sum(sp(recs[k]) for k in ks)
        print("  %s %s pasadas %d | pixeles recapturados %d | pixeles bajo la compuerta %d | pasadas con MAS pixeles bajo la compuerta que recapturados: %d" %
              (s, nombre, len(ks), rec, bajo, mas))

print("\n#### 2. PUBLICADAS SIN PRIMER PASE, por etiqueta, en F y en B")
for s in ("VIIRS375", "VIIRS750"):
    for L in ("pos", "neg", "far_ref", "sin_info"):
        tot = [k for k in comunes if k[1] == s and lab[k] == L]
        pubF = [k for k in tot if rf[k]["_pub"]]
        ks = [k for k in pubF if fp(rf[k]) == 0]
        yaB = sum(1 for k in ks if fp(rb[k]) == 0)
        pubB0 = sum(1 for k in tot if rb[k]["_pub"] and fp(rb[k]) == 0)
        print("  %s %-8s n=%4d | F publica %4d, SIN primer pase %3d (de esas, tampoco tenian primer pase en B: %3d) || B publica %4d, SIN primer pase %3d" %
              (s, L, len(tot), len(pubF), len(ks), yaB, sum(rb[k]["_pub"] for k in tot), pubB0))

print("\n#### 3. CREDIBILIDAD FISICA de las positivas V375 publicadas en F: sin primer pase contra con primer pase")


def resumen(ks, titulo):
    m = [mirova_mw(k, por)[0] for k in ks]
    raz = [rf[k]["_disp"] / x for k, x in zip(ks, m) if x]
    dist = [rf[k]["primary_cluster"]["centroid_dist_km"] for k in ks]
    npx = [rf[k]["primary_cluster"]["n_pixels"] for k in ks]
    ex = [max(exceso(rf[k])) for k in ks if exceso(rf[k])]
    mm = [x for x in m if x]
    print("  %s n=%d" % (titulo, len(ks)))
    print("     MIROVA MW min %.3f p25 %.3f mediana %.3f p75 %.3f max %.3f" % cuart(mm))
    print("     nuestra F MW mediana %.4f | razon F/MIROVA: min %.3f p25 %.3f mediana %.3f p75 %.3f max %.3f (n=%d)" %
          ((st.median(rf[k]["_disp"] for k in ks),) + cuart(raz) + (len(raz),)))
    print("     razon dentro de 0.5 a 2.0: %d de %d | distancia cumulo-crater km: mediana %.2f max %.2f | n_pixels mediana %s" %
          (sum(0.5 <= x <= 2 for x in raz), len(raz), st.median(dist), max(dist), st.median(npx)))
    print("     exceso del pixel mas caliente sobre el fondo (K): min %.2f p25 %.2f mediana %.2f p75 %.2f max %.2f" % cuart(ex))
    print("     t_bg_k mediana %.1f | zona:" % st.median(rf[k]["t_bg_k"] for k in ks),
          dict(collections.Counter(zona(rb[k]["sensor_zenith_deg"]) for k in ks)))
    print("     volcan:", dict(collections.Counter(k[0] for k in ks)))


pos = [k for k in comunes if k[1] == "VIIRS375" and lab[k] == "pos" and rf[k]["_pub"]]
resumen([k for k in pos if fp(rf[k]) == 0], "SIN primer pase en F")
resumen([k for k in pos if fp(rf[k]) > 0], "CON primer pase en F")

print("\n   por volcan: positivas publicadas en F, sin primer pase / total, y razon mediana F/MIROVA de cada grupo")
for v in sorted(set(k[0] for k in pos)):
    a = [k for k in pos if k[0] == v and fp(rf[k]) == 0]
    b = [k for k in pos if k[0] == v and fp(rf[k]) > 0]
    ra = [rf[k]["_disp"] / mirova_mw(k, por)[0] for k in a]
    rbb = [rf[k]["_disp"] / mirova_mw(k, por)[0] for k in b]
    print("     %-20s %2d / %3d | razon sin %s | con %s" % (v, len(a), len(a) + len(b),
          ("%.3f" % st.median(ra)) if ra else "  -  ", ("%.3f" % st.median(rbb)) if rbb else "  -  "))

print("\n#### 4. Las positivas V375 sin primer pase en F, una por una")
for k in [k for k in pos if fp(rf[k]) == 0]:
    r = rf[k]
    m, n = mirova_mw(k, por)
    print("  %-20s %s z %4.1f t_bg %.1f | fpB %d spB %d | spF %d npx %d dist %.2f | excesos K %s | F %.4f MW, MIROVA %.3f (x%.2f)" %
          (k[0], k[2], rb[k]["sensor_zenith_deg"], r["t_bg_k"], fp(rb[k]), sp(rb[k]), sp(r), r["primary_cluster"]["n_pixels"],
           r["primary_cluster"]["centroid_dist_km"], sorted(exceso(r), reverse=True)[:4], r["_disp"], m, r["_disp"] / m))

print("\n#### 5. Las NEGATIVAS limpias publicadas en F sin primer pase (V375 y V750), una por una")
for s in ("VIIRS375", "VIIRS750"):
    for k in [k for k in comunes if k[1] == s and lab[k] == "neg" and rf[k]["_pub"] and fp(rf[k]) == 0]:
        r = rf[k]
        print("  %s %-20s %s z %4.1f %s t_bg %.1f | fpB %d | spF %d npx %d dist %.2f | excesos K %s | F %.4f MW" %
              (s, k[0], k[2], rb[k]["sensor_zenith_deg"], zona(rb[k]["sensor_zenith_deg"]), r["t_bg_k"], fp(rb[k]), sp(r),
               r["primary_cluster"]["n_pixels"], r["primary_cluster"]["centroid_dist_km"],
               sorted(exceso(r), reverse=True)[:4], r["_disp"]))

print("\n#### 6. COTA: si el segundo pase NO corriera con el conjunto activo vacio (condicion (a) del paper) y la compuerta siguiera")
for s in ("VIIRS375", "VIIRS750"):
    for nombre, recs in (("B", rb), ("F", rf)):
        for L in ("pos", "neg"):
            tot = [k for k in comunes if k[1] == s and lab[k] == L]
            pub = sum(recs[k]["_pub"] for k in tot)
            pub_con = sum(1 for k in tot if recs[k]["_pub"] and fp(recs[k]) > 0)
            print("  %s %s %s: publica hoy %d de %d | a lo mas %d (las publicadas que tienen primer pase)" %
                  (s, nombre, L, pub, len(tot), pub_con))
