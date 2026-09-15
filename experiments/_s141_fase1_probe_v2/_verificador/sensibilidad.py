# Verificador post-corrida: sensibilidad descriptiva (NO cambia el veredicto pre-registrado)
import json, sys, io, statistics as st, collections, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from juntar import cargar
from analisis_v2 import fila_valida, evaluar, aporte_mw, planck_i04, bt_de_radiancia, FRAC_DOMINANTE
filas = cargar(HERE / "artefactos")
val = [f for f in filas if fila_valida(f)[0]]
med = lambda xs: st.median(xs) if xs else None
ev = evaluar(filas, "focal")
tot = collections.Counter(ev["conteo_agrupado"]); n = sum(tot.values())
print("agregado dominante", tot.most_common(1), "n", n, "frac", round(tot.most_common(1)[0][1]/n, 4))
for v, d in ev["por_volcan"].items():
    r = tot - collections.Counter(d["conteo"]); m = sum(r.values()); k = r.most_common(1)[0]
    print(" LOO sin", v, k, m, "frac", round(k[1]/m, 4))
print("\n== evaluar() quitando cada volcan (descriptivo) ==")
for vol in sorted(ev["por_volcan"]):
    e = evaluar([f for f in filas if f["volcan"] != vol], "focal")
    print(" sin", vol, "->", e["veredicto"])
print("\n== umbrales efectivos de los tests de indice (vecinos calientes perdidos) ==")
u = collections.Counter(); rel_neg = collections.defaultdict(lambda: [0,0]); exc_le0 = collections.defaultdict(lambda:[0,0])
for f in val:
    r = f["resumen"]; ruta = r["ruta"]
    for v in r["vecinos"]:
        if not (v["caliente"] and not v["incluido"]): continue
        m = v["margenes"]["2p"] if ruta == "contextual" else v["margenes"]["ctx"]
        u[(ruta, round(m["umbral_dnti"], 6), round(m["umbral_deti"], 6) if "umbral_deti" in m else None)] += 1
        rv = v["margen_limitante_rel"]
        if rv is not None:
            rel_neg[f["volcan"]][1] += 1; rel_neg[f["volcan"]][0] += rv < -1
        exc_le0[f["volcan"]][1] += 1; exc_le0[f["volcan"]][0] += (v["exceso_local_k"] is not None and v["exceso_local_k"] <= 0)
print(u)
print("margen_rel < -1 (indice del vecino bajo cero, no solo bajo el umbral) por volcan:", dict(rel_neg))
print("vecinos calientes perdidos con exceso_local <= 0 K por volcan:", dict(exc_le0))
print("\n== contraste: diferencia de medianas (criterio) vs mediana de diferencias pareadas por pasada ==")
for vol, d in ev["por_volcan"].items():
    fs = [f for f in val if f["volcan"] == vol]
    par = [f["resumen"]["exceso_mediano_calientes_k"] - f["resumen"]["control"]["exceso_mediano_calientes_k"] for f in fs
           if f["resumen"].get("control") and f["resumen"]["control"].get("exceso_mediano_calientes_k") is not None and f["resumen"]["exceso_mediano_calientes_k"] is not None]
    print(f" {vol:20s} criterio={d['contraste_k']:.3f} ({d['contraste']}) pareada={med(par):.3f} n={len(par)} por_pasada={[round(x,2) for x in par]}")
print("\n== fondo del centro con mascara tipo MIROVA (centro + vecinos calientes alertados), pasadas de 1 pixel publicado ==")
for f in val:
    r = f["resumen"]; idx = f["publicado"]["indices"]
    if len(idx) != 1: continue
    vs = [v for v in r["vecinos"] if v["bt_k"] is not None]
    ls_all = [planck_i04(v["bt_k"]) for v in vs if not v["incluido"]]
    ls_nohot = [planck_i04(v["bt_k"]) for v in vs if not v["incluido"] and not v["caliente"]]
    fl_all = bt_de_radiancia(sum(ls_all)/len(ls_all)); 
    fl_nohot = bt_de_radiancia(sum(ls_nohot)/len(ls_nohot)) if ls_nohot else None
    b = r["bt_centro_k"]; br = f["hoy"]["brecha_mw"]
    a_all = aporte_mw(b, fl_all); a_mir = aporte_mw(b, fl_nohot)
    print(f" {f['volcan']:20s} {f['pasada_utc']} k={r['k_calientes']} fondo_todos={fl_all:.2f} fondo_sin_calientes={fl_nohot and round(fl_nohot,2)} "
          f"frac_fondo_probe={(a_all - r['vrp_ruta_cumulo_mw'])/br:.3f} (json {r['fraccion_fondo']:.3f}) frac_fondo_mascara_miro={(a_mir - r['vrp_ruta_cumulo_mw'])/br:.3f}")
print("\n== Npix OSF vs angulo cenital del satelite (pasadas validas) ==")
xs = [(f["osf"]["satzen"], f["osf"]["Npix"], f["volcan"]) for f in val]
def rank(a):
    s = sorted(range(len(a)), key=lambda i: a[i]); rk=[0]*len(a); i=0
    while i < len(s):
        j=i
        while j+1<len(s) and a[s[j+1]]==a[s[i]]: j+=1
        for t in range(i,j+1): rk[s[t]]=(i+j)/2
        i=j+1
    return rk
ra, rb = rank([x[0] for x in xs]), rank([x[1] for x in xs]); ma, mb = st.mean(ra), st.mean(rb)
rho = sum((a-ma)*(b-mb) for a,b in zip(ra,rb))/math.sqrt(sum((a-ma)**2 for a in ra)*sum((b-mb)**2 for b in rb))
print(" spearman(satzen, Npix) =", round(rho,3), "n", len(xs))
print(" satzen>=45:", sorted((round(s,1),n,v) for s,n,v in xs if s>=45))
