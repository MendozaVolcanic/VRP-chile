"""S146 - tabla unica de brazos de la bateria del Apendice A. La leen el probe, el verificador de
cobertura, el evaluador y el workflow (por `python brazos.py --matriz`), para que no existan dos
listas que puedan divergir (A102).

Cuatro ejes, los mismos de S136 y S137 y con los mismos nombres de carpeta:
  b22            banda 22 primaria, como el paper (D21). Apagado = banda 21, lo de produccion.
  sin_compuerta  quita `bt > t_bg + 3 K` solo dentro de los Tests 2 y 3 (D22).
  fondo_local    fondo de la magnitud por vecinos 3x3, ecuacion 6 (D25). Apagado = anillo 5-25 km.
  prosa          conectiva max(C1, mu+C2*sigma), la de la prosa. Apagado = min, la de la formula.

`commiteado` es la carpeta con la salida de ese brazo que S136 o S137 dejaron en el repo (None si el
brazo nunca se corrio). Sirve solo para el control de identidad Cpx-d.

El noveno brazo es el que `docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md` seccion 5 senala como
nunca corrido: B22 + fondo local CON compuerta y con la conectiva de hoy (min).

El decimo (`por_defecto: False`) NO corre salvo que se lo nombre en el input `brazos`. Esta en la
tabla porque el brazo que da 9 de 9 usa `max`, y atribuir ESE resultado a la compuerta o al fondo
pide el par con `max`; el noveno, que es `min`, atribuye el 8 de 9 del septimo. Dejarlo definido
cuesta una linea; correrlo es decision de quien despacha.
"""
import json
import sys

CONTROL = "out_apendice"

BRAZOS = [
    # nombre (carpeta),                                  etiqueta,                b22,  sinBT, loc,   prosa, commiteado
    ("out_apendice",                                     "B21 min (produccion)",  0, 0, 0, 0, "experiments/_s136/out_apendice"),
    ("out_apendice_prosa",                               "B21 max (prosa)",       0, 0, 0, 1, "experiments/_s136/out_apendice_prosa"),
    ("out_apendice_b22",                                 "B22 min",               1, 0, 0, 0, "experiments/_s137/out_apendice_b22"),
    ("out_apendice_b22_prosa",                           "B22 max",               1, 0, 0, 1, "experiments/_s137/out_apendice_b22_prosa"),
    ("out_apendice_b22_sincompuerta",                    "B22 sinBT min",         1, 1, 0, 0, "experiments/_s137/out_apendice_b22_sincompuerta"),
    ("out_apendice_b22_sincompuerta_prosa",              "B22 sinBT max",         1, 1, 0, 1, "experiments/_s137/out_apendice_b22_sincompuerta_prosa"),
    ("out_apendice_b22_sincompuerta_fondolocal",         "B22 sinBT loc min",     1, 1, 1, 0, "experiments/_s137/out_apendice_b22_sincompuerta_fondolocal"),
    ("out_apendice_b22_sincompuerta_fondolocal_prosa",   "B22 sinBT loc max",     1, 1, 1, 1, "experiments/_s137/out_apendice_b22_sincompuerta_fondolocal_prosa"),
    ("out_apendice_b22_fondolocal",                      "B22 loc min (nuevo)",   1, 0, 1, 0, None),
    ("out_apendice_b22_fondolocal_prosa",                "B22 loc max (opcional)", 1, 0, 1, 1, None),
]
NO_POR_DEFECTO = {"out_apendice_b22_fondolocal_prosa"}


def como_dicts():
    return [{"nombre": n, "etiqueta": e, "b22": bool(b), "sin_compuerta": bool(s),
             "fondo_local": bool(f), "prosa": bool(p), "commiteado": c,
             "por_defecto": n not in NO_POR_DEFECTO}
            for (n, e, b, s, f, p, c) in BRAZOS]


def por_nombre(nombre):
    for b in como_dicts():
        if b["nombre"] == nombre:
            return b
    raise KeyError(f"brazo desconocido: {nombre!r}. Validos: {[x['nombre'] for x in como_dicts()]}")


def seleccion(texto):
    """Lista de nombres a correr. Vacio = los 9 por defecto. 'todos' = los 10. El control va SIEMPRE,
    porque la cobertura de cada brazo se compara contra el."""
    texto = (texto or "").strip()
    if not texto:
        nombres = [b["nombre"] for b in como_dicts() if b["por_defecto"]]
    elif texto.lower() == "todos":
        nombres = [b["nombre"] for b in como_dicts()]
    else:
        nombres = [t.strip() for t in texto.split(",") if t.strip()]
        for n in nombres:
            por_nombre(n)
    if CONTROL not in nombres:
        nombres.insert(0, CONTROL)
    return nombres


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--matriz":
        print(json.dumps(seleccion(sys.argv[2] if len(sys.argv) > 2 else "")))
    else:
        for b in como_dicts():
            print(b)
