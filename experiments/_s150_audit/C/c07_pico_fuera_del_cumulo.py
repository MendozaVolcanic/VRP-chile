"""C07: el pixel mas energetico dentro del inner_radius NO pertenece al cumulo primario.
Por que: la seleccion vent_anchored elige el cumulo MAS CERCANO al crater con VRP > 0, no el mas
energetico (pipeline/clustering.py, _vent_key). Con varios focos en el crater gana el mas cercano.
Prueba logica: pc.vrp_mw >= max(pixeles del pc) siempre (suma, o max con modo de un pixel, o
focal con keep_peak), asi que crater_max > pc.vrp_mw implica que el pixel mas energetico del
inner esta FUERA del pc. Margen 5 % para redondeo. Control: en records de un solo cumulo
(n_clu == 1) no deberia ocurrir salvo por redondeo o por el recorte D9.
Denominador: pasadas con pc desde 2026-03-01 (c02_pares.csv); dist_km de anomaly_pixels mide
desde el centro del volcan, no desde el ancla (pequena diferencia para los Tier A con vent movido).
"""
import io, sys
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
df = pd.read_csv("experiments/_s150_audit/C/c02_pares.csv")
df["m_cons"] = pd.to_numeric(df["m_cons"], errors="coerce")
df["fuera"] = (df.crater_max > 1.05 * df.pc_vrp) & (df.crater_max > 0.05) & (df.d9 == False)
print("control, n_clu == 1:", int(df[df.n_clu == 1].fuera.sum()), "de", int((df.n_clu == 1).sum()))
print("n_clu >= 2:", int(df[df.n_clu >= 2].fuera.sum()), "de", int((df.n_clu >= 2).sum()))
print(df[df.n_clu >= 2].groupby("fam").fuera.agg(["sum", "size"]))
p = df[(df.m_cons >= 1) & df.fuera]
print("con ALERTA de tabla >= 1 MW:", len(p), "de", int((df.m_cons >= 1).sum()))
print(p[["volcan", "dt", "sensor", "pc_vrp", "pc_n", "pc_dist", "n_clu", "spm", "crater_max", "crater_sum", "m_cons"]].to_string())
n = df[(df.volcan == "NevadosDeChillan") & (df.dt >= "2026-09-28") & df.fuera]
print("\nNdC desde 2026-09-28:", len(n))
print(n[["dt", "sensor", "pc_vrp", "pc_n", "pc_dist", "n_clu", "crater_max", "crater_sum", "m_cons", "m_ocr"]].to_string())
