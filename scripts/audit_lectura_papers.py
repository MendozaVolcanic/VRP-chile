# -*- coding: utf-8 -*-
"""¿Qué papers del repo están LEÍDOS A FONDO, y cuáles sólo mencionados?

Nicolás preguntó, con razón, si de verdad leímos todo lo que sirve. La respuesta
honesta exige medirla, no estimarla — y exige distinguir tres estados que se venían
confundiendo:

  LEIDO_A_FONDO  tiene un informe en docs/s128/ o docs/s129/ que contesta las seis
                 preguntas (qué mide · qué criterio · nuestros frentes · en qué nos
                 contradice · qué cita que no tenemos · qué NO dice)
  TRABAJADO_ANTES  una sesión previa lo trabajó en serio: tiene un doc dedicado, o
                 aparece en 3+ documentos del repo. Ejemplo: Aveni 2025 GRL, que está
                 IMPLEMENTADO verbatim en pipeline/vrptir.py desde S74
  SINTETIZADO    sólo en BIBLIOGRAPHY_SYNTHESIS.md, que es de S13 (abril) y es
                 resumen, no lectura crítica. Cubre el "qué dice", casi nunca el
                 "en qué nos contradice"
  SIN_TOCAR      en ninguna parte

⚠️ La primera versión de este script SÓLO miraba docs/s128 y la síntesis, e ignoraba
el resto de docs/ — donde las sesiones S17 a S127 registraron su lectura. Daba 52 %
"sin tocar", que es falso y en la dirección alarmista. Es A89 por tercera vez en el
día, y las tres del lado de quien auditaba.

La distinción importa: el GAP #A, el mecanismo del remuestreo y la matización de A69
salieron los tres de papers que YA estaban SINTETIZADOS. La síntesis no los vio porque
se hizo antes de que existieran esos frentes.

Read-only. Escribe su JSON y nada más.
"""
import hashlib
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "documentacion")
S128 = os.path.join(ROOT, "docs", "s128")

# Ruido: no son papers.
NO_PAPER = re.compile(
    r"BIBLIOGRAPHY_SYNTHESIS|MIROVA_DETAILED_CITATIONS|perplexity_deep_research"
    r"|literature_review_|_extracted\.txt$|^_mm_ch|^_thesis_full|^section\.txt$"
    r"|^ch5\.txt$|^nuevos$|_figs$", re.I)


def familia(nombre):
    """Agrupa el .pdf con su .md/.txt extraído: son UN paper, no dos."""
    b = re.sub(r"\.(pdf|md|txt|docx|xlsx|html\.roto|md\.roto)$", "", nombre, flags=re.I)
    return b.lower()


# ── 1. El corpus real, DEDUPLICADO por contenido ─────────────────────────
# Sin esto, los 6 grupos byte-identicos del repo (Aveni/1-s2.0-, HotLINK/feart-12,
# MOUNTS/rs11131528, Campus/The_Transition...) inflan el denominador y hacen
# parecer que falta mas de lo que falta.
por_md5, familias = {}, {}
for f in sorted(os.listdir(DOC)):
    p = os.path.join(DOC, f)
    if not os.path.isfile(p) or NO_PAPER.search(f):
        continue
    h = None
    if os.path.getsize(p) > 200_000:
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h in por_md5:
            familias[por_md5[h]].append(
                {"archivo": f, "mb": 0.0, "roto": False, "dup_de": por_md5[h]})
            continue
    fam = familia(f)
    if h:
        por_md5[h] = fam
    familias.setdefault(fam, []).append(
        {"archivo": f, "mb": round(os.path.getsize(p) / 1e6, 2),
         "roto": f.endswith((".roto",)) or f.startswith("NO_ES_"), "dup_de": None})

# ── 2. Quién quedó LEÍDO A FONDO en S128 ────────────────────────────────
informes = {}
for f in sorted(os.listdir(S128)):
    if not f.startswith("PAPERS_") or not f.endswith(".md"):
        continue
    informes[f] = open(os.path.join(S128, f), encoding="utf-8",
                       errors="replace").read().lower()

# ── 3. Quién está sólo SINTETIZADO ─────────────────────────────────────
sint = open(os.path.join(DOC, "BIBLIOGRAPHY_SYNTHESIS.md"),
            encoding="utf-8", errors="replace").read().lower()

# ── 3b. Lo que TRABAJARON las sesiones previas (S17..S127) ─────────────
# Sin esto el conteo miente: Aveni 2025 GRL sale "sin tocar" cuando esta
# implementado verbatim en pipeline/vrptir.py desde S74, y el paper de los lagos
# de Peteroa sale "sin tocar" cuando tiene su propio doc (F31_AGUILERA_2021).
DOCS = os.path.join(ROOT, "docs")
otros = {}
for dp, _dn, fn in os.walk(DOCS):
    if os.sep + "s128" in dp or os.sep + "s129" in dp:
        continue
    for f in fn:
        if not f.endswith((".md", ".txt")):
            continue
        try:
            otros[os.path.join(dp, f)] = open(os.path.join(dp, f), encoding="utf-8",
                                              errors="replace").read().lower()
        except OSError:
            pass
