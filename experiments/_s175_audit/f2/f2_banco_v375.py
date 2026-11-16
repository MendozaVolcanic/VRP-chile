#!/usr/bin/env python
"""F2 S175: VIIRS 375 de produccion contra MIROVA en las dos direcciones, por volcan, por cenit y por tramo.

POR QUE. El operador del OVDAS mira lo que el tablero publica. Dos fallas posibles: una alerta de MIROVA de 1 MW o mas
(protegida, lectura A) que no publicamos, y una publicacion nuestra donde MIROVA miro y no vio nada (negativo limpio).
El agregado puede esconder un estrato (Simpson): por eso todo va por volcan y por cenit.

VARA (preambulo S175). Todo se importa del ARBOL que se pasa como argumento (git archive del commit, sin conversion de
fin de linea): "publica" = banco_paridad.correr_node sobre frontend/index.html de ese arbol; alerta/negativo limpio =
banco_paridad.etiquetar con indexar_referencia(regla_minimas="SN") (D-9, clase_mirova); protegida = fila de alerta
(TIPOS_ALERTA) pareada a +-TOL_S con VRP >= 1 MW tras la regla SN (clase_mirova.alerta_protegida, lectura A);
referencia = data/mirova_reference/mirova_v1_snapshot del arbol. Cenit = campo `sensor_zenith_deg` del record.

LAS DOS PREGUNTAS.
P1 (si lo medido estuviera roto, lo veria): controles todo_publica/nada_publica sobre el mismo denominador (1 y 0);
   control positivo de estrato: el bin de cenit lo produce zbin() sobre el campo del record, y la linea base roja (2)
   (Chillan) prueba que ese campo separa magnitudes.
P2 (instrumento muerto): se imprimen los n de cada denominador; un denominador 0 se escribe SIN DATO, nunca tasa 0.
   El sha256 de index.html y de los CSV de referencia va en la salida.

Uso: python f2_banco_v375.py <arbol> <inicio> <fin> <salida_prefijo>
"""
import collections, csv, hashlib, json, os, sys
from datetime import timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, PREF = sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
for mod in (bp, cm):
    assert Path(mod.__file__).resolve().is_relative_to(ARBOL), mod.__file__
assert Path(SNAP_CONS).resolve().is_relative_to(ARBOL)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tasa(a, n):
    return None if not n else round(a / n, 4)


def zb(z):
    if z is None:
        return "z?"
    return "z<30" if z < 30 else ("z30-50" if z < 50 else ("z50-60" if z < 60 else "z>=60"))


ZB = ["z<30", "z30-50", "z50-60", "z>=60"]
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
salida = {"meta": {"arbol": str(ARBOL), "ventana": [INI, FIN], "sha256_index_html": sha(bp.HTML),
                   "sha256_cons": sha(SNAP_CONS), "sha256_ocr": sha(SNAP_OCR), "tol_s": bp.TOL_S,
                   "inner": inner, "cenit": "record.sensor_zenith_deg", "n_filas_ref": len(filas)}}

