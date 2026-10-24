# -*- coding: utf-8 -*-
"""S162 instrumento, T4 y T6: cuantos casos mueve la definicion por pasada sobre la referencia real (A116).

Compara, sobre la referencia unificada del snapshot del repo (consolidado + OCR + historia + respaldo):
- protegidas lectura A de la funcion vieja (`pasadas_protegidas`, fila por fila y por minuto) contra la nueva
  (`resumir_pasadas` + `es_protegida`, por pasada a +-120 s, la tabla manda), con regla de minimas "original" en las
  dos para aislar el cambio de definicion; y la nueva con SN (la decidida) y con canal tabla;
- pasadas donde el OCR contradice a la tabla, y en que direccion;
- T6: protegidas de crater con el `inner_radius_km` del tablero y la plataforma del record de produccion a +-120 s.
Uso: python -I experiments/_s162_instrumento/t4_t6_medir_referencia.py  (desde la raiz del repo; sin red)
"""
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from scripts import clase_mirova as cm  # noqa: E402
from scripts.referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
import banco_paridad as bp  # noqa: E402


def plataformas_produccion():
    """(volcan, sensor_bucket) -> lista ordenada de (instante, sensor del record) de produccion."""
    out = {}
    for v in bp.VOLS:
        d = json.loads((RAIZ / "data" / "mirova_equivalent" / (v + ".json")).read_text(encoding="utf-8"))
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            try:
                t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            except (KeyError, ValueError):
                continue
            out.setdefault((v, b), []).append((t, r.get("sensor")))
    for lst in out.values():
        lst.sort()
    return out


def plataforma_de(p, prod):
    cand = [s for t, s in prod.get((p.volcano, p.sensor_bucket), [])
            if abs((t - p.instante).total_seconds()) <= cm.VENTANA_S + 60]   # el record va al minuto
    return cand[0] if len(set(cand)) == 1 else None


def main():
    ref = cargar_referencia_unificada()
    print("filas de la referencia:", len(ref), "por fuente", dict(Counter(f["source"] for f in ref)))
    vieja = cm.pasadas_protegidas(ref)
    pas_o = cm.resumir_pasadas(ref, regla_minimas="original")
    nueva_o = [p for p in pas_o if cm.es_protegida(p)]
    print("\n== T4: protegidas lectura A, regla de minimas original en las dos")
    print("vieja (claves al minuto):", len(vieja), " nueva (pasadas a +-120 s):", len(nueva_o))
    claves_nueva = {(p.volcano, p.sensor_bucket, f["fecha_utc"][:16]) for p in nueva_o for f in p.filas
                    if f.get("tipo") in cm.TIPOS_ALERTA}
    solo_vieja = sorted(vieja - claves_nueva)
    print("claves protegidas en la vieja que la nueva no cubre:", len(solo_vieja))
    for k in solo_vieja[:20]:
        g = [p for p in pas_o if (p.volcano, p.sensor_bucket) == k[:2]
             and any(f["fecha_utc"][:16] == k[2] for f in p.filas)]
        for p in g:
            print("  ", k, "->", p.estado, p.vrp_mw, p.fuente, "contradice" if p.ocr_contradice_tabla else "",
                  [(f["source"], f["tipo"], f["vrp_mw"]) for f in p.filas])
    n_multi = sum(1 for p in nueva_o if len({f["fecha_utc"][:16] for f in p.filas
                                             if f.get("tipo") in cm.TIPOS_ALERTA}) > 1)
    print("protegidas nuevas cuyas filas de alerta caen en mas de un minuto (la vieja las contaba doble):", n_multi)
    contra = [p for p in pas_o if p.ocr_contradice_tabla]
    print("pasadas con el OCR contradiciendo a la tabla:", len(contra))
    print("  por (tabla, ocr):", dict(Counter((p.estado, cm._estado([f for f in p.filas if f["source"] != "CONS"])[0])
                                         for p in contra)))
    print("  de ellas, con alerta OCR de 1 MW o mas:",
          sum(1 for p in contra if any(f["source"] != "CONS" and f.get("tipo") in cm.TIPOS_ALERTA
                                       and (f.get("vrp_mw") or 0) >= 1 for f in p.filas)))

    print("\n== nueva, regla SN (decidida), por canal y sensor")
    for canal in cm.CANALES:
        ps = [p for p in cm.resumir_pasadas(ref, canal=canal) if cm.es_protegida(p)]
        print(canal, len(ps), dict(Counter(p.sensor_bucket for p in ps)),
              "solo_ocr", sum(p.solo_ocr for p in ps))

    print("\n== T6: protegida de crater (union, SN), radio = inner_radius_km del tablero")
    inner = bp.inner_desde_html()
    prod = plataformas_produccion()
    ps = [p for p in cm.resumir_pasadas(ref) if cm.es_protegida(p)]
    por_sensor = Counter()
    motivos = Counter()
    for p in ps:
        ok, mot = cm.protegida_de_crater(p, inner[p.volcano], plataforma_de(p, prod))
        por_sensor[(p.sensor_bucket, ok)] += 1
        for m in mot:
            motivos[(p.sensor_bucket, m)] += 1
    for s in bp.BUCKETS:
        print(s, "protegidas A", por_sensor[(s, True)] + por_sensor[(s, False)], "de crater", por_sensor[(s, True)],
              "motivos", {m: n for (b, m), n in sorted(motivos.items()) if b == s})


if __name__ == "__main__":
    main()
