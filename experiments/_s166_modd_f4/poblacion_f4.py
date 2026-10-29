# -*- coding: utf-8 -*-
"""S168, candado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §4, §5 y §11 punto 1): la POBLACIÓN del A/B.

POR QUÉ. El evaluador sellado (evaluar_f4.py) lee una población con dos tramos: C, las 5.465 pasadas MODIS nocturnas
del censo MOD-D (experiments/_s162_mxd03/poblacion.json), y E, la cola del 2026-10-17 al 2026-10-26 armada con la MISMA
regla, con la ventana como único cambio. Las dos se etiquetan con la referencia congelada posterior a D-39 (§5), porque
la referencia sellada del censo era anterior a que el consolidado recuperara 2.648 filas, entre ellas protegidas.
La etiqueta que DECIDE (`lab`) sale de la tabla sola (A119); la de tabla más OCR (`lab_union`) informa.

CÓMO SE ETIQUETA (la misma función, sin cambiar la regla). `etiquetar()` corre `poblacion_mxd03.main()` (blob de
experiments/_s162_mxd03, sin modificarlo) con cuatro cosas cambiadas desde afuera y nada más:
  - VENTANA: la del tramo (C 2026-03-01 a 2026-10-16; E 2026-10-17 a 2026-10-26);
  - bajar_remoto: devuelve las copias congeladas que este script bajó por sha (no el último commit);
  - cargar_referencia_unificada: la misma función; en el canal «tabla» se quedan sólo las filas de source CONS (la
    tabla de latest.php más su historia), en el canal «union» todas. Las capas histórica y de respaldo son las del
    checkout (como hizo S165 con estas mismas copias), salvo en el control del censo, que usa las del checkout del
    censo (reetiquetado_f4.py);
  - --salida a un temporal (no toca MANIFIESTO.json de _s162_mxd03).
El script de MxD03 sale con código 2 cuando sus tres pasadas de control no están en la ventana (tramo E): eso se
informa y no es error. Su columna `tramo` es el tramo de CENIT; aquí se renombra a `tramo_cenit`, porque el evaluador
usa `tramo` para C o E.

C se arma sobre las 5.465 claves de poblacion.json y el script exige que la ventana etiquetada traiga exactamente esas
claves. L1B y MxD03 de C son los que leyó el censo (`l1b` y `geo` de sus ab_parte*.jsonl, en
D:/vrp-trabajo/temporales/s162_modd/censo, sólo lectura); `grilla_censo` es la ruta relativa de su grilla_NNNN.npz,
presente en exactamente las 5.321 pasadas en que el port del censo corrió (port_estado ok).
E sale de data/mirova_equivalent del checkout. Su L1B y su MxD03 son los de la versión 6.1 estándar que lista CMR
(público, sin credenciales), la que pide pipeline/fetch.py primero.

COMPROBACIÓN HEAD DE E (§4). `head_e.py` hace HEAD a cada L1B y MxD03 de E y escribe head_e.json; con
`--head head_e.json` este script excluye entero cada día de E en que alguna pasada no tenga las dos URL en 200, y
las pasadas de MIROVA de ese día quedan en `sin_pasada_nuestra` (N-04). Sin --head, E queda entera y la población
lo declara (`head_e.estado = "PENDIENTE"`): esa población no es la del candado.

sin_pasada_nuestra: toda pasada MODIS nocturna de MIROVA con alerta (lectura A, protegida o bajo 1 MW; tabla más OCR,
lo conservador) en C o E sin pasada de la población a ±120 s, como [vol, dt, lab]. Siempre presente.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el etiquetado estuviera roto, ¿se vería? Sí: los controles positivos de poblacion_mxd03 en C (Láscar
   2026-03-27 07:10 protegida, dos negativos limpios) tienen que salir OK en los dos canales; las claves de C tienen
   que ser las 5.465 del censo; y reetiquetado_f4.py reproduce las etiquetas selladas con la referencia sellada.
2. Si la referencia no fuera la congelada, ¿se vería? Sí: el sha256 de cada copia se compara con el que registró S165
   para esos mismos commits (referencia_salida.txt de _s165_regla_posicion); si difiere, el script sale.

Uso (desde la raíz del checkout, árbol de data/ limpio):
    set TMP=D:\\vrp-trabajo\\temporales\\s168_candado
    python -I experiments/_s166_modd_f4/poblacion_f4.py --ref D:/vrp-trabajo/temporales/s168_candado/ref
        [--sin-bajar] [--head experiments/_s166_modd_f4/head_e.json]
Escribe poblacion_f4.json y poblacion_f4_salida.txt en esta carpeta.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

POB_CENSO = RAIZ / "experiments/_s162_mxd03/poblacion.json"
PM_RUTA = RAIZ / "experiments/_s162_mxd03/poblacion_mxd03.py"
CENSO = Path("D:/vrp-trabajo/temporales/s162_modd/censo")
VENTANA_C = ("2026-03-01", "2026-10-16")
VENTANA_E = ("2026-10-17", "2026-10-26")
NOMBRES = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv")
# §5: la referencia congelada posterior a D-39 (los commits de Mirova-v1) y el sha256 de los bytes que S165 registró
# al bajarlos (experiments/_s165_regla_posicion/referencia_salida.txt en loop/activo)
REF_F4 = {"registro_vrp_consolidado.csv": {"sha_commit": "cb91eb506c37cff0b83164dd602d8a5340277637",
                                           "sha256_s165": "811c4c07e38e55dc768197c9eb9e6e5df3659c41c39aa8f43d8e408a611f7ef4"},
          "registro_vrp_ocr.csv": {"sha_commit": "cfc57c4d8bc57c5ccd5219ff3a91749dae167b97",
                                   "sha256_s165": "01c9478d614a59017348fc7f95ae4cffc359b314d5852cf2c6d13b7f831fba6b"}}
URL_RAW = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/{nombre}"
URL_LAADS = "https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/{short}/{nombre}"
CMR = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name={short}&version=6.1"
       "&readable_granule_name={short}.{patron}*&options[readable_granule_name][pattern]=true&page_size=20")
N_GRILLAS_CENSO = 5321
TOL_S = 120


def sha256(path, lf=False):
    b = Path(path).read_bytes()
    if lf:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, text=True).stdout.strip()


def cargar_pm():
    spec = importlib.util.spec_from_file_location("poblacion_mxd03_f4", PM_RUTA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ referencia congelada
def bajar_ref(dest, ref=REF_F4, sin_bajar=False):
    """Baja cada CSV por el sha de su commit (raw.githubusercontent, público) y devuelve la procedencia."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for n in NOMBRES:
        p = dest / n
        if not sin_bajar or not p.exists():
            urllib.request.urlretrieve(URL_RAW.format(sha=ref[n]["sha_commit"], nombre=n), p)
        out[n] = {"sha_commit": ref[n]["sha_commit"], "path": str(p), "sha256": sha256(p),
                  "sha256_lf": sha256(p, lf=True), "bytes": p.stat().st_size,
                  "url": URL_RAW.format(sha=ref[n]["sha_commit"], nombre=n)}
        esperado = ref[n].get("sha256_s165")
        out[n]["igual_a_s165"] = None if esperado is None else out[n]["sha256"] == esperado
    return out


