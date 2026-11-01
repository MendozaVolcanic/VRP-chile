# -*- coding: utf-8 -*-
"""F0b S160, verificador de F4-H2 (cota de K1) y F4-H3 (minimo de cumbre 0,003), sobre los DATOS de SHA_MAIN.

Diferencias con el script de S158 (experiments/_s158_audit/f4/04_cota_k1_y_sustrato_minimos.py):
  * datos y codigo de la instantanea D:\\vrp-trabajo\\temporales\\s160_audit\\main (d516b9d8c), no del worktree;
  * tres referencias: (o) la de S158 (cargar_referencia_unificada por defecto), (t) tabla sola = latest_consolidado.csv,
    (c) combinado = latest_consolidado.csv + OCR del snapshot; sin capas historico/respaldo en (t) y (c);
  * H3 por otro camino: tambien el dETI de cumbre (Test 3 tiene su propio minimo 0,003) y por estrato de etiqueta;
  * K1 en NUESTRA produccion: el camino B (NTI > K1) no entra a la deteccion (el primer pase la reemplaza), pero
    n_nti_path decide si se activa el tope D9 de 5 MW (process_viirs.py:1439-1446). Contamos records donde subir K1
    a -0,7 apagaria el camino B (nti_max <= -0,7 con n_nti_path > 0) y ademas el tope podria actuar (t_bg < 270 K).

Pregunta 1 (si lo medido estuviera roto, lo veria?): M1 cuenta negativos sobre K1 candidatos; si nti_max no fuera
comparable, el control positivo (positivos sobre -0,7 > 0) lo distinguiria solo en parte: el instrumento NO tiene poder
para separar -0,8 de -0,7 con negativos (ver salida). M2: control positivo = la fraccion bajo umbrales cercanos a la
mediana (debe dar ~0,5).
Pregunta 2 (instrumento muerto?): n=0 se imprime SIN DATO; los conteos de nulos de cada campo se imprimen.
"""
import sys, io, os, json, collections
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP)); sys.path.insert(0, str(SNAP / "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
import referencia_mirova_unificada as rmu
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
assert str(bp.DATA).startswith(str(SNAP)), bp.DATA

VENTANA = ("2026-03-01", "2026-10-21")
coords = _coords_por_volcan()
TABLA = SNAP / "latest_consolidado.csv"
OCR = SNAP / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"

refs = {
    "o_S158_por_defecto": rmu.cargar_referencia_unificada(),
    "c_combinado": rmu.cargar_referencia_unificada(TABLA, OCR, respaldo_path=None, historico_path=None),
}
refs["t_tabla_sola"] = [f for f in refs["c_combinado"] if f["source"] == "CONS"]
print("filas por referencia:", {k: len(v) for k, v in refs.items()})

base = []
for vol in bp.VOLS:
    d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (VENTANA[0] <= r.get("datetime_utc", "")[:10] <= VENTANA[1]):
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        lat, lon = coords[vol]
        if es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        pc = r.get("primary_cluster") or {}
        base.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                     "nti_max": r.get("diag_nti_max"), "mu": r.get("diag_mu_dnti"), "sd": r.get("diag_sd_dnti"),
                     "mu_e": r.get("diag_mu_deti"), "sd_e": r.get("diag_sd_deti"),
                     "n_nti": r.get("diag_n_nti_path", r.get("n_nti_path")), "t_bg": r.get("t_bg_k"),
                     "pc_vrp": pc.get("vrp_mw"), "d9": pc.get("d9_capped"),
                     "sha": (r.get("regimen") or {}).get("codigo_sha", "")[:9]})
print(f"records nocturnos en ventana {VENTANA}: {len(base)}")
print("regimen (codigo_sha) top:", collections.Counter(r["sha"] for r in base).most_common(4))