# predicado del tablero una sola vez; se guardan tambien los flags (summit, valid, art) para explicar las perdidas
recs = bp.cargar_nuestros(coords, inner, (INI, FIN))
salida["meta"]["n_records_nocturnos"] = len(recs)
crudo = {}
for vol in bp.VOLS:
    for r in json.load(open(ARBOL / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        crudo[(vol, r.get("sensor"), r.get("datetime_utc"))] = r

res_por_regla = {}
for regla in ("SN", "original"):
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas=regla)
    rr = [dict(r) for r in recs]
    bp.etiquetar(rr, por_vb, ns, nv)
    for r in rr:
        par = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        al = [f for f in par if f["tipo"] in cm.TIPOS_ALERTA]
        r["mir_vrp"] = max([f["vrp_mw"] for f in al if f["vrp_mw"] is not None], default=None)
        r["prot"] = any(cm.alerta_protegida(f) for f in par)
        r["prot_cons_contradice"] = r["prot"] and any(f["source"] == "CONS" and not f["tipo"].startswith("ALERTA")
                                                      for f in par)
        r["mir_fuentes"] = sorted({f["source"] for f in al})
        r["mir_foto"] = next((f.get("ruta_foto") or f.get("Ruta Foto") for f in al if f.get("ruta_foto") or f.get("Ruta Foto")), None)
        r["mir_dist"] = next((f["dist_km"] for f in al if f.get("dist_km") is not None), None)
        r["tramo"] = "nrt" if r["perfil"] == "mirova_equivalent" else ("reproc" if r["perfil"] else "sin_marca")
        r["zb"] = zb(r["z"])
    sin_rec = bp.alertas_sin_record(por_vb, rr)
    # protegidas sin record nuestro (cobertura), por volcan
    nuestros = collections.defaultdict(list)
    for r in rr:
        nuestros[(r["vol"], r["b"])].append(r["dt"])
    prot_sin_rec = []
    vistos = set()
    for (vol, b), lista in por_vb.items():
        if b != "VIIRS375":
            continue
        ts = sorted(nuestros.get((vol, b), []))
        for dt, f in lista:
            if not cm.alerta_protegida(f):
                continue
            k = (vol, f["fecha_utc"][:16])
            if k in vistos:
                continue
            vistos.add(k)
            if not any(abs((t - dt).total_seconds()) <= bp.TOL_S for t in ts):
                prot_sin_rec.append({"vol": vol, "fecha_utc": f["fecha_utc"], "vrp": f["vrp_mw"], "src": f["source"],
                                     "dist": f.get("dist_km")})
    res_por_regla[regla] = (rr, sin_rec, prot_sin_rec, n_ref)

rr, sin_rec, prot_sin_rec, n_ref = res_por_regla["SN"]
v = [r for r in rr if r["b"] == "VIIRS375"]
salida["meta"]["n_records_v375"] = len(v)
salida["meta"]["n_filas_ref_nocturnas_SN"] = n_ref
salida["meta"]["etiquetas_v375_SN"] = dict(collections.Counter(r["lab"] for r in v))
salida["meta"]["etiquetas_v375_original"] = dict(collections.Counter(r["lab"] for r in res_por_regla["original"][0]
                                                                      if r["b"] == "VIIRS375"))


def bloque(sel):
    c = collections.Counter()
    for r in sel:
        c["n"] += 1
        c[r["lab"]] += 1; c[r["lab"] + "_pub"] += r["pub"]
        if r["lab"] == "pos" and r["prot"]:
            c["prot"] += 1; c["prot_pub"] += r["pub"]
        if r["neg_estricto"]:
            c["nest"] += 1; c["nest_pub"] += r["pub"]
    return {"n_pos": c["pos"], "recall_pos": tasa(c["pos_pub"], c["pos"]),
            "n_prot": c["prot"], "prot_pub": c["prot_pub"], "recall_prot": tasa(c["prot_pub"], c["prot"]),
            "n_neg": c["neg_limpio"], "neg_pub": c["neg_limpio_pub"], "tasa_pub_neg": tasa(c["neg_limpio_pub"], c["neg_limpio"]),
            "n_neg_estricto": c["nest"], "tasa_pub_neg_estricto": tasa(c["nest_pub"], c["nest"]),
            "n_far_ref": c["far_ref"], "n_sin_info": c["sin_info"]}


def noches(sel):
    e = collections.defaultdict(lambda: {"labs": set(), "pub": 0, "prot": False})
    for r in sel:
        x = e[(r["vol"], r["noche"])]
        x["labs"].add(r["lab"]); x["pub"] = max(x["pub"], r["pub"]); x["prot"] |= (r["lab"] == "pos" and r["prot"])
    c = collections.Counter()
    for x in e.values():
        if "pos" in x["labs"]:
            c["pos"] += 1; c["pos_pub"] += x["pub"]
            if x["prot"]:
                c["prot"] += 1; c["prot_pub"] += x["pub"]
        elif "neg_limpio" in x["labs"] and "far_ref" not in x["labs"]:
            c["neg"] += 1; c["neg_pub"] += x["pub"]
    return {"n_pos": c["pos"], "recall_pos": tasa(c["pos_pub"], c["pos"]), "n_prot": c["prot"],
            "recall_prot": tasa(c["prot_pub"], c["prot"]), "n_neg": c["neg"], "tasa_pub_neg": tasa(c["neg_pub"], c["neg"])}


salida["agregado"] = {"pasada": bloque(v), "noche": noches(v)}
salida["por_volcan"] = {vol: {"pasada": bloque([r for r in v if r["vol"] == vol]),
                              "noche": noches([r for r in v if r["vol"] == vol])} for vol in bp.VOLS}
salida["por_cenit"] = {z: bloque([r for r in v if r["zb"] == z]) for z in ZB + ["z?"]}
salida["por_volcan_cenit"] = {vol: {z: bloque([r for r in v if r["vol"] == vol and r["zb"] == z]) for z in ZB}
                              for vol in bp.VOLS}
salida["por_tramo"] = {t: {"pasada": bloque([r for r in v if r["tramo"] == t]), "noche": noches([r for r in v if r["tramo"] == t])}
                       for t in ("reproc", "nrt", "sin_marca")}
salida["por_mes"] = {m: bloque([r for r in v if r["noche"][:7] == m]) for m in sorted({r["noche"][:7] for r in v})}
salida["por_plataforma"] = {s: bloque([r for r in v if r["sensor"] == s]) for s in sorted({r["sensor"] for r in v})}
salida["por_regla_minimas"] = {reg: bloque([r for r in res_por_regla[reg][0] if r["b"] == "VIIRS375"]) for reg in res_por_regla}
salida["controles"] = {"todo_publica": bloque([dict(r, pub=1) for r in v]), "nada_publica": bloque([dict(r, pub=0) for r in v])}

# perdidas protegidas: por que no publico (flags del predicado), con la lamina de MIROVA
perd = [r for r in v if r["lab"] == "pos" and r["prot"] and not r["pub"]]
casos = []
for r in perd:
    c = crudo[(r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))]
    slim = {k: c.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (c.get("anomaly_pixels") or [])] \
        if c.get("f5_core_vrp_mw") is None else None
    casos.append([slim, inner[r["vol"]]])
