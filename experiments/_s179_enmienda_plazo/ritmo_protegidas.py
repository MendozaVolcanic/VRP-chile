"""S179: ¿cuándo se cierra el plazo de la reversión pre-autorizada con cada forma de contar las protegidas?

POR QUÉ: las reglas de reversión de MODIS (§4.6) y de VIIRS (D3, §4.6) cierran la pre-autorización al juntar 29
protegidas (alertas de MIROVA de 1 MW o más con record nuestro) o a los 120 días. La auditoría S179 (451, 401, DEC-12)
confirmó que con Chillán en erupción las 29 llegan en 11 a 18 días y casi todas de un volcán. Antes de proponer una
enmienda hay que saber qué haría cada alternativa en un régimen cualquiera, no sólo en esta erupción: se simula un
encendido en cada día de la ventana y se mide cuántos días tarda en cerrarse el plazo y con cuántos volcanes.

Formas de contar (todas con el tope de 120 días):
  actual   : cada pasada protegida cuenta 1 (lo sellado).
  tope10   : como la actual, pero cada volcán aporta como máximo 10 (29 obliga a 3 volcanes o más).
  noche    : una por noche de volcán (varias pasadas de la misma noche y volcán cuentan 1).
  noche10  : una por noche de volcán y como máximo 10 por volcán.

Mismo instrumento que el banco de paridad (scripts/banco_paridad.py): etiquetas, pareo a ±TOL_S, regla D-9. Se usa la
pasada `pos` con fila de alerta de MIROVA de 1 MW o más (máximo VRP de las filas pareadas), como el instrumento de la
regla cuenta «protegidas con record». Exige record de producción (es una pasada nuestra) y no exige record de la
guardia: aproxima la cuenta del vigilante desde arriba (cierra antes o igual), así que los días que da son una cota
inferior del plazo real. Las filas sólo OCR cuentan, igual que en el vigilante (lectura A): `bp.es_alerta` las acepta;
el aviso «Decide: SOLO la tabla» que imprime el banco no quita filas (corregido tras el verificador, 2026-11-11).

Uso, desde un worktree de main:  python <este script> --inicio 2026-04-09 --fin 2026-11-09 --out <json>
El inicio 04-09 es el de la primera medición S179 (todos los NOAA-21 en la referencia desde ahí). El verificador midió
también desde el 2026-03-01 y cortando el 2026-09-27 (sin la erupción de Chillán): `verificador/diag2_*.txt`.
Pregunta 1 del instrumento: si no hubiera protegidas, ninguna simulación cerraría por cuenta (todas por 120 días); se
imprime cuántas pasadas protegidas entraron, por sensor y volcán. Pregunta 2: control positivo, la forma «actual» con
encendido el 2026-11-03 en MODIS, hasta el 2026-11-09, debe contar 11 protegidas, todas de Chillán (lo midió VA en la
auditoría con el vigilante real).
"""
import argparse
import collections
import io
import json
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402

OBJETIVO, DIAS, TOPE = 29, 120, 10


def cierre(protegidas, inicio, fin_datos, forma):
    """Día (desde `inicio`) en que se junta el objetivo, o None si no se junta antes de 120 días o de que acaben los datos."""
    vence = inicio + timedelta(days=DIAS)
    por_vol, vistas_noche, n = collections.Counter(), set(), 0
    vols = collections.Counter()
    for p in protegidas:
        d = p["dt"].date()
        if d < inicio:
            continue
        if d >= vence or d > fin_datos:
            break
        if forma in ("noche", "noche10"):
            k = (p["vol"], p["noche"])
            if k in vistas_noche:
                continue
            vistas_noche.add(k)
        if forma in ("tope10", "noche10") and por_vol[p["vol"]] >= TOPE:
            continue
        por_vol[p["vol"]] += 1
        n += 1
        if n >= OBJETIVO:
            return (d - inicio).days, dict(por_vol)
    return None, dict(por_vol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ventana = (a.inicio, a.fin)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    prot = collections.defaultdict(list)
    for r in recs:
        if r["lab"] != "pos":
            continue
        fp = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        if fp and max((f["vrp_mw"] or 0) for f in fp) >= 1.0:
            prot[r["b"]].append(r)
    for s in prot:
        prot[s].sort(key=lambda r: (r["dt"], r["vol"]))

    ini, fin = date.fromisoformat(a.inicio), date.fromisoformat(a.fin)
    salida = {"ventana": ventana, "por_sensor": {}}
    for s in sorted(prot):
        cuenta = collections.Counter(r["vol"] for r in prot[s])
        print(f"== {s}: {len(prot[s])} pasadas protegidas en {ventana}; por volcán {dict(cuenta.most_common())}")
        res = {}
        for forma in ("actual", "tope10", "noche", "noche10"):
            dias, vols_cierre, sin_cerrar = [], [], 0
            d = ini
            # sólo encendidos con 120 días de datos por delante: el mismo conjunto para las cuatro formas
            while (fin - d).days >= DIAS:
                k, pv = cierre(prot[s], d, fin, forma)
                if k is not None:
                    dias.append(k)
                    vols_cierre.append(len(pv))
                else:
                    sin_cerrar += 1
                d += timedelta(days=1)
            n_eval = len(dias) + sin_cerrar
            res[forma] = {"encendidos_evaluables": n_eval, "cierran_por_cuenta": len(dias),
                          "dias_mediana": statistics.median(dias) if dias else None,
                          "dias_min": min(dias) if dias else None,
                          "volcanes_al_cerrar_mediana": statistics.median(vols_cierre) if vols_cierre else None}
            print(f"   {forma:8s}: de {n_eval} encendidos simulados, cierran por cuenta {len(dias)} "
                  f"(mediana {res[forma]['dias_mediana']} días, mínimo {res[forma]['dias_min']}; volcanes al cerrar, "
                  f"mediana {res[forma]['volcanes_al_cerrar_mediana']}); el resto cierra a los 120 días")
        # control positivo: encendido de MODIS
        if s == "MODIS":
            k, pv = cierre(prot[s], date(2026, 11, 3), fin, "actual")
            print(f"   control: encendido 2026-11-03, forma actual, hasta {fin}: cierra {k}, cuenta por volcán {pv}")
        salida["por_sensor"][s] = {"n": len(prot[s]), "por_volcan": dict(cuenta), "formas": res}
    Path(a.out).write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
