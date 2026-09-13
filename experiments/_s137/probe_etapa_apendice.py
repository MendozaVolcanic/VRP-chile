"""S137 - probe por etapa del primer paso (Tests 2 y 3) sobre casos del Apendice A, B21 contra B22.

POR QUE. Con la banda 22 la bateria del Apendice A pierde Villarrica (A6): los Tests 2 y 3 dan cero
pixeles, y el paper dice que esa anomalia "is easily detected after performing the spatial
filtering (dNTI and dETI)". Tambien pierde Eyjafjallajokull (A2), pero ahi el cumulo fuerte queda a
7-11 km de la cumbre y la bateria guarda la distancia, no la posicion. Ver
experiments/_s137/RESULTADO_BATERIA_B22.md.

QUE MIDE. El primer paso exige CUATRO cosas a la vez por pixel: dNTI sobre su umbral, dETI sobre su
umbral, estar en el ROI, y la compuerta de temperatura bt > t_bg + margen. Contar solo el resultado
final no dice cual se cae. Este probe cuenta cada condicion por separado dentro del radio de 5 km, y
reporta el mejor pixel candidato y el pixel del crater con sus valores. Para A2 guarda ademas la
POSICION del cumulo primario y su rumbo desde la cumbre del catalogo.

A75: se envuelve `first_pass_tests_2_and_3` en el NAMESPACE de process_modis, que es de donde lo
llama calculate_vrp (l. 866, solo argumentos con nombre). El envoltorio llama a la funcion original y
devuelve exactamente lo mismo: no cambia la deteccion, solo la observa.

READ-ONLY: no escribe en data/, no toca pipeline/ ni perfiles, no empuja commits.
"""
import io
import json
import math
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import yaml  # noqa: E402
import pipeline.detection_context as dc  # noqa: E402
import pipeline.process_modis as pm  # noqa: E402

INNER_KM = 5.0          # igual que la bateria: ROI1 del paper, uniforme
RADIUS_KM = 25.0
DEST = Path(os.environ.get("VRP_DEST", "/tmp/etapa137"))
OUT = HERE / "out_etapa"
PARES = [("MODIS_TERRA_L1B", "MODIS_TERRA_GEO"), ("MODIS_AQUA_L1B", "MODIS_AQUA_GEO")]
# (banda 22 primaria, remuestreo a grilla de 1 km). El tercer brazo prueba el otro paso previo del
# paper: en un foco sub-pixel el remuestreo puede cambiar como se reparte la senal entre vecinos,
# que es justo lo que decide si el crater supera el umbral del dNTI.
BRAZOS = {"B21": (False, False), "B22": (True, False), "B22_regrid": (True, True)}

CAPTURA = []


def _f(x):
    return None if x is None or not np.isfinite(x) else float(x)


def estadisticas_etapa(nti, eti, bt, dist_km, roi_mask, t_bg, bt_sanity_k, *,
                       inner_km, c1, c2, mu_dnti, sd_dnti, mu_deti, sd_deti):
    """Descompone el primer paso en sus condiciones, dentro de inner_km. Funcion pura.

    Umbral con la formula (min) y con la prosa (max), porque la bateria corre las dos.
    """
    mean8 = dc._nanmean_8neighbors_fast
    dnti = nti - mean8(nti)
    deti = eti - mean8(eti)
    ok = roi_mask & np.isfinite(dnti) & np.isfinite(deti) & (dist_km <= inner_km)

    def umbral(mu, sd, combinar):
        if mu is None or sd is None:
            return c1 if combinar is min else None
        return combinar(c1, mu + c2 * sd)

    thr = {"min": (umbral(mu_dnti, sd_dnti, min), umbral(mu_deti, sd_deti, min)),
           "max": (umbral(mu_dnti, sd_dnti, max), umbral(mu_deti, sd_deti, max))}
    gate_bt = bt > (t_bg + bt_sanity_k)
    out = {"n_inner": int(ok.sum()), "t_bg_mas_margen": _f(t_bg + bt_sanity_k)}
    for nombre, (td, te) in thr.items():
        if td is None or te is None:
            out[nombre] = None
            continue
        p2, p3 = ok & (dnti > td), ok & (deti > te)
        out[nombre] = {"thr_dnti": float(td), "thr_deti": float(te),
                       "n_dnti": int(p2.sum()), "n_deti": int(p3.sum()),
                       "n_ambos": int((p2 & p3).sum()),
                       "n_ambos_y_bt": int((p2 & p3 & gate_bt).sum())}
    if not ok.any():
        out["mejor"] = out["crater"] = None
        return out

    def pixel(idx):
        return {"dnti": _f(dnti[idx]), "deti": _f(deti[idx]), "nti": _f(nti[idx]),
                "bt": _f(bt[idx]), "pasa_bt": bool(gate_bt[idx]), "dist_km": _f(dist_km[idx])}

    peor_de_los_dos = np.where(ok, np.minimum(dnti, deti), -np.inf)
    out["mejor"] = pixel(np.unravel_index(int(np.argmax(peor_de_los_dos)), nti.shape))
    dist_ok = np.where(ok, dist_km, np.inf)
    out["crater"] = pixel(np.unravel_index(int(np.argmin(dist_ok)), nti.shape))
    out["max_dnti_inner"] = _f(np.max(np.where(ok, dnti, -np.inf)))
    out["max_deti_inner"] = _f(np.max(np.where(ok, deti, -np.inf)))
    return out


