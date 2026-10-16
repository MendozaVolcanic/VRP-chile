# -*- coding: utf-8 -*-
"""Une los records de dos o más intentos del MISMO brazo y el mismo código (vuelta 68 del loop, 2026-10-16;
tolerancia numérica y píxel de borde en la vuelta siguiente, rama loop/unir-intentos-tolerancia).

Por qué se une: en W1 cada intento del brazo diurno perdió pasadas nocturnas distintas por caídas sueltas de
descarga, y repetir otra vez puede perder otra (decisión D-13 de Nicolás: los A/B largos se repiten y se unen
los intentos). Antes de unir hay que comprobar que en los gránulos comunes los dos intentos dicen LO MISMO: si
lo dicen, la unión es una corrida completa con el mismo código. Si no, no se une y se informa. En W1: 325
comunes, 0 distintos; la unión cubre las 183 noches del control.

Por qué no basta `!=` (medido en el A/B F/K V2a, run 38648773684, intento 1 y re-run sobre el MISMO commit):
en 8 de 22 archivos difieren TODOS los records comunes, y no por el código.
  1. Ruido de máquina. `diag_mu_deti` difiere hasta 5,1e-10 relativo (1,3e-15 absoluto) y `diag_sd_deti`
     hasta 4,0e-12 relativo: es la regresión del ETI (`np.polyfit`), que pasa por LAPACK de OpenBLAS y cambia
     los últimos bits según la CPU del runner. Mismo mecanismo que el G3 del evaluador diurno (#833), y la
     tolerancia es la suya: `REL_TOL, ABS_TOL = 1e-9, 1e-14`, comparada con math.isclose. El piso absoluto
     cubre los valores casi cero (mu del dETI) y está 11 órdenes bajo el umbral físico más fino del dETI
     (C1 = 3e-3); una diferencia de 1e-3 relativo sobre un valor de orden 1e-2 no pasa. Los enteros, bools,
     None y strings se comparan exactos. El test fija los dos lados (5e-10 une, 1e-3 no).
  2. Píxel de borde. En 11.642 records comunes, 24 traen `anomaly_pixels` distinto: 9 sólo en el orden y 15
     con otro conjunto (0 a 2 píxeles). Los 15 son MODIS del control, `distance_class = far`, `vrp_mw` topado
     en 5,0 (tope D9) y campos difusos de 56 a 90 píxeles: un píxel en el borde del umbral entra o sale con el
     ruido de la regresión. Ese píxel arrastra campos que se calculan desde el conjunto de píxeles (la lista
     y el conteo de descartados, el píxel más caliente y la geometría de visión evaluada en él, `vrp_mir_mw`).

Regla de comparación de un record común (`comparar`):
  * igual / tolerancia / orden: idéntico, idéntico salvo floats dentro de la tolerancia, o idéntico salvo el
    orden de las listas de píxeles (se comparan como multiconjunto, con la misma tolerancia). Une.
  * borde: alguna lista de píxeles difiere como conjunto. Une SÓLO si (a) todo campo de CAMPOS_DECISION es
    igual dentro de la tolerancia; (b) todo otro campo distinto está en DERIVADOS_DEL_BORDE (lista cerrada);
    (c) el tablero no lee los píxeles para ese record (VIIRS 375 sin `f5_core_vrp_mw` sí los lee); y (d) el
    predicado del tablero ejecutado con node (A97, `scripts/banco_paridad.py::correr_node`, con el mismo
    record recortado que le pasan los evaluadores) da lo mismo con los dos records. Cada unión de este tipo
    se informa record por record, por stdout y en la clave `_union_intentos` del JSON de salida.
  * distinto: cualquier otra diferencia. Bloquea la unión, como en la vuelta 68.

CAMPOS_DECISION sale de leer los consumidores, no de adivinar (A89):
  * `scripts/banco_paridad.py:136` CAMPOS_JS, lo que se le pasa al predicado del tablero: primary_cluster
    (entero, incluye n_pixels del filtro de campo difuso y centroid_* del corte por inner), distance_class,
    vrp_mw, discarded_reason, triggered_test1, vrp_vent_mw, t_max_k, sensor, f5_core_vrp_mw. Dos van con
    condición, porque el predicado sólo los lee en un caso: anomaly_pixels cuando f5_core_vrp_mw es None
    (banco_paridad.py:284) y el sensor es VIIRS 375 (frontend/index.html:1238 y 1289); vrp_mir_mw cuando el
    record no tiene primary_cluster ni vrp_mw (`r.vrp_mw ?? r.vrp_mir_mw`, frontend/index.html:1148-1149).
    Fuera de esos casos son derivados del píxel de borde (vrp_mir_mw es la suma MIR de los píxeles).
  * `scripts/banco_paridad.py:282` sensor_zenith_deg («z»), con el que la l. 467 arma la zona del barrido;
    `experiments/_s149_prereg_invierno/armar_tabla.py:45` lo entrega y `medir_predicciones.py:31` lo usa igual.
  * `experiments/_s146_ab_sin_test1/evaluar.py:92-96` final_hotspot_source, n_anomalous_pixels (decide en las
    l. 372 y 378) y granule; ese cargador es el de `armar_tabla.py`, que es el de `evaluar_fk.py`.
  * `experiments/_s151_prereg_fk_11/evaluar_fk.py:145` product_version y triggered_test1.
  * `experiments/_s151_ab_diurno/evaluar_diurno.py:261` diag_umbrales_diurnos; l. 417 product_version y granule.
  * datetime_utc y sensor van además en la clave.
Ojo con el G3 de `evaluar_diurno.py:420`: compara TODOS los campos entre los dos brazos, así que un record de
borde puede aparecer ahí como diferencia de campos derivados. No es de la unión (los brazos son jobs distintos
y ya corren en CPUs distintas), pero la lista de `_union_intentos` permite rastrearlo.

Resultado sobre V2a (22 archivos, 11.642 comunes): unen 20 (con la vuelta 68, 14). Se admiten 8 records por
píxel de borde, todos de Copahue control. No unen Isluga y Nevados de Chillán control, por un record cada uno
(MODIS_TERRA 2026-03-28 01:15 y MODIS_AQUA 2026-04-17 07:30): el píxel de borde cambia el píxel más caliente
(hasta 6,8 km) y con él `sensor_zenith_deg` (hasta 0,7°), que decide la zona del barrido. En esos dos archivos
quedan además 2 y 4 records de borde que sí cumplirían la regla.

Para los records comunes la unión conserva el del PRIMER intento en el orden de la línea de comandos
(determinista); los que sólo están en un intento posterior se agregan. Los metadatos del documento salen del
primer intento.

Uso: python unir_intentos.py --out <json> [--volcan V] <intento1.json> <intento2.json> [...]
Sale con 1 si no une; con 0 si une.
"""
import argparse
import json
import math
import sys
from pathlib import Path

