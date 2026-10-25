# -*- coding: utf-8 -*-
"""S162 V750-A: pruebas del analizador `evaluar_v750a.py` (PREREGISTRO_V750A.md §5 a §7), escritas ANTES del analizador.

POR QUÉ. La regla de adopción de V750-A se aplica una sola vez sobre el censo y otra sobre la sombra; si el analizador
diera un veredicto por una razón que no es la escrita, no se corrige después. Cada escenario arma una población
sintética en el formato que el analizador lee (objetivos + resultados_00.json + pasadas sin gránulo + salida de la
prueba de equivalencia local), corre el analizador ENTERO (predicado del tablero con node incluido) y comprueba SOLO lo
que la regla escrita predice. Contra un analizador vacío cada escenario tiene que fallar POR ASERCIÓN (falta la línea
esperada), no por excepción.

Escenarios (población base B: 5 noches x Láscar y Villarrica con una protegida en T y otras tantas en O, donde P da la
magnitud de MIROVA y K un factor 0,3 a 0,75; 6 negativos limpios por ventana que K publica y P no; en O una protegida de
Cordón Caulle que P publica y P-def no, decidida por la escena; una alerta baja de Láscar que P-def no publica con el
cráter muy sobre los dos umbrales; un negativo lejano que sólo P-sinfiltro publica):
  E00 base: CUMPLE el censo; S-1 nombra la protegida de Cordón Caulle y no la de Láscar; P-sinfiltro +1 contra P.
  E01 P pierde una protegida que K publica (O): NO CUMPLE por P1.
  E02 una protegida que ni K ni P publican: no es veto, se lista; CUMPLE.
  E03 P2 PIERDE en T: NO CUMPLE (no «informar por canal»).
  E04 P2 PIERDE sólo en O: INFORMAR POR CANAL ANTES DE DECIDIR.
  E05 P2 SIN SUSTRATO en T: NO CUMPLE (LECTURA: §6.2 pide GANA o EMPATE).
  E06 P = 1,3 x MIROVA: NO CUMPLE por la razón de M.
  E07 P = K x ganancia uniforme (razón ~1): NO CUMPLE por el comparador.
  E08 P distinto de O fuera de la banda: §6.1 NO SE CUMPLE, sin veredicto del censo (salida 6).
  E09 P distinto de O dentro de la banda: se lista aparte; CUMPLE.
  E10 sin la salida de la equivalencia local: §6.1 NO SE CUMPLE (salida 6).
  E11 equivalencia local con una mutación no atrapada: §6.1 NO SE CUMPLE (salida 6).
  E12 P-def publica la protegida de Cordón Caulle: control positivo de la ROI cae, compuerta cerrada (salida 3).
  E13 el gemelo de K publica 6 negativos que K no: control nulo cae, compuerta cerrada (salida 3).
  E14 K distinto de producción en 2 pasadas: compuerta cerrada (salida 3).
  E15 2 pasadas en error: cobertura INSUFICIENTE, compuerta cerrada (salida 3).
  E16 lo mismo con --leer-con-faltantes: veredicto marcado (salida 5).
  E17 una pasada «ok» a la que le falta el brazo O: cuenta como SIN DATO y cierra la cobertura (es protegida), no
      desaparece en silencio del denominador.
  E18 sombra base: CUMPLE §6.3.
  E19 sombra, P pierde una protegida que K publica: NO CUMPLE.
  E20 sombra sin bloques bajo 1 MW y P1 = 0: CUMPLE sólo por veto (SIN SUSTRATO).
  E21 sombra con P2 PIERDE: NO CUMPLE.
  E22 el archivo de pasadas sin gránulo es de otra lista: cobertura INSUFICIENTE (salida 3).
  E23 sombra con P2 BLOQUEA (neto +2 en 6 bloques): CUMPLE (LECTURA: §6.3 sólo excluye PIERDE).
Uso: python probar_evaluar_v750a.py --dest <carpeta temporal> [--analizador <ruta>] [--evaluador <evaluar_d25.py>]
     [--solo E00,E03]
Salida: 0 si todos los escenarios dan lo esperado; 1 si alguno falla por aserción; 2 si el analizador se cayó en alguno.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SENSOR = "VIIRS_NOAA20_750"
C = 33
CRATER = {"Lascar": [33, 33], "Villarrica": [33, 33], "PuyehueCordonCaulle": [30, 36], "Tupungatito": [33, 33]}

VERDE = """VERDE: E1 1020 casos, E3 10 recortes
   mutación k1_y_minimos         atrapada por aserción (sintético)
   mutación ocho_vecinos         atrapada por aserción (sintético)
   mutación fondo_sin_halo       atrapada por aserción (sintético)
   mutación recorte              atrapada por aserción (sintético)
   mutación fondo_anillo         atrapada por aserción (sintético)
   mutación remuestreo_vecino    atrapada por aserción (sintético)
   mutación control_que_se_cae   caída (RuntimeError)
