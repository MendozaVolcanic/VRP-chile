# -*- coding: utf-8 -*-
"""S196: el record de una misma pasada sintética, con el código de ANTES (tag pre-s196-laboratorio-piso) y el de
DESPUÉS (este árbol), byte a byte, en los perfiles de producción y de la guardia K, y en los brazos del barrido del
piso que tienen que ser producción.

POR QUÉ. Las pruebas de CI comparan perfiles dentro de un mismo árbol (tests/test_laboratorio_piso_s196.py Q1):
prueban que el brazo sin zona y el control son producción, pero no que producción sea la misma que antes del cambio.
El CI no tiene el tag (checkout de profundidad 1), así que esto se corre en local y su salida queda en
salida_identidad.txt. Molde: experiments/_s195_lab_paso3/identidad_antes_despues.py.

QUÉ COMPARA, en las escenas calor, debil y quieta (la quieta es la nueva del S196: fondo parejo, manda el piso):
  1. Cada perfil operacional (producción, laboratorio, guardia K de MODIS y de VIIRS, sombra de los 34), antes contra
     después. Los dos de la guardia K no leen el gránulo falso por los lectores de la vía y dan error: el error tiene
     que ser el mismo antes y después. Por eso además se compara, antes contra después, cada constante que
     pipeline.profile resuelve para cada perfil operacional (profile.py es uno de los dos archivos del pipeline que
     cambian): es lo que la guardia K lee del cambio.
  2. El brazo sin zona y el control (sólo existen después) contra producción de antes.
  3. El brazo (s = 3,0; piso 0,003) contra el brazo s = 3,0 del barrido S195 de antes, y los brazos S195 s = 5,0, 3,0
     y 1,0 antes contra después. OJO: desde este cambio los brazos con s < 5 guardan u_ntiA y u_etiA en diag_s1 cuando
     difieren de u_nti2 y u_eti2 (el umbral de la zona, para que una medición posterior vea el que se usó). Esos dos
     campos son nuevos y pueden faltar antes: se informa la comparación entera y, aparte, la misma sin esas dos claves.
     «IGUAL SIN u_A» quiere decir que la detección, el VRP y todo lo demás del record son los de antes.

Uso: python experiments/_s196_lab_piso/identidad_antes_despues.py <carpeta_temporal>
Sale con 0 si nada de producción, la guardia K ni el control difiere; 1 si algo difiere.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
TAG = "pre-s196-laboratorio-piso"
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
ESCENAS = ("calor", "debil", "quieta")
PERFILES = ("mirova_equivalent", "laboratorio", "guardia_k_modis", "guardia_k_viirs", "sombra_34")
OPERACIONALES = PERFILES + ("experimental",)
S195 = ("_s195_lab_s50", "_s195_lab_s30", "_s195_lab_s10")
CLAVES_U_A = ("u_ntiA", "u_etiA")
ENVOLTORIO = r'''
import json, sys, traceback
sys.path.insert(0, "tests")
import _pasada_sintetica_laboratorio as S
out = {}
for f in ("MODIS", "VIIRS750", "VIIRS375"):
    try:
        out[f] = S.correr(f, sys.argv[1])
    except Exception as e:
        out[f] = {"ERROR": type(e).__name__ + ": " + str(e)[:200]}
print("@@" + json.dumps(out, default=float, sort_keys=True))
'''
# La raíz del árbol se reemplaza por <RAIZ>: PROFILES_DIR es la ruta de la carpeta de perfiles y difiere entre la copia
# del tag y el worktree sin que cambie nada de lo que lee el pipeline (S196: la primera corrida dio 6 «distintos» por
# esa sola constante). No se excluye ninguna constante.
CONSTANTES = ("import json, os, pipeline.profile as p; r = os.getcwd().replace(chr(92), '/'); "
              "print('@@' + json.dumps({k: repr(getattr(p, k)).replace(chr(92) * 2, '/').replace(chr(92), '/')"
              ".replace(r, '<RAIZ>') for k in dir(p) if k.isupper() and k != 'VALID_PROFILES'}))")


def _sub(arbol: Path, perfil: str, args: list) -> dict:
    r = subprocess.run([sys.executable, *args], cwd=arbol, capture_output=True, text=True,
                       env=dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8"), timeout=900)
    lineas = [l for l in r.stdout.splitlines() if l.startswith("@@")]
    if r.returncode != 0 or not lineas:
        return {"PROCESO": f"rc={r.returncode} {r.stderr[-300:]}"}
    return json.loads(lineas[-1][2:])


_CACHE: dict = {}


def correr(arbol: Path, perfil: str, escena: str) -> dict:
    clave = (str(arbol), perfil, escena)
    if clave not in _CACHE:
        _CACHE[clave] = _sub(arbol, perfil, ["-c", ENVOLTORIO, escena])
    return _CACHE[clave]


def sin_u_a(x):
    if isinstance(x, dict):
        return {k: sin_u_a(v) for k, v in x.items() if k not in CLAVES_U_A}
    if isinstance(x, list):
        return [sin_u_a(v) for v in x]
    return x


def _b(x) -> str:
    return json.dumps(x, sort_keys=True, default=float)


def main() -> int:
    tmp = Path(sys.argv[1])
    antes = tmp / "arbol_antes"
    if antes.exists():
        shutil.rmtree(antes)
    antes.mkdir(parents=True)
    tar = tmp / "antes.tar"
    subprocess.run(["git", "archive", "-o", str(tar), TAG, "pipeline", "scripts", "volcanoes.yaml"], cwd=RAIZ,
                   check=True)
    with tarfile.open(tar) as t:
        t.extractall(antes, filter="data")
    (antes / "tests").mkdir()
    # la pasada sintética de este árbol (la del tag no tiene la escena quieta): sólo arma el gránulo y llama a los
    # procesadores, que son los del árbol donde se copia
    shutil.copy(RAIZ / "tests" / "_pasada_sintetica_laboratorio.py", antes / "tests")
    sha = subprocess.run(["git", "rev-parse", TAG + "^{commit}"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    print(f"antes: {TAG} ({sha}); después: {RAIZ}")
    cuenta = {"prod_igual": 0, "prod_err_igual": 0, "prod_dist": 0, "lab_igual": 0, "lab_solo_u_a": 0, "lab_dist": 0}

    print("\n== 0. constantes que pipeline.profile resuelve, antes contra después ==")
    for perfil in OPERACIONALES:
        a, d = _sub(antes, perfil, ["-c", CONSTANTES]), _sub(RAIZ, perfil, ["-c", CONSTANTES])
        dif = sorted(k for k in set(a) | set(d) if a.get(k) != d.get(k))
        ok = not dif and "PROCESO" not in a
        cuenta["prod_igual" if ok else "prod_dist"] += 1
        print(f"constantes {perfil:18s} {'IGUAL' if ok else 'DISTINTO ' + str(dif[:8])} ({len(d)} constantes)")

    for escena in ESCENAS:
        print(f"\n== escena {escena} ==")
        # 1. perfiles operacionales, antes contra después
        for perfil in PERFILES:
            a, d = correr(antes, perfil, escena), correr(RAIZ, perfil, escena)
            for fam in FAMILIAS:
                ra, rd = a.get(fam, a), d.get(fam, d)
                igual = _b(ra) == _b(rd)
                es_error = "ERROR" in ra or "PROCESO" in ra
                cuenta["prod_igual"] += igual and not es_error
                cuenta["prod_err_igual"] += igual and es_error
                cuenta["prod_dist"] += not igual
                vrp = rd.get("vrp_mw") if isinstance(rd, dict) else None
                print(f"{escena:6s} {perfil:30s} {fam:9s} {'IGUAL' if igual else 'DISTINTO'}"
                      f"{' (error igual antes y después)' if igual and es_error else ''} vrp_mw={vrp}")
        # 2. sin zona y control (sólo después) contra producción de antes
        prod_antes = correr(antes, "mirova_equivalent", escena)
        for perfil in ("_s196_lab_sinzona", "_s196_lab_control"):
            d = correr(RAIZ, perfil, escena)
            for fam in FAMILIAS:
                igual = _b(prod_antes[fam]) == _b(d[fam]) and "ERROR" not in d[fam]
                cuenta["prod_igual" if igual else "prod_dist"] += 1
                print(f"{escena:6s} {perfil + ' vs prod antes':30s} {fam:9s} {'IGUAL' if igual else 'DISTINTO'} "
                      f"vrp_mw={d[fam].get('vrp_mw')}")
        # 3. brazos con s < 5: entero y sin u_ntiA / u_etiA
        pares = [("_s196_lab_p300 vs s30 antes", correr(antes, "_s195_lab_s30", escena),
                  correr(RAIZ, "_s196_lab_p300", escena))]
        pares += [(f"{p} antes vs después", correr(antes, p, escena), correr(RAIZ, p, escena)) for p in S195]
        for nombre, a, d in pares:
            for fam in FAMILIAS:
                entero = _b(a[fam]) == _b(d[fam])
                sin = _b(sin_u_a(a[fam])) == _b(sin_u_a(d[fam]))
                if entero:
                    cuenta["lab_igual"] += 1
                    estado = "IGUAL"
                elif sin:
                    cuenta["lab_solo_u_a"] += 1
                    s1 = ((d[fam].get("diag_codigo_mirova") or {}).get("s1") or {}).get("pasada1") or {}
                    estado = f"IGUAL SIN u_A (después agrega u_ntiA={s1.get('u_ntiA')} u_etiA={s1.get('u_etiA')})"
                else:
                    cuenta["lab_dist"] += 1
                    estado = "DISTINTO"
                print(f"{escena:6s} {nombre:30s} {fam:9s} {estado} vrp_mw={d[fam].get('vrp_mw')}")

    print("\nTOTAL producción, guardia K y control: "
          f"{cuenta['prod_igual']} iguales con record o constantes, {cuenta['prod_err_igual']} iguales con error, "
          f"{cuenta['prod_dist']} distintos")
    print(f"TOTAL brazos con s < 5: {cuenta['lab_igual']} iguales enteros, {cuenta['lab_solo_u_a']} iguales salvo "
          f"u_ntiA/u_etiA, {cuenta['lab_dist']} distintos")
    return 0 if cuenta["prod_dist"] == 0 and cuenta["lab_dist"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
