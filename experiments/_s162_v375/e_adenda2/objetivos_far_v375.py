# -*- coding: utf-8 -*-
"""S166 V375-E, adenda 2 (brazos de posición): lista SUPLEMENTARIA con las pasadas VIIRS 375 del marco de S159 en que
MIROVA publicó una fuente lejana (etiqueta `far_ref` de banco_paridad: fila FALSO_POSITIVO y ninguna ALERTA a ±120 s).

POR QUÉ. Nicolás decidió (2026-10-27, programa §7) medir la regla de posición del record como tres brazos (radiante,
cercano y pico) contra lo que publica MIROVA, incluidas las pasadas en que MIROVA ubicó el calor lejos del cráter. El
marco de V375-B y V375-C (`experiments/_s159/portes/poblacion_completa.json`) sólo trae `pos` y `neg_limpio`
(`experiments/_s159/portes/01_poblacion.py`, filtro de etiquetas), así que esas pasadas no tienen grilla guardada: el
verificador de S165 (H1) contó 338 en la copia de hoy de la referencia. Son justo la escena donde «cercano» puede
publicar de más. Este script NO toca el marco: corre la MISMA población con los MISMOS insumos congelados (records de
`533398f8f`, referencia de Mirova-v1 en los commits que guarda el meta del marco), cambiando sólo el filtro de
etiquetas para dejar pasar `far_ref`, y escribe aparte:

  objetivos_far_v375.json     las pasadas far_ref con gránulo, ids desde 20000 (los usados van de 0 a 5019);
  sin_granulo_far_v375.json   las far_ref sin gránulo, atadas por sha256 a la lista;
  poblacion_far.json          la población completa de esta corrida (para auditar).

Dos subclases, porque `banco_paridad.es_fp` cuenta también `FALSO_POSITIVO_OCR`, que es una etiqueta del scraper (el
OCR no pudo confirmar la imagen, A11) y no una publicación de MIROVA:
  far_tabla  la pasada trae una fila FALSO_POSITIVO del consolidado (MIROVA publicó la fuente a esa distancia): DECIDE;
  far_ocr    sólo filas FALSO_POSITIVO_OCR: se corre y se informa, no decide.

CONTROLES (si uno falla, sale 1 sin escribir ninguna lista):
  C-G1  los JSON de records que lee la población son, byte a byte, los blobs de `533398f8f` (hash de git);
  C-G2  la referencia se baja de los commits del meta del marco, no del remoto de hoy;
  C-G3  las pasadas `pos` y `neg_limpio` de esta corrida son EXACTAMENTE las del marco congelado, entrada por entrada
        (todos los campos), en los dos sensores: así se ve que el cambio de filtro no tocó nada más;
  C-G4  la grilla de cada volcán es la que usó el lote S162 (una sola por volcán en objetivos_v375_bc.json).
Se niega a escribir en la carpeta del marco o encima de salidas de otra corrida (sale 2; no borra nada).

Uso: python -I objetivos_far_v375.py --data <data/mirova_equivalent de 533398f8f> --ref-dest <carpeta> --dest <carpeta>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
V375 = AQUI.parent
RAIZ = V375.parents[1]
PORTES = RAIZ / "experiments/_s159/portes"
MARCO = PORTES / "poblacion_completa.json"
COMMIT_RECORDS = "533398f8f"
FILTRO_MARCO = 'r["lab"] not in ("pos", "neg_limpio")'
FILTRO_FAR = 'r["lab"] not in ("pos", "neg_limpio", "far_ref")'
ID0 = 20000
CRLF, LF = bytes([13, 10]), bytes([10])
ID_CTLF = 29000
EXCLUIDOS = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
SALIDAS = ("objetivos_far_v375.json", "sin_granulo_far_v375.json", "objetivos_run_far_v375.json", "poblacion_far.json",
           "poblacion_completa.json", "poblacion_far_CONTROL_FALLIDO.json")


def sha256_bytes(b):
    """sha256 con fin de línea LF (core.autocrlf puede convertir los .json al extraer: el hash no debe depender de eso)."""
    return hashlib.sha256(b.replace(CRLF, LF)).hexdigest()


def blob_git(b):
    """El hash de git de un archivo (sha1 de «blob <largo>\\0» + contenido): compara contra git ls-tree sin extraer."""
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def poblacion_con_far_ref(ruta):
    """Carga 01_poblacion.py cambiando SÓLO su filtro de etiquetas; falla si el filtro no aparece exactamente una vez."""
    src = Path(ruta).read_text(encoding="utf-8")
    n = src.count(FILTRO_MARCO)
    if n != 1:
        raise SystemExit(f"01_poblacion.py: el filtro de etiquetas aparece {n} veces (tiene que ser 1): no se genera")
    m = type(sys)("pob_far")
    m.__file__ = str(ruta)
    exec(compile(src.replace(FILTRO_MARCO, FILTRO_FAR), str(ruta), "exec"), m.__dict__)
    return m


def subclase(p):
    """far_tabla si la pasada trae alguna fila FALSO_POSITIVO del consolidado; si no, far_ocr."""
    return "far_tabla" if any(str(f.get("tipo", "")).startswith("FALSO_POSITIVO") and f.get("source") == "CONS"
                              for f in p.get("mirova") or []) else "far_ocr"


def dist_ref(p):
    """Distancia de MIROVA para la vara 3: la de la primera fila FALSO_POSITIVO del consolidado con distancia; en una
    far_ocr, la de la primera FALSO_POSITIVO_OCR (informa)."""
    fp = [f for f in p.get("mirova") or [] if str(f.get("tipo", "")).startswith("FALSO_POSITIVO")
          and f.get("dist_km") is not None]
    cons = [f for f in fp if f.get("source") == "CONS"]
    return (cons or fp or [{"dist_km": None}])[0]["dist_km"]


def comparar(pob, marco):
    """C-G3: pos y neg_limpio de esta corrida = el marco, entrada por entrada (json canónico de la entrada entera)."""
    def can(o):
        return json.dumps(o, sort_keys=True, ensure_ascii=False, default=str)
    a = sorted(can(p) for p in pob if p["lab"] in ("pos", "neg_limpio"))
    b = sorted(can(p) for p in marco)
    return a == b, len(a), len(b)


def seleccionar_far(pob, excluidos=EXCLUIDOS):
    """(far con gránulo, far sin gránulo), VIIRS 375, sin los días excluidos del marco de B y C."""
    far = [dict(p) for p in pob if p["lab"] == "far_ref" and p["b"] == "VIIRS375"
           and p["hora_utc"][:10] not in excluidos]
    for p in far:
        p["clase"] = subclase(p)
        p["dist_ref"] = dist_ref(p)
    sin_g = [{k: p.get(k) for k in ("volcan", "hora_utc", "sensor", "clase", "dist_ref")} for p in far
             if not p.get("granule")]
    return [p for p in far if p.get("granule")], sin_g


def tramo(h):
    d = h[:10]
    return "T" if d < "2026-06-13" else ("O1" if d < "2026-08-29" else "O2")


def grillas_s162():
    """C-G4: la grilla de cada volcán en el lote S162 (tiene que ser una sola por volcán)."""
    g = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        s = json.dumps(o["grilla"], sort_keys=True)
        if g.setdefault(o["volcan"], s) != s:
            raise SystemExit(f"C-G4: el volcán {o['volcan']} tiene más de una grilla en objetivos_v375_bc.json")
    return {k: json.loads(v) for k, v in g.items()}


def completar(far, grillas):
    """Campos que leen el probe (id, volcan, hora_utc, clase, granule, grilla) y el lector (lote, estrato, tramo)."""
    far.sort(key=lambda e: (e["granule"] or "", e["volcan"], e["hora_utc"]))
    for n, e in enumerate(far):
        if e["volcan"] not in grillas:
            raise SystemExit(f"C-G4: sin grilla del lote S162 para {e['volcan']}")
        e.update({"id": ID0 + n, "lote": "FAR", "tramo": tramo(e["hora_utc"]),
                  "estrato": f"{e['volcan']}|{e['estrato_z']}", "grilla": grillas[e["volcan"]]})
    return far


def control_vida():
    """Las 20 pasadas del control de vida de B2 (re-mediciones de S162 con su M14 de referencia, b2/PREREGISTRO_B2.md
    §4), con ids desde 29000 y lote CTLF: en el run FAR prueban que el port y la bajada están vivos (C7 del lector)."""
    b2 = json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]
    ctl = [dict(o) for o in b2 if o["lote"] == "CTL"]
    if len(ctl) != 20 or any(not o.get("ref_M14") for o in ctl):
        raise SystemExit("control de vida: b2/objetivos_v375_b2.json no trae las 20 pasadas CTL con ref_M14")
    for n, o in enumerate(sorted(ctl, key=lambda e: e["id"])):
        o.update({"id": ID_CTLF + n, "id_b2": o["id"], "lote": "CTLF"})
    return sorted(ctl, key=lambda e: e["id"])


def bajar_fijo(dest, shas):
    """C-G2: consolidado y OCR en los commits de Mirova-v1 que guarda el meta del marco (no el remoto de hoy)."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    from referencia_mirova_unificada import URL_RAW
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    info = {}
    for nombre, sha in shas.items():
        destino = dest / nombre
        urllib.request.urlretrieve(URL_RAW.format(sha=sha, nombre=nombre), destino)
        info[nombre] = {"sha": sha, "path": str(destino), "sha256": sha256_bytes(destino.read_bytes())}
    return info


