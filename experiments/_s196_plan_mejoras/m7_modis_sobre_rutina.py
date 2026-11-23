# -*- coding: utf-8 -*-
"""Medición previa de MEJ-7 (plan S196): pasadas MODIS que la vía de producción publica en el cráter y la tabla de
MIROVA lista como RUTINA.

POR QUÉ. MEJ-7 nació de un solo caso (Láscar 2026-05-11 07:55 UTC, Aqua): un píxel del cráter, tibio, que MIROVA dejó
en RUTINA y el port publicó. Un caso justifica investigar, no priorizar (A94). Antes de un plan hay que saber cuántos
casos de esa forma deja hoy la vía (que es la réplica, ya en producción y con la historia reprocesada) y si SWIR ve más
calor esas noches que en las RUTINA que la vía no publica. Si la vía ya publica esos casos, la mejora no es del
laboratorio: es una divergencia de la réplica (sobre-publicación) y va a la cuenta de paridad.

Qué hace, sin reprocesar: pasadas MODIS nocturnas de la tabla de MIROVA (fuente CONS, estado rutina, `clase_mirova`)
desde 2026-03-01 (A119), pareadas a 120 s con nuestros records MODIS (`data/mirova_equivalent/`, predicado del tablero
de `banco_paridad.correr_node`); cuenta las que publicamos, por volcán, con píxeles y potencia; compara la tasa de
alerta NHI a ±1 día entre «rutina publicada» y «rutina no publicada», con el control de fechas NHI corridas 15 días.

Uso: python experiments/_s196_plan_mejoras/m7_modis_sobre_rutina.py --nhi-dir <carpeta de bajar_nhi.py>
"""
import argparse
import collections
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, cargar_referencia_unificada  # noqa: E402

CAJAS = ROOT / "experiments" / "_s195_viirs_dia_control" / "nhi_cajas.json"


def cargar_modis(desde, hasta):
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    recs, casos = [], []
    for vol in bp.VOLS:
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            if bp.bucket(r.get("sensor")) != "MODIS" or not (desde <= r.get("datetime_utc", "")[:10] <= hasta):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada("MODIS", lat, lon, dt.replace(tzinfo=timezone.utc)):
                continue
            recs.append({"vol": vol, "dt": dt, "npix": r.get("n_anomalous_pixels"), "z": r.get("sensor_zenith_deg"),
                         "dist": r.get("final_hotspot_dist_km"), "via": r.get("via_codigo_mirova")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    for rec, p in zip(recs, bp.correr_node(casos)):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhi-dir", required=True)
    ap.add_argument("--desde", default="2026-03-01")
    ap.add_argument("--hasta", default="2026-11-22")
    a = ap.parse_args()
    import yaml
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    print("referencia: %s (modificado %s UTC)" % (SNAP_CONS.relative_to(ROOT), datetime.fromtimestamp(
        SNAP_CONS.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M")))
    ref = cargar_referencia_unificada()
    coords = bp._coords_por_volcan()
    rut = []
    for p in cm.resumir_pasadas(ref, canal="tabla"):
        d = p.instante.strftime("%Y-%m-%d")
        if p.sensor_bucket != "MODIS" or p.volcano not in coords or not (a.desde <= d <= a.hasta):
            continue
        lat, lon = coords[p.volcano]
        if bp.es_pasada_diurna_descartada("MODIS", lat, lon, p.instante.replace(tzinfo=timezone.utc)):
            continue
        if p.estado == "rutina" and p.fuente == "CONS":
            rut.append(p)
    recs = cargar_modis(a.desde, a.hasta)
    idx = collections.defaultdict(list)
    for r in recs:
        idx[r["vol"]].append(r)
    pub, nopub, sinrec = [], [], 0
    for p in rut:
        par = [r for r in idx[p.volcano] if abs((r["dt"] - p.instante.replace(tzinfo=None)).total_seconds()) <= cm.VENTANA_S]
        if not par:
            sinrec += 1
            continue
        (pub if any(r["pub"] for r in par) else nopub).append((p, max(par, key=lambda r: r["disp"] or 0)))
    print("ventana %s a %s; pasadas MODIS nocturnas RUTINA de la tabla: %d; con record nuestro: %d; sin record: %d" % (
        a.desde, a.hasta, len(rut), len(pub) + len(nopub), sinrec))
    print("RUTINA que la vía publica (predicado del tablero): %d" % len(pub))
    pv = collections.defaultdict(list)
    for p, r in pub:
        pv[p.volcano].append(r)
    for vol in bp.VOLS:
        L = pv.get(vol)
        if not L:
            continue
        mw = sorted(r["disp"] for r in L)
        npx = collections.Counter(min(r["npix"] or 0, 3) for r in L)
        print("  %-20s %3d  mediana %.2f MW, máx %.2f MW; píxeles 1:%d 2:%d 3+:%d; vía %d de %d" % (
            vol, len(L), mw[len(mw) // 2], mw[-1], npx[1], npx[2], npx[3], sum(1 for r in L if r["via"]), len(L)))
    print("\nLáscar, detalle de las RUTINA publicadas (fecha, MW tablero, píxeles, distancia km, cenit):")
    for p, r in sorted(((p, r) for p, r in pub if p.volcano == "Lascar"), key=lambda x: x[0].instante):
        print("  %s  %.2f  %s  %s  %s" % (p.instante.strftime("%Y-%m-%d %H:%M"), r["disp"], r["npix"], r["dist"], r["z"]))

    cj = json.loads(CAJAS.read_text(encoding="utf-8"))
    nhi, usable = {}, {}
    for vol, c in cj["volcanes"].items():
        if not c.get("en_nhi"):
            continue
        dlat = c["buffer_km"] / 111.0
        dlon = c["buffer_km"] / (111.0 * abs(math.cos(math.radians(c["lat"]))))
        usable[vol] = abs(vy[vol]["lat"] - c["lat"]) <= dlat and abs(vy[vol]["lon"] - c["lon"]) <= dlon
        ruta = Path(a.nhi_dir) / c["nombre_nhi"] / "nhi_timeseries.json"
        if ruta.exists():
            nhi[vol] = [e for e in json.loads(ruta.read_text(encoding="utf-8")) if e.get("fecha")]
    for corr, tit in ((0, "TASA DE ALERTA NHI a ±1 día"), (15, "CONTROL: NHI corrido +15 días")):
        print("\n%s (noche = fecha UTC de la pasada; una noche cuenta una vez por clase)" % tit)
        tot = collections.Counter()
        for vol in bp.VOLS:
            if not usable.get(vol) or vol not in nhi:
                continue
            fila = []
            for nombre, L in (("rutina_no_publicada", nopub), ("rutina_publicada", pub)):
                noches = {p.instante.date() for p, _ in L if p.volcano == vol}
                n = al = 0
                for d0 in noches:
                    val = [e for e in nhi[vol] if e.get("alerta") is not None and abs(
                        (date.fromisoformat(e["fecha"][:10]) + timedelta(days=corr) - d0).days) <= 1]
                    if val:
                        n += 1
                        al += any(e["alerta"] is True for e in val)
                tot[(nombre, "n")] += n
                tot[(nombre, "a")] += al
                fila.append("%d/%d" % (al, n))
            print("  %-20s no publicada %8s   publicada %8s" % (vol, *fila))
        print("  %-20s no publicada %8s   publicada %8s" % ("TOTAL", "%d/%d" % (tot[("rutina_no_publicada", "a")],
              tot[("rutina_no_publicada", "n")]), "%d/%d" % (tot[("rutina_publicada", "a")], tot[("rutina_publicada", "n")])))


if __name__ == "__main__":
    main()
