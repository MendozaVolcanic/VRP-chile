# -*- coding: utf-8 -*-
"""S159, frente pareo MODIS en el borde del granulo. Medicion 1: tasa base y clasificacion.

Corre contra un ESPEJO de origin/main (git archive de scripts, pipeline, frontend, volcanoes.yaml,
data/mirova_equivalent y data/mirova_reference) pasado por --raiz. No toca el repo.

Las dos preguntas del instrumento:
1. Si el pareo exacto perdiera pasadas, lo veria? Si: para cada record nuestro busco filas de MIROVA del
   mismo volcan y sensor a 0 y a +-5 min (granulo vecino) y a +-10 min, y al reves, cada fila de MIROVA
   contra nuestros records. Control positivo: Chillan 2026-01-19 02:40 MODIS debe salir "solo vecino".
2. Si el instrumento estuviera muerto: un cero en "solo vecino" se distingue de "no medi" porque informo
   tambien los pareos exactos (que deben ser miles) y un control negativo: +-150 min (ninguna fila de la
   misma orbita puede estar ahi; Terra y Aqua estan a ~3 h, asi que se informa aparte).

Denominador: records de los 11 Tier A en data/mirova_equivalent de origin/main; ventana = fechas en que la
referencia tiene filas de ese volcan y sensor (desde la primera fila de MIROVA del volcan). Nocturno = filtro
del pipeline (auto_audit_weekly.es_pasada_diurna_descartada), informado aparte de "todas".
"""
import argparse
import collections
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--raiz", required=True)
ap.add_argument("--out", default=str(Path(__file__).with_name("medir_pareo_salida.json")))
a = ap.parse_args()
RAIZ = Path(a.raiz)
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402

assert str(SNAP_CONS).startswith(str(RAIZ)), SNAP_CONS
coords = _coords_por_volcan()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
ref = collections.defaultdict(list)          # (vol, bucket) -> [(dt, fila)]
for f in filas:
    if f["volcano"] not in bp.VOLS or f["sensor_bucket"] not in bp.BUCKETS:
        continue
    dt = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    ref[(f["volcano"], f["sensor_bucket"])].append((dt, f))
inicio_ref = {k: min(x[0] for x in v) for k, v in ref.items()}
fin_ref = {k: max(x[0] for x in v) for k, v in ref.items()}
ref_t = {k: collections.defaultdict(list) for k in ref}
for k, v in ref.items():
    for dt, f in v:
        ref_t[k][dt].append(f)

nuestros = collections.defaultdict(list)     # (vol, bucket) -> [(dt, rec)]
for vol in bp.VOLS:
    d = json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None:
            continue
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        nuestros[(vol, b)].append((dt, r))
nuestros_t = {k: collections.defaultdict(list) for k in nuestros}
for k, v in nuestros.items():
    for dt, r in v:
        nuestros_t[k][dt].append(r)


def clase_ref(fs):
    tipos = []
    for f in fs:
        if bp.es_alerta(f["tipo"]):
            tipos.append("alerta_protegida" if (f["vrp_mw"] or 0) >= 1.0 else "alerta_bajo_1MW")
        elif bp.es_fp(f["tipo"]):
            tipos.append("falso_positivo")
        elif f["tipo"] == "RUTINA":
            tipos.append("rutina")
        else:
            tipos.append(f["tipo"] or "?")
    for t in ("alerta_protegida", "alerta_bajo_1MW", "falso_positivo", "rutina"):
        if t in tipos:
            return t
    return tipos[0] if tipos else None


def paso(b):
    return 5 if b == "MODIS" else 6   # duracion del granulo: MODIS 5 min, VIIRS 6 min


salida = {"definiciones": {}, "por_bucket": {}}
casos_borde = []
for (vol, b), lista in sorted(nuestros.items()):
    k = (vol, b)
    if k not in ref:
        continue
    lat, lon = coords[vol]
    for dt, r in lista:
        if not (inicio_ref[k] <= dt <= fin_ref[k] + timedelta(days=1)):
            continue
        noct = not es_pasada_diurna_descartada(b, lat, lon, dt)
        exacta = bool(ref_t[k].get(dt))
        # +-tol de banco_paridad (120 s): con horas al minuto y en multiplos de 5 o 6 min, equivale a +-2 min
        a120 = bool(bp.parear(ref[k], dt))
        vec = [s for s in (-1, 1) if ref_t[k].get(dt + timedelta(minutes=s * paso(b)))]
        # ventana +-10 min sin la exacta ni el vecino inmediato
        otros10 = [m for m in range(-10, 11) if m not in (0, paso(b), -paso(b))
                   and ref_t[k].get(dt + timedelta(minutes=m))]
        ctrl150 = bool(ref_t[k].get(dt + timedelta(minutes=150))) or bool(ref_t[k].get(dt - timedelta(minutes=150)))
        nuestro_vec = [s for s in (-1, 1) if nuestros_t[k].get(dt + timedelta(minutes=s * paso(b)))]
        if a120:
            cat = "pareo_120s"
        elif vec:
            cat = "solo_vecino"
        elif otros10:
            cat = "solo_otro_10min"
        else:
            cat = "sin_fila"
        e = salida["por_bucket"].setdefault(b, collections.Counter())
        e[f"{cat}|{'noche' if noct else 'dia'}"] += 1
        if ctrl150:
            e["control_150min"] += 1
        if cat == "solo_vecino":
            fs = [f for s in vec for f in ref_t[k][dt + timedelta(minutes=s * paso(b))]]
            # nuestro record en el granulo vecino: si existe, la pasada SI esta pareada por el otro record
            vecino_mirova_tiene_nuestro = any(nuestros_t[k].get(dt + timedelta(minutes=s * paso(b))) for s in vec)
            casos_borde.append({
                "vol": vol, "b": b, "sensor": r.get("sensor"), "dt": dt.strftime("%Y-%m-%d %H:%M"),
                "noche": noct, "mes": dt.strftime("%Y-%m"), "desfase_min": [s * paso(b) for s in vec],
                "clase_ref": clase_ref(fs), "tipos_ref": sorted({f["tipo"] for f in fs}),
                "vrp_ref": max((f["vrp_mw"] or 0) for f in fs), "fuentes_ref": sorted({f["source"] for f in fs}),
                "granulo": r.get("granule"), "nuestro_en_granulo_de_mirova": vecino_mirova_tiene_nuestro,
                "nuestro_vecino_lados": nuestro_vec, "zen": r.get("sensor_zenith_deg"),
                "dc": r.get("distance_class"), "pc_vrp": (r.get("primary_cluster") or {}).get("vrp_mw"),
                "n_bg_anillo": r.get("diag_n_bg_anillo"), "n_bg_used": r.get("diag_n_bg_used_first_pass"),
                "datetime_vs_granulo": (r.get("granule") or "").split(".")[2] if r.get("granule") else None,
            })

