# ════════════════════════════════════════════════════════════════════
# FICHA SDA · mirova_v750_codigo.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Vía de proceso «código MIROVA» para VIIRS 750 m (M13/M15) y para MODIS (B22 con B21 donde satura,
#                 B31; S164, MOD-D fase 3): ver el volcán como lo ve MIROVA, interpolado a su grilla fija, con su
#                 detector, su fondo y su suma. APAGADA por flag en cada sensor (enable_v750_codigo_mirova, S162;
#                 enable_modis_codigo_mirova, S164); con los flags apagados no corre nada de este archivo.
#                 ⚠️ S190 (F1M-113): APAGADA es el valor por defecto de profile.py; producción (mirova_equivalent)
#                 la ENCIENDE en los tres sensores: MODIS desde S172, VIIRS 375 y 750 desde S186 (ficha v1.18 y v1.23 a v1.25).
# Lógica        : (1) remuestreo lineal del gránulo a la grilla UTM de MIROVA del volcán (regla GEO, S159);
#                 (2) MIROVA_VIIRS750_hotspot_detection.m: NTI absoluto (K1 -0,7) + dos pasadas contextuales
#                 de NTI y ETI con umbral max(mu + s*sd, piso) por región; (3) MIROVA_VIIRS750_VRP.m: fondo por
#                 interpolación lineal bajo un halo dilatado, sin recorte, sumado sobre TODOS los alertados.
# Modelo/método : Port literal del código operacional de MIROVA (Coppola, OSF zm62w, MIT). Reglas físicas
#                 deterministicas, sin ML (punto 5.5 Res.372).
# Datos entrada : Radiancia VIIRS M13 (4,05 um) y M15 (10,76 um) del L1B y geolocalización del L1B GEO; en MODIS,
#                 radiancia B22 (3,959 um, con B21 donde B22 satura) y B31 (11,03 um) del MxD021KM y geolocalización
#                 de 1 km del MxD03. SIN datos personales.
# Variables     : NTI, contraste NTI y ETI contra la media 3 x 3, umbrales por región (BOX), fondo M13
#                 interpolado, VRP = suma de (L - L_fondo) x 1,97e7 x 0,5625 / 1e6 (V750) o x 1,89e7 x 1,0 / 1e6
#                 (MODIS, Coppola 2016a Ec. 7).
#                 Diagnóstico sin efecto en la detección (S190): dato faltante sobre el cráter medido en los
#                 píxeles del gránulo ANTES de interpolar (crater_sin_posicion, px_mir_invalido_crater,
#                 px_saturados_crater). S193 (bow-tie de VIIRS): px_bowtie_crater separa el relleno que VIIRS
#                 descarta a bordo en el borde del barrido (bit 256 de quality_flags; ese suelo lo midió el barrido
#                 contiguo) del dato perdido, y px_mir_hueco_crater y px_tir_hueco_crater cuentan el hueco por banda.
#                 Fondo no estimable (S192, F4-101; decisión de Nicolás del 2026-11-20): si ningún alertado tiene fondo,
#                 en MODIS la escena es no medida (motivo_vacio «fondo_no_estimado», 0 MW); en VIIRS se publica como el
#                 .m y el record cuenta alertados_sin_fondo. t_bg_k promedia sólo los alertados con fondo.
#                 Sin radiancia (S192, run 44768057665): si en el recorte una banda tiene menos de tres píxeles
#                 con radiancia válida (escaneos enteros con DN de relleno aunque el GEO traiga posición), la
#                 escena es no medida (motivo_vacio «sin_radiancia_valida», 0 MW) en vez de una excepción.
#                 Cráter no evaluado (S193, F3-107): escena válida sin alertados en la que ninguna celda del 7 x 7 del
#                 cráter tuvo contraste que evaluar (hueco o nube fría): motivo_vacio «crater_no_evaluado», 0 MW.
#                 Sin ángulo (S199, F8-107, F3-102, R3F3-102; acta de cierre de la auditoría Codex): si en el píxel más
#                 cercano al centro falta, es NaN o es relleno alguno de los cuatro ángulos (cenit y azimut del sol y
#                 del satélite), no se sabe si es de noche ni cuánto reflejo hay: motivo_vacio «angulo_ausente», 0 MW.
#                 diag_codigo_mirova.roi nombra la caja usada («c13_crater» en VIIRS 375; S193, F2-V303).
#                 Zona A del laboratorio (S195; nunca en producción, que no la enciende): sólo con un perfil que la
#                 encienda (laboratorio y su barrido _s195_lab_*), de noche, en las celdas de la región sensible a no
#                 más de inner_radius_km del cráter, el multiplicador s2 = 5 pasa a s_A <= 5 (mismos pisos, mismos mu y
#                 sd); con s_A = 5 el resultado es el de producción bit a bit. Cordón Caulle fuera.
#                 S196 (palanca del piso, experiments/_s196_lab_piso/PREREGISTRO.md): en la misma zona y sólo de
#                 noche, el piso de NTI y ETI (0,003) puede bajar a p_A, 0 < p_A <= 0,003, con s = s_A; con s_A = 5 y
#                 p_A = 0,003 el resultado es el de producción bit a bit. Sólo los perfiles _s196_lab_* lo declaran.
# Limitaciones  : fillmissing2 de MATLAB no documenta su triangulación; se reproduce con un Delaunay de desempate
#                 simbólico que iguala a MATLAB R2026b en 166 de 166 escenas (S163 O2), sin que el mecanismo interno
#                 de MATLAB esté verificado. La ROI por volcán la decide V750-B. El umbral contextual depende de la
#                 sigma de TODA la grilla (S-1). En MODIS es SOSPECHA que MIROVA use este mismo .m (lo publicado es
#                 el de VIIRS 750): la vía es el paquete que midió el censo MOD-D (S162), umbrales del .m incluidos.
# Refs/datos    : MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m (copia con hashes en
#                 experiments/_s158_d17_diseno/osf_codigo_mirova/); oráculo validado contra Octave en 791 de 791
#                 escenas (S159 O1). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""Vía «código MIROVA» para VIIRS 750 m (S162, V750-A). Apagada por defecto.

