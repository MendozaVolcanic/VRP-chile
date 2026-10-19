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
- INVESTIGAR (sin reversión): (i) alertas Muy Bajo (bajo 1 MW, sin las mínimas de D-9) de VIIRS 375 que la sombra
  publica y producción calla, por volcán, si la cota inferior de Wilson de su tasa supera la cota superior del
  A/B con la misma regla (SE: 7 de 161 en V1, 12 de 343 en V2; ver COTAS_AB); en MODIS y VIIRS 750 el A/B no
  guardó la pérdida diferencial y se informa sin disparar;
  (ii) persistencia, tres noches seguidas en un volcán con una alerta que la sombra publica y producción no;
  (iii) publicación de VIIRS 375 de producción en negativos limpios, si la cota inferior de Wilson supera la
  cota superior del A/B (la mayor de V1 y V2), también con la etiqueta original. La reversión y la
  persistencia usan D-9 SN: una alerta mínima no es alerta.
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
#
# DECISIÓN de Nicolás (2026-10-19, después de los verificadores): el disparador (i) es coherente con D-9. Las
# mínimas (0,05 MW o menos en VIIRS 375, NONE en el banner de MIROVA) NO cuentan, y la cota es la del A/B medida con
# la misma regla, SE (`reglas_d9.SE` de experiments/_s153_fk_v2/v1.json y v2.json): K pierde 7 Muy Bajo en V1 (suma
# SE 28 menos 21 negativos, que SE no cambia) y 12 en V2 (49 menos 37). Las 16 y 26 de la etiqueta original incluían
# 9 y 14 mínimas. El denominador con SE no quedó guardado: 33 pasadas pasan de «pos» a «mínima» en V1 y 45 en V2, y
# no todas estaban en el denominador de Muy Bajo (el verificador 4 lo acotó a 163 a 166 en V1, por las sólo OCR de
# Suomi NPP que el A/B excluye, y a cerca de 350 en V2, por las de marzo que `decide_sensor` deja fuera). Se toma 161
# y 343, el menor posible, que da la cota MÁS ALTA (0,0870 contra 0,0845 a 0,086 con el real): dispara menos, igual
# que «la mayor de V1 y V2». Con la etiqueta original, el único disparo con datos reales habría sido Llaima
# VIIRS 375 2026-10-03 07:06, 0,01 MW, una pasada que MIROVA llama NONE (verificador 3).
COTAS_AB = {
    "muy_bajo": {"VIIRS375": {"V1_SE": (7, 161), "V2_SE": (12, 343)}},
    "negativos": {"VIIRS375": {"V1": (21, 832), "V2": (37, 1010)}},
}
# DECISIÓN de Nicolás (2026-10-19): las pasadas ya juzgadas se anotan en un archivo versionado, junto a la regla, y no
# vuelven a disparar; sin eso una candidata sale todos los días hasta 120 días y cerrar su issue lo reabre.
JUZGADAS = os.path.join(ROOT, "experiments", "_s151_prereg_fk_11", "sombra_pasadas_juzgadas.json")


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
    """Instante 'YYYY-MM-DD HH:MM:SS' (UTC) del merge de adopción de K (CAMBIO_DETECTOR_UTC), o None.
    Con segundos: la adopción fue a las 09:57:30 y una pasada de las 09:57:10 es todavía de antes."""
    try:
        with open(path, encoding="utf-8") as fh:
            m = re.search(r'CAMBIO_DETECTOR_UTC\s*=\s*"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(:\d{2})?', fh.read())
    except OSError:
        return None
    return f"{m.group(1)} {m.group(2)}{m.group(3) or ':00'}" if m else None


def _diurna_por_defecto():
    coords = aa._coords_por_volcan()

    def diurna(b, vol, dt):
        ll = coords.get(vol)
        return bool(ll) and aa.es_pasada_diurna_descartada(b, ll[0], ll[1], dt)
    return diurna


def _publica(cands):
    return None if not cands else any(r["pub"] for r in cands)


