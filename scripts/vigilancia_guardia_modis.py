#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vigilancia de la guardia K de MODIS (S172; regla experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md
§4; en S172 vivía sólo en la rama loop/activo; en main desde el PR B #934; diseño docs/superpowers/specs/2026-11-01-encendido-modd-design.md, decisión 3).

POR QUÉ (fenómeno → mecanismo): la vía «código MIROVA» de MODIS ve el volcán como lo ve MIROVA (el gránulo pasado a
su grilla de 1 km, su detector, su fondo, la suma de todos los alertados) y ganó el A/B pre-registrado de MOD-D. Pero
descarta en silencio los gránulos que no cubren el volcán (100 celdas a 45 km, centro a más de 5 km; hallazgo 171-01),
y una señal débil o de borde de barrido que K publica podría quedar callada. Nicolás decidió (2026-10-31) encender la
vía sin esperar la sombra de 28 noches, con K corriendo aparte como guardia (data/guardia_k_modis/). Este script
compara cada día, sólo en MODIS, producción (la vía) contra la guardia (K) contra MIROVA, con el predicado del tablero
ejecutado con node (banco de paridad) en los dos lados.

Qué mide (reutiliza por import scripts/vigilancia_sombra.py, que vigila K y NO se modifica):
- REVERSIÓN (pre-autorizada): una alerta protegida A de MODIS (alerta del scraper de 1 MW o más, regla SN de D-9)
  nocturna, posterior al encendido, que la guardia publica y producción calla. El script NO revierte: lo dice. La regla
  pide confirmarla en la cabecera de la imagen de MIROVA y que la sesión que la detecte haga `git revert` del PR B.
- INVESTIGAR (sin reversión): (i) alertas Muy Bajo (sobre 0,05 MW y bajo 1 MW) que MIROVA publica, la guardia publica
  y producción calla, más de 2 en el plazo; (ii) publicación de producción en negativos limpios donde la guardia no
  publica, más de 3 en el plazo; las dos cotas salen de los discordantes del A/B de MOD-D (`brazos.V.p2.discordantes`
  de resultado_f4.json: 2 bajo1 a favor de K y 3 neg_limpio a favor de la vía) y las fija Nicolás al sellar; (iii) se
  informan, por semana ISO, las pasadas que la guardia registra y producción no (el descarte de borde de 171-01), sin
  disparar: la regla no da cota y A115 prohíbe inventarla. Además, antes del encendido guardia y producción son el
  mismo detector y tienen que publicar lo mismo: ese es el nulo medido de la guardia (A110); si no, INVESTIGAR.
  Y una protegida anterior al encendido cuyo record de producción ya es de la vía (el NRT re-escribe hasta 8 días
  hacia atrás) pide investigar: no está pre-autorizada, pero no puede quedar sin mirar.
- Duración: hasta ver 29 protegidas A nocturnas de MODIS en la guardia o 120 días desde el encendido. Fuera de plazo,
  una candidata se informa sin pre-autorización.
- Vigilancia ciega: guardia o producción sin datos frescos de MODIS en algún volcán, referencia de MIROVA detenida,
  una guardia que trae records de la vía (dejó de ser K), perfiles cruzados, o el flag de producción encendido sin
  records de la vía (la vía cayendo siempre a K dejaría guardia = producción: VERDE para siempre).

EL ENCENDIDO SALE DE LOS DATOS (diseño, decisión 3): el menor `processed_utc` de un record MODIS de producción con
`via_codigo_mirova: true`, no una constante que alguien tiene que llenar. ⚠️ S172 ronda 2 (mini auditoría, MA172-206):
la primera versión usaba `first_processed_utc`, pero pipeline/store.py lo hereda en todo reemplazo y el upgrade de NRT a
estándar re-escribe con la vía pasadas de hasta ~4,5 días antes: el encendido caía antes del merge. `processed_utc` lo
escribe la corrida que guardó el record, así que un record de la vía sólo puede traer uno posterior al merge. Las pasadas
anteriores al encendido re-escritas por la vía quedan del lado retrospectivo: por eso la regla de la protegida con
record de la vía anterior al encendido (investigar, no revertir).

S172 ronda 2, otros tres huecos que la mini auditoría midió con un arnés (D:/vrp-trabajo/temporales/s172_miniaud/f2):
- MA172-202: una protegida que la guardia publica y de la que producción NO tiene record (la vía descarta el gránulo
  de borde, 171-01) daba VERDE. Ahora, pasadas ESPERA_SIN_RECORD_H horas (el NRT procesa con atraso), pide INVESTIGAR.
- MA172-204: la frescura de la referencia se medía sobre todas las filas; ahora también sobre las de MODIS.
- MA172-208: un nulo con 0 pares se leía como nulo sano; ahora es aviso (vigilancia ciega).

