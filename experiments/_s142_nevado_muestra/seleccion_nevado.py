# -*- coding: utf-8 -*-
"""S142: muestra NEVADA del probe del vecino del foco (VIIRS 375 m) en ventanas del OSF no usadas.

POR QUÉ. En los volcanes de cumbre nevada el campo MIR nocturno está dominado por el gradiente
topográfico (A69), así que la pregunta "qué test deja fuera a los vecinos tibios del foco" puede
tener otra respuesta que en los focales. La muestra v2 (S141) quedó sin candidatos nevados: los de
Chaitén y Villarrica ya se habían mirado en el v1 y los de Nevados de Chillán tenían el foco de
MIROVA lejos de nuestro pico. Nicolás decidió buscar otra ventana del OSF.

QUÉ HACE. No reescribe criterio. Importa `seleccionar`, `resumen_muestra` y `_pico_persistido` de
experiments/_s141_fase1_probe_v2/muestra.py y `cargar`, `build`, `nearest`, `crater` de
scripts/descomponer_magnitud_osf.py. Lo único que cambia es la VENTANA (T0, T1 del módulo, que
`cargar` usa para filtrar OSF y records) y la lista de exclusión (v1 + v2). Además reporta un embudo
por volcán nevado (filas OSF -> con record nuestro a ±10 min -> cúmulo del cráter -> clase), que
sólo cuenta y no decide nada, para que se vea en qué paso se pierde cada ventana.

CONTROL DEL INSTRUMENTO. La ventana v2 con exclusión sólo del v1 debe reproducir byte a byte
experiments/_s141_fase1_probe_v2/muestra_resumen.json. Si no, el import no es fiel y nada vale.

USO: python experiments/_s142_nevado_muestra/seleccion_nevado.py
Salida (S91): seleccion_nevado.json en esta carpeta.
"""
import collections
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
V2 = R / "experiments" / "_s141_fase1_probe_v2"
for _p in (R, R / "scripts", V2):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import muestra as mv2  # noqa: E402  (criterio v2, sin tocar)
import descomponer_magnitud_osf as m  # noqa: E402
from build_c2ab_windows import FOCAL, NEVADO  # noqa: E402
from run_pipeline import load_volcanoes  # noqa: E402
from pipeline.f5_core import _hav_km  # noqa: E402

OSF = R / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
V1_PASADAS = R / "experiments" / "_s141_fase1_probe" / "pasadas.json"
V2_PASADAS = V2 / "pasadas.json"

VENTANAS = {
    # control: la ventana v2 debe reproducir muestra_resumen.json del v2
    "control_v2": (datetime(2025, 2, 15), datetime(2025, 12, 1)),
    "2024": (datetime(2024, 1, 1), datetime(2025, 1, 1)),
    "2025_antes_v2": (datetime(2025, 1, 1), datetime(2025, 2, 15)),
    "2025_despues_v2": (datetime(2025, 12, 1), datetime(2026, 1, 1)),
}


def _pares(path):
    return {(x["volcan"], x["pasada_utc"]) for x in json.loads(path.read_text(encoding="utf-8"))}


def correr(t0, t1, excluir, vents):
    """Mismo main() de muestra.py, con la ventana cambiada. Devuelve (sel, d)."""
    m.T0, m.T1 = t0, t1
    m.cargar(str(OSF))
    d = m.build(0)
    if len(d) == 0:
        return {"pasadas": [], "excluidas": []}, d
    osf = m.o[["t", "vol", "res", "LAT", "LON"]].rename(columns={"t": "t_osf", "LAT": "lat", "LON": "lon"})
    d = d.merge(osf, on=["t_osf", "vol", "res"], how="left").drop_duplicates(subset=["t_osf", "vol", "res"])
    picos = [mv2._pico_persistido(m, x) for x in d.itertuples()]
    d["pico_lat"] = [p[0] for p in picos]
    d["pico_lon"] = [p[1] for p in picos]
    d["pico_lat"] = d["pico_lat"].astype(float)
    d["pico_lon"] = d["pico_lon"].astype(float)
    return mv2.seleccionar(d, vents, excluir, 6, 2), d


