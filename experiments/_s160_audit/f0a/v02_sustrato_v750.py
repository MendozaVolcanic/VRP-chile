"""V0a (verificador de F1-H4, F1-H6, F1-H9) sobre los datos de SHA_MAIN d516b9d8c (instantanea D:).

Camino DISTINTO al de sustrato_corpus.py de S158: aqui el "publica" sale de correr_node (predicado del tablero con
node, regla A97), se estratifica por volcan y por tramo (todo el corpus K, desde 2026-03-01, produccion K desde
2026-09-18), y se usan los diag_mu_dnti / diag_sd_dnti / diag_mu_deti / diag_sd_deti persistidos del primer pase.

Pregunta 1 (roto -> se ve?): si los diag_* no fueran los del primer pase o fueran constantes, las fracciones no
variarian por volcan ni por umbral; se imprime la fraccion a tres cortes (0,01 / 0,0225 / 0,05) y por volcan.
Pregunta 2 (instrumento muerto?): control positivo = control_identidad_predicado de banco_paridad (5 casos del guard)
y un record con vrp 0 que debe dar pub=0 y uno publicado conocido que debe dar pub=1.
Denominador y ventana: se imprimen en cada tabla (records V750 de los 11 Tier A con diag_sd_dnti no nulo).
"""
import collections, json, os, sys, glob, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:/vrp-trabajo/temporales/s160_audit/main"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402

VOLS = bp.VOLS
inner = bp.inner_desde_html()
print("inner_radius_km:", inner)

recs = []
for vol in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))
    for r in d["records"]:
        if str(r.get("sensor", "")).endswith("_750"):
            r["_vol"] = vol
            recs.append(r)
print("records V750 Tier A:", len(recs), "ventana", min(r["datetime_utc"] for r in recs), "->", max(r["datetime_utc"] for r in recs))

# ---- "publica" con node (A97)
casos = []
for r in recs:
    slim = {k: r.get(k) for k in bp.CAMPOS_JS}
    slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
    casos.append([slim, inner[r["_vol"]]])
pred = bp.correr_node(casos)
for r, p in zip(recs, pred):
    r["_pub"] = p[4]
# control del instrumento
ctl = bp.correr_node([[{"vrp_mw": 0.0, "n_anomalous_pixels": 0, "primary_cluster": None, "distance_class": None, "sensor": "VIIRS_SNPP_750"}, 5.0],
                      [{"vrp_mw": 0.5, "primary_cluster": {"vrp_mw": 0.5, "centroid_dist_km": 1.0, "n_pixels": 1}, "distance_class": "summit", "sensor": "VIIRS_SNPP_750", "t_bg_k": 280.0}, 5.0]])
print("control node: record vacio pub =", ctl[0][4], "(esperado 0); record summit 0,5 MW pub =", ctl[1][4], "(esperado 1)")
print("publicados V750 (node):", sum(r["_pub"] for r in recs))

def tramo(r):
    dt = r["datetime_utc"]
    return ("todo", "desde_2026-03-01" if dt >= "2026-03-01" else None, "K_produccion_desde_2026-09-18" if dt >= "2026-09-18" else None)

# ---- F1-H4: que umbral manda fuera de la cumbre (dNTI) con mu + 10 sigma del primer pase
print("\n== F1-H4: fraccion de pasadas en que mu+10*sd(dNTI) < corte (si < 0,0225 manda el minimo de MIROVA en nuestras unidades; si < 0,01 manda el nuestro)")
cortes = [0.01, 0.0225, 0.05]
def tabla(sel, nombre):
    n = len(sel)
    if not n:
        print(f"  {nombre}: n=0"); return
    print(f"  {nombre}: n={n}")
    for c in cortes:
        k = sum(1 for r in sel if r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"] < c)
        print(f"    mu+10sd(dNTI) < {c}: {k} ({100*k/n:.1f} %)")
    k = sum(1 for r in sel if r["diag_mu_deti"] + 10 * r["diag_sd_deti"] < 0.01125)
    print(f"    mu+10sd(dETI) < 0,01125 (MIROVA ETI fuera 0,01 x 9/8): {k} ({100*k/n:.1f} %)")
    k = sum(1 for r in sel if r["diag_mu_deti"] + 10 * r["diag_sd_deti"] < 0.01)
    print(f"    mu+10sd(dETI) < 0,01 (nuestro): {k} ({100*k/n:.1f} %)")
    k = sum(1 for r in sel if r["diag_mu_dnti"] + 5 * r["diag_sd_dnti"] < 0.003375)
    print(f"    cumbre: mu+5sd(dNTI) < 0,003375 (MIROVA 0,003 x 9/8): {k} ({100*k/n:.1f} %)")
    k = sum(1 for r in sel if r["diag_mu_dnti"] + 5 * r["diag_sd_dnti"] < 0.003)
    print(f"    cumbre: mu+5sd(dNTI) < 0,003 (nuestro): {k} ({100*k/n:.1f} %)")
    k = sum(1 for r in sel if max(r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"], 0.0225) >= 1.5 * max(r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"], 0.01))
    print(f"    umbral de MIROVA (en nuestras unidades) >= 1,5 x el nuestro: {k} ({100*k/n:.1f} %)")

