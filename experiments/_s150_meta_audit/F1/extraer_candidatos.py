"""F1 S150 meta-auditoria: extrae lineas candidatas a recomendacion de los informes de auditoria.

Pregunta 1 del instrumento: si una recomendacion existe pero no usa ninguna palabra clave,
este script NO la ve. Es un piso, no un censo completo. Se complementa con lectura de las
secciones de cierre ("Recomendaciones", "Acciones", "Pendientes", "Proximos pasos").
Pregunta 2: control positivo = una recomendacion conocida debe salir (AUDIT_S146 Fase 3).
"""
import re, glob, os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
os.chdir(ROOT)
files = sorted(glob.glob("docs/AUDIT_S*.md"))
for d in ["docs/audit_s138","docs/audit_s139","docs/audit_s141","docs/audit_s142","docs/audit_s143",
          "docs/audit_s145","docs/audit_s146","docs/audit_s147","docs/audit_s148","docs/audit_s149","docs/audit_s150"]:
    files += sorted(glob.glob(d+"/**/*.md", recursive=True))
PAT = re.compile(r"(recomend|recommend|acci[oó]n(es)? derivad|pendiente|pr[oó]xim[oa]s? paso|siguiente paso|"
                 r"queda(n)? abiert|propuesta|propong|propone|sugerenc|\bTODO\b|backlog|follow-?up|"
                 r"a futuro|por hacer|next step|deber[ií]a(mos)? (correr|medir|agregar|probar|hacer)|"
                 r"hay que (medir|correr|probar|agregar|revisar)|queda por|falta (medir|correr|probar)|"
                 r"vigente|S\d{2,3}\+)", re.I)
HEAD = re.compile(r"^#{1,4} .*(recomend|acci|pendient|pr[oó]xim|propuest|abiert|siguient|qu[eé] hacer|decisi)", re.I)
out=[]; nfile={}
for f in files:
    lines=open(f,encoding='utf-8',errors='replace').read().splitlines()
    n=0
    for i,l in enumerate(lines,1):
        if PAT.search(l) or HEAD.search(l):
            out.append({"file":f,"line":i,"text":l.strip()[:400],"is_head":bool(HEAD.search(l))}); n+=1
    nfile[f]=(len(lines),n)
json.dump(out,open("experiments/_s150_meta_audit/F1/candidatos.json","w",encoding="utf-8"),ensure_ascii=False,indent=0)
print("archivos:",len(files),"lineas candidatas:",len(out),"encabezados:",sum(o['is_head'] for o in out))
for f,(L,n) in nfile.items(): print(f"{n:4d}/{L:5d} {f}")
# control positivo
print("CONTROL S146:", [o['line'] for o in out if o['file']=='docs/AUDIT_S146.md' and o['is_head']][:20])
