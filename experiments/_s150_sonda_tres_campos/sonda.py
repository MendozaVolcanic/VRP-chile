# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos (VIIRS 375). Corre SOLO en GitHub Actions
(.github/workflows/probe-s150-tres-campos.yml): baja granulos de NASA con EARTHDATA_TOKEN.

PREGUNTA. En las pasadas donde la conectiva `max` pierde una alerta de MIROVA, ¿pasaria el pixel los
Tests 2 y 3 si mu y sigma se midieran sobre el campo remuestreado e interpolado como lo arma MIROVA? Y
el residual que `max` apaga con razon, ¿seguiria apagado ahi? Diseño y criterio: DISENO.md.

COMO (A75, solo lectura). Para cada pasada de pasadas.json (filtrada por lote) baja el L1B y el GEO de
ese granulo exacto y corre `process_viirs.calculate_vrp` REAL varias veces, cambiando solo el sustrato:
  nativo   granulo tal cual (operacional)
  utm_nn   la grilla UTM de vecino mas cercano que ya existe (ENABLE_UTM_REGRID, pipeline/regrid.py)
  tif_nn / tif_lin / tif_cub   el granulo interpolado (vecino / lineal / cubico) a la grilla EXACTA del
           GeoTIFF de MIROVA de ese volcan (plantillas_tif.json), con la escena centrada donde la
           centra MIROVA (get_grid_center, D17) y cubriendo toda su imagen
cada uno con la conectiva `max` (perfil F) y `min` (perfil B), y en los tif_* tambien `max` sin la
compuerta de 3 K (D22). Los cambios se hacen reasignando nombres en el namespace de
pipeline.process_viirs (A89: parchear el modulo de origen no cambia nada) y se restauran al terminar
cada corrida. No se edita pipeline/, ningun perfil ni data/. El record de cada corrida pasa por el
`store.append_record` real con DATA_DIR apuntando a un temporal, para que el predicado del tablero
(node, A97) mire el mismo record que miraria en produccion.

De la corrida `max` de cada campo se capturan las entradas reales de `first_pass_tests_2_and_3` y los
argumentos de `second_pass_adjacent`, y campos.evaluar_campo recalcula con las mismas funciones dNTI,
dETI, mu, sigma, mu2, sigma2 y la decision con `min` / `max` y con / sin compuerta, por pixel.

