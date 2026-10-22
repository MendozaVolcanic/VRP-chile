#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-audit semanal de paridad vs MIROVA (S120, propuesta §8 AUDIT_S119).

POR QUÉ (fenómeno → mecanismo): la paridad con MIROVA se validaba en auditorías
episódicas (A51, cada ~20 sesiones). Entre auditorías, una regresión silenciosa
(un flip de flag, un cambio NASA, un drift del ground truth) puede correr semanas
sin detección. Este script empaqueta los criterios EXACTOS del Eje 2 de la
auditoría S119 (experiments/_s119_audit/eje2_recall_magnitud.py) en una corrida
semanal con ventana rodante → data/audit_continuous/latest.json. El workflow
audit-weekly.yml lo corre por cron y abre un issue si algo sale de banda.

Criterios (idénticos a S119, regla S91 — no re-derivar):
  - CRÁTER: pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND vrp<=50000 (A10).
  - DASHBOARD: CRÁTER AND distance_class in {summit, None}.
  - Recall por bucket de sensor sobre noches ALERTA del loader canónico (A11).
  - Magnitud: mediana per-vol de max(dash)/max(MIROVA VRP) por noche común.

Bandas (referencia S119 − margen 5pp; magnitud banda paridad [0.5, 2.0]):
  - recall crater VIIRS375 >= 93.4 (ref 98.4), VIIRS750 >= 79.5 (ref 84.5),
    MODIS >= 95.0 (ref 100) — solo si n_noches >= MIN_N_RECALL.
  - magnitud: vol fuera de banda con n>=5 → flag. Excepción documentada:
    Lastarria sub-banda es cat-b Lazufre conocido (AUDIT_S119 §2.3) — solo
    flaggea si ratio > 2.0 (sobre-estimación, que sí sería nuevo).
  - integridad: parse errors o duplicados (datetime_utc, sensor) > 0 → flag.
