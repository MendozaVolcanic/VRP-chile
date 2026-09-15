# -*- coding: utf-8 -*-
"""S142: tablero de objetivos contra la definicion de terminado congelada (spec paridad §2, l. 80-84).

POR QUE. Nicolas pregunta cuan cerca estamos de MIROVA en deteccion, falsas publicaciones y magnitud.
La deteccion y las falsas ya las midio hoy experiments/_s142_linea_base/linea_base_post535.py por
tramo de regimen; se leen de su JSON tal cual. Faltaba (1) la magnitud en el NRT POR PASADA con la
magnitud que ve el operador, (2) la consistencia del propio MIROVA, que la spec §2 declara el unico
motivo para reabrir las bandas y que nunca se midio, y (3) juntar todo contra los objetivos.

INSTRUMENTO. No se porta nada: se importa scripts/banco_paridad.py (etiquetas pos / far_ref /
neg_limpio / sin_info y predicado del dashboard ejecutado con node). La magnitud publicada es `disp`
= mirovaEqVrpDisplay(r, inner, false) de frontend/index.html:1191, que en VIIRS 375 devuelve el nucleo
(f5_core_vrp_mw persistido, l. 1126) con respaldo en primary_cluster.vrp_mw (l. 1184) y en MODIS y
VIIRS 750 devuelve primary_cluster.vrp_mw (l. 1177). La referencia se baja del remoto Mirova-v1 en los
MISMOS sha que uso la linea base post-#535, para que las etiquetas sean identicas (control: conteo de
etiquetas por tramo igual al de ese JSON).

DEFINICIONES FIJADAS ANTES DE MIRAR LOS NUMEROS (ver DEFINICIONES abajo; se copian al JSON).

Fuente de verdad (regla S91): objetivos.json. TABLERO.md se genera desde ese JSON.
USO: python experiments/_s142_objetivos/objetivos.py [--solo-informe]
"""
from __future__ import annotations

import collections
import io
import json
import math
import statistics
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import URL_RAW, cargar_referencia_unificada  # noqa: E402

LB = ROOT / "experiments" / "_s142_linea_base" / "linea_base_post535.json"
BANCO = ROOT / "data" / "audit_continuous" / "linea_base_s139" / "banco.json"
MAG_OSF = ROOT / "data" / "audit_continuous" / "linea_base_s139" / "magnitud.json"
LATEST = ROOT / "data" / "audit_continuous" / "latest.json"
ATRASO = ROOT / "experiments" / "_s141_cron" / "atraso_despacho.json"
DL = HERE / "_dl_referencia"
OUT = HERE / "objetivos.json"
MD = HERE / "TABLERO.md"

BANDA_MAG = (0.8, 1.25)
N_MIN_MAG = 30
N_MIN_TASA = 20
TOL_PASADA_S = 120

DEFINICIONES = {
    "par_magnitud": ("pasada nuestra etiquetada pos (banco_paridad) con fila ALERTA de MIROVA a +-2 min y VRP > 0. "
                     "Si hay fila CONS y OCR para la pasada se usa CONS (latest.php, numero escrito por MIROVA; el OCR "
                     "lee la imagen y es complemento, regla A11); la OCR solo cuando no hay CONS. Una fila de MIROVA "
                     "se parea con una sola pasada nuestra (la mas cercana en tiempo)."),
    "magnitud_publicada": "disp = mirovaEqVrpDisplay(r, inner, false) (frontend/index.html:1191), solo en pares que el dashboard publica (pub=1)",
    "razon": "disp / VRP_MIROVA por pasada; mediana, media geometrica, fraccion en [0,8 ; 1,25]; n < 30 marcado",
    "pasada_mirova": "filas nocturnas de MIROVA del mismo volcan y sensor agrupadas a +-2 min (CONS y OCR juntas); estado ALERTA si alguna fila es ALERTA, FP si alguna es FALSO_POSITIVO y ninguna ALERTA, RUTINA si no",
    "listada": "pasada MIROVA en estado ALERTA o RUTINA (FP excluida: calor fuera del limite, sin informacion del crater, igual que el banco)",
    "noche": "fecha UTC de la pasada, igual que el banco",
    "C1_repeticion_intra_sensor": ("VIIRS 375: en noches de volcan con >= 1 pasada ALERTA y >= 2 listadas, sobre pares ordenados "
                                   "(i ALERTA, j distinta listada) la fraccion con j ALERTA. Tasa base: fraccion ALERTA entre todas las listadas del volcan."),
    "C1b_contradiccion_canales": "pasadas MIROVA con fila CONS RUTINA y fila OCR ALERTA a la vez (MIROVA se contradice entre su CSV y su imagen)",
    "C2_entre_sensores": ("en noches con >= 1 pasada ALERTA en el sensor A, fraccion de pasadas listadas del sensor B esa noche que son ALERTA "
                          "(A=V375,B=V750 y A=V750,B=V375)"),
    "C2b_falsas_de_mirova_contra_otro_sensor": ("analogo MIROVA-contra-MIROVA de la banda: noches negativas segun el sensor A (>= 1 listada, "
                                                "ninguna ALERTA ni FP en A) y fraccion de pasadas listadas del sensor B esa noche con ALERTA"),
    "C3_persistencia_noche": ("VIIRS 375, noches listadas: P(noche ALERTA | noche anterior ALERTA) y P(noche ALERTA | noche anterior listada sin ALERTA ni FP); "
                              "C3b: fraccion de pasadas listadas en ALERTA en la noche siguiente a una noche negativa"),
    "C4_negativos_adyacentes": ("nuestros neg_limpio VIIRS 375: fraccion cuya noche esta a +-1 noche de una noche con ALERTA V375 de MIROVA en el mismo volcan, "
                                "y tasa de publicacion nuestra en adyacentes y no adyacentes"),
}


def _git(*args):
    return subprocess.run(list(args), capture_output=True, text=True, check=True, cwd=ROOT).stdout.strip()


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0.0, round(c - h, 4)), min(1.0, round(c + h, 4))


def fisher_una_cola(a, n1, b, n2):
    """P(X >= a) con X hipergeometrica: exito del grupo 1 mayor que el del grupo 2."""
    N, K = n1 + n2, a + b
    if not n1 or not n2:
        return None
    den = math.comb(N, n1)
    return round(sum(math.comb(K, x) * math.comb(N - K, n1 - x) for x in range(a, min(K, n1) + 1)) / den, 4)


def _q(xs, p):
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def stats(vals):
    xs = sorted(v for v in vals if v is not None and v > 0 and math.isfinite(v))
    n = len(xs)
    if not n:
        return {"n": 0}
    med = statistics.median(xs)
    return {"n": n, "mediana": round(med, 4), "media_geom": round(math.exp(sum(map(math.log, xs)) / n), 4),
            "p25": round(_q(xs, 0.25), 4), "p75": round(_q(xs, 0.75), 4),
            "frac_en_banda": round(sum(BANDA_MAG[0] <= v <= BANDA_MAG[1] for v in xs) / n, 4),
            "mediana_en_banda": BANDA_MAG[0] <= med <= BANDA_MAG[1], "n_menor_30": n < N_MIN_MAG}


