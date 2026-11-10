"""S179: dos mediciones que acompañan a perdidas_por_pasada.py.

1. Margen de la celda más cercana a disparar en Guallatiri y Callaqui (sombra de los 34, vía «código MIROVA»).
   POR QUÉ: Nicolás preguntó por qué no vemos sus fumarolas. `diag_codigo_mirova.s1.celda_decisiva.margen` es
   min(c_nti/u_nti, c_eti/u_eti) de la mejor celda con el umbral de su zona: 1 o más dispara, 0,5 es la mitad del umbral.
2. Alertas diurnas de MIROVA en la ventana: el NRT sólo procesa de noche (D-10, #813), así que ninguna métrica nocturna
   las cuenta como perdidas.

Uso, desde un worktree de main: python <este script> --inicio 2026-04-09 --fin 2026-11-09
Pregunta 1 del instrumento: el margen sale del mismo diagnóstico que escribe el detector; un margen de 0 en todas las
pasadas sería instrumento muerto (se imprime el rango). Pregunta 2: el conteo diurno usa el mismo filtro de día que
producción (auto_audit_weekly.es_pasada_diurna_descartada); con el filtro roto, «noche» y «día» saldrían iguales a 0.
"""
import argparse
import collections
import io
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402
from clase_mirova import aplicar_regla_minimas  # noqa: E402


def margenes():
    for v in ("Guallatiri", "Callaqui"):
        r = json.loads((RAIZ / "data" / "sombra_34" / f"{v}.json").read_text(encoding="utf-8"))["records"]
        ts = sorted(x["datetime_utc"] for x in r)
        print(f"== {v}: {len(r)} records, {ts[0]} a {ts[-1]}; pasadas con algún píxel alertado: "
              f"{sum(1 for x in r if (x.get('n_anomalous_pixels') or 0) > 0)}")
        por = collections.defaultdict(list)
        celdas = collections.Counter()
        for x in r:
            c = (((x.get("diag_codigo_mirova") or {}).get("s1") or {}).get("celda_decisiva")) or {}
            if c.get("margen") is None:
                continue
            por[x["sensor"]].append(c["margen"])
            if x["sensor"] in ("VIIRS_NOAA20", "VIIRS_NOAA21"):
                celdas[(c.get("zona"), c.get("fila"), c.get("col"))] += 1
        for s, l in sorted(por.items()):
            print(f"   {s:18s} n {len(l):2d}  margen máx {max(l):.3f}  mediana {statistics.median(l):.3f}  mín {min(l):.3f}")
        print("   celda decisiva más repetida en VIIRS 375 (zona, fila, col):", celdas.most_common(3))


def diurnas(ini, fin):
    coords = bp._coords_por_volcan()
    filas = aplicar_regla_minimas(bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR), bp.MODO_MINIMAS).filas
    c, prot, vols = collections.Counter(), collections.Counter(), collections.Counter()
    for f in filas:
        if not (ini <= f["fecha_utc"][:10] <= fin) or not bp.es_alerta(f["tipo"]):
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        dia = bp.es_pasada_diurna_descartada(f["sensor_bucket"], *coords[f["volcano"]], dt)
        c[(f["sensor_bucket"], "dia" if dia else "noche", f["source"])] += 1
        if dia and (f["vrp_mw"] or 0) >= 1:
            prot[(f["sensor_bucket"], f["source"])] += 1
            vols[f["volcano"]] += 1
    print(f"== alertas de MIROVA (filas, CONS y OCR; una pasada puede tener las dos) {ini} a {fin}")
    for k, v in sorted(c.items()):
        print("  ", k, v)
    print("   diurnas de 1 MW o más, por sensor y canal:", dict(sorted(prot.items())))
    print("   diurnas de 1 MW o más, por volcán:", dict(vols.most_common()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    a = ap.parse_args()
    margenes()
    diurnas(a.inicio, a.fin)
