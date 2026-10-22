"""Arma la LISTA.md de un verificador desde el hallazgos.csv de su auditor (gravedad 3 o más, y extras por ID).

Uso: python armar_lista.py <frente> <carpeta_verificador> [ID_EXTRA ...]
"""
import csv, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
frente, verif, extras = sys.argv[1], sys.argv[2], set(sys.argv[3:])
rows = list(csv.DictReader(open(BASE / frente / "hallazgos.csv", encoding="utf-8")))
def grav(r):
    g = (r.get("gravedad") or "").strip()
    return int(g) if g.isdigit() else 0
sel = [r for r in rows if grav(r) >= 3 or r["id"].strip() in extras]
informe = BASE / frente / "INFORME.md"
out = [f"# Lista que verificas (de {frente.upper()}: {len(sel)} de {len(rows)} hallazgos; gravedad 3 o más"
       + (f", más {sorted(extras)}" if extras else "") + ")", "",
       f"Sólo título, ubicación, gravedad y comando del auditor. No abras {informe}; sí puedes correr sus scripts "
       f"(están en {BASE / frente}).", ""]
for r in sel:
    out += [f"## {r['id']} (gravedad {r['gravedad']}, {r['confianza']})",
            f"- TÍTULO: {r['titulo']}", f"- UBICACIÓN: {r['archivo_linea']}",
            f"- COMANDO DEL AUDITOR: {r['comando_reproduccion']}", f"- SALIDA CRUDA: {r['salida_cruda']}", ""]
(BASE / verif / "LISTA.md").write_text("\n".join(out), encoding="utf-8")
print(verif, len(sel), "de", len(rows))
