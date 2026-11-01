# -*- coding: utf-8 -*-
"""Verificador S159 PORTES, v01: (a) re-lectura con la tabla de latest.php sola (pedido de Nicolás) y combinada;
(b) cota honesta del silencio en el estrato neg_resto (0 eventos, el bootstrap no la ve); (c) MODIS y VIIRS 375.

Pregunta 1 del instrumento: si el port publicara en 5 % de neg_resto, ¿lo vería? Con 38 o 45 sorteadas, la
probabilidad de no ver ninguna es 0,95^38 = 14 % y 0,95^45 = 10 %: la medición casi no lo ve; por eso se
informa la cota de Wilson del estrato y no sólo el bootstrap.
Pregunta 2: si el port no publicara nunca, el recall daría 0 (control: se imprime el recall de K en la misma
lectura, que no puede ser 0); un pase sin resultado queda SIN DATO.
Control positivo: la lectura combinada debe reproducir exactamente los números de 04_analizar_salida.txt.
Uso: python -I v01_tabla_sola_y_ic.py   (lee los artefactos del run 39712862945 en D:)
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:/vrp-trabajo/s159-n")
PORTES = ROOT / "experiments/_s159/portes"
ART = Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(PORTES))
import banco_paridad as B  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402

spec = importlib.util.spec_from_file_location("an04", PORTES / "04_analizar.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def wilson(k, n, z=1.96):
    return A.wilson(k, n, z)


def main():
    obj = {o["id"]: o for o in json.loads((PORTES / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(ART.rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    ok = {i for i, r in res.items() if r.get("estado") == "ok" and r.get("port")}
    inner = B.inner_desde_html()
    casos, idx = [], []
    for i in sorted(ok):
        o, r = obj[i], res[i]
        if o["b"] == "VIIRS750":
            continue
        for m in A.VARIANTES[o["b"]]:
            p = r["port"].get(m)
            if p and p.get("npix"):
                p["_dcen"] = A.dist_centroide(p, o["grilla"])
            rp = A.record_port(p, inner[o["volcan"]], o["sensor"])
            rp = {k: x for k, x in rp.items() if not k.startswith("_")}
            casos.append([A.slim(rp), inner[o["volcan"]]])
            idx.append((i, m))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    salida = {}
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in sorted(ok) if obj[i]["b"] == b]
        for lect in ("combinada", "tabla_sola"):
            filas = []
            for i in ids:
                o = obj[i]
                rows = o["mirova"] if lect == "combinada" else [f for f in o["mirova"] if f["source"] == "CONS"]
                if not rows:
                    continue                      # la tabla no lista la pasada: sin etiqueta
                al = [f for f in rows if B.es_alerta(f["tipo"])]
                if o["lab"] == "pos" and al:
                    c = "pos_prot" if any(alerta_protegida(f) for f in al) else "pos_bajo"
                    mir = max(f["vrp_mw"] or 0 for f in al)
                elif o["lab"] == "neg_limpio" and not al:
                    c, mir = o["clase"], 0.0
                else:
                    c, mir = "CAMBIA:" + o["clase"], 0.0
                filas.append((i, c, o["clase"], o["peso"], bool(o["pub_prod"]), mir))
            for m in ("fisica", "sensible") + (("fisica_b21", "fisica_geo5km") if b == "MODIS" else ()):
                prot = [x for x in filas if x[1] == "pos_prot"]
                bajo = [x for x in filas if x[1] == "pos_bajo"]
                neg = [x for x in filas if x[1] in ("neg_pub", "neg_resto")]
                X = lambda x: P.get((x[0], m), False)
                perd = [x[0] for x in prot if x[4] and not X(x)]
                kp = sum(X(x) for x in prot)
                kb = sum(X(x) for x in bajo)
                Kp = sum(x[4] for x in prot)
                Kb = sum(x[4] for x in bajo)
                # silencio: ponderado (HT) y cota honesta del estrato neg_resto
                w = sum(x[3] for x in neg)
                pw = sum(x[3] for x in neg if X(x)) / w if w else float("nan")
                rest = [x for x in neg if x[2] == "neg_resto"]
                pubr = [x for x in neg if x[2] == "neg_pub"]
                kr = sum(X(x) for x in rest)
                wr = sum(x[3] for x in rest)
                wp = sum(x[3] for x in pubr)
                lo, hi = wilson(kr, len(rest))
                # cota superior: neg_pub ponderado tal cual + neg_resto al límite de Wilson
                cota = (sum(x[3] for x in pubr if X(x)) + hi * wr) / w if w else float("nan")
                # ratios R4
                rr = []
                for x in prot + bajo:
                    p = res[x[0]]["port"].get(m) or {}
                    if X(x) and x[5]:
                        rr.append(p["vrp_mw"] / x[5])
                rr.sort()
                med = rr[len(rr) // 2] if rr else None
                import numpy as np
                q = np.percentile(rr, [25, 50, 75]) if rr else [None] * 3
                dentro = sum(0.8 <= r <= 1.25 for r in rr)
                cambia = [x for x in filas if x[1].startswith("CAMBIA")]
                # dE (pre-registro) y dE con neg_resto al límite de Wilson
                bp = sum(x[3] for x in bajo if x[4] and not X(x))
                bg = sum(x[3] for x in bajo if not x[4] and X(x))
                ne = sum(x[3] for x in neg if X(x) and not x[4])
                na = sum(x[3] for x in neg if x[4] and not X(x))
                dE = (bp - bg) + (ne - na)
                dE_peor = (bp - bg) + (max(ne, hi * wr) - na)
                linea = (f"{b:8s} {lect:10s} {m:13s} prot {kp}/{len(prot)} (K {Kp}) perdidas_vs_K {len(perd)} "
                         f"bajo {kb}/{len(bajo)} (K {Kb}) | neg {sum(X(x) for x in neg)}/{len(neg)} pond {pw:.4f}; "
                         f"neg_resto {kr}/{len(rest)} Wilson_sup {hi:.3f} (peso {wr:.0f} de {w:.0f}) -> cota pond "
                         f"{cota:.4f} | R4 med {q[1] if rr else None} q[{q[0] if rr else None},{q[2] if rr else None}] "
                         f"n {len(rr)} en banda {dentro} | dE {dE:+.1f} dE_peor_resto {dE_peor:+.1f} | cambian {len(cambia)}")
                print(linea)
                salida[f"{b}|{lect}|{m}"] = {"prot": [kp, len(prot)], "K_prot": Kp, "perdidas": perd,
                                             "bajo": [kb, len(bajo)], "K_bajo": Kb, "neg_pond": pw,
                                             "neg_resto": [kr, len(rest)], "wilson_sup_resto": hi,
                                             "cota_pond": cota, "R4": [float(v) for v in q] if rr else None,
                                             "R4_n": len(rr), "R4_dentro": dentro, "dE": dE, "dE_peor": dE_peor}
    (Path(__file__).with_suffix(".json")).write_text(json.dumps(salida, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
