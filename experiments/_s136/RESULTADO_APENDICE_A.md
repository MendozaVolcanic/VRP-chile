# La batería del Apéndice A: 6 de 6 en los positivos, 3 de 3 en los negativos

> Run 34284386094, success. Criterio pre-registrado, extendido a los negativos (en un caso
> negativo, publicar es el fallo). Coordenadas del catálogo Smithsonian, verificadas por altitud.
> Geometría uniforme, ROI1 de 5 km del paper.

## El resultado

| caso | volcán | fecha | el paper | nosotros |
|---|---|---|---|---|
| A1 | Bezymianny | 2012-01-08 | detecta | **CONFORME** |
| A2 | Eyjafjallajökull | 2010-04-07 | detecta | **CONFORME** |
| A3 | Erta Ale | 2009-08-16 | detecta | **CONFORME** |
| **A4** | **Dubbi** | 2013-07-03 | **NO detecta** | **falso positivo** |
| A5 | Ubinas | 2008-04-03 | detecta | **CONFORME** |
| A6 | Villarrica | 2009-06-24 | detecta | **CONFORME** |
| **A7** | **Tolbachik** | 2012-11-20 | **NO detecta** | **falso positivo** |
| A8 | Etna | 2010-02-08 | detecta | **CONFORME** |
| **A9** | **Stromboli** | 2010-01-19 | **NO detecta** | **falso positivo** |

**Cero falsos negativos en seis positivos. Tres falsos positivos en tres negativos.** Ningún caso
quedó indeterminado: los tres con NTI publicado (A5, A6, A8) pasaron el control de validez.

El patrón no podría ser más limpio: **la sensibilidad está bien o de más; el problema es la
precisión.** Y por primera vez está medido contra la referencia del autor del algoritmo, no contra
el consolidado de MIROVA — que era la limitación de fondo del frente del artefacto.

## Qué dispara en los tres negativos

| caso | pasada | VRP cúmulo | n px | dist. | `nti_max` | fondo | 1er pase | umbral fijo | Test 1 |
|---|---|---|---|---|---|---|---|---|---|
| A4 Dubbi | 19:30 | 1,548 | 6 | 2,16 km | −0,839 | 301 K | 6 | 0 | no |
| A4 Dubbi | 22:15 | 0,459 | 5 | 1,19 km | −0,867 | 271 K | 35 | 0 | no |
| A7 Tolbachik | 10:40 | **5,000** | 28 | 1,34 km | −0,943 | 247 K | 166 | 0 | no |
| A7 Tolbachik | 14:45 | **5,000** | 23 | 5,41 km | −0,934 | 250 K | 134 | 0 | no |
| A9 Stromboli | 01:15 | **22,147** | 15 | 0,63 km | −0,892 | 279 K | 75 | 0 | no |
| A9 Stromboli | 21:45 | 0,714 | 1 | 1,13 km | −0,900 | 284 K | 4 | 0 | no |
| A9 Stromboli | 20:05 | 0,476 | 2 | 3,16 km | −0,898 | 284 K | 2 | 0 | no |

**En las siete pasadas: el umbral fijo del paper da cero píxeles y el Test 1 integrado no dispara.
Lo que dispara es el primer pase contextual**, con 2 a 166 píxeles. La sobre-detección es del
camino contextual, y de nadie más.

## Y los umbrales contextuales son los del paper

Verificado leyendo `pipeline.profile`, no el YAML: `C1 = 0,003` cumbre / `0,010` escena,
`C2 = 5` cumbre / `10` escena de noche, `N·σ = 5 / 10`, filtros de píxeles inadecuados
(§267-273) **encendidos**, `MAX_SIGMA_COMPONENT_K` neutralizado en 999.

**Así que la sobre-detección no viene de umbrales laxos.** Eso descarta la explicación más obvia y
deja el frente donde importa: la diferencia con MIROVA está en algo distinto de los números de la
Tabla 1 — el pool de píxeles sobre el que se calculan μ y σ, la geometría del ROI, el segundo pase
que corre sin la condición del paper, o la rama del piso absoluto `C1` de los Tests 2 y 3, que
dispara con `dNTI > 0,003` sin mirar la variabilidad de la escena.

## Dos observaciones finas

**El «5,000 exacto» de Tolbachik no es coincidencia: es nuestro propio cap actuando.**
`PATH_D_ONLY_CAP_MW = 5.0`, el tope que el proyecto adoptó para el camino contextual en escenas
sospechosas de nube alta (D9). O sea: el pipeline **reconoció la condición** y eligió **atenuar la
magnitud en vez de descartar la detección**. MIROVA, en esa misma escena, descarta. Es un ejemplo
nítido de la diferencia entre parchear el síntoma y no generar el dato — exactamente lo que la
regla A72 pide distinguir.

**Los tres negativos fallan en tres contextos térmicos distintos**: mar templado alrededor de una
isla fría (Stromboli, fondo 279-284 K), desierto caliente (Dubbi, 301 K) y nieve (Tolbachik,
247 K). No es un solo mecanismo físico, así que difícilmente lo cure un solo umbral. En Stromboli
hay además un límite de resolución honesto: 15 píxeles de MODIS son ~15 km² y la isla mide unos
2 km, de modo que el cúmulo incluye mar por fuerza.

## Límites, declarados

- **Es MODIS.** No dice nada de VIIRS 375 m ni de la banda M.
- Nuestro criterio es «publica cúmulo con VRP > 0 dentro del ROI1»; el del paper es su *alert
  mask*. Si MIROVA aplicara un descarte posterior que el paper no describe en el apéndice, parte
  de estos falsos positivos serían de reporte y no de detección.
- Una fecha por caso.
- Tolbachik es el negativo más débil: su erupción empezó siete días después, así que prueba que no
  inventamos señal sobre un volcán en reposo, no la sensibilidad. **Stromboli es el negativo
  fuerte** — volcán en actividad permanente, nubes dispersas, y el autor no detecta.

## Qué abre

Un patrón de referencia externo para el frente del artefacto. Hasta hoy la sobre-detección sólo se
podía medir contra el consolidado de MIROVA, con el problema de que su silencio puede ser scope
operacional y no ausencia de señal (A54). Estos tres casos son distintos: **el autor publicó que su
algoritmo no detecta ahí**. Eso permite ajustar el contextual sabiendo qué se rompe del otro lado,
que es justo lo que faltaba — con los seis positivos, y en particular Ubinas y Villarrica (anomalías
reales de NTI ≈ −0,91 y −0,93), como red de seguridad contra pasarse de estricto.
