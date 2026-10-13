"""F4 (meta-auditoria S150): documentos de S147 a S150 que no aparecen en docs/INDEX.md.

Regla que se mide: cabecera de docs/INDEX.md ("al crear un doc nuevo, agregarlo aca").
Preguntas del instrumento:
1. Si un doc nuevo no estuviera indexado, se veria: busco su nombre de archivo (basename) en el
   texto de INDEX.md. Un doc citado con otra ruta o por nombre parcial cuenta como ausente
   (sesgo hacia "ausente"; se declara).
2. Control positivo: AUDIT_S149.md y AUDIT_S150.md SI estan en el indice (l. 21-22); si el
   instrumento los diera por ausentes, estaria muerto.
Denominador: archivos .md bajo docs/ cuyo primer commit es >= 2026-09-20 (inicio de S147, segun
project_s147_estado: PRs #717 en adelante, 2026-09-20/21) mas los no versionados.
"""
import io, os, subprocess, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
idx = open(os.path.join(REPO, "docs/INDEX.md"), encoding="utf-8").read()
out = subprocess.run(["git", "-C", REPO, "log", "--since=2026-09-20", "--diff-filter=A", "--name-only",
                      "--format=", "--", "docs/"], capture_output=True, text=True, encoding="utf-8").stdout
nuevos = sorted({l.strip() for l in out.splitlines() if l.strip().endswith(".md")})
aus, pres = [], []
for f in nuevos:
    if not os.path.exists(os.path.join(REPO, f)):
        continue
    (pres if os.path.basename(f) in idx else aus).append(f)
print("control positivo AUDIT_S149.md en indice:", "AUDIT_S149.md" in idx, "| AUDIT_S150.md:", "AUDIT_S150.md" in idx)
print(f"docs .md agregados desde 2026-09-20 y presentes hoy: {len(pres)+len(aus)}; en INDEX: {len(pres)}; ausentes: {len(aus)}")
for f in aus:
    print("  AUSENTE", f)
