# -*- coding: utf-8 -*-
"""F4-08: (a) contraste MODIS de A82: fraccion de pasadas con cumulo de magnitud > 0 dentro del inner
(dc summit y pc_vrp>0), en negativos limpios contra positivos (SN), pareado C0 tag vs K main 18sep-17oct;
(b) D9: cumulos topados (pc.d9_capped) por regimen. Denominador impreso.
P1: el oraculo (pub = etiqueta) daria 0 contra 1; si el instrumento no viera nada daria 0 y 0 (se reporta n).
P2: pasadas sin cumulo cuentan como 'sin cumulo dentro', que es el dato y no un faltante (el record existe)."""
import io, json, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
L = lambda f: [json.loads(x) for x in open(f, encoding="utf-8")]
Mall = L("main_jul_oct.jsonl"); M = {(r["vol"], r["dt"], r["sensor"]): r for r in Mall}
T = [t for t in L("tag_c0_ventana.jsonl") if t["noche"] <= "2026-10-17"]
c = collections.Counter()
for t in T:
    m = M.get((t["vol"], t["dt"], t["sensor"]))
    if m is None or m["reg"] != "K": continue
    lab = t.get("lab_SN")
    for nom, r in (("C0", t), ("K", m)):
        dentro = r["dc"] == "summit" and (r["pc_vrp"] or 0) > 0
        if lab in ("pos", "neg_limpio"):
            c[(r["b"], nom, lab, "n")] += 1; c[(r["b"], nom, lab, "dentro")] += dentro
        if r["d9"]:
            c[(r["b"], nom, "d9_topado")] += 1
            if r["pub"]: c[(r["b"], nom, "d9_topado_pub")] += 1
for b in ("MODIS", "VIIRS750", "VIIRS375"):
    for nom in ("C0", "K"):
        s = []
        for lab in ("neg_limpio", "pos"):
            n = c[(b, nom, lab, "n")]; d = c[(b, nom, lab, "dentro")]
            s.append(f"{lab} {d}/{n} = {d/n:.3f}" if n else f"{lab} SIN DATO")
        print(b, nom, " | ".join(s), "| d9 topados", c[(b, nom, "d9_topado")], "publicados", c[(b, nom, "d9_topado_pub")])
# D9 en todo main por regimen
d = collections.Counter((r["reg"], r["b"]) for r in Mall if r["d9"])
print("d9 topados en main 01jul-19oct por regimen:", dict(d))
for r in Mall:
    if r["d9"] and r["reg"] == "K": print("K topado:", r["vol"], r["dt"], r["sensor"], r["dc"], r["pc_vrp"], "pub", r["pub"], "lab", r.get("lab_SN"))
