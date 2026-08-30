# A Láscar le falta un píxel, no fondo — y eso cambia el diseño del experimento

> Números de `experiments/_s126_lascar/0{1,2}_*.py` → sus `.json` (S91).
> Trabajo **read-only** sobre los brazos ya en disco.

## El problema

Láscar es el sub-reporte que quedó vivo después de S126: **0,434** contra MIROVA, el
**45 %** de los pares de la muestra, y ninguno de los brazos E/F/G lo mueve (G lo deja
idéntico al control). No es un problema de posición: en las noches que MIROVA confirma
medimos a **0,18 km** del cráter con el píxel **+7,8 K** sobre el fondo. Detección
correcta, magnitud a la mitad.

## Primero, una hipótesis mía que resultó falsa

Predije que el anillo de fondo `[1,5–3] km` estaría **más caliente** que el global en
Láscar, contaminado por el halo geotermal de un cráter permanentemente activo —lo que
CLAUDE.md documenta como el problema D4—, y que eso deflactaría el ΔL.

**Es al revés.** Recuperando el fondo que el pipeline usó realmente (ver abajo), el
anillo está más **frío** que el global en los cuatro volcanes:

| volcán | bt del píxel | fondo efectivo | fondo global | efectivo − global |
|---|---|---|---|---|
| Láscar | 269,16 K | 261,83 K | 264,30 K | **−2,47 K** |
| Villarrica | 265,72 | 261,15 | 268,33 | −8,49 |
| Planchón-Peteroa | 263,26 | 257,51 | 266,17 | −8,05 |
| Puyehue-Cordón Caulle | 264,68 | 259,91 | 265,94 | −6,96 |

Láscar tiene la brecha más chica —desierto de altura, menos contraste topográfico
entre el edificio y su entorno— pero el signo es el mismo que en los nevados. El halo
crónico no aparece. Hipótesis descartada.

### Cómo se recuperó el fondo: invertir Wooster

Para un clúster de **un** píxel la magnitud es exactamente

```
vrp_mw = A_pix · WOOSTER · (L(bt_pixel) − L_bg) / 1e6
```

y todo salvo `L_bg` está persistido en el record. Despejando se obtiene el
`effective_L_bg` que el pipeline usó esa noche — una variable que **no se guarda** y
que gobierna toda la magnitud. Como el 81 % de los clústeres de Láscar son de un solo
píxel, la inversión cubre casi toda la serie.

## Entonces: ¿fondo o píxeles?

Las dos hipótesis son separables con aritmética sobre lo ya persistido. Para reproducir
el valor de MIROVA desde nuestro píxel hace falta, o bien bajar el fondo, o bien sumar
más píxeles. Se despejan las dos y se comparan contra la física de la escena: **el
fondo no puede ser más frío que el píxel más frío del disco de 3 km esa noche**.

Un par por noche, máximo de ambos lados (la convención del veredicto), restringido a
noches donde nuestra mejor pasada es un clúster de un píxel:

| volcán | n | nuestro | MIROVA | ratio | fondo usado | fondo **necesario** | píxeles necesarios |
|---|---|---|---|---|---|---|---|
| **Láscar** | 17 | 0,200 | 0,370 | 0,51 | 263,76 K | **248,34 K** | **1,96** |
| Villarrica | 6 | 0,400 | 0,560 | 0,83 | 262,72 | 257,12 | 1,20 |
| Planchón-Peteroa | 12 | 0,130 | 0,150 | 1,03 | 257,50 | 258,10 | 0,98 |
| PCC | 3 | 0,110 | 0,070 | 1,13 | 267,34 | 266,74 | 0,88 |

En Láscar el fondo necesario sería **248,34 K** cuando el píxel más frío que se vio en
el disco de 3 km era **275,61 K** — 27 K de diferencia. **Físicamente imposible en el
100 % de las noches.** Villarrica igual (100 %); PP y PCC en dos tercios.

**A Láscar no le falta fondo: le falta un píxel.** Necesita ~2 y sumamos 1.

> **Nota de método.** La primera versión de este cálculo comparaba *cada pasada* contra
> el máximo de MIROVA de la noche, y con 2-3 pasadas VIIRS 375 eso infla el objetivo:
> daba 4,85 píxeles necesarios en vez de 1,96. Corregido a un par por noche. El
> confound exageraba el déficit por un factor 2,5.

## De dónde sale el píxel que falta

Dos mecanismos, medidos:

