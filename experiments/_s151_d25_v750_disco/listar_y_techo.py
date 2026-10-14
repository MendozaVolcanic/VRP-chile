# -*- coding: utf-8 -*-
"""S151 (loop 1.5): de dónde salen los 268 negativos de VIIRS 750 y qué se puede medir sin granules.

EL FENÓMENO. En una cumbre nevada de noche, el píxel de 750 m del cráter queda más frío que la mediana
del anillo de 5 a 25 km (valle tibio). El exceso sale negativo y se recorta a 0,0 MW: cráter "detectado"
pero mudo. El fondo por vecinos (D25) lo compararía con su propio entorno inmediato.

QUÉ HACE ESTE SCRIPT (sólo lectura, sin red salvo node local):
  1. Reconstruye la población de docs/AUDIT_S149.md:81 y
     docs/audit_s149/plan_final/VERIFICADOR_MAGNITUD_CERO.md §5 con la MISMA definición que
     experiments/_s149_audit/verificador_magnitud_cero/v3_negativos.py (ventana 2026-06-01 a 2026-09-21,
     V750, negativo limpio, cúmulo primario summit con 0,0 MW dentro del inner) y la congela en
     pasadas.json (con el nombre del granule de cada pasada) para el probe de CI.
  2. Dice qué datos de los vecinos persiste el record (respuesta: ninguno; se cuenta, no se afirma).
  3. TECHO medido con el predicado real del tablero (node sobre frontend/index.html): cuántas de esas
     pasadas publicarían si el fondo nuevo les diera CUALQUIER magnitud positiva. No es el resultado de
     D25: es la cota superior, y dice si la pregunta se reduce al SIGNO del contraste con los vecinos.
  4. Escala: cuántos MW da 1 K de contraste en un píxel de 750 m a la BT de cada cráter (conversión
     determinista con las constantes del pipeline, no una medición).

CONTROLES (fijados ANTES de mirar la salida; cualquiera que falle invalida el techo):
  C1  control_identidad_predicado de banco_paridad: validez [0,1,1,1,0] y publicación [1,0].
  C2  la población sin modificar publica 0 (está definida por cúmulo summit en 0,0 MW: si alguna publica,
      la copia o la definición están mal).
  C3  el campo que se muta es el que decide: en las pasadas V750 que HOY publican con cúmulo > 0, poner
      pc.vrp_mw = 0 y vrp_mw = 0 debe apagar el 100 %, y dejarlas intactas debe publicar el 100 %.
  C4  la población de hoy debe contener a la de S149: `reconstruir_268.py` rehace el cálculo con el
      arnés, los JSON y la referencia del commit de S149 (da 3.118 / 268 / 28, los números del
      informe) y deja las claves en lista_268_s149.json. Las 268 y las 28 tienen que seguir hoy en la
      condición; si alguna salió, se lista. (first_processed_utc no sirve de marca: el reproceso de
      octubre lo reescribe; medido, da 55 de 271.)

Fuente de verdad: techo.json (regla S91). USO: python experiments/_s151_d25_v750_disco/listar_y_techo.py
"""
import collections
import copy
import io
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402

INI, FIN = "2026-06-01", "2026-09-21"
MAGNITUDES_SONDA = (0.001, 0.1, 1.0, 10.5)   # 10,5 > 10 MW cruza el corte de isCirrusArtifact
N_CONTROL_PROBE = 40                          # pasadas que ya publican, para el control del probe
SEMILLA = 151


def s0(x, inner):
    """Cúmulo primario summit con 0,0 MW dentro del inner (definición de v3_negativos.py)."""
    r = x["r"]
    pc = r.get("primary_cluster")
    if not pc or (pc.get("vrp_mw") or 0) != 0 or r.get("distance_class") != "summit":
        return False
    d = pc.get("centroid_dist_km")
    return d is not None and d <= inner[x["vol"]]


