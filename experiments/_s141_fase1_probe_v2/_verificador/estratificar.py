# Verificador post-corrida: estadistica estratificada por volcan desde artefactos crudos
import json, sys, io, statistics as st, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from juntar import cargar
from analisis_v2 import fila_valida
filas = cargar(HERE / "artefactos")
med = lambda xs: (st.median([x for x in xs if x is not None]) if [x for x in xs if x is not None] else None)
val = [f for f in filas if fila_valida(f)[0]]
print("n_filas", len(filas), "validas", len(val))
print("\n== excluidas (candidatos) ==")
for f in filas:
    ok, m = fila_valida(f)
    if not ok and m != "control":
        r = f.get("resumen") or {}
        print(f["volcan"], f["pasada_utc"], m, "dist_centro_osf", r.get("dist_centro_osf_km"), "n_hoy", f["hoy"]["n_publicado"], "Npix", f["osf"]["Npix"])
print("\n== por pasada valida ==")
tot = collections.Counter(); near = 0; nlost = 0
agg = collections.defaultdict(list)
for f in val:
    r = f["resumen"]; ruta = r["ruta"]
    lost = [v for v in r["vecinos"] if v["caliente"] and not v["incluido"]]
    t_bg = f["record"].get("t_bg_k"); an13 = f["resumen_s135"].get("bt_mediana_anillo_1.0_3.0_km")
    mc = r["margenes_centro"]
    cen_bt_margin = (mc.get("ctx") or mc.get("1p") or {}).get("margen_bt_k")
    dnti_vals=[]; umb=[]; bt_marg=[]; rel=[]
    for v in lost:
        m = v["margenes"]["2p"] if ruta=="contextual" and v["margenes"]["2p"] and not v["margenes"]["2p"].get("sin_estadistica") else (v["margenes"]["ctx"] if ruta=="test1" else v["margenes"]["1p"])
        nlost += 1
        for a,u in (("margen_dnti","umbral_dnti"),("margen_deti","umbral_deti")):
            if m and m.get(a) is not None and m.get(u):
                if abs(m[a]) < 0.1*abs(m[u]): near += 1
        if m:
            dnti_vals.append(m.get("dnti")); umb.append(m.get("umbral_dnti"))
        p1 = v["margenes"]["1p"] or v["margenes"]["ctx"] or {}
        bt_marg.append(p1.get("margen_bt_k"))
        rel.append(v["margen_limitante_rel"])
    solo = sum(1 for v in lost if v["solo_compuerta_1p"])
    ctl = r.get("control") or {}
    print(f'{f["volcan"]:20s} {f["pasada_utc"]} ruta={ruta:10s} Npix={f["osf"]["Npix"]} n_hoy={f["hoy"]["n_publicado"]} perdidos={len(lost)} '
          f'satzen={f["osf"]["satzen"]:.1f} d_osf={r["dist_centro_osf_km"]} tbg={t_bg} anillo1-3={an13 and round(an13,2)} '
          f'bt_centro={r["bt_centro_k"]} margen_bt_centro={cen_bt_margin and round(cen_bt_margin,2)} exc_centro={r["exceso_centro_k"] and round(r["exceso_centro_k"],2)} '
          f'exc_cal={r["exceso_mediano_calientes_k"]} ctl_exc_centro={ctl.get("exceso_centro_k") and round(ctl["exceso_centro_k"],2)} ctl_exc_cal={ctl.get("exceso_mediano_calientes_k") and round(ctl["exceso_mediano_calientes_k"],2)} '
          f'dnti_med={med(dnti_vals) and round(med(dnti_vals),4)} umbral_med={med(umb) and round(med(umb),4)} margen_bt_med={med(bt_marg) and round(med(bt_marg),2)} solo_compuerta_1p={solo} '
          f'frac_brecha={r["fraccion_brecha"] and round(r["fraccion_brecha"],3)} frac_fondo={r["fraccion_fondo"] and round(r["fraccion_fondo"],3)} brecha={f["hoy"]["brecha_mw"] and round(f["hoy"]["brecha_mw"],3)}')
    for v in lost:
        tot[(ruta, v["limitante"])] += 1
print("\nperdidos totales", nlost, "tests de indice con |margen|<0.1|umbral| (zona donde C4 informa):", near)
print("\n== deti falla / bt falla por ruta (vecinos calientes perdidos) ==")
for ruta in ("contextual","test1"):
    ks = {k:v for k,v in tot.items() if k[0]==ruta}
    n = sum(ks.values())
    print(ruta, "n", n, "deti presente", sum(v for k,v in ks.items() if "deti" in k[1]), "dnti presente", sum(v for k,v in ks.items() if "dnti" in k[1]), "bt presente", sum(v for k,v in ks.items() if "bt" in k[1]), "disco", sum(v for k,v in ks.items() if "disco" in k[1]))
print("\n== peso por pasada: vecinos perdidos por pasada, por volcan ==")
for vol in sorted({f["volcan"] for f in val}):
    fs=[f for f in val if f["volcan"]==vol]
    per=[(f["pasada_utc"], f["resumen"]["ruta"], sum(1 for v in f["resumen"]["vecinos"] if v["caliente"] and not v["incluido"])) for f in fs]
    n=sum(p[2] for p in per); mx=max(per,key=lambda p:p[2])
    print(vol, "rutas", collections.Counter(p[1] for p in per), "perdidos", n, "pasada con mas peso", mx, "fraccion", round(mx[2]/n,3))
print("\n== OSF lat/lon unicos por volcan (candidatos validos) ==")
for vol in sorted({f["volcan"] for f in val}):
    fs=[f for f in filas if f["volcan"]==vol]
    print(vol, len(fs), "pares unicos", len({(f["osf"]["lat"],f["osf"]["lon"]) for f in fs}), sorted({round(f["resumen"]["dist_centro_osf_km"],3) for f in fs}))
