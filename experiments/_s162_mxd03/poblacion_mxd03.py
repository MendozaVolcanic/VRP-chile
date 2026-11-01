# -*- coding: utf-8 -*-
"""S162, A/B de MxD03 sobre K (tarea 1.30, pre-registro sellado en experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md,
decision D-48): poblacion del arnes y referencia congelada.

POR QUE. El pre-registro (§5) define la poblacion como el CENSO de las pasadas MODIS nocturnas de la ventana con record
nuestro, etiquetadas con la referencia de MIROVA (no las que K publica, A109). La adenda del sello (punto 3) pide
re-medirlo en el `main` que se congela para el tag, porque los JSON de data/ cambian (reproceso, subida a estandar, A90).
Este script es la unica fuente de la poblacion: el arnes lee `poblacion.json` y el evaluador vuelve a etiquetar con la
misma referencia congelada (MANIFIESTO.json), asi que la etiqueta de aqui sirve para partir el trabajo y para los
controles, no para decidir.

Que hace:
1. Baja consolidado y OCR del remoto de Mirova-v1 fijados a su sha (referencia_mirova_unificada.bajar_remoto) y escribe
   MANIFIESTO.json con el sha del commit y el sha256 del contenido con fin de linea LF (control 6 del §8).
2. Lee los JSON de data/mirova_equivalent del checkout (que es el `main` congelado: el script imprime el sha de HEAD y se
   niega a correr con el arbol de data/ modificado).
3. Etiqueta cada record MODIS de la ventana con banco_paridad (lectura A, regla SN, pareo 120 s) y lo parte en
   protegida / bajo1 / neg_limpio / sin_info / far_ref / ...; agrega tramo de cenit, lado del barrido (regla de S151,
   85 de 85 en M), mitad de pasada partida (otro record mismo volcan y plataforma a 300 s, como el verificador),
   exposicion al borde de inner (delta de M H3, como sustrato_mirova_modis.py) y si K publica (predicado del tablero
   ejecutado con node).
4. Agrupa por granulo (MOD021KM.AAAAJJJ.HHMM) y reparte los granulos en N partes balanceadas por costo estimado
   (3 corridas por record, mas 20 en los records con cenit <= 35 grados).

Las dos preguntas del instrumento:
1. Si el etiquetado estuviera roto, ¿se veria? Controles positivos del §8 punto 7 (Lascar 2026-03-27 07:10 protegida;
   Chillan 2026-06-01 08:15 y Cordon Caulle 2026-06-19 01:15 negativos limpios) impresos y exigidos: si no dan lo
   esperado el script sale con codigo 2. Y la suma de etiquetas tiene que dar el total de records.
2. Si la referencia no se hubiera cargado, ¿se veria distinto? Si: con 0 filas indexadas todo seria sin_info; el script
   lo imprime y sale 2.

Uso (desde la raiz del checkout congelado):
    python -I experiments/_s162_mxd03/poblacion_mxd03.py --ref D:/vrp-trabajo/temporales/s162_mxd03/ref [--partes 24]
        [--sin-bajar]   (usa los CSV ya bajados y verifica su sha256 contra MANIFIESTO.json)
"""
import argparse
import collections
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402

VENTANA = ("2026-03-01", "2026-10-16")        # §5: del 17 al 20 de octubre CMR no sirve MOD021KM
CENIT_R = 35.0                                # §3: R0 a R19 solo con cenit <= 35 grados (record de K)
TOL_S = 120                                   # §5, pareo fijo
# desplazamiento mediano del pixel del crater con MxD03 (M, H3), el mismo de sustrato_mirova_modis.py (§5, expuestas)
DELTA = {("<=25", "f0"): 1.10, ("<=25", "otro"): 0.79, ("25-40", "f0"): 2.82, ("25-40", "otro"): 1.10,
         ("40-50", "f0"): 2.82, ("40-50", "otro"): 1.10, (">50", "f0"): 5.04, (">50", "otro"): 2.48}
CONTROLES = (("Lascar", "2026-03-27 07:10", "protegida"),
             ("NevadosDeChillan", "2026-06-01 08:15", "neg_limpio"),
             ("PuyehueCordonCaulle", "2026-06-19 01:15", "neg_limpio"))
NOMBRES = ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv")


def sha256_lf(path):
    b = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def tramo(z):
    if z is None:
        return "sin_geom"
    return "<=25" if z <= 25 else ("25-40" if z <= 40 else ("40-50" if z <= 50 else ">50"))


