# -*- coding: utf-8 -*-
"""Eje 4.3+4.4 auditoria S119 — clasificacion workflows y profiles.

Workflows: activos-necesarios vs one-shot ya corridos (candidatos a
`.github/workflows/_archive/`, patron PR #217). Las fechas de ultima corrida
se verificaron con `gh run list` (2026-07-01) y se hardcodean aca como dato.

Profiles: operacionales / c2ab (se quedan, reproducibilidad flip S118) /
baseline S81 / referenciados por tests o workflows activos / huerfanos.
READ-ONLY: solo propone, no mueve nada (A38).

Output: eje4_workflows_profiles.json
"""
import sys, io, json, re, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
WF = REPO / ".github" / "workflows"
PROF = REPO / "pipeline" / "profiles"
OUT = Path(__file__).resolve().parent / "eje4_workflows_profiles.json"

ACTIVE_WF = {
    "nrt.yml": "cron NRT cada 2h (core)",
    "nrt-healthcheck.yml": "monitoreo NRT",
    "nrt-monitor.yml": "monitoreo NRT",
    "nrt-retry.yml": "retry NRT",
    "pages-deploy.yml": "deploy dashboard GitHub Pages",
    "sync-mirova-csv.yml": "sync CSV ground truth Mirova-v1",
}

# gh run list --workflow=<f> --limit 1 (verificado 2026-07-01)
LAST_RUN = {
    "probe-s104-nti.yml": ("2026-06-09", "success"),
    "probe-s104-roi.yml": ("2026-06-08", "success"),
    "probe-s105-disc-tl.yml": ("2026-06-10", "success"),
    "probe-s105-disc.yml": ("2026-06-09", "success"),
    "probe-s110-ndc-assembly.yml": ("2026-06-16", "success"),
    "probe-s110-ndc-firstpass.yml": ("2026-06-16", "failure (superado por assembly)"),
    "reproc-s101-nadir-validation.yml": ("2026-06-05", "success"),
    "reproc-s101-sec3-ab.yml": ("2026-06-05", "success"),
    "reproc-s102-nadir-promote.yml": ("2026-06-05", "success"),
    "reproc-s102-viirs-nadir-ab.yml": ("2026-06-06", "success"),
    "reproc-s102-viirs-noctx-ab.yml": ("2026-06-07", "cancelled (A/B 3 brazos cerrado S102)"),
    "reproc-s103-viirs-nadir-promote.yml": ("2026-06-07", "success"),
    "reproc-s103-viirs-pcc-tupun.yml": ("2026-06-08", "success"),
    "reproc-s104-test1-nti-ab.yml": ("2026-06-09", "success"),
    "reproc-s104-test1-nti-integral.yml": ("2026-06-09", "success"),
    "reproc-s105-test1-nti-local-sweep.yml": ("2026-06-10", "success"),
    "reproc-s105-test1-nti-local.yml": ("2026-06-10", "success"),
    "reproc-s106-anchor-rest.yml": ("2026-06-12", "success"),
    "reproc-s106-anchor-v750.yml": ("2026-06-13", "success"),
    "reproc-s106-honest-anchor.yml": ("2026-06-11", "success"),
    "reproc-s107-modis-localmag-ab.yml": ("2026-06-13", "success"),
    "reproc-s108-anchor-v750-rest.yml": ("2026-06-13", "success"),
    "reproc-s109-focal-promote.yml": ("2026-06-15", "success"),
    "reproc-s109-modis-focalmag-ab.yml": ("2026-06-15", "success"),
    "reproc-s111-d11-ab.yml": ("2026-06-17", "success"),
    "reproc-s112-t1lm-ab.yml": ("2026-06-17", "success"),
    "reproc-s112-v750focal-ab.yml": ("2026-06-18", "success"),
    "reproc-s118-c2-gates-ab.yml": ("2026-06-28", "success (run 28312968093, flip S118 cerrado)"),
}


