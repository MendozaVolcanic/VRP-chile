"""C03: analisis de c02_pares.csv (S150, frente C).

Preguntas: (A) cuantas pasadas confirmadas por MIROVA quedaron recortadas por el tope D9 y con que
valor de MIROVA; (B) el modo de un solo pixel contra la suma del crater y contra MIROVA, por
tramo de magnitud de MIROVA; (C) razon pc/MIROVA por tramo de magnitud y sensor (si el sistema
subestima mas cuanto mas fuerte es la senal); (D) fragmentacion: crater_sum mucho mayor que pc.
Instrumento: control positivo = el par NdC 2026-10-01 08:35 debe aparecer en (C) MODIS 5-10 MW.
Denominador y ventana: pasadas con primary_cluster desde 2026-03-01 (VIIRS: se reporta tambien
desde 2026-04-01 por A119), pareadas +-8 min a una ALERTA de la tabla consolidada.
"""
import io
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
df = pd.read_csv("experiments/_s150_audit/C/c02_pares.csv")
df["m_cons"] = pd.to_numeric(df["m_cons"], errors="coerce")
df["m_ocr"] = pd.to_numeric(df["m_ocr"], errors="coerce")
p = df[df["m_cons"] > 0].copy()
print("pasadas con pc:", len(df), "| pareadas a ALERTA de tabla con VRP>0:", len(p))
print("\n(A) tope D9 (pc.d9_capped) en toda la ventana:")
print(df.groupby(["fam", "d9"]).size().unstack(fill_value=0))
a = df[df["d9"] == True]
print("records con d9_capped por volcan:")
print(a.groupby(["volcan", "fam"]).size())
ap = a[a["m_cons"] > 0]
print("d9_capped pareados a ALERTA de tabla:", len(ap))
print(ap[["volcan", "dt", "sensor", "pc_vrp", "pc_n", "pc_dist", "dclass", "t_bg", "m_cons", "m_cons_dist"]].to_string())
ao = a[a["m_ocr"] > 0]
print("d9_capped pareados a OCR:", len(ao))
print(ao[["volcan", "dt", "sensor", "pc_vrp", "pc_n", "dclass", "t_bg", "m_ocr"]].to_string())
# Cuantas pasadas tienen el predicado del tope activo (aunque no recorte): cap activo <=> scene==5.0
# no es observable directo; se usa t_bg<270 y n_nti==0 como reconstruccion.
df["cap_activo"] = (df["t_bg"] < 270) & (df["n_nti"] == 0)
print("\npredicado reconstruido del tope (t_bg<270 y n_nti==0) por familia, fraccion de pasadas con pc:")
print(df.groupby("fam")["cap_activo"].mean().round(3))
print("idem en pasadas pareadas a ALERTA de tabla:")
print(p.assign(cap_activo=(p["t_bg"] < 270) & (p["n_nti"] == 0)).groupby("fam")["cap_activo"].agg(["mean", "size"]).round(3))

bins = [0, 0.5, 1, 2, 5, 10, 1e9]
lab = ["<0.5", "0.5-1", "1-2", "2-5", "5-10", ">10"]
p["tramo"] = pd.cut(p["m_cons"], bins=bins, labels=lab)
p["r_pc"] = p["pc_vrp"] / p["m_cons"]
p["r_crater"] = p["crater_sum"] / p["m_cons"]
p["mag_op"] = np.where((p["fam"] == "VIIRS375") & p["f5"].notna(), p["f5"], p["pc_vrp"])
p["r_op"] = p["mag_op"] / p["m_cons"]
print("\n(C) mediana de razon contra MIROVA por familia y tramo de MIROVA (n, pc, suma crater, magnitud que ve el operador):")
g = p.groupby(["fam", "tramo"], observed=True).agg(n=("r_pc", "size"), r_pc=("r_pc", "median"),
                                                     r_crater=("r_crater", "median"), r_op=("r_op", "median"))
print(g.round(3).to_string())
for desde in ("2026-04-01",):
    q = p[p["dt"] >= desde]
    print(f"\n(C') idem solo desde {desde}:")
    print(q.groupby(["fam", "tramo"], observed=True).agg(n=("r_pc", "size"), r_pc=("r_pc", "median"),
          r_crater=("r_crater", "median"), r_op=("r_op", "median")).round(3).to_string())
print("\n(C'') por volcan, solo MIROVA >= 2 MW:")
q = p[p["m_cons"] >= 2]
print(q.groupby(["volcan", "fam"]).agg(n=("r_pc", "size"), r_pc=("r_pc", "median"),
      r_crater=("r_crater", "median"), r_op=("r_op", "median")).round(3).to_string())

print("\n(B) modo de un solo pixel (spm) en pasadas pareadas:")
print(p.groupby(["fam", "spm"]).size().unstack(fill_value=0))
b = p[p["spm"] == True]
print(b.groupby(["fam", "tramo"], observed=True).agg(n=("r_pc", "size"), r_pc=("r_pc", "median"),
      r_crater=("r_crater", "median")).round(3).to_string())

print("\n(D) fragmentacion: pasadas pareadas donde crater_sum > 1,5 x pc y crater_sum > 0,5 MW:")
p["frag"] = (p["crater_sum"] > 1.5 * p["pc_vrp"]) & (p["crater_sum"] > 0.5)
print(p.groupby("fam")["frag"].agg(["sum", "size"]))
print(p[p["frag"] & (p["m_cons"] >= 2)][["volcan", "dt", "sensor", "pc_vrp", "pc_n", "n_clu", "spm",
      "crater_sum", "crater_n", "m_cons"]].to_string())
