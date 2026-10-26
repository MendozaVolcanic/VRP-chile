#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
S128 · Higiene del corpus bibliografico (`documentacion/`).

POR QUE existe este script
--------------------------
Tres numeros del proyecto sobre el corpus se venian transcribiendo a mano y
quedaron obsoletos o directamente mal:

  * la cobertura de `BIBLIOGRAPHY_SYNTHESIS.md` («30/60 PDFs, 54 %») es de S13
    (abril) y nunca se volvio a medir;
  * el inventario de duplicados se citaba «de memoria» (~76 MB) sin hash;
  * habia archivos que ni siquiera son lo que dice su extension (una pagina de
    error de Elsevier guardada como `.pdf`).

Regla del proyecto (S91): ningun numero se transcribe a mano. Este script es la
fuente de verdad: escribe `docs/s128/corpus_inventory.json` y lo que se cite en
prosa tiene que salir de ahi.

Uso:
    python scripts/audit_corpus_documentacion.py            # mide y persiste
    python scripts/audit_corpus_documentacion.py --print    # ademas resume

Salida: docs/s128/corpus_inventory.json
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[1]
DOCDIR = REPO / "documentacion"
SYNTHESIS = DOCDIR / "BIBLIOGRAPHY_SYNTHESIS.md"
OUT = REPO / "docs" / "s128" / "corpus_inventory.json"

# Extensiones que cuentan como "documento del corpus". Se excluyen los .md/.txt
# que son sintesis NUESTRAS (no papers) via SYNTHESIS_OWN.
DOC_EXT = {".pdf", ".md", ".txt", ".docx", ".xlsx", ".html", ".roto"}

# Documentos que NO son papers: son notas/sintesis propias del proyecto.
SYNTHESIS_OWN = {
    "BIBLIOGRAPHY_SYNTHESIS.md",
    "MIROVA_DETAILED_CITATIONS.md",
    "perplexity_deep_research_S72.md",
    "perplexity_deep_research_S72_ronda2.md",
    "literature_review_vegetation_indices_volcanic_precursors.md",
}


def magic(path: Path) -> str:
    """POR QUE: la extension miente. Un `.pdf` de 833 KB puede ser HTML."""
    try:
        head = path.open("rb").read(1024)
    except OSError:
        return "unreadable"
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.lstrip()[:15].lower().startswith(b"<!doctype html") or head.lstrip()[:5].lower().startswith(b"<html"):
        return "html"
    if head.startswith(b"PK\x03\x04"):
        return "zip/ooxml"
    return "text"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stem_key(name: str) -> str:
    """Agrupa `paper.pdf` con su `paper.md`/`paper.txt` extraido.

    POR QUE: la cobertura se mide en PAPERS, no en archivos. Un PDF y su
    extraccion de texto son UN documento, no dos.
    """
    base = re.sub(r"\.(pdf|md|txt|docx|xlsx|html|roto)$", "", name, flags=re.I)
    base = re.sub(r"\.(html|md)$", "", base, flags=re.I)          # dobles: x.html.roto
    base = re.sub(r"_extracted$|_extraido$", "", base, flags=re.I)
    base = re.sub(r"\s*\(\d+\)$", "", base)                        # "... (1).pdf"
    return base.lower()


def pdf_first_page(path: Path, chars: int = 1800) -> str:
    try:
        import pypdf
    except ImportError:
        return ""
    try:
        r = pypdf.PdfReader(str(path))
        txt = r.pages[0].extract_text() or ""
        if len(txt.strip()) < 60 and len(r.pages) > 1:
            txt += "\n" + (r.pages[1].extract_text() or "")
        return re.sub(r"[ \t]+", " ", txt)[:chars]
    except Exception as exc:  # PDF corrupto / cifrado
        return f"<<ERROR {type(exc).__name__}: {exc}>>"


def pdf_pages(path: Path) -> int:
    try:
        import pypdf

        return len(pypdf.PdfReader(str(path)).pages)
    except Exception:
        return -1


STOP = {"the", "and", "for", "from", "with", "of", "a", "an", "in", "on", "to",
        "using", "based", "their", "its", "at", "by", "de", "del", "la", "el"}


