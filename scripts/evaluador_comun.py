# -*- coding: utf-8 -*-
"""Evaluador común del instrumento (S162, fase 0 del programa por sensor): sirve a VIIRS 375, VIIRS 750 y MODIS.

POR QUÉ. En el A/B de D25 el 2026-10-12 a los tres brazos les faltaban 44 pasadas que producción sí tenía (una
protegida de Chillán de 8,44 MW), porque CMR no devolvió los gránulos reprocesados; el job dijo «Cobertura: completa»,
la cobertura comparó brazos entre sí y el evaluador sólo revisaba protegidas que ya tenían record en algún brazo
(`experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`). Un hueco común a todos los brazos no se ve
comparando brazos entre sí; se ve partiendo de las pasadas de MIROVA. Eso hace este módulo:

- T1, cobertura contra la referencia: cada pasada de MIROVA (`clase_mirova.resumir_pasadas`, una por pasada a
  ±120 s) se busca en cada lado (brazos y control, que suele ser producción). Es INVÁLIDO POR INSTRUMENTO, antes de
  leer ningún veredicto: (a) una protegida (lectura A) sin record en algún brazo y que el control sí tiene (basta un
  brazo: uno con menos cobertura sesga igual que un hueco común, verificador de #904); (b) un volcán, sensor y día con
  pasadas de MIROVA y cero records en un brazo; (c) una protegida que algún brazo tiene y el control no (el control no
  sirve de vara de cobertura). Los días declarados como excluidos (D-29) no cuentan y se informan.
- T2, «no observado» como estado propio: si ningún lado (ni el control) tiene record de la pasada, no se sabe si el
  volcán cayó fuera del gránulo, si la escena fue inválida (el procesador devuelve None sin dejar record,
  `pipeline/process_viirs.py`, «if not np.any(roi_mask): return None») o si hubo un hueco común con el control. Esa
  pasada sale de todos los denominadores y se cuenta aparte. Si el control la tiene y el brazo no, es
  `falta_cobertura` (cuenta contra el instrumento, no contra el detector).
- T5, P1b en las dos direcciones (cruces de 1 MW del valor publicado entre control y brazo) y publicaciones sobre
  pasadas que la tabla de MIROVA lista como RUTINA (VE162-03), que P2 no cuenta cuando otra pasada de la noche alertó.

Las pruebas viven en `tests/test_evaluador_comun_s162.py`. El placebo de ganancia y el comparador d′ (T3) van en un
PR aparte sobre este mismo módulo.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import clase_mirova as cm  # noqa: E402

TOL_S = cm.VENTANA_S
UMBRAL_P1B_MW = cm.UMBRAL_PROTEGIDA_MW
OBSERVADO, FALTA, NO_OBSERVADO = "observado", "falta_cobertura", "no_observado"
INVALIDO = "INVALIDO POR INSTRUMENTO"
COBERTURA_OK = "COBERTURA OK"


# ------------------------------------------------------------------------------------------- pareo
def indexar_records(recs):
    """(volcán, sensor) -> lista ordenada de (instante, record). Los records traen `vol`, `b` y `dt` (naive UTC)."""
    idx = collections.defaultdict(list)
    for r in recs:
        idx[(r["vol"], r["b"])].append((r["dt"].replace(tzinfo=None), r))
    for v in idx.values():
        v.sort(key=lambda x: x[0])
    return idx


def record_de(idx, p, tol_s=TOL_S):
    """El record más cercano a la pasada dentro de ±tol_s, o None."""
    lista = idx.get((p.volcano, p.sensor_bucket), [])
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, p.instante - timedelta(seconds=tol_s))
    mejor = None
    while i < len(lista) and lista[i][0] <= p.instante + timedelta(seconds=tol_s):
        d = abs((lista[i][0] - p.instante).total_seconds())
        if mejor is None or d < mejor[0]:
            mejor = (d, lista[i][1])
        i += 1
    return None if mejor is None else mejor[1]


def clave(p):
    return "%s|%s|%s" % (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d %H:%M:%S"))


def tabla_por_pasada(pasadas, recs_por_lado, control, tol_s=TOL_S):
    """Una fila por pasada de MIROVA con el record de cada lado y su estado de cobertura.

    Estado del brazo: observado (tiene record), falta_cobertura (no lo tiene y el control sí), no_observado (nadie lo
    tiene). Estado del control: observado o no_observado.
    """
    if control not in recs_por_lado:
        raise ValueError("el control %r no está entre los lados %s" % (control, sorted(recs_por_lado)))
    idx = {lado: indexar_records(recs) for lado, recs in recs_por_lado.items()}
    alertas_noche = {(p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d"))
                     for p in pasadas if p.estado == "alerta"}
    T = []
    for p in pasadas:
        rec = {lado: record_de(ix, p, tol_s) for lado, ix in idx.items()}
        hay_ctrl = rec[control] is not None
        cob = {}
        for lado, r in rec.items():
            if r is not None:
                cob[lado] = OBSERVADO
            elif lado != control and hay_ctrl:
                cob[lado] = FALTA
            else:
                cob[lado] = NO_OBSERVADO
        T.append({"pasada": p, "clave": clave(p), "dia": p.instante.strftime("%Y-%m-%d"), "rec": rec, "cob": cob,
                  "protegida": cm.es_protegida(p),
                  "noche_con_alerta": (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d")) in alertas_noche})
    return T


# ------------------------------------------------------------------------------------------- T1 y T2
def cobertura(T, recs_por_lado, control, dias_excluidos=()):
    """Fallas de cobertura contra la referencia de MIROVA y resumen por lado. Ver el docstring del módulo."""
    brazos = sorted(l for l in recs_por_lado if l != control)
    excl = set(dias_excluidos)
    con_rec = collections.defaultdict(collections.Counter)    # lado -> (vol, b, día) -> n records
    for lado, recs in recs_por_lado.items():
        for r in recs:
            con_rec[lado][(r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d"))] += 1
    protegidas_sin_record, alertas_sin_record, excluidas = [], [], []
    control_sin_protegida, control_sin_record = [], 0
    dias_mirova = collections.Counter()
    no_obs_dia = collections.Counter()
    for f in T:
        p = f["pasada"]
        dias_mirova[(p.volcano, p.sensor_bucket, f["dia"])] += 1
        if f["cob"][control] == NO_OBSERVADO and f["dia"] not in excl:
            no_obs_dia[f["dia"]] += 1
        faltan = [b for b in brazos if f["rec"][b] is None]
        tienen = [b for b in brazos if f["rec"][b] is not None]
        if f["rec"][control] is None and tienen and f["dia"] not in excl:
            # Verificador de #904, hallazgo 2: el control no cubre lo que un brazo sí; no sirve de vara de cobertura.
            if f["protegida"]:
                control_sin_protegida.append("%s (MIROVA %s MW) la tiene %s" % (f["clave"], p.vrp_mw, ", ".join(tienen)))
            else:
                control_sin_record += 1
        # Verificador de #904, hallazgo 1: basta que falte en UN brazo (un brazo con menos cobertura sesga igual).
        if not (faltan and f["rec"][control] is not None and p.estado == "alerta"):
            continue
        destino = excluidas if f["dia"] in excl else (protegidas_sin_record if f["protegida"] else alertas_sin_record)
        destino.append("%s (MIROVA %s MW) falta en %s" % (f["clave"], p.vrp_mw, ", ".join(faltan)))
    dias_vacios = []
    for (vol, b, dia), n in sorted(dias_mirova.items()):
        for lado in brazos:
            if con_rec[lado][(vol, b, dia)] == 0:
                (excluidas if dia in excl else dias_vacios).append(
                    "%s|%s|%s sin records en %s (MIROVA %d pasadas, control %d records)"
                    % (vol, b, dia, lado, n, con_rec[control][(vol, b, dia)]))
    resumen = {}
    for lado in recs_por_lado:
        c = collections.Counter(f["cob"][lado] for f in T if f["dia"] not in excl)
        resumen[lado] = {"pasadas": sum(c.values()), OBSERVADO: c[OBSERVADO], FALTA: c[FALTA],
                         NO_OBSERVADO: c[NO_OBSERVADO]}
    veredicto = INVALIDO if (protegidas_sin_record or dias_vacios or control_sin_protegida) else COBERTURA_OK
    return {"veredicto": veredicto, "protegidas_sin_record_en_brazos": protegidas_sin_record,
            "dias_con_pasadas_de_mirova_y_sin_records": dias_vacios,
            "control_sin_protegida_que_un_brazo_tiene": control_sin_protegida,
            "aviso_control_sin_record_que_un_brazo_tiene": control_sin_record,
            "aviso_alertas_no_protegidas_sin_record_en_brazos": alertas_sin_record,
            # Verificador de #904, hallazgo 3: las no observadas por día dejan ver un hueco común con el control.
            "no_observado_por_dia": dict(sorted(no_obs_dia.items(), key=lambda x: (-x[1], x[0]))),
            "en_dias_excluidos": excluidas, "por_lado": resumen}


def observada_en(f, *lados):
    """La pasada entra a un denominador sólo si todos los lados la observaron (T2)."""
    return all(f["cob"][l] == OBSERVADO for l in lados)


# ------------------------------------------------------------------------------------------- T5
def _pub(r):
    return bool(r is not None and r.get("pub"))


def _disp(r):
    return float((r or {}).get("disp") or 0.0) if _pub(r) else 0.0


def p1b(T, control, brazo, umbral=UMBRAL_P1B_MW, dias_excluidos=()):
    """Cruces de `umbral` del valor publicado, en las dos direcciones, sobre pasadas observadas por los dos lados.

    abajo: protegida A que los dos publican, el control con `umbral` o más y el brazo debajo (el de D25).
    arriba: pasada donde el brazo publica `umbral` o más y el control publica menos o no publica; se informa por
    estado de MIROVA (una protegida que sube es acercarse a MIROVA; una RUTINA o un FALSO_POSITIVO que sube es una
    publicación de clase Bajo que MIROVA no hizo).
    """
    excl = set(dias_excluidos)
    abajo, arriba = [], collections.defaultdict(list)
    for f in T:
        if f["dia"] in excl or not observada_en(f, control, brazo):
            continue
        c, b, p = f["rec"][control], f["rec"][brazo], f["pasada"]
        if f["protegida"] and _pub(c) and _pub(b) and _disp(c) >= umbral > _disp(b):
            abajo.append("%s | %s %.3f -> %s %.3f | MIROVA %s" % (f["clave"], control, _disp(c), brazo, _disp(b),
                                                                  p.vrp_mw))
        if _pub(b) and _disp(b) >= umbral > _disp(c):
            estrato = "protegida" if f["protegida"] else p.estado
            arriba[estrato].append("%s | %s %.3f -> %s %.3f | MIROVA %s %s" % (
                f["clave"], control, _disp(c), brazo, _disp(b), p.estado, p.vrp_mw))
    return {"abajo": abajo, "arriba": dict(arriba)}


def publicaciones_sobre_rutina(T, lados, dias_excluidos=()):
    """Por lado: pasadas que la TABLA de MIROVA lista como RUTINA (fuente CONS) y el lado publica, separadas por si
    otra pasada del mismo volcán, sensor y día alertó (las que P2 no cuenta, VE162-03). Sólo pasadas observadas por
    todos los lados (T2)."""
    excl = set(dias_excluidos)
    out = {}
    base = [f for f in T if f["dia"] not in excl and f["pasada"].estado == "rutina" and f["pasada"].fuente == "CONS"
            and observada_en(f, *lados)]
    for lado in lados:
        con = [f["clave"] for f in base if _pub(f["rec"][lado]) and f["noche_con_alerta"]]
        sin = [f["clave"] for f in base if _pub(f["rec"][lado]) and not f["noche_con_alerta"]]
        out[lado] = {"rutinas_observadas": len(base), "publica_en_noche_con_alerta": con,
                     "publica_en_noche_sin_alerta": sin}
    return out


# ------------------------------------------------------------------------------------------- carga real
def cargar_lado(directorio, ventana, sensores, coords, inner):
    """Records nocturnos de un directorio de JSON por volcán, con el predicado del tablero (node) de banco_paridad.

    A diferencia de `banco_paridad.cargar_nuestros`, un volcán sin archivo no hace caer la carga: se informa (un
    brazo sin el JSON de un volcán es en sí una falla de cobertura, que verá `cobertura`)."""
    import banco_paridad as bp
    recs, casos, faltan = [], [], []
    for vol in bp.VOLS:
        ruta = Path(directorio) / ("%s.json" % vol)
        if not ruta.exists():
            faltan.append(vol)
            continue
        for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b not in sensores or not (ventana[0] <= t[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=__import__("datetime").timezone.utc)):
                continue
            recs.append({"vol": vol, "b": b, "dt": dt, "sensor": r.get("sensor")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs, faltan


def pasadas_nocturnas(ref, ventana, sensores, coords, canal, regla_minimas):
    import banco_paridad as bp
    from datetime import timezone
    out = []
    for p in cm.resumir_pasadas(ref, canal=canal, regla_minimas=regla_minimas):
        dia = p.instante.strftime("%Y-%m-%d")
        if p.sensor_bucket not in sensores or not (ventana[0] <= dia <= ventana[1]) or p.volcano not in coords:
            continue
        lat, lon = coords[p.volcano]
        if bp.es_pasada_diurna_descartada(p.sensor_bucket, lat, lon, p.instante.replace(tzinfo=timezone.utc)):
            continue
        out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evaluador común: cobertura contra MIROVA, no observado, P1b, RUTINA")
    ap.add_argument("--lado", action="append", required=True, help="NOMBRE=DIRECTORIO (repetible; brazos y control)")
    ap.add_argument("--control", required=True, help="nombre del lado control (p. ej. produccion)")
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--sensores", default="VIIRS375,VIIRS750,MODIS")
    ap.add_argument("--ref", required=True, help="carpeta congelada con registro_vrp_consolidado.csv, registro_vrp_ocr.csv,"
                                                  " consolidado_filas_perdidas.csv y respaldo_20260408.csv")
    ap.add_argument("--canal", default="union", choices=cm.CANALES)
    ap.add_argument("--regla-minimas", default=cm.MODO_MINIMAS, choices=cm.MODOS_MINIMAS)
    ap.add_argument("--excluir-dias", default="", help="días UTC separados por coma (D-29)")
    ap.add_argument("--salida", help="JSON de salida")
    a = ap.parse_args(argv)
    import banco_paridad as bp
    from referencia_mirova_unificada import cargar_referencia_unificada
    ref_dir = Path(a.ref)
    opc = lambda n: (ref_dir / n) if (ref_dir / n).exists() else None  # noqa: E731
    ref = cargar_referencia_unificada(ref_dir / "registro_vrp_consolidado.csv", ref_dir / "registro_vrp_ocr.csv",
                                      respaldo_path=opc("respaldo_20260408.csv"),
                                      historico_path=opc("consolidado_filas_perdidas.csv"))
    sensores = tuple(s for s in a.sensores.split(",") if s)
    ventana = (a.desde, a.hasta)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    lados = dict(x.split("=", 1) for x in a.lado)
    recs, faltan = {}, {}
    for nombre, d in lados.items():
        recs[nombre], faltan[nombre] = cargar_lado(d, ventana, sensores, coords, inner)
    pasadas = pasadas_nocturnas(ref, ventana, sensores, coords, a.canal, a.regla_minimas)
    excl = tuple(x for x in a.excluir_dias.split(",") if x)
    T = tabla_por_pasada(pasadas, recs, a.control)
    brazos = [l for l in lados if l != a.control]
    res = {"ventana": ventana, "sensores": sensores, "canal": a.canal, "regla_minimas": a.regla_minimas,
           "dias_excluidos": excl, "volcanes_sin_archivo": faltan, "pasadas_mirova": len(pasadas),
           "cobertura": cobertura(T, recs, a.control, excl),
           "p1b": {b: p1b(T, a.control, b, dias_excluidos=excl) for b in brazos},
           "rutina": publicaciones_sobre_rutina(T, list(lados), excl)}
    if any(faltan.values()) and res["cobertura"]["veredicto"] == COBERTURA_OK:
        res["cobertura"]["veredicto"] = INVALIDO
    c = res["cobertura"]
    print("COBERTURA CONTRA MIROVA:", c["veredicto"])
    print("  protegidas sin record en algún brazo que el control tiene:", len(c["protegidas_sin_record_en_brazos"]))
    for x in c["protegidas_sin_record_en_brazos"][:20]:
        print("    ", x)
    print("  volcán-sensor-día con pasadas de MIROVA y sin records en un brazo:",
          len(c["dias_con_pasadas_de_mirova_y_sin_records"]))
    for x in c["dias_con_pasadas_de_mirova_y_sin_records"][:20]:
        print("    ", x)
    print("  protegidas que algún brazo tiene y el control no:", len(c["control_sin_protegida_que_un_brazo_tiene"]))
    for x in c["control_sin_protegida_que_un_brazo_tiene"][:20]:
        print("    ", x)
    print("  aviso: pasadas que algún brazo tiene y el control no:", c["aviso_control_sin_record_que_un_brazo_tiene"])
    print("  no observadas por día (las 5 más):", list(c["no_observado_por_dia"].items())[:5])
    print("  aviso: alertas no protegidas sin record en algún brazo que el control tiene:",
          len(c["aviso_alertas_no_protegidas_sin_record_en_brazos"]))
    print("  en días excluidos (no cuentan):", len(c["en_dias_excluidos"]))
    print("  volcanes sin archivo:", {k: v for k, v in faltan.items() if v})
    for lado, r in c["por_lado"].items():
        print("  %-12s %s" % (lado, r))
    for b, r in res["p1b"].items():
        print("P1b %s: abajo %d, arriba %s" % (b, len(r["abajo"]), {k: len(v) for k, v in r["arriba"].items()}))
    for lado, r in res["rutina"].items():
        print("RUTINA %s: de %d observadas, publica %d en noche con alerta y %d en noche sin alerta" % (
            lado, r["rutinas_observadas"], len(r["publica_en_noche_con_alerta"]), len(r["publica_en_noche_sin_alerta"])))
    if a.salida:
        Path(a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if c["veredicto"] == COBERTURA_OK else 2


if __name__ == "__main__":
    sys.exit(main())
