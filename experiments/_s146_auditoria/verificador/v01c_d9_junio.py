# -*- coding: utf-8 -*-
"""V-01c: la misma poblacion sobre el corpus TAL COMO ESTABA el 2026-06-19 (git show, solo lectura) y la referencia de ese mismo commit.
(1) roto? imprime n de records por volcan leidos del commit. (2) muerto? compara con la medicion de hoy (216): si el commit no cargara daria 0."""
import io, sys, json, subprocess, csv, datetime as dt
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from vlib import VOLS, ROOT, bucket, bucket_ref, ALIAS
C = "1d6b5b932b9323bc2a7bedcd93574ace8d4bdaee"
def show(p): return subprocess.run(["git", "-C", ROOT, "show", f"{C}:{p}"], capture_output=True).stdout.decode("utf-8", "replace")
ref = []
for p in ("latest_consolidado.csv", "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
    for row in csv.DictReader(io.StringIO(show(p))):
        ref.append((ALIAS.get(row["Volcan"].strip(), row["Volcan"].strip()), row["Fecha_Satelite_UTC"], bucket_ref(row["Sensor"]), row["Tipo_Registro"].strip()))
print("ref del commit:", len(ref), Counter(x[3] for x in ref), "max", max(x[1] for x in ref))
for w in (("2026-05-01", "2026-06-18"), ("2026-01-01", "2026-06-18")):
    su = []; far = []; ntot = 0
    for v in VOLS:
        rs = json.loads(show(f"data/mirova_equivalent/{v}.json"))["records"]; ntot += len(rs)
        for r in rs:
            f = r["datetime_utc"][:10]
            if not (w[0] <= f <= w[1]): continue
            pc = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            d = r.get("diag_n_dnti_ctx_path") or 0; o = sum(r.get(k) or 0 for k in ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
            if pc > 0 and r.get("t_bg_k") is not None and r["t_bg_k"] < 262 and d > o:
                (su if r.get("distance_class") == "summit" else far).append((v, r["datetime_utc"], bucket(r["sensor"]), pc))
    n = len(su)
    print("ventana", w, "records totales", ntot, "| far", len(far), "far pc>5:", sum(1 for x in far if x[3] > 5), "| summit", n, Counter(x[0] for x in su).most_common(4))
    def conf(tipos, sens):
        K = {(a, b[:10], c) if sens else (a, b[:10]) for a, b, c, t in ref if tipos is None or t in tipos}
        return sum(1 for v, d0, b, _ in su if ((v, d0[:10], b) if sens else (v, d0[:10])) in K)
    for nom, tp in (("ALERTA", {"ALERTA_TERMICA"}), ("ALERTA+OCR", {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR"}), ("+FALSO_POSITIVO", {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR", "FALSO_POSITIVO", "FALSO_POSITIVO_OCR"}), ("cualquier fila incl. RUTINA", None)):
        for s in (True, False):
            k = conf(tp, s); print(f"   {nom:28s} misma fecha, mismo_sensor={s}: {k}/{n} = {100*k/n:.1f}%" if n else "SIN DATO")