Env: VRP_PROFILE=_s147_ab_sin_test1_max (obligatorio), EARTHDATA_TOKEN (obligatorio, nunca usuario y
clave: A71), PROBE_LOTE (entero) o PROBE_CLAVES (claves separadas por ';'), TIF_DIR (raiz del checkout
disperso de mirova-tif-archive), PROBE_OUT (carpeta de salida).
Salida: <PROBE_OUT>/<vol>_<fecha>_<hhmm>.json por pasada + cobertura_lote_<n>.json
"""
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path

if not isinstance(sys.stdout, io.TextIOWrapper) or (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
import numpy as np  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for p in (RAIZ, RAIZ / "scripts", AQUI):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

PERFIL_ESPERADO = "_s147_ab_sin_test1_max"
PRODUCTOS = {"VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
             "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
             "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO")}
METODOS_TIF = {"tif_nn": "nearest", "tif_lin": "linear", "tif_cub": "cubic"}
# corridas por campo: (nombre, conectiva, compuerta). La primera de cada campo es la que se captura.
CORRIDAS = {"nativo": [("max", "max", True), ("min", "min", True), ("max_sin_compuerta", "max", False)],
            "utm_nn": [("max", "max", True), ("min", "min", True), ("max_sin_compuerta", "max", False)],
            "tif_nn": [("max", "max", True), ("min", "min", True), ("max_sin_compuerta", "max", False)],
            "tif_lin": [("max", "max", True), ("min", "min", True), ("max_sin_compuerta", "max", False)],
            "tif_cub": [("max", "max", True), ("min", "min", True), ("max_sin_compuerta", "max", False)]}
FLAGS_ESPERADOS = {"ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": False,
                   "ENABLE_UTM_REGRID": False, "ENABLE_FIRST_PASS_TESTS_2_AND_3": True,
                   "ENABLE_SECOND_PASS_ADJACENT": True, "ENABLE_ROI1_BOX_PAPER": False}
CAMPOS_RECORD = ["sensor", "granule", "datetime_utc", "product_version", "vrp_mw", "vrp_mir_mw", "t_bg_k",
                 "t_max_i04_k", "t_max_k", "n_anomalous_pixels", "distance_class", "final_hotspot_source",
                 "final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km", "primary_cluster",
                 "discarded_reason", "triggered_test1", "vrp_vent_mw", "f5_core_vrp_mw", "anomaly_pixels",
                 "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "diag_n_bg_used_first_pass",
                 "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "sensor_zenith_deg"]


def guardas_de_entorno(exigir_token=True):
    """Falla al instante, antes de importar fetch, si falta lo que hace que la corrida mida algo."""
    if os.environ.get("VRP_PROFILE") != PERFIL_ESPERADO:
        raise SystemExit("VRP_PROFILE debe ser %s (es %r)" % (PERFIL_ESPERADO, os.environ.get("VRP_PROFILE")))
    if exigir_token and not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        raise SystemExit("EARTHDATA_TOKEN vacio: sin token no se corre (A71: el login por clave bloquea la cuenta)")
    for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
        if os.environ.get(k):
            raise SystemExit("%s presente en el entorno: esta sonda autentica SOLO por token (A71)" % k)


class Captura:
    """Envoltorios de solo lectura sobre pipeline.process_viirs (A75). Guardan referencias, no copias."""

    NOMBRES = ("read_viirs_l1b", "read_viirs_geo", "first_pass_tests_2_and_3", "second_pass_adjacent",
               "_regrid_viirs_granule")

    def __init__(self, pv):
        self.pv = pv
        self.real = {n: getattr(pv, n) for n in self.NOMBRES}
        self.cache = {}
        self.cap = {}
        self.capturar = True

    def instalar(self):
        self.pv.read_viirs_l1b = self._l1b
        self.pv.read_viirs_geo = self._geo
        self.pv.first_pass_tests_2_and_3 = self._fp
        self.pv.second_pass_adjacent = self._sp

    def desinstalar(self):
        for n, f in self.real.items():
            setattr(self.pv, n, f)

    def _l1b(self, path):
        k = ("l1b", str(path))
        if k not in self.cache:
            self.cache[k] = self.real["read_viirs_l1b"](path)
        return {b: v.copy() for b, v in self.cache[k].items()}

    def _geo(self, path):
        k = ("geo", str(path))
        if k not in self.cache:
            self.cache[k] = self.real["read_viirs_geo"](path)
        g = self.cache[k]
        out = {kk: (v.copy() if isinstance(v, np.ndarray) else v) for kk, v in g.items() if kk != "angles"}
        out["angles"] = {kk: (v.copy() if v is not None else None) for kk, v in (g.get("angles") or {}).items()}
        self.cap["geo_nativo"] = out
        return out

    def _fp(self, *a, **kw):
        hot, diag = self.real["first_pass_tests_2_and_3"](*a, **kw)
        if self.capturar:
            self.cap["fp_kw"] = kw
            self.cap["fp_hot"] = hot
            self.cap["fp_eti_id"] = id(diag.get("eti")) if diag else None
            self.cap["fp_diag"] = {k: v for k, v in (diag or {}).items() if not isinstance(v, np.ndarray)}
        return hot, diag

    def _sp(self, *a, **kw):
        out = self.real["second_pass_adjacent"](*a, **kw)
        if self.capturar and id(kw.get("eti")) == self.cap.get("fp_eti_id"):
            self.cap["sp_kw"] = {k: ("ARRAY" if isinstance(v, np.ndarray) else v) for k, v in kw.items()
                                 if k not in ("nti", "eti", "active_mask")}
            self.cap["sp_out_n"] = int(np.sum(out))
            am = kw.get("active_mask")
            self.cap["sp_in_n"] = int(np.sum(am)) if am is not None else None   # diagnostico: debe ser = fp_hot
        return out

    def envolver_regrid(self, fn):
        def w(*a, **kw):
            bands, geo = fn(*a, **kw)
            self.cap["geo_grilla"] = geo
            return bands, geo
        return w

    def limpiar_pasada(self):
        self.cache.clear()
        self.cap.clear()


def rss_max_mb():
    """Memoria residente maxima del proceso hasta ahora, en MB (Linux: ru_maxrss en KB). None en Windows."""
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
    except Exception:
        return None


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def bajar_par(fetch, vol, plataforma, dt, stamp, destino, granulo_ab=None):
    """Busca y baja el L1B y el GEO de ESA pasada (mismo sello AYYYYDDD.HHMM). Devuelve (l1b, geo) o None.
    Prefiere el MISMO archivo L1B que proceso el A/B (granulo_ab) y, si no esta, el estandar antes que el NRT:
    asi el control de identidad contra el record del A/B compara lo mismo (verificador D22, H9)."""
    l1b_key, geo_key = PRODUCTOS[plataforma]
    rutas = {}
    for key in (l1b_key, geo_key):
        grs = fetch.search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt)
        sel = [g for g in grs if stamp in gname(g)]
        sel.sort(key=lambda g: (gname(g) != granulo_ab, "NRT" in gname(g).upper()))
        print("    %s: %d granulos del dia, %d con %s" % (key, len(grs), len(sel), stamp), flush=True)
        if not sel:
            return None
        got = [p for p in fetch.download_granules(sel[:1], destino) if stamp in Path(p).name]
        if not got:
            return None
        rutas[key] = Path(got[0])
    return rutas[l1b_key], rutas[geo_key]


def puntos_objetivo(pasada):
    """Lo que B publico: centroide del cumulo primario y sus pixeles de anomalia a <= 1,5 km de el."""
    from pipeline.scan_geometry import haversine_km
    b = pasada["B"]
    pts = []
    if b.get("pc_lat") is not None:
        pts.append((b["pc_lat"], b["pc_lon"]))
        for q in b.get("anomaly_pixels") or []:
            if q.get("lat") is None:
                continue
            if float(haversine_km(b["pc_lat"], b["pc_lon"], q["lat"], q["lon"])) <= 1.5:
                pts.append((q["lat"], q["lon"]))
    return pts


def resumir_record(r):
    if r is None:
        return None
    out = {k: copy.deepcopy(r.get(k)) for k in CAMPOS_RECORD if k in r}
    return json.loads(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


class Contexto:
    """Todo lo que procesar_pasada necesita, armado una sola vez."""

    def __init__(self):
        import pipeline.process_viirs as pv
        import pipeline.store as store
        import run_pipeline
        import campos as cp
        self.pv, self.store, self.rp, self.cp = pv, store, run_pipeline, cp
        flags = {k: getattr(pv, k) for k in list(FLAGS_ESPERADOS) + ["ENABLE_SECOND_PASS_CONDITIONED", "CLOUD_MASK_BT_K"]}
        print("flags efectivos (leidos de pipeline.process_viirs):", flags, flush=True)
        malos = {k: (flags[k], v) for k, v in FLAGS_ESPERADOS.items() if flags[k] != v}
        if malos:
            raise SystemExit("flags del perfil F distintos a los del A/B: %s" % malos)
        self.flags = flags
        self.cap = Captura(pv)
        self.cap.instalar()
        self.real_regrid = self.cap.real["_regrid_viirs_granule"]
        self.originales = {k: getattr(pv, k) for k in ("ENABLE_UTM_REGRID", "ENABLE_TESTS_23_PROSE_BRANCH",
                                                     "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375")}
        self.vols = {v["name"]: v for v in run_pipeline.load_volcanoes()}
        self.plantillas = json.loads((AQUI / "plantillas_tif.json").read_text(encoding="utf-8"))
        self.store_dir_original = store.DATA_DIR
        self.rng_master = np.random.default_rng(150)


def persistir(ctx, vol, rec):
    """Pasa el record por store.append_record real con DATA_DIR en un temporal y lo relee."""
    if rec is None:
        return None
    tmpd = Path(tempfile.mkdtemp(prefix="store_"))
    try:
        ctx.store.DATA_DIR = tmpd
        ctx.store.append_record(vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"],
                                overwrite=True, max_hotspot_dist_km=vol.get("radius_km"),
                                enable_pixel_level_distance_filter=ctx.rp.vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                max_cluster_pixels=vol.get("max_cluster_pixels"),
                                inner_radius_km=vol.get("inner_radius_km"),
                                volcanic_features=ctx.rp.VOLCANIC_FEATURES.get(vol["name"]))
        f = tmpd / ("%s.json" % vol["name"])
        if not f.exists():
            return None
        rs = json.loads(f.read_text())["records"]
        return rs[-1] if rs else None
    finally:
        ctx.store.DATA_DIR = ctx.store_dir_original
        shutil.rmtree(tmpd, ignore_errors=True)


def procesar_pasada(ctx, pasada, l1b, geo, tif=None, campos_a_correr=None):
    """Corre los campos sobre un par L1B/GEO ya en disco y devuelve la fila de salida (dict)."""
    from pipeline.geo_utils import get_detection_anchor, get_grid_center
    pv, cp, cap = ctx.pv, ctx.cp, ctx.cap
    vol = ctx.vols[pasada["vol"]]
    ancla = get_detection_anchor(vol); centro_grilla = get_grid_center(vol)
    fila = {"clave": pasada["clave"], "grupo": pasada["grupo"], "lote": pasada.get("lote"),
            "granule_ab": pasada.get("granule"), "granule_usado": Path(l1b).name,
            "mismo_granulo_que_ab": Path(l1b).name == pasada.get("granule"),
            "ancla": ancla, "centro_grilla": centro_grilla, "campos": {}, "corridas": {},
            "validacion_tif": {}, "errores": [], "puntos_objetivo": puntos_objetivo(pasada)}
    for campo, corridas in CORRIDAS.items():
        if campos_a_correr and campo not in campos_a_correr:
            continue
        deposito = {}
        for (nombre_c, conectiva, compuerta) in corridas:
            clave_c = "%s|%s" % (campo, nombre_c)
            try:
                pv.ENABLE_TESTS_23_PROSE_BRANCH = (conectiva == "max")
                pv.ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 = (not compuerta)
                if campo == "nativo":
                    pv.ENABLE_UTM_REGRID = False
                    pv._regrid_viirs_granule = ctx.real_regrid
                    c_lat, c_lon, radio = vol["lat"], vol["lon"], vol["radius_km"]
                elif campo == "utm_nn":
                    pv.ENABLE_UTM_REGRID = True
                    pv._regrid_viirs_granule = cap.envolver_regrid(ctx.real_regrid)
                    c_lat, c_lon, radio = vol["lat"], vol["lon"], vol["radius_km"]
                else:
                    if pasada["vol"] not in ctx.plantillas:
                        raise RuntimeError("sin plantilla de grilla para %s" % pasada["vol"])
                    pv.ENABLE_UTM_REGRID = True
                    pv._regrid_viirs_granule = cap.envolver_regrid(
                        cp.hacer_regrid_tif(ctx.plantillas[pasada["vol"]], METODOS_TIF[campo], deposito))
                    c_lat, c_lon, radio = centro_grilla[0], centro_grilla[1], max(vol["radius_km"], 26.0)
                cap.capturar = (nombre_c == "max")
                if cap.capturar:
                    for k in ("fp_kw", "fp_hot", "fp_diag", "sp_kw", "sp_out_n", "sp_in_n", "geo_grilla", "fp_eti_id"):
                        cap.cap.pop(k, None)
                rec = pv.calculate_vrp(
                    l1b, geo, c_lat, c_lon, radio,
                    vent_lat=ancla[0], vent_lon=ancla[1],
                    vent_radius_km=vol.get("vent_radius_km", 4.0),
                    inner_radius_km=vol.get("inner_radius_km"),
                    exclude_zones=vol.get("exclude_zones"),
                    active_water_bodies=vol.get("active_water_bodies"),
                    lbg_global_compatible=vol.get("lbg_global_compatible", False),
                    local_kernel_bg_compatible=vol.get("local_kernel_bg", False),
                    lava_lake_magmatic=vol.get("lava_lake_magmatic", False))
                persistido = persistir(ctx, vol, rec)
                fila["corridas"][clave_c] = {"record": resumir_record(persistido),
                                             "record_crudo_none": rec is None, "persistido_none": persistido is None}
                if cap.capturar:
                    if "fp_kw" not in cap.cap:
                        raise RuntimeError("first_pass_tests_2_and_3 no corrio en %s" % clave_c)
                    g = cap.cap["geo_nativo"] if campo == "nativo" else cap.cap["geo_grilla"]
                    rng = np.random.default_rng(int(ctx.rng_master.integers(1 << 31)))
                    ev = cp.evaluar_campo(cap.cap, g["lat"], g["lon"], fila["puntos_objetivo"], rng)
                    ev["sp_out_n_real"] = cap.cap.get("sp_out_n")
                    ev["sp_in_n_real"] = cap.cap.get("sp_in_n")
                    if campo.startswith("tif_"):
                        ev["frac_celdas_con_dato"] = deposito.get("frac_celdas_con_dato")
                        ev["interp"] = deposito.get("info")
                        if tif is not None and "L_I04" in deposito:
                            fila["validacion_tif"][campo] = cp.validar_contra_tif(deposito["L_I04"], tif)
                    fila["campos"][campo] = ev
                    dmax = (ev.get("decision") or {}).get("max|con_compuerta", {})
                    dmin = (ev.get("decision") or {}).get("min|con_compuerta", {})
                    print("    %-8s n_roi %s | sd_dNTI %s | identidad 1er pase %s | obj_final max %s min %s | dc %s" % (
                        campo, ev.get("n_roi"), (ev.get("primer_pase") or {}).get("sd_dnti"),
                        ev.get("identidad_primer_pase"), dmax.get("objetivo_final"), dmin.get("objetivo_final"),
                        (persistido or {}).get("distance_class")), flush=True)
            except Exception as e:
                fila["errores"].append("%s: %s" % (clave_c, e))
                fila["corridas"].setdefault(clave_c, {})["error"] = traceback.format_exc()[-3000:]
                print("    %s FALLO: %s" % (clave_c, e), flush=True)
            finally:
                for k, v in ctx.originales.items():
                    setattr(pv, k, v)
                pv._regrid_viirs_granule = ctx.real_regrid
                cap.capturar = True
                cap.cap.pop("fp_kw", None)   # soltar los arrays del granulo entero
                cap.cap.pop("fp_hot", None)
        deposito.clear()
    fila["ok"] = not fila["errores"]
    return fila


def leer_tif(ctx, pasada, tif_dir):
    """El GeoTIFF de MIROVA pareado a la pasada (si hay y es usable), solo si esta en la grilla de la plantilla."""
    tif, tif_meta = None, {}
    if not (pasada.get("tif") and pasada["tif"].get("usable") and tif_dir is not None):
        return tif, tif_meta
    ruta_tif = Path(tif_dir) / pasada["tif"]["tif_path"]
    if not ruta_tif.exists():
        return None, {"ausente": str(ruta_tif)}
    import rasterio
    with rasterio.open(ruta_tif) as ds:
        tif = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            tif[tif == ds.nodata] = np.nan
        t = ds.transform
        tif_meta = {"crs": str(ds.crs), "forma": list(ds.shape), "ruta": pasada["tif"]["tif_path"],
                    "transform": [t.a, t.b, t.c, t.d, t.e, t.f]}
    # la validacion compara celda a celda: solo vale si el TIF esta en la MISMA grilla que la plantilla
    pl = ctx.plantillas.get(pasada["vol"]) or {}
    misma = (tif_meta["crs"] == pl.get("crs") and tif_meta["forma"] == [pl.get("alto"), pl.get("ancho")]
             and all(abs(a - b) < 1e-6 for a, b in zip(tif_meta["transform"], pl.get("transform") or [])))
    tif_meta["misma_grilla_que_plantilla"] = bool(misma)
    return (tif if misma else None), tif_meta


def main():
    guardas_de_entorno()
    import pipeline.fetch as fetch
    out_dir = Path(os.environ.get("PROBE_OUT") or (AQUI / "out")); out_dir.mkdir(parents=True, exist_ok=True)
    tif_dir = Path(os.environ["TIF_DIR"]) if os.environ.get("TIF_DIR") else None
    sel = json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))
    lote = os.environ.get("PROBE_LOTE", "").strip()
    claves = [c for c in os.environ.get("PROBE_CLAVES", "").split(";") if c.strip()]
    lista = [p for p in sel["pasadas"] if (not lote or str(p["lote"]) == lote) and (not claves or p["clave"] in claves)]
    print("sonda S150 tres campos | perfil %s | lote %r | %d pasadas" % (os.environ["VRP_PROFILE"], lote, len(lista)), flush=True)
    if not lista:
        raise SystemExit("sin pasadas para este filtro: no se mide nada")
    ctx = Contexto()
    fetch.auth()
    destino = Path(tempfile.mkdtemp(prefix="granulos_"))
    cobertura = {"lote": lote, "flags": ctx.flags, "pasadas": {}}
    for pasada in lista:
        t0 = time.time()
        dt = datetime.strptime(pasada["pasada_utc"], "%Y-%m-%d %H:%M")
        stamp = "A%d%03d.%s" % (dt.year, dt.timetuple().tm_yday, dt.strftime("%H%M"))
        nombre = "%s_%s.json" % (pasada["vol"], pasada["pasada_utc"].replace(" ", "_").replace(":", ""))
        print("=== %s [%s] %s ===" % (pasada["clave"], pasada["grupo"], stamp), flush=True)
        try:
            par = bajar_par(fetch, ctx.vols[pasada["vol"]], pasada["plataforma"], dt, stamp, destino, pasada.get("granule"))
            if par is None:
                raise RuntimeError("granulo no encontrado o no descargado")
            tif, tif_meta = leer_tif(ctx, pasada, tif_dir)
            fila = procesar_pasada(ctx, pasada, par[0], par[1], tif)
            fila["tif"] = tif_meta
            if tif_meta.get("ausente"):
                fila["errores"].append("TIF pareado ausente del checkout")
                fila["ok"] = False
        except Exception as e:
            fila = {"clave": pasada["clave"], "grupo": pasada["grupo"], "ok": False,
                    "errores": ["pasada: %s" % e], "traceback": traceback.format_exc()[-3000:]}
            print("    FALLO pasada: %s" % e, flush=True)
        finally:
            ctx.cap.limpiar_pasada()
            for p in destino.glob("*"):
                try:
                    p.unlink()
                except OSError:
                    pass
        fila["stamp"] = stamp
        fila["segundos"] = round(time.time() - t0, 1)
        fila["rss_max_mb"] = rss_max_mb()   # el piloto lee esto (DISENO §10 bis): memoria del job hasta aca
        (out_dir / nombre).write_text(json.dumps(ctx.cp.a_json(fila), ensure_ascii=False), encoding="utf-8")
        cobertura["pasadas"][pasada["clave"]] = {"ok": fila["ok"], "errores": fila["errores"][:5],
                                                 "campos": sorted(fila.get("campos", {})),
                                                 "corridas": sorted(fila.get("corridas", {}))}
        print("    %.0f s | ok=%s" % (fila["segundos"], fila["ok"]), flush=True)
    (out_dir / ("cobertura_lote_%s.json" % (lote or "x"))).write_text(
        json.dumps(cobertura, ensure_ascii=False, indent=1), encoding="utf-8")
    n_ok = sum(1 for v in cobertura["pasadas"].values() if v["ok"])
    print("COBERTURA lote %s: %d de %d pasadas completas" % (lote, n_ok, len(lista)), flush=True)
    if n_ok < len(lista):
        sys.exit(3)   # A108: un run verde tiene que haber medido todo


if __name__ == "__main__":
    main()
