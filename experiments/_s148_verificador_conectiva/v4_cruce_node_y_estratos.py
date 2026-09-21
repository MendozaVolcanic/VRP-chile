# -*- coding: utf-8 -*-
"""V4: (a) mi port del predicado contra el predicado REAL del tablero ejecutado con node (via el
cargador del repo, usado SOLO como contraste), record por record; (b) recall por estrato de VRP de
MIROVA; (c) cobertura y ventana; (d) MODIS primer pase.

Uso: python v4_cruce_node_y_estratos.py <repo> <dir_salidas_run> <dir_congelado> <fin>
"""
import sys
import collections
from datetime import datetime
from pathlib import Path
from verif_base import B, F, VOLS, cargar_brazo, cargar_ref, etiquetar

REPO, D, CONG, FIN = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
rb, _ = cargar_brazo(D + "/" + B)
rf, _ = cargar_brazo(D + "/" + F)
lab, por = etiquetar(rb, cargar_ref(CONG), "2026-09-01", FIN)

print("## (a) port propio contra node (predicado real de frontend/index.html)")
for p in (REPO, REPO + "/scripts", REPO + "/experiments/_s146_ab_sin_test1"):
    sys.path.insert(0, p)
import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo as cb_repo, clave  # noqa: E402
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
print("   inner del html:", inner)
for nombre, mio in ((B, rb), (F, rf)):
    recs = cb_repo(Path(D) / nombre, coords, inner, ("2026-09-01", FIN))
    n = dif = dif_disp = 0
    for r in recs:
        k = clave(r)
        if k not in mio:
            continue
        n += 1
        if r["pub"] != mio[k]["_pub"]:
            dif += 1
            print("      DIFIERE", k, "node", r["pub"], r["disp"], "port", mio[k]["_pub"], mio[k]["_disp"])
        elif abs((r["disp"] or 0) - (mio[k]["_disp"] or 0)) > 1e-9:
            dif_disp += 1
    print("   %s: comparados %d | decision de publicar distinta %d | magnitud publicada distinta %d" % (nombre, n, dif, dif_disp))
    fuera = [k for k in mio if "2026-09-01" <= k[2][:10] <= FIN and k in lab and k not in {clave(r) for r in recs}]
    extra = [clave(r) for r in recs if clave(r) not in lab]
    print("      nocturnas segun mi criterio (solar_zenith>90) que el repo descarta: %d | del repo que yo descarto: %d" % (len(fuera), len(extra)))

print("\n## (b) recall V375 por estrato del VRP que publico MIROVA")
filas = collections.defaultdict(list)
for k in lab:
    if k[1] != "VIIRS375" or lab[k] != "pos" or k not in rf:
        continue
    t = datetime.strptime(k[2], "%Y-%m-%d %H:%M")
    m = [f["vrp"] for f in por[(k[0], k[1])] if abs((f["dt"] - t).total_seconds()) <= 120 and f["tipo"].startswith("ALERTA") and f["vrp"]]
    v = max(m) if m else None
    e = "sin VRP" if v is None else ("<0.1" if v < 0.1 else ("0.1-0.2" if v < 0.2 else ("0.2-0.5" if v < 0.5 else ">=0.5")))
    filas[e].append(k)
for e in ("<0.1", "0.1-0.2", "0.2-0.5", ">=0.5", "sin VRP"):
    s = filas.get(e, [])
    print("   MIROVA %-8s n=%3d | B publica %3d | F publica %3d" % (e, len(s), sum(rb[k]["_pub"] for k in s), sum(rf[k]["_pub"] for k in s)))

print("\n## (c) cobertura de la ventana completa y fechas")
kb, kf = set(rb), set(rf)
print("   records B %d, F %d | solo en F %d | solo en B %d" % (len(kb), len(kf), len(kf - kb), len(kb - kf)))
print("   solo en F por volcan:", dict(collections.Counter(k[0] for k in kf - kb)))
print("   solo en F por fecha:", dict(sorted(collections.Counter(k[2][:10] for k in kf - kb).items())))
print("   fecha minima B %s, F %s | maxima B %s, F %s" % (min(k[2] for k in kb), min(k[2] for k in kf), max(k[2] for k in kb), max(k[2] for k in kf)))
print("   (corte de regimen #535 = 2026-08-28 23:00 UTC; records anteriores al corte: B %d, F %d)" % (
    sum(k[2] < "2026-08-28 23:00" for k in kb), sum(k[2] < "2026-08-28 23:00" for k in kf)))
cm = [k for k in kb & kf if k[2][:10] <= FIN]
print("   tramo hasta %s: comunes %d (todas, incluidas diurnas)" % (FIN, len(cm)))
print("   processed_utc B: %s a %s | F: %s a %s" % (min(r["processed_utc"] for r in rb.values()), max(r["processed_utc"] for r in rb.values()),
                                                  min(r["processed_utc"] for r in rf.values()), max(r["processed_utc"] for r in rf.values())))

print("\n## (d) MODIS: pasadas con pixeles del primer pase (todas las etiquetas, tramo)")
km = [k for k in lab if k[1] == "MODIS" and k in rf]
print("   B %d de %d | F %d de %d" % (sum((rb[k].get("diag_n_first_pass_pixels") or 0) > 0 for k in km), len(km),
                                     sum((rf[k].get("diag_n_first_pass_pixels") or 0) > 0 for k in km), len(km)))
for s in ("VIIRS375", "VIIRS750"):
    kk = [k for k in lab if k[1] == s and k in rf]
    print("   %s B %d de %d | F %d de %d" % (s, sum((rb[k].get("diag_n_first_pass_pixels") or 0) > 0 for k in kk), len(kk),
                                            sum((rf[k].get("diag_n_first_pass_pixels") or 0) > 0 for k in kk), len(kk)))

print("\n## (e) sigma del dNTI en F: positivas contra negativas V375 (el umbral sube donde no hay nada?)")
import statistics
for L in ("pos", "neg"):
    for z in ("nadir", "medio", "borde"):
        from verif_base import zona
        kk = [k for k in lab if k[1] == "VIIRS375" and lab[k] == L and k in rf and rf[k].get("diag_sd_dnti") is not None
              and rf[k].get("sensor_zenith_deg") is not None and zona(rf[k]["sensor_zenith_deg"]) == z]
        if kk:
            print("   %s %-6s n=%3d | mediana mu+5sigma dNTI %.4f | mediana mu+5sigma dETI %.4f" % (
                L, z, len(kk), statistics.median(rf[k]["diag_mu_dnti"] + 5 * rf[k]["diag_sd_dnti"] for k in kk),
                statistics.median(rf[k]["diag_mu_deti"] + 5 * rf[k]["diag_sd_deti"] for k in kk)))