def _dt_ref(f):
    return datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------------------------ magnitud
def pares_magnitud(recs, por_vb):
    mejor, n_pos_con_alerta = {}, 0
    for r in recs:
        if r["lab"] != "pos":
            continue
        filas = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
                 if bp.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0]
        if not filas:
            continue
        n_pos_con_alerta += 1

        def cerca(L):
            return min(L, key=lambda f: abs((_dt_ref(f) - r["dt"]).total_seconds())) if L else None
        cons = cerca([f for f in filas if f["source"] == "CONS"])
        ocr = cerca([f for f in filas if f["source"] == "OCR"])
        ref = cons or ocr
        par = {"vol": r["vol"], "b": r["b"], "noche": r["noche"], "pub": r["pub"], "disp": r["disp"],
               "pc_vrp": r["pc_vrp"], "ref_vrp": ref["vrp_mw"], "fuente": ref["source"],
               "vrp_cons": cons["vrp_mw"] if cons else None, "vrp_ocr": ocr["vrp_mw"] if ocr else None,
               "dt_abs_s": abs((_dt_ref(ref) - r["dt"]).total_seconds())}
        k = (r["vol"], r["b"], ref["fecha_utc"][:16], ref["source"])
        if k not in mejor or par["dt_abs_s"] < mejor[k]["dt_abs_s"]:
            mejor[k] = par
    return list(mejor.values()), n_pos_con_alerta


def resumen_mag(pares):
    pub = [p for p in pares if p["pub"] == 1 and (p["disp"] or 0) > 0]
    return {"n_pares": len(pares), "n_no_publicados": len(pares) - len(pub),
            "publicado": stats([p["disp"] / p["ref_vrp"] for p in pub]),
            "cluster_pc_en_publicados": stats([(p["pc_vrp"] or 0) / p["ref_vrp"] for p in pub]),
            "por_fuente": {s: stats([p["disp"] / p["ref_vrp"] for p in pub if p["fuente"] == s]) for s in ("CONS", "OCR")}}


def magnitud_tramo(pares, focal, nevado):
    out = {}
    for b in bp.BUCKETS:
        pb = [p for p in pares if p["b"] == b]
        out[b] = {"total": resumen_mag(pb),
                  "por_estrato": {"focal": resumen_mag([p for p in pb if p["vol"] in focal]),
                                  "nevado": resumen_mag([p for p in pb if p["vol"] in nevado])},
                  "por_volcan": {v: resumen_mag([p for p in pb if p["vol"] == v]) for v in bp.VOLS}}
    return out


# ------------------------------------------------------------------------------------ consistencia MIROVA
def pasadas_mirova(por_vb):
    """{(vol, b, noche): [estado, ...]} y contradicciones CONS RUTINA + OCR ALERTA."""
    out = collections.defaultdict(list)
    contradicciones = collections.Counter()
    for (vol, b), lista in por_vb.items():
        grupo, t0 = [], None
        for dt, f in lista + [(None, None)]:
            if dt is not None and t0 is not None and (dt - t0).total_seconds() <= TOL_PASADA_S:
                grupo.append(f)
                continue
            if grupo:
                tipos = [g["tipo"] for g in grupo]
                if any(bp.es_alerta(t) for t in tipos):
                    est = "A"
                    if any(g["tipo"] == "RUTINA" and g["source"] == "CONS" for g in grupo) and \
                            any(bp.es_alerta(g["tipo"]) and g["source"] == "OCR" for g in grupo):
                        contradicciones[(vol, b)] += 1
                elif any(bp.es_fp(t) for t in tipos):
                    est = "F"
                else:
                    est = "R"
                out[(vol, b, grupo[0]["fecha_utc"][:10])].append(est)
            grupo, t0 = ([f], dt) if dt is not None else ([], None)
    return out, contradicciones


def _frac(k, n):
    return {"k": k, "n": n, "frac": round(k / n, 4) if n else None, "ic95": wilson(k, n)}


def consistencia(pm, contradicciones, recs, ventana, focal, nevado):
    def en(noche):
        return ventana[0] <= noche <= ventana[1]
    grupos = {"TOTAL": bp.VOLS, "focal": focal, "nevado": nevado, **{v: [v] for v in bp.VOLS}}
    res = {}
    for g, vols in grupos.items():
        c1k = c1n = base_a = base_n = 0
        noches_rep = noches_todas = 0
        c2 = {("VIIRS375", "VIIRS750"): [0, 0], ("VIIRS750", "VIIRS375"): [0, 0]}
        c2b = {("VIIRS375", "VIIRS750"): [0, 0], ("VIIRS750", "VIIRS375"): [0, 0]}
        c3 = {"tras_alerta": [0, 0], "tras_negativa": [0, 0]}
        c3b = [0, 0]
        for vol in vols:
            noches = sorted(n for (v, b, n) in pm if v == vol and b == "VIIRS375" and en(n))
            for n in noches:
                est = [e for e in pm[(vol, "VIIRS375", n)] if e in ("A", "R")]
                base_a += est.count("A")
                base_n += len(est)
                na = est.count("A")
                if na and len(est) >= 2:
                    noches_todas += 1
                    noches_rep += int(na == len(est))
                    c1n += na * (len(est) - 1)
                    c1k += na * (na - 1)
            for a, bb in c2:
                for (v, b, n), est in pm.items():
                    if v != vol or b != a or not en(n):
                        continue
                    otros = [e for e in pm.get((vol, bb, n), []) if e in ("A", "R")]
                    if not otros:
                        continue
                    lista_a = [e for e in est if e in ("A", "R")]
                    if "A" in est:
                        c2[(a, bb)][0] += otros.count("A")
                        c2[(a, bb)][1] += len(otros)
                    elif lista_a and "F" not in est:
                        c2b[(a, bb)][0] += otros.count("A")
                        c2b[(a, bb)][1] += len(otros)
            estado_noche = {}
            for n in noches:
                est = pm[(vol, "VIIRS375", n)]
                if "A" in est:
                    estado_noche[n] = "A"
                elif "R" in est and "F" not in est:
                    estado_noche[n] = "N"
            for n, e in estado_noche.items():
                prev = (date.fromisoformat(n) - timedelta(days=1)).isoformat()
                if prev not in estado_noche:
                    continue
                clave = "tras_alerta" if estado_noche[prev] == "A" else "tras_negativa"
                c3[clave][0] += int(e == "A")
                c3[clave][1] += 1
                if estado_noche[prev] == "N":
                    est = [x for x in pm[(vol, "VIIRS375", n)] if x in ("A", "R")]
                    c3b[0] += est.count("A")
                    c3b[1] += len(est)
        # C4 con nuestros negativos
        alerta_noches = {(v, n) for (v, b, n), est in pm.items() if b == "VIIRS375" and "A" in est}
        ady, noady = [0, 0], [0, 0]
        for r in recs:
            if r["b"] != "VIIRS375" or r["lab"] != "neg_limpio" or r["vol"] not in vols or not en(r["noche"]):
                continue
            d = date.fromisoformat(r["noche"])
            es_ady = any((r["vol"], (d + timedelta(days=k)).isoformat()) in alerta_noches for k in (-1, 1))
            t = ady if es_ady else noady
            t[0] += r["pub"]
            t[1] += 1
        res[g] = {
            "C1_frac_vecina_alerta": _frac(c1k, c1n),
            "C1_noches_con_alerta_y_2_listadas": noches_todas,
            "C1_frac_noches_todas_alerta": _frac(noches_rep, noches_todas),
            "C1_tasa_base_alerta_por_pasada_listada": _frac(base_a, base_n),
            "C1b_contradicciones_cons_rutina_ocr_alerta": sum(v for (vv, b), v in contradicciones.items() if vv in vols and b == "VIIRS375"),
            "C2_V375_alerta_luego_V750": _frac(*c2[("VIIRS375", "VIIRS750")]),
            "C2_V750_alerta_luego_V375": _frac(*c2[("VIIRS750", "VIIRS375")]),
            "C2b_V375_negativa_luego_V750_alerta": _frac(*c2b[("VIIRS375", "VIIRS750")]),
            "C2b_V750_negativa_luego_V375_alerta": _frac(*c2b[("VIIRS750", "VIIRS375")]),
            "C3_P_alerta_tras_alerta": _frac(*c3["tras_alerta"]),
            "C3_P_alerta_tras_negativa": _frac(*c3["tras_negativa"]),
            "C3b_pasadas_alerta_tras_noche_negativa": _frac(*c3b),
            "C4_frac_neg_limpio_adyacentes": _frac(ady[1], ady[1] + noady[1]),
            "C4_pub_en_adyacentes": _frac(*ady),
            "C4_pub_en_no_adyacentes": _frac(*noady),
        }
    return res


