# Qué dice la literatura de MIROVA sobre por qué calla donde la réplica publica (S147)

> **Encargo**: agente con contexto limpio, preámbulo anti-fabricación entero y la regla de leer
> los PDF renderizando la página a imagen (A95). Recibió la descripción medida del residual (un
> píxel, bajo 0,05 MW, a unos 3 km del cráter, en el borde del barrido y sobre fondo frío) y la
> pregunta de qué hace MIROVA que la vuelve inmune ahí. Leyó primero
> `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md` para no rehacerlo. Barrió los 79 PDF de
> `documentacion/`. **Aporta cuatro fuentes del grupo MIROVA que el frente F no había abierto.**

## Hallazgos, por relevancia

### H-1 (5). El antecesor directo del algoritmo une el criterio absoluto y el estadístico con AND
Coppola, Laiolo, Delle Donne, Ripepe, Cigolini (2014), *Int. J. Remote Sensing* 35(9):3403-3426,
**página impresa 3409**, ecuación "(test 2)", vista en imagen:

> `Alert2 = (NTI_ROI3 > NTI_Max2) and [NTI_ROI3 > (NTI_Mean2 + 3 × NTI_std2)]`

y al cierre del apartado: *"...all the pixels passing test 1 (Alert 1) **or** test 2 (Alert 2)"*.

En 2014 la estructura es inequívoca: **el OR va entre tests distintos, y dentro de un test el
criterio de nivel y el estadístico van con AND**, o sea manda el más estricto. `NTI_Max2` cumple
ahí el papel que en 2016 pasa a cumplir `C1`: un piso que hay que superar sí o sí. Es la lectura
que la prosa de 2016 sugiere y que su fórmula impresa contradice. CONFIRMADO el texto; SOSPECHA
la continuidad, porque nadie dice que 2016 quisiera conservar el AND.

Contraste, también visto en imagen: `sp426.5.pdf` página índice 6 imprime
`dNTI > C1 or dNTI > μ + C2σ (Test 2) and dETI > C1 or dETI > μ + C2σ (Test 3)`. **El código
reproduce literalmente la fórmula impresa de 2016. La ambigüedad es del paper, no nuestra.**

### H-2 (5). El remuestreo es el paso (ii) de la cadena NRT y su función declarada es corregir el borde del barrido
- Coppola et al. 2023, *Front. Earth Sci.* 11:1240107, **p. 3**, §2.1 (imagen): *"resampled to
  regular 51 × 51 UTM grids... This step is crucial to ensure that all pixels represent a ground
  area of 1 km², minimizing the effect of geometrical distortions... Once the scenes are
  geometrically corrected (i.e., pixels affected by bow-tie distortions are identified and
  removed), the MIR and TIR bands are employed to run the hotspot detection algorithm."*
- Aveni et al. 2023, *Remote Sens.* 15:2528, **p. 16** (imagen): el cenital alto integra la
  radiancia de un foco sub-píxel sobre un área creciente, y *"this is partially corrected during
  the resampling step"*. **p. 8** (imagen): *"duplicate pixels might lead to overestimation of the
  thermal anomalies"*.
- Campus et al. 2022, *Sensors* 22:1713, **p. 7**, §3.1: los cuatro pasos de la cadena NRT, con
  el remuestreo como segundo.
- Coppola et al. 2014, **p. 3406** (imagen): el remuestreo existe por el crecimiento del píxel
  (hasta ~10 km² a 55° de barrido) y el mecanismo es **repartir, no promediar**: *"one hot-spot
  pixel, whose area is 2 km²... becomes two pixels with equal areas of 1 km²"*.

La réplica tiene `ENABLE_UTM_REGRID = False`. **Salvedad del propio agente**: ninguna fuente de
MIROVA dice el método (SIN LOCALIZAR), y el indicio de 2014 es duplicación, que **no baja el ruido
por promedio**. Y la cara "duplicados" del problema ya está cubierta en VIIRS: el L1B trae la
marca `Bowtie_Deleted` y `pipeline/process_viirs.py:83` la descarta.

> **Nota del orquestador**: el informe de TIF de esta misma sesión
> (`INFORME_TIF_QUE_VE_MIROVA.md`) midió que la imagen remuestreada de MIROVA y la nuestra
> **coinciden en 0,17 K de mediana** en los píxeles del residual, y que su remuestreo conserva
> picos de una sola celda. O sea que el remuestreo existe, pero **no es lo que apaga el residual**.

### H-3 (5). El ROI de umbrales permisivos de MIROVA es una caja de 5 × 5 km, y el paper dice para qué
Coppola et al. 2023, **p. 3**, §2.1 (imagen): *"in the summit area (5 × 5 km) slightly lower
thresholds are applied... At greater distances, the algorithm uses slightly higher thresholds
**which reduce false alerts**"*.

La réplica: `ENABLE_ROI1_BOX_PAPER = False`, así que rige el círculo por volcán (3 a 20 km). El
círculo de 5 km cubre 3,1 veces la caja, el de 7 km 6,2 veces, el de 20 km 50 veces. En esa
corona se aplica C1 = 0,003 y C2 = 5 donde MIROVA aplicaría 0,01 y 10. Es **D18, ya catalogada**;
lo nuevo es la fuente de 2023 y que **nombra la finalidad**.

