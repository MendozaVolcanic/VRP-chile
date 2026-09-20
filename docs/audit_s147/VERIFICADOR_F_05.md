# Verificador con contexto limpio de F-05 (S147)

> **Encargo**: verificar el hallazgo *"MIROVA suma TODOS los píxeles alertados de la pasada;
> nosotros publicamos el núcleo de un cúmulo"* (`docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:407`,
> fila 17 en `:108`). El verificador recibió sólo el título y la ruta, con el preámbulo
> anti-fabricación entero y la regla de leer los PDF renderizando la página a imagen (A95).

## Veredicto

**Las citas son reales y correctas, la divergencia de código existe, y la premisa de A10 queda sin
respaldo citable. Pero el tamaño que F-05 le atribuye no sobrevive la medición.** Sobre 1.512
pares publicados, pasar a la suma cierra el **26 %** de la brecha de magnitud, no la mitad, y **no
mejora en los volcanes donde está el déficit**.

F-05 entra al plan **como divergencia a catalogar**, no como la palanca del 0,7.

La magnitud publicada la calculó **node ejecutando `frontend/index.html`** (A97), nunca un
predicado reescrito.

## Hallazgos

### 1. El valor se evapora al estratificar por volcán (gravedad 4, CONFIRMADO)
Sobre **1.512 pares publicados** (11 Tier A, ventana 2026-03-01 a 2026-09-20, referencia CONS más
OCR con alerta y VRP mayor que 0, pareo a 120 s, nocturno), la mediana de la razón contra MIROVA
pasa de **0,706 a 0,783** en VIIRS 375 (n = 1.285). Eso cierra 0,077 de 0,294, o sea el **26 %**.

| volcán (VIIRS 375) | n | publicado | suma | delta |
|---|---:|---:|---:|---:|
| Láscar | 271 | 0,560 | 0,591 | +0,031 |
| Isluga | 267 | 0,600 | 0,615 | +0,015 |
| PuyehueCordonCaulle | 200 | 1,037 | 1,719 | +0,682 |
| Lastarria | 177 | 0,550 | 0,782 | +0,232 |
| Tupungatito | 161 | 0,674 | 0,674 | +0,000 |
| PlanchonPeteroa | 121 | 0,966 | 0,975 | +0,009 |
| Chaitén | 46 | 1,330 | 1,349 | +0,019 |
| Villarrica | 26 | 0,903 | 0,903 | +0,000 |
| NevadosDeChillan | 9 | 1,120 | 1,120 | +0,000 |
| Copahue | 4 | 0,962 | 1,052 | +0,090 |
| Llaima | 3 | 0,431 | 0,431 | +0,000 |

Los dos volcanes con más muestra (Láscar e Isluga, 538 de 1.285 pares) se mueven +0,03 y +0,02 y
siguen en 0,56 y 0,62. En **5 de 11** el delta es exactamente 0,000, porque el record es de un
solo píxel y la suma ya es el núcleo. El que más gana (Puyehue Cordón Caulle) **ya estaba en
paridad** y pasaría a sobreestimar un 72 %. Es la misma compensación entre volcanes que la rebaja
S146 de A99 documentó.

**Consecuencia**: el déficit de Láscar e Isluga, que son el grueso del corpus, hay que buscarlo en
el **fondo** (D25, ya abierta) o en la detección, no en la agregación.

Partido por el cambio de régimen (A104), medianas de la razón por par:

| tramo | sensor | n | publicado | suma de píxeles |
|---|---|---:|---:|---:|
| antes de #535 | VIIRS375 | 1.152 | 0,692 | 0,766 |
| | VIIRS750 | 208 | 0,572 | 0,642 |
| desde #535 | VIIRS375 | 133 | 0,824 | 0,942 |
| | VIIRS750 | 10 | 0,323 | 0,475 |

El tramo posterior a #535 son 23 días con n = 144: el verificador declara que no lo usaría para
decidir. MODIS tiene 9 pares en total y lo marca como anecdótico.

### 2. La cita clave de Coppola 2026 está truncada, y lo cortado es el calificador (gravedad 3, CONFIRMADO)
`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`, página índice 5,
sección *Volcanic Radiative Power computation*, segundo párrafo. El párrafo real dice **"When more
than one pixel is detected,** pixel-level VRP values are subsequently summed ... the summed VRP of
all alerted pixels **associated with a volcanic thermal anomaly**".