Port de MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m, código operacional de MIROVA publicado por
Diego Coppola en OSF (https://osf.io/zm62w/, doi 10.17605/OSF.IO/ZM62W), v1.0, bajo licencia MIT:

    Copyright (c) Diego Coppola. Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute,
    sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions: The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT
    WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. (Texto completo: experiments/_s158_d17_diseno/osf_codigo_mirova/
    LICENSE.txt.)

La traducción sigue, línea por línea, al oráculo `experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`, salvo el
`fillmissing2`, que aquí es el de MATLAB (desempate simbólico; ver más abajo): la prueba
`experiments/_s162_v750a/equivalencia_v750a.py` exige la misma máscara índice por índice, la misma grilla y el mismo
VRP a 1e-9 relativo que ese oráculo con el mismo `fillmissing2`, y `tests/test_mirova_v750_codigo_s162.py` y
`experiments/_s162_v750a/oro_fillmissing2_o2.py` comparan el fondo y el VRP contra las salidas de MATLAB de O2. Lo que se agrega al oráculo no cambia ninguna
máscara: la grilla por volcán (regla GEO), la caja por volcán, el record con el esquema de hoy y los contrastes de la
celda decisiva para el diagnóstico S-1 (PREREGISTRO_V750A.md §5).

Interfaz (contrato de la prueba de equivalencia): detectar_mirova, vrp_mirova, remuestrear_grilla. Pensada para que
VIIRS 375 la reutilice: la grilla sale de la misma regla con otro paso (grilla_del_volcan(..., paso_m=375)), la caja
se arma con caja_roi(..., n=134, lado_sensible=13) en el cráter, y el coeficiente del VRP es un argumento.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np

# Constantes de Planck del código operacional (.m l. 410-412 y 430-432), NO las CODATA de pipeline/constants.py:
# la vía tiene que reproducir los números de MIROVA, y MIROVA usa estas.
_H = 6.6256e-34
_C = 2.9979e8
_K = 1.38e-23
LAMBDA_M13 = 4.05     # .m l. 144
LAMBDA_M15 = 10.763   # .m l. 145

# VRP (MIROVA_VIIRS750_VRP.m l. 88-91): coeficiente de Wooster 1,97e7 por el área de la celda de 750 m en km²
COEF_VRP_V750 = 1.97e7 * 0.5625 / 1e6
# MODIS (S164, MOD-D fase 3): banda 22 a 3,959 um (Coppola 2016a, sp426_5.txt l. 176-177) y RP = 18,9 x A_pix x dL
# con A_pix = 1 km² nadir fijo (sp426_5.txt l. 374; CLAUDE.md «Reglas científicas», S14). La TIR es la banda 31 a
# 11,03 um, la de producción y la del censo MOD-D; el NTI del paper usa la banda 32 (l. 214-216), divergencia D20 que la
# vía hereda (verificador S164, V164-02).
LAMBDA_MODIS_B22 = 3.959
LAMBDA_MODIS_B31 = 11.03
COEF_VRP_MODIS = 1.89e7 * 1.0 / 1e6
# VIIRS 375 (S165, V375-E): bandas I4 a 3,74 um e I5 a 11,45 um (pipeline/process_viirs.py, I04_LAMBDA y la inversión
# de Planck de I05) y RP = 18,0 x A_pix x dL con A_pix = 0,140625 km² nadir fijo (CLAUDE.md «Reglas científicas», S14,
# validado contra el OSF de MIROVA). Son los números del port de V375-B/C (experiments/_s159/portes/mirova_port.py,
# SENSORES["VIIRS375"]).
LAMBDA_I4 = 3.74
LAMBDA_I5 = 11.45
COEF_VRP_V375 = 1.80e7 * 0.140625 / 1e6

PASO_V750_M = 750.0
PASO_MODIS_M = 1000.0
PASO_V375_M = 375.0
# ROI1 de VIIRS 375: la «física» de S159, el mismo tamaño en metros que el anillo de 21 celdas de 750 m del .m (±7.875 m
# alrededor de X0, Y0), o sea 42 x 42 celdas de 375 m (mirova_port.HALF_ROI1_M).
HALF_ROI1_V375_M = 10.5 * 750.0
MEDIA_GRILLA_M = 25000.0   # regla GEO: centros en X0 - 25000 : paso : X0 + 25000
RADIO_RECORTE_KM = 45.0    # como probe_n.grillar: sólo se interpolan los píxeles a menos de 45 km
# S192: mínimo de píxeles con radiancia finita (por banda, en el recorte) para que la interpolación lineal exista: 
# una triangulación de Delaunay en el plano pide tres puntos no colineales. Con menos, la escena es no medida
# (motivo_vacio «sin_radiancia_valida», calcular_vrp_granulo). Es geometría, no un umbral físico.
MIN_PX_TRIANGULAR = 3
# S192: ya no es el corte. Era «DN >= 65528 son banderas» (UserGuide Aug 2021, uint16); el lector usa el valid_max de
# cada variable (pipeline/banderas_viirs_l1b.py), porque M13 de VJ202MOD v2.1 viene en uint32 y el corte fijo borraba
# M13 sobre unos 512 K. Se conserva el nombre para los verificadores que lo leen (experiments/_s164_modis_codigo).
FLAG_MIN_DN = 65528
# Bit de saturación de <banda>_quality_flags del L1B de VIIRS: «bit value» 4 de la Tabla C.1 del UserGuide (transcrita
# en docs/F28_SATURATION_INVESTIGATION.md), el mismo SAT_BIT_MASK = 0b100 que lee la guardia K
# (process_viirs.py, process_viirs_mod.py). Sólo diagnóstico: la vía no enmascara el píxel saturado.
BIT_SATURACION_VIIRS = 0b100
# Bit «Bowtie_Deleted» de <banda>_quality_flags (Tabla C.1 del UserGuide VIIRS L1B Aug 2021: bit value 256). Se lee el
# bit y no el DN de bandera porque M13 no lo codifica como 65533: en VJ202MOD_NRT v2.1 los píxeles bow-tie de M13 traen
# DN 327678 (probe S192, run 44818788733), mientras I04, I05 y M15 traen 65533 como dice el UserGuide (págs. 21 y 23).
# Sólo diagnóstico (S193): la radiancia del píxel bow-tie sigue en NaN, como toda bandera.
BIT_BOWTIE_VIIRS = 0b100000000
# Radio, en celdas de la grilla del sensor, dentro del cual un píxel perdido cuenta como dato faltante del cráter
# (plan F1M-G3 del 2026-11-19): 2 km en MODIS, 1,5 km en VIIRS 750, 0,75 km en VIIRS 375. Es una decisión de
# diagnóstico, no un valor de MIROVA: cubre el píxel del cráter y sus vecinos inmediatos con cualquier desorden
# de barrido cerca del nadir.
CELDAS_DATO_CRATER = 2
TIPOS_ROI = ("def", "sens", "crater", "inner", "corona")
# S193 (F2-V303): nombre que el diagnóstico da a la caja de VIIRS 375, que no es ninguna de TIPOS_ROI: caja_v375, la C13
# (13 x 13 celdas de 375 m) sobre el cráter dentro de la ROI1 física. Sólo etiqueta; no elige nada.
ROI_DIAG_V375 = "c13_crater"
# S193 (F3-107, F3-V201): motivo_vacio de la escena válida en la que el detector corrió pero no pudo evaluar ninguna
# celda del 7 x 7 del cráter (celda_decisiva nula) y no alertó en ninguna parte. Ver procesar_grilla.
MOTIVO_CRATER_NO_EVALUADO = "crater_no_evaluado"
# S199 (F8-107 y F3-102 de la auditoría Codex ronda 2, R3F3-102 de la ronda 3; acta de cierre aprobada por Nicolás,
# docs/ACTA_CIERRE_AUDITORIA_CODEX_2026-11-24.md: «marcar "sin ángulo" como escena no medida»): motivo_vacio de la
# pasada en que falta alguno de los cuatro ángulos que deciden la noche y el reflejo solar. Ver calcular_vrp_granulo.
MOTIVO_ANGULO_AUSENTE = "angulo_ausente"
# Los cuatro ángulos de observación que la vía lee del píxel más cercano al centro de la grilla, con su rango físico en
# grados (cenit de 0 a 180; azimut de -180 a 360, para aceptar las dos convenciones). Es geometría, no un umbral de
# MIROVA: fuera de ese rango un ángulo no existe. El relleno de NASA escalado (int16 -32768 o -32767 por 0,01, o sea
# -327,68 o -327,67) cae fuera, y por eso basta el rango para reconocerlo sin leer el _FillValue de cada producto.
RANGO_ANGULOS = {"sensor_zenith": (0.0, 180.0), "sensor_azimuth": (-180.0, 360.0),
                 "solar_zenith": (0.0, 180.0), "solar_azimuth": (-180.0, 360.0)}

_GRILLAS_YAML = Path(__file__).resolve().parent / "grillas_mirova.yaml"

# Lo único que el .m hace depender del sensor, más lo que vive fuera del .m (grilla, caja, lectura). POR QUÉ una tabla
# y no una copia del módulo para MODIS: una lógica copiada en línea diverge (A102); así VIIRS 750 y MODIS corren las
# mismas funciones y sólo cambian estos números. La caja de MODIS es la «fisica» del censo MOD-D: el mismo tamaño en
# metros que la de 750 m (±2.625 m sensible, ±7.875 m conservadora alrededor de X0, Y0), o sea 5 x 5 y 15 x 15 celdas
# de 1 km (experiments/_s159/portes/mirova_port.py::caja). dist_max_centro_km: como el probe del censo, si el píxel más
# cercano al centro de la grilla está a más de 5 km el volcán quedó fuera del gránulo (VIIRS 750 no tiene ese corte).
FAMILIAS = {
    "VIIRS750": {"paso_m": PASO_V750_M, "lam_mir": LAMBDA_M13, "lam_tir": LAMBDA_M15, "coef": COEF_VRP_V750,
                 "lado_sensible": 7, "lado_anillo": 21, "bandas": ("M13", "M15"), "clave_roi": "roi_v750",
                 "dist_max_centro_km": None},
    "MODIS": {"paso_m": PASO_MODIS_M, "lam_mir": LAMBDA_MODIS_B22, "lam_tir": LAMBDA_MODIS_B31, "coef": COEF_VRP_MODIS,
              "lado_sensible": 5, "lado_anillo": 15, "bandas": ("MIR", "TIR"), "clave_roi": "roi_modis",
              "dist_max_centro_km": 5.0},
    # VIIRS 375 (S165): la caja no sale del yaml sino de PD1 (C13 en todos, S164 bajo D-48), ver caja_v375; el corte de
    # 5 km al centro es el del probe de V375-B/C (experiments/_s162_v375/probe_v375.py).
    "VIIRS375": {"paso_m": PASO_V375_M, "lam_mir": LAMBDA_I4, "lam_tir": LAMBDA_I5, "coef": COEF_VRP_V375,
                 "lado_sensible": 13, "lado_anillo": None, "bandas": ("I04", "I05"), "clave_roi": "roi_v375",
                 "dist_max_centro_km": 5.0, "roi1_half_m": HALF_ROI1_V375_M},
}

# ---------------------------------------------------------------------------------------------------- miniatura
# S184 (docs/DISENO_MINIATURAS_POR_PASADA.md): una imagen chica de cada pasada para las «Últimas 10 imágenes» del
# tablero, como el panel Latest10NTI de MIROVA. POR QUÉ: una pasada con VRP 0 no dice si el volcán estaba tranquilo,
# nublado o con la escena cortada en el borde de la franja; la imagen sí. NO decide nada: no toca la máscara, el VRP ni
# el record (sólo agrega una clave interna que scripts/run_pipeline.py saca antes de guardar). APAGADA por defecto,
# porque 49 archivos (pruebas, experimentos, probes) llaman a la vía o a los procesadores y ninguno debe ver la clave;
# la enciende sólo `run_pipeline.py --miniaturas`, que sólo usa el NRT de producción (nrt.yml).
GENERAR_MINIATURA = False
# Escala fija del gris: el NTI de un cuerpo negro a 240 K (negro) y a 300 K (blanco) con las longitudes de onda de cada
# sensor y la Planck del .m. POR QUÉ fija y no estirada por escena: así una noche nublada (fría) se ve más oscura que
# una despejada. POR QUÉ esas temperaturas (medido, no supuesto): en la corrida real de la rama S184 (Chillán y
# Villarrica, 12 al 15 de noviembre de 2026, 59 escenas con dato) el percentil 98 del NTI por escena llegó a -0,921 en
# VIIRS 375, -0,890 en MODIS y -0,882 en VIIRS 750, y el percentil 2 bajó (percentil 10 entre escenas) a -0,980, -0,957
# y -0,968. Con 290 K de blanco VIIRS 375 dejaba en blanco puro el 2,7 % de las celdas en la escena mediana (36 % en
# el percentil 90), y un foco no se distinguía del fondo tibio; con 300 K (V375 -0,910, MODIS -0,869, V750 -0,850) y
# 240 K de negro (-0,989, -0,980, -0,975) caben todos. Más frío que 240 K (nube alta) satura en negro; el foco, en
# blanco. Cada miniatura guarda los percentiles 2 y 98 de su NTI para volver a medirlo con más volcanes.
ESCALA_MINIATURA_T_K = (240.0, 300.0)


# ---------------------------------------------------------------------------------------------------- Planck
def radiancia_a_temperatura(L, lam_um):
    """.m l. 403-421."""
    c2 = (_H * _C) / _K
    num = 2 * _H * (_C ** 2)
    lam = lam_um * 1e-6
    with np.errstate(divide="ignore", invalid="ignore"):
        return c2 / lam / np.log(num / (lam ** 5 * (L * 1e6)) + 1)


def temperatura_a_radiancia(T, lam_um):
    """.m l. 424-444 (con 3,14 en vez de pi, como el original)."""
    c1 = 2 * 3.14 * _H * (_C ** 2)
    c2 = (_H * _C) / _K
    lam = lam_um * 1e-6
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        M = c1 / (lam ** 5 * (np.exp(c2 / (lam * T)) - 1)) * 1e-6
    return M / 3.14


# ---------------------------------------------------------------------------------------------------- grilla
@lru_cache(maxsize=1)
def _referencias():
    import yaml
    return yaml.safe_load(_GRILLAS_YAML.read_text(encoding="utf-8"))["volcanes"]


@lru_cache(maxsize=1)
def _volcanes_yaml():
    import yaml
    ruta = Path(__file__).resolve().parents[1] / "volcanoes.yaml"
    return [(v["name"], float(v["lat"]), float(v["lon"]))
            for v in yaml.safe_load(ruta.read_text(encoding="utf-8"))["volcanoes"]]


def volcan_por_coordenadas(lat, lon, tol_grados=1e-6):
    """Nombre del volcán de volcanoes.yaml cuyas coordenadas son (lat, lon), o None. El procesador recibe las del yaml
    tal cual (run_pipeline pasa volcano["lat"], volcano["lon"]), así que la igualdad es exacta salvo redondeo."""
    if lat is None or lon is None:
        return None
    for nombre, la, lo in _volcanes_yaml():
        if abs(la - float(lat)) <= tol_grados and abs(lo - float(lon)) <= tol_grados:
            return nombre
    return None


def n_celdas(paso_m):
    """Regla GEO: centros en X0 - 25000 : paso : X0 + 25000 (como el rango de MATLAB): floor(50000 / paso) + 1."""
    return int(math.floor(2 * MEDIA_GRILLA_M / paso_m)) + 1


def grilla_del_volcan(nombre, paso_m=PASO_V750_M, clave_roi="roi_v750"):
    """Grilla de MIROVA del volcán, o None si no está en grillas_mirova.yaml.

    POR QUÉ: MIROVA interpola cada gránulo a una grilla UTM fija por volcán; ver el volcán como MIROVA exige usar
    SU grilla, no la geometría de barrido. Columnas de oeste a este desde X0 - 25000; filas de SUR a norte desde
    Y0 - 25000, así que la esquina norte es Y0 - 25000 + (n - 1) paso + paso / 2 (no simétrica con la oeste).
    Devuelve el mismo dict que usan probe_n y la prueba de equivalencia: epsg, ul_x, ul_y, centro_lat, centro_lon,
    más n y paso. La ROI sale de la clave del sensor (roi_v750, roi_modis); si el yaml no la trae, "def"."""
    r = _referencias().get(nombre)
    if r is None:
        return None
    n = n_celdas(paso_m)
    return {"epsg": int(r["epsg"]), "ul_x": float(r["x0"]) - MEDIA_GRILLA_M - paso_m / 2,
            "ul_y": float(r["y0"]) - MEDIA_GRILLA_M + (n - 1) * paso_m + paso_m / 2,
            "centro_lat": float(r["centro_lat"]), "centro_lon": float(r["centro_lon"]), "n": n, "paso": paso_m,
            "roi": r.get(clave_roi, "def"), "x0": float(r["x0"]), "y0": float(r["y0"])}


def _haversine(lat, lon, lat0, lon0):
    """Distancia en km (R = 6371), la misma expresión que el recorte de remuestrear_grilla y que el probe del censo."""
    dlat, dlon = np.radians(lat - lat0), np.radians(lon - lon0)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(lat0)) * np.sin(dlon / 2) ** 2
    with np.errstate(invalid="ignore"):
        return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def remuestrear_grilla(lat, lon, m13, m15, grilla, radio_km=RADIO_RECORTE_KM):
    """Interpolación LINEAL de M13 y M15 a los centros de celda de la grilla (fila 0 = norte).

    POR QUÉ: es la pieza que, según V750-C, calla las cumbres tibias de un píxel: el promedio lineal reparte el calor
    de un píxel aislado entre las celdas vecinas. Se recortan antes los píxeles a menos de radio_km del centro de la
    grilla (como probe_n.grillar) para que la triangulación sea la misma."""
    from pyproj import Transformer
    from scipy.interpolate import griddata
    n = int(grilla.get("n", n_celdas(PASO_V750_M)))
    paso = float(grilla.get("paso", PASO_V750_M))
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    dlat, dlon = np.radians(lat - grilla["centro_lat"]), np.radians(lon - grilla["centro_lon"])
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat)) * np.cos(np.radians(grilla["centro_lat"])) * np.sin(dlon / 2) ** 2)
    with np.errstate(invalid="ignore"):
        sel = np.isfinite(lat) & (6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) < radio_km)
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(lon[sel], lat[sel])
    X, Y = np.meshgrid(grilla["ul_x"] + paso * (np.arange(n) + 0.5), grilla["ul_y"] - paso * (np.arange(n) + 0.5))
    out = []
    for v in (np.asarray(m13, float)[sel], np.asarray(m15, float)[sel]):
        ok = np.isfinite(v)
        out.append(griddata(np.column_stack([x[ok], y[ok]]), v[ok], (X, Y), method="linear"))
    return tuple(out)


