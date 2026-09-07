"""S135 paso 0 — tabla persistido vs probe (régimen viejo vs código de hoy) + cota A93.

cota_sep_km = |d_pico_GVP − d_mirova| : un radio no es una posición; la diferencia de dos
radios es una COTA INFERIOR de la distancia entre los dos puntos (A93). Si es > ~1 km, el
pico nuestro y el hotspot de MIROVA no son el mismo objeto aunque la noche coincida.
Distancia MIROVA: desde su centro de grilla = `mirova_center_lat/lon` de volcanoes.yaml
(S115: re-anclar SIEMPRE al mismo origen para comparar distancias), cuantizada a la celda
(D15). `mirova_center` coincide con el centro del TIF de MIROVA a ±200 m (AUDIT_S128.md:188-210);
presupuesto de error de la cota ≈ 0,55 km (semidiagonal de la celda 0,27 + residuo por sensor
0,18-0,31). Por eso d_pico se mide acá desde `mirova_center`, NO desde el vent ni desde el
punto del catálogo (en Tupungatito el cráter queda a 2,9 km del catálogo y a 4,9 del
mirova_center; MIROVA lo reporta a 4,9-5,2: el origen correcto es mirova_center, que los 11
Tier A tienen). Si un volcán no lo tuviera, la cota se deja vacía en vez de inventar un origen.
"""
import io, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analisis import haversine_km
import yaml
_VOLS = {v["name"]: v for v in yaml.safe_load(open(Path(__file__).resolve().parents[2] / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(__file__).parent / "out_paso0"
filas = []
for p in sorted(D.glob("*.json")):
    if p.name.startswith("criterio"):
        continue
    f = json.loads(p.read_text(encoding="utf-8"))
    if f.get("clase") not in ("cat_b", "control_fp0"):
        continue
    r = f["resumen"]; kp = r.get("keep_peak"); per = f.get("persistido") or {}; m = f.get("mirova") or {}
    rec = f["record"]
    d_pico = kp["dist_vent_km"] if kp else None
    vc = _VOLS.get(f["volcan"], {})
    mc = (vc.get("mirova_center_lat"), vc.get("mirova_center_lon"))
    d_pico_gvp = (round(float(haversine_km(mc[0], mc[1], kp["lat"], kp["lon"])), 3)
                  if (kp and mc[0] is not None) else None)
    cota = round(abs(d_pico_gvp - m["dist_km"]), 2) if (d_pico_gvp is not None and m.get("dist_km") is not None) else None
    filas.append({
        "pasada": f"{f['volcan']} {f['pasada_utc']} {f['sensor']}", "clase": f["clase"],
        "persistido_fp": per.get("n_first_pass"), "persistido_pc_dist": per.get("pc_dist_km"), "persistido_t_bg": per.get("t_bg_k"),
        "hoy_source": rec.get("final_hotspot_source"), "hoy_d_final": rec.get("final_hotspot_dist_km"), "hoy_fp": rec.get("diag_n_first_pass_pixels"), "hoy_t_bg": rec.get("t_bg_k"),
        "crater_en_mask": r["test1"]["n_mask_a_menos_0_5km"], "rango_crater": r["test1"]["rango_bt_crater_en_mask"],
        "pico_km": d_pico, "pico_km_mirova_center": d_pico_gvp, "pico_bt_vs_bg": (kp["bt_menos_t_bg_global_k"] if kp else None),
        "inter_sin_pico": (r.get("interseccion_sin_pico") or {}).get("n"),
        "mirova_vrp": m.get("vrp_mw"), "mirova_dist": m.get("dist_km"), "cota_sep_km": cota,
        "i04_disco_vs_bg": (r.get("nube") or {}).get("i04_disco_menos_t_bg_k"),
    })
(Path(__file__).parent / "tabla_paso0.json").write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
print("| pasada | clase | fp persistido→hoy | t_bg persistido→hoy | pc_dist persist. | hoy source d_final | cráter en mask (rango) | pico km vent / mirova_center (ΔBT) | ∩ sin pico | MIROVA MW @ km (su centro) | cota sep |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for x in filas:
    print(f"| {x['pasada']} | {x['clase']} | {x['persistido_fp']}→{x['hoy_fp']} | {x['persistido_t_bg']}→{x['hoy_t_bg']} | {x['persistido_pc_dist']} | {x['hoy_source']} {x['hoy_d_final']} | {x['crater_en_mask']} ({x['rango_crater']}) | {x['pico_km']} / {x['pico_km_mirova_center']} ({x['pico_bt_vs_bg']}) | {x['inter_sin_pico']} | {x['mirova_vrp']} @ {x['mirova_dist']} | {x['cota_sep_km']} |")
n_fp_per = sum(1 for x in filas if x['persistido_fp'] == 0); n_fp_hoy = sum(1 for x in filas if x['hoy_fp'] == 0)
print(f"\nfirst pass vacío: persistido {n_fp_per}/12 → hoy {n_fp_hoy}/12 · t_bg mediana persistido→hoy: "
      f"{sorted(x['persistido_t_bg'] for x in filas)[6]} → {sorted(x['hoy_t_bg'] for x in filas)[6]}")
