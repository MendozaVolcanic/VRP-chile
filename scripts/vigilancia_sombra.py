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
Hasta S156 la regla existía y el código no: nadie iba a ver esa pérdida.

Qué mide, sobre la ventana desde la frontera de datos de K (frontend/cambio_detector.js) hasta hoy, con el
predicado del tablero ejecutado con node (banco de paridad) para producción y para la sombra:
- REVERSIÓN (pre-autorizada): una alerta protegida A (alerta del scraper de 1 MW o más) nocturna que la
  sombra publica y producción calla. El script NO revierte: abre el aviso. La regla pide confirmarla en la
  cabecera de la imagen de MIROVA y que la sesión que la detecte haga `git revert` del PR de adopción.
- INVESTIGAR (sin reversión): (i) alertas Muy Bajo (bajo 1 MW, regla D-9 SN) que la sombra publica y
  producción calla, por volcán y sensor, si la cota inferior de Wilson de su tasa supera la cota superior
  medida en el A/B; (ii) persistencia, tres noches seguidas en un volcán con una alerta que la sombra publica
  y producción no; (iii) publicación de VIIRS 375 de producción en negativos limpios, si la cota inferior de
  Wilson supera la cota superior del A/B.
- Duración: hasta ver 29 protegidas A nocturnas en la sombra o 120 días desde la adopción.
- Aviso si la sombra dejó de producir: una sombra muerta deja la vigilancia ciega sin error.

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
OUTDIR = aa.OUTDIR
PROTEGIDAS_OBJETIVO = 29     # con 29, una pérdida de 1 de cada 10 se ve con 95 % (1 − 0,9^29), paso 9
DIAS_MAXIMOS = 120
MAX_DIAS_SOMBRA_SIN_DATOS = 3   # experimental-diario corre a las 14:00 UTC; tres días sin datos es falla
TOL_S = cm.VENTANA_S            # el pareo del etiquetador (banco_paridad.TOL_S)

