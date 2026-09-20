"""S146 - bateria del Apendice A de Coppola 2016a, UN brazo por corrida, guardando todo lo que S136
descartaba: todos los cumulos por pasada y la lista de pixeles alertados con su camino.

QUE HACE. Lo mismo que experiments/_s136/conformidad_apendice.py (mismo universo de pasadas, mismos
argumentos de calculate_vrp, mismo predicado, importado de ese archivo y no copiado), mas:
  - por pasada: `cumulos` (todos, con posicion, magnitud y n de pixeles) y `pixeles_alertados`
    (lat, lon, magnitud, caminos), capturados por experiments/_s146_bateria/captura.py;
  - por caso: `intentos`, una fila por granulo nocturno con su desenlace, para que la cobertura se
    pueda contar y comparar entre brazos (A108: un run verde no prueba cobertura pareja);
  - termina con codigo distinto de cero cuando algo no se midio, en vez de salir verde.

SOLO LECTURA (A75): no edita pipeline/ ni perfiles ni data/. Los brazos se arman reasignando flags y
funciones en el namespace de pipeline.process_modis, igual que S136 y S137. Escribe unicamente en
experiments/_s146_bateria/out/<brazo>/. Corre en GitHub Actions: MODIS necesita HDF4 (pyhdf) y
credenciales Earthdata.

Entorno: BATERIA_BRAZO (nombre de brazos.py, obligatorio), APENDICE_CASO (opcional, A1..A9),
EARTHDATA_USERNAME y EARTHDATA_PASSWORD (obligatorios), VRP_DEST (descargas, fuera del repo).

Codigos de salida: 0 todo medido; 2 sin credenciales; 3 algun caso con cero granulos procesados;
4 alguna excepcion o descarga vacia; 5 la captura no cuadra con el record.

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si lo que mide estuviera roto (el brazo no aplica su variante, o la captura pierde pixeles),
    fallaria? Si: cada flag se exige existente antes de reasignarlo (AttributeError si el nombre
    cambio) y se imprime su valor efectivo leido del procesador; la captura se coteja contra el
    record en cada pasada y cualquier diferencia da salida 5.
(2) Si el instrumento estuviera muerto (secreto ausente, NASA caida, cero granulos), se veria
    distinto? Si: salidas 2, 3 y 4. Un secreto ausente en Actions llega como string vacio y no como
    error, por eso se revisa antes de autenticar.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(HERE))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import brazos as B  # noqa: E402
import captura as C  # noqa: E402

FLAGS_EXIGIDOS = ("ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY",
                  "ENABLE_LOCAL_KERNEL_BG", "first_pass_tests_2_and_3")


def cargar_s136():
    """Importa el modulo de S136 sin ejecutarlo como script: de ahi salen el predicado, el parche de
    la compuerta y las constantes, para que exista UNA sola copia de esa logica (A102)."""
    ruta = RAIZ / "experiments" / "_s136" / "conformidad_apendice.py"
    spec = importlib.util.spec_from_file_location("conformidad_apendice_s136", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def armar_brazo(pm, s136, brazo):
    for nombre in FLAGS_EXIGIDOS:
        getattr(pm, nombre)     # AttributeError si el procesador ya no tiene ese nombre
    if brazo["prosa"]:
        pm.ENABLE_TESTS_23_PROSE_BRANCH = True
    if brazo["b22"]:
        pm.ENABLE_MODIS_B22_PRIMARY = True
    if brazo["sin_compuerta"]:
        pm.first_pass_tests_2_and_3 = s136.sin_compuerta_t23(pm.first_pass_tests_2_and_3)
    if brazo["fondo_local"]:
        pm.ENABLE_LOCAL_KERNEL_BG = True   # las dos llaves: esta y el argumento por volcan
    efectivo = {"ENABLE_TESTS_23_PROSE_BRANCH": bool(pm.ENABLE_TESTS_23_PROSE_BRANCH),
                "ENABLE_MODIS_B22_PRIMARY": bool(pm.ENABLE_MODIS_B22_PRIMARY),
                "ENABLE_LOCAL_KERNEL_BG": bool(pm.ENABLE_LOCAL_KERNEL_BG),
                "local_kernel_bg_compatible": bool(brazo["fondo_local"]),
                "compuerta_t23_quitada": bool(brazo["sin_compuerta"])}
    # OJO: en produccion ENABLE_LOCAL_KERNEL_BG ya vale True; lo que decide es el argumento por
    # volcan. Lo que el brazo exige es la conjuncion, y eso es lo que se comprueba.
    esperado = {"ENABLE_TESTS_23_PROSE_BRANCH": brazo["prosa"],
                "ENABLE_MODIS_B22_PRIMARY": brazo["b22"]}
    for k, v in esperado.items():
        if efectivo[k] != v:
            raise RuntimeError(f"brazo {brazo['nombre']}: {k} efectivo={efectivo[k]} y se esperaba {v}. "
                               f"El perfil cambio desde S137; este brazo ya no es el que dice ser.")
    return efectivo


def correr_caso(caso, is_nighttime, pm, s136, fetch, cap, dest, fondo_local):
    dt_dia = datetime.strptime(caso["fecha"], "%Y-%m-%d")
    print(f"\n{'=' * 84}\n{caso['caso']}, {caso['name']}, {caso['fecha']}, "
          f"el paper: {caso['veredicto'].upper()}\n{'=' * 84}", flush=True)
    pasadas, intentos = [], []
    for l1b_key, geo_key in s136.PARES:
        try:
            grs = fetch.search_granules(l1b_key, caso["lat"], caso["lon"], s136.RADIUS_KM, dt_dia)
        except Exception as e:
            print(f"  {l1b_key}: BUSQUEDA FALLO, {e}", flush=True)
            intentos.append({"granule": l1b_key, "estado": "busqueda_fallo", "detalle": str(e)[:300]})
            continue
        print(f"  {l1b_key}: {len(grs)} granules ese dia", flush=True)
        for g in grs:
            nom, ini = s136.gname(g), s136.ginicio(g)
            if ini is None:
                intentos.append({"granule": nom, "estado": "sin_hora"})
                continue
            if not is_nighttime(caso["lat"], caso["lon"], ini):
                print(f"    {nom}  {ini}  diurna, fuera del universo", flush=True)
                continue
            cap.reset()
            try:
                l1b = [Path(p) for p in fetch.download_granules([g], dest)]
                if not l1b:
                    print(f"    {nom}  descarga vacia", flush=True)
                    intentos.append({"granule": nom, "inicio": str(ini), "estado": "descarga_vacia"})
                    continue
                gg = fetch.search_granules(geo_key, caso["lat"], caso["lon"], s136.RADIUS_KM, dt_dia)
                sel = [x for x in gg if ini.strftime("%H%M") in s136.gname(x)]
                geo = [Path(p) for p in fetch.download_granules(sel[:1], dest)] if sel else [None]
                rec = pm.calculate_vrp(
                    l1b[0], geo[0] if geo else None,
                    caso["lat"], caso["lon"], s136.RADIUS_KM,
                    vent_lat=caso["lat"], vent_lon=caso["lon"],
                    vent_radius_km=4.0, inner_radius_km=s136.INNER_KM,
                    exclude_zones=None, active_water_bodies=None,
                    lbg_global_compatible=False, local_kernel_bg_compatible=fondo_local,
                )
            except Exception as e:
                print(f"    {nom}  EXCEPCION: {e}", flush=True)
                traceback.print_exc()
                intentos.append({"granule": nom, "inicio": str(ini), "estado": "excepcion",
                                 "detalle": str(e)[:300]})
                continue
            if rec is None:
                print(f"    {nom}  {ini}  calculate_vrp -> None", flush=True)
                intentos.append({"granule": nom, "inicio": str(ini), "estado": "procesada_none"})
                continue
            cumulos, pixeles, publicada, disc = C.extraer(cap, rec, caso["lat"], caso["lon"])
            pc = rec.get("primary_cluster") or {}
            clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
            d = s136.hav(clat, clon, caso["lat"], caso["lon"]) if clat is not None else None
            f = {"granule": nom, "inicio": str(ini), "nti_max": s136.nti_de(rec),
                 "vrp_pc_mw": pc.get("vrp_mw"), "n_pixels_pc": pc.get("n_pixels"),
                 "pc_lat": clat, "pc_lon": clon,
                 "dist_crater_km": d, "distance_class": rec.get("distance_class"),
                 "t_bg_k": rec.get("t_bg_k"),
                 "diag_n_first_pass_pixels": rec.get("diag_n_first_pass_pixels"),
                 "diag_n_nti_path": rec.get("diag_n_nti_path"),
                 "triggered_test1": rec.get("triggered_test1"),
                 # --- lo nuevo de S146 ---
                 "final_hotspot_source": rec.get("final_hotspot_source"),
                 "n_anomalous_pixels": rec.get("n_anomalous_pixels"),
                 "vrp_escena_mw": rec.get("vrp_mw"),
                 "pc_d9_capped": bool(pc.get("d9_capped")),
                 "llamada_publicada": publicada,
                 "cumulos": cumulos,
                 "pixeles_alertados": pixeles,
                 "captura_discrepancias": disc}
            pasadas.append(f)
            intentos.append({"granule": nom, "inicio": str(ini), "estado": "procesada"})
            print(f"    {nom}  {ini}  nti_max={f['nti_max']}  vrp_pc={f['vrp_pc_mw']}  "
                  f"d_crater={None if d is None else round(d, 2)}  cumulos={len(cumulos)}  "
                  f"pixeles={len(pixeles)}  publicada={publicada}"
                  + (f"  CAPTURA NO CUADRA: {disc}" if disc else ""), flush=True)
    return pasadas, intentos


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    brazo = B.por_nombre((os.environ.get("BATERIA_BRAZO") or "").strip())
    if not (os.environ.get("EARTHDATA_USERNAME") or "").strip() \
            or not (os.environ.get("EARTHDATA_PASSWORD") or "").strip():
        print("ERROR: EARTHDATA_USERNAME o EARTHDATA_PASSWORD vacios. En Actions un secreto ausente "
              "llega como string vacio; sin credenciales no se mide nada. Salida 2.", flush=True)
        return 2

    import yaml
    import pipeline.process_modis as pm
    import pipeline.profile as P
    from pipeline import fetch
    from run_pipeline import is_nighttime
    s136 = cargar_s136()

    efectivo = armar_brazo(pm, s136, brazo)
    cap = C.instalar(pm)     # DESPUES de los parches del brazo
    dest = Path(os.environ.get("VRP_DEST", "/tmp/apendice_s146"))
    dest.mkdir(parents=True, exist_ok=True)

    casos = yaml.safe_load((RAIZ / "experiments/_s136/apendice_a.yaml").read_text(encoding="utf-8"))["casos"]
    solo = (os.environ.get("APENDICE_CASO") or "").strip()
    if solo:
        casos = [c for c in casos if c["caso"] == solo or c["name"] == solo]
        if not casos:
            print(f"ERROR: APENDICE_CASO={solo!r} no coincide con ningun caso. Salida 3.")
            return 3
    print(f"BATERIA S146, Apendice A de Coppola 2016a, {len(casos)} casos, brazo {brazo['nombre']} "
          f"({brazo['etiqueta']})")
    print(f"perfil={os.environ['VRP_PROFILE']}  inner={s136.INNER_KM} km  "
          f"exclude_zones={P.ENABLE_EXCLUDE_ZONES}")
    print(f"flags EFECTIVOS en el procesador: {efectivo}", flush=True)
    fetch.auth()

    salida, resumen_intentos = [], {}
    for c in casos:
        try:
            pas, intentos = correr_caso(c, is_nighttime, pm, s136, fetch, cap, dest,
                                        brazo["fondo_local"])
        except Exception as e:
            print(f"  EXCEPCION en el caso: {e}", flush=True)
            traceback.print_exc()
            pas, intentos = [], [{"granule": c["caso"], "estado": "excepcion", "detalle": str(e)[:300]}]
        ver, det = s136.evaluar_caso(c, pas)
        print(f"  >>> {c['caso']} {c['name']}: {ver}, {det}   (vara VIEJA de S136; la corregida la "
              f"aplica evaluar_bateria.py)", flush=True)
        salida.append({"caso": c["caso"], "name": c["name"], "fecha": c["fecha"],
                       "veredicto_paper": c["veredicto"], "nti_paper": c.get("nti_paper"),
                       "resultado": ver, "detalle": det, "pasadas": pas, "intentos": intentos})
        resumen_intentos[c["caso"]] = intentos

    out = HERE / "out" / brazo["nombre"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "resultado_apendice.json").write_text(
        json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                             text=True).stdout.strip()
    except Exception:
        sha = None
    sin_granulos = [s["caso"] for s in salida if not s["pasadas"]]
    malos = [(k, i["granule"], i["estado"]) for k, its in resumen_intentos.items() for i in its
             if i["estado"] in ("excepcion", "descarga_vacia", "busqueda_fallo", "sin_hora")]
    disc = [(s["caso"], p["granule"], p["captura_discrepancias"]) for s in salida
            for p in s["pasadas"] if p["captura_discrepancias"]]
    meta = {"brazo": brazo, "flags_efectivos": efectivo, "commit": sha,
            "corrido_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": os.environ.get("GITHUB_RUN_ID"), "caso_unico": solo or None,
            "pasadas_por_caso": {s["caso"]: len(s["pasadas"]) for s in salida},
            "casos_sin_granulos": sin_granulos, "intentos_malos": malos,
            "captura_discrepancias": disc}
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 84}\nCOBERTURA DE ESTE BRAZO (pasadas nocturnas procesadas por caso)\n{'=' * 84}")
    for s in salida:
        print(f"  {s['caso']:4s} {s['name']:18s} {len(s['pasadas'])} pasadas   {s['resultado']}")
    print(f"escrito: {out}")
    if disc:
        print(f"ERROR: la captura no cuadra con el record en {len(disc)} pasadas: {disc}. Salida 5.")
        return 5
    if malos:
        print(f"ERROR: {len(malos)} granulos no se midieron: {malos}. Salida 4.")
        return 4
    if sin_granulos:
        print(f"ERROR: casos con CERO granulos procesados: {sin_granulos}. Salida 3.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