# ------------------------------------------------------------------ etiquetado (poblacion_mxd03.main sin modificar)
def etiquetar(ventana, ref, canal, historico=None, respaldo=None):
    """Corre poblacion_mxd03.main() con la ventana, la referencia y el canal dados. Devuelve (dict de la población que
    escribió ese script, log, código de salida). canal: "tabla" (sólo filas source CONS) o "union" (todas)."""
    assert canal in ("tabla", "union")
    PM = cargar_pm()
    original = PM.cargar_referencia_unificada
    info = {n: {"sha": ref[n]["sha_commit"], "path": ref[n]["path"]} for n in NOMBRES}

    def cargar(cons, ocr):
        kw = {}
        if historico is not None:
            kw["historico_path"] = Path(historico)
        if respaldo is not None:
            kw["respaldo_path"] = Path(respaldo)
        filas = original(cons, ocr, **kw)
        return [f for f in filas if f["source"] == "CONS"] if canal == "tabla" else filas

    tmpd = Path(tempfile.mkdtemp(prefix="etq_"))
    salida = tmpd / "pob.json"
    bio = io.BytesIO()
    w0 = io.TextIOWrapper(bio, encoding="utf-8")
    viejo = sys.stdout
    codigo = 0
    err = io.StringIO()
    try:
        sys.stdout = w0
        with patch.object(PM, "VENTANA", tuple(ventana)), patch.object(PM, "bajar_remoto", lambda _ref: info), \
                patch.object(PM, "cargar_referencia_unificada", cargar), \
                patch.object(sys, "argv", ["poblacion_mxd03.py", "--ref", str(tmpd), "--salida", str(salida)]), \
                contextlib.redirect_stderr(err):
            try:
                PM.main()
            except SystemExit as e:
                codigo = e.code
        sys.stdout.flush()
        log = bio.getvalue().decode("utf-8")
    finally:
        sys.stdout = viejo
    log += err.getvalue()
    if not salida.exists():
        raise RuntimeError(f"poblacion_mxd03 no escribió la población (código {codigo}):\n{log[-3000:]}")
    pob = json.loads(salida.read_text(encoding="utf-8"))
    salida.unlink()
    tmpd.rmdir()
    return pob, log, codigo


