"""S112 Parte B (Test1-lowmag) — junta los artifacts del A/B en data/.

Descarga los artifacts s112t1lm-{profile}-{vol}-{chunkstart} de un run de GH Actions y
une los 3 chunks por (profile, vol) en data/{profile}/{vol}.json (union por granule;
chunks disjuntos por fecha → sin conflicto). Luego correr audit_t1lm_ab.py.

Uso: python experiments/_s112_test1_lowmag/gather_ab_artifacts.py <RUN_ID>
Requiere gh CLI autenticado.
"""
import json, io, sys, subprocess, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
PROFILES = [
    "_t1lm_q0_control", "_t1lm_q2_global", "_t1lm_q3_ring24", "_t1lm_q3_ring35",
    "_t1lm_q3_ring15", "_t1lm_q4_te700", "_t1lm_q4_te1000", "_t1lm_q5_ntilocal",
    "_t1lm_q6_spatialcore",
]
PREFIX = "s112t1lm-"


def gather(run_id):
    tmp = Path(tempfile.mkdtemp(prefix="s112t1lm_"))
    print(f"Descargando artifacts del run {run_id} -> {tmp}", flush=True)
    subprocess.run(["gh", "run", "download", str(run_id), "-D", str(tmp)],
                   cwd=str(ROOT), check=True)
    merged = {}  # (profile, vol) -> {granule: record}
    for art_dir in sorted(tmp.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith(PREFIX):
            continue
        rest = art_dir.name[len(PREFIX):]
        prof = next((p for p in PROFILES if rest.startswith(p + "-")), None)
        if prof is None:
            print(f"  ?? no profile match: {art_dir.name}", flush=True); continue
        tail = rest[len(prof) + 1:]
        # chunkstart = YYYY-MM-DD (3 guiones); los volcanes no tienen guion → rsplit 3.
        vol = tail.rsplit("-", 3)[0]
        jf = art_dir / f"{vol}.json"
        if not jf.exists():
            js = list(art_dir.glob("*.json"))
            if not js:
                print(f"  ?? sin json en {art_dir.name}", flush=True); continue
            jf = js[0]
        doc = json.loads(jf.read_text(encoding="utf-8"))
        recs = doc["records"] if isinstance(doc, dict) else doc
        key = (prof, vol)
        merged.setdefault(key, {})
        for r in recs:
            merged[key][r.get("granule")] = r
    for (prof, vol), bygran in merged.items():
        outdir = ROOT / "data" / prof
        outdir.mkdir(parents=True, exist_ok=True)
        records = list(bygran.values())
        (outdir / f"{vol}.json").write_text(
            json.dumps({"volcano": vol, "updated": "s112_t1lm_ab", "records": records},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {prof}/{vol}.json — {len(records)} records", flush=True)
    print("\nListo. Ahora: python experiments/_s112_test1_lowmag/audit_t1lm_ab.py", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gather_ab_artifacts.py <RUN_ID>"); sys.exit(1)
    gather(sys.argv[1])
