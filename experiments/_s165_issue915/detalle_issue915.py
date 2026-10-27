"""S165, issue #915: detalle por pasada y por noche de los items que la vuelta 1 no clasifico.

Solo lectura. Corre el codigo del auto-audit (scripts/auto_audit_weekly.py) de un arbol extraido de
origin/main con `git archive` (por defecto D:/vrp-trabajo/temporales/s165_issue915/main, sha en SHA.txt),
asi que los records y los loaders son los de main, no los del checkout local (A8).

Dos referencias, a eleccion (--cons):
  snapshot : data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv (la que uso el audit del 10-26)
  latest   : latest_consolidado.csv (la copia de hoy, la que sync-mirova-csv refresca cada hora; D-39)
El OCR es siempre el del snapshot (sync-mirova-csv lo refresca ahi).

Parte A: las tres protegidas (Tupungatito V375 09-28 05:18 y 09-29 04:54, PCC V750 10-10 05:54): estado segun
el banco, todas las filas de la referencia del volcan a +-3 h y todos nuestros records a +-3 h.
Parte B: las cinco celdas de magnitud del issue: noche por noche, con la misma regla que evaluar_detector
(max(pub) de la noche / max VRP de alerta de MIROVA de la noche), y los datos de la pasada que da el maximo
de cada lado.

Salida: imprimir; el que llama redirige a <nombre>_salida.txt.
"""
import argparse
import importlib
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="D:/vrp-trabajo/temporales/s165_issue915/main")
ap.add_argument("--cons", choices=["snapshot", "latest"], default="latest")
ap.add_argument("--desde", default="2026-08-27")
ap.add_argument("--hasta", default="2026-10-26")
ap.add_argument("--hoy", default="2026-10-26", help="fecha que el audit usa para ceses de plataforma")
args = ap.parse_args()

ROOT = os.path.abspath(args.root)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)
aw = importlib.import_module("auto_audit_weekly")
import banco_paridad as bp  # noqa: E402
assert os.path.abspath(aw.ROOT) == ROOT, (aw.ROOT, ROOT)
if args.cons == "latest":
    aw.CONS = os.path.join(ROOT, "latest_consolidado.csv")
print(f"arbol: {ROOT}  sha main: {open(os.path.join(ROOT, 'SHA.txt')).read().strip()}")
print(f"consolidado: {aw.CONS}")
print(f"OCR: {aw.OCR}")
print(f"ventana: {args.desde} a {args.hasta}")

win = (args.desde, args.hasta)
hoy = datetime.fromisoformat(args.hoy).date()
frontera = aw.leer_frontera_k()
vigente = aw.detector_vigente(frontera)
print(f"frontera K: {frontera}  vigente: {vigente}")

alertas = aw.alertas_mirova(cons=aw.CONS, ocr=aw.OCR, historico=aw.HISTORICO)
coords = aw._coords_por_volcan()
filas_ref = aw.cargar_filas_referencia()
mir, inst_mir, _ = aw.noches_mirova_con_instante(aw.aplicar_d9(alertas, aw.REGLA_MINIMAS, filas_ref), coords, win)
ceses, _ = aw.leer_ceses()
desde_plat = aw.juzga_desde(ceses, hoy)
mir, _ = aw.partir_por_plataformas(mir, desde_plat)
records_por_volcan, _ = aw.cargar_records()
nuestros = aw.nuestros_por_noche(records_por_volcan, win, frontera)
ours = nuestros["ours"]

# indice de records por (vol, 'YYYY-MM-DD HH:MM', sensor)
idx = {}
for vol, recs in records_por_volcan.items():
    for r in recs:
        idx[(vol, r.get("datetime_utc"), r.get("sensor"))] = r


def fila_rec(r):
    pc = r.get("primary_cluster") or {}
    tm, tb = r.get("t_max_k"), r.get("t_bg_k")
    dt_k = round(tm - tb, 2) if isinstance(tm, (int, float)) and isinstance(tb, (int, float)) else None
    reg = r.get("regimen") or {}
    return (f"{r['datetime_utc']} {r.get('sensor'):<18} clase={r.get('distance_class')} "
            f"fuente={r.get('final_hotspot_source')} fh_dist={r.get('final_hotspot_dist_km')} "
            f"pc_dist={pc.get('centroid_dist_km')} pc_npix={pc.get('n_pixels')} pc_vrp={pc.get('vrp_mw')} "
            f"f5={r.get('f5_core_vrp_mw')} n_anom={r.get('n_anomalous_pixels')} vrp_mw={r.get('vrp_mw')} "
            f"tmax-tbg={dt_k} z={r.get('sensor_zenith_deg')} sha={str(reg.get('codigo_sha'))[:9]}")


