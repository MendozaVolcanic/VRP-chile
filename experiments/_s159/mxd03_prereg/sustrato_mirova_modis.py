"""S159, pre-registro de MxD03: sustrato MODIS contra MIROVA, NO condicionado a lo que publica K.

POR QUÉ. El probe M eligió records `summit` (publicados por K): cualquier perturbación de la posición sobre una
población elegida por pasar un umbral apaga más de lo que enciende (A109, verificador de M). El A/B tiene que mirar
las pasadas que MIROVA etiqueta (alertas protegidas, alertas bajo 1 MW, negativos limpios), publique K o no.

Qué cuenta, por pasada MODIS nocturna con record nuestro (11 Tier A), en la ventana pedida:
- etiqueta de `banco_paridad.etiquetar` (pos / neg_limpio / far_ref / sin_info / ...), con la tolerancia de pareo
  de producción (120 s) y con 300 s (el desfase de gránulo que midió el verificador de M);
- pos partido en protegida (alguna alerta de la pasada con VRP de 1 MW o más, lectura A) y bajo 1 MW;
- tramo de cenit del record (<=25, 25-40, 40-50, >50) y lado del barrido (regla de S151, 85 de 85 en M);
- si K publica (predicado del tablero con node, `pub` de `banco_paridad.cargar_nuestros`);
- exposición: pasadas cuyo cúmulo primario cae a menos de delta(cenit, lado) del borde de inner, con delta el
  desplazamiento mediano medido en M (`experiments/_s159/m/INFORME.md` H3): es un TECHO de lo que MxD03 puede
  mover por la vía del borde, no una predicción (no ve el fondo ni la selección).
Y las noches-volcán: con alerta MODIS de MIROVA, y cuántas tienen además publicación VIIRS de K (si la noche ya
está cubierta por VIIRS, un cambio MODIS no cambia lo que el operador ve esa noche, A94).

Las dos preguntas del instrumento:
1. Si el etiquetado estuviera roto, ¿se vería? Control positivo: Láscar 2026-02-11 07:00 (Aqua) tiene que salir
   `pos` 0,48 MW (verificador de M). Y la suma de etiquetas tiene que dar el total de pasadas.
2. Si la referencia no se hubiera cargado, ¿se vería distinto? Sí: imprime filas de referencia indexadas y sus
   shas; con 0 filas todas las pasadas serían `sin_info` y el script lo dice.

Uso: python sustrato_mirova_modis.py --data DIR_JSON --dl DIR_REF --desde 2026-03-01 --hasta 2026-10-16
     [--excluir 2026-10-17,2026-10-18,2026-10-19,2026-10-20]
"""
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\vrp-trabajo\s159-pruebas")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402

# desplazamiento mediano del píxel del cráter con MxD03 (M, H3; km). Bajo 40° M midió 1,10 (f0) y 0,79 (otro)
# cerca del nadir con n = 4 cada uno; para 25-40 no hay medición propia: se usa el valor de 40-50 del lado
# contrario como cota (SIN DATO, declarado).
DELTA = {("<=25", "f0"): 1.10, ("<=25", "otro"): 0.79, ("25-40", "f0"): 2.82, ("25-40", "otro"): 1.10,
         ("40-50", "f0"): 2.82, ("40-50", "otro"): 1.10, (">50", "f0"): 5.04, (">50", "otro"): 2.48}


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def tramo(z):
    if z is None:
        return "sin_geom"
    return "<=25" if z <= 25 else ("25-40" if z <= 40 else ("40-50" if z <= 50 else ">50"))


