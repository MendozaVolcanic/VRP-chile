#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vigilancia de la sombra de K (S156, arreglo 4 de docs/AUDIT_S155.md §5, hallazgo V1-04).

POR QUÉ (fenómeno → mecanismo): el detector K (adoptado el 2026-10-18, #850) dejó de usar el Test 1
integrado en el ROI, que era lo que veía la señal térmica débil en un volcán nevado: un foco incandescente
chico, sub-píxel, al empezar una fase efusiva. Con K la réplica publica mucho menos ruido, pero el costo
posible es justamente ese evento incipiente de baja energía. La regla de adopción
(experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4, paso 9) dejó una SOMBRA para vigilarlo: el
laboratorio `experimental`, congelado en el detector anterior (C0), corre a diario en data/experimental_v2/.
Si MIROVA publica una alerta, la sombra la publica y producción calla, K está perdiendo algo que C0 veía.
Hasta S156 la regla existía y el código no.

Lectura decidida por Nicolás el 2026-10-19 (marca al inicio del paso 9 de la regla): la unidad es la PASADA
y la vigilancia cuenta desde la ADOPCIÓN (CAMBIO_DETECTOR_UTC de frontend/cambio_detector.js). Lo anterior
(datos reprocesados con K que la sombra también cubre) se informa como RETROSPECTIVO y no dispara.

Qué mide, con el predicado del tablero ejecutado con node (banco de paridad) para producción y para la sombra:
- REVERSIÓN (pre-autorizada): una alerta protegida A (alerta del scraper de 1 MW o más) nocturna que la
  sombra publica y producción calla. El script NO revierte: lo dice. La regla pide confirmarla en la cabecera
  de la imagen de MIROVA y que la sesión que la detecte haga `git revert` del PR de adopción.
- INVESTIGAR (sin reversión): (i) alertas Muy Bajo (bajo 1 MW, regla D-9 SN) de VIIRS 375 que la sombra
  publica y producción calla, por volcán, si la cota inferior de Wilson de su tasa supera la cota superior del
  A/B (V1, 16 de 194); en MODIS y VIIRS 750 el A/B no guardó la pérdida diferencial y se informa sin disparar;
  (ii) persistencia, tres noches seguidas en un volcán con una alerta que la sombra publica y producción no;
  (iii) publicación de VIIRS 375 de producción en negativos limpios, si la cota inferior de Wilson supera la
  cota superior del A/B (la mayor de V1 y V2).
- Duración: hasta ver 29 protegidas A nocturnas en la sombra después de la adopción, o 120 días.
- Vigilancia ciega: la sombra dejó de producir, no hay frontera o adopción declaradas, o la «sombra» trae
  records de producción. Una vigilancia ciega no da error: da VERDE. Por eso cada caso tiene su veredicto.

Salida: data/audit_continuous/sombra_latest.json y una línea en sombra_history.jsonl.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from math import sqrt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import auto_audit_weekly as aa  # noqa: E402
import clase_mirova as cm  # noqa: E402

SOMBRA = os.path.join(ROOT, "data", "experimental_v2")
PERFIL_SOMBRA = "experimental"
PERFIL_PRODUCCION = "mirova_equivalent"
OUTDIR = aa.OUTDIR
PROTEGIDAS_OBJETIVO = 29     # con 29, una pérdida de 1 de cada 10 se ve con 95 % (1 − 0,9^29), paso 9
DIAS_MAXIMOS = 120
MAX_DIAS_SOMBRA_SIN_DATOS = 3   # experimental-diario corre una vez al día; tres días sin datos es falla
TOL_S = cm.VENTANA_S            # el pareo del etiquetador (banco_paridad.TOL_S)

# Cotas del A/B de adopción (detector K, lectura A), sección 6 de experiments/_s153_fk_v2/v1.log y v2.log:
# «Muy Bajo perdidas k de n» y «negativos publicados k de n». Para los negativos la regla dice «se usa la mayor
# de V1 y V2». Para las Muy Bajo cita V1, 16 de 194, que es VIIRS 375: ahí C0 no perdió ninguna (0 de 194), así
# que la pérdida de K ES la diferencial (sombra publica, producción calla) que mide el disparador. En MODIS y
# VIIRS 750 C0 también perdía (4 de 4 y 10 de 30 en V1) y el A/B no guardó el detalle por pasada: no hay cota
# diferencial y (i) se informa sin disparar (verificador de S156, hallazgo 3). Lo vigila
# tests/test_vigilancia_sombra_s156.py contra el log.
COTAS_AB = {
    "muy_bajo": {"VIIRS375": {"V1": (16, 194), "V2": (26, 388)}},
    "negativos": {"VIIRS375": {"V1": (21, 832), "V2": (37, 1010)}},
}


def wilson(k, n, z=1.96):
    """Intervalo de Wilson al 95 % de k/n. (None, None) si n = 0."""
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - m), min(1.0, c + m))