El verificador fue a ver si el calificador invalida el hallazgo y concluye que **no**: la
asociación "volcánica" se decide después, por record, no por píxel. En la página índice 4 el paper
dice que los incendios no se filtran en ese paso y entran al cálculo de VRP, y la clasificación
por DBSCAN de la página índice 9 y 10 opera sobre la **serie de detecciones**, no sobre los
píxeles de una pasada.

### 3. F-05 atribuye a la ruta de 375 m dos banderas que no la gobiernan (gravedad 3, CONFIRMADO)
F-05 dice que el tablero publica `f5_core_vrp_mw` "con `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True` y
`FOCAL_CLUSTER_KEEP_PEAK = True`". Las dos banderas valen True, pero **`pipeline/process_viirs.py`,
que es el procesador de 375 m, no las importa ni las usa**: `ENABLE_FOCAL_CLUSTER_MAGNITUDE` la
importa sólo `process_modis.py`, y la variante `_VIIRS750` sólo `process_viirs_mod.py`.

**Consecuencia**: quien intente el A/B siguiendo el texto de F-05 tocaría las banderas equivocadas
para el sensor equivocado. Es un caso de manual de **A89**, cometido otra vez por quien auditaba.

### 4. El predicado que propone F-05 corre sobre una lista truncada a 100 píxeles (gravedad 3, CONFIRMADO)
`anomaly_pixels` es un **top 100 por VRP** (`np.argsort(-per_pixel_vrp_mw)[:100]` en los dos
procesadores), y algunos píxeles se mudan a `discarded_anomaly_pixels`. Ejemplo verificado en
`data/mirova_equivalent/Villarrica.json`, record 2025-02-15 06:30 MODIS_AQUA: `n_anomalous_pixels
= 302`, `len(anomaly_pixels) = 87`. El flag que ya existe, `ENABLE_SUM_VRP_REPORTING` (hoy False),
suma esa misma lista truncada.

El efecto medido es **inmaterial en esta población** (la razón suma sobre escena tiene mediana
1,0000 y el 97,0 % de los pares cae dentro del 2 %), pero la afirmación "ya está persistido el
predicado del paper" es falsa en general, y en un reproceso eruptivo el truncamiento mordería.

### 5. En VIIRS 750 la adopción no acerca, sobrepasa (gravedad 2, CONFIRMADO)
En razón agregada, VIIRS 750 pasa de **0,725 publicado a 1,153 sumando** (n = 218). El 17,4 % de
los pares superaría 1,5 veces a MIROVA, el 14,2 % superaría 3 veces y el 7,3 % superaría 10 veces.
En VIIRS 375 el agregado va de 0,647 a 0,856, que sí acerca.

**Consecuencia**: la decisión no puede ser un encendido uniforme. Por sensor es legítimo (el perfil
ya distingue sensores); por volcán está excluido por MISSION.