def celda_de(grilla, lat, lon):
    """(fila, columna) entera de la celda de la grilla donde cae (lat, lon); fila 0 = norte."""
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(lon, lat)
    paso = float(grilla.get("paso", PASO_V750_M))
    return int((grilla["ul_y"] - y) // paso), int((x - grilla["ul_x"]) // paso)


def posicion_de(grilla, lat, lon):
    """Posición fraccionaria (fila, columna) en índices de celda (el centro de la celda i está en i), para medir la
    distancia desde el cráter con el mismo origen que el centroide de un cúmulo."""
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(lon, lat)
    paso = float(grilla.get("paso", PASO_V750_M))
    return (grilla["ul_y"] - y) / paso - 0.5, (x - grilla["ul_x"]) / paso - 0.5


def latlon_de(grilla, fila, col):
    from pyproj import Transformer
    t = Transformer.from_crs(f"EPSG:{grilla['epsg']}", "EPSG:4326", always_xy=True)
    paso = float(grilla.get("paso", PASO_V750_M))
    lon, lat = t.transform(grilla["ul_x"] + paso * (col + 0.5), grilla["ul_y"] - paso * (fila + 0.5))
    return float(lat), float(lon)


# ---------------------------------------------------------------------------------------------------- ROI
def caja_roi(tipo="def", n=None, celda_crater=None, inner_km=None, lado_sensible=7, lado_anillo=21,
             paso_m=PASO_V750_M):
    """BOX del .m: 0 resto de la grilla, 1 región conservadora, 2 región sensible (los nombres ROI1/ROI2 de los
    comentarios del .m están al revés de la matriz: BOX == 2 es la cumbre sensible; memoria del código OSF, S158).

    ⚠️ S193 (auditoría Codex ronda 2, F9-106, verificada): la zona 0 NO queda fuera de la búsqueda. El .m la busca con
    los mismos umbrales conservadores que la zona 1 (`_pasada_contextual`, a0, l. 389-391 del .m); sólo el borde de la
    grilla (NaN, l. 102-103) queda fuera. Un brazo que deje una zona en 0 la vuelve conservadora, no ciega. Texto
    anterior: «BOX del .m: 0 fuera, 1 región conservadora, 2 región sensible».

    POR QUÉ es por volcán: el .m declara que la ROI se ajusta por volcán (l. 105-125), y en Cordón Caulle y
    Tupungatito el calor no está en el centro de la grilla (V750-C, V750-B). Tipos (los brazos de V750-B):
      def    la matriz de ejemplo del .m: sensible lado_sensible x lado_sensible al centro, dentro de un anillo
             conservador lado_anillo x lado_anillo (B0)
      sens   todo el lado_anillo x lado_anillo sensible (B1)
      crater def con el cuadro sensible movido al cráter (B2; para VIIRS 375, lado_sensible=13 es la caja C13)
      inner  def con la región sensible = el círculo de inner_km alrededor del centro (B3)
      corona la lectura del comentario del .m: corona sensible 21 x 21 con el centro conservador 7 x 7 (B5)
    """
    n = n_celdas(paso_m) if n is None else n
    c = n // 2
    h1, h2 = lado_anillo // 2, lado_sensible // 2
    b = np.zeros((n, n))
    if tipo == "corona":
        b[c - h1:c + h1 + 1, c - h1:c + h1 + 1] = 2
        b[c - h2:c + h2 + 1, c - h2:c + h2 + 1] = 1
        return b
    b[c - h1:c + h1 + 1, c - h1:c + h1 + 1] = 1
    if tipo == "def":
        b[c - h2:c + h2 + 1, c - h2:c + h2 + 1] = 2
    elif tipo == "sens":
        b[b == 1] = 2
    elif tipo == "crater":
        if celda_crater is None:
            raise ValueError("caja_roi('crater') necesita celda_crater")
        f, k = celda_crater
        if h2 <= f <= n - 1 - h2 and h2 <= k <= n - 1 - h2:
            b[f - h2:f + h2 + 1, k - h2:k + h2 + 1] = 2
    elif tipo == "inner":
        if inner_km is None:
            raise ValueError("caja_roi('inner') necesita inner_km")
        r, q = np.indices((n, n))
        b[np.hypot(r - c, q - c) * paso_m / 1000.0 <= inner_km] = 2
    else:
        raise ValueError(f"tipo de ROI desconocido: {tipo!r} (válidos {TIPOS_ROI})")
    return b


def caja_v375(grilla, vent_lat, vent_lon, lado_sensible=13, half_roi1_m=HALF_ROI1_V375_M):
    """BOX de VIIRS 375 (S165, PD1 = C13 en todos los volcanes): 1 en la ROI1 física de S159 (las celdas cuyo centro
    está a ±half_roi1_m de X0, Y0 en las dos coordenadas), 2 en el cuadro de lado_sensible x lado_sensible celdas
    centrado en la celda cuyo centro es el más cercano al cráter (recortado al borde), 0 fuera.

    POR QUÉ no caja_roi: en la grilla de 134 celdas X0 no cae en un centro de celda (25.000 m no es múltiplo de 375), así
    que la ROI1 de 42 x 42 no es un cuadro centrado en n // 2; y V375-C midió la caja con brazos.caja(..., "C13", ...),
    que elige la celda del cráter por el centro más cercano. Esta función reproduce esa caja celda por celda (prueba
    test_caja_de_375_es_la_del_brazo_c13_en_los_volcanes_con_grilla). La ROI1 no cambia la detección (las BOX 0 y 1
    tienen los mismos umbrales en el .m), pero se conserva igual al port para que la comparación sea limpia."""
    from pyproj import Transformer
    n, paso = int(grilla["n"]), float(grilla["paso"])
    xs = grilla["ul_x"] + paso * (np.arange(n) + 0.5)
    ys = grilla["ul_y"] - paso * (np.arange(n) + 0.5)
    b = np.zeros((n, n))
    en_x = np.abs(xs - grilla["x0"]) <= half_roi1_m
    en_y = np.abs(ys - grilla["y0"]) <= half_roi1_m
    b[np.ix_(en_y, en_x)] = 1
    xc, yc = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True).transform(vent_lon, vent_lat)
    i0, j0 = int(np.argmin(np.abs(ys - yc))), int(np.argmin(np.abs(xs - xc)))
    h = (lado_sensible - 1) // 2
    b[max(i0 - h, 0):i0 + h + 1, max(j0 - h, 0):j0 + h + 1] = 2
    return b


# ---------------------------------------------------------------------------------------------------- detección
def _media_3x3_omitnan(A):
    """colfilt(A,[3 3],'sliding',@(v) mean(v,1,'omitnan')): relleno con ceros fuera de la matriz, central incluido."""
    P = np.pad(A, 1, mode="constant", constant_values=0.0)
    n, m = A.shape
    pila = np.stack([P[i:i + n, j:j + m] for i in range(3) for j in range(3)])
    with np.errstate(invalid="ignore"):
        cuenta = np.sum(~np.isnan(pila), axis=0)
        suma = np.nansum(pila, axis=0)
        out = suma / cuenta
    out[cuenta == 0] = np.nan
    return out


def _std_omitnan(x):
    v = x[~np.isnan(x)]
    if v.size < 2:
        return np.nan if v.size == 0 else 0.0
    return float(np.std(v, ddof=1))


def _mean_omitnan(x):
    v = x[~np.isnan(x)]
    return float(v.mean()) if v.size else np.nan


