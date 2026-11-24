# -*- coding: utf-8 -*-
"""F5 S175: insumos comunes del frente «identidad del pareo con MIROVA».

Corre sobre una copia privada de la base 752d348bc (git archive) en C:\\Users\\nmend\\vrp-temporales\\s175_audit\\f5\\root,
con los tres CSV de la referencia reemplazados por las copias LF de la ola 0 (sha256 f833bf..., 577a33..., dee768...).
Importa SIN MODIFICAR los módulos de la base (auto_audit_weekly, banco_paridad, referencia_mirova_unificada,
clase_mirova): el instrumento es el código de la base, no una reconstrucción a mano (regla A97).

Escribe un pickle con: recs del banco (predicado del tablero con node) etiquetados con D-9 SN y original, las
filas de la referencia unificada, las alertas del cargador del audit, y los records crudos indexados por pasada.
"""
import os
import pickle
import sys
import json
from datetime import datetime, timezone

ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import auto_audit_weekly as aw  # noqa: E402
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

WIN = ("2026-06-11", "2026-11-07")   # banco: desde el hito de calidad del OCR (A119) hasta el fin de la base


def main():
    assert os.path.realpath(aw.ROOT) == os.path.realpath(ROOT), aw.ROOT
    coords = aw._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aw.CONS, aw.OCR)
    recs = bp.cargar_nuestros(coords, inner, WIN)
    pv, ns, nv, n = bp.indexar_referencia(filas, coords, WIN)
    bp.etiquetar(recs, pv, ns, nv)
    for r in recs:
        r["lab_original"] = r["lab"]
    pv, ns, nv, n = bp.indexar_referencia(filas, coords, WIN, regla_minimas=aw.REGLA_MINIMAS)
    bp.etiquetar(recs, pv, ns, nv)
    crudos = {}
    records_por_volcan, integ = aw.cargar_records()
    for vol, rs in records_por_volcan.items():
        for r in rs:
            crudos[(vol, r.get("sensor"), r.get("datetime_utc"))] = {
                k: r.get(k) for k in ("final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km",
                                      "final_hotspot_source", "distance_class", "f5_core_vrp_mw", "vrp_mw",
                                      "sensor_zenith_deg", "granule", "via_codigo_mirova", "t_max_k")}
            crudos[(vol, r.get("sensor"), r.get("datetime_utc"))]["pc"] = {
                k: (r.get("primary_cluster") or {}).get(k)
                for k in ("vrp_mw", "centroid_lat", "centroid_lon", "centroid_dist_km", "n_pixels")}
            crudos[(vol, r.get("sensor"), r.get("datetime_utc"))]["n_anom"] = len(r.get("anomaly_pixels") or [])
    alertas = aw.alertas_mirova()
    out = {"win": WIN, "recs": recs, "filas": filas, "alertas": alertas, "crudos": crudos, "coords": coords,
           "inner_html": inner, "inner_audit": aw.INNER, "integ": integ,
           "generado": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with open(os.path.join(TMP, "f5_base.pkl"), "wb") as fh:
        pickle.dump(out, fh)
    import collections
    print("recs", len(recs), dict(collections.Counter(r["lab"] for r in recs)))
    print("filas", len(filas), "alertas_cargador", len(alertas), "crudos", len(crudos))
    print("inner html", inner)
    print("inner audit", aw.INNER)
    print("integridad", json.dumps(integ)[:300])


if __name__ == "__main__":
    main()