flags = bp.correr_node(casos) if casos else []
salida["protegidas_no_publicadas"] = [
    {"vol": r["vol"], "pasada_utc": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "cenit": r["z"],
     "tramo": r["tramo"], "mirova_vrp_mw": r["mir_vrp"], "mirova_dist_km": r["mir_dist"], "mirova_fuentes": r["mir_fuentes"],
     "cons_contradice": r["prot_cons_contradice"], "lamina": r["mir_foto"], "dc": r["dc"], "pc_vrp": r["pc_vrp"],
     "pc_dist": r["pc_dist"], "disp": r["disp"], "summit_valid_art_disp_pub": f}
    for r, f in zip(perd, flags)]
salida["protegidas_sin_record"] = prot_sin_rec
salida["protegidas_sin_record_original"] = res_por_regla["original"][2]
# negativos limpios publicados, de mayor a menor display
negp = sorted([r for r in v if r["lab"] == "neg_limpio" and r["pub"]], key=lambda r: -(r["disp"] or 0))
salida["neg_limpios_publicados_top"] = [
    {"vol": r["vol"], "pasada_utc": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "cenit": r["z"],
     "disp_mw": r["disp"], "pc_dist": r["pc_dist"], "dc": r["dc"], "estricto": r["neg_estricto"], "tramo": r["tramo"]}
    for r in negp[:40]]
salida["neg_limpios_publicados_hist_mw"] = dict(collections.Counter(
    ("<0.1" if (r["disp"] or 0) < 0.1 else "<1" if r["disp"] < 1 else "<5" if r["disp"] < 5 else ">=5") for r in negp))
# D-9: pasadas que la regla SN saca del recall y que publicamos o no
d9 = collections.Counter()
orig = {(r["vol"], r["sensor"], r["dt"]): r for r in res_por_regla["original"][0] if r["b"] == "VIIRS375"}
for r in v:
    o = orig[(r["vol"], r["sensor"], r["dt"])]
    if o["lab"] != r["lab"]:
        d9[f'{o["lab"]}->{r["lab"]}|pub={r["pub"]}'] += 1
salida["d9_cambios_original_a_SN"] = dict(d9)

