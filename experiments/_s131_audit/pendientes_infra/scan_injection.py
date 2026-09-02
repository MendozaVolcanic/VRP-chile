import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import glob

files = sorted(glob.glob(".github/workflows/*.yml"))
total_risk = 0
per_file = {}
for f in files:
    lines = open(f, encoding="utf-8").readlines()
    in_run = False
    run_indent = None
    risk_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip("\n")
        m = re.match(r"^(\s*)run:\s*\|?\s*$", stripped)
        m_inline = re.match(r"^(\s*)run:\s*(.+)$", stripped)
        if m:
            in_run = True
            run_indent = len(m.group(1))
            continue
        if in_run:
            # a run: block ends when indentation drops to <= run_indent and line non-blank and not deeper
            if stripped.strip() == "":
                continue
            cur_indent = len(line) - len(line.lstrip(" "))
            if cur_indent <= run_indent:
                in_run = False
            else:
                if "github.event.inputs" in stripped:
                    risk_lines.append((i, stripped.strip()))
        # also catch single-line `run: something ${{ github.event.inputs`
        if m_inline and "github.event.inputs" in m_inline.group(2) and not m:
            risk_lines.append((i, stripped.strip()))
    if risk_lines:
        per_file[f] = risk_lines
        total_risk += len(risk_lines)

for f, rl in per_file.items():
    print(f"=== {f} ({len(rl)}) ===")
    for i, txt in rl:
        print(f"  {i}: {txt}")
print()
print("TOTAL workflows con riesgo real (dentro de run:):", len(per_file))
print("TOTAL ocurrencias:", total_risk)
