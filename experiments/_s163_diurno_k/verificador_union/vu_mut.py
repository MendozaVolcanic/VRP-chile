# Mutaciones en una COPIA fuera del worktree (git archive del commit). No toca el repo.
import sys, json, subprocess, pathlib, re
arch=pathlib.Path(sys.argv[1]); worktree=pathlib.Path(sys.argv[2])
M=json.loads((worktree/"experiments/_s163_diurno_k/mutaciones_exclusion.json").read_text(encoding="utf-8"))["mutaciones"]
propias=[
 ("P1","evaluar_con_exclusion.py","filas_x, recs_x = quitar_dias(filas, recs, dias)","filas_x, recs_x = filas, recs","main() no aplica la exclusion"),
 ("P2","evaluar_con_exclusion.py","    dias = list(exc[\"excluir_dias\"])","    dias = []","main() ignora la lista"),
 ("P3","evaluar_con_exclusion.py","    logs = ev.problemas_de_logs(a.raiz, (control, brazo), control)","    logs = []","main() no revisa los logs (I1a)"),
 ("P4","evaluar_con_exclusion.py","    if distintos:\n        print(","    if False:\n        print(","main() no comprueba el sha de la referencia"),
 ("P5","evaluar_con_exclusion.py","ev.evaluar_completo(filas_x, recs_x, control, brazo, a.opcion_e,","ev.evaluar_completo(filas_x, recs_x, control, brazo, 'e-i',","main() fija la opcion e"),
 ("P6","evaluar_con_exclusion.py","[x for x in rs if x[\"dt\"].strftime(\"%Y-%m-%d\") not in dias]","[x for x in rs if x[\"dt\"].strftime(\"%Y-%m-%d\") in dias]","records: filtro invertido"),
 ("P7","evaluar_con_exclusion.py","p.vrp_mw >= 1.0","p.vrp_mw > 1.0","lo_que_sale: frontera de protegida"),
 ("P8","evaluar_con_exclusion.py","str(x[\"fecha_utc\"])[:10] not in dias","str(x[\"fecha_utc\"])[:10] in dias","referencia: filtro invertido"),
 ("P9","evaluar_con_exclusion.py","    ev.imprimir(r[\"principal\"]","    pass; (lambda *a: None)(r[\"principal\"]","main() no imprime el veredicto"),
]
todas=[(m["id"],pathlib.Path(m["archivo"]).name,m["viejo"],m["nuevo"],m["que"]) for m in M]+propias
def correr():
    p=subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider","-x","--tb=line","experiments/_s163_diurno_k/test_evaluar_con_exclusion.py"],cwd=arch,capture_output=True,text=True,timeout=300)
    o=p.stdout+p.stderr
    nf=len(re.findall(r"^FAILED|^ERROR",o,re.M))
    aser="AssertionError" in o or re.search(r"^E\s+assert",o,re.M) is not None or ": assert" in o
    return p.returncode,o,aser
base=correr(); print("linea base rc=%d" % base[0]); 
for id_,nombre,viejo,nuevo,que in todas:
    f=arch/"experiments/_s163_diurno_k"/nombre
    orig=f.read_text(encoding="utf-8")
    if viejo not in orig: print(id_,"SIN DATO: el texto viejo no esta en la copia (LF)",que); continue
    f.write_text(orig.replace(viejo,nuevo,1),encoding="utf-8")
    try: rc,o,aser=correr()
    finally: f.write_text(orig,encoding="utf-8")
    ult=[l for l in o.splitlines() if l.startswith(("FAILED","ERROR","E "))][:2]
    est="NO ATRAPADA (rc=0)" if rc==0 else ("ATRAPADA por asercion" if aser else "CAIDA/otra falla")
    print("%s %s | %s | %s" % (id_,est,que,ult))
