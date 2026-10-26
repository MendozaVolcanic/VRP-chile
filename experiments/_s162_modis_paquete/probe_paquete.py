# -*- coding: utf-8 -*-
"""S162 MOD-D, arnés del censo del paquete MODIS contra K. Pre-registro sellado: experiments/_s162_modis_paquete/
PREREGISTRO.md (v2, sello D-48, adendas 1 a 3). Sólo lectura: no escribe en data/, no commitea, no hace push.

POR QUÉ. La pregunta sellada es si el código de MIROVA portado a MODIS (PM) publica lo que MIROVA publica y calla
donde MIROVA calla mejor que producción (K), sin perder una protegida, sobre las 5.465 pasadas nocturnas de MOD-B.
El A/B se arma sobre el MISMO L1B y el MISMO MxD03 en cada pasada, bajados una vez por gránulo:
  K        producción del main congelado: calculate_vrp + store.append_record con los argumentos de run_pipeline,
           con el brazo de MOD-B (probe_mxd03_ab.brazo, sin copiarlo). Tiene que reproducir data/ (control 1).
  K33      K con ENABLE_MODIS_MIR_LAMBDA_POR_BANDA encendido en memoria (D33). Informa.
  PM       experiments/_s159/portes/probe_portes.procesar SIN MODIFICARLO (blob 8ec50e7b) con sin_k=True: sus
           variantes `fisica` (= PM), `fisica_geo5km` (= PM-geo5), `sensible` (= PM-sens), y además `pixel` y
           `fisica_b21`, que el probe corre igual y se guardan sin decidir. El probe baja sus propios archivos con
           `bajar_par`; aquí se reemplaza SÓLO esa función para que devuelva enlaces duros a los archivos ya bajados
           (el probe los borra al terminar; el original queda para el resto de los brazos). Así no se descarga dos
           veces y el port es el mismo blob que en S159 y MOD-C.
  placebo  K x 1,2: no corre aquí, lo arma el evaluador (control de cableado de M, §8 control 3).
El record del port lo arma el evaluador con `record_port` de 04_analizar.py (sin cambios), sobre lo que aquí se guarda.
Aquí sólo se juntan los insumos; ninguna regla del §4 al §6 se aplica en el runner.

Además, por pasada: la fila y el frame del píxel MxD03 más cercano al cráter (costura de barrido, §3), el diagnóstico
S-1 de la sigma de escena sobre la grilla del PM (diagnostico_s1.medir, informa) y la grilla 51 x 51 que el probe ya
guarda (`grilla_NNNN.npz`, para la equivalencia de la fase 3).

Las dos preguntas del instrumento:
1. Si el PM no corriera, ¿se vería? Sí: cada pasada guarda el estado del probe y el `port` entero; una pasada sin port
   es "port_<estado>" y no «no publica». El control 2 (PM = S159 en las pasadas del lote 39712862945) compara contra
   lo que el mismo blob dio en S159. Si K33 no cambiara nada, se vería: se guarda si su record difiere del de K.
2. Si un brazo se cayera, ¿se vería distinto de «no publica»? Sí: un record None queda None con su motivo, una
   excepción es "error" (el job sale 2), un gránulo no bajado es "no_bajado".
Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
    python experiments/_s162_modis_paquete/probe_paquete.py --parte 0 --out out [--solo clave,clave]
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s162_mxd03"))
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_mxd03_ab as PB  # noqa: E402  (brazo de produccion, bajar, resumen, decide, difiere_de_guardado)
import probe_portes as PP  # noqa: E402  (blob 8ec50e7b, sin modificar)
import diagnostico_s1 as S1  # noqa: E402

pm, P = PB.pm, PB.P
MP = PP.MP
POBLACION = RAIZ / "experiments/_s162_mxd03/poblacion.json"
GRILLAS = AQUI / "grillas.json"
VARIANTES = ("fisica", "fisica_geo5km", "sensible", "pixel", "fisica_b21")
BLOBS = {"experiments/_s159/portes/probe_portes.py": "8ec50e7bbb76c16e765a92e2773270c26c6ed9ac",
         "experiments/_s159/portes/mirova_port.py": "96769a89e6ee2233d86d973917c696cdb2405f29",
         "experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py": "07da701094f5aca7f14d7d9de39741589721c478"}


def blob(ruta):
    """git hash-object, sin git: sha1 de 'blob <n>\\0' + contenido (bytes tal como estan en disco)."""
    b = (RAIZ / ruta).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def id_pasada(pob):
    """Índice estable de cada pasada (vol, dt) en la población: nombra la grilla guardada (grilla_NNNN.npz)."""
    filas = sorted((f["vol"], f["dt"]) for g in pob["granulos"] for f in g["records"])
    return {k: i for i, k in enumerate(filas)}


def resumen_port(p):
    """Lo que el evaluador necesita del resultado de mirova_port.correr (todo serializable)."""
    if not p:
        return None
    return {k: p.get(k) for k in ("npix", "vrp_mw", "pixeles", "motivo_vacio", "n_abs", "n_p1", "n_p2", "nan_mir",
                                  "nan_tir", "umbrales_p1", "vrp_banda")}


def k33(l1b, geo, volcan, feats, datos):
    """K con D33 encendido en memoria: calculate_vrp lee la global del modulo al llamarse (process_modis.py:600)."""
    with patch.object(pm, "ENABLE_MODIS_MIR_LAMBDA_POR_BANDA", True):
        return PB.brazo(l1b, geo, volcan, feats, datos)[0]


def correr_port(o, l1b, geo, destino, outdir):
    """probe_portes.procesar sin cambios, con bajar_par devolviendo enlaces duros a los archivos ya bajados."""
    tmp = Path(tempfile.mkdtemp(prefix="modd_", dir=destino))
    enl = []
    for p in (l1b, geo):
        q = tmp / Path(p).name
        try:
            os.link(p, q)
        except OSError:
            import shutil
            shutil.copy2(p, q)
        enl.append(q)
    try:
        with patch.object(PP, "bajar_par", lambda *_a, **_k: (tuple(enl), None)):
            r = PP.procesar(o, destino, outdir, sin_k=True)
    finally:
        for q in enl:
            q.unlink(missing_ok=True)
        tmp.rmdir()
    return r


def s1_de_grilla(outdir, o, r):
    """Diagnóstico S-1 sobre la grilla `fisica` que el probe guardó (mir, tir)."""
    import numpy as np
    f = Path(outdir) / f"grilla_{o['id']:03d}.npz"
    if r.get("estado") != "ok" or not f.exists():
        return {"estado": "sin_grilla"}
    z = np.load(f)
    g = o["grilla"]
    box = MP.caja(g, g["X0"], g["Y0"], "fisica")
    return S1.medir(z["mir"].astype(float), z["tir"].astype(float), box, r.get("dayflag", 0),
                    r.get("sunglint", 180.0), MP.SENSORES["MODIS"])


def medir_record(l1b, geo, volcan, feats, datos, latlon_m, f, clave, o, destino, outdir):
    vent = PB.get_detection_anchor(volcan)
    out = {"vol": f["vol"], "dt": f["dt"], "noche": f.get("noche"), "sensor": f["sensor"], "clave": clave,
           "lab": f["lab"], "z": f["z"], "inner": volcan.get("inner_radius_km"), "id": o["id"]}
    desp = P.desplazamiento_crater(datos["lat"], datos["lon"], latlon_m[0], latlon_m[1], vent)
    n_l, n_f = (int(x) for x in latlon_m[0].shape)
    i, j = desp["linea"], desp["frame"]
    import numpy as np
    vec = latlon_m[0][max(i - 1, 0):i + 2, max(j - 1, 0):j + 2]
    # SIN DATO del verificador de la A61 (VA61-01, H1): a qué distancia del cráter está el píxel MxD03 más cercano y si
    # sus 8 vecinos tienen posición (con relleno o en el borde del gránulo, el cráter puede no estar en la imagen)
    out["crater_mxd03"] = {"linea": i, "frame": j, "costura": i % 10 in (0, 9), "forma": [n_l, n_f],
                           "borde": i in (0, n_l - 1) or j in (0, n_f - 1),
                           "dist_km": round(float(pm.haversine_km(vent[0], vent[1], latlon_m[0][i, j],
                                                                  latlon_m[1][i, j])), 4),
                           "vecinos_validos": bool(vec.size == 9 and np.isfinite(vec).all())}
    rk = PB.brazo(l1b, geo, volcan, feats, datos)[0]
    rk33 = k33(l1b, geo, volcan, feats, datos)
    pk, pk33 = P.publica([rk, rk33], f["inner"])
    out["brazos"] = {"K": PB.resumen(rk), "K33": PB.resumen(rk33)}
    out["pub"] = {"K": pk, "K33": pk33}
    out["k33_igual_k"] = P.registros_iguales(rk, rk33)
    # slim del record de K para el evaluador (predicado y magnitud mostrada con node, placebo)
    import banco_paridad as bp
    out["k_slim"] = None if rk is None else {k: rk.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    if rk is not None:
        out["k_slim"]["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                           for p in (rk.get("anomaly_pixels") or [])]
    out["k_difiere_de_guardado"] = PB.difiere_de_guardado(f, out["brazos"]["K"], pk)
    out["decide"] = PB.decide(f)
    r = correr_port(o, l1b, geo, destino, outdir)
    out["port_estado"] = r.get("estado")
    out["port_grilla"] = r.get("port_estado")          # "grilla_incompleta" si la grilla tiene mas de la mitad NaN
    out["geometria_centro"] = r.get("geometria_centro")
    out["dayflag"], out["sunglint"] = r.get("dayflag"), r.get("sunglint")
    out["saturados"] = r.get("saturados")              # b22_nan_con_b21: pixeles donde entra B21 (D33 dentro del PM)
    out["port"] = {m: resumen_port((r.get("port") or {}).get(m)) for m in VARIANTES} if r.get("port") else None
    if r.get("estado") != "ok":
        out["port_traza"] = r.get("traza")
        out["port_dist_min_km"] = r.get("dist_min_km")
    out["s1"] = s1_de_grilla(outdir, o, r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--solo", default="", help="claves de granulo separadas por coma (humo)")
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    malos = {r: blob(r) for r, h in BLOBS.items() if blob(r) != h}
    if malos:
        sys.exit(f"blobs del port distintos de los sellados: {malos}")
    PP.prueba_sin_red()
    S1.probar_diagnostico_s1()
    import run_pipeline as rp
    from pipeline.fetch import auth
    auth()
    pob = json.load(open(POBLACION, encoding="utf-8"))
    grillas = json.load(open(GRILLAS, encoding="utf-8"))
    ids = id_pasada(pob)
    por_clave = {g["clave"]: g for g in pob["granulos"]}
    claves = pob["partes"][args.parte]
    if args.solo:
        claves = [c for c in sorted(por_clave) if c in set(args.solo.split(","))]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hdf, retenidos = out / "hdf", out / "retenidos"
    destino = Path(os.environ.get("VRP_TMP_DIR", tempfile.gettempdir())) / "modd_port"
    destino.mkdir(parents=True, exist_ok=True)
    salida = open(out / f"ab_parte{args.parte:02d}.jsonl", "w", encoding="utf-8")
    cab = {"tipo": "cabecera", "parte": args.parte, "n_granulos": len(claves), **PB.Q.procedencia(),
           "poblacion_checkout": pob["checkout"], "referencia": pob["referencia"], "blobs": BLOBS,
           "flag_ENABLE_MODIS_B22_PRIMARY": bool(pm.ENABLE_MODIS_B22_PRIMARY),
           "flag_ENABLE_MODIS_MIR_LAMBDA_POR_BANDA": bool(pm.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA),
           "sha256_frontend_index": hashlib.sha256((RAIZ / "frontend/index.html").read_bytes()
                                                   .replace(b"\r\n", b"\n")).hexdigest()}
    salida.write(json.dumps(cab, ensure_ascii=False) + "\n")
    errores, t0 = 0, time.time()
    vol_cache = {}
    for clave in claves:
        g = por_clave[clave]
        prod, patron = clave.split(".", 1)
        l1b = geo = None
        retener = False
        try:
            l1b = PB.bajar(prod, patron, hdf)
            geo = PB.bajar(prod.replace("021KM", "03"), patron, hdf)
            if l1b is None or geo is None:
                for f in g["records"]:
                    salida.write(json.dumps({"tipo": "record", "clave": clave, "vol": f["vol"], "dt": f["dt"],
                                             "estado": "no_bajado",
                                             "falta": "L1B" if l1b is None else "MxD03"}) + "\n")
                    errores += 1
                continue
            datos = pm.read_modis_l1b(l1b)
            lat_m, lon_m = P._leer_mxd03(geo)
            if lat_m.shape != datos["lat"].shape:
                raise ValueError(f"MxD03 {lat_m.shape} y L1B {datos['lat'].shape} no calzan")
            for f in g["records"]:
                fila = {"tipo": "record", "clave": clave, "l1b": Path(l1b).name, "geo": Path(geo).name}
                try:
                    if f["vol"] not in vol_cache:
                        v = rp.load_volcanoes(f["vol"])[0]
                        if v.get("inner_radius_km") != f["inner"] and f["inner"] is not None:
                            raise ValueError(f"inner de volcanoes.yaml {v.get('inner_radius_km')} distinto del "
                                             f"del frontend {f['inner']}")
                        vol_cache[f["vol"]] = v
                    volcan = vol_cache[f["vol"]]
                    o = {"id": ids[(f["vol"], f["dt"])], "volcan": f["vol"], "hora_utc": f["dt"], "b": "MODIS",
                         "granule": f["granule"], "grilla": grillas[f["vol"]]}
                    fila.update(medir_record(l1b, geo, volcan, rp.VOLCANIC_FEATURES.get(volcan["name"]), datos,
                                             (lat_m, lon_m), f, clave, o, destino, out))
                    fila["estado"] = "ok"
                    if fila["decide"] and fila["k_difiere_de_guardado"]:
                        fila["retenido_para_sha"] = f["codigo_sha"]
                        retener = True
                except Exception as e:  # noqa: BLE001
                    fila.update({"vol": f["vol"], "dt": f["dt"], "estado": "error",
                                 "error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]})
                    errores += 1
                salida.write(json.dumps(fila, ensure_ascii=False, default=float) + "\n")
                salida.flush()
                pf = ((fila.get("port") or {}).get("fisica") or {})
                print(json.dumps({"clave": clave, "vol": fila.get("vol"), "estado": fila.get("estado"),
                                  "port": fila.get("port_estado"), "pub_K": (fila.get("pub") or {}).get("K"),
                                  "pm_npix": pf.get("npix"), "pm_vrp": pf.get("vrp_mw"),
                                  "k_vs_data": fila.get("k_difiere_de_guardado")}, ensure_ascii=False), flush=True)
        except Exception as e:  # noqa: BLE001
            for f in g["records"]:
                salida.write(json.dumps({"tipo": "record", "clave": clave, "vol": f["vol"], "dt": f["dt"],
                                         "estado": "error", "error": f"{type(e).__name__}: {e}"}) + "\n")
                errores += 1
        finally:
            for p in (l1b, geo):
                if p is None:
                    continue
                if retener:
                    retenidos.mkdir(parents=True, exist_ok=True)
                    Path(p).replace(retenidos / Path(p).name)
                else:
                    Path(p).unlink(missing_ok=True)
    salida.write(json.dumps({"tipo": "pie", "errores": errores, "minutos": round((time.time() - t0) / 60, 1)}) + "\n")
    salida.close()
    print(f"parte {args.parte}: {len(claves)} granulos, {errores} records con error, "
          f"{(time.time() - t0) / 60:.1f} min")
    sys.exit(2 if errores else 0)




if __name__ == "__main__":
    main()
