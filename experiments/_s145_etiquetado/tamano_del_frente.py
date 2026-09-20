# -*- coding: utf-8 -*-
"""S145: cuanto pesa, en el dashboard, el sitio tibio lejos del crater que publicamos como summit.

POR QUE. S144 cerro el frente de `keep_peak` con una medida: el lugar donde ese camino conserva su
pixel destaca en el campo de radiancia de MIROVA, pero el 86 % de ese exceso es PERMANENTE, o sea
terreno tibio estable y no un evento de esa noche (A69, A109). Eso no autoriza a apagarlo, porque
la radiancia sola no separa relieve tibio de fuente volcanica permanente (A83): lo que queda
abierto es de ETIQUETADO, no de deteccion (A72).

Pero el traspaso de S145 deja la premisa del frente marcada como SOSPECHA: "el sitio tibio que
publicamos molesta al operador en el dashboard: nadie lo reporto". Antes de proponer cualquier
cambio de display hay que saber de que tamano es el fenomeno. Este script lo mide y nada mas: NO
propone, NO filtra, NO toca el pipeline.

QUE CUENTA. Una pasada entra si (a) el predicado del dashboard la publica y (b) su cumulo primario
cae dentro del radio interno, o sea el dashboard la pinta como summit, PERO (c) su centroide esta a
mas de UMBRAL_KM del crater. Es el caso que el operador ve en rojo lejos del cono.

POR QUE IMPORTA EL RADIO INTERNO POR VOLCAN. No es parejo: va de 3 km (Lastarria) a 20 km (Puyehue
Cordon Caulle). En PCC el lacolito esta a ~7 km del crater y es real (A68), asi que TODO lo que cae
en esos 20 km se pinta summit y el mapa se ve denso sin que haya un error detras. Por eso la cuenta
se da SIEMPRE por volcan: una mediana agrupada acá invierte el veredicto (S126).

Se reporta en records y en NOCHES (A94): el operador vive en noches.

Fuente de verdad: tamano_del_frente.json (regla S91). Ningun numero se escribe a mano.
USO: python experiments/_s145_etiquetado/tamano_del_frente.py [--umbral-km 3.0]
"""
import argparse
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

SALIDA = HERE / "tamano_del_frente.json"


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default=bp.INICIO_DEFECTO)
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--umbral-km", type=float, default=3.0,
                    help="a partir de cuantos km del crater se considera 'lejos'")
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(
        bp.cargar_referencia_unificada(cons, ocr), coords, ventana)

    # A110: el instrumento se valida antes de leer nada. Si el predicado de node no es el del
    # dashboard, toda esta cuenta mide otra cosa.
    identidad = bp.control_identidad_predicado()

    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    def es_lejos(r):
        return r.get("pc_dist") is not None and r["pc_dist"] > a.umbral_km

    publicadas = [r for r in recs if r.get("pub")]
    lejos = [r for r in publicadas if es_lejos(r)]

    por_volcan = {}
    for vol in sorted({r["vol"] for r in recs}):
        pub_v = [r for r in publicadas if r["vol"] == vol]
        lej_v = [r for r in lejos if r["vol"] == vol]
        noches_pub = {r["noche"] for r in pub_v}
        # Una noche cuenta como "solo lejos" si TODO lo que publicamos esa noche esta lejos del
        # crater: son las noches en que el operador no tiene nada cerca del cono con que contrastar.
        noches_lejos = {r["noche"] for r in lej_v}
        # Usa el mismo predicado, no pertenencia a la lista: comparar dicts con `in` es por valor
        # y ademas cuadratico.
        noches_cerca = {r["noche"] for r in pub_v if not es_lejos(r)}
        por_volcan[vol] = {
            "inner_radius_km": inner.get(vol),
            "n_publicadas": len(pub_v),
            "n_publicadas_lejos": len(lej_v),
            "frac_lejos": round(len(lej_v) / len(pub_v), 4) if pub_v else None,
            "mediana_dist_km_de_las_lejos": (
                round(sorted(r["pc_dist"] for r in lej_v)[len(lej_v) // 2], 3) if lej_v else None),
            "n_noches_publicadas": len(noches_pub),
            "n_noches_solo_lejos": len(noches_lejos - noches_cerca),
            "lejos_que_mirova_confirmo": sum(1 for r in lej_v if r["lab"] == "pos"),
            "lejos_que_mirova_miro_y_no_vio": sum(1 for r in lej_v if r["lab"] == "neg_limpio"),
            "por_sensor": dict(collections.Counter(r["b"] for r in lej_v)),
        }

    out = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana": {"inicio": a.inicio, "fin": a.fin},
        "umbral_km": a.umbral_km,
        "control_identidad_predicado": identidad,
        "definiciones": {
            "publicada": "predicado del dashboard de frontend/index.html ejecutado con node (A97)",
            "lejos": (f"centroide del cumulo primario a mas de {a.umbral_km} km del ANCLA DE "
                      "DETECCION, que es de donde mide centroid_dist_km "
                      "(pipeline/clustering.py:103, con _vlat/_vlon de process_viirs_mod.py:1016). "
                      "El ancla es el crater en la mayoria de los volcanes, pero es una eleccion "
                      "del pipeline y no la coordenada nominal del GVP (A3, A6, D17)"),
            "n_noches_solo_lejos": ("noches donde TODO lo publicado de ese volcan esta lejos: "
                                    "el operador no tiene nada cerca del cono con que contrastar"),
        },
        "total": {
            "n_publicadas": len(publicadas),
            "n_publicadas_lejos": len(lejos),
            "frac_lejos": round(len(lejos) / len(publicadas), 4) if publicadas else None,
        },
        "por_volcan": por_volcan,
    }
    SALIDA.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"escrito {SALIDA}")
    print(f"ventana {a.inicio} a {a.fin} | umbral {a.umbral_km} km"
          f" | control de identidad: {identidad}")
    print(f"\nTOTAL: {len(lejos)} de {len(publicadas)} pasadas publicadas estan lejos del crater"
          f" ({out['total']['frac_lejos']})")
    print(f"\n{'volcan':<22}{'inner':>6}{'publ':>7}{'lejos':>7}{'frac':>8}"
          f"{'medkm':>8}{'noches solo lejos':>20}")
    for vol, v in sorted(por_volcan.items(), key=lambda kv: -(kv[1]["frac_lejos"] or 0)):
        print(f"{vol:<22}{v['inner_radius_km'] or 0:>6.0f}{v['n_publicadas']:>7}"
              f"{v['n_publicadas_lejos']:>7}"
              f"{(v['frac_lejos'] if v['frac_lejos'] is not None else 0):>8.3f}"
              f"{(v['mediana_dist_km_de_las_lejos'] or 0):>8.2f}"
              f"{v['n_noches_solo_lejos']:>12} de {v['n_noches_publicadas']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
