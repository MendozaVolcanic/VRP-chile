# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c02: tabla por pasada de la retrospectiva, con codigo propio.

QUE HACE. Con los insumos de c01 (VIA = D2 + D4, K-gemelo = D3, K de disco de e7cfbaf54) arma una fila por pasada
nocturna y le pone: tramo, etiqueta de MIROVA (tabla sola y union con OCR), y lo que publica el tablero para K, la
via (el record tal cual: posicion radiante), el K-gemelo y un brazo K x 1,2.

VARAS (las del preambulo, no el lector): "publica" = scripts/banco_paridad.py::correr_node con el frontend que se
indique (--frontend); etiquetas = banco_paridad.indexar_referencia (regla SN) + etiquetar + clase_mirova.
alerta_protegida (lectura A), importados de --raiz (por defecto la instantanea de main 438a60a1e). La referencia es
la congelada de la retrospectiva (CONS 811c4c07, OCR 01c9478d). NO se importa leer_retro.py ni sus reglas.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si la tabla estuviera rota (pasadas mal etiquetadas o mal pareadas), lo veria? En parte: los conteos por tramo,
   sensor y etiqueta se cruzan contra lectura.json (c04) y contra el §7 del pre-registro (9, 26 y 30 protegidas).
2. Si el instrumento estuviera muerto? 0 pasadas, 0 protegidas o un node que no corre abortan con mensaje.
Control positivo: el brazo K x 1,2 TIENE que cambiar la magnitud mostrada en toda pasada publicada (se cuenta).

