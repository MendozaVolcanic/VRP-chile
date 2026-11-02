# -*- coding: utf-8 -*-
"""¿Que hace la vigilancia de la sombra de K con los records MODIS de la via que quedan en data/ despues del revert
de B? El revert de B se lleva el arreglo MA172-101 (`scripts/vigilancia_sombra.py` de B excluye la via por clave) y
deja el de A (identico al de la base y al que midio la mini auditoria). Los records de la via ya escritos NO se borran
(experiments/_s171_modd_adopcion/PR_B_CUERPO.md l. 79-80).

Se corre el codigo REAL de cada version (cargar_insumos, pasadas_de_alerta y disparadores de scripts/vigilancia_sombra.py,
con el predicado del tablero por node en banco_paridad.cargar_nuestros), sobre JSON sinteticos en una carpeta de esta
auditoria: una pasada MODIS nocturna de Lascar con alerta protegida de MIROVA (2,0 MW), C0 (sombra) publica.
  E1 record de la VIA que calla, con marca de regimen (como la escribe store.append_record)
  E2 record de K que calla (control positivo: la vigilancia de K TIENE que disparar en las dos versiones)
  E3 record de la via que publica (control negativo: no dispara en ninguna)
Preguntas del instrumento:
1. Si la version tratara la via como K, ¿se veria? Si: E1 dispara REVERSION igual que E2.
2. Si el instrumento estuviera muerto (node no corre, la referencia no se parea), ¿se veria? Si: E2 no dispararia.
Uso: python m_postrevert_vigilancia_sombra.py <worktree> <etiqueta> <carpeta_trabajo>
"""
import json
import os
import shutil
import sys
from pathlib import Path

C = Path(sys.argv[1]).resolve()
ETQ = sys.argv[2]
W = Path(sys.argv[3]).resolve() / ETQ
sys.dont_write_bytecode = True
sys.path[:0] = [str(C / "scripts"), str(C)]
os.chdir(C)
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402
import vigilancia_sombra as vs  # noqa: E402

coords = vs.aa._coords_por_volcan()
DT = "2026-11-05 07:35"
SHA = {"perfil": "mirova_equivalent", "codigo_sha": "c9525f9946ccd03bdaad5ac28b5ef2318bcaee50", "origen": "actions"}
lat, lon = coords["Lascar"]


def publica(extra):
    r = {"datetime_utc": DT, "sensor": "MODIS_AQUA", "granule": "MYD021KM.A2026309.0735.061.hdf", "vrp_mw": 2.0,
         "distance_class": "summit", "triggered_test1": False, "vrp_vent_mw": 0.0, "t_max_k": 320.0,
         "primary_cluster": {"vrp_mw": 2.0, "n_pixels": 2, "centroid_lat": lat, "centroid_lon": lon,
                             "centroid_dist_km": 0.4},
         "anomaly_pixels": [{"lat": lat, "lon": lon, "vrp_mw": 2.0, "bt_k": 320.0, "dist_km": 0.4}],
         "final_hotspot_lat": lat, "final_hotspot_lon": lon, "final_hotspot_dist_km": 0.4}
    r.update(extra)
    return r


def calla(extra):
    r = {"datetime_utc": DT, "sensor": "MODIS_AQUA", "granule": "MYD021KM.A2026309.0735.061.hdf", "vrp_mw": 0.0,
         "distance_class": None, "triggered_test1": False, "vrp_vent_mw": 0.0, "t_max_k": None,
         "primary_cluster": None, "anomaly_pixels": []}
    r.update(extra)
    return r


ESC = {"E1_via_calla": calla({"via_codigo_mirova": True, "final_hotspot_source": None, "regimen": SHA}),
       "E2_k_calla": calla({"regimen": SHA}),
       "E3_via_publica": publica({"via_codigo_mirova": True, "final_hotspot_source": "codigo_mirova",
                                  "regimen": SHA})}
sombra_rec = publica({"regimen": {"perfil": "experimental", "codigo_sha": "x", "origen": "actions"}})
fila = {"volcano": "Lascar", "sensor_bucket": "MODIS", "fecha_utc": DT + ":00", "tipo": "ALERTA_TERMICA",
        "vrp_mw": 2.0, "source": "CONS", "dist_km": 0.5}
rmu.cargar_referencia_unificada = lambda cons, ocr: [dict(fila)]
win = ("2026-11-01", "2026-11-10")
tiene_via_arg = "via" in vs.cargar_insumos.__code__.co_varnames
out = {"version": ETQ, "cargar_insumos_acepta_via": tiene_via_arg}
for nombre, rec in ESC.items():
    dp, ds = W / nombre / "prod", W / nombre / "sombra"
    for d, r in ((dp, rec), (ds, sombra_rec)):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        for v in bp.VOLS:
            (d / f"{v}.json").write_text(json.dumps({"records": [r] if v == "Lascar" else []}), encoding="utf-8")
    bp.DATA = dp
    vs.SOMBRA = str(ds)
    if tiene_via_arg:
        # B: la exclusion se arma con la misma funcion del auto-audit sobre los records de produccion
        via = vs.aa.claves_via_modis({"Lascar": [rec]})
        filas, prod, sombra = vs.cargar_insumos(win, via=via)
    else:
        filas, prod, sombra = vs.cargar_insumos(win)
    pas = vs.pasadas_de_alerta(filas, prod, sombra, win, diurna=lambda b, v, dt: False)
    d = vs.disparadores(pas, prod, "2026-11-06", adopcion="2026-10-18 09:57:30")
    out[nombre] = {"prod_como_k": len(prod), "veredicto": d["veredicto"], "n_reversion": len(d["reversion"]),
                   "n_fuera_de_plazo": len(d.get("fuera_de_plazo", []))}
    print(f"{ETQ} {nombre:16s} prod_como_K={len(prod)} -> veredicto={d['veredicto']} "
          f"reversion={len(d['reversion'])} fuera_de_plazo={len(d.get('fuera_de_plazo', []))}")
(W.parent / f"postrevert_vigilancia_{ETQ}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")