def filas_de(pob):
    out = {}
    for g in pob["granulos"]:
        for f in g["records"]:
            k = (f["vol"], f["dt"])
            if k in out:
                raise RuntimeError(f"clave (vol, dt) repetida en la población: {k}")
            out[k] = f
    return out


def controles_del_log(log):
    return [ln for ln in log.splitlines() if ln.startswith("control ")]


# ------------------------------------------------------------------ censo MOD-D (sólo lectura)
def leer_censo():
    """{(vol, dt): {"l1b", "geo", "id", "port_estado", "grilla" (ruta relativa o None)}} de los ab_parte del censo."""
    import glob
    recs, npz = {}, {}
    for a in sorted(glob.glob(str(CENSO / "run_*" / "*" / "ab_parte*.jsonl"))):
        d = Path(a).parent
        for f in d.glob("grilla_*.npz"):
            i = int(f.stem.split("_")[1])
            if i in npz:
                raise RuntimeError(f"grilla id {i} repetida: {npz[i]} y {f}")
            npz[i] = f.relative_to(CENSO).as_posix()
        for x in open(a, encoding="utf-8"):
            r = json.loads(x)
            if r.get("tipo") != "record":
                continue
            k = (r["vol"], r["dt"])
            if k in recs:
                raise RuntimeError(f"pasada repetida en el censo: {k}")
            recs[k] = {"l1b": r.get("l1b"), "geo": r.get("geo"), "id": r.get("id"), "estado": r.get("estado"),
                       "port_estado": r.get("port_estado"), "sensor": r.get("sensor")}
    for k, r in recs.items():
        r["grilla"] = npz.get(r["id"])
    return recs, npz


# ------------------------------------------------------------------ CMR (público)
def cmr_granulo(short, patron, cache):
    """Nombre y URL de descarga (link data#) del gránulo 6.1 estándar de CMR, o (None, motivo)."""
    k = (short, patron)
    if k in cache:
        return cache[k]
    u = CMR.format(short=short, patron=patron)
    ultimo = None
    for intento in range(3):           # CMR es un listado público, no la cuenta: reintentar no bloquea nada
        try:
            e = json.load(urllib.request.urlopen(u, timeout=60))["feed"]["entry"]
            break
        except Exception as ex:  # noqa: BLE001
            ultimo = ex
            time.sleep(5 * (intento + 1))
    else:
        cache[k] = (None, None, f"cmr_error: {ultimo!r}"[:200])
        return cache[k]
    cand = []
    for x in e:
        nombre = x.get("producer_granule_id") or x.get("title")
        links = [l["href"] for l in x.get("links", []) if "data#" in l.get("rel", "")
                 and l["href"].startswith("https://data.laadsdaac.earthdatacloud.nasa.gov/")]
        if nombre and links:
            cand.append((nombre, links[0]))
    cand = sorted(set(cand))
    if not cand:
        cache[k] = (None, None, "cmr_sin_granulo")
    elif len(cand) > 1:
        cache[k] = (cand[-1][0], cand[-1][1], f"cmr_varios: {[c[0] for c in cand]}")
    else:
        cache[k] = (cand[0][0], cand[0][1], None)
    return cache[k]


