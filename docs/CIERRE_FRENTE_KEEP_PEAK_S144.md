# Cierre del frente: ¿el cúmulo lejano de `keep_peak` es el objeto que MIROVA vio? (S144)

> **Estado: frente CERRADO el 2026-09-19 por decisión de Nicolás.** La medida pre-registrada
> (`PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`, v7, commit `1b0c37a5d`) **nunca se corrió sobre su
> muestra**. No hizo falta: los nulos y controles que las siete rondas de verificación midieron sobre
> estratos ajenos a esa muestra ya contestan la pregunta, y correrla habría dado INCONCLUSO el 90 % de
> las veces con los umbrales pre-registrados.
>
> Todo lo que este documento afirma está medido por una ronda concreta, con su informe versionado al
> lado y su script en `experiments/_s144_keep_peak_direccion/verificadores/`.

## 1. De dónde venía el frente

El A/B de S143 midió que **apagar `keep_peak` es lo único que baja la sobre-publicación** de VIIRS 375,
pero la regla de cero pérdidas le cobró 5 noches: MIROVA alertó y un cúmulo nuestro caía dentro de su
cota de distancia. Esa cota compara **radios sin acimut** (A93, A107), así que no puede decidir si era
el mismo objeto. La decisión 1 del traspaso S144 pedía medirlo con dirección, usando los GeoTIFF que
MIROVA publica por pasada.

## 2. Lo que quedó medido

### 2.1 El fenómeno del cúmulo lejano

| qué se midió | valor | ronda |
|---|---|---|
| el sitio donde publicamos, contra otro punto de la misma banda, en una imagen de MIROVA que no lo eligió | **+0,0514** [+0,0264, +0,0766] | 7 |
| de eso, la parte que aparece igual en imágenes de **otras noches** | **+0,0441** (el 86 %) | 7 |
| lo que queda para **esa noche** | **+0,0073** [-0,0241, +0,0385] | 7 |
| el mismo sitio esta noche contra el mismo sitio otras noches (eje 2 literal) | **+0,0132** [-0,0089, +0,0343], sobre una base de 0,0705 | 7 |
| cuánto del efecto lo pone el máximo sobre el disco y no la celda exacta | **tres cuartos** | 7 |

**Lectura física.** El lugar donde `keep_peak` conserva su píxel **sí destaca** en el campo de
radiancia de MIROVA: no es ruido. Pero destaca **todas las noches**, no la noche de la detección. Y el
efecto se apoya en el máximo sobre el entorno, no en la celda: es la firma de un terreno con más
textura, no la de un foco puntual. Es el borde de cota baja del disco del Test 1 que describe A69,
tibio por altitud y por tipo de superficie, y que también está tibio en la imagen de MIROVA porque es
relieve, no lava.

**Lo que esto no dice**: no separa relieve tibio de fuente volcánica permanente (lago de lava, campo
fumarólico, lacolito). Esa separación con radiancia sola es la que A83 declara agotada; pedirla exige
otro dato, típicamente SWIR de alta resolución (A77).

### 2.2 Dónde ocurre la coincidencia que sostuvo las 5 noches

| qué se midió | valor | ronda |
|---|---|---|
| pasadas donde el radio de nuestro cúmulo es compatible con el `Distancia_km` de MIROVA, en Lastarria | **12 de 15** | 2 y 3 |
| lo mismo, fuera de Lastarria | **1 de 19**, y ahí el cúmulo está a 0,15 km del cráter (no es el caso) | 2 |
| pasadas de M1 que sobreviven a todos los filtros | **12, todas de Lastarria** | 6 y 7 |

Fuera de Lastarria, las pasadas que parecían compatibles lo son por **aritmética del centro de grilla**:
en Cordón Caulle `mirova_center` está a 7,57 km del cráter, en Tupungatito a 4,86 y en Planchón-Peteroa
a 2,02, así que cualquier punto cercano al cráter "coincide" con el radio publicado. La compatibilidad
de radio sólo informa donde el centro de grilla está casi sobre el cráter.

**Conclusión del eje dirección**: la coincidencia de radio que sostuvo las pérdidas del A/B S143 es hoy
**un fenómeno de Lastarria**, el volcán que tiene un foco real desplazado del cráter (el campo
fumarólico Lazufre). No es un fenómeno general de los nevados de señal débil, que era la premisa con
que se abrió el frente.

### 2.3 Las 5 noches, revisadas

- **Son 4, no 5**: Láscar 2026-06-13 no tiene un cúmulo lejano (está a 0,32 km del cráter y a 0,49 km
  del `final_hotspot`), así que nunca fue un caso de D19 (ronda 3, reproducido por la 5).
