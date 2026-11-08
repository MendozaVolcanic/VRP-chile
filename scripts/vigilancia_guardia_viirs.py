#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · vigilancia_guardia_viirs.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Avisar el mismo día si la vía «código MIROVA» de VIIRS 375 o VIIRS 750 calla una alerta protegida de
#                 MIROVA que el detector K habría publicado. Es la condición del encendido de cada vía.
# Lógica        : Compara cada día, sensor por sensor, producción (la vía, una vez encendida) contra la guardia K
#                 (data/guardia_k_viirs/) contra MIROVA, con el predicado del tablero en los dos lados. Reglas fijas: no
#                 revierte, abre un issue.
# Modelo/método : Comparación determinista de publicaciones por pasada. NO es caja negra (punto 5.5 Res.372).
# Datos entrada : Records JSON de data/mirova_equivalent y data/guardia_k_viirs; registros públicos de MIROVA. SIN datos
#                 personales.
# Variables     : Alerta protegida (1 MW o más, lectura A), D-9 (0,05 MW o menos en VIIRS 375 no es alerta), pasada
#                 nocturna, distancia temporal de pareo (120 s).
# Limitaciones  : Sólo ve las pasadas que MIROVA alerta y que la guardia procesó. Antes del encendido sólo mide el nulo.
#                 Las cotas de investigación son las de la regla; las PENDIENTE DE NICOLÁS se informan sin disparar.
# Refs/datos    : experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md, modelo
#                 experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §4. Entrenamiento: No aplica (sin ML).
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md.
# ════════════════════════════════════════════════════════════════════
"""Vigilancia de la guardia K de VIIRS 375 y VIIRS 750 (S176; diseño docs/superpowers/specs/2026-11-08-encendido-v375e-design.md,
decisiones 3 y 7).

POR QUÉ (fenómeno → mecanismo): con las vías encendidas, VIIRS verá cada volcán como lo ve MIROVA: el gránulo pasado a su
grilla, su detector, su fondo y la suma de todos los alertados. En la sombra casi calza con MIROVA, pero el costo aceptado
es que puede callar señales débiles que K publica, y en un volcán que empieza una fase efusiva esa señal débil es la que
importa. Nicolás prefirió encender con K corriendo aparte como guardia. Este script compara, cada día y sensor por sensor,
producción (la vía) contra la guardia (K) contra MIROVA, y dice qué hacer con lo que encuentra.

Los dos encendidos (B1 para VIIRS 375, B2 para VIIRS 750) se revierten por separado: por eso se corre una vez por sensor
(`--sensor v375` o `--sensor v750`), con salida, juzgadas e issue propios, y una alerta callada en un sensor nunca pide
revertir el otro. Antes del encendido guardia y producción son el mismo detector y tienen que publicar lo mismo: ese es el
nulo medido de la guardia (A110), al menos tres noches antes de pedir B.

Las reglas son las de la vigilancia de MODIS y se reutilizan por import: scripts/vigilancia_guardia_modis.py recibe el
sensor como argumento. Lo propio de aquí: las cotas de cada sensor, la carga de los insumos y el informe de la región
sensible de VIIRS 750, que decide si K sobre-publicaba en Cordón Caulle (decisión 7).

Salida: data/audit_continuous/guardia_v375_latest.json (o v750) y una línea en guardia_v375_history.jsonl.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import vigilancia_guardia_modis as vg  # noqa: E402  (mismas reglas; aquí sólo se les pasa el sensor)

vs = vg.vs
aa = vg.aa
PRODUCCION = os.path.join(ROOT, "data", "mirova_equivalent")
GUARDIA = os.path.join(ROOT, "data", "guardia_k_viirs")
PERFIL_GUARDIA = "guardia_k_viirs"
OUTDIR = aa.OUTDIR
JUZGADAS = os.path.join(ROOT, "experiments", "_s176_v375e_adopcion", "sombra_pasadas_juzgadas_viirs.json")
GRILLAS = os.path.join(ROOT, "pipeline", "grillas_mirova.yaml")
SENSORES = {"v375": "VIIRS375", "v750": "VIIRS750"}
# Cotas de investigación de la regla de reversión (§4.4). POR QUÉ no se eligen aquí: una cota elegida después de ver los
# datos no es pre-registro (A115). None = PENDIENTE DE NICOLÁS: se cuenta y se informa, sin disparar. Se llenan al sellar.
COTAS = {"VIIRS375": {"muy_bajo": None, "sobrepublicacion": None},
         "VIIRS750": {"muy_bajo": None, "sobrepublicacion": None}}


def _hoy():
    return datetime.now(timezone.utc).date().isoformat()


def leer_juzgadas(path=JUZGADAS):
    return vs.leer_juzgadas(path)


def volcanes_sens(path=GRILLAS):
    """Los volcanes Tier A cuya ROI de VIIRS 750 es la sensible, leídos de la grilla (no se copian aquí: A102)."""
    with open(path, encoding="utf-8") as fh:
        volcanes = yaml.safe_load(fh)["volcanes"]
    return sorted(v for v, d in volcanes.items() if d.get("roi_v750") == "sens")


def informe_sens(prod, guardia, encendido, vols):
    """POR QUÉ (decisión 7): en Cordón Caulle y Tupungatito la región sensible de la vía de VIIRS 750 corre desde #939, con
    pocas pasadas, y en Cordón Caulle la sombra publicó 1 vez contra 4 de producción sin saberse si esas 3 son
    sobre-publicación de K. Se cuenta, por volcán y desde el encendido, lo que publica cada uno en las mismas pasadas. No
    dispara nada: no hay cota citable (A115) y la diferencia puede ser un acierto de la vía."""
    if not encendido:
        return {}
    enc_dt = datetime.strptime(encendido, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    out = {}
    for v in vols:
        pares, solo_g, solo_p, pasadas = 0, 0, 0, []
        for p in prod:
            if p["vol"] != v or p["b"] != "VIIRS750" or p.get("via") is not True or p["dt"] < enc_dt:
                continue
            g = [x for x in guardia if x["vol"] == v and x["b"] == "VIIRS750"
                 and abs((x["dt"] - p["dt"]).total_seconds()) <= vg.TOL_S]
            if not g:
                continue
            pares += 1
            gpub, ppub = any(x["pub"] for x in g), bool(p["pub"])
            solo_g += gpub and not ppub
            solo_p += ppub and not gpub
            if gpub and not ppub:
                pasadas.append(p["dt"].strftime("%Y-%m-%d %H:%M"))
        out[v] = {"pares": pares, "solo_guardia": solo_g, "solo_via": solo_p, "pasadas_solo_guardia": pasadas}
    return out


def avisos_cotas(flag, sensor):
    """Con la vía encendida, una cota PENDIENTE DE NICOLÁS es un disparador apagado: se cuenta y nada lo dispara."""
    if not flag:
        return []
    pendientes = [k for k, v in COTAS[sensor].items() if v is None]
    if not pendientes:
        return []
    return [f"la vía de {vg.ETIQUETAS[sensor]} está encendida y siguen PENDIENTES DE NICOLÁS estas cotas de la regla "
            f"(§4.4): {', '.join(pendientes)}. Se cuentan, pero ningún disparador las vigila"]


def leer_encendido(sensor):
    raw = {}
    for vol in aa.VOLS:
        try:
            with open(os.path.join(PRODUCCION, vol + ".json"), encoding="utf-8") as fh:
                raw[vol] = json.load(fh).get("records") or []
        except (OSError, ValueError):
            raw[vol] = []
    return vg.encendido_desde_datos(raw, sensor=sensor)


def cargar_insumos(win, via, caidas, sensor):
    """Referencia, records del sensor en producción (marcados con `via` y `caida_k`) y en la guardia, con el predicado del
    tablero, y cuántos records crudos de la guardia traen la marca de la vía.

    POR QUÉ con D-9 SN: en VIIRS 375 una alerta de 0,05 MW o menos es «MIROVA no vio nada», así que una pasada con sólo
    esas alertas cuenta como negativa. En VIIRS 750 la regla no cambia nada."""
    import banco_paridad as bp  # noqa: E402  (node; se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == sensor]
    for r in prod:
        clave = (r["vol"], r.get("sensor"), r["dt"].strftime("%Y-%m-%d %H:%M"))
        r["via"] = clave in via
        r["caida_k"] = (caidas or {}).get(clave)
    try:
        guardia = [r for r in bp.cargar_nuestros(coords, inner, win, data=GUARDIA) if r["b"] == sensor]
    except FileNotFoundError:
        guardia = []          # la guardia todavía no escribe algún volcán: la frescura lo dice volcán por volcán
    n_via = 0
    for vol in aa.VOLS:
        try:
            with open(os.path.join(GUARDIA, vol + ".json"), encoding="utf-8") as fh:
                recs = json.load(fh).get("records") or []
        except (OSError, ValueError):
            continue
        n_via += sum(1 for r in recs if "via_codigo_mirova" in r and aa.our_bucket(str(r.get("sensor") or "")) == sensor
                     and win[0] <= str(r.get("datetime_utc") or "")[:10] <= win[1])
    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])
    return filas, prod, guardia, n_via


def evaluar(hoy, clave):
    sensor = SENSORES[clave]
    enc = leer_encendido(sensor)
    encendido = enc["encendido_utc"]
    flag = vg.flag_produccion_encendido(sensor)
    h = date.fromisoformat(hoy)
    d0 = h - timedelta(days=vg.DIAS_NULO)
    if encendido:
        d0 = min(d0, date.fromisoformat(encendido[:10]) - timedelta(days=max(vg.DIAS_ANTES_DEL_ENCENDIDO, vg.DIAS_NULO)))
    win = (d0.isoformat(), hoy)
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sensor": sensor,
           "regla": "experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md §4",
           "encendido_utc": encendido, "primera_observacion_via": enc["primera_observacion"],
           "flag_produccion": flag, "ventana": list(win),
           "fase": "antes_del_encendido" if not encendido else "vigilando"}
    filas, prod, guardia, n_via_g = cargar_insumos(win, enc["via"], enc.get("caidas"), sensor)
    pasadas = vg.pasadas_modis(filas, prod, guardia, win, diurna=vs._diurna_por_defecto(), sensor=sensor)
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if ahora[:10] != hoy:
        ahora = f"{hoy} 23:59:59"
    d = vg.disparadores(pasadas, prod, guardia, hoy, encendido, juzgadas=leer_juzgadas(), ahora=ahora, sensor=sensor,
                        cotas=COTAS[sensor])
    if d["duracion"]["cumplida"]:
        out["fase"] = "plazo_cumplido"
    ciegos = (vs.avisos_referencia(filas, hoy) + vg.avisos_referencia_modis(filas, hoy, sensor=sensor)
              + vs._avisos_frescura(guardia, hoy, "la guardia (K)", "guardia-k-viirs.yml", sensores=[sensor])
              + vs._avisos_frescura(prod, hoy, "producción", "nrt.yml", sensores=[sensor])
              + vg.avisos_perfiles(prod, guardia, n_via_g, perfil_guardia=PERFIL_GUARDIA)
              + vg.avisos_via(flag, encendido, prod, sensor=sensor) + vg.avisos_nulo(d["nulo"])
              + avisos_cotas(flag, sensor))
    avisos = ciegos + vg.avisos_caidas(flag, encendido, prod, hoy, sensor=sensor)
    veredicto = d["veredicto"]
    if veredicto == "VERDE" and avisos:
        veredicto = "VIGILANCIA_CIEGA"      # un aviso no tapa una reversión: sólo impide leer la falta de disparos
    if sensor == "VIIRS750":
        out["region_sensible"] = informe_sens(prod, guardia, encendido, volcanes_sens())
    out.update({"veredicto": veredicto, "avisos": avisos,
                "solo_caidas_a_k": veredicto == "VIGILANCIA_CIEGA" and not ciegos,
                "guardia_desde": min((r["noche"] for r in guardia), default=None),
                "guardia_hasta": max((r["noche"] for r in guardia), default=None),
                "n_pasadas_alerta": len(pasadas),
                "n_pasadas_alerta_con_guardia": sum(1 for p in pasadas if p["guardia_pub"] is not None),
                **{k: v for k, v in d.items() if k != "veredicto"},
                "caidas_a_k": vg.caidas_a_k(encendido, prod, sensor=sensor),
                "protegidas_sin_publicar_produccion": [p for p in pasadas if p["protegida"] and p["prod_pub"] is False]})
    return out


def imprimir(out):
    print(f"Vigilancia de la guardia K de {vg.ETIQUETAS[out['sensor']]}: {out['veredicto']} · fase {out.get('fase')} · "
          f"encendido {out.get('encendido_utc')} · guardia {out.get('guardia_desde')} a {out.get('guardia_hasta')}")
    for a in out.get("avisos", []):
        print("AVISO:", a)
    e = vg.ETIQUETAS[out["sensor"]]
    for p in out.get("reversion", []):
        print(f"  REVERSIÓN CANDIDATA: {p['volcano']} {e} {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: la guardia (K) "
              "publica y producción (la vía) calla. Confirmar en la cabecera de la imagen de MIROVA antes de revertir")
    for p in out.get("fuera_de_plazo", []):
        print(f"  CANDIDATA FUERA DE PLAZO: {p['volcano']} {e} {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: sin "
              "pre-autorización, decide Nicolás")
    for p in out.get("borde_del_encendido", []):
        print(f"  BORDE DEL ENCENDIDO: {p['volcano']} {e} {p['fecha_utc']} UTC: investigar")
    for p in out.get("protegidas_calladas_por_k_de_produccion", []):
        print(f"  CALLADA POR K DE PRODUCCIÓN: {p['volcano']} {e} {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW "
              f"({p.get('prod_caida_k') or 'K sin marca'}): investigar; no es candidata a reversión")
    for p in out.get("protegidas_sin_record_produccion", []):
        print(f"  SIN RECORD DE PRODUCCIÓN: {p['volcano']} {e} {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: "
              "la guardia (K) publica y producción no tiene record de la pasada: investigar")
    for nombre in ("muy_bajo", "sobrepublicacion"):
        m = out.get(nombre) or {}
        if m.get("k"):
            print(f"  {nombre}: {m['k']} (cota {m['cota'] if m['cota'] is not None else 'PENDIENTE'}, n {m['n']})"
                  f"{' · DISPARA' if m['dispara'] else ''}")
    n = out.get("nulo") or {}
    print(f"  nulo (antes del encendido): {n.get('distintas')} pasadas distintas de {n.get('pares')} pareadas")
    b = out.get("borde_171_01") or {}
    if b.get("total"):
        print(f"  pasadas que la guardia registra y producción no, por semana: {b['por_semana']}")
    for v, i in (out.get("region_sensible") or {}).items():
        print(f"  región sensible {v}: {i['pares']} pares; sólo la guardia {i['solo_guardia']}, sólo la vía {i['solo_via']}")
    du = out.get("duracion") or {}
    print(f"  duración: {du.get('protegidas_vistas_en_guardia')} de {du.get('objetivo')} protegidas vistas en la guardia "
          f"desde el encendido; vence {du.get('vence')}")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Vigilancia de la guardia K de VIIRS (REGLA_REVERSION_V375E §4)")
    ap.add_argument("--sensor", required=True, choices=sorted(SENSORES))
    ap.add_argument("--cons", help="CSV consolidado de Mirova-v1 (por defecto, el snapshot del repo)")
    ap.add_argument("--ocr", help="CSV OCR de Mirova-v1 (por defecto, el snapshot del repo)")
    a = ap.parse_args(argv)
    if a.cons:
        aa.CONS = a.cons
    if a.ocr:
        aa.OCR = a.ocr
    hoy = _hoy()
    out = evaluar(hoy, a.sensor)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, f"guardia_{a.sensor}_latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=str)
    linea = {"date": hoy, "sensor": out["sensor"], "veredicto": out["veredicto"], "fase": out.get("fase"),
             "encendido_utc": out.get("encendido_utc"),
             "n_reversion": len(out.get("reversion", [])), "n_fuera_de_plazo": len(out.get("fuera_de_plazo", [])),
             "n_calladas_por_k": len(out.get("protegidas_calladas_por_k_de_produccion", [])),
             "n_caidas_a_k": len(out.get("caidas_a_k", [])),
             "protegidas_vistas_en_guardia": (out.get("duracion") or {}).get("protegidas_vistas_en_guardia"),
             "muy_bajo_k": (out.get("muy_bajo") or {}).get("k"),
             "sobrepublicacion_k": (out.get("sobrepublicacion") or {}).get("k"),
             "nulo_distintas": (out.get("nulo") or {}).get("distintas"),
             "borde_171_01_total": (out.get("borde_171_01") or {}).get("total")}
    with open(os.path.join(OUTDIR, f"guardia_{a.sensor}_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    imprimir(out)


if __name__ == "__main__":
    main()
