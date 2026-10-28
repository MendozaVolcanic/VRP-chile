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
Cordón Caulle que P publica y P-def no, decidida por la escena (con u1 distinto de u2 en la zona 2); una alerta baja de
Láscar que P-def no publica con el cráter muy sobre los dos umbrales; una alerta baja de Villarrica que P-def no publica
porque cambió el cráter con el mismo umbral; un negativo lejano que sólo P-sinfiltro publica):
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
  E24 P2 BLOQUEA en T (neto +2 en 6 bloques): NO CUMPLE (§6.2 excluye PIERDE y BLOQUEA).
  E25 P2 en T decidido por 6 alertas bajo 1 MW que P publica y K no (sin negativos): CUMPLE.
  E26 protegida sólo del OCR en O que K publica y P no: NO CUMPLE en tabla más OCR y no con la tabla sola.
  E27 O alerta otra celda con el mismo VRP (máscara distinta): §6.1 NO SE CUMPLE (salida 6).
  E23 sombra con P2 BLOQUEA (neto +2 en 6 bloques): CUMPLE (LECTURA: §6.3 sólo excluye PIERDE).
Agregados tras el verificador limpio (verificador/INFORME.md, VA-01 a VA-08), cada uno fija una regla que una rotura de
una línea dejaba pasar:
  E28 una sola pasada no protegida con K distinto de producción entre 109: control OK (hasta 1 %, L18 por D-48), la
      pasada sale de los brazos (P2 en T pasa de 6 a 5 bloques) y se lista; CUMPLE.
  E29 K publica igual pero su VRP difiere 0,01 MW de producción: compuerta cerrada.
  E30 K de 9,0 MW con t_max 270 K: K x 1,2 cae en el filtro de cirro del tablero; la diferencia la explica el filtro
      (t_max bajo 278,15 K), se lista y el control no cae (L7 por D-48); CUMPLE.
  E31 12 protegidas que K no publica y P publica al doble: entran a la razón (L4 por D-48): NO CUMPLE por M razón 2,0;
      la razón sobre las que publican K y P (1,0) se imprime al lado.
  E32 y E33 P = 0,85 y 1,15 x MIROVA: NO CUMPLE por la razón (bordes de la banda).
  E34 2 pasadas sin gránulo del generador: cobertura INSUFICIENTE.
  E35 y E36 con 10 negativos de relleno, 1 pasada en error: SUFICIENTE si no es protegida, INSUFICIENTE si lo es.
  E37 una pasada diurna: SIN DATO «diurna».
  E38 a E41 prueba local con 4 mutaciones atrapadas, sin el control caído, ROJA, o con 100 casos de E1: §6.1 no se cumple.
  E42 --solo-controles: sin veredicto, salida 0.
  E43 6 bloques en 2 noches x 3 volcanes: el bloque de P2 lleva el volcán; GANA.
  E44 T con 2 noches de alertas (4 pares): M SIN SUSTRATO.
  E45 protegida con `decide` falso que P pierde: no es veto; CUMPLE.
  E46 el gemelo de K da la magnitud de MIROVA: el nulo K contra K cae por M.
  E47 sombra con una protegida sólo del OCR que P pierde: NO CUMPLE en tabla más OCR, no con la tabla sola.
  E48 P = 1,3 x MIROVA sólo en T: NO CUMPLE por la razón en T y no en O.
  E49 sombra sin protegidas: CUMPLE marcado «SIN PROTEGIDAS».
Agregados al resolver L2, L4, L7 y L18 por D-48 (relevo VIIRS 750, 2026-10-25):
  E50 dos pasadas no protegidas con K distinto entre 110 (más del 1 %): compuerta cerrada (L18).
  E51 prueba local con 5 mutaciones atrapadas: §6.1 no se cumple (L2: son 6 de 6).
  E52 una sola protegida con el VRP de K distinto de producción entre 110 (bajo el 1 %): cierra igual (L18).
Agregados tras la segunda vuelta del verificador (verificador_v2/INFORME.md, VB-A01 a VB-A07):
  E53 y E54 P = 0,9 y 1,1 x MIROVA: la razón no entra a los motivos (los bordes de la banda están incluidos; el
      comparador da NEUTRO a esa ganancia pareja, conducta de evaluar_d25.py anotada por el verificador).
  E55 la pasada con K distinto (dentro del 1 %) y P distinto de O: §6.1 la sigue mirando y no se cumple (la
      equivalencia P = O se exige sobre todas las observadas, con K o sin K).
  E56 sombra, 1 pasada con K distinto de 24 (más del 1 %): compuerta cerrada. E57 la misma con 114: no cierra, se lista.
  E58 una protegida sólo del OCR con K distinto, entre 111: cierra («ninguna protegida» es tabla más OCR).
  E59 K de 45.000 MW con t_max tibio: K x 1,2 pasa el tope de 50.000 MW del tablero; explicada, se lista y no cierra.
  E60 prueba local con seis líneas «atrapada» pero una de otra pieza: §6.1 no se cumple (las seis se exigen por nombre).
Agregados con los brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27). Tres escenas de píxeles: «cerca y
lejos» (un alertado débil en el cráter y otro más radiante a 11,25 km: radiante y pico lejos, cercano en la cumbre),
«línea» (el más radiante en el cráter y 15 más débiles contiguos hacia el este: el centroide del cúmulo a 5,6 km, fuera
del radio de 5 km; pico y cercano en el cráter) y la de Llaima con el cráter corrido del centro de la grilla:
  E61 6 alertas bajo 1 MW «cerca y lejos»: P-cercano gana en P2' y es elegible; el §6 se evalúa sobre P-cercano (P2 contra
      K en T pasa de neto -6 a -12) y las 6 pasadas que cambian salen por nombre.
  E62 6 bajas «línea» y 6 negativos «cerca y lejos»: P-pico gana solo (P-cercano empata) y el §6 se evalúa sobre él.
  E63 3 bajas «cerca y lejos» (SIN SUSTRATO): ninguno gana y queda P (radiante).
  E64 una protegida «cerca y lejos» que K publica: P y P-pico no son elegibles, P-cercano sí y no es peor: se elige.
  E65 la protegida de E64 y 6 negativos que sólo P-cercano publica (PIERDE): NINGUNA POSICIÓN ELEGIBLE, NO CUMPLE.
  E66 ganan los dos, P-cercano con menor E + E_lejana: se elige P-cercano.
  E67 ganan los dos con el mismo E + E_lejana: se elige P-pico.
  E68 6 bajas que P-cercano gana y 6 far_ref que publica de más: con E_lejana empata y queda P.
  E69 P-cercano gana con el canal que decide (bajas del OCR en O) y con la tabla sola es SIN SUSTRATO con neto +1: no gana.
  E70 Llaima con el cráter a 6,4 km del centro y un alertado en el centro: medido desde el cráter, P-cercano no publica.
  E71 3 far_ref sin alertados que K publica: E_lejana 0 marcado «no dice nada», y las far_ref no entran a P2 contra K.
  E72 base sin far_ref: la vara lejana es SIN DATO y la regla se lee igual (queda P).
  E73 4 alertas sólo del OCR antes del 2026-06-13: no entran a la distancia contra MIROVA (A119).
