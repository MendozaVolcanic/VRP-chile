# FICHA (SDA, CPLT 372): probe de solo lectura (S192). Baja gránulos L1B de VIIRS NOAA-21 a un temporal, mide de qué está
# hecho el «dato faltante» que el marcador del cráter (#1060) cuenta, y los borra. No es detección de producción; no escribe
# en data/, no commitea, no hace push.
"""Uso (desde la raíz del repo, con EARTHDATA_TOKEN; lo corre .github/workflows/probe-s192-bowtie.yml):
    python experiments/_s192_bowtie/medir_bowtie.py --out out
    python experiments/_s192_bowtie/medir_bowtie.py --autoprueba        (sin red: prueba del instrumento)

POR QUÉ. El 2026-11-20, 27 pasadas VIIRS de los 11 Tier A traen px_mir_invalido_crater > 0, todas de NOAA-21 con cenit del
sensor de 54,7° a 67,0°. Sospecha: es la supresión «bow-tie» de VIIRS. Al final del barrido los barridos vecinos se
solapan; el satélite descarta a bordo los detectores del borde de cada barrido y el L1B los entrega con DN 65533
(«Bowtie_Deleted», UserGuide VIIRS L1B Aug 2021, tablas de las variables EV de I04-I05 y M12-M16) y el bit 256 de
quality_flags (Tabla C.1). leer_radiancia_l1b pone en NaN todo DN >= 65528 y dato_faltante_crater lo cuenta igual que un
Missing_EV o un Cal_Fail. Si la sospecha es cierta, el suelo de esos píxeles sí se midió con el barrido contiguo.

QUÉ MIDE, por cada gránulo y cada Tier A que cubre, con la MISMA ventana, el MISMO radio y la MISMA función del marcador:
  1. el conteo oficial (MV.dato_faltante_crater) para compararlo con lo publicado (control del instrumento);
  2. para cada píxel contado: DN crudo de la banda MIR y de la TIR, bits de quality_flags, fila, detector dentro del
     barrido (fila mód 16 en M, mód 32 en I), cenit del sensor, y distancia al píxel VÁLIDO más cercano (MIR y TIR finitas);
  3. la distancia del cráter al píxel válido más cercano (si el cráter quedó cubierto por el barrido vecino);
  4. en el gránulo entero: en qué columnas aparece el DN 65533, qué detectores, y el cenit en la primera columna.

REGLAS DEL VEREDICTO (escritas antes de ver datos):
  - SIN DATO si falta algún gránulo o si el conteo oficial recalculado no iguala al publicado en algún record
    (el instrumento no reproduce lo que pretende explicar).
  - CONFIRMADO si >= 90 % de los píxeles contados tienen DN 65533 en la MIR o en la TIR (bow-tie) Y cada uno de esos
    píxeles tiene un píxel válido a menos de un paso de la grilla del sensor (750 m o 375 m): el suelo se midió.
  - REFUTADO si < 50 % son 65533.
  - entre 50 % y 90 %: MIXTO, se informa la composición.
"""
import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

DN_BOWTIE = 65533      # UserGuide VIIRS L1B Aug 2021: 65532 = Missing_EV, 65533 = Bowtie_Deleted, 65534 = Cal_Fail
NOMBRE_DN = {65532: "Missing_EV", 65533: "Bowtie_Deleted", 65534: "Cal_Fail", 65535: "Fill"}
QF_BITS = {1: "Substitute_Cal", 2: "Out_of_Range", 4: "Saturation", 8: "Temp_not_Nominal", 256: "Bowtie_Deleted",
           512: "Missing_EV", 1024: "Cal_Fail", 2048: "Dead_Detector", 4096: "Noisy_Detector"}
TIER_A = ["Lascar", "Isluga", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
# pasadas del 2026-11-20 con marca, y un volcán que el gránulo cubre (para la búsqueda en CMR)
PASADAS = {"A2026324.0442": "Lascar", "A2026324.0448": "NevadosDeChillan",
           "A2026324.0624": "Copahue", "A2026324.0630": "PuyehueCordonCaulle"}
FAMILIAS = {"MOD": {"familia": "VIIRS750", "l1b": "VIIRS_NOAA21_MOD_L1B", "geo": "VIIRS_NOAA21_MOD_GEO", "ndet": 16},
            "IMG": {"familia": "VIIRS375", "l1b": "VIIRS_NOAA21_L1B", "geo": "VIIRS_NOAA21_GEO", "ndet": 32}}


def bits(q):
    return [n for b, n in QF_BITS.items() if int(q) & b]


def volcanes_yaml():
    import yaml
    from pipeline.geo_utils import get_detection_anchor
    d = yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))
    out = {}
    for v in d["volcanoes"]:
        if v["name"] in TIER_A:
            out[v["name"]] = get_detection_anchor(v)
    return out


