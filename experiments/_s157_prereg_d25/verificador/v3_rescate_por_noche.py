# -*- coding: utf-8 -*-
r"""Verificador S157 1.29 (A94): el rescatable del sustrato contado en NOCHES, la unidad del operador.
Para cada pasada rescatable (cúmulo del cráter en 0,0 MW que K no publica, definición de sustrato_k.rescatable):
  en alertas (rescP): ¿K ya publica OTRA pasada de ese volcán esa noche (cualquier sensor)? si sí, recuperarla no
     cambia lo que el operador ve esa noche.
  en negativos limpios (rescN): ¿K ya publica algo ese volcán esa noche? si no, encenderla estrena una noche falsa.
Uso: python v3_rescate_por_noche.py --kunido D:\vrp-trabajo\temporales\verif_s157\k_unido > v3_salida.txt
"""
import argparse, collections, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sustrato_k as sk  # noqa
fk, bp = sk.fk, sk.bp

ap = argparse.ArgumentParser(); ap.add_argument("--kunido", required=True); a = ap.parse_args()
inner = bp.inner_desde_html()
for nombre, (desde, hasta, ref, solo) in sk.VENTANAS.items():
    recs, _ = fk.etiquetar_todo(a.kunido, fk.cargar_filas(ref, solo), (desde, hasta), set(bp.VOLS))
    recs = [r for r in recs if not (r["vol"] == "NevadosDeChillan" and r["noche"] < sk.FRONTERA_K)]
    pub_noche = collections.defaultdict(int)
    for r in recs:
        pub_noche[(r["vol"], r["noche"])] += bool(r["pub"])
    print("\n######## %s" % nombre)
    for s in ("VIIRS375", "VIIRS750"):
        out = collections.Counter(); noches_n = set(); noches_n_nuevas = set()
        for r in recs:
            if r["b"] != s or not sk.rescatable(r, inner):
                continue
            k = (r["vol"], r["noche"])
            if r["lab"] == "pos":
                out["rescP_pasadas"] += 1
                out["rescP_noche_ya_publicada_por_K"] += pub_noche[k] > 0
            elif r["lab"] == "neg_limpio":
                out["rescN_pasadas"] += 1
                noches_n.add(k)
                if pub_noche[k] == 0:
                    noches_n_nuevas.add(k)
        out["rescN_noches"] = len(noches_n); out["rescN_noches_que_K_no_publica"] = len(noches_n_nuevas)
        print("  %s %s" % (s, dict(out)))