Agregados tras el verificador limpio de los brazos de posición (verificador_posicion/INFORME.md, LISTO CON CAMBIOS;
W3 y W4 son suyos, W5 adaptado):
  E74 (W3) una protegida sólo del OCR que K y P publican y cercano y pico pierden (escena «anillo»): «elegible» mira
      también tabla más OCR, así que P-cercano no es elegible aunque gane P2' y queda P (radiante).
  E75 (W4) bajas y far_ref sólo del OCR en O: con la tabla sola E_lejana no cuenta los FALSO_POSITIVO_OCR (SIN SUSTRATO
      con neto 0, no peor) y P-cercano gana con el canal que decide (neto -8 en 16 bloques).
  E76 (W5) 24 pasadas que cambian contra P: la lista impresa dice que se cortó a 20 (VP-01).
La población base suma para el S-1: celda de Cordón Caulle en el pase 2 y la zona 2 (el pase 1 y la zona 1 con otro
umbral), una alerta de Tupungatito cuyo NTI cruza entre los umbrales pero el ETI no, y un diagnóstico mal formado.
Una caída nativa del analizador (código fuera de 0, 3, 5 y 6, sin Traceback) se reintenta 2 veces y si sigue es CAÍDA,
nunca falla por aserción (VA-08).
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
CRATER = {"Lascar": [33, 33], "Villarrica": [33, 33], "PuyehueCordonCaulle": [30, 36], "Tupungatito": [33, 33],
          "Llaima": [27, 39]}   # §6 bis (E70): cráter a 6,4 km del centro de la grilla, radio interior de 5 km
PAQ = ("P", "Pdef", "O")

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


def diag(c=0.2, u=0.04, sd=0.010, zona=2, u1=None, c_eti=None, pase=1, u_otro_pase=None):
    """Diagnóstico del .m que deja el productor del artefacto para el S-1: sd y umbrales de cada pase y la celda
    decisiva del cráter (contraste NTI y ETI, pase y zona). u es el umbral de la zona 2 (u2); u1 el de las zonas 0 y 1;
    u_otro_pase, si se da, es TODO umbral del pase que no es el de la celda (para distinguir pase 1 de pase 2)."""
    u1 = u if u1 is None else u1
    p = {"sd_nti": sd, "sd_eti": sd, "u_nti1": u1, "u_nti2": u, "u_eti1": u1, "u_eti2": u}
    q = dict(p) if u_otro_pase is None else {"sd_nti": sd, "sd_eti": sd, "u_nti1": u_otro_pase,
                                             "u_nti2": u_otro_pase, "u_eti1": u_otro_pase, "u_eti2": u_otro_pase}
    pases = {"pasada1": dict(p), "pasada2": dict(q)} if pase == 1 else {"pasada1": dict(q), "pasada2": dict(p)}
    return dict(pases, celda_decisiva={"pase": pase, "zona": zona, "c_nti": c, "c_eti": c if c_eti is None else c_eti})


def salida_paquete(vrp, volcan, far=False, d=None):
    """Salida del .m (como la del oráculo): npix, vrp_mw, píxeles [fila, col, zona, -, M13] y diagnóstico."""
    if vrp is None:
        return {"npix": 0, "vrp_mw": None, "pixeles": [], "diag": d or diag(c=0.0)}
    f, c = CRATER[volcan]
    if far:
        c += 15                                   # 11,25 km del cráter: fuera de cualquier inner salvo Cordón Caulle
    return {"npix": 1, "vrp_mw": vrp, "pixeles": [[f, c, 2, 0.0, 1.0]], "diag": d or diag()}


