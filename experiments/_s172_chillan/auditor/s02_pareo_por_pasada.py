# -*- coding: utf-8 -*-
"""s02 (S172, auditoria Chillan): razon de magnitud POR PASADA contra MIROVA, con el predicado del tablero en node.

POR QUE: el auto-audit divide nuestro maximo de la noche por el maximo de MIROVA de la noche; las dos pasadas pueden ser
distintas (otro satelite, otro cenit, otra hora). Para descomponer el deficit hay que parear la MISMA pasada: misma
plataforma y sensor, a +-TOL_S (banco_paridad, 120 s). Asi la razon compara dos lecturas del mismo granulo.

"Publica" = predicado del tablero ejecutado con node (banco_paridad.cargar_nuestros); la magnitud publicada es `disp`
(mirovaEqVrpDisplay con USE_F5_CORE = true, o sea f5_core en VIIRS 375 con fallback a pc.vrp_mw, y pc.vrp_mw en MODIS
y VIIRS 750). Se compara ademas con la lectura directa del JSON (f5_core_vrp_mw o pc.vrp_mw) como control.

Alerta de MIROVA = fila ALERTA de la union CONS+OCR (referencia_mirova_unificada) con D-9 en modo SN. VRP de MIROVA de la
pasada: el de la fila CONS si hay, si no el OCR (variante "cons_sola": solo filas CONS).

P1 (si lo medido estuviera roto, lo veria): control positivo, se multiplica `disp` por 2 en una copia y la mediana debe
    doblarse; control de pareo: la diferencia de plataforma entre nuestra pasada y la fila de MIROVA (deben coincidir).
P2 (instrumento muerto): control negativo, pareo con la referencia corrida +1 dia: los pares deben caer casi a 0.
Uso: python -B s02_pareo_por_pasada.py <raiz copia> <inicio> <fin> <salida_prefijo>
"""
import collections, csv, json, math, os, statistics, sys
from datetime import timedelta

ROOT, INI, FIN, PRE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402

VOL = "NevadosDeChillan"
bp.VOLS = [VOL]
ventana = (INI, FIN)
coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
ident = bp.control_identidad_predicado()
filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
recs = bp.cargar_nuestros(coords, inner, ventana)

# campos extra del JSON, por (sensor, datetime)
d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", VOL + ".json"), encoding="utf-8"))
extra = {}


