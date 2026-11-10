"""S179: Nevados de Chillán, octubre y noviembre de 2026, los tres sensores: producción, la vía «código MIROVA» y MIROVA.

POR QUÉ: Nicolás (2026-11-10) pidió comparar nuestros datos de Chillán, donde hay alertas en los tres sensores, y
avisó que una colada de lava avanza hacia el sureste y hoy llega a casi 1 km. Dos preguntas: (1) por pasada, ¿publicamos
lo que MIROVA alerta, y con qué magnitud?; (2) en el espacio, ¿nuestros píxeles calientes se alargan hacia el SE como
la colada?

Brazos:
  prod  data/mirova_equivalent de main: VIIRS con K; MODIS con K hasta el 2026-11-02 y con la vía desde ahí.
  via   la vía «código MIROVA» en los tres sensores: trozos de la retrospectiva D2 (run 42507820590, 10-01 a 10-16) y
        de la historia P4 (run 42749607584, 10-17 a 11-09), perfil _s172_retro_paquete, tag s178-retro-historia.
«Publica» = predicado del tablero ejecutado con node (scripts/banco_paridad.py::correr_node), igual para los dos brazos.
Pareo y etiqueta de MIROVA: banco_paridad (±120 s, regla D-9 SN). Distancias y rumbos desde el punto del yaml
(lat -36.863, lon -71.377); el centro de la grilla de MIROVA está a ~0,4 km al oeste.

Las dos preguntas del instrumento: (1) si el pareo estuviera roto, ninguna pasada saldría `pos` (se imprime n por
etiqueta); (2) si la geometría estuviera muerta, todos los rumbos serían iguales o nulos (se imprime la distribución por
cuadrante y un control: el centroide de los píxeles de Cordón Caulle no aplica aquí, así que el control es la mediana de
distancia de los píxeles de VIIRS 375, que tiene que ser del orden de la resolución, no 0 ni decenas de km).

Uso, desde un worktree de main:
  python <este script> --via <carpeta con subcarpetas de trozos> --out <carpeta de salida>
"""
import argparse
import collections
import glob
import io
import json
import math
import statistics
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402

VOL = "NevadosDeChillan"
LAT0, LON0 = -36.863, -71.377
VENTANA = ("2026-10-01", "2026-11-09")


def enu_km(lat, lon):
    dn = (lat - LAT0) * 111.32
    de = (lon - LON0) * 111.32 * math.cos(math.radians(LAT0))
    return de, dn


def rumbo(de, dn):
    return (math.degrees(math.atan2(de, dn)) + 360) % 360


def cargar_brazo(data_dir, coords, inner, por_vb, ns, nv):
    recs = bp.cargar_nuestros(coords, inner, VENTANA, data=data_dir)
    bp.etiquetar(recs, por_vb, ns, nv)
    return {(r["b"], r["dt"]): r for r in recs if r["vol"] == VOL}


def records_completos(path_json_list):
    out = {}
    for p in path_json_list:
        for r in json.loads(Path(p).read_text(encoding="utf-8"))["records"]:
            out[(r["sensor"], r["datetime_utc"])] = r
    return out


def geometria(rec):
    px = [p for p in (rec.get("anomaly_pixels") or []) if p.get("lat") is not None]
    if not px:
        return None
    pts = [enu_km(p["lat"], p["lon"]) for p in px]
    w = [max(p.get("vrp_mw") or 0, 0) for p in px]
    sw = sum(w) or len(w)
    ce = sum(e * (wi if sum(w) else 1) for (e, _), wi in zip(pts, w)) / sw
    cn = sum(n * (wi if sum(w) else 1) for (_, n), wi in zip(pts, w)) / sw
    dist = [math.hypot(e, n) for e, n in pts]
    se = [d for (e, n), d in zip(pts, dist) if 90 <= rumbo(e, n) <= 180]
    caliente = max(range(len(px)), key=lambda i: (px[i].get("bt_k") or 0))
    return {"n": len(px), "cent_e": round(ce, 3), "cent_n": round(cn, 3),
            "cent_dist": round(math.hypot(ce, cn), 3), "cent_rumbo": round(rumbo(ce, cn)),
            "max_dist": round(max(dist), 3), "max_dist_se": round(max(se), 3) if se else None,
            "n_se": len(se), "pix_caliente_dist": round(dist[caliente], 3),
            "pix_caliente_rumbo": round(rumbo(*pts[caliente]))}