def k_record(vrp, t_max=300.0):
    if vrp is None:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": t_max, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, K=None, P=None, Pdef="=P", O="=P", gemelo="=K", mirova_vrp=None,
               tabla=True, z=20.0, dP=None, dPdef=None, dO=None, far=False, banda=False, estado="ok",
               pub_prod="=K", falta=(), decide=True, dayflag=0, k_tmax=300.0, px=None, dist_ref=11.0):
        """px (§6 bis): píxeles alertados de P, P-def y O cuando no es el de un solo píxel en el cráter (los tres
        iguales, así la equivalencia P = O se mantiene). lab «far_ref»: MIROVA publicó una fuente lejana (fila
        FALSO_POSITIVO de la tabla, o del OCR con tabla=False, a dist_ref km, y ninguna ALERTA)."""
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "CONS"})
            else:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": mirova_vrp,
                              "dist_km": 0.5, "source": "OCR"})
        elif lab == "far_ref":
            filas.append({"fecha_utc": hora + ":00", "tipo": "FALSO_POSITIVO" if tabla else "FALSO_POSITIVO_OCR",
                          "vrp_mw": 0.5, "dist_km": dist_ref, "source": "CONS" if tabla else "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None,
                          "source": "CONS"})
        Pdef = P if Pdef == "=P" else Pdef
        O = P if O == "=P" else O
        gemelo = K if gemelo == "=K" else gemelo
        pp = (K is not None) if pub_prod == "=K" else pub_prod
        self.objs.append({"id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab,
                          "decide": lab == "pos" and decide, "alerta_tabla": lab == "pos" and tabla,
                          "protegida": lab == "pos" and (mirova_vrp or 0) >= 1.0, "mirova": filas,
                          "mirova_vrp": mirova_vrp if lab == "pos" else None, "pub_prod": pp,
                          "pc_vrp": K or 0.0, "z": z, "pos_crater": CRATER[volcan]})
        if lab == "far_ref":
            self.objs[-1]["dist_ref"] = dist_ref
        r = {"id": i, "estado": estado, "dayflag": dayflag, "cobertura": {"nan_7_crater": 0, "nan_crater": False},
             "brazos": {"K": {"record": k_record(K, k_tmax)}, "Kgemelo": {"record": k_record(gemelo, k_tmax)},
                        "Kgeo": {"record": k_record(K)}, "P": {"record": k_record(P)}},
             "paquete": {"P": salida_paquete(P, volcan, far, dP), "Pdef": salida_paquete(Pdef, volcan, far, dPdef),
                         "O": salida_paquete(O, volcan, far, dO)},
             "banda_triangulacion": banda}
        if px is not None:
            for b in PAQ:
                if r["paquete"][b]["vrp_mw"] is not None:
                    r["paquete"][b]["pixeles"] = copy.deepcopy(px)
                    r["paquete"][b]["npix"] = len(px)
        for b in falta:
            r["paquete"].pop(b, None)
        self.res.append(r)
        return i

    def escribir(self, d, verde=VERDE, sin_granulo_otra_lista=False, sin_granulo=()):
        d.mkdir(parents=True, exist_ok=True)
        art = d / "art"
        art.mkdir(exist_ok=True)
        fo = d / "objetivos.json"
        fo.write_text(json.dumps(self.objs, ensure_ascii=False), encoding="utf-8")
        (art / "resultados_00.json").write_text(json.dumps(self.res, ensure_ascii=False), encoding="utf-8")
        sha = hashlib.sha256(fo.read_bytes()).hexdigest()
        if sin_granulo_otra_lista:
            sha = "0" * 64
        (d / "sin_granulo.json").write_text(json.dumps({"objetivos_sha256": sha, "pasadas": list(sin_granulo)}),
                                            encoding="utf-8")
        if verde is not None:
            (d / "equivalencia_local.txt").write_text(verde, encoding="utf-8")


# factores de K respecto de MIROVA: distintos por volcán para que la mediana de d′ sea negativa en los dos
F_LASCAR = (0.30, 0.35, 0.40, 0.60, 0.70)
F_VILLA = (0.32, 0.38, 0.62, 0.68, 0.75)
M_ALERTA = (2.0, 3.0, 1.5, 4.0, 2.5)


def base(p_de=None, negs_T="gana", negs_O="gana", extra=None, pcc_pdef=None, gemelo_negs=False, p_de_T=None,
         noches_T=5, gemelo_mirova=False, relleno=0):
    """Población base. p_de(m, k) da el VRP de P a partir del de MIROVA y del de K (por defecto, el de MIROVA);
    p_de_T lo reemplaza sólo en la ventana T. noches_T: noches con alertas en T. gemelo_mirova: el gemelo de K da la
    magnitud de MIROVA en las alertas (publica lo mismo que K). relleno: negativos que nadie publica, de más."""
    p_def = p_de or (lambda m, k: m)
    pb = Pob()
    for v_ in ("T", "O"):
        mes = "2026-04" if v_ == "T" else "2026-07"
        p_de = (p_de_T or p_def) if v_ == "T" else p_def
        for n in range(noches_T if v_ == "T" else 5):
            dia = f"{mes}-{10 + n:02d}"
            for vol, F in (("Lascar", F_LASCAR), ("Villarrica", F_VILLA)):
                m = M_ALERTA[n]
                k = round(m * F[n], 3)
                pb.pasada(vol, f"{dia} 06:{10 + 5 * n:02d}", "pos", K=k, P=round(p_de(m, k), 3), mirova_vrp=m,
                          gemelo=m if gemelo_mirova else "=K")
        modo = negs_T if v_ == "T" else negs_O
        for n in range(6):
            dia = f"{mes}-{20 + n:02d}"
            vol = ("Lascar", "Villarrica", "Tupungatito")[n % 3]
            if modo == "gana" or (modo == "bloquea" and n >= 4):   # K publica y P no: el error es de K
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=0.2, P=None)
            elif modo in ("pierde", "bloquea"):                    # P publica y K no: el error es de P
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=0.2)
            elif modo == "gana_misma_noche":   # 6 bloques en 2 noches x 3 volcanes: el bloque lleva el volcán
                pb.pasada(vol, f"{mes}-{20 + n // 3:02d} 05:{n:02d}", "neg_limpio", K=0.2, P=None)
            else:                     # ninguno publica: no hay bloque
                pb.pasada(vol, f"{dia} 05:00", "neg_limpio", K=None, P=None)
        for n in range(6):            # negativos que nadie publica: sustrato del nulo del contador
            pb.pasada("Lascar", f"{mes}-0{1 + n} 04:00", "neg_limpio", K=None, P=None)
    # O: protegida de Cordón Caulle que P publica y P-def no (control positivo de la ROI), decidida por la escena: el
    # contraste del cráter (0,05) queda entre el umbral de P (0,04) y el de P-def (0,06)
    # (celda en el pase 2, zona 2; el pase 1 y la zona 1 tienen umbral 0,10: si el analizador mira otro pase u otra zona,
    # ningún brazo alerta y la marca desaparece)
    pb.pasada("PuyehueCordonCaulle", "2026-07-28 06:30", "pos", K=1.2, P=3.0,
              Pdef=3.0 if pcc_pdef == "publica" else None, mirova_vrp=3.0,
              dP=diag(c=0.05, u=0.04, u1=0.10, pase=2, u_otro_pase=0.10),
              dPdef=diag(c=0.05, u=0.06, sd=0.012, u1=0.10, pase=2, u_otro_pase=0.10),
              dO=diag(c=0.05, u=0.04, u1=0.10, pase=2, u_otro_pase=0.10), z=35.0)
    # O: alerta baja de Láscar que P-def no publica con el cráter muy sobre los dos umbrales (no la decide la escena)
    pb.pasada("Lascar", "2026-07-29 06:30", "pos", K=0.3, P=0.6, Pdef=None, mirova_vrp=0.6,
              dP=diag(c=0.2, u=0.04), dPdef=diag(c=0.2, u=0.06, sd=0.012))
    # O: alerta baja de Villarrica que P-def no publica porque cambió el CRÁTER (0,03 contra 0,05) con el mismo umbral
    pb.pasada("Villarrica", "2026-07-29 06:40", "pos", K=0.25, P=0.5, Pdef=None, mirova_vrp=0.5,
              dP=diag(c=0.05, u=0.04), dPdef=diag(c=0.03, u=0.04))
    # O: alerta baja de Tupungatito que P-def no publica; el NTI de la celda queda entre los dos umbrales pero el ETI
    # (0,01) queda bajo los dos: el .m exige los dos tests, así que el cambio de umbral NO cambia su alerta
    pb.pasada("Tupungatito", "2026-07-29 06:50", "pos", K=0.2, P=0.4, Pdef=None, mirova_vrp=0.4,
              dP=diag(c=0.05, c_eti=0.01, u=0.04), dPdef=diag(c=0.05, c_eti=0.01, u=0.06))
    # O: negativo lejano que P detecta a 11 km: P no lo publica (far), P-sinfiltro sí; P-def sin diagnóstico válido
    pb.pasada("Lascar", "2026-07-30 05:00", "neg_limpio", K=None, P=0.4, far=True, dPdef={"roto": True})
    if gemelo_negs:
        for n in range(6):
            pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 05:00", "neg_limpio", K=None, P=None,
                      gemelo=0.2)
    for n in range(relleno):
        pb.pasada("Villarrica", f"2026-{8 + n // 28:02d}-{1 + n % 28:02d} 04:00", "neg_limpio", K=None, P=None)
    if extra:
        extra(pb)
    return pb