mutaciones: TODAS COMO SE ESPERA
"""


def diag(c=0.2, u=0.04, sd=0.010, zona=2):
    """Diagnóstico del .m que deja el productor del artefacto para el S-1: sd y umbrales de cada pase y la celda
    decisiva del cráter (contraste NTI y ETI, pase y zona)."""
    p = {"sd_nti": sd, "sd_eti": sd, "u_nti1": u, "u_nti2": u, "u_eti1": u, "u_eti2": u}
    return {"pasada1": dict(p), "pasada2": dict(p),
            "celda_decisiva": {"pase": 1, "zona": zona, "c_nti": c, "c_eti": c}}


def salida_paquete(vrp, volcan, far=False, d=None):
    """Salida del .m (como la del oráculo): npix, vrp_mw, píxeles [fila, col, zona, -, M13] y diagnóstico."""
    if vrp is None:
        return {"npix": 0, "vrp_mw": None, "pixeles": [], "diag": d or diag(c=0.0)}
    f, c = CRATER[volcan]
    if far:
        c += 15                                   # 11,25 km del cráter: fuera de cualquier inner salvo Cordón Caulle
    return {"npix": 1, "vrp_mw": vrp, "pixeles": [[f, c, 2, 0.0, 1.0]], "diag": d or diag()}


def k_record(vrp):
    if vrp is None:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, K=None, P=None, Pdef="=P", O="=P", gemelo="=K", mirova_vrp=None,
               tabla=True, z=20.0, dP=None, dPdef=None, dO=None, far=False, banda=False, estado="ok",
               pub_prod="=K", falta=()):
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "CONS"})
            else:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None,
                          "source": "CONS"})
        Pdef = P if Pdef == "=P" else Pdef
        O = P if O == "=P" else O
        gemelo = K if gemelo == "=K" else gemelo
        pp = (K is not None) if pub_prod == "=K" else pub_prod
        self.objs.append({"id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab,
                          "decide": lab == "pos", "alerta_tabla": lab == "pos" and tabla,
                          "protegida": lab == "pos" and (mirova_vrp or 0) >= 1.0, "mirova": filas,
                          "mirova_vrp": mirova_vrp if lab == "pos" else None, "pub_prod": pp,
                          "pc_vrp": K or 0.0, "z": z, "pos_crater": CRATER[volcan]})
        r = {"id": i, "estado": estado, "dayflag": 0, "cobertura": {"nan_7_crater": 0, "nan_crater": False},
             "brazos": {"K": {"record": k_record(K)}, "Kgemelo": {"record": k_record(gemelo)},
                        "Kgeo": {"record": k_record(K)}, "P": {"record": k_record(P)}},
             "paquete": {"P": salida_paquete(P, volcan, far, dP), "Pdef": salida_paquete(Pdef, volcan, far, dPdef),
                         "O": salida_paquete(O, volcan, far, dO)},
             "banda_triangulacion": banda}
        for b in falta:
            r["paquete"].pop(b, None)
        self.res.append(r)
        return i

    def escribir(self, d, verde=VERDE, sin_granulo_otra_lista=False):
        d.mkdir(parents=True, exist_ok=True)
        art = d / "art"
        art.mkdir(exist_ok=True)
        fo = d / "objetivos.json"
        fo.write_text(json.dumps(self.objs, ensure_ascii=False), encoding="utf-8")
        (art / "resultados_00.json").write_text(json.dumps(self.res, ensure_ascii=False), encoding="utf-8")
        sha = hashlib.sha256(fo.read_bytes()).hexdigest()
        if sin_granulo_otra_lista:
            sha = "0" * 64
        (d / "sin_granulo.json").write_text(json.dumps({"objetivos_sha256": sha, "pasadas": []}), encoding="utf-8")
        if verde is not None:
            (d / "equivalencia_local.txt").write_text(verde, encoding="utf-8")


# factores de K respecto de MIROVA: distintos por volcán para que la mediana de d′ sea negativa en los dos
F_LASCAR = (0.30, 0.35, 0.40, 0.60, 0.70)
F_VILLA = (0.32, 0.38, 0.62, 0.68, 0.75)
M_ALERTA = (2.0, 3.0, 1.5, 4.0, 2.5)


def base(p_de=None, negs_T="gana", negs_O="gana", extra=None, pcc_pdef=None, gemelo_negs=False):
    """Población base. p_de(m, k) da el VRP de P a partir del de MIROVA y del de K (por defecto, el de MIROVA)."""
    p_de = p_de or (lambda m, k: m)
    pb = Pob()
    for v_ in ("T", "O"):
        mes = "2026-04" if v_ == "T" else "2026-07"
        for n in range(5):
            dia = f"{mes}-{10 + n:02d}"
            for vol, F in (("Lascar", F_LASCAR), ("Villarrica", F_VILLA)):
                m = M_ALERTA[n]
                k = round(m * F[n], 3)
                pb.pasada(vol, f"{dia} 06:{10 + 5 * n:02d}", "pos", K=k, P=round(p_de(m, k), 3), mirova_vrp=m)
        modo = negs_T if v_ == "T" else negs_O
        for n in range(6):
            dia = f"{mes}-{20 + n:02d}"
            vol = ("Lascar", "Villarrica", "Tupungatito")[n % 3]
            if modo == "gana":        # K publica y P no: el error es de K
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
            elif modo == "pierde":    # P publica y K no: el error es de P
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=0.2)
            else:                     # ninguno publica: no hay bloque
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=None)
        for n in range(6):            # negativos que nadie publica: sustrato del nulo del contador
            pb.pasada("Lascar", f"{mes}-0{1 + n} 04:00", "neg_limpio", K=None, P=None)
    # O: protegida de Cordón Caulle que P publica y P-def no (control positivo de la ROI), decidida por la escena: el
    # contraste del cráter (0,05) queda entre el umbral de P (0,04) y el de P-def (0,06)
    pb.pasada("PuyehueCordonCaulle", "2026-07-28 06:30", "pos", K=1.2, P=3.0,
              Pdef=3.0 if pcc_pdef == "publica" else None, mirova_vrp=3.0,
              dP=diag(c=0.05, u=0.04), dPdef=diag(c=0.05, u=0.06, sd=0.012), dO=diag(c=0.05, u=0.04), z=35.0)
    # O: alerta baja de Láscar que P-def no publica con el cráter muy sobre los dos umbrales (no la decide la escena)
    pb.pasada("Lascar", "2026-07-29 06:30", "pos", K=0.3, P=0.6, Pdef=None, mirova_vrp=0.6,
              dP=diag(c=0.2, u=0.04), dPdef=diag(c=0.2, u=0.06, sd=0.012))
    # O: negativo lejano que P detecta a 11 km: P no lo publica (far), P-sinfiltro sí
    pb.pasada("Lascar", "2026-07-30 05:00", "neg_limpio", K=None, P=0.4, far=True)
    if gemelo_negs:
        for n in range(6):
            pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 05:00", "neg_limpio", K=None, P=None,
                      gemelo=0.2)
    if extra:
        extra(pb)
    return pb


def esc_sombra(p1=False, negs="gana"):
    """Sombra: sólo K y P (record del perfil sombra), desde el 2026-11-03."""
    pb = Pob()
    for n in range(6):
        dia = f"2026-11-{4 + n:02d}"
        for vol in ("Lascar", "Villarrica"):
            perder = p1 and n == 0 and vol == "Lascar"
            pb.pasada(vol, f"{dia} 06:00", "pos", K=1.0, P=None if perder else 2.0, mirova_vrp=2.0)
    for n in range(6):
        dia = f"2026-11-{12 + n:02d}"
        if negs == "gana":
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
        elif negs == "pierde" or (negs == "bloquea" and n < 4):
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=None, P=0.2)
        elif negs == "bloquea":
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
        else:
            pb.pasada("Lascar", f"{dia} 05:00", "neg_limpio", K=None, P=None)
    for n in range(6):
        pb.pasada("Villarrica", f"2026-11-{20 + n:02d} 05:00", "neg_limpio", K=None, P=None)
    return pb


def _p1_en_O(pb):
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Lascar" and o["hora_utc"].startswith("2026-07-12"))
    for b in ("P", "Pdef", "O"):
        pb.res[j]["paquete"][b] = salida_paquete(None, "Lascar")


def _prot_nadie(pb):
    pb.pasada("Villarrica", "2026-07-31 06:00", "pos", K=None, P=None, mirova_vrp=2.0)


def _p_distinto_de_o(banda):
    def f(pb):
        j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Villarrica"
                 and o["hora_utc"].startswith("2026-07-11"))
        pb.res[j]["paquete"]["O"]["vrp_mw"] += 0.01
        pb.res[j]["banda_triangulacion"] = banda
    return f


def _k_distinto(pb):
    for o in pb.objs[:2]:
        o["pub_prod"] = not o["pub_prod"]


def _errores(pb):
    for r in pb.res[:2]:
        r["estado"] = "error_K"


def _falta_o(pb):
    pb.res[0]["paquete"].pop("O")


def ganancia_uniforme():
    """P = K x g con g fija por ventana igual a 1 / mediana de los factores de K: razón ~1, comparador NEUTRO."""
    import statistics
    g = 1.0 / statistics.median(F_LASCAR + F_VILLA)
    return lambda m, k: k * g


ESCENARIOS = {
    "E00": dict(pob=lambda: base(), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("== compuerta del veredicto", ["ABIERTA"]),
                       ("== §6.1 equivalencia: CUMPLE", []),
                       ("   S-1 al lado del veredicto", ["PuyehueCordonCaulle 2026-07-28 06:30"]),
                       ("== S-1 par (P, Pdef)", ["publicación distinta 2", "decididas por la escena 1",
                                                 "PuyehueCordonCaulle 2026-07-28 06:30", "c/u 1.25/1.25",
                                                 "Δsd nti1 mediana 0.0000 máx 0.0020"]),
                       ("== P-sinfiltro contra P", ["neto 1"])],
                no_tiene=["== §6 censo: NO CUMPLE", "== §6 censo: INFORMAR"],
                no_contiene=[("== S-1 par (P, Pdef)", "Lascar 2026-07-29 06:30")]),
    "E01": dict(pob=lambda: base(extra=_p1_en_O), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P1"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E02": dict(pob=lambda: base(extra=_prot_nadie), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("   protegidas que ni K ni P publican", ["Villarrica 2026-07-31 06:00"])],
                no_tiene=["== §6 censo: NO CUMPLE"]),
    "E03": dict(pob=lambda: base(negs_T="pierde"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P2"])],
                no_tiene=["== §6 censo: CUMPLE", "== §6 censo: INFORMAR"]),
    "E04": dict(pob=lambda: base(negs_O="pierde"), rc=0,
                tiene=[("== §6 censo: INFORMAR POR CANAL ANTES DE DECIDIR", [])],
                no_tiene=["== §6 censo: CUMPLE", "== §6 censo: NO CUMPLE"]),
    "E05": dict(pob=lambda: base(negs_T="nada"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["P2", "SIN SUSTRATO"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    "E06": dict(pob=lambda: base(p_de=lambda m, k: 1.3 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E07": dict(pob=lambda: base(p_de=ganancia_uniforme()), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M comparador"])],
                no_tiene=["== §6 censo: CUMPLE"], no_contiene=[("== §6 censo: NO CUMPLE", "M razón")]),
    "E08": dict(pob=lambda: base(extra=_p_distinto_de_o(False)), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["Villarrica 2026-07-11"])],
                no_tiene=["== §6 censo:"]),
    "E09": dict(pob=lambda: base(extra=_p_distinto_de_o(True)), rc=0,
                tiene=[("== §6.1 equivalencia: CUMPLE", []),
                       ("   P distinto de O dentro de la banda de triangulación", ["Villarrica 2026-07-11"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E10": dict(pob=lambda: base(), verde=None, rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E11": dict(pob=lambda: base(), verde=VERDE.replace("TODAS COMO SE ESPERA", "1 FUERA DE LO ESPERADO"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E12": dict(pob=lambda: base(pcc_pdef="publica"), rc=3,
                tiene=[("== control positivo de la ROI", ["FALLA"]), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E13": dict(pob=lambda: base(gemelo_negs=True), rc=3,
                tiene=[("== control nulo K contra K gemelo", ["FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E14": dict(pob=lambda: base(extra=_k_distinto), rc=3,
                tiene=[("== control K = producción", ["FALLA"]), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E15": dict(pob=lambda: base(extra=_errores), rc=3,
                tiene=[("== cobertura: INSUFICIENTE", []), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    "E16": dict(pob=lambda: base(extra=_errores), args=["--leer-con-faltantes", "prueba sintética"], rc=5,
                tiene=[("== §6 censo: CUMPLE", ["LEÍDO CON FALTANTES"])]),
    "E17": dict(pob=lambda: base(extra=_falta_o), rc=3,
                tiene=[("   SIN DATO por motivo", ["falta_brazo"]), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6 censo:"]),
    "E18": dict(pob=lambda: esc_sombra(), fase="sombra", rc=0, tiene=[("== §6.3 sombra: CUMPLE", [])],
                no_tiene=["== §6.3 sombra: NO CUMPLE"]),
    "E19": dict(pob=lambda: esc_sombra(p1=True), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["P1"])], no_tiene=["== §6.3 sombra: CUMPLE"]),
    "E20": dict(pob=lambda: esc_sombra(negs="nada"), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: CUMPLE", ["SIN SUSTRATO"])]),
    "E21": dict(pob=lambda: esc_sombra(negs="pierde"), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["P2"])], no_tiene=["== §6.3 sombra: CUMPLE"]),
    "E23": dict(pob=lambda: esc_sombra(negs="bloquea"), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: CUMPLE", ["BLOQUEA"])]),
    "E22": dict(pob=lambda: base(), sg_otra=True, rc=3,
                tiene=[("== cobertura: INSUFICIENTE", []), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
}


def correr(nombre, e, analizador, evaluador, dest):
    d = dest / nombre
    pb = e["pob"]()
    pb.escribir(d, verde=e.get("verde", VERDE), sin_granulo_otra_lista=e.get("sg_otra", False))
    cmd = [sys.executable, str(analizador), "--fase", e.get("fase", "censo"), "--art", str(d / "art"),
           "--objetivos", str(d / "objetivos.json"), "--evaluador", str(evaluador),
           "--sin-granulo", str(d / "sin_granulo.json"), "--salida", str(d / "salida.txt")]
    if (d / "equivalencia_local.txt").exists():
        cmd += ["--equivalencia-local", str(d / "equivalencia_local.txt")]
    cmd += e.get("args", [])
    o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    if "Traceback (most recent call last)" in txt:
        return "CAÍDA", [txt.strip().splitlines()[-1][:300]]
    lineas = o.stdout.splitlines()
    fallas = []
    if o.returncode != e["rc"]:
        fallas.append(f"código de salida {o.returncode}, se esperaba {e['rc']}")
    for pref, subs in e.get("tiene", []):
        if not any(l.startswith(pref) and all(s in l for s in subs) for l in lineas):
            fallas.append(f"falta una línea «{pref}» con {subs}")
    for pref in e.get("no_tiene", []):
        if any(l.startswith(pref) for l in lineas):
            fallas.append(f"sobra una línea «{pref}»")
    for pref, s in e.get("no_contiene", []):
        if any(l.startswith(pref) and s in l for l in lineas):
            fallas.append(f"la línea «{pref}» no debería contener «{s}»")
    return ("OK" if not fallas else "FALLA"), fallas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--analizador", default=str(AQUI / "evaluar_v750a.py"))
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura")
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    sel = [x for x in a.solo.split(",") if x] or list(ESCENARIOS)
    L, n_falla, n_caida = [], 0, 0
    for nom in sel:
        est, det = correr(nom, ESCENARIOS[nom], Path(a.analizador), Path(a.evaluador), a.dest)
        n_falla += est == "FALLA"
        n_caida += est == "CAÍDA"
        s = f"{nom} | {est}" + (" | " + " ; ".join(det) if det else "")
        print(s, flush=True)
        L.append(s)
    if n_caida:
        res = f"== PRUEBAS: CAÍDAS {n_caida} (fallas por aserción {n_falla}) de {len(sel)}"
    elif n_falla:
        res = f"== PRUEBAS: FALLAS {n_falla} de {len(sel)}"
    else:
        res = f"== PRUEBAS: TODOS LOS ESCENARIOS COMO SE ESPERA ({len(sel)})"
    print(res)
    L.append(res)
    (a.dest / "probar_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 2 if n_caida else (1 if n_falla else 0)


if __name__ == "__main__":
    sys.exit(main())
