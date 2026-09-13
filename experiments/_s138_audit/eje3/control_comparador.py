"""S138 eje 3 - control positivo y negativo del comparador de brazos (instrumento 5).

Pregunta 1: si un brazo estuviera roto (todo FP o todo FN), el comparador lo veria? -> JSON 0/9.
Pregunta 2: si el instrumento estuviera muerto, se veria distinto? -> JSON 9/9 debe dar CUMPLE
            y 0/9 debe dar 'no cumple'; un directorio vacio debe salir 'ausente', no 0/9.
Escribe solo en un directorio temporal bajo experiments/_s138_audit/eje3/tmp_comparador/.
"""
import json, subprocess, sys, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
TMP = HERE / "tmp_comparador"
CASOS = [("A1","Bezymianny","detecta"),("A2","Eyjafjallajokull","detecta"),("A3","ErtaAle","detecta"),
         ("A4","Dubbi","no_detecta"),("A5","Ubinas","detecta"),("A7","Tolbachik","no_detecta"),
         ("A8","Etna","detecta"),("A9","Stromboli","no_detecta"),("A6","Villarrica","detecta")]
def arma(d, modo):
    out=[]
    for c,n,v in CASOS:
        if modo=="todo_ok": r="CONFORME"
        elif modo=="todo_mal": r="NO CONFORME (falso negativo)" if v=="detecta" else "NO CONFORME (falso positivo)"
        elif modo=="todo_indet": r="INDETERMINADO"
        out.append({"caso":c,"name":n,"fecha":"x","veredicto_paper":v,"resultado":r,"detalle":"","pasadas":[]})
    (d/"resultado_apendice.json").write_text(json.dumps(out),encoding="utf-8")
if TMP.exists(): shutil.rmtree(TMP)
for sub,modo in [("out_apendice","todo_ok"),("out_apendice_prosa","todo_mal"),("out_apendice_b22","todo_indet")]:
    d=TMP/sub; d.mkdir(parents=True); arma(d,modo)
(TMP/"out_apendice_b22_prosa").mkdir()  # directorio sin JSON: debe salir 'ausente'
r=subprocess.run([sys.executable,str(RAIZ/"experiments/_s137/comparar_brazos_apendice.py"),str(TMP)],
                 capture_output=True,text=True,env={**__import__("os").environ,"PYTHONIOENCODING":"utf-8"})
print(r.stdout); print(r.stderr[-500:])