def _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, excluidos, s1, s2, n1, n2, e1, e2,
                       lam_mir=LAMBDA_M13, zona_a=None, s_a=None, piso_a=None):
    """contextualDetectionPass, .m l. 252-400: tres máscaras (BOX 0, 1 y 2), diagnóstico y los mapas de contraste.

    POR QUÉ: el detector compara cada celda con la media de sus 8 vecinos MÁS ella misma, en NTI y en ETI (el NTI
    menos lo que la regresión cuadrática contra el NTI esperado de la superficie predice), y exige los dos. El
    umbral es max(mu + s * sd, piso) con mu y sd de TODA la grilla: por eso un cambio lejos del cráter puede mover
    el umbral del cráter (S-1).

    zona_a, s_a (S195, sólo el perfil laboratorio y su barrido; nunca producción): en las celdas de zona_a (región
    sensible a <= inner_radius_km del cráter, mascara_zona_a) el multiplicador de la región 2 es s_a en vez de s2, con
    los mismos pisos n2 y e2 y los mismos mu y sd. POR QUÉ así: es un solo número, monótono en «ver más» (menor s_a, más
    alertas), y con s_a == s2 los umbrales son los mismos floats que u_nti2 y u_eti2, así que el resultado es
    idéntico a producción bit a bit (el control sellado del barrido, experiments/_s194_lab_zona_a/PREREGISTRO.md §5).
    s_a > s2 haría al laboratorio más ciego que producción en el cráter: es error.

    piso_a (S196, palanca del piso, experiments/_s196_lab_piso/PREREGISTRO.md §3 y §9): en las mismas celdas el piso
    de NTI y el de ETI pasan de n2 y e2 a piso_a (None: los de producción). POR QUÉ: en una escena quieta el término
    mu + s·sd queda bajo 0,003 y manda el piso fijo, que deja fuera un foco chico justo donde mejor se vería; bajar
    sólo s no lo destapa (el barrido S195 se aplanó por eso). Un solo número para los dos contrastes, como el .m.
    Con piso_a == n2 == e2 los umbrales son los mismos floats que sin él. Mayor que n2 o e2 haría al laboratorio más
    ciego en el cráter, y cero o negativo dejaría sin freno a una escena cuyo término no es finito: los dos son error."""
    if zona_a is not None and s_a > s2:
        raise ValueError(f"zona A con s_a={s_a} mayor que s2={s2}: el laboratorio vería menos que producción en el "
                         "cráter (tests/test_guard_laboratorio_no_mas_ciego_s147.py)")
    if zona_a is not None and piso_a is not None and not 0 < piso_a <= min(n2, e2):
        raise ValueError(f"zona A con piso_a={piso_a}: tiene que ser positivo y no mayor que los pisos de producción "
                         f"n2={n2}, e2={e2} (tests/test_laboratorio_piso_s196.py)")
    pn = n2 if piso_a is None else piso_a      # S196: pisos de la zona A
    pe = e2 if piso_a is None else piso_a
    vacio = np.zeros(nti_roi.shape, bool)
    pob = nti_roi.copy()                       # l. 275
    pob[excluidos] = np.nan                    # l. 276-277
    fondo_loc = _media_3x3_omitnan(pob)        # l. 285-287
    fondo_loc[excl] = np.nan                   # l. 288
    c_nti = pob - fondo_loc                    # l. 293-294
    with np.errstate(invalid="ignore"):
        c_nti[c_nti < -0.1] = np.nan           # l. 298
    mu, sd = _mean_omitnan(c_nti), _std_omitnan(c_nti)   # l. 303-304
    u_nti1 = max(mu + s1 * sd, n1)             # l. 306-308 (MATLAB max ignora NaN)
    u_nti2 = max(mu + s2 * sd, n2)
    if np.isnan(mu + s1 * sd):
        u_nti1 = n1
    if np.isnan(mu + s2 * sd):
        u_nti2 = n2
    if zona_a is not None:                     # S195: zona A del laboratorio, misma forma que u_nti2
        u_ntia = pn if np.isnan(mu + s_a * sd) else max(mu + s_a * sd, pn)

    m13_esp = temperatura_a_radiancia(bt15, lam_mir)               # l. 319-320 (λ MIR del sensor, l. 144)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti_esp = (m13_esp - m15) / (m13_esp + m15)                 # l. 324-326
    nti_esp[excluidos] = np.nan                                     # l. 328-329
    nti_esp[excl] = np.nan                                          # l. 330
    ok = np.isfinite(nti_esp) & np.isfinite(pob)                    # l. 335-337
    diag = {"mu_nti": mu, "sd_nti": sd, "u_nti1": u_nti1, "u_nti2": u_nti2, "n_ajuste": int(ok.sum())}
    if zona_a is not None:
        diag["u_ntiA"] = u_ntia
    c_eti = np.full(nti_roi.shape, np.nan)
    if ok.sum() < 3:                                                # l. 339-341
        return vacio, vacio, vacio, diag, c_nti, c_eti
    coef = np.polyfit(nti_esp[ok], pob[ok], 2)                      # l. 343-345
    ref = np.polyval(coef, nti_esp)                                 # l. 349-350
    eti = pob - ref                                                 # l. 357-358
    c_eti = eti - _media_3x3_omitnan(eti)                           # l. 362-368
    c_eti[excl] = np.nan                                            # l. 369
    mu_e, sd_e = _mean_omitnan(c_eti), _std_omitnan(c_eti)          # l. 373-374
    u_eti1 = max(mu_e + s1 * sd_e, e1) if np.isfinite(mu_e + s1 * sd_e) else e1   # l. 376-378
    u_eti2 = max(mu_e + s2 * sd_e, e2) if np.isfinite(mu_e + s2 * sd_e) else e2   # l. 380-382
    diag.update({"coef": coef.tolist(), "mu_eti": mu_e, "sd_eti": sd_e, "u_eti1": u_eti1, "u_eti2": u_eti2})
    if zona_a is not None:                     # S195: zona A del laboratorio (ver docstring)
        u_etia = max(mu_e + s_a * sd_e, pe) if np.isfinite(mu_e + s_a * sd_e) else pe
        diag["u_etiA"] = u_etia
        u_nti2 = np.where(zona_a, u_ntia, u_nti2)
        u_eti2 = np.where(zona_a, u_etia, u_eti2)
    with np.errstate(invalid="ignore"):
        a0 = (c_nti * m0 > u_nti1) & (c_eti * m0 > u_eti1)          # l. 389-391
        a1 = (c_nti * m1 > u_nti1) & (c_eti * m1 > u_eti1)          # l. 393-395
        a2 = (c_nti * m2 > u_nti2) & (c_eti * m2 > u_eti2)          # l. 397-399
    return a0, a1, a2, diag, c_nti, c_eti


def detectar_mirova(m13, m15, box, dayflag, sunglint, devolver_diag=False, lam_mir=LAMBDA_M13,
                    lam_tir=LAMBDA_M15, zona_a=None, s_a=None, piso_a=None):
    """MIROVA_VIIRS750_hotspot_detection.m. Devuelve la máscara booleana de alertados (o (máscara, diag)).

    POR QUÉ las piezas: el Test 1 (NTI > -0,7 de noche) es una alerta directa y además saca esas celdas del fondo
    del primer pase contextual; el segundo pase repite la regresión sin las alertas del primero. Sin compuerta de
    temperatura, sin modo de un píxel y sin tope de magnitud (el código no los tiene). El diag lleva, por pase,
    mu, sd y umbrales, y los mapas de contraste para la celda decisiva (S-1). lam_mir y lam_tir son las longitudes de
    onda del .m l. 144-145 (M13 y M15 por defecto; en MODIS, B22 y B31): lo único del detector que depende del sensor.

    zona_a, s_a (S195): zona A del perfil laboratorio (ver _pasada_contextual). Sólo de noche: de día el .m usa s = 15
    en las dos regiones y MIR sólo es nocturno, así que con dayflag 1 se ignora. Sin zona_a el detector es el .m.
    piso_a (S196): el piso de la zona A (ver _pasada_contextual), con las mismas reglas: sólo de noche y sólo con
    zona_a."""
    m13 = np.asarray(m13, float)
    vacio = np.zeros(m13.shape, bool)

    def _salida(mask, d):
        return (mask, d) if devolver_diag else mask

    d = {"motivo": None}
    if not np.isfinite(sunglint) or sunglint < 12:                   # l. 87-89
        d["motivo"] = "sunglint"
        return _salida(vacio, d)
    m15 = np.array(m15, float)
    box = np.array(box, float)
    box[:, [0, -1]] = np.nan                                         # l. 102
    box[[0, -1], :] = np.nan                                         # l. 103
    m0 = np.where(box == 0, 1.0, np.nan)                             # l. 132-138
    m1 = np.where(box == 1, 1.0, np.nan)
    m2 = np.where(box == 2, 1.0, np.nan)
    excl = np.isnan(box)                                             # l. 140

    bt15 = radiancia_a_temperatura(m15, lam_tir)                     # l. 150
    with np.errstate(invalid="ignore"):
        frio = bt15 <= 200                                           # l. 151
    bt15[frio] = np.nan                                              # l. 153
    m15[frio] = np.nan                                               # l. 154
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13 - m15) / (m13 + m15)                              # l. 159
    if nti.size == 0 or np.isnan(nti).sum() >= np.floor(nti.size / 2):   # l. 163-167
        d["motivo"] = "escena_invalida"
        return _salida(vacio, d)
    nti_roi = nti.copy()
    nti_roi[excl] = np.nan                                           # l. 170-171

    if dayflag == 0:                                                 # l. 177-199
        u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003
    else:
        u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02
    if dayflag != 0 or s_a is None:                                  # S195: la zona A es sólo nocturna
        zona_a = None
    if zona_a is not None:
        zona_a = np.asarray(zona_a, bool) & (box == 2)              # nunca fuera de la región sensible

    with np.errstate(invalid="ignore"):
        absol = nti_roi > u_abs                                      # l. 206
    p1 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol, s1, s2, n1, n2, e1, e2,
                            lam_mir=lam_mir, zona_a=zona_a, s_a=s_a, piso_a=piso_a)                # l. 211-218
    ctx1 = p1[0] | p1[1] | p1[2]
    p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1, s1, s2, n1, n2, e1, e2,
                            lam_mir=lam_mir, zona_a=zona_a, s_a=s_a, piso_a=piso_a)                # l. 228-235
    mask = ctx1 | absol | p2[0] | p2[1] | p2[2]                      # l. 241-248 (unión de las siete listas)
    d.update({"pasada1": p1[3], "pasada2": p2[3], "n_abs": int(absol.sum()), "n_p1": int(ctx1.sum()),
              "n_p2": int((p2[0] | p2[1] | p2[2]).sum()), "nti": nti_roi,
              "contrastes": {1: (p1[4], p1[5]), 2: (p2[4], p2[5])}, "box": box, "zona_a": zona_a})
    return _salida(mask, d)


# ---------------------------------------------------------------------------------------------------- fillmissing2
# POR QUÉ esta triangulación y no la de scipy: en una grilla regular cuatro centros vecinos están en un mismo círculo,
# así que la triangulación de Delaunay no es única, y el fondo bajo un píxel caliente depende de qué diagonal se elige
# (en un hueco de 3 x 3 los cuatro vecinos del medio son cocirculares y el centro cae justo sobre esa arista). MATLAB
# rompe cada empate como una perturbación simbólica al estilo CGAL (orden lexicográfico y orientación) en el marco
# x = fila, y = columna. Con esa regla el VRP es el de MATLAB R2026b en 166 de 166 escenas de O2 (máximo 1,55e-15) y el
# fondo completo en 84 de 84, incluida Etna al valor del OSF v2.5; con los ejes cambiados calza en 42 de 166 y Qhull
# en 41 de 84 fondos. Regla hallada por el subagente de la coordinadora S163 (rama s163-o2-alternativa, commit
# cd812c746, experiments/_s163_o2alt/INFORME.md H1 y delaunay_perturbado.py); aquí se porta tal cual, sin el control de
# aristas ilegales, que vive en la prueba. Que MATLAB use CGAL por dentro es SOSPECHA: lo medido es la igualdad.

def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (v > 0) - (v < 0)


def _incircle(a, b, c, d):
    """> 0 si d está dentro del círculo de a, b, c (antihorario). Entero exacto."""
    adx, ady = a[0] - d[0], a[1] - d[1]
    bdx, bdy = b[0] - d[0], b[1] - d[1]
    cdx, cdy = c[0] - d[0], c[1] - d[1]
    ad, bd, cd = adx * adx + ady * ady, bdx * bdx + bdy * bdy, cdx * cdx + cdy * cdy
    v = adx * (bdy * cd - bd * cdy) - ady * (bdx * cd - bd * cdx) + ad * (bdx * cdy - bdy * cdx)
    return (v > 0) - (v < 0)


def _lado_perturbado(p0, p1, p2, p):
    """side_of_oriented_circle(p0, p1, p2, p, perturb=true) de CGAL: +1 dentro, -1 fuera; p0 p1 p2 antihorario."""
    s = _incircle(p0, p1, p2, p)
    if s != 0:
        return s
    pts = sorted([(tuple(p0), 0), (tuple(p1), 1), (tuple(p2), 2), (tuple(p), 3)], key=lambda t: t[0])
    for i in (3, 2):
        quien = pts[i][1]
        if quien == 3:
            return -1
        o = 0
        if quien == 2:
            o = _orient(p0, p1, p)
        elif quien == 1:
            o = _orient(p0, p, p2)
        elif quien == 0:
            o = _orient(p, p1, p2)
        if o != 0:
            return o
    raise RuntimeError("perturbación sin decidir")


