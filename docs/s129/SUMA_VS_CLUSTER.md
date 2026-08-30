# S129 · MIROVA suma todos los píxeles alertados; nosotros publicamos uno solo

> Medición: `experiments/_s129_suma/01_suma_vs_cluster.py` → `01_suma_vs_cluster.json`.
> Read-only. Un par por noche, máximo de ambos lados, estratificado por volcán.

## El fenómeno

Una anomalía térmica volcánica rara vez cabe en un píxel. Un domo, un campo fumarólico
o un lago cratérico caliente elevan varios píxeles vecinos, cada uno un poco sobre el
fondo. **La energía del rasgo es la suma de todos esos excesos**, no la del más caliente
ni la de un subconjunto elegido por cercanía.

Coppola et al. 2019 —el paper que describe el sistema que clonamos, leído a fondo por
primera vez en esta sesión— escribe la magnitud así (p. 3, verbatim):

> **VRP = 18,9 · A_pixel · Σ<sub>i=1</sub><sup>npix</sup> (L<sub>MIR,alert</sub> − L<sub>MIR,bk</sub>)<sub>i</sub>**
>
> *«where **npix is the number of alerted pixels** … A_pixel is the pixel size (1 km² for
> the resampled MODIS pixels), and 18.9 is a constant of proportionality»*

Nosotros publicamos `primary_cluster.vrp_mw`: **un** clúster, elegido por cercanía al
cráter. `ENABLE_SUM_VRP_REPORTING = False`.

## La tensión con A10, y por qué las dos cosas eran ciertas

La regla **A10** dice desde S60 lo contrario — que `pc.vrp_mw` «es lo que MIROVA
reporta», y que usar la suma scene-wide oculta problemas. A10 no salió de la nada: la
suma scene-wide de **nuestro** pipeline incluye píxeles calientes a 20 km —salares,
incendios, el valle tibio de A69— que el criterio de alerta de MIROVA nunca habría
marcado.

Por eso la medición necesita un **tercer brazo**, y el criterio se pre-registró antes de
mirar: si sumar explica parte del déficit, el brazo intermedio queda **entre** los otros
dos y más cerca de 1,0 que el actual.

## El resultado

| brazo | qué es | n | mediana | IC95 |
|---|---|---|---|---|
| **A** | `primary_cluster.vrp_mw` — lo que publicamos hoy | 1.049 | **0,730** | [0,704 – 0,767] |
| **B** | suma de los anómalos dentro de 5 km — la lectura del paper, acotada por su corte proximal (p. 4) | 922 | **0,798** | [0,763 – 0,833] |
| **C** | `record.vrp_mw` scene-wide — lo que A10 prohíbe, con razón | 1.026 | **0,924** | [0,879 – 0,967] |

**B queda entre A y C, y más cerca de 1,0 que A**, exactamente como se pre-registró. Los
intervalos de A y B apenas se tocan (0,767 contra 0,763); los de A y C no se solapan.

**Lectura**: pasar de «un clúster» a «la suma de lo próximo» recupera unos **7 puntos**
del déficit. Los otros 13 que aparecen en el brazo C son mayoritariamente contaminación
—A10 tenía razón sobre eso— y no señal recuperable.

**Las dos reglas eran compatibles y nadie lo había medido**: MIROVA suma, pero suma **lo
que alertó**, y su alerta ya está acotada por distancia. El campo correcto para comparar
no es ninguno de los dos que teníamos: es **la suma dentro del radio de alerta**.

## Por volcán — dos casos que importan

| volcán (VIIRS375) | A cluster | B suma <5 km | Δ |
|---|---|---|---|
| **Lastarria** | 0,575 | **0,844** | **+0,27** |
| Láscar | 0,603 | 0,683 | +0,08 |
| Planchón-Peteroa | 0,921 | 1,040 | +0,12 |
| Isluga | 0,579 | 0,603 | +0,02 |
| Tupungatito | 0,692 | 0,706 | +0,01 |
| Chaitén | 1,257 | 1,637 | +0,38 (empeora: ya sobre-reporta) |
| **PCC** | 0,836 | **0,113** (n=23) | ⚠️ ver abajo |

**Lastarria es el caso de manual**: su anomalía es el campo fumarólico Lazufre, extendido
y difuso. Un clúster puntual se pierde casi un tercio de la energía; sumar lo próximo la
recupera. Es coherente con lo que Steffke & Harris documentan — en anomalías débiles y
repartidas, perder píxeles marginales cuesta desproporcionadamente.

**⚠️ PCC es un artefacto de MI corte, no un resultado.** Su lacolito está a 7-10 km del
punto de referencia (por eso su `inner_radius_km` es 20, el único así), de modo que un
radio proximal de 5 km excluye casi toda su anomalía: quedan 23 pares de 100 y la mediana
se desploma a 0,113. **No es que sumar le haga mal a PCC — es que el corte de 5 km está
mal para PCC.** Un brazo B por volcán tendría que usar su propio radio.

## Qué NO prueba

**No reemplaza el A/B** (A18): el reproceso real vuelve a correr la selección de clúster
desde cero y puede elegir otra cosa. Esto dice **dónde apuntar**, no cuánto va a mejorar.

Y es **un cuarto mecanismo** que se suma a los tres de S128, no un reemplazo. El déficit
de magnitud tiene ahora cuatro contribuyentes identificados, todos con respaldo verbatim:

| mecanismo | firma | cuánto explica |
|---|---|---|
| remuestreo faltante (+ bow-tie) | crece con el cenit | ~1,41× entre nadir y 35-50° |
| **selección de clúster vs suma** | **uniforme, mayor en anomalías extendidas** | **~7 puntos (0,730 → 0,798)** |
| fondo autorreferente de magnitud | uniforme | sin medir (necesita reproceso) |
| umbral inflado (GAP #A) | mayor en régimen débil | sin medir (necesita reproceso) |
