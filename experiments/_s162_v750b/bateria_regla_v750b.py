# -*- coding: utf-8 -*-
"""Batería de la regla §6 de V750-B, v3 (sellada con el pre-registro): comprueba SOLA el resultado esperado de cada
escenario y sale 1 si alguno no coincide. Suma a la v2 los escenarios V1, V3, V5 y V6 de la segunda vuelta del
verificador (verificador_v2/escenarios_v2.py) y una población base con 3 protegidas de Cordón Caulle que B0 y B5
pierden y B1 publica (el control positivo v3 lo exige). Todos los escenarios llevan --censo-omitido-solo-pruebas, así
que todo veredicto sale con rc 4 y marcado.

v2 (adaptada por la sesión VIIRS 750 tras el verificador): misma batería del verificador V750-B (VB), con los cambios
mínimos para la v2 del analizador: brazo B5, estados error_K y grilla_incompleta del probe v2, bandera
--censo-omitido-solo-pruebas (los escenarios son sintéticos y no hay censo), y las líneas de salida nuevas.
Original: verificador/mutaciones_regla_s6.py (no se modifica).

Verificador V750-B (VB): bateria de mutaciones sinteticas contra la regla §6 de analizar_v750b.py.

POR QUE. La regla de decision se aplica una sola vez sobre un run de 2 h; si puede dar un veredicto por una razon que no
es la del pre-registro, no se puede corregir despues. Aqui se arman poblaciones sinteticas en el formato exacto que deja
el probe (objetivos + resultados_00.json), con publicacion controlada por brazo, y se corre analizar_v750b.py entero
(predicado del tablero con node incluido). Cada escenario predice lo que la regla ESCRITA deberia dar y mira lo que el
codigo da.

Pregunta 1 (si la regla estuviera rota, se ve?): el escenario E0 es el control positivo del instrumento: un brazo que
pierde una protegida TIENE que salir de los elegibles; si no sale, la bateria no mide nada.
Pregunta 2 (instrumento muerto): si analizar_v750b.py no corre o no imprime la linea ROI elegida, el escenario queda
SIN DATO (campos None), no ok.
Uso: python mutaciones_regla_s6.py --arbol <arbol de origin/main con _s162_v750b y evaluar_d25.py del tag> --dest <tmp>
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--arbol", required=True)
ap.add_argument("--dest", required=True, type=Path)
a = ap.parse_args()
A = Path(a.arbol)
ANALIZAR = A / "experiments/_s162_v750b/analizar_v750b.py"
EVAL = A / "experiments/_s157_prereg_d25/evaluar_d25.py"
SENSOR = "VIIRS_SNPP_750"
PUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 1, "n_p2": 0, "npix": 1, "vrp_mw": 0.5,
       "pixeles": [[33, 33, 2, 0.0, 0.9]]}
NOPUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False}
INNER = {"Lascar": 5.0, "PuyehueCordonCaulle": 20.0, "Tupungatito": 7.0}
CELDA = {"Lascar": [32, 33], "PuyehueCordonCaulle": [23, 30], "Tupungatito": [27, 30]}


def k_record(pub, vrp=0.5):
    if not pub:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, pubs, vrp_mirova=None, ocr_vrp=None, tabla=True, k_error=False,
               grilla_incompleta=False):
        """pubs: dict brazo -> publica (K, B0, B1, B2, B3). Protegida si alguna fila ALERTA tiene 1 MW o mas
        (clase_mirova.alerta_protegida no mira la fuente)."""
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova,
                              "dist_km": 0.5, "source": "CONS"})
            if ocr_vrp is not None:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": ocr_vrp,
                              "dist_km": 0.5, "source": "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None,
                          "source": "CONS"})
        alertas = [f for f in filas if f["tipo"].startswith("ALERTA")]
        prot = any((f["vrp_mw"] or 0) >= 1.0 for f in alertas)
        self.objs.append({
            "id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab, "protegida": prot,
            "alerta_tabla": (lab == "pos" and tabla),
            "decide": lab == "neg_limpio" or (lab == "pos" and tabla) or hora >= "2026-06-13",
            "mirova": filas, "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0),
            "z": 30.0, "pub_prod": bool(pubs["K"]) and not k_error, "dc": "summit" if pubs["K"] else None,
            "pc_vrp": 0.5 if pubs["K"] else 0.0, "pc_n": 1 if pubs["K"] else None, "granule": f"g{i}",
            "en_sc": False, "celda_crater": CELDA[volcan], "inner_km": INNER[volcan]})
        if k_error:
            kb = {"error": "RuntimeError: sintetico", "traza": ""}
        else:
            kb = {"record": k_record(pubs["K"]), "pc_pix": [[10, 10]] if pubs["K"] else []}
        r = {"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": 0, "sunglint": 40.0,
             "brazos": {"K": kb}}
        if grilla_incompleta:
            r["oraculo"], r["oraculo_estado"] = {}, "grilla_incompleta"
        else:
            r["cobertura"] = COB
            r["oraculo"] = {b: (PUB if pubs.get(b, pubs["B0"]) else NOPUB) for b in ("B0", "B1", "B2", "B3", "B5")}
        if k_error:
            r["estado"] = "error_K"
        if grilla_incompleta:
            r["estado"] = "grilla_incompleta"
        self.res.append(r)

    def escribir(self, d, sin_granulo=(), sha_ajeno=False):
        """v3: también el archivo de pasadas sin gránulo, atado por sha256 a la lista (VB3-02); sha_ajeno lo ata a otra."""
        import hashlib
        (d / "art").mkdir(parents=True, exist_ok=True)
        (d / "art" / "resultados_00.json").write_text(json.dumps(self.res), encoding="utf-8")
        texto = json.dumps(self.objs)
        (d / "objetivos.json").write_text(texto, encoding="utf-8")
        sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        (d / "sin_granulo.json").write_text(json.dumps(
            {"objetivos_sha256": ("0" * 64) if sha_ajeno else sha, "pasadas": list(sin_granulo)}), encoding="utf-8")


def todos(k=True, b=True):
    return {"K": k, "B0": b, "B1": b, "B2": b, "B3": b}


def base(con_pcc=True):
    """Poblacion comun: 4 protegidas y 3 bajas en T, 4 protegidas y 3 bajas en O, todas publicadas por todos; 10
    negativos limpios en T y 10 en O que nadie publica. v2: con_pcc agrega una protegida de Cordón Caulle en O que
    B0 y B5 no publican (el control positivo de la v2 lo exige para abrir la compuerta; en los datos reales da 7)."""
    p = Pob()
    if con_pcc:   # v3: tres, porque el control positivo pide que B1 publique 3 o más de las que B0 pierde
        for n in range(3):
            p.pasada("PuyehueCordonCaulle", f"2026-09-0{1 + n} 05:00", "pos",
                     {"K": True, "B0": False, "B1": True, "B2": True, "B3": True, "B5": False}, vrp_mirova=1.2)
    for n in range(4):
        p.pasada("Lascar", f"2026-05-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
        p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
    for n in range(3):
        p.pasada("Lascar", f"2026-05-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
        p.pasada("Lascar", f"2026-07-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
    for n in range(10):
        p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
        p.pasada("Lascar", f"2026-08-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
    return p


def correr(nombre, p, sin_granulo=(), sha_ajeno=False):
    d = a.dest / nombre
    p.escribir(d, sin_granulo, sha_ajeno)
    o = subprocess.run([sys.executable, str(ANALIZAR), "--art", str(d / "art"), "--objetivos",
                        str(d / "objetivos.json"), "--evaluador", str(EVAL), "--salida", str(d / "salida.txt"),
                        "--censo-omitido-solo-pruebas", "--sin-granulo", str(d / "sin_granulo.json")],
                       capture_output=True, text=True, cwd=str(A), timeout=600, encoding="utf-8", errors="replace")
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    eleg = re.search(r"6\.1 elegibles.*?:\s*(\[.*?\])", txt)
    roi = re.search(r"ROI elegida: (\S+) \((.*?)\)", txt)
    marca = "[SIN CENSO, NO VALE PARA EL RUN] ROI elegida" in txt
    cob = re.search(r"observadas: (\d+) \| no observadas \(fuera del denominador\): (\{.*?\}) \| SIN DATO: (\d+)",
                    txt)
    prot_sin = re.search(r"protegidas SIN DATO \(falla de cobertura, no de brazo\): (.*)", txt)
    cpos = re.search(r"control positivo: protegidas de Cord.n Caulle que B0 pierde (\d+)", txt)
    p2 = {}
    bloque = txt.rfind("== ventana TO, canal decide")
    if bloque >= 0:
        for m in re.finditer(r"^\s+(B\d)\s+prot.*?P2 contra B1: ([A-Z ]+?) \(", txt[bloque:], re.M):
            p2[m.group(1)] = m.group(2).strip()
    return {"rc": o.returncode, "elegibles": eleg.group(1) if eleg else None, "roi": roi.group(1) if roi else None,
            "motivo": roi.group(2) if roi else None, "cobertura": cob.groups() if cob else None,
            "prot_sin_dato": prot_sin.group(1).strip() if prot_sin else None,
            "control_positivo": cpos.group(1) if cpos else None, "p2_TO_todo": p2, "marca": marca}


out = []


FALLAS = []


def informar(nombre, esperado, r, rc=4, roi="-", en=(), fuera=()):
    """rc esperado; roi esperada ("-" = no se mira; None = sin veredicto); brazos que tienen que estar (en) o no estar
    (fuera) entre los elegibles. Todo veredicto tiene que salir marcado (la bandera de pruebas está puesta)."""
    eleg = r["elegibles"] or ""
    malo = []
    if r["rc"] != rc:
        malo.append(f"rc {r['rc']} != {rc}")
    if roi != "-" and r["roi"] != roi:
        malo.append(f"ROI {r['roi']} != {roi}")
    malo += [f"{b} no elegible" for b in en if f"'{b}'" not in eleg]
    malo += [f"{b} elegible" for b in fuera if f"'{b}'" in eleg]
    if r["roi"] is not None and not r["marca"]:
        malo.append("veredicto sin la marca SIN CENSO")
    if malo:
        FALLAS.append((nombre, malo))
    _informar(nombre, esperado + ("" if not malo else f" | FALLA: {malo}"), r)


def _informar(nombre, esperado, r):
    s = (f"\n== {nombre}\n   esperado por la regla escrita: {esperado}\n"
         f"   codigo: rc={r['rc']} elegibles={r['elegibles']} ROI={r['roi']} ({r['motivo']})\n"
         f"   cobertura (ok, no_obs, SIN DATO)={r['cobertura']} protegidas SIN DATO={r['prot_sin_dato']} "
         f"control positivo={r['control_positivo']}\n   P2 contra B1 (TO, todo): {r['p2_TO_todo']}")
    out.append(s)
    print(s, flush=True)


# E0, control positivo del instrumento: B2 y B0 pierden una protegida de PCC en O. B4 = B1 en PCC, asi que B4 sigue.
p = base()
p.pasada("PuyehueCordonCaulle", "2026-07-05 05:30", "pos",
         {"K": True, "B0": False, "B1": True, "B2": False, "B3": True}, vrp_mirova=1.2)
informar("E0 control positivo: B2 y B0 pierden una protegida de PCC",
         "elegibles sin B0 ni B2 (B4 = B1 en PCC, sigue); control positivo del analizador = 1", correr("E0", p),
         roi="B4", en=("B1", "B3", "B4"), fuera=("B0", "B2", "B5"))

# E1: nadie pierde protegidas; B0 (y por tanto B2 y B4 en Lascar) publica 8 negativos limpios que B1 no publica, en 8
# noches distintas: B0, B2 y B4 PIERDEN contra B1 (p = 1/256). B3 = B1.
p = base()
for n in range(8):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": False, "B2": True, "B3": False})
informar("E1 B4, B2 y B0 PIERDEN contra B1 (8 negativos de mas en 8 bloques); B3 = B1",
         "6.2: nadie GANA; 6.3 cubre empates o BLOQUEA, no PIERDE; un brazo que pierde con p = 1/256 no es igual "
         "desempeno: deberia quedar B1 (o B3), nunca B4", correr("E1", p), roi="B1")

# E2: en T (tabla sola decide) una alerta con CONS 0,6 MW y OCR 1,3 MW; B2 no la publica.
p = base()
p.pasada("Lascar", "2026-05-03 05:00", "pos", {"K": True, "B0": True, "B1": True, "B2": False, "B3": True},
         vrp_mirova=0.6, ocr_vrp=1.3)
informar("E2 protegida SOLO por el OCR en T (CONS 0,6 / OCR 1,3); B2 no la publica",
         "programa 2 y A119: en T decide la tabla sola, no es protegida en T; B2 deberia seguir elegible (pierde "
         "una baja, no una protegida)", correr("E2", p), roi="B4", en=("B2",))

# E3: una protegida en O con error en el brazo K y otra con grilla incompleta.
p = base()
p.pasada("Lascar", "2026-07-30 05:00", "pos", todos(), vrp_mirova=2.0, k_error=True)
p.pasada("Lascar", "2026-07-31 05:00", "pos", todos(), vrp_mirova=2.0, grilla_incompleta=True)
informar("E3 una protegida con error de K y otra con grilla incompleta",
         "las dos en protegidas SIN DATO y en SIN DATO, no en no observadas", correr("E3", p), rc=3, roi=None)

# E4: control positivo del analizador en 0 (ninguna protegida de PCC perdida por B0).
p = base(con_pcc=False)
informar("E4 control positivo del analizador en 0 (B0 no pierde ninguna de PCC)",
         "7: el instrumento no ve la ROI: no deberia imprimirse veredicto", correr("E4", p), rc=3, roi=None)

# E5: B2 y B3 GANAN contra B1 (apagan 6 negativos que B1 publica); B2 ademas pierde 2 bajas (E mayor).
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": True, "B2": False, "B3": False})
for n in range(2):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {"K": True, "B0": True, "B1": True, "B2": False, "B3": True}, vrp_mirova=0.4)
informar("E5 B2 y B3 GANAN contra B1; B2 con mas E", "6.2: el de menor E en T u O: B3", correr("E5", p), roi="B3")

# E6: B2 GANA en el canal todo pero PIERDE en el canal tabla (los negativos que apaga... no: las bajas que pierde son
# de la tabla y los negativos que apaga son de noches cuya alerta... ). Version simple: B2 apaga 6 negativos de B1
# (gana en los dos canales) y pierde 6 bajas que solo el OCR trae en O (no cuentan en tabla). Que decide el codigo?
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": True, "B2": False, "B3": True})
for n in range(6):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {"K": True, "B0": True, "B1": True, "B2": False, "B3": True}, tabla=False, ocr_vrp=0.4)
informar("E6 B2 apaga 6 negativos de B1 y pierde 6 bajas que solo el OCR trae (O)",
         "con todo: neto 0 (EMPATE); con la tabla sola: GANA. 6.2 no dice que canal decide", correr("E6", p), roi="B4", en=("B2",))

# E7: un negativo limpio cuyo brazo K vino con record None (calculate_vrp devuelve None con ROI vacia,
# process_viirs_mod.py:541-542, o el store no escribe, probe_n.guardar_como_store). En N fue 0 de 510, pero el run tiene
# ~6.900. Que hace el analizador con una sola?
p = base()
p.pasada("Lascar", "2026-08-25 05:00", "neg_limpio", todos(b=False, k=False))
p.res[-1]["brazos"]["K"] = {"record": None, "pc_pix": [], "segundos": 1.0, "contadores": None}
informar("E7 un negativo con record de K = None (ROI vacia o store sin escribir)",
         "la pasada deberia quedar SIN DATO para K y el resto seguir; el analizador no deberia caerse", correr("E7", p), roi="B4")

# ---------------------------------------------------------------- escenarios de la segunda vuelta (verificador_v2)
# V1 (VB2-01): B2 EMPATA en el canal que decide pero PIERDE con la tabla sola; B0 (y B4 en Láscar) pierden en los dos.
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B0": True, "B2": True})
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {**todos(), "B1": False, "B3": False, "B0": False, "B5": False, "B2": True}, tabla=False, ocr_vrp=0.4)
informar("V1 B2 EMPATA con el canal que decide pero PIERDE con la tabla sola", "§6.3: B2 no puede ser elegido",
         correr("V1", p), roi="B1")
# V3 (VB2-02): B2 y B0 (y B4 en Láscar) publican 4 negativos de más en 4 noches: SIN SUSTRATO con neto +4.
p = base()
for n in range(4):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True, "B0": True})
informar("V3 SIN SUSTRATO con neto en contra", "§6.3: un brazo peor en todos los bloques no se elige por fidelidad",
         correr("V3", p), roi="B1")
# V6 (VB2-06): oráculo muerto (ningún brazo publica, producción sí): el control positivo tiene que cerrar la compuerta.
p = Pob()
muerto = {"K": True, "B0": False, "B1": False, "B2": False, "B3": False, "B5": False}
for n in range(3):
    p.pasada("PuyehueCordonCaulle", f"2026-09-0{1 + n} 05:00", "pos", muerto, vrp_mirova=1.2)
for n in range(6):
    p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", muerto, vrp_mirova=1.5)
for n in range(10):
    p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
informar("V6 oráculo muerto", "sin veredicto", correr("V6", p), rc=3, roi=None)

# ---------------------------------------------------------------- escenarios de la tercera vuelta (verificador_v3)
# S1 (mata M2): B2 GANA con el canal que decide (15 bajas sólo del OCR que B1 no publica) pero PIERDE con la tabla sola
# (6 negativos de más): §6.2 no lo deja ganar y §6.3 no lo admite. ROI B4.
p = base()
for n in range(15):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "pos",
             {**todos(), "B1": False, "B0": False, "B3": False, "B5": False, "B2": True}, tabla=False, ocr_vrp=0.4)
for n in range(6):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True})
informar("S1 B2 gana con el canal que decide y pierde con la tabla sola", "§6.2 y §6.3: B2 fuera; ROI B4",
         correr("S1", p), roi="B4")
# S2 (mata M3): B0 (B4 en Láscar) no publica 4 bajas sólo del OCR: con el canal que decide SIN SUSTRATO neto +4; con la
# tabla sola, 0 bloques. §6.3: B4 no entra; ROI B2 (igual a B1 aquí).
p = base()
for n in range(4):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "pos", {**todos(), "B0": False, "B5": False}, tabla=False, ocr_vrp=0.4)
informar("S2 B4 peor con el canal que decide y no peor con la tabla", "§6.3: B4 fuera; ROI B2", correr("S2", p), roi="B2")
# E5b (mata M7): B3 y B2 GANAN de verdad; B2 con más E. B3 apaga 8 negativos que B1 publica; B2 apaga los mismos y además
# pierde 1 baja (neto -7 en 9 bloques, p 10/512). §6.2: el de menor E, B3.
p = base()
for n in range(8):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B1": True, "B0": True,
                                                                    "B5": True})
p.pasada("Lascar", "2026-09-20 05:00", "pos", {**todos(), "B2": False}, vrp_mirova=0.3)
informar("E5b B2 y B3 ganan de verdad; B2 con más E", "§6.2: el de menor E, B3", correr("E5b", p), roi="B3")
# E3b (mata M9): una protegida con grilla incompleta en una población de más de 100 pasadas (bajo el 2 %): la protegida
# SIN DATO frena sola la lectura.
p = base()
for n in range(80):
    p.pasada("Lascar", f"2026-08-{1 + n % 28:02d} 0{n // 28}:30", "neg_limpio", todos(b=False, k=False))
p.pasada("Lascar", "2026-07-30 05:00", "pos", todos(), vrp_mirova=2.0, grilla_incompleta=True)
informar("E3b una protegida SIN DATO bajo el 2 %", "sin veredicto", correr("E3b", p), rc=3, roi=None)
# K distinta (mata M10): producción no publicó una protegida que el K del run sí publica: K = producción cierra.
p = base()
p.objs[5]["pub_prod"] = False
informar("KD una protegida con K distinto de producción", "sin veredicto", correr("KD", p), rc=3, roi=None)
# SG (mata M5): una protegida sin gránulo en el archivo del generador frena la lectura.
informar("SG una protegida sin gránulo", "sin veredicto",
         correr("SG", base(), sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-07-01 05:00", "lab": "pos",
                                            "protegida": True}]), rc=3, roi=None)
# SGx (VB3-02): el archivo de pasadas sin gránulo es de otra lista de objetivos: SIN DATO, sin veredicto.
informar("SGx archivo sin gránulo de otra lista", "sin veredicto", correr("SGx", base(), sha_ajeno=True), rc=3, roi=None)

(a.dest / "mutaciones_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n== BATERÍA:", "TODOS LOS ESCENARIOS COMO SE ESPERA" if not FALLAS else f"FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)
