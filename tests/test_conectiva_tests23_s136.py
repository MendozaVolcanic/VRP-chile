"""S136 - la conectiva de los Tests 2 y 3: la formula del paper contra su propia prosa.

EL PROBLEMA. Coppola 2016a define los Tests 2/3 con un `or` literal (verificado en el PDF, p.7):
    dNTI > C1  or  dNTI > mu + C2*sigma
que es equivalente a  dNTI > min(C1, mu + C2*sigma), y es lo que el pipeline implementa.

Pero tres lineas mas abajo el MISMO paper explica: "the parameter C1 implies that a MINIMUM
THRESHOLD needs to be EXCEEDED in order to flag a pixel as active. HOWEVER, when highly variable
scenes are analysed, the detection is achieved using STATISTICAL ANALYSIS of the whole scene."
Eso describe  max(C1, mu + C2*sigma):
  - escena homogenea (sigma chico): C1 es el minimo a superar     -> max = C1
  - escena variable  (sigma grande): manda el estadistico          -> max = mu + C2*sigma
Con min() pasa lo contrario en los dos casos, y medido sobre los records en disco el piso C1
gobierna el 100 % de MODIS y el 99,9 % de VIIRS: el contraste con la escena nunca decide.

QUE ATAN ESTOS TESTS. Que el flag exista, que su default NO cambie el comportamiento de hoy, y
que la rama de la prosa se comporte como la prosa dice en los DOS regimenes de escena. Sin esto,
un A/B sobre la conectiva no tendria sustrato verificable (leccion de S130/S133: medir que el
brazo realmente lee lo que declara antes de interpretar sus numeros).
"""
import numpy as np
import pytest

FLAG = "ENABLE_TESTS_23_PROSE_BRANCH"


def _bg(shape, rng, noise):
    """Fondo bien condicionado para la regresion: NTI = NTI_app + ruido."""
    nti_app = rng.uniform(-0.99, -0.95, shape)
    nti = nti_app + rng.normal(0.0, noise, shape)
    return nti, nti_app


def _escena(noise, pico_nti, seed):
    """Escena de 20x20 con un solo pixel candidato en el centro.

    `noise` fija la variabilidad del fondo, o sea sigma: chico = escena homogenea (sin nubes,
    terreno parejo), grande = escena variable (nubes dispersas, mosaico nieve/roca).
    `pico_nti` fija cuanto sobresale el candidato.
    """
    shape = (20, 20)
    rng = np.random.default_rng(seed)
    nti, nti_app = _bg(shape, rng, noise)
    bt = np.full(shape, 268.0)
    nti[10, 10] = pico_nti
    nti_app[10, 10] = -0.97      # se aparta de la diagonal => dETI alto, Test 3 pasa
    bt[10, 10] = 285.0
    return {"nti": nti, "nti_app": nti_app, "bt": bt,
            "roi_mask": np.ones(shape, dtype=bool),
            "dist_km": np.full(shape, 2.0)}


def _correr(data, prosa=None):
    from pipeline.detection_context import first_pass_tests_2_and_3
    kw = dict(nti=data["nti"], nti_app=data["nti_app"], bt=data["bt"],
              roi_mask=data["roi_mask"], dist_km=data["dist_km"],
              t_bg=268.0, bt_sanity_k=3.0,
              c1_dnti_summit=0.003, c1_deti_summit=0.003,
              c2_dnti_summit=5, c2_deti_summit=5, inner_km=5.0)
    if prosa is not None:
        kw["use_prose_branch"] = prosa
    hot, diag = first_pass_tests_2_and_3(**kw)
    return int(np.sum(hot)), diag


# ------------------------------------------------------------------ el flag

def test_el_flag_existe_y_su_default_es_el_comportamiento_de_hoy():
    """El default NO puede cambiar produccion: la formula literal sigue siendo la de por defecto."""
    import pipeline.profile as P
    assert hasattr(P, FLAG), f"falta el flag {FLAG} en pipeline.profile"
    assert getattr(P, FLAG) is False, (
        f"{FLAG} debe ser False en el perfil operacional: encenderlo es una adopcion que "
        "exige A/B con criterio pre-registrado (A18/A91)")