def _triangular_perturbado(P):
    """Delaunay único por perturbación simbólica: Qhull de partida y volteos de Lawson con el predicado perturbado,
    en aritmética entera, hasta que ninguna arista lo viole. Devuelve triángulos (i, j, k) antihorarios."""
    from scipy.spatial import Delaunay
    tri = Delaunay(P.astype(float))
    if len(tri.coplanar):
        raise RuntimeError("Qhull dejó puntos fuera de la triangulación")
    pts = [tuple(int(v) for v in q) for q in P]
    T = []
    for s in tri.simplices:
        i, j, k = (int(x) for x in s)
        o = _orient(pts[i], pts[j], pts[k])
        if o == 0:
            raise RuntimeError("triángulo plano en la triangulación inicial")
        T.append([i, j, k] if o > 0 else [i, k, j])
    ar = {}
    for t, (i, j, k) in enumerate(T):
        ar[(i, j)] = t
        ar[(j, k)] = t
        ar[(k, i)] = t
    pila = list(ar.keys())
    while pila:
        a, b = pila.pop()
        t1, t2 = ar.get((a, b)), ar.get((b, a))
        if t1 is None or t2 is None:
            continue
        c = [v for v in T[t1] if v != a and v != b][0]
        d = [v for v in T[t2] if v != a and v != b][0]
        if _lado_perturbado(pts[a], pts[b], pts[c], pts[d]) > 0:
            if _orient(pts[c], pts[a], pts[d]) <= 0 or _orient(pts[d], pts[b], pts[c]) <= 0:
                raise RuntimeError("volteo sobre cuadrilátero no convexo")
            for e in ((a, b), (b, c), (c, a), (b, a), (a, d), (d, b)):
                ar.pop(e, None)
            T[t1], T[t2] = [c, a, d], [d, b, c]
            for t in (t1, t2):
                i, j, k = T[t]
                ar[(i, j)] = t
                ar[(j, k)] = t
                ar[(k, i)] = t
            pila.extend([(a, d), (d, b), (b, c), (c, a)])
    return T


def _fillmissing2_lineal(A):
    """fillmissing2(A, 'linear') de MATLAB: interpolación lineal sobre el Delaunay perturbado (x = fila, y = columna)
    de las celdas con dato; FUERA de la envolvente convexa queda NaN, porque MATLAB no extrapola (Etna: 230 celdas en
    NaN en el fondo de MATLAB R2026b; confirmado con MATLAB real en VIIRS 375, 38.955 celdas en 12 escenas, y en MODIS,
    159 en 10; coordinadora S163, 2026-10-26). La versión anterior ponía el vecino más cercano y el oro no lo vio porque
    comparaba con nanmax, que se salta los NaN de MATLAB. Con `sum(..., 'omitnan')` del .m un NaN bajo una alerta se
    descarta de L_bk y un valor extrapolado se sumaría: no da lo mismo."""
    A = np.asarray(A, float)
    filas, cols = np.indices(A.shape)
    ok = np.isfinite(A)
    B = A.copy()
    if ok.all() or not ok.any():
        return B
    P = np.column_stack([filas[ok], cols[ok]]).astype(np.int64)
    val = A[ok]
    T = _triangular_perturbado(P)
    Q = np.column_stack([filas[~ok], cols[~ok]]).astype(np.int64)
    Ta = np.array(T)
    tx, ty = P[Ta, 0], P[Ta, 1]
    xmin, xmax, ymin, ymax = tx.min(1), tx.max(1), ty.min(1), ty.max(1)
    out = np.full(len(Q), np.nan)
    for qi, (qx, qy) in enumerate(Q):
        for t in np.nonzero((xmin <= qx) & (qx <= xmax) & (ymin <= qy) & (qy <= ymax))[0]:
            i, j, k = T[t]
            a, b, c = P[i], P[j], P[k]
            den = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            w1 = (b[0] - qx) * (c[1] - qy) - (b[1] - qy) * (c[0] - qx)
            w2 = (c[0] - qx) * (a[1] - qy) - (c[1] - qy) * (a[0] - qx)
            w3 = (a[0] - qx) * (b[1] - qy) - (a[1] - qy) * (b[0] - qx)
            if w1 >= 0 and w2 >= 0 and w3 >= 0:
                out[qi] = (w1 * val[i] + w2 * val[j] + w3 * val[k]) / den
                break
    B[~ok] = out          # lo que ningún triángulo cubre (fuera de la envolvente) queda NaN, como en MATLAB
    return B


def vrp_mirova(m13, mascara, coef=COEF_VRP_V750):
    """MIROVA_VIIRS750_VRP.m: VRP de la UNIÓN de los alertados con el fondo del código.

    POR QUÉ: la magnitud de MIROVA es la radiancia de todos los alertados menos el fondo que el .m interpola por
    debajo de ellos tras sacar un halo de 3, 5 o 7 celdas (según cuántos haya), SIN recortar a cero y sumando todos:
    con este fondo el oráculo da la magnitud de MIROVA al centésimo (S159 N-2: 0,999), y el fondo del anillo de K
    da 0,458 (V750-C)."""
    from scipy.ndimage import binary_dilation
    m13 = np.asarray(m13, float)
    mascara = np.asarray(mascara, bool)
    npix = int(mascara.sum())                                        # l. 61
    if npix == 0:                                                    # l. 50-52
        return {"VRP_MW": np.nan, "npix": 0, "L_hot": np.nan, "L_bk": np.nan, "deltaL": np.nan, "n_sin_fondo": 0}
    enm = m13.copy()
    enm[mascara] = np.nan                                            # l. 64-65
    k = 3 if npix <= 4 else (5 if npix <= 30 else 7)                 # l. 68-74
    excl = binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))   # l. 76-77
    enm[excl] = np.nan                                               # l. 78
    fondo = _fillmissing2_lineal(enm)                                # l. 81
    L_hot = float(np.nansum(m13[mascara]))                           # l. 83
    L_bk = float(np.nansum(fondo[mascara]))                          # l. 84
    dL = L_hot - L_bk                                                # l. 85
    # S192 (F4-101, F2-V201): cuántos alertados quedaron sin fondo (fillmissing2 no extrapola fuera de la envolvente de
    # las celdas con dato y el .m los suma como cero). No cambia ningún valor del .m; lo usa procesar_grilla.
    n_sin = int(np.isnan(fondo[mascara]).sum())
    return {"VRP_MW": dL * coef, "npix": npix, "L_hot": L_hot, "L_bk": L_bk, "deltaL": dL, "n_sin_fondo": n_sin}


def t_bg_de(v, lam):
    """Temperatura de brillo del fondo medio de los alertados QUE TIENEN fondo (S192), o None si ninguno lo tiene.

    POR QUÉ: L_bk suma sólo los fondos que existen; dividirlo por todos los alertados mete ceros y da un suelo varios
    kelvin más frío (o 0 K si ninguno tiene fondo). Sólo se muestra; no decide nada."""
    con = v["npix"] - v.get("n_sin_fondo", 0)
    if v["npix"] <= 0 or con <= 0:
        return None
    return round(float(radiancia_a_temperatura(np.array([v["L_bk"] / con]), lam)[0]), 2)


def angulos_invalidos_de(geom):
    """Claves de RANGO_ANGULOS que en `geom` faltan, no son finitas o caen fuera de su rango físico (ordenadas; [] si
    los cuatro sirven). Ver el POR QUÉ en calcular_vrp_granulo."""
    malos = []
    for k, (lo, hi) in RANGO_ANGULOS.items():
        v = geom.get(k)
        if v is None or not math.isfinite(v) or not lo <= v <= hi:
            malos.append(k)
    return sorted(malos)


def sunglint_deg(sat_zen, sun_zen, sat_azi, sun_azi):
    """README.txt / run_example.m del OSF: ángulo de sun-glint."""
    c = (np.cos(np.radians(sat_zen)) * np.cos(np.radians(sun_zen))
         - np.sin(np.radians(sat_zen)) * np.sin(np.radians(sun_zen)) * np.cos(np.radians(sun_azi - sat_azi)))
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


# ---------------------------------------------------------------------------------------------------- S-1
def _umbral_de(diag_pase, zona, en_zona_a=False):
    """Umbral (NTI, ETI) de una celda según su zona: u1 en las zonas 0 y 1, u2 en la 2 (.m l. 389-399). S195: en una
    celda de la zona A del laboratorio, el de la zona A (con s_a == s2 es el mismo float que u2)."""
    s = "A" if en_zona_a and zona == 2 else ("2" if zona == 2 else "1")
    return diag_pase.get(f"u_nti{s}", np.nan), diag_pase.get(f"u_eti{s}", np.nan)


def celda_decisiva(diag, celda_crater, radio=3):
    """La celda del 7 x 7 alrededor del cráter que más cerca está de alertar (o que más alerta), con sus contrastes.

    POR QUÉ: el diagnóstico S-1 (PREREGISTRO_V750A.md §5) pregunta si un cambio de publicación entre dos brazos lo
    decidió el cráter o la sigma de la escena. Para eso hace falta, en cada brazo, la celda que decide y su margen
    contra SU umbral. Margen de una celda = min(c_nti / u_nti, c_eti / u_eti) con el umbral de su zona y de su pase
    (las dos pruebas a la vez, como el .m): sobre 1 alerta. Se elige la de margen mayor entre los dos pases; si el
    cráter no alerta en ninguno, es la que estuvo más cerca. None si no hay contraste finito en el 7 x 7."""
    if not diag or "contrastes" not in diag:
        return None
    box = diag["box"]
    zona_a = diag.get("zona_a")
    n = box.shape[0]
    f0, k0 = celda_crater
    mejor = None
    for pase in (1, 2):
        c_nti, c_eti = diag["contrastes"][pase]
        dp = diag[f"pasada{pase}"]
        for f in range(max(f0 - radio, 0), min(f0 + radio + 1, n)):
            for k in range(max(k0 - radio, 0), min(k0 + radio + 1, n)):
                z = box[f, k]
                if not np.isfinite(z) or not (np.isfinite(c_nti[f, k]) and np.isfinite(c_eti[f, k])):
                    continue
                u_n, u_e = _umbral_de(dp, int(z), zona_a is not None and bool(zona_a[f, k]))
                if not (np.isfinite(u_n) and np.isfinite(u_e)) or u_n <= 0 or u_e <= 0:
                    continue
                margen = min(c_nti[f, k] / u_n, c_eti[f, k] / u_e)
                if mejor is None or margen > mejor["margen"]:
                    mejor = {"pase": pase, "zona": int(z), "fila": f, "col": k, "c_nti": float(c_nti[f, k]),
                             "c_eti": float(c_eti[f, k]), "u_nti": float(u_n), "u_eti": float(u_e),
                             "margen": float(margen)}
    return mejor


def diag_s1(diag, celda_crater):
    """Bloque que el diagnóstico S-1 lee del record: sd y umbrales de cada pase y la celda decisiva."""
    def pase(dp):
        out = {k: (None if dp.get(k) is None or not np.isfinite(dp.get(k)) else round(float(dp[k]), 6))
               for k in ("sd_nti", "sd_eti", "mu_nti", "mu_eti", "u_nti1", "u_nti2", "u_eti1", "u_eti2")}
        # S196: el umbral de la zona A del laboratorio, sólo cuando difiere del de la región sensible. POR QUÉ sólo
        # entonces: con la zona sin efecto (apagada, o s_A = 5 y piso 0,003) el record tiene que seguir siendo el de
        # producción byte a byte (control del barrido, experiments/_s196_lab_piso/PREREGISTRO.md §5); ausente quiere
        # decir «igual a u_nti2 y u_eti2».
        for k, k2 in (("u_ntiA", "u_nti2"), ("u_etiA", "u_eti2")):
            v = dp.get(k)
            if v is not None and np.isfinite(v) and round(float(v), 6) != out[k2]:
                out[k] = round(float(v), 6)
        return out
    if not diag or "pasada1" not in diag:
        return {"motivo": (diag or {}).get("motivo")}
    cd = celda_decisiva(diag, celda_crater)
    return {"pasada1": pase(diag["pasada1"]), "pasada2": pase(diag["pasada2"]),
            "celda_decisiva": None if cd is None else {k: (round(v, 6) if isinstance(v, float) else v)
                                                       for k, v in cd.items()}}


# ---------------------------------------------------------------------------------------------------- record
def _cumulo_del_mas_radiante(mascara, m13):
    """Celdas (fila, col) del cúmulo 8-conexo que contiene a la alertada de mayor M13 (corrige C-4 del censo S159:
    la posición es la del objeto más radiante, no la de una suma de objetos lejanos)."""
    pos = set(zip(*np.nonzero(mascara)))
    semilla = max(pos, key=lambda p: m13[p])
    vistos, pila = {semilla}, [semilla]
    while pila:
        a, b = pila.pop()
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                q = (a + da, b + db)
                if q in pos and q not in vistos:
                    vistos.add(q)
                    pila.append(q)
    return sorted(vistos)


