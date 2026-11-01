# -*- coding: utf-8 -*-
"""V1 (S158): de las alertas V750 nocturnas de MIROVA en K (v1/cruce_v750_k.csv, n=58, tabla + OCR dedup), cuantas
tienen record nuestro publicado (>0) a |dt| <= 8 min, por clase: protegida (>=1 MW) o Muy Bajo. Ademas separa
lectura A (sin ALERTA_SIN_GEOMETRIA_OCR). Control: si el pareo estuviera roto daria 0 publicadas."""
import json, pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = pd.DataFrame(json.load(open("experiments/_s158_audit/v1/pub_v750.json")))
P = P[P.t >= "2026-09-18"]; P["tt"] = pd.to_datetime(P.t)
alias = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
P["vol"] = P.v.map(lambda x: alias.get(x, x))
C = pd.read_csv("experiments/_s158_audit/v1/cruce_v750_k.csv"); C["tt"] = pd.to_datetime(C.t)
o = pd.read_csv("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
sg = set(zip(o[o.Tipo_Registro == "ALERTA_SIN_GEOMETRIA_OCR"].Volcan, o[o.Tipo_Registro == "ALERTA_SIN_GEOMETRIA_OCR"].Fecha_Satelite_UTC))
C["sin_geom"] = [(v, t) in sg for v, t in zip(C.volcan, C.t)]
def pub(r):
    x = P[(P.vol == r.volcan) & ((P.tt - r.tt).abs() <= pd.Timedelta(minutes=8))]
    return bool((x.pub > 0).any())
C["publicada"] = C.apply(pub, axis=1)
N = C[~C.dia]
for nm, s in [("todas nocturnas", N.index == N.index), ("lectura A (sin SIN_GEOMETRIA)", ~N.sin_geom)]:
    x = N[s]
    for cl, m in [("protegidas >=1", x.vrp >= 1), ("Muy Bajo <1", x.vrp < 1)]:
        print(f"{nm} | {cl}: {int(x[m].publicada.sum())} de {int(m.sum())}")
print(N[~N.publicada][["volcan", "t", "canal", "vrp", "dist", "par", "n_pix", "sin_geom"]].to_string(index=False))

# Razon de magnitud publicada/MIROVA en las alertas nocturnas publicadas de la lectura A (tabla, con distancia)
def pubv(r):
    x = P[(P.vol == r.volcan) & ((P.tt - r.tt).abs() <= pd.Timedelta(minutes=8))]
    return x.pub.max() if len(x) else None
A = N[N.publicada & ~N.sin_geom & (N.canal == "tabla")].copy()
A["nuestro"] = A.apply(pubv, axis=1); A["razon"] = A.nuestro / A.vrp
print("\nrazon publicado/MIROVA, lectura A tabla nocturna publicada, n =", len(A), " mediana", round(A.razon.median(), 3),
      " cuartiles", A.razon.quantile([.25, .75]).round(3).tolist())
print(A.groupby("volcan").razon.agg(["size", "median"]).round(3).to_string())