def test_el_parametro_por_defecto_no_altera_el_resultado():
    """Llamar sin el parametro y con prosa=False debe dar exactamente lo mismo."""
    d = _escena(noise=0.0005, pico_nti=-0.5, seed=42)
    assert _correr(d)[0] == _correr(d, prosa=False)[0]


# ------------------------------------------------------------------ los dos regimenes

def test_en_escena_VARIABLE_la_prosa_es_mas_estricta():
    """El caso de Stromboli: nubes dispersas suben sigma.

    Con la formula (min) el piso queda por debajo del contraste y AFLOJA el umbral justo cuando
    la escena es dificil. Con la prosa (max) manda el contraste, que es lo que el paper dice
    para escenas muy variables.
    """
    d = _escena(noise=0.01, pico_nti=-0.93, seed=7)     # candidato marginal, fondo con textura
    n_formula, diag = _correr(d, prosa=False)
    n_prosa, _ = _correr(d, prosa=True)
    assert diag["sd_dnti"] is not None and diag["sd_dnti"] > 0
    umbral_estadistico = diag["mu_dnti"] + 5 * diag["sd_dnti"]
    assert umbral_estadistico > 0.003, (
        "la escena de este test debe ser variable: el contraste tiene que quedar por ENCIMA "
        f"del piso 0.003, y quedo en {umbral_estadistico}")
    assert n_prosa <= n_formula, "la prosa nunca puede ser mas permisiva en escena variable"
    assert n_prosa < n_formula, (
        f"en escena variable la prosa debe cortar pixeles que la formula deja pasar "
        f"(formula {n_formula}, prosa {n_prosa})")


def _escena_lisa(pico_nti, seed):
    """Escena SIN textura local: el fondo es un gradiente suave, no ruido.

    Ojo, esto es el corazon del test y me costo un intento: `dNTI` es el NTI del pixel menos la
    media de sus 8 vecinos, o sea mide textura LOCAL. Un fondo aleatorio uniforme, aunque su
    rango global sea chico, es localmente aspero y dispara sigma_dNTI. "Terreno homogeneo" en el
    sentido del paper es terreno SIN textura de pixel a pixel: un gradiente ordenado lo
    representa, y ademas conserva el rango global que la regresion NTI_bk necesita.
    """
    shape = (20, 20)
    rng = np.random.default_rng(seed)
    fil = np.linspace(-0.99, -0.95, shape[0])[:, None]
    nti_app = np.repeat(fil, shape[1], axis=1) + rng.normal(0.0, 1e-6, shape)
    nti = nti_app.copy()
    bt = np.full(shape, 268.0)
    nti[10, 10] = pico_nti
    nti_app[10, 10] = float(fil[10, 0])   # se aparta de la diagonal => dETI alto
    bt[10, 10] = 285.0
    return {"nti": nti, "nti_app": nti_app, "bt": bt,
            "roi_mask": np.ones(shape, dtype=bool),
            "dist_km": np.full(shape, 2.0)}