def hav(a, b, c, e):
    R, r = 6371.0, math.pi / 180
    x = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((e - b) * r / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


for r in d["records"]:
    pc = r.get("primary_cluster") or {}
    px = r.get("anomaly_pixels") or []
    pos = [p for p in px if (p.get("vrp_mw") or 0) > 0]
    # nucleo F5 (solo para CONTAR pixeles; la magnitud la da node): ancla = pico dentro de inner del centroide
    n_core = None
    if pc.get("centroid_lat") is not None and px:
        cand = [p for p in px if p.get("lat") is not None and hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= inner[VOL]]
        if cand:
            pk = max(cand, key=lambda p: p.get("vrp_mw") or 0)
            core = [p for p in cand if p is pk or hav(p["lat"], p["lon"], pk["lat"], pk["lon"]) <= 0.75 or (p.get("bt_k") or 0) >= 295.0]
            n_core = sum(1 for p in core if (p.get("vrp_mw") or 0) > 0)
    extra[(r.get("sensor"), r.get("datetime_utc"))] = {
        "pc_n": pc.get("n_pixels"), "pc_vrp": pc.get("vrp_mw"), "f5": r.get("f5_core_vrp_mw"),
        "n_all": r.get("n_anomalous_pixels"), "n_list": len(px), "n_pos": len(pos), "n_core_pos": n_core,
        "pc_dist": pc.get("centroid_dist_km"), "t_bg": r.get("t_bg_k"), "t_max": r.get("t_max_k"),
        "single": pc.get("single_pixel_mode"), "fhs": r.get("final_hotspot_source"),
        "proc": r.get("processed_utc"), "sha": (r.get("regimen") or {}).get("codigo_sha"),
        "solz": r.get("solar_zenith_deg")}


def vrp_mirova(fs, cons_sola=False):
    al = [f for f in fs if bp.es_alerta(f["tipo"]) and (f["source"] == "CONS" or not cons_sola)]
    if not al:
        return None, None
    c = [f for f in al if f["source"] == "CONS"]
    f = (c or al)[0]
    return f["vrp_mw"], f


rows = []
for r in recs:
    if r["vol"] != VOL:
        continue
    fs = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
    vm, fm = vrp_mirova(fs)
    vmc, _ = vrp_mirova(fs, cons_sola=True)
    fs_sh = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"] + timedelta(days=1))
    vsh, _ = vrp_mirova(fs_sh)
    e = extra.get((r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), {})
    json_pub = (e.get("f5") if (r["b"] == "VIIRS375" and isinstance(e.get("f5"), (int, float)) and e.get("f5") > 0) else e.get("pc_vrp"))
    rows.append({"dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "noche": r["noche"], "b": r["b"], "sensor": r["sensor"],
                 "z": r["z"], "pub": r["pub"], "disp": r["disp"], "json_pub": json_pub, "dc": r["dc"],
                 "vrp_M": vm, "vrp_M_cons": vmc, "src_M": (fm or {}).get("source"), "dist_M": (fm or {}).get("dist_km"),
                 "sensor_M": (fm or {}).get("sensor_raw"), "fecha_M": (fm or {}).get("fecha_utc"),
                 "vrp_M_shift1d": vsh, "lab": None, **e})

# etiquetas del banco (para contar positivos sin publicar)
bp.etiquetar([r for r in recs if r["vol"] == VOL], por_vb, ns, nv)
labmap = {(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")): r["lab"] for r in recs if r["vol"] == VOL}
for x in rows:
    x["lab"] = labmap.get((x["sensor"], x["dt"]))

with open(PRE + "_pasadas.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


out = {"ventana": ventana, "identidad_predicado": ident, "inner": inner[VOL], "n_filas_ref_nocturnas": n_ref,
       "n_records_nocturnos": len(rows), "por_sensor": {}}
for b in bp.BUCKETS:
    R = [x for x in rows if x["b"] == b]
    pos = [x for x in R if x["vrp_M"] is not None and x["vrp_M"] > 0]
    par = [x for x in pos if x["pub"] == 1 and x["disp"] > 0]
    parc = [x for x in R if x["vrp_M_cons"] and x["pub"] == 1 and x["disp"] > 0]
    sh = [x for x in R if x["vrp_M_shift1d"] and x["pub"] == 1 and x["disp"] > 0]
    # por noche: el par de la pasada con mayor VRP de MIROVA
    noche = collections.defaultdict(list)
    for x in par:
        noche[x["noche"]].append(x)
    rn = [max(v, key=lambda y: y["vrp_M"])["disp"] / max(v, key=lambda y: y["vrp_M"])["vrp_M"] for v in noche.values()]
    out["por_sensor"][b] = {
        "n_pasadas_nocturnas": len(R), "n_pasadas_publicadas": sum(x["pub"] for x in R),
        "n_pasadas_alerta_MIROVA": len(pos), "n_alerta_sin_publicar": len(pos) - len(par),
        "n_pares": len(par), "razon_mediana_por_pasada": med([x["disp"] / x["vrp_M"] for x in par]),
        "n_noches_par": len(rn), "razon_mediana_por_noche": med(rn),
        "cons_sola": {"n_pares": len(parc), "razon_mediana_por_pasada": med([x["disp"] / x["vrp_M_cons"] for x in parc])},
        "control_pos_x2": med([2 * x["disp"] / x["vrp_M"] for x in par]),
        "control_neg_shift1d_n_pares": len(sh),
        "control_json_vs_node_difieren": sum(1 for x in par if x["json_pub"] is None or abs(x["json_pub"] - x["disp"]) > 1e-6),
        # MIROVA no trae plataforma (columna Sensor = MODIS / VIIRS / VIIRS375): el pareo por hora la identifica
        "control_dt_max_s": max([abs((__import__("datetime").datetime.strptime(x["fecha_M"][:19], "%Y-%m-%d %H:%M:%S") - __import__("datetime").datetime.strptime(x["dt"], "%Y-%m-%d %H:%M")).total_seconds()) for x in par], default=None),
    }
json.dump(out, open(PRE + "_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
