import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from juntar import resumen_total
out = resumen_total(HERE / "artefactos")
(Path(__file__).parent / "criterio_total_reproducido.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
orig = json.loads((HERE / "criterio_total.json").read_text(encoding="utf-8"))
print("identico_objeto:", out == orig)
a = json.dumps(out, indent=1, ensure_ascii=False); b = (HERE / "criterio_total.json").read_text(encoding="utf-8")
print("identico_texto:", a == b)
for k, v in out["criterio"].items():
    print(k, v["veredicto"], v["control"])