def grep_refs(name_stem, roots):
    """Busca referencias a un profile por nombre en tests/, workflows activos y scripts/."""
    hits = []
    pat = re.compile(re.escape(name_stem))
    for root in roots:
        for p in root.rglob("*"):
            if p.suffix not in {".py", ".yml", ".yaml", ".sh"} or not p.is_file():
                continue
            try:
                if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(p.relative_to(REPO)))
            except OSError:
                pass
    return hits


def main():
    # ---- 4.3 workflows ----
    wf_files = sorted(p.name for p in WF.glob("*.yml"))
    wf_report = {"activos_necesarios": [], "candidatos_archive": [], "archive_dir_existente": (WF / "_archive").exists()}
    for f in wf_files:
        if f in ACTIVE_WF:
            wf_report["activos_necesarios"].append({"file": f, "rol": ACTIVE_WF[f]})
        else:
            last = LAST_RUN.get(f, ("?", "?"))
            wf_report["candidatos_archive"].append({
                "file": f, "ultima_corrida": last[0], "conclusion": last[1],
                "razon": "one-shot probe/reproc de sesion cerrada; sin corridas desde su sesion",
            })

    # ---- 4.4 profiles ----
    tests_dir = REPO / "tests"
    prof_files = sorted(p.name for p in PROF.glob("*.yaml"))
    test_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                          for p in tests_dir.rglob("*.py"))
    active_wf_text = "\n".join((WF / f).read_text(encoding="utf-8", errors="ignore")
                               for f in ACTIVE_WF)
    prof_report = {"operacionales": [], "c2ab_quedarse": [], "baseline_s81": [],
                   "referenciados_por_tests": [], "huerfanos_candidatos_archive": []}
    for f in prof_files:
        stem = f[:-5]
        in_tests = stem in test_text
        in_active_wf = stem in active_wf_text
        entry = {"file": f, "en_tests": in_tests, "en_workflows_activos": in_active_wf}
        if f in ("mirova_equivalent.yaml", "experimental.yaml"):
            prof_report["operacionales"].append(entry)
        elif stem.startswith("_c2ab_"):
            entry["razon"] = "reproducibilidad flip S118 C2 (quedan por decision de tarea)"
            prof_report["c2ab_quedarse"].append(entry)
        elif "_f_s81_" in stem:
            entry["razon"] = ("baseline A/B S81 gates intra-radio; experimento cerrado "
                              "(S118 flip OFF). Candidato archive"
                              + (" PERO referenciado por tests — mover requiere tocar tests" if in_tests else ""))
            prof_report["baseline_s81"].append(entry)
        elif in_tests:
            entry["razon"] = "profile A/B historico PERO cargado por la suite de tests — NO archivar sin refactor de tests"
            prof_report["referenciados_por_tests"].append(entry)
        else:
            entry["razon"] = "A/B/probe historico sin referencias en tests ni workflows activos"
            prof_report["huerfanos_candidatos_archive"].append(entry)

    report = {"workflows": wf_report, "profiles": prof_report,
              "resumen": {
                  "wf_total": len(wf_files),
                  "wf_activos": len(wf_report["activos_necesarios"]),
                  "wf_candidatos_archive": len(wf_report["candidatos_archive"]),
                  "prof_total": len(prof_files),
                  "prof_operacionales": len(prof_report["operacionales"]),
                  "prof_c2ab": len(prof_report["c2ab_quedarse"]),
                  "prof_s81": len(prof_report["baseline_s81"]),
                  "prof_ref_tests": len(prof_report["referenciados_por_tests"]),
                  "prof_huerfanos": len(prof_report["huerfanos_candidatos_archive"]),
              }}
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report["resumen"], indent=2))
    print("huerfanos:", [e["file"] for e in prof_report["huerfanos_candidatos_archive"]])
    print("ref_tests:", [e["file"] for e in prof_report["referenciados_por_tests"]])
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
