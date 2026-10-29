# -*- coding: utf-8 -*-
"""Batería de la adenda 3 de V750-B (regla N-3), escrita ANTES de ver datos y antes de que el lector exista en
producción de la lectura.

POR QUÉ. La regla cambia quién veta: si el lector la aplica de más (por ejemplo a NOAA-20, a una protegida que la tabla
también trae o a una pasada del 2026-10-09), V750-B puede elegir una ROI que pierde una protegida real; si la aplica
de menos, descarta una ROI por una alerta que quizás no estaba. Cada escena predice lo que dice el texto de la adenda
y mira lo que da el lector, que corre el analizador sellado entero (predicado del tablero con node incluido).

Las escenas se arman con el constructor de la batería sellada (`bateria_regla_v750b.py`: `Pob`, `base`, `todos` y
sus constantes), extraído con ast y ejecutado sin copiar a mano. Todas llevan `--censo-omitido-solo-pruebas`, así
que el veredicto sale con salida 4 y marcado, como en la batería sellada.

Rojo antes: `--lector <analizar_v750b.py>` corre la misma batería contra el analizador sellado, sin la adenda; las
escenas de N-3 tienen que fallar por aserción.
Salida: 0 si todo como se espera; 1 «FALLAS» si alguna aserción falla; 2 «CAÍDA DEL LECTOR» si alguna escena se cae
con traza (una caída no es una aserción y no cuenta como atrapar una mutación, S156).
Uso: python probar_adenda3.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta temporal>
     [--lector <ruta del lector>]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
V750B = AQUI.parent
BATERIA = V750B / "bateria_regla_v750b.py"
EXTRAER = ("SENSOR", "PUB", "NOPUB", "COB", "INNER", "CELDA", "k_record", "Pob", "todos", "base")


def constructor():
    """Las piezas del constructor de escenas de la batería sellada, extraídas con ast."""
    src = BATERIA.read_text(encoding="utf-8")
    arbol = ast.parse(src)
    piezas = {}
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in EXTRAER:
            piezas[n.name] = ast.get_source_segment(src, n)
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], "id", None) in EXTRAER:
            piezas[n.targets[0].id] = ast.get_source_segment(src, n)
    faltan = set(EXTRAER) - set(piezas)
    assert not faltan, f"la batería sellada no trae {faltan}"
    ns = {"json": json}
    exec("\n\n".join(piezas[k] for k in EXTRAER), ns)
    return ns


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--lector", default=str(AQUI / "leer_n3_v750b.py"))
    a = ap.parse_args()
    a.lector = str(Path(a.lector).resolve())   # las escenas corren con la carpeta de V750-B como carpeta de trabajo
    K = constructor()
    fallas, caidas = [], []

    def correr(nombre, p, extra=(), salida=True):
        d = a.dest / nombre
        p.escribir(d)
        sal = ["--salida", str(d / "salida.txt")] if salida else []
        o = subprocess.run([sys.executable, a.lector, "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
                            "--evaluador", a.evaluador, *sal,
                            "--censo-omitido-solo-pruebas", "--sin-granulo", str(d / "sin_granulo.json"), *extra],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                           cwd=str(V750B))
        txt = o.stdout + o.stderr
        (d / "stdout.txt").write_text(txt, encoding="utf-8")
        return o.returncode, txt

    def elegibles(txt):
        m = re.search(r"§6\.1 elegibles: (\[.*?\])", txt)
        return m.group(1) if m else ""

    def linea_p1(txt, brazo, ventana="TO", canal="decide"):
        """La línea de métricas del brazo en esa ventana y canal."""
        k = txt.find(f"== ventana {ventana}, canal {canal}")
        if k < 0:
            return ""
        m = re.search(rf"^\s+{brazo}\s+prot.*$", txt[k:], re.M)
        return m.group(0) if m else ""

    def revisar(nombre, rc, txt, esperado_rc=4, roi=None, en=(), fuera=(), n3=None, p1=(), extra=()):
        if "Traceback (most recent call last)" in txt:
            caidas.append(nombre)
            print(f"{nombre} | CAÍDA | {txt.strip().splitlines()[-1][:160]}", flush=True)
            return
        malo = []
        if rc != esperado_rc:
            malo.append(f"salida {rc} != {esperado_rc}")
        if roi is not None:
            m = re.search(r"ROI elegida: (\S+) \(.*\[con la adenda 3, regla N-3\]", txt)
            if not m or m.group(1) != roi:
                malo.append(f"ROI con la adenda 3 {m.group(1) if m else 'sin línea'} != {roi}")
        el = elegibles(txt)
        malo += [f"{b} no elegible" for b in en if f"'{b}'" not in el]
        malo += [f"{b} elegible" for b in fuera if f"'{b}'" in el]
        if n3 is not None:
            m = re.search(r"protegidas informadas aparte \(.*?\): (\d+)", txt)
            if not m or int(m.group(1)) != n3:
                malo.append(f"N-3 aparte {m.group(1) if m else 'sin línea'} != {n3}")
        for brazo, ventana, canal, veta, todas, aparte in p1:
            lin = linea_p1(txt, brazo, ventana, canal)
            esp = f"P1 {veta:3d} (que veta; todas {todas}, N-3 aparte {aparte})"
            if esp not in lin:
                malo.append(f"{brazo} {ventana} {canal}: falta «{esp}» en «{lin[:90]}»")
        for frag in extra:
            if frag not in txt:
                malo.append(f"falta «{frag}»")
        if malo:
            fallas.append(nombre)
        print(f"{nombre} | {'OK' if not malo else 'FALLA | ' + '; '.join(malo)}", flush=True)

    def n3_lascar(p, hora, pubs, sensor=None, tabla=False, vrp_tabla=None):
        """Una protegida de Láscar en O: por defecto sólo del OCR (1,5 MW) y de Suomi NPP."""
        p.pasada("Lascar", hora, "pos", pubs, vrp_mirova=vrp_tabla, ocr_vrp=1.5, tabla=tabla)
        if sensor:
            p.objs[-1]["sensor"] = sensor
            for b in p.res[-1]["brazos"].values():
                if "record" in b:
                    b["record"]["sensor"] = sensor
    pierde_b2 = {"K": True, "B0": True, "B1": True, "B2": False, "B3": True}

    # N0, control: la población base de la batería sellada (B0 y B5 pierden 3 protegidas de Cordón Caulle de la tabla)
    p = K["base"]()
    rc, txt = correr("N0", p)
    revisar("N0 base: nada que N-3 toque, B0 y B5 siguen fuera", rc, txt, roi="B4", en=("B1", "B2", "B3", "B4"),
            fuera=("B0", "B5"), n3=0, p1=(("B0", "TO", "decide", 3, 3, 0),))

    # N1: B2 pierde una protegida sólo del OCR de Suomi NPP del 2026-09-20 (ventana O): con N-3 sigue elegible
    p = K["base"]()
    n3_lascar(p, "2026-09-20 05:00", pierde_b2)
    rc, txt = correr("N1", p)
    revisar("N1 la regla: B2 pierde una N-3 y sigue elegible", rc, txt, roi="B4", en=("B2",), fuera=("B0", "B5"),
            n3=1, p1=(("B2", "TO", "decide", 0, 1, 1), ("B2", "O", "todo", 0, 1, 1), ("B2", "O", "tabla", 0, 0, 0)),
            extra=("Lascar 2026-09-20 05:00 ventana O | publican ['B0', 'B1', 'B3', 'B4', 'B5'] | no publican ['B2']",
                   "elegibles contando también las N-3 (regla sin la adenda 3; sólo informa): ['B1', 'B3', 'B4']"))

    # N2: la misma pasada el día del hito (2026-10-09): ya no es N-3, veta
    p = K["base"]()
    n3_lascar(p, "2026-10-09 05:00", pierde_b2)
    rc, txt = correr("N2", p)
    revisar("N2 borde: el 2026-10-09 ya veta", rc, txt, roi="B4", fuera=("B2",), n3=0,
            p1=(("B2", "TO", "decide", 1, 1, 0),))

    # N3: la misma pasada pero de NOAA-20: veta
    p = K["base"]()
    n3_lascar(p, "2026-09-20 05:00", pierde_b2, sensor="VIIRS_NOAA20_750")
    rc, txt = correr("N3", p)
    revisar("N3 otra plataforma (NOAA-20): veta", rc, txt, roi="B4", fuera=("B2",), n3=0,
            p1=(("B2", "TO", "decide", 1, 1, 0),))

    # N4: Suomi NPP antes del hito, protegida por el OCR (1,5) pero CON alerta de la tabla (0,6): veta
    p = K["base"]()
    n3_lascar(p, "2026-09-20 05:00", pierde_b2, tabla=True, vrp_tabla=0.6)
    rc, txt = correr("N4", p)
    revisar("N4 con alerta de la tabla (aunque bajo 1 MW): veta", rc, txt, roi="B4", fuera=("B2",), n3=0,
            p1=(("B2", "TO", "decide", 1, 1, 0),))

    # N5: la que cambia la ROI. B0 pierde una N-3 en Láscar, y B4 en Láscar es la caja B0: sin la adenda B4 sale de los
    # elegibles y el §6.3 elige B2; con la adenda B4 vuelve y es la primera del orden de cercanía al .m
    p = K["base"]()
    n3_lascar(p, "2026-09-21 05:00", {"K": True, "B0": False, "B1": True, "B2": True, "B3": True, "B5": True})
    rc, txt = correr("N5", p)
    revisar("N5 la N-3 decide la ROI: con la adenda B4, sin ella B2", rc, txt, roi="B4", en=("B4",), n3=1,
            p1=(("B4", "TO", "decide", 0, 1, 1),),
            extra=("elegibles contando también las N-3 (regla sin la adenda 3; sólo informa): ['B1', 'B2', 'B3']",))

    # N6: una sólo del OCR de Suomi NPP en T (antes del 2026-06-13). En T decide la tabla sola y la población la marca
    # `decide` falso, así que no es etiqueta en ningún canal: nunca vetó, la adenda no la toca y no se lista
    p = K["base"]()
    n3_lascar(p, "2026-05-25 05:00", pierde_b2)
    rc, txt = correr("N6", p)
    revisar("N6 una sólo del OCR en T: no es etiqueta, no veta ni se lista", rc, txt, roi="B4", en=("B2",), n3=0,
            p1=(("B2", "TO", "decide", 0, 0, 0), ("B2", "T", "todo", 0, 0, 0)))

    # N7: dos N-3 perdidas y una protegida de la tabla perdida por B2: la de la tabla veta igual
    p = K["base"]()
    n3_lascar(p, "2026-09-22 05:00", pierde_b2)
    n3_lascar(p, "2026-09-23 05:00", pierde_b2)
    p.pasada("Lascar", "2026-09-24 05:00", "pos", pierde_b2, vrp_mirova=1.4)
    rc, txt = correr("N7", p)
    revisar("N7 dos N-3 y una de la tabla: veta por la de la tabla", rc, txt, roi="B4", fuera=("B2",), n3=2,
            p1=(("B2", "TO", "decide", 1, 3, 2),))

    # N8: un analizador que no es el sellado (un comentario de más): el lector se niega con salida 2. La copia vive en
    # la carpeta temporal, no en la sellada (VA3-04)
    ajeno = a.dest / "_ajeno_analizar_v750b.py"
    a.dest.mkdir(parents=True, exist_ok=True)
    ajeno.write_text((V750B / "analizar_v750b.py").read_text(encoding="utf-8") + "\n# ajeno\n", encoding="utf-8")
    rc, txt = correr("N8", K["base"](), extra=("--analizador", str(ajeno)))
    revisar("N8 analizador ajeno: se niega", rc, txt, esperado_rc=2, extra=("RECHAZO: el analizador no es el sellado",))

    # N9 (VA3-01): la N-3 de N1 sin la caja B5. La compuerta de la adenda 1 cierra (cobertura con las cajas
    # INSUFICIENTE) y no se lee: salida 3, sin veredicto. El analizador solo la sacaría de las observadas sin aviso
    p = K["base"]()
    n3_lascar(p, "2026-09-20 05:00", pierde_b2)
    p.res[-1]["oraculo"].pop("B5")
    rc, txt = correr("N9", p)
    revisar("N9 una protegida sin una caja: la compuerta de la adenda 1 no deja leer", rc, txt, esperado_rc=3,
            extra=("cobertura con las cajas: INSUFICIENTE", "== LECTOR: cobertura con las cajas INSUFICIENTE"))
    if "ROI elegida" in txt and "Traceback" not in txt:
        fallas.append("N9 una protegida sin una caja: la compuerta de la adenda 1 no deja leer")
        print("N9 | FALLA | hay veredicto con la compuerta cerrada", flush=True)

    # N10: la misma con --leer-con-faltantes: se lee, con la marca de la adenda 1 en el veredicto y la regla N-3 aplicada
    rc, txt = correr("N10", p, extra=("--leer-con-faltantes", "prueba N10"))
    revisar("N10 con --leer-con-faltantes: se lee con la marca", rc, txt, roi="B4", n3=0,
            extra=("[LEÍDO CON FALTANTES DE LA ADENDA: prueba N10] == §6",))

    # N11 (VA3-02): --salida=ruta, sola (sin otro --salida antes), se respeta
    p = K["base"]()
    d11 = a.dest / "N11"
    rc, txt = correr("N11", p, extra=(f"--salida={d11 / 'otra_salida.txt'}",), salida=False)
    revisar("N11 --salida=ruta se respeta", rc, txt, roi="B4")
    if not (d11 / "otra_salida.txt").exists():
        fallas.append("N11 --salida=ruta se respeta")
        print("N11 | FALLA | --salida=ruta no escribió en la ruta pedida", flush=True)

    n = 12
    if caidas:
        print(f"== PRUEBAS: CAÍDA DEL LECTOR en {caidas} (fallas por aserción {len(fallas)}) de {n}")
        return 2
    if fallas:
        fallas = sorted(set(fallas))   # una escena con dos aserciones caídas cuenta una vez
        print(f"== PRUEBAS: FALLAS {len(fallas)} de {n}: {fallas}")
        return 1
    print(f"== PRUEBAS: TODOS LOS ESCENARIOS COMO SE ESPERA ({n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