def control_records(data, vols):
    """C-G1: cada JSON de records que lee la población es el blob de 533398f8f. Devuelve la lista de distintos."""
    malos = []
    for vol in vols:
        f = Path(data) / f"{vol}.json"
        esperado = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", f"{COMMIT_RECORDS}:data/mirova_equivalent/{vol}.json"],
                                  capture_output=True, text=True).stdout.strip()
        crudo = f.read_bytes() if f.exists() else None
        real = None if crudo is None else blob_git(crudo)
        if crudo is not None and real != esperado:        # un checkout con autocrlf deja CRLF; git guarda LF
            real = blob_git(crudo.replace(CRLF, LF))
        if not esperado or real != esperado:
            malos.append((vol, esperado, real))
    return malos


def generar(dest, data, ref_dest, marco_ruta=MARCO, portes=PORTES, dep=None):
    """dep (para la batería): {'poblar': f(dest, data, ref_dest, shas) -> escribe dest/poblacion_completa.json,
    'vols': [...], 'control_records': f(data, vols), 'grillas': f()}."""
    dest = Path(dest)
    if dest.resolve() == Path(portes).resolve():
        print(f"--dest no puede ser la carpeta del marco ({portes}): pisaría su poblacion_completa.json")
        return 2
    previos = [n for n in SALIDAS if (dest / n).exists()]
    if previos:
        print(f"en {dest} ya hay salidas de otra corrida {previos}: usa una carpeta nueva (no se escribe encima)")
        return 2
    marco = json.loads(Path(marco_ruta).read_text(encoding="utf-8"))
    dep = dep or dependencias_reales()
    malos = dep["control_records"](data, dep["vols"])
    if malos:
        print("C-G1 FALLA: records distintos de", COMMIT_RECORDS, malos[:5])
        return 1
    print(f"C-G1 OK: {len(dep['vols'])} archivos de records iguales a los blobs de {COMMIT_RECORDS}")
    shas = marco["meta"]["referencia"]
    dest.mkdir(parents=True, exist_ok=True)
    dep["poblar"](dest, data, ref_dest, shas)
    crudo = dest / "poblacion_completa.json"
    pob_d = json.loads(crudo.read_text(encoding="utf-8"))
    if pob_d["meta"]["referencia"] != shas:
        crudo.rename(dest / "poblacion_far_CONTROL_FALLIDO.json")
        print("C-G2 FALLA: la referencia no es la del marco", pob_d["meta"]["referencia"], shas)
        return 1
    print("C-G2 OK: referencia del marco", shas)
    igual, na, nb = comparar(pob_d["pasadas"], marco["pasadas"])
    if not igual:
        crudo.rename(dest / "poblacion_far_CONTROL_FALLIDO.json")
        print(f"C-G3 FALLA: pos y neg_limpio de esta corrida ({na}) distintos del marco ({nb}): no se escribe ninguna lista")
        return 1
    print(f"C-G3 OK: pos y neg_limpio IGUALES al marco, entrada por entrada ({na} contra {nb})")
    crudo.rename(dest / "poblacion_far.json")
    pob_sha = sha256_bytes((dest / "poblacion_far.json").read_bytes())
    far, sin_g = seleccionar_far(pob_d["pasadas"])
    far = completar(far, dep["grillas"]())
    meta = {"marco": str(Path(marco_ruta).relative_to(RAIZ)) if Path(marco_ruta).is_relative_to(RAIZ) else str(marco_ruta),
            "marco_sha256": sha256_bytes(Path(marco_ruta).read_bytes()), "records": COMMIT_RECORDS,
            "referencia": shas, "capas_locales": dep["capas"](), "poblacion_far_sha256": pob_sha,
            "excluidos": list(EXCLUIDOS), "id0": ID0,
            "clases": {c: sum(1 for p in far if p["clase"] == c) for c in ("far_tabla", "far_ocr")}}
    txt = json.dumps({"meta": meta, "pasadas": far}, ensure_ascii=False, indent=0, default=str)
    (dest / "objetivos_far_v375.json").write_bytes(txt.encode("utf-8"))
    sha_obj = sha256_bytes(txt.encode("utf-8"))
    (dest / "sin_granulo_far_v375.json").write_bytes(json.dumps(
        {"objetivos_far_sha256": sha_obj, "pasadas": sin_g}, ensure_ascii=False, indent=0).encode("utf-8"))
    ctlf = dep["control_vida"]()
    run = {"meta": {**meta, "objetivos_far_sha256": sha_obj, "n_far": len(far), "n_ctlf": len(ctlf)},
           "pasadas": far + ctlf}
    txt_run = json.dumps(run, ensure_ascii=False, indent=0, default=str)
    (dest / "objetivos_run_far_v375.json").write_bytes(txt_run.encode("utf-8"))
    import collections
    print(f"far_ref VIIRS 375 con gránulo: {len(far)} {meta['clases']}; sin gránulo: {len(sin_g)}")
    print("  por volcán:", dict(sorted(collections.Counter(p["volcan"] for p in far).items())))
    print("  por tramo:", dict(sorted(collections.Counter(p["tramo"] for p in far).items())))
    print("  por subclase y tramo:", dict(sorted(collections.Counter((p["clase"], p["tramo"]) for p in far).items())))
    print("  producción publica:", sum(bool(p.get("pub_prod")) for p in far), "de", len(far))
    d = sorted(p["dist_ref"] for p in far if p["dist_ref"] is not None)
    if d:
        print(f"  distancia de MIROVA (km): mín {d[0]}, mediana {d[len(d) // 2]}, máx {d[-1]}")
    print("control de vida CTLF (re-medidas de S162, como en B2):", len(ctlf), "ids", ctlf[0]["id"] if ctlf else None,
          "a", ctlf[-1]["id"] if ctlf else None)
    print("sha256 objetivos_far_v375.json:", sha_obj)
    print("sha256 objetivos_run_far_v375.json (lo que lee el run):", sha256_bytes(txt_run.encode("utf-8")))
    print("sha256 poblacion_far.json:", pob_sha)
    return 0