"""
import sys
import io
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import clase_mirova as cm  # noqa: E402  S156: D-9 y alerta protegida, una sola implementación
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from pipeline.profile import ENABLE_DAYTIME_MODIS  # noqa: E402
from pipeline.diurno import flag_viirs_diurno  # noqa: E402  S151 D-10
import yaml  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")
# S151 (loop, pendiente i de la tarea 0.1): filas que el consolidado remoto perdio en silencio (#778).
HISTORICO = os.path.join(ROOT, "data", "mirova_reference", "union_historica", "consolidado_filas_perdidas.csv")
OUTDIR = os.path.join(ROOT, "data", "audit_continuous")
VOLCANOES_YAML = os.path.join(ROOT, "volcanoes.yaml")

WINDOW_DAYS = 60
# S142: primer día del régimen vigente para la métrica de falsas publicaciones. POR QUÉ: #535
# (2026-08-28) apagó la máscara de nube de 260 K, que dejaba sin fondo las pasadas de invierno
# (nieve fría leída como nube) y así ocultaba la sobre-publicación; #571 (2026-08-31) quitó el piso
# VRP. V375 pasó de 62,1 % a 87,1 % de publicación en negativos limpios
# (experiments/_s142_linea_base/linea_base_post535.json). Una ventana que cruza el corte mezcla
# regímenes y el número sube solo. Recall y magnitud no se recortan: el recall no se movió.
INICIO_REGIMEN_FALSAS = "2026-09-01"


def alertas_mirova(cons=CONS, ocr=OCR, historico=HISTORICO):
    """ALERTAs de MIROVA del snapshot (CONS u OCR) mas las que el remoto perdio (union historica, #778).

    POR QUE: el consolidado de Mirova-v1 perdio 40 ALERTA_TERMICA en cinco caidas y el snapshot las hereda.
    Sin esta capa una alerta perdida no cuenta como alerta y su noche sale del recall. La fila del snapshot
    gana siempre; la historica solo agrega pasadas (volcan, sensor, minuto) que no estan. `historico=None`
    apaga la capa (control).
    """
    alertas = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    if historico is None:
        return alertas
    clave = lambda a: (a["volcano"], a["sensor_bucket"], (a["fecha_utc"] or "")[:16])  # noqa: E731
    vistas = {clave(a) for a in alertas}
    for a in load_mirova_alertas(cons_path=historico, ocr_path=None):
        if clave(a) not in vistas:
            vistas.add(clave(a))
            alertas.append(a)
    return alertas


def ventana_falsas(today):
    """Ventana de falsas publicaciones: la rodante de WINDOW_DAYS, sin empezar antes del régimen."""
    inicio = max((today - timedelta(days=WINDOW_DAYS)).isoformat(), INICIO_REGIMEN_FALSAS)
    return (inicio, today.isoformat())


MIN_N_RECALL = 15   # noches ALERTA mínimas para que el recall del bucket sea flaggeable
MIN_N_RATIO = 5     # noches comunes mínimas para que el ratio per-vol sea flaggeable

# --- S124: guarda de COBERTURA ---
# Sin esto la auditoría tiene una asimetría perversa: grita cuando fallamos
# nosotros y se calla cuando falla la REFERENCIA. Dos modos concretos, ambos
# ya ocurridos:
#   (a) el NRT se cae (20-jul→04-ago, token expirado) y MIROVA sigue publicando
#       → las noches en que no miramos entran al DENOMINADOR del recall y el
#       veredicto culpa a la detección. Abrió 3 issues seguidos por un problema
#       que no era de detección (#499/#500/#504).
#   (b) el scraper de mirovaweb se congela → en la ventana rodante `n` cae bajo
#       los mínimos, los flags se SALTAN y el veredicto sale VERDE. La referencia
#       muerta se lee como "todo bien".
# Un veredicto solo es interpretable si la ventana tuvo cobertura de AMBOS lados.
MAX_GT_STALE_DAYS = 7      # días sin ALERTA nueva de MIROVA → referencia sospechosa
MIN_COVERAGE_PCT = 80.0    # % de días de la ventana con datos nuestros

VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000
RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}
# --- S124: DOS bandas, no una ---
# `~memory/reference_paridad_mirova_umbrales.md` las distingue por una razón
# física. MIROVA declara ±30 % de error en el método MIR, así que el ratio de una
# noche PUNTUAL fluctúa naturalmente entre 0,54 y 1,85 sin que haya nada roto —
# de ahí la banda ancha. Pero una MEDIANA sobre decenas de noches ya no fluctúa:
# textual, *"más estricto que individual porque mide tendencia central, no
# outliers puntuales. Mediana 2.0 = sesgo sistemático, no ruido"*.
#
# Hasta S124 este script aplicaba la banda ANCHA a la mediana: 4× de ancho donde
# el criterio propio pide 2×. Con eso, cuatro volcanes sub-reportando 35-50 %
# quedaban invisibles (Lascar 0,62 · Isluga 0,61 · Lastarria 0,47 · Llaima 0,36)
# y dos selecciones de cluster que difieren 17 % "pasaban" las dos.
# Ver docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md.
RATIO_BAND_INDIVIDUAL = (0.5, 2.0)   # una detección suelta (referencia, no se usa acá)
RATIO_BAND_MEDIAN = (0.7, 1.4)       # la mediana per-volcán: lo que este script juzga
RATIO_BAND = RATIO_BAND_MEDIAN       # compat con lectores externos del módulo
# Excepciones documentadas: sub-banda esperada, no flaggear.
# - Lastarria: cat-b Lazufre (AUDIT_S119 §2.3), excepción física.
# - Lascar e Isluga (S141, decisión Nicolás 2026-09-14): déficit de régimen débil de S124
#   (docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md), que es el objeto de la Fase 1 del plan de
#   paridad (docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md §4). Salieron
#   en el issue semanal cuatro semanas seguidas (#511, #568, #603, #661) por lo mismo; un aviso
#   que repite lo sabido deja de leerse y tapa la regresión real. QUITARLOS al cerrar la Fase 1.
#   La magnitud sigue medida en latest.json; sólo deja de abrir issue por debajo de la banda.
UNDER_BAND_KNOWN = {"Lastarria", "Lascar", "Isluga"}


def evaluar_ratio_mediano(volcan: str, ratio: float, n_noches: int, sensor: str = None):
    """Veredicto del ratio mediano de un volcán (o de un volcán y sensor). None = en banda / no concluyente.

    S156 (F3-07 de AUDIT_S155): el texto ya no ATRIBUYE la causa al déficit de régimen débil de S124.
    #779 lo decía de Tupungatito cuando la caída de esa ventana venía en parte del cambio de detector y
    de publicar menos pasadas por noche. S124 queda nombrado como antecedente, no como diagnóstico.
    """
    if n_noches < MIN_N_RATIO:
        return None
    lo, hi = RATIO_BAND_MEDIAN
    etiqueta = f"{volcan} {sensor}" if sensor else volcan
    if ratio > hi:
        return (f"magnitud {etiqueta} {ratio}x > {hi} (SOBRE-estima, n={n_noches})")
    if ratio < lo and volcan not in UNDER_BAND_KNOWN:
        return (f"magnitud {etiqueta} {ratio}x < {lo} (SUB-estima, n={n_noches}; causa sin medir, "
                f"antecedente: déficit de régimen débil S124, "
                f"docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md)")
    return None


# --- S140 (Fase 0, tarea 6): falsas publicaciones, SIN alarma ---
# POR QUÉ: la brecha con MIROVA es sobre-publicación (S139): en pasadas donde MIROVA
# miró el volcán y no vio nada, el dashboard publica igual. Este script sólo medía
# recall y magnitud, así que esa brecha no se veía semana a semana. Ahora se mide con
# el banco de paridad (scripts/banco_paridad.py), por sensor y por régimen.
# DECISIÓN de Nicolás (2026-09-14): medir SIN alarma. V375 está hoy en ~64 % contra
# una banda de terminado de 10 %: con flag, el workflow abriría un issue cada lunes
# hasta cerrar la Fase 1 y taparía las regresiones reales. La banda va al lado.
FALSAS_BANDA_TERMINADO = {"focal": 10.0, "nevado": 15.0}   # spec §2 revisada (§7.5)
# Partición de régimen de S131 (scripts/build_c2ab_windows.py:41-42).
REGIMEN = {**{v: "focal" for v in ("Lascar", "Lastarria", "Isluga",
                                   "PlanchonPeteroa", "PuyehueCordonCaulle")},
           **{v: "nevado" for v in ("Llaima", "Copahue", "Villarrica",
                                    "NevadosDeChillan", "Tupungatito", "Chaiten")}}


def _pct_falsas(recs, campo="lab"):
    neg = [r for r in recs if r[campo] == "neg_limpio"]
    pub = sum(r["pub"] for r in neg)
    return {"n_neg_limpio": len(neg), "n_publica": pub,
            "falsas_pub_pct": round(100.0 * pub / len(neg), 1) if neg else None}


def resumir_falsas(recs, flags):
    """Falsas publicaciones por sensor y por régimen, sobre pasadas etiquetadas por el banco.

    Recibe `flags` para dejar explícito el contrato: esta métrica NO los modifica.
    """
    por_sensor = {s: _pct_falsas([r for r in recs if r["b"] == s]) for s in SENSORS}
    por_regimen = {}
    for reg, banda in FALSAS_BANDA_TERMINADO.items():
        por_regimen[reg] = {}
        for s in SENSORS:
            d = _pct_falsas([r for r in recs if r["b"] == s and REGIMEN.get(r["vol"]) == reg])
            d["banda_terminado_pct"] = banda
            d["sobre_banda_terminado"] = (d["falsas_pub_pct"] > banda
                                          if d["falsas_pub_pct"] is not None else None)
            por_regimen[reg][s] = d
    return {"por_sensor": por_sensor, "por_regimen": por_regimen, "alarma": False,
            "nota": ("medición sin alarma (decisión Nicolás S140); la banda es la de "
                     "terminado de la spec §2, no un umbral de regresión")}


def banco_ventana(win):
    """Etiqueta con el banco de paridad las pasadas nocturnas de la ventana. Devuelve (recs, filas).

    Usa el predicado del dashboard ejecutado con node desde frontend/index.html, igual
    que el banco; la referencia es la unión consolidado + OCR + respaldo (tarea 2).
    S156: `lab` lleva la regla D-9 decidida (SN, issue #811) y `lab_original` la etiqueta del
    scraper, que se informa al lado. La etiqueta de una pasada depende sólo de su noche, así que
    filtrar estos recs a una ventana más corta da lo mismo que etiquetar esa ventana.
    """
    import banco_paridad as bp  # noqa: E402  (importa este módulo: se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONS, OCR)
    recs = bp.cargar_nuestros(coords, inner, win)
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, win)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r in recs:
        r["lab_original"] = r["lab"]
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, win,
                                                                  regla_minimas=REGLA_MINIMAS)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    return recs, filas


def medir_falsas_ventana(win_falsas, banco=None):
    """Recs del banco dentro de la ventana de falsas (recortados del banco de la ventana larga si viene)."""
    recs = banco[0] if banco is not None else banco_ventana(win_falsas)[0]
    return [r for r in recs if win_falsas[0] <= r["noche"] <= win_falsas[1]]


def resumir_falsas_por_detector(recs, frontera, vigente):
    """Falsas del detector vigente (con las claves de siempre) y las de cada detector por separado.

    POR QUÉ (F3-02 de AUDIT_S155): en la ventana del 2026-10-19 VIIRS 375 publicaba en negativos
    limpios 86,5 % con C0 y 2,0 % con K, y el audit escribía 33,3 %, un número que no es de ningún
    detector y que la sombra de K iba a comparar contra la cota del A/B (0,0166 a 0,0383).
    """
    import banco_paridad as bp  # noqa: E402
    for r in recs:
        r["det"] = _detector_banco(r, frontera)
    vig = [r for r in recs if r["det"] == vigente]
    out = resumir_falsas(vig, None)
    out["detector"] = vigente
    out["regla_minimas"] = REGLA_MINIMAS
    out["por_sensor_regla_original"] = {s: _pct_falsas([r for r in vig if r["b"] == s], "lab_original")
                                        for s in SENSORS}
    out["por_detector"] = {d: {s: _pct_falsas([r for r in recs if r["det"] == d and r["b"] == s])
                               for s in SENSORS}
                           for d in DETECTORES if any(r["det"] == d for r in recs)}
    # Estrato 3 de F3: la publicación de V375 cae con el cenit (F2-02); sin el estrato una semana con
    # más pasadas de borde se lee como regresión.
    zb = defaultdict(list)
    for r in vig:
        if r["b"] == "VIIRS375":
            zb[bp.zbin(r["z"]) if r.get("z") is not None else "sin_cenit"].append(r)
    out["cenital_VIIRS375"] = {k: _pct_falsas(v) for k, v in sorted(zb.items())}
    return out


# --- S124: no evaluarnos con pasadas DIURNAS de MIROVA ---
# De día el Sol reflejado en nube o nieve entra en la banda MIR de 3,7-4 µm con
# intensidad comparable a la de un foco incandescente: el sensor no distingue
# "caliente" de "brillante". MIROVA publica de vez en cuando alertas diurnas que
# son reflexión (A76); nuestro pipeline las descarta por diseño. Sin este filtro
# esas pasadas entraban al DENOMINADOR del recall y nos penalizaban por no ver
# lo que decidimos no mirar (82 de 1338 alertas = 6,1 % en la ventana S124; en
# Nevados de Chillán la alerta MÁS GRANDE del período era diurna).
#
# Se reusa `_reject_daytime` de store.py A PROPÓSITO en vez de un umbral propio:
# la auditoría debe excluir EXACTAMENTE lo que el pipeline excluye. Si algún día
# se activa MODIS diurno (ENABLE_DAYTIME_MODIS), la auditoría lo sigue sola.
# S151 D-10: lo mismo para VIIRS diurno (ENABLE_DAYTIME_VIIRS, leído vivo por
# pipeline/diurno.py, el mismo valor que ven fetch, run_pipeline y los procesadores).
_BUCKET_SENSOR = {"MODIS": "MODIS_TERRA",
                  "VIIRS375": "VIIRS_SNPP",       # sin sufijo = I-band 375 m (A48)
                  "VIIRS750": "VIIRS_SNPP_750"}


def bucket_representative_sensor(bucket: str) -> str:
    """Nombre de sensor representativo del bucket, en la convención del proyecto."""
    return _BUCKET_SENSOR.get(bucket, bucket)


def es_pasada_diurna_descartada(bucket, lat, lon, dt_utc) -> bool:
    """¿El pipeline habría descartado esta pasada por diurna?"""
    elev = _solar_elevation(lat, lon, dt_utc)
    return _reject_daytime(bucket_representative_sensor(bucket), elev,
                           ENABLE_DAYTIME_MODIS,
                           enable_daytime_viirs=flag_viirs_diurno())


def _coords_por_volcan():
    with open(VOLCANOES_YAML, encoding="utf-8") as fh:
        return {v["name"]: (v["lat"], v["lon"])
                for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def _csv_ultima_fecha(path):
    """Fecha más reciente registrada en el CSV MIROVA (cualquier Tipo_Registro).

    Devuelve 'YYYY-MM-DD' o None si no se puede leer. Incluye RUTINA a
    propósito: es lo que distingue "el scraper murió" de "no hubo actividad".
    """
    try:
        import csv as _csv
        with open(path, encoding="utf-8", errors="replace") as fh:
            fechas = [r.get("Fecha_Satelite_UTC") or "" for r in _csv.DictReader(fh)]
        fechas = [f[:10] for f in fechas if f[:4].isdigit()]
        return max(fechas) if fechas else None
    except (OSError, KeyError):
        return None


# --- S150 (auditoria S150, D-02): apagon no es falla de deteccion ---
# El 2026-10-05 este audit abrio #757 ("recall VIIRS 375 bajo la banda") cuando 11 de sus 14 fallos eran
# noches del apagon del NRT (token vencido) sin NINGUN record nuestro. Dos defectos: el denominador del
# recall contaba esas noches, y la guarda de cobertura contaba dias con DETECCION en el crater (no dias con
# DATOS) y no miraba la cola de la ventana, que es justo donde vive un apagon en curso: diez dias sin
# datos al final dejan 83,6 %, sobre el umbral de 80 %. Test: tests/test_auto_audit_cobertura_s150.py.
MAX_COLA_SIN_DATOS_DIAS = 1   # hoy puede no tener records todavia (el NRT procesa con retraso)


def cobertura_de_ventana(dias_con_datos, win, hoy):
    """Dias con CUALQUIER record nuestro (no solo con deteccion) y la cola sin datos al final."""
    d0 = datetime.fromisoformat(win[0]).date()
    dias_ventana = (hoy - d0).days + 1
    dentro = {d for d in dias_con_datos if win[0] <= d <= win[1]}
    pct = round(100.0 * len(dentro) / dias_ventana, 1)
    ultimo = max(dentro) if dentro else None
    cola = (hoy - datetime.fromisoformat(ultimo).date()).days if ultimo else dias_ventana
    avisos = []
    if pct < MIN_COVERAGE_PCT:
        avisos.append(f"cobertura propia {pct}% < {MIN_COVERAGE_PCT}% ({len(dentro)}/{dias_ventana} días con datos)")
    if cola > MAX_COLA_SIN_DATOS_DIAS:
        avisos.append(f"{cola} días sin datos nuestros al final de la ventana (último dato {ultimo}): "
                      "probable apagón del NRT en curso, revisar nrt-healthcheck y el token")
    return {"cobertura_propia_pct": pct, "dias_con_datos": len(dentro), "dias_ventana": dias_ventana,
            "ultimo_dia_con_datos": ultimo, "cola_sin_datos_dias": cola, "avisos": avisos}


def recall_por_sensor(mir, vistos, ours, sensores, vols):
    """Recall sobre noches con alerta de MIROVA EN QUE TENEMOS ALGUN RECORD. Las noches sin ningun record
    nuestro del mismo sensor (apagon, gránulo no bajado) se informan aparte: no miramos != no vimos."""
    out = {}
    for s in sensores:
        n = c = d = sin_datos = 0
        for (vol, b, fecha) in mir:
            if b != s or vol not in vols:
                continue
            if (vol, b, fecha) not in vistos:
                sin_datos += 1
                continue
            n += 1
            o = ours.get((vol, b, fecha))
            c += bool(o and o["crater"]); d += bool(o and o["dash"])
        out[s] = {"n_noches": n, "noches_sin_datos": sin_datos,
                  "recall_crater_pct": round(c / n * 100, 1) if n else None,
                  "recall_dash_pct": round(d / n * 100, 1) if n else None}
    return out


# --- S156 (arreglos 2 y 3 de docs/AUDIT_S155.md §5): un detector a la vez ---
# POR QUÉ: desde la fecha de OBSERVACIÓN 2026-09-18 los records de data/mirova_equivalent/ son del
# detector K (sin el Test 1 integrado, conectiva max, banda 22 primaria en MODIS) y antes, de C0. La
# ventana rodante de 60 días juntaba las dos mitades y las promediaba como una sola serie: el recall
# de K en VIIRS 375 (91,5 %, bajo la banda) quedaba tapado por el de C0 (99,1 %) y las magnitudes de
# Chillán y Tupungatito salían fuera de banda por la mezcla (F3-01, F3-02, F3-06). Ahora cada noche
# se evalúa sólo con records de su detector, cada detector se informa entero, y SÓLO el vigente decide
# los flags. Se dice «detector» y no «régimen» porque REGIMEN ya nombra focal y nevado en este script.
#
# La frontera se lee de frontend/cambio_detector.js (DATOS_K_DESDE_UTC), la misma que dibuja el tablero
# y que tests/test_cambio_detector_frontera_s155.py vigila contra los JSON: cuando el histórico con K
# la mueva, esa prueba se pone roja y al moverla este audit la sigue sin tocarlo.
CAMBIO_DETECTOR_JS = os.path.join(ROOT, "frontend", "cambio_detector.js")
DETECTORES = ("C0", "K", "sin_marca")
# D-9 (Nicolás, 2026-10-15, issue #811): las alertas de VIIRS 375 de 0,05 MW o menos, que el banner de
# MIROVA llama NONE, cuentan como «MIROVA no vio nada». La original se informa al lado.
REGLA_MINIMAS = cm.MODO_MINIMAS
TOL_PASADA_S = cm.VENTANA_S   # el pareo del etiquetador (banco_paridad.TOL_S)


def leer_frontera_k(path=CAMBIO_DETECTOR_JS):
    """Fecha 'YYYY-MM-DD' desde la que los datos son de K, o None si el tablero no declara ninguna."""
    import re
    try:
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
    except OSError:
        return None
    m = re.search(r'DATOS_K_DESDE_UTC\s*=\s*"(\d{4}-\d{2}-\d{2})T', txt)
    return m.group(1) if m else None


def detector_vigente(frontera):
    return "K" if frontera else "C0"


def detector_de_noche(fecha, frontera):
    return "K" if frontera and fecha[:10] >= frontera else "C0"


def _detector(tiene_marca, fecha, frontera):
    """K si el record trae codigo_sha (la marca nació con K, S151 loop 0.6: ningún record C0 la lleva,
    AUDIT_S155 frente 3 §0); sin marca, C0 antes de la frontera y `sin_marca` después (los MODIS Terra
    que el reproceso no pudo reescribir, F2-08). Si algún día se revierte K, la reversión también trae
    marca: habrá que comparar el sha contra el commit de la reversión, y ese día cambia esta función."""
    if tiene_marca:
        return "K"
    return "C0" if detector_de_noche(fecha, frontera) == "C0" else "sin_marca"


def detector_de_record(rec, frontera):
    return _detector(bool((rec.get("regimen") or {}).get("codigo_sha")),
                     rec.get("datetime_utc") or "", frontera)


def _detector_banco(r, frontera):
    return _detector(bool(r.get("sha")), r["noche"], frontera)


def aplicar_d9(alertas, modo=REGLA_MINIMAS, filas_ref=None):
    """Quita las pasadas mínimas (D-9) de las alertas del cargador canónico. 'original' no toca nada.

    La regla es la de `clase_mirova.aplicar_regla_minimas` (una sola implementación): una pasada es
    mínima sólo si TODAS sus filas de alerta tienen 0,05 MW o menos y ninguna alerta más alta del mismo
    volcán y sensor cae a 120 s. Para el recall, SN y SE dan lo mismo: la noche mínima no es alerta.
    Las mínimas se calculan sobre `filas_ref`, las filas de la referencia unificada (consolidado y OCR
    por separado, VRP vacío como vacío), que es sobre lo que la regla está definida. Sin ellas se
    calculan sobre las alertas del cargador, que ya vienen deduplicadas (el consolidado le gana al OCR)
    y con el VRP vacío en 0: el verificador de S156 mostró dos casos sintéticos donde eso diverge.
    """
    if modo == "original":
        return alertas
    if filas_ref is None:
        filas_ref = [{"volcano": a["volcano"], "sensor_bucket": a["sensor_bucket"],
                      "fecha_utc": a["fecha_utc"] or "", "vrp_mw": a.get("vrp_mw"), "tipo": "ALERTA_TERMICA"}
                     for a in alertas if a.get("fecha_utc")]
    minimas = cm.aplicar_regla_minimas(filas_ref, "SN").minimas
    return [a for a in alertas
            if (a["volcano"], a["sensor_bucket"], (a["fecha_utc"] or "")[:16]) not in minimas]


def noches_mirova(alertas, coords, win):
    """Noches con ALERTA nocturna de MIROVA por (volcán, sensor, fecha) con su VRP máximo."""
    mir, _, n_diurnas = noches_mirova_con_instante(alertas, coords, win)
    return mir, n_diurnas


def noches_mirova_con_instante(alertas, coords, win):
    """Lo mismo que noches_mirova y además la hora UTC de la alerta que da el máximo de cada noche (S157:
    para contar en qué noches nuestra pasada máxima y la de MIROVA son la misma)."""
    mir = defaultdict(float)
    inst = {}
    n_diurnas = 0
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if not (dt and win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in SENSORS:
            continue
        # S124: las pasadas diurnas no nos evalúan — el pipeline no las mira.
        latlon = coords.get(a["volcano"])
        if latlon:
            try:
                dt_obj = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
            except ValueError:
                dt_obj = None
            if dt_obj and es_pasada_diurna_descartada(a["sensor_bucket"], latlon[0], latlon[1], dt_obj):
                n_diurnas += 1
                continue
        key = (a["volcano"], a["sensor_bucket"], dt[:10])
        if key not in inst or (a["vrp_mw"] or 0.0) > mir[key]:
            inst[key] = dt
        mir[key] = max(mir[key], a["vrp_mw"] or 0.0)
    return mir, inst, n_diurnas


def nuestros_por_noche(records_por_volcan, win, frontera):
    """Records por noche con los criterios cráter/dash del eje 2 de S119, cada noche SÓLO con los de su
    detector. Los demás se cuentan en `fuera_de_detector` (p. ej. «sin_marca en noche K»).

    `pub` es la magnitud que el tablero publica: el núcleo F5 en VIIRS 375 (`f5_core_vrp_mw`, A10 matiz
    S132) y `pc.vrp_mw` en los otros dos (F3-06: el audit medía un número que no se publica).
    """
    ours = defaultdict(lambda: {"crater": [], "dash": [], "pub": [], "npix": [], "z_pub": [], "dt_pub": []})
    vistos, dias = set(), set()
    fuera, n_det = defaultdict(int), defaultdict(int)
    for vol, records in records_por_volcan.items():
        for rec in records:
            dt = rec.get("datetime_utc")
            if not (dt and win[0] <= dt[:10] <= win[1]):
                continue
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            dias.add(dt[:10])   # S150: hubo dato, haya o no detección, sea del detector que sea
            d_rec, d_noche = detector_de_record(rec, frontera), detector_de_noche(dt, frontera)
            n_det[d_rec] += 1
            if d_rec != d_noche:
                fuera[f"{d_rec} en noche {d_noche}"] += 1
                continue
            key = (vol, b, dt[:10])
            vistos.add(key)
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cdist = pc.get("centroid_dist_km")
            if (0 < vrp <= CAP) and (cdist is not None and cdist <= INNER[vol]):
                ours[key]["crater"].append(vrp)
                dclass = rec.get("distance_class")
                if not dclass or dclass == "summit":
                    ours[key]["dash"].append(vrp)
                    core = rec.get("f5_core_vrp_mw")
                    ours[key]["pub"].append(core if (b == "VIIRS375" and isinstance(core, (int, float))
                                                     and core > 0) else vrp)
                    # S157: cenit y hora de CADA publicación, en paralelo a `pub` (estratos de agregar_estratos).
                    ours[key]["z_pub"].append(rec.get("sensor_zenith_deg"))
                    ours[key]["dt_pub"].append(dt[:16])
                    # S124: el conteo de pixeles es la variable que estratifica
                    # los DOS modos de falla (ver bloque de estratificación).
                    ours[key]["npix"].append(len(rec.get("anomaly_pixels") or []))
    return {"ours": ours, "vistos": vistos, "dias_con_datos": dias, "fuera_de_detector": dict(fuera),
            "n_records_por_detector": dict(n_det)}


def cargar_records():
    """Records de data/mirova_equivalent/ por volcán, e integridad sobre TODO el archivo."""
    records_por_volcan = {}
    integrity = {"parse_errors": [], "duplicates_total": 0}
    for vol in VOLS:
        path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — A47-style corrupción es justo lo vigilado
            integrity["parse_errors"].append(f"{vol}: {e}")
            continue
        seen = set()
        for rec in d["records"]:
            k2 = (rec.get("datetime_utc"), rec.get("sensor"))
            if k2 in seen:
                integrity["duplicates_total"] += 1
            seen.add(k2)
        records_por_volcan[vol] = d["records"]
    return records_por_volcan, integrity


def cargar_filas_referencia():
    """Filas de la referencia unificada (para D-9), o None si no se pueden leer (cae al cargador)."""
    try:
        from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
        return cargar_referencia_unificada(CONS, OCR)
    except Exception:  # noqa: BLE001
        return None


def _mediana(xs):
    return round(statistics.median(xs), 3)


def evaluar_detector(mir, ours, vistos, detector, frontera):
    """Recall y magnitud sobre las noches de MIROVA de UN detector."""
    mir_d = {k: v for k, v in mir.items() if k[0] in VOLS and detector_de_noche(k[2], frontera) == detector}
    recall = recall_por_sensor(mir_d, vistos, ours, SENSORS, set(VOLS))
    por_vol, por_vs, pasadas_vs, por_npix = (defaultdict(list) for _ in range(4))
    for (vol, s, fecha), mvrp in mir_d.items():
        o = ours.get((vol, s, fecha))
        if not (o and o["dash"]) or mvrp <= 0:
            continue
        r_pc = max(o["dash"]) / mvrp
        por_vol[vol].append(r_pc)
        por_vs[f"{vol}|{s}"].append(max(o["pub"]) / mvrp)
        pasadas_vs[f"{vol}|{s}"].append(len(o["pub"]))
        # S124 — estratificación por conteo de píxeles. La mediana sola
        # promedia dos modos de falla OPUESTOS y los vuelve invisibles:
        # en régimen débil (1-2 px) sub-integramos y en campo difuso
        # (6+ px) sobre-integramos. Publicar los bins es lo que impide
        # que se vuelva a esconder. Agrupa los 11 volcanes: es señal de
        # deriva semana a semana, no medición del gap (para eso, el
        # script per-volcán de docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md).
        n = max(o["npix"]) if o["npix"] else 0
        por_npix["1px" if n == 1 else "2px" if n == 2 else "3-5px" if n <= 5 else "6+px"].append(r_pc)
    return {
        "detector": detector,
        "recall": recall,
        "magnitud_ratio_by_vol": {v: {"n_noches": len(r), "ratio_mediano": _mediana(r)}
                                  for v, r in sorted(por_vol.items())},
        # F3-06: la magnitud que el operador ve, por volcán Y sensor (calibraciones distintas), y cuántas
        # pasadas publican por noche, para separar «cuánto» de «cuántas» (el máximo de la noche sale de
        # menos candidatos cuando se publica en menos pasadas).
        "magnitud_publicada_by_vol_sensor": {
            k: {"n_noches": len(r), "ratio_mediano": _mediana(r),
                "pasadas_publicadas_por_noche": statistics.median(pasadas_vs[k])}
            for k, r in sorted(por_vs.items())},
        "magnitud_ratio_by_npix": {b: {"n_noches": len(r), "ratio_mediano": _mediana(r)}
                                   for b, r in sorted(por_npix.items()) if r},
    }


# --- S157 (tarea 1.35 del loop): estratos por cenit del sensor y por régimen, SIN veredicto ---
# POR QUÉ: en Nevados de Chillán la razón contra MIROVA cae con el cenit del sensor (VIIRS 0,64 a 0,72 a
# 20-22°, 0,41 a 0,46 a 49°, 0,12 a 0,35 a 67,6°, experiments/_s154_chillan/razon_por_cenit.py; atribución
# SIN ATRIBUIR). Un píxel oblicuo es más grande y más deformado, y el agregado por volcán y sensor promedia
# la curva: una semana con más pasadas de borde se lee como deriva del volcán (A90, A114). Y una ventana
# que cruza #535 (2026-08-28 23:00 UTC, A104) o la frontera de K mezcla tres regímenes. Todo esto son
# claves NUEVAS de latest.json, calculadas DESPUÉS del veredicto: no tocan flags, avisos ni claves de
# siempre (tests/test_auto_audit_cenit_s157.py lo fija contra el código previo).
CORTE_535 = "2026-08-28 23:00"   # A104: #535 apagó la máscara de nube de 260 K
REGIMENES = ("antes_535", "535_a_571", "571_a_K", "K")   # #571 = INICIO_REGIMEN_FALSAS (quitó el piso VRP)
TRAMOS_CENIT = ("z<30", "z30-50", "z50-60", "z>=60", "sin_cenit")   # orden de lectura, de nadir a borde


def tramo_cenit(z):
    """Tramo de cenit del banco de paridad (una sola implementación, A102); sin cenit, estrato aparte."""
    if z is None:
        return "sin_cenit"
    import banco_paridad as bp  # noqa: E402  (importa este módulo: se carga en runtime)
    return bp.zbin(z)


def regimen_de_pasada(dt, frontera):
    """'antes_535', '535_a_571', '571_a_K' o 'K' según la hora UTC 'YYYY-MM-DD HH:MM' de la pasada.
    El corte de #571 es INICIO_REGIMEN_FALSAS, el mismo que recorta la ventana de falsas."""
    if detector_de_noche(dt, frontera) == "K":
        return "K"
    if dt[:16] < CORTE_535:
        return "antes_535"
    return "535_a_571" if dt[:10] < INICIO_REGIMEN_FALSAS else "571_a_K"


def _por_tramo(d):
    return sorted(d.items(), key=lambda kv: TRAMOS_CENIT.index(kv[0]))


def _resumen_razones(rs):
    """rs: pares (razón, misma pasada que MIROVA: True / False / None si no se conoce la hora de MIROVA)."""
    misma = [m for _, m in rs]
    return {"n_noches": len(rs), "ratio_mediano": _mediana([x for x, _ in rs]),
            "n_misma_pasada": None if any(m is None for m in misma) else sum(misma)}


def _misma_pasada(dt_nuestra, dt_mirova):
    """¿Nuestra pasada máxima y la de MIROVA son la misma, a ±TOL_PASADA_S (el pareo del banco)?
    Nuestra hora tiene resolución de minuto ('YYYY-MM-DD HH:MM'). None si no se conoce la de MIROVA."""
    if not dt_mirova:
        return None
    try:
        a = datetime.fromisoformat(dt_nuestra[:16])
        b = datetime.fromisoformat(dt_mirova[:19])
    except ValueError:
        return None
    return abs((a - b).total_seconds()) <= TOL_PASADA_S


def estratificar_magnitud(mir, ours, frontera, vigente, instantes_mirova=None):
    """Magnitud publicada por volcán y sensor, por tramo de cenit (detector vigente, la misma población
    que `magnitud_publicada_by_vol_sensor`) y por régimen (todas las noches de la ventana, cada una con
    los records de su detector), con el cenit dentro de cada régimen.

    La razón de una noche es max(pub) / MIROVA, así que su cenit y su régimen son los de la pasada que
    publica ese máximo: la de otra pasada no entra al número.

    OJO, A116: el tramo NO es «la razón a ese cenit» pareada por pasada como la curva de S154
    (experiments/_s154_chillan/razon_por_cenit.py). Divide NUESTRO máximo de la noche por el máximo de
    MIROVA de la noche, y el cenit es sólo el de nuestra pasada: la de MIROVA puede ser otra, con otro
    cenit (verificador de S157: en las noches K pasa en 35 de 98 noches VIIRS 375 y 4 de 22 VIIRS 750).
    Por eso cada celda lleva `n_misma_pasada`, las noches en que las dos pasadas coinciden a ±120 s
    (`instantes_mirova`: hora de la alerta máxima de MIROVA por noche; sin ella el conteo queda None).
    """
    cen = defaultdict(lambda: defaultdict(list))
    reg = defaultdict(lambda: defaultdict(list))
    reg_cen = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for (vol, s, fecha), mvrp in mir.items():
        if vol not in VOLS:
            continue
        o = ours.get((vol, s, fecha))
        if not (o and o["dash"]) or mvrp <= 0:
            continue
        i = max(range(len(o["pub"])), key=lambda j: o["pub"][j])
        tramo = tramo_cenit(o["z_pub"][i])
        razon = (o["pub"][i] / mvrp,
                 _misma_pasada(o["dt_pub"][i], (instantes_mirova or {}).get((vol, s, fecha))))
        k, rg = f"{vol}|{s}", regimen_de_pasada(o["dt_pub"][i], frontera)
        if detector_de_noche(fecha, frontera) == vigente:
            cen[k][tramo].append(razon)
        reg[k][rg].append(razon)
        reg_cen[k][rg][tramo].append(razon)
    por_cenit = {k: {t: _resumen_razones(r) for t, r in _por_tramo(d)} for k, d in sorted(cen.items())}
    por_regimen = {k: {rg: {**_resumen_razones(r),
                            "por_cenit": {t: _resumen_razones(x) for t, x in _por_tramo(reg_cen[k][rg])}}
                       for rg, r in sorted(d.items(), key=lambda kv: REGIMENES.index(kv[0]))}
                   for k, d in sorted(reg.items())}
    return {"por_cenit": por_cenit, "por_regimen": por_regimen}


def falsas_por_cenit(recs, frontera, vigente):
    """Falsas publicaciones en negativos limpios del detector vigente, por sensor y tramo de cenit."""
    out = {}
    for s in SENSORS:
        zb = defaultdict(list)
        for r in recs:
            if r["b"] == s and _detector_banco(r, frontera) == vigente:
                zb[tramo_cenit(r.get("z"))].append(r)
        out[s] = {t: _pct_falsas(v) for t, v in _por_tramo(zb) if any(x["lab"] == "neg_limpio" for x in v)}
    return out


def agregar_estratos(out, mir, ours, frontera, vigente, recs_falsas, instantes_mirova=None):
    """Agrega a `out` las claves de S157. Sólo agrega: no reemplaza ni borra ninguna clave existente."""
    est = estratificar_magnitud(mir, ours, frontera, vigente, instantes_mirova)
    out["magnitud_publicada_by_vol_sensor_cenit"] = est["por_cenit"]
    out["magnitud_publicada_by_vol_sensor_regimen"] = est["por_regimen"]
    falsas = out.get("falsas_publicaciones")
    if isinstance(falsas, dict) and "error" not in falsas and recs_falsas is not None:
        falsas["por_cenit"] = falsas_por_cenit(recs_falsas, frontera, vigente)


def flags_de_evaluacion(ev):
    """Flags de recall (cráter, bandas de S119) y de magnitud PUBLICADA por volcán y sensor.

    El recall sigue juzgando «cráter» porque RECALL_MIN se calibró sobre cráter (S119) y no hay bandas
    para publicación (A115: no inventar un umbral). La publicación la protege la lista nominal de
    alertas protegidas (flags_protegidas)."""
    flags = []
    for s in SENSORS:
        r = ev["recall"][s]
        if r["n_noches"] >= MIN_N_RECALL and r["recall_crater_pct"] is not None \
                and r["recall_crater_pct"] < RECALL_MIN[s]:
            flags.append(f"recall {s} {r['recall_crater_pct']}% < banda {RECALL_MIN[s]}% "
                         f"(n={r['n_noches']}, detector {ev['detector']})")
    for k, m in ev["magnitud_publicada_by_vol_sensor"].items():
        vol, s = k.split("|")
        v = evaluar_ratio_mediano(vol, m["ratio_mediano"], m["n_noches"], sensor=s)
        if v:
            flags.append(v)
    return flags


def alertas_protegidas(filas, recs_banco, win, frontera, diurna=None):
    """Cada pasada nocturna de la ventana con una alerta protegida de MIROVA (lectura A: alerta del
    scraper de 1 MW o más, `clase_mirova.alerta_protegida`) y qué hizo el tablero con ella.

    POR QUÉ (F3-04 de AUDIT_S155): el criterio de victoria de la réplica no acepta perder ninguna, y el
    audit no lo miraba: dos protegidas MODIS de Chillán (2026-10-12 07:20, 2,18 MW; 2026-10-15 01:05,
    1,72 MW) se perdieron sin aviso, y la banda de recall MODIS no puede dispararse desde el 2026-08-03
    porque ninguna ventana junta 15 noches. Con n chico una sola pérdida es el dato: lista, no tasa.

    estado: `publicada` (algún record nuestro a ±120 s la publica, predicado del tablero con node),
    `sin_publicar` (hay record y no publica) o `sin_record` (no miramos: no es «no vimos», S150).
    """
    if diurna is None:
        coords = _coords_por_volcan()

        def diurna(b, vol, dt):
            ll = coords.get(vol)
            return bool(ll) and es_pasada_diurna_descartada(b, ll[0], ll[1], dt)
    prot, instante, fuentes = {}, {}, defaultdict(set)
    for f in filas:
        if not cm.alerta_protegida(f) or not (win[0] <= f["fecha_utc"][:10] <= win[1]):
            continue
        try:
            dt = datetime.fromisoformat(f["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if diurna(f["sensor_bucket"], f["volcano"], dt):
            continue
        k = cm.clave_pasada(f)
        prot[k] = max(prot.get(k, 0.0), f["vrp_mw"])
        instante.setdefault(k, dt)
        fuentes[k].add(f.get("source"))
    por_vb = defaultdict(list)
    for r in recs_banco:
        por_vb[(r["vol"], r["b"])].append(r)
    lista = []
    for k in sorted(prot, key=lambda x: (x[2], x[0], x[1])):
        vol, b, minuto = k
        dt = instante[k]
        cand = [r for r in por_vb.get((vol, b), []) if abs((r["dt"] - dt).total_seconds()) <= TOL_PASADA_S]
        estado = ("sin_record" if not cand else "publicada" if any(r["pub"] for r in cand) else "sin_publicar")
        otras = [r for b2 in SENSORS for r in por_vb.get((vol, b2), [])
                 if r["noche"] == minuto[:10] and not any(r is c for c in cand)]
        lista.append({"volcano": vol, "sensor": b, "fecha_utc": minuto, "vrp_mirova_mw": round(prot[k], 3),
                      "detector": detector_de_noche(minuto, frontera), "estado": estado,
                      "detector_records": sorted({_detector_banco(r, frontera) for r in cand}),
                      "noche_publicada_otra_pasada": any(r["pub"] for r in otras),
                      "referencia_sospechosa": (fuentes[k] == {"OCR"} and minuto[:10] < HITO_OCR_SUOMI_NPP
                                                and any("SNPP" in (r.get("sensor") or "") for r in cand))})
    return lista


# A119: antes de este hito, en las filas SÓLO OCR de Suomi NPP la distancia y la clase pueden ser de OTRA
# pasada (el VRP sí es de la suya). Una protegida que descansa sólo en una de esas filas sigue siendo
# protegida por su VRP, pero el flag lo dice: dos de las cinco del 2026-10-19 (Tupungatito 28 y 29 de
# septiembre) eran así, con nuestros cúmulos a 21,6 y 9,4 km (verificador de S156). El hito vive en
# scripts/calidad_referencia_mirova.py, no copiado acá.
def _hito_ocr_suomi_npp():
    try:
        from calidad_referencia_mirova import HITOS  # noqa: E402
    except ImportError:
        from scripts.calidad_referencia_mirova import HITOS  # noqa: E402
    return next(f for f, canal, quien, _ in HITOS if canal == "ocr" and "Suomi" in quien)


HITO_OCR_SUOMI_NPP = _hito_ocr_suomi_npp()


def avisos_protegidas_sin_record(lista, vigente):
    """S160 (V3-01 de docs/AUDIT_S160.md): protegidas de MIROVA en pasadas de las que no tenemos record.

    POR QUÉ: cuando una plataforma se calla (Suomi NPP cesa el 2026-11-02) las otras siguen dando datos ese
    día, así que la guarda de cobertura por días no se entera. S150 separó `sin_record` de `sin_publicar`
    porque «no miramos» no es «no vimos»: por eso va como aviso de cobertura (veredicto DEGRADADO), no como
    flag de pérdida de detección. Test: tests/test_auto_audit_protegida_sin_record_s160.py."""
    return [f"alerta protegida sin record nuestro: {p['volcano']} {p['sensor']} {p['fecha_utc']} UTC, "
            f"MIROVA {p['vrp_mirova_mw']} MW (no miramos esa pasada: plataforma callada o gránulo perdido)"
            for p in lista if p["detector"] == vigente and p["estado"] == "sin_record"]


def flags_protegidas(lista, vigente):
    out = []
    for p in lista:
        if p["detector"] != vigente or p["estado"] != "sin_publicar":
            continue
        noche = ("la noche sí se publicó en otra pasada" if p["noche_publicada_otra_pasada"]
                 else "ninguna otra pasada de esa noche se publicó")
        sospecha = (f"; referencia sospechosa: sólo OCR de Suomi NPP antes del {HITO_OCR_SUOMI_NPP}, la "
                    "distancia puede ser de otra pasada (A119)" if p.get("referencia_sospechosa") else "")
        out.append(f"alerta protegida sin publicar: {p['volcano']} {p['sensor']} {p['fecha_utc']} UTC, "
                   f"MIROVA {p['vrp_mirova_mw']} MW (detector {p['detector']}; {noche}{sospecha})")
    return out


def linea_historial(out, cobertura_pct, gt_stale_dias):
    """Linea de `history.jsonl`: lo unico que se conserva semana a semana (latest.json se sobrescribe).

    POR QUE lleva la publicacion en negativos limpios (S153, adopcion de K, REGLA_ADOPCION.md §4.8):
    con K la de VIIRS 375 cae de 85 a 88 % a 2,5 a 3,7 % (experiments/_s153_fk_v2/, seccion 9 de los
    logs), y la sombra del §4.9 investiga si sube por sobre lo medido en el A/B. Sin la serie no hay
    contra que comparar. Sin alarma (decision S140): no agrega flags ni toca el veredicto. Si el banco
    no corrio, el valor queda en None y `falsas_error` lo dice, en vez de un cero que se leeria como
    "no publica en ningun negativo".
    """
    # S156: desde esta línea, recall y falsas son SÓLO del detector vigente y la clave `detector` dice
    # cuál, con su frontera de datos y la regla D-9 usada. Las líneas anteriores no la traen: eran la
    # mezcla de C0 y K (F3-02), y no se comparan con las nuevas.
    falsas = out.get("falsas_publicaciones") or {}
    por_sensor = falsas.get("por_sensor") or {}
    return {"date": out["generated_utc"][:10], "verdict": out["verdict"],
            "detector": out.get("detector"),
            "cobertura_pct": cobertura_pct, "gt_stale_dias": gt_stale_dias,
            "recall": {s: out["recall"][s]["recall_crater_pct"] for s in SENSORS},
            "n_flags": len(out["flags"]),
            "falsas_pub_pct": {s: (por_sensor.get(s) or {}).get("falsas_pub_pct") for s in SENSORS},
            "n_neg_limpio": {s: (por_sensor.get(s) or {}).get("n_neg_limpio") for s in SENSORS},
            "falsas_error": "error" in falsas}


def main():
    today = datetime.now(timezone.utc).date()
    win = ((today - timedelta(days=WINDOW_DAYS)).isoformat(), today.isoformat())
    frontera = leer_frontera_k()
    vigente = detector_vigente(frontera)

    # 1. MIROVA (loader canónico, CONS ∪ OCR ∪ filas perdidas): noches ALERTA por (vol, bucket, fecha).
    #    S156: con la regla D-9 decidida (SN) y, aparte, con la original, que sólo se informa.
    alertas = alertas_mirova()
    coords = _coords_por_volcan()
    filas_ref = cargar_filas_referencia()
    mir, inst_mir, n_diurnas_excluidas = noches_mirova_con_instante(aplicar_d9(alertas, REGLA_MINIMAS, filas_ref),
                                                                    coords, win)
    mir_original, _ = noches_mirova(alertas, coords, win)

    # 2. Nuestros records + integridad (la integridad mira TODO el archivo, no sólo la ventana)
    records_por_volcan, integrity = cargar_records()
    nuestros = nuestros_por_noche(records_por_volcan, win, frontera)
    ours, vistos = nuestros["ours"], nuestros["vistos"]

    # 3. Recall y magnitud, un detector a la vez. Sólo el vigente decide flags.
    por_detector = {det: evaluar_detector(mir, ours, vistos, det, frontera) for det in ("C0", "K")
                    if det == vigente or any(detector_de_noche(k[2], frontera) == det for k in mir)}
    ev = por_detector[vigente]
    recall_original = recall_por_sensor(
        {k: v for k, v in mir_original.items() if detector_de_noche(k[2], frontera) == vigente},
        vistos, ours, SENSORS, set(VOLS))

    # 4. Flags contra bandas
    flags = flags_de_evaluacion(ev)
    if integrity["parse_errors"]:
        flags.append(f"integridad: {len(integrity['parse_errors'])} JSON con parse error")
    if integrity["duplicates_total"]:
        flags.append(f"integridad: {integrity['duplicates_total']} records duplicados (datetime,sensor)")

    avisos_detector = []
    n_k_en_c0 = nuestros["fuera_de_detector"].get("K en noche C0")
    if n_k_en_c0 and frontera is None:
        avisos_detector.append(
            f"no se leyó DATOS_K_DESDE_UTC de frontend/cambio_detector.js y hay {n_k_en_c0} records de K: "
            "todas las noches se están evaluando como C0 y K queda fuera del veredicto")
    elif n_k_en_c0:
        avisos_detector.append(
            f"{n_k_en_c0} records de K con fecha anterior a la frontera {frontera}: si el histórico con K ya "
            "se aplicó, mover DATOS_K_DESDE_UTC en frontend/cambio_detector.js (esas noches se están "
            "evaluando con C0)")

    # 5. Banco de paridad (predicado del tablero con node): alertas protegidas y falsas publicaciones.
    #    Si no corre, las protegidas quedan sin evaluar y eso SÍ degrada el veredicto: el criterio de
    #    victoria de la réplica no puede darse por cumplido sin mirarlo.
    banco, protegidas, error_banco = None, None, None
    try:
        banco = banco_ventana(win)
        protegidas = alertas_protegidas(banco[1], banco[0], win, frontera)
        flags.extend(flags_protegidas(protegidas, vigente))
    except Exception as e:  # noqa: BLE001
        error_banco = f"{type(e).__name__}: {str(e)[:300]}"
    # S156 (verificador, mutación «sin sha en el banco»): si el banco perdiera la marca de detector, las
    # falsas de K quedarían con n 0 y valor None sin que nada lo dijera.
    n_k_nuestros = nuestros["n_records_por_detector"].get("K", 0)
    if banco is not None and n_k_nuestros and not any(r.get("sha") for r in banco[0]):
        avisos_detector.append(f"el banco de paridad no trae la marca de detector (sha) y hay {n_k_nuestros} "
                               "records de K en la ventana: las falsas por detector no se pueden separar")

    # --- S124: cobertura de la ventana, ANTES de interpretar los flags ---
    # S150 (D-02): dias con DATOS (no con deteccion) y la cola sin datos al final de la ventana.
    cob = cobertura_de_ventana(nuestros["dias_con_datos"], win, today)
    dias_ventana, cobertura_pct = cob["dias_ventana"], cob["cobertura_propia_pct"]

    # Frescura del ground truth: se mide sobre TODO el CSV, no sobre las ALERTAS.
    # Un período sin alertas es información legítima (los volcanes pueden estar
    # tranquilos); lo que delata a un scraper muerto es que el archivo entero
    # deje de crecer, y el CSV trae también los registros de RUTINA (los "miré y
    # no había nada"), que se generan todos los días haya o no actividad.
    gt_ultima, gt_stale_dias = _csv_ultima_fecha(CONS), None
    if gt_ultima:
        gt_stale_dias = (today - datetime.fromisoformat(gt_ultima).date()).days

    # S156: un aviso de detector también degrada. Si la frontera no se lee o quedó atrás de los datos,
    # las noches de K se evalúan como C0 y K desaparece del veredicto sin que nada lo diga (verificador).
    cobertura_avisos = list(cob["avisos"]) + [f"detector: {a}" for a in avisos_detector]
    if gt_stale_dias is None:
        cobertura_avisos.append("no se pudo leer la fecha del ground truth: referencia sospechosa")
    elif gt_stale_dias > MAX_GT_STALE_DAYS:
        cobertura_avisos.append(
            f"ground truth stale: el CSV MIROVA no registra nada hace "
            f"{gt_stale_dias} días (> {MAX_GT_STALE_DAYS}) — es el scraper, no los volcanes")
    if error_banco:
        cobertura_avisos.append(f"no se pudieron evaluar las alertas protegidas (banco de paridad): {error_banco}")
    if protegidas:
        cobertura_avisos.extend(avisos_protegidas_sin_record(protegidas, vigente))

    cobertura = {
        "cobertura_propia_pct": cobertura_pct,
        "dias_con_datos": cob["dias_con_datos"],
        "dias_ventana": dias_ventana,
        "ultimo_dia_con_datos": cob["ultimo_dia_con_datos"],
        "cola_sin_datos_dias": cob["cola_sin_datos_dias"],
        "gt_ultima_fecha_csv": gt_ultima,
        "gt_stale_dias": gt_stale_dias,
        # Transparencia: un filtro que descarta en silencio es tan malo como no
        # tenerlo. Si este número se dispara, es señal de otra cosa (A76).
        "alertas_diurnas_excluidas": n_diurnas_excluidas,
        "avisos": cobertura_avisos,
    }

    # DEGRADADO gana sobre todo: si no sabemos si la ventana es interpretable,
    # decirlo es más honesto que un VERDE o un FUERA_DE_BANDA que no se sostiene.
    if cobertura_avisos:
        verdict = "DEGRADADO"
    elif flags:
        verdict = "FUERA_DE_BANDA"
    else:
        verdict = "VERDE"

    # S140 (Fase 0, tarea 6): falsas publicaciones, medidas sin alarma (decisión Nicolás).
    # Si el banco no puede correr (sin node, CSV ilegible), el error queda escrito en el
    # bloque en vez de tumbar el audit: recall y magnitud siguen valiendo por sí solos.
    # S156: por detector; las claves de siempre son las del vigente.
    win_falsas = ventana_falsas(today)
    recs_falsas = None
    if banco is None:
        falsas = {"error": error_banco, "alarma": False}
    else:
        recs_falsas = medir_falsas_ventana(win_falsas, banco)
        falsas = resumir_falsas_por_detector(recs_falsas, frontera, vigente)

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": list(win),
        "ventana_falsas": list(win_falsas),
        "detector": {"vigente": vigente, "frontera_datos": frontera, "regla_minimas": REGLA_MINIMAS},
        "cobertura": cobertura,
        "criteria": ("eje2 S119 (crater A10 + dash), loader canónico CONS∪OCR, referencia filtrada a pasadas "
                     "nocturnas con la misma regla del pipeline (_reject_daytime, S124); S156: cada noche con "
                     "records de su detector, flags sólo del vigente, D-9 SN, magnitud publicada por volcán "
                     "y sensor, alertas protegidas (lectura A) nominales"),
        "recall": ev["recall"],
        "recall_regla_original": recall_original,
        "magnitud_ratio_by_vol": ev["magnitud_ratio_by_vol"],
        "magnitud_publicada_by_vol_sensor": ev["magnitud_publicada_by_vol_sensor"],
        "magnitud_ratio_by_npix": ev["magnitud_ratio_by_npix"],
        "por_detector": por_detector,
        "fuera_de_detector": nuestros["fuera_de_detector"],
        "avisos_detector": avisos_detector,
        "alertas_protegidas": {"lectura": "A", "umbral_mw": cm.UMBRAL_PROTEGIDA_MW, "lista": protegidas,
                               "error": error_banco},
        "falsas_publicaciones": falsas,
        "integrity": integrity,
        "flags": flags,
        "verdict": verdict,
    }
    # S157: estratos por cenit y régimen, después del veredicto y sin tocarlo.
    agregar_estratos(out, mir, ours, frontera, vigente, recs_falsas, inst_mir)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    hist_line = linea_historial(out, cobertura_pct=cobertura_pct, gt_stale_dias=gt_stale_dias)
    with open(os.path.join(OUTDIR, "history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(hist_line, ensure_ascii=False) + "\n")

    print(f"Auto-audit semanal — ventana {win[0]} → {win[1]} · detector vigente {vigente} "
          f"(datos desde {frontera}) · D-9 {REGLA_MINIMAS}")
    for det, e in por_detector.items():
        for s in SENSORS:
            r = e["recall"][s]
            print(f"  [{det}] {s:<9} recall crater {r['recall_crater_pct']}% "
                  f"publicación {r['recall_dash_pct']}% (n={r['n_noches']})")
    for k, m in ev["magnitud_publicada_by_vol_sensor"].items():
        print(f"  [{vigente}] magnitud publicada {k:<30} {m['ratio_mediano']}x (n={m['n_noches']})")
        tramos = (out.get("magnitud_publicada_by_vol_sensor_cenit") or {}).get(k) or {}
        if tramos:
            print("      por cenit: " + " · ".join(f"{t} {v['ratio_mediano']}x (n={v['n_noches']})"
                                               for t, v in tramos.items()))
    if "error" in falsas:
        print(f"FALSAS PUBLICACIONES: no se pudo medir: {falsas['error']}")
    else:
        for det, ps in falsas["por_detector"].items():
            for s in SENSORS:
                p = ps[s]
                print(f"  [{det}] falsas {s:<9} {p['falsas_pub_pct']}% de {p['n_neg_limpio']} pasadas "
                      f"negativas limpias (sin alarma)")
    for p in (protegidas or []):
        if p["estado"] != "publicada":
            print(f"  protegida {p['estado']:<12} [{p['detector']}] {p['volcano']} {p['sensor']} "
                  f"{p['fecha_utc']} MIROVA {p['vrp_mirova_mw']} MW")
    for a in avisos_detector:
        print(f"DETECTOR: {a}")
    for av in cobertura_avisos:
        print(f"COBERTURA: {av}")
    print(f"VEREDICTO: {out['verdict']}" + (f" — {len(flags)} flags" if flags else ""))
    for fl in flags:
        print("  ⚠", fl)


if __name__ == "__main__":
    main()