# ---------------------------------------------------------------------------------------------------- zona A (S195)
# POR QUÉ existe (perfil laboratorio, extensión MEJ-5, plan docs/PLAN_EXPERIMENTAL_S190.md §6; paso 3 en
# docs/superpowers/plans/2026-11-22-laboratorio-paso3.md): un foco chico en el cráter queda al borde del umbral
# contextual de MIROVA y la vía lo copia a propósito. El laboratorio baja SÓLO el multiplicador de sigma de la región
# sensible y sólo en la cumbre, para medir lo que aparece contra NHI y persistencia, nunca contra MIROVA (A115).
# POR QUÉ el círculo cortado por la región sensible y no el círculo entero (decisión (a) de Nicolás, 2026-11-22): con
# el círculo entero, 4.636 celdas que en producción son conservadoras (s1 = 10, pisos 0,02 y 0,01) bajarían de umbral
# ya con s = 5, y el brazo de control del barrido sellado (s = 5 igual a producción) no podría cumplirse. Con la
# intersección, s = 5 es la identidad exacta. Producción nunca enciende la zona (tests/test_laboratorio_paso1_s193.py G4).
def s_zona_a(nombre_volcan):
    """Multiplicador de la zona A para este volcán según el perfil activo, o None (zona apagada, volcán fuera).

    Lee pipeline.profile al llamarse y no al importar el módulo: la vía se usa también fuera del pipeline (pruebas,
    experimentos) sin perfil que importar hasta que procesa un gránulo."""
    zona = _zona_a_activa(nombre_volcan)
    return None if zona is None else float(zona["valor"])


def piso_zona_a(nombre_volcan):
    """Piso de la zona A (S196) para este volcán según el perfil activo, o None: zona apagada, volcán fuera, o perfil
    que no declara la clave (entonces rige el piso de producción, como en el barrido S195)."""
    zona = _zona_a_activa(nombre_volcan)
    p = None if zona is None else zona.get("piso")
    return None if p is None else float(p)


def _zona_a_activa(nombre_volcan):
    """El bloque laboratorio_zona_a del perfil activo si la zona está encendida y el volcán no está fuera; si no, None.
    Es el único lugar de la vía que lee el perfil (G4 de tests/test_laboratorio_paso1_s193.py)."""
    from . import profile as _perfil
    if not _perfil.ENABLE_LAB_ZONA_A:
        return None
    zona = _perfil.LAB_ZONA_A
    if nombre_volcan in zona.get("volcanes_fuera", []):
        return None
    return zona


def mascara_zona_a(box, pos_crater, paso_m, inner_km):
    """Celdas de la región sensible (BOX == 2) a no más de inner_km del cráter, con la misma distancia que decide
    distance_class (pos_crater fraccionaria, en celdas por el paso). None si el volcán no tiene inner_km."""
    if inner_km is None:
        return None
    r, q = np.indices(np.shape(box))
    return (np.asarray(box) == 2) & (np.hypot(r - pos_crater[0], q - pos_crater[1]) * paso_m / 1000.0 <= inner_km)


def procesar_grilla(m13g, m15g, grilla, box, dayflag, sunglint, pos_crater, inner_km, sensor,
                    coef=None, familia="VIIRS750", roi=None, zona_a=None, s_a=None, piso_a=None):
    """Detección + VRP + record (esquema de hoy) sobre una grilla ya remuestreada.

    Record: vrp_mw = primary_cluster.vrp_mw = VRP de la UNIÓN de los alertados (lo que publica MIROVA, D32);
    posición, centroide y distance_class = el cúmulo 8-conexo de la alertada más radiante, con la distancia medida
    desde el cráter (pos_crater, posición fraccionaria en la grilla, como producción mide desde
    get_detection_anchor). Sin modo de un píxel y sin tope D9 (N-5: el tope recorta una erupción real). familia elige
    las longitudes de onda y el coeficiente (FAMILIAS); coef, si se da, reemplaza al de la familia. roi es el nombre de
    la caja `box` para el diagnóstico (S193, F2-V303: calcular_vrp_granulo pasa la que de verdad usó); sin él, el de la
    grilla. zona_a y s_a: la zona A del perfil laboratorio (S195; detectar_mirova), None en producción."""
    cfg = FAMILIAS[familia]
    coef = cfg["coef"] if coef is None else coef
    lam = cfg["lam_mir"]
    mascara, d = detectar_mirova(m13g, m15g, box, dayflag, sunglint, devolver_diag=True, lam_mir=lam,
                                 lam_tir=cfg["lam_tir"], zona_a=zona_a, s_a=s_a, piso_a=piso_a)
    v = vrp_mirova(m13g, mascara, coef=coef)
    # POR QUÉ (S192, F4-101 y F2-108; decisión de Nicolás del 2026-11-20, opción a): si NINGÚN alertado tiene fondo, el
    # .m publica la radiancia entera de los píxeles como si fuera exceso. En MODIS MIROVA no tiene ninguna detección
    # con fondo 0 en 262.455 del OSF v2.5 (ese fondo 0 nace de correr aquí el código de VIIRS 750, D36) y el único caso
    # cotejable fue un falso positivo nuestro: la escena es no medida (0 MW, sin píxeles, motivo propio). En VIIRS el
    # OSF sí publica con fondo 0 (501 en 375 y 464 en 750): se conserva la cifra y queda la marca alertados_sin_fondo.
    sin_fondo_modis = familia == "MODIS" and v["npix"] > 0 and v["n_sin_fondo"] == v["npix"]
    celda_c = (int(round(pos_crater[0])), int(round(pos_crater[1])))
    paso_km = float(grilla.get("paso", PASO_V750_M)) / 1000.0
    rec = {"sensor": sensor, "triggered_test1": False, "vrp_vent_mw": 0.0, "via_codigo_mirova": True,
           "n_anomalous_pixels": 0 if sin_fondo_modis else int(v["npix"]), "diag_codigo_mirova": {
               "motivo_vacio": "fondo_no_estimado" if sin_fondo_modis else d.get("motivo"), "n_abs": d.get("n_abs"),
               "n_p1": d.get("n_p1"), "n_p2": d.get("n_p2"), "L_hot": v["L_hot"] if v["npix"] else None,
               "L_bk": v["L_bk"] if v["npix"] else None, "alertados_sin_fondo": v["n_sin_fondo"] if v["npix"] else None,
               "roi": grilla.get("roi") if roi is None else roi, "s1": diag_s1(d, celda_c)}}
    # POR QUÉ (S193, F3-107 y F3-V201 de la auditoría Codex ronda 2): una escena puede pasar el corte de media grilla
    # (l. 163-167 del .m) con el hueco justo sobre el cráter: escaneos sin dato, nube fría bajo 200 K en la banda
    # térmica (l. 151-154) o un ajuste imposible. Si en el 7 x 7 del cráter no queda ni una celda con contraste NTI y
    # ETI que comparar (celda_decisiva nula) y el detector no alertó en ninguna parte, el cráter no se miró: no es una
    # noche sin anomalía. El .m deja ese VRP indefinido y pide no leerlo como cero (MIROVA_VIIRS750_VRP.m l. 20-22).
    # La cifra sigue en 0 MW, como las demás escenas no medidas (ficha v1.27; el 0,0 en vez de NaN es D36, «Pasada
    # válida sin alerta»); lo que cambia es que el record lo dice, y el tablero la trata como escena sin dato. En main
    # del 2026-11-21 son 23 records de los 11 principales (censo S193). Con un alertado en cualquier parte la escena es
    # una medición con VRP y no se toca; si el detector no corrió (reflejo solar, media escena: sin pasada1) su motivo queda.
    s1 = rec["diag_codigo_mirova"]["s1"]
    if not v["npix"] and "pasada1" in s1 and s1.get("celda_decisiva") is None:
        rec["diag_codigo_mirova"]["motivo_vacio"] = MOTIVO_CRATER_NO_EVALUADO
    if not v["npix"] or sin_fondo_modis:
        rec.update({"vrp_mw": 0.0, "primary_cluster": None, "t_bg_k": None, "distance_class": None, "anomaly_pixels": [],
                    "t_max_k": None, "hotspot_lat": None, "hotspot_lon": None, "hotspot_dist_km": None,
                    "final_hotspot_lat": None, "final_hotspot_lon": None, "final_hotspot_dist_km": None,
                    "final_hotspot_source": None})
        return rec
    vrp_mw = round(float(v["VRP_MW"]), 3)
    cu = _cumulo_del_mas_radiante(mascara, m13g)
    fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    dcen = float(np.hypot(fr - pos_crater[0], fc - pos_crater[1]) * paso_km)
    clat, clon = latlon_de(grilla, fr, fc)
    pico = max(cu, key=lambda p: m13g[p])
    plat, plon = latlon_de(grilla, *pico)
    dpico = float(np.hypot(pico[0] - pos_crater[0], pico[1] - pos_crater[1]) * paso_km)
    t_max = float(radiancia_a_temperatura(np.array([m13g[pico]]), lam)[0])
    dc = None if inner_km is None else ("summit" if dcen <= inner_km else "far")
    pix = []
    for f, k in zip(*np.nonzero(mascara)):
        la, lo = latlon_de(grilla, f, k)
        pix.append({"lat": round(la, 5), "lon": round(lo, 5),
                    "dist_km": round(float(np.hypot(f - pos_crater[0], k - pos_crater[1]) * paso_km), 2),
                    "bt_k": round(float(radiancia_a_temperatura(np.array([m13g[f, k]]), lam)[0]), 2),
                    "fila": int(f), "col": int(k)})
    rec.update({
        "vrp_mw": vrp_mw, "t_max_k": round(t_max, 2), "distance_class": dc, "anomaly_pixels": pix,
        # fondo medio del .m bajo los alertados que lo tienen, en temperatura de brillo (para el log y el tablero; no
        # decide nada). S192: antes L_bk / npix, que con alertados sin fondo daba un suelo más frío o 0 K.
        "t_bg_k": t_bg_de(v, lam),
        "primary_cluster": {"vrp_mw": vrp_mw, "n_pixels": len(cu), "centroid_lat": round(clat, 5),
                            "centroid_lon": round(clon, 5), "centroid_dist_km": round(dcen, 3),
                            "single_pixel_mode": False},
        "hotspot_lat": round(plat, 5), "hotspot_lon": round(plon, 5), "hotspot_dist_km": round(dpico, 3),
        "final_hotspot_lat": round(clat, 5), "final_hotspot_lon": round(clon, 5),
        "final_hotspot_dist_km": round(dcen, 3), "final_hotspot_source": "codigo_mirova"})
    return rec


