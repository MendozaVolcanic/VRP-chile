# -*- coding: utf-8 -*-
"""S128 Fase 1 — cierre por MEDICION de los 19 pendientes de AUDIT_S121.

Regla C del protocolo: los pendientes de la auditoria anterior son la puerta de
entrada de la siguiente. Regla B: ningun hallazgo pasa a CONFIRMADO / REFUTADO /
OBSOLETO sin un test que lo mida, o la razon escrita de por que no se puede.

Cada item devuelve {afirmacion, evidencia}. Los numeros salen de aca, no de la
prosa (S91). Read-only: no escribe nada fuera de su propio JSON.
"""
import csv as _csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLECHA = "→"
R = {}


def leer(p):
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp):
        return None
    return open(fp, encoding="utf-8", errors="replace").read()


def du_mb(rel):
    """Tamano de un directorio en MB. os.walk, no `du` (portabilidad Windows)."""
    base = os.path.join(ROOT, rel)
    if not os.path.exists(base):
        return None
    tot = 0
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return round(tot / 1e6, 1)


def git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=300).stdout
    except Exception as e:                                    # noqa: BLE001
        return "ERROR: %s" % e


WF = os.path.join(ROOT, ".github", "workflows")
ACTIVOS = sorted(f for f in os.listdir(WF) if f.endswith((".yml", ".yaml"))) \
    if os.path.isdir(WF) else []

# -- L69 . filtro H8 de store.py no limpia vrp_mw en MODIS/VIIRS750 -----------
src = leer("pipeline/store.py") or ""
lineas = src.splitlines()
R["L69_h8_store"] = {
    "afirmacion": "el filtro pixel-por-pixel de store.py no limpia vrp_mw para "
                  "MODIS/VIIRS750; el VRP persistido sigue contaminado",
    "lineas_filtro_distancia": [i + 1 for i, l in enumerate(lineas)
                                if re.search(r"max_hotspot_dist|hotspot_dist_km", l)][:25],
    "lineas_que_tocan_vrp_mw": [i + 1 for i, l in enumerate(lineas)
                                if "vrp_mw" in l][:40],
    "n_lineas_store": len(lineas),
}

# -- L74 . inputs de workflow_dispatch interpolados sin comillas en `run:` ----
# Vector de inyeccion: ${{ github.event.inputs.X }} o ${{ inputs.X }} DENTRO de
# un bloque run:, sin pasar por env:. El fix canonico es env: + comillas.
inj = []
for f in ACTIVOS:
    txt = open(os.path.join(WF, f), encoding="utf-8", errors="replace").read()
    en_run = False
    for n, l in enumerate(txt.splitlines(), 1):
        if re.match(r"\s*run:\s*\|?", l):
            en_run = True
            continue
        if en_run and re.match(r"\s*(-\s+)?(name|uses|with|env|if|id):", l):
            en_run = False
        if en_run and re.search(r"\$\{\{\s*(github\.event\.)?inputs\.", l):
            inj.append({"wf": f, "linea": n, "txt": l.strip()[:120]})
R["L74_inyeccion_inputs"] = {
    "afirmacion": "3 workflows activos interpolan inputs sin comillas en run: "
                  "-> inyeccion de comandos con acceso a secrets NASA",
    "n_workflows_activos": len(ACTIVOS),
    "ocurrencias": inj,
    "n_workflows_afectados": len({o["wf"] for o in inj}),
}

# -- L79 . run_pipeline.py dice 'Cleaned up' aunque el borrado falle ---------
rp_path = "scripts/run_pipeline.py" if os.path.exists(
    os.path.join(ROOT, "scripts/run_pipeline.py")) else "run_pipeline.py"
rp = leer(rp_path) or ""
rl = rp.splitlines()
cl = [i + 1 for i, l in enumerate(rl) if "cleaned up" in l.lower()]
R["L79_cleanup_miente"] = {
    "afirmacion": "imprime 'Cleaned up' aunque los 3 reintentos de borrado fallen",
    "archivo": rp_path,
    "lineas": cl,
    "contexto": [rl[i].rstrip()[:150] for i in range(max(0, cl[0] - 16), min(len(rl), cl[0] + 3))]
    if cl else [],
}