S175 (docs/AUDIT_S175.md §8 decisión 11, hallazgos 151, 152 y V1-01; decisión 3 de S174, hallazgo 253; aprobadas por
Nicolás el 2026-11-07). Con el flag encendido, cuando la vía no puede correr el procesador escribe K con la marca en
texto (`via_codigo_mirova`: "sin_grilla", "sin_mxd03", "geo_distinta"). Esa pasada compara K con K y no dice nada de
la vía. Por eso, del lado prospectivo, cada pasada mira si su record de producción es de la vía (`prod_via`):
- la reversión pre-autorizada exige el record de la vía; una protegida que la caída a K calla y la guardia publica pide
  INVESTIGAR (`protegidas_calladas_por_k_de_produccion`), nunca REVERSION_CANDIDATA (151, mutación M6);
- el plazo de 29 protegidas, Muy Bajo y la sobre-publicación cuentan sólo pasadas de la vía (V1-01);
- la frescura de la vía se mide POR VOLCÁN, desde el encendido: si la vía cae a K o deja de escribir en un solo volcán,
  aviso (152, mutaciones M2 y M2c); antes se comparaba la última noche de la vía con la última de MODIS sumando los 11;
- cada caída a K se lista (`caidas_a_k`) y, si es de los últimos DIAS_AVISO_CAIDA días, es aviso: cuenta como K, no
  como la vía (decisión 3 de S174). Un VERDE con ese aviso sigue siendo VIGILANCIA_CIEGA (la regla, §4: un VERDE con
  avisos no es VERDE), pero si es el único aviso la salida lo marca (`solo_caidas_a_k`) y la issue dice lo que pasa: las
  demás pasadas sí se miraron (VPR959-05).
Y el descarte de borde (153) se nombra pasada por pasada en `borde_171_01.pasadas`, no sólo por semana.

Salida: data/audit_continuous/guardia_modis_latest.json y una línea en guardia_modis_history.jsonl.
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import vigilancia_sombra as vs  # noqa: E402  (vigila K; se importa, no se modifica)

aa = vs.aa
SENSOR = "MODIS"
PRODUCCION = os.path.join(ROOT, "data", "mirova_equivalent")
GUARDIA = os.path.join(ROOT, "data", "guardia_k_modis")
PERFIL_GUARDIA = "guardia_k_modis"
PERFIL_PRODUCCION = "mirova_equivalent"
OUTDIR = aa.OUTDIR
PROTEGIDAS_OBJETIVO = vs.PROTEGIDAS_OBJETIVO   # 29: una pérdida de 1 de cada 10 se ve con 95 %, como con K
DIAS_MAXIMOS = vs.DIAS_MAXIMOS                 # 120
TOL_S = vs.TOL_S                               # el pareo del etiquetador (±120 s)
# §4.4 (i) y (ii) de la regla de reversión: cotas D1 y D2, contestadas «Sí» por Nicolás el 2026-11-02. Más de COTA dispara.
COTA_MUY_BAJO = 2
COTA_SOBREPUBLICACION = 3
UMBRAL_MINIMO_MW = 0.05                        # «sobre 0,05 MW»: lo de 0,05 o menos no cuenta como Muy Bajo
DIAS_NULO = 14                                 # cuántos días antes del encendido (o de hoy) mide el nulo
# Cuántos días una caída a K sigue siendo aviso (decisión 3 de S174). Propuesta del implementador, la fija Nicolás; es
# otro parámetro que el del nulo, aunque hoy valga lo mismo (VPR959-05).
DIAS_AVISO_CAIDA = 14
DIAS_ANTES_DEL_ENCENDIDO = 10                  # la ventana cubre el re-escrito de 8 días del NRT, con margen
# MA172-202: horas que se espera antes de leer como silencio una pasada sin record de producción (el NRT procesa con
# atraso: LANCE ~3 h y el cron). Propuesta del implementador; la fija Nicolás al sellar la regla.
ESPERA_SIN_RECORD_H = 24
# Decisión de K del 2026-10-19 aplicada a MODIS (§4 de la regla, «como (d) de K»): las pasadas ya juzgadas no vuelven
# a disparar. Mismo formato estricto que experiments/_s151_prereg_fk_11/sombra_pasadas_juzgadas.json.
JUZGADAS = os.path.join(ROOT, "experiments", "_s171_modd_adopcion", "sombra_pasadas_juzgadas_modis.json")


