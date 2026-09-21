# -*- coding: utf-8 -*-
"""S149. Evalua UNA ventana del pre-registro v3, de punta a punta y en el orden que el pre-registro exige:
   1. extrae las salidas de los runs (git archive CON RUTA; un run posterior pisa al anterior: reparaciones);
   2. COBERTURA pareja entre brazos, ANTES de mirar ningun resultado (A108). Si falla, se detiene;
   3. determinismo contra el gemelo, si se le pasa;
   4. arma la tabla contra la referencia CONGELADA de la ventana y corre medir_predicciones.py.

  python evaluar_ventana.py --nombre mayo --desde 2026-05-01 --hasta 2026-05-31 \
      --control _s146_ab_sin_test1 --brazo _s147_ab_sin_test1_max --runs 35599902448 \
      [--gemelo _s149_ab_sin_test1_gemelo --runs-gemelo 35599941522] [--sensor VIIRS375] --tmp DIR
"""
import argparse, collections, io, json, shutil, subprocess, sys, tarfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
MAX_FALTAN = 0.01   # fraccion de pasadas que puede faltarle a un brazo respecto del otro, por volcan


def extraer(runs, tmp):
    base = tmp / "runs"
    for r in runs:
        subprocess.run(["git", "fetch", "-q", "origin", "refs/heads/s146-ab/%s:refs/remotes/origin/s146-ab/%s" % (r, r)], cwd=RAIZ, check=True)
        ruta = "experiments/_s146_ab_sin_test1/salidas/%s" % r
        tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(tar)).extractall(base)
    return base / "experiments" / "_s146_ab_sin_test1" / "salidas"


def unir(salidas, runs, perfil, destino):
    d = destino / perfil; d.mkdir(parents=True, exist_ok=True); origen = {}
    for r in runs:   # en orden: el posterior pisa
        for f in sorted((salidas / str(r) / perfil).glob("*.json")) if (salidas / str(r) / perfil).exists() else []:
            shutil.copy(f, d / f.name); origen[f.stem] = r
    return d, origen


def main():
    ap = argparse.ArgumentParser()
    for k in ("nombre", "desde", "hasta", "control", "brazo", "tmp"): ap.add_argument("--" + k, required=True)
    ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--gemelo"); ap.add_argument("--runs-gemelo", nargs="*", default=[])
    ap.add_argument("--sensor", default="VIIRS375"); ap.add_argument("--congelado", help="carpeta con los dos CSV; por defecto _congelado/<nombre>")
    a = ap.parse_args()
    tmp = Path(a.tmp) / a.nombre; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    salidas = extraer(list(dict.fromkeys(a.runs + a.runs_gemelo)), tmp)
    dc, oc = unir(salidas, a.runs, a.control, tmp / "union"); db, ob = unir(salidas, a.runs, a.brazo, tmp / "union")
    print("== ventana %s, %s a %s | control %s | brazo %s" % (a.nombre, a.desde, a.hasta, a.control, a.brazo))
    print("   archivos del control:", {v: r for v, r in sorted(oc.items())}); print("   archivos del brazo:  ", {v: r for v, r in sorted(ob.items())})
    C = AQUI / "_congelado" / a.nombre.split("_")[0]
    if not C.exists(): C = AQUI / "_congelado" / a.nombre
    if a.congelado: C = Path(a.congelado)
    tabla = tmp / "tabla.json"
    subprocess.run([sys.executable, str(AQUI / "armar_tabla.py"), "--control", str(dc), "--brazo", str(db), "--cons", str(C / "registro_vrp_consolidado.csv"),
                    "--ocr", str(C / "registro_vrp_ocr.csv"), "--desde", a.desde, "--hasta", a.hasta, "--out", str(tabla)], check=True, stderr=subprocess.DEVNULL)
    T = json.loads(tabla.read_text(encoding="utf-8"))["pasadas"]
    # ---- 2. cobertura, ANTES de mirar resultados
    print("\n== COBERTURA (antes de mirar nada)")
    por = collections.defaultdict(lambda: collections.Counter())
    for k, v in T.items():
        vol, b, _ = k.split("|"); por[(vol, b)]["ambos" if len(v) == 2 else ("solo_" + next(iter(v)))] += 1
    mal = []
    for (vol, b), c in sorted(por.items()):
        tot = sum(c.values()); falta = c["solo_control"] + c["solo_brazo"]
        if falta: print("   %-20s %-8s ambos %4d | solo control %3d | solo brazo %3d" % (vol, b, c["ambos"], c["solo_control"], c["solo_brazo"]))
        if falta / tot > MAX_FALTAN: mal.append((vol, b, falta, tot))
    vols = {k.split("|")[0] for k in T}
    print("   pasadas %d | en ambos brazos %d | volcanes %d" % (len(T), sum(1 for v in T.values() if len(v) == 2), len(vols)))
    if mal or len(vols) < len(oc) or set(oc) != set(ob):
        print("   COBERTURA DESPAREJA: %s | volcanes control %d, brazo %d. INDECIDIBLE: repetir el job corto y volver a evaluar. No se mira nada mas." % (mal, len(oc), len(ob)))
        return 2
    print("   cobertura pareja: OK")
    # ---- 3. determinismo
    if a.gemelo:
        dg, og = unir(salidas, a.runs_gemelo or a.runs, a.gemelo, tmp / "union"); tg = tmp / "tabla_gemelo.json"
        dcl = tmp / "union" / "_control_lascar"; dcl.mkdir(exist_ok=True)
        for f in dg.glob("*.json"): shutil.copy(dc / f.name, dcl / f.name)
        subprocess.run([sys.executable, str(AQUI / "armar_tabla.py"), "--control", str(dcl), "--brazo", str(dg), "--cons", str(C / "registro_vrp_consolidado.csv"),
                        "--ocr", str(C / "registro_vrp_ocr.csv"), "--desde", a.desde, "--hasta", a.hasta, "--out", str(tg)], check=True, stderr=subprocess.DEVNULL)
        G = json.loads(tg.read_text(encoding="utf-8"))["pasadas"]; amb = [v for v in G.values() if len(v) == 2]
        ig = sum(1 for v in amb if v["control"]["pub"] == v["brazo"]["pub"])
        print("\n== DETERMINISMO (gemelo de B sobre %s): %d pasadas, en ambos %d, misma decision de publicar %d (%.1f %%) | %s" % (
            sorted(og), len(G), len(amb), ig, 100 * ig / len(amb) if amb else 0, "OK" if amb and ig / len(amb) >= .98 and len(amb) == len(G) else "FALLA: INDECIDIBLE"))
    # ---- 4. predicciones
    print("\n== PREDICCIONES")
    sys.stdout.flush()
    subprocess.run([sys.executable, str(AQUI / "medir_predicciones.py"), str(tabla), a.sensor])
    return 0


if __name__ == "__main__":
    sys.exit(main())