PROCESO = {"processed_utc", "first_processed_utc", "regimen", "updated"}
REL_TOL, ABS_TOL = 1e-9, 1e-14          # = G3_REL_TOL, G3_ABS_TOL de evaluar_diurno.py (el test lo vigila)
LISTAS_PIXELES = ("anomaly_pixels", "discarded_anomaly_pixels")
CAMPOS_DECISION = {
    "primary_cluster": "banco_paridad.py:136 (predicado)", "distance_class": "banco_paridad.py:136",
    "vrp_mw": "banco_paridad.py:136",
    "discarded_reason": "banco_paridad.py:136", "triggered_test1": "banco_paridad.py:136, evaluar_fk.py:145",
    "vrp_vent_mw": "banco_paridad.py:136", "t_max_k": "banco_paridad.py:136", "sensor": "banco_paridad.py:136",
    "f5_core_vrp_mw": "banco_paridad.py:136", "sensor_zenith_deg": "banco_paridad.py:282 y 467 (zona)",
    "final_hotspot_source": "_s146_ab_sin_test1/evaluar.py:92", "n_anomalous_pixels": "evaluar.py:95",
    "granule": "evaluar.py:96, evaluar_diurno.py:417", "product_version": "evaluar_fk.py:145",
    "diag_umbrales_diurnos": "evaluar_diurno.py:261", "datetime_utc": "clave",
}
# Lo que se calcula desde el conjunto de píxeles y ningún consumidor lee (grep de los cinco consumidores de
# arriba: 0 usos). Lista CERRADA: un campo nuevo que difiera en un record de borde bloquea hasta que se agregue
# aquí con su razón.
DERIVADOS_DEL_BORDE = {
    "anomaly_pixels": "la lista misma", "discarded_anomaly_pixels": "la lista de descartados",
    "discarded_n_pixels": "conteo de descartados",
    "hotspot_lat": "píxel más caliente", "hotspot_lon": "píxel más caliente", "hotspot_dist_km": "píxel más caliente",
    "final_hotspot_lat": "píxel más caliente", "final_hotspot_lon": "píxel más caliente",
    "final_hotspot_dist_km": "píxel más caliente",
    "sensor_azimuth_deg": "geometría en el hotspot", "solar_zenith_deg": "geometría en el hotspot",
    "solar_azimuth_deg": "geometría en el hotspot",
    # va en CAMPOS_JS, pero el predicado sólo lo lee como respaldo de `r.vrp_mw ?? r.vrp_mir_mw` cuando el
    # record NO tiene primary_cluster (frontend/index.html:1148-1149); en ese caso decide y bloquea (comparar)
    "vrp_mir_mw": "suma de VRP MIR de los píxeles",
}
_VIIRS375 = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")


