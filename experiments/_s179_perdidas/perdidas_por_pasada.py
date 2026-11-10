"""S179: qué alertas nocturnas de MIROVA no publica producción, por sensor, volcán y magnitud, y qué traía nuestro record.

POR QUÉ: Nicolás preguntó qué umbrales nos hacen perder alertas. El banco de paridad (scripts/banco_paridad.py) da el
recall agregado; aquí se listan las pasadas `pos` que el predicado del tablero NO publica, con el VRP de MIROVA de esa
pasada (para separar protegidas de 1 MW o más de las débiles) y lo que vio nuestro detector.

Mismo instrumento que el banco: importa sus funciones sin reescribirlas (etiquetas, pareo a +-TOL_S, predicado del
tablero ejecutado con node, regla de mínimas D-9). Se corre desde un worktree de main (los datos de producción):
  cd <worktree main> && python <este script> --inicio 2026-04-09 --fin 2026-11-09 --out <json>

Las dos preguntas del instrumento: (1) si el predicado publicara todo, la lista saldría vacía y si no publicara nada,
saldría igual a todas las `pos`: se imprime ese control; (2) un instrumento muerto daría 0 `pos`: se imprime n_pos.
"""
import argparse
import collections
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ventana = (a.inicio, a.fin)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    # Registros completos de producción para describir lo que vio el detector en las pasadas perdidas.
    completos = {}
    for vol in bp.VOLS:
        d = json.loads((bp.DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            completos[(vol, r.get("sensor"), r.get("datetime_utc"))] = r

    pos = [r for r in recs if r["lab"] == "pos"]
    # La unidad del operador es la noche (A94): ¿publicamos ALGO de ese volcán esa noche, en cualquier sensor?
    noche_pub = {(r["vol"], r["noche"]) for r in recs if r["pub"]}
    perdidas = []
    for r in pos:
        if r["pub"]:
            continue
        filas_p = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        vrp_m = max((f["vrp_mw"] or 0) for f in filas_p) if filas_p else None
        fuentes = sorted({f["source"] for f in filas_p})
        full = completos.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))) or {}
        pc = full.get("primary_cluster") or {}
        perdidas.append({
            "volcan": r["vol"], "sensor": r["b"], "satelite": r["sensor"], "utc": r["dt"].strftime("%Y-%m-%d %H:%M"),
            "vrp_mirova_mw": vrp_m, "fuentes_mirova": fuentes, "dist_mirova_tabla_km": r.get("dist_ref_tabla"),
            "protegida": (vrp_m or 0) >= 1.0,
            "via": full.get("via_codigo_mirova"), "n_anom": full.get("n_anomalous_pixels"),
            "nuestro_vrp_mw": pc.get("vrp_mw"), "dist_class": full.get("distance_class"),
            "dist_final_km": full.get("final_hotspot_dist_km"), "z": full.get("sensor_zenith_deg"),
            "disp": r.get("disp"), "noche_con_otra_publicacion": (r["vol"], r["noche"]) in noche_pub,
        })

    res = collections.defaultdict(lambda: collections.Counter())
    for p in perdidas:
        clave = (p["sensor"], p["volcan"])
        res[clave]["perdidas"] += 1
        res[clave]["protegidas"] += p["protegida"]
        res[clave]["sin_anomalia_nuestra"] += (p["n_anom"] or 0) == 0
        res[clave]["solo_ocr"] += p["fuentes_mirova"] == ["OCR"]
    n_pos = collections.Counter((r["b"], r["vol"]) for r in pos)

    print(f"ventana {a.inicio} a {a.fin}; pos {len(pos)}; perdidas {len(perdidas)}; "
          f"protegidas perdidas {sum(p['protegida'] for p in perdidas)}")
    print("control: con todo publicado, perdidas 0; con nada publicado, perdidas = pos =", len(pos))
    print(f"{'sensor':9s} {'volcan':22s} pos perd prot sin_anom solo_ocr")
    for (s, v), c in sorted(res.items()):
        print(f"{s:9s} {v:22s} {n_pos[(s, v)]:3d} {c['perdidas']:4d} {c['protegidas']:4d} {c['sin_anomalia_nuestra']:8d} {c['solo_ocr']:8d}")
    mags = collections.Counter()
    for p in perdidas:
        m = p["vrp_mirova_mw"] or 0
        mags[(p["sensor"], "<0.3" if m < 0.3 else "0.3-1" if m < 1 else ">=1")] += 1
    print("magnitud MIROVA de las perdidas:", dict(sorted(mags.items())))
    for p in sorted((p for p in perdidas if p["protegida"]), key=lambda p: p["utc"]):
        print(f"  protegida perdida: {p['utc']} {p['satelite']} {p['volcan']} MIROVA {p['vrp_mirova_mw']} MW "
              f"{p['fuentes_mirova']} dist_tabla {p['dist_mirova_tabla_km']} | nuestro n_anom {p['n_anom']} "
              f"vrp {p['nuestro_vrp_mw']} {p['dist_class']} {p['dist_final_km']} km | via {p['via']} | "
              f"otra publicacion esa noche: {p['noche_con_otra_publicacion']}")
    noches_perdidas = {(p["volcan"], p["utc"][:10]) for p in perdidas if not p["noche_con_otra_publicacion"]}
    print(f"noches de volcán con alerta de MIROVA y NADA publicado por nosotros: {len(noches_perdidas)}")
    Path(a.out).write_text(json.dumps({"ventana": ventana, "n_pos": len(pos), "perdidas": perdidas},
                                      ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
