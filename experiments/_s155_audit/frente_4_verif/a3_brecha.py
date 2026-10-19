# -*- coding: utf-8 -*-
"""F4-03: ¿se invirtio A98? Recall y publicacion en negativos limpios, por pasada y por noche de volcan, con
banco_paridad.metricas (no reconstruido), reglas 'original' y 'SN', por sensor.
P1: control todo_publica/nada_publica sobre el mismo denominador debe dar 1 y 0 (se imprime).
P2: n de cada celda impreso; n=0 => SIN DATO. Comparacion PAREADA: mismas pasadas en el tag C0 y en main K.
"""
import io, json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
L = lambda f: [json.loads(x) for x in open(f, encoding="utf-8")]
M = L("main_jul_oct.jsonl"); T = L("tag_c0_ventana.jsonl")
def prep(rs, regla, lo, hi, reg=None):
    out = []
    for r in rs:
        if not (lo <= r["noche"] <= hi) or (reg and r["reg"] != reg): continue
        r = dict(r); r["lab"] = r["lab_" + regla]; r["neg_estricto"] = r["negE_" + regla]; out.append(r)
    return out
S = collections.Counter()
casos = [("C0 tag 18sep-17oct (pareado)", T, "2026-09-18", "2026-10-17", None),
         ("K main 18sep-17oct (pareado)", M, "2026-09-18", "2026-10-17", None),
         ("K main 18sep-17oct solo reg K", M, "2026-09-18", "2026-10-17", "K"),
         ("C0 main 29ago-17sep", M, "2026-08-29", "2026-09-17", None),
         ("C0 main 01jul-28ago (pre #535)", M, "2026-07-01", "2026-08-28", None)]
for regla in ("original", "SN"):
    print("==== regla", regla)
    for nom, rs, lo, hi, reg in casos:
        rr = prep(rs, regla, lo, hi, reg)
        for b in ("VIIRS375", "VIIRS750", "MODIS", None):
            p, n = bp.metricas(rr, S, bp._filtro(b=b))
            print(f"{nom:34s} {b or 'TODOS':8s} pasada rec {p['recall_pos']} (n{p['n_pos']}) negpub {p['tasa_pub_neg']} (n{p['n_neg_limpio']}) | noche rec {n['recall_pos']} (n{n['n_pos']}) negpub {n['tasa_pub_neg']} (n{n['n_neg']})")
        if regla == "SN" and nom.startswith("K main 18sep-17oct (pareado)"):
            todo = [dict(r, pub=1) for r in rr]; nada = [dict(r, pub=0) for r in rr]
            print("  control todo:", bp.metricas(todo, S, bp._filtro())[1], " nada:", bp.metricas(nada, S, bp._filtro())[1])
            # noches positivas perdidas
            no = collections.defaultdict(lambda: {"labs": set(), "pub": 0, "b": set()})
            for r in rr:
                e = no[(r["vol"], r["noche"])]; e["labs"].add(r["lab"]); e["pub"] = max(e["pub"], r["pub"])
                if r["lab"] == "pos": e["b"].add(r["b"])
            print("  noches pos perdidas (K):", sorted((k, sorted(e["b"])) for k, e in no.items() if "pos" in e["labs"] and not e["pub"]))
            rrT = prep(T, regla, lo, hi)
            noT = collections.defaultdict(lambda: {"labs": set(), "pub": 0})
            for r in rrT:
                e = noT[(r["vol"], r["noche"])]; e["labs"].add(r["lab"]); e["pub"] = max(e["pub"], r["pub"])
            print("  noches pos perdidas (C0 tag):", sorted(k for k, e in noT.items() if "pos" in e["labs"] and not e["pub"]))
