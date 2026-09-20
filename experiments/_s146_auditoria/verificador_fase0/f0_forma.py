"""Verificador Fase 0 (solo lectura): forma del diff.
1) cada linea eliminada de los .md debe reaparecer integra dentro de las agregadas del mismo hunk/archivo
2) lineas agregadas: sin guion largo/medio, sin voseo
"""
import subprocess, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
FILES = ["CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md",
         "docs/audit_s139/BORRADOR_CORREO_COPPOLA.md", "experiments/_s145_censo_cierres/censo.py"]
VOSEO = r"\b(vos|ten[eé]s|pod[eé]s|quer[eé]s|sab[eé]s|mir[aá]|toc[aá]|fijate|and[aá]|dale|prob[aá]|eleg[ií]|pon[eé]|busc[aá]|marc[aá]|le[eé]|us[aá]|corr[eé]|verific[aá]|dudás|trabajés|hac[eé]|abr[ií]|revis[aá]|cont[aá]|compar[aá]|pregunt[aá]|record[aá])\b"
for f in FILES:
    d = subprocess.run(["git", "diff", "-U0", "--", f], capture_output=True, text=True, encoding="utf-8").stdout
    minus, plus = [], []
    for l in d.split("\n"):
        if l.startswith("---") or l.startswith("+++"): continue
        if l.startswith("-"): minus.append(l[1:])
        elif l.startswith("+"): plus.append(l[1:])
    allplus = "\n".join(plus)
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    nplus = norm(allplus)
    print(f"##### {f}: -{len(minus)} +{len(plus)}")
    for m in minus:
        if norm(m) and norm(m) not in nplus:
            # buscar mayor prefijo/sufijo
            print("  ELIMINADA SIN REAPARECER INTEGRA:", m[:160])
    for i, p in enumerate(plus):
        if "\u2014" in p or "\u2013" in p:
            print("  GUION LARGO/MEDIO en agregada:", p[:140])
        for mm in re.finditer(VOSEO, p):
            w = mm.group(0)
            if re.search(r"[áéí]$", w) or w in ("vos", "fijate", "dale"):
                print(f"  VOSEO? '{w}':", p[max(0, mm.start()-50):mm.end()+40])
