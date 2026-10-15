# ════════════════════════════════════════════════════════════════════
# FICHA SDA · diurno.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Decidir, en un solo lugar, si la réplica procesa VIIRS de día y con qué umbrales
#                 (rama diurna de MIROVA, D-10, issue #813). Apagado por flag en producción.
# Lógica        : Con ENABLE_DAYTIME_VIIRS = True y una pasada diurna (elevación solar > 0 sobre el
#                 volcán), los Tests 2 y 3 y el umbral K1 usan la columna diurna de la Tabla 1 de
#                 Coppola 2016a; el filtro nocturno de descarga y de proceso deja de aplicarse a VIIRS.
#                 Con el flag apagado devuelve los umbrales nocturnos tal cual (sin copia) y el
#                 filtro nocturno de siempre: el pipeline es bit a bit el anterior.
# Modelo/método : Regla determinista (selección de umbrales publicados). Sin ML. NO es caja negra (5.5).
# Datos entrada : Nombre de plataforma/sensor, fecha UTC de la pasada, lat/lon del volcán. SIN datos
#                 personales.
# Variables     : ENABLE_DAYTIME_VIIRS, NTI_K1_DAY, DNTI_CONTEXTUAL_C1_DAY, C2_DNTI_DAY, C2_DETI_DAY,
#                 N_SIGMA_MIR_DAY (pipeline.profile); elevación solar (pipeline.store).
# Limitaciones  : De día la luz solar reflejada entra al MIR; el paper la compensa subiendo umbrales
#                 y acepta falsas alertas diurnas bajo 5 MW (Coppola 2016a p. 16-17). Los caminos
#                 sin número diurno en el paper quedan como de noche (lista abajo, PREGUNTAS).
# Refs/datos    : Coppola 2016a (sp426.5.pdf p. 7 Tabla 1); Campus et al. 2022 (Sensors 22:1713,
#                 p. 16 §5, p. 17 Tabla 4). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""Rama diurna de VIIRS: la única lectura del flag y la única fuente de los umbrales diurnos.

EL FENÓMENO. De día el canal de infrarrojo medio (3,7 a 4 µm) suma a la emisión térmica la luz
solar reflejada: una nube, un salar o una ladera clara levantan píxeles sin que haya nada caliente
debajo, y el NTI y el ETI de toda la escena se vuelven más variables. MIROVA no deja de mirar de día:
sube los umbrales (Coppola 2016a, p. 7, columna derecha: los parámetros se separan de noche y de
día porque «solar effects amplify the variability» de NTI y ETI). MIROVA procesa VIIRS de día
(Campus et al. 2022, p. 16 §5 y p. 17 Tabla 4: la frecuencia de alerta baja de 51 % de noche a
20 % de día por esos umbrales). Nuestra réplica descartaba todo VIIRS diurno.

POR QUÉ UN MÓDULO. El descarte del día vive en cuatro lugares distintos del pipeline: el filtro
previo a la descarga (fetch.py), el salto del gránulo (scripts/run_pipeline.py), los umbrales de
los procesadores y el rechazo de store.py; y la auditoría semanal reusa la regla de store para
filtrar la referencia. En S92 un A/B diurno de MODIS abrió una sola compuerta y midió cero sin
saberlo (experiments/_s92_daytime_diag/FINDINGS.md). Acá todos los consumidores llaman a este
módulo, y el flag se lee en el momento de la llamada desde pipeline.profile (A89, A118).

PREGUNTAS (caminos que de día quedan igual que de noche porque el paper no da número; no se
inventan umbrales):
- Test 1 integrado (compute_test1_mir): suma MIR ABSOLUTO sobre un disco de 3 km. Es un detector
  propio (D30) sin columna diurna en ningún paper. De día el Sol calienta y refleja en todo el disco;
  es el camino con más riesgo de sobre-publicar. Queda con TEST1_K_SIGMA de noche.
- Compuerta bt > t_bg + NTI_BT_SANITY_K de los Tests 2 y 3 (D22): no está en el paper ni de noche.
- Camino de BT (apagado en producción, D31): con el flag encendido usa N·σ = N_SIGMA_MIR_DAY (15),
  la misma analogía con C2 que ya usa de noche (5/10), igual que la rama diurna de MODIS (S90).