def esc_sombra(p1=False, negs="gana", prot_ocr=False, sin_prot=False):
    """Sombra: sólo K y P (record del perfil sombra), desde el 2026-11-03."""
    pb = Pob()
    for n in range(0 if sin_prot else 6):
        dia = f"2026-11-{4 + n:02d}"
        for vol in ("Lascar", "Villarrica"):
            perder = p1 and n == 0 and vol == "Lascar"
            pb.pasada(vol, f"{dia} 06:00", "pos", K=1.0, P=None if perder else 2.0, mirova_vrp=2.0)
    if prot_ocr:   # protegida sólo del OCR que K publica y P no: P1 en tabla más OCR, no con la tabla sola
        pb.pasada("Villarrica", "2026-11-11 06:30", "pos", K=1.0, P=None, mirova_vrp=2.0, tabla=False)
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
        pb.res[j]["paquete"]["O"]["vrp_mw"] += 1e-5   # sobre la tolerancia de 1e-6 MW, bajo cualquier redondeo
        pb.res[j]["banda_triangulacion"] = banda
    return f


def _bajas_T(pb):
    """6 alertas bajo 1 MW en T que P publica y K no: P2 se decide por las bajas, no por los negativos."""
    for n in range(6):
        pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-05-{10 + n:02d} 06:00", "pos", K=None, P=0.3,
                  mirova_vrp=0.4)


def _prot_solo_ocr(pb):
    """Protegida sólo del OCR en O que K publica y P no: P1 en tabla más OCR, no con la tabla sola."""
    pb.pasada("Villarrica", "2026-07-31 06:40", "pos", K=0.9, P=None, mirova_vrp=2.0, tabla=False)


def _o_otra_celda(pb):
    """O alerta la celda vecina con el mismo VRP: la máscara difiere aunque el VRP no."""
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Villarrica"
             and o["hora_utc"].startswith("2026-07-11"))
    px = pb.res[j]["paquete"]["O"]["pixeles"][0]
    pb.res[j]["paquete"]["O"]["pixeles"] = [[px[0], px[1] + 1] + px[2:]]
    # y la diferencia la explica la escena: la celda (0,05) queda entre el umbral de P (0,04) y el de O (0,06)
    pb.res[j]["paquete"]["P"]["diag"] = diag(c=0.05, u=0.04)
    pb.res[j]["paquete"]["O"]["diag"] = diag(c=0.05, u=0.06)


def _k_distinto_uno(pb):
    """Una sola pasada no protegida con K distinto de producción (§7: «en todas las pasadas ok»)."""
    j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
    pb.objs[j]["pub_prod"] = False


def _k_distinto_dos(pb):
    """Dos pasadas no protegidas con K distinto de producción: más del 1 % de 110 (L18)."""
    js = [i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"]][:2]
    for j in js:
        pb.objs[j]["pub_prod"] = False


def _k_distinto_y_p_distinto_de_o(pb):
    """La pasada con K distinto (negativo de Láscar del 2026-04-20) tiene además una celda que O alerta y P no."""
    _k_distinto_uno(pb)
    j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "Lascar" and o["hora_utc"] == "2026-04-20 05:00")
    pb.res[j]["paquete"]["O"] = salida_paquete(0.1, "Lascar")


def _sombra_k_distinto(relleno):
    def f():
        pb = esc_sombra()
        j = next(i for i, o in enumerate(pb.objs) if o["lab"] == "neg_limpio" and o["pub_prod"])
        pb.objs[j]["pub_prod"] = False
        for n in range(relleno):
            pb.pasada("Villarrica", f"2026-12-{1 + n % 28:02d} {n // 28:02d}:30", "neg_limpio", K=None, P=None)
        return pb
    return f


def _protegida_ocr_k_distinto(pb):
    """Protegida sólo del OCR (O) que K publica pero producción no: K distinto en una protegida."""
    pb.pasada("Villarrica", "2026-08-05 06:40", "pos", K=0.9, P=0.9, mirova_vrp=2.0, tabla=False, pub_prod=False)