# ---------------------------------------------------------------------------------------------------- gránulo
def leer_radiancia_l1b(ruta, bandas=("M13", "M15")):
    """M13 y M15 (o las bandas pedidas: I04 e I05 en VIIRS 375) en radiancia (W m-2 sr-1 um-1) del L1B, con las
    banderas en NaN; el código de MIROVA trabaja en radiancia, no en temperatura de brillo. En 375 es la lectura del
    probe de V375-B/C (experiments/_s159/portes/probe_portes.py::leer_viirs). S192: bandera es todo DN sobre el valid_max
    de la variable (banderas_viirs_l1b.dn_invalido), no DN >= 65528: M13 de VJ202MOD v2.1 viene en uint32 y ese corte
    borraba M13 sobre unos 512 K."""
    import h5py
    from .banderas_viirs_l1b import dn_invalido
    out = {}
    with h5py.File(ruta, "r") as f:
        obs = f["observation_data"]
        for b in bandas:
            if b not in obs:
                return None
            ds = obs[b]
            crudo = ds[:]
            dn = crudo.astype(np.float64)
            sf = float(np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0])
            ao = float(np.asarray(ds.attrs.get("add_offset", 0.0)).ravel()[0])
            rad = dn * sf + ao
            rad[dn_invalido(ds, crudo)] = np.nan
            out[b] = rad
        # S190 (F1V-101), sólo diagnóstico: un I04 o M13 saturado llega con radiancia finita (el L1B la deja en el
        # techo y enciende el bit de saturación, no un DN de bandera), así que la VRP sale baja sin aviso. Se guarda
        # la máscara del bit para la banda MIR (la primera pedida); la radiancia no cambia. Sin el dataset, no hay
        # clave y la marca queda sin dato. Un dataset que no es entero (no ocurre en el L1B de NASA) tampoco da clave:
        # un diagnóstico no puede tumbar una pasada que la detección sí procesa (verificador S191).
        qf = obs.get(f"{bandas[0]}_quality_flags")
        if qf is not None:
            try:
                q = qf[:]
                out["saturado_mir"] = (q & BIT_SATURACION_VIIRS) != 0
                out["bowtie_mir"] = (q & BIT_BOWTIE_VIIRS) != 0
            except TypeError:
                pass
        # POR QUÉ (S192, adoptado en S193; sólo diagnóstico): el relleno bow-tie no es dato perdido. Lejos del nadir los
        # barridos vecinos de VIIRS se solapan y el satélite descarta a bordo los detectores del borde de cada barrido,
        # cuyo suelo ya midió el barrido contiguo. La radiancia no cambia (sigue en NaN, como toda bandera); la máscara
        # sólo deja que dato_faltante_crater no los cuente como hueco. Sin quality_flags no hay clave y la separación
        # queda sin dato.
        qt = obs.get(f"{bandas[1]}_quality_flags")
        if qt is not None:
            try:
                out["bowtie_tir"] = (qt[:] & BIT_BOWTIE_VIIRS) != 0
            except TypeError:
                pass
    return out


def bandas_ausentes_l1b(ruta, bandas=("M13", "M15")):
    """Las bandas pedidas que el L1B no trae, en el orden pedido ([] si están todas).

    POR QUÉ (S190, H03 de la auditoría de Codex): `leer_radiancia_l1b` devuelve None si falta una banda y no dice cuál.
    Los procesadores usan esto para que el error de una pasada sin medir nombre la banda que faltó, en vez de que la
    pasada desaparezca en silencio. Sólo mira los nombres de `observation_data`; no lee datos."""
    import h5py
    with h5py.File(ruta, "r") as f:
        presentes = set(f["observation_data"].keys()) if "observation_data" in f else set()
    return [b for b in bandas if b not in presentes]


def leer_geo_l1b(ruta):
    """lat, lon (float64, como el probe del oráculo) y ángulos de observación en grados del L1B GEO de VIIRS."""
    import h5py
    with h5py.File(ruta, "r") as f:
        g = f["geolocation_data"]
        lat = g["latitude"][:].astype(np.float64)
        lon = g["longitude"][:].astype(np.float64)
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan
        ang = {}
        for k in ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth"):
            if k in g:
                ds = g[k]
                sf = float(np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0])
                a = ds[:].astype(np.float64) * sf
                a[np.isnan(lat)] = np.nan
                ang[k] = a
    return lat, lon, ang


def dato_faltante_crater(rad, lat, lon, b_mir, b_tir, vent_lat, vent_lon, paso_m, ventana=None):
    """Marcas de dato faltante sobre el cráter, medidas en los píxeles del gránulo ANTES de interpolar. Sólo diagnóstico.

    POR QUÉ (S190, F1M-101, F1M-108, F1V-104, F1V-101). En el volcán, la noche más caliente es justo la que puede dejar
    el píxel del cráter sin valor: un flujo o una fuente de lava satura la MIR de MODIS en las bandas 22 y 21, o el L1B
    de VIIRS marca el píxel con una bandera (Missing_EV, Cal_Fail); otras veces el escaneo que cruza el cráter llega
    sin posición. Ese píxel se pierde antes de interpolar, y la interpolación lineal rellena el hueco con los vecinos,
    más fríos: el detector ve una noche tranquila y publica 0 MW, o una fracción de la potencia, sin ninguna marca
    (celdas_sin_dato se cuenta después de interpolar y no lo ve). Estas marcas no cambian ninguna detección, potencia ni
    posición; dejan escrito en el record que esa pasada no midió el cráter entero, para que el operador no la lea como
    noche sin anomalía. Qué hace el tablero con ellas (paso B) se decide después de contarlas.

    - crater_sin_posicion: la regla «cráter sin dato» de la guardia K (process_modis.crater_cubierto, importada para
      que haya una sola copia, A102): el píxel con posición más cercano al cráter está en el borde del gránulo o a
      alguno de sus 8 vecinos le falta lat o lon.
    - px_mir_invalido_crater: píxeles con posición a menos de CELDAS_DATO_CRATER celdas de la grilla del cráter cuya
      MIR o TIR no es finita (sin TIR el píxel tampoco tiene NTI). Cuenta también el relleno bow-tie; se deja igual para
      que la serie desde #1060 siga comparable.
    - px_bowtie_crater (S192, adoptado en S193): de los píxeles cercanos, los que traen el bit Bowtie_Deleted (256) en
      quality_flags de la MIR o de la TIR. No es dato perdido: el suelo lo midió el barrido contiguo, y la interpolación
      usa ese píxel. None si el lector no trae quality_flags (siempre en MODIS, que no descarta a bordo).
    - px_mir_hueco_crater y px_tir_hueco_crater (S192, adoptado en S193): píxeles cercanos con la MIR (o la TIR) no
      finita por una causa que NO es bow-tie (Missing_EV, Cal_Fail; en MODIS la doble saturación o el relleno).
      Separados porque perder la MIR esconde el foco y perder sólo la TIR puede destapar parte de él (S191,
      tir_perdida). Son lo que debe leer el paso B, no el total.
    - px_saturados_crater: lo mismo con el bit de saturación de quality_flags de la banda MIR (VIIRS). None si el
      lector no lo trae: siempre en MODIS, donde la saturación es un DN que el lector ya deja en NaN (B22 cae a B21, y si
      las dos saturan cuenta en px_mir_invalido_crater), y en un L1B sin quality_flags. None es «no medido», no cero.

    ventana: (slice de filas, slice de columnas) donde mirar; calcular_vrp_granulo pasa la caja de los píxeles del
    recorte de 45 km. POR QUÉ: en un gránulo VIIRS 375 entero (6464 × 6400) medir sobre todo multiplica el tiempo y la
    memoria de cada pasada (costo sin medir con script), y fuera de esa caja no hay nada del cráter. Da lo mismo que sin ventana mientras el píxel más cercano al
    cráter esté dentro de la caja: un borde de la caja junto a ese píxel es borde del gránulo o vecino sin posición, y
    la regla de K responde igual en los dos casos (prueba de equivalencia en test_via_dato_faltante_crater_s190.py)."""
    from .process_modis import crater_cubierto
    v = (slice(None), slice(None)) if ventana is None else ventana
    lat = np.asarray(lat, float)[v]
    lon = np.asarray(lon, float)[v]
    cerca = _haversine(lat, lon, vent_lat, vent_lon) < CELDAS_DATO_CRATER * float(paso_m) / 1000.0
    cerca &= np.isfinite(lat) & np.isfinite(lon)
    mir_ok = np.isfinite(np.asarray(rad[b_mir], float)[v])
    tir_ok = np.isfinite(np.asarray(rad[b_tir], float)[v])
    invalido = ~(mir_ok & tir_ok)
    sat = rad.get("saturado_mir")
    # POR QUÉ (S192, adoptado en S193): el 2026-11-20 los 105 píxeles que este marcador contó en 27 pasadas NOAA-21 de
    # cenit alto (54,7° a 67,0°) eran todos relleno bow-tie (bit 256 en MIR y TIR, probe S192, run 44818788733), no
    # dato perdido. Se separan del hueco, y el hueco de la MIR del de la TIR. Sin máscara (MODIS, que no descarta a
    # bordo, o un L1B sin quality_flags) nada se descuenta y px_bowtie_crater queda None (no medido, no cero).
    bt_m, bt_t = rad.get("bowtie_mir"), rad.get("bowtie_tir")
    btm = np.zeros(mir_ok.shape, bool) if bt_m is None else np.asarray(bt_m, bool)[v]
    btt = np.zeros(tir_ok.shape, bool) if bt_t is None else np.asarray(bt_t, bool)[v]
    return {"crater_sin_posicion": not crater_cubierto(lat, lon, vent_lat, vent_lon),
            "px_mir_invalido_crater": int((cerca & invalido).sum()),
            "px_saturados_crater": None if sat is None else int((cerca & np.asarray(sat, bool)[v]).sum()),
            "px_bowtie_crater": None if bt_m is None and bt_t is None else int((cerca & (btm | btt)).sum()),
            "px_mir_hueco_crater": int((cerca & ~mir_ok & ~btm).sum()),
            "px_tir_hueco_crater": int((cerca & ~tir_ok & ~btt).sum())}