def url_laads(nombre):
    return URL_LAADS.format(short=nombre.split(".")[0], nombre=nombre) if nombre else None


# ------------------------------------------------------------------ MIROVA sin pasada nuestra
def alertas_mirova(ref, ventanas):
    """Pasadas MODIS nocturnas de MIROVA con alerta (lectura A, regla SN, tabla más OCR) en las ventanas, de los 11
    Tier A: {(vol, dt_minuto): {"vrp": max, "fuentes": set, "dt": datetime}}."""
    import banco_paridad as bp
    from auto_audit_weekly import _coords_por_volcan
    from referencia_mirova_unificada import cargar_referencia_unificada
    filas = cargar_referencia_unificada(Path(ref[NOMBRES[0]]["path"]), Path(ref[NOMBRES[1]]["path"]))
    coords = _coords_por_volcan()
    out = {}
    for v in ventanas:
        por_vb, _ns, _nv, _n = bp.indexar_referencia(filas, coords, v, regla_minimas="SN")
        for (vol, b), lista in por_vb.items():
            if b != "MODIS" or vol not in bp.VOLS:
                continue
            for dt, f in lista:
                if not bp.es_alerta(f["tipo"]):
                    continue
                k = (vol, f["fecha_utc"][:16])
                x = out.setdefault(k, {"vrp": 0.0, "fuentes": set(), "dt": dt})
                x["vrp"] = max(x["vrp"], f["vrp_mw"] or 0.0)
                x["fuentes"].add(f["source"])
    return out


def diagnostico_canal(ref, ventanas):
    """Control del cero de lab_union (A116): filas MODIS nocturnas de MIROVA por fuente y tipo en cada ventana, y
    cuántas alertas del OCR no tienen alerta de la tabla en su misma pasada (±120 s). Si son 0, tabla y unión dan la
    misma etiqueta en toda alerta, y un lab_union idéntico a lab no es un canal mal cableado."""
    import banco_paridad as bp
    from auto_audit_weekly import _coords_por_volcan
    from referencia_mirova_unificada import cargar_referencia_unificada
    filas = cargar_referencia_unificada(Path(ref[NOMBRES[0]]["path"]), Path(ref[NOMBRES[1]]["path"]))
    coords = _coords_por_volcan()
    out = {}
    for v in ventanas:
        por_vb, _ns, _nv, _n = bp.indexar_referencia(filas, coords, v, regla_minimas="SN")
        filas_m = [(vol, dt, f) for (vol, b), lista in por_vb.items() if b == "MODIS" and vol in bp.VOLS
                   for dt, f in lista]
        solo = [(vol, f["fecha_utc"], f["vrp_mw"]) for vol, dt, f in filas_m
                if f["source"] == "OCR" and bp.es_alerta(f["tipo"])
                and not any(g["source"] == "CONS" and bp.es_alerta(g["tipo"]) for g in bp.parear(por_vb[(vol, "MODIS")], dt))]
        out["%s a %s" % v] = {"filas": {"%s %s" % k: n for k, n in sorted(collections.Counter(
            (f["source"], f["tipo"]) for _, _, f in filas_m).items())}, "alertas_ocr_sin_alerta_de_tabla": solo}
    return out