def dependencias_reales():
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "scripts"))
    import banco_paridad as B

    def poblar(dest, data, ref_dest, shas):
        P = poblacion_con_far_ref(PORTES / "01_poblacion.py")
        P.AQUI = Path(dest)                         # escribe poblacion_completa.json en dest; generar() lo renombra
        P.bajar_remoto = lambda d: bajar_fijo(d, shas)
        viejo = sys.argv
        sys.argv = ["01_poblacion.py", "--data", str(data), "--ref-dest", str(ref_dest)]
        try:
            P.main()
        finally:
            sys.argv = viejo

    return {"poblar": poblar, "vols": list(B.VOLS), "control_records": control_records, "grillas": grillas_s162,
            "control_vida": control_vida, "capas": capas_locales}


def capas_locales():
    """VE2-02 del verificador: cargar_referencia_unificada suma por defecto dos capas locales del repo (las filas que
    la tabla de Mirova-v1 tuvo y perdió, y el respaldo del 2026-04-08), y 15 de las 330 lejanas sacan de ahí su fila
    FALSO_POSITIVO. Se fijan por sha256 LF junto a los commits de la referencia."""
    import referencia_mirova_unificada as R
    return {str(Path(q).relative_to(RAIZ)).replace(chr(92), "/"): sha256_bytes(Path(q).read_bytes())
            for q in (R.HISTORICO_RECUPERADAS, R.RESPALDO_20260408)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    ap.add_argument("--dest", default=str(AQUI))
    a = ap.parse_args(argv)
    return generar(a.dest, a.data, a.ref_dest)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
