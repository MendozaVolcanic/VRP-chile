# -*- coding: utf-8 -*-
"""Sustrato del A/B diurno de VIIRS sobre K (tarea 1.32, D-10, issue #813), con las clases del criterio de victoria.

POR QUÉ. El pre-registro (PREREGISTRO.md de esta carpeta) decide con el criterio de victoria de la réplica
(docs/MISSION.md): ninguna alerta protegida perdida y, bajo 1 MW, una alerta perdida pesa lo mismo que una publicación
de más en un negativo limpio. Antes de fijar la regla hay que saber cuántas pasadas de cada clase caben en cada
ventana: un A/B sin sustrato no mide nada (S130) y un umbral que no sale de los datos es un gusto (A115). Este script
cuenta, sobre la referencia congelada de MIROVA, con la MISMA regla día/noche del pipeline
(`pipeline.store._solar_elevation` > 0 sobre las coordenadas del volcán) y la MISMA partición en pasadas del
evaluador común (`clase_mirova.resumir_pasadas`, ±120 s, regla de mínimas SN de D-9):

  * protegida: pasada diurna VIIRS con alerta de 1 MW o más (lectura A, D-4);
  * alerta_mb: pasada diurna VIIRS con alerta bajo 1 MW (con SN, las de 0,05 MW o menos de VIIRS 375 ya son RUTINA);
  * negativo: pasada diurna de la TABLA (CONS), RUTINA, en un volcán, sensor y día UTC sin ninguna alerta ni
    FALSO_POSITIVO DIURNO de MIROVA (la definición de `evaluador_comun.clase_p2`, mirada por periodo: verificador V2);
  * otra: el resto (FALSO_POSITIVO, RUTINA en un día con alerta o FALSO_POSITIVO diurno, sólo OCR sin alerta, sin
    geometría).

Además mide la vara de cobertura que el evaluador usa para el día (el control no tiene records diurnos, así que no
sirve de vara): la fracción de pasadas NOCTURNAS de MIROVA sin record en producción (`data/mirova_equivalent/`), por
sensor y tramo, que es la tasa natural de «MIROVA lista la pasada y nosotros no tenemos record».

Controles (A110), que pueden fallar y hacen salir con error: (C1) la regla día/noche sobre dos pasadas con respuesta
conocida; (C2) la partición es exhaustiva (las cuatro clases suman las pasadas diurnas); (C3) el pareo con producción
encuentra el record de una pasada nocturna conocida.

Uso:  python -I experiments/_s163_diurno_k/congelar_referencia.py --commit 047bd5692 --salida <REF> --sin-comprobar
      python -I experiments/_s163_diurno_k/sustrato_k.py --ref <REF> --commit-ref 047bd5692 > experiments/_s163_diurno_k/sustrato_k_salida.txt
La referencia sale del COMMIT (git show), no del árbol: en Windows el árbol tiene fines de línea CRLF y sus sha256 no
serían los del blob que extrae el evaluador.
Salida: sustrato_k.json (cuentas, sha256 de cada CSV de la referencia y commit), que el evaluador exige reproducir.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import clase_mirova as cm  # noqa: E402

# Ventanas del pre-registro (§3): las mismas W1 a W6 del A/B sobre C0, para que los dos resultados se puedan leer lado a
# lado. W1 es anterior a abril (A119: la tasa por pasada de VIIRS no se suma) y se informa aparte. No hay W7: la tabla
# de MIROVA del árbol se corta el 2026-10-19 y el 12 y el 13 de octubre tiene huecos (D-39, sesión de Mirova-v1).
VENTANAS = [
    ("W1", "2026-03-01", "2026-03-20", ("Lascar",)),
    ("W2", "2026-06-13", "2026-06-30", None),
    ("W3", "2026-07-20", "2026-07-31", None),
    ("W4", "2026-08-13", "2026-08-31", None),
    ("W5", "2026-09-01", "2026-09-20", None),
    ("W6", "2026-10-01", "2026-10-14", None),
]
DECIDEN = ("W2", "W3", "W4", "W5", "W6")
SENSORES = ("VIIRS375", "VIIRS750")
ARCHIVOS_REF = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv", "consolidado_filas_perdidas.csv",
                "respaldo_20260408.csv")
ORIGEN_REF = {
    "registro_vrp_consolidado.csv": "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv",
    "registro_vrp_ocr.csv": "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
    "consolidado_filas_perdidas.csv": "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv",
    "respaldo_20260408.csv": "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
}


def es_dia(lat, lon, instante):
    """La regla del pipeline (store._solar_elevation > 0), sobre la hora de la pasada en UTC."""
    from pipeline.store import _solar_elevation
    return _solar_elevation(lat, lon, instante.replace(tzinfo=None)) > 0


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cargar_ref(ref_dir):
    """Referencia desde una carpeta congelada con los 4 CSV (nombres de ARCHIVOS_REF)."""
    from referencia_mirova_unificada import cargar_referencia_unificada
    ref_dir = Path(ref_dir)
    return cargar_referencia_unificada(ref_dir / "registro_vrp_consolidado.csv", ref_dir / "registro_vrp_ocr.csv",
                                       respaldo_path=ref_dir / "respaldo_20260408.csv",
                                       historico_path=ref_dir / "consolidado_filas_perdidas.csv")


def cargar_ref_arbol():
    """Referencia desde las rutas del árbol de trabajo (ORIGEN_REF)."""
    from referencia_mirova_unificada import cargar_referencia_unificada
    r = {n: ROOT / ORIGEN_REF[n] for n in ARCHIVOS_REF}
    return cargar_referencia_unificada(r["registro_vrp_consolidado.csv"], r["registro_vrp_ocr.csv"],
                                       respaldo_path=r["respaldo_20260408.csv"],
                                       historico_path=r["consolidado_filas_perdidas.csv"])


def clasificar(pasadas, coords):
    """(pasada, es_dia, clase). «Día con alerta» y «día con FALSO_POSITIVO» se miran por PERIODO, igual que el
    evaluador (`evaluar_diurno_k.banderas_por_periodo`, verificador V2 y V7): una pasada diurna sólo mira las diurnas
    de su volcán, sensor y día UTC, y una nocturna sólo las nocturnas."""
    marcadas = []
    for p in pasadas:
        if p.volcano not in coords:
            continue
        lat, lon = coords[p.volcano]
        marcadas.append((p, es_dia(lat, lon, p.instante)))
    k = lambda p, d: (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d"), d)  # noqa: E731
    alerta_dia = {k(p, d) for p, d in marcadas if p.estado == "alerta"}
    fp_dia = {k(p, d) for p, d in marcadas if p.estado == "fp"}
    out = []
    for p, dia in marcadas:
        if p.estado == "alerta":
            c = "protegida" if cm.es_protegida(p) else "alerta_mb"
        elif p.estado == "rutina" and p.fuente == "CONS" and k(p, dia) not in alerta_dia and k(p, dia) not in fp_dia:
            c = "negativo"
        else:
            c = "otra"
        out.append((p, dia, c))
    return out


def contar(clasif, ventana, vols):
    _, desde, hasta, _ = ventana
    cuenta = {s: collections.Counter() for s in SENSORES}
    bloques = {s: collections.defaultdict(set) for s in SENSORES}
    for p, dia, c in clasif:
        d = p.instante.strftime("%Y-%m-%d")
        if not dia or p.sensor_bucket not in SENSORES or not (desde <= d <= hasta):
            continue
        if vols and p.volcano not in vols:
            continue
        cuenta[p.sensor_bucket][c] += 1
        cuenta[p.sensor_bucket]["diurnas"] += 1
        bloques[p.sensor_bucket][c].add("%s|%s" % (p.volcano, d))
    return ({s: dict(cuenta[s]) for s in SENSORES},
            {s: {c: len(b) for c, b in bloques[s].items()} for s in SENSORES})


def produccion_nocturna(clasif, ventanas, coords):
    """Fracción de pasadas NOCTURNAS VIIRS de MIROVA sin record de producción a ±120 s, por sensor (vara del día)."""
    import banco_paridad as bp
    idx = collections.defaultdict(list)
    for vol in bp.VOLS:
        ruta = ROOT / "data" / "mirova_equivalent" / ("%s.json" % vol)
        if not ruta.exists():
            continue
        for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b not in SENSORES:
                continue
            try:
                idx[(vol, b)].append(datetime.strptime(t, "%Y-%m-%d %H:%M"))
            except ValueError:
                continue
    for v in idx.values():
        v.sort()
    import bisect
    res = {}
    for s in SENSORES:
        tot = sin = 0
        ejemplo = None
        for p, dia, _ in clasif:
            d = p.instante.strftime("%Y-%m-%d")
            if dia or p.sensor_bucket != s or not any(w[0] in DECIDEN and w[1] <= d <= w[2] for w in ventanas):
                continue
            ts = idx.get((p.volcano, s), [])
            t = p.instante.replace(tzinfo=None)
            i = bisect.bisect_left(ts, t - timedelta(seconds=cm.VENTANA_S))
            hay = i < len(ts) and ts[i] <= t + timedelta(seconds=cm.VENTANA_S)
            tot += 1
            sin += 0 if hay else 1
            if hay and ejemplo is None:
                ejemplo = (p.volcano, s, t.strftime("%Y-%m-%d %H:%M"))
        res[s] = {"pasadas_nocturnas": tot, "sin_record_produccion": sin, "ejemplo_con_record": ejemplo}
    return res


def controles(coords):
    prob = []
    lat, lon = coords["Lascar"]
    # C1: la pasada diurna de A76 (Láscar 2026-06-15 17:24 UTC, mediodía) y una nocturna (05:00 UTC) del mismo día.
    if not es_dia(lat, lon, datetime(2026, 6, 15, 17, 24)):
        prob.append("C1: Láscar 2026-06-15 17:24 UTC tendría que ser día")
    if es_dia(lat, lon, datetime(2026, 6, 15, 5, 0)):
        prob.append("C1: Láscar 2026-06-15 05:00 UTC tendría que ser noche")
    return prob


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=None, help="carpeta con los 4 CSV extraídos de un commit (congelar_referencia.py)")
    ap.add_argument("--commit-ref", default=None, help="commit del que se extrajo --ref (se guarda en el json)")
    ap.add_argument("--salida", default=str(AQUI / "sustrato_k.json"))
    a = ap.parse_args(argv)
    import banco_paridad as bp
    coords = bp._coords_por_volcan()
    prob = controles(coords)
    if a.ref:
        ref_dir = Path(a.ref)
        rutas = {n: ref_dir / n for n in ARCHIVOS_REF}
    else:
        rutas = {n: ROOT / ORIGEN_REF[n] for n in ARCHIVOS_REF}
        ref_dir = None
    from referencia_mirova_unificada import cargar_referencia_unificada
    filas = cargar_referencia_unificada(rutas["registro_vrp_consolidado.csv"], rutas["registro_vrp_ocr.csv"],
                                        respaldo_path=rutas["respaldo_20260408.csv"],
                                        historico_path=rutas["consolidado_filas_perdidas.csv"])
    print("referencia: %d filas, %s a %s" % (len(filas), min(f["fecha_utc"] for f in filas),
                                            max(f["fecha_utc"] for f in filas)))
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                                check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        commit = None
    if a.ref and not a.commit_ref:
        print("con --ref hace falta --commit-ref")
        return 2
    out = {"commit_arbol": commit, "commit_referencia": a.commit_ref if a.ref else "ARBOL (no congelada)", "sha256": {n: sha256(r) for n, r in rutas.items()}, "ventanas": {},
           "canales": {}}
    for canal in ("union", "tabla"):
        pas = cm.resumir_pasadas(filas, canal=canal, regla_minimas=cm.MODO_MINIMAS)
        clasif = clasificar(pas, coords)
        n_dia = sum(1 for _, d, _ in clasif if d)
        print("\n=== canal %s: %d pasadas, %d diurnas (todos los sensores)" % (canal, len(clasif), n_dia))
        ventanas_out = {}
        for w in VENTANAS:
            cuenta, bloques = contar(clasif, w, w[3])
            ventanas_out[w[0]] = {"desde": w[1], "hasta": w[2], "volcanes": list(w[3]) if w[3] else "11 Tier A",
                                  "cuenta": cuenta, "bloques": bloques,
                                  "etiqueta_que_decide_A119": _etiqueta(w[1])}
            for s in SENSORES:
                c = cuenta[s]
                if sum(c.get(k, 0) for k in ("protegida", "alerta_mb", "negativo", "otra")) != c.get("diurnas", 0):
                    prob.append("C2: %s %s %s: las clases no suman las diurnas" % (canal, w[0], s))
                print("%s %-8s %s a %s | diurnas %5d | protegidas %3d | alerta_mb %3d | negativos %5d (%4d bloques) "
                      "| otra %4d" % (w[0], s, w[1], w[2], c.get("diurnas", 0), c.get("protegida", 0),
                                      c.get("alerta_mb", 0), c.get("negativo", 0),
                                      bloques[s].get("negativo", 0), c.get("otra", 0)))
        tot = {s: collections.Counter() for s in SENSORES}
        for w in DECIDEN:
            for s in SENSORES:
                tot[s].update(ventanas_out[w]["cuenta"][s])
        print("Total W2 a W6:", {s: dict(tot[s]) for s in SENSORES})
        out["canales"][canal] = {"ventanas": ventanas_out, "total_que_decide": {s: dict(tot[s]) for s in SENSORES}}
        if canal == "union":
            noct = produccion_nocturna(clasif, VENTANAS, coords)
            for s, r in noct.items():
                if r["ejemplo_con_record"] is None:
                    prob.append("C3: %s: el pareo con producción no encontró ningún record nocturno" % s)
                print("vara de cobertura %s: %d de %d pasadas nocturnas de MIROVA (W2 a W6) sin record de producción"
                      % (s, r["sin_record_produccion"], r["pasadas_nocturnas"]))
            out["vara_cobertura_nocturna_produccion"] = noct
            # Lista de positivos diurnos (protegidas) de W2 a W6, para que el evaluador los encuentre uno a uno.
            out["protegidas_diurnas"] = sorted(
                "%s|%s|%s|%s|%s" % (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d %H:%M:%S"), p.fuente,
                                    p.vrp_mw)
                for p, dia, c in clasif if dia and c == "protegida" and p.sensor_bucket in SENSORES
                and any(w[0] in DECIDEN and w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in VENTANAS))
    out["ventanas_def"] = [list(w[:3]) + [list(w[3]) if w[3] else None] for w in VENTANAS]
    if prob:
        print("\nCONTROLES FALLIDOS:")
        for x in prob:
            print("  ", x)
        return 1
    print("\ncontroles C1, C2, C3: OK")
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


def _etiqueta(desde):
    try:
        import calidad_referencia_mirova as crm
        return crm.etiqueta_que_decide(desde)
    except Exception as e:  # noqa: BLE001
        return "SIN DATO (%s)" % e


if __name__ == "__main__":
    sys.exit(main())
