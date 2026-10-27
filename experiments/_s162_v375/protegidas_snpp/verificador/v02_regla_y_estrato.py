# -*- coding: utf-8 -*-
"""VP162 verificador, v02: regla de #903 importada de una extraccion fresca de 719e9c32e (git archive, no la copia
del informe), aplicada a las 6; conteo del estrato 234/128; plataforma de cada pasada resuelta con el record propio.

Pregunta 1: si la regla clasificara mal (p. ej. no viera el hito), las 6 saldrian de crater, porque sus distancias
(0,81 a 5,68 km) caen todas dentro del inner (5 o 7 km): lo comprueba la misma corrida con plataforma NOAA-20.
Pregunta 2: si la regla estuviera muerta (siempre False), el control positivo (protegidas de la tabla dentro del
radio) daria 0 de cráter. Ventana: toda la referencia congelada en la rama medida (2026-01-10 al 2026-10-18).
"""
import io, json, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
EXT = Path(sys.argv[1])          # extraccion de 719e9c32e
sys.path.insert(0, str(EXT))
import scripts.clase_mirova as cm
import scripts.referencia_mirova_unificada as ru
print("modulo:", cm.__file__, "HITO_OCR_SNPP", cm.HITO_OCR_SNPP, "VENTANA_S", cm.VENTANA_S)
SNAP = R/"data/mirova_reference/mirova_v1_snapshot"
ref = ru.cargar_referencia_unificada(SNAP/"registro_vrp_consolidado.csv", SNAP/"registro_vrp_ocr.csv",
                                     SNAP/"registro_vrp_consolidado_respaldo_20260408.csv",
                                     R/"data/mirova_reference/union_historica/consolidado_filas_perdidas.csv")
print("filas:", len(ref), "rango", min(f["fecha_utc"] for f in ref), max(f["fecha_utc"] for f in ref))
import yaml
vy = yaml.safe_load(open(R/"volcanoes.yaml", encoding="utf-8"))
vl = vy["volcanoes"] if isinstance(vy, dict) and "volcanoes" in vy else vy
inner = {}
for v in vl:
    nm = v.get("name") or v.get("id"); key = (v.get("json_name") or nm)
    inner[str(nm).replace(" ", "").replace("-", "")] = v.get("inner_radius_km")
def rad(vol):
    k = vol.replace(" ", "").replace("-", "")
    for kk, val in inner.items():
        if kk.lower() == k.lower(): return val
    return None
# records propios para plataforma
_cache = {}
def recs(vol):
    if vol not in _cache:
        p = R/"data/mirova_equivalent"/f"{vol}.json"
        _cache[vol] = [(_dt(r["datetime_utc"]), r["sensor"])
                       for r in json.load(open(p, encoding="utf-8"))["records"]] if p.exists() else []
    return _cache[vol]
def _dt(x):
    x = x.replace("T", " ").replace("Z", "")[:19]
    return datetime.strptime(x, "%Y-%m-%d %H:%M:%S" if len(x) >= 19 else "%Y-%m-%d %H:%M")
def plataforma(vol, t, tol_min=3):
    c = [(abs((tt-t).total_seconds()), s) for tt, s in recs(vol) if not s.endswith("_750") and "VIIRS" in s
         and abs((tt-t).total_seconds()) <= tol_min*60]
    return min(c)[1] if c else None