def caso(r, inner_km, pc_mw=None, rec_mw=None):
    c = copy.deepcopy({k: r.get(k) for k in bp.CAMPOS_JS})
    if pc_mw is not None and c.get("primary_cluster") is not None:
        c["primary_cluster"]["vrp_mw"] = pc_mw
    if rec_mw is not None:
        c["vrp_mw"] = rec_mw
    return [c, inner_km]


def mw_por_k(bt_k):
    """MW que da 1 K de exceso (centrado en bt_k) en un píxel M13 de área nadir fija."""
    import numpy as np
    from pipeline.process_viirs_mod import (M13_LAMBDA, NADIR_PIXEL_AREA_M2, WOOSTER_COEFF,
                                            bt_to_spectral_radiance)
    dl = float(bt_to_spectral_radiance(np.float64(bt_k + 0.5), M13_LAMBDA)
               - bt_to_spectral_radiance(np.float64(bt_k - 0.5), M13_LAMBDA))
    return NADIR_PIXEL_AREA_M2 * WOOSTER_COEFF * dl / 1e6


def _git_show(rev, ruta):
    import subprocess
    o = subprocess.run(["git", "show", f"{rev}:{ruta}"], capture_output=True, cwd=ROOT, check=True)
    return o.stdout


def poblacion(coords, inner, rev=None, rev_ref=None):
    """Records V750 nocturnos de la ventana, etiquetados; rev=None lee el disco, si no, ese commit.

    rev_ref: commit del snapshot de la referencia (por defecto el mismo `rev`).
    """
    rev_ref = rev_ref or rev
    if rev is None:
        filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
        cargar = lambda vol: json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))  # noqa: E731
    else:
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        rutas = []
        for snap in (SNAP_CONS, SNAP_OCR):
            dst = tmp / snap.name
            dst.write_bytes(_git_show(rev_ref, snap.relative_to(ROOT).as_posix()))
            rutas.append(dst)
        filas = cargar_referencia_unificada(*rutas)
        cargar = lambda vol: json.loads(_git_show(rev, f"data/mirova_equivalent/{vol}.json"))  # noqa: E731
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (INI, FIN))
    recs = []
    for vol in bp.VOLS:
        for r in cargar(vol)["records"]:
            if bp.bucket(r.get("sensor")) != "VIIRS750" or not (INI <= r.get("datetime_utc", "")[:10] <= FIN):
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if bp.es_pasada_diurna_descartada("VIIRS750", *coords[vol], dt):
                continue
            recs.append({"vol": vol, "b": "VIIRS750", "dt": dt, "noche": r["datetime_utc"][:10], "r": r})
    pubs = bp.correr_node([[{k: x["r"].get(k) for k in bp.CAMPOS_JS}, inner[x["vol"]]] for x in recs])
    for x, p in zip(recs, pubs):
        x["pub"] = p[4]
    bp.etiquetar(recs, por_vb, ns, nv)
    return recs


