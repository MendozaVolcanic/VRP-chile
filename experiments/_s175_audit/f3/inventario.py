# -*- coding: utf-8 -*-
"""F3 S175: inventario de decisiones de Nicolas desde S160, sacado de la bitacora de loop/activo.
Fuente: git show 06de6876a:tasks/LOOP_OBJETIVOS.md (secciones 5 y 6) y BLOQUE_ARRANQUE_S161..S175 de esa rama.
Criterio: linea que menciona a Nicolas junto a una marca de decision (cita textual «...», 'aprob', 'decid',
'respuesta textual', 'frase', 'pre-autoriz', 'sí a'). Es un PISO: una decision redactada sin nombrar a Nicolas no sale.
Control: debe encontrar D-45 (seccion 5) y la decision de MODIS a la via del 2026-10-31 (S172)."""
import io, re, sys, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REF = "06de6876a"
def show(p):
    return subprocess.run(["git","show",f"{REF}:{p}"],capture_output=True).stdout.decode("utf-8","replace")
MARCA = re.compile(r"«[^»]{6,}»|aprob|decid|respuesta textual|pre-?autoriz|\bS[ií] a\b|frase", re.I)
NIC = re.compile(r"Nicol[aá]s")
filas=[]
lo = show("tasks/LOOP_OBJETIVOS.md").split("\n")
sec=None; ent=None; s160=False
for i,l in enumerate(lo,1):
    if l.startswith("## "): sec=l[:40]
    if l.startswith("### "): ent=l[4:120]
    if not sec or not (sec.startswith("## 5") or sec.startswith("## 6")): continue
    if sec.startswith("## 6") and ent and re.search(r"2026-10-(0\d|1\d|20|21)\b", ent) and "S160" not in ent: continue
    if NIC.search(l) and MARCA.search(l):
        filas.append(dict(fuente=f"LOOP_OBJETIVOS.md:{i}", seccion=sec[:6], entrada=ent, texto=l.strip()[:600],
                          citas=re.findall(r"«([^»]{6,400})»", l)))
for n in range(161,176):
    b = show(f"tasks/BLOQUE_ARRANQUE_S{n}.md").split("\n")
    for i,l in enumerate(b,1):
        if NIC.search(l) and MARCA.search(l):
            filas.append(dict(fuente=f"BLOQUE_ARRANQUE_S{n}.md:{i}", seccion="bloque", entrada=f"S{n}", texto=l.strip()[:600],
                              citas=re.findall(r"«([^»]{6,400})»", l)))
ctrl = dict(d45=any("D-45" in f["texto"] for f in filas), via_modis=any("2026-10-31" in f["texto"] and re.search("v[ií]a|MODIS",f["texto"]) for f in filas))
json.dump(dict(ref=REF, control=ctrl, n=len(filas), filas=filas), open("inventario.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("control", ctrl, "n", len(filas))
# citas unicas
cit={}
for f in filas:
    for c in f["citas"]:
        cit.setdefault(c.strip(),[]).append(f["fuente"])
with open("inventario_citas.md","w",encoding="utf-8") as fh:
    for c,fs in cit.items():
        fh.write(f"- «{c}» :: {fs[0]} (+{len(fs)-1})\n")
print("citas unicas", len(cit))
