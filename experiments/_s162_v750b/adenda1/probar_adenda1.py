# -*- coding: utf-8 -*-
"""Prueba de la adenda 1 de V750-B (S162, relevo VIIRS 750): la pasada «ok» a la que le falta una caja del oráculo.

POR QUÉ. El analizador sellado (`analizar_v750b.py`, tag `s162-v750b-sellado`, l. 208-209) arma las pasadas observadas
exigiendo las cinco cajas del oráculo, pero no cuenta como SIN DATO la que no las tiene: esa pasada sale del
denominador y del numerador a la vez, sin nombre, y si es protegida la cobertura sigue diciendo SUFICIENTE. El §4 del
pre-registro ya dice que un error del brazo es SIN DATO; la adenda no cambia esa regla, agrega el compañero
`cobertura_cajas_v750b.py` que la aplica a este caso, y el analizador sellado no se edita (§9: «No se edita el
analizador después del sello»).

Escenarios (cada uno comprueba solo su resultado y la batería sale 1 si alguno no coincide):
- D1 (el defecto existe): población con una protegida «ok» sin la caja B3. El analizador sellado la pierde: observadas
  + no observadas + SIN DATO = objetivos - 1, y la cobertura sale SUFICIENTE con una protegida que nadie miró.
- A1: el compañero la lista con su caja faltante, la cuenta como SIN DATO y, por ser protegida, cierra (salida 3).
- A2: una no protegida sin caja entre 100 pasadas: 1 % de SIN DATO, SUFICIENTE (salida 0) y listada por nombre.
- A3: tres no protegidas sin caja entre 100: 3 % sobre el 2 %, INSUFICIENTE (salida 3).
- A4 (identidad): sin cajas faltantes, con una pasada sin gránulo, un error de K, una grilla incompleta, una diurna, una
  «fuera» y una «sin_crater», el compañero da el MISMO SIN DATO y el mismo veredicto de cobertura que el analizador.
- A5: una caja presente pero vacía (`None`) es tan faltante como una ausente.
- A6: archivo de pasadas sin gránulo de otra lista: INSUFICIENTE, igual que el analizador (VB3-02).
- A7 y A8 (agregados por el nulo, `mutar_adenda1.py`): una protegida sin caja bajo el 2 % cierra igual; una diurna
  sin cajas se cuenta una sola vez (ya es SIN DATO del analizador).
Uso: python probar_adenda1.py [--companero <ruta>] [--dest <carpeta temporal>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
V750B = AQUI.parent
RAIZ = V750B.parents[1]
ANALIZAR = V750B / "analizar_v750b.py"
SENSOR = "VIIRS_SNPP_750"
CAJAS = ("B0", "B1", "B2", "B3", "B5")
PUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 1, "n_p2": 0, "npix": 1, "vrp_mw": 0.5,
       "pixeles": [[33, 33, 2, 0.0, 0.9]]}
NOPUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False, "nan_7_crater": 0, "nan_crater": False}
COB_SIN_CRATER = dict(COB, nan_7_crater=3)


def k_record(pub):
    if not pub:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": 0.5, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": 0.5, "vrp_mir_mw": 0.5, "discarded_reason": None, "triggered_test1": False,
            "vrp_vent_mw": None, "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    """Mismo formato que deja el probe (objetivos + resultados_00.json), como bateria_regla_v750b.py."""

    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, hora, lab="neg_limpio", vrp_mirova=None, sin_caja=(), caja_vacia=(), estado="ok", dayflag=0,
               cob=COB, volcan="Lascar", caja_rara=None):
        i = len(self.objs)
        if lab == "pos":
            filas = [{"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova, "dist_km": 0.5,
                      "source": "CONS"}]
        else:
            filas = [{"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None, "source": "CONS"}]
        prot = lab == "pos" and (vrp_mirova or 0) >= 1.0
        pub = lab == "pos"
        self.objs.append({
            "id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab, "protegida": prot,
            "alerta_tabla": lab == "pos", "decide": True, "mirova": filas,
            "mirova_vrp": vrp_mirova or 0.0, "z": 30.0, "pub_prod": pub, "dc": "summit" if pub else None,
            "pc_vrp": 0.5 if pub else 0.0, "pc_n": 1 if pub else None, "granule": f"g{i}", "en_sc": False,
            "celda_crater": [32, 33], "inner_km": 5.0})
        r = {"id": i, "volcan": volcan, "hora_utc": hora, "estado": estado, "dayflag": dayflag, "sunglint": 40.0}
        if dayflag == "ausente":
            del r["dayflag"]
        if estado == "volcan_fuera_del_granulo":
            self.res.append(r)
            return i
        if estado == "error_K":
            r["brazos"] = {"K": {"error": "RuntimeError: sintetico", "traza": ""}}
        else:
            r["brazos"] = {"K": {"record": k_record(pub), "pc_pix": [[10, 10]] if pub else []}}
        if estado == "grilla_incompleta":
            r["oraculo"], r["oraculo_estado"] = {}, "grilla_incompleta"
        else:
            r["cobertura"] = cob
            r["oraculo"] = {b: (PUB if pub else NOPUB) for b in CAJAS if b not in sin_caja}
            for b in caja_vacia:
                r["oraculo"][b] = None
            for b, v in (caja_rara or {}).items():
                r["oraculo"][b] = v
        self.res.append(r)
        return i

    def escribir(self, d, sin_granulo=(), sha_ajeno=False):
        (d / "art").mkdir(parents=True, exist_ok=True)
        (d / "art" / "resultados_00.json").write_text(json.dumps(self.res), encoding="utf-8")
        texto = json.dumps(self.objs)
        (d / "objetivos.json").write_text(texto, encoding="utf-8")
        sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        (d / "sin_granulo.json").write_text(json.dumps(
            {"objetivos_sha256": ("0" * 64) if sha_ajeno else sha, "pasadas": list(sin_granulo)}), encoding="utf-8")


def base(n_neg=20):
    p = Pob()
    for n in range(4):
        p.pasada(f"2026-05-{10 + n:02d} 05:00", "pos", 1.5)
    for n in range(n_neg):
        p.pasada(f"2026-04-{1 + n % 28:02d} {n // 28:02d}:00")
    return p


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def analizador(d, evaluador):
    """Corre el analizador sellado sólo con controles y devuelve (observadas, no_obs, sin_dato, sin_granulo, cob)."""
    rc, out = correr([sys.executable, str(ANALIZAR), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
                      "--evaluador", str(evaluador), "--sin-granulo", str(d / "sin_granulo.json"),
                      "--solo-controles", "--censo-omitido-solo-pruebas", "--salida", str(d / "analizador.txt")])
    m = re.search(r"observadas: (\d+) \| no observadas \(fuera del denominador\): (\{[^}]*\}) \| SIN DATO: (\d+)", out)
    g = re.search(r"pasadas sin gránulo \(del generador\): (\d+)", out)
    c = re.search(r"== cobertura: (SUFICIENTE|INSUFICIENTE)", out)
    if not (m and g and c):
        return None, out
    no_obs = sum(int(x) for x in re.findall(r": (\d+)", m.group(2)))
    return (int(m.group(1)), no_obs, int(m.group(3)), int(g.group(1)), c.group(1)), out


CAIDAS = []
LECTOR = AQUI / "leer_v750b.py"


def companero(ruta, d):
    rc, out = correr([sys.executable, str(ruta), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
                      "--sin-granulo", str(d / "sin_granulo.json")])
    m = re.search(r"SIN DATO total: (\d+) \(analizador sellado (\d+), sin gránulo (\d+), falta caja (\d+)\)", out)
    c = re.search(r"== cobertura con las cajas: (SUFICIENTE|INSUFICIENTE)", out)
    if "Traceback" in out:
        CAIDAS.append(d.name)
    mi = re.search(r"cajas ilegibles: (\d+)", out)
    lista = re.findall(r"falta caja: id (\d+) [^\n]*?cajas faltantes \[([^\]]*)\]", out)
    if not (m and c):
        return rc, None, out
    return rc, {"total": int(m.group(1)), "sellado": int(m.group(2)), "sin_g": int(m.group(3)),
                "falta": int(m.group(4)), "cob": c.group(1), "lista": lista,
                "ilegibles": int(mi.group(1)) if mi else None}, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companero", default=str(AQUI / "cobertura_cajas_v750b.py"))
    ap.add_argument("--evaluador", default="", help="evaluar_d25.py del tag s161-d25-lectura (sólo para D1 y A4)")
    ap.add_argument("--dest", default="")
    ap.add_argument("--lector", default=str(AQUI / "leer_v750b.py"))
    a = ap.parse_args()
    dest = Path(a.dest) if a.dest else Path(tempfile.mkdtemp(prefix="adenda1_"))
    ev = Path(a.evaluador) if a.evaluador else None
    fallas, filas = [], []

    def chequear(nombre, cond, detalle):
        filas.append(f"{'OK   ' if cond else 'FALLA'} {nombre}: {detalle}")
        if not cond:
            fallas.append(nombre)

    def esc(nombre):
        d = dest / nombre
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        return d

    # D1 y A1: una protegida «ok» sin la caja B3
    p = base()
    i_prot = p.pasada("2026-07-15 05:00", "pos", 2.0, sin_caja=("B3",))
    d = esc("D1_A1")
    p.escribir(d)
    if ev:
        an, out = analizador(d, ev)
        if an is None:
            chequear("D1 analizador sellado", False, "no se pudo leer su salida: " + out[-300:].replace("\n", " | "))
        else:
            obs, no_obs, sd, sg, cob = an
            chequear("D1 el analizador sellado pierde la pasada", obs + no_obs + sd + sg == len(p.objs) - 1,
                     f"observadas {obs} + no obs {no_obs} + SIN DATO {sd} + sin gránulo {sg} contra {len(p.objs)} objetivos")
            chequear("D1 y cobertura SUFICIENTE con la protegida sin mirar", cob == "SUFICIENTE", f"cobertura {cob}")
    rc, c, out = companero(a.companero, d)
    chequear("A1 lectura de la salida", c is not None, f"salida {rc}: " + out[-200:].replace("\n", " | "))
    if c:
        chequear("A1 falta caja contada", c["falta"] == 1 and c["total"] == 1, f"{c}")
        chequear("A1 nombrada con la caja", c["lista"] == [(str(i_prot), "'B3'")], f"{c['lista']}")
        chequear("A1 protegida cierra", c["cob"] == "INSUFICIENTE" and rc == 3, f"cob {c['cob']}, salida {rc}")

    # A2: una no protegida sin caja entre 100 pasadas
    p = base(n_neg=95)
    p.pasada("2026-08-01 05:00", "neg_limpio", sin_caja=("B0", "B5"))
    d = esc("A2")
    p.escribir(d)
    rc, c, out = companero(a.companero, d)
    chequear("A2 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A2 bajo el 2 %: SUFICIENTE y listada", c["cob"] == "SUFICIENTE" and rc == 0 and c["falta"] == 1
                 and len(c["lista"]) == 1, f"{c}, salida {rc}")

    # A3: tres no protegidas sin caja entre 100
    p = base(n_neg=93)
    for n in range(3):
        p.pasada(f"2026-08-0{2 + n} 05:00", "neg_limpio", sin_caja=("B2",))
    d = esc("A3")
    p.escribir(d)
    rc, c, out = companero(a.companero, d)
    chequear("A3 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A3 sobre el 2 %: INSUFICIENTE", c["cob"] == "INSUFICIENTE" and rc == 3 and c["falta"] == 3,
                 f"{c}, salida {rc}")

    # A4: identidad con el analizador cuando no falta ninguna caja (200 pasadas para quedar bajo el 2 %)
    p = base(n_neg=196)
    p.pasada("2026-08-10 05:00", estado="error_K")
    p.pasada("2026-08-11 05:00", estado="grilla_incompleta")
    p.pasada("2026-08-12 05:00", dayflag=1)
    p.pasada("2026-08-13 05:00", estado="volcan_fuera_del_granulo")
    p.pasada("2026-08-14 05:00", cob=COB_SIN_CRATER)
    d = esc("A4")
    p.escribir(d, sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-08-15 05:00", "protegida": False}])
    rc, c, out = companero(a.companero, d)
    chequear("A4 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A4 conteos propios", c["sellado"] == 3 and c["sin_g"] == 1 and c["falta"] == 0, f"{c}")
        if ev:
            an, outa = analizador(d, ev)
            ok_an = an is not None
            chequear("A4 analizador legible", ok_an, outa[-200:].replace("\n", " | "))
            if ok_an:
                chequear("A4 identidad con el analizador", an[2] == c["sellado"] and an[3] == c["sin_g"]
                         and an[4] == c["cob"], f"analizador {an} contra compañero {c}")

    # A5: caja presente pero vacía
    p = base()
    p.pasada("2026-07-20 05:00", "pos", 1.8, caja_vacia=("B1",))
    d = esc("A5")
    p.escribir(d)
    rc, c, out = companero(a.companero, d)
    chequear("A5 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A5 caja null = ilegible, cierra", c["ilegibles"] == 1 and c["falta"] == 0
                 and c["cob"] == "INSUFICIENTE" and rc == 3, f"{c}")

    # A6: archivo sin gránulo de otra lista
    p = base()
    d = esc("A6")
    p.escribir(d, sha_ajeno=True)
    rc, c, out = companero(a.companero, d)
    chequear("A6 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A6 sin gránulo ajeno: INSUFICIENTE", c["cob"] == "INSUFICIENTE" and rc == 3, f"{c}")
        if ev:
            an, outa = analizador(d, ev)
            chequear("A6 identidad con el analizador", an is not None and an[4] == c["cob"],
                     f"analizador {an} contra compañero {c['cob']}")

    # A7 (nulo, M3): una protegida sin caja entre 200 pasadas (0,5 %): cierra por ser protegida, no por el porcentaje
    p = base(n_neg=195)
    p.pasada("2026-07-25 05:00", "pos", 3.0, sin_caja=("B5",))
    d = esc("A7")
    p.escribir(d)
    rc, c, out = companero(a.companero, d)
    chequear("A7 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A7 protegida bajo el 2 % igual cierra", c["falta"] == 1 and c["cob"] == "INSUFICIENTE" and rc == 3,
                 f"{c}, salida {rc}")

    # A8 (nulo, M6): una diurna sin cajas ya es SIN DATO del analizador; no se cuenta dos veces
    p = base(n_neg=95)
    p.pasada("2026-08-20 05:00", dayflag=1, sin_caja=CAJAS)
    d = esc("A8")
    p.escribir(d)
    rc, c, out = companero(a.companero, d)
    chequear("A8 lectura", c is not None, f"salida {rc}")
    if c:
        chequear("A8 diurna contada una vez", c["sellado"] == 1 and c["falta"] == 0 and c["total"] == 1, f"{c}")

    # agregados tras el verificador de la adenda (verificador/INFORME.md, VAD-01 a VAD-05)
    def con_analizador(nombre, d, c):
        """Donde no falta ninguna caja, el compañero tiene que dar lo mismo que el analizador sellado (VAD-05)."""
        if not ev or c is None:
            return
        an, outa = analizador(d, ev)
        chequear(f"{nombre} identidad con el analizador", an is not None and an[2] == c["sellado"]
                 and an[3] == c["sin_g"] and an[4] == c["cob"], f"analizador {an} contra compañero {c}")

    def caso(nombre, p, cond, detalle, sin_granulo=(), identidad=True):
        d = esc(nombre)
        p.escribir(d, sin_granulo=sin_granulo)
        rc, c, out = companero(a.companero, d)
        chequear(f"{nombre} lectura", c is not None, f"salida {rc}")
        if c:
            chequear(f"{nombre} {detalle}", cond(rc, c), f"{c}, salida {rc}")
            if identidad:
                con_analizador(nombre, d, c)
        return d

    # A9 (VAD-03): caja null en una no protegida, 1 de 100: el analizador se caería; cierra igual
    p = base(n_neg=95)
    p.pasada("2026-08-21 05:00", caja_vacia=("B2",))
    caso("A9", p, lambda rc, c: c["ilegibles"] == 1 and c["cob"] == "INSUFICIENTE" and rc == 3,
         "caja null cierra bajo el 2 %", identidad=False)
    # A10 (VAD-04): caja {} (sin npix ni vrp_mw ni pixeles): el analizador la leería como «no publica»; cierra
    p = base(n_neg=95)
    p.pasada("2026-08-22 05:00", caja_rara={"B3": {}})
    caso("A10", p, lambda rc, c: c["ilegibles"] == 1 and c["cob"] == "INSUFICIENTE" and rc == 3, "caja {} cierra",
         identidad=False)
    # A11 (VAD-05, V2): borde exacto, 2 SIN DATO en 100: SUFICIENTE (el 2 % incluye el borde)
    p = base(n_neg=96)
    for j in range(2):
        p.res[10 + j]["estado"] = "error_K"
    caso("A11", p, lambda rc, c: c["cob"] == "SUFICIENTE" and c["sellado"] == 2, "borde exacto del 2 %")
    # A12 (V3): 100 objetivos, 10 fuera y 2 SIN DATO: el denominador es 90, así que 2 pasa el 2 % (1,8): INSUFICIENTE
    p = base(n_neg=86)
    for j in range(10):
        p.pasada(f"2026-08-{1 + j:02d} 09:00", estado="volcan_fuera_del_granulo")
    for j in range(2):
        p.res[10 + j]["estado"] = "error_K"
    caso("A12", p, lambda rc, c: c["cob"] == "INSUFICIENTE", "denominador sin las fuera")
    # A13 (V4): 99 objetivos + 1 sin gránulo y 1 error de K: denominador 100, 2 SIN DATO: SUFICIENTE
    p = base(n_neg=95)
    p.res[10]["estado"] = "error_K"
    caso("A13", p, lambda rc, c: c["cob"] == "SUFICIENTE" and c["total"] == 2, "denominador con las sin gránulo",
         sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-09-01 05:00", "protegida": False}])
    # A14 (V5): una protegida sin gránulo entre 200: cierra
    p = base(n_neg=196)
    caso("A14", p, lambda rc, c: c["cob"] == "INSUFICIENTE", "protegida sin gránulo cierra",
         sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-09-02 05:00", "protegida": True}])
    # A15 (V6): una protegida con error de K entre 200: cierra
    p = base(n_neg=196)
    p.res[0]["estado"] = "error_K"
    caso("A15", p, lambda rc, c: c["cob"] == "INSUFICIENTE" and c["sellado"] == 1, "protegida SIN DATO cierra")
    # A16 (V7): una sin_crater sin cajas no es «falta caja» (no observada, fuera del denominador)
    p = base(n_neg=95)
    p.pasada("2026-08-23 05:00", cob=COB_SIN_CRATER, sin_caja=CAJAS)
    caso("A16", p, lambda rc, c: c["cob"] == "SUFICIENTE" and c["falta"] == 0 and c["total"] == 0,
         "sin_crater sin cajas no cuenta")
    # A17 (V8): una pasada sin dayflag es SIN DATO del analizador
    p = base(n_neg=95)
    p.pasada("2026-08-24 05:00", dayflag="ausente")
    caso("A17", p, lambda rc, c: c["sellado"] == 1, "dayflag ausente es SIN DATO")

    # L1 a L3 (VAD-01): el lector no deja pasar al analizador si el compañero cierra
    if ev:
        def lector(d, extra=()):
            return correr([sys.executable, str(a.lector), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
                           "--sin-granulo", str(d / "sin_granulo.json"), "--evaluador", str(ev), "--solo-controles",
                           "--censo-omitido-solo-pruebas", "--salida", str(d / "lector.txt"), *extra])
        rc, out = lector(dest / "D1_A1")
        chequear("L1 lector con protegida sin caja: no corre el analizador",
                 rc == 3 and "== compuerta del veredicto" not in out, f"salida {rc}")
        rc, out = lector(dest / "A4")
        # el analizador corre y sale con SU código (aquí 3: la población sintética no trae el control positivo de
        # Cordón Caulle, así que su propia compuerta cierra; eso es del analizador, no del lector)
        chequear("L2 lector con cobertura buena: corre el analizador", rc in (0, 3) and "== compuerta del veredicto" in out
                 and "== LECTOR:" not in out, f"salida {rc}")
        rc, out = lector(dest / "A3", ("--leer-con-faltantes", "prueba"))
        chequear("L3 lector con faltantes declarados: corre el analizador y marca cada línea",
                 "[LEÍDO CON FALTANTES DE LA ADENDA: prueba] == compuerta del veredicto" in out
                 and "\n== compuerta del veredicto" not in out, f"salida {rc}")
        rc, out = lector(dest / "A9", ("--leer-con-faltantes", "prueba"))
        chequear("L4 lector con caja ilegible: no se lee ni con faltantes", rc == 3
                 and "== compuerta del veredicto" not in out, f"salida {rc}")

    for f in filas:
        print(f)
    print("D1, A4 y A6 contra el analizador sellado:", "corridos" if ev else "OMITIDOS (sin --evaluador)")
    if CAIDAS:   # un compañero que se cae no es un compañero que falla por aserción (VA-08)
        print(f"CAÍDA DEL COMPAÑERO en {CAIDAS}")
        return 2
    if fallas:
        print(f"FALLAS ({len(fallas)}): {fallas}")
        return 1
    print(f"TODOS LOS CHEQUEOS COMO SE ESPERA ({len(filas)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
