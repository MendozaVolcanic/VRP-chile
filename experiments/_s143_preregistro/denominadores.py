# -*- coding: utf-8 -*-
"""S143: tamaño del universo del A/B D22/D25 (VIIRS 375) ANTES de correrlo.

POR QUÉ. Un criterio pre-registrado sin denominador no es un criterio (A90, A91). Antes de fijar
qué volcanes entran al A/B hay que saber, por volcán y en la ventana 2026-06-01 a 2026-08-31,
cuántas pasadas nocturnas son negativos limpios (MIROVA miró y no vio nada) y cuántas noches
tienen alerta de MIROVA. Esos dos números no dependen del brazo: salen de la referencia y de qué
pasadas existen. La TASA de publicación, en cambio, sí depende del código, y la de los records
guardados mezcla el régimen anterior a #535; por eso aquí se reporta como contexto, no como
línea base del A/B (la línea base del A/B es el brazo control reprocesado).

Etiquetas y predicado: los de scripts/banco_paridad.py (predicado del dashboard con node).
Escribe denominadores.json (regla S91: ningún número del pre-registro se transcribe a mano).
USO: python experiments/_s143_preregistro/denominadores.py
"""
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

VENTANA = ("2026-06-01", "2026-08-31")
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(bp.cargar_referencia_unificada(cons, ocr), coords, VENTANA)
    recs = bp.cargar_nuestros(coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)

    por_vol = {}
    for vol in FOCAL + NEVADO:
        rr = [r for r in recs if r["vol"] == vol and r["b"] == "VIIRS375"]
        neg = [r for r in rr if r["lab"] == "neg_limpio"]
        pos = [r for r in rr if r["lab"] == "pos"]
        noches_alerta_ref = sorted({n for (v, b, n), d in ns.items() if v == vol and b == "VIIRS375" and d["alerta"]})
        noches_neg = sorted({r["noche"] for r in neg})
        por_vol[vol] = {
            "estrato": "focal" if vol in FOCAL else "nevado",
            "pasadas_v375": len(rr),
            "pasadas_neg_limpio": len(neg),
            "pasadas_neg_limpio_publicadas_guardadas": sum(r["pub"] for r in neg),
            "pasadas_pos": len(pos),
            "pasadas_pos_publicadas_guardadas": sum(r["pub"] for r in pos),
            "noches_con_alerta_nocturna_v375_referencia": len(noches_alerta_ref),
            "noches_con_neg_limpio": len(noches_neg),
            "etiquetas": dict(collections.Counter(r["lab"] for r in rr)),
        }
    out = {
        "meta": {"ventana": list(VENTANA), "referencia": {k: v["sha"] for k, v in info.items()},
                 "sha_index_html": bp.sha_git(bp.HTML),
                 "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "definiciones": {
            "pasadas_neg_limpio": "pasada nocturna V375 nuestra pareada (+-2 min) con RUTINA CONS en 0 MW y sin ALERTA ni FP de V375 en la noche del volcan (banco_paridad.etiquetar)",
            "pasadas_*_publicadas_guardadas": "predicado del dashboard sobre los records GUARDADOS (regimen mixto, antes de #535 casi toda la ventana): contexto, NO linea base del A/B",
            "noches_con_alerta_nocturna_v375_referencia": "noches UTC con alguna ALERTA nocturna V375 en CONS u OCR (pasadas diurnas descartadas por el banco)",
            "estratos": "scripts/build_c2ab_windows.py:41-42",
        },
        "por_volcan": por_vol,
    }
    (HERE / "denominadores.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for vol, d in por_vol.items():
        print(f"{vol:22s} {d['estrato']:6s} v375={d['pasadas_v375']:4d} neg={d['pasadas_neg_limpio']:4d} "
              f"(pub {d['pasadas_neg_limpio_publicadas_guardadas']:3d}) pos={d['pasadas_pos']:4d} "
              f"noches_alerta={d['noches_con_alerta_nocturna_v375_referencia']:3d} noches_neg={d['noches_con_neg_limpio']:3d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