def _t(texto_utc):
    """'YYYY-MM-DDTHH:MM:SSZ' a 'YYYY-MM-DD HH:MM:SS', o None."""
    try:
        return datetime.fromisoformat(str(texto_utc).replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def encendido_desde_datos(raw_por_volcan):
    """{encendido_utc, primera_observacion, via, caidas}: el menor `processed_utc` de un record MODIS de producción con
    `via_codigo_mirova` True (MA172-206: no `first_processed_utc`, que hereda la fecha de K), la observación más temprana
    de la vía, el conjunto de claves (volcán, sensor, 'YYYY-MM-DD HH:MM') de esos records y, S175, las caídas a K
    {clave: marca} (marca en texto, `"sin_grilla"` y compañía): no son la vía, son K con aviso (decisión 3 de S174)."""
    via, proc, obs, caidas = set(), [], [], {}
    for vol, recs in raw_por_volcan.items():
        for r in recs:
            if not str(r.get("sensor") or "").startswith("MODIS"):
                continue
            dt = str(r.get("datetime_utc") or "")[:16].replace("T", " ")
            marca = r.get("via_codigo_mirova")
            if isinstance(marca, str):
                caidas[(vol, r.get("sensor"), dt)] = marca
            if marca is not True:
                continue
            via.add((vol, r.get("sensor"), dt))
            obs.append(dt)
            t = _t(r.get("processed_utc"))
            if t:
                proc.append(t)
    return {"encendido_utc": min(proc) if proc else None, "primera_observacion": min(obs) if obs else None,
            "via": via, "caidas": caidas}


def leer_encendido():
    raw = {}
    for vol in aa.VOLS:
        try:
            with open(os.path.join(PRODUCCION, vol + ".json"), encoding="utf-8") as fh:
                raw[vol] = json.load(fh).get("records") or []
        except (OSError, ValueError):
            raw[vol] = []
    return encendido_desde_datos(raw)


def flag_produccion_encendido():
    """ENABLE_MODIS_CODIGO_MIROVA de producción leído desde pipeline.profile en un proceso aparte (A89), o None."""
    env = dict(os.environ, VRP_PROFILE=PERFIL_PRODUCCION, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"],
                           cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    ultima = (r.stdout.strip().splitlines() or [""])[-1]
    return {"True": True, "False": False}.get(ultima) if r.returncode == 0 else None


def leer_juzgadas(path=JUZGADAS):
    return vs.leer_juzgadas(path)


def _cerca(recs, dt):
    return [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= TOL_S]


def _por_volcan(recs):
    out = defaultdict(list)
    for r in recs:
        if r["b"] == SENSOR:
            out[r["vol"]].append(r)
    return out


def pasadas_modis(filas, prod, guardia, win, diurna=None):
    """Pasadas nocturnas de MODIS con alerta de MIROVA (vigilancia_sombra.pasadas_de_alerta, la misma lectura A y el
    mismo pareo por volcán y sensor), con `guardia_pub` y `prod_via` (algún record de producción de la pasada es de
    la vía; None si producción no tiene record; False si todos son K, por ejemplo una caída a K, cuya marca va en
    `prod_caida_k`)."""
    pasadas = vs.pasadas_de_alerta(filas, prod, guardia, win, diurna=diurna)
    idx = _por_volcan(prod)
    out = []
    for p in pasadas:
        if p["sensor"] != SENSOR:
            continue
        p = dict(p)
        p["guardia_pub"] = p.pop("sombra_pub")
        dt = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        cand = _cerca(idx.get(p["volcano"], []), dt)
        p["prod_via"] = any(r.get("via") is True for r in cand) if cand else None
        p["prod_caida_k"] = next((r["caida_k"] for r in cand if r.get("caida_k")), None)
        out.append(p)
    return out


def _dt(texto):
    return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def disparadores(pasadas, prod, guardia, hoy, encendido=None, juzgadas=None, ahora=None):
    """Los niveles de §4 sobre lo posterior al encendido; lo anterior, retrospectivo y nulo. `ahora`: instante UTC
    'YYYY-MM-DD HH:MM:SS' de la corrida (por defecto, la medianoche de `hoy`), para la espera de MA172-202."""
    juzgadas = juzgadas or {}
    ahora = ahora or f"{hoy} 00:00:00"
    corte = encendido or "9999-99-99 99:99:99"
    pros = [p for p in pasadas if p["instante_utc"] >= corte]
    retro = [p for p in pasadas if p["instante_utc"] < corte]
    vence_utc = (_dt(encendido) + timedelta(days=DIAS_MAXIMOS)).strftime("%Y-%m-%d %H:%M:%S") if encendido else None
    vence = vence_utc[:10] if vence_utc else None
    # V1-01 (S175): una protegida cuyo record de producción es K (prod_via False) compara K con K y no avanza el plazo
    # de §4.6. Sin record de producción (None) sí cuenta: es la vía que descartó la pasada (y pide investigar, abajo).
    vistas = sorted((p for p in pros if p["protegida"] and p["guardia_pub"] is not None
                     and p.get("prod_via") is not False),
                    key=lambda p: (p["instante_utc"], p["volcano"]))
    orden = {vs._clave(p): i + 1 for i, p in enumerate(vistas)}

    def en_plazo_instante(p):
        return bool(vence_utc) and p["instante_utc"] < vence_utc

    def dentro_de_plazo(p):
        return en_plazo_instante(p) and orden.get(vs._clave(p), 10 ** 9) <= PROTEGIDAS_OBJETIVO

    def calla(p):
        return p["guardia_pub"] is True and p["prod_pub"] is False

    # 151 (S175): la regla pre-autoriza revertir cuando «producción (la vía) tiene record y no publica». Si el record es
    # una caída a K, la diferencia es entre dos corridas de K, no de la vía: investigar, nunca revertir (mutación M6).
    candidatas = [p for p in pros if p["protegida"] and calla(p) and p.get("prod_via") is True
                  and vs._clave(p) not in juzgadas]
    reversion = [p for p in candidatas if dentro_de_plazo(p)]
    fuera_de_plazo = [p for p in candidatas if not dentro_de_plazo(p)]
    calladas_por_k = [p for p in pros if p["protegida"] and calla(p) and p.get("prod_via") is not True
                      and vs._clave(p) not in juzgadas]

    # (i) Muy Bajo: sobre 0,05 MW, bajo 1 MW, que la guardia publica y producción calla, en el plazo.
    mb_base = [p for p in pros if not p["protegida"] and not p["minima"] and en_plazo_instante(p)
               and (p["vrp_mirova_mw"] or 0) > UMBRAL_MINIMO_MW
               and p["prod_pub"] is not None and p["guardia_pub"] is not None and p.get("prod_via") is True]
    mb = [p for p in mb_base if calla(p) and vs._clave(p) not in juzgadas]
    muy_bajo = {"k": len(mb), "n": len(mb_base), "cota": COTA_MUY_BAJO, "dispara": len(mb) > COTA_MUY_BAJO,
                "pasadas": mb}

    # (ii) negativos limpios en que producción publica y la guardia, que miró la misma pasada, no.
    gidx = _por_volcan(guardia)
    enc_dt = _dt(encendido) if encendido else None
    vence_dt = _dt(vence_utc) if vence_utc else None
    sp, n_neg = [], 0
    for r in prod:
        if (r["b"] != SENSOR or r.get("lab") != "neg_limpio" or r.get("via") is not True or enc_dt is None
                or not (enc_dt <= r["dt"] < vence_dt)):
            continue
        g = _cerca(gidx.get(r["vol"], []), r["dt"])
        if not g:
            continue
        n_neg += 1
        if r["pub"] and not any(x["pub"] for x in g):
            clave = (r["vol"], SENSOR, r["dt"].strftime("%Y-%m-%d %H:%M"))
            if clave not in juzgadas:
                sp.append({"volcano": r["vol"], "fecha_utc": clave[2]})
    sobrepublicacion = {"k": len(sp), "n": n_neg, "cota": COTA_SOBREPUBLICACION,
                        "dispara": len(sp) > COTA_SOBREPUBLICACION, "pasadas": sp}

    # (iii) pasadas que la guardia registra y producción no, por semana ISO (sin disparo: la regla no da cota).
    pidx = _por_volcan(prod)
    semanas, sin_prod = defaultdict(int), []
    for g in guardia:
        if g["b"] != SENSOR or enc_dt is None or g["dt"] < enc_dt:
            continue
        if not _cerca(pidx.get(g["vol"], []), g["dt"]):
            iso = g["dt"].isocalendar()
            semanas[f"{iso[0]}-W{iso[1]:02d}"] += 1
            sin_prod.append({"volcano": g["vol"], "sensor": g.get("sensor"),
                             "fecha_utc": g["dt"].strftime("%Y-%m-%d %H:%M")})
    # 153 (S175): cada pasada con su nombre; el pipeline no deja rastro del descarte y la semana sola no dice cuál fue.
    borde = {"por_semana": dict(sorted(semanas.items())), "total": sum(semanas.values()), "pasadas": sin_prod,
             "nota": "pasadas que la guardia (K) registra y producción (la vía) no: el descarte de borde 171-01. "
                     "Se informa sin disparar: la regla no da cota (A115)"}

    # Nulo: antes del encendido guardia y producción (K las dos) tienen que publicar lo mismo en cada pasada pareada.
    limite = enc_dt or _dt(f"{hoy} 23:59:59")
    desde = limite - timedelta(days=DIAS_NULO)
    pares, distintas = 0, []
    for g in guardia:
        if g["b"] != SENSOR or not (desde <= g["dt"] < limite):
            continue
        p = [x for x in _cerca(pidx.get(g["vol"], []), g["dt"]) if x.get("via") is not True]
        if not p:
            continue
        pares += 1
        if bool(g["pub"]) != any(x["pub"] for x in p):
            clave = (g["vol"], SENSOR, g["dt"].strftime("%Y-%m-%d %H:%M"))
            if clave not in juzgadas:
                distintas.append({"volcano": g["vol"], "fecha_utc": clave[2], "guardia_pub": bool(g["pub"])})
    # MA172-208: 0 pares no es «coinciden», es «no medí»; evaluar() lo convierte en aviso.
    nulo = {"pares": pares, "distintas": len(distintas), "detalle": distintas, "sin_medir": pares == 0,
            "nota": "antes del encendido guardia y producción son el mismo detector K: deben publicar lo mismo (A110)"}

    # MA172-202: protegida posterior al encendido que la guardia publica y de la que producción no tiene record, pasada
    # la espera del NRT. Para el operador es silencio; la regla pre-autoriza revertir sólo «calla», así que investiga.
    limite_espera = (_dt(ahora) - timedelta(hours=ESPERA_SIN_RECORD_H)).strftime("%Y-%m-%d %H:%M:%S")
    sin_record = [p for p in pros if p["protegida"] and p["guardia_pub"] is True and p["prod_pub"] is None
                  and p["instante_utc"] <= limite_espera and vs._clave(p) not in juzgadas]

    # Protegida anterior al encendido cuyo record de producción ya es de la vía (re-escrito del NRT): investigar.
    borde_enc = [p for p in retro if p["protegida"] and calla(p) and p.get("prod_via") is True
                 and vs._clave(p) not in juzgadas]

    duracion = {"protegidas_vistas_en_guardia": len(vistas), "objetivo": PROTEGIDAS_OBJETIVO,
                "encendido": encendido, "vence": vence, "vence_utc": vence_utc,
                "cumplida": bool(encendido) and (len(vistas) >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence))}
    retrospectivo = {
        "nota": "anterior al encendido: se informa y no dispara la reversión (§4, decisión (b) de K)",
        "n_pasadas": len(retro),
        "protegidas_que_la_guardia_publica_y_prod_calla": [p for p in retro if p["protegida"] and calla(p)],
    }

    if reversion:
        veredicto = "REVERSION_CANDIDATA"
    elif fuera_de_plazo:
        veredicto = "CANDIDATA_FUERA_DE_PLAZO"
    elif muy_bajo["dispara"] or sobrepublicacion["dispara"] or distintas or borde_enc or sin_record or calladas_por_k:
        veredicto = "INVESTIGAR"
    else:
        veredicto = "VERDE"
    return {"veredicto": veredicto, "reversion": reversion, "fuera_de_plazo": fuera_de_plazo, "muy_bajo": muy_bajo,
            "protegidas_sin_record_produccion": sin_record, "espera_sin_record_h": ESPERA_SIN_RECORD_H,
            "protegidas_calladas_por_k_de_produccion": calladas_por_k,
            "sobrepublicacion": sobrepublicacion, "borde_171_01": borde, "nulo": nulo,
            "borde_del_encendido": borde_enc, "duracion": duracion, "retrospectivo": retrospectivo,
            "juzgadas": [dict(p, juicio=juzgadas[vs._clave(p)]) for p in pasadas if vs._clave(p) in juzgadas]}


def avisos_guardia(guardia, hoy):
    return vs._avisos_frescura(guardia, hoy, "la guardia (K)", "guardia-k-modis.yml", sensores=[SENSOR])


def avisos_produccion(prod, hoy):
    return vs._avisos_frescura(prod, hoy, "producción", "nrt.yml", sensores=[SENSOR])


def avisos_referencia_modis(filas, hoy):
    """MA172-204: la frescura de la referencia, medida en las filas de MODIS (RUTINA incluidas, como el auto-audit).
    vigilancia_sombra.avisos_referencia mide todas las filas: con VIIRS fresco y MODIS detenido daría VERDE sin una
    sola alerta MODIS contra qué comparar."""
    fechas = [f["fecha_utc"][:10] for f in filas
              if f.get("sensor_bucket") == SENSOR and (f.get("fecha_utc") or "")[:4].isdigit()]
    if not fechas:
        return ["la referencia de MIROVA no trae ninguna fila de MODIS: no hay contra qué vigilar la vía"]
    dias = (date.fromisoformat(hoy) - date.fromisoformat(max(fechas))).days
    if dias > aa.MAX_GT_STALE_DAYS:
        return [f"la referencia de MIROVA no registra MODIS hace {dias} días (última fila MODIS {max(fechas)}): es el "
                "scraper de Mirova-v1 o la tabla de MIROVA, no los volcanes"]
    return []


def avisos_nulo(nulo):
    """MA172-208: un nulo sin pares no mide nada y no se puede leer como guardia = producción."""
    if nulo.get("sin_medir"):
        return [f"el nulo de la guardia no tiene pasadas pareadas en los {DIAS_NULO} días previos al encendido (o a "
                "hoy): no se midió que guardia y producción publiquen lo mismo"]
    return []


def avisos_perfiles(prod, guardia, n_guardia_con_via):
    av = []
    mal_g = sum(1 for r in guardia if r.get("perfil") == PERFIL_PRODUCCION)
    mal_p = sum(1 for r in prod if r.get("perfil") == PERFIL_GUARDIA)
    if mal_g:
        av.append(f"{mal_g} records de la guardia traen el perfil {PERFIL_PRODUCCION}: no es la guardia")
    if mal_p:
        av.append(f"{mal_p} records de producción traen el perfil {PERFIL_GUARDIA}: no es producción")
    if n_guardia_con_via:
        av.append(f"{n_guardia_con_via} records de la guardia traen la marca de la vía: la guardia dejó de ser K y "
                  "nunca va a publicar algo que producción calle")
    return av


def caidas_a_k(encendido, prod):
    """Decisión 3 de S174 (S175): records MODIS de producción posteriores al encendido en que la vía cayó a K."""
    if not encendido:
        return []
    enc_dt = _dt(encendido)
    return [{"volcano": r["vol"], "sensor": r.get("sensor"), "fecha_utc": r["dt"].strftime("%Y-%m-%d %H:%M"),
             "marca": r["caida_k"]}
            for r in sorted(prod, key=lambda x: (x["dt"], x["vol"]))
            if r["b"] == SENSOR and r.get("caida_k") and r["dt"] >= enc_dt]


def avisos_via(flag, encendido, prod, vols=None):
    """El flag de producción encendido sin records de la vía, o una vía que dejó de escribir, deja guardia =
    producción y la vigilancia en VERDE sin vigilar nada.

    152 (S175): POR VOLCÁN. La vía puede morir en un volcán y no en otro (grilla de MIROVA ausente, MxD03 que no calza
    con su órbita); sumando los 11 volcanes, el que queda en K se tapa con los demás (mutaciones M2 y M2c). En cada
    volcán con records MODIS posteriores al encendido, la última noche de la vía no puede quedar más de
    MAX_DIAS_SOMBRA_SIN_DATOS días detrás de la última de producción. Un volcán sin records posteriores lo avisa la
    frescura de producción (avisos_produccion). Las caídas a K sueltas van aparte, en avisos_caidas."""
    if flag is None:
        return ["no se pudo leer ENABLE_MODIS_CODIGO_MIROVA de pipeline.profile: no se sabe si la vía está encendida"]
    if flag and encendido is None:
        return ["el flag de la vía de MODIS está encendido en producción y no hay ningún record MODIS de la vía: la "
                "vía no está escribiendo (o cae siempre a K) y guardia y producción son lo mismo"]
    if not (flag and encendido):
        return []
    av = []
    enc_dt = _dt(encendido)
    for v in vols or aa.VOLS:
        post = [r for r in prod if r["vol"] == v and r["b"] == SENSOR and r["dt"] >= enc_dt]
        if not post:
            continue
        ultima = max(r["noche"] for r in post)
        ultima_via = max((r["noche"] for r in post if r.get("via") is True), default=None)
        if ultima_via is None or (date.fromisoformat(ultima) - date.fromisoformat(ultima_via)).days \
                > vs.MAX_DIAS_SOMBRA_SIN_DATOS:
            hasta = (f"la vía sólo hasta el {ultima_via}" if ultima_via
                     else "ningún record suyo desde el encendido es de la vía")  # VPR959-04: nunca un None en la issue
            av.append(f"producción de {v} escribe MODIS hasta el {ultima} y {hasta}: en {v} la vía dejó de correr (o "
                      "cae a K) y lo que se compara con la guardia es K contra K")
    return av


def avisos_caidas(flag, encendido, prod, hoy):
    """Decisión 3 de S174: cada caída a K de los últimos DIAS_AVISO_CAIDA días es aviso. Va separado de avisos_via
    (VPR959-05): una pasada que cayó a K no deja ciega a la vigilancia en las demás, y la issue tiene que poder decirlo."""
    if not (flag and encendido):
        return []
    desde = (date.fromisoformat(hoy) - timedelta(days=DIAS_AVISO_CAIDA)).isoformat()
    recientes = [c for c in caidas_a_k(encendido, prod) if c["fecha_utc"][:10] >= desde]
    if not recientes:
        return []
    lista = ", ".join(f"{c['volcano']} {c['sensor']} {c['fecha_utc']} ({c['marca']})" for c in recientes[:10])
    return [f"{len(recientes)} records MODIS de producción de los últimos {DIAS_AVISO_CAIDA} días cayeron a K (la vía no "
            f"corrió; cuentan como K, no como la vía, decisión 3 de S174): {lista}"
            f"{' ...' if len(recientes) > 10 else ''}"]


def cargar_insumos(win, via, caidas=None):
    """Referencia, records MODIS de producción (marcados con `via` y, S175, con `caida_k`, la marca de la caída a K o
    None) y de la guardia con el predicado del tablero, y cuántos records crudos de la guardia traen la marca de la vía.
    Producción queda etiquetada por el banco (regla original; D-9 no toca MODIS)."""
    import banco_paridad as bp  # noqa: E402  (node; se carga en runtime)
    from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == SENSOR]
    for r in prod:
        clave = (r["vol"], r.get("sensor"), r["dt"].strftime("%Y-%m-%d %H:%M"))
        r["via"] = clave in via
        r["caida_k"] = (caidas or {}).get(clave)
    try:
        guardia = [r for r in bp.cargar_nuestros(coords, inner, win, data=GUARDIA) if r["b"] == SENSOR]
    except FileNotFoundError:
        guardia = []          # la guardia todavía no escribe algún volcán: la frescura lo dice volcán por volcán
    n_via = 0
    for vol in aa.VOLS:
        try:
            with open(os.path.join(GUARDIA, vol + ".json"), encoding="utf-8") as fh:
                recs = json.load(fh).get("records") or []
        except (OSError, ValueError):
            continue
        n_via += sum(1 for r in recs if "via_codigo_mirova" in r
                     and win[0] <= str(r.get("datetime_utc") or "")[:10] <= win[1])
    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win)[:3])
    return filas, prod, guardia, n_via