for canal in ("union", "tabla"):
    pas = cm.resumir_pasadas(ref, canal=canal)
    obj = [("Tupungatito", "2026-08-01 05:00"), ("Lascar", "2026-08-22 05:06"), ("Isluga", "2026-09-09 06:06"),
           ("Tupungatito", "2026-09-14 06:18"), ("Tupungatito", "2026-09-28 05:18"), ("Tupungatito", "2026-09-29 04:54")]
    print(f"\n== canal {canal}: {len(pas)} pasadas")
    for vol, ts in obj:
        t0 = datetime.strptime(ts, "%Y-%m-%d %H:%M")
        m = [p for p in pas if p.volcano == vol and p.sensor_bucket == "VIIRS375" and abs((p.instante-t0).total_seconds()) <= 300]
        if not m: print(f"  {vol} {ts}: SIN PASADA"); continue
        p = m[0]; pl = plataforma(vol, p.instante)
        print(f"  {vol} {ts}: estado {p.estado} vrp {p.vrp_mw} dist {p.dist_km} solo_ocr {p.solo_ocr} protA {cm.es_protegida(p)} "
              f"radio {rad(vol)} plataforma_record {pl} -> {cm.protegida_de_crater(p, rad(vol), pl)} | si fuera NOAA20 -> {cm.protegida_de_crater(p, rad(vol), 'VIIRS_NOAA20')}")
    if canal == "union":
        protA = [p for p in pas if p.sensor_bucket == "VIIRS375" and cm.es_protegida(p, "A")]
        pre = [p for p in protA if p.solo_ocr and p.instante.strftime("%Y-%m-%d") < cm.HITO_OCR_SNPP]
        tab = [p for p in protA if not p.solo_ocr]
        post = [p for p in protA if p.solo_ocr and p.instante.strftime("%Y-%m-%d") >= cm.HITO_OCR_SNPP]
        print(f"\n  protegidas A VIIRS375 union: {len(protA)}; solo OCR antes del hito: {len(pre)}; tabla: {len(tab)}; solo OCR desde el hito: {len(post)}")
        print("  rango fechas protA:", min(p.instante for p in protA), max(p.instante for p in protA))
        cnt = Counter(); cnt_vol = Counter(); cnt_crater = Counter()
        for p in pre:
            pl = plataforma(p.volcano, p.instante)
            cnt[pl] += 1; cnt_vol[(p.volcano, pl)] += 1
            cnt_crater[(pl, cm.protegida_de_crater(p, rad(p.volcano), pl)[1])] += 1
        print("  plataforma (record propio a <=3 min) de las solo-OCR antes del hito:", dict(cnt))
        print("  por volcan:", dict(sorted(cnt_vol.items(), key=lambda x: -x[1])))
        print("  motivos de la regla por plataforma:", dict(cnt_crater))
        print("  de cráter en toda protA (con plataforma del record):",
              Counter(cm.protegida_de_crater(p, rad(p.volcano), plataforma(p.volcano, p.instante))[0] for p in protA))
        # control positivo
        ctl = [p for p in tab if p.dist_km is not None and rad(p.volcano) and p.dist_km <= rad(p.volcano)
               and p.instante.strftime("%Y-%m-%d") >= cm.HITO_OCR_DISTANCIA]
        print(f"  control positivo tabla dentro del radio desde hito distancia: {len(ctl)}, de crater {sum(cm.protegida_de_crater(p, rad(p.volcano), plataforma(p.volcano,p.instante))[0] for p in ctl)}")
        print(f"  tabla (todas las 104) de crater: {Counter(cm.protegida_de_crater(p, rad(p.volcano), plataforma(p.volcano,p.instante)) for p in tab).most_common(5)}")

# Diagnostico de las sin plataforma: record VIIRS 375 mas cercano (cualquier distancia temporal) y su sensor
print("\n== solo-OCR antes del hito sin record a <=3 min: record VIIRS375 mas cercano")
pas = cm.resumir_pasadas(ref, canal="union")
protA = [p for p in pas if p.sensor_bucket == "VIIRS375" and cm.es_protegida(p, "A")]
pre = [p for p in protA if p.solo_ocr and p.instante.strftime("%Y-%m-%d") < cm.HITO_OCR_SNPP]
dist_min = Counter(); por_mes = Counter()
for p in pre:
    if plataforma(p.volcano, p.instante) is not None: continue
    c = [(abs((tt-p.instante).total_seconds())/60, s) for tt, s in recs(p.volcano) if "VIIRS" in s and not s.endswith("_750")]
    m = min(c) if c else (None, None)
    b = "sin records" if m[0] is None else ("<=30min" if m[0] <= 30 else ("<=1d" if m[0] <= 1440 else ">1d"))
    dist_min[(p.volcano, b)] += 1; por_mes[p.instante.strftime("%Y-%m")] += 1
print(" ", dict(dist_min)); print("  por mes:", dict(sorted(por_mes.items())))
