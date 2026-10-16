# -*- coding: utf-8 -*-
"""Une los records de dos o más intentos del MISMO brazo y el mismo código (vuelta 68 del loop, 2026-10-16;
tolerancia numérica y píxel de borde en la vuelta siguiente, rama loop/unir-intentos-tolerancia).

Por qué se une: en W1 cada intento del brazo diurno perdió pasadas nocturnas distintas por caídas sueltas de
descarga, y repetir otra vez puede perder otra (decisión D-13 de Nicolás: los A/B largos se repiten y se unen
los intentos). Antes de unir hay que comprobar que en los gránulos comunes los dos intentos dicen LO MISMO: si
lo dicen, la unión es una corrida completa con el mismo código. Si no, no se une y se informa. En W1: 325
comunes, 0 distintos; la unión cubre las 183 noches del control.

Una sola regla en los dos modos (verificador del PR #841, vueltas 1 y 2): los comunes se clasifican SIEMPRE
con `comparar`, el predicado del tablero se corre sobre los de borde, y cualquier `distinto` que quede BLOQUEA.
Una diferencia de decisión entre dos corridas del mismo commit dice que los intentos no son del mismo código o
que el pipeline no es determinista en ese campo; en los dos casos el A/B pierde sentido, y `evaluar_fk.py` no
lee `_union_intentos`, así que informarla no basta. Sólo cuando no hay distintos cambia qué se entrega: si un
intento SOLO cubre todas las pasadas de la unión, ese intento ENTERO (el primero en el orden de la línea de
comandos, y sin pasadas repetidas), sin mezclar records de dos corridas en un archivo; si ninguno las cubre, la
mezcla record a record. Sobre V2a, 21 de 22 archivos tienen un intento completo.

Por qué no basta `!=` (medido en el A/B F/K V2a, run 38648773684, intento 1 y re-run sobre el MISMO commit):
en 8 de 22 archivos difieren TODOS los records comunes, y no por el código.
  1. Ruido de máquina. `diag_mu_deti` difiere hasta 5,1e-10 relativo (1,3e-15 absoluto) y `diag_sd_deti`
     hasta 4,0e-12 relativo: es la regresión del ETI (`np.polyfit`), que pasa por LAPACK de OpenBLAS y cambia
     los últimos bits según la CPU del runner. Mismo mecanismo que el G3 del evaluador diurno (#833), y la
     tolerancia es la suya: `REL_TOL, ABS_TOL = 1e-9, 1e-14`, comparada con math.isclose. El piso absoluto
     cubre los valores casi cero (mu del dETI) y está 11 órdenes bajo el umbral físico más fino del dETI
     (C1 = 3e-3); una diferencia de 1e-3 relativo sobre un valor de orden 1e-2 no pasa. Los enteros, bools,
     None y strings se comparan exactos. El test fija los dos lados (5e-10 une, 1e-3 no).
  2. Empates en el recorte de la lista de píxeles (lo que el código llama «borde»). En 11.642 records comunes,
     24 traen `anomaly_pixels` distinto: 9 sólo en el orden y 15 con otro conjunto, más 1 con sólo
     `discarded_anomaly_pixels` distinto. Ningún píxel cruza un umbral: la máscara de detección es la misma
     en los dos intentos (`n_anomalous_pixels`, de 273 a 789, y `primary_cluster` idénticos). Lo que cambia
     es cuáles entran a la lista guardada, que se recorta a los 100 de mayor VRP con
     `np.argsort(-per_pixel_vrp_mw)[:100]` (`pipeline/process_modis.py:1085`), un orden NO estable: en los 16
     casos la lista mide exactamente 100 y cada píxel que entra o sale tiene el mismo `vrp_mw` que el mínimo
     de la lista, valor que comparten de 1 a 45 píxeles (se intercambian hasta 8 por lado). Después
     `pipeline/store.py:285-301` reparte esa lista por distancia y recalcula `vrp_mir_mw` y `hotspot_*`, y de
     ahí salen los derivados distintos. Dos records (Isluga MODIS_TERRA 2026-03-28 01:15 y Chillán MODIS_AQUA
     2026-04-17 07:30) tienen además un empate en el MÁXIMO (dos píxeles de 3,3930 y de 2,6865 MW): el que el
     sort deja primero pasa a `final_hotspot`, y con él la geometría de visión evaluada ahí, incluido
     `sensor_zenith_deg`, que en MODIS es derivado (ver abajo). Todos son MODIS del control, `far`, topados en
     5,0 MW.
     SOSPECHA no verificada: que el orden de los empates cambie con la CPU por el despacho SIMD del sort de
     numpy, el mismo patrón que OpenBLAS en el ETI. (Medido por el verificador del PR #841, `a3_empates.py`.)

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
  * sensor_zenith_deg decide SÓLO en VIIRS 375 y por eso va en DERIVADOS_DEL_BORDE con condición (grep de
    `"z"`, `zbin` y `sensor_zenith` en la cadena, vuelta 2 del verificador): `scripts/banco_paridad.py:282` y
    `_s146_ab_sin_test1/evaluar.py:91` lo copian como «z»; su único lector en banco_paridad es
    `cenital_neg_v375` (l. 464-469), que filtra `r["b"] == "VIIRS375"`; `armar_tabla.py:45` lo entrega y
    `evaluar_fk.py` no lo lee (0 usos). Fuera de la cadena F/K, `_s149_prereg_invierno/medir_predicciones.py:12
    y 31` arma la zona del barrido para el sensor que recibe por argumento (VIIRS375 por defecto): si alguien
    lo corre con MODIS sobre una unión con un record de borde, ese record trae el cenit del intento entregado.
  * `experiments/_s146_ab_sin_test1/evaluar.py:92-96` final_hotspot_source, n_anomalous_pixels (decide en las
    l. 372 y 378) y granule; ese cargador es el de `armar_tabla.py`, que es el de `evaluar_fk.py`.
  * `experiments/_s151_prereg_fk_11/evaluar_fk.py:145` product_version y triggered_test1.
  * `experiments/_s151_ab_diurno/evaluar_diurno.py:261` diag_umbrales_diurnos; l. 417 product_version y granule.
  * datetime_utc y sensor van además en la clave.
La clave es la PASADA, (sensor, datetime_utc al minuto), igual que agrupan los evaluadores
(`_s146_ab_sin_test1/evaluar.py:109-110`, `evaluar_diurno.py:253`), no el gránulo. Con el gránulo en la clave
(vuelta 68), la misma pasada con otro gránulo o versión (NRT contra estándar, o un reproceso de NASA entre
intentos) salía dos veces y `armar_tabla.py:43` se quedaba en silencio con la última. Ahora se comparan, y
`granule` y `product_version` distintos son una diferencia que bloquea la mezcla.
Nota de diseño: CAMPOS_DECISION y DERIVADOS_DEL_BORDE son disjuntos (se comprueba al importar), así que en un
record de borde quien bloquea es la lista cerrada de derivados: todo campo distinto que no esté en ella
bloquea. CAMPOS_DECISION documenta de dónde sale cada campo; agregarle uno no cambia la regla.
Estándar incoherente PENDIENTE (otro PR): el G3 de `evaluar_diurno.py:386-401 y 420` compara las listas de
píxeles POSICIONALMENTE, así que marcaría como diferencia los 8 records de orden y los 14 de borde que esta
herramienta declara «mismo pipeline» (`verif_841/a4_g3.py`). No lo crea la unión: entre los dos brazos, que
son jobs distintos, el mismo empate del sort puede dar FALLA de G3. `evaluar_fk.py` no tiene G3 campo a campo.

Resultado sobre V2a: ver el informe del PR (se vuelve a correr en cada cambio, no se fija aquí).

En la mezcla, para los records comunes se conserva el del PRIMER intento en el orden de la línea de comandos
(determinista); los que sólo están en un intento posterior se agregan. Los metadatos del documento salen del
primer intento. Con un intento entero, todo (records y metadatos) sale de ese intento.

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
    "f5_core_vrp_mw": "banco_paridad.py:136",
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
    # geometría de visión en el píxel más caliente; decide sólo en VIIRS 375 (banco_paridad.py:464-469), ahí bloquea
    "sensor_zenith_deg": "geometría en el hotspot",
}
_VIIRS375 = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")
assert not set(CAMPOS_DECISION) & set(DERIVADOS_DEL_BORDE), "un campo no puede decidir y ser derivado a la vez"


def clave(r):
    """La pasada, como la agrupan los evaluadores: (sensor, minuto). Sin el gránulo (verificador del PR #841)."""
    return (r.get("sensor"), (r.get("datetime_utc") or "")[:16])


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
    if "sensor_zenith_deg" in no_tol and a.get("sensor") in _VIIRS375:
        bloquean.append("sensor_zenith_deg")
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
    """(salida o None, informe). Clasifica los comunes, corre el predicado sobre los de borde y bloquea ante
    cualquier distinto, en los dos modos. Sin distintos entrega el intento que cubre todas las pasadas, entero,
    o si no hay ninguno, la mezcla conservando el record del primer intento."""
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
    entero = None
    for i, d in enumerate(docs):
        ks = [clave(r) for r in d["records"]]
        if len(set(ks)) == len(ks) and set(ks) == set(union):
            entero = i
            break
    inf = {"ok": not distintos, "modo": "mezcla" if entero is None else "intento_entero",
           "intento_entero": None if entero is None else entero + 1, "volcan": volcan,
           "por_intento": [len(d["records"]) for d in docs], "nuevos_por_intento": nuevos,
           "comunes": sum(estados.values()), "estados": estados, "borde": borde, "distintos": distintos,
           "union": len(union)}
    if distintos:
        return None, inf
    if entero is not None:
        salida = dict(docs[entero])
        regla = "un intento cubre todas las pasadas: se usa entero, sin mezclar"
    else:
        salida = {c: v for c, v in docs[0].items() if c != "records"}
        salida["records"] = sorted(union.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
        regla = "mezcla: en los comunes se conserva el record del primer intento"
    salida["_union_intentos"] = {"regla": regla, "intento_entero": inf["intento_entero"],
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
    if inf["ok"] and inf["modo"] == "intento_entero":
        for b in inf["borde"]:
            print("  borde admitido %s intentos %s: pixeles %s, %s %s MW, derivados distintos %s"
                  % ("|".join(map(str, b["clave"])), b["intentos"], b["pixeles"], b["distance_class"],
                     b["vrp_mw"], b["campos_derivados"]))
        json.dump(salida, open(a.out, "w", encoding="utf-8"))
        print("%s: intentos %s -> usa ENTERO el intento %d (%d records, cubre las %d pasadas); comunes %d %s"
              % (volcan, inf["por_intento"], inf["intento_entero"], len(salida["records"]), inf["union"],
                 inf["comunes"], inf["estados"]))
        return
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