def lado(sensor, az):
    if az is None or sensor is None:
        return "?"
    aqua = "AQUA" in sensor
    return "f0" if (aqua and az > 0) or (not aqua and az < 0) else "otro"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    data = Path(arg("--data"))
    ventana = (arg("--desde", "2026-03-01"), arg("--hasta", "2026-10-16"))
    excluir = set((arg("--excluir", "") or "").split(",")) - {""}
    info = bajar_remoto(Path(arg("--dl")))
    print("referencia:", {k: v["sha"] for k, v in info.items()})
    filas = cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                        Path(info["registro_vrp_ocr.csv"]["path"]))
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    print("inner (frontend):", inner)
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
    print(f"filas de referencia nocturnas indexadas en la ventana (todos los sensores): {n_ref}")
    recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
    # azimut no viene en el rec de banco_paridad: se relee del JSON (mismo orden de filtros)
    az = {}
    for vol in bp.VOLS:
        d = json.load(open(data / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            az[(vol, r.get("datetime_utc"), r.get("sensor"))] = (r.get("sensor_azimuth_deg"), r.get("granule"))
    recs = [r for r in recs if r["noche"] not in excluir]
    modis = [r for r in recs if r["b"] == "MODIS"]
    viirs_pub_noche = {(r["vol"], r["noche"]) for r in recs if r["b"] != "MODIS" and r.get("pub")}
    print(f"pasadas nuestras en la ventana: {len(recs)} (MODIS {len(modis)}); días excluidos: {sorted(excluir)}")

    salida = {}
    for tol in (120, 300):
        bp.TOL_S = tol
        # parear usa el valor por defecto ligado en la definición: se le pasa tol envolviendo
        orig = bp.parear
        bp.parear = lambda lista, t, tol=tol, _o=orig: _o(lista, t, tol)
        bp.etiquetar(modis, por_vb, ns, nv)
        bp.parear = orig
        tab = collections.defaultdict(collections.Counter)
        for r in modis:
            azi, gran = az.get((r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"]), (None, None))
            t, s = tramo(r["z"]), lado(r["sensor"], azi)
            filas_p = bp.parear(por_vb.get((r["vol"], "MODIS"), []), r["dt"], tol)
            vrps = [f["vrp_mw"] or 0 for f in filas_p if bp.es_alerta(f["tipo"])]
            lab = r["lab"]
            if lab == "pos":
                lab = "protegida" if max(vrps) >= 1.0 else "bajo1"
            r["lab2"], r["tramo"], r["lado"] = lab, t, s
            c = tab[(t, s)]
            c[lab] += 1
            c[lab + "_pubK"] += int(bool(r.get("pub")))
            pcd = r.get("pc_dist")
            if pcd is not None and r["vol"] in inner:
                cerca = abs(pcd - inner[r["vol"]]) < DELTA.get((t, s), 0)
                c[lab + "_expuesta"] += int(cerca)
        salida[tol] = {f"{k[0]}|{k[1]}": dict(v) for k, v in tab.items()}
        tot = collections.Counter()
        for v in tab.values():
            for k2, n in v.items():
                if not k2.endswith(("_pubK", "_expuesta")):
                    tot[k2] += n
        print(f"\n=== tolerancia de pareo {tol} s; total por etiqueta: {dict(tot)} (suma {sum(tot.values())})")
        for k in sorted(tab):
            print(f"  {k[0]:>8} {k[1]:>4}: {dict(sorted(tab[k].items()))}")
        # controles: casos con etiqueta conocida (verificador de M y marca S151 de D18)
        for vol, hh, esperado in (("Lascar", "2026-02-11 07:00", "bajo1 0,48 MW"),
                                  ("Lascar", "2026-03-27 07:10", "protegida 1,0 MW (veto de la caja, D18)"),
                                  ("NevadosDeChillan", "2026-06-01 08:15", "neg (RUTINA)"),
                                  ("PuyehueCordonCaulle", "2026-06-19 01:15", "neg (RUTINA)")):
            ctl = [r for r in modis if r["vol"] == vol and r["dt"].strftime("%Y-%m-%d %H:%M") == hh]
            print(f"  control {vol} {hh} (esperado {esperado}):",
                  [(r["lab2"], r["sensor"], r["tramo"], r["lado"]) for r in ctl] or "fuera de la ventana o sin record")
        # detalle de alertas expuestas al borde
        for r in modis:
            if r["lab2"] in ("protegida", "bajo1") and r.get("pc_dist") is not None and \
                    abs(r["pc_dist"] - inner[r["vol"]]) < DELTA.get((r["tramo"], r["lado"]), 0):
                print(f"    expuesta: {r['vol']} {r['dt']:%Y-%m-%d %H:%M} {r['sensor']} {r['lab2']} z={r['z']} "
                      f"lado={r['lado']} pc_dist={r['pc_dist']} inner={inner[r['vol']]} pubK={r.get('pub')}")
        # alertas que K no publica (lo que X podría recuperar), con su cúmulo
        for r in modis:
            if r["lab2"] in ("protegida", "bajo1") and not r.get("pub"):
                print(f"    K no publica: {r['vol']} {r['dt']:%Y-%m-%d %H:%M} {r['sensor']} {r['lab2']} z={r['z']} "
                      f"lado={r['lado']} dc={r['dc']} pc_dist={r['pc_dist']} pc_vrp={r['pc_vrp']}")
        # por volcán (poder del veto y regla de dos volcanes) y estrato donde actúa el fondo (cúmulo summit cerca de 0 MW)
        pv = collections.defaultdict(collections.Counter)
        for r in modis:
            pv[r["vol"]][r["lab2"]] += 1
            if r["lab2"] in ("protegida", "bajo1") and r.get("pub"):
                pv[r["vol"]]["alerta_pubK"] += 1
            if r["dc"] == "summit" and r.get("pc_vrp") is not None and r["pc_vrp"] <= 0.1:
                pv[r["vol"]][f"fondo_actua_{r['lab2']}"] += 1
        for vol in bp.VOLS:
            print(f"    por volcán {vol}: {dict(sorted(pv[vol].items()))}")
        # noches con alerta MODIS de MIROVA
        noches_pos = collections.defaultdict(set)
        for r in modis:
            if r["lab2"] in ("protegida", "bajo1"):
                noches_pos[r["lab2"]].add((r["vol"], r["noche"]))
        for lab, s in noches_pos.items():
            cub = sum(1 for x in s if x in viirs_pub_noche)
            print(f"  noches-volcán con {lab} MODIS: {len(s)}; con publicación VIIRS de K esa noche: {cub}")
    out = Path(__file__).with_name("sustrato_mirova_modis.json")
    out.write_text(json.dumps({"ventana": ventana, "excluir": sorted(excluir), "ref": {k: v['sha'] for k, v in info.items()},
                               "tabla": salida}, indent=1, ensure_ascii=False), encoding="utf-8")
    print("escrito", out)


if __name__ == "__main__":
    main()
