"""S111 D11 — junta los artifacts del A/B (run reproc-s111-d11-ab) en data/.

Descarga los artifacts s111d11-{arm}-{vol}-{chunk} de un run de GH Actions y une
los 2 chunks por (arm, vol) en data/_d11_modis_{arm}/{vol}.json (union por granule;
chunks disjuntos por fecha → sin conflicto). Luego correr audit_d11_ab.py.

Uso: python gather_ab_artifacts.py <RUN_ID>
Requiere gh CLI autenticado.
"""
import json, io, sys, subprocess, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
ARMS = ["_d11_modis_nogate", "_d11_modis_gated"]


def gather(run_id):
    tmp = Path(tempfile.mkdtemp(prefix="d11ab_"))
    print(f"Descargando artifacts del run {run_id} → {tmp}", flush=True)
    subprocess.run(["gh", "run", "download", str(run_id), "-D", str(tmp)],
                   cwd=str(ROOT), check=True)
    # estructura: tmp/<artifact_name>/<vol>.json
    merged = {}  # (arm, vol) -> {granule: record}
    for art_dir in sorted(tmp.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith("s111d11-"):
            continue
        # s111d11-{arm}-{vol}-{chunkstart}; arm puede tener guiones → parse por ARMS
        rest = art_dir.name[len("s111d11-"):]
        arm = next((a for a in ARMS if rest.startswith(a + "-")), None)
        if arm is None:
            print(f"  ?? no arm match: {art_dir.name}", flush=True); continue
        tail = rest[len(arm) + 1:]
        vol = tail.rsplit("-", 1)[0]  # quita chunkstart (YYYY-MM-DD → último -)
        # chunkstart es 2026-01-29 (3 guiones); vol no tiene guiones → rsplit 3 veces
        vol = tail.rsplit("-", 3)[0]
        jf = art_dir / f"{vol}.json"
        if not jf.exists():
            # fallback: cualquier .json
            js = list(art_dir.glob("*.json"))
            if not js:
                print(f"  ?? sin json en {art_dir.name}", flush=True); continue
            jf = js[0]
        doc = json.loads(jf.read_text(encoding="utf-8"))
        recs = doc["records"] if isinstance(doc, dict) else doc
        key = (arm, vol)
        merged.setdefault(key, {})
        for r in recs:
            merged[key][r.get("granule")] = r
    # escribir data/_d11_modis_{arm}/{vol}.json
    for (arm, vol), bygran in merged.items():
        outdir = ROOT / "data" / arm
        outdir.mkdir(parents=True, exist_ok=True)
        records = list(bygran.values())
        (outdir / f"{vol}.json").write_text(
            json.dumps({"volcano": vol, "updated": "d11_ab", "records": records},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {arm}/{vol}.json — {len(records)} records", flush=True)
    print("\nListo. Ahora: python experiments/_s111_d11/audit_d11_ab.py", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gather_ab_artifacts.py <RUN_ID>"); sys.exit(1)
    gather(sys.argv[1])