### H-4 (4). La nube en MIROVA nunca se enmascara: se excluye de los conjuntos de referencia
- Coppola 2014, **p. 3409** (imagen): los píxeles de referencia de los que salen la media y el
  desvío se eligen con un corte por abajo, y *"exclusively includes the pixels... not contaminated
  by hot-spots or clouds"*.
- Coppola 2012, *JVGR* 215-216:48-60, **p. 51**, §3.4 (imagen): el fondo de la magnitud es la media
  de los 8 vecinos *"which are not contaminated by clouds"*, con nube definida como
  **BT12 < 265 K**. Es la **única cifra de nube explícita** de toda la línea MIROVA, y aplica al
  fondo de la magnitud, no al detector.
- 2016 (texto extraído, la desigualdad no se verificó en imagen): *"the presence of clouds is not
  taken into account by the algorithm"*; los no aptos son los píxeles de borde y los de dNTI o
  dETI bajo −0,1.

La réplica no tiene ninguna exclusión por temperatura del pozo estadístico. Un campo frío y plano
da dNTI cercano a cero, pasa el filtro de no aptos y entra al cálculo del sigma. **La lección no
es volver a prender la máscara de escena**: el lugar donde MIROVA trata la nube es el pozo.

### H-5 (4). Un tercero que reimplementó MIROVA sobre VIIRS 375 subió C1 veinticinco veces
HotLINK (Saunders-Shultz et al. 2024, *Front. Earth Sci.* 12:1345104). **No es MIROVA**, es USGS
AVO. Su Ec. 5 (imagen) lee la conectiva igual que nuestro código (OR adentro, AND entre tests), y
su búsqueda de parámetros dio **C1 nocturno = 0,075 contra el 0,003 de MIROVA**, mientras C2 casi
no se movió (5 a 5,25). Remuestrean con vecino más cercano a resolución nadir. O sea: lo que hay
que recalibrar al cambiar de resolución es el **piso absoluto**, no el multiplicador del sigma,
que es la forma del hallazgo F-02 del frente F (C1 = 0,003 vale 0,43 σ en MODIS y 2,20 σ en
VIIRS 375) medida por otra gente con otro método. Los valores numéricos vienen de texto extraído.

### H-6 (3). Pisos de VRP por sensor, Coppola 2026 Tabla 1 (imagen)
Umbral nocturno: MODIS 0,1 MW, VIIRS 750 **5 MW**, VIIRS 375 **0,01 MW**. El de 375 coincide con
la cuantización que se midió en la referencia. El de 750 borra todo, incluidas coincidencias
reales: o hay errata o no rige en el NRT. **Es del archivo OSF (A105), no del NRT**: SOSPECHA.

### H-7 (3). La intención de diseño declarada en 2016 favorece el AND
`sp426.5.pdf` página índice 6 (imagen): C1 *"implies that a minimum threshold... needs to be
exceeded"*, y en escenas muy variables la detección *"is achieved using statistical analysis of
the whole scene"*. "Needs to be exceeded" es lenguaje de condición necesaria. Bajo OR con C1 fijo
esa adaptación queda anulada justo en la escena variable. CONFIRMADO el texto, SOSPECHA la
inferencia.

### H-8 (3). En datos del propio grupo el VRP cae con el cenital
Aveni 2023, **p. 10** y **Fig. 9, p. 16** (imagen): pares casi simultáneos, 2 a 26 MW con cenital
de 68° contra 278 a 665 MW con 5° a 40°. En MIROVA el cenital alto **atenúa**, no infla. Que la
réplica publique de más ahí apunta a que lo que crece con el ángulo es el **ruido**, no la señal.
El corte de 40° de ese paper es criterio de análisis, **no** filtro del NRT.

### H-9 (2). En 2012 MIROVA restaba un sitio de control por el gradiente topográfico
Coppola 2012, **p. 51**, §3.5 (imagen): su método *"produces a small apparent anomaly... also in
absence of any thermal anomaly"* por un *"important topographic thermal gradient"*. Es la física de
A69 diagnosticada por el propio autor. El paso no sobrevive en 2016: antecedente, no divergencia.

### H-10 (2). El NRT de MIROVA no filtra nube ni geometría; el filtro es el operador
Campus 2022, **p. 8**, §3.4 (imagen): los datos *"must always be evaluated and interpreted by an
end-user"*, y el NRT corre *"where such supervision is not applied"*.

## Verificado limpio: qué se buscó y NO está

1. **Ningún paper posterior a 2016 del grupo re-enuncia los Tests 2 y 3.** `dNTI` y `dETI`
   aparecen sólo en cuatro documentos del corpus: `sp426.5`, HotLINK, Di Bella 2024 (Catania, no
   es MIROVA) y una mención en Coppola 2012. Cero en Campus 2022 y 2024, Coppola 2020, 2023 y
   2026, la tesis de Massimetti, el capítulo Springer, Aveni 2023 y 2024. **La conectiva no se
   resuelve en ningún texto posterior.** Lo más cercano es H-1, que es anterior y dice AND.
2. Ningún texto describe un mínimo de píxeles por detección en el NRT.
3. Ningún texto da el método de remuestreo.
4. Ningún texto de la era VIIRS menciona máscara de nube ni umbral en kelvin.
5. Ningún texto impone un límite de ángulo en el NRT.
6. Ningún texto recalibra C1 o C2 para VIIRS: Campus 2022 p. 7 dice *"the same used for MODIS"*.
7. La fuente que el código alegaba para el Test 1 integrado sigue sin estar en `documentacion/`.