def envolver(original):
    """Observa sin alterar: devuelve exactamente lo que devuelve la original."""
    def envoltorio(*args, **kw):
        resultado = original(*args, **kw)
        _hot, diag = resultado
        if args:
            CAPTURA.append({"error": "llamada posicional, no se puede observar"})
            return resultado
        try:
            if diag.get("eti") is None:
                CAPTURA.append({"error": "sin eti: pool de fondo insuficiente",
                                "n_bg_used": diag.get("n_bg_used")})
            else:
                st = estadisticas_etapa(
                    kw["nti"], diag["eti"], kw["bt"], kw["dist_km"], kw["roi_mask"],
                    kw["t_bg"], kw["bt_sanity_k"], inner_km=kw["inner_km"],
                    c1=kw["c1_dnti_summit"], c2=kw["c2_dnti_summit"],
                    mu_dnti=diag["mu_dnti"], sd_dnti=diag["sd_dnti"],
                    mu_deti=diag["mu_deti"], sd_deti=diag["sd_deti"])
                st["n_first_pass_escena"] = diag["n_first_pass_pixels"]
                st["sd_dnti"], st["sd_deti"] = diag["sd_dnti"], diag["sd_deti"]
                CAPTURA.append(st)
        except Exception as e:  # observar nunca debe romper la corrida
            CAPTURA.append({"error": repr(e)})
        return resultado
    return envoltorio