def ventana_del_volcan(MV, lat, lon, nombre, fam):
    """La ventana que calcular_vrp_granulo le pasa a dato_faltante_crater (misma receta, líneas copiadas), o None si
    la vía no produciría record (sin grilla, < 100 píxeles en 45 km o centro a más de dist_max_centro_km)."""
    cfg = MV.FAMILIAS[fam]
    g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    if g is None:
        return None, None
    dist = MV._haversine(lat, lon, g["centro_lat"], g["centro_lon"])
    sel = np.isfinite(dist) & (dist < MV.RADIO_RECORTE_KM)
    if sel.sum() < 100:
        return None, g
    i0 = np.unravel_index(np.nanargmin(np.where(sel, dist, np.inf)), dist.shape)
    if cfg["dist_max_centro_km"] is not None and dist[i0] > cfg["dist_max_centro_km"]:
        return None, g
    filas, cols = np.flatnonzero(sel.any(axis=1)), np.flatnonzero(sel.any(axis=0))
    return (slice(filas[0], filas[-1] + 1), slice(cols[0], cols[-1] + 1)), g


def desglose(MV, rad, dn, qf, lat, lon, zen, b_mir, b_tir, vlat, vlon, paso_m, ventana, ndet):
    """Los píxeles que el marcador cuenta en px_mir_invalido_crater, uno por uno, y la cobertura del cráter."""
    v = ventana
    la, lo = lat[v], lon[v]
    cerca = MV._haversine(la, lo, vlat, vlon) < MV.CELDAS_DATO_CRATER * float(paso_m) / 1000.0
    cerca &= np.isfinite(la) & np.isfinite(lo)
    mir, tir = np.asarray(rad[b_mir], float)[v], np.asarray(rad[b_tir], float)[v]
    valido = np.isfinite(mir) & np.isfinite(tir) & np.isfinite(la) & np.isfinite(lo)
    contados = cerca & ~(np.isfinite(mir) & np.isfinite(tir))
    vla, vlo = la[valido], lo[valido]
    px = []
    for r, c in zip(*np.nonzero(contados)):
        fila, col = int(r + v[0].start), int(c + v[1].start)
        dval = MV._haversine(vla, vlo, la[r, c], lo[r, c])
        px.append({"fila": fila, "col": col, "detector": fila % ndet,
                   "dn_mir": int(dn[b_mir][fila, col]), "dn_tir": int(dn[b_tir][fila, col]),
                   "qf_mir": bits(qf[b_mir][fila, col]) if qf.get(b_mir) is not None else None,
                   "qf_tir": bits(qf[b_tir][fila, col]) if qf.get(b_tir) is not None else None,
                   "cenit": round(float(zen[fila, col]), 2) if zen is not None else None,
                   "dist_crater_km": round(float(MV._haversine(la[r, c], lo[r, c], vlat, vlon)), 3),
                   "dist_valido_mas_cercano_km": round(float(dval.min()), 3) if dval.size else None})
    dcrater = MV._haversine(vla, vlo, vlat, vlon)
    return px, (round(float(dcrater.min()), 3) if dcrater.size else None)


