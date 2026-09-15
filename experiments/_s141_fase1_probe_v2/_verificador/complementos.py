# Verificador post-corrida: complementos descriptivos (no cambian el veredicto pre-registrado)
import sys, io, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from juntar import cargar
from analisis_v2 import fila_valida, aporte_mw, planck_i04, bt_de_radiancia, _clase_fondo, CONTRASTE_MIN_K
filas = cargar(HERE / "artefactos")
val = [f for f in filas if fila_valida(f)[0]]
med = lambda xs: st.median(xs) if xs else None
vols = sorted({f["volcan"] for f in val})
print("== A. contraste: todos los calientes (criterio) vs solo calientes PERDIDOS vs solo calientes INCLUIDOS ==")
for vol in vols:
    fs = [f for f in val if f["volcan"] == vol]
    per_lost, per_inc, n_inc = [], [], 0
    for f in fs:
        vv = f["resumen"]["vecinos"]
        lo = [v["exceso_local_k"] for v in vv if v["caliente"] and not v["incluido"] and v["exceso_local_k"] is not None]
        ic = [v["exceso_local_k"] for v in vv if v["caliente"] and v["incluido"] and v["exceso_local_k"] is not None]
        n_inc += len(ic)
        if lo: per_lost.append(med(lo))
        if ic: per_inc.append(med(ic))
    ctl = med([f["resumen"]["control"]["exceso_mediano_calientes_k"] for f in fs if f["resumen"].get("control")])
    todos = med([f["resumen"]["exceso_mediano_calientes_k"] for f in fs])
    cl = med(per_lost) - ctl
    print(f" {vol:20s} n_calientes_incluidos={n_inc} pasadas_con_incluidos={len(per_inc)} contraste_criterio={todos-ctl:.3f} "
          f"contraste_solo_perdidos={cl:.3f} ({'VECINOS_TIBIOS' if cl >= CONTRASTE_MIN_K else 'SIN_CONTRASTE'}) exceso_mediano_incluidos={med(per_inc) and round(med(per_inc),2)}")
print("\n== B. compuerta bt > t_bg + 3 K frente al anillo local 1-3 km ==")
for vol in vols:
    fs = [f for f in val if f["volcan"] == vol]
    off = [f["record"]["t_bg_k"] - f["resumen_s135"]["bt_mediana_anillo_1.0_3.0_km"] for f in fs]
    n_bt, n_pasa_local = 0, 0
    cen_fail = []
    for f in fs:
        r = f["resumen"]; an = f["resumen_s135"]["bt_mediana_anillo_1.0_3.0_km"]
        mc = r["margenes_centro"]; c = (mc.get("ctx") if r["ruta"] == "test1" else mc.get("1p")) or {}
        if c.get("margen_bt_k") is not None and c["margen_bt_k"] <= 0:
            cen_fail.append((f["pasada_utc"], r["ruta"], round(c["margen_bt_k"], 2)))
        if r["ruta"] != "test1": continue
        for v in r["vecinos"]:
            if v["caliente"] and not v["incluido"] and "bt_ctx" in (v["limitante"] or ""):
                n_bt += 1; n_pasa_local += v["bt_k"] > an + 3.0
    print(f" {vol:20s} t_bg_anillo_ruta - mediana_BT_1a3km: mediana={med(off):.2f} K min={min(off):.2f} max={max(off):.2f} | "
          f"test1: vecinos perdidos con bt_ctx={n_bt}, de ellos superan mediana_1a3km+3K={n_pasa_local} | centros bajo la compuerta={cen_fail}")
print("\n== C. fondo del cumulo con mascara tipo MIROVA (vecinos calientes alertados), solo pasadas de 1 pixel en el cumulo ==")
for vol in vols:
    fs = [f for f in val if f["volcan"] == vol]
    prob, mir = [], []
    for f in fs:
        r = f["resumen"]
        if len(f["publicado"]["indices"]) != 1: continue
        vs = [v for v in r["vecinos"] if v["bt_k"] is not None and not v["incluido"]]
        nh = [planck_i04(v["bt_k"]) for v in vs if not v["caliente"]]
        if not nh: continue
        br = f["hoy"]["brecha_mw"]
        prob.append(r["fraccion_fondo"])
        mir.append((aporte_mw(r["bt_centro_k"], bt_de_radiancia(sum(nh) / len(nh))) - r["vrp_ruta_cumulo_mw"]) / br)
    print(f" {vol:20s} n={len(prob)} mediana_probe={med(prob) and round(med(prob),3)} ({_clase_fondo(med(prob))}) mediana_mascara_miro={med(mir) and round(med(mir),3)} ({_clase_fondo(med(mir))})")
print("\n== D. indices del cumulo vs n_publicado_hoy (F5) en pasadas validas ==")
print([ (f["volcan"], f["pasada_utc"], len(f["publicado"]["indices"]), f["hoy"]["n_publicado"]) for f in val if len(f["publicado"]["indices"]) != f["hoy"]["n_publicado"]])
