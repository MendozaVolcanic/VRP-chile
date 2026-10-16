# Tarea 1.17 del loop: poblacion y muestra del probe que re-etiqueta MODIS con MxD03.
# Solo lectura de data/mirova_equivalent/ y de la referencia de MIROVA. Escribe poblacion.json en esta
# carpeta, que es lo que el workflow lee: la muestra queda fijada en git antes de correr.
# Criterio y justificacion: README.md. Version 2 (arreglos del verificador de #834).
#
# POR QUE LA BANDA ES POR RECORD. Un corrimiento solo puede cambiar la etiqueta (o la publicacion) si la
# posicion que la decide esta a menos del corrimiento del limite summit/far. #828 confirmo el mecanismo
# (el frame s de MODIS recibe la posicion del frame 0,99778*s + 2) pero midio hasta 47 grados de cenit;
# el mismo modelo predice 4,8 km a 54 grados y 9,6 km a 65 grados del lado del frame 0. Una banda fija
# de 3 km dejaba fuera un tercio de la poblacion (verificador, punto 2a). Aca la banda de cada record es
# el corrimiento que predice el modelo para SU cenit, acimut y satelite, mas 1 km por la componente a lo
# largo de la traza y el terreno.
#
# POR QUE UN CENSO DE ALERTAS. La regla 1 del criterio de victoria (docs/MISSION.md) dice que en la
# replica no se acepta ningun cambio que pierda una alerta protegida (lectura A: alerta del scraper de
# 1 MW o mas, docs/S151_CRITERIO_CLASE_MIROVA.md). Arreglar la posicion es un cambio de produccion en la
# replica, asi que esa regla es la compuerta: las pasadas con alerta de MIROVA se miden TODAS.
#
# Uso: python seleccionar_mxd03.py [--snapshot]   (local; necesita node y, sin --snapshot, gh)
import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

VENTANA = ("2026-03-01", "2026-10-12")   # A119: MODIS completo desde marzo; Standard L1B ya publicado
MARGEN_TRAZA_KM = 1.0                    # componente a lo largo de la traza y terreno (#828: 0,2 a 0,45 km)
MARGEN_CONTROL_KM = 2.0                  # control: el limite queda a mas de banda + 2 km
TOPES = {"A": 30, "B_far": 6, "control": 4, "fuera": 3}   # B_summit y las pasadas con alerta de MIROVA: censo
MAX_POR_JOB = 48
SAL = "s151-tarea-1.17"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]

# --------------------------------------------------------------------- modelo de #828
ALTURA_KM, RADIO_KM = 705.0, 6371.0
PASO_GRADOS = 110.0 / 1354          # angulo de barrido por frame
FRAME_NADIR = 676.5


def _suelo(theta):
    t = math.radians(theta)
    s = (RADIO_KM + ALTURA_KM) / RADIO_KM * math.sin(t)
    return RADIO_KM * (math.asin(min(s, 1.0)) - t)


def _cenit(theta):
    return math.degrees(math.asin(min(1.0, (RADIO_KM + ALTURA_KM) / RADIO_KM * math.sin(math.radians(theta)))))


def lado_frame0(acimut, sensor):
    """Regla de los 7 granulos de #828 (7 de 7): de noche, Aqua tiene el frame 0 del lado de acimut
    positivo y Terra del negativo (las dos pasan de noche en sentidos opuestos)."""
    return (acimut > 0) if sensor == "MODIS_AQUA" else (acimut < 0)


def corrimiento_predicho(cenit, acimut, sensor):
    """Corrimiento a lo largo del barrido (km) que predice el modelo 0,99778*s + 2 de #828."""
    if cenit is None or acimut is None:
        return None
    lo, hi = 0.0, 55.0
    for _ in range(60):
        m = (lo + hi) / 2
        if _cenit(m) < cenit:
            lo = m
        else:
            hi = m
    th = (lo + hi) / 2
    s = FRAME_NADIR - th / PASO_GRADOS if lado_frame0(acimut, sensor) else FRAME_NADIR + th / PASO_GRADOS
    s = max(0.0, min(1353.0, s))
    espaciado = _suelo(th + PASO_GRADOS / 2) - _suelo(th - PASO_GRADOS / 2)
    return abs((2.0 - 0.00222 * s) * espaciado)


# --------------------------------------------------------------------- estratos
def distancias(rec):
    pc = rec.get("primary_cluster") or {}
    return rec.get("final_hotspot_dist_km"), pc.get("centroid_dist_km")