- **La coincidencia fue entre pasadas distintas**: MIROVA alertó en una pasada y el cúmulo que coincidió
  es de otra pasada de la misma noche, de 18 a 78 minutos antes o después. En la pasada con alerta
  nuestro cúmulo estaba sobre el `final_hotspot` en las 5 noches (ronda 3).
- **3 de las 4 restantes son de Lastarria**; la cuarta (Isluga 2026-06-16) no tiene TIF en sus pasadas
  con alerta (ronda 1, confirmado por la 2).

## 3. Lo que aprendimos del instrumento (y que sirve para otros frentes)

| hallazgo | valor | ronda |
|---|---|---|
| medir sobre el TIF de **la misma pasada** infla el resultado, porque nuestro detector eligió ese píxel en ese gránulo y MIROVA hizo la imagen del mismo gránulo | imagen propia **+0,1214** contra cruzada **+0,0786** con el estadístico final; **+0,1091 contra +0,0145** con el anterior | 5 y 7 |
| un control que compara el punto con su **reflejo** a través del cráter mide textura del flanco, no calor | nulo **+0,1014** [+0,018, +0,197] sin nada que detectar | 3 |
| un control que compara el mismo punto en **otras noches** es ciego a los focos permanentes, que son la categoría b que A54 pide no destruir | por construcción; medido, el 97,1 % de nuestros P tiene otro P a menos de 0,75 km en otra noche | 4 |
| un control de **intercambio de roles** atenúa el sesgo exactamente cinco veces: habría certificado como limpio el instrumento ya refutado | `C1 = −sesgo/5` | 5 |
| el **estrato hermano** (mismo objeto, otra etiqueta de MIROVA) no es un nivel de instrumento: contiene la señal | +0,0120 = **-0,0355 de suelo + 0,0476 de sitio** | 6 |
| la grilla UTM de MIROVA duró **1,5 días** (8 adquisiciones, 14 y 15 de septiembre); el resto es EPSG:4326 | A106 corregida | S144, conteo |

## 4. Qué NO hay que rehacer (anti-A8)

- **No volver a proponer el control reflejado** (mide textura), **ni el control temporal solo** (ciego a
  permanentes), **ni el intercambio de roles** (atenúa por construcción), **ni usar el estrato hermano
  como nivel** (contiene la señal). Los cuatro están refutados con medición, no con opinión.
- **No medir sobre el TIF de la propia pasada**: infla por selección. Si hace falta medir sobre el campo
  de MIROVA, usar otra pasada de la misma noche, con separación de 45 a 120 minutos.
- **No reabrir "la compatibilidad de radio" fuera de Lastarria**: donde el centro de grilla está lejos
  del cráter, esa compatibilidad es aritmética.
- **No esperar que el TIF separe relieve de fuente**: no lo hace ningún diseño de esta serie.

## 5. Qué queda abierto, y qué decisión habilita

1. **`keep_peak` sigue encendido.** Lo que publica no es ruido, pero tampoco es un evento de esa noche:
   es un sitio tibio estable. Eso **no autoriza por sí solo a apagarlo**, porque no distingue relieve de
   fuente permanente, y apagar por error destruiría categoría b (A54, A83).
2. **La regla de cota de S143 sí puede reabrirse con dirección**, y ahora se sabe con qué alcance: sólo
   en volcanes donde `mirova_center` está casi sobre el cráter, y hoy el caso es Lastarria. Un
   pre-registro nuevo tendría que decir qué hace con un volcán que además tiene un foco real desplazado.
3. **El frente natural que queda es de etiquetado, no de detección**: si lo que se publica lejos del
   cráter es un rasgo estable del terreno, la pregunta operacional es cómo se muestra en el dashboard,
   con el marco de A72 (artefacto contra señal real sub-umbral) y sabiendo que este frente no cerró esa
   clasificación.
4. **Para separar relieve de fuente** haría falta otro instrumento: SWIR de alta resolución (A77,
   Landsat-v1 o NHI-v1), que es un proyecto distinto.

## 6. Materiales

- Pre-registro final y sus siete informes de verificación:
  `docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md` y `..._VERIFICADOR{,_V2,...,_V7}.md`.
- Conteo versionado de la muestra: `experiments/_s144_conteo_tif/` (`RESULTADO.md` lo genera el script).
- Records del brazo control del A/B S143, congelados antes de que vencieran en GitHub:
  `experiments/_s144_keep_peak_direccion/control_s143/` con `MANIFIESTO.json`.
- Scripts de los verificadores: `experiments/_s144_keep_peak_direccion/verificadores/`.
