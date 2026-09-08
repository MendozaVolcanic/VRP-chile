"""S136 - test de conformidad contra el caso A6 del paper: Villarrica, 24 de junio de 2009.

POR QUE. El Apendice A de Coppola 2016a trae NUEVE casos resueltos por el propio autor, con fecha
y veredicto conocido (6 detecta, 3 NO detecta). Es el conjunto de validacion del algoritmo que
clonamos, y el proyecto nunca lo uso. A6 es Villarrica, o sea un volcan que ya esta configurado, y
su fenomeno es exactamente el de A69: cumbre helada a 2.847 m contra el lago a 215 m.

QUE AFIRMA EL PAPER (sp426_5.txt:812-817), imagen "cloud-free" de MODIS:
  (1) DETECTA la anomalia de la cumbre, NTI ~ -0,93 -- muy por debajo del umbral fijo K1 = -0,80,
      que por lo tanto NO la ve; la ve el filtrado espacial (dNTI y dETI).
  (2) NO genera deteccion sobre el lago tibio: "the warm lake surface almost disappears in the
      ETI map".

Las mascaras geograficas estan apagadas en el perfil operacional (ENABLE_EXCLUDE_ZONES = False,
leido de pipeline.profile y no del YAML), asi que nada oculta el lago artificialmente y la
afirmacion (2) se mide de verdad.

CRITERIO: docs/PREREGISTRO_CONFORMIDAD_A6_S136.md, fijado antes de correr. El control de validez
va PRIMERO y puede dejar el run no interpretable.

READ-ONLY sobre pipeline/: solo llama a calculate_vrp. No escribe en data/.
"""
import io
import json
import math
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
# El reencode de stdout va DENTRO de main(): hacerlo al importar reemplaza el stdout de
# pytest y rompe la captura de TODA la suite (2242 errores, cazado al correrla completa).

import yaml  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
import pipeline.process_modis as pm  # noqa: E402
import pipeline.profile as P  # noqa: E402

FECHA = "2009-06-24"                # el caso A6 del Apendice A
VOLCAN = "Villarrica"
NTI_PAPER = -0.93
BANDA_CONTROL = (-0.97, -0.85)      # criterio pre-registrado
LAGO = (-39.27, -72.09, 7.0)        # centro y radio de la zona "Lago Villarrica"
DEST = Path(os.environ.get("VRP_DEST", "/tmp/a6"))
DEST.mkdir(parents=True, exist_ok=True)
PARES = [("MODIS_TERRA_L1B", "MODIS_TERRA_GEO"), ("MODIS_AQUA_L1B", "MODIS_AQUA_GEO")]


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p = math.radians
    dla, dlo = p(la2 - la1), p(lo2 - lo1)
    a = math.sin(dla / 2) ** 2 + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def ginicio(g):
    try:
        s = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def cargar_volcan():
    vc = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))
    for v in vc["volcanoes"]:
        if v["name"] == VOLCAN:
            return v
    raise SystemExit(f"{VOLCAN} no esta en volcanoes.yaml")


def main():
    from run_pipeline import is_nighttime

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    vol = cargar_volcan()
    print("=" * 84)
    print(f"CONFORMIDAD A6 — {VOLCAN}, {FECHA} — MODIS, perfil {os.environ['VRP_PROFILE']}")
    print(f"El paper: DETECTA la cumbre (NTI ~ {NTI_PAPER}) y el lago NO produce deteccion.")
    print(f"ENABLE_EXCLUDE_ZONES = {P.ENABLE_EXCLUDE_ZONES}  (False => el lago no esta enmascarado)")
    print("=" * 84, flush=True)

    auth()
    dt_dia = datetime.strptime(FECHA, "%Y-%m-%d")
    ancla_lat, ancla_lon = get_detection_anchor(vol)
    print(f"ancla de deteccion: {ancla_lat:.5f} / {ancla_lon:.5f}   "
          f"crater {vol['vent_lat']:.5f} / {vol['vent_lon']:.5f}   "
          f"inner_radius {vol.get('inner_radius_km')} km", flush=True)

    filas = []
    for l1b_key, geo_key in PARES:
        try:
            grs = search_granules(l1b_key, vol["lat"], vol["lon"], vol["radius_km"], dt_dia)
        except Exception as e:
            print(f"  {l1b_key}: BUSQUEDA FALLO — {e}", flush=True)
            continue
        print(f"\n  {l1b_key}: {len(grs)} granules ese dia", flush=True)
        for g in grs:
            nom, ini = gname(g), ginicio(g)
            noche = is_nighttime(vol["lat"], vol["lon"], ini) if ini else None
            print(f"    {nom}  inicio {ini}  nocturna={noche}", flush=True)
            if not noche:
                filas.append({"granule": nom, "inicio": str(ini), "nocturna": False,
                              "motivo": "pasada diurna, fuera del universo del pipeline"})
                continue
            try:
                l1b = [Path(p) for p in download_granules([g], DEST)]
                gg = search_granules(geo_key, vol["lat"], vol["lon"], vol["radius_km"], dt_dia)
                sel = [x for x in gg if ini and ini.strftime("%H%M") in gname(x)]
                geo = [Path(p) for p in download_granules(sel[:1], DEST)] if sel else [None]
                if not l1b:
                    filas.append({"granule": nom, "inicio": str(ini), "nocturna": True,
                                  "motivo": "descarga L1B vacia"})
                    continue
                rec = pm.calculate_vrp(
                    l1b[0], geo[0] if geo else None,
                    vol["lat"], vol["lon"], vol["radius_km"],
                    vent_lat=ancla_lat, vent_lon=ancla_lon,
                    vent_radius_km=vol.get("vent_radius_km", 4.0),
                    inner_radius_km=vol.get("inner_radius_km"),
                    exclude_zones=vol.get("exclude_zones"),
                    active_water_bodies=vol.get("active_water_bodies"),
                    lbg_global_compatible=vol.get("lbg_global_compatible", False),
                    local_kernel_bg_compatible=vol.get("local_kernel_bg", False),
                )
            except Exception as e:
                print(f"      EXCEPCION: {e}", flush=True)
                traceback.print_exc()
                filas.append({"granule": nom, "inicio": str(ini), "nocturna": True,
                              "motivo": f"excepcion: {e}"})
                continue
            if rec is None:
                filas.append({"granule": nom, "inicio": str(ini), "nocturna": True,
                              "motivo": "calculate_vrp devolvio None (sin cobertura util)"})
                print("      calculate_vrp -> None", flush=True)
                continue
            pc = rec.get("primary_cluster") or {}
            clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
            d_crater = (hav(clat, clon, vol["vent_lat"], vol["vent_lon"])
                        if clat is not None else None)
            d_lago = hav(clat, clon, LAGO[0], LAGO[1]) if clat is not None else None
            fila = {
                "granule": nom, "inicio": str(ini), "nocturna": True,
                "nti_max": rec.get("nti_max"),
                "t_bg_k": rec.get("t_bg_k"),
                "vrp_pc_mw": pc.get("vrp_mw"),
                "n_pixels_pc": pc.get("n_pixels"),
                "centroid_lat": clat, "centroid_lon": clon,
                "dist_crater_km": d_crater, "dist_lago_km": d_lago,
                "distance_class": rec.get("distance_class"),
                "n_anomalous_pixels": rec.get("n_anomalous_pixels"),
                "diag_n_nti_path": rec.get("diag_n_nti_path"),
                "diag_n_first_pass_pixels": rec.get("diag_n_first_pass_pixels"),
                "triggered_test1": rec.get("triggered_test1"),
            }
            filas.append(fila)
            print(f"      nti_max={fila['nti_max']}  vrp_pc={fila['vrp_pc_mw']}  "
                  f"d_crater={d_crater}  d_lago={d_lago}", flush=True)

    (HERE / "out_a6").mkdir(exist_ok=True)
    (HERE / "out_a6" / "conformidad_a6.json").write_text(
        json.dumps(filas, indent=2, ensure_ascii=False), encoding="utf-8")
    evaluar(filas, vol)


