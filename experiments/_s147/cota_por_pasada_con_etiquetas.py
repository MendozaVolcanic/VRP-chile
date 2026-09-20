"""S147 - la cota del estadistico corregido, cruzada con las etiquetas de MIROVA.

LA PREGUNTA QUE RESPONDE. El estadistico corregido apaga ~9 de cada 10 disparos del Test 1 en
VIIRS 375 (`efecto_del_estadistico_corregido.py`). Eso, solo, no dice si es bueno o malo: lo que
decide es QUE apaga. Si lo que muere son pasadas en que MIROVA tampoco vio nada, el arreglo
sirve. Si muere alguna pasada en que MIROVA publico alerta, el arreglo cuesta recall.

DE DONDE SALEN LAS ETIQUETAS. No se inventan: se reusa el banco de paridad vetado
(`scripts/banco_paridad.py`, Fase 0 del plan S139), que etiqueta cada pasada nuestra contra la
referencia de MIROVA como `pos` (MIROVA publico ALERTA a +-2 min), `neg_limpio` (MIROVA listo ese
granule con VRP 0 y no alerto esa noche y sensor), `far_ref` o `sin_info`, y que ademas corre el
predicado REAL del dashboard con node para saber si el operador VE cada record (A97: la
atribucion se decide simulando la etapa siguiente, con el predicado del operador, nunca con uno
reconstruido a mano).

QUE ES Y QUE NO ES. Sigue siendo una COTA sobre lo persistido, no una re-ejecucion: marcar
SOSPECHA. El limite que mas importa: apagar el disparo del Test 1 NO equivale a no publicar,
porque el Test 1 compite por la fuente del cumulo y otro camino puede publicar igual. Por eso la
columna que manda es la de pasadas `pos` que HOY publica SOLO el Test 1 (sin cumulo con energia
propia): esas son las unicas en riesgo cierto, y son las que el A/B tiene que confirmar.

Uso:  python experiments/_s147/cota_por_pasada_con_etiquetas.py
"""
from __future__ import annotations
import collections
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.banco_paridad import (  # noqa: E402
    DATA, SNAP_CONS, SNAP_OCR, VOLS, _coords_por_volcan, bucket,
    cargar_nuestros, cargar_referencia_unificada, etiquetar,
    indexar_referencia, inner_desde_html,
)

APIX = {"VIIRS375": 0.140625, "VIIRS750": 0.5625, "MODIS": 1.0}
ROI_KM = 3.0
K_HOY = 3.0
MEDIA_NULA = 1.0 / math.sqrt(2.0 * math.pi)
DESV_NULA = math.sqrt(0.5 - 1.0 / (2.0 * math.pi))
VENTANA = ("2026-08-29", "2026-09-20")   # entera posterior al cambio de regimen de #535 (A104)


def umbral_corregido(b: str) -> float:
    n_pix = math.pi * ROI_KM ** 2 / APIX[b]
    return MEDIA_NULA * math.sqrt(n_pix) + K_HOY * DESV_NULA


def campos_test1_por_pasada() -> dict:
    """(volcan, bucket, datetime_utc) -> campos del Test 1 y del cumulo."""
    out = {}
    for vol in VOLS:
        d = json.loads((DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            if b is None:
                continue
            ts = r.get("datetime_utc", "")
            if not (VENTANA[0] <= ts[:10] <= VENTANA[1]):
                continue
            pc = r.get("primary_cluster") or {}
            out[(vol, b, ts)] = {
                "disparo": bool(r.get("triggered_test1")),
                "k": r.get("test1_k_observed"),
                "pc_vrp": pc.get("vrp_mw"),
                "fuente": r.get("final_hotspot_source"),
            }
    return out


def main() -> None:
    coords = _coords_por_volcan()
    inner = inner_desde_html()
    filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    por_vb, noche_sensor, noche_volcan, _ = indexar_referencia(filas, coords, VENTANA)
    recs = cargar_nuestros(coords, inner, VENTANA)
    etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    t1 = campos_test1_por_pasada()

    tabla = collections.defaultdict(lambda: collections.Counter())
    en_riesgo = []
    for r in recs:
        ts = r["dt"].strftime("%Y-%m-%d %H:%M")
        info = t1.get((r["vol"], r["b"], ts))
        if not info or not info["disparo"] or not isinstance(info["k"], (int, float)):
            continue
        b, lab = r["b"], r["lab"]
        sobrevive = float(info["k"]) > umbral_corregido(b)
        tabla[(b, lab)]["disparos"] += 1
        tabla[(b, lab)]["sobreviven"] += int(sobrevive)
        if r["pub"]:
            tabla[(b, lab)]["publica_hoy"] += 1
        # Solo sosten del Test 1: el cumulo que el dashboard publica lo ARMO el Test 1, o sea
        # `final_hotspot_source` es test1. OJO, falso cero corregido en esta misma sesion: la
        # primera version pedia "el cumulo no aporta energia propia" (pc_vrp <= 0), y eso da
        # CERO POR CONSTRUCCION, porque el predicado del dashboard exige pc.vrp_mw > 0 para
        # publicar. Un criterio que no puede dar distinto de cero no mide nada (A110).
        solo_test1 = str(info["fuente"] or "").startswith("test1")
        if r["pub"] and solo_test1:
            tabla[(b, lab)]["sostiene_test1"] += 1
        if r["pub"] and solo_test1 and not sobrevive:
            tabla[(b, lab)]["en_riesgo"] += 1
            if lab == "pos":
                en_riesgo.append((r["vol"], b, ts, info["k"], info["fuente"]))

    print(f"ventana {VENTANA[0]} a {VENTANA[1]} (posterior al cambio de regimen de #535)")
    print("COTA sobre lo persistido, NO una re-ejecucion. Marcar SOSPECHA.")
    print()
    print(f"{'sensor':10} {'etiqueta':12} {'umbral corr.':>12} {'disparos':>9} "
          f"{'sobreviven':>11} {'publica hoy':>12} {'en riesgo':>10}")
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        for lab in ("pos", "neg_limpio", "far_ref", "sin_info"):
            c = tabla.get((b, lab))
            if not c:
                continue
            print(f"{b:10} {lab:12} {umbral_corregido(b):12.2f} {c['disparos']:9d} "
                  f"{c['sobreviven']:11d} {c['publica_hoy']:12d} {c['en_riesgo']:10d}")

    print()
    if en_riesgo:
        print("PASADAS POSITIVAS EN RIESGO CIERTO (MIROVA alerto, hoy publica solo el Test 1,")
        print("y su disparo no sobrevive al estadistico corregido):")
        for vol, b, ts, k, fuente in sorted(en_riesgo):
            print(f"  {vol:22} {b:9} {ts}  k_obs={k:.2f}  fuente={fuente}")
    else:
        print("NINGUNA pasada positiva queda en riesgo cierto por esta cota.")
    print()
    print("LIMITE: apagar el disparo no equivale a no publicar. Lo decide el A/B, por pasada.")


if __name__ == "__main__":
    main()
