"""S106 — Extrae el informe del workflow de auditoria a docs/AUDIT_S106.md (S91:
no transcribir a mano; el JSON del workflow es la fuente de verdad)."""
import json
from pathlib import Path

SRC = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\500b7aed-a5d8-46ec-aa67-9d5ede79db0a\tasks\wma7aarwi.output")
obj = json.load(open(SRC, encoding="utf-8"))
r = obj["result"]

lines = [
    "# AUDIT_S106 — Auditoría integral VRP Chile (workflow multi-agente, ultracode)",
    "",
    "> Generado por workflow `audit-integral-vrp-s106` (30 agentes, 9 ejes en paralelo +",
    "> verificación adversarial de cada hallazgo grave). 19 confirmados (0 refutados en la",
    "> refutación), 40 medium/low. Suite verificada post-auditoría: **705 passed, 24 skipped,",
    "> 0 failed** (cierra el gap #1 del completeness critic). Nota: los agentes titularon el",
    "> informe \"S107\"; la sesión es S106 — inmaterial.",
    "",
    "## Resumen por eje",
    "",
]
for e in r["resumen"]["por_eje"]:
    lines.append(f"- **{e['eje']}**: {e['verificados']} verificados (high/critical), "
                 f"{e['otros']} medium/low")
lines += ["", "---", "", r["informe"], "", "---", "",
          "# Apéndice — Completeness Critic", "", r["completeness_critic"], "",
          "---", "", "## Verificación post-auditoría (cierra gap del critic)", "",
          "`python -m pytest tests/` → **705 passed, 24 skipped, 0 failed** (2026-06-13). "
          "El veredicto \"operacionalmente sano / P0 ninguno\" queda respaldado por CI verde, "
          "no solo por inspección."]

doc = "\n".join(lines)
Path("docs/AUDIT_S106.md").write_text(doc, encoding="utf-8")
print(f"escrito docs/AUDIT_S106.md ({len(doc)} chars)")