# ---------------------------------------------------------------- Parte A
print("\n" + "=" * 100 + "\nPARTE A: alertas protegidas\n" + "=" * 100)
banco = aw.banco_ventana(win)
prot = aw.alertas_protegidas(banco[1], banco[0], win, frontera)
sin_pub = [p for p in prot if p["detector"] == vigente and p["estado"] == "sin_publicar"]
print(f"protegidas en la ventana: {len(prot)}; sin_publicar ({vigente}): {len(sin_pub)}")
for p in sin_pub:
    print("  ", json.dumps(p, ensure_ascii=False))

OBJETIVOS = [("Tupungatito", "VIIRS375", "2026-09-28 05:18"), ("Tupungatito", "VIIRS375", "2026-09-29 04:54"),
             ("PuyehueCordonCaulle", "VIIRS750", "2026-10-10 05:54")]
filas = banco[1]
for vol, b, minuto in OBJETIVOS:
    t0 = datetime.fromisoformat(minuto)
    print("\n" + "-" * 100 + f"\n{vol} {b} {minuto}")
    est = [p for p in prot if (p["volcano"], p["sensor"], p["fecha_utc"]) == (vol, b, minuto)]
    print("  estado banco:", json.dumps(est, ensure_ascii=False) if est else "NO ESTA en la lista de protegidas")
    print("  filas de la referencia (todas las fuentes y tipos) del volcan a +-3 h:")
    for f in filas:
        if f["volcano"] != vol:
            continue
        try:
            tf = datetime.fromisoformat(f["fecha_utc"][:19])
        except ValueError:
            continue
        if abs((tf - t0).total_seconds()) <= 3 * 3600:
            print(f"    {f['fecha_utc']} {f['source']:<4} {f.get('origen'):<10} {f.get('sensor_raw'):<22} "
                  f"tipo={f.get('tipo')} vrp={f.get('vrp_mw')} dist={f.get('dist_km', f.get('distancia_km'))} "
                  f"protegida={aw.cm.alerta_protegida(f)}")
    print("  nuestros records del volcan a +-3 h (todos los sensores; pub = predicado del tablero):")
    pubs = {(r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"]): r.get("pub") for r in banco[0]}
    for (v2, dt, s), r in sorted(idx.items(), key=lambda kv: kv[0][1] or ""):
        if v2 != vol or not dt:
            continue
        if abs((datetime.fromisoformat(dt) - t0).total_seconds()) <= 3 * 3600:
            print(f"    pub={pubs.get((v2, dt, s))!s:<5} {fila_rec(r)}")

# ---------------------------------------------------------------- Parte B
print("\n" + "=" * 100 + "\nPARTE B: magnitud publicada por noche (misma regla que evaluar_detector)\n" + "=" * 100)
CELDAS = ["NevadosDeChillan|MODIS", "NevadosDeChillan|VIIRS375", "NevadosDeChillan|VIIRS750",
          "PuyehueCordonCaulle|VIIRS750", "Tupungatito|VIIRS375"]
# fila de MIROVA que da el maximo: la alerta de esa hora (inst_mir) en la referencia unificada
ref_por_min = defaultdict(list)
for f in filas:
    ref_por_min[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)

resumen = {}
for celda in CELDAS:
    vol, s = celda.split("|")
    noches = []
    for (v, s2, fecha), mvrp in sorted(mir.items()):
        if (v, s2) != (vol, s) or aw.detector_de_noche(fecha, frontera) != vigente:
            continue
        o = ours.get((v, s2, fecha))
        if not (o and o["dash"]) or mvrp <= 0:
            continue
        i = max(range(len(o["pub"])), key=lambda j: o["pub"][j])
        dt_n, z_n = o["dt_pub"][i], o["z_pub"][i]
        im = inst_mir.get((v, s2, fecha))
        fm = ref_por_min.get((v, s2, (im or "")[:16]), [])
        fuentes = sorted({f["source"] for f in fm if bp.es_alerta(f.get("tipo"))} or {f["source"] for f in fm})
        dist_m = [f.get("dist_km") for f in fm]
        # nuestro record de la pasada que publica el maximo
        cand = [r for (v3, dt3, s3), r in idx.items() if v3 == v and dt3 == dt_n and aw.our_bucket(s3) == s]
        r = cand[0] if cand else {}
        pc = r.get("primary_cluster") or {}
        tm, tb = r.get("t_max_k"), r.get("t_bg_k")
        noches.append({
            "fecha": fecha, "mirova_mw": round(mvrp, 3), "mirova_dt": (im or "")[:16], "mirova_fuente": "+".join(fuentes),
            "mirova_dist": dist_m, "nuestra_mw": round(o["pub"][i], 3), "nuestra_dt": dt_n,
            "misma_pasada": aw._misma_pasada(dt_n, im), "z": z_n, "npix_pc": pc.get("n_pixels"),
            "npix_max_noche": max(o["npix"]) if o["npix"] else 0, "pc_dist": pc.get("centroid_dist_km"),
            "fuente_hotspot": r.get("final_hotspot_source"),
            "tmax_tbg": round(tm - tb, 2) if isinstance(tm, (int, float)) and isinstance(tb, (int, float)) else None,
            "n_pub_noche": len(o["pub"]), "razon": round(o["pub"][i] / mvrp, 3)})
    print("\n" + "-" * 100 + f"\n{celda}: n_noches={len(noches)}")
    hdr = ("fecha       MIROVA_mw  hora_M            fuente  dist_M        nuestra_mw hora_N            misma  "
           "z      npix  pc_dist  fuenteHS     dT     npub razon")
    print(hdr)
    for n in noches:
        print(f"{n['fecha']}  {n['mirova_mw']:>7}   {n['mirova_dt']:<17} {n['mirova_fuente']:<7} "
              f"{str(n['mirova_dist']):<13} {n['nuestra_mw']:>7}   {n['nuestra_dt']:<17} {str(n['misma_pasada']):<6} "
              f"{str(n['z']):<6} {str(n['npix_pc']):<5} {str(n['pc_dist']):<8} {str(n['fuente_hotspot']):<12} "
              f"{str(n['tmax_tbg']):<6} {n['n_pub_noche']:<4} {n['razon']}")
    rz = [n["razon"] for n in noches]
    if not rz:
        continue
    med = statistics.median(rz)
    loo = [statistics.median(rz[:k] + rz[k + 1:]) for k in range(len(rz))] if len(rz) > 1 else [med]
    def sub(pred):
        x = [n["razon"] for n in noches if pred(n)]
        return (len(x), round(statistics.median(x), 3) if x else None)
    res = {
        "n": len(rz), "mediana": round(med, 3), "loo_min": round(min(loo), 3), "loo_max": round(max(loo), 3),
        "frac_bajo_0_7": round(sum(x < 0.7 for x in rz) / len(rz), 3),
        "solo_tabla_CONS": sub(lambda n: n["mirova_fuente"].startswith("CONS")),
        "solo_OCR": sub(lambda n: n["mirova_fuente"] == "OCR"),
        "misma_pasada": sub(lambda n: n["misma_pasada"] is True),
        "otra_pasada": sub(lambda n: n["misma_pasada"] is False),
        "z<30": sub(lambda n: n["z"] is not None and n["z"] < 30),
        "z>=30": sub(lambda n: n["z"] is not None and n["z"] >= 30),
        "npix_pc<=2": sub(lambda n: (n["npix_pc"] or 0) <= 2),
        "npix_pc>=3": sub(lambda n: (n["npix_pc"] or 0) >= 3),
        "mirova<1MW": sub(lambda n: n["mirova_mw"] < 1),
        "mirova>=1MW": sub(lambda n: n["mirova_mw"] >= 1),
        "misma_pasada_y_CONS": sub(lambda n: n["misma_pasada"] is True and n["mirova_fuente"].startswith("CONS")),
    }
    resumen[celda] = res
    for k, v in res.items():
        print(f"  {k}: {v}")

print("\nRESUMEN_JSON " + json.dumps(resumen, ensure_ascii=False))
