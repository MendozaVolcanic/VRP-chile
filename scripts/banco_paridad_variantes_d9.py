# -*- coding: utf-8 -*-
"""Banco de paridad con todas las variantes de la regla D-9 (F7-318 de la auditoría Codex ronda 2, R3F9-107 ronda 3).

POR QUÉ. El scraper de Mirova-v1 llama ALERTA a todo VRP mayor que cero, pero en VIIRS 375 el banner de MIROVA dice
NONE en las pasadas de 0,04 MW o menos y VERY LOW desde 0,06; 0,05 exacto sale de los dos lados. La regla D-9
(`docs/MISSION.md`, regla 5 del criterio de victoria, issue #811) decide SN: una pasada de VIIRS 375 cuyas alertas son
todas de 0,05 MW o menos cuenta como «MIROVA no vio nada». Como Nicolás pidió probar todas las opciones, D-9 exige que
cada evaluación informe además SE (estrato aparte), la regla original y la variante con umbral 0,04, y diga si algo
cambia. `scripts/banco_paridad.py` sólo corre SN (`MODO_MINIMAS`). Lo que está en juego: la regla mueve el costo
contado en negativos limpios de VIIRS 375 (cuántas noches «MIROVA no vio nada» y cuántas publicamos ahí), y por
construcción no toca ninguna alerta protegida (1 MW o más); este script lo muestra con los conteos, no lo supone.

POR QUÉ UN ARCHIVO APARTE. `scripts/banco_paridad.py` está en el manifiesto del candado de la retrospectiva
(`experiments/_s172_retro_paquete/leer_retro.py`, REQUERIDOS_MANIFIESTO; §11 de PREREGISTRO_RETRO_PAQUETE.md): cambiar
sus bytes deja el candado en rojo. Este script lo importa y reusa sin copiar su etiquetador (`indexar_referencia`,
`etiquetar`, `alertas_sin_record`, `metricas`) y su carga de records con el predicado del tablero ejecutado en node.

QUÉ ENTREGA. Por variante y por sensor, en la pasada y en la noche de volcán: positivos y cuántos publicamos,
negativos limpios y cuántos publicamos, estrato «minima» (SE), y las protegidas de la referencia (pasadas, con record
nuestro, publicadas). Además la diferencia de cada variante contra la decidida y si las protegidas son iguales en todas.
Con `--anexar-a` agrega la sección `variantes_d9` al JSON que escribió el banco, sólo si la variante decidida
reproduce exactamente las métricas por sensor del banco (misma ventana): si no coinciden, no anexa y sale con error.

LAS DOS PREGUNTAS DEL INSTRUMENTO. P1 (si lo medido estuviera roto, lo vería): la variante decidida tiene que dar las
mismas métricas que el banco (control al anexar; prueba `test_la_decidida_es_la_regla_del_banco`). P2 (instrumento
muerto): sobre un caso sintético cada variante da conteos distintos y conocidos
(`tests/test_banco_paridad_variantes_d9_s198.py`).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402

# Las cinco lecturas que pide D-9, armadas desde las constantes de la regla (clase_mirova), no escritas aparte.
# La regla original no depende del umbral, así que va una sola vez.
_SUF = {cm.UMBRAL_MINIMA_MW: "005", cm.UMBRAL_MINIMA_VARIANTE_MW: "004"}
VARIANTES_D9 = ((f"{cm.MODO_MINIMAS}_{_SUF[cm.UMBRAL_MINIMA_MW]}", cm.MODO_MINIMAS, cm.UMBRAL_MINIMA_MW),
                (f"SE_{_SUF[cm.UMBRAL_MINIMA_MW]}", "SE", cm.UMBRAL_MINIMA_MW),
                ("original", "original", cm.UMBRAL_MINIMA_MW),
                (f"SN_{_SUF[cm.UMBRAL_MINIMA_VARIANTE_MW]}", "SN", cm.UMBRAL_MINIMA_VARIANTE_MW),
                (f"SE_{_SUF[cm.UMBRAL_MINIMA_VARIANTE_MW]}", "SE", cm.UMBRAL_MINIMA_VARIANTE_MW))
VARIANTE_DECIDIDA = VARIANTES_D9[0][0]
SENSORES = bp.BUCKETS + ["CUALQUIERA"]
CAMPOS_DIFERENCIA = ("n_pos", "pos_publicados", "n_neg_limpio", "neg_limpio_publicados", "n_minima")


def _protegidas(por_vb, recs):
    """Pasadas protegidas de la referencia (lectura A, 1 MW o más) en la ventana nocturna, cuántas tienen record
    nuestro a ±VENTANA_S y cuántas de esas publicamos. Si D-9 tocara una protegida, estos tres números cambiarían
    entre variantes."""
    claves = {cm.clave_pasada(f) for lista in por_vb.values() for _, f in lista if cm.alerta_protegida(f)}
    con_record, publicadas = set(), set()
    for r in recs:
        for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]):
            if cm.alerta_protegida(f):
                k = cm.clave_pasada(f)
                con_record.add(k)
                if r["pub"]:
                    publicadas.add(k)
    return {"pasadas_ref": len(claves), "con_record": len(con_record), "publicadas": len(publicadas)}


def _por_sensor(recs, sin_record):
    out = {}
    for b in SENSORES:
        filtro = bp._filtro(b=None if b == "CUALQUIERA" else b)
        pasada, noche = bp.metricas(recs, sin_record, filtro)
        sel = [r for r in recs if filtro(r)]
        c = collections.Counter(r["lab"] for r in sel)
        pub = collections.Counter(r["lab"] for r in sel if r["pub"])
        pasada = dict(pasada, pos_publicados=pub["pos"], neg_limpio_publicados=pub["neg_limpio"],
                      n_minima=c["minima"], minima_publicados=pub["minima"])
        out[b] = {"pasada": pasada, "noche_volcan": noche}
    return out


def medir_variantes(filas, recs_base, coords, ventana):
    """Etiqueta los mismos records con cada variante de D-9 y mide. `recs_base` ya trae `pub` (predicado del
    tablero); no se mutan ni las filas ni los records de entrada."""
    variantes = {}
    for nombre, modo, umbral in VARIANTES_D9:
        por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(
            filas, coords, ventana, regla_minimas=modo, umbral_minima_mw=umbral)
        recs = [dict(r) for r in recs_base]
        bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        sin_record = bp.alertas_sin_record(por_vb, recs)
        tocadas = cm.aplicar_regla_minimas(filas, modo, umbral).minimas
        variantes[nombre] = {
            "modo": modo, "umbral_minima_mw": umbral, "n_filas_ref_nocturnas": n_ref,
            "pasadas_minimas_en_ventana": sum(1 for k in tocadas if ventana[0] <= k[2][:10] <= ventana[1]),
            "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
            "protegidas": _protegidas(por_vb, recs),
            "por_sensor": _por_sensor(recs, sin_record)}
    base = variantes[VARIANTE_DECIDIDA]["por_sensor"]
    diferencia = {n: {b: {k: v["por_sensor"][b]["pasada"][k] - base[b]["pasada"][k] for k in CAMPOS_DIFERENCIA}
                      for b in SENSORES} for n, v in variantes.items()}
    protegidas = {json.dumps(v["protegidas"], sort_keys=True) for v in variantes.values()}
    return {"variante_decidida": VARIANTE_DECIDIDA, "variantes": variantes,
            "diferencia_contra_decidida": diferencia, "protegidas_iguales_en_todas": len(protegidas) == 1}


def anexar_al_banco(banco, medido, ventana=None):
    """Agrega `variantes_d9` al JSON del banco sólo si la variante decidida reproduce sus métricas por sensor (cada
    campo que el banco publica, en la pasada y en la noche de volcán) y la ventana es la misma. Si no, ValueError:
    anexar números de otra corrida a la salida del banco sería mezclar dos instrumentos."""
    if ventana is not None and list(banco["meta"]["ventana"]) != list(ventana):
        raise ValueError(f"ventana del banco {banco['meta']['ventana']} distinta de la medida {list(ventana)}")
    nuestro = medido["variantes"][VARIANTE_DECIDIDA]["por_sensor"]
    distintos = []
    for b, unidades in banco.get("por_sensor", {}).items():
        for u, campos in unidades.items():
            mio = nuestro.get(b, {}).get(u, {})
            distintos += [f"{b}.{u}.{k}" for k, v in campos.items() if mio.get(k) != v]
    if distintos or not banco.get("por_sensor"):
        raise ValueError("la variante decidida no reproduce al banco: " + (", ".join(distintos) or "banco sin por_sensor"))
    out = dict(banco)
    out["variantes_d9"] = dict(medido, coincide_con_banco=True)
    return out


def _referencia(a):
    """La misma carga de referencia que `banco_paridad.main` (snapshot del repo o remoto de Mirova-v1)."""
    if a.snapshot:
        cons, ocr = bp.SNAP_CONS, bp.SNAP_OCR
        procedencia = {"fuente": "snapshot", "sha_cons": bp.sha_git(bp.SNAP_CONS), "sha_ocr": bp.sha_git(bp.SNAP_OCR)}
    else:
        info = bp.bajar_remoto(Path(a.dest))
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
        procedencia = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                       "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    procedencia["sha_respaldo_20260408"] = bp.sha_git(bp.RESPALDO_20260408)
    procedencia["sha_union_historica"] = bp.sha_git(bp.HISTORICO_RECUPERADAS)
    return bp.cargar_referencia_unificada(cons, ocr), procedencia


def _imprimir(medido):
    print(f"variante decidida {medido['variante_decidida']} | protegidas iguales en todas: "
          f"{medido['protegidas_iguales_en_todas']}")
    for nombre, v in medido["variantes"].items():
        print(f"[{nombre}] modo {v['modo']} umbral {v['umbral_minima_mw']} | pasadas minimas en ventana "
              f"{v['pasadas_minimas_en_ventana']} | protegidas {v['protegidas']} | etiquetas {v['etiquetas']}")
        for b in SENSORES:
            p, n = v["por_sensor"][b]["pasada"], v["por_sensor"][b]["noche_volcan"]
            d = medido["diferencia_contra_decidida"][nombre][b]
            print(f"  {b:10s} pasada: pos {p['pos_publicados']}/{p['n_pos']} (recall {p['recall_pos']}) "
                  f"neg_limpio {p['neg_limpio_publicados']}/{p['n_neg_limpio']} (tasa {p['tasa_pub_neg']}) "
                  f"minima {p['minima_publicados']}/{p['n_minima']} | noche: recall {n['recall_pos']} (n {n['n_pos']}) "
                  f"pub_neg {n['tasa_pub_neg']} (n {n['n_neg']}) | contra {medido['variante_decidida']}: {d}")


def main(argv=None):
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", action="store_true", help="referencia desde el snapshot del repo (sin red)")
    ap.add_argument("--inicio", default=bp.INICIO_DEFECTO)
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--dest", default=str(ROOT / "experiments" / "_s140" / "_dl_referencia"))
    ap.add_argument("--out", default=str(ROOT / "experiments" / "_s140" / "banco_paridad_variantes_d9_out.json"))
    ap.add_argument("--anexar-a", default=None,
                    help="JSON que escribió banco_paridad.py: le agrega la sección variantes_d9 si la decidida coincide")
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    filas, procedencia = _referencia(a)
    coords = bp._coords_por_volcan()
    recs = bp.cargar_nuestros(coords, bp.inner_desde_html(), ventana, excluir_escenas_invalidas=True)
    medido = medir_variantes(filas, recs, coords, ventana)
    salida = {"meta": {"ventana": list(ventana), "referencia": procedencia, "sha_index_html": bp.sha_git(bp.HTML),
                       "sha_banco_paridad": bp.sha_git(ROOT / "scripts" / "banco_paridad.py"),
                       "n_records_nocturnos": len(recs), "regla": "docs/MISSION.md, regla 5 (D-9, issue #811)",
                       "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "segundos": round(time.time() - t0, 1)},
              **medido}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(procedencia, ensure_ascii=False))
    print(f"ventana {ventana[0]} a {ventana[1]} | records nocturnos {len(recs)}")
    _imprimir(medido)
    if a.anexar_a:
        banco = json.loads(Path(a.anexar_a).read_text(encoding="utf-8"))
        try:
            banco = anexar_al_banco(banco, medido, ventana)
        except ValueError as e:
            print(f"NO ANEXADO a {a.anexar_a}: {e}")
            return 1
        Path(a.anexar_a).write_text(json.dumps(banco, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"anexado variantes_d9 a {a.anexar_a} (la decidida reproduce al banco)")
    print(f"listo en {salida['meta']['segundos']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