def clave(x):
    return (x["vol"], x["r"]["datetime_utc"], x["r"]["sensor"])


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    recs = poblacion(coords, inner)

    N = [x for x in recs if x["lab"] == "neg_limpio" and s0(x, inner)]
    P = [x for x in recs if x["lab"] == "pos" and s0(x, inner)]
    PUB = [x for x in recs if x["lab"] in ("neg_limpio", "pos") and x["pub"]
           and ((x["r"].get("primary_cluster") or {}).get("vrp_mw") or 0) > 0]
    out = {"generado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "ventana": [INI, FIN], "definicion": "V750, nocturna, neg_limpio (banco_paridad.etiquetar), "
           "primary_cluster.vrp_mw == 0, distance_class summit, centroid_dist_km <= inner del tablero",
           "referencia": {"cons": str(SNAP_CONS.relative_to(ROOT)), "ocr": str(SNAP_OCR.relative_to(ROOT)),
                          "sha_cons": bp.sha_git(SNAP_CONS)}}

    # ---- C1
    val, pub = bp.control_identidad_predicado()
    c1 = val == [0, 1, 1, 1, 0] and pub == [1, 0]
    # ---- C2
    base = bp.correr_node([caso(x["r"], inner[x["vol"]]) for x in N + P])
    c2 = sum(b[4] for b in base) == 0
    # ---- C3
    intactas = bp.correr_node([caso(x["r"], inner[x["vol"]]) for x in PUB])
    apagadas = bp.correr_node([caso(x["r"], inner[x["vol"]], pc_mw=0.0, rec_mw=0.0) for x in PUB])
    c3 = (len(PUB) > 0 and sum(b[4] for b in intactas) == len(PUB) and sum(b[4] for b in apagadas) == 0)
    # ---- C4
    s149 = json.loads((HERE / "lista_268_s149.json").read_text(encoding="utf-8"))
    N149 = {tuple(k) for k in s149["negativos"]}
    P149 = {tuple(k) for k in s149["alertas"]}
    hoyN, hoyP = {clave(x) for x in N}, {clave(x) for x in P}

    def en_s149(x):
        return clave(x) in N149 or clave(x) in P149
    n_s149, p_s149 = len(N149), len(P149)
    c4 = (s149["coincide_con_el_informe"] and N149 <= hoyN and P149 <= hoyP)
    out["controles"] = {
        "C1_identidad_predicado": {"ok": c1, "validez": val, "publicacion": pub},
        "C2_poblacion_sin_tocar_publica_0": {"ok": c2, "publican": sum(b[4] for b in base), "n": len(base)},
        "C3_campo_que_decide": {"ok": c3, "n_que_publican_hoy": len(PUB),
                                "intactas_publican": sum(b[4] for b in intactas),
                                "con_cero_publican": sum(b[4] for b in apagadas)},
        "C4_contiene_a_S149": {"ok": c4, "rev_s149": s149["rev"], "negativos_hoy": len(N), "negativos_en_S149": n_s149,
                               "alertas_hoy": len(P), "alertas_en_S149": p_s149,
                               "negativos_S149_que_faltan_hoy": sorted(map(list, N149 - hoyN)),
                               "negativos_nuevos_hoy": sorted(map(list, hoyN - N149)),
                               "alertas_S149_que_faltan_hoy": sorted(map(list, P149 - hoyP))},
    }

    # ---- qué persiste el record de los vecinos
    claves = collections.Counter()
    for x in N:
        claves.update(x["r"].keys())
    vecinales = sorted(k for k in claves if any(s in k.lower() for s in ("vecin", "neigh", "kernel", "local")))
    con_ap = [x for x in N if x["r"].get("anomaly_pixels")]
    out["datos_de_vecinos_en_el_record"] = {
        "campos_con_nombre_vecinal": {k: claves[k] for k in vecinales},
        "diag_L_bg_local_no_nulo": sum(1 for x in N if x["r"].get("diag_L_bg_local_w_m2_sr_um") is not None),
        "con_anomaly_pixels": len(con_ap),
        "nota": "anomaly_pixels guarda sólo píxeles alertados (lat, lon, dist_km, bt_k, vrp_mw); ninguno es vecino no alertado",
        "anomaly_pixels_con_vrp_positivo": sum(1 for x in con_ap if any((q.get('vrp_mw') or 0) > 0 for q in x['r']['anomaly_pixels'])),
    }

    # ---- techo: cualquier magnitud positiva, con el predicado real
    techo = {}
    for m in MAGNITUDES_SONDA:
        rn = bp.correr_node([caso(x["r"], inner[x["vol"]], pc_mw=m, rec_mw=max(m, x["r"].get("vrp_mw") or 0)) for x in N])
        rp = bp.correr_node([caso(x["r"], inner[x["vol"]], pc_mw=m, rec_mw=max(m, x["r"].get("vrp_mw") or 0)) for x in P])
        por_vol = collections.Counter(x["vol"] for x, b in zip(N, rn) if b[4])
        techo[str(m)] = {"negativos_publicarian": sum(b[4] for b in rn), "de": len(N),
                         "de_los_268_publicarian": sum(b[4] for x, b in zip(N, rn) if clave(x) in N149),
                         "alertas_publicarian": sum(b[4] for b in rp), "de_alertas": len(P),
                         "negativos_por_volcan": dict(por_vol),
                         "artefacto_marcado_neg": sum(b[2] for b in rn)}
    out["techo_cualquier_magnitud_positiva"] = techo
    out["negativos_por_volcan"] = dict(collections.Counter(x["vol"] for x in N))
    out["negativos_tasa_base_publicacion_v750"] = {
        "neg_limpio_v750_total": sum(1 for x in recs if x["lab"] == "neg_limpio"),
        "neg_limpio_v750_publican_hoy": sum(1 for x in recs if x["lab"] == "neg_limpio" and x["pub"]),
        "pos_v750_total": sum(1 for x in recs if x["lab"] == "pos"),
        "pos_v750_publican_hoy": sum(1 for x in recs if x["lab"] == "pos" and x["pub"])}

    # ---- escala: contraste del píxel caliente contra el fondo de HOY, y MW por K
    filas_esc = []
    for x in con_ap:
        r = x["r"]
        bt = max(q.get("bt_k") or 0 for q in r["anomaly_pixels"])
        filas_esc.append({"dT_contra_anillo_k": round(bt - r["t_bg_k"], 2), "mw_por_k": mw_por_k(bt)})
    filas_esc.sort(key=lambda f: f["dT_contra_anillo_k"])
    med = lambda v: v[len(v) // 2] if v else None  # noqa: E731
    out["escala"] = {
        "n": len(filas_esc),
        "dT_pixel_menos_anillo_k_mediana": med([f["dT_contra_anillo_k"] for f in filas_esc]),
        "dT_pixel_menos_anillo_k_min_max": [filas_esc[0]["dT_contra_anillo_k"], filas_esc[-1]["dT_contra_anillo_k"]] if filas_esc else None,
        "pixel_bajo_o_igual_al_anillo": sum(f["dT_contra_anillo_k"] <= 0 for f in filas_esc),
        "mw_por_k_mediana": med(sorted(f["mw_por_k"] for f in filas_esc)),
        "nota": "conversión determinista: área nadir 562.500 m2 x 19,7 x dL/dT(M13); no es una medición de D25",
    }

    # ---- lista congelada para el probe
    rnd = random.Random(SEMILLA)
    ctrl = sorted(rnd.sample(PUB, min(N_CONTROL_PROBE, len(PUB))), key=lambda x: (x["vol"], x["dt"]))

    def fila(x, clase):
        r = x["r"]
        pc = r.get("primary_cluster") or {}
        return {"clase": clase, "volcan": x["vol"], "pasada_utc": r["datetime_utc"], "sensor": r["sensor"],
                "granule": r.get("granule"), "product_version": r.get("product_version"),
                "en_s149": en_s149(x), "persistido": {
                    "pc_vrp_mw": pc.get("vrp_mw"), "pc_n_pixels": pc.get("n_pixels"),
                    "pc_centroid_dist_km": pc.get("centroid_dist_km"), "vrp_mw": r.get("vrp_mw"),
                    "t_bg_k": r.get("t_bg_k"), "final_hotspot_source": r.get("final_hotspot_source"),
                    "triggered_test1": r.get("triggered_test1"),
                    "diag_n_first_pass_pixels": r.get("diag_n_first_pass_pixels")}}
    lista = [fila(x, "neg_cero") for x in N] + [fila(x, "alerta_cero") for x in P] + [fila(x, "control_publica") for x in ctrl]
    (HERE / "pasadas.json").write_text(json.dumps(lista, indent=1, ensure_ascii=False), encoding="utf-8")
    out["pasadas_json"] = {"neg_cero": len(N), "alerta_cero": len(P), "control_publica": len(ctrl),
                           "sin_granule": sum(1 for f in lista if not f["granule"])}
    (HERE / "techo.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if not (c1 and c2 and c3):
        print("CONTROL FALLIDO: el techo no vale", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