# El codigo tambien cuenta: un paper implementado esta leido.
for sub in ("pipeline", "scripts"):
    d = os.path.join(ROOT, sub)
    for dp, _dn, fn in os.walk(d):
        for f in fn:
            if f.endswith(".py"):
                try:
                    otros[os.path.join(dp, f)] = open(
                        os.path.join(dp, f), encoding="utf-8",
                        errors="replace").read().lower()
                except OSError:
                    pass


# Palabras que aparecen en cualquier informe y no identifican a nadie.
GENERICO = {"main", "pdf", "md", "txt", "the", "and", "for", "with", "data", "v1",
            "v2", "v3", "v4", "of", "a", "to", "in", "on", "de", "la", "el", "2014",
            "2011", "2013", "2018", "2019", "2020", "2021", "2022", "2023", "2024",
            "2025", "2026", "sensor", "remote", "sensing", "volcanic", "thermal"}


def claves_de(fam, archivos):
    """Identificadores que SI distinguen a este paper de los otros 96.

    Un apellido solo no basta (A89, el caso Laiolo) y el nombre de archivo tampoco:
    un informe puede citar el paper por DOI, por patron de editorial o por apellido.
    Se juntan las tres vias y se descarta lo generico.
    """
    claves = set()
    for a in archivos:
        n = a["archivo"].lower()
        claves.add(n)
        claves.add(familia(n))
        for m in re.finditer(r"(10\.\d{4,5}[-/][^\s\"'),]+|s\d{5}-\d{3}-\d{5}-\w"
                             r"|1-s2\.0-[\w.]+|remotesensing-[\d-]+|feart-[\d.-]+"
                             r"|rs\d{7,}|nhess-[\d-]+|s\d{5}-\d{3}-\d{4,5}-\w)", n):
            claves.add(m.group(1))
        # apellido + anio, que es como los informes citan en prosa
        for m in re.finditer(r"([a-z]{5,})[_ ]?(19|20)(\d{2})", n):
            if m.group(1) not in GENERICO:
                claves.add("%s %s%s" % (m.group(1), m.group(2), m.group(3)))
                claves.add("%s_%s%s" % (m.group(1), m.group(2), m.group(3)))
    return {k for k in claves if k and len(k) > 6 and k not in GENERICO}


def citado_en(texto, fam, archivos):
    return any(k in texto for k in claves_de(fam, archivos))


filas = []
for fam, archivos in sorted(familias.items()):
    quien = [n for n, t in informes.items() if citado_en(t, fam, archivos)]
    donde = [os.path.relpath(n, ROOT) for n, t in otros.items()
             if citado_en(t, fam, archivos)]
    if quien:
        estado = "LEIDO_A_FONDO"
    elif len(donde) >= 3 or any("/f" in d.lower() or "\f" in d.lower() for d in donde):
        estado = "TRABAJADO_ANTES"
    elif citado_en(sint, fam, archivos):
        estado = "SINTETIZADO"
    elif donde:
        estado = "MENCIONADO"
    else:
        estado = "SIN_TOCAR"
    filas.append({"paper": fam, "estado": estado, "informe": quien,
                  "otros_docs": donde[:6], "n_otros_docs": len(donde),
                  "archivos": [a["archivo"] for a in archivos],
                  "mb": round(sum(a["mb"] for a in archivos), 2),
                  "roto": any(a["roto"] for a in archivos)})

por_estado = {}
for f in filas:
    por_estado.setdefault(f["estado"], []).append(f)

R = {"_meta": {"corpus_papers_distintos": len(filas),
               "nota": "un .pdf y su .md/.txt extraido cuentan como UN paper"},
     "conteo": {k: len(v) for k, v in sorted(por_estado.items())},
     "por_estado": por_estado}
out = os.path.join(ROOT, "docs", "s128", "lectura_papers.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

tot = len(filas)
print("CORPUS: %d papers distintos (agrupando .pdf con su texto extraído)\n" % tot)
for est in ("LEIDO_A_FONDO", "TRABAJADO_ANTES", "SINTETIZADO",
            "MENCIONADO", "SIN_TOCAR"):
    v = por_estado.get(est, [])
    print("== %s: %d (%.0f %%) ==" % (est, len(v), 100.0 * len(v) / tot))
    for f in sorted(v, key=lambda x: -x["mb"]):
        marca = " [ROTO]" if f["roto"] else ""
        print("   %-62s %6.1f MB%s" % (f["paper"][:62], f["mb"], marca))
    print()
print("escrito:", out)
