"""Arma INFORME.md: el texto (informe_texto.md) con las tablas generadas por script (tabla_informe.md y
area_umbral_salida.txt), sin transcribir números a mano."""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
texto = (AQUI / "informe_texto.md").read_text(encoding="utf-8")
tablas = (AQUI / "tabla_informe.md").read_text(encoding="utf-8")
area = "\n".join(l for l in (AQUI / "area_umbral_salida.txt").read_text(encoding="utf-8").splitlines()
                 if l.startswith("|"))
out = texto.replace("{{TABLAS}}", tablas.strip()).replace("{{AREA}}", area)
assert "{{" not in out
with open(AQUI / "INFORME.md", "w", encoding="utf-8", newline="") as fh:
    fh.write(out)
print("INFORME.md escrito,", len(out.splitlines()), "líneas")
