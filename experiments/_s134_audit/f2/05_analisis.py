# -*- coding: utf-8 -*-
"""F2/05 - Analisis de resultados.json. Medianas por volcan y por regimen, con n.
Declara denominador y ventana en cada numero (A90). Estratifica por VOLCAN, no solo por
regimen (feedback S126: una mediana agrupada invirtio un veredicto)."""
import json, os, statistics as st
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(_d, "resultados.json"), encoding="utf-8"))
R = D["filas"]
print("VENTANA: %s | emparejamiento <=%d s | n=%d pasadas\n" % (D["ventana"], D["tol_emparejamiento_s"], len(R)))

def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return (round(st.median(v), 2), len(v)) if v else (None, 0)
def frac(rows, k, u):
    v = [r[k] for r in rows if r.get(k) is not None]
    return (round(sum(1 for x in v if x < u)/len(v), 3), len(v)) if v else (None, 0)

print("=== TABLA 1 · POR VOLCAN (mediana km al crater, vent_lat/lon) ===")
print("%-21s %4s | %-13s %-15s | %-15s %-14s | %-11s" % (
    "volcan","n","d_max_TIF","d_centroide_TIF","d_crater_nuestro","d_pico_nuestro","dist_MIROVA"))
por_vol = {}
for v in sorted(set(r["volcan"] for r in R)):
    g = [r for r in R if r["volcan"] == v]
    por_vol[v] = g
    c = [med(g,k)[0] for k in ("d_max_tif_km","d_centroide_tif_km","d_crater_nuestro_km","d_pico_nuestro_km","dist_km_mirova")]
    fm = frac(g,"d_max_tif_km",1.0)[0]; fn = frac(g,"d_crater_nuestro_km",1.0)[0]
    print("%-21s %4d | %-6s (<1km %-4s) %-15s | %-6s (<1km %-4s) %-14s | %-11s" % (
        v, len(g), c[0], fm, c[1], c[2], fn, c[3], c[4]))

print("\n=== TABLA 2 · POR REGIMEN ===")
print("%-14s %4s | %-11s %-15s | %-16s %-14s | %s" % (
    "regimen","n","d_max_TIF","d_centroide_TIF","d_crater_nuestro","d_pico_nuestro","dist_MIROVA"))
for rg in ["focal","fumarolico","nevado_debil","difuso"]:
    g = [r for r in R if r["regimen"] == rg]
    if not g: print("%-14s %4d | SIN DATO" % (rg, 0)); continue
    c = [med(g,k) for k in ("d_max_tif_km","d_centroide_tif_km","d_crater_nuestro_km","d_pico_nuestro_km","dist_km_mirova")]
    print("%-14s %4d | %-5s(n=%-3d) %-7s(n=%-3d) | %-7s(n=%-3d) %-7s(n=%-3d) | %s(n=%d)" % (
        rg, len(g), c[0][0],c[0][1], c[1][0],c[1][1], c[2][0],c[2][1], c[3][0],c[3][1], c[4][0],c[4][1]))

print("\n=== TABLA 3 · LA PREGUNTA DEL FRENTE: MIROVA integra el crater? ===")
print("Comparacion pareada, MISMA pasada: d(max TIF de MIROVA) vs d(nuestro cumulo)")
print("%-21s %4s | %-9s %-9s | %-10s | %s" % ("volcan","n","TIF_med","nuestro_med","delta_med","gana_TIF"))
glob_t, glob_n, glob_d = [], [], []
for v, g in sorted(por_vol.items()):
    p = [r for r in g if r.get("d_max_tif_km") is not None and r.get("d_crater_nuestro_km") is not None]
    if not p: print("%-21s %4d | SIN DATO (sin cumulo publicado)" % (v, len(g))); continue
    t = [r["d_max_tif_km"] for r in p]; n = [r["d_crater_nuestro_km"] for r in p]
    d = [b-a for a, b in zip(t, n)]
    glob_t += t; glob_n += n; glob_d += d
    print("%-21s %4d | %-9.2f %-9.2f | %-10.2f | %.0f%%" % (
        v, len(p), st.median(t), st.median(n), st.median(d), 100*sum(1 for x in d if x > 0)/len(d)))
print("%-21s %4d | %-9.2f %-9.2f | %-10.2f | %.0f%%" % (
    "GLOBAL", len(glob_t), st.median(glob_t), st.median(glob_n), st.median(glob_d),
    100*sum(1 for x in glob_d if x > 0)/len(glob_d)))
print("  ('gana_TIF' = %% de pasadas en que el maximo de MIROVA esta MAS CERCA del crater que nuestro cumulo)")

print("\n=== TABLA 4 · CONTROL: que ancla reproduce la Distancia_km que MIROVA declara? ===")
print("Si ninguna la reproduce, la Distancia_km del CSV no es 'del crater' y no se puede")
print("comparar contra la nuestra sin re-anclar (D15, reference_s115_pcc_anchor_parity).")
print("%-16s %6s %-12s %-12s %-12s" % ("ancla","n","err_mediano","err_p90","frac_err<1km"))
for anc in ("vent","gvp","mirova_center"):
    k = "d_max_tif_a_%s" % anc
    e = sorted(abs(r[k]-r["dist_km_mirova"]) for r in R
               if r.get(k) is not None and r.get("dist_km_mirova") is not None)
    if not e: print("%-16s SIN DATO" % anc); continue
    print("%-16s %6d %-12.2f %-12.2f %-12.3f" % (
        anc, len(e), st.median(e), e[int(.9*len(e))], sum(1 for x in e if x < 1)/len(e)))
dm = [r["dist_km_mirova"] for r in R if r.get("dist_km_mirova") is not None]
print("  Distancia_km declarada por MIROVA: n=%d mediana=%.2f min=%.2f max=%.2f valores distintos=%d" % (
    len(dm), st.median(dm), min(dm), max(dm), len(set(dm))))

print("\n=== CONTROL: nocturnidad y sanidad de la geometria ===")
sz = [r["solar_zenith_deg"] for r in R if r.get("solar_zenith_deg") is not None]
print("solar_zenith_deg: n=%d de %d | min=%.1f (>90 = noche) -> %s" % (
    len(sz), len(R), min(sz) if sz else -1,
    "TODAS nocturnas" if sz and min(sz) > 90 else ("SIN DATO" if not sz else "HAY DIURNAS")))
sa = [r["semiancho_diag_km"] for r in R]
print("semiancho diagonal del raster: mediana=%.2f km (esperado 25,5*raiz(2)=36,06 para grilla 51x51 km)" % st.median(sa))
ce = [r["celdas_en_inner"] for r in R]
print("celdas dentro del inner: mediana=%d min=%d (si fuera 0 la medicion seria vacua)" % (st.median(ce), min(ce)))
npx = [r["n_anomaly_pixels_persistidos"] for r in R if r.get("n_anomaly_pixels_persistidos")]
nan = [r["n_anomalous_pixels"] for r in R if r.get("n_anomalous_pixels")]
print("anomaly_pixels persistidos: mediana=%s | n_anomalous_pixels: mediana=%s" % (
    st.median(npx) if npx else "SIN DATO", st.median(nan) if nan else "SIN DATO"))
