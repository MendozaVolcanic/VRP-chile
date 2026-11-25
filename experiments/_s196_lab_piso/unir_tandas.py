# -*- coding: utf-8 -*-
"""S201: une las tandas del barrido del piso (S196) en una carpeta por brazo, la entrada de `evaluar.py calibrar`
(--sin-zona, --control, --brazo piso=carpeta). No corre calibrar ni mira resultados de detección.

POR QUÉ. El barrido se despacha por tandas mensuales (pre-registro, decisión 3 de Nicolás) y cada tanda deja sus
salidas en la rama `s196-lab-piso/<run>`. El evaluador re-sellado recibe una carpeta por brazo, así que alguien tiene
que unir las tandas, y esa unión no estaba escrita. El verificador limpio del frente A de la ronda 5 de la auditoría
externa con Codex (D:\\codex-vrp\\_salida\\ronda5\\fa_r5_verificacion\\VEREDICTO.md) mostró que el evaluador puede
terminar en ELEGIDO con otro piso si un brazo trae filas duplicadas de otro código (R5FA-102), copias de una pasada
(R5FA-101) o noches que no están en todos los brazos (R5FA-105), y que la cadena oficial no produce esos casos salvo
que la unión de las tandas no los impida. Las tandas no son disjuntas: Cordón Caulle va en todas (da poder al control
donde la zona no actúa) y marzo se corrió en tres runs (t1, t2 y t2c) con volcanes caídos en t2 (401 de NASA). Por eso
la unión sigue un manifiesto explícito (MANIFIESTO_TANDAS.json: qué run vale para cada volcán y mes) y se detiene ante
cualquier ambigüedad en vez de elegir en silencio. El verificador limpio de este PR (S201,
D:\\vrp-trabajo\\temporales\\s201\\verif_1133\\VEREDICTO.md) mostró que la recolección publica igual los datos
parciales de trabajos caídos: con Isluga de marzo tomada de t2 la primera versión entregaba 8 records en vez de 271
sin ningún problema. De ahí los controles 2 y 4.

QUÉ EXIGE (cada falla queda en `problemas`; con problemas NO se escribe ninguna carpeta de brazo y la línea de
comandos sale con 2):
  1. manifiesto: los 11 volcanes de VOLCANES y ningún otro, inicio en INICIO, fechas ISO con ini <= fin, y cada
     (volcán, mes) en una sola entrada;
  2. trabajos: en el último intento de cada run, todos los trabajos `reproc` de cada volcán usado terminaron en
     success (la CLI lo consulta con `gh run view <run> --json jobs`; sin dato, es problema);
  3. cobertura: cada volcán tiene cada mes, de INICIO al último fin, cubierto;
  4. cada brazo y volcán de cada run existe en su rama y no deja vacío ningún trozo de 5 días de su ventana (así se
     reparten los trabajos del workflow: días 1 a 5, 6 a 10, ... desde `ini`);
  5. cada record trae `datetime_utc` y `sensor` y cae en la ventana [ini, fin] de su run;
  6. una clave (sensor, datetime_utc) repetida es idéntica salvo processed_utc y first_processed_utc; si difiere en
     cualquier otro campo, incluido regimen.codigo_sha, es CONFLICTIVO;
  7. todos los brazos tienen el mismo conjunto de claves que el control en cada volcán, en las dos direcciones;
  8. con --fin-esperado, el último fin del manifiesto es ése (el fin sellado es 2026-11-23, R4FD-107).
Escribe en <salida>.parcial y sólo si no hubo problemas lo renombra a <salida>; se niega a usar una carpeta que ya
exista. Deja siempre <salida>.parcial/informe_union.json o <salida>/informe_union.json (manifiesto, problemas,
conteos, sha256 de cada archivo escrito).

Uso: python experiments/_s196_lab_piso/unir_tandas.py experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json SALIDA \\
         --fin-esperado 2026-11-23
Las ramas se bajan antes: git fetch origin "+refs/heads/s196-lab-piso/*:refs/remotes/origin/s196-lab-piso/*"
Pruebas: tests/test_lab_piso_union_tandas_s201.py.
"""
import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BRAZOS = ["_s196_lab_sinzona", "_s196_lab_control", "_s196_lab_p300", "_s196_lab_p275", "_s196_lab_p250",
          "_s196_lab_p225", "_s196_lab_p200", "_s196_lab_p175", "_s196_lab_p150"]
CONTROL = "_s196_lab_control"
VOLCANES = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
INICIO = "2026-03-01"
DIAS_TROZO = 5
VOLATILES = {"processed_utc", "first_processed_utc"}
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_TRABAJO = re.compile(r"^reproc \(([^,]+),")


