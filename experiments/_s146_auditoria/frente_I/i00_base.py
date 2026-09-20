# -*- coding: utf-8 -*-
"""I-00. Reproduce el banco con SUS funciones y deja un cache de pasadas con campos extra.

P1 (si lo medido estuviera roto, fallaria?): si: compara etiquetas y tasas contra banco_s145.json
    y avisa de cada diferencia; una diferencia no explicada por data nueva es una alarma.
P2 (instrumento muerto?): si el cache saliera vacio o node no corriera, los conteos dan 0 y el
    assert de n>1000 corta.
No escribe fuera de frente_I. Solo lectura del repo.
"""
import sys, json, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import banco_paridad as bp
from datetime import datetime, timezone

AQUI = Path(__file__).parent
DL = ROOT / "experiments" / "_s145_paridad" / "_dl_referencia"
VENT = ("2026-09-01", "2026-09-20")

def cargar_con_extras(coords, inner, ventana, filtrar_diurnas=True):
    recs, casos = [], []
    for vol in bp.VOLS:
        d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            diurna = bp.es_pasada_diurna_descartada(b, lat, lon, dt)
            if diurna and filtrar_diurnas:
                continue
            pc = r.get("primary_cluster") or {}
            recs.append({"vol": vol, "b": b, "sensor": r.get("sensor"), "dt": dt.isoformat(),
                         "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                         "pc_dist": pc.get("centroid_dist_km"), "z": r.get("sensor_zenith_deg"),
                         "vrp_mw": r.get("vrp_mw"), "f5": r.get("f5_core_vrp_mw"),
                         "t1": r.get("triggered_test1"), "pv": r.get("product_version"),
                         "gran": r.get("granule_id") or r.get("granule"), "diurna": diurna,
                         "npix": r.get("n_anomalous_pixels")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = p
    return recs

if __name__ == "__main__":
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
    print("sha index.html hoy:", bp.sha_git(bp.HTML))
    print("identidad predicado:", bp.control_identidad_predicado())
    # 1) banco tal cual, con sus funciones
    filas = bp.cargar_referencia_unificada(DL / "registro_vrp_consolidado.csv", DL / "registro_vrp_ocr.csv")
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, VENT)
    recs = bp.cargar_nuestros(coords, inner, VENT)
    bp.etiquetar(recs, por_vb, ns, nv)
    sr = bp.alertas_sin_record(por_vb, recs)
    ps, pv = bp.resumen(recs, sr)
    viejo = json.load(open(ROOT / "experiments/_s145_paridad/banco_s145.json", encoding="utf-8"))
    print("n_ref nocturnas:", n_ref, "| banco_s145:", viejo["meta"]["n_filas_ref_nocturnas"])
    print("etiquetas hoy:", dict(collections.Counter(r["lab"] for r in recs)), "| banco_s145:", viejo["meta"]["etiquetas"])
    for b in bp.BUCKETS + ["CUALQUIERA"]:
        p, n = ps[b]["pasada"], ps[b]["noche_volcan"]
        vp, vn = viejo["por_sensor"][b]["pasada"], viejo["por_sensor"][b]["noche_volcan"]
        print(f"{b:10s} HOY  recall_pas {p['recall_pos']} n{p['n_pos']} | pub_neg {p['tasa_pub_neg']} n{p['n_neg_limpio']} | noche recall {n['recall_pos']} n{n['n_pos']} pub_neg {n['tasa_pub_neg']} n{n['n_neg']}")
        print(f"{'':10s} S145 recall_pas {vp['recall_pos']} n{vp['n_pos']} | pub_neg {vp['tasa_pub_neg']} n{vp['n_neg_limpio']} | noche recall {vn['recall_pos']} n{vn['n_pos']} pub_neg {vn['tasa_pub_neg']} n{vn['n_neg']}")
    # 2) cache con extras (incluye diurnas marcadas)
    ext = cargar_con_extras(coords, inner, VENT, filtrar_diurnas=False)
    noct = [r for r in ext if not r["diurna"]]
    assert len(noct) == len(recs) and len(noct) > 1000, (len(noct), len(recs))
    assert [r["pub"] for r in noct] == [r["pub"] for r in recs]
    json.dump(ext, open(AQUI / "_cache_recs.json", "w", encoding="utf-8"))
    print("cache:", len(ext), "records (", len(noct), "nocturnos,", len(ext) - len(noct), "diurnos )")