K1_CAND = [-0.87, -0.8, -0.7, -0.6]
out = {}
for nombre, filas in refs.items():
    recs = [dict(r) for r in base]
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    print(f"\n######## referencia {nombre}: filas nocturnas {n_ref}")
    print("etiquetas:", dict(sorted(collections.Counter((r['b'], r['lab']) for r in recs).items())))
    o = out.setdefault(nombre, {})
    print("--- M1 cota K1 (max nti_max en negativos limpios) ---")
    for b in bp.BUCKETS:
        for lab in ("neg_limpio", "pos"):
            x = np.array([r["nti_max"] for r in recs if r["b"] == b and r["lab"] == lab and r["nti_max"] is not None], float)
            nnull = sum(1 for r in recs if r["b"] == b and r["lab"] == lab and r["nti_max"] is None)
            if len(x) == 0:
                print(f"{b} {lab}: SIN DATO (n=0, nulos {nnull})"); continue
            cnt = {k: int((x > k).sum()) for k in K1_CAND}
            print(f"{b:9s} {lab:10s} n={len(x):5d} nulos={nnull:3d} max={x.max():.3f} p99={np.percentile(x,99):.3f} "
                  f"| n(>k): " + " ".join(f"{k}:{cnt[k]}" for k in K1_CAND))
            o[f"M1|{b}|{lab}"] = {"n": int(len(x)), "nulos": nnull, "max": float(x.max()), "n_sobre": {str(k): cnt[k] for k in K1_CAND}}
    print("--- M2 minimo de cumbre 0,003: fraccion con mu+5sd < 0,003 (dNTI, Test 2) y (dETI, Test 3) ---")
    for b in bp.BUCKETS:
        for lab in ("neg_limpio", "pos", "sin_info", "todas"):
            g = [r for r in recs if r["b"] == b and (lab == "todas" or r["lab"] == lab)]
            gd = [r for r in g if r["mu"] is not None and r["sd"] is not None]
            ge = [r for r in g if r["mu_e"] is not None and r["sd_e"] is not None]
            if not gd:
                print(f"{b} {lab}: SIN DATO dNTI (n={len(g)})"); continue
            t5 = np.array([r["mu"] + 5 * r["sd"] for r in gd])
            te5 = np.array([r["mu_e"] + 5 * r["sd_e"] for r in ge]) if ge else np.array([])
            med = float(np.median(t5))
            ctrl = float((t5 < med).mean())
            print(f"{b:9s} {lab:10s} n={len(gd):5d} nulos={len(g)-len(gd):4d} | dNTI mu+5sd<0,003: {int((t5<0.003).sum())} ({(t5<0.003).mean():.4f}) "
                  f"mediana {med:.4f} min {t5.min():.4f} | dETI mu+5sd<0,003: {int((te5<0.003).sum()) if len(te5) else 'SIN DATO'} "
                  f"({(te5<0.003).mean() if len(te5) else float('nan'):.4f}) mediana {np.median(te5) if len(te5) else float('nan'):.4f} "
                  f"min {te5.min() if len(te5) else float('nan'):.4f} | control (<mediana) {ctrl:.3f}")
            o[f"M2|{b}|{lab}"] = {"n": len(gd), "dnti_lt": int((t5 < 0.003).sum()), "deti_lt": int((te5 < 0.003).sum()) if len(te5) else None,
                                 "n_deti": len(te5), "mediana_dnti": med}

# --- K1 en NUESTRA produccion (independiente de la referencia) ---
print("\n######## K1 en produccion: camino B (n_nti_path) y tope D9")
for b in bp.BUCKETS:
    g = [r for r in base if r["b"] == b]
    nn = [r for r in g if r["n_nti"] is not None]
    con_b = [r for r in nn if r["n_nti"] > 0]
    apagaria = [r for r in con_b if r["nti_max"] is not None and r["nti_max"] <= -0.7]
    tope_posible = [r for r in apagaria if r["t_bg"] is not None and r["t_bg"] < 270.0]
    tope_y_mas5 = [r for r in tope_posible if r["pc_vrp"] is not None and r["pc_vrp"] > 5.0]
    # control positivo: records hoy topados (d9) deben tener n_nti_path == 0
    d9 = [r for r in g if r["d9"]]
    d9_con_b = [r for r in d9 if (r["n_nti"] or 0) > 0]
    print(f"{b:9s} records {len(g)} (n_nti_path nulo {len(g)-len(nn)}) | con camino B>0: {len(con_b)} | "
          f"de esos con nti_max<=-0,7 (K1=-0,7 los apagaria): {len(apagaria)} | y t_bg<270: {len(tope_posible)} | "
          f"y pc.vrp>5 MW (el tope cambiaria la magnitud): {len(tope_y_mas5)} | control: topados D9 {len(d9)}, de ellos con camino B>0 {len(d9_con_b)}")
    out[f"prod|{b}"] = {"records": len(g), "con_b": len(con_b), "apagaria": len(apagaria), "tope_posible": len(tope_posible),
                        "tope_y_mas5": len(tope_y_mas5), "d9": len(d9), "d9_con_b": len(d9_con_b),
                        "ejemplos_tope_y_mas5": [(r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["nti_max"], r["t_bg"], r["pc_vrp"]) for r in tope_y_mas5[:10]]}
    for e in out[f"prod|{b}"]["ejemplos_tope_y_mas5"]:
        print("    ", e)
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