# -- L84 . flecha Unicode en mensaje RUNTIME de fetch.py (crash cp1252) ------
fe = leer("pipeline/fetch.py") or ""
flechas = []
for i, l in enumerate(fe.splitlines(), 1):
    if FLECHA not in l:
        continue
    s = l.strip()
    flechas.append({"linea": i, "comentario": s.startswith("#"),
                    "runtime": bool(re.search(r"(print|_diag|log|logger)\s*\(", l)),
                    "txt": s[:120]})
R["L84_unicode_fetch"] = {
    "afirmacion": "queda una flecha Unicode en un mensaje runtime (_diag), no solo "
                  "en comentarios",
    "total": len(flechas),
    "en_runtime": [f for f in flechas if f["runtime"]],
    "solo_comentario": sum(1 for f in flechas if f["comentario"]),
}

# -- L106 . AUDIT_S119 seccion 8: 8 de 10 mejoras nunca construidas ----------
R["L106_mejoras_s119"] = {
    "afirmacion": "8 de 10 mejoras de auditoria propuestas por Nicolas siguen sin "
                  "construirse (solo el auto-audit semanal se hizo)",
    "existe_audit_s119": bool(leer("docs/AUDIT_S119.md")),
    "auto_audit_script": os.path.exists(os.path.join(ROOT, "scripts",
                                                     "auto_audit_weekly.py")),
    "workflows_de_audit": [f for f in ACTIVOS if "audit" in f],
}

# -- L111 / L131 / L213 . el peso real en disco -----------------------------
sub = os.path.join(ROOT, "data")
subdirs = sorted(os.listdir(sub)) if os.path.isdir(sub) else []
R["L111_data_peso"] = {
    "afirmacion": "data/ tiene 2,0 GB de los cuales solo ~180 MB es operacional",
    "data_total_mb": du_mb("data"),
    "operacional_mirova_equivalent_mb": du_mb("data/mirova_equivalent"),
    "subdirs": subdirs,
}
exp = os.path.join(ROOT, "experiments")
R["L131_experiments_peso"] = {
    "afirmacion": "experiments/ 458 MB; 3 subdirs (S98/S104/S109) concentran 366 MB",
    "experiments_total_mb": du_mb("experiments"),
    "top8": sorted(((du_mb("experiments/" + d) or 0, d)
                    for d in (os.listdir(exp) if os.path.isdir(exp) else [])
                    if os.path.isdir(os.path.join(exp, d))), reverse=True)[:8],
}
ab = {d: du_mb("data/" + d) for d in subdirs
      if d.startswith("mirova_equivalent") and d != "mirova_equivalent"}
R["L213_snapshots_ab"] = {
    "afirmacion": "pre_s27 (195 MB) + ~10 subcarpetas mirova_equivalent_* = ~556 MB",
    "por_subdir_mb": ab,
    "suma_mb": round(sum(v for v in ab.values() if v), 1),
    "n_subdirs": len(ab),
}

# -- L116 . AVTOD (Reath 2019) nunca integrado ------------------------------
hits = [x for x in git("grep", "-ril", "AVTOD", "--", "scripts", "pipeline",
                       "experiments", "docs", "tests").split("\n") if x]
R["L116_avtod"] = {
    "afirmacion": "EXT-8 AVTOD (Reath 2019), ground truth independiente ya "
                  "descargado, nunca integrado al workflow de validacion",
    "pdf_en_repo": os.path.exists(os.path.join(ROOT, "documentacion",
                                               "AVTOD_Reath_2019.pdf")),
    "archivos_que_lo_mencionan": hits[:25],
    "lo_usa_codigo": [x for x in hits if x.startswith(("scripts/", "pipeline/"))],
}

# -- L126 . PDF duplicado exacto en documentacion/ --------------------------
doc = os.path.join(ROOT, "documentacion")
por_hash = {}
for f in sorted(os.listdir(doc)):
    fp = os.path.join(doc, f)
    if not os.path.isfile(fp) or os.path.getsize(fp) < 500_000:
        continue
    h = hashlib.md5(open(fp, "rb").read()).hexdigest()
    por_hash.setdefault(h, []).append((f, os.path.getsize(fp)))
dups = {h: v for h, v in por_hash.items() if len(v) > 1}
R["L126_pdf_duplicado"] = {
    "afirmacion": "PDF duplicado exacto en documentacion/ (26 MB desperdiciados)",
    "grupos": [{"md5": h[:12], "archivos": [a for a, _ in v], "bytes_c_u": v[0][1],
                "desperdicio_mb": round(v[0][1] * (len(v) - 1) / 1e6, 1)}
               for h, v in dups.items()],
    "desperdicio_total_mb": round(sum(v[0][1] * (len(v) - 1)
                                      for v in dups.values()) / 1e6, 1),
}

