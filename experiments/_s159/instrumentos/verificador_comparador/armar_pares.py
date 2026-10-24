# -*- coding: utf-8 -*-
"""Verificador S159 del comparador D-28: arma los pares REALES de K (sólo K, D = K) por estrato y ventana, con la
misma selección que placebo_real.py, y los guarda en pares_k.json para los experimentos. NO lee ninguna salida de los
brazos del A/B de D25.

Uso: python armar_pares.py <TMP>
"""
import collections
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402


def main(tmp):
    datos, _ = S.unir_k(tmp)
    out = {}
    for nombre, (desde, hasta, ref, solo_tabla) in S.VENTANAS.items():
        filas = S.fk.cargar_filas(ref, solo_tabla)
        recs, _ = S.fk.etiquetar_todo(datos, filas, (desde, hasta), set(S.bp.VOLS))
        pares = collections.defaultdict(list)
        for r in recs:
            if r["b"] not in X.SENS or r["lab"] != "pos" or not r["pub"] or not r.get("vrp_ref") or not (r.get("disp") or 0) > 0:
                continue
            if solo_tabla and r["noche"] < "2026-04-01":
                continue
            clave = "%s|%s|%s" % (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))
            nom, _ = X.estrato(clave, r.get("z"))
            pares[nom].append({"k": r["disp"], "d": r["disp"], "m": r["vrp_ref"], "clave": clave,
                               "bloque": "%s|%s" % (r["vol"], r["noche"])})
        out[nombre] = dict(pares)
        print(nombre, {n: len(P) for n, P in pares.items()})
    (AQUI / "pares_k.json").write_text(json.dumps(out), encoding="utf-8")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
