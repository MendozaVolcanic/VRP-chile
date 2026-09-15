# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): probe del vecino del foco, VIIRS 375 m (A75, sólo lectura, sólo CI).

POR QUÉ. El v1 no pudo decir dónde se pierden los vecinos tibios que MIROVA suma: no controlaba que
MIROVA mirara el mismo foco, leía en fila dos rutas paralelas y medía la brecha contra el backfill.
Este runner corre `calculate_vrp` real sobre cada pasada de `pasadas.json` y registra, sin tocar el
pipeline, qué etapas corrieron, qué llamada produjo el cúmulo publicado y lo que se publica hoy
(núcleo F5 en la misma corrida). Todo el análisis vive en `analisis_v2.py`; el criterio
pre-registrado, en docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md.

CÓMO. Reutiliza la descarga y los parches del probe S135 (`experiments/_s135_probe_etapas/
probe_etapas.py`, que parchea en el namespace de pipeline.process_viirs al importarse, A89) y
envuelve encima con `captura.Captura`. No escribe en data/, no hace push.

Env: PROBE_VOL filtra volcán; PROBE_PASADAS ruta al JSON (por defecto pasadas.json de esta carpeta).
Salida: out/<vol>_<fecha>_<hhmm>.json + out/criterio.json
"""
import json
import os
import sys
import traceback
from pathlib import Path

# NO se envuelve sys.stdout aquí: probe_etapas (S135) ya lo envuelve al importarse. Envolverlo dos
# veces deja huérfano el primer TextIOWrapper, que al recolectarse cierra la salida (run 34928488409).
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S135 = ROOT / "experiments" / "_s135_probe_etapas"
for p in (ROOT, ROOT / "scripts", S135, HERE):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etapas as s135  # noqa: E402  (aplica los parches de S135 al importarse)
import run_pipeline  # noqa: E402  (el mismo módulo de perfil que usa store.append_record, A89)
from analisis_v2 import evaluar  # noqa: E402
from captura import Captura  # noqa: E402
from ensamblar import analizar  # noqa: E402
from flags import verificar_flags  # noqa: E402

pv = s135.pv
FILTRO_DISTANCIA = run_pipeline.vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER   # run_pipeline.py:251
OUT = HERE / "out"
s135.OUT = OUT
s135.DEST = HERE / "granules"

CAP = Captura()
pv.calculate_vrp = CAP.envolver_calcular(pv.calculate_vrp)
pv.cluster_hotspots = CAP.envolver_cluster(pv.cluster_hotspots)
pv.first_pass_tests_2_and_3 = CAP.envolver_first_pass(pv.first_pass_tests_2_and_3)
pv.second_pass_adjacent = CAP.envolver_second_pass(pv.second_pass_adjacent)
pv.compute_test1_mir = CAP.envolver_test1(pv.compute_test1_mir)
pv.apply_contextual_test1_filter = CAP.envolver_ctx(pv.apply_contextual_test1_filter)
pv.resolve_test1_source_priority = CAP.envolver_prioridad(pv.resolve_test1_source_priority)
pv.dual_roi_contextual_dnti_hot_mask = CAP.envolver_dnti_ctx(pv.dual_roi_contextual_dnti_hot_mask)
pv.select_test1_effective_lbg = CAP.envolver_lbg(pv.select_test1_effective_lbg)

FLAGS = ("ENABLE_FIRST_PASS_TESTS_2_AND_3", "ENABLE_SECOND_PASS_ADJACENT", "ENABLE_TEST1_CONTEXTUAL_FILTER",
         "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK", "ENABLE_TEST1_PIXEL_FILTER", "ENABLE_TEST1_SPATIAL_CORE",
         "ENABLE_TEST1_NTI_INTEGRAL", "ENABLE_ETI_QUADRATIC_SCENE", "PATH_D_ATM_GATE_TBG_MIN_K",
         "ENABLE_SINGLE_PIXEL_SUB_MW_MODE", "SINGLE_PIXEL_MAX_CLUSTER_PIXELS", "ENABLE_HONEST_ANCHOR",
         "ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375", "ENABLE_TEST1_LAVA_LAKE_EQ16")


def main():
    # H10: las imposibilidades por construcción del plan dependen de estos flags; si cambian, se detiene.
    verificar_flags(pv)
    print("flags de la taxonomía verificados", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    s135.DEST.mkdir(parents=True, exist_ok=True)
    ruta =os.environ.get("PROBE_PASADAS", "").strip() or str(HERE / "pasadas.json")
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    lista = [x for x in json.loads(Path(ruta).read_text(encoding="utf-8")) if not f_vol or x["volcan"] == f_vol]
    print(f"Probe S141 vecinos v2: {len(lista)} pasadas (perfil {os.environ['VRP_PROFILE']})", flush=True)
    if not lista:
        print("sin pasadas para este filtro: nada que procesar", flush=True)
        return
    print("flags efectivos:", {k: getattr(pv, k, None) for k in FLAGS}, flush=True)
    s135.auth()
    vols = {v["name"]: v for v in s135.load_volcanoes()}
    filas = []
    for x in lista:
        try:
            fila = s135.correr_pasada(vols[x["volcan"]], x["pasada_utc"], x["sensor"], x["clase"], x.get("persistido"))
            fila["resumen_s135"] = fila.pop("resumen", None)
            fila.update({"regimen": x["regimen"], "osf": x["osf"], "persistido": x["persistido"]})
            if fila.get("ok"):
                # H4: un error del análisis NO saca la pasada del control: conserva `ok` del pipeline.
                try:
                    fila = analizar(fila, vols[x["volcan"]], x, CAP, FILTRO_DISTANCIA)
                except Exception as e:
                    fila["error_analisis"] = str(e)
                    fila["traceback_analisis"] = traceback.format_exc()
                r = fila.get("resumen") or {}
                print(f"    v2: publicado={(fila.get('publicado') or {}).get('ruta')} "
                      f"n_hoy={(fila.get('hoy') or {}).get('n_publicado')} foco_ok={r.get('foco_ok')} "
                      f"replica={r.get('replica_ok')} alineacion={r.get('alineacion_bt')} "
                      f"limitantes={[v['limitante'] for v in r.get('vecinos', []) if v.get('caliente')]} "
                      f"error_analisis={fila.get('error_analisis')}", flush=True)
        except Exception as e:
            fila = {**x, "ok": False, "error": str(e), "traceback": traceback.format_exc()}
            print(f"    FALLO: {e}", flush=True)
        CAP.reset()
        filas.append(fila)
        nombre = f"{x['volcan']}_{x['pasada_utc'].replace(' ', '_').replace(':', '')}.json"
        (OUT / nombre).write_text(json.dumps(s135.a_json(fila), indent=1, ensure_ascii=False), encoding="utf-8")
        for p in s135.DEST.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
    crit = {k: evaluar(filas, None if k == "total" else k) for k in ("total", "focal", "nevado")}
    (OUT / "criterio.json").write_text(json.dumps(s135.a_json(crit), indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s135.a_json({k: v["veredicto"] for k, v in crit.items()}), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
