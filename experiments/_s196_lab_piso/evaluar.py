# -*- coding: utf-8 -*-
"""Evaluador pre-registrado de la palanca del piso en la zona A del laboratorio (MEJ-5), S196.

ESCRITO ANTES DE TENER DATOS DEL LABORATORIO CON ESTA PALANCA. El criterio está sellado en
`experiments/_s196_lab_piso/PREREGISTRO.md`; no se edita después del sello sin re-sellar: la prueba
`tests/test_lab_piso_preregistro_s196.py` compara su sha256 (fin de línea LF) con el que declara el pre-registro, y
también el del evaluador S194 del que importa la vara.

POR QUÉ existe. En la región sensible el umbral contextual nocturno es max(mu + s * sd, piso), en NTI y en ETI, con
s = 5 y piso = 0,003 en los dos (pipeline/mirova_v750_codigo.py::detectar_mirova, .m l. 177-199). El barrido de s
(S195) se aplanó porque al bajar s manda el piso; con s = 5, en cambio, manda el término mu + 5 sd en cuanto el
piso baja de 0,0015 (experiments/_s196_lab_piso/salida_medir_cruces.txt). Este evaluador elige el piso de la zona A
con s fijo en S_A, sobre el mismo camino monótono que empezó el barrido de s: producción (s = 5, piso 0,003), luego
(S_A, 0,003), luego (S_A, pisos menores).

QUÉ CAMBIA RESPECTO DEL S194 Y QUÉ NO.
  - NO cambia la vara (§3 y §4 del pre-registro S194): `veredicto`, el pareo NHI, la permutación estratificada, el
    control de 15 días, SIN PODER bajo 10, la persistencia temporal. Se importan del evaluador S194 sin copiarlos.
  - Cambia la regla para elegir el valor (§5 del S194): `elegir_piso` en vez de `elegir_valor`, con la misma tasa
    objetivo (30 %), la misma unidad (la noche), la misma ventana (desde 2026-03-01) y el mismo mínimo de 30 negativos.
  - Cambia el control de identidad: el brazo de producción dentro del barrido (`control`, la zona encendida con
    s = 5 y piso 0,003) tiene que ser idéntico, record a record, al brazo con la zona apagada de la misma corrida, y
    dar las cuentas de producción (lo del S194). Si S_A == 5, el primer brazo de la grilla es ese mismo brazo.

Uso:
  python experiments/_s196_lab_piso/evaluar.py calibrar --sin-zona <dir> --control <dir> \
      --brazo 0.003=<dir> --brazo 0.00275=<dir> ... --dest <tmp> --out c.json
  python experiments/_s196_lab_piso/evaluar.py evaluar ...   (la vara del S194, sin cambios)
  python experiments/_s196_lab_piso/evaluar.py poder         (tabla de poder del S194)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUTA_S194 = ROOT / "experiments" / "_s194_lab_zona_a" / "evaluar.py"


def _cargar_s194():
    spec = importlib.util.spec_from_file_location("evaluar_s194_para_s196", RUTA_S194)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _cargar_s194()

# ------------------------------------------------------------------------------------------------ valores sellados
S_CONTROL = 5.0                # s2 nocturno de producción (.m)
PISO_PROD = 0.003              # n2 = e2 nocturnos de producción (.m): el piso de hoy, en NTI y en ETI
S_A = 3.0                      # s de la zona A en todos los brazos de piso (PREREGISTRO §3; pregunta 1 a Nicolás)
GRILLA_PISO = (0.003, 0.00275, 0.0025, 0.00225, 0.002, 0.00175, 0.0015)   # un solo piso para NTI y ETI
CONTROL = "control"            # brazo (S_CONTROL, PISO_PROD) con la zona encendida
CAMINO = (CONTROL,) + GRILLA_PISO
TASA_OBJETIVO = E.TASA_OBJETIVO
UNIDAD_TASA = E.UNIDAD_TASA
N_MIN_NEG = E.N_MIN_NEG_SENSOR
INVALIDO, SIN_PODER = E.INVALIDO, E.SIN_PODER
# Campos que el control de identidad compara record a record (los que deciden qué publica el tablero y dónde).
CAMPOS_IDENTIDAD = ("vrp_mw", "distance_class", "final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km")
CAMPOS_PC = ("vrp_mw", "centroid_dist_km", "n_pixels")
CAMPOS_DIAG = ("n_abs", "n_p1", "n_p2", "motivo_vacio")
# Records en que la zona A no puede actuar (de día, o fuera de la vía): en todo brazo tienen que ser los del brazo sin
# zona. Es lo único que vigila una fuga del piso fuera de la zona, porque en el brazo control el piso vale lo mismo
# dentro y fuera (verificador S196, debilidad 3).

# La vara: la misma función del S194, no una copia (PREREGISTRO §4).
veredicto = E.veredicto


# ------------------------------------------------------------------------------------------------ calibración
def elegir_piso(tasas, unidad=None):
    """Regla del §5 de este pre-registro. `tasas`: {clave_brazo: {clave: (n_pub, n_neg)}} con clave_brazo en CAMINO
    (CONTROL y cada piso de GRILLA_PISO) y clave cada sensor (unidad pasada) o "NOCHE" (unidad noche), medidas con
    `E.tasas_barrido`. Devuelve {"estado", "valor", "detalle"}; valor = {"s_a", "piso_a"} o None."""
    claves = E.CLAVES_UNIDAD[unidad or UNIDAD_TASA]
    falta = [k for k in CAMINO if k not in tasas]
    if falta:
        return {"estado": INVALIDO, "valor": None, "detalle": "faltan brazos del barrido: %s" % falta}
    for sen in claves:
        if any(tasas[k][sen][1] < N_MIN_NEG for k in CAMINO):
            return {"estado": SIN_PODER, "valor": None,
                    "detalle": "%s con menos de %d negativos limpios en algún brazo" % (sen, N_MIN_NEG)}
        r = [tasas[k][sen][0] / tasas[k][sen][1] for k in CAMINO]
        if any(r[i + 1] < r[i] for i in range(len(r) - 1)):
            return {"estado": INVALIDO, "valor": None,
                    "detalle": "%s: la tasa baja a lo largo del camino control, pisos (no monótona): %s"
                               % (sen, [round(x, 4) for x in r])}

    def ok(k):   # entero, sin coma flotante: n_pub / n_neg <= 0,30  <=>  10 n_pub <= 3 n_neg
        return all(10 * tasas[k][sen][0] <= round(10 * TASA_OBJETIVO) * tasas[k][sen][1] for sen in claves)

    if not ok(CONTROL):
        return {"estado": "SIN VALOR", "valor": None, "detalle": "producción ya supera la tasa objetivo"}
    if not ok(GRILLA_PISO[0]):
        return {"estado": "SIN VALOR DE PISO", "valor": None,
                "detalle": "con s = %.1f y el piso de hoy ya se supera la tasa objetivo: el valor está en el tramo de "
                           "s entre 5 y %.1f, que este barrido no corre; a Nicolás" % (S_A, S_A)}
    elegido = GRILLA_PISO[0]
    for p in GRILLA_PISO[1:]:
        if not ok(p):
            break
        elegido = p
    valor = {"s_a": S_A, "piso_a": elegido}
    if S_A == S_CONTROL and elegido == PISO_PROD:
        return {"estado": "SIN EXTENSION", "valor": valor, "detalle": "el primer piso menor ya supera la tasa"}
    det = "menor piso de la grilla que cumple"
    if elegido == GRILLA_PISO[0]:
        det += " (el piso de hoy: sólo actúa el s de la zona A)"
    if elegido == GRILLA_PISO[-1]:
        det += " (el piso de la grilla: el barrido no alcanzó la tasa objetivo)"
    return {"estado": "ELEGIDO", "valor": valor, "detalle": det}


def control_tasas(tasas, tasas_prod):
    """El brazo de producción del barrido da exactamente las cuentas de producción (como el control del S194)."""
    if tasas.get(CONTROL) != tasas_prod:
        return False
    return S_A != S_CONTROL or tasas.get(GRILLA_PISO[0]) == tasas_prod


def _firma(r):
    pc = r.get("primary_cluster") or {}
    dg = r.get("diag_codigo_mirova") or {}
    return (tuple(r.get(c) for c in CAMPOS_IDENTIDAD) + tuple(pc.get(c) for c in CAMPOS_PC)
            + tuple(dg.get(c) for c in CAMPOS_DIAG) + (json.dumps(dg.get("s1"), sort_keys=True),))


def zona_no_actua(r):
    """De día (dayflag 1) o sin la vía (record de la guardia K): la zona A no tiene cómo cambiar el record."""
    return not r.get("via_codigo_mirova") or (r.get("diag_codigo_mirova") or {}).get("dayflag") == 1


def identidad_records(recs_brazo, recs_sin_zona, permitir_vacio=False):
    """Record a record: mismas pasadas (volcán, sensor, hora) y misma firma de detección (incluidos mu, sd, umbrales y
    celda decisiva de cada pase). Devuelve {"identico", "n", "diferencias"} con hasta 10 diferencias para el informe.
    Vacío no es identidad, salvo con permitir_vacio (el subconjunto «la zona no actúa» puede no tener records)."""
    a = {(r["_vol"], r.get("sensor"), r.get("datetime_utc")): _firma(r) for r in recs_brazo}
    b = {(r["_vol"], r.get("sensor"), r.get("datetime_utc")): _firma(r) for r in recs_sin_zona}
    dif = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return {"identico": not dif and (permitir_vacio or len(a) > 0), "n": len(a), "diferencias": [list(k) for k in dif[:10]],
            "n_diferencias": len(dif)}


def cargar_records(directorio):
    """Todos los records del brazo (sin ventana: la identidad se exige en todo lo que se corrió), de los 10 volcanes
    de la zona A y, si el brazo los trae, de los volcanes fuera (Cordón Caulle), donde la zona nunca actúa."""
    out = []
    for vol in E.VOLCANES_ZONA_A + E.VOLCANES_FUERA:
        ruta = Path(directorio) / ("%s.json" % vol)
        if not ruta.exists():
            if vol in E.VOLCANES_FUERA:
                continue
            raise FileNotFoundError("falta %s" % ruta)
        d = json.loads(ruta.read_text(encoding="utf-8"))
        for r in (d["records"] if isinstance(d, dict) else d):
            out.append(dict(r, _vol=vol))
    return out


def _sin_actuar(recs):
    return [r for r in recs if zona_no_actua(r) or r["_vol"] in E.VOLCANES_FUERA]


# ------------------------------------------------------------------------------------------------ re-sello S200
# Decisión de Nicolás del 2026-11-25 («Sí, re-sella»), antes de mirar ningún resultado del barrido. Arreglos de la ronda
# 4 de la auditoría externa con Codex (frente D), verificados por un Claude de contexto limpio
# (experiments/_s196_lab_piso/PROPUESTA_RESELLO_S199.md). La vara (S194) no cambia. Pruebas:
# tests/test_lab_piso_resello_s200.py.
N_MIN_FUERA = N_MIN_NEG        # R4FD-102: mínimo de records comparados donde la zona no actúa (el umbral de poder §5)
# R4FD-107 (S200c; acta de cierre de la ronda 4, aprobada por Nicolás el 2026-11-25). POR QUÉ: con las mismas carpetas,
# fin 2026-05-31 elegía 0,0025, fin 07-31 elegía 0,00225 y fin 11-20 elegía 0,002; quien evalúa podía elegir el fin
# mirando el resultado. El fin queda sellado en el último día de la última tanda despachada, antes de mirar nada.
FIN_SELLADO = "2026-11-23"
PERFIL_LAB = ROOT / "pipeline" / "profiles" / "laboratorio.yaml"
CSV_REFERENCIA = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv")


def _dia_modis_lab():
    """El laboratorio guarda MODIS de día sólo si su perfil lo declara (hoy no: `paths.enable_daytime_modis: false`)."""
    import yaml
    p = yaml.safe_load(PERFIL_LAB.read_text(encoding="utf-8")) or {}
    return bool((p.get("paths") or {}).get("enable_daytime_modis", False))


def _herramientas_almacen():
    """La regla de día del almacén y las coordenadas de volcanoes.yaml, cargadas UNA vez por llamada a
    prod_como_laboratorio (re-sello S200b: releerlas en cada record costaba unos 82 minutos sobre producción entera,
    medido por el verificador de #1129)."""
    for p in (str(ROOT), str(ROOT / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    from pipeline.store import _reject_daytime, _solar_elevation
    import banco_paridad as bp
    return _reject_daytime, _solar_elevation, bp._coords_por_volcan()


def rechaza_como_laboratorio(r, vol, dia_modis_lab=None, herramientas=None):
    """R4FD-V201. POR QUÉ: desde el 2026-11-15 12:30 UTC producción guarda las pasadas MODIS de día y el almacén del
    laboratorio las rechaza (pipeline/store.py::_reject_daytime con su perfil), así que el control «el brazo de
    producción da las cuentas de producción» salía INVÁLIDO por construcción con cualquier ventana que llegue hasta
    hoy. Se aplica a producción la MISMA regla del almacén (misma función, mismas coordenadas de volcanoes.yaml) con los
    flags del laboratorio. VIIRS no se filtra aquí: su día lo decide el mismo flag vivo en los dos perfiles
    (pipeline/diurno.py), así que no puede separar al laboratorio de producción. Un record sin hora legible el almacén
    lo guarda, y aquí se conserva."""
    _reject_daytime, _solar_elevation, coords = herramientas or _herramientas_almacen()
    try:
        dt = datetime.strptime(r.get("datetime_utc", ""), "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return False
    lat, lon = coords[vol]
    dia = _dia_modis_lab() if dia_modis_lab is None else dia_modis_lab
    return _reject_daytime(r.get("sensor", ""), _solar_elevation(lat, lon, dt), dia, enable_daytime_viirs=True)


def prod_como_laboratorio(prod, destino):
    """Copia de los JSON de producción (los volcanes del banco) sin los records que el almacén del laboratorio habría
    rechazado. Devuelve (carpeta, {volcán: records quitados})."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    dia = _dia_modis_lab()
    herr = _herramientas_almacen()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    quitados = {}
    for vol in bp.VOLS:
        ruta = Path(prod) / ("%s.json" % vol)
        if not ruta.exists():
            continue
        d = json.loads(ruta.read_text(encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) else d
        quedan = [r for r in recs if not rechaza_como_laboratorio(r, vol, dia, herr)]
        quitados[vol] = len(recs) - len(quedan)
        salida = dict(d, records=quedan) if isinstance(d, dict) else {"records": quedan}
        (destino / ("%s.json" % vol)).write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    return str(destino), quitados


def _en_ventana(r, fin):
    return E.VENTANA_CALIBRACION_INICIO <= str(r.get("datetime_utc", ""))[:10] <= fin


def _clave(r):
    return (r["_vol"], r.get("sensor"), r.get("datetime_utc"))


def cobertura_brazos(recs_por_brazo, fin):
    """R4FD-101. POR QUÉ: si un brazo pierde pasadas que otro tiene (un trozo que muere a mitad de la lista, un brazo
    que cae un día), su tasa por noche cambia y la elección del piso también, sin que nada lo invalide (caso medido:
    17 noches perdidas en 0,00175 cambiaban la elección de 0,002 a 0,00175). Todos los brazos tienen que cubrir
    exactamente las mismas pasadas (volcán, sensor, hora) dentro de la ventana de calibración; la referencia es el
    brazo sin zona."""
    claves = {k: {_clave(r) for r in recs if _en_ventana(r, fin)} for k, recs in recs_por_brazo.items()}
    ref = claves["sin_zona"]
    dif = {}
    for k, c in claves.items():
        if c != ref:
            dif[k] = {"faltan": len(ref - c), "sobran": len(c - ref),
                      "ejemplos": [list(x) for x in sorted(ref ^ c, key=lambda x: tuple(map(str, x)))[:5]]}
    return {"igual": not dif, "n": len(ref), "diferencias": dif}


def codigo_brazos(recs_por_brazo, fin):
    """R4FD-105. POR QUÉ: juntar tandas de corridas distintas, o relanzar sólo algunos brazos, podía mezclar versiones
    del código sin aviso. En cada pasada todos los brazos tienen que traer el mismo `regimen.codigo_sha`. Entre tandas
    el código puede cambiar (cada mes se despacha aparte): se declara cada código con el tramo de fechas que cubre."""
    por = {}
    for k, recs in recs_por_brazo.items():
        for r in recs:
            if _en_ventana(r, fin):
                por.setdefault(_clave(r), {})[k] = (r.get("regimen") or {}).get("codigo_sha")
    mezcla = sorted((c for c, d in por.items() if len(set(d.values())) > 1), key=lambda x: tuple(map(str, x)))
    codigos = {}
    for c, d in por.items():
        for sha in set(d.values()):
            t = codigos.setdefault(str(sha), {"desde": c[2], "hasta": c[2], "n": 0})
            t["desde"], t["hasta"], t["n"] = min(t["desde"], c[2]), max(t["hasta"], c[2]), t["n"] + 1
    return {"igual": not mezcla, "n_mezcla": len(mezcla), "ejemplos": [list(x) for x in mezcla[:5]], "codigos": codigos}


def _sha256(ruta):
    import hashlib
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------------ re-sello S202
# Decisión de Nicolás del 2026-11-26 («Sí, re-séllalo así»), antes de calcular ninguna tasa del barrido: arreglo (a) de
# R5C-101 (cierre de la ronda 5 de la auditoría externa con Codex; verificador Claude de contexto limpio,
# D:/codex-vrp/_salida/ronda5/cierre_verificacion/VEREDICTO.md). Pruebas: tests/test_lab_piso_resello_s202.py.
# POR QUÉ. De noche, con el piso bajo, un foco débil pegado a un hueco de datos puede quedar alertado sin vecinos para
# estimar su fondo: la vía guarda la escena MODIS como no medida (`motivo_vacio = fondo_no_estimado`) sólo en ese
# brazo. Y al revés en VIIRS 375 (R5C-V201): una escena que el control no midió (`crater_no_evaluado`) se vuelve
# válida y publica con el piso bajo. Como cada brazo sacaba sus inválidas por separado, los brazos se comparaban
# sobre muestras distintas y ningún control lo veía. Arreglo: la muestra es común; toda escena inválida en alguno de
# los nueve brazos sale de los nueve y de producción (si sale sólo de los brazos, `control_tasas` da INVÁLIDO por
# construcción: R5C-V203), y la salida la declara. Dos frenos sellados acotan lo que la exclusión puede mover.
TOPE_EXCLUIDAS = 0.01          # freno 2: las excluidas no pueden pasar del 1 % de las noches negativas del control


def supera_tope(n_excluidas, n_noches_neg):
    """Freno 2, en enteros: n_excluidas > 1 % de n_noches_neg  <=>  100 n_excluidas > n_noches_neg."""
    return round(1 / TOPE_EXCLUIDAS) * n_excluidas > n_noches_neg


def _clave_canonica(vol, sensor, t):
    """(volcán, sensor, hora) con la hora en el formato del almacén: la misma clave sale del record crudo y de la pasada
    que carga el banco (que la reescribe desde un datetime)."""
    try:
        t = datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        pass
    return (vol, sensor, t)


def escenas_validez_distinta(recs_por_brazo):
    """{clave: {brazo: motivo_vacio o None}} de las escenas inválidas en algún brazo y válidas en otro (la misma regla
    de inválida que el banco: `banco_paridad.es_escena_invalida`, motivo_vacio no vacío). Las inválidas en todos los
    brazos ya salen de todos por la regla de siempre: no se cuentan como exclusión nueva."""
    por = {}
    for k, recs in recs_por_brazo.items():
        for r in recs:
            m = (r.get("diag_codigo_mirova") or {}).get("motivo_vacio") or None
            por.setdefault(_clave_canonica(r["_vol"], r.get("sensor"), r.get("datetime_utc")), {})[k] = m
    return {c: d for c, d in por.items() if any(v is not None for v in d.values()) and any(v is None for v in d.values())}


def _contable(clave, fin, coords):
    """La escena entra a las cuentas de E.tasas_barrido: volcán de la zona A, sensor con cubo, dentro de la ventana y
    no descartada de día por el banco."""
    import banco_paridad as bp
    vol, sensor, t = clave
    b = bp.bucket(sensor)
    if vol not in E.VOLCANES_ZONA_A or b is None or not _en_ventana({"datetime_utc": t}, fin):
        return False
    try:
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    return not bp.es_pasada_diurna_descartada(b, *coords[vol], dt)


def excluir_de_carpeta(origen, destino, claves):
    """Copia los JSON de `origen` a `destino` sin los records cuya clave está en `claves`. Devuelve {volcán: quitados}."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    quitados = {}
    for ruta in sorted(Path(origen).glob("*.json")):
        vol = ruta.stem
        d = json.loads(ruta.read_text(encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) else d
        quedan = [r for r in recs if _clave_canonica(vol, r.get("sensor"), r.get("datetime_utc")) not in claves]
        quitados[vol] = len(recs) - len(quedan)
        salida = dict(d, records=quedan) if isinstance(d, dict) else {"records": quedan}
        (destino / ruta.name).write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    return quitados


def noches_por_brazo(brazos, fin, dest):
    """{brazo: {(volcán, noche): [(clave, etiqueta, publica)]}}: las pasadas que cuenta E.tasas_barrido (mismo cargador
    con las inválidas del brazo fuera, mismo etiquetador, misma referencia ya bajada a `dest`), agrupadas por noche de
    volcán. Es una réplica del conteo por noche para ver qué noches toca la exclusión; `calibrar` exige que, quitadas
    las excluidas, dé exactamente las cuentas NOCHE de E.tasas_barrido (si no, INVÁLIDO)."""
    import banco_paridad as bp
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    ventana = (E.VENTANA_CALIBRACION_INICIO, fin)
    filas = bp.cargar_referencia_unificada(Path(dest) / CSV_REFERENCIA[0], Path(dest) / CSV_REFERENCIA[1])
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    out = {}
    for k, d in brazos.items():
        recs = [r for r in bp.cargar_nuestros(coords, inner, ventana, data=d, excluir_escenas_invalidas=True)
                if r["vol"] in E.VOLCANES_ZONA_A]
        bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        noches = {}
        for r in recs:
            c = _clave_canonica(r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
            noches.setdefault((r["vol"], r["noche"]), []).append((c, r["lab"], bool(r["pub"])))
        out[k] = noches
    return out


def _estado_noche(pasadas):
    """(entra al denominador, publica) con la regla de E.tasas_barrido: alguna `neg_limpio` y ninguna `pos` ni
    `far_ref`; publica si alguna pasada de la noche publica."""
    labs = [l for _, l, _ in pasadas]
    neg = "neg_limpio" in labs and not any(l in ("pos", "far_ref") for l in labs)
    return neg, any(p for _, _, p in pasadas)


def frenos_exclusion(noches, excluidas):
    """Freno 1 y lo que la exclusión mueve. Para cada brazo y cada noche con una escena excluida: «decide su noche» si
    quitarla cambia si la noche entra al denominador (era la única negativa limpia, o la única pasada con alerta o
    falso positivo de MIROVA). Si la noche sigue en el denominador y deja de publicar, es una publicación quitada:
    lo que la muestra común quiere (una publicación sobre una escena que otro brazo no pudo medir), y se declara.
    Devuelve (decisivas, publicaciones_quitadas, cuentas NOCHE de la réplica sin las excluidas)."""
    decisivas, quitadas, cuentas = [], {}, {}
    for k, por_noche in noches.items():
        n_pub = n_neg = 0
        for (vol, noche), pasadas in por_noche.items():
            sin = [p for p in pasadas if p[0] not in excluidas]
            neg_sin, pub_sin = _estado_noche(sin)
            if neg_sin:
                n_neg += 1
                n_pub += pub_sin
            if len(sin) == len(pasadas):
                continue
            neg_con, pub_con = _estado_noche(pasadas)
            if neg_con != neg_sin:
                decisivas.append({"brazo": str(k), "volcan": vol, "noche": noche,
                                  "efecto": "sale del denominador" if neg_con else "entra al denominador",
                                  "excluidas": [list(p[0]) for p in pasadas if p[0] in excluidas]})
            elif neg_sin and pub_con and not pub_sin:
                quitadas[str(k)] = quitadas.get(str(k), 0) + 1
        cuentas[k] = (n_pub, n_neg)
    return decisivas, quitadas, cuentas


def calibrar(sin_zona, control, brazos, prod, fin, dest):
    """Corre la calibración completa. `brazos`: {piso: carpeta}. Orden de los controles: primero los que invalidan
    (cobertura, código, identidad, fuga fuera de la zona, cuentas de producción), después el de poder. Antes de todo,
    el fin tiene que ser el sellado (R4FD-107): con otro fin no se carga ni se cuenta nada."""
    if fin != FIN_SELLADO:
        return {"estado": INVALIDO, "valor": None,
                "detalle": "el fin pedido (%s) no es el fin sellado de la ventana (%s): R4FD-107, acta de cierre de la "
                           "ronda 4" % (fin, FIN_SELLADO)}
    base = cargar_records(sin_zona)
    recs = {"sin_zona": base, CONTROL: cargar_records(control)}
    recs.update({str(p): cargar_records(d) for p, d in brazos.items()})
    # R4FD-107, segunda parte: la muestra queda identificada por el sha256 de cada archivo leído de cada brazo.
    carpetas = {"sin_zona": sin_zona, CONTROL: control, **{str(p): d for p, d in brazos.items()}}
    muestra = {k: {f.name: _sha256(f) for f in sorted(Path(d).glob("*.json"))} for k, d in carpetas.items()}
    cob = cobertura_brazos(recs, fin)
    cod = codigo_brazos(recs, fin)
    ident = {CONTROL: identidad_records(recs[CONTROL], base)}
    if S_A == S_CONTROL and GRILLA_PISO[0] in brazos:
        ident[str(GRILLA_PISO[0])] = identidad_records(recs[str(GRILLA_PISO[0])], base)
    fuera = {str(p): identidad_records(_sin_actuar(recs[str(p)]), _sin_actuar(base), permitir_vacio=True)
             for p in brazos}
    fuera_en_ventana = {str(p): sum(1 for r in _sin_actuar(recs[str(p)]) if _en_ventana(r, fin)) for p in brazos}
    # R4FD-V201 y R4FD-106: producción contada con las reglas de día del laboratorio, y una sola bajada de la
    # referencia de MIROVA para todos los brazos y producción, con el sha256 de lo que se bajó.
    prod_lab, quitados = prod_como_laboratorio(prod, Path(dest) / "produccion_como_laboratorio")
    # Re-sello S202 (R5C-101): la muestra común. Las escenas de validez distinta entre los nueve brazos salen de los
    # brazos contados y de producción antes de contar; las cuentas las hace E.tasas_barrido sobre esas copias.
    excluidas = escenas_validez_distinta(recs)
    originales = {CONTROL: control, **brazos, "prod": prod_lab}
    if excluidas:
        comun = Path(dest) / "muestra_comun"
        a_contar = {k: str(comun / str(k).replace(".", "_")) for k in originales}
        records_quitados = {str(k): excluir_de_carpeta(originales[k], a_contar[k], excluidas) for k in originales}
    else:
        a_contar, records_quitados = dict(originales), {}
    todas = E.tasas_barrido(a_contar, fin, dest)
    tasas_prod = todas.pop("prod")
    tasas = todas
    referencia = {n: _sha256(Path(dest) / n) for n in CSV_REFERENCIA if (Path(dest) / n).exists()}
    import banco_paridad as bp
    coords = bp._coords_por_volcan()
    contables = sorted((c for c in excluidas if _contable(c, fin, coords)), key=lambda x: tuple(map(str, x)))
    decisivas, pub_quitadas, replica_igual = [], {}, True
    if contables:
        decisivas, pub_quitadas, cuentas = frenos_exclusion(noches_por_brazo(originales, fin, dest), set(excluidas))
        oficiales = dict(tasas, prod=tasas_prod)
        replica_igual = all(cuentas.get(k) == tuple(oficiales[k]["NOCHE"]) for k in originales)
    n_neg_control = (tasas.get(CONTROL) or {}).get("NOCHE", (0, 0))[1]
    # Freno 3 (decisión de Nicolás del 2026-11-26, «Agregar freno 3», tras el verificador del re-sello, R202V-1). POR
    # QUÉ: con los frenos 1 y 2 en verde, lo único que la exclusión mueve son publicaciones quitadas (noches que siguen
    # en el denominador y dejan de publicar), así que sólo puede bajar la tasa de un brazo y, con ella, el piso elegido:
    # un sesgo hacia bajar el umbral, el riesgo que el laboratorio tiene que evitar. Se elige también con esas
    # publicaciones devueltas a cada brazo; si la elección cambia, la exclusión decidió el piso e INVÁLIDO.
    devueltas = {k: dict(v, NOCHE=(v["NOCHE"][0] + pub_quitadas.get(str(k), 0), v["NOCHE"][1]))
                 for k, v in tasas.items() if "NOCHE" in v}
    eleccion_devueltas = elegir_piso(devueltas)
    exclusion = {"n": len(contables), "n_total": len(excluidas), "tope": TOPE_EXCLUIDAS,
                 "eleccion_con_publicaciones_devueltas": {k: eleccion_devueltas[k] for k in ("estado", "valor")},
                 "noches_negativas_control": n_neg_control, "decisivas": decisivas,
                 "publicaciones_quitadas": pub_quitadas, "replica_por_noche_igual": replica_igual,
                 "records_quitados": records_quitados,
                 "escenas": [{"clave": list(c), "contable": c in contables,
                              "motivos": {str(k): v for k, v in excluidas[c].items()}}
                             for c in sorted(excluidas, key=lambda x: tuple(map(str, x)))]}
    res = elegir_piso(tasas)
    if not cob["igual"]:
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "los brazos no cubren las mismas pasadas en la ventana: %s"
                          % {k: (v["faltan"], v["sobran"]) for k, v in cob["diferencias"].items()}}
    elif not cod["igual"]:
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "%d pasadas con brazos que no corrieron el mismo código (regimen.codigo_sha)" % cod["n_mezcla"]}
    elif not all(v["identico"] for v in ident.values()):
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "el brazo de producción no es idéntico, record a record, al brazo sin zona"}
    elif not all(v["identico"] for v in fuera.values()):
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "un brazo de piso cambia records donde la zona A no actúa (de día, fuera de la vía o en "
                          "Cordón Caulle): la palanca se filtra fuera de la zona"}
    elif not control_tasas(tasas, tasas_prod):
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "el brazo de producción no reproduce las cuentas de producción: %s contra %s"
                          % (tasas.get(CONTROL), tasas_prod)}
    elif not replica_igual:
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "la réplica por noche de los frenos de la exclusión no da las cuentas NOCHE de "
                          "E.tasas_barrido: los frenos no miran lo que se cuenta (re-sello S202)"}
    elif decisivas:
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "%d noches en que una escena excluida por validez distinta entre brazos decide su noche "
                          "(era su única negativa limpia o su única alerta o falso positivo de MIROVA): freno 1 del "
                          "re-sello S202 (R5C-101)" % len(decisivas)}
    elif supera_tope(len(contables), n_neg_control):
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "%d escenas excluidas por validez distinta entre brazos pasan del 1 %% de las %d noches "
                          "negativas del control: freno 2 del re-sello S202 (R5C-101)" % (len(contables), n_neg_control)}
    elif (eleccion_devueltas["estado"], eleccion_devueltas["valor"]) != (res["estado"], res["valor"]):
        res = {"estado": INVALIDO, "valor": None,
               "detalle": "las publicaciones quitadas por la exclusión cambian la elección (%s %s con ellas devueltas, "
                          "%s %s sin ellas): la exclusión decidiría el piso; freno 3 del re-sello S202 (R202V-1)"
                          % (eleccion_devueltas["estado"], eleccion_devueltas["valor"], res["estado"], res["valor"])}
    # Re-sello S200b (verificador de #1129): el poder cuenta sólo los records de la ventana de calibración donde la zona
    # no actúa (la identidad sigue mirando todos), y SIN PODER no tapa un INVALIDO que ya dio elegir_piso (por ejemplo,
    # tasa no monótona: un instrumento roto se informa como roto).
    elif res["estado"] != INVALIDO and any(v < N_MIN_FUERA for v in fuera_en_ventana.values()):
        res = {"estado": SIN_PODER, "valor": None,
               "detalle": "la identidad donde la zona no actúa compara menos de %d records de la ventana en algún "
                          "brazo: %s" % (N_MIN_FUERA, {k: v for k, v in fuera_en_ventana.items() if v < N_MIN_FUERA})}
    res.update({"identidad": ident, "identidad_donde_no_actua": fuera,
                "donde_no_actua_en_ventana": fuera_en_ventana, "tasas_produccion": tasas_prod,
                "tasas": {str(k): v for k, v in tasas.items()}, "s_a": S_A, "grilla_piso": list(GRILLA_PISO),
                "cobertura_brazos": cob, "codigo_brazos": cod, "referencia_mirova": referencia,
                "produccion_como_laboratorio": {"carpeta": prod_lab, "quitados": quitados}, "fin": fin,
                "muestra": muestra, "exclusion_comun": exclusion})
    return res


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("evaluar", "poder"):
        return E.main(argv)       # la vara del S194, sin cambios
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrar")
    c.add_argument("--sin-zona", required=True, help="brazo con la zona A apagada, de la misma corrida")
    c.add_argument("--control", required=True, help="brazo con la zona encendida, s = 5 y piso 0,003")
    c.add_argument("--brazo", action="append", required=True, help="piso=carpeta de records del brazo (s = S_A)")
    c.add_argument("--prod", default=str(ROOT / "data" / "mirova_equivalent"))
    c.add_argument("--fin", default=FIN_SELLADO, help="fin de la ventana; sólo vale el sellado (R4FD-107)")
    c.add_argument("--dest", required=True, help="carpeta temporal para la referencia de MIROVA")
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    brazos = {float(x.split("=", 1)[0]): x.split("=", 1)[1] for x in a.brazo}
    res = calibrar(a.sin_zona, a.control, brazos, a.prod, a.fin, a.dest)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("estado", "valor", "detalle")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
