# -*- coding: utf-8 -*-
"""S162, A/B de MxD03, control 4 del §8: corre el brazo K con el codigo de OTRO commit (el `codigo_sha` que escribio el
record de data/) sobre un granulo ya bajado. Lo lanza recorrer_en_sha.py en un proceso aparte, con el arbol de ese commit
primero en sys.path, para que pipeline/, el perfil y run_pipeline sean los de ese commit y no los de main.

Los argumentos de calculate_vrp y append_record son los que arma scripts/run_pipeline.py de main (rama MODIS), filtrados
por la firma de la funcion del commit viejo (un argumento que el commit viejo no tenia no se le pasa; uno que si tenia y
main no, queda en su valor por defecto). Esa es una aproximacion declarada: si la firma vieja cambio de significado, la
re-corrida no reproduce y el control lo dice (no lo esconde).

Imprime una sola linea JSON en stdout: {"rec": <record guardado o null>, "firma_omitidos": [...]}.
Uso: python k_en_sha.py --arbol DIR --l1b F --geo F --vol NOMBRE
"""
import argparse
import inspect
import json
import os
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", required=True)
    ap.add_argument("--l1b", required=True)
    ap.add_argument("--geo", required=True)
    ap.add_argument("--vol", required=True)
    a = ap.parse_args()
    arbol = Path(a.arbol).resolve()
    sys.path.insert(0, str(arbol / "scripts"))
    sys.path.insert(0, str(arbol))
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import run_pipeline as rp
    from pipeline import process_modis as pm
    from pipeline import store
    from pipeline import profile as vrp_profile
    from pipeline.geo_utils import get_detection_anchor
    assert Path(pm.__file__).resolve().is_relative_to(arbol), f"pipeline importado de {pm.__file__}, no de {arbol}"
    v = rp.load_volcanoes(a.vol)[0]
    vlat, vlon = get_detection_anchor(v)
    kw = {"vent_lat": vlat, "vent_lon": vlon, "vent_radius_km": v.get("vent_radius_km", 4.0),
          "inner_radius_km": v.get("inner_radius_km"), "exclude_zones": v.get("exclude_zones"),
          "active_water_bodies": v.get("active_water_bodies"),
          "lbg_global_compatible": v.get("lbg_global_compatible", False),
          "local_kernel_bg_compatible": v.get("local_kernel_bg", False)}
    firma = inspect.signature(pm.calculate_vrp).parameters
    omit = [k for k in kw if k not in firma]
    res = pm.calculate_vrp(Path(a.l1b), Path(a.geo), v["lat"], v["lon"], v["radius_km"],
                           **{k: x for k, x in kw.items() if k in firma})
    rec = None
    if res:
        kw2 = {"volcano_lat": v["lat"], "volcano_lon": v["lon"], "overwrite": True,
               "max_hotspot_dist_km": v.get("radius_km"),
               "enable_pixel_level_distance_filter": getattr(vrp_profile, "ENABLE_PIXEL_LEVEL_DISTANCE_FILTER", None),
               "max_cluster_pixels": v.get("max_cluster_pixels"), "inner_radius_km": v.get("inner_radius_km"),
               "volcanic_features": getattr(rp, "VOLCANIC_FEATURES", {}).get(v["name"])}
        f2 = inspect.signature(store.append_record).parameters
        omit += [k for k in kw2 if k not in f2]
        with tempfile.TemporaryDirectory() as tmp:
            store.DATA_DIR = Path(tmp)
            store.append_record(v["name"], res, **{k: x for k, x in kw2.items() if k in f2})
            p = Path(tmp) / f"{v['name']}.json"
            if p.exists():
                rr = json.load(open(p, encoding="utf-8"))["records"]
                rec = rr[-1] if rr else None
    print(json.dumps({"rec": rec, "firma_omitidos": omit}, default=str))


if __name__ == "__main__":
    main()