**1. El filtro contextual recorta el clúster a uno solo** — es el término dominante.
El 81 % de los clústeres de Láscar son de un píxel. Y encaja con el A/B: apagar el
filtro (brazo E) movió Láscar 0,434 → 0,635, en la dirección correcta.

**2. `single_pixel_mode` se lleva el resto.** Está activo en los **110 de 110** records
de Láscar, aunque el docstring del propio módulo dice: *"Volcanes NO afectados … Lascar
…"*. Sobre los clústeres multi-píxel reporta el máximo en vez de la suma:

| volcán | records | multi-píxel con el modo activo | recorte |
|---|---|---|---|
| Láscar | 110 | 21 (19 %) | **1,34×** |
| PCC | 181 | 50 (28 %) | **1,67×** |
| Villarrica | 171 | 2 (1 %) | 1,46× |
| Planchón-Peteroa | 146 | 1 | 1,36× |

Es otra intención declarada que no coincide con la realidad — la misma clase de bug que
la máscara de nube. No explica el déficit por sí solo (sólo toca el 19 % en Láscar) pero
es real, y en PCC toca al 28 %.

## Lo que esto le hace al experimento en curso

Acá está el punto que cambia el diseño.

El A/B de la corona que está corriendo prueba **corona ON contra OFF, con el filtro
contextual encendido en los dos brazos**. Pero lo que el conjunto de la evidencia
sugiere es un **2×2**, y la celda interesante es la que nadie corrió:

| | filtro contextual ON | filtro contextual OFF |
|---|---|---|
| **anillo `[1,5–3]`** | control (hoy) | **brazo E** — Láscar mejora, Villarrica/PP explotan |
| **corona Eq.6** | brazo corona (corriendo) | **sin correr** ← acá |

El razonamiento: bajo un fondo **local**, un píxel de terreno tiene vecinos a su misma
temperatura, así que aporta ΔL ≈ 0 aunque se lo incluya. Es decir, **la corona vuelve
seguro incluir más píxeles**. Eso es exactamente lo que hace falta:

- **Láscar** necesita el segundo píxel → el filtro apagado se lo da.
- **Villarrica y Planchón** explotan con el filtro apagado porque los píxeles extra son
  terreno → con la corona esos mismos píxeles se autocancelan.

Ninguno de los dos ejes por separado resuelve las dos cosas; la combinación podría. Es
una hipótesis, no un resultado — pero es la celda que falta y es barata de correr.

## Riesgo para el criterio 3 del pre-registro

El pre-registro pide que **Láscar no caiga más de un 20 %** (es el canario de falso
negativo). La corona sola, sin tocar el filtro, **le baja la magnitud** —la estimación
read-only daba corona/hoy = 0,717 en noches confirmadas—, así que Láscar ya está en
0,434 y podría irse a ~0,31. **El brazo de la corona sola probablemente falle su propio
canario**, y por la razón correcta: le está sacando energía a un volcán al que ya le
falta.

Eso no invalida el A/B: lo que mide sigue siendo válido y hay que leerlo con el
criterio escrito. Pero conviene saber de antemano que un NO ADOPTAR en ese brazo **no
refuta la corona** — refuta la corona *sin* el segundo píxel.

## Qué hacer

1. Leer el A/B en curso contra su pre-registro, sin cambiarle los criterios.
2. Correr la celda faltante (**corona ON + filtro contextual OFF**) cuando se liberen
   slots de CI. No lanzarla ahora: hay 4 reprocesos en vuelo y sus jobs `merge`
   comparten el grupo `push-main`, que ya costó una corrida en S125.
3. Revisar `single_pixel_mode`: su docstring y su alcance real no coinciden. Decidir si
   Láscar y PCC deben estar dentro, con su propio A/B — no cambiarlo de prepo.

---

# Apéndice — `single_pixel_mode`: la justificación caducó, pero quitarlo no conviene

> Números de `experiments/_s126_lascar/03_costo_single_pixel_mode.py`.

El modo reporta `max(per_pixel_vrp)` en vez de la suma cuando el clúster cae en régimen
sub-MW. Nació para **desinflar** volcanes que sobre-reportaban —Tupungatito 30×,
Chaitén 2,5×— y su docstring dice textual: *"Volcanes NO afectados … Lascar …"*. Está
activo en los **110 de 110** records de Láscar.

**El cálculo es exacto, no un preview** (A18): el modo se aplica *después* de la
selección del clúster y sólo cambia el número reportado — no toca detección, ni
posición, ni qué clúster gana. Revertirlo sobre los records persistidos da el valor que
habría salido. El método de identificar los píxeles del clúster (los `n_pixels` más
cercanos al centroide) se validó contra los clústeres de un píxel: **525 de 525
coinciden**, peor desvío 0,0005 MW.