def test_en_escena_HOMOGENEA_la_prosa_impone_el_piso():
    """El otro extremo: sin nubes y terreno parejo, sigma tiende a 0.

    Ahi el contraste da un umbral irrisorio y el paper dice que C1 impone "un umbral minimo que
    hay que superar". Con la formula (min) el piso NO actua y pasa un candidato debilisimo que
    con la prosa quedaria cortado.
    """
    # Se barre la intensidad del candidato en vez de calibrar un valor a mano: lo que hay que
    # probar es que EXISTE la franja donde la formula deja pasar y la prosa corta, no un numero.
    hallada = None
    for pico in (-0.9699, -0.9695, -0.969, -0.968, -0.9675, -0.967, -0.966, -0.965):
        d = _escena_lisa(pico_nti=pico, seed=11)
        n_formula, diag = _correr(d, prosa=False)
        n_prosa, _ = _correr(d, prosa=True)
        umbral_estadistico = diag["mu_dnti"] + 5 * diag["sd_dnti"]
        assert umbral_estadistico < 0.003, (
            "la escena de este test debe ser homogenea: el contraste tiene que quedar por DEBAJO "
            f"del piso 0.003, y quedo en {umbral_estadistico}")
        assert n_prosa <= n_formula, "la prosa nunca puede ser mas permisiva"
        if n_formula >= 1 and n_prosa == 0:
            hallada = (pico, n_formula, n_prosa)
            break
    assert hallada is not None, (
        "en escena homogenea debe existir un candidato que la formula deje pasar (porque el "
        "piso C1 no actua) y que la prosa corte (porque C1 es el minimo a superar). No se "
        "encontro en el barrido, asi que la rama de la prosa no esta imponiendo el piso.")


def test_un_pico_franco_se_detecta_con_las_dos_lecturas():
    """Red de seguridad: una anomalia clara no puede perderse por cambiar la conectiva.

    Es el papel que cumplen Ubinas (-0,91) y Villarrica (-0,93) en la bateria del Apendice A.
    """
    d = _escena(noise=0.0005, pico_nti=-0.5, seed=42)
    assert _correr(d, prosa=False)[0] >= 1
    assert _correr(d, prosa=True)[0] >= 1


# ------------------------------------------------------------------ el segundo pase

def test_el_segundo_pase_tambien_respeta_la_conectiva():
    """El paper: el second run REAPLICA los tests 2 y 3, asi que le toca la misma conectiva."""
    import inspect
    from pipeline.detection_context import second_pass_adjacent
    par = inspect.signature(second_pass_adjacent).parameters
    assert "use_prose_branch" in par, (
        "second_pass_adjacent reaplica los Tests 2/3 (sp426_5.txt:354-356): si no acepta el "
        "parametro, el brazo del A/B quedaria a medias y sus numeros serian ininterpretables")
    assert par["use_prose_branch"].default is False


# ------------------------------------------------------------------ cableado real

def test_los_tres_procesadores_pasan_el_flag():
    """Un flag que existe pero nadie cablea es el anti-patron A89: el A/B correria sin sustrato."""
    import re
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    for archivo in ("process_viirs.py", "process_modis.py", "process_viirs_mod.py"):
        src = (raiz / "pipeline" / archivo).read_text(encoding="utf-8")
        # frontera de palabra, no subcadena (A92)
        assert re.search(r"(?<![A-Za-z0-9_])use_prose_branch\s*=", src), (
            f"{archivo} no pasa use_prose_branch al first pass")
        assert re.search(r"(?<![A-Za-z0-9_])" + FLAG + r"(?![A-Za-z0-9_])", src), (
            f"{archivo} no importa ni usa {FLAG}")


def test_la_formula_y_la_prosa_son_min_y_max_de_verdad():
    """Guard de forma: que el codigo siga eligiendo entre min y max, y no otra cosa."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "pipeline" / "detection_context.py").read_text(
        encoding="utf-8")
    # S138 (AUDIT_S138 C4): los asserts anteriores (`max(` con frontera y `"min(" in src`)
    # pasaban por coincidencia con recortes de bounding box, `max(anomaly_floor_k, ...)` y
    # `min_bg_pixels`. La conectiva real es una expresion, no una llamada: se vigila esa expresion
    # y que aparezca en el primer pase y en el segundo (l. 510 y 924 al escribir esto).
    patron = r"combinar\s*=\s*max\s+if\s+use_prose_branch\s+else\s+min\b"
    n = len(re.findall(patron, src))
    assert n >= 2, (
        f"la conectiva `combinar = max if use_prose_branch else min` aparece {n} veces; "
        "se esperan al menos 2 (primer y segundo pase)")