### 6. El archivo de MIROVA trae `Npix` y `Max_Dist`, y F-05 no los miró (gravedad 2, CONFIRMADO)
`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, volcanes chilenos, pasadas nocturnas:

| sensor | n | Npix mediana | Npix p90 | Npix máx | % con 1 píxel | Max_Dist mediana |
|---|---:|---:|---:|---:|---:|---:|
| MODIS | 12.938 | 3 | 8 | 97 | 18,4 % | 1.414 m |
| VIIRS 750 | 2.300 | 6 | 11 | 44 | 0,0 % | 1.677 m |
| VIIRS 375 | 32.669 | 3 | 7 | 37 | 18,3 % | 1.912 m |

O sea que "todos los píxeles alertados dentro de la caja de 50 por 50 km" es, en la práctica
chilena, **un puñado de píxeles dentro de unos 2 km**. Refuerza el hallazgo y a la vez lo acota:
no es una suma de escena. Pareando nuestros records de 2025 contra ese archivo, nuestra mediana de
`n_anomalous_pixels` es 2 y la de MIROVA es 2: **el conjunto alertado es comparable, lo que difiere
es cuánto de él publicamos**.

**Caveat declarado por el verificador**: ese archivo es el OSF (A105), filtrado, y el pareo es
íntegramente anterior a #535. Sirve para la forma del objeto, no como vara de paridad.

### 7. Adoptar la suma no cambia qué publicamos, sólo el número (gravedad 2)
La puerta de publicación usa `primary_cluster.vrp_mw` y `distance_class`, no la magnitud mostrada.
Cambiar de núcleo a suma **no abre ni cierra detecciones**, salvo el borde donde el núcleo da 0 y
la suma no (no cuantificado, SOSPECHA). O sea que F-05 **no toca la sobre-publicación**, que es la
brecha dominante. Baja el riesgo de adoptarlo y baja también su premio.

### 8. F-05 no está catalogada como divergencia (gravedad 1, CONFIRMADO)
Con las citas verificadas, merece número propio, como lo tienen D25 (fondo) y D17 (remuestreo),
que son sus hermanas de la misma tabla.

## La objeción del encargo, resuelta: archivo contra tiempo casi real

El encargo pedía vigilar que las citas no mezclaran el conjunto de datos publicado a posteriori
con el canal de tiempo casi real, que es lo que clonamos. El verificador lo resolvió con una cita
directa: **Campus et al. 2022, Sensors 22:1713, página impresa 7, sección 3.2**: *"The NRT
processing chain is made of 4 successive steps: (i) download; (ii) resampling; (iii) hot-spot
detection and (iv) calculation of the VRP."* La suma es el paso (iv) **de la cadena de tiempo casi
real**. Lo exclusivo del archivo es el umbral de VRP por sensor de la Tabla 1 y la clasificación
por DBSCAN, y ninguno de los dos es la regla de suma.

Las tres citas, renderizadas a 200 dpi y miradas: Campus et al. 2024 (Bull Volcanol 86:25, página
impresa 3, Eq. 1), Coppola et al. 2026 (Scientific Data, páginas índice 4 y 5), Campus et al. 2022
(Sensors 22:1713, página impresa 7, secciones 3.2 y 3.3). Ninguna inventada, ninguna mal atribuida.

## Sobre A10, que es lo que más cuesta

La contradicción que F-05 denuncia no es sólo textual, es **empírica**. De los cuatro candidatos,
`pc.vrp_mw`, que es el campo que A10 declara "lo que MIROVA reporta", es el **peor** contra MIROVA
en VIIRS 375: mediana **0,600**, contra 0,706 del núcleo publicado y 0,783 de la suma. La premisa
de A10 no la sostiene ni el paper ni el dato.

## Verificado limpio

- Las tres citas de F-05 son reales y están bien localizadas, incluida la que el propio F-05
  marcaba como no vista en imagen.
- La divergencia de comportamiento existe: no publicamos la suma de los píxeles alertados, sino un
  recorte, y hay dos recortes encadenados (cúmulo de 8 conexos, y después núcleo en 375 m).
- `pipeline/f5_core.py` está sano: cabecera FICHA presente, restricción a banda I explícita,
  paridad con el JavaScript con test (`tests/test_f5_core_python_s132.py`).
- El camino ya está andado en el código: `ENABLE_SUM_VRP_REPORTING` existe desde S37 y persiste
  `vrp_mw_sum_active`. Un A/B no exige escribir el cálculo, sólo encender el flag y reprocesar.
- Controles del instrumento: el control trivial de referencia contra sí misma da 1,000 y el de
  publicación da lo esperado.
- **Suciedad menor anotada, no tocada**: el control de identidad de `isValidDetection` devolvió
  `[0,1,1,1,0]` donde el docstring de `scripts/banco_paridad.py:154` espera `[1,1,1,1,0]`. No es
  fallo de la medición: es el cambio S139 (con cúmulo presente, `pc.vrp_mw = 0` ya no es detección
  válida) que dejó ese comentario desactualizado.
- Ningún archivo del repositorio fue modificado.

## Lo que no se pudo medir con lo que hay en disco

El efecto sobre **negativos limpios**. La población del verificador está condicionada a noches con
alerta de MIROVA y publicación nuestra, así que no dice nada de la sobre-publicación. Como el
cambio no toca la puerta de publicación (hallazgo 7), sospecha que el efecto ahí es sólo de
magnitud, pero **no lo midió**.