def banda(rec):
    """Banda del record: corrimiento predicho + margen de traza. Sin angulos, la mayor posible."""
    p = corrimiento_predicho(rec.get("sensor_zenith_deg"), rec.get("sensor_azimuth_deg"), rec.get("sensor"))
    if p is None:
        p = corrimiento_predicho(65.0, 1.0, "MODIS_AQUA")
    return p + MARGEN_TRAZA_KM


def estrato(rec, inner):
    """A: el hotspot final puede cruzar el limite (cambia la etiqueta).
    B_summit: solo el cumulo puede cruzar, y el record es summit (puede apagarse la publicacion).
    B_far: solo el cumulo puede cruzar y el record es far (por reubicacion no deberia publicarse).
    control: todo a mas de banda + 2 km del limite. fuera: entre medio. sin: sin distancias."""
    final, pc = distancias(rec)
    ds = [d for d in (final, pc) if d is not None]
    if not ds:
        return "sin"
    b = banda(rec)
    if final is not None and abs(final - inner) <= b:
        return "A"
    if pc is not None and abs(pc - inner) <= b:
        return "B_summit" if rec.get("distance_class") == "summit" else "B_far"
    if all(abs(d - inner) > b + MARGEN_CONTROL_KM for d in ds):
        return "control"
    return "fuera"


