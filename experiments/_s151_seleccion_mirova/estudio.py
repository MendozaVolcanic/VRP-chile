# -*- coding: utf-8 -*-
"""Tarea 1.4 del loop, estudio previo al codigo: QUE objeto informa MIROVA cuando hay calor lejos del crater.

EL FENOMENO. De noche, en el recuadro de 50 x 50 km de un volcan puede haber mas de una fuente de calor: el
crater y, por ejemplo, un incendio, un salar o un campo geotermal a decenas de km. MIROVA publica una sola fila
por pasada, con un VRP y una distancia (sin acimut) desde el centro de su grilla. Nicolas decidio que la replica
reproduzca tambien lo lejano. Antes de cambiar la regla de seleccion (`vent_anchored` -> `vrp_max`) hay que saber
que hace MIROVA: si informa la anomalia mayor, la del crater cuando hay algo en el crater, la mas cercana al
centro, o todo lo alertado junto (la lectura de los papers: Campus 2022 §3.2, suma de todos los pixeles
alertados; S139: la distancia se comporta como la del pixel alertado MAS LEJANO, SOSPECHA).

EL INSTRUMENTO. El GeoTIFF de MIROVA de la misma pasada (campo de radiancia del infrarrojo medio). El calor
puntual se ve como EXCESO LOCAL: el campo menos su mediana movil (paso alto), en desvios robustos (z). Con eso:
  P1. En las 359 filas lejanas nocturnas (FALSO_POSITIVO de la tabla, VERIFICADOR_DATOS D2): hay un foco en el
      anillo a la distancia que dice el CSV? Si lo hay, su POSICION se compara con nuestros pixeles.
  P2. En las pasadas con calor en el crater y lejos a la vez, cual informa MIROVA.
  P3. Que regla de seleccion es compatible, con casos a favor y en contra.

CONTROLES QUE PUEDEN FALLAR (A110: cada uno con su nulo medido, no razonado):
  N1 umbral del foco: el p95 del maximo de z en el MISMO anillo en pasadas RUTINA (MIROVA miro y no alerto nada),
     con las distancias del CSV de las lejanas del mismo volcan y sensor. Un foco "identificado" debe superar ese
     p95. Si las lejanas no superan el nulo mas que el 5 % del nulo mismo, el TIF no ve el objeto de MIROVA.
  N2 anillo corrido: el mismo TIF con el anillo 3 km mas afuera o mas adentro. Si el foco es el de MIROVA, el
     anillo a la distancia del CSV debe ganarle a los corridos.
  N3 posicion: el foco identificado girado alrededor del centro de grilla (11 angulos, misma distancia). Nuestros
     pixeles deben coincidir con el foco real mucho mas que con los girados.
  N4 crater: el maximo de z en discos del mismo radio a 8 km del crater (4 rumbos) en el mismo raster. En las
     ALERTA el crater debe superarlo (control positivo de la georreferencia); en RUTINA no tanto.
  N5 energia: el exceso local por el coeficiente de Wooster debe correlacionar con el VRP que MIROVA publica
     (Spearman, lejanas y alertas por separado). Si no correlaciona, comparar "mayor contra menor" no vale.

Uso: python experiments/_s151_seleccion_mirova/estudio.py   (baja TIF a VRP_TIF_CACHE, fuera del repo)
Salida: estudio_salida.txt, estudio_salida.json y pasadas.csv en esta carpeta.
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import math
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (str(AQUI), str(RAIZ / "experiments" / "_s151_ab_vrp_max"), str(RAIZ / "scripts")):
    sys.path.insert(0, _p)
import comun as C  # noqa: E402  (records, anclas, banco_paridad)
import comun_tif as T  # noqa: E402
import yaml  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, cargar_referencia_unificada  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
VENTANA = ("2026-03-01", "2026-10-09")   # la del universo de 359 (sustrato.py del A/B)
N_RUTINA_POR_SENSOR = 150
SEMILLA = 151
ANG_NULO = list(range(30, 360, 30))
DESPLAZ_KM = 3.0
R_NULO_CRATER_KM = 8.0
ATRIB_K = 1.0     # |dBT| maximo para dar por verificado que el TIF es de la misma pasada (S147 midio 0,2 K)
ATRIB_NO_K = 5.0  # |dBT| sobre el cual el TIF se da por de OTRA pasada


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def centro_grilla_yaml():
    cfg = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    out = {}
    for v in cfg["volcanoes"]:
        if v["name"] in C.VOLS:
            out[v["name"]] = (v.get("mirova_center_lat", v["lat"]), v.get("mirova_center_lon", v["lon"]))
    return out


def limite_scraper(filas):
    """Corte ALERTA/FALSO_POSITIVO del scraper por volcan, despejado de los datos (S139 §8): punto medio entre la
    ALERTA mas lejana y la FALSO_POSITIVO mas cercana; si se solapan, la FALSO_POSITIVO mas cercana."""
    a, f = collections.defaultdict(list), collections.defaultdict(list)
    for r in filas:
        if r["source"] != "CONS" or (r["vrp_mw"] or 0) <= 0 or r["dist_km"] is None:
            continue
        if r["tipo"] == "ALERTA_TERMICA":
            a[r["volcano"]].append(r["dist_km"])
        elif r["tipo"] == "FALSO_POSITIVO":
            f[r["volcano"]].append(r["dist_km"])
    out = {}
    for v in C.VOLS:
        ma, mf = max(a.get(v, [0.0])), min(f.get(v, [99.0]))
        out[v] = ((ma + mf) / 2) if ma < mf else mf
    return out, {v: (max(a.get(v, [0.0])), min(f.get(v, [99.0]))) for v in C.VOLS}


def t_de(f):
    return datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def es_noche(f):
    return int(f["fecha_utc"][11:13]) < 12


def escena(rec):
    return [p for p in (rec.get("anomaly_pixels") or []) + (rec.get("discarded_anomaly_pixels") or [])
            if p.get("lat") is not None]


def medir_pasada(f, fila_tif, rec, ancla, gc, lim, inner, rec_ajeno=None):
    """Todas las medidas de una pasada sobre su TIF. Devuelve dict o None si el TIF no se puede leer.

    rec_ajeno: record nuestro de OTRA pasada del mismo volcan y sensor, para el nulo del control de atribucion."""
    b = f["sensor_bucket"]
    R = T.leer(T.ruta_tif(fila_tif), b)
    if R is None:
        return None
    o_lat, o_lon = R["clat"], R["clon"]
    d_o = T.dist_desde(R, o_lat, o_lon)
    d_cr = T.dist_desde(R, ancla[0], ancla[1])
    m = {"vol": f["volcano"], "sensor": b, "fecha_utc": f["fecha_utc"], "tipo": f["tipo"], "vrp_csv": f["vrp_mw"],
         "dist_csv": f["dist_km"], "tif": fila_tif.tif_path, "crs": R["crs"], "version_tif": fila_tif.get("_motivo"),
         "georef_centro_vs_grilla_km": float(T.dist_km(o_lat, o_lon, gc[0], gc[1])),
         "crater_en_raster": bool(d_cr.min() <= T.PX_KM[b]),
         "crater_a_centro_km": float(T.dist_km(ancla[0], ancla[1], o_lat, o_lon))}
    # crater y su nulo (N4)
    fc = T.foco_en(R, d_cr <= T.R_CRATER_KM[b])
    if fc:
        m.update(z_cr=fc[0], e_cr=T.energia_mw(R, fc[1], fc[2]),
                 cr_lat=float(R["lat"][fc[1], fc[2]]), cr_lon=float(R["lon"][fc[1], fc[2]]))
    nul = []
    for ang in (0, 90, 180, 270):
        la = ancla[0] + R_NULO_CRATER_KM * math.cos(math.radians(ang)) / 110.574
        lo = ancla[1] + R_NULO_CRATER_KM * math.sin(math.radians(ang)) / (111.320 * math.cos(math.radians(ancla[0])))
        fn = T.foco_en(R, T.dist_desde(R, la, lo) <= T.R_CRATER_KM[b])
        if fn:
            nul.append(fn[0])
    m["z_cr_nulo"] = float(np.median(nul)) if nul else None
    # objeto lejano mas fuerte de la escena: fuera del corte del scraper (medido desde el centro de grilla, como
    # lo mide el scraper) Y a mas de 5 km del crater (en Tupungatito el crater esta a 4,8 km del centro y el corte
    # es 5,0 km: sin la segunda condicion el "objeto lejano" seria el propio crater)
    ff = T.foco_en(R, (d_o > lim) & (d_cr > 5.0))
    if ff:
        m.update(z_far=ff[0], e_far=T.energia_mw(R, ff[1], ff[2]), far_lat=float(R["lat"][ff[1], ff[2]]),
                 far_lon=float(R["lon"][ff[1], ff[2]]), far_d_o=float(d_o[ff[1], ff[2]]),
                 far_d_cr=float(d_cr[ff[1], ff[2]]))
    # anillo a la distancia del CSV (para las lejanas) y anillos corridos (N2)
    d_ref = m["dist_csv"]
    if d_ref is not None and d_ref > 0:
        tol = T.TOL_ANILLO_KM[b]
        fr = T.foco_en(R, np.abs(d_o - d_ref) <= tol)
        if fr:
            m.update(z_ring=fr[0], e_ring=T.energia_mw(R, fr[1], fr[2]), ring_lat=float(R["lat"][fr[1], fr[2]]),
                     ring_lon=float(R["lon"][fr[1], fr[2]]), ring_d_cr=float(d_cr[fr[1], fr[2]]))
        corr = []
        for s in (-DESPLAZ_KM, DESPLAZ_KM):
            if d_ref + s > lim:
                fs = T.foco_en(R, np.abs(d_o - (d_ref + s)) <= tol)
                if fs:
                    corr.append(fs[0])
        m["z_ring_corrido"] = max(corr) if corr else None
    # nuestro record de la misma pasada
    m["record"] = rec is not None
    if rec_ajeno is not None:
        m["dbt_ajeno"], m["n_dbt_ajeno"] = T.dbt_mediana(R, escena(rec_ajeno))
    if rec is not None:
        px = escena(rec)
        m["n_px"] = len(px)
        m["dbt"], m["n_dbt"] = T.dbt_mediana(R, px)
        m["hot_lat"], m["hot_lon"] = rec.get("hotspot_lat"), rec.get("hotspot_lon")
        pc = rec.get("primary_cluster") or {}
        m["pc_lat"], m["pc_lon"], m["pc_vrp"] = pc.get("centroid_lat"), pc.get("centroid_lon"), pc.get("vrp_mw")
        # nuestro calor en el crater (inner) y lejos (fuera del corte, desde el centro de grilla)
        e_in = sum(p.get("vrp_mw") or 0 for p in px if float(T.dist_km(p["lat"], p["lon"], ancla[0], ancla[1])) <= inner)
        lej = [p for p in px if float(T.dist_km(p["lat"], p["lon"], o_lat, o_lon)) > lim]
        m["nuestro_e_cr"], m["nuestro_e_far"] = e_in, sum(p.get("vrp_mw") or 0 for p in lej)
        m["nuestro_max_far"] = max([p.get("vrp_mw") or 0 for p in lej], default=0.0)
        m["nuestro_max_cr"] = max([p.get("vrp_mw") or 0 for p in px
                                   if float(T.dist_km(p["lat"], p["lon"], ancla[0], ancla[1])) <= inner], default=0.0)
        # z del TIF donde estan NUESTROS pixeles lejanos (el mas energetico) y su nulo girado
        if lej:
            p0 = max(lej, key=lambda p: p.get("vrp_mw") or 0)
            m["nuestro_far_d_o"] = float(T.dist_km(p0["lat"], p0["lon"], o_lat, o_lon))
            cc = T.celda(R, p0["lat"], p0["lon"])
            if cc:
                m["z_en_nuestro_far"] = float(R["z"][cc])
                zn = []
                for ang in ANG_NULO:
                    la, lo = T.rotar(p0["lat"], p0["lon"], o_lat, o_lon, ang)
                    c2 = T.celda(R, la, lo)
                    if c2 and R["fin"][c2]:
                        zn.append(float(R["z"][c2]))
                m["z_en_nuestro_far_nulo"] = float(np.median(zn)) if zn else None
        # coincidencia en POSICION del foco del anillo con nuestros pixeles / hotspot (N3)
        if "ring_lat" in m:
            def dmin(la, lo):
                ds = [float(T.dist_km(p["lat"], p["lon"], la, lo)) for p in px]
                return min(ds) if ds else None

            def dh(la, lo):
                return float(T.dist_km(m["hot_lat"], m["hot_lon"], la, lo)) if m["hot_lat"] is not None else None
            m["d_ring_px"] = dmin(m["ring_lat"], m["ring_lon"])
            m["d_ring_hot"] = dh(m["ring_lat"], m["ring_lon"])
            rot = [T.rotar(m["ring_lat"], m["ring_lon"], o_lat, o_lon, a) for a in ANG_NULO]
            rot = [(la, lo) for la, lo in rot if T.celda(R, la, lo)]
            m["d_ring_px_nulo"] = [dmin(la, lo) for la, lo in rot]
            m["d_ring_hot_nulo"] = [dh(la, lo) for la, lo in rot]
    return m


def frac(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs), len(xs))


def main():
    out = io.StringIO()

    def P(*a):
        print(*a)
        print(*a, file=out)

    rng = random.Random(SEMILLA)
    coords = C._coords_por_volcan()
    ancla, inner, _ = C.anclas_y_inner()
    gc = centro_grilla_yaml()
    filas = cargar_referencia_unificada()
    lim, lim_det = limite_scraper(filas)
    P(f"referencia: snapshot CONS sha256 {sha(SNAP_CONS)[:12]}; {len(filas)} filas. TIF: indice en commit {T.TIF_SHA[:10]}")
    P("corte del scraper por volcan (ALERTA mas lejana, FALSO_POSITIVO mas cercana -> corte), medido desde el centro"
      " de grilla:")
    for v in C.VOLS:
        P(f"   {v:20s} {lim_det[v][0]:6.2f} {lim_det[v][1]:6.2f} -> {lim[v]:6.2f} km")

    base = [f for f in filas if f["source"] == "CONS" and f["origen"] == "principal" and es_noche(f)
            and VENTANA[0] <= f["fecha_utc"][:10] <= VENTANA[1] and f["volcano"] in C.VOLS]
    lejanas = [f for f in base if f["tipo"] == "FALSO_POSITIVO" and (f["vrp_mw"] or 0) > 0]
    alertas = [f for f in base if f["tipo"] == "ALERTA_TERMICA" and (f["vrp_mw"] or 0) > 0]
    rutina = [f for f in base if f["tipo"] == "RUTINA"]
    P(f"\n== universo: lejanas nocturnas {len(lejanas)} (D2: 359) por sensor "
      f"{dict(collections.Counter(f['sensor_bucket'] for f in lejanas))}; alertas {len(alertas)}; rutina {len(rutina)}")

    ix = T.indice()
    P(f"indice de TIF: {len(ix)} filas, adquisiciones {ix.acq.min()} a {ix.acq.max()}; filas con md5 ambiguo "
      f"(mismo archivo con otra hora de adquisicion, A106): {int(ix.md5_ambiguo.sum())}")
    grupos = {k: g for k, g in ix.dropna(subset=["acq"]).groupby(["vol", "sensor"])}

    def con_tif(lista, nombre):
        res, mot = [], collections.Counter()
        for f in lista:
            fila, motivo = T.tif_de_pasada(grupos.get((f["volcano"], f["sensor_bucket"])), pd.Timestamp(t_de(f)))
            mot[motivo] += 1
            if fila is not None:
                fila = fila.copy()
                fila["_motivo"] = motivo
                res.append((f, fila))
        P(f"   {nombre}: {dict(mot)}")
        return res

    P("\n== pareo con el TIF de la misma pasada (adquisicion a +-120 s):")
    P_lej = con_tif(lejanas, "lejanas")
    fuera = collections.Counter("antes del 2026-05-09" if f["fecha_utc"] < "2026-05-09" else
                                "despues del 2026-09-22" if f["fecha_utc"] > "2026-09-22 11" else "dentro"
                                for f in lejanas)
    P(f"   lejanas por ventana del archivo de TIF: {dict(fuera)}")
    P_al = con_tif(alertas, "alertas")
    P_ru_all = con_tif(rutina, "rutina")
    P_ru = []
    for s in C.BUCKETS:
        xs = [x for x in P_ru_all if x[0]["sensor_bucket"] == s]
        rng.shuffle(xs)
        P_ru += xs[:N_RUTINA_POR_SENSOR]
    P(f"   rutina muestreada (semilla {SEMILLA}, hasta {N_RUTINA_POR_SENSOR} por sensor): {len(P_ru)}")

    todos = P_lej + P_al + P_ru
    with ThreadPoolExecutor(8) as ex:
        okb = list(ex.map(lambda x: T.bajar_tif(x[1]), todos))
    P(f"   TIF bajados y con md5 correcto: {sum(okb)} de {len(okb)} (cache {T.CACHE})")

    # records nuestros
    recs = C.cargar_records(C.ROOT / "data" / "mirova_equivalent", VENTANA, coords)
    idx = collections.defaultdict(list)
    for x in recs:
        idx[(x["vol"], x["b"])].append(x)

    def rec_de(f):
        t = t_de(f)
        ms = [x for x in idx[(f["volcano"], f["sensor_bucket"])] if abs((x["dt"] - t).total_seconds()) <= 120]
        return min(ms, key=lambda x: abs((x["dt"] - t).total_seconds()))["rec"] if ms else None

    # nulo N1: a cada rutina se le asigna una distancia del CSV de una lejana del mismo volcan y sensor
    dist_lej = collections.defaultdict(list)
    for f in lejanas:
        dist_lej[(f["volcano"], f["sensor_bucket"])].append(f["dist_km"])
    dist_lej_s = collections.defaultdict(list)
    for f in lejanas:
        dist_lej_s[f["sensor_bucket"]].append(f["dist_km"])

    M, no_legibles = [], collections.Counter()
    for grupo, lista in (("lejana", P_lej), ("alerta", P_al), ("rutina", P_ru)):
        for f, fila in lista:
            if not T.ruta_tif(fila).exists():
                continue
            f2 = dict(f)
            if grupo == "rutina":
                pool = dist_lej.get((f["volcano"], f["sensor_bucket"])) or dist_lej_s[f["sensor_bucket"]]
                f2["dist_km"] = rng.choice(pool)
            elif grupo == "alerta":
                # para la alerta el anillo se pone a una distancia de lejana prestada: control "MIROVA alerto cerca"
                pool = dist_lej.get((f["volcano"], f["sensor_bucket"])) or dist_lej_s[f["sensor_bucket"]]
                f2["dist_km"] = rng.choice(pool)
            t = t_de(f)
            otros = [x for x in idx[(f["volcano"], f["sensor_bucket"])]
                     if abs((x["dt"] - t).total_seconds()) > 3 * 3600 and escena(x["rec"])]
            ajeno = rng.choice(otros)["rec"] if otros else None
            m = medir_pasada(f2, fila, rec_de(f), ancla[f["volcano"]], gc[f["volcano"]], lim[f["volcano"]],
                             inner[f["volcano"]], rec_ajeno=ajeno)
            if m is None:
                no_legibles[grupo] += 1
                continue
            m["grupo"] = grupo
            m["dist_csv_real"] = f["dist_km"]
            M.append(m)
    df = pd.DataFrame(M)
    P(f"\n== pasadas medidas: {dict(collections.Counter(df.grupo))}; TIF no legibles: {dict(no_legibles)}; "
      "por sensor y grupo:")
    P(df.groupby(["grupo", "sensor"]).size().to_string())

    # ------------------------------------------------------------------ atribucion: el TIF es de esta pasada?
    P(f"\n== Atribucion (A106): BT del TIF menos BT de nuestros pixeles de la MISMA pasada, contra el nulo de los"
      f" pixeles de OTRA pasada (mas de 3 h) del mismo volcan y sensor sobre el mismo TIF")
    for s in C.BUCKETS:
        d = df[(df.sensor == s)]
        a = d.dbt.dropna().abs()
        nlo = d.dbt_ajeno.dropna().abs()
        P(f"   {s:9s} misma pasada: n={len(a)} |dBT| mediana {a.median():.2f} K, <=1 K {100 * (a <= 1).mean():.1f} %, "
          f"<=2 K {100 * (a <= 2).mean():.1f} %   | nulo otra pasada: n={len(nlo)} mediana {nlo.median():.2f} K, "
          f"<=1 K {100 * (nlo <= 1).mean():.1f} %, <=2 K {100 * (nlo <= 2).mean():.1f} %")
    # Cortes elegidos DESPUES de ver estas dos distribuciones (dicho): en VIIRS la misma pasada da <= 1 K en 62 %
    # (375) y 45 % (750) contra 21 % y 16 % del nulo, y > 5 K en 9 % contra 50 % y 57 %. En MODIS el control NO
    # separa (mediana 5,6 K contra 10,3 K, <= 1 K 2 % contra 6 %): ahi la atribucion queda sin dato.
    def atrib(r):
        if r.sensor == "MODIS" or pd.isna(r.dbt):
            return "sin_dato"
        return "verificada" if r.dbt <= ATRIB_K else ("rechazada" if r.dbt > ATRIB_NO_K else "dudosa")
    df["atrib"] = [atrib(r) for r in df.itertuples()]
    P(f"   verificada <= {ATRIB_K} K, rechazada > {ATRIB_NO_K} K, dudosa entre medio; MODIS sin dato: "
      f"{df.groupby(['grupo', 'atrib']).size().to_dict()}")
    rech = df[df.atrib == "rechazada"]
    P(f"   las RECHAZADAS salen del analisis principal ({len(rech)}); las dudosas y sin dato se quedan; todo el"
      f" analisis se repite despues solo con las verificadas.")
    df_todo = df
    df = df[df.atrib != "rechazada"].copy()

    def analizar(df, titulo, umbrales=None):
        """Todo el analisis sobre un subconjunto de pasadas. Devuelve los umbrales y los resultados."""
        P(f"\n\n############################ {titulo}: {len(df)} pasadas")
        # ------------------------------------------------------------------ georreferencia
        P("\n== Georreferencia (cada TIF): distancia del centro del raster al centro de grilla de volcanoes.yaml")
        P(df.groupby("vol").georef_centro_vs_grilla_km.agg(["median", "max"]).round(3).to_string())
        P(f"   CRS: {dict(collections.Counter(df.crs))}; crater fuera del raster: {int((~df.crater_en_raster).sum())}")
        P("   N4 control positivo: z del crater contra z de discos a 8 km (mediana; fraccion crater > nulo)")
        for g in ("alerta", "lejana", "rutina"):
            for s in C.BUCKETS:
                d = df[(df.grupo == g) & (df.sensor == s)].dropna(subset=["z_cr", "z_cr_nulo"])
                if len(d):
                    P(f"   {g:7s} {s:9s} n={len(d):4d} z_crater {d.z_cr.median():6.2f} nulo {d.z_cr_nulo.median():6.2f} "
                      f"crater>nulo {100 * (d.z_cr > d.z_cr_nulo).mean():5.1f} %")

        # ------------------------------------------------------------------ umbrales medidos (N1)
        Z_ID, Z_CAL, Z_FAR = {}, {}, {}

        def p95(x):
            x = x.dropna()
            return float(np.percentile(x, 95)) if len(x) >= 20 else float("nan")
        for s in C.BUCKETS:
            ru = df[(df.grupo == "rutina") & (df.sensor == s)]
            Z_ID[s], Z_CAL[s], Z_FAR[s] = p95(ru.z_ring), p95(ru.z_cr_nulo), p95(ru.z_far)
        if umbrales is not None:
            # el subconjunto verificado tiene pocas rutinas por sensor: se usan los umbrales del analisis principal
            Z_ID, Z_CAL, Z_FAR = dict(umbrales["z_id"]), dict(umbrales["z_cal"]), dict(umbrales["z_far"])
        P("\n== N1 umbrales del nulo RUTINA (p95, MIROVA miro y no alerto nada): foco en el anillo Z_ID / calor en un"
          " disco del radio del crater Z_CAL / foco mas fuerte de toda la zona lejana Z_FAR"
          + (" [heredados del analisis principal]" if umbrales is not None else ""))
        for s in C.BUCKETS:
            P(f"   {s:9s} Z_ID {Z_ID[s]:6.2f}   Z_CAL {Z_CAL[s]:6.2f}   Z_FAR {Z_FAR[s]:6.2f}")
        P("   (la zona lejana tiene miles de pixeles, por eso su maximo es alto aun sin nada: por eso tiene su propio nulo)")
        df["ring_id"] = [r.z_ring >= Z_ID[r.sensor] if pd.notna(r.z_ring) else False for r in df.itertuples()]

        P("\n== P1a. Hay calor en el anillo a la distancia del CSV? (fraccion con foco sobre Z_ID; N1 da 5 % por"
          " construccion en rutina)")
        for s in C.BUCKETS:
            for g in ("lejana", "alerta", "rutina"):
                d = df[(df.grupo == g) & (df.sensor == s) & df.z_ring.notna()]
                if len(d):
                    P(f"   {s:9s} {g:7s} n={len(d):4d} foco identificado {int(d.ring_id.sum()):4d} "
                      f"({100 * d.ring_id.mean():5.1f} %), z mediano {d.z_ring.median():6.2f}")
        d = df[(df.grupo == "lejana") & df.z_ring.notna() & df.z_ring_corrido.notna()]
        P(f"   N2 anillo corrido +-{DESPLAZ_KM:.0f} km, lejanas: el anillo del CSV gana en {int((d.z_ring > d.z_ring_corrido).sum())}"
          f" de {len(d)} ({100 * (d.z_ring > d.z_ring_corrido).mean():.1f} %); con foco identificado: "
          f"{int(((d.z_ring > d.z_ring_corrido) & d.ring_id).sum())} de {int(d.ring_id.sum())}")
        d = df[(df.grupo == "rutina") & df.z_ring.notna() & df.z_ring_corrido.notna()]
        P(f"   N2 en rutina (nulo): gana en {int((d.z_ring > d.z_ring_corrido).sum())} de {len(d)} "
          f"({100 * (d.z_ring > d.z_ring_corrido).mean():.1f} %)")

        P("\n== P1b. Coincidencia en POSICION del foco identificado con nuestra pasada (N3: el mismo foco girado)")
        lj = df[(df.grupo == "lejana") & df.ring_id]
        P(f"   lejanas con foco identificado: {len(lj)}; con record nuestro {int(lj.record.sum())}")
        res_p1b = {}
        for s in C.BUCKETS:
            d = lj[(lj.sensor == s) & lj.record]
            if not len(d):
                continue
            tol = T.COINCIDE_KM[s]
            for campo in ("px", "hot"):
                real = [x <= tol for x in d[f"d_ring_{campo}"] if x is not None and x == x]
                nulos = [x <= tol for xs in d[f"d_ring_{campo}_nulo"] for x in xs if x is not None]
                res_p1b[(s, campo)] = (sum(real), len(real), sum(nulos), len(nulos))
                P(f"   {s:9s} {'cualquier pixel nuestro (escena)' if campo == 'px' else 'nuestro pixel alertado de mas VRP':34s}"
                  f" a <= {tol} km: real {sum(real)}/{len(real)} ({100 * sum(real) / max(len(real), 1):5.1f} %)  nulo girado "
                  f"{sum(nulos)}/{len(nulos)} ({100 * sum(nulos) / max(len(nulos), 1):5.1f} %)")
        d = df[df.z_en_nuestro_far.notna() & df.z_en_nuestro_far_nulo.notna()] if "z_en_nuestro_far" in df else df.iloc[:0]
        P("   al reves: z del TIF donde esta NUESTRO pixel lejano mas energetico, contra el mismo punto girado")
        for g in ("lejana", "alerta", "rutina"):
            for s in C.BUCKETS:
                e = d[(d.grupo == g) & (d.sensor == s)]
                if len(e):
                    P(f"   {g:7s} {s:9s} n={len(e):4d} z {e.z_en_nuestro_far.median():6.2f} nulo "
                      f"{e.z_en_nuestro_far_nulo.median():6.2f}; sobre Z_CAL {int((e.z_en_nuestro_far >= Z_CAL[s]).sum())}"
                      f" (nulo {int((e.z_en_nuestro_far_nulo >= Z_CAL[s]).sum())})")

        # ------------------------------------------------------------------ N5 energia
        P("\n== N5. La energia del foco en el TIF (exceso x Wooster) contra el VRP que publica MIROVA (Spearman)")
        res_n5 = {}
        for g, col in (("lejana", "e_ring"), ("alerta", "e_cr")):
            d = df[(df.grupo == g) & df[col].notna() & (df.vrp_csv > 0)]
            if g == "lejana":
                d = d[d.ring_id]
            if len(d) >= 5:
                rho, p = spearmanr(d[col], d.vrp_csv)
                q = np.log10(d[col].clip(lower=1e-4) / d.vrp_csv)
                res_n5[g] = (len(d), rho, p)
                P(f"   {g:7s} ({'foco del anillo' if g == 'lejana' else 'foco del crater'}): n={len(d)} rho={rho:.3f} "
                  f"p={p:.2g}; log10(energia TIF / VRP MIROVA) mediana {q.median():+.2f} (p25 {q.quantile(.25):+.2f}, "
                  f"p75 {q.quantile(.75):+.2f})")

        # ------------------------------------------------------------------ P2 y P3
        # Cuatro reglas candidatas. Para cada una, que predice en una pasada con calor en el crater Y lejos:
        #   R1 la mayor: informa el objeto de mas energia (lejos si el lejano pesa mas).
        #   R2 el crater si hay algo en el crater: informa cerca.
        #   R3 la mas cercana al centro de grilla: informa cerca (el crater esta a 0 a 4,8 km del centro; el lejano mas).
        #   R4 todo lo alertado junto, con la distancia del pixel alertado mas lejano (Campus 2022 §3.2 + S139): informa
        #      lejos siempre que el lejano este alertado por MIROVA, y su VRP es la SUMA.
        P("\n== P2/P3. Calor en el crater Y lejos en la misma pasada: que informa MIROVA y que regla lo predice")
        res_p3 = {}
        peso = {s: sum(1 for f, _ in P_ru_all if f["sensor_bucket"] == s) / max(1, ((df.grupo == "rutina") & (df.sensor == s)).sum())
                for s in C.BUCKETS}
        for s in C.BUCKETS:
            lj = df[(df.grupo == "lejana") & (df.sensor == s) & df.ring_id & df.z_cr.notna()].copy()
            al = df[(df.grupo == "alerta") & (df.sensor == s) & df.z_cr.notna()].copy()
            if not len(lj) and not len(al):
                continue
            zc_alerta = float(al.z_cr.median()) if len(al) else float("nan")
            P(f"\n   ---- {s}: lejanas con foco identificado {len(lj)}, alertas {len(al)}. Umbral de 'calor en el crater': "
              f"Z_CAL {Z_CAL[s]:.2f} (p95 del nulo) y, estricto, la mediana del crater en las alertas {zc_alerta:.2f}")
            r = {}
            for nombre, zc in (("Z_CAL", Z_CAL[s]), ("mediana_alertas", zc_alerta)):
                h = lj[lj.z_cr >= zc]
                mayor_ok = int((h.e_ring >= h.e_cr).sum())
                r[nombre] = {"lejanas_con_crater_caliente": len(h), "de_lejanas": len(lj),
                             "crater_pesa_mas_que_el_lejano": int((h.e_cr > h.e_ring).sum())}
                P(f"   T1 [{nombre}] lejanas con calor en el crater: {len(h)} de {len(lj)} (rutina, crater sobre el mismo umbral: "
                  f"{int((df[(df.grupo == 'rutina') & (df.sensor == s)].z_cr >= zc).sum())} de "
                  f"{int(((df.grupo == 'rutina') & (df.sensor == s) & df.z_cr.notna()).sum())}). MIROVA informo LEJOS en todas: "
                  f"R2 y R3 en contra {len(h)}, R4 a favor {len(h)}")
                P(f"   T2 [{nombre}] de esas, el lejano pesa mas (R1 a favor) {mayor_ok}; el crater pesa mas y MIROVA igual "
                  f"informo lejos (R1 en contra, R4 a favor) {len(h) - mayor_ok}")
                for x in h[h.e_cr > h.e_ring].itertuples():
                    P(f"        {x.vol} {x.fecha_utc}: VRP MIROVA {x.vrp_csv} a {x.dist_csv_real} km; TIF crater {x.e_cr:.2f} MW "
                      f"(z {x.z_cr:.1f}), lejano {x.e_ring:.2f} MW (z {x.z_ring:.1f}), suma {x.e_cr + x.e_ring:.2f}")
            # T3 magnitud: si MIROVA informa la suma (R4), en las lejanas con crater caliente el VRP debe parecerse a
            # lejano+crater; si informa la mayor (R1), al lejano solo. La calibracion sale de las lejanas con crater frio.
            frio = lj[lj.z_cr < Z_CAL[s]]
            cal = lj[lj.z_cr >= zc_alerta]
            if len(frio) >= 5 and len(cal) >= 5:
                q0 = np.log10(frio.e_ring / frio.vrp_csv)
                q1 = np.log10(cal.e_ring / cal.vrp_csv)
                q2 = np.log10((cal.e_ring + cal.e_cr) / cal.vrp_csv)
                # control del ruido: sumarle al lejano la energia de un crater FRIO tambien sube el cociente (el exceso
                # positivo de una ventana 3x3 nunca es cero). Si R4 vale, q2 debe parecerse a q0 MAS ese ruido; si R1
                # vale, q1 debe parecerse a q0.
                q0n = np.log10((frio.e_ring + frio.e_cr) / frio.vrp_csv)
                p1 = mannwhitneyu(q1, q0).pvalue
                p2 = mannwhitneyu(q2, q0n).pvalue
                P(f"   T3 log10(energia TIF / VRP MIROVA), mediana [p25, p75]: lejanas con crater frio (calibracion) "
                  f"{q0.median():+.3f} [{q0.quantile(.25):+.3f}, {q0.quantile(.75):+.3f}] n={len(frio)} (con su crater frio "
                  f"sumado, ruido: {q0n.median():+.3f}); con crater caliente (estricto), solo el lejano {q1.median():+.3f} "
                  f"[{q1.quantile(.25):+.3f}, {q1.quantile(.75):+.3f}] (Mann-Whitney contra la calibracion p={p1:.3f}) y "
                  f"lejano+crater {q2.median():+.3f} [{q2.quantile(.25):+.3f}, {q2.quantile(.75):+.3f}] (contra la calibracion"
                  f" con ruido p={p2:.3f}) n={len(cal)}")
                r["T3"] = {"calibracion": [round(float(q0.median()), 3), len(frio)], "calibracion_con_ruido": round(float(q0n.median()), 3),
                           "solo_lejano": [round(float(q1.median()), 3), round(float(p1), 4)],
                           "lejano_mas_crater": [round(float(q2.median()), 3), round(float(p2), 4)], "n": len(cal)}
            # T4 alertas (MIROVA informo el crater) con un foco lejano fuerte en el TIF
            for fac in (1.0, 2.0):
                a4 = al[al.z_far >= fac * Z_FAR[s]]
                r[f"T4_{fac:g}xZ_FAR"] = {"alertas_con_foco_lejano": len(a4), "lejano_pesa_mas": int((a4.e_far > a4.e_cr).sum())}
                P(f"   T4 alertas (MIROVA informo el crater) con foco lejano z >= {fac:g} x Z_FAR ({fac * Z_FAR[s]:.1f}): "
                  f"{len(a4)} de {len(al)}; lejano pesa mas que el crater en {int((a4.e_far > a4.e_cr).sum())}")
                if fac == 1.0:
                    for x in a4.itertuples():
                        P(f"        {x.vol} {x.fecha_utc}: VRP MIROVA {x.vrp_csv} a {x.dist_csv_real} km; TIF crater {x.e_cr:.2f} "
                          f"MW (z {x.z_cr:.1f}), lejano {x.e_far:.2f} MW (z {x.z_far:.1f}) a {x.far_d_o:.1f} km del centro")
            # Que tan seguido MIROVA informa lejos cuando el TIF tiene un foco lejano de cierta fuerza (rutina pesada por
            # su fraccion muestreada). Si es bajo, un foco del TIF no equivale a un pixel alertado por MIROVA y T4 no
            # puede usarse contra R4.
            P(f"   P(MIROVA informa lejos | foco lejano del TIF con z >= X), rutina pesada x{peso[s]:.1f}:")
            dd = df[(df.sensor == s) & df.z_far.notna()]
            for X in (Z_FAR[s], 2 * Z_FAR[s], 4 * Z_FAR[s]):
                nl = int(((dd.grupo == "lejana") & (dd.z_far >= X)).sum())
                na = int(((dd.grupo == "alerta") & (dd.z_far >= X)).sum())
                nr = int(((dd.grupo == "rutina") & (dd.z_far >= X)).sum())
                tot = nl + na + nr * peso[s]
                P(f"      X={X:7.1f}: lejanas {nl}, alertas {na}, rutina {nr} (pesada {nr * peso[s]:.0f}) -> "
                  f"{100 * nl / tot if tot else float('nan'):5.1f} %")
            # nuestros datos: pasadas donde nuestro pixel alertado mas energetico (hotspot) esta lejos y tenemos cumulo en
            # el crater. Nuestra energia del lejano no se guarda (anomaly_pixels se reescribe con los del Test 1 cuando
            # gana la Regla D), asi que aqui solo se cuenta que informo MIROVA.
            dd = df[df.grupo.isin(["lejana", "alerta"]) & (df.sensor == s) & df.record & df.hot_lat.notna() & df.pc_lat.notna()].copy()
            if len(dd):
                anc = ancla
                dd["hot_d_cr"] = [float(T.dist_km(x.hot_lat, x.hot_lon, *anc[x.vol])) for x in dd.itertuples()]
                dd["pc_d_cr"] = [float(T.dist_km(x.pc_lat, x.pc_lon, *anc[x.vol])) for x in dd.itertuples()]
                amb = dd[(dd.hot_d_cr > 5.0) & (dd.pc_d_cr <= dd.vol.map(inner))]
                P(f"   NUESTROS: hotspot a mas de 5 km del crater y cumulo en el inner: {len(amb)}; MIROVA informo lejos "
                  f"{int((amb.grupo == 'lejana').sum())}, cerca {int((amb.grupo == 'alerta').sum())}")
                r["nuestros_ambos"] = {"lejos": int((amb.grupo == "lejana").sum()), "cerca": int((amb.grupo == "alerta").sum())}
            res_p3[s] = r
        return {"z_id": Z_ID, "z_cal": Z_CAL, "z_far": Z_FAR, "p1b": {f"{k[0]}|{k[1]}": v for k, v in res_p1b.items()},
                "n5": {k: [v[0], round(float(v[1]), 3), float(v[2])] for k, v in res_n5.items()}, "p3": res_p3}

    R_main = analizar(df, "SIN LAS RECHAZADAS POR ATRIBUCION")
    R_ver = analizar(df_todo[df_todo.atrib == "verificada"].copy(), "SOLO LAS VERIFICADAS (|dBT| <= 1 K)",
                     umbrales=R_main)
    Z_ID = R_main["z_id"]

    # tabla por pasada (sin listas)
    df_todo["ring_id"] = [r.z_ring >= Z_ID[r.sensor] if pd.notna(r.z_ring) else False for r in df_todo.itertuples()]
    cols = [c for c in df_todo.columns if not c.endswith("_nulo") or c in ("z_cr_nulo", "z_en_nuestro_far_nulo")]
    df_todo[cols].to_csv(AQUI / "pasadas.csv", index=False, float_format="%.4g")
    (AQUI / "estudio_salida.txt").write_text(out.getvalue(), encoding="utf-8")
    js = {"principal": R_main, "verificadas": R_ver, "n_medidas": dict(collections.Counter(df_todo.grupo)),
          "atribucion": {f"{g}|{a}": int(n) for (g, a), n in df_todo.groupby(["grupo", "atrib"]).size().items()},
          "tif_sha": T.TIF_SHA, "snap_cons_sha256": sha(SNAP_CONS)}
    (AQUI / "estudio_salida.json").write_text(json.dumps(js, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