def pasadas_de_alerta(filas, prod, sombra, win, diurna=None):
    """Cada pasada nocturna de la ventana con alerta de MIROVA (lectura A: ALERTA_TERMICA u ALERTA_TERMICA_OCR,
    nunca las filas sin geometría), con lo que hicieron producción y sombra en el MISMO sensor:
    `prod_pub` / `sombra_pub` = True o False si hay record a ±120 s, None si no miró.

    `minima`: la pasada es mínima según D-9 (todas sus alertas de 0,05 MW o menos en VIIRS 375). La regla SN
    dice que ahí MIROVA no vio nada: no cuenta para la reversión, la persistencia ni el disparador (i) (decisión
    de Nicolás del 2026-10-19: (i) coherente con D-9, contra la cota SE del A/B).
    """
    diurna = diurna or _diurna_por_defecto()
    minimas = cm.aplicar_regla_minimas(filas, "SN").minimas
    por_pasada = defaultdict(list)
    for f in filas:
        if f.get("tipo") in cm.TIPOS_ALERTA and win[0] <= f["fecha_utc"][:10] <= win[1]:
            por_pasada[cm.clave_pasada(f)].append(f)
    idx = {"prod": defaultdict(list), "sombra": defaultdict(list)}
    for nombre, recs in (("prod", prod), ("sombra", sombra)):
        for r in recs:
            idx[nombre][(r["vol"], r["b"])].append(r)
    out = []
    for clave, fs in sorted(por_pasada.items()):
        vol, b, minuto = clave
        try:
            dt = datetime.fromisoformat(fs[0]["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if diurna(b, vol, dt):
            continue
        # El pareo es por volcán Y sensor: en PCC el 2026-10-10 K publicó la pasada en VIIRS 375 y calló en
        # VIIRS 750; parear sin sensor borra justo la pérdida (mutación M1 del verificador 2).
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
                    "instante_utc": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "vrp_mirova_mw": round(max(vrps), 3) if vrps else None,
                    "protegida": bool(protegidas), "minima": clave in minimas,
                    "referencia_sospechosa": sospechosa,
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
    """Pasadas que la sombra publica y producción, que SÍ miró, calla. Sin record de producción no es «calla»."""
    return [p for p in pasadas if p["sombra_pub"] is True and p["prod_pub"] is False]


def _persistencia(calla):
    por_volcan = defaultdict(list)
    for p in calla:
        por_volcan[p["volcano"]].append(p["fecha_utc"][:10])
    return [{"volcano": v, "noches": c} for v, fs in sorted(por_volcan.items()) for c in _corridas(fs)]


def _instante(adopcion):
    return datetime.strptime(adopcion, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def leer_juzgadas(path=JUZGADAS):
    """Claves (volcán, sensor, minuto) de las pasadas ya juzgadas, con su registro. Archivo ausente = ninguna;
    archivo ilegible = error (una lista de excepciones que no se puede leer no se ignora en silencio)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    # Formato estricto: una entrada mal escrita («T», hora sin cero, nombre de volcán distinto) no calzaría con
    # ninguna pasada y la candidata seguiría disparando sin que nadie entienda por qué (verificador 4, hallazgo 4).
    # Mejor que el script caiga: el workflow abre el issue «el script fallo».
    out = {}
    for p in d["pasadas"]:
        if (p.get("volcano") not in aa.VOLS or p.get("sensor") not in aa.SENSORS
                or not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", p.get("fecha_utc") or "")):
            raise ValueError(f"entrada inválida en {path}: {p!r}; se espera volcano de {aa.VOLS}, sensor de "
                             f"{aa.SENSORS} y fecha_utc 'YYYY-MM-DD HH:MM'")
        out[(p["volcano"], p["sensor"], p["fecha_utc"])] = p
    return out


def _clave(p):
    return (p["volcano"], p["sensor"], p["fecha_utc"][:16])


def disparadores(pasadas, negs_prod, hoy, adopcion=None, juzgadas=None):
    """Los tres niveles del paso 9 sobre las pasadas POSTERIORES a la adopción; lo anterior, retrospectivo.

    `adopcion`: 'YYYY-MM-DD HH:MM:SS' UTC (por defecto, la del tablero). `negs_prod`: records de producción
    etiquetados por el banco, con `dt` y `lab_original`. Sin adopción declarada no hay nada prospectivo.
    `juzgadas`: {(volcán, sensor, minuto): registro} de las pasadas ya decididas. Una juzgada sale SÓLO de la
    reversión (lo que se decidió fue si revertir): sigue contando en la persistencia, en los conteos y en la
    duración, porque la sombra la vio igual (verificador 4 de S156, hallazgo 2).
    """
    adopcion = adopcion or leer_adopcion()
    juzgadas = juzgadas or {}
    corte = adopcion or "9999-99-99 99:99:99"
    pros = [p for p in pasadas if p["instante_utc"] >= corte]
    retro = [p for p in pasadas if p["instante_utc"] < corte]

    # Plazo de la regla PASADA POR PASADA (verificador 4, hallazgo 1): «hasta ver 29 protegidas» o 120 días. Una
    # protegida está dentro del plazo si es una de las primeras 29 vistas en la sombra (la 29.ª incluida) y su
    # instante es anterior al vencimiento. Así una pasada no cambia de clase con el día en que se corre.
    vence = ((date.fromisoformat(adopcion[:10]) + timedelta(days=DIAS_MAXIMOS)).isoformat()
             if adopcion else None)
    vistas_pros = sorted((p for p in pros if p["protegida"] and p["sombra_pub"] is not None),
                         key=lambda p: (p["instante_utc"], p["volcano"], p["sensor"]))
    orden = {_clave(p): i + 1 for i, p in enumerate(vistas_pros)}

    def dentro_de_plazo(p):
        return bool(vence) and orden.get(_clave(p), 10 ** 9) <= PROTEGIDAS_OBJETIVO and p["instante_utc"][:10] < vence

    calla = _sombra_si_produccion_no(pros)
    candidatas = [p for p in calla if p["protegida"] and _clave(p) not in juzgadas]
    reversion = [p for p in candidatas if dentro_de_plazo(p)]
    fuera_de_plazo = [p for p in candidatas if not dentro_de_plazo(p)]

    # (i) Muy Bajo de VIIRS 375 por volcán, coherente con D-9 (decisión de Nicolás): sin las mínimas, y contra la
    # cota del A/B medida con la regla SE.
    muy_bajo = {}
    conteo = defaultdict(lambda: [0, 0])
    for p in pros:
        if p["protegida"] or p["minima"] or p["prod_pub"] is None or p["sombra_pub"] is None:
            continue
        c = conteo[(p["volcano"], p["sensor"])]
        c[1] += 1
        c[0] += bool(p["sombra_pub"] and not p["prod_pub"])
    for (vol, s), (kk, n) in sorted(conteo.items()):
        lo, hi = wilson(kk, n)
        cota = cota_superior("muy_bajo", s)
        muy_bajo[f"{vol}|{s}"] = {"k": kk, "n": n, "wilson": [round(lo, 4), round(hi, 4)],
                                  "cota_ab": round(cota, 4) if cota is not None else None,
                                  "dispara": cota is not None and lo > cota}

    # (ii) persistencia: «una alerta de MIROVA»; con D-9 SN, las mínimas no son alertas.
    persistencia = _persistencia([p for p in calla if not p["minima"]])

    # (iii) negativos limpios de VIIRS 375 con la etiqueta ORIGINAL, la misma con que se midió la cota del A/B:
    # SN convierte en negativo una pasada donde MIROVA vio algo de 0,05 MW o menos y casi duplica la tasa
    # (verificador 2 de S156, hallazgo 6).
    corte_dt = _instante(adopcion) if adopcion else None
    negs = [r for r in negs_prod if r["b"] == "VIIRS375" and r.get("lab_original") == "neg_limpio"
            and corte_dt is not None and r["dt"] >= corte_dt]
    kn = sum(bool(r["pub"]) for r in negs)
    lo, hi = wilson(kn, len(negs))
    cota = cota_superior("negativos", "VIIRS375")
    negativos = {"k": kn, "n": len(negs), "wilson": [round(lo, 4), round(hi, 4)] if negs else None,
                 "cota_ab": round(cota, 4), "dispara": bool(negs) and lo > cota}

    vistas = len(vistas_pros)
    duracion = {"protegidas_vistas_en_sombra": vistas, "objetivo": PROTEGIDAS_OBJETIVO,
                "adopcion": adopcion, "vence": vence,
                "cumplida": vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)}

    calla_retro = _sombra_si_produccion_no(retro)
    retrospectivo = {
        "nota": "anterior a la adopción (datos K reprocesados): se informa y no dispara; una pérdida protegida "
                "se investiga con un issue abierto a mano (el retrospectivo es fijo: la sombra no crece hacia "
                "atrás). REGLA_ADOPCION §4 paso 9, lectura del 2026-10-19",
        "n_pasadas": len(retro),
        "protegidas_vistas_en_sombra": sum(1 for p in retro if p["protegida"] and p["sombra_pub"] is not None),
        "protegidas_que_la_sombra_publica_y_k_calla": [p for p in calla_retro if p["protegida"]],
        "muy_bajo_que_la_sombra_publica_y_k_calla": sum(1 for p in calla_retro if not p["protegida"]),
        "persistencia": _persistencia([p for p in calla_retro if not p["minima"]]),
    }

    # Fuera del plazo, una candidata se sigue informando pero ya no está pre-autorizada (decisión de Nicolás).
    if reversion:
        veredicto = "REVERSION_CANDIDATA"
    elif fuera_de_plazo:
        veredicto = "CANDIDATA_FUERA_DE_PLAZO"
    elif persistencia or negativos["dispara"] or any(m["dispara"] for m in muy_bajo.values()):
        veredicto = "INVESTIGAR"
    else:
        veredicto = "VERDE"
    return {"veredicto": veredicto, "reversion": reversion, "fuera_de_plazo": fuera_de_plazo, "muy_bajo": muy_bajo,
            "persistencia": persistencia, "negativos_VIIRS375": negativos, "duracion": duracion,
            "retrospectivo": retrospectivo,
            "juzgadas": [dict(p, juicio=juzgadas[_clave(p)]) for p in pasadas if _clave(p) in juzgadas]}


def _avisos_frescura(recs, hoy, nombre, revisar, vols=None, sensores=None):
    """Frescura POR VOLCÁN Y SENSOR. Si un lado muere en un solo volcán o en un solo sensor, sumar todo lo deja
    verde: el verificador 2 lo mostró con la sombra de Chillán (protegida de 5 MW, VERDE) y el 3 con la sombra
    sin MODIS (13 protegidas MODIS sin mirar, VERDE)."""
    vols = vols or aa.VOLS
    sensores = sensores or aa.SENSORS
    ultima = defaultdict(str)
    for r in recs:
        ultima[(r["vol"], r["b"])] = max(ultima[(r["vol"], r["b"])], r["noche"])
    av = []
    for v in vols:
        for s in sensores:
            u = ultima.get((v, s))
            if not u:
                av.append(f"no hay records de {nombre} de {v} en {s} en la ventana: ese volcán y sensor están ciegos")
                continue
            dias = (date.fromisoformat(hoy) - date.fromisoformat(u)).days
            if dias > MAX_DIAS_SOMBRA_SIN_DATOS:
                av.append(f"{nombre} de {v} en {s} no produce hace {dias} días (último dato {u}): revisar "
                          f"{revisar}; mientras tanto ese volcán y sensor están ciegos")
    return av


def avisos_sombra(sombra, hoy, vols=None, sensores=None):
    return _avisos_frescura(sombra, hoy, "la sombra", "experimental-diario.yml", vols, sensores)


def avisos_produccion(prod, hoy, vols=None, sensores=None):
    """Producción sin records de K en un volcán o sensor (por ejemplo, si el filtro por `codigo_sha` deja
    todo afuera) tampoco puede «callar»: la vigilancia no la ve (verificador 3, hallazgo 1)."""
    return _avisos_frescura(prod, hoy, "producción (K)", "nrt.yml y la marca de régimen", vols, sensores)


def avisos_referencia(filas, hoy):
    """Una referencia de MIROVA vacía o detenida no da alertas y la vigilancia sale VERDE sin mirar nada
    (verificador 3, hallazgo 1). Se mide sobre TODAS las filas, RUTINA incluidas, como el auto-audit
    (`MAX_GT_STALE_DAYS`): un período sin alertas es legítimo, un archivo que no crece no."""
    fechas = [f["fecha_utc"][:10] for f in filas if (f.get("fecha_utc") or "")[:4].isdigit()]
    if not fechas:
        return ["la referencia de MIROVA está vacía: no hay contra qué vigilar"]
    dias = (date.fromisoformat(hoy) - date.fromisoformat(max(fechas))).days
    if dias > aa.MAX_GT_STALE_DAYS:
        return [f"la referencia de MIROVA no registra nada hace {dias} días (última fila {max(fechas)}): "
                "es el scraper de Mirova-v1, no los volcanes"]
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
    Los de producción quedan etiquetados por el banco con la regla original en `lab_original` (para los
    negativos limpios, como la cota del A/B) y con D-9 SN en `lab`."""
    import banco_paridad as bp  # noqa: E402  (node; se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]   # sólo records de K
    sombra = bp.cargar_nuestros(coords, inner, win, data=SOMBRA)
    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win)[:3])
    for r in prod:
        r["lab_original"] = r["lab"]
    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])
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
    d = disparadores(pasadas, prod, hoy, adopcion, juzgadas=leer_juzgadas())
    avisos = (avisos_referencia(filas, hoy) + avisos_sombra(sombra, hoy) + avisos_produccion(prod, hoy)
              + avisos_perfiles(prod, sombra))
    # Un aviso no tapa una reversión ni una investigación: sólo impide que la falta de disparos se lea como VERDE.
    veredicto = d["veredicto"]
    if veredicto == "VERDE" and avisos:
        veredicto = "VIGILANCIA_CIEGA"
    out.update({"ventana": list(win), "veredicto": veredicto, "avisos": avisos,
                "sombra_desde": min((r["noche"] for r in sombra), default=None),
                "sombra_hasta": max((r["noche"] for r in sombra), default=None),
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
    for p in out.get("fuera_de_plazo", []):
        print(f"  CANDIDATA FUERA DE PLAZO: {p['volcano']} {p['sensor']} {p['fecha_utc']} UTC, MIROVA "
              f"{p['vrp_mirova_mw']} MW: la sombra publica y producción calla, fuera del plazo de la regla; sin "
              "pre-autorización, decide Nicolás")
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
    for p in out.get("juzgadas", []):
        print(f"  ya juzgada (no dispara): {p['volcano']} {p['sensor']} {p['fecha_utc']} · "
              f"{p['juicio'].get('decision')} ({p['juicio'].get('fecha_decision')})")


if __name__ == "__main__":
    main()