# Cotas del A/B de adopción (detector K, lectura A), sección 6 de experiments/_s153_fk_v2/v1.log y v2.log:
# «Muy Bajo perdidas k de n» y «negativos publicados k de n». La regla cita V1 (16 de 194 y 21 de 832) y para
# los negativos dice «se usa la mayor de V1 y V2»; se aplica lo mismo a las Muy Bajo, y en VIIRS 375 la mayor
# es la de V1, o sea la letra de la regla. Lo vigila tests/test_vigilancia_sombra_s156.py contra el log.
COTAS_AB = {
    "muy_bajo": {"MODIS": {"V1": (3, 4), "V2": (5, 26)},
                 "VIIRS375": {"V1": (16, 194), "V2": (26, 388)},
                 "VIIRS750": {"V1": (14, 30), "V2": (26, 75)}},
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
    return max(wilson(k, n)[1] for k, n in COTAS_AB[tipo][sensor].values())


def leer_adopcion(path=aa.CAMBIO_DETECTOR_JS):
    """Fecha 'YYYY-MM-DD' del merge de adopción de K (CAMBIO_DETECTOR_UTC), o None."""
    try:
        with open(path, encoding="utf-8") as fh:
            m = re.search(r'CAMBIO_DETECTOR_UTC\s*=\s*"(\d{4}-\d{2}-\d{2})T', fh.read())
    except OSError:
        return None
    return m.group(1) if m else None


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
        out.append({"volcano": vol, "sensor": b, "fecha_utc": minuto,
                    "vrp_mirova_mw": round(max(vrps), 3) if vrps else None,
                    "protegida": any(cm.alerta_protegida(f) for f in fs),
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


def disparadores(pasadas, negs_prod, hoy, adopcion=None):
    """Los tres niveles del paso 9 sobre las pasadas clasificadas y los records de producción etiquetados."""
    calla = [p for p in pasadas if p["sombra_pub"] is True and p["prod_pub"] is False]
    reversion = [p for p in calla if p["protegida"]]

    muy_bajo = {}
    conteo = defaultdict(lambda: [0, 0])
    for p in pasadas:
        if p["protegida"] or p["prod_pub"] is None or p["sombra_pub"] is None:
            continue
        c = conteo[f"{p['volcano']}|{p['sensor']}"]
        c[1] += 1
        c[0] += p["sombra_pub"] and not p["prod_pub"]
    for k, (kk, n) in sorted(conteo.items()):
        lo, hi = wilson(kk, n)
        cota = cota_superior("muy_bajo", k.split("|")[1])
        muy_bajo[k] = {"k": kk, "n": n, "wilson": [round(lo, 4), round(hi, 4)], "cota_ab": round(cota, 4),
                       "dispara": lo > cota}

    por_volcan = defaultdict(list)
    for p in calla:
        por_volcan[p["volcano"]].append(p["fecha_utc"][:10])
    persistencia = [{"volcano": v, "noches": c} for v, fs in sorted(por_volcan.items()) for c in _corridas(fs)]

    negs = [r for r in negs_prod if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"]
    kn = sum(bool(r["pub"]) for r in negs)
    lo, hi = wilson(kn, len(negs))
    cota = cota_superior("negativos", "VIIRS375")
    negativos = {"k": kn, "n": len(negs), "wilson": [round(lo, 4), round(hi, 4)] if negs else None,
                 "cota_ab": round(cota, 4), "dispara": bool(negs) and lo > cota}

    adopcion = adopcion or leer_adopcion()
    vence = (date.fromisoformat(adopcion) + timedelta(days=DIAS_MAXIMOS)).isoformat() if adopcion else None
    vistas = sum(1 for p in pasadas if p["protegida"] and p["sombra_pub"] is not None)
    duracion = {"protegidas_vistas_en_sombra": vistas, "objetivo": PROTEGIDAS_OBJETIVO,
                "adopcion": adopcion, "vence": vence,
                "cumplida": vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)}

    if reversion:
        veredicto = "REVERSION_CANDIDATA"
    elif persistencia or negativos["dispara"] or any(m["dispara"] for m in muy_bajo.values()):
        veredicto = "INVESTIGAR"
    else:
        veredicto = "VERDE"
    return {"veredicto": veredicto, "reversion": reversion, "muy_bajo": muy_bajo, "persistencia": persistencia,
            "negativos_VIIRS375": negativos, "duracion": duracion}


def avisos_sombra(ultima_sombra, hoy):
    if ultima_sombra is None:
        return ["no hay records de la sombra en la ventana (data/experimental_v2): la vigilancia está ciega"]
    dias = (date.fromisoformat(hoy) - date.fromisoformat(ultima_sombra)).days
    if dias > MAX_DIAS_SOMBRA_SIN_DATOS:
        return [f"la sombra no produce hace {dias} días (último dato {ultima_sombra}): revisar "
                "experimental-diario.yml; mientras tanto la vigilancia está ciega"]
    return []


def main():
    import banco_paridad as bp  # noqa: E402  (node; se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    hoy = datetime.now(timezone.utc).date().isoformat()
    frontera = aa.leer_frontera_k()
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "regla": "experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4 paso 9"}
    if frontera is None:
        out.update({"veredicto": "SIN_FRONTERA", "avisos": [
            "no se leyó DATOS_K_DESDE_UTC de frontend/cambio_detector.js: no se sabe desde cuándo vigilar"]})
    else:
        win = (frontera, hoy)
        coords = aa._coords_por_volcan()
        inner = bp.inner_desde_html()
        filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
        prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]   # sólo records de K
        sombra = bp.cargar_nuestros(coords, inner, win, data=SOMBRA)
        idx = bp.indexar_referencia(filas, coords, win, regla_minimas="SN")
        bp.etiquetar(prod, *idx[:3])
        pasadas = pasadas_de_alerta(filas, prod, sombra, win)
        d = disparadores(pasadas, prod, hoy)
        ultima = max((r["noche"] for r in sombra), default=None)
        avisos = avisos_sombra(ultima, hoy)
        veredicto = d["veredicto"]
        if veredicto == "VERDE" and avisos:
            veredicto = "SOMBRA_DETENIDA"
        con_sombra = [p for p in pasadas if p["sombra_pub"] is not None]
        out.update({"ventana": list(win), "veredicto": veredicto, "avisos": avisos,
                    "sombra_desde": min((r["noche"] for r in sombra), default=None), "sombra_hasta": ultima,
                    "n_pasadas_alerta": len(pasadas), "n_pasadas_alerta_con_sombra": len(con_sombra),
                    **{k: v for k, v in d.items() if k != "veredicto"},
                    "protegidas_sin_publicar_k": [p for p in pasadas if p["protegida"] and p["prod_pub"] is False]})
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "sombra_latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    linea = {"date": hoy, "veredicto": out["veredicto"], "n_reversion": len(out.get("reversion", [])),
             "protegidas_vistas_en_sombra": (out.get("duracion") or {}).get("protegidas_vistas_en_sombra"),
             "negativos_VIIRS375": out.get("negativos_VIIRS375")}
    with open(os.path.join(OUTDIR, "sombra_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")

    print(f"Vigilancia de la sombra: {out['veredicto']} · ventana {out.get('ventana')} · sombra "
          f"{out.get('sombra_desde')} a {out.get('sombra_hasta')}")
    for a in out.get("avisos", []):
        print("AVISO:", a)
    for p in out.get("reversion", []):
        print(f"  REVERSIÓN CANDIDATA: {p['volcano']} {p['sensor']} {p['fecha_utc']} UTC, MIROVA "
              f"{p['vrp_mirova_mw']} MW: la sombra publica y producción calla. Confirmar en la cabecera de la "
              "imagen de MIROVA antes de revertir (REGLA_ADOPCION.md §4 paso 9)")
    for p in out.get("protegidas_sin_publicar_k", []):
        print(f"  protegida que K no publica: {p['volcano']} {p['sensor']} {p['fecha_utc']} MIROVA "
              f"{p['vrp_mirova_mw']} MW · sombra: "
              f"{ {True: 'publica', False: 'no publica', None: 'sin record'}[p['sombra_pub']] }")
    for k, m in (out.get("muy_bajo") or {}).items():
        if m["k"]:
            print(f"  Muy Bajo que la sombra publica y K no: {k} {m['k']} de {m['n']} · Wilson {m['wilson']} "
                  f"contra cota {m['cota_ab']}{' · DISPARA' if m['dispara'] else ''}")
    for p in out.get("persistencia", []):
        print(f"  PERSISTENCIA: {p['volcano']} noches {p['noches']}")
    n = out.get("negativos_VIIRS375")
    if n:
        print(f"  K VIIRS 375 en negativos limpios: {n['k']} de {n['n']} · Wilson {n['wilson']} contra cota "
              f"{n['cota_ab']}{' · DISPARA' if n['dispara'] else ''}")
    du = out.get("duracion")
    if du:
        print(f"  duración: {du['protegidas_vistas_en_sombra']} de {du['objetivo']} protegidas vistas en la "
              f"sombra; vence {du['vence']}")


if __name__ == "__main__":
    main()
