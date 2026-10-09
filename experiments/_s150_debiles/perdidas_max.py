# -*- coding: utf-8 -*-
"""S150 (alertas debiles que `max` pierde). Paso 2: une la tabla por pasada (armar_tabla.py, mismo
predicado del tablero ejecutado con node) con los records crudos de B (min) y F (max), y escribe una
fila por alerta de MIROVA que B publica, marcando si F la conserva o la pierde.

  python perdidas_max.py --tmp <dir del paso 1> --out filas.json

INSTRUMENTO. Control de reproduccion: los conteos por sensor (B publica, F conserva) tienen que dar
los de experiments/_s149_prereg_invierno/resultados/agregado_abril_agosto.txt (VIIRS375: 988 y 946;
VIIRS750: 155 y 151). Si no dan, el pareo con los records crudos esta roto y no se interpreta nada.

Umbrales que F aplica en el primer pase (detection_context.py:525-535 con use_prose_branch=True):
  cumbre: dNTI > max(C1s, mu_dNTI + C2s*sd_dNTI) y dETI > max(C1s, mu_dETI + C2s*sd_dETI)
  escena: idem con C1e, C2e. C1s=0,003 C1e=0,010 C2s=5 C2e=10 (pipeline.profile del perfil F hoy).
mu y sd son los del record (diag_mu_dnti, diag_sd_dnti, ...), que no dependen de la conectiva: el
pool de fondo sale antes de combinar (detection_context.py:492-510). El script lo comprueba
comparando los diag de B y F en la misma pasada.
"""
import argparse, io, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
C1S, C1E, C2S, C2E = 0.003, 0.010, 5.0, 10.0
MESES = {"abril": ("2026-04-01", "2026-04-30"), "mayo": ("2026-05-01", "2026-05-31"),
         "junio": ("2026-06-01", "2026-06-30"), "julio": ("2026-07-01", "2026-07-31"),
         "agosto": ("2026-08-01", "2026-08-27")}
CONG = RAIZ / "experiments" / "_s149_prereg_invierno" / "_congelado"
DIAG = ["sensor", "granule", "sensor_zenith_deg", "t_bg_k", "t_max_i04_k", "t_max_i05_k", "diag_sigma_bg_k",
        "diag_nti_bg", "diag_nti_std", "nti_max", "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti",
        "diag_n_bg_used_first_pass", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture",
        "n_anomalous_pixels", "n_hotspots_clustered", "distance_class", "final_hotspot_source",
        "final_hotspot_dist_km", "vrp_mw", "f5_core_vrp_mw", "diag_n_bg_anillo", "n_dnti_ctx_path"]


def crudos(d):
    out = {}
    for p in Path(d).glob("*.json"):
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if b in ("VIIRS375", "VIIRS750"):
                out["%s|%s|%s" % (p.stem, b, r.get("datetime_utc"))] = r
    return out


def resumen(r):
    if r is None:
        return None
    s = {k: r.get(k) for k in DIAG}
    pc = r.get("primary_cluster") or {}
    s["pc_vrp"] = pc.get("vrp_mw"); s["pc_n"] = pc.get("n_pixels"); s["pc_dist"] = pc.get("centroid_dist_km")
    ap = r.get("anomaly_pixels") or []
    s["n_ap"] = len(ap)
    s["ap_dist_min"] = min((q["dist_km"] for q in ap), default=None)
    s["ap_bt_max"] = max((q["bt_k"] for q in ap), default=None)
    mu, sd, mue, sde = (r.get(k) for k in ("diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti"))
    if None not in (mu, sd, mue, sde):
        s["stat_dnti_s"] = mu + C2S * sd; s["stat_deti_s"] = mue + C2S * sde
        s["thrF_dnti_s"] = max(C1S, s["stat_dnti_s"]); s["thrF_deti_s"] = max(C1S, s["stat_deti_s"])
        s["stat_dnti_e"] = mu + C2E * sd; s["stat_deti_e"] = mue + C2E * sde
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tmp", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); tmp = Path(a.tmp)
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
    filas, cuenta = [], {}
    diag_distinto = 0; n_comparados = 0
    for mes, ventana in MESES.items():
        T = json.loads((tmp / mes / "tabla.json").read_text(encoding="utf-8"))["pasadas"]
        rb, rf = crudos(tmp / mes / B), crudos(tmp / mes / F)
        ref = cargar_referencia_unificada(CONG / mes / "registro_vrp_consolidado.csv", CONG / mes / "registro_vrp_ocr.csv")
        por_vb, _, _, _ = bp.indexar_referencia(ref, coords, ventana)
        for k, v in T.items():
            vol, b, dts = k.split("|")
            if b not in ("VIIRS375", "VIIRS750") or len(v) != 2:
                continue
            c, f = v["control"], v["brazo"]
            if c["lab"] != "pos" or not c["pub"]:
                continue
            perdida = not f["pub"]
            cuenta.setdefault(b, [0, 0]); cuenta[b][0] += 1; cuenta[b][1] += (not perdida)
            xb, xf = rb.get(k), rf.get(k)
            if xb and xf:
                n_comparados += 1
                if any(abs((xb.get(q) or 0) - (xf.get(q) or 0)) > 1e-9 for q in ("diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti")):
                    diag_distinto += 1
            dt = datetime.strptime(dts, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            ff = bp.parear(por_vb.get((vol, b), []), dt)
            al = [x for x in ff if bp.es_alerta(x["tipo"])]
            al.sort(key=lambda x: x["source"] != "CONS")
            filas.append({
                "mes": mes, "clave": k, "vol": vol, "b": b, "dt": dts, "inner_km": inner.get(vol),
                "perdida": perdida, "solo_ocr": c.get("alerta_solo_ocr"),
                "mirova": [{q: x.get(q) for q in ("source", "tipo", "vrp_mw", "dist_km", "clasificacion", "fecha_utc", "ultima_actualizacion")} for x in al],
                "B_disp": c.get("disp"), "F_disp": f.get("disp"), "F_pc_dist_tabla": f.get("pc_dist"),
                "B": resumen(xb), "F": resumen(xf)})
    print("control de reproduccion (B publica, F conserva):", cuenta, "| esperado VIIRS375 [988, 946], VIIRS750 [155, 151]")
    print("pasadas con mu/sd distintos entre B y F:", diag_distinto, "de", n_comparados)
    Path(a.out).write_text(json.dumps(filas, ensure_ascii=False, indent=0), encoding="utf-8")
    print("filas:", len(filas), "| perdidas:", sum(r["perdida"] for r in filas))


if __name__ == "__main__":
    main()
