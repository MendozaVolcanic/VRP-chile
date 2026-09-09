# El paper se contradice consigo mismo en los Tests 2 y 3, y nosotros implementamos la fórmula

> Hallazgo de S136, verificado en el **PDF original** (no en el texto extraído, que corrompe los
> símbolos). Explica la sobre-detección de los tres casos negativos del Apéndice A, y es el
> primer candidato del proyecto que tiene un criterio de decisión externo listo.

## Lo que dice la fórmula, verbatim del PDF

Página 7 de `documentacion/sp426.5.pdf`, extraída con PyMuPDF línea por línea (el operador `>`
aparece como `.` en el texto plano del repo, así que **ese archivo no sirve para leer conectivas**):

```
un píxel se marca como 'active' cuando:

    dNTI_PIX  >  C1
    or
    dNTI_PIX  >  μ_dNTI + C2·σ_dNTI          (Test 2)
    and
    dETI_PIX  >  C1
    or
    dETI_PIX  >  μ_dETI + C2·σ_dETI          (Test 3)
```

El `or` **es literal**: aparece en su propia línea, dos veces, y el `and` une Test 2 con Test 3.
Nuestra implementación (`pipeline/detection_context.py`, `thr = min(C1, μ + C2·σ)`) es
**matemáticamente equivalente** a ese `or` y por lo tanto fiel a la fórmula. No hay bug de código.

## Lo que dice la prosa del mismo paper, tres líneas más abajo

> *"In the case of very homogeneous scenes (i.e. in the absence of clouds and over homogeneous
> terrain), the parameter C1 implies that **a minimum threshold** (for both dNTI and dETI) **needs
> to be exceeded** in order to flag a pixel as `active'. **However, when highly variable scenes are
> analysed, the detection of clear positive outliers (hotspots) is achieved using statistical
> analysis of the whole scene.**"*

Eso describe el comportamiento **contrario** al de la fórmula:

| | la prosa pide | la fórmula (`or` → `min`) hace |
|---|---|---|
| escena **homogénea** (σ pequeño) | C1 actúa como mínimo a superar | manda `μ+C2σ`, **C1 no actúa** |
| escena **muy variable** (σ grande) | manda el análisis estadístico | manda **C1**, que *relaja* |

La prosa describe `max(C1, μ + C2·σ)`. La fórmula, `min(...)`. **El paper se contradice consigo
mismo**, y nosotros implementamos la mitad que está escrita como ecuación.

## Y la consecuencia medida: el mecanismo adaptativo está inerte

Sobre los records en disco de los 11 Tier A, comparando el piso contra el contraste estadístico
(`scripts` en `experiments/_s136/que_rama_manda.py`):

| sensor | records | el umbral efectivo es el PISO C1 (cumbre) | mediana de μ+5σ | mediana de σ |
|---|---|---|---|---|
| MODIS | 11.907 | **11.907 — 100,0 %** | 0,03485 | 0,00697 |
| VIIRS 375 m | 21.047 | 21.023 — 99,9 % | 0,00695 | 0,00137 |
| VIIRS 750 m | 23.312 | 23.277 — 99,8 % | 0,00822 | 0,00164 |

**En la práctica el contraste con la escena nunca decide nada.** La detección la gobierna un número
fijo. Y la escala lo empeora: en MODIS el piso de 0,003 queda a **menos de 1σ** del fondo, cuando
la rama estadística de la Tabla 1 pide 5σ en la cumbre y 10σ en la escena. O sea el umbral efectivo
es unas cinco veces más laxo de lo que esa tabla pretende.

## Tres líneas de evidencia convergentes de que MIROVA implementa la prosa

1. **Los tres casos negativos del Apéndice A.** Con la fórmula literal detectamos en Dubbi,
   Tolbachik y Stromboli, donde el autor publica que su algoritmo **no** detecta. Y en las siete
   pasadas el disparo viene del primer pase contextual, con los umbrales de la Tabla 1 puestos.
   Con `min`, una escena caótica (nubes dispersas en Stromboli) *baja* el umbral efectivo al piso;
   con `max`, lo sube. El patrón de fallo coincide exactamente con el signo equivocado.
2. **El propio paper describe a MIROVA como de umbrales autoadaptativos**, «independientes de las
   condiciones locales». Con `min` no se autoadaptan: los fija C1 en el 100 % de los casos.
3. **La economía del texto.** El paper dedica media página a explicar el análisis estadístico de la
   escena, define μ y σ «de todos los píxeles adecuados de la imagen» y tabula C2 por ROI y por
   día/noche. Sería absurdo hacer todo eso para un término que nunca decide.

## Qué NO se puede afirmar todavía

- Que MIROVA use `max`. No hay cita que lo diga: hay una fórmula que dice `or` y una prosa que
  describe `max`. Lo que sí está probado es que **las dos lecturas no pueden ser ciertas a la vez**.
- Que `max` cure los tres negativos sin romper los seis positivos. **Eso es exactamente lo que hay
  que medir**, y por primera vez el criterio existe y es externo.
- Nada sobre magnitud: esto es un umbral de detección.

## El experimento, que ya tiene su patrón de medida

Cambiar `min` por `max` es **una línea** en `pipeline/detection_context.py`. Toca el pipeline, así
que requiere tag defensivo y confirmación explícita (A45), detrás de un flag con el comportamiento
actual por defecto.

Y el criterio de decisión ya está construido y no hay que inventarlo: **la batería del Apéndice A**.
Un brazo con `max` es conforme si y sólo si mantiene los **6 positivos** y cura los **3 negativos**.
Los positivos incluyen Ubinas (NTI ≈ −0,91) y Villarrica (≈ −0,93), anomalías reales muy débiles
detectadas por filtrado espacial: son el freno duro contra pasarse de estricto, que es la tensión
que bloqueó los cinco brazos del A/B de S135.

Después, y sólo si pasa esa puerta, corresponde el A/B sobre los volcanes chilenos con paridad de
magnitud y falsos negativos por volcán, como manda el pre-registro de siempre.

## Nota sobre MISSION

La puerta 1 pregunta si está documentado en papers core. Acá **las dos lecturas tienen cita del
mismo paper**, así que la puerta no discrimina sola: se resuelve con la batería, que es evidencia
del propio autor. Y la regla de verificación verbatim de MISSION queda reforzada con un caso nuevo:
**el texto extraído del repo corrompe los operadores matemáticos** (`>` aparece como `.`), así que
cualquier afirmación sobre una fórmula o una conectiva debe verificarse contra el PDF.