# lado MIROVA: filas sin record nuestro a 120 s
filas_sin_par = collections.Counter()
filas_sin_par_det = []
for k, lista in sorted(ref.items()):
    vol, b = k
    lat, lon = coords[vol]
    ts_n = nuestros_t.get(k, {})
    if not ts_n:
        continue
    ini_n = min(ts_n)
    vistas = set()
    for dt, f in lista:
        if dt < ini_n or dt in vistas:
            continue
        vistas.add(dt)
        fs = ref_t[k][dt]
        noct = not es_pasada_diurna_descartada(b, lat, lon, dt)
        if ts_n.get(dt):
            cat = "con_par"
        elif any(ts_n.get(dt + timedelta(minutes=s * paso(b))) for s in (-1, 1)):
            cat = "solo_vecino"
            filas_sin_par_det.append({"vol": vol, "b": b, "dt": dt.strftime("%Y-%m-%d %H:%M"), "noche": noct,
                                      "clase_ref": clase_ref(fs), "mes": dt.strftime("%Y-%m"),
                                      "vrp_ref": max((x["vrp_mw"] or 0) for x in fs)})
        else:
            cat = "sin_record_cerca"
        filas_sin_par[f"{b}|{cat}|{'noche' if noct else 'dia'}"] += 1

# MIROVA lista ambos granulos de una misma orbita? pares de filas a +-paso del mismo vol y sensor
pares_ref = collections.Counter()
for (vol, b), tt in ref_t.items():
    for dt in tt:
        if tt.get(dt + timedelta(minutes=paso(b))):
            pares_ref[b] += 1
pares_nuestros = collections.Counter()
for (vol, b), tt in nuestros_t.items():
    for dt in tt:
        if tt.get(dt + timedelta(minutes=paso(b))):
            pares_nuestros[b] += 1
n_nuestros = collections.Counter(b for (v, b), l in nuestros.items() for _ in l)
n_ref = collections.Counter(b for (v, b), t in ref_t.items() for _ in t)

salida["por_bucket"] = {b: dict(c) for b, c in salida["por_bucket"].items()}
salida["filas_mirova"] = dict(filas_sin_par)
salida["pares_granulos_consecutivos"] = {"mirova_pasadas": dict(pares_ref), "mirova_total_pasadas": dict(n_ref),
                                         "nuestros": dict(pares_nuestros), "nuestros_total": dict(n_nuestros)}
salida["casos_borde"] = casos_borde
salida["filas_mirova_solo_vecino"] = filas_sin_par_det
salida["ventana_ref"] = {f"{v}|{b}": [inicio_ref[(v, b)].isoformat(), fin_ref[(v, b)].isoformat()] for (v, b) in ref}
Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

print("records nuestros por categoria (ventana con referencia):")
for b, c in salida["por_bucket"].items():
    print(" ", b, dict(sorted(c.items())))
print("filas MIROVA por categoria:", dict(sorted(filas_sin_par.items())))
print("pares de granulos consecutivos (misma orbita) en la referencia:", dict(pares_ref), "de", dict(n_ref))
print("pares de granulos consecutivos en nuestros records:", dict(pares_nuestros), "de", dict(n_nuestros))
cb = [c for c in casos_borde if c["b"] == "MODIS"]
print("MODIS solo_vecino:", len(cb), "nocturnos:", sum(c["noche"] for c in cb))
print("  con nuestro record en el granulo de MIROVA tambien:", sum(c["nuestro_en_granulo_de_mirova"] for c in cb))
print("  por clase_ref (noche):", collections.Counter(c["clase_ref"] for c in cb if c["noche"]))
print("  por volcan (noche):", collections.Counter(c["vol"] for c in cb if c["noche"]))
print("  por mes (noche):", dict(sorted(collections.Counter(c["mes"] for c in cb if c["noche"]).items())))
print("  por desfase:", collections.Counter(tuple(c["desfase_min"]) for c in cb))
print("  por sensor:", collections.Counter(c["sensor"] for c in cb))
print("  datetime == hora del granulo:", sum(c["datetime_vs_granulo"] == c["dt"][11:13] + c["dt"][14:16] for c in cb), "de", len(cb))
ctrl = [c for c in casos_borde if c["vol"] == "NevadosDeChillan" and c["dt"] == "2026-01-19 02:40"]
print("CONTROL POSITIVO Chillan 2026-01-19 02:40:", ctrl)