| volcán | noches | ratio hoy | ratio sin el modo | cambio | noches tocadas |
|---|---|---|---|---|---|
| Puyehue-Cordón Caulle | 21 | 0,722 | **0,860** | +0,138 | 7 |
| Villarrica | 8 | 0,764 | 0,832 | +0,068 | 2 |
| **Láscar** | 35 | 0,434 | **0,480** | +0,045 | 12 |
| Isluga | 94 | 0,541 | 0,573 | +0,032 | 23 |
| Planchón-Peteroa | 13 | 0,957 | 0,966 | +0,008 | 1 |
| **Tupungatito** | 49 | 0,713 | **0,713** | **0,000** | **0** |
| Lastarria | 74 | 0,417 | 0,417 | 0,000 | 2 |
| **Chaitén** | 22 | 1,177 | **1,414** | **+0,237** | 13 |

## Dos lecturas, y llevan a decisiones distintas

**La justificación original caducó.** En **Tupungatito el modo no toca ni una sola
noche** — y es el volcán para el que se construyó (30× de sobre-reporte). Lo curaron
otras cosas en el camino (nadir-fijo S103, ctxpeak S100), y hoy ya no tiene clústeres
multi-píxel en régimen sub-MW. La razón por la que existe se evaporó.

**Pero quitarlo perdería un volcán de banda.** Chaitén pasa de 1,177 a **1,414** —
cruza el techo de la banda \[0,7–1,4] por un pelo, y ahí el modo sí está haciendo su
trabajo (13 de 22 noches tocadas). Contando volcanes en banda: **7/9 hoy contra 6/9 sin
el modo**. Es el mismo criterio pre-registrado que hizo caer al brazo E, y da el mismo
veredicto.

## Recomendación

**No quitarlo, y corregir su docstring.** El modo es hoy un neto casi nulo: le devuelve
entre 0,03 y 0,14 de ratio a cinco volcanes y le saca 0,24 a Chaitén. No es la palanca
de Láscar —le devuelve 0,045 de los 0,57 que le faltan— así que sacarlo no resuelve
nada y cuesta un volcán.

Lo que sí hay que arreglar es la **documentación**: el docstring afirma que Láscar y
PCC no están afectados y están entre los que más toca (12 y 7 noches). Es la misma
clase de defecto que la máscara de nube: una afirmación sobre el estado del sistema que
nadie verificó. Y conviene registrar que **su justificación original ya no aplica**, por
si en el futuro alguien lo evalúa creyendo que sigue sosteniendo a Tupungatito.

---

# Re-verificación con la máscara de nube apagada (A8)

Todo el análisis de arriba usó `_s125_mag_control`, reprocesado en S125 — es decir **con
la máscara de nube encendida**. Después del A/B de la máscara quedó disponible
`_s126_corona_off`, un control fresco reprocesado **con la máscara apagada**, que es como
corre producción hoy. Repetir el cálculo ahí es obligatorio antes de dar el hallazgo por
bueno (A8: verificar con data fresca, no asumir).

| volcán | n | ratio | fondo usado | fondo **necesario** | píxeles necesarios | fondo imposible en |
|---|---|---|---|---|---|---|
| **Láscar** | 11 | 0,64 | 261,59 K | **238,37 K** | **1,57** | 100 % |
| Villarrica | 5 | 0,86 | 262,60 | 257,12 | 1,16 | 100 % |
| Planchón-Peteroa | 10 | 1,02 | 259,30 | 258,10 | 0,99 | 70 % |

**La conclusión no cambia y se refuerza.** El fondo que haría falta en Láscar baja a
238,4 K contra un píxel más frío disponible de 272,8 K — 34 K de diferencia, aún más
imposible que con la máscara encendida. Sigue siendo un problema de píxeles.

Lo que sí cambia es el **tamaño** del déficit: Láscar pasa de necesitar 1,96 píxeles a
1,57, y su ratio sube de 0,51 a 0,64. Eso es coherente con el veredicto de la máscara
—apagarla ya lo acercó a MIROVA— y significa que el hueco que queda por cerrar con el
segundo píxel es algo menor de lo que decía la primera medición.

El `n` cae (Láscar 17 → 11) porque el control fresco tiene más detecciones y por lo
tanto más clústeres multi-píxel, que este cálculo excluye por construcción.
