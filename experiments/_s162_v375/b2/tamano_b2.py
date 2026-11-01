# -*- coding: utf-8 -*-
"""S162 V375-B2: cuántas noches limpias nuevas (neg_resto) hacen falta para que la regla sellada de V375-B pueda decidir.

POR QUÉ. En el lote S162 la regla de B (`evaluar.lecturas`, «silencio») dio NO RESUELTO: la cota superior conservadora
de todos los negativos limpios fue (N_pub x cota de neg_pub + N_resto x cota de neg_resto) / N = 4,10 %, contra la vara
de K, 133 / 3.456 = 3,85 %. La parte de neg_pub no puede achicarse: las 133 noches neg_pub del marco ya están todas
medidas (20 en S159 y 113 en S162), así que en el conjunto que decide su cota es la de 31 de 113 (36,5 %). Toda la mejora
tiene que venir de neg_resto: su cota tiene que bajar de 2,80 % a (133 - 133 x 0,3652) / 3.323 = 2,54 % o menos.
Esta simulación da la probabilidad de que la regla decida (SILENCIO ACOTADO BAJO K) según la tasa real del port en
neg_resto y el tamaño de la segunda muestra, sola (lo que decide) o sumada a las 389 de S162 (el borrador descartado). Binomial con peso parejo (la
asignación proporcional deja los pesos casi iguales: n efectivo 385 de 389 en S162).
Uso: python -I tamano_b2.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import evaluar as EV  # noqa: E402

D = json.loads((AQUI.parent / "resultado_run40116289866/evaluar.json").read_text(encoding="utf-8"))["decision_s162"]
B = D["B_detalle"]
NP, NR = 133, 3323
VARA = NP / (NP + NR)
PUB_HI = B["neg_pub"]["ic"][1]
K0, N0 = B["neg_resto"]["crudo"]


def simular(base_k, base_n, tamanos, tasas, semilla):
    rng = np.random.default_rng(semilla)
    for p in tasas:
        fila = []
        for m in tamanos:
            ok = 0
            for _ in range(4000):
                k = base_k + rng.binomial(m, p)
                hi = EV.wilson(k, base_n + m)[1]
                ok += (NP * PUB_HI + NR * hi) / (NP + NR) < VARA
            fila.append(f"{m}: {ok / 4000:.2f}")
        print(f"  tasa real {p:.4f} ->", ", ".join(fila))


def main():
    lim = (VARA * (NP + NR) - NP * PUB_HI) / NR
    print(f"lote S162: neg_resto {K0} de {N0}, cota {B['neg_resto']['ic_kish'][1]:.4f}; neg_pub cota {PUB_HI:.4f}; "
          f"todos {B['negativos']['ic_conservador'][1]:.4f} contra K {VARA:.4f}")
    print(f"cota de neg_resto necesaria para decidir: {lim:.5f}")
    tasas = (0.0080, 0.0095, 0.0103, 0.0116, 0.0140, 0.0170, 0.0200, 0.0254)
    print()
    print("DECIDE B2 SOLA en neg_resto (PREREGISTRO_B2.md §5.1, tras el verificador del borrador, F1):")
    simular(0, 0, (600, 800, 1000, 1200, 1500, 2000), tasas, 163)
    print()
    print("borrador descartado, S162 + B2 (sólo para comparar; reutilizaba lo ya visto):")
    simular(K0, N0, (400, 600, 800, 1000, 1200), tasas, 162)


if __name__ == "__main__":
    main()
