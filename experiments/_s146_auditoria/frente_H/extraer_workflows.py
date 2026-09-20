# Frente H S146: extrae de cada workflow de A/B o probe la ventana, volcanes, perfiles y sensores
# que declara, mas la fecha del primer commit. Solo lee. Salida: workflows_ab.json
import re, json, subprocess, glob, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORTE = "2026-08-28"
out = []
files = sorted(glob.glob(".github/workflows/_archive/*.yml")) + sorted(
    f for f in glob.glob(".github/workflows/*.yml")
    if re.search(r"(reproc|probe)", os.path.basename(f)))
for f in files:
    txt = open(f, encoding="utf-8", errors="replace").read()
    fechas = sorted(set(re.findall(r"20(?:25|26)-\d{2}-\d{2}", txt)))
    perfiles = sorted(set(re.findall(r"(?:profile|VRP_PROFILE)[^\n]*?([_a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+)", txt)))
    vols = sorted(set(re.findall(r"\b(Lascar|Lastarria|Isluga|Villarrica|Llaima|Copahue|Chaiten|Tupungatito|PlanchonPeteroa|Planchon-Peteroa|PuyehueCordonCaulle|NevadosDeChillan)\b", txt)))
    sens = sorted(set(re.findall(r"\b(modis|viirs375|viirs750|viirs|MODIS|VIIRS)\b", txt)))
    try:
        log = subprocess.run(["git","log","--diff-filter=A","--follow","--format=%ad %h","--date=short","--",f],
                             capture_output=True,text=True).stdout.strip().splitlines()
        alta = log[-1] if log else "SIN DATO"
    except Exception as e:
        alta = "ERR"
    fd = [x for x in fechas]
    rel = "SIN FECHAS"
    if fd:
        rel = "ANTERIOR" if max(fd) < CORTE else ("POSTERIOR" if min(fd) >= CORTE else "CRUZA")
    out.append(dict(archivo=f.replace("\\","/"), alta=alta, fechas_en_yml=fd, rel_535_segun_yml=rel,
                    volcanes=vols, perfiles=perfiles[:12], sensores=sens))
json.dump(out, open("experiments/_s146_auditoria/frente_H/workflows_ab.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
for o in out:
    print(os.path.basename(o["archivo"]), "|", o["alta"], "|", o["fechas_en_yml"][:1], o["fechas_en_yml"][-1:], o["rel_535_segun_yml"], "|", len(o["volcanes"]), "vols |", ",".join(o["sensores"]))