def leer_git(run, brazo, volcan):
    """El JSON de un brazo y volcán en la rama de salidas del run, o None si no está."""
    ruta = f"origin/s196-lab-piso/{run}:experiments/_s196_lab_piso/salidas/{run}/{brazo}/{volcan}.json"
    r = subprocess.run(["git", "-C", str(RAIZ), "show", ruta], capture_output=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode("utf-8"))


def trabajos_gh(run):
    """{volcán: [conclusión de cada trabajo reproc]} del último intento del run, o None sin dato (tres intentos).
    POR QUÉ la API REST con per_page=50: `gh run view --json jobs` y per_page=100 devuelven HTTP 500 o 502 en los runs
    con varios intentos (t3 tiene 7), medido el 2026-11-25; con 50 por página responde."""
    url = f"repos/MendozaVolcanic/VRP-chile/actions/runs/{run}/jobs?filter=latest&per_page=50"
    for i in range(3):
        r = subprocess.run(["gh", "api", url, "--paginate", "-q", ".jobs[] | [.name, (.conclusion // .status)] | @tsv"],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0 and r.stdout.strip():
            out = defaultdict(list)
            for linea in r.stdout.splitlines():
                nombre, _, concl = linea.partition("\t")
                m = RE_TRABAJO.match(nombre)
                if m:
                    out[m.group(1).strip()].append(concl.strip())
            return dict(out)
        time.sleep(10 * (i + 1))
    return None


def huella(rec):
    return json.dumps({k: v for k, v in rec.items() if k not in VOLATILES}, sort_keys=True, ensure_ascii=False)


def meses(ini, fin):
    a, b = date.fromisoformat(ini), date.fromisoformat(fin)
    out, y, m = [], a.year, a.month
    while (y, m) <= (b.year, b.month):
        out.append("%04d-%02d" % (y, m))
        y, m = y + (m == 12), m % 12 + 1
    return out


def trozos(ini, fin):
    """Ventanas de DIAS_TROZO días desde ini, como las reparte el workflow (la última puede ser más corta)."""
    a, b, out = date.fromisoformat(ini), date.fromisoformat(fin), []
    while a <= b:
        z = min(a + timedelta(days=DIAS_TROZO - 1), b)
        out.append((a.isoformat(), z.isoformat()))
        a = z + timedelta(days=1)
    return out


def validar_manifiesto(manifiesto, fin_esperado=None):
    problemas = []
    for e in manifiesto:
        for campo in ("run", "etiqueta", "ini", "fin", "volcanes"):
            if campo not in e:
                problemas.append(f"entrada sin «{campo}»: {e}")
        if not (RE_FECHA.match(str(e.get("ini", ""))) and RE_FECHA.match(str(e.get("fin", "")))):
            problemas.append(f"{e.get('etiqueta')}: fechas fuera de formato AAAA-MM-DD ({e.get('ini')}, {e.get('fin')})")
        elif e["ini"] > e["fin"]:
            problemas.append(f"{e.get('etiqueta')}: ini {e['ini']} posterior a fin {e['fin']}")
        for v in e.get("volcanes", []):
            if v not in VOLCANES:
                problemas.append(f"{e.get('etiqueta')}: volcán desconocido «{v}»")
    if problemas:
        return problemas
    usados = {v for e in manifiesto for v in e["volcanes"]}
    for v in VOLCANES:
        if v not in usados:
            problemas.append(f"{v}: no aparece en el manifiesto")
    ini_global = min(e["ini"] for e in manifiesto)
    fin_global = max(e["fin"] for e in manifiesto)
    if ini_global != INICIO:
        problemas.append(f"el manifiesto empieza en {ini_global}, no en {INICIO}")
    if fin_esperado and fin_global != fin_esperado:
        problemas.append(f"fin del manifiesto {fin_global} distinto del esperado {fin_esperado}")
    vistos = {}
    for e in manifiesto:
        for v in e["volcanes"]:
            for m in meses(e["ini"], e["fin"]):
                if (v, m) in vistos:
                    problemas.append(f"{v} {m}: en dos entradas ({vistos[(v, m)]} y {e['etiqueta']})")
                vistos[(v, m)] = e["etiqueta"]
    for v in VOLCANES:
        for m in meses(INICIO, fin_global):
            if (v, m) not in vistos:
                problemas.append(f"{v} {m}: ningún run del manifiesto lo cubre")
    return problemas


def unir(manifiesto, salida, fin_esperado=None, leer=None, trabajos=None):
    """`leer(run, brazo, volcán)` devuelve el JSON o None; `trabajos(run)` devuelve {volcán: [conclusiones]} o None.
    Devuelve (problemas, conteo). Sólo si no hay problemas deja las carpetas de brazo en `salida`."""
    leer = leer or leer_git
    trabajos = trabajos or trabajos_gh
    salida = Path(salida)
    parcial = salida.with_name(salida.name + ".parcial")
    if salida.exists() or parcial.exists():
        return [f"la salida {salida} o {parcial} ya existe: use una carpeta nueva"], {}
    problemas = validar_manifiesto(manifiesto, fin_esperado)
    conteo = defaultdict(dict)
    if problemas:
        parcial.mkdir(parents=True)
        _informe(parcial, manifiesto, fin_esperado, problemas, conteo)
        return problemas, conteo
    for e in manifiesto:                                                 # 2. trabajos verdes
        t = trabajos(e["run"])
        if t is None:
            problemas.append(f"{e['etiqueta']} ({e['run']}): sin dato de sus trabajos")
            continue
        for v in e["volcanes"]:
            concl = t.get(v, [])
            if not concl or any(c != "success" for c in concl):
                problemas.append(f"{e['etiqueta']} ({e['run']}) {v}: trabajos no todos en success: {sorted(concl)}")
    claves = defaultdict(dict)
    for b in BRAZOS:
        for v in VOLCANES:
            union, origen = {}, {}
            n_leidos = n_dup = 0
            for e in manifiesto:
                if v not in e["volcanes"]:
                    continue
                d = leer(e["run"], b, v)
                if d is None:                                            # 4. brazo presente
                    problemas.append(f"{b} {v}: falta en {e['etiqueta']} ({e['run']})")
                    continue
                recs = d["records"] if isinstance(d, dict) else d
                fechas = set()
                for r in recs:
                    n_leidos += 1
                    dt, sensor = r.get("datetime_utc"), r.get("sensor")
                    if not isinstance(dt, str) or not RE_FECHA.match(dt[:10]) or not sensor:   # 5. campos
                        problemas.append(f"{b} {v}: record sin datetime_utc o sensor válidos en {e['etiqueta']}")
                        continue
                    if not (e["ini"] <= dt[:10] <= e["fin"]):           # 5. ventana
                        problemas.append(f"{b} {v}: record {dt} fuera de la ventana de {e['etiqueta']}")
                        continue
                    fechas.add(dt[:10])
                    k = (sensor, dt)
                    if k in union:                                       # 6. duplicados
                        if huella(union[k]) == huella(r):
                            n_dup += 1
                        else:
                            problemas.append(f"{b} {v}: duplicado CONFLICTIVO {k} entre {origen[k]} y {e['etiqueta']}")
                        continue
                    union[k] = r
                    origen[k] = e["etiqueta"]
                for a, z in trozos(e["ini"], e["fin"]):                 # 4. trozos no vacíos
                    if not any(a <= f <= z for f in fechas):
                        problemas.append(f"{b} {v}: trozo {a} a {z} de {e['etiqueta']} sin ningún record")
            ordenados = [union[k] for k in sorted(union, key=lambda k: (k[1], k[0]))]
            texto = json.dumps({"volcano": v, "updated": "unir_tandas S201", "records": ordenados}, ensure_ascii=False)
            dest = parcial / b / f"{v}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(texto, encoding="utf-8", newline="")
            conteo[b][v] = {"leidos": n_leidos, "unidos": len(ordenados), "duplicados_identicos": n_dup,
                            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest()}
            claves[v][b] = set(union)
    for v, porb in claves.items():                                       # 7. mismas claves que el control
        ref = porb.get(CONTROL, set())
        for b, ks in porb.items():
            if ks != ref:
                problemas.append(f"{v}: {b} tiene {len(ks - ref)} claves que el control no y le faltan {len(ref - ks)}")
    _informe(parcial, manifiesto, fin_esperado, problemas, conteo)
    if problemas:
        for b in BRAZOS:                                                 # nada de brazos con problemas
            shutil.rmtree(parcial / b, ignore_errors=True)
        return problemas, conteo
    parcial.rename(salida)
    return problemas, conteo


def _informe(carpeta, manifiesto, fin_esperado, problemas, conteo):
    carpeta.mkdir(parents=True, exist_ok=True)
    informe = {"manifiesto": manifiesto, "fin_esperado": fin_esperado, "problemas": problemas, "conteo": conteo}
    (carpeta / "informe_union.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8",
                                                 newline="")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifiesto")
    ap.add_argument("salida")
    ap.add_argument("--fin-esperado")
    a = ap.parse_args(argv)
    man = json.loads(Path(a.manifiesto).read_text(encoding="utf-8"))
    problemas, conteo = unir(man, a.salida, a.fin_esperado, leer=leer_git, trabajos=trabajos_gh)
    tot = {b: sum(c["unidos"] for c in conteo[b].values()) for b in conteo}
    print("records unidos por brazo:", tot)
    print("duplicados idénticos quitados (control):",
          {v: c["duplicados_identicos"] for v, c in conteo.get(CONTROL, {}).items() if c["duplicados_identicos"]})
    print("problemas:", len(problemas))
    for p in problemas[:40]:
        print("  ", p)
    return 2 if problemas else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
