"""S97 — Ensamblar el snapshot de staging del refresh operacional.

Combina, por volcán Tier A:
  - MODIS  de data/_s94_reproc_modis  (Jan29–May29, post-#297, reusado)
  - VIIRS  de data/_s97_refresh_viirs  (reproc S97 rango completo, código actual)
deduplicando por (datetime_utc, sensor) → escribe data/_s97_refresh/<vol>.json.

NO toca operacional. La promoción a data/mirova_equivalent es otro paso (promote_*.py)
con tag defensivo + OK Nicolás (A45).

Integridad §0.5: resumen a archivo, números desde el script.
Uso: python assemble_staging.py
"""
import os, io, sys, json
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_fd = os.dup(1)
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

MODIS_DIR = os.path.join(REPO, "data/_s94_reproc_modis")
# VIIRS reproc S97: feb en _s97_refresh_viirs (chunk 1) + mar/apr/may en dirs aislados
# (paralelizados). Se unen todos por (datetime_utc, sensor).
VIIRS_DIRS = [os.path.join(REPO, d) for d in (
    "data/_s97_refresh_viirs",       # feb (chunk 1)
    "data/_s97_refresh_viirs_mar",
    "data/_s97_refresh_viirs_apr",
    "data/_s97_refresh_viirs_may",
)]
DEST_DIR = os.path.join(REPO, "data/_s97_refresh")
TIER = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
        "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]


def load(p):
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


os.makedirs(DEST_DIR, exist_ok=True)
OUT.write("=" * 90 + "\n")
OUT.write("S97 — ensamblar staging (MODIS _s94_reproc_modis + VIIRS _s97_refresh_viirs)\n")
OUT.write("=" * 90 + "\n")
OUT.write(f"{'Volcán':<22}{'MODIS':>7}{'VIIRS':>7}{'merged':>8}{'mrange':>24}{'vrange':>24}\n")
OUT.write("-" * 90 + "\n")
for vol in TIER:
    md = load(os.path.join(MODIS_DIR, f"{vol}.json"))
    mrecs = (md.get("records", []) if isinstance(md, dict) else (md or [])) if md else []
    vrecs = []
    venv = None
    for vdir in VIIRS_DIRS:
        vd = load(os.path.join(vdir, f"{vol}.json"))
        if vd is None:
            continue
        vrecs += (vd.get("records", []) if isinstance(vd, dict) else (vd or []))
        if venv is None and isinstance(vd, dict):
            venv = vd
    by_key = {}
    for r in mrecs:
        by_key[(r.get("datetime_utc"), r.get("sensor"))] = r
    for r in vrecs:
        by_key[(r.get("datetime_utc"), r.get("sensor"))] = r
    merged = sorted(by_key.values(), key=lambda r: (r.get("datetime_utc", ""), str(r.get("sensor", ""))))
    env = md if isinstance(md, dict) else (venv or {})
    out = {"volcano": env.get("volcano", vol), "updated": env.get("updated"), "records": merged}
    with open(os.path.join(DEST_DIR, f"{vol}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    def rng(recs):
        ds = sorted(r.get("datetime_utc", "")[:10] for r in recs if r.get("datetime_utc"))
        return f"{ds[0]}..{ds[-1]}" if ds else "-"
    OUT.write(f"{vol:<22}{len(mrecs):>7}{len(vrecs):>7}{len(merged):>8}{rng(mrecs):>24}{rng(vrecs):>24}\n")
OUT.write("-" * 90 + "\n")
OUT.write(f"Escrito a {os.path.relpath(DEST_DIR, REPO)}/\n")
OUT.flush()
