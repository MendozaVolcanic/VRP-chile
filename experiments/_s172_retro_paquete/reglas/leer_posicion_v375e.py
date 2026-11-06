# -*- coding: utf-8 -*-
"""S166 V375-E, adenda 2 (PREREGISTRO_E.md §8): los tres brazos de posición del record sobre la MISMA detección de la
vía «código MIROVA» de VIIRS 375, contra lo que publica MIROVA. Sólo lectura.

EL FENÓMENO. La regla de posición importa sólo en una escena: un píxel débil junto al cráter y una fuente más radiante
lejos (otro foco del complejo, un borde de nube, un incendio). La vía (`pipeline/mirova_v750_codigo.py::procesar_grilla`)
ubica el record en el centroide del cúmulo 8-conexo de la alertada más radiante (RADIANTE); si cae fuera del radio
interior el record queda lejano y el tablero calla. Con CERCANO (el alertado más cercano al cráter) el mismo record
queda en la cumbre y el tablero publica la suma de todos los alertados. Con PICO (el alertado de mayor radiancia MIR,
el mismo que siembra el cúmulo) manda un píxel solo: difiere de radiante cuando el cúmulo cruza el borde del radio.
El VRP y la máscara no cambian entre brazos: sólo cambia la distancia, y con ella `distance_class`.

QUÉ LEE. (1) La vía de `pipeline/` sobre las grillas guardadas de los lotes S159, S162, S162b (marco de V375-B y C) y del
lote FAR (pasadas en que MIROVA publicó una fuente lejana, `objetivos_far_v375.py`). (2) Por pasada, las tres
distancias medidas desde el cráter (`posicion_de`, como producción mide desde `get_detection_anchor`), frontera
inclusiva (`summit` si la distancia es `inner_radius_km` o menos, igual que la vía). (3) Cada variante del record pasa
por `store.append_record` (como en producción) y por el predicado del tablero ejecutado con node (A97).

VARAS (§8.4 del pre-registro):
  1. Alertas y negativos limpios del marco, con los pesos de PREREGISTRO_B.md §3: las lecturas de evaluar.py (P1,
     P1b, recall, silencio, MISSION, magnitud), tomadas de evaluar.py sin copiar (identificado por sha256 con fin de
     línea LF), para cada brazo contra K.
  2. Pasadas lejanas de MIROVA (`far_tabla`, censo, peso 1): cuántas tienen algún alertado en la caja (si no, un cero de
     «publica» no distingue «la escena no ocurrió» de «el brazo no publica de más») y cuántas publica cada brazo
     (lo correcto es cero), por nombre; P2-L de cada brazo contra K (prueba de signos por bloque noche-volcán, D-45).
     `far_ocr` (etiqueta del scraper, A11) se informa y no decide.
  3. Distancia de cada brazo medida desde el punto de referencia de MIROVA (X0, Y0) contra la `Distancia_km` de
     MIROVA: diferencia de radios, no de posiciones (A93): sirve para descartar, no para afirmar. Informa.
REGLA DE POSICIÓN (RP, §8.5): veto por protegida que K publica; entre los que quedan, el que GANA a todos en la prueba
de signos del error de posición; si ninguno, radiante si no lo vence nadie; si no, NO RESUELTO y decide Nicolás.

CONTROLES (si uno cae: exit 3 y «LECTURA NO LEGIBLE»): C1 una sola alertada => tres brazos iguales (con un caso al
menos); C2 el predicado responde a distance_class en las dos direcciones; C3 listas (ids, clases, sin gránulo atado por
sha256); C4 evaluar.py es el del pre-registro; C5 radiante y pico recalculados = el record de la vía; C6 el almacén no
cambia la distance_class de ninguna variante; C7 control de vida del run FAR (las 20 re-medidas de S162 dan el mismo
M14); C8 el PLACEBO (K x 1,2) publica donde K re-corrido publica; C9 el placebo de M con comparador no da MEJORA (§9.4).
Una pasada sin resultado o sin grilla es SIN DATO: se cuenta antes de cualquier número. COMPUERTA (§9.3): si la
equivalencia da NO EQUIVALENTE, exit 4 y no se lee la regla de posición ni el §5.
ADENDA 3 (§9, S167): con el brazo que elige la RP, el §5.2 (M con el evaluador común), el §5.3 (curva, informa en la
retrospectiva) y la regla del §5.4 en código (`criterios_retro`, `regla_adopcion`), todo fijado antes de leer.

Uso: python -I leer_posicion_v375e.py --art-far <artefactos del run FAR> [--art-s159 ..] [--art-s162 ..]
       [--art-s162b ..] [--salida ..] [--json ..]
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
V375 = AQUI.parent
RAIZ = V375.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(V375))

SHA_EVALUAR_LF = "2126b7439809cc541d3e8c3aec26b09b0b4b02eb562ea716d165a8ab2742bc66"   # evaluar.py de main 248d21f17
BLOB_VIA_921 = "a9c00eaf137896231c5cb43759b1110b1e0d539c"   # pipeline/mirova_v750_codigo.py en bd711db63 (#921)
BRAZOS_POS = ("radiante", "cercano", "pico")
CLASES_FAR = ("far_tabla", "far_ocr")
FRONTERA_OCR = "2026-06-13"         # A119: antes, el OCR no tiene distancia medida
TOL_DIST_KM = 5e-4 + 1e-9           # C5: el record redondea a 1e-3 km (media unidad, más el error de coma flotante)
UMBRAL_COBERTURA = 0.10
SENSOR_SNPP = "VIIRS_SNPP"           # §8.13 (N-3)
HITO_N3 = "2026-10-09"
TOL_VRP_MW = 1e-3                  # §3.1: VRP a 1e-3 MW en el 99 % o más
FRAC_VRP = 0.99
ID_FAR = (20000, 29000)
ID_CTLF = (29000, 30000)
# VE2-10: sin rutas por defecto, para que leer el marco sea siempre explícito (no se mira antes del sello). Las de los
# lotes para el §8.9: D:\vrp-trabajo\temporales\s159_portes\run_39712862945 (S159),
# C:\vrp-trabajo\temporales\s162_v375\run_40116289866 (S162) y C:\vrp-trabajo\temporales\s162_v375\run_40131572769 (S162b).
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def sha256_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def blob_git(ruta):
    """El hash de git del archivo como lo guarda git: con core.autocrlf el checkout de Windows tiene CRLF y el blob LF,
    así que se normaliza antes (sin esto, un archivo idéntico al de #921 daba DISTINTO)."""
    b = Path(ruta).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def cargar_evaluar():
    """C4: evaluar.py se identifica ANTES de importarlo; si no es el del pre-registro, no se carga."""
    s = sha256_lf(V375 / "evaluar.py")
    if s != SHA_EVALUAR_LF:
        return None, s
    import evaluar as E
    return E, s


# ---------------------------------------------------------------- las tres distancias
def pos_ref(g):
    """X0, Y0 (punto de referencia de MIROVA) en índices fraccionarios de celda, con el origen de posicion_de."""
    paso = float(g["paso"])
    return (g["ul_y"] - g["y0"]) / paso - 0.5, (g["x0"] - g["ul_x"]) / paso - 0.5


def distancias(mascara, m13, crater, ref, paso_km, cumulo):
    """Las tres distancias (km) sobre la misma máscara. `cumulo` es la función de la vía (_cumulo_del_mas_radiante):
    radiante y pico salen del mismo cúmulo que usa procesar_grilla, con su mismo desempate. Cercano: el alertado de
    menor distancia al cráter; a igual distancia, el de menor (fila, columna). Cada brazo se mide también desde X0, Y0
    (vara 3), con el MISMO objeto elegido desde el cráter."""
    celdas = [(int(a), int(b)) for a, b in zip(*np.nonzero(mascara))]
    if not celdas:
        return None
    cu = cumulo(mascara, m13)
    fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    pico = max(cu, key=lambda p: m13[p])

    def d(a, b, o):
        return float(np.hypot(a - o[0], b - o[1]) * paso_km)
    cer = min(celdas, key=lambda p: (d(p[0], p[1], crater), p))
    return {"radiante": d(fr, fc, crater), "cercano": d(cer[0], cer[1], crater), "pico": d(pico[0], pico[1], crater),
            "radiante_ref": d(fr, fc, ref), "cercano_ref": d(cer[0], cer[1], ref), "pico_ref": d(pico[0], pico[1], ref),
            "n_alertados": len(celdas), "n_cumulo": len(cu)}


def distancias_desde_record(rec):
    """Para la sombra prospectiva (§8.6), donde no hay grilla: radiante = centroid_dist_km, pico = hotspot_dist_km (el
    pico del cúmulo de la alertada más radiante es esa misma alertada), cercano = el menor dist_km de anomaly_pixels
    (redondeado a 0,01 km por la vía). Devuelve None si el record no trae lo necesario."""
    pc = rec.get("primary_cluster") or {}
    px = rec.get("anomaly_pixels") or []
    if not pc or not px or rec.get("hotspot_dist_km") is None or any(p.get("dist_km") is None for p in px):
        return None
    return {"radiante": float(pc["centroid_dist_km"]), "pico": float(rec["hotspot_dist_km"]),
            "cercano": float(min(p["dist_km"] for p in px))}


def clase_dc(dist, inner):
    return "summit" if dist <= inner else "far"


def variante(rec, dist, inner):
    """El record de la vía con la distancia del brazo: cambian distance_class, el centroide del cúmulo y el
    final_hotspot (el guard A46 de store y mirovaEqVrp del tablero leen pc.centroid_dist_km). VRP y máscara, iguales."""
    r = copy.deepcopy(rec)
    if not r.get("primary_cluster"):
        return r
    r["distance_class"] = clase_dc(dist, inner)
    r["primary_cluster"]["centroid_dist_km"] = round(dist, 3)
    r["final_hotspot_dist_km"] = round(dist, 3)
    return r


def elegir_vara(npix, vrp_port, m, regla_matlab):
    """La vara del VRP del port (§7.3 y §8.6 b). m: la escena de o2_375/matlab_v375.json para esa pasada (o None);
    regla_matlab(): el VRP del port con la regla de relleno de MATLAB por código independiente. De 1 a 4 píxeles, la
    salida de MATLAB si es de esa misma máscara y ese mismo VRP del port; si no, la regla de MATLAB. Sin píxeles, None."""
    if not npix:
        return None
    if 1 <= npix <= 4 and m is not None and m["npix"] == npix and abs(m["vrp_port_mw"] - vrp_port) <= 1e-6:
        return m["vrp_vara_mw"]
    return regla_matlab()


# ---------------------------------------------------------------- la vía real (sólo en main)
def record_de_la_via(o, g, mir, tir, r, v, MV):
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    box = MV.caja_v375(g, vlat, vlon)
    pos = MV.posicion_de(g, vlat, vlon)
    rec = MV.procesar_grilla(mir, tir, g, box, r["dayflag"], r["sunglint"], pos, v["inner_radius_km"], o["sensor"],
                             familia="VIIRS375")
    mascara = MV.detectar_mirova(mir, tir, box, r["dayflag"], r["sunglint"], lam_mir=MV.LAMBDA_I4, lam_tir=MV.LAMBDA_I5)
    return rec, mascara, pos


def por_el_almacen(rec, nombre, v, tmp, dt="2026-01-01 05:00"):
    """Como en producción: store.append_record sobre un directorio temporal; devuelve el record que quedó escrito o None
    si el almacén no lo escribió."""
    from pipeline import store
    rec = json.loads(json.dumps(rec))
    rec["datetime_utc"] = dt
    rec.setdefault("product_version", "standard")
    viejo = store.DATA_DIR
    store.DATA_DIR = Path(tmp)
    try:
        store.append_record(nombre, rec, max_hotspot_dist_km=v.get("radius_km"),
                            enable_pixel_level_distance_filter=True, max_cluster_pixels=v.get("max_cluster_pixels"),
                            inner_radius_km=v.get("inner_radius_km"), overwrite=True)
        f = Path(tmp) / f"{nombre}.json"
        recs = json.loads(f.read_text(encoding="utf-8"))["records"] if f.exists() else []
        return recs[-1] if recs else None
    finally:
        store.DATA_DIR = viejo
        for q in Path(tmp).glob("*.json"):
            q.unlink()


# ---------------------------------------------------------------- objetivos y listas
def objetivos(far_ruta=None):
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        assert o["id"] not in obj, ("id repetido", o["id"])
        if o["lote"] != "CTL":          # el control de vida de B2 ya se leyó en B2; aquí vale el del run FAR (CTLF)
            obj[o["id"]] = dict(o)
    excl = json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["meta"]["excluidos"]
    for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in excl:
            assert o["id"] not in obj, ("id repetido", o["id"])
            obj[o["id"]] = {**o, "lote": "S159", "estrato": f"{o['volcan']}|{o['estrato_z']}"}
    if far_ruta:
        for o in json.loads(Path(far_ruta).read_text(encoding="utf-8"))["pasadas"]:
            assert o["id"] not in obj, ("id repetido", o["id"])
            obj[o["id"]] = dict(o)
    return obj


def control_listas(obj, far_ruta, sin_g_ruta):
    """C3. Devuelve la lista de fallas (vacía si todo bien)."""
    fallas = []
    far = {i: o for i, o in obj.items() if o.get("lote") == "FAR"}
    ctlf = {i: o for i, o in obj.items() if o.get("lote") == "CTLF"}
    if any(not (ID_FAR[0] <= i < ID_FAR[1]) for i in far):
        fallas.append("ids FAR fuera de [20000, 29000)")
    if any(not (ID_CTLF[0] <= i < ID_CTLF[1]) for i in ctlf):
        fallas.append("ids CTLF fuera de [29000, 30000)")
    if any(i >= ID_FAR[0] for i, o in obj.items() if o.get("lote") not in ("FAR", "CTLF")):
        fallas.append("un id del marco cae en el rango de FAR o CTLF")
    if any(o.get("clase") not in CLASES_FAR for o in far.values()):
        fallas.append("una pasada FAR sin clase far_tabla o far_ocr")
    if any(not o.get("ref_M14") for o in ctlf.values()):
        fallas.append("una pasada CTLF sin ref_M14")
    if far_ruta and sin_g_ruta:
        sg = json.loads(Path(sin_g_ruta).read_text(encoding="utf-8"))
        obj_far = Path(far_ruta).parent / "objetivos_far_v375.json"
        if sg.get("objetivos_far_sha256") != sha256_lf(obj_far):
            fallas.append("sin_granulo_far_v375.json no está atado a objetivos_far_v375.json (sha256)")
    elif far_ruta:
        fallas.append("falta --sin-granulo-far")
    return fallas


# ---------------------------------------------------------------- error de posición y regla RP
def err_pos(x, a, E):
    """El error que cuenta la regla de posición: protegida sin publicar, alerta bajo 1 MW sin publicar, publicación en
    negativo limpio (E.err) o publicación en una pasada lejana de la tabla. far_ocr no cuenta."""
    pub = E.publica(x, a)
    return E.err(x, a) or (x["c"] == "pos_prot" and not pub) or (x["c"] == "far_tabla" and pub)


def p2_con(filas, a, ref, E, f_err):
    blo = collections.defaultdict(float)
    tramo_de = {}
    for x in filas:
        ea, er = f_err(x, a), f_err(x, ref)
        if ea != er:
            blo[x["bloque"]] += x["w"] * (1 if ea else -1)
            tramo_de[x["bloque"]] = x["tramo"]
    sumas = [blo[k] for k in sorted(blo)]
    neto = float(sum(sumas))
    p = E.prueba_signos(sumas, neto)
    return {"neto": neto, "B": len(sumas), "p": p, "veredicto": E.regla_signos(neto, len(sumas), p),
            "bloques_por_tramo": dict(sorted(collections.Counter(tramo_de.values()).items()))}


def decidir_brazo(vivos, veredicto_par):
    """§8.5 pasos 2 a 4, sobre los brazos que pasaron el veto. veredicto_par(a, b) es el veredicto de a contra b en la
    prueba de signos del error de posición (GANA si a comete menos errores con valor-p 5 % o menos)."""
    if not vivos:
        return "NINGUN BRAZO PASA EL VETO", []
    if len(vivos) == 1:
        return f"ELEGIDO {vivos[0].upper()} (unico que pasa el veto)", list(vivos)
    gana = [a for a in vivos if all(veredicto_par(a, b) == "GANA" for b in vivos if b != a)]
    if len(gana) == 1:
        return f"ELEGIDO {gana[0].upper()} (gana a los demas)", gana
    no_vencidos = [a for a in vivos if not any(veredicto_par(b, a) == "GANA" for b in vivos if b != a)]
    if not no_vencidos:          # ciclo (a vence a b, b a c, c a a): VE2-09 del verificador
        return "NO RESUELTO ENTRE " + " Y ".join(x.upper() for x in vivos) + " (ciclo; decide Nicolas)", list(vivos)
    if len(no_vencidos) == 1:
        return f"ELEGIDO {no_vencidos[0].upper()} (nadie lo vence)", no_vencidos
    if "radiante" in no_vencidos:
        return "SE QUEDA RADIANTE (nadie la vence; la del codigo)", no_vencidos
    return "NO RESUELTO ENTRE " + " Y ".join(x.upper() for x in no_vencidos) + " (decide Nicolas)", no_vencidos


def resultado_rp(veredicto):
    """Lo que dice un veredicto de la RP, sin la explicación: el brazo (ELEGIDO x, o RADIANTE si se queda), o la clase
    del no-resultado (NO RESUELTO, NINGUN, NO DECIDE). Para comparar la unión con cada tramo (N-2)."""
    if veredicto.startswith("ELEGIDO"):
        return veredicto.split()[1]
    if veredicto.startswith("SE QUEDA RADIANTE"):
        return "RADIANTE"
    for k in ("NO RESUELTO", "NINGUN", "NO DECIDE"):
        if veredicto.startswith(k):
            return k
    return veredicto


def no_veta_n3(x):
    """§8.13 (N-3), sellado por Nicolás el 2026-10-28: una protegida sólo del OCR (sin alerta de la tabla) de Suomi NPP
    anterior al 2026-10-09 se informa aparte y no veta, ni en la regla de posición ni en el §5.4 (a), igual que en el
    auto-audit (PR #924). La de la tabla, la de otra plataforma o la de ese día en adelante siguen vetando."""
    return x["c"] == "pos_prot" and not x["tabla"] and x.get("sensor") == SENSOR_SNPP and x["hora"][:10] < HITO_N3


def regla_posicion(filas, E, far_ok=True, solo_tabla=False):
    """§8.5. filas: marco + far_tabla (sin CTL ni CTLF). solo_tabla: el veto cuenta sólo protegidas con alerta de la
    tabla (informa). Devuelve (veredicto, detalle)."""
    det = {"veto": {}, "pares": {}}
    marco = [x for x in filas if x["c"] not in CLASES_FAR]
    prot_k = [x for x in marco if x["c"] == "pos_prot" and x["K"] and (x["tabla"] or not solo_tabla)]
    # §8.13 (N-3, sellado por Nicolás): la protegida sólo del OCR de Suomi NPP anterior al hito no veta; se informa aparte
    det["informadas_aparte_n3"] = [(x["vol"], x["hora"]) for x in prot_k if no_veta_n3(x)]
    prot_k = [x for x in prot_k if not no_veta_n3(x)]
    # VE2-01: el veto de la posición cuenta sólo lo que depende de la posición, la protegida que K publica, el brazo
    # calla y OTRO brazo publica. La que callan los tres no la arregla ninguna regla de posición: se informa aparte y
    # sigue siendo veto del paquete en el §5.4 (a), no de esta elección.
    det["perdidas_comunes"] = [(x["vol"], x["hora"]) for x in prot_k
                               if not any(x["X"][("VIA", b)] for b in BRAZOS_POS)]
    for a in BRAZOS_POS:
        det["veto"][a] = [(x["vol"], x["hora"]) for x in prot_k
                          if not x["X"][("VIA", a)] and any(x["X"][("VIA", b)] for b in BRAZOS_POS if b != a)]
    vivos = [a for a in BRAZOS_POS if not det["veto"][a]]
    det["vivos"] = vivos
    if not far_ok:
        return "NO DECIDE: LAS LEJANAS SIN COBERTURA", det
    for a in vivos:
        for b in vivos:
            if a != b:
                det["pares"][f"{a}|{b}"] = p2_con(filas, ("VIA", a), ("VIA", b), E, lambda x, k: err_pos(x, k, E))
    ver, det["no_vencidos"] = decidir_brazo(vivos, lambda a, b: det["pares"][f"{a}|{b}"]["veredicto"])
    return ver, det


# ---------------------------------------------------------------- lecturas por brazo
def lecturas_far(filas, a, E):
    """Vara 2 para el brazo a (o 'K'). Devuelve conteos por subclase y tramo y la lista de las que publica."""
    out = {}
    for c in CLASES_FAR:
        lst = [x for x in filas if x["c"] == c]
        pub = [x for x in lst if E.publica(x, a)]
        out[c] = {"n": len(lst), "con_alertado": sum(1 for x in lst if x["npix"].get(("VIA", "radiante"), 0)),
                  "publica": len(pub), "por_tramo": dict(sorted(collections.Counter(x["tramo"] for x in pub).items())),
                  "lista": [(x["vol"], x["hora"], round(x.get("dref") or -1, 2)) for x in pub][:40]}
    return out


def vara3(filas, a):
    """Vara 3: |distancia del brazo desde X0, Y0 − Distancia_km de MIROVA|, por grupo (A93: informa)."""
    out = {}
    for g in ("alerta_tabla", "alerta_ocr", "far_tabla"):
        d = [abs(x["dist_ref"][a] - x["dmiro"][g]) for x in filas
             if x.get("dist_ref") and x["dmiro"].get(g) is not None]
        out[g] = {"n": len(d)} if not d else {"n": len(d), "mediana": round(float(np.median(d)), 3),
                                              "a_una_celda": sum(1 for v in d if v <= 0.375),
                                              "a_1km": sum(1 for v in d if v <= 1.0)}
    return out


def distancias_mirova(o):
    """Distancia de MIROVA por grupo: la mayor alerta de la tabla, la mayor alerta del OCR desde el 2026-06-13 (A119) y,
    en una far_tabla, la de la fila FALSO_POSITIVO del consolidado (dist_ref del generador)."""
    out = {}
    filas = o.get("mirova") or []
    t = [f for f in filas if str(f.get("tipo", "")).startswith("ALERTA") and f.get("source") == "CONS"
         and f.get("dist_km") is not None and (f.get("vrp_mw") or 0) > 0]
    oc = [f for f in filas if str(f.get("tipo", "")).startswith("ALERTA") and f.get("source") == "OCR"
          and f.get("dist_km") is not None and (f.get("vrp_mw") or 0) > 0 and o["hora_utc"][:10] >= FRONTERA_OCR]
    if t:
        out["alerta_tabla"] = max(t, key=lambda f: f["vrp_mw"])["dist_km"]
    if oc:
        out["alerta_ocr"] = max(oc, key=lambda f: f["vrp_mw"])["dist_km"]
    if o.get("clase") == "far_tabla" and o.get("dist_ref") is not None:
        out["far_tabla"] = o["dist_ref"]
    return out


# ---------------------------------------------------------------- §9 (adenda 3, S167): magnitud, curva y §5.4 en código
# POR QUÉ. El verificador del cuerpo (VC167-03 y VC167-04) mostró que el §5.2, el §5.3 y la regla del §5.4 no tenían
# quién los calculara, y que el §5.4 no decía qué hacer con varias salidas posibles. Si eso se escribe después de ver
# qué brazo salió, el pre-registro pierde su valor. Aquí queda todo fijado antes de abrir el run FAR o el marco.
MODO_M = "decide"                      # §9.5: el corte que decide (c) es la unión del marco, en modo «decide»
CUMPLE, NO_CUMPLE, NICOLAS, INFORMA = "CUMPLE", "NO CUMPLE", "DECIDE NICOLAS", "INFORMA"


def pares_magnitud(filas, a):
    """§9.5: pares de M (D-27) del brazo a contra K, como `evaluador_comun.pares_m`: alertas de MIROVA con VRP (pos_prot
    y pos_bajo) que los dos publican con magnitud mayor que 0. La de K es la de K re-corrido (VK), la única que el
    predicado del tablero muestra en el run. Sin peso de población: el evaluador común remuestrea por bloque
    noche-volcán (D-27); las protegidas, que son censo, pesan más que en la población, y por eso se informa también
    por clase. Devuelve (pares, cuántas salen porque publica uno solo)."""
    pares, salen = [], 0
    for x in filas:
        if not x["c"].startswith("pos") or not x["mir"] > 0:
            continue
        pk, pa = bool(x["K"]), bool(x["X"][a])
        if pk != pa:
            salen += 1
            continue
        k, d = x.get("VK"), x["V"].get(a)
        if not pk or k is None or not k > 0 or d is None or not d > 0:
            continue
        pares.append({"k": float(k), "d": float(d), "m": float(x["mir"]), "clave": f"{x['vol']}|{x['hora']}",
                      "bloque": x["bloque"], "z": x["z"], "c": x["c"], "tabla": x["tabla"], "tramo": x["tramo"]})
    return pares, salen


def estado_c(veredicto_m):
    """§9.7 (c): MEJORA (que en modo «decide» ya exige d′ MEJORA, D-28) y NEUTRO cumplen; EMPEORA, INDECIDIBLE y SIN
    SUSTRATO no (el instrumento no certifica que no empeore)."""
    return CUMPLE if veredicto_m in ("MEJORA", "NEUTRO") else NO_CUMPLE


def magnitud(filas, a, EC):
    """§9.5: M del brazo a contra K con el evaluador común. Decide la unión; informan los cortes por tramo de 10° de
    cenit, volcán, canal (tabla o sólo OCR) y clase. A104: si O1 u O2 por separado, con sustrato, da otro estado de (c)
    que la unión (en cualquier dirección), se marca y decide Nicolás."""
    P, salen = pares_magnitud(filas, a)
    r, det = EC.decidir_estrato(P, MODO_M)
    cortes = {"cenit": lambda p: EC.tramo_cenit(p["z"]), "volcan": lambda p: p["clave"].split("|")[0],
              "canal": lambda p: "tabla" if p["tabla"] else "solo_ocr", "clase": lambda p: p["c"]}
    inf = {}
    for nom, f in cortes.items():
        g = collections.defaultdict(list)
        for p in P:
            g[f(p)].append(p)
        inf[nom] = {k: EC.decidir_estrato(v, "informa")[0] for k, v in sorted(g.items())}
    por_tramo = {tr: EC.decidir_estrato([p for p in P if p["tramo"] == tr], MODO_M)[0] for tr in ("T", "O1", "O2")}
    a104 = [tr for tr in ("O1", "O2") if por_tramo[tr] != "SIN SUSTRATO" and estado_c(por_tramo[tr]) != estado_c(r)]
    return {"veredicto": r, "n": len(P), "salen_publica_uno": salen, "detalle": det, "informa": inf,
            "por_tramo": por_tramo, "a104": a104}


def pares_k(filas):
    """Los pares de K consigo mismo (para el placebo de M): alertas de MIROVA con VRP que K publica con magnitud > 0."""
    return [{"k": float(x["VK"]), "d": float(x["VK"]), "m": float(x["mir"]), "clave": f"{x['vol']}|{x['hora']}",
             "bloque": x["bloque"]}
            for x in filas if x["c"].startswith("pos") and x["mir"] > 0 and x["K"] and (x.get("VK") or 0) > 0]


def control_placebo_m(filas, EC):
    """C9 (§2 y §9.4): el placebo K x 1,2 (y x 0,8) con el comparador no puede dar MEJORA (d′ es 0 por construcción).
    Si la da, el instrumento está roto. Devuelve (ok, detalle)."""
    pl = EC.placebo_ganancia(pares_k(filas), MODO_M)
    return all(v["con_comparador"] != "MEJORA" for v in pl.values()), pl


def placebo_k(rec, factor):
    """El record de K re-corrido con el VRP x factor (PLACEBO del §2), en los tres campos que puede mostrar el tablero."""
    r = copy.deepcopy(rec)
    for k in ("vrp_mw", "f5_core_vrp_mw"):
        if r.get(k) is not None:
            r[k] = float(r[k]) * factor
    if r.get("primary_cluster") and r["primary_cluster"].get("vrp_mw") is not None:
        r["primary_cluster"]["vrp_mw"] = float(r["primary_cluster"]["vrp_mw"]) * factor
    r["_placebo_k"] = True
    return r


def curva(filas, a, E, CC):
    """§9.6: la curva de cenit (`curva_cenit.py`) del brazo a (o 'K') sobre las alertas del marco, condicionada y sin
    condicionar. En la retrospectiva INFORMA: medido sobre la lista antes de leer, el marco tiene a lo más 5 noches para el
    nulo de cenit parecido, bajo el mínimo de 8, así que da SIN SUSTRATO por construcción."""
    pas = [{"vol": x["vol"], "hora": x["hora"], "z": x["z"], "mir": x["mir"], "plat": x.get("sensor"),
            "pub": bool(E.publica(x, a)), "vrp": x.get("VK") if a == "K" else x["V"].get(a)}
           for x in filas if x["c"].startswith("pos")]
    out = {}
    for nom, cond in (("condicionada", True), ("sin_condicionar", False)):
        r = CC.resumen(CC.pares_por_noche(pas, "vrp", "pub", condicionar=cond),
                       nulo=CC.pares_nulo(pas, "vrp", "pub", condicionar=cond))
        out[nom] = {"veredicto": CC.veredicto(r), "noches": r["todas"]["n_noches"], "noches_nulo": r["nulo"]["n_noches"],
                    "d": r["todas"]["d"]}
    return out


def estado_d_sombra(cur_p, cur_k):
    """§9.7 (d), para la SOMBRA (en la retrospectiva informa): con la curva condicionada, REPRODUCE LA CURVA cumple;
    también cumple si el extremo inferior del IC de D del paquete supera al extremo superior del IC de D de K (cada uno
    con sus pares, como los arma curva_cenit) y el paquete no CAE MENOS QUE MIROVA; SIN SUSTRATO y NULO SESGADO pasan a
    Nicolás; lo demás no cumple."""
    v = cur_p["veredicto"]
    if v in ("SIN SUSTRATO", "NULO SESGADO"):
        return NICOLAS
    if v == "REPRODUCE LA CURVA":
        return CUMPLE
    if v != "CAE MENOS QUE MIROVA" and cur_k["veredicto"] not in ("SIN SUSTRATO", "NULO SESGADO") \
            and cur_p["d"][1][0] > cur_k["d"][1][1]:
        return CUMPLE
    return NO_CUMPLE


def criterios_retro(v1, p2l, m):
    """§9.7: los criterios (a), (b) y (c) del §5.4 en la retrospectiva para un brazo; (d) informa (sólo decide en la
    sombra). v1 = vara1[a], p2l = P2-L del brazo contra K, m = magnitud(...)."""
    c = {"a": CUMPLE if not v1["P1_veto_n3"] else NO_CUMPLE,
         "b": CUMPLE if (v1["P2_K"]["veredicto"] in ("GANA", "EMPATE", "SIN SUSTRATO")
                         and v1["lecturas"]["silencio"]["veredicto"] != "ENCIENDE DE MAS"
                         and p2l["veredicto"] not in ("PIERDE", "BLOQUEA")) else NO_CUMPLE,
         "c": NICOLAS if m["a104"] else estado_c(m["veredicto"]),
         "d": INFORMA}
    v = list(c.values())
    c["retrospectiva"] = NO_CUMPLE if NO_CUMPLE in v else NICOLAS if NICOLAS in v else "CUMPLE (falta la sombra)"
    return c


def regla_adopcion(ver_rp, det_rp, crit):
    """§9.7: del veredicto de la RP y de los criterios por brazo, el estado del paquete en la retrospectiva. ELEGIDO o
    SE QUEDA RADIANTE sin marca A104: el del brazo. NINGUN BRAZO PASA EL VETO: NO CUMPLE. NO RESUELTO (ciclo incluido),
    NO DECIDE o marca A104: DECIDE NICOLAS entre los candidatos, salvo que ninguno cumpla (entonces NO CUMPLE).
    Devuelve (estado, candidatos)."""
    r = resultado_rp(ver_rp)
    if r == "NINGUN":
        return NO_CUMPLE, []
    if r == "NO DECIDE":
        cand = list(BRAZOS_POS)
    elif r == "NO RESUELTO":
        cand = list(det_rp.get("no_vencidos") or BRAZOS_POS)
    else:
        cand = [r.lower()]
        if "A104" not in ver_rp:
            return crit[cand[0]]["retrospectiva"], cand
    if all(crit[a]["retrospectiva"] == NO_CUMPLE for a in cand):
        return NO_CUMPLE, cand
    return NICOLAS, cand


def codigo_salida(fallas, out):
    """3 si cayó un control (LECTURA NO LEGIBLE); 4 si la equivalencia no pasa (el paquete no es el código, §9.3); 0 si
    la lectura llegó al final."""
    if fallas:
        return 3
    return 4 if out.get("corte") == "NO EQUIVALENTE" else 0


# ---------------------------------------------------------------- análisis (sin red ni grillas: lo prueba la batería)
def analizar(pasadas, obj, meta, publicar, E, art_far_presente):
    """pasadas: {id: {'rec': record de la vía tras el almacén (o None), 'dist': distancias(...) o None, 'npix': n,
    'vrp_port': VRP del port C13 (vara de la adenda 1), 'mascara_igual': bool, 'k_rec': record K re-corrido o None,
    'dc_almacen_igual': {brazo: bool}, 'inner': inner del tablero, 'm14': (npix, vrp) del runner o None}}.
    publicar(casos) -> [(disp, pub)] con casos = [(record, inner)]. Devuelve (salida, fallas_de_instrumento)."""
    fallas = []
    out = {}
    # ---- publicación de cada brazo, del port con la misma posición (equivalencia), de K re-corrido y controles
    casos, idx = [], []
    for i, p in sorted(pasadas.items()):
        for a in BRAZOS_POS:
            ra = None if p["rec"] is None or p["dist"] is None else variante(p["rec"], p["dist"][a], p["inner_v"])
            casos.append((ra if ra is not None else (p["rec"] or {}), p["inner"]))
            idx.append((i, "via", a))
            if ra is not None and p.get("vrp_port") is not None:
                rp = copy.deepcopy(ra)
                rp["vrp_mw"] = round(float(p["vrp_port"]), 3)
                rp["primary_cluster"]["vrp_mw"] = rp["vrp_mw"]
                casos.append((rp, p["inner"]))
                idx.append((i, "port", a))
        if p.get("k_rec") is not None:
            casos.append((p["k_rec"], p["inner"]))
            idx.append((i, "Krun", ""))
            casos.append((placebo_k(p["k_rec"], E.FACTOR_PLACEBO), p["inner"]))     # PLACEBO del §2 (C8)
            idx.append((i, "Kplac", ""))
    base = {"vrp_mw": 0.4, "distance_class": "summit", "t_max_k": 290, "sensor": "VIIRS_NOAA20",
            "triggered_test1": False, "via_codigo_mirova": True,
            "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}
    casos += [(base, 5.0), (variante(base, 9.0, 5.0), 5.0), (variante(variante(base, 9.0, 5.0), 0.5, 5.0), 5.0)]
    idx += [("C2", "summit", ""), ("C2", "far", ""), ("C2", "vuelta", "")]
    P = {k: (float(x[0] or 0.0), bool(x[1])) for k, x in zip(idx, publicar(casos))}
    c2 = [P[("C2", "summit", "")][1], P[("C2", "far", "")][1], P[("C2", "vuelta", "")][1]]
    pr(f"  C2 predicado (summit publica, far no, de vuelta a summit publica): {c2}")
    if c2 != [True, False, True]:
        fallas.append("C2")
    # C8 (§2 y §9.4): el PLACEBO (K re-corrido con el VRP x 1,2) publica exactamente donde K re-corrido publica: 0
    # discordantes en P1 y P2. Si no, el predicado depende de la magnitud de una forma que el pre-registro no supone.
    dis_c8 = [i for (i, t, _) in P if t == "Kplac" and P[(i, "Kplac", "")][1] != P[(i, "Krun", "")][1]]
    n_c8 = sum(1 for (_, t, _) in P if t == "Kplac")
    pr(f"  C8 PLACEBO K x {E.FACTOR_PLACEBO} publica igual que K re-corrido: {n_c8 - len(dis_c8)} de {n_c8}", dis_c8[:10])
    if dis_c8:
        fallas.append("C8")

    # ---- C1, C5, C6 y equivalencia por brazo
    uno = [i for i, p in pasadas.items() if p["dist"] and p["dist"]["n_alertados"] == 1]
    malos_c1 = [i for i in uno if len({round(pasadas[i]["dist"][a], 9) for a in BRAZOS_POS}) != 1]
    pr(f"  C1 una sola alertada => tres brazos iguales: {len(uno) - len(malos_c1)} de {len(uno)}")
    if not uno or malos_c1:
        fallas.append("C1")
    con = [i for i, p in pasadas.items() if p["dist"] and p["rec"] and p["rec"].get("primary_cluster")]
    malos_c5 = [i for i in con if abs(pasadas[i]["dist"]["radiante"] - pasadas[i]["rec"]["primary_cluster"]["centroid_dist_km"]) > TOL_DIST_KM
                or abs(pasadas[i]["dist"]["pico"] - pasadas[i]["rec"]["hotspot_dist_km"]) > TOL_DIST_KM
                or pasadas[i]["rec"]["distance_class"] != clase_dc(pasadas[i]["dist"]["radiante"], pasadas[i]["inner_v"])]
    pr(f"  C5 radiante y pico recalculados = record de la vía: {len(con) - len(malos_c5)} de {len(con)}", malos_c5[:10])
    if not con or malos_c5:
        fallas.append("C5")
    malos_c6 = [(i, a) for i, p in pasadas.items() for a, ok in (p.get("dc_almacen_igual") or {}).items() if not ok]
    pr(f"  C6 el almacén no cambia la distance_class de ninguna variante: distintas {len(malos_c6)}", malos_c6[:10])
    if malos_c6:
        fallas.append("C6")
    mm = [i for i, p in pasadas.items() if not p.get("mascara_igual", True)]
    eq = {a: [i for i in pasadas if (i, "port", a) in P and P[(i, "port", a)][1] != P[(i, "via", a)][1]]
          for a in BRAZOS_POS}
    pr(f"  equivalencia (paso 1, §8.3): máscara distinta vía/port en {len(mm)}; publicación distinta vía/port, por "
       f"brazo: " + ", ".join(f"{a} {len(v)}" for a, v in eq.items()))
    con_vrp = [i for i, p in pasadas.items() if p.get("vrp_via") is not None and p.get("vrp_port") is not None]
    fuera = [(i, round(abs(pasadas[i]["vrp_via"] - pasadas[i]["vrp_port"]), 6)) for i in con_vrp
             if abs(pasadas[i]["vrp_via"] - pasadas[i]["vrp_port"]) > TOL_VRP_MW]
    vrp_ok = bool(con_vrp) and len(fuera) <= (1 - FRAC_VRP) * len(con_vrp)
    pr(f"  equivalencia, VRP a {TOL_VRP_MW} MW contra la vara (§7.3 y §8.6 b): {len(con_vrp) - len(fuera)} de "
       f"{len(con_vrp)} (exigido {FRAC_VRP:.0%}); fuera {sorted(fuera, key=lambda t: -t[1])[:10]}")
    # N-1: la misma cifra con la vara vieja del §7.3 (de 1 a 4 px MATLAB, sobre 4 brazos.py tal cual), informativa, para
    # que el efecto del §8.6 b se vea en la lectura y no sólo en el texto (en #921: 289 de 329 contra 329 de 329)
    con_v = [i for i in con_vrp if pasadas[i].get("vrp_port_vieja") is not None]
    fuera_v = [i for i in con_v if abs(pasadas[i]["vrp_via"] - pasadas[i]["vrp_port_vieja"]) > TOL_VRP_MW]
    pr(f"  equivalencia, VRP con la vara vieja del §7.3 (informa, no decide): {len(con_v) - len(fuera_v)} de {len(con_v)}")
    out["equivalencia"] = {"mascara_distinta": mm, "pub_distinta": eq, "vrp": [len(con_vrp) - len(fuera), len(con_vrp)],
                           "vrp_fuera": fuera, "vrp_vara_vieja": [len(con_v) - len(fuera_v), len(con_v)],
                           "veredicto": "EQUIVALENTE" if not mm and not any(eq.values()) and vrp_ok
                           else "NO EQUIVALENTE"}
    pr("  equivalencia:", out["equivalencia"]["veredicto"])

    # ---- C7 control de vida del run FAR
    ctlf = [i for i, o in obj.items() if o.get("lote") == "CTLF"]
    if art_far_presente:
        ok_c = [i for i in ctlf if i in pasadas and pasadas[i].get("m14") is not None]
        dif = [i for i in ok_c if not (pasadas[i]["m14"][0] == obj[i]["ref_M14"][0] and (
            (pasadas[i]["m14"][1] is None and obj[i]["ref_M14"][1] is None) or (
                pasadas[i]["m14"][1] is not None and obj[i]["ref_M14"][1] is not None
                and abs(pasadas[i]["m14"][1] - obj[i]["ref_M14"][1]) < 1e-6)))]
        vivos = sum(1 for i in ok_c if pasadas[i]["m14"][0])
        pr(f"  C7 control de vida del run FAR: {len(ok_c)} de {len(ctlf)} re-medidas; iguales a S162 "
           f"{len(ok_c) - len(dif)}; con píxeles {vivos}", dif[:10])
        if not ctlf or len(ok_c) < 0.9 * len(ctlf) or dif or not vivos:
            fallas.append("C7")
    else:
        pr("  C7 control de vida: SIN RUN FAR (las lejanas quedan SIN DATO y la regla de posición no decide)")

    # ---- K: re-corrido contra publicado (misma regla que evaluar.py)
    con_k = [i for i in pasadas if (i, "Krun", "") in P and obj[i].get("lote") not in ("CTL", "CTLF")]
    igual = sum(1 for i in con_k if P[(i, "Krun", "")][1] == bool(obj[i]["pub_prod"]))
    frac = igual / len(con_k) if con_k else 0.0
    usa_rec = frac < E.UMBRAL_K_RECORRIDO
    pr(f"  K re-corrido publica igual que lo publicado: {igual} de {len(con_k)} ({frac:.3f}); la lectura de K usa "
       f"{'lo RE-CORRIDO' if usa_rec else 'lo publicado'}")

    # ---- filas (pesos del marco: N_h / n_ok_h; far: censo, peso 1)
    arms, pub_k, vk = {}, {}, {}
    for i, p in pasadas.items():
        if obj[i].get("lote") in ("CTL", "CTLF"):
            continue
        arms[i] = {("VIA", a): (P[(i, "via", a)][1], P[(i, "via", a)][0], p["npix"]) for a in BRAZOS_POS}
        # P-sinfiltro (§2 y §9.4): la vía publicando todo lo que detecta, sin el predicado de cumbre. Informa.
        arms[i][("VIA", "sinfiltro")] = (p["npix"] > 0, float(p.get("vrp_via") or 0.0), p["npix"])
        if (i, "Krun", "") in P:
            pub_k[i], vk[i] = P[(i, "Krun", "")][1], P[(i, "Krun", "")][0]
        elif usa_rec:
            pub_k[i] = bool(obj[i]["pub_prod"])
    n_ok = collections.Counter((obj[i]["clase"], obj[i]["estrato"]) for i in arms if obj[i]["clase"] not in CLASES_FAR)
    pesos = {(c, h): v["N"] / n_ok[(c, h)] for c, est in meta.items() for h, v in est.items() if n_ok.get((c, h))}
    for i in arms:
        if obj[i]["clase"] in CLASES_FAR:
            pesos[(obj[i]["clase"], obj[i]["estrato"])] = 1.0
    out["pesos_far"] = sorted({w for k, w in pesos.items() if k[0] in CLASES_FAR})
    filas = E.armar({i: obj[i] for i in arms}, {i: {"geometria_centro": pasadas[i].get("geom") or {}} for i in arms},
                    arms, None, pub_k, vk, usa_rec, pesos)
    for x in filas:
        p = pasadas[x["i"]]
        x["dref"] = obj[x["i"]].get("dist_ref")
        x["sensor"] = obj[x["i"]].get("sensor")
        x["dmiro"] = distancias_mirova(obj[x["i"]])
        x["dist_ref"] = None if not p["dist"] else {a: p["dist"][f"{a}_ref"] for a in BRAZOS_POS}
    marco = [x for x in filas if x["c"] not in CLASES_FAR]
    far = [x for x in filas if x["c"] in CLASES_FAR]

    # ---- cobertura (A108), antes de cualquier número
    pr("\n== cobertura (A108)")
    cob = collections.Counter((o.get("lote"), o.get("clase"), "ok" if i in arms or (i in pasadas and o.get("lote") in ("CTL", "CTLF")) else "SIN DATO")
                              for i, o in obj.items())
    for k, v in sorted(cob.items(), key=str):
        pr("  ", k, v)
    far_tab = [i for i, o in obj.items() if o.get("clase") == "far_tabla"]
    far_ok = bool(far_tab) and art_far_presente and sum(1 for i in far_tab if i in arms) >= (1 - UMBRAL_COBERTURA) * len(far_tab)
    for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto", "far_tabla"):
        n_c = sum(1 for o in obj.values() if o.get("clase") == c)
        n_s = sum(1 for i, o in obj.items() if o.get("clase") == c and i not in arms)
        if n_c and n_s / n_c > UMBRAL_COBERTURA:
            pr(f"   AVISO: {c} tiene {n_s} de {n_c} SIN DATO (más del 10 %)")
    pr("   SIN DATO por nombre:", [(i, obj[i].get("lote"), obj[i]["volcan"], obj[i]["hora_utc"], obj[i].get("clase"))
                                   for i in sorted(obj) if i not in arms and obj[i].get("lote") not in ("CTL", "CTLF")][:60])
    out["cobertura"] = {str(k): v for k, v in cob.items()}

    import evaluador_comun as EC
    ok_c9, pl = control_placebo_m(marco, EC)
    out["placebo_m"] = pl
    pr(f"  C9 placebo de M (K x 1,2 y x 0,8, con comparador; no puede dar MEJORA): "
       + ", ".join(f"x{g} {v['con_comparador']} (sin comparador {v['sin_comparador']})" for g, v in pl.items()))
    if not ok_c9:
        fallas.append("C9")
    if fallas:
        return out, fallas
    # §9.3 (VC167-05): la equivalencia es compuerta. NO EQUIVALENTE en cualquier brazo corta aquí: el paquete no es el
    # código (§3.1) y no se lee nada más. Corta todo y no sólo ese brazo, porque la máscara y el VRP son los mismos en
    # los tres: una publicación distinta en uno viene de un VRP distinto, que toca a los tres.
    if out["equivalencia"]["veredicto"] != "EQUIVALENTE":
        out["corte"] = "NO EQUIVALENTE"
        pr("")
        pr("PAQUETE NO ES EL CODIGO (§3.1 y §9.3): la equivalencia no pasa; no se lee la regla de posición ni el §5")
        return out, fallas

    # ---- vara 1: marco, cada brazo contra K, con las lecturas de evaluar.py
    rng = np.random.default_rng(E.SEMILLA)
    N_neg = {c: sum(v["N"] for v in meta[c].values()) for c in E.CLASES_NEG}
    tasa_k_neg = N_neg["neg_pub"] / (N_neg["neg_pub"] + N_neg["neg_resto"])
    pr("\n== vara 1: alertas y negativos limpios del marco (unión S159 + S162 + S162b, pesos N_h / n_ok_h, §9.2), cada "
       "brazo contra K (cercano = el alertado más cercano al CRÁTER, no al punto X0, Y0 de evaluar.py: VC167-08)")
    out["vara1"] = {}
    for a in BRAZOS_POS:
        lk = E.lecturas(marco, ("VIA", a), rng, N_neg, tasa_k_neg)
        p2k = E.p2(marco, ("VIA", a), "K")
        # §8.13 (N-3): el P1 que veta en el §5.4 (a) deja fuera las protegidas sólo OCR de Suomi NPP anteriores al hito;
        # el P1 de evaluar.py (todas) se sigue informando al lado
        veta = [(x["vol"], x["hora"]) for x in marco
                if x["c"] == "pos_prot" and x["K"] and not x["X"][("VIA", a)] and not no_veta_n3(x)]
        aparte = [(x["vol"], x["hora"]) for x in marco
                  if x["c"] == "pos_prot" and x["K"] and not x["X"][("VIA", a)] and no_veta_n3(x)]
        out["vara1"][a] = {"lecturas": lk, "P2_K": p2k, "P1_veto_n3": veta, "P1_aparte_n3": aparte}
        pr(f"  {a:9s} P1 que veta (§5.4 a con §8.13): {len(veta)} {veta[:6]}; informadas aparte (Suomi NPP OCR antes "
           f"del hito): {len(aparte)} {aparte[:6]}")
        pr(f"  {a:9s} P1: perdidas {lk['P1']['perdidas']} de {lk['P1']['de']}, que K publica "
           f"{lk['P1']['perdidas_que_K_publica']} {lk['P1']['lista'][:6]} | recall prot {lk['recall_prot']['crudo']} "
           f"bajo {lk['recall_bajo']['crudo']} | silencio {lk['silencio']['veredicto']} | P2 contra K {p2k['veredicto']} "
           f"(neto {p2k['neto']:+.1f}, B {p2k['B']}) | MISSION (informa; cuenta también las de §8.13) "
           f"{lk['MISSION_K']['veredicto']} | mediana VRP/MIROVA (informa) {lk['M'].get('mediana')}")
    lsf = E.lecturas(marco, ("VIA", "sinfiltro"), rng, N_neg, tasa_k_neg)
    out["vara1"]["sinfiltro"] = {"lecturas": lsf, "P2_K": E.p2(marco, ("VIA", "sinfiltro"), "K")}
    pr(f"  P-sinfiltro (informa, §9.4): P1 perdidas {lsf['P1']['perdidas']} de {lsf['P1']['de']} | silencio "
       f"{lsf['silencio']['veredicto']} | P2 contra K {out['vara1']['sinfiltro']['P2_K']['veredicto']}")
    pr("  cambian de publicación contra radiante, por nombre:")
    for a in ("cercano", "pico"):
        ca = [(x["vol"], x["hora"], x["c"], "publica" if x["X"][("VIA", a)] else "calla")
              for x in marco if x["X"][("VIA", a)] != x["X"][("VIA", "radiante")]]
        out["vara1"][a]["cambios_contra_radiante"] = ca
        pr(f"    {a}: {len(ca)} {ca[:20]}")

    # ---- vara 2: pasadas lejanas
    pr("\n== vara 2: pasadas en que MIROVA publicó una fuente lejana (lo correcto es no publicar)")
    out["vara2"] = {}
    for a in BRAZOS_POS + ("K",):
        clave = a if a == "K" else ("VIA", a)
        lf = lecturas_far(far, clave, E)
        out["vara2"][a] = lf
        pr(f"  {a:9s} far_tabla: publica {lf['far_tabla']['publica']} de {lf['far_tabla']['n']} (con alertado "
           f"{lf['far_tabla']['con_alertado']}), por tramo {lf['far_tabla']['por_tramo']} | far_ocr (informa): "
           f"{lf['far_ocr']['publica']} de {lf['far_ocr']['n']}")
        pr(f"            {lf['far_tabla']['lista'][:20]}")
    far_t = [x for x in far if x["c"] == "far_tabla"]
    for a in BRAZOS_POS:
        v = p2_con(far_t, ("VIA", a), "K", E, lambda x, k: x["c"] == "far_tabla" and E.publica(x, k))
        out["vara2"][a]["P2L_K"] = v
        pr(f"  P2-L {a} contra K (sólo far_tabla): {v['veredicto']} (neto {v['neto']:+.1f}, B {v['B']})")

    # ---- vara 3
    pr("\n== vara 3 (informa, A93): |distancia del brazo desde X0, Y0 − Distancia_km de MIROVA|")
    out["vara3"] = {}
    for a in BRAZOS_POS:
        out["vara3"][a] = vara3(filas, a)
        pr(f"  {a:9s} {out['vara3'][a]}")

    # ---- regla de posición
    ver, det = regla_posicion(marco + far_t, E, far_ok=far_ok)
    # VE2-06 y N-2 (A104): la misma regla dentro de cada tramo. Si O1 u O2 por separado no da el mismo resultado que la
    # unión (otro brazo, SE QUEDA RADIANTE frente a un elegido, NO RESUELTO, NINGUNO), la elección se marca y decide
    # Nicolás. Un tramo sin pasadas no cuenta como discordancia.
    por_tramo = {}
    for tr in ("T", "O1", "O2"):
        sub = [x for x in marco + far_t if x["tramo"] == tr]
        por_tramo[tr] = regla_posicion(sub, E, far_ok=far_ok)[0] if sub else "SIN PASADAS"
    otros = [tr for tr in ("O1", "O2") if por_tramo[tr] != "SIN PASADAS"
             and resultado_rp(por_tramo[tr]) != resultado_rp(ver)]
    if otros:
        ver = (f"{ver} [A104: en {' y '.join(otros)} el resultado es otro ("
               + "; ".join(f"{tr}: {por_tramo[tr]}" for tr in otros) + "); decide Nicolas]")
    det["por_tramo"] = por_tramo
    n_alert = sum(1 for x in far_t if x["npix"].get(("VIA", "radiante"), 0))
    det["far_tabla_con_alertado"] = n_alert
    out["regla_posicion"] = {"veredicto": ver, "detalle": det}
    out["pesos"] = {f"{c}|{h}": round(w, 6) for (c, h), w in sorted(pesos.items())}
    pr("\n== regla de posición (§8.5)")
    pr("  informadas aparte por §8.13 (protegidas sólo OCR de Suomi NPP antes del 2026-10-09; no vetan):",
       det["informadas_aparte_n3"])
    pr("  pérdidas comunes a los tres brazos (no dependen de la posición; veto del paquete en §5.4 a):",
       det["perdidas_comunes"])
    pr("  veto (protegida que K publica, el brazo calla y otro brazo publica):", {a: det["veto"][a] for a in BRAZOS_POS})
    pr(f"  far_tabla con algún alertado en la caja: {n_alert}"
       + (" (menos de 5: las lejanas no tienen sustrato para pesar en la elección; informa)" if n_alert < 5 else ""))
    pr("  por tramo (A104):", por_tramo)
    for k, v in det.get("pares", {}).items():
        pr(f"  {k}: {v['veredicto']} (neto {v['neto']:+.1f}, B {v['B']}, bloques por tramo {v['bloques_por_tramo']})")
    pr("  VEREDICTO POSICION:", ver)
    ver_t, det_t = regla_posicion(marco + far_t, E, far_ok=far_ok, solo_tabla=True)
    out["regla_posicion_tabla_sola"] = {"veredicto": ver_t, "detalle": det_t}
    pr("  informa, veto sólo con protegidas de la tabla:", ver_t, {a: det_t["veto"][a] for a in BRAZOS_POS})

    # ---- §5.2 magnitud (M) y §5.3 curva, por brazo (§9.5 y §9.6), y la regla del §5.4 en código (§9.7)
    import curva_cenit as CC
    pr("\n== §5.2 magnitud M contra K (evaluador común, D-27 con d′ de D-28; decide la unión del marco, modo decide)")
    out["M"], out["curva"], out["criterios"] = {}, {"K": curva(marco, "K", E, CC)}, {}
    for a in BRAZOS_POS:
        m = magnitud(marco, ("VIA", a), EC)
        out["M"][a] = m
        d = m["detalle"]
        pr(f"  {a:9s} M {m['veredicto']} (n {m['n']}, salen por publicar uno solo {m['salen_publica_uno']}; d mediana "
           f"{d.get('d_mediana')}, IC {d.get('ic95')}; d′ {d.get('regla_dprima')} {d.get('ic95_dprima')}; ĝ "
           f"{d.get('g_hat_factor')}) | por tramo {m['por_tramo']}" + (f" | A104 en {m['a104']}" if m["a104"] else ""))
        pr(f"            informa por corte: {m['informa']}")
    pr("\n== §5.3 curva de cenit (informa en la retrospectiva: el marco no da 8 noches de nulo, §9.6)")
    pr(f"  K         {out['curva']['K']}")
    for a in BRAZOS_POS:
        out["curva"][a] = curva(marco, ("VIA", a), E, CC)
        pr(f"  {a:9s} {out['curva'][a]}")
    pr("\n== §5.4 en la retrospectiva (§9.7; (d) decide sólo en la sombra)")
    for a in BRAZOS_POS:
        out["criterios"][a] = criterios_retro(out["vara1"][a], out["vara2"][a]["P2L_K"], out["M"][a])
        pr(f"  {a:9s} {out['criterios'][a]}")
    est, cand = regla_adopcion(ver, det, out["criterios"])
    out["paquete"] = {"estado_retrospectiva": est, "candidatos": cand}
    pr(f"  PAQUETE (vía con el brazo de la RP): {est}; brazo(s) {cand}")
    return out, fallas


# ---------------------------------------------------------------- main (datos reales)
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--art-far", required=True)
    ap.add_argument("--objetivos-far", default=str(AQUI / "objetivos_run_far_v375.json"))
    ap.add_argument("--sin-granulo-far", default=str(AQUI / "sin_granulo_far_v375.json"))
    ap.add_argument("--art-s159", required=True)
    ap.add_argument("--art-s162", required=True)
    ap.add_argument("--art-s162b", required=True)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    E, s = cargar_evaluar()
    pr("== 0. procedencia")
    pr(f"  C4 evaluar.py sha256 LF {s}: {'el del pre-registro' if E else 'DISTINTO: no se carga'}")
    if E is None:
        pr("LECTURA NO LEGIBLE (C4)")
        return 3
    import banco_paridad as B
    from pipeline import mirova_v750_codigo as MV
    import brazos as BR
    sys.path.insert(0, str(RAIZ / "experiments/_s165_v375_via"))
    import equivalencia_v375e as EQ
    bv = blob_git(RAIZ / "pipeline/mirova_v750_codigo.py")
    pr(f"  pipeline/mirova_v750_codigo.py blob {bv}: {'el de #921' if bv == BLOB_VIA_921 else 'DISTINTO del de #921 (AVISO; C5 lo vigila)'}")
    obj = objetivos(a.objetivos_far if a.art_far else None)
    fallas = control_listas(obj, a.objetivos_far if a.art_far else None, a.sin_granulo_far if a.art_far else None)
    pr("  C3 listas:", fallas or "OK")
    V = E.volcanes()
    inner_html = B.inner_desde_html()
    meta = json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["meta"]["estratos"]
    arts = {"S159": a.art_s159, "S162": a.art_s162, "S162b": a.art_s162b, "FAR": a.art_far, "CTLF": a.art_far}
    mat = {e["id"]: e for e in json.loads((V375 / "o2_375/matlab_v375.json").read_text(encoding="utf-8"))["escenas"]
           if "C13" in e["brazos"]}
    res = {}
    for lote, art in arts.items():
        if art:
            for i, r in E.leer_resultados(art).items():
                if i in obj and obj[i]["lote"] == lote:
                    res[i] = r
    pasadas = {}
    with tempfile.TemporaryDirectory() as tmp:
        for k, i in enumerate(sorted(obj)):
            o, r = obj[i], res.get(i)
            if r is None or r.get("estado") != "ok":
                continue
            gz = E.grilla_npz(arts[o["lote"]], i)
            if gz is None:
                continue
            mir, tir, _ = gz
            v = V[o["volcan"]]
            g = MV.grilla_del_volcan(o["volcan"], paso_m=375.0, clave_roi="roi_v375")
            m14 = None
            if o["lote"] in ("CTL", "CTLF"):
                pm = (r.get("port") or {}).get("M14") or {}
                m14 = (pm.get("npix"), pm.get("vrp_mw"))
            rec, mascara, pos = record_de_la_via(o, g, mir, tir, r, v, MV)
            go = o["grilla"]
            xc, yc = BR.crater_xy(go, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
            box_p = BR.caja(go, "C13", go["X0"], go["Y0"], xc, yc, v["inner_radius_km"], o["volcan"])
            port = BR.correr_box(mir, tir, go, box_p, go["X0"], go["Y0"], r["dayflag"], r["sunglint"],
                                 BR.MP.SENSORES["VIIRS375"], semillas=0, modo="C13")
            mask_v = {(int(x), int(y)) for x, y in zip(*np.nonzero(mascara))}
            dist = distancias(mascara, mir, pos, pos_ref(g), float(g["paso"]) / 1000.0, MV._cumulo_del_mas_radiante)
            rec_a = por_el_almacen(rec, o["volcan"], v, tmp, dt=o["hora_utc"])
            dc_ok = {}
            if rec_a is not None and dist:
                for b in BRAZOS_POS:
                    vb = variante(rec_a, dist[b], v["inner_radius_km"])
                    va = por_el_almacen(vb, o["volcan"], v, tmp, dt=o["hora_utc"])
                    dc_ok[b] = va is not None and va.get("distance_class") == vb.get("distance_class")
            krec = (r.get("K") or {}).get("record")
            # la vara del VRP (§7.3 y §8.6 b): de 1 a 4 píxeles la salida de MATLAB si la hay para esa escena; si no (más
            # de 4 píxeles, o una pasada FAR, que MATLAB no corrió), brazos.py con la regla de relleno de MATLAB por
            # código independiente (delaunay_perturbado.py de S163, vía equivalencia_v375e.vrp_port_con_regla_matlab)
            vara = elegir_vara(port["npix"], port["vrp_mw"], mat.get(i),
                               lambda: EQ.vrp_port_con_regla_matlab(mir, port["pixeles"]))
            vara_vieja = elegir_vara(port["npix"], port["vrp_mw"], mat.get(i), lambda: port["vrp_mw"])   # N-1, informa
            vrp_via = float(MV.vrp_mirova(mir, mascara, coef=MV.COEF_VRP_V375)["VRP_MW"]) if mask_v else None
            pasadas[i] = {"rec": rec_a, "dist": dist, "npix": len(mask_v), "inner": inner_html.get(o["volcan"], v["inner_radius_km"]),
                          "inner_v": v["inner_radius_km"], "vrp_port": vara, "vrp_port_vieja": vara_vieja, "vrp_via": vrp_via,
                          "geom": r.get("geometria_centro"),
                          "mascara_igual": mask_v == {(q[0], q[1]) for q in port["pixeles"]},
                          "k_rec": None if krec is None else E.slim(krec), "dc_almacen_igual": dc_ok, "m14": m14}
            if (k + 1) % 200 == 0:
                print(f"   ... {k + 1} de {len(obj)}", flush=True)

    def publicar(casos):
        return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inner] for r, inner in casos])]
    pr("\n== controles")
    out, f2 = analizar(pasadas, obj, meta, publicar, E, bool(a.art_far))
    fallas += f2
    if a.json:
        Path(a.json).write_text(json.dumps(out, default=str, ensure_ascii=False, indent=1), encoding="utf-8")
    if fallas:
        pr("LECTURA NO LEGIBLE:", fallas)
    if a.salida:
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    return codigo_salida(fallas, out)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
