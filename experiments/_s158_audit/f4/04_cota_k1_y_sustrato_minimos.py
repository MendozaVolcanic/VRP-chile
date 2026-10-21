# -*- coding: utf-8 -*-
"""F4 S158: dos mediciones contra la referencia NRT de MIROVA (snapshot del scraper), por sensor.

M1. COTA INFERIOR de K1 por sensor desde los negativos limpios. Física: el Test 1 de MIROVA es incondicional
    (NTI > K1 => alerta directa, H:245), así que si MIROVA miró una pasada y no vio nada, ningún píxel suyo tenía
    NTI > K1. Nuestro `nti_max` (máximo del NTI sobre el ROI de detección, barrido nativo) en esas pasadas da una
    cota: K1 >= max(nti_max sobre negativos), con el matiz de que el remuestreo de MIROVA suaviza el pico (su
    máximo es <= al nuestro), así que la cota es conservadora HACIA ARRIBA (puede exigir más de lo que el dato
    de MIROVA exige).
    Pregunta 1: si K1_375 fuera -0,8 y hubiera negativos con nti_max en (-0,8, -0,7], esta medición los cuenta.
    Pregunta 2: si `nti_max` no se persistiera, n=0 => SIN DATO, no cero.
    CONTROL POSITIVO (instrumento): VIIRS 750, donde K1 = -0,7 está en el código. La fracción de negativos
    limpios con nti_max > -0,7 debe ser ~0; si no lo es, nuestro nti_max no es comparable con el NTI de MIROVA
    y la cota NO vale para ningún sensor.
M2. SUSTRATO de los mínimos fijos: en cuántas pasadas la rama estadística mu + N*sigma queda por DEBAJO del mínimo
    fijo (ahí es donde el número trasladado decide algo). Con los diag_mu_dnti / diag_sd_dnti del primer pase
    (nuestros: dNTI de 8 vecinos, sigma sobre la caja nativa; matiz de escala 9/8 y D17).
Ventana: desde 2026-03-01 (A119) hasta hoy. Referencia: snapshot del repo (sin red). Etiquetas de banco_paridad.
"""
import sys, io, json, collections, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada

VENTANA = ("2026-03-01", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
coords = _coords_por_volcan()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")

recs = []
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
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "z": r.get("sensor_zenith_deg"),
                     "nti_max": r.get("diag_nti_max"), "mu": r.get("diag_mu_dnti"), "sd": r.get("diag_sd_dnti"),
                     "mu_e": r.get("diag_mu_deti"), "sd_e": r.get("diag_sd_deti"),
                     "sha": (r.get("regimen") or {}).get("codigo_sha")})
bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
print(f"ventana {VENTANA} | filas ref nocturnas {n_ref} | records nocturnos {len(recs)}")
print("etiquetas:", dict(collections.Counter((r['b'], r['lab']) for r in recs)))

K1_CAND = [-0.8, -0.7, -0.6, -0.5]
salida = {"ventana": VENTANA, "M1": {}, "M2": {}}
print("\n=== M1: cota inferior de K1 desde negativos limpios (nti_max = max NTI en el ROI nativo) ===")
for b in bp.BUCKETS:
    for lab in ("neg_limpio", "pos"):
        x = np.array([r["nti_max"] for r in recs if r["b"] == b and r["lab"] == lab and r["nti_max"] is not None], float)
        n_sin = sum(1 for r in recs if r["b"] == b and r["lab"] == lab and r["nti_max"] is None)
        if len(x) == 0:
            print(f"{b} {lab}: SIN DATO (n=0, sin nti_max={n_sin})"); continue
        fr = {k: float((x > k).mean()) for k in K1_CAND}
        cnt = {k: int((x > k).sum()) for k in K1_CAND}
        print(f"{b:9s} {lab:10s} n={len(x):5d} (sin nti_max {n_sin}) max={x.max():.3f} p99={np.percentile(x,99):.3f} "
              f"p95={np.percentile(x,95):.3f} mediana={np.median(x):.3f} | n(>K1): " +
              " ".join(f">{k}:{cnt[k]}({fr[k]:.3f})" for k in K1_CAND))
        salida["M1"][f"{b}|{lab}"] = {"n": int(len(x)), "sin_nti_max": n_sin, "max": float(x.max()),
                                      "p99": float(np.percentile(x, 99)), "n_sobre": {str(k): cnt[k] for k in K1_CAND}}
    # por volcán, negativos con nti_max > -0.7 (para ver si es un volcán o todos)
    pv = collections.Counter(r["vol"] for r in recs if r["b"] == b and r["lab"] == "neg_limpio"
                             and r["nti_max"] is not None and r["nti_max"] > -0.7)
    tot = collections.Counter(r["vol"] for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and r["nti_max"] is not None)
    print(f"   negativos con nti_max > -0.7 por volcán: " + ", ".join(f"{v}:{pv[v]}/{tot[v]}" for v in tot if pv[v]))
    salida["M1"][f"{b}|neg_por_volcan_sobre_-0.7"] = {v: [pv[v], tot[v]] for v in tot}

print("\n=== M2: sustrato de los mínimos fijos (primer pase, dNTI de 8 vecinos, sigma de la caja nativa) ===")
for b in bp.BUCKETS:
    g = [r for r in recs if r["b"] == b and r["lab"] in ("neg_limpio", "pos") and r["mu"] is not None and r["sd"] is not None]
    if not g:
        print(f"{b}: SIN DATO"); continue
    mu = np.array([r["mu"] for r in g]); sd = np.array([r["sd"] for r in g])
    t10 = mu + 10 * sd; t5 = mu + 5 * sd
    mue = np.array([r["mu_e"] for r in g if r["mu_e"] is not None]); sde = np.array([r["sd_e"] for r in g if r["sd_e"] is not None])
    te10 = mue + 10 * sde if len(mue) else np.array([])
    res = {"n": len(g), "fuera_dnti_10s_lt_0.02": float((t10 < 0.02).mean()), "fuera_dnti_10s_lt_0.01": float((t10 < 0.01).mean()),
           "cumbre_dnti_5s_lt_0.003": float((t5 < 0.003).mean()), "mediana_mu+10s": float(np.median(t10)), "mediana_mu+5s": float(np.median(t5)),
           "fuera_deti_10s_lt_0.01": float((te10 < 0.01).mean()) if len(te10) else None, "n_deti": int(len(te10))}
    salida["M2"][b] = res
    print(f"{b:9s} n={len(g)} | fuera: mu+10sd<0.02 en {res['fuera_dnti_10s_lt_0.02']:.3f}, <0.01 en {res['fuera_dnti_10s_lt_0.01']:.3f} "
          f"(mediana mu+10sd={res['mediana_mu+10s']:.4f}) | cumbre: mu+5sd<0.003 en {res['cumbre_dnti_5s_lt_0.003']:.3f} "
          f"(mediana {res['mediana_mu+5s']:.4f}) | dETI fuera: mu+10sd<0.01 en {res['fuera_deti_10s_lt_0.01']} (n {res['n_deti']})")
Path(__file__).with_suffix(".json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
