"""S136 - bateria de conformidad contra los NUEVE casos del Apendice A de Coppola 2016a.

POR QUE. El paper que este proyecto clona trae su propio conjunto de validacion: nueve escenas
con fecha exacta y veredicto del autor, SEIS donde el algoritmo detecta y TRES donde
deliberadamente NO detecta. En 136 sesiones nunca se uso. Para una mision de clon literal los
negativos valen tanto como los positivos: si detectamos donde el autor no detecta, eso es
sobre-deteccion estructural medida contra su referencia, que es el frente del artefacto.

QUE MIDE. Por caso: si alguna pasada nocturna de MODIS publica un cumulo dentro del ROI del
crater. Positivo => debe publicar. Negativo => NO debe publicar nada.

GEOMETRIA UNIFORME, y es deliberado: inner_radius_km = 5 para los nueve, que es el ROI1 del
paper (D18), igual para todos los objetivos. No hay valores oficiales de MIROVA por volcan para
los ocho extranjeros, e inventarlos seria el parche per-volcan que MISSION prohibe. Por eso la
bateria corre Villarrica tambien con geometria uniforme, aunque su caso ya se verifico con la
configuracion operacional del volcan (run 34281070800, CONFORME).

CONTROL DE VALIDEZ. Donde el paper da el NTI de la anomalia (A5 -0,91 / A6 -0,93 / A8 -0,9) se
exige que alguna pasada nocturna caiga a +-0,06 de ese valor; si no, no estamos mirando su escena
y el caso queda INDETERMINADO, no NO CONFORME. Donde el paper no da numero, no hay control y se
declara asi.

READ-ONLY: solo llama a calculate_vrp. No escribe en data/, no toca pipeline/ ni ningun perfil.
Corre en Actions porque MODIS necesita HDF4.
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

import yaml  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
import pipeline.process_modis as pm  # noqa: E402
import pipeline.profile as P  # noqa: E402

INNER_KM = 5.0          # ROI1 del paper (D18), uniforme
RADIUS_KM = 25.0        # replica la grilla 51x51 km
TOL_NTI = 0.06          # banda del control de validez alrededor del NTI que da el paper
DEST = Path(os.environ.get("VRP_DEST", "/tmp/apendice"))
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


def nti_de(rec):
    """A89: MODIS persiste `diag_nti_max`; `nti_max` es el nombre de VIIRS y da None."""
    v = rec.get("diag_nti_max")
    return v if v is not None else rec.get("nti_max")


def correr_caso(caso, is_nighttime):
    dt_dia = datetime.strptime(caso["fecha"], "%Y-%m-%d")
    print(f"\n{'='*84}\n{caso['caso']}, {caso['name']}, {caso['fecha']}, "
          f"el paper: {caso['veredicto'].upper()}\n{'='*84}", flush=True)
    pasadas = []
    for l1b_key, geo_key in PARES:
        try:
            grs = search_granules(l1b_key, caso["lat"], caso["lon"], RADIUS_KM, dt_dia)
        except Exception as e:
            print(f"  {l1b_key}: BUSQUEDA FALLO, {e}", flush=True)
            continue
        print(f"  {l1b_key}: {len(grs)} granules ese dia", flush=True)
        for g in grs:
            nom, ini = gname(g), ginicio(g)
            if ini is None:
                continue
            if not is_nighttime(caso["lat"], caso["lon"], ini):
                print(f"    {nom}  {ini}  diurna, fuera del universo", flush=True)
                continue
            try:
                l1b = [Path(p) for p in download_granules([g], DEST)]
                if not l1b:
                    print(f"    {nom}  descarga vacia", flush=True)
                    continue
                gg = search_granules(geo_key, caso["lat"], caso["lon"], RADIUS_KM, dt_dia)
                sel = [x for x in gg if ini.strftime("%H%M") in gname(x)]
                geo = [Path(p) for p in download_granules(sel[:1], DEST)] if sel else [None]
                rec = pm.calculate_vrp(
                    l1b[0], geo[0] if geo else None,
                    caso["lat"], caso["lon"], RADIUS_KM,
                    vent_lat=caso["lat"], vent_lon=caso["lon"],
                    vent_radius_km=4.0, inner_radius_km=INNER_KM,
                    exclude_zones=None, active_water_bodies=None,
                    lbg_global_compatible=False, local_kernel_bg_compatible=False,
                )
            except Exception as e:
                print(f"    {nom}  EXCEPCION: {e}", flush=True)
                traceback.print_exc()
                continue
            if rec is None:
                print(f"    {nom}  {ini}  calculate_vrp -> None", flush=True)
                continue
            pc = rec.get("primary_cluster") or {}
            clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
            d = hav(clat, clon, caso["lat"], caso["lon"]) if clat is not None else None
            f = {"granule": nom, "inicio": str(ini), "nti_max": nti_de(rec),
                 "vrp_pc_mw": pc.get("vrp_mw"), "n_pixels_pc": pc.get("n_pixels"),
                 "dist_crater_km": d, "distance_class": rec.get("distance_class"),
                 "t_bg_k": rec.get("t_bg_k"),
                 "diag_n_first_pass_pixels": rec.get("diag_n_first_pass_pixels"),
                 "diag_n_nti_path": rec.get("diag_n_nti_path"),
                 "triggered_test1": rec.get("triggered_test1")}
            pasadas.append(f)
            print(f"    {nom}  {ini}  nti_max={f['nti_max']}  vrp_pc={f['vrp_pc_mw']}  "
                  f"d_crater={None if d is None else round(d, 2)}", flush=True)
    return pasadas


def evaluar_caso(caso, pasadas):
    """Devuelve (veredicto, detalle). El control de validez puede DETENER el caso."""
    if not pasadas:
        return "INDETERMINADO", "ninguna pasada nocturna procesable de esa fecha"
    npap = caso.get("nti_paper")
    if npap is not None:
        en_banda = [p for p in pasadas
                    if isinstance(p["nti_max"], (int, float))
                    and abs(p["nti_max"] - npap) <= TOL_NTI]
        if not en_banda:
            vistos = [p["nti_max"] for p in pasadas]
            return ("INDETERMINADO",
                    f"control de validez: el paper da NTI {npap} y ninguna pasada cae a "
                    f"+-{TOL_NTI} (vistos {vistos}). No es su escena; nada mas es interpretable")
        pasadas = en_banda
    publica = [p for p in pasadas
               if (p.get("vrp_pc_mw") or 0) > 0 and p.get("dist_crater_km") is not None
               and p["dist_crater_km"] <= INNER_KM]
    if caso["veredicto"] == "detecta":
        if publica:
            return "CONFORME", f"publica en {len(publica)} de {len(pasadas)} pasadas utiles"
        return ("NO CONFORME (falso negativo)",
                f"el paper detecta y nosotros no publicamos en ninguna de {len(pasadas)}")
    if publica:
        mx = max(p["vrp_pc_mw"] for p in publica)
        return ("NO CONFORME (falso positivo)",
                f"el paper NO detecta y nosotros publicamos en {len(publica)} de "
                f"{len(pasadas)} pasadas, hasta {mx:.3f} MW, sobre-deteccion")
    return "CONFORME", f"no publicamos nada, como el paper, en {len(pasadas)} pasadas"


def _si(valor):
    return (valor or "").strip().lower() in ("1", "true", "si")


def brazo_desde_env(env):
    """Que brazo corre y donde escribe, a partir de las variables de entorno.

    Dos ejes independientes:
      APENDICE_PROSA  (S136) conectiva de los Tests 2/3: max en vez de min.
      APENDICE_B22    (S137) banda MIR primaria: B22, como el paper (banda L21ok), en vez de B21.
    POR QUE B22. El probe de S137 (experiments/_s137/RESULTADO_SIGMA_DNTI.md) midio que con B21
    unos 60 pixeles por escena pasan el primer paso por ruido de cuantizacion, y con B22 casi
    ninguno. Esta bateria es la unica referencia que puede decir si lo que desaparece era ruido o
    senal, porque trae los veredictos del autor.
    Cada combinacion escribe en su propio directorio: los brazos no se pisan entre si (A93).
    """
    prosa, b22 = _si(env.get("APENDICE_PROSA")), _si(env.get("APENDICE_B22"))
    nombre = "out_apendice" + ("_b22" if b22 else "") + ("_prosa" if prosa else "")
    return {"prosa": prosa, "b22": b22, "out": nombre}


def main():
    from run_pipeline import is_nighttime
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    DEST.mkdir(parents=True, exist_ok=True)
    # Brazos (S136 conectiva, S137 banda). Patron A75: se reasigna el flag en el NAMESPACE del
    # procesador, que es de donde el codigo lo lee; no se edita ningun modulo ni perfil.
    brazo = brazo_desde_env(os.environ)
    prosa = brazo["prosa"]
    if prosa:
        pm.ENABLE_TESTS_23_PROSE_BRANCH = True
    if brazo["b22"]:
        pm.ENABLE_MODIS_B22_PRIMARY = True
    casos = yaml.safe_load((HERE / "apendice_a.yaml").read_text(encoding="utf-8"))["casos"]
    solo = (os.environ.get("APENDICE_CASO") or "").strip()
    if solo:
        casos = [c for c in casos if c["caso"] == solo or c["name"] == solo]
    print(f"BATERIA DE CONFORMIDAD, Apendice A de Coppola 2016a, {len(casos)} casos")
    print(f"perfil={os.environ['VRP_PROFILE']}  inner={INNER_KM} km (ROI1 del paper, uniforme)  "
          f"exclude_zones={P.ENABLE_EXCLUDE_ZONES}")
    print(f"conectiva Tests 2/3: {'PROSA  max(C1, mu+C2*sigma)' if prosa else 'FORMULA  min(C1, mu+C2*sigma)'}"
          f"   (flag efectivo en el procesador: {pm.ENABLE_TESTS_23_PROSE_BRANCH})")
    print(f"banda MIR primaria: {'B22, como el paper' if brazo['b22'] else 'B21, lo de hoy'}"
          f"   (flag efectivo en el procesador: {pm.ENABLE_MODIS_B22_PRIMARY})"
          f"   salida: {brazo['out']}/")
    auth()
    salida = []
    for c in casos:
        try:
            pas = correr_caso(c, is_nighttime)
        except Exception as e:
            print(f"  EXCEPCION en el caso: {e}", flush=True)
            traceback.print_exc()
            pas = []
        ver, det = evaluar_caso(c, pas)
        print(f"  >>> {c['caso']} {c['name']}: {ver}, {det}", flush=True)
        salida.append({"caso": c["caso"], "name": c["name"], "fecha": c["fecha"],
                       "veredicto_paper": c["veredicto"], "nti_paper": c.get("nti_paper"),
                       "resultado": ver, "detalle": det, "pasadas": pas})
    out = HERE / brazo["out"]
    out.mkdir(exist_ok=True)
    (out / "resultado_apendice.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*84}\nRESUMEN\n{'='*84}")
    print(f"{'caso':6s} {'volcan':18s} {'fecha':12s} {'paper':12s} resultado")
    print("-" * 84)
    for s in salida:
        print(f"{s['caso']:6s} {s['name']:18s} {s['fecha']:12s} "
              f"{s['veredicto_paper']:12s} {s['resultado']}")
    conf = sum(1 for s in salida if s["resultado"] == "CONFORME")
    ind = sum(1 for s in salida if s["resultado"] == "INDETERMINADO")
    fp = sum(1 for s in salida if "falso positivo" in s["resultado"])
    fn = sum(1 for s in salida if "falso negativo" in s["resultado"])
    print(f"\nCONFORME {conf} · falso positivo {fp} · falso negativo {fn} · "
          f"indeterminado {ind}  (de {len(salida)})")
    if fp:
        print("\nUn falso positivo es sobre-deteccion medida contra la referencia del autor:")
        print("detectamos donde el algoritmo original no detecta. Es el frente del artefacto.")


if __name__ == "__main__":
    main()