con = [r for r in recs if r.get("diag_sd_dnti") is not None and r.get("diag_mu_dnti") is not None and r.get("diag_sd_deti") is not None]
print("records con diag del primer pase:", len(con), "de", len(recs))
tabla(con, "todo el corpus")
tabla([r for r in con if r["datetime_utc"] >= "2026-03-01"], "desde 2026-03-01")
tabla([r for r in con if r["datetime_utc"] >= "2026-09-18"], "produccion K desde 2026-09-18")
tabla([r for r in con if r["_pub"]], "publicados (node), todo el corpus")
tabla([r for r in con if r["_pub"] and r["datetime_utc"] >= "2026-09-18"], "publicados (node), produccion K")
print("  por volcan (desde 2026-03-01): n, % mu+10sd<0,0225, % <0,01")
for vol in VOLS:
    sel = [r for r in con if r["_vol"] == vol and r["datetime_utc"] >= "2026-03-01"]
    if sel:
        a = sum(1 for r in sel if r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"] < 0.0225)
        b = sum(1 for r in sel if r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"] < 0.01)
        print(f"    {vol:22s} n={len(sel):5d}  {100*a/len(sel):5.1f} %  {100*b/len(sel):5.1f} %")

# sustrato: pixeles alertados fuera del inner (donde el umbral de fuera decide algo)
print("\n  sustrato: records con algun pixel alertado (top-100 + descartados) con dist_km > inner, y publicados entre ellos")
for nombre, sel in [("desde 2026-03-01", [r for r in recs if r["datetime_utc"] >= "2026-03-01"]), ("produccion K", [r for r in recs if r["datetime_utc"] >= "2026-09-18"])]:
    fuera = [r for r in sel if any((p.get("dist_km") or 0) > inner[r["_vol"]] for p in (r.get("anomaly_pixels") or []) + (r.get("discarded_anomaly_pixels") or []))]
    print(f"    {nombre}: n={len(sel)} con pixeles fuera del inner={len(fuera)} ({100*len(fuera)/max(1,len(sel)):.1f} %), de ellos publicados={sum(r['_pub'] for r in fuera)}; "
          f"publicados totales={sum(r['_pub'] for r in sel)}")

# ---- F1-H6: lo publicado contra la suma de todos los alertados guardados
print("\n== F1-H6: publicados V750 (node): modo de un pixel y razon pc.vrp_mw / suma de todos los pixeles guardados (top-100 + descartados)")
def h6(sel, nombre):
    pub = [r for r in sel if r["_pub"]]
    if not pub:
        print(f"  {nombre}: 0 publicados"); return
    spm = sum(1 for r in pub if (r.get("primary_cluster") or {}).get("single_pixel_mode"))
    multi = sum(1 for r in pub if (r.get("primary_cluster") or {}).get("single_pixel_mode") and (r["primary_cluster"].get("n_pixels") or 0) > 1)
    llenos = sum(1 for r in pub if len(r.get("anomaly_pixels") or []) >= 100)
    razones = []
    for r in pub:
        s = sum((p.get("vrp_mw") or 0) for p in (r.get("anomaly_pixels") or []) + (r.get("discarded_anomaly_pixels") or []))
        if s > 0:
            razones.append(r["primary_cluster"]["vrp_mw"] / s)
    razones.sort()
    n = len(razones)
    q = lambda f: razones[min(n - 1, int(f * n))]
    print(f"  {nombre}: publicados={len(pub)} single_pixel_mode={spm} (con n_pixels>1: {multi}) top100 llenos={llenos}")
    print(f"    razon pc/suma: n={n} mediana={q(0.5):.3f} p5={q(0.05):.3f} p25={q(0.25):.3f} <0,9: {sum(1 for x in razones if x < 0.9)} ({100*sum(1 for x in razones if x < 0.9)/n:.1f} %) ==1: {sum(1 for x in razones if abs(x-1) < 1e-6)}")
    mp = [r for r in pub if (r.get("primary_cluster") or {}).get("n_pixels", 0) > 1]
    print(f"    publicados con cumulo de >1 pixel: {len(mp)}; n_pixels mediana de los publicados: {sorted((r['primary_cluster'].get('n_pixels') or 0) for r in pub)[len(pub)//2]}")
h6(recs, "todo el corpus")
h6([r for r in recs if r["datetime_utc"] >= "2026-03-01"], "desde 2026-03-01")
h6([r for r in recs if r["datetime_utc"] >= "2026-09-18"], "produccion K desde 2026-09-18")

# ---- F1-H9: records sin deteccion valen 0,0
print("\n== F1-H9: records V750 con n_anomalous_pixels == 0: valor de vrp_mw y si se distingue 'sin fondo' de 'miro y no vio'")
cero = [r for r in recs if not (r.get("n_anomalous_pixels") or 0)]
vals = collections.Counter(type(r.get("vrp_mw")).__name__ + ":" + str(r.get("vrp_mw")) for r in cero)
print("  sin deteccion:", len(cero), "de", len(recs), "; valores de vrp_mw:", vals.most_common(5))
print("  de ellos con diag_n_bg_anillo < 10 (anillo insuficiente, deberia no existir el record):",
      sum(1 for r in cero if (r.get("diag_n_bg_anillo") or 0) < 10), "; con t_bg_k None:", sum(1 for r in cero if r.get("t_bg_k") is None))
print("  campos que distinguirian nube/cobertura en un record sin deteccion (presentes en >0 records):",
      [k for k in ("cloud_fraction", "coverage", "n_valid_pixels", "diag_n_nan", "fraccion_nan", "roi_coverage") if any(k in r for r in cero)])
print("  primary_cluster en sin deteccion:", collections.Counter(str(r.get("primary_cluster")) for r in cero).most_common(2))
print("  pub (node) en sin deteccion:", sum(r["_pub"] for r in cero), "(esperado 0)")