# -- L136 . contradiccion documental sobre el GAP #A ------------------------
gap = {}
for p in ("CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md",
          "docs/AUDIT_S114_PARITY_BY_SENSOR.md"):
    t = leer(p) or ""
    gap[p] = [l.strip()[:170] for l in t.splitlines() if "GAP #A" in l][:6]
R["L136_gap_a"] = {
    "afirmacion": "CLAUDE.md/MISSION.md dicen 'pendiente' del GAP #A; "
                  "MIROVA_DIVERGENCES/AUDIT_S114 dicen 'resuelto S115 (mislabel)'",
    "menciones": gap,
}

# -- L178 . la data domina la historia del repo; .git 3,1 GB ---------------
tot = git("rev-list", "--count", "HEAD").strip()
dat = git("rev-list", "--count", "HEAD", "--", "data").strip()
co = git("count-objects", "-vH")
R["L178_git_peso"] = {
    "afirmacion": "data/ = 83,8 % de los commits; .git ya es 3,1 GB",
    "commits_totales": tot,
    "commits_que_tocan_data": dat,
    "pct": round(100 * int(dat) / int(tot), 1)
    if tot.isdigit() and dat.isdigit() and int(tot) else None,
    "count_objects": {k.strip(): v.strip() for k, v in
                      (l.split(":", 1) for l in co.splitlines() if ":" in l)},
    "git_dir_mb": du_mb(".git"),
}

# -- L188 . el ground truth CSV esta fresco --------------------------------
frescura = {}
for p in ("latest_consolidado.csv",
          "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
          "data/mirova_reference/registro_vrp_ocr.csv",
          "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"):
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp):
        frescura[p] = "NO EXISTE"
        continue
    fechas = []
    for r in _csv.DictReader(open(fp, encoding="utf-8", errors="replace")):
        f = (r.get("Fecha_Satelite_UTC") or r.get("Fecha_UTC") or "")[:10]
        if len(f) == 10 and f[:2] == "20":
            fechas.append(f)
    frescura[p] = {"filas_con_fecha": len(fechas),
                   "min": min(fechas) if fechas else None,
                   "max": max(fechas) if fechas else None}
R["L188_gt_fresco"] = {
    "afirmacion": "el ground truth CSV (mirova_v1_snapshot) SI esta fresco",
    "por_archivo": frescura,
}

# -- L193 / L198 / L203 . guards de los workflows --------------------------
wfinfo = {}
for f in ACTIVOS:
    txt = open(os.path.join(WF, f), encoding="utf-8", errors="replace").read()
    g = re.search(r"group:\s*(\S+)", txt)
    wfinfo[f] = {
        "concurrency_nivel_workflow": bool(re.search(r"^concurrency:", txt, re.M)),
        "concurrency_nivel_job": bool(re.search(r"^\s+concurrency:", txt, re.M)),
        "grupo": g.group(1) if g else None,
        "timeout_minutes": bool(re.search(r"timeout-minutes:", txt)),
        "on_quoted": bool(re.search(r'^"on":', txt, re.M)),
        "hace_push": "git push" in txt,
    }
R["L193_L198_L203_workflows"] = {
    "afirmacion": "nrt.yml sin concurrency a nivel workflow; nrt-retry.yml sin "
                  "timeout-minutes; backfill y reproc-s120 sin concurrency",
    "por_workflow": wfinfo,
}

# -- L208 . ningun echo/print de secrets ----------------------------------
fugas = []
for f in ACTIVOS:
    txt = open(os.path.join(WF, f), encoding="utf-8", errors="replace").read()
    for n, l in enumerate(txt.splitlines(), 1):
        if re.search(r"\b(echo|print|cat)\b", l) and "secrets." in l:
            fugas.append({"wf": f, "linea": n, "txt": l.strip()[:120]})
R["L208_secrets"] = {
    "afirmacion": "sin echo/print de secrets en los workflows activos (eje sano)",
    "n_workflows_revisados": len(ACTIVOS),
    "fugas": fugas,
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "01_s121_pendientes.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("escrito:", out)
for k, v in R.items():
    print("\n=== " + k + " ===")
    print(json.dumps(v, ensure_ascii=False, indent=1)[:1500])