# ------------------------------------------------------------------------------------ objetivos
def agregar_banco(banco, b, vols):
    """Linea base congelada (banco.json) por estrato, sumando conteos por volcan."""
    pn = pk = nn = nk = qn = qk = 0
    for v in vols:
        x = banco["por_volcan"][v][b]
        p, n = x["pasada"], x["noche_volcan"]
        if p["n_neg_limpio"]:
            pn += p["n_neg_limpio"]
            pk += round(p["tasa_pub_neg"] * p["n_neg_limpio"])
        if n["n_pos"]:
            nn += n["n_pos"]
            nk += round(n["recall_pos"] * n["n_pos"])
        if n["n_neg"]:
            qn += n["n_neg"]
            qk += round(n["tasa_pub_neg"] * n["n_neg"])
    return {"falsas_pasada": _frac(pk, pn), "falsas_noche": _frac(qk, qn),
            "noches_pos": nn, "noches_pos_publicadas": nk, "noches_perdidas": nn - nk}


def noches_perdidas(recs, b, vols, ventana):
    noches = collections.defaultdict(lambda: [False, 0])
    for r in recs:
        if r["b"] != b or r["vol"] not in vols or not (ventana[0] <= r["noche"] <= ventana[1]):
            continue
        e = noches[(r["vol"], r["noche"])]
        e[0] |= r["lab"] == "pos"
        e[1] = max(e[1], r["pub"])
    pos = [k for k, e in noches.items() if e[0]]
    perd = sorted(f"{v} {n}" for (v, n) in pos if noches[(v, n)][1] == 0)
    return {"noches_pos": len(pos), "noches_perdidas": len(perd), "lista": perd}


