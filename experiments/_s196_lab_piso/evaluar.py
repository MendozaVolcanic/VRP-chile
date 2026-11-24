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


def calibrar(sin_zona, control, brazos, prod, fin, dest):
    """Corre la calibración completa. `brazos`: {piso: carpeta}."""
    base = cargar_records(sin_zona)
    ident = {CONTROL: identidad_records(cargar_records(control), base)}
    if S_A == S_CONTROL and GRILLA_PISO[0] in brazos:
        ident[str(GRILLA_PISO[0])] = identidad_records(cargar_records(brazos[GRILLA_PISO[0]]), base)
    fuera = {str(p): identidad_records(_sin_actuar(cargar_records(d)), _sin_actuar(base), permitir_vacio=True)
             for p, d in brazos.items()}
    tasas = E.tasas_barrido({CONTROL: control, **brazos}, fin, dest)
    tasas_prod = E.tasas_barrido({"prod": prod}, fin, dest)["prod"]
    res = elegir_piso(tasas)
    if not all(v["identico"] for v in ident.values()):
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
    res.update({"identidad": ident, "identidad_donde_no_actua": fuera, "tasas_produccion": tasas_prod, "tasas": {str(k): v for k, v in tasas.items()},
                "s_a": S_A, "grilla_piso": list(GRILLA_PISO)})
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
