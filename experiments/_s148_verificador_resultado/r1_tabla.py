# -*- coding: utf-8 -*-
"""Verificador S148 del RESULTADO: arma una tabla por pasada con los dos brazos.
pub/etiqueta del evaluador (node) Y pub/etiqueta del port independiente (verif_base del verificador
anterior, extraido de la rama con git show). Solo lee. Escribe tabla.json en esta carpeta."""
import json, sys, subprocess, importlib.util
from pathlib import Path
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
P = RAIZ / "experiments/_s147_lectura/experiments/_s146_ab_sin_test1/salidas/prelim_s148"
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"

src = subprocess.run(["git", "show", "origin/s148-resultado-conectiva:experiments/_s148_verificador_conectiva/verif_base.py"],
                     capture_output=True, cwd=RAIZ).stdout.decode("utf-8")
(AQUI / "_verif_base_copia.py").write_text(src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("vb", AQUI / "_verif_base_copia.py"); vb = importlib.util.module_from_spec(spec); spec.loader.exec_module(vb)

par = json.loads(ev.PARAMETROS.read_text(encoding="utf-8")); ventana = tuple(par["ventana"])
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(ev.CONGELADO / "registro_vrp_consolidado.csv", ev.CONGELADO / "registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
filas_vb = vb.cargar_ref(ev.CONGELADO)
tabla = {}
for arm in (B, F):
    recs = ev.cargar_brazo(P / arm, coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
    crudo, dup = vb.cargar_brazo(P / arm)
    lab2, _ = vb.etiquetar(crudo, filas_vb, ventana[0], ventana[1])
    print(arm, "recs evaluador", len(recs), "crudos", len(crudo), "dup", dup)
    for r in recs:
        k = ev.clave(r); raw = crudo[k]
        tabla.setdefault("|".join(k), {})[arm] = {
            "lab": r["lab"], "lab2": lab2.get(k), "pub": int(bool(r["pub"])), "pub2": raw["_pub"],
            "disp": r["disp"], "disp2": raw["_disp"], "vrp_ref": r.get("vrp_ref"),
            "pc_lat": r["pc_lat"], "pc_lon": r["pc_lon"], "pc_dist": r["pc_dist"], "pc_vrp": r["pc_vrp"],
            "z": r["z"], "t_bg": raw.get("t_bg_k"), "granule": r["granule"], "pv": raw.get("product_version"),
            "fuente": r["fuente"], "n_px": r["n_px"], "proc": raw.get("processed_utc"),
            "n_fp": raw.get("diag_n_first_pass_pixels"), "n_sp": raw.get("diag_n_second_pass_recapture"),
            "pc_npx": (raw.get("primary_cluster") or {}).get("n_pixels"), "sensor": raw.get("sensor"),
            "t_max": raw.get("t_max_k")}
(AQUI / "tabla.json").write_text(json.dumps(tabla, ensure_ascii=False), encoding="utf-8")
print("claves", len(tabla))