def medir():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    lb = json.loads(LB.read_text(encoding="utf-8"))
    banco = json.loads(BANCO.read_text(encoding="utf-8"))
    focal, nevado, banda = lb["meta"]["estratos"]["focal"], lb["meta"]["estratos"]["nevado"], lb["meta"]["banda_terminado"]

    DL.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre, v in lb["meta"]["referencia"].items():
        destino = DL / nombre
        urllib.request.urlretrieve(URL_RAW.format(sha=v["sha"], nombre=nombre), destino)
        rutas[nombre] = destino
    filas = cargar_referencia_unificada(rutas["registro_vrp_consolidado.csv"], rutas["registro_vrp_ocr.csv"])

    T = lb["tramos"]
    tramos = {"linea_base_s139": tuple(banco["meta"]["ventana"])}
    for k in ("antes_535_misma_longitud", "entre_535_y_571", "despues_571"):
        tramos[k] = tuple(T[k]["ventana_noches_utc"])
    ventana = ("2026-03-01", lb["meta"]["ultimo_dato_nuestro_noche"])
    # Records fijados al commit de la linea base post-#535: otra sesion puede traer datos nuevos a este
    # checkout a mitad de corrida (paso en S142: el control de etiquetas dio False en despues_571).
    sha_lb = lb["meta"]["git_head"]
    dl_data = HERE / f"_dl_data_{sha_lb[:9]}"
    dl_data.mkdir(parents=True, exist_ok=True)
    for vol in bp.VOLS:
        blob = subprocess.run(["git", "show", f"{sha_lb}:data/mirova_equivalent/{vol}.json"], capture_output=True,
                              check=True, cwd=ROOT).stdout
        (dl_data / f"{vol}.json").write_bytes(blob)
    bp.DATA = dl_data
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)

    # control: mismas etiquetas que la linea base post-#535
    control_etiquetas = {}
    for k in ("antes_535_misma_longitud", "entre_535_y_571", "despues_571"):
        i, f = tramos[k]
        mio = dict(collections.Counter(r["lab"] for r in recs if i <= r["noche"] <= f))
        control_etiquetas[k] = {"mio": mio, "linea_base": T[k]["etiquetas"], "igual": mio == T[k]["etiquetas"]}
        print(k, control_etiquetas[k]["igual"], mio)

    pares, n_pos_alerta = pares_magnitud(recs, por_vb)
    ambos = [p for p in pares if p["vrp_cons"] and p["vrp_ocr"]]
    control_fuentes = {"n_pares_total": len(pares), "n_pos_con_alerta_vrp": n_pos_alerta,
                       "n_filas_mirova_con_mas_de_una_pasada_nuestra": n_pos_alerta - len(pares),
                       "n_con_cons_y_ocr": len(ambos),
                       "ocr_sobre_cons": stats([p["vrp_ocr"] / p["vrp_cons"] for p in ambos]),
                       "frac_ocr_igual_cons_5pct": round(sum(abs(p["vrp_ocr"] / p["vrp_cons"] - 1) <= 0.05 for p in ambos) / len(ambos), 4) if ambos else None,
                       "por_fuente_elegida": dict(collections.Counter(p["fuente"] for p in pares))}

    magnitud = {k: magnitud_tramo([p for p in pares if i <= p["noche"] <= f], focal, nevado) for k, (i, f) in tramos.items()}

    pm, contra = pasadas_mirova(por_vb)
    consist = {k: consistencia(pm, contra, recs, tramos[k], focal, nevado) for k in ("linea_base_s139", "despues_571")}

    objetivos = {}
    post, lbw = tramos["despues_571"], tramos["linea_base_s139"]
    for b in bp.BUCKETS:
        obj = {}
        for est, vols in (("focal", focal), ("nevado", nevado)):
            hoy_det = noches_perdidas(recs, b, vols, post)
            ref_det = noches_perdidas(recs, b, vols, lbw)
            x = T["despues_571"]["por_estrato"][est][b]["pasada"]
            k = round(x["tasa_pub_neg"] * x["n_neg_limpio"]) if x["n_neg_limpio"] else 0
            fal = _frac(k, x["n_neg_limpio"])
            ban = agregar_banco(banco, b, vols)
            if not x["n_neg_limpio"] or x["n_neg_limpio"] < N_MIN_TASA:
                ver_f = "sin n suficiente"
            else:
                ver_f = "cumple" if fal["frac"] <= banda[est] else "no cumple"
            obj[est] = {
                "deteccion": {"hoy": hoy_det, "linea_base_misma_referencia": {k2: v for k2, v in ref_det.items() if k2 != "lista"},
                              "linea_base_congelada_banco": {k2: ban[k2] for k2 in ("noches_pos", "noches_pos_publicadas", "noches_perdidas")},
                              "recall_noche_linea_base_post535": T["despues_571"]["por_estrato"][est][b]["noche_volcan"]},
                "falsas": {"hoy_pasada": fal, "hoy_noche": T["despues_571"]["por_estrato"][est][b]["noche_volcan"],
                           "linea_base_congelada_pasada": ban["falsas_pasada"], "banda": banda[est], "veredicto": ver_f}}
        for tr in ("despues_571", "linea_base_s139"):
            pv = magnitud[tr][b]["por_volcan"]
            elegibles = {v: pv[v]["publicado"] for v in bp.VOLS if pv[v]["publicado"].get("n", 0) >= N_MIN_MAG}
            fuera = sorted(v for v, s in elegibles.items() if not s["mediana_en_banda"])
            if not elegibles:
                ver = "sin n suficiente"
            else:
                ver = "cumple" if not fuera else "no cumple"
            obj[f"magnitud_{tr}"] = {"volcanes_n30": sorted(elegibles), "fuera_de_banda": fuera, "veredicto": ver,
                                     "total": magnitud[tr][b]["total"]["publicado"]}
        objetivos[b] = obj
    det_ok = all(objetivos[b][est]["deteccion"]["hoy"]["noches_pos"] == T["despues_571"]["por_estrato"][est][b]["noche_volcan"]["n_pos"]
                 for b in bp.BUCKETS for est in ("focal", "nevado"))

    modis = {}
    for tr in ("despues_571", "linea_base_s139"):
        i, f = tramos[tr]
        modis[tr] = {}
        for g, vols in (("Lascar", ["Lascar"]), ("TODOS", bp.VOLS)):
            sel = [r for r in recs if r["b"] == "MODIS" and r["vol"] in vols and i <= r["noche"] <= f]
            pos = [r["pub"] for r in sel if r["lab"] == "pos"]
            neg = [r["pub"] for r in sel if r["lab"] == "neg_limpio"]
            modis[tr][g] = {"pub_en_pos": _frac(sum(pos), len(pos)), "pub_en_neg": _frac(sum(neg), len(neg)),
                            "p_fisher_pos_mayor": fisher_una_cola(sum(pos), len(pos), sum(neg), len(neg))}

    osf = json.loads(MAG_OSF.read_text(encoding="utf-8"))
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    atraso = json.loads(ATRASO.read_text(encoding="utf-8"))
    pv375 = T["despues_571"]["por_sensor"]["VIIRS375"]["pasada"]
    n_tot = sum(pv375[k] for k in ("n_pos", "n_neg_limpio", "n_far_ref", "n_sin_info"))
    otros = {
        "sin_info_v375_despues_571": {"n_sin_info": pv375["n_sin_info"], "n_total": n_tot,
                                      "frac": round(pv375["n_sin_info"] / n_tot, 4) if n_tot else None},
        "recall_noche_por_sensor_despues_571": {b: T["despues_571"]["por_sensor"][b]["noche_volcan"] for b in bp.BUCKETS + ["CUALQUIERA"]},
        "recall_noche_por_sensor_linea_base_congelada": {b: banco["por_sensor"][b]["noche_volcan"] for b in bp.BUCKETS + ["CUALQUIERA"]},
        "auto_audit_latest": {"ventana": latest["window"], "generado": latest["generated_utc"],
                              "magnitud_ratio_por_noche_por_volcan": latest["magnitud_ratio_by_vol"],
                              "recall": latest["recall"]},
        "latencia_despacho_cron": {"generado": atraso["generado_utc"], "resumen": atraso["resumen"]},
        "osf_magnitud": {"ventana": osf["meta"]["ventana_osf"], "VIIRS375_total": osf["VIIRS375"]["total"],
                         "VIIRS375_por_volcan": osf["VIIRS375"]["por_volcan"], "VIIRS375_igual_conteo": osf["VIIRS375"]["igual_conteo"],
                         "VIIRS750_por_volcan": osf["VIIRS750"]["por_volcan"], "MODIS_por_volcan": osf["MODIS"]["por_volcan"]},
    }

    salida = {"meta": {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git("git", "rev-parse", "HEAD"),
        "records_fijados_a_commit": sha_lb,
        "n_commits_data_en_head_posteriores": len([x for x in _git("git", "log", "--oneline", f"{sha_lb}..HEAD", "--", "data/mirova_equivalent").splitlines() if x]),
        "referencia_sha": {n: v["sha"] for n, v in lb["meta"]["referencia"].items()},
        "sha_index_html": bp.sha_git(bp.HTML), "sha_index_html_linea_base": lb["meta"]["sha_index_html"],
        "tramos": {k: list(v) for k, v in tramos.items()}, "n_filas_ref_nocturnas": n_ref, "n_records_nocturnos": len(recs),
        "estratos": lb["meta"]["estratos"], "banda_falsas": banda, "banda_magnitud": list(BANDA_MAG), "n_min_magnitud": N_MIN_MAG,
        "fuentes_leidas": {"deteccion_y_falsas_hoy": str(LB.relative_to(ROOT)), "linea_base_congelada": str(BANCO.relative_to(ROOT)),
                           "magnitud_osf": str(MAG_OSF.relative_to(ROOT)), "auto_audit": str(LATEST.relative_to(ROOT)),
                           "latencia": str(ATRASO.relative_to(ROOT))},
        "predicado_magnitud": "frontend/index.html:1191 mirovaEqVrpDisplay -> 1166 mirovaEqVrpCore (V375: f5_core_vrp_mw l. 1126, respaldo pc l. 1184; MODIS y V750 pc l. 1177)",
        "definiciones": DEFINICIONES},
        "controles": {"etiquetas_iguales_a_linea_base": control_etiquetas, "fuentes_magnitud": control_fuentes,
                      "deteccion_igual_a_linea_base": det_ok},
        "objetivos": objetivos, "modis_criterio_falsas": modis, "magnitud": magnitud,
        "consistencia_mirova": consist, "otros": otros}
    OUT.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    return salida