def _k_en_el_tope(pb):
    """K de 45.000 MW con t_max 300 K publica; por 1,2 = 54.000 MW el tablero lo lleva a 0 (tope de 50.000 MW)."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=45000.0, P=None, k_tmax=300.0)


def _pc_vrp_distinto(pb):
    """K publica igual que producción pero su VRP difiere en 0,01 MW (más que 0,001)."""
    pb.objs[0]["pc_vrp"] = round(pb.objs[0]["pc_vrp"] + 0.01, 3)


def _placebo_publica_distinto(pb):
    """K de 9,0 MW con t_max 270 K publica; K x 1,2 = 10,8 MW cae en el filtro de cirro del tablero (>10 MW, <273 K)."""
    pb.pasada("Lascar", "2026-07-31 05:30", "neg_limpio", K=9.0, P=None, k_tmax=270.0)


def _protegidas_que_k_no(pb):
    """12 protegidas en O que K no publica y P publica al doble de MIROVA: entran a la razón de §6.2 (L4 por D-48)."""
    for n in range(12):
        pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-08-{10 + n:02d} 06:00", "pos", K=None, P=4.0,
                  mirova_vrp=2.0)


def _un_error(protegida):
    def f(pb):
        j = next(i for i, o in enumerate(pb.objs) if o["protegida"] == protegida)
        pb.res[j]["estado"] = "error_K"
    return f


def _diurna(pb):
    pb.res[0]["dayflag"] = 1


def _prot_no_decide(pb):
    """Protegida que no decide (flag `decide` falso): K la publica y P no, y no es veto."""
    pb.pasada("Villarrica", "2026-07-31 06:20", "pos", K=0.9, P=None, mirova_vrp=2.0, decide=False)


SIN_G = [{"volcan": "Lascar", "hora_utc": "2026-07-31 05:00", "protegida": False},
         {"volcan": "Villarrica", "hora_utc": "2026-07-31 05:10", "protegida": False}]


def _sin_lineas(*claves):
    return "\n".join(x for x in VERDE.splitlines() if not any(k in x for k in claves)) + "\n"


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


# ---------------------------------------------------------------- §6 bis, brazos de posición
def px_cerca_lejos(volcan):
    """Un alertado débil (M13 1,0) en el cráter y uno más radiante (M13 2,0) 15 celdas al este (11,25 km): el cúmulo
    del más radiante y el pico quedan lejos; el más cercano, en la cumbre."""
    f, c = CRATER[volcan]
    return [[f, c, 2, 0.0, 1.0], [f, c + 15, 2, 0.0, 2.0]]


def px_linea(volcan):
    """El alertado más radiante en el cráter y 15 más débiles contiguos hacia el este: el centroide del cúmulo queda a
    7,5 celdas (5,6 km, fuera del radio de 5 km); el pico y el más cercano, en el cráter."""
    f, c = CRATER[volcan]
    return [[f, c, 2, 0.0, 2.0]] + [[f, c + k, 2, 0.0, 1.0] for k in range(1, 16)]


def px_llaima_centro(volcan):
    """E70: un alertado débil en el CENTRO de la grilla (a 6,4 km del cráter de Llaima) y uno más radiante 15 celdas al
    este del cráter. Medido desde el cráter, el más cercano es el del centro y queda lejos; medido desde el centro de la
    grilla quedaría a 0 km."""
    f, c = CRATER[volcan]
    return [[C, C, 2, 0.0, 1.0], [f, c + 15, 2, 0.0, 2.0]]


def _escena(volcan, dias, lab, px, mes="2026-05", hora="06:00", K=None, P=0.3, mirova_vrp=0.4, tabla=True):
    """Una pasada por día (cada una en su propio bloque noche-volcán) con los píxeles de la escena."""
    def f(pb):
        for d in dias:
            pb.pasada(volcan, f"{mes}-{d:02d} {hora}", lab, K=K, P=P, px=None if px is None else px(volcan),
                      mirova_vrp=mirova_vrp if lab == "pos" else None, tabla=tabla)
    return f


def _y(*fs):
    def f(pb):
        for g in fs:
            g(pb)
    return f


def _prot_cerca_lejos(pb):
    """E64: protegida de Láscar en O que K publica; sólo el brazo cercano la publica."""
    pb.pasada("Lascar", "2026-09-01 06:00", "pos", K=1.2, P=3.0, mirova_vrp=3.0, px=px_cerca_lejos("Lascar"))


def px_anillo(volcan):
    """Verificador de posición (W2, W3): borde de un cuadrado de 8 celdas de radio centrado en el cráter. Es 8-conexo y su
    centroide cae EN el cráter (summit para el radiante), pero todos sus píxeles quedan a 6 km o más (far para cercano y
    pico). El más radiante es una esquina."""
    f, c = CRATER[volcan]
    pts = set()
    for k in range(-8, 9):
        pts.update({(f - 8, c + k), (f + 8, c + k), (f + k, c - 8), (f + k, c + 8)})
    px = [[a, b, 2, 0.0, 1.0] for a, b in sorted(pts)]
    px[0][4] = 2.0
    return px


def _prot_ocr_anillo(pb):
    """E74 (W3): protegida de Láscar en O, sólo del OCR, que K y el radiante publican y cercano y pico pierden."""
    pb.pasada("Lascar", "2026-09-01 06:00", "pos", K=1.2, P=3.0, mirova_vrp=3.0, px=px_anillo("Lascar"), tabla=False)


SEIS = range(1, 7)
NEGS_CERCANO = _escena("Villarrica", range(11, 17), "neg_limpio", px_cerca_lejos, hora="05:00")


ESCENARIOS = {
    "E00": dict(pob=lambda: base(), rc=0,
                tiene=[("== §6 censo: CUMPLE", []),
                       ("== compuerta del veredicto", ["ABIERTA"]),
                       ("== §6.1 equivalencia: CUMPLE", []),
                       ("   S-1 al lado del veredicto", ["PuyehueCordonCaulle 2026-07-28 06:30"]),
                       ("== S-1 par (P, Pdef)", ["publicación distinta 4", "decididas por la escena 1",
                                                 "PuyehueCordonCaulle 2026-07-28 06:30", "c/u 1.25/1.25",
                                                 "Δsd nti1 mediana 0.0000 máx 0.0020", "(SIN DATO 1)"]),
                       ("== S-1 par (Pdef, O)", ["publicación distinta 4", "decididas por la escena 1",
                                                 "PuyehueCordonCaulle 2026-07-28 06:30", "(SIN DATO 1)"]),
                       ("== S-1 por pasada", ["filas"]),
                       ("== §6.2 ventana O, canal tabla", ["M comparador MEJORA (pares 14"]),
                       ("== P-sinfiltro contra P", ["neto 1"])],
                no_tiene=["== §6 censo: NO CUMPLE", "== §6 censo: INFORMAR"],
                no_contiene=[("== S-1 par (P, Pdef)", "Lascar 2026-07-29 06:30"),
                             ("== S-1 par (P, Pdef)", "Villarrica 2026-07-29 06:40"),
                             ("== S-1 par (P, Pdef)", "Tupungatito 2026-07-29 06:50")]),
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
    "E24": dict(pob=lambda: base(negs_T="bloquea"), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: P2 BLOQUEA"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E25": dict(pob=lambda: base(negs_T="nada", extra=_bajas_T), rc=0,
                tiene=[("== §6 censo: CUMPLE", [])], no_tiene=["== §6 censo: NO CUMPLE"]),
    "E26": dict(pob=lambda: base(extra=_prot_solo_ocr), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/todo: P1 1"]),
                       ("== §6.2 ventana O, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"])], no_tiene=["== §6 censo: CUMPLE"],
                no_contiene=[("== §6 censo: NO CUMPLE", "O/tabla: P1")]),
    "E27": dict(pob=lambda: base(extra=_o_otra_celda), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["Villarrica 2026-07-11", "decidida por la escena"])],
                no_tiene=["== §6 censo:"]),
    "E28": dict(pob=lambda: base(relleno=60, extra=_k_distinto_uno), rc=0,
                tiene=[("== control K = producción", ["distintas 1 de 109", "OK", "Lascar 2026-04-20"]),
                       ("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -5, bloques 5"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E50": dict(pob=lambda: base(relleno=61, extra=_k_distinto_dos), rc=3,
                tiene=[("== control K = producción", ["distintas 2 de 110", "FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E29": dict(pob=lambda: base(extra=_pc_vrp_distinto), rc=3,
                tiene=[("== control K = producción", ["FALLA"])], no_tiene=["== §6 censo:"]),
    "E30": dict(pob=lambda: base(extra=_placebo_publica_distinto), rc=0,
                tiene=[("== control placebo K×1,2 (publicación)", ["explicadas por los filtros de artefacto del tablero "
                                                                   "(t_max bajo 278.15 K) o su tope de 50000 MW 1", "Lascar 2026-07-31 05:30",
                                                                   "sin explicar 0", "OK"]),
                       ("== compuerta del veredicto", ["ABIERTA"]), ("== §6 censo: CUMPLE", [])]),
    "E31": dict(pob=lambda: base(extra=_protegidas_que_k_no), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["O/tabla: M razón 2.000"]),
                       ("   razón en protegidas que publican K y P", ["1.000"])],
                no_tiene=["== §6 censo: CUMPLE"], no_contiene=[("== §6 censo: NO CUMPLE", "T/tabla: M razón")]),
    "E53": dict(pob=lambda: base(p_de=lambda m, k: round(0.9 * m, 3)), rc=0,
                tiene=[("== §6 censo:", []), ("== §6.2 ventana T, canal tabla", ["M razón en protegidas 0.900"])],
                no_contiene=[("== §6 censo:", "M razón")]),
    "E54": dict(pob=lambda: base(p_de=lambda m, k: round(1.1 * m, 3)), rc=0,
                tiene=[("== §6 censo:", []), ("== §6.2 ventana T, canal tabla", ["M razón en protegidas 1.100"])],
                no_contiene=[("== §6 censo:", "M razón")]),
    "E55": dict(pob=lambda: base(relleno=60, extra=_k_distinto_y_p_distinto_de_o), rc=6,
                tiene=[("== control K = producción", ["distintas 1 de 109", "OK"]),
                       ("== §6.1 equivalencia: NO SE CUMPLE", ["Lascar 2026-04-20 05:00"])], no_tiene=["== §6 censo:"]),
    "E56": dict(pob=_sombra_k_distinto(0), fase="sombra", rc=3,
                tiene=[("== control K = producción", ["distintas 1 de 24", "FALLA"])],
                no_tiene=["== §6.3 sombra: CUMPLE", "== §6.3 sombra: NO CUMPLE"]),
    "E57": dict(pob=_sombra_k_distinto(90), fase="sombra", rc=0,
                tiene=[("== control K = producción", ["distintas 1 de 114", "OK", "Lascar 2026-11-12 05:00"]),
                       ("== §6.3 sombra: CUMPLE", [])]),
    "E58": dict(pob=lambda: base(relleno=62, extra=_protegida_ocr_k_distinto), rc=3,
                tiene=[("== control K = producción", ["distintas 1 de 112", "Villarrica 2026-08-05 06:40", "FALLA"])],
                no_tiene=["== §6 censo:"]),
    "E59": dict(pob=lambda: base(extra=_k_en_el_tope), rc=0,
                tiene=[("== control placebo K×1,2 (publicación)", ["tope de 50000 MW 1", "Lascar 2026-07-31 05:30",
                                                                   "sin explicar 0", "OK"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E60": dict(pob=lambda: base(), verde=VERDE.replace("mutación fondo_anillo ", "mutación otra_pieza   "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["por nombre: 5 de 6"])], no_tiene=["== §6 censo:"]),
    "E52": dict(pob=lambda: base(relleno=61, extra=_pc_vrp_distinto), rc=3,
                tiene=[("== control K = producción", ["distintas 1 de 110", "FALLA"]),
                       ("== compuerta del veredicto", ["CERRADA"])], no_tiene=["== §6 censo:"]),
    "E51": dict(pob=lambda: base(), verde=_sin_lineas("recorte "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["atrapadas 5", "mínimo 6"])], no_tiene=["== §6 censo:"]),
    "E32": dict(pob=lambda: base(p_de=lambda m, k: 0.85 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón 0.850"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E33": dict(pob=lambda: base(p_de=lambda m, k: 1.15 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["M razón 1.150"])], no_tiene=["== §6 censo: CUMPLE"]),
    "E34": dict(pob=lambda: base(), sin_granulo=SIN_G, rc=3,
                tiene=[("   pasadas sin gránulo (del generador): 2", []), ("== cobertura: INSUFICIENTE", [])],
                no_tiene=["== §6 censo:"]),
    "E35": dict(pob=lambda: base(relleno=10, extra=_un_error(False)), rc=0,
                tiene=[("== cobertura: SUFICIENTE", []), ("== §6 censo: CUMPLE", [])]),
    "E36": dict(pob=lambda: base(relleno=10, extra=_un_error(True)), rc=3,
                tiene=[("== cobertura: INSUFICIENTE", [])], no_tiene=["== §6 censo:"]),
    "E37": dict(pob=lambda: base(extra=_diurna), rc=3,
                tiene=[("   SIN DATO por motivo", ["diurna"]), ("== cobertura: INSUFICIENTE", [])]),
    "E38": dict(pob=lambda: base(), verde=_sin_lineas("ocho_vecinos", "recorte "), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["atrapadas 4"])], no_tiene=["== §6 censo:"]),
    "E39": dict(pob=lambda: base(), verde=_sin_lineas("control_que_se_cae"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["control caído False"])], no_tiene=["== §6 censo:"]),
    "E40": dict(pob=lambda: base(), verde=VERDE.replace("VERDE: E1 1020 casos, E3 10 recortes",
                                                       "ROJA: el módulo pipeline.mirova_v750_codigo no existe"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E41": dict(pob=lambda: base(), verde=VERDE.replace("E1 1020 casos", "E1 100 casos"), rc=6,
                tiene=[("== §6.1 equivalencia: NO SE CUMPLE", ["local"])], no_tiene=["== §6 censo:"]),
    "E42": dict(pob=lambda: base(), args=["--solo-controles"], rc=0,
                tiene=[("== sin veredicto: --solo-controles", [])], no_tiene=["== §6 censo:", "== §6.1"]),
    "E43": dict(pob=lambda: base(negs_T="gana_misma_noche"), rc=0,
                tiene=[("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", [])]),
    "E44": dict(pob=lambda: base(noches_T=2), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: M comparador SIN SUSTRATO"])]),
    "E45": dict(pob=lambda: base(extra=_prot_no_decide), rc=0, tiene=[("== §6 censo: CUMPLE", [])]),
    "E46": dict(pob=lambda: base(gemelo_mirova=True), rc=3,
                tiene=[("== control nulo K contra K gemelo", ["FALLA"])], no_tiene=["== §6 censo:"]),
    "E47": dict(pob=lambda: esc_sombra(prot_ocr=True), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: NO CUMPLE", ["todo: P1 1"])],
                no_contiene=[("== §6.3 sombra: NO CUMPLE", "tabla: P1")]),
    "E48": dict(pob=lambda: base(p_de_T=lambda m, k: 1.3 * m), rc=0,
                tiene=[("== §6 censo: NO CUMPLE", ["T/tabla: M razón 1.300"])],
                no_contiene=[("== §6 censo: NO CUMPLE", "O/tabla: M razón")]),
    "E49": dict(pob=lambda: esc_sombra(sin_prot=True), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: CUMPLE", ["SIN PROTEGIDAS"])]),
    "E23": dict(pob=lambda: esc_sombra(negs="bloquea"), fase="sombra", rc=0,
                tiene=[("== §6.3 sombra: CUMPLE", ["BLOQUEA"])]),
    "E22": dict(pob=lambda: base(), sg_otra=True, rc=3,
                tiene=[("== cobertura: INSUFICIENTE", []), ("== compuerta del veredicto", ["CERRADA"])],
                no_tiene=["== §6 censo:"]),
    # ------------------------------------------------------------ §6 bis, brazos de posición
    "E61": dict(pob=lambda: base(extra=_escena("Lascar", SEIS, "pos", px_cerca_lejos)), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) sí", "P-cercano sí", "P-pico sí"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -6, bloques 6)",
                                                  "tabla sola GANA (neto -6, bloques 6)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P-cercano", ["gana contra P"]),
                       ("   §6 bis cambian de publicación contra P (radiante), P-cercano: 6",
                        ["Lascar 2026-05-01 06:00", "baja", "publica"]),
                       ("   §6 bis cambian de publicación contra P (radiante), P-pico: 0", []),
                       ("== §6.2 ventana T, canal tabla", ["posición P-cercano", "P2 contra K GANA (neto -12, bloques 12"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-cercano]"])]),
    "E62": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_linea), NEGS_CERCANO)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide EMPATE (neto 0, bloques 12)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-pico", []),
                       ("== §6.2 ventana T, canal tabla", ["posición P-pico", "P2 contra K GANA (neto -12, bloques 12"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-pico]"])]),
    "E63": dict(pob=lambda: base(extra=_escena("Lascar", (1, 2, 3), "pos", px_cerca_lejos)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide SIN SUSTRATO (neto -3, bloques 3)"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("== §6.2 ventana T, canal tabla", ["posición P (radiante)", "P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P (radiante)]"])]),
    "E64": dict(pob=lambda: base(extra=_prot_cerca_lejos), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) no", "P-cercano sí", "P-pico no"]),
                       ("== §6 bis posición elegida: P-cercano", ["P no es elegible"]),
                       ("== §6.2 ventana O, canal tabla", ["posición P-cercano", "P1 0"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P-cercano]"])],
                no_tiene=["== §6 censo: NO CUMPLE"]),
    "E65": dict(pob=lambda: base(extra=_y(_prot_cerca_lejos, NEGS_CERCANO)), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) no", "P-cercano sí", "P-pico no"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide PIERDE (neto 6, bloques 6)"]),
                       ("== §6 bis posición elegida: NINGUNA POSICIÓN ELEGIBLE", ["P no se adopta"]),
                       ("== §6 censo: NO CUMPLE", ["§6 bis: NINGUNA POSICIÓN ELEGIBLE"])],
                no_tiene=["== §6 censo: CUMPLE"]),
    "E66": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_linea),
                                          _escena("Villarrica", range(11, 17), "pos", px_cerca_lejos))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -12, bloques 12)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-cercano", ["ganan los dos", "menor E + E_lejana"])]),
    "E67": dict(pob=lambda: base(extra=_escena("Lascar", SEIS, "pos", px_linea)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("   §6 bis P2' P-pico", ["canal que decide GANA (neto -6, bloques 6)"]),
                       ("== §6 bis posición elegida: P-pico", ["ganan los dos", "a igual valor, P-pico"])]),
    "E68": dict(pob=lambda: base(extra=_y(_escena("Lascar", SEIS, "pos", px_cerca_lejos),
                                          _escena("Villarrica", SEIS, "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00"))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide EMPATE (neto 0, bloques 12)",
                                                  "tabla sola EMPATE (neto 0, bloques 12)", "E_lejana 6"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("== §6 bis vara lejana: far_ref en los objetivos 6, observadas 6", []),
                       ("   §6 bis pasadas lejanas", ["con algún alertado 6 de 6", "P (radiante) publica 0",
                                                     "P-cercano publica 6", "P-pico publica 0"])],
                no_tiene=["== §6 bis vara lejana: far_ref en los objetivos 6, observadas 6: SIN DATO"]),
    "E69": dict(pob=lambda: base(extra=_y(_escena("Villarrica", range(1, 9), "pos", px_cerca_lejos, mes="2026-09",
                                                  tabla=False),
                                          _escena("Lascar", (1,), "neg_limpio", px_cerca_lejos, hora="05:00"))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -7, bloques 9)",
                                                  "tabla sola SIN SUSTRATO (neto 1, bloques 1)"]),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"])]),
    "E70": dict(pob=lambda: base(extra=_escena("Llaima", SEIS, "pos", px_llaima_centro)), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P (radiante)", [])]),
    "E71": dict(pob=lambda: base(extra=_escena("Lascar", (1, 2, 3), "far_ref", None, hora="05:00", K=0.2, P=None)),
                rc=0,
                tiene=[("== §6 bis vara lejana: far_ref en los objetivos 3, observadas 3", []),
                       ("   §6 bis pasadas lejanas", ["con algún alertado 0 de 3", "un cero de E_lejana no dice nada"]),
                       ("== §6.2 ventana T, canal tabla", ["P2 contra K GANA (neto -6, bloques 6"]),
                       ("== §6 censo: CUMPLE", [])],
                no_tiene=["== §6 bis vara lejana: far_ref en los objetivos 3, observadas 3: SIN DATO"]),
    "E72": dict(pob=lambda: base(), rc=0,
                tiene=[("== §6 bis vara lejana: far_ref en los objetivos 0, observadas 0: SIN DATO", []),
                       ("== §6 bis posición elegida: P (radiante)", ["ninguno gana"]),
                       ("   §6 bis multiplicidad", ["mayor que 5 %"]),
                       ("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                        ["P (radiante) 0.50 km, 0.96, n=24"]),
                       ("== §6 censo: CUMPLE", ["[posición del record: P (radiante)]"])]),
    "E73": dict(pob=lambda: base(extra=_escena("Villarrica", (1, 2, 3, 4), "pos", None, tabla=False)), rc=0,
                tiene=[("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                        ["P (radiante) 0.50 km, 0.96, n=24", "P-cercano 0.50 km, 0.96, n=24"])],
                no_contiene=[("   §6 bis distancia desde la celda central contra MIROVA, alertas con distancia",
                              "n=28")]),
    "E74": dict(pob=lambda: base(extra=_y(_prot_ocr_anillo,
                                          _escena("Lascar", range(10, 16), "pos", px_cerca_lejos, mes="2026-09"))), rc=0,
                tiene=[("== §6 bis elegibles", ["P (radiante) sí", "P-cercano no", "P-pico no"]),
                       ("   §6 bis P2' P-cercano", ["canal que decide GANA"]),
                       ("== §6 bis posición elegida: P (radiante)", [])]),
    "E75": dict(pob=lambda: base(extra=_y(_escena("Villarrica", range(1, 13), "pos", px_cerca_lejos, mes="2026-09",
                                                  tabla=False),
                                          _escena("Lascar", range(15, 19), "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00", tabla=False))), rc=0,
                tiene=[("   §6 bis P2' P-cercano", ["canal que decide GANA (neto -8, bloques 16)",
                                                  "tabla sola SIN SUSTRATO (neto 0, bloques 0)"]),
                       ("== §6 bis posición elegida: P-cercano", ["gana contra P"])]),
    "E76": dict(pob=lambda: base(extra=_y(_escena("Lascar", range(1, 15), "pos", px_linea),
                                          _escena("Villarrica", range(1, 5), "pos", px_cerca_lejos),
                                          _escena("Villarrica", range(11, 17), "far_ref", px_cerca_lejos, mes="2026-09",
                                                  hora="05:00"))), rc=0,
                tiene=[("   §6 bis cambian de publicación contra P (radiante), P-cercano: 24", ["(y 4 más, cortada a 20)"]),
                       ("== §6 bis posición elegida: P-pico", ["ganan los dos", "menor E + E_lejana"])]),
}


def correr(nombre, e, analizador, evaluador, dest):
    d = dest / nombre
    pb = e["pob"]()
    pb.escribir(d, verde=e.get("verde", VERDE), sin_granulo_otra_lista=e.get("sg_otra", False),
                sin_granulo=e.get("sin_granulo", ()))
    cmd = [sys.executable, str(analizador), "--fase", e.get("fase", "censo"), "--art", str(d / "art"),
           "--objetivos", str(d / "objetivos.json"), "--evaluador", str(evaluador),
           "--sin-granulo", str(d / "sin_granulo.json"), "--salida", str(d / "salida.txt")]
    if (d / "equivalencia_local.txt").exists():
        cmd += ["--equivalencia-local", str(d / "equivalencia_local.txt")]
    cmd += e.get("args", [])
    # VA-08 del verificador: una caída nativa del proceso (0xC0000005 bajo carga, sin Traceback) no es una falla por
    # aserción. Los códigos que el analizador puede dar son 0, 3, 5 y 6; cualquier otro es caída. Una caída nativa se
    # reintenta hasta 2 veces y el reintento queda escrito en la salida.
    reint = 0
    while True:
        o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        txt = o.stdout + o.stderr
        nativa = o.returncode not in (0, 3, 5, 6) and "Traceback (most recent call last)" not in txt
        if not nativa or reint >= 2:
            break
        reint += 1
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    if "Traceback (most recent call last)" in txt or o.returncode not in (0, 3, 5, 6):
        return "CAÍDA", [f"código {o.returncode}, reintentos {reint}", (txt.strip().splitlines() or [""])[-1][:300]]
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
    if reint:
        fallas.append(f"(nota: {reint} reintento(s) por caída nativa)")
        return ("OK" if len(fallas) == 1 else "FALLA"), fallas
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