def resumen_bowtie(dn_mir, zen, ndet):
    """Dónde aparece el DN 65533 en el gránulo entero: columnas, detectores y cenit en la frontera."""
    m = dn_mir == DN_BOWTIE
    cols = np.flatnonzero(m.any(axis=0))
    out = {"n_px_65533": int(m.sum()), "n_px_total": int(m.size), "n_columnas": int(dn_mir.shape[1])}
    if cols.size == 0:
        return out
    mitad = dn_mir.shape[1] // 2
    for lado, cc in (("izq", cols[cols < mitad]), ("der", cols[cols >= mitad])):
        if cc.size == 0:
            continue
        frontera = int(cc.max()) if lado == "izq" else int(cc.min())   # la columna con 65533 más cerca del nadir
        filas = np.flatnonzero(m[:, frontera])
        sub = m[:, cc]
        dets_frontera = sorted(set(int(f % ndet) for f in filas))
        dets_borde = sorted(set(int(f % ndet) for f in np.flatnonzero(m[:, int(cc.min()) if lado == "izq" else int(cc.max())])))
        out[lado] = {"col_frontera": frontera, "n_columnas_con_65533": int(cc.size),
                     "cenit_frontera": round(float(np.nanmedian(zen[:, frontera])), 2) if zen is not None else None,
                     "detectores_en_frontera": dets_frontera, "detectores_en_borde_del_barrido": dets_borde,
                     "fraccion_filas_65533_en_borde": round(float(sub[:, 0 if lado == "izq" else -1].mean()), 4)}
    # ¿los 65533 traen posición? (si no, el marcador no los contaría en px_mir_invalido sino en crater_sin_posicion)
    return out


def leer_crudos(ruta, bandas):
    import h5py
    dn, qf = {}, {}
    with h5py.File(ruta, "r") as f:
        obs = f["observation_data"]
        for b in bandas:
            dn[b] = obs[b][:]
            q = obs.get(f"{b}_quality_flags")
            qf[b] = q[:] if q is not None else None
    return dn, qf


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def bajar(clave, sello, vlat, vlon, destino):
    from pipeline.fetch import download_granules, search_granules
    dt = datetime.strptime(sello[1:], "%Y%j.%H%M")
    grs = [g for g in search_granules(clave, vlat, vlon, 25, dt) if sello in gname(g)]
    if not grs:
        return None
    got = [Path(p) for p in download_granules(grs[:1], destino) if sello in Path(p).name]
    return got[0] if got else None


def clave_granulo(nombre):
    """'VJ202MOD_NRT.A2026324.0448.021.x.nc' y 'VJ202MOD.A2026324.0448...' -> 'VJ202MOD.A2026324.0448' (NRT o estándar)."""
    p = nombre.split(".")
    return ".".join([p[0].replace("_NRT", "")] + p[1:3])


def publicados():
    """px_mir_invalido_crater publicado por (volcán, gránulo) en data/mirova_equivalent del checkout."""
    out = {}
    for v in TIER_A:
        d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{v}.json", encoding="utf-8"))
        for r in d["records"]:
            dg = r.get("diag_codigo_mirova") or {}
            if "px_mir_invalido_crater" in dg and r.get("granule", "").startswith("VJ2") and ".A2026324." in r["granule"]:
                out[(v, clave_granulo(r["granule"]))] = {
                    "px_mir_invalido_crater": dg["px_mir_invalido_crater"],
                    "crater_sin_posicion": dg["crater_sin_posicion"], "granule": r["granule"]}
    return out


