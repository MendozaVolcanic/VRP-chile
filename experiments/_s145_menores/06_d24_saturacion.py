"""S145 D24 - Que tan cerca de la saturacion llega el corpus de MODIS, con el
instrumento correcto.

POR QUE: el catalogo respalda el "invisible hoy" de D24 con
`sanity_cap_tocado = 0`. Ese contador es otra cosa: `store.py:130-144` lo prende
cuando el VRP supera 50 GW, o sea cuando un pixel saturado se COLO y exploto la
magnitud (el bug F28 de S73, 695.431 MW). Despues del fix, un pixel saturado se
vuelve NaN y la magnitud BAJA, asi que el tope de cordura no puede prenderse por
esta causa: el instrumento mide el fenomeno contrario al que D24 describe.

El instrumento que si corresponde: cuanto se acerca la BT MIR maxima observada
al umbral de saturacion de la banda primaria. Hoy la primaria es la 21
(ENABLE_MODIS_B22_PRIMARY = False), que satura entre 450 y 500 K
(docs/F28_SATURATION_INVESTIGATION.md, citando a Wooster 2003 y Coppola 2025).
Un pixel saturado NO aparece en t_max_k (ya es NaN), asi que esta medida es una
cota: dice cuan lejos esta el corpus del regimen donde D24 muerde, no cuantos
pixeles perdio.

Salida: 06_d24_saturacion.json
"""
import json
import glob
import statistics as stats
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "06_d24_saturacion.json"

SAT_B21_MIN = 450.0   # Wooster 2003, saturacion especificada banda 21
SAT_B21_MAX = 500.0   # Coppola 2025 Cap.11 Tabla 1 / guard BT_SAT_MIR_K_MODIS
SAT_B22 = 335.0       # banda 22, standard gain (Wooster 2003)

st = defaultdict(lambda: defaultdict(int))
tmax = defaultdict(list)
ventana = defaultdict(lambda: ["9999", "0000"])
top = defaultdict(list)

for f in sorted(glob.glob(str(ROOT / "data/mirova_equivalent/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    vol = Path(f).stem
    for r in recs:
        s = str(r.get("sensor") or "")
        if not s.startswith("MODIS"):
            continue
        b = "MODIS"
        st[b]["n_records"] += 1
        dt = str(r.get("datetime_utc") or "")
        if dt:
            ventana[b][0] = min(ventana[b][0], dt)
            ventana[b][1] = max(ventana[b][1], dt)
        t = r.get("t_max_k")
        if t is None:
            st[b]["sin_t_max_k"] += 1
            continue
        t = float(t)
        tmax[b].append(t)
        for lim, nombre in ((SAT_B22, "sobre_335K_saturaria_B22"),
                            (400.0, "sobre_400K"),
                            (SAT_B21_MIN, "sobre_450K_saturaria_B21_nominal"),
                            (SAT_B21_MAX, "sobre_500K_guard_del_pipeline")):
            if t > lim:
                st[b][nombre] += 1
        top[b].append((t, vol, dt, r.get("vrp_mw"), r.get("n_anomalous_pixels")))

out = {"definiciones": {
    "instrumento": "BT MIR maxima por record (t_max_k) contra los umbrales de "
                   "saturacion de cada banda",
    "sat_B21": f"{SAT_B21_MIN}-{SAT_B21_MAX} K (banda primaria hoy)",
    "sat_B22": f"{SAT_B22} K (banda primaria si se adopta D21)",
    "instrumento_equivocado_del_catalogo": (
        "sanity_cap_tocado cuenta VRP > 50 GW (store.py:130-144), o sea el bug "
        "F28 con los pixeles saturados COLANDOSE; con el fix vigente un pixel "
        "saturado es NaN y la magnitud BAJA, asi que ese contador no puede "
        "prenderse por saturacion"),
    "cota": "un pixel ya saturado es NaN y no entra en t_max_k: esto mide la "
            "distancia del corpus al regimen de D24, no los pixeles perdidos",
}, "por_bucket": {}}

for b in st:
    v = sorted(tmax[b])
    out["por_bucket"][b] = {
        "ventana_utc": ventana[b],
        "conteos": dict(sorted(st[b].items())),
        "t_max_k": {
            "n": len(v),
            "mediana": round(stats.median(v), 2),
            "p99": round(v[int(0.99 * (len(v) - 1))], 2),
            "p999": round(v[int(0.999 * (len(v) - 1))], 2),
            "maximo_observado": round(v[-1], 2),
            "margen_al_umbral_B21_nominal_K": round(SAT_B21_MIN - v[-1], 2),
            "margen_al_umbral_B22_K": round(SAT_B22 - v[-1], 2),
        },
        "top10_records_mas_calientes": [
            {"t_max_k": round(t, 2), "volcan": vo, "datetime_utc": dt,
             "vrp_mw": vr, "n_anomalous_pixels": na}
            for t, vo, dt, vr, na in sorted(top[b], reverse=True)[:10]],
    }

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for b, v in out["por_bucket"].items():
    print(f"\n== {b}  n_records={v['conteos']['n_records']}  "
          f"ventana={v['ventana_utc'][0][:10]}..{v['ventana_utc'][1][:10]}")
    print("   t_max_k:", json.dumps(v["t_max_k"], ensure_ascii=False))
    for k, n in v["conteos"].items():
        if k.startswith("sobre_"):
            print(f"   {k:38s} {n}")
    print("   mas caliente:", json.dumps(v["top10_records_mas_calientes"][:3],
                                         ensure_ascii=False))
