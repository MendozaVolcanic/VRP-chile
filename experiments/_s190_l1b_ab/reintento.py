# FICHA (SDA, CPLT 372): reintento de solo lectura del A/B de fase de grilla (PREREGISTRO.md). No es detección de producción.
"""Reintenta gránulos que ab_fase.py no pudo bajar porque el cortacircuito de búsqueda de CMR (pipeline/fetch.py, S116)
se encendió con un solo ReadTimeout y saltó todo lo que venía después en esa parte (run 44016316141, intentos 1 y 2).

DESVÍO OPERATIVO, anotado en el informe: no cambia la medición ni la regla. Usa las mismas funciones de ab_fase.py
(bajar, correr_brazos, reproduce) y el mismo manifiesto sellado; solo resetea el cortacircuito antes de cada búsqueda y
prueba hasta 3 veces por gránulo. Escribe out/s190_reintento.json (el ensamblado lo reemplaza en la parte de origen).

Uso: python experiments/_s190_l1b_ab/reintento.py --granulos "G1,G2,..." --out out
"""
import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for p in (ROOT, AQUI):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import ab_fase as AB  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

INTENTOS = 3


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--granulos", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=os.environ.get("VRP_TMP_DIR", str(ROOT / "granulos_tmp")))
    a = ap.parse_args()
    if not (os.environ.get("EARTHDATA_TOKEN") or "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 2
    from pipeline.fetch import auth, reset_transient_breakers
    auth()
    pedidos = [g.strip() for g in a.granulos.split(",") if g.strip()]
    man = json.load(open(AQUI / "manifiesto_s190.json", encoding="utf-8"))["pasadas"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res, faltan = [], 0
    for gran in pedidos:
        ps = [p for p in man if p["l1b"] == gran]
        if not ps:
            raise SystemExit(f"{gran} no está en el manifiesto sellado")
        tmp = Path(a.tmp) / "s190_reintento"
        ok, ultimo = False, None
        for intento in range(1, INTENTOS + 1):
            print("\n== %s intento %d (%s)" % (gran, intento, ", ".join(p["volcan"] for p in ps)), flush=True)
            try:
                reset_transient_breakers()
                tmp.mkdir(parents=True, exist_ok=True)
                k1, k2 = AB.PRODUCTOS[gran[:3]]
                v0 = ps[0]["vent"]
                rl, nota = AB.bajar(k1, gran, v0[0], v0[1], tmp)
                if rl is None:
                    raise RuntimeError(nota)
                reset_transient_breakers()
                rg, nota_g = AB.bajar(k2, gran, v0[0], v0[1], tmp, exacto=False)
                if rg is None:
                    raise RuntimeError(nota_g)
                rad = MV.leer_radiancia_l1b(rl)
                lat, lon, ang = MV.leer_geo_l1b(rg)
                nuevos = []
                for p in ps:
                    item = {k: p[k] for k in ("volcan", "dt", "l1b", "cat", "estrato", "rol", "ref")}
                    item.update({"gran_usado": rl.name, "geo_usado": rg.name, "nota_granulo": nota, "reintento": intento})
                    item["brazos"] = AB.correr_brazos(rad, lat, lon, ang, p)
                    item["reproduce"] = AB.reproduce(item["brazos"].get("A"), p["ref"])
                    item["ok"] = True
                    print("  %s %s reproduce=%s n_pix=%s" % (p["volcan"], p["cat"], item["reproduce"],
                          {b: v.get("n_pix") for b, v in item["brazos"].items()}), flush=True)
                    nuevos.append(item)
                res.extend(nuevos)   # solo si el gránulo entero salió: un reintento no deja pasadas duplicadas
                ok = True
                break
            except Exception as e:
                ultimo = "%s: %s" % (type(e).__name__, e)
                print("  FALLA intento %d: %s" % (intento, ultimo))
                traceback.print_exc()
                time.sleep(20 * intento)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        if not ok:
            for p in ps:
                res.append({k: p[k] for k in ("volcan", "dt", "l1b", "cat", "estrato", "rol")} | {"ok": False, "error": ultimo})
                faltan += 1
        json.dump(res, open(out / "s190_reintento.json", "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
    print("\npasadas medidas: %d de %d" % (len(res) - faltan, len(res)))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