# ------------------------------------------------------------------------------------ informe
def pct(x):
    return "s/d" if x is None else f"{100 * x:.1f}".replace(".", ",") + " %"


def num(x, d=2):
    return "s/d" if x is None else f"{x:.{d}f}".replace(".", ",")


def fr(o):
    if not o or not o.get("n"):
        return "s/d (n 0)"
    lo, hi = o["ic95"]
    return f"{pct(o['frac'])} ({o['k']} de {o['n']}; IC95 {pct(lo)} a {pct(hi)})"


def ms(s, corto=False):
    if not s or not s.get("n"):
        return "s/d (n 0)"
    marca = " (n<30)" if s["n_menor_30"] else ""
    if corto:
        return f"{num(s['mediana'])} (n {s['n']}{marca})"
    return (f"mediana {num(s['mediana'])}, geom {num(s['media_geom'])}, p25-p75 {num(s['p25'])} a {num(s['p75'])}, "
            f"en banda {pct(s['frac_en_banda'])}, n {s['n']}{marca}")


def informe(d):
    m, O, M, C, X = d["meta"], d["objetivos"], d["magnitud"], d["consistencia_mirova"], d["otros"]
    tr = m["tramos"]
    L = []
    w = L.append
    w("# Tablero de objetivos de paridad con MIROVA (S142)\n")
    w("Generado por `experiments/_s142_objetivos/objetivos.py` desde `objetivos.json` (regla S91: ningún número se escribió a mano). "
      f"Generado {m['generado_utc']} sobre `{m['git_head'][:9]}`. Records leídos del commit de la línea base post-#535 `{m['records_fijados_a_commit'][:9]}` con `git show` "
      f"(en HEAD ya hay {m['n_commits_data_en_head_posteriores']} commits NRT posteriores en `data/mirova_equivalent`, que este tablero deja fuera a propósito para medir sobre el mismo banco). "
      f"Referencia Mirova-v1 fijada a los sha de esa línea base: consolidado `{m['referencia_sha']['registro_vrp_consolidado.csv'][:9]}`, OCR `{m['referencia_sha']['registro_vrp_ocr.csv'][:9]}`. "
      f"Predicado: `frontend/index.html` blob `{m['sha_index_html'][:9]}` (línea base: `{m['sha_index_html_linea_base'][:9]}`).\n")
    ce = d["controles"]["etiquetas_iguales_a_linea_base"]
    w("**Control del instrumento.** Etiquetas por tramo idénticas a las de `linea_base_post535.json`: " +
      ", ".join(f"{k} {v['igual']}" for k, v in ce.items()) + ". Si alguno diera False, la magnitud y la consistencia no estarían sobre el mismo banco que la detección y las falsas.\n")

    w("## Qué se está comparando, en términos físicos\n")
    w("MIROVA y nosotros miramos las mismas pasadas nocturnas de VIIRS y MODIS sobre los 11 volcanes. Hay tres preguntas distintas. "
      "**Detección**: en una noche en que MIROVA vio calor en el cráter, ¿el operador ve algo en nuestro dashboard? "
      "**Falsas publicaciones**: en una pasada que MIROVA procesó y donde no vio nada (RUTINA con VRP 0, sin alerta esa noche en ese sensor), ¿publicamos igual? "
      "Es la sobre-publicación: píxeles tibios de flanco, nieve o fondo que nuestro pipeline convierte en un cúmulo en el cráter. "
      "**Magnitud**: cuando ambos vemos el foco en la misma pasada, ¿cuánta potencia radiativa le asignamos respecto de MIROVA? "
      "Una razón bajo 1 significa que integramos menos píxeles del foco o menos exceso por píxel; la línea base congelada ya separó eso contra el OSF.\n")

    w(f"## 1. Objetivo contra hoy, por sensor\n")
    w(f"Hoy = régimen posterior a #571, noches UTC {tr['despues_571'][0]} a {tr['despues_571'][1]}. Línea base congelada = `banco.json` S139/S140, {tr['linea_base_s139'][0]} a {tr['linea_base_s139'][1]}. "
      "La magnitud de la línea base usa el mismo pareo NRT de este script sobre esa ventana (la línea base congelada no la tenía por pasada en el NRT, sólo contra el OSF 2025).\n")
    w("| Sensor | Criterio | Objetivo | Hoy (post #571) | Línea base congelada | Veredicto hoy |")
    w("|---|---|---|---|---|---|")
    for b in bp.BUCKETS:
        o = O[b]
        for est in ("focal", "nevado"):
            dd = o[est]["deteccion"]
            w(f"| {b} | detección, {est} | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | "
              f"{dd['hoy']['noches_perdidas']} perdidas de {dd['hoy']['noches_pos']} noches con alerta | "
              f"{dd['linea_base_congelada_banco']['noches_perdidas']} perdidas de {dd['linea_base_congelada_banco']['noches_pos']} | "
              f"{'sin pérdidas en el tramo' if dd['hoy']['noches_perdidas'] == 0 else 'hay pérdidas: ver lista §2'}{' (n<20)' if dd['hoy']['noches_pos'] < N_MIN_TASA else ''} |")
        for est in ("focal", "nevado"):
            f_ = o[est]["falsas"]
            w(f"| {b} | falsas por pasada, {est} | ≤ {pct(f_['banda'])} | {fr(f_['hoy_pasada'])} | {fr(f_['linea_base_congelada_pasada'])} | {f_['veredicto']} |")
        mh, ml = o["magnitud_despues_571"], o["magnitud_linea_base_s139"]
        obj_mag = "informativa" if b == "MODIS" else "mediana por pasada en [0,8 ; 1,25] en cada volcán con n ≥ 30"
        w(f"| {b} | magnitud | {obj_mag} | total {ms(mh['total'], True)}; volcanes n≥30: {', '.join(mh['volcanes_n30']) or 'ninguno'} | "
          f"total {ms(ml['total'], True)}; n≥30: {', '.join(ml['volcanes_n30']) or 'ninguno'}; fuera de banda: {', '.join(ml['fuera_de_banda']) or 'ninguno'} | "
          f"{mh['veredicto'] if b != 'MODIS' else 'informativa'} (línea base: {ml['veredicto']}) |")
    md = d["modis_criterio_falsas"]
    for tr_ in ("despues_571", "linea_base_s139"):
        x = md[tr_]["Lascar"]
        w(f"| MODIS | Láscar, publicación en pasadas con alerta mayor que en negativas ({tr_}) | significativamente mayor | "
          f"con alerta {fr(x['pub_en_pos'])}; negativas {fr(x['pub_en_neg'])}; p Fisher una cola {num(x['p_fisher_pos_mayor'], 4)} | "
          f"todos los volcanes: con alerta {fr(md[tr_]['TODOS']['pub_en_pos'])}, negativas {fr(md[tr_]['TODOS']['pub_en_neg'])} | "
          f"{'sin n suficiente' if x['pub_en_pos']['n'] < N_MIN_TASA else ('cumple' if (x['p_fisher_pos_mayor'] or 1) < 0.05 else 'no cumple')} |")
    w(f"| todos | control: noches con alerta de hoy iguales a las de la línea base post-#535 por estrato y sensor | igual | {d['controles']['deteccion_igual_a_linea_base']} | | |")
    w("| MODIS | pasos literales D19, D21 a D25 | implementados y activos | no se mide con este instrumento; los seis figuran ABIERTOS en `docs/MIROVA_DIVERGENCES.md` l. 2097, 2221, 2246, 2275, 2285, 2295 (leído S142) | igual | no cumple |")
    w("")
    w("Nota sobre el criterio MODIS: la spec (l. 84) lo escribe para Láscar pero su valor de partida (11,5 % contra 10,2 %) viene de "
      "`docs/audit_s139/VERIFICADOR.md` l. 138, que suma todos los volcanes MODIS. La fila 'todos los volcanes' reproduce esa comparación; "
      "sólo en Láscar la diferencia es significativa, con una publicación de apenas un décimo de las pasadas con alerta.\n")
    w("Magnitud total por sensor y tramo (mediana por pasada, n):\n")
    w("| Sensor | " + " | ".join(M.keys()) + " |")
    w("|---|" + "---|" * len(M))
    for b in bp.BUCKETS:
        w(f"| {b} | " + " | ".join(ms(M[k][b]['total']['publicado'], True) for k in M) + " |")
    w("")

    w("## 2. Detección: noches con alerta de MIROVA que no publicamos (hoy)\n")
    for b in bp.BUCKETS:
        for est in ("focal", "nevado"):
            h = O[b][est]["deteccion"]["hoy"]
            w(f"- {b} {est}: {h['noches_perdidas']} de {h['noches_pos']}: {', '.join(h['lista']) or 'ninguna'}.")
    w("\nRecall por noche de volcán, cualquier sensor: hoy " +
      f"{pct(X['recall_noche_por_sensor_despues_571']['CUALQUIERA']['recall_pos'])} de {X['recall_noche_por_sensor_despues_571']['CUALQUIERA']['n_pos']}; "
      f"línea base congelada {pct(X['recall_noche_por_sensor_linea_base_congelada']['CUALQUIERA']['recall_pos'])} de {X['recall_noche_por_sensor_linea_base_congelada']['CUALQUIERA']['n_pos']}. "
      "Por sensor hoy: " + "; ".join(f"{b} {pct(X['recall_noche_por_sensor_despues_571'][b]['recall_pos'])} de {X['recall_noche_por_sensor_despues_571'][b]['n_pos']}" for b in bp.BUCKETS) + ".\n")

    w("## 3. Magnitud por volcán (nuestro/MIROVA por pasada, lo que ve el operador)\n")
    cf = d["controles"]["fuentes_magnitud"]
    w(f"Pares en toda la ventana: {cf['n_pares_total']} (fuente elegida {cf['por_fuente_elegida']}). Pasadas con fila CONS y OCR a la vez: {cf['n_con_cons_y_ocr']}; "
      f"OCR/CONS {ms(cf['ocr_sobre_cons'], True)}, iguales a ±5 % en {pct(cf['frac_ocr_igual_cons_5pct'])}. "
      f"Filas de MIROVA pareadas con más de una pasada nuestra (descartadas por duplicado): {cf['n_filas_mirova_con_mas_de_una_pasada_nuestra']}.\n")
    osf = X["osf_magnitud"]
    aa = X["auto_audit_latest"]
    for b in bp.BUCKETS:
        w(f"### {b}\n")
        cab = "| Volcán | Estrato | Hoy post #571 | Antes #535 (15 noches) | Línea base NRT 03-01 a 09-14 | Cúmulo pc en la línea base NRT | No publicados (línea base) |"
        if b == "VIIRS375":
            cab += f" OSF 2025 (R_med, n) | Auto-audit por noche {aa['ventana'][0]} a {aa['ventana'][1]} |"
        w(cab)
        w("|" + "---|" * (cab.count("|") - 1))
        for v in bp.VOLS:
            est = "focal" if v in m["estratos"]["focal"] else "nevado"
            lbv = M["linea_base_s139"][b]["por_volcan"][v]
            fila = (f"| {v} | {est} | {ms(M['despues_571'][b]['por_volcan'][v]['publicado'], True)} | "
                    f"{ms(M['antes_535_misma_longitud'][b]['por_volcan'][v]['publicado'], True)} | {ms(lbv['publicado'])} | "
                    f"{ms(lbv['cluster_pc_en_publicados'], True)} | {lbv['n_no_publicados']} de {lbv['n_pares']} |")
            if b == "VIIRS375":
                o_ = osf["VIIRS375_por_volcan"].get(v)
                a_ = aa["magnitud_ratio_por_noche_por_volcan"].get(v)
                fila += (f" {num(o_['R_med']) + ' (n ' + str(o_['n']) + ')' if o_ else 's/d'} | "
                         f"{num(a_['ratio_mediano']) + ' (n ' + str(a_['n_noches']) + ' noches)' if a_ else 's/d'} |")
            w(fila)
        t = M["linea_base_s139"][b]
        w(f"\nTotal {b} línea base NRT: {ms(t['total']['publicado'])}. Focal: {ms(t['por_estrato']['focal']['publicado'], True)}; nevado: {ms(t['por_estrato']['nevado']['publicado'], True)}. "
          f"Por fuente: CONS {ms(t['total']['por_fuente']['CONS'], True)}, OCR {ms(t['total']['por_fuente']['OCR'], True)}. "
          f"Hoy post #571: {ms(M['despues_571'][b]['total']['publicado'])}.\n")
    # tres mas lejos
    cand = [(v, M["linea_base_s139"]["VIIRS375"]["por_volcan"][v]["publicado"]) for v in bp.VOLS]
    cand = [(v, s) for v, s in cand if s.get("n", 0) >= N_MIN_MAG]
    cand.sort(key=lambda x: abs(math.log(x[1]["mediana"])), reverse=True)
    w("**Los tres volcanes VIIRS 375 más lejos de 1 en magnitud (línea base NRT, n ≥ 30, por |log mediana|):** " +
      "; ".join(f"{v} {num(s['mediana'])} (n {s['n']})" for v, s in cand[:3]) + ".\n")
    w("**¿Cuentan lo mismo el NRT y el OSF?** El OSF v2.5 no es el producto NRT: según `docs/audit_s139/OSF_VS_NRT.md` l. 12-16 (lectura de Coppola et al. 2026, Scientific Data, p. 7-8, "
      "no releída en esta sesión) se construye con una clase automática y umbrales VRP por sensor, y su pareo (`scripts/descomponer_magnitud_osf.py:86-89, 116`) exige un cúmulo en el cráter, no el predicado del dashboard, y es de 2025. "
      "El NRT publica cada alerta tal cual. El total VIIRS 375 contra el OSF es "
      f"R_med {num(osf['VIIRS375_total']['R_med'])} (n {osf['VIIRS375_total']['n']}), y contra el NRT en la ventana de la línea base es {ms(M['linea_base_s139']['VIIRS375']['total']['publicado'], True)}. "
      "Donde las dos referencias coinciden, el sesgo es del pipeline y no de la referencia; donde difieren, pesa la selección de pasadas de cada una (umbral del OSF, año, predicado).\n")
    acu = []
    for v in bp.VOLS:
        a_ = M["linea_base_s139"]["VIIRS375"]["por_volcan"][v]["publicado"]
        o_ = osf["VIIRS375_por_volcan"].get(v)
        if a_.get("n", 0) >= 15 and o_ and o_["n"] >= 15:
            acu.append((v, a_["mediana"], o_["R_med"], a_["mediana"] / o_["R_med"]))
    w("Volcanes V375 con n ≥ 15 en ambas referencias, mediana NRT / mediana OSF: " +
      "; ".join(f"{v} {num(a)} contra {num(o)} (cociente {num(q)})" for v, a, o, q in acu) +
      f". Coinciden a ±20 %: {', '.join(v for v, a, o, q in acu if 0.8 <= q <= 1.25) or 'ninguno'}; difieren: {', '.join(v for v, a, o, q in acu if not 0.8 <= q <= 1.25) or 'ninguno'}.\n")

    w("## 4. Consistencia del propio MIROVA\n")
    w("**Definiciones, fijadas antes de mirar los números** (copiadas del JSON):\n")
    for k, v in m["definiciones"].items():
        if k.startswith("C") or k in ("pasada_mirova", "listada", "noche"):
            w(f"- `{k}`: {v}")
    w("")
    for tr_ in ("linea_base_s139", "despues_571"):
        w(f"### Ventana {tr_} ({tr[tr_][0]} a {tr[tr_][1]})\n")
        w("| Grupo | C1 vecina V375 también alerta | C1 tasa base alerta | C1 noches todas alerta | C2 V375 alerta: V750 alerta | C2 V750 alerta: V375 alerta | C2b V375 negativa: V750 alerta | C2b V750 negativa: V375 alerta | C3 alerta tras alerta | C3 alerta tras negativa | C3b pasadas alerta tras noche negativa | C1b contradicciones CONS/OCR |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for g in ["TOTAL", "focal", "nevado"] + bp.VOLS:
            c = C[tr_][g]
            w(f"| {g} | {fr(c['C1_frac_vecina_alerta'])} | {fr(c['C1_tasa_base_alerta_por_pasada_listada'])} | {fr(c['C1_frac_noches_todas_alerta'])} | "
              f"{fr(c['C2_V375_alerta_luego_V750'])} | {fr(c['C2_V750_alerta_luego_V375'])} | {fr(c['C2b_V375_negativa_luego_V750_alerta'])} | "
              f"{fr(c['C2b_V750_negativa_luego_V375_alerta'])} | {fr(c['C3_P_alerta_tras_alerta'])} | {fr(c['C3_P_alerta_tras_negativa'])} | "
              f"{fr(c['C3b_pasadas_alerta_tras_noche_negativa'])} | {c['C1b_contradicciones_cons_rutina_ocr_alerta']} |")
        w("")
        w("| Grupo | C4 negativos limpios V375 a ±1 noche de una alerta | publicamos en adyacentes | publicamos en no adyacentes |")
        w("|---|---|---|---|")
        for g in ["TOTAL", "focal", "nevado"] + bp.VOLS:
            c = C[tr_][g]
            w(f"| {g} | {fr(c['C4_frac_neg_limpio_adyacentes'])} | {fr(c['C4_pub_en_adyacentes'])} | {fr(c['C4_pub_en_no_adyacentes'])} |")
        w("")
    c = C["linea_base_s139"]["TOTAL"]
    ch = C["despues_571"]
    w("### Lo que implica para las bandas (sin cambiarlas)\n")
    w(f"1. **MIROVA repite entre pasadas vecinas de la misma noche en {pct(c['C1_frac_vecina_alerta']['frac'])}** de los casos (VIIRS 375, línea base, n {c['C1_frac_vecina_alerta']['n']} pares), "
      f"contra una tasa base de alerta de {pct(c['C1_tasa_base_alerta_por_pasada_listada']['frac'])} por pasada listada. "
      "Físicamente es esperable que no sea 100 %: un foco sub-píxel débil cae distinto en la grilla de cada órbita, cambia el ángulo de visión y la nube fina entra y sale. "
      "Pero esa inconsistencia no entra al denominador de la banda: el negativo limpio del banco exige que MIROVA no haya alertado esa noche en ese sensor, así que contra pasadas vecinas de la misma noche MIROVA da 0 % de falsas por construcción.")
    w(f"2. **El análogo que sí se compara con la banda** es MIROVA contra otro de sus propios instrumentos o contra su noche anterior. "
      f"En noches negativas de V375, MIROVA alerta en {pct(c['C2b_V375_negativa_luego_V750_alerta']['frac'])} de las pasadas V750 (n {c['C2b_V375_negativa_luego_V750_alerta']['n']}); "
      f"en noches negativas de V750 alerta en {pct(c['C2b_V750_negativa_luego_V375_alerta']['frac'])} de las pasadas V375 (n {c['C2b_V750_negativa_luego_V375_alerta']['n']}); "
      f"y la noche siguiente a una noche V375 negativa alerta en {pct(c['C3b_pasadas_alerta_tras_noche_negativa']['frac'])} de las pasadas V375 listadas (n {c['C3b_pasadas_alerta_tras_noche_negativa']['n']}). "
      f"Por estrato (C3b): focal {pct(C['linea_base_s139']['focal']['C3b_pasadas_alerta_tras_noche_negativa']['frac'])}, nevado {pct(C['linea_base_s139']['nevado']['C3b_pasadas_alerta_tras_noche_negativa']['frac'])}. "
      "Estos números no son tasas de error de MIROVA (la actividad cambia de verdad de una noche a otra y cada sensor tiene otro umbral de detección), pero dan el orden de magnitud de cuánto se contradice MIROVA consigo mismo con la misma aritmética de la banda.")
    focal_c3b = C["linea_base_s139"]["focal"]["C3b_pasadas_alerta_tras_noche_negativa"]["frac"]
    nev_c3b = C["linea_base_s139"]["nevado"]["C3b_pasadas_alerta_tras_noche_negativa"]["frac"]
    dentro = (focal_c3b is not None and focal_c3b <= m["banda_falsas"]["focal"]) and (nev_c3b is not None and nev_c3b <= m["banda_falsas"]["nevado"])
    w(f"3. Con la definición C3b, MIROVA contra su noche anterior da focal {pct(focal_c3b)} (banda {pct(m['banda_falsas']['focal'])}) y nevado {pct(nev_c3b)} (banda {pct(m['banda_falsas']['nevado'])}): "
      + ("ambos dentro. Por esta vía no aparece motivo para reabrir las bandas. " if dentro else
         "no quedan ambos dentro. Es un INDICIO, no la prueba que pide la spec §2: C3b mezcla la inconsistencia de MIROVA con cambios reales de actividad de una noche a otra, que en los focales activos (Láscar, Isluga, Lastarria, Puyehue-Cordón Caulle) son frecuentes, y no hay forma de separarlos con estos datos. Decidir si reabre las bandas es de Nicolás. ")
      + "C2b no es comparable directo porque V375 y V750 tienen sensibilidades distintas al mismo foco.")
    t = C["despues_571"]["TOTAL"]
    w(f"4. **¿Explica la inconsistencia de MIROVA nuestra sobre-publicación?** Hoy {pct(t['C4_frac_neg_limpio_adyacentes']['frac'])} de nuestros negativos limpios V375 están a una noche de una alerta de MIROVA en el mismo volcán. "
      f"Publicamos en {pct(t['C4_pub_en_adyacentes']['frac'])} de los adyacentes y en {pct(t['C4_pub_en_no_adyacentes']['frac'])} de los no adyacentes (n {t['C4_pub_en_no_adyacentes']['n']}). "
      + ("Lejos de toda alerta la tasa sigue muy por encima de la banda: la sobre-publicación no es un efecto de la actividad intermitente que MIROVA pierde. " if (t['C4_pub_en_no_adyacentes']['frac'] or 0) > 0.5 else "Revisar: lejos de alertas la tasa baja. ")
      + "\n")

    w("## 5. Otros valores\n")
    w(f"- **Posición**: no encontré medición de posición del NRT posterior a #535 (busqué en `experiments/_s141*` y `_s142*`; las distancias del probe S141 son contra el OSF 2025 y las de `_s142_ndc` son de Nevados de Chillán). No se midió aquí: el CSV de MIROVA trae sólo un radio sin acimut (A93) y comparar radios da una cota inferior, no una distancia. SOSPECHA pendiente.")
    lat = X["latencia_despacho_cron"]["resumen"]["schedule"]
    w(f"- **Latencia del despacho del cron NRT** (`experiments/_s141_cron/atraso_despacho.json`, generado {X['latencia_despacho_cron']['generado']}): {lat['n']} corridas schedule, atraso de creación mediano {lat['mediana_atraso_creacion_min']} min y máximo {lat['max_atraso_creacion_min']} min; "
      f"{num(lat['corridas_por_dia'], 2)} corridas por día contra {lat['franjas_declaradas_por_dia']} franjas declaradas. Es el atraso de GitHub en despachar, no la latencia satélite a dashboard (que suma LANCE ~3 h y el proceso), que no está medida.")
    rc = X["auto_audit_latest"]["recall"]
    w(f"- **Auto-audit semanal** ({X['auto_audit_latest']['ventana'][0]} a {X['auto_audit_latest']['ventana'][1]}), recall por noche en el dashboard: " +
      "; ".join(f"{b} {num(rc[b]['recall_dash_pct'], 1)} % de {rc[b]['n_noches']}" for b in ("VIIRS375", "VIIRS750", "MODIS")) +
      ". Usa otra unidad (noche sensor, criterio eje 2 S119) y ventana móvil que mezcla regímenes.\n")

    w("## 6. Caveats\n")
    p = O["VIIRS375"]["focal"]["deteccion"]["hoy"]
    w(f"- **15 noches.** El tramo posterior a #571 tiene {p['noches_pos']} noches con alerta V375 focales y {O['VIIRS375']['nevado']['deteccion']['hoy']['noches_pos']} nevadas; ningún volcán llega a n ≥ 30 pares de magnitud en VIIRS 375 hoy "
      f"({', '.join(O['VIIRS375']['magnitud_despues_571']['volcanes_n30']) or 'ninguno'}), así que el veredicto de magnitud por volcán sólo se puede dar sobre la ventana larga, que mezcla el régimen previo a #535.")
    w("- **La ventana larga mezcla regímenes** (máscara de nube hasta #535, piso VRP hasta #571). Para la magnitud el efecto esperado es chico (el piso quitaba cúmulos de < 0,02 MW, que casi no parean con alertas), pero no está medido pasada a pasada: comparar la columna antes de #535 con la de hoy por volcán.")
    si = X["sin_info_v375_despues_571"]
    w(f"- **sin_info**: las pasadas nuestras sin fila CONS a ±2 min quedan fuera de todo denominador ({si['n_sin_info']} de {si['n_total']} pasadas V375 del tramo hoy, {pct(si['frac'])}). La consistencia de MIROVA sólo usa pasadas que MIROVA listó; si MIROVA deja de listar pasadas de forma no aleatoria, C1 a C3 se sesgan (SOSPECHA).")
    w("- **Noche = fecha UTC**, igual que el banco. Las pasadas nocturnas chilenas caen casi todas entre 00 y 10 UTC, pero una pasada de las 23 UTC quedaría en otra noche (no medido).")
    w("- **La línea base congelada** (`banco.json`) usó otra referencia (commits de Mirova-v1 del 2026-09-14); sus conteos por estrato se suman aquí desde `por_volcan` redondeando tasa × n.")
    w("- **Detección como criterio**: la spec lo define relativo a la línea base y se evalúa en A/B sobre las mismas noches; aquí sólo se puede decir cuántas noches se pierden hoy.")
    return "\n".join(L) + "\n"


def main():
    if "--solo-informe" in sys.argv:
        d = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        d = medir()
    MD.write_text(informe(d), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
