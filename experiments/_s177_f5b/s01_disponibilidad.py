# -*- coding: utf-8 -*-
"""s01: comprobar que las láminas, los TIF de referencia y los insumos de F5b siguen en disco, con el mismo md5.
Por qué: la medición entera cuelga de 303 láminas PNG de MIROVA (los GeoTIFF dejaron de actualizarse el 2026-09-22); si faltaran
o hubieran cambiado, no se reemplazan. Pregunta 2 (instrumento): si el md5 no coincidiera, el conteo de 'cambiadas' sería > 0.
Sólo lee."""
import json, os, sys, hashlib, collections
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
H = r"C:\Users\nmend\vrp-temporales\s177_f5b\orig"
recs = [x for x in json.load(open(H + r"\p8_clases.json", encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
cache = json.load(open(H + r"\p8_ocr_cache.json", encoding="utf-8"))
refs = json.load(open(H + r"\p6_tif_referencia_out.json", encoding="utf-8"))
print("aciertos en el universo F5b:", len(recs), "| con lámina:", sum(1 for x in recs if x.get("png")), "| sin lámina:", sum(1 for x in recs if not x.get("png")))
faltan, cambiadas, ok = [], [], 0
vistas = set()
for x in recs:
    if not x.get("png"): continue
    p = x["png"]
    if p in vistas: continue
    vistas.add(p)
    fn = os.path.join(TMP, "png", p.split("/")[-2] + "_" + os.path.basename(p))
    if not os.path.exists(fn): faltan.append(fn); continue
    md5 = hashlib.md5(open(fn, "rb").read()).hexdigest()
    if md5 != cache[p]["md5"]: cambiadas.append(fn)
    else: ok += 1
print("láminas distintas usadas:", len(vistas), "| md5 igual al de F5b:", ok, "| faltan:", len(faltan), "| md5 distinto:", len(cambiadas))
tf = []
for k, v in refs.items():
    fn = os.path.join(TMP, "tif_ref", k.split("|")[0] + "_" + os.path.basename(v["ref_sep"]["path"]))
    tf.append((k, os.path.exists(fn)))
print("TIF de referencia (grilla prestada):", sum(1 for _, e in tf if e), "de", len(tf), "presentes")
print("volcán/sensor sin lámina:", collections.Counter((x["vol"], x["b"]) for x in recs if not x.get("png")))
