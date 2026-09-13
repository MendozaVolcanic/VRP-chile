"""S139 eje 6: que PDF de documentacion/ no aparecen citados en BIBLIOGRAPHY_SYNTHESIS.md
ni en MISSION.md, y cuales son del grupo MIROVA (afiliacion Torino/Firenze/Sapienza en p.1).
Pregunta 1 del instrumento: si el PDF estuviera sintetizado con otro nombre (autor+anio y no
nombre de archivo), este cruce lo marcaria como NO sintetizado (falso positivo): por eso se
buscan tambien apellido del primer autor + anio y DOI. Pregunta 2: si fitz no lee el PDF, sale
'SIN TEXTO', no 'no MIROVA'. Control positivo: sp426.5.pdf DEBE salir sintetizado."""
import re, pathlib, fitz
R=pathlib.Path(__file__).resolve().parents[3]
doc=R/'documentacion'; syn=(doc/'BIBLIOGRAPHY_SYNTHESIS.md').read_text(encoding='utf-8',errors='ignore')
mis=(R/'docs/MISSION.md').read_text(encoding='utf-8',errors='ignore')
base=(syn+mis).lower()
grp=['coppola','laiolo','massimetti','campus','aveni','cigolini']
for p in sorted(doc.glob('*.pdf')):
    try:
        f=fitz.open(p); t=' '.join(f[i].get_text() for i in range(min(2,len(f)))); n=len(f)
    except Exception as e:
        print('SIN TEXTO',p.name,e); continue
    tl=t.lower()
    doi=re.search(r'10\.\d{4,9}/[^\s,;]+',t)
    doi=doi.group(0).rstrip('.').lower() if doi else ''
    autores=[g for g in grp if g in tl]
    unito=('unito' in tl or 'torino' in tl or 'turin' in tl)
    cited = p.name.lower() in base or p.stem.lower() in base or (doi and doi in base)
    title=' '.join(t.split())[:110]
    print(f"{'CIT' if cited else 'NO '} | MIROVA={'SI' if (autores and unito) else ('auth' if autores else 'no')} | pags={n} | {p.name} | doi={doi} | {title}")