def embudo(vents):
    """Conteos por volcán nevado sobre m.o y m.ours ya cargados (sólo describe)."""
    out = {}
    o = m.o[(m.o["class"] == 1) & (m.o.VRP > 0) & (m.o.res == 375)]
    nrec = collections.Counter(k[0] for k, L in m.ours.items() if k[1] == 375 for _ in L)
    for vol in NEVADO:
        g = o[o.vol == vol]
        g3 = g[g.Npix >= 3]
        con_rec = crater_ok = 0
        dist_foco_crater = []
        for x in g3.itertuples():
            vlat, vlon = vents[vol]
            if x.LAT == x.LAT and x.LON == x.LON:
                dist_foco_crater.append(_hav_km(x.LAT, x.LON, vlat, vlon))
            par = m.nearest(vol, 375, x.t.to_pydatetime())
            if par is None:
                continue
            con_rec += 1
            if m.crater(par[1], vol):
                crater_ok += 1
        dist_foco_crater.sort()
        meses = collections.Counter(t.strftime("%Y-%m") for t in g3.t)
        out[vol] = {
            "records_375_nuestros_en_ventana_mas_7h": int(nrec.get(vol, 0)),
            "osf_noche_clase1_vrp_pos_375": int(len(g)),
            "osf_npix_ge_3": int(len(g3)),
            "osf_npix_ge_3_por_mes": dict(sorted(meses.items())),
            "osf_npix_ge_3_foco_a_le_0_75_km_del_crater": int(sum(1 for z in dist_foco_crater if z <= 0.75)),
            "osf_npix_ge_3_dist_foco_crater_km_mediana": (round(dist_foco_crater[len(dist_foco_crater) // 2], 3)
                                                        if dist_foco_crater else None),
            "con_record_nuestro_10min": con_rec,
            "con_cumulo_crater": crater_ok,
        }
    return out


def main():
    t_ini = time.time()
    vents = {v["name"]: (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])) for v in load_volcanoes()}
    v1, v2 = _pares(V1_PASADAS), _pares(V2_PASADAS)
    salida = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "osf": str(OSF), "criterio": "experiments/_s141_fase1_probe_v2/muestra.py (importado)",
                       "radio_foco_km": mv2.RADIO_FOCO_KM, "tope_candidatos": 6, "tope_controles": 2,
                       "nevado": NEVADO, "focal": FOCAL, "excluidas_v1": len(v1), "excluidas_v2": len(v2)},
              "ventanas": {}}
    for nombre, (t0, t1) in VENTANAS.items():
        excluir = v1 if nombre == "control_v2" else (v1 | v2)
        sel, d = correr(t0, t1, excluir, vents)
        res = mv2.resumen_muestra(sel)
        bloque = {"t0": t0.strftime("%Y-%m-%d"), "t1": t1.strftime("%Y-%m-%d"),
                  "n_filas_build": int(len(d)), "resumen": res, "embudo_nevado": embudo(vents)}
        if nombre == "control_v2":
            ref = json.loads((V2 / "muestra_resumen.json").read_text(encoding="utf-8"))
            bloque["reproduce_muestra_resumen_v2"] = (json.dumps(res, sort_keys=True) == json.dumps(ref, sort_keys=True))
        else:
            bloque["pasadas_nevado"] = [x for x in sel["pasadas"] if x["regimen"] == "nevado"]
            bloque["excluidas_nevado"] = [x for x in sel["excluidas"] if x["volcan"] in NEVADO]
            bloque["pasadas_todas"] = sel["pasadas"]
        salida["ventanas"][nombre] = bloque
        print(nombre, "filas build:", len(d), "| resumen:", json.dumps(res["por_volcan"], ensure_ascii=False),
              "| control ok:" if nombre == "control_v2" else "", bloque.get("reproduce_muestra_resumen_v2", ""),
              flush=True)
    salida["meta"]["segundos"] = round(time.time() - t_ini, 1)
    (HERE / "seleccion_nevado.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    for nombre, b in salida["ventanas"].items():
        print("\n==", nombre, b["t0"], b["t1"])
        for vol, e in b["embudo_nevado"].items():
            print(" ", vol, json.dumps(e, ensure_ascii=False))
    print("listo en", salida["meta"]["segundos"], "s")


if __name__ == "__main__":
    main()
