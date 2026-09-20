# -*- coding: utf-8 -*-
"""Vuelca TODOS los atributos publicos de pipeline.profile por perfil y los compara contra
mirova_equivalent. Sirve para probar que cada brazo del A/B difiere del perfil de produccion
exactamente en lo que el pre-registro declara y en nada mas.

(1) Si lo que mide estuviera roto, fallaria? Si: el control es el propio perfil de produccion
    comparado consigo mismo, que debe dar CERO diferencias. Si el volcado perdiera atributos o
    los comparara mal, esa fila daria distinto de cero y se veria.
(2) Si el instrumento estuviera muerto (por ejemplo, si leyera siempre el mismo perfil), se
    veria distinto? Si: un brazo con una diferencia declarada tiene que mostrarla; si todas las
    filas dieran cero, el instrumento no esta leyendo los perfiles.

Cada perfil se carga en un subproceso propio porque pipeline.profile lee VRP_PROFILE una sola
vez, al importarse.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "mirova_equivalent"
BRAZOS = ["_s146_ab_control", "_s146_ab_sin_test1", "_s146_ab_sin_prioridad_debil"]
# Lo que cada brazo TIENE derecho a cambiar. Todo lo demas es un hallazgo.
DECLARADO = {
    "_s146_ab_control": set(),
    "_s146_ab_sin_test1": {"ENABLE_TEST1_PATH"},
    "_s146_ab_sin_prioridad_debil": {"ENABLE_TEST1_PRIORITY_WEAK_CLUSTER"},
}
# Atributos de identidad del perfil: cambian por construccion en todos los brazos.
IDENTIDAD = {"PROFILE_NAME", "DATA_SUBDIR"}

VOLCADO = r"""
import json, pipeline.profile as p
out = {}
for k in dir(p):
    if k.startswith("_") or not k.isupper():
        continue
    v = getattr(p, k)
    # Un set se repr-ea en orden arbitrario y cambia entre procesos: se ordena antes de
    # comparar. Sin esto, VALID_PROFILES (el listado del directorio de perfiles) aparece
    # como diferencia en TODAS las filas, incluida la del perfil consigo mismo.
    if isinstance(v, (set, frozenset)):
        v = sorted(v)
    try:
        json.dumps(v)
    except TypeError:
        v = repr(v)
    out[k] = v
print(json.dumps(out, sort_keys=True))
"""


def volcar(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    o = subprocess.run([sys.executable, "-c", VOLCADO], cwd=str(ROOT), env=env,
                       capture_output=True, text=True)
    if o.returncode != 0:
        raise SystemExit("fallo al cargar %s:\n%s" % (perfil, o.stderr[-2000:]))
    return json.loads(o.stdout)


def main():
    base = volcar(BASE)
    print("perfil base %s: %d atributos" % (BASE, len(base)))
    filas, ok = [], True
    for perfil in [BASE] + BRAZOS:
        d = volcar(perfil)
        faltan = sorted(set(base) - set(d))
        sobran = sorted(set(d) - set(base))
        difs = {k: [base[k], d[k]] for k in sorted(set(base) & set(d))
                if base[k] != d[k] and k not in IDENTIDAD}
        esperado = DECLARADO.get(perfil, set())
        inesperadas = sorted(set(difs) - esperado)
        sin_aplicar = sorted(esperado - set(difs))
        # El aislamiento del A/B depende de que cada brazo escriba en su propio directorio
        # (A47: dos procesos sobre el mismo data_subdir corrompen los JSON). Se comprueba
        # aparte porque DATA_SUBDIR esta excluido de la comparacion por ser identidad.
        subdir_aislado = (perfil == BASE) or (d.get("DATA_SUBDIR") == perfil)
        if not subdir_aislado:
            ok = False
        fila = {"perfil": perfil, "n_atributos": len(d), "faltan": faltan, "sobran": sobran,
                "data_subdir": d.get("DATA_SUBDIR"), "subdir_aislado": subdir_aislado,
                "diferencias": difs, "declaradas": sorted(esperado),
                "inesperadas": inesperadas, "declaradas_sin_aplicar": sin_aplicar}
        filas.append(fila)
        estado = ("OK" if not (faltan or sobran or inesperadas or sin_aplicar)
                  and subdir_aislado else "REVISAR")
        if estado == "REVISAR":
            ok = False
        print("\n[%s] %s" % (estado, perfil))
        print("  atributos: %d | faltan: %s | sobran: %s | data_subdir: %s (aislado: %s)"
              % (len(d), faltan or "-", sobran or "-", d.get("DATA_SUBDIR"), subdir_aislado))
        print("  diferencias contra %s (sin contar identidad): %s"
              % (BASE, json.dumps(difs, sort_keys=True) if difs else "ninguna"))
        print("  declaradas: %s | inesperadas: %s | declaradas sin aplicar: %s"
              % (sorted(esperado) or "-", inesperadas or "-", sin_aplicar or "-"))
    salida = Path(__file__).with_name("diff_perfiles.json")
    salida.write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\ncontrol: %s comparado consigo mismo da %d diferencias (tiene que ser 0)"
          % (BASE, len(filas[0]["diferencias"])))
    print("VEREDICTO:", "todos los brazos difieren solo en lo declarado" if ok else "HAY ALGO SIN DECLARAR")
    print("->", salida)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