def evaluar(hoy):
    enc = leer_encendido()
    encendido = enc["encendido_utc"]
    flag = flag_produccion_encendido()
    h = date.fromisoformat(hoy)
    d0 = h - timedelta(days=DIAS_NULO)
    if encendido:
        d0 = min(d0, date.fromisoformat(encendido[:10]) - timedelta(days=max(DIAS_ANTES_DEL_ENCENDIDO, DIAS_NULO)))
    win = (d0.isoformat(), hoy)
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "regla": "experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §4 (en main desde el PR B #934; "
                    "hasta S173, borrador en la rama loop/activo)",
           "encendido_modis_utc": encendido, "primera_observacion_via": enc["primera_observacion"],
           "flag_produccion": flag, "ventana": list(win),
           "fase": ("antes_del_encendido" if not encendido else "vigilando")}
    filas, prod, guardia, n_via_g = cargar_insumos(win, enc["via"], enc.get("caidas"))
    pasadas = pasadas_modis(filas, prod, guardia, win, diurna=vs._diurna_por_defecto())
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if ahora[:10] != hoy:
        ahora = f"{hoy} 23:59:59"           # una corrida con `hoy` fijado (pruebas, re-lectura) mide al cierre de ese día
    d = disparadores(pasadas, prod, guardia, hoy, encendido, juzgadas=leer_juzgadas(), ahora=ahora)
    if d["duracion"]["cumplida"]:
        out["fase"] = "plazo_cumplido"
    ciegos = (vs.avisos_referencia(filas, hoy) + avisos_referencia_modis(filas, hoy) + avisos_guardia(guardia, hoy)
              + avisos_produccion(prod, hoy) + avisos_perfiles(prod, guardia, n_via_g)
              + avisos_via(flag, encendido, prod) + avisos_nulo(d["nulo"]))
    avisos = ciegos + avisos_caidas(flag, encendido, prod, hoy)
    veredicto = d["veredicto"]
    if veredicto == "VERDE" and avisos:
        veredicto = "VIGILANCIA_CIEGA"      # un aviso no tapa una reversión: sólo impide leer la falta de disparos
    out.update({"veredicto": veredicto, "avisos": avisos,
                # VPR959-05: el veredicto es el de la regla; esto sólo le dice a la issue que no ponga «no puede mirar»
                "solo_caidas_a_k": veredicto == "VIGILANCIA_CIEGA" and not ciegos,
                "guardia_desde": min((r["noche"] for r in guardia), default=None),
                "guardia_hasta": max((r["noche"] for r in guardia), default=None),
                "n_pasadas_alerta": len(pasadas),
                "n_pasadas_alerta_con_guardia": sum(1 for p in pasadas if p["guardia_pub"] is not None),
                **{k: v for k, v in d.items() if k != "veredicto"},
                "caidas_a_k": caidas_a_k(encendido, prod),
                "protegidas_sin_publicar_produccion": [p for p in pasadas if p["protegida"] and p["prod_pub"] is False]})
    return out