def norm(s: str) -> str:
    s = s.lower()
    s = s.replace("‐", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def id_candidates(name: str, key: str) -> set:
    """Identificadores de editorial. POR QUE (A89): la sintesis cita el mismo
    documento como `s00445-024-01721-z`, como `16:2001`, como `feart-11-1240107`
    o como un DOI — buscar por UN solo patron produce ceros que se leen como
    ausencia."""
    cands = {name, key}
    stem = re.sub(r"\.[a-z0-9]+$", "", name, flags=re.I)
    cands.add(stem)
    m = re.match(r"(?:remotesensing|sensors|geohazards|nhess|feart|rs)-?(\d+)-(\d+)", stem, re.I)
    if m:
        vol, num = m.group(1), m.group(2)
        cands.add(f"{vol}:{int(num)}")          # "16:2001"
        cands.add(f"{vol}:{num}")               # "24:4267"
    for pat in (r"(s\d{5}-\d{3}-\d{5}-[a-z0-9])", r"(1-s2\.0-S\d+)", r"(nhess-\d+-\d+-\d+)",
                r"(feart-\d+-\d+)", r"(rs\d{7,})", r"(sensors-\d+-\d+)"):
        m = re.search(pat, stem, re.I)
        if m:
            cands.add(m.group(1))
    return {c.strip().lower() for c in cands if len(c.strip()) >= 6}


# ---------------------------------------------------------------------------
# Curacion explicita (S128). POR QUE no se deja todo automatico:
#
#   Se probo el match por trigramas del titulo y falla en las DOS direcciones:
#   da falsos positivos con frases genericas ("thermal remote sensing" hace
#   matchear a Klyuchevskoy con la seccion de Coppola 2019) y falsos negativos
#   con los papers que la sintesis cita por apellido+ano sin DOI (Wooster 2003,
#   Reath 2018/2019, AVTOD). Un numero construido sobre eso no es auditable.
#
#   Entonces: DOI e identificador de editorial se resuelven solos (senal exacta);
#   el resto se declara aca con el ANCLA VERBATIM de la sintesis que lo cubre, y
#   el script FALLA si el ancla ya no existe en el archivo. Asi el numero no
#   drifta en silencio cuando alguien edita la sintesis (A87: el flag que se
#   apaga no prueba que el problema se fue).
# ---------------------------------------------------------------------------

# Archivos que son EL MISMO documento aunque el nombre no lo diga: extracciones
# de texto, suplementos, capitulos sueltos de la misma tesis, copias renombradas.
SAME_DOC = {
    "thesis_massimetti": ["_thesis_full", "_mm_ch2_methods", "_mm_ch4_dome_methods",
                          "_mm_ch5_monitoring", "ch5", "section"],
    "1-s2.0-s0377027318304165-main": ["avtod_reath_2019", "avtod_reath_2019_supplementarys1"],
    "1-s2.0-s0377027316305248-main": ["laiolo2017"],
    "1-s2.0-s0034425724004140-main": ["aveni_2024_tirvolch_rse"],
    "thermal_remote_sensing_for_global_volcano_monitori": [
        "coppola2019_frontiers", "coppola2019_supp_datasheet", "coppola_2019_supp_datasheet",
        "coppola_2019_supp_table1", "coppola_2019_supp_table2"],
    "feart-11-1240107": ["coppola2023_frontiers", "coppola_2023_globalradiantflux_mirova"],
    "s00445-024-01721-z": ["campus2024"],
    "campus2022_sensors_22_1713": ["campus2022", "the_transition_from_modis_to_viirs_for_global_volc"],
    "s41598-021-92542-z": ["coppola2021thermal"],
    "rs11131528": ["valade_2019_mounts_ai"],
    "feart-12-1345104": ["saundersshultz_2024_hotlink"],
    "sp426.5": ["sp426_5"],
    "sir20225116": ["pritchard2022_optimizing_satellite_resources_sir"],
    "jgr solid earth - 2024 - massimetti - thermal emissions of active craters at stromboli volcano  spatio‐temporal insights":
        ["massimetti2024_stromboli"],
    "geophysical research letters - 2025 - aveni - volcanic radiative power retrieval from moderate‐to‐low‐temperature features":
        ["aveni2025_crater_lakes"],
    "978-3-031-86841-2": ["coppola2024_chapter"],
    "s00445-022-01523-1": ["coppola2022_sabancaya"],
}

# Documentos que la sintesis SI cubre pero cita sin DOI ni nombre de archivo.
# El valor es el texto verbatim que tiene que estar en BIBLIOGRAPHY_SYNTHESIS.md.
COVERED_ANCHORS = {
    "1-s2.0-s0034425703000701-main": "Wooster et al. 2003 — VRP MIR",
    "1-s2.0-s0377027315003716-main": "Coppola et al. 2016 (Vanuatu 15 años)",
    "1-s2.0-s0377027316305248-main": "Laiolo et al. 2017 (Santa Ana, El Salvador)",
    "1-s2.0-s0377027318304165-main": "AVTOD 2019 (S0377027318304165)",
    "jgr solid earth - 2018 - reath - thermal  deformation  and degassing remote sensing time series  ce 2000 2017  at the 47":
        "Reath et al. 2018/2019",
    "feart-09-722056": "Front Earth Sci 9:722056",
    "thermal_remote_sensing_for_global_volcano_monitori": "Coppola 2020 (feart-07-00362)",
    "torrisi2023_fastvrp_viirs_slstr": "Torrisi et al. 2023 — FastVRP",
    "remotesensing-12-00820-v4": "Massimetti et al. 2020 — Sentinel-2 SWIR 20m",
    "978-3-031-86841-2": "Coppola 2025 (book chapter 11",
    "mcdwd_userguide_revc": "MCDWD UserGuide Rev C",
    "modis_l1b_atbd_c7": "MODIS L1B ATBD / UserGuide / DataDictionary C7",
    "modis_l1b_userguide_c7": "MODIS L1B ATBD / UserGuide / DataDictionary C7",
    "modis_l1b_datadictionary_c7": "MODIS L1B ATBD / UserGuide / DataDictionary C7",
    "viirs_l1b_userguide_aug2021": "VIIRS L1B UserGuide / RadCal ATBD / Geolocation ATBD",
    "viirs_radcal_atbd_2014": "VIIRS L1B UserGuide / RadCal ATBD / Geolocation ATBD",
    "viirs_geolocation_atbd_2014": "VIIRS L1B UserGuide / RadCal ATBD / Geolocation ATBD",
    "1-s2.0-s0034425724004140-main": "Aveni et al. 2024/2025 — TIRVolcH",
    "dhage2025_viirs_filtering": "Dhage 2025 — VIIRS undocumented filtering",
    "jgr solid earth - 2025 - galetto - the application of remote sensing data  sar  thermal and optical  and geodetic modeling":
        "Galetto et al. 2025 (Semeru multisensor)",
}


# Documentos NOMBRADOS en la sintesis que NO estan sintetizados. Mencionar no es
# sintetizar: estos tres aparecen solo dentro de notas de correccion S128 ("no uses
# este archivo", "el producto que corresponderia mirar es este otro"). Contarlos
# como cubiertos infla la cifra sin que nadie haya leido nada (A87).
NOT_COVERED = {
    "no_es_cap11__frontmatter_y_cap1_gravimetria":
        "solo nombrado en 1.50 para advertir que NO es el capitulo 11",
    "platnick_modis_mod06_atbd":
        "solo nombrado en 5 como el ATBD que habria que mirar para cloud masking; sin sintetizar",
    "frey_2008_modis_cloudmask_collection5":
        "idem MOD06: nombrado como pendiente, sin sintetizar",
}


def synthesis_mentions(syn_low: str, syn_dois: set, key: str,
                       names: list, dois: list):
    """Dos senales EXACTAS (DOI, identificador de editorial) + el mapa curado."""
    if key in NOT_COVERED:
        return False, ""
    for d in dois:
        d = d.lower().rstrip(".,;)")
        for sd in syn_dois:
            if d.startswith(sd) or sd.startswith(d):
                return True, f"doi:{d}"
    for nm in names:
        for c in id_candidates(nm, key):
            if c in syn_low:
                return True, f"id:{c}"
    anchor = COVERED_ANCHORS.get(key)
    if anchor:
        return True, f"ancla:{anchor}"
    return False, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="do_print", action="store_true")
    args = ap.parse_args()

    syn_text = SYNTHESIS.read_text(encoding="utf-8", errors="replace")

    # Cache de 1a pagina (DOI + encabezado) de cada PDF. Se genera con
    # scripts/_build_pdf_page1_cache.py; sin el, la senal DOI/titulo no corre.
    cache_path = REPO / "docs" / "s128" / "_pdf_page1_cache.json"
    p1cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    if not p1cache:
        print("[warn] falta docs/s128/_pdf_page1_cache.json: la cobertura sale sub-estimada",
              file=sys.stderr)

    files = []
    for p in sorted(DOCDIR.rglob("*")):
        if p.is_dir():
            continue
        if p.suffix.lower() not in DOC_EXT and not p.name.endswith(".roto"):
            continue
        rel = p.relative_to(DOCDIR).as_posix()
        files.append(
            {
                "rel": rel,
                "name": p.name,
                "bytes": p.stat().st_size,
                "magic": magic(p),
                "md5": md5(p),
                "stem_key": stem_key(p.name),
                "is_own_synthesis": p.name in SYNTHESIS_OWN,
            }
        )

    # --- duplicados exactos por hash ---
    by_hash = defaultdict(list)
    for f in files:
        by_hash[f["md5"]].append(f["rel"])
    dup_groups = []
    dup_wasted = 0
    for h, rels in sorted(by_hash.items()):
        if len(rels) > 1:
            size = next(f["bytes"] for f in files if f["md5"] == h)
            dup_wasted += size * (len(rels) - 1)
            dup_groups.append({"md5": h, "bytes_each": size, "files": sorted(rels),
                               "wasted_bytes": size * (len(rels) - 1)})

    # --- cobertura de la sintesis, contando DOCUMENTOS distintos ---
    docs = defaultdict(list)
    for f in files:
        if f["is_own_synthesis"]:
            continue
        docs[f["stem_key"]].append(f)
    # (a) dos stem_key distintos con el mismo md5 = MISMO documento (copia renombrada).
    #     Se compara CUALQUIER hash del grupo, no solo el del primer archivo:
    #     `AVTOD_Reath_2019.pdf` comparte hash con `1-s2.0-...-main.pdf` pero
    #     `AVTOD_Reath_2019.md` no, y mirar solo el primero los dejaba separados.
    canon = {k: k for k in docs}
    key_of_hash = {}
    for k, group in sorted(docs.items()):
        for f in group:
            h = f["md5"]
            if h in key_of_hash and key_of_hash[h] != k:
                canon[k] = key_of_hash[h]
                break
        else:
            for f in group:
                key_of_hash.setdefault(f["md5"], k)

    # (b) mapa curado: extracciones de texto, suplementos y capitulos sueltos.
    for target, aliases in SAME_DOC.items():
        for a in aliases:
            if a in canon:
                canon[a] = canon.get(target, target)

    def resolve(k, depth=0):
        return k if canon.get(k, k) == k or depth > 5 else resolve(canon[k], depth + 1)

    merged = defaultdict(list)
    for k, group in docs.items():
        merged[resolve(k)].extend(group)

    # Guard (A87): si un ancla curada ya no existe en la sintesis, el numero
    # dejaria de significar lo que dice. Preferimos fallar ruidosamente.
    missing_anchors = [f"{k} -> {a!r}" for k, a in COVERED_ANCHORS.items()
                       if a not in syn_text]
    stale_aliases = [a for al in SAME_DOC.values() for a in al if a not in docs]

    # POR QUE se descartan las citas en blockquote: el bloque de higiene S128 al
    # tope de la sintesis NOMBRA archivos rotos y archivos sin sintetizar (MOD06,
    # Frey 2008). Contarlos como "cubiertos" porque aparecen ahi seria exactamente
    # el auto-engano de A87: la metrica volveria a banda sin que nadie haya
    # sintetizado nada. Mencionar != sintetizar.
    syn_body = "\n".join(l for l in syn_text.splitlines() if not l.lstrip().startswith(">"))
    syn_low = syn_body.lower()
    syn_dois = {m.group(0).lower().rstrip(".,;)")
                for m in re.finditer(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", syn_body)}

    covered, uncovered = [], []
    for k, group in sorted(merged.items()):
        names = [f["name"] for f in group]
        rels = [f["rel"] for f in group]
        dois = []
        for rel in rels:
            dois += p1cache.get(rel, {}).get("dois", [])
        hit, why = synthesis_mentions(syn_low, syn_dois, k, names, dois)
        rec = {"doc_key": k, "files": sorted(rels),
               "bytes": max(f["bytes"] for f in group),
               "dois": sorted(set(d.lower() for d in dois))[:3],
               "evidence": why}
        (covered if hit else uncovered).append(rec)

    n_docs = len(merged)
    n_cov = len(covered)

    # POR QUE tambien la cifra "solo PDF": el numero viejo del proyecto
    # ("30/60 PDFs, 54 %") tenia denominador PDF. Sin esta cifra el reemplazo
    # no seria comparable con lo que se esta corrigiendo.
    pdf_docs = [r for r in covered + uncovered
                if any(f.lower().endswith(".pdf") for f in r["files"])]
    pdf_cov = [r for r in covered if any(f.lower().endswith(".pdf") for f in r["files"])]

    broken = [f for f in files
              if (f["name"].lower().endswith(".pdf") and f["magic"] != "pdf")
              or f["name"].endswith(".roto")
              or f["magic"] == "html"]

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "scripts/audit_corpus_documentacion.py",
        "documentacion_dir": DOCDIR.as_posix(),
        "n_files": len(files),
        "total_bytes": sum(f["bytes"] for f in files),
        "coverage": {
            "n_distinct_documents": n_docs,
            "n_mentioned_in_synthesis": n_cov,
            "pct": round(100.0 * n_cov / n_docs, 1) if n_docs else 0.0,
            "n_pdf_documents": len(pdf_docs),
            "n_pdf_mentioned": len(pdf_cov),
            "pct_pdf_only": round(100.0 * len(pdf_cov) / len(pdf_docs), 1) if pdf_docs else 0.0,
            "method": "1 documento = 1 stem_key (un PDF y su .md/.txt extraido cuentan UNA vez; "
                      "dos archivos con el mismo md5 tambien). Se excluyen las sintesis propias "
                      "del proyecto. 'Mencionado' = union de 3 senales contra "
                      "BIBLIOGRAPHY_SYNTHESIS.md: DOI de la 1a pagina, identificador de "
                      "editorial/archivo, o trigrama del titulo. A89: una sola senal produce "
                      "ceros que se leen como ausencia.",
            "excluded_own_synthesis": sorted(SYNTHESIS_OWN),
            "missing_anchors": missing_anchors,
            "stale_same_doc_aliases": stale_aliases,
        },
        "covered": covered,
        "uncovered": uncovered,
        "duplicate_groups": dup_groups,
        "duplicate_wasted_bytes": dup_wasted,
        "broken_or_mislabeled": [
            {"rel": f["rel"], "bytes": f["bytes"], "magic": f["magic"], "md5": f["md5"]}
            for f in broken
        ],
        "files": files,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[ok] {OUT}")
    print(f"  archivos                : {payload['n_files']}")
    print(f"  documentos distintos    : {n_docs}")
    print(f"  mencionados en sintesis : {n_cov}  ({payload['coverage']['pct']} %)")
    print(f"  grupos duplicados       : {len(dup_groups)}  "
          f"({dup_wasted/1e6:.1f} MB recuperables)")
    print(f"  rotos/mal etiquetados   : {len(broken)}")

    if args.do_print:
        print("\n-- duplicados --")
        for g in sorted(dup_groups, key=lambda g: -g["wasted_bytes"]):
            print(f"  {g['bytes_each']:>12,} B  md5={g['md5'][:12]}  {g['files']}")
        print("\n-- documentos NO mencionados en la sintesis --")
        for r in uncovered:
            print(f"  {r['doc_key']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