def lado(sensor, az):
    if az is None or sensor is None:
        return "?"
    aqua = "AQUA" in sensor
    return "f0" if (aqua and az > 0) or (not aqua and az < 0) else "otro"


def clave_granulo(g):
    return ".".join(str(g).split(".")[:3])


def partir(granulos, n):
    """Reparte granulos en n partes por costo (greedy, determinista: costo descendente, clave ascendente)."""
    costo = {g["clave"]: sum(3 + (20 if r["r_nulos"] else 0) for r in g["records"]) for g in granulos}
    partes = [[] for _ in range(n)]
    carga = [0] * n
    for c in sorted(costo, key=lambda k: (-costo[k], k)):
        i = min(range(n), key=lambda k: (carga[k], k))
        partes[i].append(c)
        carga[i] += costo[c]
    return [sorted(p) for p in partes], carga


def git(*a):
    return subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, text=True).stdout.strip()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--partes", type=int, default=24)
    ap.add_argument("--sin-bajar", action="store_true")
    ap.add_argument("--salida", default=None, help="escribe la poblacion aqui en vez de poblacion.json (re-etiquetado "
                                                   "del evaluador, VMX-04); no toca MANIFIESTO.json")
    args = ap.parse_args()
    ref = Path(args.ref)
    manif = AQUI / "MANIFIESTO.json"

    sucio = git("status", "--porcelain", "--", "data/mirova_equivalent")
    head = git("merge-base", "HEAD", "origin/main")       # el main congelado: la rama del tag sale de el
    rutas = ("data/mirova_equivalent", "pipeline", "scripts", "volcanoes.yaml", "frontend")
    distinto = subprocess.run(["git", "diff", "--quiet", head, "HEAD", "--", *rutas], cwd=RAIZ).returncode
    print("main congelado:", head, "| data/ modificado localmente:", bool(sucio),
          "| HEAD distinto del main congelado en", rutas, ":", bool(distinto))
    if sucio or distinto:
        sys.exit("la poblacion tiene que salir del main congelado sin cambios en data/, pipeline/, scripts/ ni frontend/")

    if args.sin_bajar:
        m = json.loads(manif.read_text(encoding="utf-8"))
        for n in NOMBRES:
            h = sha256_lf(ref / n)
            if h != m["referencia"][n]["sha256_lf"]:
                sys.exit(f"{n}: sha256 {h} distinto del MANIFIESTO {m['referencia'][n]['sha256_lf']}")
        info = {n: {"sha": m["referencia"][n]["sha_commit"], "path": str(ref / n)} for n in NOMBRES}
    else:
        info = bajar_remoto(ref)
    referencia = {n: {"sha_commit": info[n]["sha"], "sha256_lf": sha256_lf(info[n]["path"]),
                      "bytes": Path(info[n]["path"]).stat().st_size} for n in NOMBRES}
    print("referencia:", json.dumps(referencia, ensure_ascii=False))

    filas = cargar_referencia_unificada(Path(info[NOMBRES[0]]["path"]), Path(info[NOMBRES[1]]["path"]))
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    print(f"filas de referencia nocturnas indexadas en la ventana: {n_ref}")
    if not n_ref:
        print("ERROR: referencia vacia")
        sys.exit(2)
    recs = bp.cargar_nuestros(coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)
    modis = [r for r in recs if r["b"] == "MODIS"]

    # campos que banco_paridad no trae: azimut, granulo, sha, publicado guardado (se releen del JSON, misma clave)
    extra = {}
    for vol in bp.VOLS:
        d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            if str(r.get("sensor", "")).startswith("MODIS"):
                pc = r.get("primary_cluster") or {}
                extra[(vol, r.get("datetime_utc"), r.get("sensor"))] = {
                    "az": r.get("sensor_azimuth_deg"), "granule": r.get("granule"),
                    "product_version": r.get("product_version"),
                    "codigo_sha": (r.get("regimen") or {}).get("codigo_sha"),
                    "pc_vrp_guardada": pc.get("vrp_mw"), "dc_guardada": r.get("distance_class")}
    por_vs = collections.defaultdict(list)
    for r in modis:
        por_vs[(r["vol"], r["sensor"])].append(r)

    filas_out, tab = [], collections.Counter()
    for r in modis:
        e = extra[(r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"])]
        lab, vrp_mirova = r["lab"], None
        if lab == "pos":
            vrps = [f["vrp_mw"] or 0 for f in bp.parear(por_vb.get((r["vol"], "MODIS"), []), r["dt"], TOL_S)
                    if bp.es_alerta(f["tipo"])]
            lab = "protegida" if max(vrps) >= 1.0 else "bajo1"
            vrp_mirova = max(vrps)            # M (§6): el VRP de MIROVA de la pasada (la mayor alerta a 120 s)
        t, s = tramo(r["z"]), lado(r["sensor"], e["az"])
        hermanos = [o for o in por_vs[(r["vol"], r["sensor"])]
                    if o is not r and abs((o["dt"] - r["dt"]).total_seconds()) == 300]
        pcd = r.get("pc_dist")
        expuesta = bool(pcd is not None and r["vol"] in inner and abs(pcd - inner[r["vol"]]) < DELTA.get((t, s), 0))
        fila = {"vol": r["vol"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "noche": r["noche"], "sensor": r["sensor"],
                "granule": e["granule"], "clave": clave_granulo(e["granule"]), "z": r["z"], "az": e["az"],
                "tramo": t, "lado": s, "lab": lab, "vrp_mirova": vrp_mirova, "pub_guardada": int(bool(r.get("pub"))),
                "pc_vrp_guardada": e["pc_vrp_guardada"], "dc_guardada": e["dc_guardada"],
                "pc_dist_guardada": pcd, "inner": inner.get(r["vol"]), "expuesta": expuesta,
                "partida": bool(hermanos), "hermanos_lab": sorted(h["lab"] for h in hermanos),
                "codigo_sha": e["codigo_sha"], "product_version": e["product_version"],
                "r_nulos": bool(r["z"] is not None and r["z"] <= CENIT_R)}
        filas_out.append(fila)
        tab[lab] += 1
        tab[lab + "_pubK"] += fila["pub_guardada"]

    print(f"records MODIS en la ventana: {len(filas_out)}")
    tot = {k: v for k, v in sorted(tab.items()) if not k.endswith("_pubK")}
    print("por etiqueta:", tot, "| suma", sum(tot.values()))
    print("K publica por etiqueta:", {k: v for k, v in sorted(tab.items()) if k.endswith("_pubK")})
    est = collections.Counter((f["tramo"], f["lado"], f["lab"]) for f in filas_out)
    for k in sorted(est):
        print("  ", k, est[k])

    ok = True
    for vol, hh, esperado in CONTROLES:
        c = [f["lab"] for f in filas_out if f["vol"] == vol and f["dt"] == hh]
        bien = c == [esperado]
        ok &= bien
        print(f"control {vol} {hh}: {c} (esperado [{esperado}]) {'OK' if bien else 'FALLA'}")

    gran = collections.defaultdict(list)
    for f in filas_out:
        gran[f["clave"]].append(f)
    granulos = [{"clave": c, "records": sorted(v, key=lambda x: x["vol"])} for c, v in sorted(gran.items())]
    n35 = sum(f["r_nulos"] for f in filas_out)
    g35 = sum(1 for g in granulos if any(f["r_nulos"] for f in g["records"]))
    print(f"granulos {len(granulos)}; records con cenit <= {CENIT_R:g}: {n35} en {g35} granulos")
    print(f"mitades de pasada partida: {sum(f['partida'] for f in filas_out)}; expuestas: "
          f"{[(f['vol'], f['dt'], f['lab']) for f in filas_out if f['expuesta'] and f['lab'] in ('protegida', 'bajo1')]}")
    shas = collections.Counter((f["codigo_sha"] or "?")[:9] for f in filas_out)
    print(f"codigo_sha distintos: {len(shas)}; mayores: {shas.most_common(6)}")
    print("product_version:", dict(collections.Counter(f["product_version"] for f in filas_out)))

    partes, carga = partir(granulos, args.partes)
    print(f"partes {args.partes}: corridas estimadas por parte min {min(carga)} max {max(carga)} total {sum(carga)}")

    pob = {"pre_registro": "experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md (sello D-48)",
           "checkout": head, "ventana": VENTANA, "tol_s": TOL_S, "cenit_r": CENIT_R, "regla_minimas": "SN",
           "referencia": referencia, "granulos": granulos, "partes": partes}
    destino = Path(args.salida) if args.salida else AQUI / "poblacion.json"
    destino.write_text(json.dumps(pob, ensure_ascii=False, indent=0), encoding="utf-8")
    if not args.sin_bajar and not args.salida:
        manif.write_text(json.dumps({"checkout": head, "ventana": VENTANA, "referencia": referencia},
                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito", destino)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
