# -*- coding: utf-8 -*-
"""Verificador S146: la subclase "rival_debil_lt_0.01MW" del informe, puesta a prueba.

POR QUE. El informe separa T1_SOBRE_CTX en "fuente_unica" y "rival_debil_lt_0.01MW" mirando si los
contadores legacy dnti_ctx/nti estan en cero. Pero `resolve_test1_source_priority`
(pipeline/test1_integrated.py l. 175-182) tiene TRES ramas, y la PRIMERA no exige rival debil:

    if test1_summit_hit and eruption_far: return True     <- el cumulo contextual puede ser fuerte
    if only_test1_source: return True
    if weak_cluster_enabled and test1_summit_hit and cluster_vrp < 0,01: return True

`eruption_far` es `hotspot_dist_km > inner_radius_km` con el pixel suelto mas caliente de la escena
(process_viirs.py l. 1738), y `hotspot_dist_km` SI esta persistido. Si la rama 1 explica la mayoria,
la etiqueta "rival debil" del informe es falsa para esos casos, y con ella la lectura de la cota
inferior del contrafactual: un cumulo contextual fuerte se habria publicado igual sin el Test 1.

LAS DOS PREGUNTAS. (1) Si mi lectura estuviera rota, fallaria: exijo que TODA pasada clasificada
T1_SOBRE_CTX cumpla al menos una de las tres ramas; si alguna no cumple ninguna, mi reconstruccion
de la cascada esta mal y lo digo. (2) Si el instrumento estuviera muerto daria una sola categoria;
reporto las tres ramas por separado y sus solapes.
"""
from __future__ import annotations

import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s146_fase1_sustrato"))
import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

AQUI = Path(__file__).resolve().parent
REF = ROOT / "experiments" / "_s145_paridad" / "_dl_referencia"
VENTANA = ("2026-09-01", "2026-09-20")


def main():
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, VENTANA)
    recs = bp.cargar_nuestros(coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    # re-leer los campos crudos que bp no guarda
    crudo = {}
    for vol in bp.VOLS:
        d = json.loads((bp.DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            crudo[(vol, r.get("sensor"), r.get("datetime_utc"))] = r

    out = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}}
    tab = {}
    sin_rama = []
    for b in bp.BUCKETS:
        tab[b] = {}
        for lab in ("neg_limpio", "pos"):
            c = collections.Counter()
            for r in recs:
                if r["b"] != b or r["lab"] != lab or not r["pub"]:
                    continue
                # localizar el record crudo
                k = None
                for (vol, sens, dt), rr in crudo.items():
                    if vol == r["vol"] and dt == r["dt"].strftime("%Y-%m-%d %H:%M") and bp.bucket(sens) == b:
                        k = rr
                        break
                if k is None or k.get("final_hotspot_source") != "ctx_cluster":
                    continue
                pc = k.get("primary_cluster") or {}
                mismo = (pc.get("centroid_lat") is not None and k.get("final_hotspot_lat") is not None
                         and abs(pc["centroid_lat"] - k["final_hotspot_lat"]) < 1e-5
                         and abs(pc["centroid_lon"] - k["final_hotspot_lon"]) < 1e-5)
                if mismo:
                    continue  # AMBOS / CTX_SOLO, no es T1_SOBRE_CTX
                inn = inner[r["vol"]]
                hd = k.get("hotspot_dist_km")
                rama1 = hd is not None and hd > inn          # eruption_far (+ test1_summit_hit)
                rama2 = ((k.get("diag_n_dnti_ctx_path") or 0) == 0 and (k.get("diag_n_nti_path") or 0) == 0
                         and (k.get("diag_n_bt_path") or 0) == 0 and (k.get("diag_n_eti_path") or 0) == 0)
                c["n_T1_SOBRE_CTX"] += 1
                c["rama1_eruption_far"] += rama1
                c["rama2_only_test1_source"] += rama2
                c["rama1_sin_rama2"] += rama1 and not rama2
                c["ni_rama1_ni_rama2_(=>rival_debil)"] += (not rama1) and (not rama2)
                c["subclase_informe_rival_debil"] += not rama2
                if not rama1 and not rama2:
                    sin_rama.append([r["vol"], b, k.get("datetime_utc"), hd, inn,
                                     k.get("diag_n_dnti_ctx_path"), pc.get("vrp_mw")])
            tab[b][lab] = dict(c)
    out["ramas_de_la_cascada"] = tab
    out["casos_solo_rival_debil"] = sin_rama[:40]
    (AQUI / "subclase_t1_sobre_ctx.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(tab, ensure_ascii=False, indent=1))
    print("n casos que SOLO se explican por rival debil:", len(sin_rama))
    return 0


if __name__ == "__main__":
    sys.exit(main())