Path(PREF + ".json").write_text(json.dumps(salida, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
L = [f"F2 banco V375 | arbol {ARBOL.name} | ventana {INI}..{FIN} | records nocturnos {len(recs)} | V375 {len(v)}",
     f"sha256 index.html {salida['meta']['sha256_index_html'][:16]} cons {salida['meta']['sha256_cons'][:16]} ocr {salida['meta']['sha256_ocr'][:16]}",
     f"etiquetas V375 SN {salida['meta']['etiquetas_v375_SN']}", f"etiquetas V375 original {salida['meta']['etiquetas_v375_original']}",
     "AGREGADO pasada " + json.dumps(salida["agregado"]["pasada"]), "AGREGADO noche " + json.dumps(salida["agregado"]["noche"]),
     "CONTROL todo_publica " + json.dumps(salida["controles"]["todo_publica"]),
     "CONTROL nada_publica " + json.dumps(salida["controles"]["nada_publica"]), "", "POR VOLCAN (pasada | noche)"]
for vol in bp.VOLS:
    p, n = salida["por_volcan"][vol]["pasada"], salida["por_volcan"][vol]["noche"]
    L.append(f"  {vol:20s} pos {p['n_pos']:4d} rec {p['recall_pos']} | prot {p['prot_pub']}/{p['n_prot']} | neg {p['neg_pub']}/{p['n_neg']} = {p['tasa_pub_neg']} | est {p['tasa_pub_neg_estricto']} (n {p['n_neg_estricto']}) || noche pos {n['n_pos']} rec {n['recall_pos']} prot {n['recall_prot']} (n {n['n_prot']}) neg {n['tasa_pub_neg']} (n {n['n_neg']})")
L.append("POR CENIT")
for z in ZB + ["z?"]:
    p = salida["por_cenit"][z]
    L.append(f"  {z:7s} pos {p['n_pos']} rec {p['recall_pos']} prot {p['prot_pub']}/{p['n_prot']} neg {p['neg_pub']}/{p['n_neg']} = {p['tasa_pub_neg']}")
L.append("VOLCAN x CENIT: tasa_pub_neg (n) | recall_prot (n)")
for vol in bp.VOLS:
    L.append(f"  {vol:20s} " + "  ".join(f"{z}:{salida['por_volcan_cenit'][vol][z]['tasa_pub_neg']}({salida['por_volcan_cenit'][vol][z]['n_neg']})|{salida['por_volcan_cenit'][vol][z]['recall_prot']}({salida['por_volcan_cenit'][vol][z]['n_prot']})" for z in ZB))
L.append("POR TRAMO")
for t, d in salida["por_tramo"].items():
    L.append(f"  {t:9s} {json.dumps(d['pasada'])}")
L.append("POR MES")
for m, d in salida["por_mes"].items():
    L.append(f"  {m} pos {d['n_pos']} rec {d['recall_pos']} prot {d['prot_pub']}/{d['n_prot']} neg {d['neg_pub']}/{d['n_neg']} = {d['tasa_pub_neg']}")
L.append("POR PLATAFORMA")
for s, d in salida["por_plataforma"].items():
    L.append(f"  {s:13s} pos {d['n_pos']} rec {d['recall_pos']} prot {d['prot_pub']}/{d['n_prot']} neg {d['neg_pub']}/{d['n_neg']} = {d['tasa_pub_neg']}")
L.append("REGLA MINIMAS: " + json.dumps(salida["por_regla_minimas"]))
L.append("D9 cambios original->SN: " + json.dumps(salida["d9_cambios_original_a_SN"]))
L.append(f"PROTEGIDAS NO PUBLICADAS ({len(salida['protegidas_no_publicadas'])}):")
for x in salida["protegidas_no_publicadas"]:
    L.append("  " + json.dumps(x, ensure_ascii=False, default=str))
L.append(f"PROTEGIDAS SIN RECORD NUESTRO SN ({len(prot_sin_rec)}): " + json.dumps(prot_sin_rec, ensure_ascii=False))
L.append("NEG LIMPIOS PUBLICADOS por MW: " + json.dumps(salida["neg_limpios_publicados_hist_mw"]))
for x in salida["neg_limpios_publicados_top"][:15]:
    L.append("  " + json.dumps(x, ensure_ascii=False, default=str))
txt = "\n".join(L)
Path(PREF + "_salida.txt").write_text(txt + "\n", encoding="utf-8")
print(txt)