def autoprueba():
    """Sin red: un gránulo sintético con una fila 65533 junto al cráter debe dar el desglose esperado."""
    from pipeline import mirova_v750_codigo as MV
    n = 40
    lat = np.linspace(-23.2, -23.5, n)[:, None] * np.ones((1, n))
    lon = np.linspace(-67.9, -67.6, n)[None, :] * np.ones((n, 1))
    vlat, vlon = float(lat[20, 20]), float(lon[20, 20])
    dn = {"M13": np.full((n, n), 1000, np.uint16), "M15": np.full((n, n), 1000, np.uint16)}
    dn["M13"][20, :] = DN_BOWTIE
    dn["M15"][20, :] = DN_BOWTIE
    dn["M13"][21, 21] = 65532
    qf = {"M13": np.zeros((n, n), np.uint16), "M15": np.zeros((n, n), np.uint16)}
    qf["M13"][20, :] = 256
    rad = {b: np.where(dn[b] >= MV.FLAG_MIN_DN, np.nan, dn[b] * 0.001) for b in dn}
    zen = np.full((n, n), 60.0)
    oficial = MV.dato_faltante_crater(rad, lat, lon, "M13", "M15", vlat, vlon, 750.0)
    px, dcr = desglose(MV, rad, dn, qf, lat, lon, zen, "M13", "M15", vlat, vlon, 750.0,
                       (slice(0, n), slice(0, n)), 16)
    assert oficial["px_mir_invalido_crater"] == len(px), (oficial, len(px))
    assert sorted({p["dn_mir"] for p in px}) == [65532, 65533], px
    assert all(p["qf_mir"] == ["Bowtie_Deleted"] for p in px if p["dn_mir"] == DN_BOWTIE)
    assert all(p["detector"] == 20 % 16 for p in px if p["dn_mir"] == DN_BOWTIE)
    rb = resumen_bowtie(dn["M13"], zen, 16)
    assert rb["n_px_65533"] == n, rb
    # control de caída: sin la fila bow-tie el instrumento debe dar cero 65533
    dn2 = {b: np.full((n, n), 1000, np.uint16) for b in dn}
    rad2 = {b: dn2[b] * 0.001 for b in dn2}
    px2, _ = desglose(MV, rad2, dn2, {}, lat, lon, zen, "M13", "M15", vlat, vlon, 750.0, (slice(0, n), slice(0, n)), 16)
    assert px2 == [], px2
    print("autoprueba OK:", len(px), "píxeles contados,", sum(p["dn_mir"] == DN_BOWTIE for p in px), "bow-tie")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=os.environ.get("VRP_TMP_DIR", str(ROOT / "granulos_tmp")))
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args()
    if a.autoprueba:
        return autoprueba()
    if not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 2
    from pipeline.fetch import auth
    from pipeline import mirova_v750_codigo as MV
    auth()
    vents = volcanes_yaml()
    pub = publicados()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res, faltan = [], 0
    for sello, vref in PASADAS.items():
        for tipo, F in FAMILIAS.items():
            print(f"\n== {sello} {tipo}", flush=True)
            item = {"sello": sello, "tipo": tipo, "ok": False}
            tmp = Path(a.tmp) / f"{sello}_{tipo}"
            try:
                tmp.mkdir(parents=True, exist_ok=True)
                vlat, vlon = vents[vref]
                rl = bajar(F["l1b"], sello, vlat, vlon, tmp)
                rg = bajar(F["geo"], sello, vlat, vlon, tmp)
                if rl is None or rg is None:
                    raise RuntimeError(f"sin gránulo: l1b={rl} geo={rg}")
                item["l1b"], item["geo"] = rl.name, rg.name
                bandas = MV.FAMILIAS[F["familia"]]["bandas"]
                b_mir, b_tir = bandas
                rad = MV.leer_radiancia_l1b(rl, bandas=bandas)
                lat, lon, ang = MV.leer_geo_l1b(rg)
                dn, qf = leer_crudos(rl, bandas)
                zen = ang.get("sensor_zenith")
                item["resumen_bowtie_mir"] = resumen_bowtie(dn[b_mir], zen, F["ndet"])
                item["resumen_bowtie_tir"] = resumen_bowtie(dn[b_tir], zen, F["ndet"])
                m = dn[b_mir] == DN_BOWTIE
                item["bowtie_mir_sin_posicion"] = int((m & ~np.isfinite(lat)).sum())
                item["volcanes"] = {}
                for nombre, (vla, vlo) in vents.items():
                    ventana, g = ventana_del_volcan(MV, lat, lon, nombre, F["familia"])
                    if ventana is None:
                        continue
                    of = MV.dato_faltante_crater(rad, lat, lon, b_mir, b_tir, vla, vlo, g["paso"], ventana=ventana)
                    px, dcr = desglose(MV, rad, dn, qf, lat, lon, zen, b_mir, b_tir, vla, vlo, g["paso"], ventana,
                                       F["ndet"])
                    p = pub.get((nombre, clave_granulo(rl.name)))
                    item["volcanes"][nombre] = {"oficial_recalculado": of, "publicado": p, "paso_m": g["paso"],
                                                "dist_crater_a_valido_km": dcr, "pixeles": px}
                    print(f"  {nombre}: recalculado {of['px_mir_invalido_crater']} publicado "
                          f"{None if p is None else p['px_mir_invalido_crater']} | DN MIR {[x['dn_mir'] for x in px]} "
                          f"| det {[x['detector'] for x in px]} | cráter a válido {dcr} km", flush=True)
                item["ok"] = True
            except Exception as e:
                item["error"] = f"{type(e).__name__}: {e}"
                traceback.print_exc()
                faltan += 1
            finally:
                for f in tmp.glob("*"):
                    try:
                        f.unlink()
                    except OSError:
                        pass
            res.append(item)
            json.dump(res, open(out / "bowtie_resultados.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