def cota_superior(tipo, sensor):
    """La mayor de las cotas superiores de V1 y V2, o None si el A/B no dejó cota para ese sensor."""
    cotas = COTAS_AB[tipo].get(sensor)
    return max(wilson(k, n)[1] for k, n in cotas.values()) if cotas else None


def leer_adopcion(path=aa.CAMBIO_DETECTOR_JS):
    """Instante 'YYYY-MM-DD HH:MM' (UTC) del merge de adopción de K (CAMBIO_DETECTOR_UTC), o None."""
    try:
        with open(path, encoding="utf-8") as fh:
            m = re.search(r'CAMBIO_DETECTOR_UTC\s*=\s*"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})', fh.read())
    except OSError:
        return None
    return f"{m.group(1)} {m.group(2)}" if m else None


def _diurna_por_defecto():
    coords = aa._coords_por_volcan()

    def diurna(b, vol, dt):
        ll = coords.get(vol)
        return bool(ll) and aa.es_pasada_diurna_descartada(b, ll[0], ll[1], dt)
    return diurna


def _publica(cands):
    return None if not cands else any(r["pub"] for r in cands)


def pasadas_de_alerta(filas, prod, sombra, win, diurna=None):
    """Cada pasada nocturna de la ventana con alerta de MIROVA (D-9 SN aplicada), con lo que hicieron
    producción y sombra: `prod_pub` / `sombra_pub` = True o False si hay record a ±120 s, None si no miró."""
    diurna = diurna or _diurna_por_defecto()
    por_pasada = defaultdict(list)
    for f in cm.aplicar_regla_minimas(filas, "SN").filas:
        if f.get("tipo") in cm.TIPOS_ALERTA and win[0] <= f["fecha_utc"][:10] <= win[1]:
            por_pasada[cm.clave_pasada(f)].append(f)
    idx = {"prod": defaultdict(list), "sombra": defaultdict(list)}
    for nombre, recs in (("prod", prod), ("sombra", sombra)):
        for r in recs:
            idx[nombre][(r["vol"], r["b"])].append(r)
    out = []
    for (vol, b, minuto), fs in sorted(por_pasada.items()):
        try:
            dt = datetime.fromisoformat(fs[0]["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if diurna(b, vol, dt):
            continue
        cerca = {n: [r for r in idx[n].get((vol, b), []) if abs((r["dt"] - dt).total_seconds()) <= TOL_S]
                 for n in idx}
        vrps = [f["vrp_mw"] for f in fs if f.get("vrp_mw") is not None]
        protegidas = [f for f in fs if cm.alerta_protegida(f)]
        # A119, como en el auto-audit: una protegida que descansa sólo en el OCR de Suomi NPP antes del hito
        # puede llevar la distancia de otra pasada (el VRP sí es suyo).
        sospechosa = (bool(protegidas) and {f.get("source") for f in protegidas} == {"OCR"}
                      and minuto[:10] < aa.HITO_OCR_SUOMI_NPP
                      and any("SNPP" in (r.get("sensor") or "") for n in cerca for r in cerca[n]))
        out.append({"volcano": vol, "sensor": b, "fecha_utc": minuto,
                    "vrp_mirova_mw": round(max(vrps), 3) if vrps else None,
                    "protegida": bool(protegidas), "referencia_sospechosa": sospechosa,
                    "prod_pub": _publica(cerca["prod"]), "sombra_pub": _publica(cerca["sombra"])})
    return out


def _corridas(fechas, largo=3):
    """Corridas de noches consecutivas de `largo` o más."""
    dias = sorted({date.fromisoformat(f) for f in fechas})
    out, actual = [], []
    for d in dias:
        if actual and (d - actual[-1]).days == 1:
            actual.append(d)
        else:
            if len(actual) >= largo:
                out.append(actual)
            actual = [d]
    if len(actual) >= largo:
        out.append(actual)
    return [[d.isoformat() for d in c] for c in out]


def _sombra_si_produccion_no(pasadas):
    return [p for p in pasadas if p["sombra_pub"] is True and p["prod_pub"] is False]


def _persistencia(calla):
    por_volcan = defaultdict(list)
    for p in calla:
        por_volcan[p["volcano"]].append(p["fecha_utc"][:10])
    return [{"volcano": v, "noches": c} for v, fs in sorted(por_volcan.items()) for c in _corridas(fs)]


def disparadores(pasadas, negs_prod, hoy, adopcion=None):
    """Los tres niveles del paso 9 sobre las pasadas POSTERIORES a la adopción; lo anterior, retrospectivo.

    `adopcion`: 'YYYY-MM-DD HH:MM' UTC (por defecto, la del tablero). `negs_prod`: records de producción
    etiquetados por el banco, con `dt`. Sin adopción declarada no hay nada prospectivo que vigilar.
    """
    adopcion = adopcion or leer_adopcion()
    corte = adopcion or "9999-99-99 99:99"
    pros = [p for p in pasadas if p["fecha_utc"][:16] >= corte]
    retro = [p for p in pasadas if p["fecha_utc"][:16] < corte]

    calla = _sombra_si_produccion_no(pros)
    reversion = [p for p in calla if p["protegida"]]

    muy_bajo = {}
    conteo = defaultdict(lambda: [0, 0])
    for p in pros:
        if p["protegida"] or p["prod_pub"] is None or p["sombra_pub"] is None:
            continue
        c = conteo[(p["volcano"], p["sensor"])]
        c[1] += 1
        c[0] += p["sombra_pub"] and not p["prod_pub"]
    for (vol, s), (kk, n) in sorted(conteo.items()):
        lo, hi = wilson(kk, n)
        cota = cota_superior("muy_bajo", s)
        muy_bajo[f"{vol}|{s}"] = {"k": kk, "n": n, "wilson": [round(lo, 4), round(hi, 4)],
                                  "cota_ab": round(cota, 4) if cota is not None else None,
                                  "dispara": cota is not None and lo > cota}

    persistencia = _persistencia(calla)

    corte_dt = (datetime.strptime(corte, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                if adopcion else None)
    negs = [r for r in negs_prod if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"
            and corte_dt is not None and r["dt"] >= corte_dt]
    kn = sum(bool(r["pub"]) for r in negs)
    lo, hi = wilson(kn, len(negs))
    cota = cota_superior("negativos", "VIIRS375")
    negativos = {"k": kn, "n": len(negs), "wilson": [round(lo, 4), round(hi, 4)] if negs else None,
                 "cota_ab": round(cota, 4), "dispara": bool(negs) and lo > cota}

    vence = ((date.fromisoformat(adopcion[:10]) + timedelta(days=DIAS_MAXIMOS)).isoformat()
             if adopcion else None)
    vistas = sum(1 for p in pros if p["protegida"] and p["sombra_pub"] is not None)
    duracion = {"protegidas_vistas_en_sombra": vistas, "objetivo": PROTEGIDAS_OBJETIVO,
                "adopcion": adopcion, "vence": vence,
                "cumplida": vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)}

    calla_retro = _sombra_si_produccion_no(retro)
    retrospectivo = {
        "nota": "anterior a la adopción (datos K reprocesados): se informa y no dispara (REGLA_ADOPCION §4 paso 9, "
                "lectura del 2026-10-19)",
        "n_pasadas": len(retro),
        "protegidas_vistas_en_sombra": sum(1 for p in retro if p["protegida"] and p["sombra_pub"] is not None),
        "protegidas_que_la_sombra_publica_y_k_calla": [p for p in calla_retro if p["protegida"]],
        "muy_bajo_que_la_sombra_publica_y_k_calla": sum(1 for p in calla_retro if not p["protegida"]),
        "persistencia": _persistencia(calla_retro),
    }

    if reversion:
        veredicto = "REVERSION_CANDIDATA"
    elif persistencia or negativos["dispara"] or any(m["dispara"] for m in muy_bajo.values()):
        veredicto = "INVESTIGAR"
    else:
        veredicto = "VERDE"
    return {"veredicto": veredicto, "reversion": reversion, "muy_bajo": muy_bajo, "persistencia": persistencia,
            "negativos_VIIRS375": negativos, "duracion": duracion, "retrospectivo": retrospectivo}


def avisos_sombra(ultima_sombra, hoy):
    if ultima_sombra is None:
        return ["no hay records de la sombra en la ventana (data/experimental_v2): la vigilancia está ciega"]
    dias = (date.fromisoformat(hoy) - date.fromisoformat(ultima_sombra)).days
    if dias > MAX_DIAS_SOMBRA_SIN_DATOS:
        return [f"la sombra no produce hace {dias} días (último dato {ultima_sombra}): revisar "
                "experimental-diario.yml; mientras tanto la vigilancia está ciega"]
    return []


def avisos_perfiles(prod, sombra):
    """Una «sombra» que trae records de producción, o al revés, hace que las dos digan lo mismo: la vigilancia
    da VERDE sin mirar nada (mutación del verificador de S156). La marca de régimen dice el perfil cuando
    existe (en la sombra falta en unos 75 % de los records, que no cuentan ni a favor ni en contra)."""
    av = []
    mal_s = sum(1 for r in sombra if r.get("perfil") == PERFIL_PRODUCCION)
    mal_p = sum(1 for r in prod if r.get("perfil") == PERFIL_SOMBRA)
    if mal_s:
        av.append(f"{mal_s} records de la sombra traen el perfil {PERFIL_PRODUCCION}: no es la sombra")
    if mal_p:
        av.append(f"{mal_p} records de producción traen el perfil {PERFIL_SOMBRA}: no es producción")
    return av


def cargar_insumos(win):
    """Referencia unificada, records de producción (sólo K) y de la sombra, con el predicado del tablero.
    Los de producción quedan etiquetados por el banco con D-9 SN (para los negativos limpios)."""
    import banco_paridad as bp  # noqa: E402  (node; se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]   # sólo records de K
    sombra = bp.cargar_nuestros(coords, inner, win, data=SOMBRA)
    idx = bp.indexar_referencia(filas, coords, win, regla_minimas="SN")
    bp.etiquetar(prod, *idx[:3])
    return filas, prod, sombra


def evaluar(hoy):
    """Todo menos escribir: devuelve el dict de salida."""
    frontera, adopcion = aa.leer_frontera_k(), leer_adopcion()
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "regla": "experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4 paso 9 (lectura del 2026-10-19)",
           "frontera_datos_k": frontera, "adopcion_k_utc": adopcion}
    if frontera is None or adopcion is None:
        out.update({"veredicto": "VIGILANCIA_CIEGA", "avisos": [
            "no se leyeron DATOS_K_DESDE_UTC y CAMBIO_DETECTOR_UTC de frontend/cambio_detector.js: no se sabe "
            "desde cuándo vigilar"]})
        return out
    win = (frontera, hoy)
    filas, prod, sombra = cargar_insumos(win)
    pasadas = pasadas_de_alerta(filas, prod, sombra, win)
    d = disparadores(pasadas, prod, hoy, adopcion)
    ultima = max((r["noche"] for r in sombra), default=None)
    avisos = avisos_sombra(ultima, hoy) + avisos_perfiles(prod, sombra)
    veredicto = d["veredicto"]
    if veredicto == "VERDE" and avisos:
        veredicto = "VIGILANCIA_CIEGA"
    out.update({"ventana": list(win), "veredicto": veredicto, "avisos": avisos,
                "sombra_desde": min((r["noche"] for r in sombra), default=None), "sombra_hasta": ultima,
                "n_pasadas_alerta": len(pasadas),
                "n_pasadas_alerta_con_sombra": sum(1 for p in pasadas if p["sombra_pub"] is not None),
                **{k: v for k, v in d.items() if k != "veredicto"},
                "protegidas_sin_publicar_k": [p for p in pasadas if p["protegida"] and p["prod_pub"] is False]})
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Vigilancia de la sombra de K (REGLA_ADOPCION.md §4 paso 9)")
    ap.add_argument("--cons", help="CSV consolidado de Mirova-v1 (por defecto, el snapshot del repo)")
    ap.add_argument("--ocr", help="CSV OCR de Mirova-v1 (por defecto, el snapshot del repo)")
    a = ap.parse_args(argv)
    # El workflow diario baja la referencia fresca a una carpeta temporal y la pasa acá: el consolidado del
    # snapshot sólo se refresca los lunes (audit-weekly), y una alerta de ayer tiene que poder disparar hoy.
    if a.cons:
        aa.CONS = a.cons
    if a.ocr:
        aa.OCR = a.ocr
    hoy = datetime.now(timezone.utc).date().isoformat()
    out = evaluar(hoy)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "sombra_latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    linea = {"date": hoy, "veredicto": out["veredicto"], "adopcion_k_utc": out.get("adopcion_k_utc"),
             "n_reversion": len(out.get("reversion", [])),
             "protegidas_vistas_en_sombra": (out.get("duracion") or {}).get("protegidas_vistas_en_sombra"),
             "negativos_VIIRS375": out.get("negativos_VIIRS375")}
    with open(os.path.join(OUTDIR, "sombra_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    imprimir(out)


def imprimir(out):
    print(f"Vigilancia de la sombra: {out['veredicto']} · ventana {out.get('ventana')} · adopción "
          f"{out.get('adopcion_k_utc')} · sombra {out.get('sombra_desde')} a {out.get('sombra_hasta')}")
    for a in out.get("avisos", []):
        print("AVISO:", a)
    for p in out.get("reversion", []):
        print(f"  REVERSIÓN CANDIDATA: {p['volcano']} {p['sensor']} {p['fecha_utc']} UTC, MIROVA "
              f"{p['vrp_mirova_mw']} MW: la sombra publica y producción calla. Confirmar en la cabecera de la "
              "imagen de MIROVA antes de revertir (REGLA_ADOPCION.md §4 paso 9)")
    estado = {True: "publica", False: "no publica", None: "sin record"}
    for p in out.get("protegidas_sin_publicar_k", []):
        print(f"  protegida que K no publica: {p['volcano']} {p['sensor']} {p['fecha_utc']} MIROVA "
              f"{p['vrp_mirova_mw']} MW · sombra: {estado[p['sombra_pub']]}"
              f"{' · referencia sospechosa (A119)' if p.get('referencia_sospechosa') else ''}")
    for k, m in (out.get("muy_bajo") or {}).items():
        if m["k"]:
            print(f"  Muy Bajo que la sombra publica y K no: {k} {m['k']} de {m['n']} · Wilson {m['wilson']} "
                  f"contra cota {m['cota_ab']}{' · DISPARA' if m['dispara'] else ''}")
    for p in out.get("persistencia", []):
        print(f"  PERSISTENCIA: {p['volcano']} noches {p['noches']}")
    n = out.get("negativos_VIIRS375")
    if n:
        print(f"  K VIIRS 375 en negativos limpios desde la adopción: {n['k']} de {n['n']} · Wilson {n['wilson']} "
              f"contra cota {n['cota_ab']}{' · DISPARA' if n['dispara'] else ''}")
    du = out.get("duracion")
    if du:
        print(f"  duración: {du['protegidas_vistas_en_sombra']} de {du['objetivo']} protegidas vistas en la "
              f"sombra desde la adopción; vence {du['vence']}")
    r = out.get("retrospectivo")
    if r:
        print(f"  retrospectivo (no dispara): {r['protegidas_vistas_en_sombra']} protegidas vistas en la sombra; "
              f"{len(r['protegidas_que_la_sombra_publica_y_k_calla'])} que la sombra publica y K calla")
        for p in r["protegidas_que_la_sombra_publica_y_k_calla"]:
            print(f"    {p['volcano']} {p['sensor']} {p['fecha_utc']} MIROVA {p['vrp_mirova_mw']} MW")


if __name__ == "__main__":
    main()