def evaluar(filas, vol):
    inner = float(vol.get("inner_radius_km") or 5.0)
    noct = [f for f in filas if f.get("nocturna") and f.get("nti_max") is not None]
    print("\n" + "=" * 84)
    print("CONTROL DE VALIDEZ — ¿estamos mirando la escena del paper? (se evalua PRIMERO)")
    print("=" * 84)
    print(f"pasadas nocturnas procesadas: {len(noct)} de {len(filas)} granules del dia")
    en_banda = [f for f in noct
                if BANDA_CONTROL[0] <= float(f["nti_max"]) <= BANDA_CONTROL[1]]
    for f in noct:
        print(f"  {f['granule']}  nti_max={float(f['nti_max']):+.4f}  "
              f"{'EN BANDA' if f in en_banda else 'fuera'}")
    if not noct:
        print("\n>>> INDETERMINADO: ninguna pasada nocturna procesable de esa fecha.")
        print(">>> El paper no dice si su imagen es nocturna; el pipeline es night-only por")
        print(">>> diseno. No es un fallo del algoritmo.")
        return
    if not en_banda:
        print(f"\n>>> INDETERMINADO POR CONTROL: ninguna pasada cae en {BANDA_CONTROL}.")
        print(">>> No estamos mirando la escena del paper, o el indice no es comparable.")
        print(">>> Ningun otro numero de este run es interpretable.")
        return
    print(f"\ncontrol SUPERADO: {len(en_banda)} pasada(s) en la banda {BANDA_CONTROL}")

    print("\n" + "=" * 84)
    print("DESENLACE segun el criterio pre-registrado")
    print("=" * 84)
    def publica(f):
        return (f.get("vrp_pc_mw") or 0) > 0 and f.get("dist_crater_km") is not None
    cumbre = [f for f in en_banda if publica(f) and f["dist_crater_km"] <= inner]
    lago = [f for f in en_banda if publica(f) and (f.get("dist_lago_km") or 1e9) <= LAGO[2]]
    print(f"  (1) detecta en la cumbre (cumulo a <= {inner} km del crater): "
          f"{len(cumbre)} de {len(en_banda)}")
    print(f"  (2) detecta sobre el lago (cumulo dentro de {LAGO[2]} km del lago): {len(lago)}")
    fn, fp = not cumbre, bool(lago)
    if not fn and not fp:
        print("\n>>> CONFORME. Reproducimos las dos afirmaciones del paper sobre este caso.")
        print(">>> No absuelve a VIIRS 375 m: este caso es MODIS (limite declarado).")
    else:
        if fn:
            print("\n>>> NO CONFORME — FALSO NEGATIVO: el paper detecta la cumbre y nosotros no.")
            print(">>> Defecto localizado en el contextual, con referencia del autor.")
        if fp:
            print("\n>>> NO CONFORME — FALSO POSITIVO: publicamos deteccion sobre el lago, que")
            print(">>> el paper dice que el ETI hace desaparecer. Defecto en la cancelacion del")
            print(">>> gradiente topografico (A69 / D11), con referencia del autor.")


if __name__ == "__main__":
    main()
