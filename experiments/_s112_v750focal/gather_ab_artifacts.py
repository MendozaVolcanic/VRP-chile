"""S112 focal V750 — junta los artifacts del A/B en data/.

Descarga s112v750-{profile}-{vol}-{chunkstart} de un run y une los 2 chunks por
(profile, vol) en data/{profile}/{vol}.json (union por granule). Luego audit_v750focal_ab.py.

Uso: python experiments/_s112_v750focal/gather_ab_artifacts.py <RUN_ID>
"""
import json, io, sys, subprocess, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
PROFILES = ["_v750focal_base", "_v750focal_on"]
PREFIX = "s112v750-"


def gather(run_id):
    tmp = Path(tempfile.mkdtemp(prefix="s112v750_"))
    print(f"Descargando artifacts del run {run_id} -> {tmp}", flush=True)
    subprocess.run(["gh", "run", "download", str(run_id), "-D", str(tmp)],
                   cwd=str(ROOT), check=True)
    merged = {}
    for art_dir in sorted(tmp.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith(PREFIX):
            continue
        rest = art_dir.name[len(PREFIX):]
        prof = next((p for p in PROFILES if rest.startswith(p + "-")), None)
        if prof is None:
            print(f"  ?? no profile: {art_dir.name}", flush=True); continue
        vol = rest[len(prof) + 1:].rsplit("-", 3)[0]
        jf = art_dir / f"{vol}.json"
        if not jf.exists():
            js = list(art_dir.glob("*.json"))
            if not js:
                continue
            jf = js[0]
        doc = json.loads(jf.read_text(encoding="utf-8"))
        recs = doc["records"] if isinstance(doc, dict) else doc
        merged.setdefault((prof, vol), {})
        for r in recs:
            merged[(prof, vol)][r.get("granule")] = r
    for (prof, vol), bygran in merged.items():
        outdir = ROOT / "data" / prof
        outdir.mkdir(parents=True, exist_ok=True)
        records = list(bygran.values())
        (outdir / f"{vol}.json").write_text(
            json.dumps({"volcano": vol, "updated": "s112_v750focal_ab", "records": records},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {prof}/{vol}.json — {len(records)} records", flush=True)
    print("\nListo. Ahora: python experiments/_s112_v750focal/audit_v750focal_ab.py", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gather_ab_artifacts.py <RUN_ID>"); sys.exit(1)
    gather(sys.argv[1])
