"""S146 - cobertura de la bateria: cuenta pasadas por brazo y por caso y FALLA si no es pareja.

POR QUE. En este proyecto un run 100 % verde ya escondio cobertura dispareja (A108: 54 de 54 jobs
verdes y 3 con pasadas de menos por cortes de NASA). Comparar brazos con distinto numero de pasadas
es comparar escenas distintas. Este script corre dentro del workflow, despues de los brazos y antes
del evaluador, y corta el run si la comparacion no es valida.

FALLA (salida 1) si, para algun brazo pedido:
  - falta su salida o su meta.json;
  - algun caso tiene cero pasadas procesadas;
  - algun caso tiene MENOS pasadas que el brazo de control (produccion) de este mismo run;
  - algun caso tiene MENOS pasadas que la linea base commiteada de S136
    (experiments/_s136/out_apendice, 24 pasadas en 9 casos). Esta segunda vara es la que atrapa el
    corte de NASA que le pega a TODOS los brazos por igual, control incluido;
  - el meta.json del brazo registra granulos sin medir o discrepancias de captura.
Tener MAS pasadas que la linea base no es error: se avisa (NASA pudo reprocesar el catalogo).

Uso: python verificar_cobertura.py --brazos '["out_apendice", ...]' [--out DIR] [--caso A2]

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si la cobertura estuviera rota (un brazo con pasadas de menos), fallaria? Si, salida 1 con la
    fila culpable. prueba_local.py le quita una pasada a un brazo sintetico y comprueba el fallo.
(2) Si el instrumento estuviera muerto (no lee nada), se veria distinto? Si: una carpeta ausente o
    vacia es fallo, no "nada que reportar", y la tabla impresa muestra los conteos leidos.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(HERE))
import brazos as B  # noqa: E402

LINEA_BASE = RAIZ / "experiments" / "_s136" / "out_apendice" / "resultado_apendice.json"


def conteos(ruta):
    return {c["caso"]: len(c["pasadas"]) for c in json.loads(Path(ruta).read_text(encoding="utf-8"))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazos", required=True, help="lista JSON de nombres de brazo esperados")
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--caso", default="")
    a = ap.parse_args(argv)
    esperados = json.loads(a.brazos)
    out = Path(a.out)
    base = conteos(LINEA_BASE)
    casos = [a.caso] if a.caso.strip() else sorted(base)
    fallas, avisos, tabla = [], [], {}
    for nom in esperados:
        B.por_nombre(nom)
        f, m = out / nom / "resultado_apendice.json", out / nom / "meta.json"
        if not f.exists() or not m.exists():
            fallas.append(f"{nom}: falta resultado_apendice.json o meta.json")
            continue
        tabla[nom] = conteos(f)
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("intentos_malos"):
            fallas.append(f"{nom}: granulos sin medir {meta['intentos_malos']}")
        if meta.get("captura_discrepancias"):
            fallas.append(f"{nom}: la captura no cuadra {meta['captura_discrepancias']}")
    control = tabla.get(B.CONTROL)
    if control is None:
        fallas.append(f"falta el brazo de control {B.CONTROL}: no hay contra que comparar")
    print("%-52s" % "brazo" + "".join("%-5s" % k for k in casos) + "total")
    print("%-52s" % "(linea base S136 commiteada)" + "".join("%-5d" % base.get(k, 0) for k in casos)
          + str(sum(base.get(k, 0) for k in casos)))
    for nom, t in tabla.items():
        print("%-52s" % nom + "".join("%-5d" % t.get(k, 0) for k in casos) + str(sum(t.get(k, 0) for k in casos)))
        for k in casos:
            n = t.get(k, 0)
            if n == 0:
                fallas.append(f"{nom} {k}: CERO pasadas procesadas")
            if control is not None and n < control.get(k, 0):
                fallas.append(f"{nom} {k}: {n} pasadas, menos que el control ({control.get(k, 0)})")
            if n < base.get(k, 0):
                fallas.append(f"{nom} {k}: {n} pasadas, menos que la linea base de S136 ({base.get(k, 0)})")
            elif n > base.get(k, 0):
                avisos.append(f"{nom} {k}: {n} pasadas, MAS que la linea base ({base.get(k, 0)})")
    for x in avisos:
        print("AVISO:", x)
    if fallas:
        print("\nCOBERTURA NO PAREJA, el run NO sirve para comparar brazos:")
        for x in fallas:
            print("  -", x)
        return 1
    print("\ncobertura pareja: todos los brazos con al menos las pasadas del control y de la linea base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
