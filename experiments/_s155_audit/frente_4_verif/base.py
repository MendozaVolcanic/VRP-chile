# -*- coding: utf-8 -*-
"""Verificador F4 (S155): tabla por record de los 11 Tier A desde un ref git, con el predicado del tablero
ejecutado con node (banco_paridad.correr_node sobre frontend/index.html, A97) y las etiquetas de MIROVA
(banco_paridad.indexar_referencia + etiquetar, snapshot del repo, reglas 'original' y 'SN').

P1 (si lo medido estuviera roto, ¿lo veria?): controles todo/nada de banco_paridad no se repiten aca; se usa
   control_identidad_predicado() y se aborta si no da ([0,1,1,1,0],[1,0]).
P2 (instrumento muerto): cada fila guarda 'lab' (sin_info si no hay referencia), y 'pub' sale del node; un
   node caido aborta (RuntimeError), no devuelve ceros.
Uso: python base.py REF DESDE HASTA SALIDA.jsonl
"""
import io, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada

CORTE = "2026-10-18T09:57:30Z"
EXTRA = ["datetime_utc", "processed_utc", "first_processed_utc", "regimen", "sensor_zenith_deg", "solar_zenith_deg",
         "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "diag_n_first_pass_pixels",
         "diag_n_first_pass_summit", "diag_n_second_pass_recapture", "diag_n_dnti_ctx_path", "diag_n_eti_path",
         "n_test1_pixels", "triggered_test1", "test1_k_observed", "final_hotspot_source"]


def cargar(ref, vol):
    if ref == "WORKTREE":
        return json.loads((ROOT / "data/mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))["records"]
    txt = subprocess.run(["git", "show", f"{ref}:data/mirova_equivalent/{vol}.json"], capture_output=True,
                         encoding="utf-8", check=True, cwd=ROOT).stdout
    return json.loads(txt)["records"]


def main():
    ref, desde, hasta, salida = sys.argv[1:5]
    ident = bp.control_identidad_predicado()
    assert ident == ([0, 1, 1, 1, 0], [1, 0]), ident
    coords = _coords_por_volcan(); inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    idx = {m: bp.indexar_referencia(filas, coords, (desde, hasta), regla_minimas=m) for m in ("original", "SN")}
    recs, casos = [], []
    for vol in bp.VOLS:
        for r in cargar(ref, vol):
            b = bp.bucket(r.get("sensor")); d = r.get("datetime_utc", "")
            if b is None or not (desde <= d[:10] <= hasta):
                continue
            dt = datetime.strptime(d, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            lat, lon = coords[vol]
            pc = r.get("primary_cluster") or {}
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "sensor": r.get("sensor"),
                   "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                   "pc_npix": pc.get("n_pixels"), "d9": pc.get("d9_capped"), "z": r.get("sensor_zenith_deg"),
                   "diurna_desc": es_pasada_diurna_descartada(b, lat, lon, dt), "f5": r.get("f5_core_vrp_mw")}
            for k in EXTRA:
                rec[k] = r.get(k)
            rec["reg"] = "K" if (r.get("processed_utc") or "") >= CORTE else "C0"
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = p
    noct = [r for r in recs if not r["diurna_desc"]]
    for m, (por_vb, ns, nv, _) in idx.items():
        bp.etiquetar(noct, por_vb, ns, nv)
        for r in noct:
            r["lab_" + m] = r["lab"]; r["negE_" + m] = r["neg_estricto"]; r["rut_" + m] = r["rutina_pasada"]
            r["ncas_" + m] = r["noche_con_alerta_sensor"]
    with open(salida, "w", encoding="utf-8") as fh:
        for r in recs:
            r = dict(r); r["dt"] = r["dt"].strftime("%Y-%m-%d %H:%M")
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"{ref} {desde}..{hasta}: {len(recs)} records, {len(noct)} nocturnos, pub {sum(r['pub'] for r in recs)}")


if __name__ == "__main__":
    main()