def asimetria_se(filas_out, prod_full, via_full):
    """¿Los píxeles alertados se extienden más hacia el SE (rumbo 135°) que hacia el NO, desde el foco?

    POR QUÉ: una colada que baja al SE desde el cráter agrega píxeles calientes de un solo lado; el desenfoque del sensor
    y el error de geolocalización ensanchan la mancha hacia los dos lados por igual. El foco no se supone: es la mediana
    de la posición del píxel más caliente de VIIRS 375 en todo el período, por brazo (el yaml no marca el cráter activo).
    Control: la misma medida sobre el eje perpendicular (NE contra SO) tiene que salir pareja si sólo hay desenfoque.
    """
    ux, uy = math.sin(math.radians(135)), math.cos(math.radians(135))   # eje SE
    vx, vy = math.sin(math.radians(45)), math.cos(math.radians(45))     # eje NE (control)
    print("\n== Asimetría hacia el SE de los píxeles alertados, desde el foco (VIIRS 375 y 750, pasadas publicadas)")
    for b in ("VIIRS375", "VIIRS750"):
        for nombre, full in (("prod", prod_full), ("via", via_full)):
            pasadas = []
            for f in filas_out:
                if f["sensor"] != b or not f[nombre] or not f[nombre]["pub"]:
                    continue
                rec = full.get((f[nombre]["sat"], f["utc"])) or {}
                px = [p for p in rec.get("anomaly_pixels") or [] if p.get("lat") is not None and p.get("bt_k")]
                if len(px) >= 2:
                    pasadas.append((f["utc"], px))
            if not pasadas:
                continue
            calientes = [max(px, key=lambda p: p["bt_k"]) for _, px in pasadas]
            flat = statistics.median(p["lat"] for p in calientes)
            flon = statistics.median(p["lon"] for p in calientes)
            fe, fn = enu_km(flat, flon)
            print(f"  {b} {nombre}: foco (mediana del píxel más caliente) lat {flat:.5f} lon {flon:.5f}, a "
                  f"{math.hypot(fe, fn):.2f} km rumbo {rumbo(fe, fn):.0f}° del punto del yaml; n pasadas {len(pasadas)}")
            por_q = collections.defaultdict(list)
            for utc, px in pasadas:
                pr = [((enu_km(p["lat"], p["lon"])[0] - fe) * ux + (enu_km(p["lat"], p["lon"])[1] - fn) * uy) for p in px]
                pq = [((enu_km(p["lat"], p["lon"])[0] - fe) * vx + (enu_km(p["lat"], p["lon"])[1] - fn) * vy) for p in px]
                dia = int(utc[8:10])
                q = utc[:7] + ("-01a10" if dia <= 10 else "-11a20" if dia <= 20 else "-21a31")
                por_q[q].append((max(pr), -min(pr), max(pq), -min(pq), len(px)))
            for q, l in sorted(por_q.items()):
                med = [statistics.median(x[i] for x in l) for i in range(5)]
                print(f"     {q}: n {len(l):2d} | píxeles {med[4]:.0f} | alcance SE {med[0]:.2f} km, NO {med[1]:.2f} km "
                      f"(SE-NO {med[0] - med[1]:+.2f}) | control NE {med[2]:.2f}, SO {med[3]:.2f} (NE-SO {med[2] - med[3]:+.2f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA, regla_minimas=bp.MODO_MINIMAS)

    # La vía: une los trozos en un JSON con el mismo formato que producción; los demás volcanes, vacíos.
    trozos = sorted(glob.glob(str(Path(a.via) / "*" / f"{VOL}.json")))
    via_full = records_completos(trozos)
    tmp = Path(tempfile.mkdtemp(prefix="s179_chillan_"))
    for v in bp.VOLS:
        recs = list(via_full.values()) if v == VOL else []
        (tmp / f"{v}.json").write_text(json.dumps({"volcano": v, "records": recs}), encoding="utf-8")
    prod = cargar_brazo(None, coords, inner, por_vb, ns, nv)
    via = cargar_brazo(str(tmp), coords, inner, por_vb, ns, nv)
    prod_full = records_completos([bp.DATA / f"{VOL}.json"])

    # Las pasadas son las nuestras (prod y vía comparten la hora del gránulo). Una alerta de MIROVA sin ninguna pasada
    # nuestra a ±TOL_S se cuenta aparte (cobertura), nunca como pasada con clave de MIROVA: eso la contaba dos veces.
    claves = sorted(set(prod) | set(via))
    sin_record = collections.Counter()
    for (vol, b), lista in por_vb.items():
        if vol != VOL:
            continue
        nuestras = sorted(dt for (bb, dt) in claves if bb == b)
        for dt, f in lista:
            if bp.es_alerta(f["tipo"]) and not any(abs((dt - t).total_seconds()) <= bp.TOL_S for t in nuestras):
                sin_record[(b, (f["vrp_mw"] or 0) >= 1)] += 1
    filas_out = []
    for b, dt in claves:
        ref = bp.parear(por_vb.get((VOL, b), []), dt)
        al = [f for f in ref if bp.es_alerta(f["tipo"])]
        fila = {"sensor": b, "utc": dt.strftime("%Y-%m-%d %H:%M"),
                "mirova_tipo": sorted({f["tipo"] for f in ref}) or None,
                "mirova_vrp": max((f["vrp_mw"] or 0) for f in al) if al else (0.0 if ref else None),
                "mirova_dist_tabla": next((f["dist_km"] for f in al if f["source"] == "CONS" and f["dist_km"] is not None), None)}
        for nombre, brazo, full in (("prod", prod, prod_full), ("via", via, via_full)):
            r = brazo.get((b, dt))
            if r is None:
                fila[nombre] = None
                continue
            rec = full.get((r["sensor"], fila["utc"])) or {}
            pc = rec.get("primary_cluster") or {}
            # Magnitud: `disp`, lo que el tablero muestra (mirovaEqVrp ejecutado con node), igual en los dos brazos.
            # Los píxeles de la vía no traen VRP propio (sólo el total del record), por eso no se suma por píxel.
            fila[nombre] = {"lab": r["lab"], "pub": bool(r["pub"]), "disp": r["disp"], "sat": r["sensor"],
                            "via": rec.get("via_codigo_mirova"), "vrp_pc": pc.get("vrp_mw"),
                            "dist_final": rec.get("final_hotspot_dist_km"), "z": rec.get("sensor_zenith_deg"),
                            "geo": geometria(rec)}
        filas_out.append(fila)
    (out / "pasadas.json").write_text(json.dumps(filas_out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------------------------------------------------------- resumen por sensor y brazo
    print(f"Chillán {VENTANA[0]} a {VENTANA[1]}: {len(filas_out)} pasadas (unión de prod, vía y MIROVA)")
    print("etiquetas prod:", dict(collections.Counter(f['prod']['lab'] for f in filas_out if f['prod'])),
          "| vía:", dict(collections.Counter(f['via']['lab'] for f in filas_out if f['via'])))
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        fs = [f for f in filas_out if f["sensor"] == b]
        pos = [f for f in fs if (f["mirova_vrp"] or 0) > 0 and f["mirova_tipo"] and any(t.startswith("ALERTA") for t in f["mirova_tipo"])]
        prot = [f for f in pos if f["mirova_vrp"] >= 1]
        print(f"\n== {b}: pasadas nuestras con alerta de MIROVA {len(pos)} (de 1 MW o más {len(prot)}); alertas de MIROVA "
              f"sin pasada nuestra a ±{bp.TOL_S} s: {sin_record[(b, True)]} de 1 MW o más, {sin_record[(b, False)]} menores")
        for nombre in ("prod", "via"):
            con = [f for f in pos if f[nombre]]
            pub = [f for f in con if f[nombre]["pub"]]
            pubp = [f for f in prot if f[nombre] and f[nombre]["pub"]]
            sin = len(pos) - len(con)
            razones = [(f[nombre]["disp"] or 0) / f["mirova_vrp"] for f in pub if f["mirova_vrp"] > 0]
            neg = [f for f in fs if f[nombre] and f[nombre]["lab"] == "neg_limpio"]
            negpub = [f for f in neg if f[nombre]["pub"]]
            r_txt = (f"razón VRP suma/MIROVA mediana {statistics.median(razones):.2f} "
                     f"[p25 {sorted(razones)[len(razones)//4]:.2f}; p75 {sorted(razones)[3*len(razones)//4]:.2f}] n {len(razones)}"
                     if razones else "razón SIN DATO")
            print(f"   {nombre:4s}: publica {len(pub)} de {len(con)} con record (sin record {sin}); "
                  f"protegidas publicadas {len(pubp)} de {len(prot)}; {r_txt}; negativos limpios publicados {len(negpub)} de {len(neg)}")
        # Geometría: VIIRS 375 es la única con resolución para ver ~1 km
        for nombre in ("prod", "via"):
            gs = [(f["utc"], f[nombre]["geo"]) for f in pos if f[nombre] and f[nombre]["pub"] and f[nombre]["geo"]]
            if not gs:
                continue
            por_semana = collections.defaultdict(list)
            for utc, g in gs:
                sem = utc[:8] + ("01-07" if int(utc[8:10]) <= 7 else "08-14" if int(utc[8:10]) <= 14 else
                                 "15-21" if int(utc[8:10]) <= 21 else "22-31")
                por_semana[sem].append(g)
            print(f"   geometría {nombre} (pasadas publicadas con alerta de MIROVA), por semana:")
            for sem, l in sorted(por_semana.items()):
                print(f"      {sem}: n {len(l):2d} | píxeles por pasada med {statistics.median(g['n'] for g in l):.0f} | "
                      f"centroide E {statistics.median(g['cent_e'] for g in l):+.2f} N {statistics.median(g['cent_n'] for g in l):+.2f} km "
                      f"| píxel más caliente a {statistics.median(g['pix_caliente_dist'] for g in l):.2f} km, rumbo med "
                      f"{statistics.median(g['pix_caliente_rumbo'] for g in l):.0f}° | pasadas con píxel al SE {sum(1 for g in l if g['n_se'])} "
                      f"| SE más lejano med {statistics.median([g['max_dist_se'] for g in l if g['max_dist_se'] is not None] or [float('nan')]):.2f} km")
    asimetria_se(filas_out, prod_full, via_full)
    print("\ncontrol de geometría: mediana de distancia de TODOS los píxeles VIIRS 375 publicados (vía):",
          end=" ")
    ds = []
    for f in filas_out:
        if f["sensor"] == "VIIRS375" and f["via"] and f["via"]["pub"]:
            rec = via_full.get((f["via"]["sat"], f["utc"])) or {}
            ds += [math.hypot(*enu_km(p["lat"], p["lon"])) for p in rec.get("anomaly_pixels") or [] if p.get("lat") is not None]
    print(f"{statistics.median(ds):.2f} km (n {len(ds)})" if ds else "SIN DATO")


if __name__ == "__main__":
    main()