def calcular_vrp_granulo(rad, lat, lon, angulos, nombre_volcan, vent_lat, vent_lon, inner_km, sensor,
                         grilla=None, tipo_roi=None, familia="VIIRS750"):
    """Del gránulo (radiancia y geolocalización ya leídas) al record, para un volcán con grilla de MIROVA.

    Devuelve None si el volcán no tiene grilla en grillas_mirova.yaml (el llamador decide qué hacer: la vía no
    inventa una grilla) o si el gránulo no cubre el volcán (menos de 100 píxeles en el recorte de 45 km o, en MODIS y
    VIIRS 375, el píxel más cercano al centro a más de 5 km). Si el gránulo cubre el volcán pero en el recorte una
    banda tiene menos de MIN_PX_TRIANGULAR píxeles con radiancia válida, devuelve la escena vacía con motivo_vacio
    «sin_radiancia_valida» (S192). Si falta, no es finito o está fuera de rango alguno de los cuatro ángulos de
    observación, devuelve la escena vacía con motivo_vacio «angulo_ausente» (S199). familia: "VIIRS750" (rad con M13 y M15), "MODIS" (rad
    con MIR y TIR, ver leer_radiancia_modis) o "VIIRS375" (rad con I04 e I05; la caja es siempre caja_v375)."""
    cfg = FAMILIAS[familia]
    g = grilla or grilla_del_volcan(nombre_volcan, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    if g is None:
        return None
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    dist = _haversine(lat, lon, g["centro_lat"], g["centro_lon"])
    sel = np.isfinite(dist) & (dist < RADIO_RECORTE_KM)
    if sel.sum() < 100:
        return None
    i0 = np.unravel_index(np.nanargmin(np.where(sel, dist, np.inf)), dist.shape)
    if cfg["dist_max_centro_km"] is not None and dist[i0] > cfg["dist_max_centro_km"]:
        return None
    geom = {k: float(np.asarray(v)[i0]) for k, v in (angulos or {}).items() if v is not None}
    # POR QUÉ (S199; F8-107 y F3-102 de la auditoría Codex ronda 2, R3F3-102 de la ronda 3; decisión del acta de cierre
    # aprobada por Nicolás, docs/ACTA_CIERRE_AUDITORIA_CODEX_2026-11-24.md: «Aceptar con marca: marcar "sin ángulo" como
    # escena no medida cuando aparezca»). El cenit del sol decide si la pasada es de noche o de día (umbrales
    # distintos, .m l. 177-199) y los cuatro ángulos dan el reflejo solar que anula la escena bajo 12 grados (.m l.
    # 87-89; fórmula del README del OSF). Antes, un ángulo ausente se rellenaba en silencio (180 para la noche, 0 para el
    # reflejo) y uno NaN o de relleno entraba tal cual: con el satélite bajo 12 grados o sin ningún ángulo la escena
    # salía «reflejo solar» con 0 MW; con el cenit del sol NaN o de relleno corría con umbrales de día de noche; y sin
    # él, con umbrales de noche sin saber si era de noche. Ninguna de esas pasadas se midió de verdad. Ahora, si falta
    # cualquiera de los cuatro, la escena es no medida con su propio motivo (0 MW como las demás, D36), sin dayflag ni
    # sunglint inventados, y angulos_invalidos dice cuáles. El .m no tiene este caso (recibe dayflag y sunglint ya
    # calculados por su llamador) y, con el reflejo NaN, devuelve la escena vacía; nosotros decimos por qué. Hoy son 0
    # records (ningún record de la vía con un ángulo ausente o no finito, censos F8-107 i2 y R3F3-102 i1). Con los
    # cuatro ángulos válidos el cálculo es el de siempre, con los mismos valores: el record no cambia.
    angulos_invalidos = angulos_invalidos_de(geom)
    if angulos_invalidos:
        dayflag, sg = None, float("nan")   # el reflejo NaN corta el detector en su primera línea (.m l. 87-89)
    else:
        dayflag = 0 if geom["solar_zenith"] > 90 else 1
        sg = sunglint_deg(geom["sensor_zenith"], geom["solar_zenith"], geom["sensor_azimuth"], geom["solar_azimuth"])
    b_mir, b_tir = cfg["bandas"]
    # POR QUÉ (S192, run 44768057665): el filtro de arriba cuenta píxeles con POSICIÓN, pero remuestrear_grilla
    # interpola sólo los que además tienen RADIANCIA. La geolocalización sale de la órbita y la actitud y existe
    # siempre; la radiancia puede faltar en escaneos enteros. En MOD021KM.A2026213.0300 los 81 primeros escaneos
    # (filas 0 a 809) traen en las bandas 21, 22 y 31 el DN 65527, «Rotation of Earth view Sector from nominal science
    # collection position» (MODIS L1B C7 UserGuide, Tabla 5.6.1): Mentolat, MacaCay y Hudson tenían 1.714 a 1.838
    # píxeles con posición y 0 con radiancia (experiments/_s192_no_points/diag_s192_no_points.json), y griddata
    # lanzó «No points given». Con menos de tres puntos no hay
    # triangulación (cero: ValueError; uno o dos: QhullError). La escena no está medida: se guarda vacía (0 MW, sin
    # píxeles) con motivo propio, como las escenas con media grilla sin dato (escena_invalida, ficha v1.27), en vez de
    # una excepción que deja la pasada sin record y el job en rojo. Desde tres puntos el camino es el de siempre.
    n_rad = {k: int((sel & np.isfinite(np.asarray(rad[b], float))).sum()) for k, b in (("mir", b_mir), ("tir", b_tir))}
    sin_radiancia = min(n_rad.values()) < MIN_PX_TRIANGULAR
    if sin_radiancia:
        m13g = np.full((g["n"], g["n"]), np.nan)
        m15g = m13g.copy()
    else:
        m13g, m15g = remuestrear_grilla(lat, lon, rad[b_mir], rad[b_tir], g)
    pos = posicion_de(g, vent_lat, vent_lon)
    # POR QUÉ (S193, F2-V303): diag_codigo_mirova.roi debe nombrar la caja que el detector usó. Antes decía la de la
    # grilla: «def» en todos los records V375 de la vía (28.930 en data/mirova_equivalent y 1.621 en sombra_34 en main
    # del 2026-11-21) aunque VIIRS 375 busca siempre en la C13 del cráter; y la de la grilla aunque se pasara tipo_roi.
    if cfg.get("roi1_half_m") is not None:
        # VIIRS 375: la caja de PD1 (C13 en el cráter dentro de la ROI1 física), igual en todos los volcanes
        box = caja_v375(g, vent_lat, vent_lon, lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
        roi_usada = ROI_DIAG_V375
    else:
        celda = celda_de(g, vent_lat, vent_lon)
        roi_usada = tipo_roi or g.get("roi", "def")
        box = caja_roi(roi_usada, n=g["n"], celda_crater=celda, inner_km=inner_km,
                       lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
    # S195: la zona A del laboratorio; en producción s_zona_a es None y la llamada es la de siempre.
    s_a = s_zona_a(nombre_volcan)
    zona_a = None if s_a is None else mascara_zona_a(box, pos, float(g["paso"]), inner_km)
    rec = procesar_grilla(m13g, m15g, g, box, dayflag, sg, pos, inner_km, sensor, familia=familia, roi=roi_usada,
                          zona_a=zona_a, s_a=s_a, piso_a=piso_zona_a(nombre_volcan))
    if angulos_invalidos:
        # el detector devolvió la escena vacía por el reflejo NaN; el motivo se reemplaza porque la causa es otra (S199).
        # Si además no hubo radiancia, el bloque siguiente pone ese motivo (no había nada que medir) y la lista queda.
        rec["diag_codigo_mirova"].update({"motivo_vacio": MOTIVO_ANGULO_AUSENTE,
                                          "angulos_invalidos": angulos_invalidos})
    if sin_radiancia:
        # con la grilla toda sin dato el detector ya devolvió la escena vacía (reflejo solar o media escena); el motivo
        # se reemplaza porque la causa es otra: no hubo radiancia que interpolar.
        rec["diag_codigo_mirova"].update({"motivo_vacio": "sin_radiancia_valida", "px_radiancia_valida": n_rad})
    # celdas_sin_dato cuenta celdas de la grilla sin dato DESPUÉS de interpolar: griddata llena todo lo que cae dentro
    # de la envolvente de los píxeles válidos, así que sólo ve celdas fuera de ella (bordes del gránulo). Un píxel
    # perdido dentro del gránulo no aparece aquí; para eso están las marcas de dato_faltante_crater (S190, F1M-V201).
    rec["diag_codigo_mirova"].update({"dayflag": dayflag, "sunglint": None if angulos_invalidos else round(sg, 2),
                                      "celdas_sin_dato": int(np.isnan(m13g).sum())})
    filas, cols = np.flatnonzero(sel.any(axis=1)), np.flatnonzero(sel.any(axis=0))
    ventana = (slice(filas[0], filas[-1] + 1), slice(cols[0], cols[-1] + 1))
    rec["diag_codigo_mirova"].update(dato_faltante_crater(rad, lat, lon, b_mir, b_tir, vent_lat, vent_lon,
                                                          g["paso"], ventana=ventana))
    # S199 (R3F3-107): un ángulo NaN se escribe null, no NaN: json.dump escribe NaN, que no es JSON y rompe la carga del
    # volcán en el navegador. Con los cuatro ángulos finitos es lo de siempre.
    rec.update({f"{k}_deg": round(v, 2) if math.isfinite(v) else None for k, v in geom.items()})
    if GENERAR_MINIATURA:
        # S184: también en las pasadas sin anomalía, con sun glint o escena inválida (la grilla existe igual): son las
        # que el operador necesita ver. Los alertados son los del record, para que imagen y número digan lo mismo.
        rec["_miniatura"] = miniatura_nti(m13g, m15g, [[p["fila"], p["col"]] for p in rec["anomaly_pixels"]],
                                          familia)
    return rec


def escala_nti(familia):
    """(NTI negro, NTI blanco) de la miniatura: el NTI de un cuerpo negro a ESCALA_MINIATURA_T_K con las longitudes de
    onda de la familia, con la misma Planck del .m que usa la vía."""
    cfg = FAMILIAS[familia]
    out = []
    for T in ESCALA_MINIATURA_T_K:
        a = float(temperatura_a_radiancia(T, cfg["lam_mir"]))
        b = float(temperatura_a_radiancia(T, cfg["lam_tir"]))
        out.append((a - b) / (a + b))
    return tuple(out)


def miniatura_nti(m13g, m15g, alertadas, familia):
    """NTI de la grilla ENTERA cuantizado a uint8: 0 a 254 gris en la escala fija, 255 sin dato.

    POR QUÉ el NTI y no la temperatura del térmico: de noche el NTI correlaciona 0,97 (mediana, 298 escenas de V750)
    con la temperatura de M15, así que la nube fría sale oscura igual, y además el foco salta en blanco; es lo que
    muestra MIROVA. POR QUÉ recalcularlo y no usar el del detector: el del detector pone en NaN lo que queda fuera de
    la caja y el M15 frío (BT <= 200 K), y la miniatura tiene que mostrar la escena entera; aquí sólo es sin dato lo que
    no tiene radiancia (fuera de la franja). Devuelve también los percentiles 2 y 98 del NTI para recalibrar la escala."""
    m13g = np.asarray(m13g, float)
    m15g = np.asarray(m15g, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13g - m15g) / (m13g + m15g)
    ok = np.isfinite(nti)
    lo, hi = escala_nti(familia)
    with np.errstate(invalid="ignore"):
        q = np.round(np.clip((nti - lo) / (hi - lo), 0.0, 1.0) * 254.0)
    u8 = np.where(ok, q, 255).astype(np.uint8)
    p2 = p98 = None
    if ok.any():
        p2, p98 = (round(float(x), 5) for x in np.percentile(nti[ok], (2, 98)))
    return {"u8": u8, "n": int(u8.shape[0]), "escala_nti": [round(lo, 6), round(hi, 6)],
            "alertadas": [[int(f), int(c)] for f, c in alertadas], "nti_p2": p2, "nti_p98": p98}


# ---------------------------------------------------------------------------------------------------- MODIS (S164)
def leer_radiancia_modis(ruta):
    """MIR y TIR de MODIS en radiancia (W m-2 sr-1 um-1, float64), como el probe del censo MOD-D
    (experiments/_s159/portes/probe_portes.py::leer_modis): las bandas por el lector de producción (DN > 32767 a NaN,
    MODIS L1B C7 UserGuide 5.6) y la MIR fusionada con la banda 22 primaria y la 21 donde la 22 satura (Coppola 2016a,
    la banda L21ok). POR QUÉ siempre B22 primaria y no el flag de producción: es la vía que midió el censo."""
    from .process_modis import read_modis_l1b, merge_mir_bands
    d = read_modis_l1b(ruta)
    b21, b22, b31 = (np.asarray(d[k], np.float64) for k in ("band21", "band22", "band31"))
    return {"MIR": merge_mir_bands(b21, b22, True), "TIR": b31}


def leer_geo_mxd03(ruta):
    """lat, lon (float64) y ángulos de observación en grados del MxD03 (geolocalización de 1 km).

    POR QUÉ el MxD03 y no la grilla de 5 km del MxD021KM que interpola producción: el censo MOD-D corrió con el MxD03,
    y la interpolada corre las posiciones 1 a 3 km hacia el nadir (memoria S151, project_modis_geo_interp_offset); el
    censo la midió aparte (fisica_geo5km) y no es la vía aprobada. Como el probe del censo: fuera de rango a NaN y los
    ángulos con su factor de escala, sin enmascararlos."""
    from pyhdf.SD import SD, SDC
    sd = SD(str(ruta), SDC.READ)
    lat = sd.select("Latitude").get().astype(np.float64)
    lon = sd.select("Longitude").get().astype(np.float64)
    ang = {}
    for k, nm in (("sensor_zenith", "SensorZenith"), ("sensor_azimuth", "SensorAzimuth"),
                  ("solar_zenith", "SolarZenith"), ("solar_azimuth", "SolarAzimuth")):
        s = sd.select(nm)
        ang[k] = s.get().astype(np.float64) * float(s.attributes().get("scale_factor", 1.0))
    sd.end()
    lat[(lat < -90) | (lat > 90)] = np.nan
    lon[(lon < -180) | (lon > 180)] = np.nan
    return lat, lon, ang
