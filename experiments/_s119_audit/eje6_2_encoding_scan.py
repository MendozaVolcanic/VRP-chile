# S119 audit Eje 6.2 — scan cp1252: prints con Unicode sin wrapper TextIOWrapper/reconfigure
import sys, io, json, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "eje6_2_encoding_scan.json")

targets = sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py"))) + \
          sorted(glob.glob(os.path.join(ROOT, "experiments", "_s118_c2ab", "*.py")))

WRAPPER_RE = re.compile(r"TextIOWrapper|reconfigure\(|PYTHONIOENCODING")
PRINT_RE = re.compile(r"\bprint\s*\(|sys\.stdout\.write|logging\.|logger\.")

def non_ascii(s):
    return [ch for ch in s if ord(ch) > 127]

offenders = []
scanned = []
for path in targets:
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    src = "".join(lines)
    has_wrapper = bool(WRAPPER_RE.search(src))
    file_hits = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # solo lineas que IMPRIMEN (print/write/logging), no comentarios ni docstrings sueltos
        if not PRINT_RE.search(stripped):
            continue
        if stripped.startswith("#"):
            continue
        chars = non_ascii(line)
        if chars:
            file_hits.append({"line": i, "chars": sorted(set(chars)),
                              "snippet": stripped[:100]})
    scanned.append({"file": rel, "has_wrapper": has_wrapper, "n_unicode_prints": len(file_hits)})
    if file_hits and not has_wrapper:
        offenders.append({"file": rel, "hits": file_hits})

result = {"n_scanned": len(targets), "offenders": offenders, "scanned": scanned}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Escaneados: {len(targets)} archivos")
print(f"Ofensores (prints Unicode SIN wrapper): {len(offenders)}")
for o in offenders:
    for h in o["hits"]:
        print(f"  {o['file']}:{h['line']}  chars={''.join(h['chars'])}  | {h['snippet'][:70]}")
print(f"OK -> {OUT}")
