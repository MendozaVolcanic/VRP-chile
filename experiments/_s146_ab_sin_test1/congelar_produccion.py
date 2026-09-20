"""S147 - congela la produccion y la referencia que el A/B usa como control positivo.

POR QUE (verificador con contexto limpio del pre-registro, H6). `parametros.json` dice que la
ventana es FIJA, pero lo fijo eran las FECHAS, no el contenido. El cron NRT escribe
`data/mirova_equivalent` cada dos horas y el scraper de MIROVA sigue trayendo filas, asi que el
corpus se mueve solo: entre dos corridas del mismo banco, con los mismos argumentos y con horas de
diferencia, los records pasaron de 2.360 a 2.386 y una vara de recall cambio de clasificacion por
el borde de su corte. Los techos de C3 son tasas absolutas calibradas sobre 373 y 622 negativos
limpios: si al evaluar hay 390 y 640, un brazo puede cruzar un techo por movimiento del
denominador y no por efecto del flag. Es la trampa A90 (un conteo sobre un corpus vivo no es
comparable consigo mismo) aplicada al control positivo de un experimento.

QUE CONGELA, y que no:
- **Congela** los records de produccion de la ventana, ya cargados y etiquetados, con el predicado
  del operador ya evaluado con node. Eso es lo que el control positivo compara. Pesa poco porque
  guarda solo los campos que el evaluador mira, no los JSON completos (276 MB).
- **NO congela** `data/mirova_equivalent` entero ni los CSV de referencia: los ancla por su sha de
  git, que es recuperable con `git show <sha>` y no cuesta espacio. Si el sha cambia, el evaluador
  lo dice.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el corpus no se moviera, esto lo mostraria? SI: el manifiesto guarda el sha de cada entrada,
   asi que una corrida posterior sobre entradas identicas da los mismos sha.
2. Si el instrumento estuviera muerto? El propio evaluador vuelve a comparar los sha y el conteo
   de records, y declara la diferencia en su salida en vez de seguir como si nada.

Uso:
  python experiments/_s146_ab_sin_test1/congelar_produccion.py \
      --cons <ruta>/registro_vrp_consolidado.csv --ocr <ruta>/registro_vrp_ocr.csv
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import scripts.banco_paridad as bp  # noqa: E402
from evaluar import anotar_vrp_mirova, cargar_brazo  # noqa: E402

SALIDA = Path(__file__).resolve().parent / "_congelado" / "produccion_ventana.json"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default="2026-09-20")
    ap.add_argument("--out", default=str(SALIDA))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = cargar_brazo(ROOT / "data" / "mirova_equivalent", coords, inner, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    anotar_vrp_mirova(recs, por_vb)

    serial = []
    for r in recs:
        s = dict(r)
        s["dt"] = r["dt"].strftime("%Y-%m-%d %H:%M")
        serial.append(s)

    manifiesto = {
        "congelado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana": list(ventana),
        "n_records": len(serial),
        "n_filas_referencia_nocturnas": n_ref,
        "sha_git": {
            "index_html": bp.sha_git(bp.HTML),
            "consolidado": bp.sha_git(Path(a.cons)),
            "ocr": bp.sha_git(Path(a.ocr)),
        },
        "etiquetas": {lab: sum(1 for r in serial if r["lab"] == lab)
                      for lab in ("pos", "neg_limpio", "far_ref", "sin_info")},
        "_que_es": ("Produccion congelada para el control positivo del A/B S146. Generado por "
                    "congelar_produccion.py ANTES de despachar ningun brazo (S147, H6). El "
                    "evaluador compara contra ESTO, no contra data/mirova_equivalent vivo."),
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"manifiesto": manifiesto, "records": serial},
                              indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifiesto, ensure_ascii=False, indent=1))
    print(f"-> {out}  ({out.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
