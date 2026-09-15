# -*- coding: utf-8 -*-
"""S141, Fase 1: probe por etapa del vecino del foco, VIIRS 375 m (A75, sólo lectura, sólo CI).

Reutiliza los monkeypatch del probe S135 (`experiments/_s135_probe_etapas/probe_etapas.py`, que
parchea en el namespace de pipeline.process_viirs al importarse, A89) y agrega la captura de los
índices del cúmulo final. No escribe en data/, no hace push. Plan y criterio pre-registrado:
docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md

Env: PROBE_VOL filtra volcán; PROBE_PASADAS ruta al JSON (por defecto pasadas.json de esta carpeta).
Salida: out/<vol>_<fecha>_<hhmm>.json + out/criterio.json
"""
import io
import json
import os
import sys
import traceback
from pathlib import Path

# NO se envuelve sys.stdout aquí: probe_etapas (S135) ya lo envuelve al importarse. Envolverlo dos
# veces deja huérfano el primer TextIOWrapper, que al recolectarse cierra el buffer compartido, y
# run_pipeline.py cae con "I/O operation on closed file" (corrida 34928488409, S141).
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S135 = ROOT / "experiments" / "_s135_probe_etapas"
for p in (ROOT, ROOT / "scripts", S135, HERE):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etapas as s135  # noqa: E402  (aplica los parches de S135 al importarse)
from analisis_vecinos import evaluar_criterio, resumir_vecindario  # noqa: E402

pv = s135.pv
OUT = HERE / "out"
s135.OUT = OUT
s135.DEST = HERE / "granules"

_REAL_CL = pv.cluster_hotspots


def _cl_con_indices(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
    """Envuelve el wrapper de S135 y guarda los índices del cúmulo primario, que S135 descarta."""
    cl = _REAL_CL(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
    s135._CAP.setdefault("cluster_indices", []).append(
        {"shape": list(np.asarray(hot_mask_2d).shape),
         "primario": [list(ij) for ij in (cl[0].get("pixel_indices") or [])] if cl else []})
    return cl


pv.cluster_hotspots = _cl_con_indices


def mascaras_de(cap, forma):
    """Máscaras por etapa sobre la grilla `forma`; una etapa que no corrió queda en None."""
    def m(x):
        return None if x is None else np.asarray(x, bool)
    sp_union = None
    for s in cap.get("second_pass") or []:
        o = np.asarray(s["out"], bool)
        if sp_union is None:
            sp_union = o
        elif sp_union.shape == o.shape:
            sp_union = sp_union | o
    ci = cap.get("cluster_indices") or []
    if ci:
        cl = np.zeros(tuple(ci[-1]["shape"]), bool)
        for a, b in ci[-1]["primario"]:
            cl[a, b] = True
    else:
        cl = np.zeros(forma, bool)
    return {"first_pass": m((cap.get("first_pass") or {}).get("hot")),
            "second_pass": sp_union,
            "test1": m((cap.get("test1") or {}).get("mask_contributing")),
            "ctx_filter_out": m((cap.get("ctx_filter") or {}).get("mask_out")),
            "cluster": cl}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s135.DEST.mkdir(parents=True, exist_ok=True)
    ruta = os.environ.get("PROBE_PASADAS", "").strip() or str(HERE / "pasadas.json")
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    lista = [x for x in json.loads(Path(ruta).read_text(encoding="utf-8"))
             if not f_vol or x["volcan"] == f_vol]
    print(f"Probe S141 vecinos: {len(lista)} pasadas (perfil {os.environ['VRP_PROFILE']})", flush=True)
    if not lista:
        print("sin pasadas para este filtro: nada que procesar", flush=True)
        return
    s135.auth()
    vols = {v["name"]: v for v in s135.load_volcanoes()}
    filas = []
    for x in lista:
        try:
            fila = s135.correr_pasada(vols[x["volcan"]], x["pasada_utc"], x["sensor"], x["clase"],
                                      x.get("persistido"))
            fila.update({"regimen": x["regimen"], "osf": x["osf"], "persistido": x["persistido"]})
            pc_hoy = (fila.get("record") or {}).get("primary_cluster") or {}
            fila["hoy"] = {"pc_n": pc_hoy.get("n_pixels"), "pc_vrp_mw": pc_hoy.get("vrp_mw"),
                           "n_anomalous_pixels": (fila.get("record") or {}).get("n_anomalous_pixels")}
            t1 = s135._CAP.get("test1") or {}
            if fila.get("ok") and t1.get("bt") is not None and x["osf"].get("lat") is not None:
                forma = np.asarray(t1["bt"]).shape
                res = resumir_vecindario(t1["bt"], t1["lat"], t1["lon"], mascaras_de(s135._CAP, forma),
                                         x["osf"]["lat"], x["osf"]["lon"], fila["record"].get("t_bg_k"))
                brecha = x["osf"]["vrp_mw"] - x["persistido"]["pub_mw"]
                if res.get("grilla_ok") and brecha > 0:
                    res["fraccion_brecha_fondo_local"] = round(res["aporte_perdidos_fondo_local_mw"] / brecha, 4)
                fila["resumen"] = res
                print(f"    vecinos: {res.get('conteo')} grilla_ok={res.get('grilla_ok')} "
                      f"frac_brecha_local={res.get('fraccion_brecha_fondo_local')}", flush=True)
            elif fila.get("ok"):
                fila["ok"] = False
                fila["error"] = "sin BT del Test 1 o sin lat/lon OSF"
        except Exception as e:
            fila = {**x, "ok": False, "error": str(e), "traceback": traceback.format_exc()}
        filas.append(fila)
        nombre = f"{x['volcan']}_{x['pasada_utc'].replace(' ', '_').replace(':', '')}.json"
        (OUT / nombre).write_text(json.dumps(s135.a_json(fila), indent=1, ensure_ascii=False), encoding="utf-8")
        for p in s135.DEST.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
    crit = {"total": evaluar_criterio(filas), "focal": evaluar_criterio(filas, "focal"),
            "nevado": evaluar_criterio(filas, "nevado")}
    (OUT / "criterio.json").write_text(json.dumps(s135.a_json(crit), indent=1, ensure_ascii=False),
                                       encoding="utf-8")
    print(json.dumps(s135.a_json(crit), indent=1, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