def clave(r):
    return (r.get("sensor"), r.get("datetime_utc"), r.get("granule"))


def iguales(a, b):
    """Igualdad con tolerancia: floats con math.isclose(REL_TOL, ABS_TOL), resto exacto; recursiva en listas y
    dicts (posicional en listas; las listas de píxeles se comparan aparte como multiconjunto)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return True
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(iguales(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(iguales(x, y) for x, y in zip(a, b))
    return a == b


def mismo_multiconjunto(a, b):
    """True si las dos listas tienen los mismos elementos (dentro de la tolerancia) en cualquier orden."""
    a, b = list(a or []), list(b or [])
    if len(a) != len(b):
        return False
    libres = list(range(len(b)))
    for x in a:
        for j, i in enumerate(libres):
            if iguales(x, b[i]):
                del libres[j]
                break
        else:
            return False
    return True


def comparar(a, b):
    """Estado de un record común: ('igual'|'tolerancia'|'orden'|'borde'|'distinto', detalle)."""
    x = {c: v for c, v in a.items() if c not in PROCESO}
    y = {c: v for c, v in b.items() if c not in PROCESO}
    if x == y:
        return "igual", {}
    campos = sorted(set(x) | set(y))
    # un campo presente en un intento y ausente en el otro es diferencia, aunque valga None o []
    no_tol = [c for c in campos if (c in x) != (c in y) or
              (c not in LISTAS_PIXELES and not iguales(x.get(c), y.get(c)))]
    orden = [c for c in LISTAS_PIXELES if c in x and c in y and not iguales(x[c], y[c])]
    conjunto = [c for c in orden if not mismo_multiconjunto(x.get(c), y.get(c))]
    if not no_tol and not conjunto:
        return ("orden" if orden else "tolerancia"), {"listas_reordenadas": orden}
    if not conjunto:
        return "distinto", {"campos": no_tol}
    # borde: decide la lista de decisión, la lista cerrada de derivados y si el tablero lee los píxeles
    bloquean = [c for c in no_tol if c in CAMPOS_DECISION or c not in DERIVADOS_DEL_BORDE]
    if a.get("sensor") in _VIIRS375 and a.get("f5_core_vrp_mw") is None and "anomaly_pixels" in conjunto:
        bloquean.append("anomaly_pixels")
    if "vrp_mir_mw" in no_tol and not (a.get("primary_cluster") and a.get("vrp_mw") is not None):
        bloquean.append("vrp_mir_mw")
    det = {"pixeles": {c: [len(x.get(c) or []), len(y.get(c) or [])] for c in conjunto},
           "campos_derivados": [c for c in no_tol if c not in bloquean]}
    if bloquean:
        det["campos"] = sorted(set(bloquean))
        return "distinto", det
    return "borde", det


def _predicado(pares, volcan):
    """Predicado del tablero (frontend/index.html con node) sobre (record1, record2), con el mismo recorte que
    le hacen los evaluadores (banco_paridad.py:283-286). Devuelve la lista de índices donde difiere."""
    raiz = Path(__file__).resolve().parents[2]
    for p in (str(raiz), str(raiz / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import banco_paridad as bp
    inner = bp.inner_desde_html()[volcan]

    def slim(r):
        s = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            s["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                   for q in (r.get("anomaly_pixels") or [])]
        return s
    casos = [[slim(r), inner] for par in pares for r in par]
    out = bp.correr_node(casos)
    return [i for i in range(len(pares)) if out[2 * i] != out[2 * i + 1]]


def unir(docs, volcan):
    """(salida o None, informe). Conserva el record del primer intento en los comunes."""
    union, origen = {}, {}
    estados = {e: 0 for e in ("igual", "tolerancia", "orden", "borde", "distinto")}
    distintos, borde, nuevos = [], [], []
    for i, d in enumerate(docs):
        n = 0
        for r in d["records"]:
            k = clave(r)
            if k not in union:
                union[k], origen[k] = r, i
                n += 1
                continue
            est, det = comparar(union[k], r)
            estados[est] += 1
            if est == "distinto":
                distintos.append(dict(det, clave=list(k), intentos=[origen[k] + 1, i + 1]))
            elif est == "borde":
                borde.append(dict(det, clave=list(k), intentos=[origen[k] + 1, i + 1],
                                  distance_class=union[k].get("distance_class"), vrp_mw=union[k].get("vrp_mw"),
                                  _par=(union[k], r)))
        nuevos.append(n)
    if borde and not distintos:
        try:
            malos = _predicado([b["_par"] for b in borde], volcan)
        except Exception as e:  # sin node o sin el volcán en el tablero: no se puede probar, no se une
            malos = list(range(len(borde)))
            for b in borde:
                b["predicado"] = "no se pudo correr: %s" % e
        for j in malos:
            b = borde[j]
            b.setdefault("predicado", "el tablero da distinto con los dos records")
            b["campos"] = ["predicado del tablero"]
            distintos.append(b)
            estados["borde"] -= 1
            estados["distinto"] += 1
        borde = [b for j, b in enumerate(borde) if j not in malos]
    for b in borde + distintos:
        b.pop("_par", None)
    inf = {"ok": not distintos, "volcan": volcan, "por_intento": [len(d["records"]) for d in docs],
           "nuevos_por_intento": nuevos, "comunes": sum(estados.values()), "estados": estados,
           "borde": borde, "distintos": distintos, "union": len(union)}
    if distintos:
        return None, inf
    salida = {c: v for c, v in docs[0].items() if c != "records"}
    salida["records"] = sorted(union.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
    salida["_union_intentos"] = {"regla": "comunes: se conserva el record del primer intento",
                                 "tolerancia": [REL_TOL, ABS_TOL], "por_intento": inf["por_intento"],
                                 "estados": estados, "borde": borde}
    return salida, inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--volcan", help="nombre del volcán para el inner del tablero (por defecto, el del JSON)")
    ap.add_argument("intentos", nargs="+")
    a = ap.parse_args()
    docs = [json.load(open(p, encoding="utf-8")) for p in a.intentos]
    volcan = a.volcan or docs[0].get("volcano") or Path(a.intentos[0]).stem
    salida, inf = unir(docs, volcan)
    for b in inf["borde"]:
        print("  borde admitido %s intentos %s: pixeles %s, %s %s MW, derivados distintos %s"
              % ("|".join(map(str, b["clave"])), b["intentos"], b["pixeles"], b["distance_class"], b["vrp_mw"],
                 b["campos_derivados"]))
    if not inf["ok"]:
        print("NO SE UNE %s: %d gránulos comunes distintos, p. ej. %s"
              % (volcan, len(inf["distintos"]), json.dumps(inf["distintos"][:3], ensure_ascii=False)))
        sys.exit(1)
    json.dump(salida, open(a.out, "w", encoding="utf-8"))
    print("%s: intentos %s -> unión %d records; comunes %d %s; %d por píxel de borde"
          % (volcan, inf["por_intento"], inf["union"], inf["comunes"], inf["estados"], len(inf["borde"])))


if __name__ == "__main__":
    main()
