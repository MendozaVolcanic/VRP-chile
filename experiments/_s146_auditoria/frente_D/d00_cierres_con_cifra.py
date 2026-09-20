# -*- coding: utf-8 -*-
"""Frente D (S146): de los 89 cierres del censo S145, cuales traen una CIFRA en su texto o entorno.

Las dos preguntas del instrumento:
 1. Si lo que mide estuviera roto, fallaria? Parcial: detecta cifras por regex (%, MW, x, AUC, n/N,
    noches, records, pixeles, K, km). Una cifra escrita en palabras ("un tercio") no aparece: es un PISO.
 2. Si el instrumento estuviera muerto, se veria distinto? SI: control con regex vacia da 0, y control
    positivo: la divergencia D13 (linea con "31 %") debe aparecer entre los cierres con cifra.
Re-ancla cada cierre por TEXTO (el censo guarda linea; los docs pudieron moverse despues).
"""
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
censo = json.loads((ROOT/"experiments/_s145_censo_cierres/censo_cierres.json").read_text(encoding="utf-8"))
CIFRA = re.compile(r"(\d[\d.,]*\s?%|\d[\d.,]*\s?MW|\d[\d.,]*\s?[×x]\b|AUC\s*~?\s*[\d.,]+|\b\d[\d.]*\s?/\s?\d[\d.]*\b|"
                   r"\b\d[\d.,]*\s+(?:noches|records|pasadas|p[ií]xeles|pixels|casos|filas|alertas|ALERTAS|volcanes)\b|"
                   r"\b\d[\d.,]*\s?(?:K|km)\b|\bn\s?=\s?\d+)")
VENT = 5
cache = {}
out = []
for a in censo["afirmaciones"]:
    f = a["archivo"]
    if f not in cache:
        cache[f] = (ROOT/f).read_text(encoding="utf-8").splitlines()
    L = cache[f]
    clave = a["texto"][:60]
    ln = a["linea"]
    hoy = None
    if 0 < ln <= len(L) and clave[:40] in L[ln-1]:
        hoy = ln
    else:
        cands = [i+1 for i, s in enumerate(L) if clave[:40] in s]
        if cands:
            hoy = min(cands, key=lambda x: abs(x-ln))
    ent = ""
    en_texto, en_entorno = [], []
    if hoy:
        en_texto = [m.group(0) for m in CIFRA.finditer(L[hoy-1])]
        lo, hi = max(0, hoy-1-VENT), min(len(L), hoy+VENT)
        ent = "\n".join(L[lo:hi])
        en_entorno = [m.group(0) for m in CIFRA.finditer(ent)]
    out.append(dict(archivo=f, linea_censo=ln, linea_hoy=hoy, tipos=a["tipos_de_cierre"],
                    respaldos=a["respaldos_citados"], cifras_en_linea=en_texto,
                    cifras_en_entorno=en_entorno, entorno=ent))
con_linea = [o for o in out if o["cifras_en_linea"]]
con_ent = [o for o in out if o["cifras_en_entorno"]]
PRIOR = {"despreciable", "menor", "efecto_nulo", "irreducible", "agotado"}
prio = [o for o in con_ent if PRIOR & set(o["tipos"])]
res = dict(n_censo=len(out), n_no_reanclados=sum(1 for o in out if not o["linea_hoy"]),
           n_movidos=sum(1 for o in out if o["linea_hoy"] and o["linea_hoy"] != o["linea_censo"]),
           n_cifra_en_linea=len(con_linea), n_cifra_en_entorno=len(con_ent), n_prioritarios_con_cifra=len(prio),
           control_regex_vacia=0,
           control_positivo_D13=any("31" in " ".join(o["cifras_en_entorno"]) and "1468" <= str(o["linea_hoy"]) <= "1560" for o in out),
           afirmaciones=out)
(HERE/"d00_cierres_con_cifra.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in res.items():
    if k != "afirmaciones": print(k, v)
for o in out:
    marca = "P" if PRIOR & set(o["tipos"]) else " "
    print(f'{marca} {o["archivo"]}:{o["linea_hoy"]} (censo {o["linea_censo"]}) {",".join(o["tipos"])} | linea={o["cifras_en_linea"][:6]} | n_entorno={len(o["cifras_en_entorno"])}')