Uso: python c02_tabla_pasadas.py --frontend {tag|main|sin_modulo} [--sin-capas] --salida tabla_X.json
"""
import argparse
import collections
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

INS = Path("D:/vrp-trabajo/temporales/s179-audit/c/insumos")
MAIN = Path("D:/vrp-trabajo/temporales/s179-audit/main")
WT = Path("D:/vrp-trabajo/worktrees/s178-lectura")          # ref de lectura (solo lectura)
TMP = Path("D:/vrp-trabajo/temporales/s179-audit/c")
TRAMOS = {"F26-V": ("2026-02-01", "2026-03-31", ("VIIRS375", "VIIRS750")),
          "F26-M": ("2026-02-01", "2026-02-28", ("MODIS",)),
          "F26-M3": ("2026-03-01", "2026-03-31", ("MODIS",)),
          "R25": ("2025-02-15", "2025-12-31", ("MODIS", "VIIRS375", "VIIRS750")),
          "DM": ("2026-10-01", "2026-10-16", ("MODIS", "VIIRS375", "VIIRS750"))}
DM_SIN_VIIRS = ("2026-10-12", "2026-10-13")


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def tramo_de(b, dia):
    for t, (a, z, bs) in TRAMOS.items():
        if b in bs and a <= dia <= z:
            if t == "DM" and b != "MODIS" and dia in DM_SIN_VIIRS:
                return None
            return t
    return None


def cargar(carpeta):
    out = {}
    for f in sorted(Path(carpeta).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d["records"]:
            out[(d["volcano"], r.get("sensor"), r.get("datetime_utc"))] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontend", choices=("tag", "main", "sin_modulo"), required=True)
    ap.add_argument("--raiz", default=str(MAIN))
    ap.add_argument("--sin-capas", action="store_true", help="referencia sin las capas de historia y respaldo")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    raiz = Path(a.raiz)
    sys.path.insert(0, str(raiz / "scripts"))
    sys.path.insert(0, str(raiz))
    import banco_paridad as bp
    import clase_mirova as clase
    import referencia_mirova_unificada as rmu
    if a.frontend == "sin_modulo":
        # control del candado: el index.html del tag SIN cambio_detector.js al lado (copia en la carpeta temporal)
        d = TMP / "frontend_sin_modulo"
        d.mkdir(exist_ok=True)
        shutil.copyfile(WT / "frontend" / "index.html", d / "index.html")
        bp.HTML = d / "index.html"
    else:
        bp.HTML = (WT if a.frontend == "tag" else MAIN) / "frontend" / "index.html"
    print("raiz de las varas:", raiz, "| frontend:", bp.HTML)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    via, k, kg = cargar(INS / "via"), cargar(INS / "k_e7cfbaf54"), cargar(INS / "kgemelo")
    print("records: via", len(via), "K", len(k), "K-gemelo", len(kg))
    filas = []
    for key in sorted(set(via) | set(k), key=lambda x: (x[0], str(x[1]), str(x[2]))):
        vol, sensor, dts = key
        b = bucket(sensor)
        if b is None or not dts:
            continue
        dia = dts[:10]
        t = tramo_de(b, dia)
        if t is None or (vol == "Tupungatito" and (t == "R25" or dia < "2026-02-23")):
            continue
        dt = datetime.strptime(dts[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt):
            continue
        rk, rv = k.get(key), via.get(key)
        marca = (rv or {}).get("via_codigo_mirova")
        estado = ("sobra_en_via" if rk is None else "k_con_marca" if rk.get("via_codigo_mirova") is True else
                  "sin_dato_cobertura" if rv is None else "ok" if marca is True else
                  "via_caida_k:%s" % marca if marca in ("sin_grilla", "sin_mxd03") else "via_sin_marca:%s" % marca)
        z = (rv or rk or {}).get("sensor_zenith_deg")
        filas.append({"vol": vol, "sensor": sensor, "b": b, "dt": dts[:16], "noche": dia, "tramo": t, "z": z,
                      "estado": estado, "_k": rk, "_v": rv, "_kg": kg.get(key), "en_kg": key in kg})
    print("pasadas nocturnas en tramos:", len(filas))
    if not filas:
        sys.exit("ABORTA: 0 pasadas")
    # ---- etiquetas (tabla sola decide; union informa)
    kw = {"respaldo_path": None, "historico_path": None} if a.sin_capas else {
        "respaldo_path": WT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
        "historico_path": WT / "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"}
    ref = rmu.cargar_referencia_unificada(WT / "experiments/_s178_lectura/_congelado/registro_vrp_consolidado.csv",
                                          WT / "experiments/_s178_lectura/_congelado/registro_vrp_ocr.csv", **kw)
    no_r25 = [f for f in filas if f["tramo"] != "R25"]
    ventana = (min(f["noche"] for f in no_r25), max(f["noche"] for f in no_r25))
    origen = collections.Counter((r.get("source"), r.get("origen")) for r in ref
                                 if "2026-02-01" <= r["fecha_utc"][:10] <= "2026-03-31")
    print("filas de la referencia en F26 por (source, origen):", dict(origen))
    for canal, rr in (("tabla", [r for r in ref if r["source"] == "CONS"]), ("union", list(ref))):
        por_vb, ns, nv, _n = bp.indexar_referencia(rr, coords, ventana, regla_minimas="SN")
        shim = [{"vol": f["vol"], "b": f["b"], "noche": f["noche"],
                 "dt": datetime.strptime(f["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)} for f in no_r25]
        bp.etiquetar(shim, por_vb, ns, nv)
        for f, s in zip(no_r25, shim):
            lab, vrp = s["lab"], None
            if lab == "pos":
                pares = [x for x in bp.parear(por_vb.get((f["vol"], f["b"]), []), s["dt"]) if bp.es_alerta(x["tipo"])]
                lab = "protegida" if any(clase.alerta_protegida(x, lectura="A") for x in pares) else "bajo1"
                vrp = max([x["vrp_mw"] or 0.0 for x in pares] or [0.0])
            elif lab in ("minima", "sin_geometria"):
                lab = "sin_info"
            f["lab" if canal == "tabla" else "lab_union"] = lab
            f["mir" if canal == "tabla" else "mir_union"] = vrp
    for f in filas:
        f.setdefault("lab", "sin_info")
        f.setdefault("lab_union", f["lab"])
        f.setdefault("mir", None)

    # ---- predicado del tablero (vara: banco_paridad.correr_node, con el armado de cargar_nuestros)
    def slim(r, g=1.0):
        s = {c: r.get(c) for c in bp.CAMPOS_JS if c != "anomaly_pixels"}
        if g != 1.0:
            s = json.loads(json.dumps(s))
            for c in ("vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "f5_core_vrp_mw"):
                if isinstance(s.get(c), (int, float)):
                    s[c] *= g
            if isinstance(s.get("primary_cluster"), dict) and isinstance(s["primary_cluster"].get("vrp_mw"), (int, float)):
                s["primary_cluster"]["vrp_mw"] *= g
        if r.get("f5_core_vrp_mw") is None:
            s["anomaly_pixels"] = [{c: p.get(c) for c in ("lat", "lon", "vrp_mw", "bt_k")}
                                   for p in (r.get("anomaly_pixels") or [])]
            if g != 1.0:
                for p in s["anomaly_pixels"]:
                    if isinstance(p.get("vrp_mw"), (int, float)):
                        p["vrp_mw"] *= g
        return s

    casos, idx = [], []
    for i, f in enumerate(filas):
        for brazo, rec, g in (("K", f["_k"], 1.0), ("V", f["_v"], 1.0), ("KG", f["_kg"], 1.0), ("PL", f["_k"], 1.2)):
            if rec is not None:
                casos.append([slim(rec, g), inner[f["vol"]]])
                idx.append((i, brazo))
    print("casos al predicado:", len(casos))
    res = []
    for i0 in range(0, len(casos), 15000):
        res += bp.correr_node(casos[i0:i0 + 15000])
    if len(res) != len(casos):
        sys.exit("ABORTA: node devolvio %d de %d" % (len(res), len(casos)))
    for (i, brazo), p in zip(idx, res):
        filas[i]["pub_" + brazo], filas[i]["mag_" + brazo] = int(p[4]), float(p[3] or 0.0)
        filas[i]["art_" + brazo] = int(p[2])
    # ---- salida compacta
    out = []
    for f in filas:
        g = {c: v for c, v in f.items() if not c.startswith("_")}
        for brazo, rec in (("K", f["_k"]), ("V", f["_v"]), ("KG", f["_kg"])):
            if rec is not None:
                pc = rec.get("primary_cluster") or {}
                g["pc_" + brazo] = pc.get("vrp_mw")
                g["dc_" + brazo] = rec.get("distance_class")
                g["npx_" + brazo] = len(rec.get("anomaly_pixels") or [])
                g["fh_" + brazo] = rec.get("final_hotspot_dist_km")
                g["f5_" + brazo] = rec.get("f5_core_vrp_mw")
                g["sha_" + brazo] = (rec.get("regimen") or {}).get("codigo_sha")
                if brazo == "V":
                    g["roi_V"] = (rec.get("diag_codigo_mirova") or {}).get("roi")
                    g["gran_V"] = rec.get("granule")
                if brazo == "K":
                    g["gran_K"] = rec.get("granule")
        out.append(g)
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    c = collections.Counter((f["tramo"], f["b"], f["estado"].split(":")[0]) for f in out)
    print("pasadas por (tramo, sensor, estado):")
    for kk, v in sorted(c.items()):
        print("   %s|%s|%s %d" % (kk + (v,)))
    pub_k = sum(1 for f in out if f.get("pub_K"))
    cambian = sum(1 for f in out if f.get("pub_K") and abs(f.get("mag_PL", 0) - f["mag_K"]) > 1e-12)
    print("control positivo: pasadas que K publica %d; en ellas K x 1,2 cambia la magnitud mostrada en %d"
          % (pub_k, cambian))
    prot = collections.Counter((f["b"], f["tramo"]) for f in out if f["lab"] == "protegida")
    print("protegidas de la tabla por (sensor, tramo), todas las pasadas:", dict(sorted(prot.items())))
    if not pub_k or not prot:
        sys.exit("ABORTA: 0 publicadas o 0 protegidas")


if __name__ == "__main__":
    main()