def rumbo_deg(la1, lo1, la2, lo2):
    p = math.radians
    y = math.sin(p(lo2 - lo1)) * math.cos(p(la2))
    x = math.cos(p(la1)) * math.sin(p(la2)) - math.sin(p(la1)) * math.cos(p(la2)) * math.cos(p(lo2 - lo1))
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def correr_brazo(l1b, geo, caso, b22, regrid=False):
    prev_flag, prev_fn = pm.ENABLE_MODIS_B22_PRIMARY, pm.first_pass_tests_2_and_3
    prev_regrid = pm.ENABLE_UTM_REGRID
    pm.ENABLE_MODIS_B22_PRIMARY = b22
    pm.ENABLE_UTM_REGRID = regrid
    pm.first_pass_tests_2_and_3 = envolver(prev_fn)
    del CAPTURA[:]
    try:
        rec = pm.calculate_vrp(
            l1b, geo, caso["lat"], caso["lon"], RADIUS_KM,
            vent_lat=caso["lat"], vent_lon=caso["lon"],
            vent_radius_km=4.0, inner_radius_km=INNER_KM,
            exclude_zones=None, active_water_bodies=None,
            lbg_global_compatible=False, local_kernel_bg_compatible=False,
        )
    except Exception as e:
        traceback.print_exc()
        return {"error": repr(e), "etapa": list(CAPTURA)}
    finally:
        pm.ENABLE_MODIS_B22_PRIMARY, pm.first_pass_tests_2_and_3 = prev_flag, prev_fn
        pm.ENABLE_UTM_REGRID = prev_regrid
    out = {"etapa": list(CAPTURA)}
    if rec is None:
        out["record"] = None
        return out
    pc = rec.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    out["record"] = {
        "nti_max": rec.get("diag_nti_max"), "t_bg_k": rec.get("t_bg_k"),
        "n_first_pass_summit": rec.get("diag_n_first_pass_summit"),
        "n_second_pass_recapture": rec.get("diag_n_second_pass_recapture"),
        "triggered_test1": rec.get("triggered_test1"),
        "final_hotspot_source": rec.get("final_hotspot_source"),
        "pc_lat": clat, "pc_lon": clon, "pc_dist_km": pc.get("centroid_dist_km"),
        "pc_rumbo_deg": None if clat is None else round(rumbo_deg(caso["lat"], caso["lon"], clat, clon), 1),
        "pc_vrp_mw": pc.get("vrp_mw"), "pc_n_pixels": pc.get("n_pixels"),
    }
    return out


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    from run_pipeline import is_nighttime
    from pipeline.fetch import auth, download_granules, search_granules
    sys.path.insert(0, str(RAIZ / "experiments" / "_s136"))
    import conformidad_apendice as ca

    pedidos = [s.strip() for s in (os.environ.get("ETAPA_CASOS") or "A6,A2").split(",") if s.strip()]
    casos = [c for c in yaml.safe_load((RAIZ / "experiments" / "_s136" / "apendice_a.yaml")
                                       .read_text(encoding="utf-8"))["casos"]
             if c["caso"] in pedidos or c["name"] in pedidos]
    DEST.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    auth()
    salida = []
    for caso in casos:
        dia = datetime.strptime(caso["fecha"], "%Y-%m-%d")
        print("\n" + "=" * 84 + "\n" + caso["caso"] + " " + caso["name"] + " " + caso["fecha"], flush=True)
        for l1b_key, geo_key in PARES:
            try:
                grs = search_granules(l1b_key, caso["lat"], caso["lon"], RADIUS_KM, dia)
            except Exception as e:
                print("  busqueda fallo " + l1b_key + ": " + str(e), flush=True)
                continue
            for g in grs:
                nom, ini = ca.gname(g), ca.ginicio(g)
                if ini is None or not is_nighttime(caso["lat"], caso["lon"], ini):
                    continue
                try:
                    l1b = [Path(p) for p in download_granules([g], DEST)]
                    if not l1b:
                        continue
                    gg = search_granules(geo_key, caso["lat"], caso["lon"], RADIUS_KM, dia)
                    sel = [x for x in gg if ini.strftime("%H%M") in ca.gname(x)]
                    geo = ([Path(p) for p in download_granules(sel[:1], DEST)] or [None])[0]
                except Exception as e:
                    print("  descarga fallo " + nom + ": " + str(e), flush=True)
                    continue
                fila = {"caso": caso["caso"], "volcan": caso["name"], "granule": nom, "inicio": str(ini)}
                for brazo, (b22, regrid) in BRAZOS.items():
                    fila[brazo] = correr_brazo(l1b[0], geo, caso, b22, regrid)
                salida.append(fila)
                imprimir(fila)
                (OUT / "etapa_apendice.json").write_text(
                    json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "etapa_apendice.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")


def imprimir(fila):
    print("  " + fila["inicio"] + "  " + fila["granule"], flush=True)
    for brazo in BRAZOS:
        b = fila[brazo]
        et = (b.get("etapa") or [{}])[-1]
        rec = b.get("record") or {}
        if "error" in et:
            print("    " + brazo + "  etapa: " + str(et["error"]), flush=True)
        else:
            m = et.get("min") or {}
            mj, cr = et.get("mejor") or {}, et.get("crater") or {}
            print("    %s  inner=%s  thr_min dNTI=%s  dNTI>thr=%s dETI>thr=%s ambos=%s ambos+BT=%s  "
                  "escena=%s" % (brazo, et.get("n_inner"), _r(m.get("thr_dnti")), m.get("n_dnti"),
                                 m.get("n_deti"), m.get("n_ambos"), m.get("n_ambos_y_bt"),
                                 et.get("n_first_pass_escena")), flush=True)
            print("         mejor: dNTI=%s dETI=%s bt=%s pasaBT=%s d=%s | crater: dNTI=%s dETI=%s d=%s | "
                  "tbg+margen=%s" % (_r(mj.get("dnti")), _r(mj.get("deti")), _r(mj.get("bt")),
                                     mj.get("pasa_bt"), _r(mj.get("dist_km")), _r(cr.get("dnti")),
                                     _r(cr.get("deti")), _r(cr.get("dist_km")),
                                     _r(et.get("t_bg_mas_margen"))), flush=True)
        print("         cumulo: vrp=%s px=%s d=%s rumbo=%s lat=%s lon=%s fuente=%s" % (
            rec.get("pc_vrp_mw"), rec.get("pc_n_pixels"), _r(rec.get("pc_dist_km")),
            rec.get("pc_rumbo_deg"), rec.get("pc_lat"), rec.get("pc_lon"),
            rec.get("final_hotspot_source")), flush=True)


def _r(x):
    return None if x is None else round(x, 4)


if __name__ == "__main__":
    main()