def clave_granulo(rec):
    """'MYD021KM.A2026073.0705': producto y hora del granulo, sin version ni fecha de proceso."""
    g = rec.get("granule")
    if g:
        partes = g.split(".")
        if len(partes) >= 3 and partes[0] in ("MOD021KM", "MYD021KM"):
            return ".".join(partes[:3])
    prod = {"MODIS_TERRA": "MOD021KM", "MODIS_AQUA": "MYD021KM"}.get(rec.get("sensor") or "")
    try:
        dt = datetime.strptime(rec.get("datetime_utc", ""), "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    if prod is None:
        return None
    return "%s.A%s.%s" % (prod, dt.strftime("%Y%j"), dt.strftime("%H%M"))


def muestrear(items, n, sal=SAL, clave=lambda x: x):
    """Los n primeros segun sha1(sal + clave): uniforme, determinista y sin depender del orden."""
    return sorted(items, key=lambda x: hashlib.sha1((sal + clave(x)).encode()).hexdigest())[:n]


def es_censo(fila):
    """Se mide siempre: toda pasada con alerta de MIROVA (reglas 1 y 2) y todo B_summit."""
    return fila["lab"] == "pos" or fila["prot"] or fila["estrato"] == "B_summit"


def construir_poblacion(records_por_volcan, inner, etiqueta, ventana=VENTANA, topes=TOPES):
    """`etiqueta(volcan, rec) -> dict(lab, prot, vrp_ref, pub)`: etiqueta de banco_paridad, alerta
    protegida (lectura A) y publicacion del record guardado."""
    out = {}
    for vol, recs in records_por_volcan.items():
        vistos = {}
        for r in recs:
            if not (r.get("sensor") or "").startswith("MODIS"):
                continue
            if not (ventana[0] <= (r.get("datetime_utc") or "")[:10] <= ventana[1]):
                continue
            k = clave_granulo(r)
            if k is not None:
                vistos.setdefault(k, r)
        filas = []
        for k, r in vistos.items():
            final, pc = distancias(r)
            e = etiqueta(vol, r)
            p = corrimiento_predicho(r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg"), r.get("sensor"))
            filas.append({"clave": k, "estrato": estrato(r, inner[vol]), "lab": e["lab"], "prot": bool(e["prot"]),
                          "vrp_ref": e.get("vrp_ref"), "pub_guardada": int(e["pub"]),
                          "datetime_utc": r.get("datetime_utc"), "sensor": r.get("sensor"),
                          "sensor_zenith_deg": r.get("sensor_zenith_deg"),
                          "sensor_azimuth_deg": r.get("sensor_azimuth_deg"),
                          "corrimiento_predicho_km": None if p is None else round(p, 3),
                          "dc_guardada": r.get("distance_class"), "final_dist_guardada": final,
                          "pc_dist_guardada": pc})
        N = {}   # poblacion por estrato y etiqueta de MIROVA: denominadores del estimador
        for f in filas:
            N.setdefault(f["estrato"], {}).setdefault(f["lab"], 0)
            N[f["estrato"]][f["lab"]] += 1
        censo = [f for f in filas if es_censo(f)]
        muestra = [dict(f, censo=True) for f in censo]
        ya = {f["clave"] for f in censo}
        for e, tope in topes.items():
            cand = [f for f in filas if f["estrato"] == e and f["clave"] not in ya]
            for f in muestrear(cand, tope, clave=lambda x: x["clave"]):
                muestra.append(dict(f, censo=False))
        out[vol] = {"inner_radius_km": inner[vol], "N": N, "n_records": len(filas),
                    "n_pub_tramo": sum(f["pub_guardada"] for f in filas),
                    "n_protegidas": sum(f["prot"] for f in filas), "muestra": muestra}
    return out


def repartir_en_jobs(pob, max_por_job=MAX_POR_JOB):
    """Un job por volcan; el que pasa de `max_por_job` se parte (Lascar, con 40 protegidas)."""
    jobs = {}
    for vol, v in pob.items():
        m = v["muestra"]
        n = max(1, math.ceil(len(m) / max_por_job))
        for i in range(n):
            jid = vol if n == 1 else "%s-%d" % (vol, i + 1)
            jobs[jid] = {"volcan": vol, "granulos": [g["clave"] for g in m[i::n]]}
    return jobs


# --------------------------------------------------------------------- E/S
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="store_true", help="referencia desde el snapshot del repo (sin red)")
    a = ap.parse_args()
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    sys.path.insert(0, str(RAIZ / "scripts"))
    sys.path.insert(0, str(RAIZ))
    import banco_paridad as bp   # predicado del tablero con node (A97) y etiquetador de la referencia
    from auto_audit_weekly import _coords_por_volcan
    from clase_mirova import alerta_protegida
    from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, bajar_remoto, cargar_referencia_unificada
    if a.snapshot:
        cons, ocr = SNAP_CONS, SNAP_OCR
        proc = {"fuente": "snapshot", "sha_cons": bp.sha_git(SNAP_CONS), "sha_ocr": bp.sha_git(SNAP_OCR)}
    else:   # la referencia es el remoto del dueno (Mirova-v1), fijado a un commit
        info = bajar_remoto(Path(tempfile.mkdtemp()))
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
        proc = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    filas_ref = cargar_referencia_unificada(cons, ocr)
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(filas_ref, coords, VENTANA, regla_minimas="SN")
    recs = {}
    for vol in VOLS:
        with open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8") as fh:
            recs[vol] = json.load(fh)["records"]
    pub = {}   # publicacion de cada record guardado, en lote por volcan (node)
    for vol in VOLS:
        rs = [r for r in recs[vol] if (r.get("sensor") or "").startswith("MODIS")
              and VENTANA[0] <= (r.get("datetime_utc") or "")[:10] <= VENTANA[1]]
        casos = []
        for r in rs:
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
        for r, p in zip(rs, bp.correr_node(casos) if casos else []):
            pub[id(r)] = int(p[4])

    def etiqueta(vol, r):
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        t = [{"vol": vol, "b": "MODIS", "dt": dt, "noche": dt.strftime("%Y-%m-%d")}]
        bp.etiquetar(t, por_vb, ns, nv)
        fr = bp.parear(por_vb.get((vol, "MODIS"), []), dt)
        return {"lab": t[0]["lab"], "prot": any(alerta_protegida(f, lectura="A") for f in fr),
                "vrp_ref": max([f["vrp_mw"] or 0 for f in fr if f["tipo"] != "RUTINA"], default=None),
                "pub": pub[id(r)]}

    pob = construir_poblacion(recs, inner, etiqueta)
    jobs = repartir_en_jobs(pob)
    for vol, v in pob.items():
        print(vol, "records", v["n_records"], "protegidas", v["n_protegidas"], "publicadas", v["n_pub_tramo"],
              "muestra", len(v["muestra"]), "censo", sum(g["censo"] for g in v["muestra"]))
    print("jobs:", {j: len(x["granulos"]) for j, x in jobs.items()})
    meta = {"version": 2, "ventana": VENTANA, "margen_traza_km": MARGEN_TRAZA_KM,
            "margen_control_km": MARGEN_CONTROL_KM, "topes": TOPES, "max_por_job": MAX_POR_JOB, "sal": SAL,
            "regla_minimas": "SN", "referencia": proc, "fuente": "data/mirova_equivalent/*.json (origin/main)"}
    with open(AQUI / "poblacion.json", "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "volcanes": pob, "jobs": jobs}, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