def sin_pareja(alertas, pasadas):
    por_vol = collections.defaultdict(list)
    for p in pasadas:
        por_vol[p["vol"]].append(datetime.strptime(p["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
    out = []
    for (vol, dtm), x in sorted(alertas.items()):
        if not any(abs((t - x["dt"]).total_seconds()) <= TOL_S for t in por_vol.get(vol, ())):
            out.append({"vol": vol, "dt": dtm, "lab": "protegida" if x["vrp"] >= 1.0 else "bajo1",
                        "vrp_mirova": x["vrp"], "fuentes": sorted(x["fuentes"])})
    return out


# ------------------------------------------------------------------ armado
CAMPOS_PM = ("noche", "sensor", "granule", "clave", "z", "az", "lado", "inner", "codigo_sha", "product_version",
             "pub_guardada", "pc_vrp_guardada", "dc_guardada", "pc_dist_guardada", "expuesta", "partida", "r_nulos")


def pasada(tramo, ft, fu):
    """Fila de la población desde las dos etiquetadas (tabla ft, unión fu) de la misma pasada."""
    p = {"vol": ft["vol"], "dt": ft["dt"], "tramo": tramo, **{k: ft.get(k) for k in CAMPOS_PM},
         "tramo_cenit": ft.get("tramo"), "lab": ft["lab"]}
    p["granule_guardado"] = p.pop("granule")
    vt, vu = ft.get("vrp_mirova"), fu.get("vrp_mirova")
    if fu["lab"] != ft["lab"]:
        p["lab_union"] = fu["lab"]
    # el VRP de MIROVA que usa el evaluador (M, razón, curvas) va con la etiqueta que decide (tabla); si la tabla no
    # trae alerta y la unión sí, se pone el de la unión (sólo lo lee P1 para informar la pérdida sólo OCR)
    p["vrp_mirova"] = vt if ft["lab"] in ("protegida", "bajo1") else vu
    if vu != p["vrp_mirova"]:
        p["vrp_mirova_union"] = vu
    return p


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="carpeta para las copias congeladas de la referencia")
    ap.add_argument("--sin-bajar", action="store_true", help="usa las copias ya bajadas (verifica su sha256)")
    ap.add_argument("--head", default=None, help="head_e.json de head_e.py: aplica la exclusión de días de E (§4)")
    ap.add_argument("--salida", default=str(AQUI / "poblacion_f4.json"))
    a = ap.parse_args()
    t0 = time.time()
    L = []

    def pr(*x):
        s = " ".join(str(v) for v in x)
        L.append(s)
        print(s, flush=True)

    pr("poblacion_f4.py | hora del servidor local UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    head_sha = git("rev-parse", "HEAD")
    sucio = git("status", "--porcelain", "--", "data/mirova_equivalent", "pipeline", "scripts", "frontend",
                "volcanoes.yaml", "experiments/_s162_mxd03/poblacion_mxd03.py", "experiments/_s162_mxd03/poblacion.json")
    pr("checkout HEAD:", head_sha, "| cambios sin commitear en data/, pipeline/, scripts/, frontend/ o el molde:",
       bool(sucio))
    if sucio:
        sys.exit("la población tiene que salir de un checkout sin cambios locales en esas rutas")
    blob_pm = git("hash-object", str(PM_RUTA))
    blob_pm_head = git("rev-parse", f"HEAD:{PM_RUTA.relative_to(RAIZ).as_posix()}")
    pr("poblacion_mxd03.py blob:", blob_pm, "| igual al de HEAD:", blob_pm == blob_pm_head)

    # ---------------- 1. referencia congelada
    ref = bajar_ref(a.ref, sin_bajar=a.sin_bajar)
    for n in NOMBRES:
        r = ref[n]
        pr(f"referencia {n}: commit {r['sha_commit']} sha256 {r['sha256']} (LF {r['sha256_lf']}) "
           f"{r['bytes']} bytes | igual al sha256 de S165: {r['igual_a_s165']}")
    if not all(ref[n]["igual_a_s165"] for n in NOMBRES):
        sys.exit("la copia bajada no es la que registró S165 para ese commit")
    from referencia_mirova_unificada import HISTORICO_RECUPERADAS, RESPALDO_20260408
    capas = {}
    for nom, p in (("historico", HISTORICO_RECUPERADAS), ("respaldo", RESPALDO_20260408)):
        capas[nom] = {"ruta": p.relative_to(RAIZ).as_posix(), "sha256_lf": sha256(p, lf=True),
                      "blob_head": git("rev-parse", f"HEAD:{p.relative_to(RAIZ).as_posix()}")}
    pr("capas de la referencia unificada (del checkout, como en S165):", json.dumps(capas, ensure_ascii=False))

    # ---------------- 2. etiquetado de C y E en los dos canales
    et = {}
    for tramo, ven in (("C", VENTANA_C), ("E", VENTANA_E)):
        for canal in ("tabla", "union"):
            t1 = time.time()
            pob, log, cod = etiquetar(ven, ref, canal)
            et[(tramo, canal)] = filas_de(pob)
            ctl = controles_del_log(log)
            por = collections.Counter(f["lab"] for f in et[(tramo, canal)].values())
            pr(f"etiquetado {tramo} {canal} {ven[0]} a {ven[1]}: {len(et[(tramo, canal)])} pasadas, código {cod}, "
               f"{time.time() - t1:.0f} s | etiquetas {dict(sorted(por.items()))}")
            for c in ctl:
                pr("    ", c)
            if tramo == "C" and (cod != 0 or not ctl or any("FALLA" in c for c in ctl)):
                sys.exit(f"los controles de poblacion_mxd03 fallan en C ({canal}): {ctl}")
            if set(et[(tramo, "tabla")] if canal == "union" else et[(tramo, canal)]) != set(et[(tramo, canal)]):
                sys.exit(f"las claves de {tramo} cambian entre canales")

    # ---------------- 3. tramo C sobre el censo
    pob_censo = json.load(open(POB_CENSO, encoding="utf-8"))
    cen = filas_de(pob_censo)
    pr("censo (experiments/_s162_mxd03/poblacion.json):", len(cen), "pasadas; checkout", pob_censo["checkout"])
    if set(cen) != set(et[("C", "tabla")]):
        sys.exit(f"C etiquetada no trae las claves del censo: faltan {sorted(set(cen) - set(et[('C', 'tabla')]))[:5]} "
                 f"sobran {sorted(set(et[('C', 'tabla')]) - set(cen))[:5]}")
    ab, npz = leer_censo()
    pr("censo MOD-D (ab_parte*.jsonl):", len(ab), "records;", len(npz), "grillas npz;",
       dict(collections.Counter(r["port_estado"] for r in ab.values())))
    if set(ab) != set(cen):
        sys.exit("las pasadas de los ab_parte del censo no son las de poblacion.json")
    con_grilla = {k for k, r in ab.items() if r["grilla"]}
    port_ok = {k for k, r in ab.items() if r["port_estado"] == "ok"}
    pr("pasadas con grilla del censo:", len(con_grilla), "| con port_estado ok:", len(port_ok),
       "| iguales:", con_grilla == port_ok)
    if len(con_grilla) != N_GRILLAS_CENSO or con_grilla != port_ok or len(npz) != N_GRILLAS_CENSO:
        sys.exit("el censo no trae exactamente las 5.321 grillas en las pasadas con port ok")
    l1b_dist = sum(1 for k in cen if ab[k]["l1b"] != cen[k]["granule"])
    pr("pasadas de C cuyo L1B del censo difiere del granule de poblacion.json:", l1b_dist)

    pasadas, cambios = [], []
    for k in sorted(cen):
        p = pasada("C", et[("C", "tabla")][k], et[("C", "union")][k])
        r = ab[k]
        p.update({"lab_censo": cen[k]["lab"], "vrp_mirova_censo": cen[k]["vrp_mirova"],
                  "grilla_censo": r["grilla"] or False, "id_censo": r["id"], "l1b": r["l1b"], "geo": r["geo"],
                  "url_l1b": url_laads(r["l1b"]), "url_geo": url_laads(r["geo"])})
        if p["lab"] != cen[k]["lab"] or p.get("lab_union", p["lab"]) != cen[k]["lab"]:
            cambios.append({"vol": k[0], "dt": k[1], "censo": cen[k]["lab"], "lab": p["lab"],
                            "lab_union": p.get("lab_union", p["lab"]), "vrp_mirova": p["vrp_mirova"],
                            "vrp_mirova_censo": cen[k]["vrp_mirova"]})
        pasadas.append(p)

    # ---------------- 4. tramo E (data/ del checkout, L1B y MxD03 de CMR)
    cache = {}
    e_cand = []
    for k in sorted(et[("E", "tabla")]):
        p = pasada("E", et[("E", "tabla")][k], et[("E", "union")][k])
        prod, patron = p["clave"].split(".", 1)
        l1b, u1, m1 = cmr_granulo(prod, patron, cache)
        geo, u2, m2 = cmr_granulo(prod.replace("021KM", "03"), patron, cache)
        p.update({"grilla_censo": False, "l1b": l1b, "geo": geo, "url_l1b": u1, "url_geo": u2,
                  "cmr_aviso": [m for m in (m1, m2) if m] or None,
                  "l1b_distinto_del_guardado": bool(l1b) and l1b != p["granule_guardado"]})
        e_cand.append(p)
    pr(f"E candidatas: {len(e_cand)} pasadas en {len({p['clave'] for p in e_cand})} gránulos; sin L1B en CMR "
       f"{sum(1 for p in e_cand if not p['url_l1b'])}, sin MxD03 {sum(1 for p in e_cand if not p['url_geo'])}; "
       f"L1B de CMR distinto del granule guardado {sum(1 for p in e_cand if p['l1b_distinto_del_guardado'])}; "
       f"avisos CMR {sum(1 for p in e_cand if p['cmr_aviso'])}")
    pr("E candidatas por día:", dict(sorted(collections.Counter(p["dt"][:10] for p in e_cand).items())))

    # ---------------- 5. HEAD de E (§4)
    excluidos = {}
    if a.head:
        h = json.load(open(a.head, encoding="utf-8"))
        pr("head_e:", a.head, "| modo", h.get("modo"), "| hora UTC", h.get("hora_utc"), "| controles",
           {k: v.get("estado") for k, v in (h.get("controles") or {}).items()})
        if any(v.get("estado") != "OK" for v in (h.get("controles") or {}).values()) or not h.get("controles"):
            sys.exit("los controles de head_e.json no están en OK: la comprobación no vale")
        urls = h["urls"]
        faltan = sorted({u for p in e_cand for u in (p["url_l1b"], p["url_geo"]) if u and u not in urls})
        if faltan:
            sys.exit(f"head_e.json no cubre {len(faltan)} URL de E (otra población): {faltan[:3]}")
        por_dia = collections.defaultdict(list)
        for p in e_cand:
            for lado, u in (("L1B", p["url_l1b"]), ("MxD03", p["url_geo"])):
                st = urls[u]["status"] if u else None
                if st != 200:
                    por_dia[p["dt"][:10]].append({"vol": p["vol"], "dt": p["dt"], "archivo": lado,
                                                  "url": u, "status": st, "error": (urls.get(u) or {}).get("error")})
        excluidos = {d: v for d, v in sorted(por_dia.items())}
        estado_head = "APLICADO"
    else:
        estado_head = "PENDIENTE"
        pr("SIN --head: E queda entera y la población NO es la del candado (head_e.estado = PENDIENTE)")
    for d, v in excluidos.items():
        pr(f"día de E excluido {d}: {len(v)} archivos sin 200, p. ej. {v[0]}")
    e_final = [p for p in e_cand if p["dt"][:10] not in excluidos]
    pasadas += e_final

    canal = diagnostico_canal(ref, (VENTANA_C, VENTANA_E))
    for v, d in canal.items():
        pr(f"canal {v}: filas MODIS nocturnas {d['filas']} | alertas OCR sin alerta de la tabla en su pasada: "
           f"{len(d['alertas_ocr_sin_alerta_de_tabla'])} {d['alertas_ocr_sin_alerta_de_tabla'][:5]}")

    # ---------------- 6. MIROVA sin pasada nuestra
    al = alertas_mirova(ref, (VENTANA_C, VENTANA_E))
    sin = sin_pareja(al, pasadas)
    sin_antes = sin_pareja(al, pasadas + [p for p in e_cand if p["dt"][:10] in excluidos])
    pr(f"alertas MODIS nocturnas de MIROVA (tabla más OCR) en C y E: {len(al)}; sin pasada de la población a ±120 s: "
       f"{len(sin)} (antes de excluir días de E: {len(sin_antes)})")
    for x in sin:
        pr("    sin pasada nuestra:", json.dumps(x, ensure_ascii=False))

    # ---------------- 7. resumen y escritura
    for t in ("C", "E"):
        pt = [p for p in pasadas if p["tramo"] == t]
        pr(f"tramo {t}: {len(pt)} pasadas | lab {dict(sorted(collections.Counter(p['lab'] for p in pt).items()))} "
           f"| lab_union distinta en {sum(1 for p in pt if 'lab_union' in p)} "
           f"| con grilla_censo {sum(1 for p in pt if p['grilla_censo'])}")
    pr("cambios de etiqueta de C contra el censo:", len(cambios))
    tr = collections.Counter((c["censo"], c["lab"], c["lab_union"]) for c in cambios)
    for (c0, c1, c2), n in sorted(tr.items()):
        pr(f"    censo {c0} -> lab {c1} / lab_union {c2}: {n}")
    for c in cambios if len(cambios) <= 50 else [c for c in cambios if "protegida" in (c["censo"], c["lab"],
                                                                                         c["lab_union"])]:
        pr("    cambio:", json.dumps(c, ensure_ascii=False))
    prot = [p for p in pasadas if p["lab"] == "protegida"]
    prot_u = [p for p in pasadas if p.get("lab_union", p["lab"]) == "protegida"]
    pr(f"protegidas (tabla): C {sum(1 for p in prot if p['tramo'] == 'C')}, E {sum(1 for p in prot if p['tramo'] == 'E')}"
       f" | protegidas de la unión: {len(prot_u)} (sólo OCR: {sum(1 for p in prot_u if p['lab'] != 'protegida')})")
    for p in prot:
        if p["tramo"] == "E":
            pr("    protegida de E:", p["vol"], p["dt"], p["vrp_mirova"], "z", p["z"])
    claves = [(p["vol"], p["dt"]) for p in pasadas]
    if len(claves) != len(set(claves)):
        sys.exit("claves repetidas en la población final")

    PM = cargar_pm()
    gran = collections.defaultdict(list)
    for p in pasadas:
        gran[p["clave"]].append(p)
    granulos = [{"clave": c, "pasadas": sorted((p["vol"], p["dt"]) for p in v)} for c, v in sorted(gran.items())]
    partes, carga = PM.partir([{"clave": g["clave"], "records": gran[g["clave"]]} for g in granulos], 24)

    out = {
        "pre_registro": "experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md (sellado, tag s168-modd-f4-sellado), §4 y §5",
        "checkout": head_sha, "generado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "ventanas": {"C": VENTANA_C, "E": VENTANA_E}, "tol_s": TOL_S, "regla_minimas": "SN",
        "etiquetador": {"script": PM_RUTA.relative_to(RAIZ).as_posix(), "blob": blob_pm,
                        "canal_lab": "tabla (filas source CONS)", "canal_lab_union": "tabla más OCR"},
        "referencia": {n: {k: ref[n][k] for k in ("sha_commit", "sha256", "sha256_lf", "bytes", "url")}
                       for n in NOMBRES},
        "capas_referencia": capas,
        "head_e": {"estado": estado_head, "archivo": a.head, "dias_excluidos": sorted(excluidos),
                   "detalle_excluidos": excluidos},
        "dias_e_excluidos": sorted(excluidos),
        "pasadas": pasadas,
        "sin_pasada_nuestra": [[x["vol"], x["dt"], x["lab"]] for x in sin],
        "sin_pasada_nuestra_detalle": sin,
        "cambios_etiqueta_C": cambios,
        "diagnostico_canal": canal,
        "e_candidatas": e_cand,
        "granulos": granulos, "partes": partes, "carga_partes": carga,
        "conteos": {"C": sum(1 for p in pasadas if p["tramo"] == "C"),
                    "E": sum(1 for p in pasadas if p["tramo"] == "E"),
                    "E_candidatas": len(e_cand),
                    "grilla_censo": sum(1 for p in pasadas if p["grilla_censo"]),
                    "cambios_etiqueta_C": len(cambios), "sin_pasada_nuestra": len(sin)},
    }
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=0, default=sorted), encoding="utf-8")
    pr("escrito", a.salida, "| sha256", sha256(a.salida), f"| {time.time() - t0:.0f} s")
    (AQUI / "poblacion_f4_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