def imprimir(out):
    print(f"Vigilancia de la guardia K de MODIS: {out['veredicto']} · fase {out.get('fase')} · encendido "
          f"{out.get('encendido_modis_utc')} · guardia {out.get('guardia_desde')} a {out.get('guardia_hasta')}")
    for a in out.get("avisos", []):
        print("AVISO:", a)
    for p in out.get("reversion", []):
        print(f"  REVERSIÓN CANDIDATA: {p['volcano']} MODIS {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: la "
              "guardia (K) publica y producción (la vía) calla. Confirmar en la cabecera de la imagen de MIROVA antes de "
              "revertir (git revert del PR B, REGLA_REVERSION_MODD §4)")
    for p in out.get("fuera_de_plazo", []):
        print(f"  CANDIDATA FUERA DE PLAZO: {p['volcano']} MODIS {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: "
              "sin pre-autorización, decide Nicolás")
    for p in out.get("borde_del_encendido", []):
        print(f"  BORDE DEL ENCENDIDO: {p['volcano']} MODIS {p['fecha_utc']} UTC, anterior al encendido y con record "
              "de la vía: investigar")
    for p in out.get("protegidas_calladas_por_k_de_produccion", []):
        print(f"  CALLADA POR K DE PRODUCCIÓN: {p['volcano']} MODIS {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: "
              f"la guardia publica y el record de producción no es de la vía ({p.get('prod_caida_k') or 'K sin marca'}): "
              "investigar; no es candidata a reversión")
    for p in out.get("protegidas_sin_record_produccion", []):
        print(f"  SIN RECORD DE PRODUCCIÓN: {p['volcano']} MODIS {p['fecha_utc']} UTC, MIROVA {p['vrp_mirova_mw']} MW: "
              "la guardia (K) publica y producción no tiene record de la pasada (borde 171-01): investigar")
    for nombre in ("muy_bajo", "sobrepublicacion"):
        m = out.get(nombre) or {}
        if m.get("k"):
            print(f"  {nombre}: {m['k']} (cota {m['cota']}, n {m['n']}){' · DISPARA' if m['dispara'] else ''}")
    n = out.get("nulo") or {}
    print(f"  nulo (antes del encendido): {n.get('distintas')} pasadas distintas de {n.get('pares')} pareadas")
    b = out.get("borde_171_01") or {}
    if b.get("total"):
        print(f"  pasadas que la guardia registra y producción no, por semana: {b['por_semana']}")
        for x in b.get("pasadas", [])[-10:]:
            print(f"    {x['volcano']} {x['sensor']} {x['fecha_utc']} UTC")
    du = out.get("duracion") or {}
    print(f"  duración: {du.get('protegidas_vistas_en_guardia')} de {du.get('objetivo')} protegidas vistas en la "
          f"guardia desde el encendido; vence {du.get('vence')}")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Vigilancia de la guardia K de MODIS (REGLA_REVERSION_MODD §4)")
    ap.add_argument("--cons", help="CSV consolidado de Mirova-v1 (por defecto, el snapshot del repo)")
    ap.add_argument("--ocr", help="CSV OCR de Mirova-v1 (por defecto, el snapshot del repo)")
    a = ap.parse_args(argv)
    if a.cons:
        aa.CONS = a.cons
    if a.ocr:
        aa.OCR = a.ocr
    hoy = datetime.now(timezone.utc).date().isoformat()
    out = evaluar(hoy)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "guardia_modis_latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=str)
    linea = {"date": hoy, "veredicto": out["veredicto"], "fase": out.get("fase"),
             "encendido_modis_utc": out.get("encendido_modis_utc"),
             "n_reversion": len(out.get("reversion", [])), "n_fuera_de_plazo": len(out.get("fuera_de_plazo", [])),
             "n_calladas_por_k": len(out.get("protegidas_calladas_por_k_de_produccion", [])),
             "n_caidas_a_k": len(out.get("caidas_a_k", [])),
             "protegidas_vistas_en_guardia": (out.get("duracion") or {}).get("protegidas_vistas_en_guardia"),
             "muy_bajo_k": (out.get("muy_bajo") or {}).get("k"),
             "sobrepublicacion_k": (out.get("sobrepublicacion") or {}).get("k"),
             "nulo_distintas": (out.get("nulo") or {}).get("distintas"),
             "borde_171_01_total": (out.get("borde_171_01") or {}).get("total")}
    with open(os.path.join(OUTDIR, "guardia_modis_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    imprimir(out)


if __name__ == "__main__":
    main()
