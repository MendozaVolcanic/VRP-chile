# -*- coding: utf-8 -*-
"""d08: A83 ('no existe discriminante fisico que separe cat-b REAL de ARTEFACTO; AUC 0,859; 37 % confirmados').
El JSON fuente (experiments/_s116_followup/c2_discriminator.json) etiqueta TP = ALERTA de MIROVA y llama 'artifact' a TODO lo demas.
Aca: AUC de test1_k_observed para la etiqueta 'MIROVA alerto esa noche-sensor' sobre records summit con cumulo dentro del inner,
(a) ventana que S116 pudo ver (2026-02-01..06-27), (b) regimen previo completo, (c) actual; y NULO con etiquetas barajadas por volcan.
Instrumento: (1) AUC con etiqueta barajada debe dar ~0,5; con un oraculo (feature = etiqueta) da 1,0. (2) n_pos y n_neg impresos; SIN DATO si n_pos<10."""
import io, sys, json, random
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
D = cargar()
def auc(pos, neg):
    allv = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg]); i = 0; rs = 0.0; n = len(allv)
    while i < n:
        j = i
        while j < n and allv[j][0] == allv[i][0]: j += 1
        rk = (i + j + 1) / 2.0
        rs += rk * sum(l for _, l in allv[i:j]); i = j
    return round((rs - len(pos)*(len(pos)+1)/2) / (len(pos)*len(neg)), 3)
def medir(w, solo_recapture=False):
    mir, _ = cargar_mirova(w); rows = []
    for v in VOLS:
        ks = set(mir.get(v) or {})
        for r in D[v]:
            f = r["datetime_utc"][:10]; pc = r.get("pc") or {}
            if not (w[0] <= f <= w[1]) or r.get("distance_class") != "summit" or (pc.get("vrp_mw") or 0) <= 0: continue
            if pc.get("centroid_dist_km") is None or pc["centroid_dist_km"] > INNER[v] or r.get("test1_k_observed") is None: continue
            if solo_recapture and not (r.get("diag_n_second_pass_recapture") or 0) > 0: continue
            rows.append((v, bucket(r["sensor"]), r["test1_k_observed"], int((f, bucket(r["sensor"])) in ks)))
    res = {}
    for b in ("todos", "v375", "v750", "modis"):
        sub = [x for x in rows if b == "todos" or x[1] == b]
        pos = [x[2] for x in sub if x[3]]; neg = [x[2] for x in sub if not x[3]]
        if len(pos) < 10 or len(neg) < 10: res[b] = {"n_pos": len(pos), "n_neg": len(neg), "auc": "SIN DATO"}; continue
        rnd = random.Random(146); byv = {}
        for x in sub: byv.setdefault(x[0], []).append(x)
        ps, ns = [], []
        for v, xs in byv.items():
            labs = [x[3] for x in xs]; rnd.shuffle(labs)
            for x, l in zip(xs, labs): (ps if l else ns).append(x[2])
        res[b] = {"n_pos": len(pos), "n_neg": len(neg), "pct_pos": round(100*len(pos)/len(sub), 1), "auc_test1_k": auc(pos, neg),
                  "auc_nulo_barajado": auc(ps, ns), "auc_oraculo": auc([1]*len(pos), [0]*len(neg))}
    return res
out = {"S116_pudo_ver(02-01..06-27),solo_recapture": medir(("2026-02-01", "2026-06-27"), True),
       "previo(01-29..08-28)": medir(("2026-01-29", "2026-08-28")), "actual(09-01..09-19)": medir(("2026-09-01", "2026-09-19"))}
json.dump(out, open("d08_A83_etiqueta.json", "w"), indent=1); print(json.dumps(out, indent=1))
