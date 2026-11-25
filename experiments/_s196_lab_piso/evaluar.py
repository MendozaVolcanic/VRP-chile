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
PERFIL_LAB = ROOT / "pipeline" / "profiles" / "laboratorio.yaml"
CSV_REFERENCIA = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv")


def _dia_modis_lab():
    """El laboratorio guarda MODIS de día sólo si su perfil lo declara (hoy no: `paths.enable_daytime_modis: false`)."""
    import yaml
    p = yaml.safe_load(PERFIL_LAB.read_text(encoding="utf-8")) or {}
    return bool((p.get("paths") or {}).get("enable_daytime_modis", False))


def rechaza_como_laboratorio(r, vol, dia_modis_lab=None):
    """R4FD-V201. POR QUÉ: desde el 2026-11-15 12:30 UTC producción guarda las pasadas MODIS de día y el almacén del
    laboratorio las rechaza (pipeline/store.py::_reject_daytime con su perfil), así que el control «el brazo de
    producción da las cuentas de producción» salía INVÁLIDO por construcción con cualquier ventana que llegue hasta
    hoy. Se aplica a producción la MISMA regla del almacén (misma función, mismas coordenadas de volcanoes.yaml) con los
    flags del laboratorio. VIIRS no se filtra aquí: su día lo decide el mismo flag vivo en los dos perfiles
    (pipeline/diurno.py), así que no puede separar al laboratorio de producción. Un record sin hora legible el almacén
    lo guarda, y aquí se conserva."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from pipeline.store import _reject_daytime, _solar_elevation
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    try:
        dt = datetime.strptime(r.get("datetime_utc", ""), "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return False
    lat, lon = bp._coords_por_volcan()[vol]
    dia = _dia_modis_lab() if dia_modis_lab is None else dia_modis_lab
    return _reject_daytime(r.get("sensor", ""), _solar_elevation(lat, lon, dt), dia, enable_daytime_viirs=True)


def prod_como_laboratorio(prod, destino):
    """Copia de los JSON de producción (los volcanes del banco) sin los records que el almacén del laboratorio habría
    rechazado. Devuelve (carpeta, {volcán: records quitados})."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    dia = _dia_modis_lab()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    quitados = {}
    for vol in bp.VOLS:
        ruta = Path(prod) / ("%s.json" % vol)
        if not ruta.exists():
            continue
        d = json.loads(ruta.read_text(encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) else d
        quedan = [r for r in recs if not rechaza_como_laboratorio(r, vol, dia)]
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


def calibrar(sin_zona, control, brazos, prod, fin, dest):
    """Corre la calibración completa. `brazos`: {piso: carpeta}. Orden de los controles: primero los que invalidan
    (cobertura, código, identidad, fuga fuera de la zona, cuentas de producción), después el de poder."""
    base = cargar_records(sin_zona)
    recs = {"sin_zona": base, CONTROL: cargar_records(control)}
    recs.update({str(p): cargar_records(d) for p, d in brazos.items()})
    cob = cobertura_brazos(recs, fin)
    cod = codigo_brazos(recs, fin)
    ident = {CONTROL: identidad_records(recs[CONTROL], base)}
    if S_A == S_CONTROL and GRILLA_PISO[0] in brazos:
        ident[str(GRILLA_PISO[0])] = identidad_records(recs[str(GRILLA_PISO[0])], base)
    fuera = {str(p): identidad_records(_sin_actuar(recs[str(p)]), _sin_actuar(base), permitir_vacio=True)
             for p in brazos}
    # R4FD-V201 y R4FD-106: producción contada con las reglas de día del laboratorio, y una sola bajada de la
    # referencia de MIROVA para todos los brazos y producción, con el sha256 de lo que se bajó.
    prod_lab, quitados = prod_como_laboratorio(prod, Path(dest) / "produccion_como_laboratorio")
    todas = E.tasas_barrido({CONTROL: control, **brazos, "prod": prod_lab}, fin, dest)
    tasas_prod = todas.pop("prod")
    tasas = todas
    referencia = {n: _sha256(Path(dest) / n) for n in CSV_REFERENCIA if (Path(dest) / n).exists()}
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
    elif any(v["n"] < N_MIN_FUERA for v in fuera.values()):
        res = {"estado": SIN_PODER, "valor": None,
               "detalle": "la identidad donde la zona no actúa compara menos de %d records en algún brazo: %s"
                          % (N_MIN_FUERA, {k: v["n"] for k, v in fuera.items() if v["n"] < N_MIN_FUERA})}
    res.update({"identidad": ident, "identidad_donde_no_actua": fuera, "tasas_produccion": tasas_prod,
                "tasas": {str(k): v for k, v in tasas.items()}, "s_a": S_A, "grilla_piso": list(GRILLA_PISO),
                "cobertura_brazos": cob, "codigo_brazos": cod, "referencia_mirova": referencia,
                "produccion_como_laboratorio": {"carpeta": prod_lab, "quitados": quitados}})
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
    c.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
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