- N_SIGMA_MIR uniforme (umbral de diagnóstico y camino de BT sin dual-ROI): sin cambio.
- Máscara de nube por I05 (apagada en producción, cloud_mask_bt_k = 0): sin cambio.
- Tope D9 (fondo bajo 270 K): calibrado de noche contra cirrus; sin cambio.
- Compuerta de consistencia TIR y VRP TIR (I05): «sólo noche» en vrptir.py; sin cambio.
- Overrides de experimento C1_SUMMIT_OVERRIDE y C2_SUMMIT_OVERRIDE (None en producción): si se
  fijaran, también actuarían de día. El override VIIRS_C2_OVERRIDE_NIGHT sí se anula de día.
"""
from __future__ import annotations

from datetime import datetime


def flag_viirs_diurno() -> bool:
    """Valor VIVO del flag (se lee en cada llamada, no al importar), para que un solo parche en
    pipeline.profile alcance a todos los consumidores."""
    from pipeline import profile as _perfil
    return bool(_perfil.ENABLE_DAYTIME_VIIRS)


def es_viirs(nombre: str) -> bool:
    """Plataforma o sensor VIIRS en la convención del proyecto (VIIRS_SNPP, VIIRS_NOAA20_750...)."""
    return str(nombre).upper().startswith("VIIRS")


def viirs_diurno_habilitado(nombre: str) -> bool:
    """True si el perfil abre el día para esta plataforma o sensor."""
    return es_viirs(nombre) and flag_viirs_diurno()


def aplica_filtro_nocturno(nighttime_only: bool, plataforma: str) -> bool:
    """¿Se descarta el gránulo diurno de esta plataforma antes de descargarlo o procesarlo?

    POR QUÉ: con el flag apagado es exactamente `nighttime_only` (comportamiento de siempre). Con el
    flag encendido, VIIRS no se filtra y MODIS sigue con su regla (su rama diurna tiene flag propio).
    """
    return bool(nighttime_only) and not viirs_diurno_habilitado(plataforma)


def pasada_es_diurna(fecha_utc: str, lat: float, lon: float) -> bool:
    """True si el Sol está sobre el horizonte del volcán a la hora de la pasada.

    Misma regla que store.py (`_solar_elevation`, elevación > 0) y que la rama diurna de MODIS
    (`process_modis._scene_is_day`), sobre la misma fecha que se escribe en el record, así que el
    procesador y store no pueden discrepar sobre la misma pasada. Fecha no parseable: noche
    (conservador, no se aplican umbrales diurnos a una pasada dudosa).
    """
    from pipeline.store import _solar_elevation
    try:
        dt = datetime.strptime(str(fecha_utc), "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return False
    return _solar_elevation(lat, lon, dt) > 0


def umbrales_viirs(es_dia: bool, habilitado: bool, noche: dict) -> dict:
    """Juego de umbrales de la pasada para un procesador VIIRS.

    `noche` lo arma el procesador con SUS globales (así un parche de test sobre el módulo sigue
    actuando). Si la pasada no es diurna o el flag está apagado se devuelve ESE MISMO objeto, sin
    copiar ni releer nada: no hay forma de que el camino apagado cambie un valor.

    Día (Coppola 2016a, p. 7, Tabla 1, columna Daytime, ROI1 = ROI2): K1 = -0,6, C1 = 0,02 y
    C2 = 15 para dNTI y dETI. El override nocturno de C2 de VIIRS (Di Bella n = 12, S46) no tiene
    versión diurna y se anula.
    """
    if not (habilitado and es_dia):
        return noche
    from pipeline import profile as P
    return {
        "dia": True,
        "nti_k1": P.NTI_K1_DAY,
        "n_sigma_summit": P.N_SIGMA_MIR_DAY,
        "n_sigma_scene": P.N_SIGMA_MIR_DAY,
        "c1": P.DNTI_CONTEXTUAL_C1_DAY,
        "c1_summit": P.DNTI_CONTEXTUAL_C1_DAY,
        "c1_scene": P.DNTI_CONTEXTUAL_C1_DAY,
        "c2_dnti_summit": P.C2_DNTI_DAY,
        "c2_dnti_scene": P.C2_DNTI_DAY,
        "c2_deti_summit": P.C2_DETI_DAY,
        "c2_deti_scene": P.C2_DETI_DAY,
        "viirs_c2_override": None,
    }
