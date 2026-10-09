# Sonda S150 de los tres campos: diseño (escrito y probado en local, SIN despachar)

> **Estado.** Un verificador con contexto limpio revisó la primera versión
> (`docs/audit_s150/VERIFICADOR_SONDA_TRES_CAMPOS.md`) y concluyó que no se podía sellar: el evaluador podía
> imprimir CONFIRMA aunque el nativo no reprodujera las pérdidas, y la prueba local P6 lo mostraba en verde.
> Esta versión aplica sus «cambios mínimos para sellar» (puntos 1 a 5): gates del instrumento ANTES de H1 y
> D22, sin «salvedades» (§5 y §5 bis), R_L como contraste dentro de la corrida y guarda de brecha (§6),
> control positivo de D22 que frena (§7), sello que cubre también el código medido y el predicado, piloto sin
> veredictos (§10 bis), y las salvedades de los hallazgos que no se corrigen (§9). Un **segundo verificador**
> (`docs/audit_s150/VERIFICADOR2_SONDA_TRES_CAMPOS.md`, sobre `5eda5b942`) confirmó esos cierres y encontró otros
> caminos por los que salía un veredicto no diseñado; esta versión aplica sus cuatro cambios obligatorios (V2-1 a
> V2-4) y los baratos (V2-5 a V2-10), cada uno con su caso en P7b que falla con el código de `5eda5b942`. Un **tercer
> verificador** (`docs/audit_s150/VERIFICADOR3_SONDA_TRES_CAMPOS.md`, sobre `aae4a4ed0`) confirmó las doce y encontró
> cuatro huecos (N1, N2, N3, N5), cerrados aquí con su caso en P7c que falla con `aae4a4ed0`. **Todavía no está
> aprobada**: falta que un verificador revise esta ronda. No se bajó ningún gránulo de NASA ni se
> usaron credenciales. Nada de `pipeline/`, perfiles ni `data/` se tocó. El despacho exige (1) que un
> verificador apruebe este documento, (2) que quien lo aprueba corra
> `python sellar.py --aprobo "<nombre>" --informe <informe del verificador>` para sellar los archivos que
> fijan el criterio y la lista y los que deciden el resultado (§10 bis), (3) el input
> `preregistro_aprobado = si` del workflow `.github/workflows/probe-s150-tres-campos.yml` y (4) correr
> primero el piloto (`piloto = si`, `lotes = 1`). Sin el sello el workflow no corre.

Todos los archivos están en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_sonda_tres_campos\`.

## 0. En una pantalla

**La pregunta.** La conectiva `max` de los Tests 2 y 3 (Coppola 2016a) baja los falsos de VIIRS 375 a
unos 3 %, pero pierde 42 alertas de MIROVA de abril a agosto (32 con etiqueta confiable). La
investigación previa (`docs/S150_ALERTAS_DEBILES_MAX.md`) mostró que esas alertas no alcanzan μ + 5σ, y
que lo que más las separa de las que `max` conserva es la σ de la escena (AUC 0,80 a 0,85, §4), pero que
en todo lo que guarda el record son indistinguibles del residual que `max` apaga con razón (§4). Quedan
dos explicaciones con evidencia, y esta sonda las mide **por separado**:

- **H1, la σ del campo.** Nosotros medimos dNTI, dETI, μ y σ sobre el gránulo nativo; MIROVA, sobre una
  grilla remuestreada de 134 × 134 celdas de 375 m (Aveni et al. 2024, RSE 315, 114388, p. 5, §3.2, citado
  en `docs/MIROVA_DIVERGENCES.md` D17). Si su remuestreo interpola, el ruido de píxel a píxel se suaviza,
  la σ baja y el umbral μ + 5σ también. Pero el pico del foco también se suaviza. ¿Cuál gana?
- **D22 y D26, la compuerta y el pozo del segundo pase.** 15 de las 42 (14 confiables) las publicaba el
  brazo `min` sólo por el segundo pase, porque la compuerta de 3 K (D22, que el paper no tiene) las bloquea
  en el primero. El verificador del A/B de D22 (`docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md`, H1)
  mostró que un A/B con reproceso no aísla la compuerta: en esas pasadas quitarla sólo cambia el umbral
  del primer pase (μ₁ + 5σ₁, pozo con filtros de no aptos) por el del segundo (μ₂ + 5σ₂, pozo SIN esos
  filtros, D26). Esta sonda calcula offline las cuatro combinaciones y separa las dos divergencias.

**El instrumento.** Por cada pasada se baja el gránulo exacto y se corre `process_viirs.calculate_vrp`
REAL sobre cinco sustratos (§3), con `max` y con `min`, y (en todos) `max` sin compuerta. Cada record pasa
por el `store.append_record` real y el predicado del tablero ejecutado con node (A97) decide si se publica.
De la corrida `max` de cada campo se capturan, por monkeypatch de solo lectura (A75), las entradas reales de
`first_pass_tests_2_and_3` y los argumentos de `second_pass_adjacent`, y se recalcula por píxel con las
mismas funciones del pipeline, comprobando identidad contra ellas (§6).

**Qué se corre.** 365 pasadas de VIIRS 375 en 35 lotes de hasta 12 (`pasadas.json`), 15 corridas de
`calculate_vrp` por pasada (3 sobre el gránulo entero, 12 sobre grillas de 134 × 134). Con GeoTIFF de MIROVA
usable para validar el campo: 135 pasadas (10 de las 42 pérdidas).

## 1. Por qué (el fenómeno)

De noche, un foco débil sube apenas la radiancia MIR de un píxel sobre la de sus ocho vecinos. El Test 2 mide
ese exceso en NTI (dNTI) y el Test 3 en ETI (dETI). Con `min` basta superar un piso fijo C1 = 0,003; con
`max` además hay que superar μ + 5σ, donde σ es la variabilidad del dNTI en **toda la escena**. Esa σ no es una
propiedad del volcán: es una propiedad del **sustrato** sobre el que se mide. En el gránulo nativo cada píxel
es una medición independiente, con el ruido del detector, el estiramiento del borde del barrido y el bow tie.
En una grilla interpolada cada celda es un promedio ponderado de varias mediciones vecinas: el ruido de celda
a celda se suaviza y la σ baja. Pero un foco de un solo píxel también se reparte entre celdas, y su exceso
baja. Si MIROVA mide σ en una grilla interpolada, las alertas débiles que publica pueden pasar su μ + 5σ y no
el nuestro. Si además el residual que `max` apaga no pasa en esa grilla, el arreglo es el campo, no la
conectiva ni C2. Eso es lo que esta sonda decide (H1).

Dos indicios ya medidos, ninguno decisivo:
- En MODIS, el remuestreo al **vecino más cercano** subió la σ 13 a 15 % (`experiments/_s137/RESULTADO_SIGMA_DNTI.md`,
  citado en S150 §6). Vecino no interpola: no es el campo de MIROVA si MIROVA interpola.
- La textura de los GeoTIFF de MIROVA tiene autocorrelación positiva a una celda en el contraste dL
  (mediana +0,25 en EPSG:4326 y +0,36 en UTM, 171 TIF nocturnos del 12 al 17 de septiembre,
  `textura_utm_vs_geo_salida.txt`). Un campo de píxeles independientes pasado por el kernel de 8 vecinos da
  autocorrelación negativa; positiva indica un campo suavizado. Es consistente con interpolación, no la prueba.
  El mismo script muestra que el TIF geográfico **no** es más suave que el UTM (σ relativa mediana 0,029 contra
  0,032; no pareado, n UTM = 31): no hay señal de una interpolación extra al exportar a EPSG:4326.

## 2. Qué pasadas entran (lista congelada)

`seleccionar_pasadas.py` (salida en `seleccionar_pasadas_salida.txt`) reconstruye la tabla por pasada con el
**mismo instrumento** de S150 (`experiments/_s149_prereg_invierno/armar_tabla.py`, predicado con node, referencias
congeladas de `_s149_prereg_invierno/_congelado/<mes>/`) sobre las mismas salidas del A/B, leídas con
`git archive` de las ramas `origin/s146-ab/<run>` (sin fetch, sin checkout). Controles de reproducción, todos
cumplidos (si uno falla el script no escribe la lista):

| control | esperado | obtenido |
|---|---|---|
| alertas de VIIRS 375 que B publica / F conserva | 988 / 946 (S150 §1) | 988 / 946 |
| pérdidas de VIIRS 375 / con etiqueta confiable | 42 / 32 (S150 §0) | 42 / 32, mismas 42 claves que `filas.json` |
| pérdidas por el camino D22 / confiables | 15 / 14 (S150 §3; verificador D22 H1) | 15 / 14 |
| negativos del residual por el camino D22 / criterio amplio | 271 / 576 (verificador D22 H4) | 271 / 576 |
| noches de pérdidas D22 confiables sin otra publicación de F | 4 (verificador D22 H5) | 4: Tupungatito 04-22, Planchón 04-10 y 08-24, Chaitén 08-18 |

Definiciones (todas de VIIRS 375, abril a agosto de 2026, agosto hasta el 27; B = perfil `_s146_ab_sin_test1`,
`min`; F = `_s147_ab_sin_test1_max`, `max`):

| grupo | definición | en la ventana | en la sonda | rol |
|---|---|---|---|---|
| `perdida` | alerta de MIROVA, B publica, F no | 42 | 42 (todas) | lo que se quiere recuperar |
| `conservada_debil` | alerta < 0,10 MW, B y F publican | 208 | 84 | control positivo: el campo no debe matarlas |
| `residual_apagado` | negativo limpio, B publica, F no | 766 | 84 | control negativo: lo que `max` apaga con razón |
| `residual_sobrevive` | negativo limpio, B y F publican | 63 | 42 | falsos que `max` deja pasar |
| `negativo_b_no_publica` | negativo limpio, ni B ni F publican | 1.495 | 42 | que el campo no invente donde nadie veía |
| `muestra_negativos_d22` | muestra **uniforme** de los 271 negativos del camino D22 | 271 | 80 (71 nuevas + 9 que ya estaban) | selectividad de D22 y D26 dentro del estrato |

- Los controles de los cuatro primeros grupos se sortean con semilla 150 **del mismo volcán y mes** que cada
  pérdida (2, 2, 1 y 1 por pérdida), bajando a «mismo volcán» o «cualquiera» sólo si no alcanza (conteos por
  nivel en la salida). La muestra D22 es uniforme sobre los 271, semilla 172, y la lista completa de los 271 y
  de los 576 queda congelada en `negativos_camino_d22.json` (pedido del verificador D22, H4 b).
- Etiqueta confiable (A119): no es una de las 5 filas OCR con imagen de otra pasada (S150 §2) y, si es sólo
  OCR, es del 2026-06-13 o después. Las 10 no confiables se procesan y se informan aparte; no deciden.
- **VIIRS 750 queda fuera** (4 pérdidas): va por `process_viirs_mod.py` con otras bandas y otra grilla
  (67 × 67, D17). Con 4 casos no se decidiría nada y duplicaría el código de la sonda.
- **TIF de MIROVA usable** (mismo volcán, `acquisition_utc` a ±180 s de la pasada, md5 no reusado en otra hora,
  A106; índice del archivo fijado en el commit `3660cdfa77bdb177ce7de7f2743a1161f0736ef7`, último que toca
  `index.csv`, bajado con `gh api`): **135 de 365 pasadas**. Por grupo: pérdidas 10 (las 10 confiables; 5 del
  camino D22: Chaitén 05-19 05:06 y 06:48, Isluga 05-25, Tupungatito 05-24 y 08-21), conservadas 36, residual
  apagado 29, sobrevive 17, B no publica 15 (por grupo primario), muestra D22 31 (por pertenencia; 28 por grupo
  primario). Abril no tiene ningún TIF (el archivo empieza el
  2026-05-09).

## 3. Los cinco campos

Todos corren el `calculate_vrp` real; lo único que cambia es el sustrato, reasignando nombres en el namespace
de `pipeline.process_viirs` (A89) y restaurándolos al terminar cada corrida.

| campo | qué es | centro y radio de la escena |
|---|---|---|
| `nativo` | el gránulo tal cual (operacional) | `lat/lon` del catálogo, `radius_km` (25 km): igual que producción |
| `utm_nn` | la grilla UTM de vecino que ya existe (`ENABLE_UTM_REGRID`, `pipeline/regrid.py`, `process_viirs.py:489-545`), 134 × 134 de 375 m | igual que producción (D17: centrada en el catálogo, no en el marco de MIROVA) |
| `tif_nn` | el gránulo llevado por **vecino** a la grilla exacta del GeoTIFF de MIROVA | centro = `get_grid_center` (marco de MIROVA, `geo_utils.py:29`), radio 26 km para cubrir toda su imagen |
| `tif_lin` | ídem, interpolación **lineal** (Delaunay) | ídem |
| `tif_cub` | ídem, **cúbica** (Clough Tocher) | ídem |

- **La grilla de MIROVA es fija por volcán.** `plantillas_tif.py` leyó la cabecera de los 3.541 TIF de VIIRS 375
  que hay en disco (`experiments/_s144_conteo_tif/_dl_tif/`): cada volcán tiene **una sola** grilla EPSG:4326 de
  134 × 134 (Chaitén 362 TIF, Copahue 328, etc.; `plantillas_tif_salida.txt`), y aparte 1 a 4 TIF UTM de las
  fechas de A106, que no entran. Eso permite construir los campos `tif_*` para todas las pasadas, también las de
  abril; el TIF de la pasada sólo se usa para validar. La sonda comprueba en cada TIF que su grilla sea la de la
  plantilla (`sonda.leer_tif`); si no, no lo usa.
- **Se interpola radiancia, no temperatura de brillo**, porque es lo que publica el TIF (valores de unos
  0,05 W m⁻² sr⁻¹ µm⁻¹ en I04, que con Planck a 3,74 µm corresponden a unos 255 K). `campos.hacer_regrid_tif`
  tiene la misma firma y el mismo esquema de salida que `_regrid_viirs_granule`, interpola I04 e I05 en radiancia
  y devuelve temperatura de brillo con la inversa exacta de Planck (mismas constantes que `bt_to_spectral_radiance`;
  la ida y vuelta es exacta, P1 de la prueba local).
- **Qué interpolador usa MIROVA no está escrito en ningún paper leído.** Los TIF dicen
  `TIFFTAG_SOFTWARE = MATLAB R2024b, Mapping Toolbox 24.2` (leído con rasterio en esta sesión). Por eso hay tres
  candidatos y el TIF decide cuál se parece más (§5). Vecino, lineal y cúbico no agotan las opciones (MATLAB tiene
  también vecino natural); si ninguno reproduce el TIF, H1 queda indeterminada por instrumento.

## 4. Qué se calcula y qué se guarda

**Por corrida (15 por pasada).** El record persistido por el `store.append_record` real (con `DATA_DIR` apuntando
a un temporal), resumido a los campos que lee el predicado del tablero más los diagnósticos de μ y σ. El evaluador
corre el predicado con node sobre esos records: esa es la **publicación**, la unidad del operador.

**Por campo, desde la corrida `max` (offline, `campos.evaluar_campo`).** Con las entradas reales del primer pase
(NTI, NTI aparente, BT de I04, ROI, distancia al ancla, t_bg, C1, C2, filtros):
- dNTI, dETI, μ y σ del primer pase, con el pozo de fondo de `build_unsuitable_mask` (`detection_context.py:492-510`).
- Para cada conectiva (`min`, `max`) × compuerta (con, sin) × pozo del segundo pase (el real, sin filtros; o
  «d26», con los mismos filtros de no aptos del primer pase): máscara del primer pase, dNTI₂, dETI₂, μ₂, σ₂ y
  máscara final. Son 8 combinaciones. La variante «d26» no existe en el pipeline; se calcula sólo acá.
- La decisión en la **zona objetivo** (celdas a 0,75 km o menos de lo que B publicó: el centroide de su cúmulo
  primario y sus píxeles de anomalía a 1,5 km o menos de él; sensibilidad a 0,5 y 1,0 km informada, no decide),
  en la **cumbre** (cualquier píxel final dentro de `inner_radius_km` del ancla) y en **50 zonas nulas** sorteadas
  dentro del ROI a más de 3 km del objetivo, con el umbral de cumbre aplicado a toda la escena.
- El margen z del píxel más favorable del objetivo, min((dNTI − μ)/σ, (dETI − μₑ)/σₑ), y la razón al umbral.

**Por píxel** (los del objetivo, y en la cumbre los que pasan C1 en algún test o quedan activos en alguna
combinación; tope 4.000 por campo que **nunca** corta el objetivo ni un píxel de cumbre activo en el primer pase o
final en alguna de las 8 variantes, hallazgo 7: el cupo restante se llena por dNTI decreciente, y se informa cuántos
había y cuántos se guardaron): fila, columna, lat, lon, distancia al ancla, cumbre, objetivo, BT de I04,
**BT − t_bg**, radiancia I04, radiancia I05 (hallazgo 5; derivada del NTI con álgebra exacta,
L5 = L4 · (1 − NTI) / (1 + NTI), porque la captura no trae I05), NTI, dNTI, dETI, si pasa la compuerta, y por cada conectiva × compuerta: dNTI₂, dETI₂,
activo en el primer pase, final con el pozo real y final con el pozo «d26». Con eso y los μ, σ, μ₂, σ₂ guardados
se rehace offline cualquier decisión sin volver a bajar el gránulo (pedido 1 de la ampliación).

**Validación contra el TIF** (`campos.validar_contra_tif`), en las pasadas con TIF usable, para cada campo `tif_*`:
correlación de la radiancia (r_L), diferencia relativa mediana, correlación del contraste de 8 vecinos dL (r_dL),
razón de desviaciones sd(dL campo)/sd(dL TIF) (s_ratio) y autocorrelación a una celda de dL en el campo y en el TIF.
El borde de una celda se excluye. r_L dice si es la misma escena bien georreferenciada; r_dL y s_ratio dicen si la
**textura** que fija σ es la de MIROVA, que es lo que importa para H1.

## 5. Las dos preguntas del instrumento, y los controles

**¿Si estuviera roto, se vería?** Todos los controles de esta lista son **gates**: se evalúan ANTES de H1 y de
D22 y, si uno falla, el veredicto es INDETERMINADO POR INSTRUMENTO (o POR COBERTURA) y no se lee. No existe
«CONFIRMA con salvedad»: un veredicto con salvedad se leería igual, y la primera versión de este evaluador lo
imprimía con un acuerdo del 30 % en `nativo|max` (verificador S150, hallazgo 1). Los números de cada gate y por
qué son esos están en §5 bis.
1. **Identidad con el pipeline, en cada pasada y campo.** μ y σ recalculados contra el diag que devolvió la
   función real (diferencia relativa < 1e-9), mismo tamaño de pozo, la máscara del primer pase recalculada contra
   `first_pass_tests_2_and_3` real con la misma conectiva y compuerta (4 combinaciones), y la réplica del segundo
   pase contra `second_pass_adjacent` real. Además, contra la corrida real **sobre el gránulo entero**
   (hallazgo 6): en `max|con_compuerta` la réplica sobre el recorte tiene que contar los mismos píxeles del primer
   pase que la máscara real (`fp_hot`) y los mismos finales que la llamada real a `second_pass_adjacent`
   (`sp_out_n`); se guarda también lo que entró al segundo pase (`sp_in_n`, tiene que ser `fp_hot`). Un par
   pasada-campo que falle cualquiera de estas se excluye y se cuenta; si fallan más del 5 %, INDETERMINADO POR
   INSTRUMENTO. Las pasadas excluidas cuentan como faltantes para la cobertura.
2. **Cobertura con n mínimo (A108, hallazgo 2).** Cada lote sale en rojo si alguna pasada no completó sus 15
   corridas, pero el evaluador corre igual (`if: always()`), así que la cobertura es un gate del evaluador: pasadas
   usables (completas y con identidad) por grupo, contra las esperadas de `pasadas.json` entero, **no** contra los
   lotes que corrieron. Falla si faltan más de 2 de las 32 pérdidas confiables o si algún grupo queda bajo el 90 % de
   sus pasadas; D22 falla además si faltan más de 1 de sus 14 pérdidas. Cada tasa se informa con su n.
3. **σ del nativo contra el record del A/B, pasada por pasada (hallazgo 1, punto 5).** La σ dNTI del primer pase del
   nativo tiene que ser la del record del brazo F (que en el A/B es idéntica a la de B en las 365: el pozo no depende
   de la conectiva ni de la compuerta) con diferencia relativa < 1e-6, en al menos el 95 % de las pasadas usables. Es
   la prueba directa de que el nativo es el mismo cálculo que el A/B: mismo gránulo, mismo código, mismo entorno.
   Una σ ausente, nula o no finita (NaN) cuenta como **distinta** (V2-10: antes un NaN contaba como idéntica). Se
   calcula también en el piloto (V2-4), junto con la fracción de pasadas que usaron el mismo L1B que el A/B.
   Además, si una pasada aparece más de una vez en la salida (por ejemplo, el piloto y el despacho completo en la
   misma carpeta), es una falla del instrumento: se informan los archivos y no hay veredicto (V2-5).
4. **Reproducción del A/B, POR GRUPO (hallazgo 1, punto 1; extendida a todos los grupos por V2-2).** En cada
   pasada usable, `nativo|max` publica lo que publicó F y `nativo|min` lo que publicó B en su grupo primario: en las
   pérdidas confiables `max` NO y `min` SÍ; en las conservadas los dos SÍ; en el residual apagado y en la muestra D22
   `max` NO y `min` SÍ; en el residual que sobrevive los dos SÍ; en los negativos que B no publica, ninguno. Máximo de
   fallas: 2 pérdidas confiables y el 5 % de cada otro grupo (4 de 84, 2 de 42, 3 de 71). Sin esto, un `nativo|min`
   que publicara los negativos que B no publicó inflaba la brecha y fabricaba CONFIRMA (V2-2). Las pérdidas no
   confiables sólo se informan. Las pérdidas que pasan este control son las **pérdidas
   reproducidas**, el denominador de R_L (§6) y de la recuperación de D22 (§7). El acuerdo agregado sobre las 365 de
   la versión anterior se sigue informando, pero no decide: toleraba unos 18 desacuerdos que podían caer todos en las
   42 pérdidas. Se informa también cuántas pasadas usaron el mismo archivo L1B que el A/B.
5. **Validación del campo contra el TIF de MIROVA** (§4). **Gate de registro por pasada (hallazgo 4 b):** una pasada
   entra a la validación sólo si r_L ≥ 0,90 con `tif_nn`; si no, el TIF no es esa escena o no está registrado, y se
   descarta de la validación de los tres campos (la misma población para los tres) y se cuenta. Si entran menos de la
   mitad de las pasadas con TIF usable esperadas (135), INDETERMINADO POR INSTRUMENTO. Un campo `tif_*` es **válido**
   si la mediana de r_dL es 0,80 o más y la mediana de s_ratio está entre 0,80 y 1,25. Entre los válidos, el **campo
   MIROVA (M)** es el de mayor r_dL (empate: s_ratio más cerca de 1). Se elige mirando sólo el TIF, nunca los
   resultados de H1. Si ningún campo es válido, H1 es INDETERMINADO POR INSTRUMENTO. Los umbrales 0,80 y
   [0,80; 1,25] no salen de un dato medido: son la cota de «misma textura» que se fija antes de ver datos. La validez
   se informa además **por volcán** (hallazgo 4 d), para ver si los cinco que concentran las pérdidas (Tupungatito,
   Chaitén, Puyehue Cordón Caulle, Planchón Peteroa, Lastarria) validan como el resto; informa, no decide.

**¿Puede dar distinto de cero? (A116)**
- **Control positivo de la decisión:** las conservadas débiles publican con `max` en el nativo (por definición en
  el A/B) y las pérdidas publican con `min` (B las publicó). Si el instrumento no las ve publicar, no puede ver una
  recuperación.
- **Control positivo de la validación:** en la prueba local, contra un «TIF» hecho con interpolación lineal
  conocida, la validación da r_dL = 1 y s_ratio = 1 para `tif_lin` y distingue a `tif_nn` (r_dL 0,800) y
  `tif_cub` (0,970), y el evaluador elige `tif_lin` (`prueba_local_salida.txt`, P3 y P5).
- **Control negativo:** el residual apagado y los negativos que B no publica no publican con `max` en el nativo.
  Y las **zonas nulas**: si en M con `max` la fracción media de zonas nulas que pasa supera a la del nativo con
  `min` (el campo conocido como demasiado permisivo), una recuperación en M no es específica y H1 no se confirma.
  Es un control **débil** (hallazgo 11): sólo detecta un campo peor que `min`. Lo que cubre de verdad la
  especificidad es ΔFP (§6).
- **Control del evaluador (A110 d).** Un evaluador sólo se puede creer si se le ve dar cada veredicto cuando
  corresponde y ninguno cuando no. `prueba_local.py` arma poblaciones sintéticas con la **meta real** de
  `pasadas.json` (365 pasadas) y el predicado real del tablero: P6 (clones que publican en todo) tiene que dar
  INDETERMINADO POR INSTRUMENTO, y P7 recorre CONFIRMA, REFUTA por falsos, REFUTA por recall, la zona gris, la
  cobertura del piloto, el borde de cada gate (2 pérdidas faltantes o mal reproducidas pasan, 3 no), la brecha,
  la σ contra el A/B, el control positivo de D22, la identidad de escena y el modo piloto.

## 5 bis. Los números de los gates (elecciones pre-registradas, escritas antes de ver ningún dato de la sonda)

Ningún dato de la sonda existe todavía: no se despachó nada. Los números de esta tabla son **elecciones**, salvo
donde se dice otra cosa, y se fijan ahora para que no se puedan acomodar después.

| gate | valor | de dónde sale |
|---|---|---|
| identidad (μ, σ, máscaras, recorte y gránulo entero) | ≤ 5 % de pares pasada-campo con falla; tolerancia numérica 1e-9 | heredado de la versión anterior; 1e-9 es error de redondeo de doble precisión, no una elección física |
| cobertura de pérdidas confiables | faltan ≤ 2 de 32 | elección: el número que propuso el verificador («menos de 30 de 32»). Con 30 pérdidas el error estándar de R_L en 0,5 sube de 0,088 a 0,091: dos faltantes no cambian la potencia; tres o más empiezan a ser un patrón de fallas que puede no ser al azar |
| cobertura por grupo | ≥ 90 % de las esperadas | elección: el número que propuso el verificador. FP pondera tres estratos; perder más de un décimo de uno cambia su peso sin aviso |
| cobertura de D22 | faltan ≤ 1 de 14, contado sobre las pérdidas D22 **reproducidas** (las que deciden), no sólo las usables | elección: con 14 casos y cota 7, cada caso es 7 puntos de recuperación; uno faltante se tolera, dos ya mueven la cota. V2-6: el gate general tolera 2 pérdidas no reproducidas que podían ser todas D22, y D22 llegaba a decidir sobre 11 |
| σ del nativo contra el record del A/B | diferencia relativa < 1e-6 en ≥ 95 % de las pasadas | dato: B y F, dos corridas distintas del A/B sobre el mismo gránulo, dan la misma σ con diferencia 0,0 en las 365 (medido sobre `pasadas.json`). 1e-6 es una elección: margen sobre el redondeo de float32 si cambia el orden de suma (otra versión de numpy). 95 %: el mismo 5 % que la identidad |
| reproducción en pérdidas confiables | ≤ 2 fallas | elección: el número que propuso el verificador. Las pérdidas son casos de borde (justo debajo de μ + 5σ); más de 2 de 32 que el entorno mueve sobre el umbral ya no es ruido sino otro cálculo |
| reproducción en cada otro grupo (conservadas, residual apagado, residual que sobrevive, negativos que B no publica, muestra D22), en `nativo|max` y `nativo|min` | ≤ 5 % del grupo (4 de 84, 2 de 42, 3 de 71) | elección: el mismo 5 % de la identidad; extendido de las conservadas a todos los grupos por V2-2, sin número nuevo |
| control positivo de D22 | 0 fallas: `nativo|min` publica TODAS las pérdidas D22 usables | literal: las 14 las publicó B por definición; si `min` no publica una, el instrumento no puede ver su recuperación. Que falte un gránulo es cobertura (fila de arriba), no esto |
| registro del TIF por pasada | r_L ≥ 0,90 con `tif_nn` | elección: el número que propuso el verificador. En P4 una sola celda de corrimiento deja r_L en 0,95; bajo 0,90 la escena no es la misma o no está registrada |
| pasadas que pasan el registro | ≥ 50 % de las 135 con TIF usable | elección: si más de la mitad de los TIF no es la escena, el pareo mismo es sospechoso y la mediana vendría de un subconjunto que no es al azar |
| brecha FP(nativo, min) − FP(nativo, max) | ≥ 0,10, e informada contra la del A/B (766 / 2.324 = 0,330) | elección: con brecha 0,10 la tolerancia de CONFIRMA (¼ de la brecha) es 0,025, del orden del error estándar de ΔFP (0,02 a 0,03, hallazgo 9): debajo de eso el criterio mide ruido. Desde V2-2 es un **segundo candado**: con la reproducción por grupo en pie la brecha sin parear no podía bajar de unos 0,27 (peor caso aritmético: 4 de 84 fallas en el residual apagado, 2 de 42 en los otros dos estratos, con los pesos de la ventana); desde N2 la brecha se calcula pareada y es, por construcción, la del A/B en esa muestra (0,330) |
| M publica las conservadas como el nativo | R_K(M, max) ≥ R_K(nativo, max) − 0,10; si no, INDETERMINADO POR INSTRUMENTO | sin número nuevo: la misma cota que ya usaba CONFIRMA, adelantada a gate (V2-1). Un M que no publica las alertas de MIROVA que el nativo publica no es el campo donde MIROVA detecta, y su «no recuperar» daba REFUTA |

Lo que **no** se cambió, a propósito: las cotas de H1 (½ y ¼) y de D22 (0,50 y 0,25), y las de validez del campo
(0,80 y [0,80; 1,25]). El verificador las revisó y concluyó que fallan hacia INDETERMINADO, no hacia CONFIRMA, y
que el azar no cumple las de H1 (hallazgo 9).

## 6. Criterio de H1 (σ del campo), pre-registrado

Unidad: publicación por el predicado del tablero. Sólo se calcula si pasaron todos los gates de §5. Tasas sobre la
muestra de la sonda, cada una con su n:
- **R_L(M, max)**, contraste **dentro de la corrida** (hallazgo 1, punto 2): sobre las **pérdidas reproducidas**
  (pérdidas confiables usables donde `nativo|max` de esta misma corrida no publica y `nativo|min` sí, §5.4), la
  fracción que `M|max` publica. Una pérdida que el entorno subió sobre el umbral en el nativo no está en el
  denominador, así que no se le puede atribuir al campo. La fracción absoluta sobre las 32 (y sobre las 42) se
  informa en la tabla H3, no decide.
- **R_K(c, k)**: fracción de las conservadas débiles publicadas en el campo c con la conectiva k.
- **FP(c, k)**: tasa de publicación en negativos limpios, ponderada por estrato con los totales de la ventana
  (residual apagado 766, sobrevive 63, B no publica 1.495). Como la muestra está pareada al volcán y mes de las
  pérdidas, FP describe los negativos de esos volcanes y meses, no la tasa global. En el A/B, F publica 2,7 % y B
  35,7 % de los 2.324 negativos limpios (S150 §6; verificador D22 H4): la brecha que `max` compró.

Con `brecha = FP(nativo, min) − FP(nativo, max)` y `ΔFP = FP(M, max) − FP(nativo, max)`, ambas medidas en la sonda:

| veredicto | condición |
|---|---|
| INDETERMINADO POR COBERTURA / POR INSTRUMENTO | falla algún gate de §5 (se dice cuál), **o** brecha < 0,10 (§5 bis: el nativo no reproduce lo que `max` compró en falsos y ΔFP ≤ ¼ · brecha se cumpliría con ΔFP = 0), **o** R_K(M, max) < R_K(nativo, max) − 0,10 (V2-1: M no publica las alertas de MIROVA que el nativo publica; antes un M muerto daba REFUTA). En cualquiera de estos casos **no se escriben** la tabla H3, el mecanismo, el nulo ni los números de H1 (V2-3); sólo los diagnósticos de los gates |
| **CONFIRMA** | R_L(M, max) ≥ 0,50 **y** ΔFP ≤ 0,25 · brecha **y** R_K(M, max) ≥ R_K(nativo, max) − 0,10 **y** zonas nulas sanas |
| **REFUTA** | R_L(M, max) < 0,25, **o** ΔFP > 0,50 · brecha (el campo mueve pérdidas y falsos juntos, como bajar C2) |
| INDETERMINADO | el resto |

**Contraste pareado (tercer verificador, N2).** ΔFP, la brecha y R_K se calculan **sólo sobre las pasadas que el
nativo reproduce** (las dos corridas del nativo iguales al A/B, §5.4), igual que R_L se calcula sólo sobre las
pérdidas reproducidas. Así FP(nativo, max) y FP(nativo, min) son exactamente los del A/B en esa muestra, y los
desvíos que tolera el 5 % del gate de reproducción no entran a la línea base: antes, desvíos tolerados que inflaban
FP(nativo, max) llevaban un M que reabre el 30 % del residual de INDETERMINADO a CONFIRMA. La tabla H3 sigue
informando las tasas sobre todas las pasadas usables. Consecuencia de diseño de V2-1, dicha aquí: REFUTA por recall
sólo sale si M publica las conservadas como el nativo y pierde las pérdidas; un suavizado que mate todas las alertas
débiles da INDETERMINADO POR INSTRUMENTO, no REFUTA, porque un campo que no ve lo que MIROVA vio no es el suyo.

**Potencia (hallazgo 9).** Con unas 32 pérdidas reproducidas, el error estándar de R_L ronda 0,09: si la tasa real
fuera exactamente 0,5, la cota de CONFIRMA se cruzaría la mitad de las veces. Es una cota pre-registrada, no una
prueba con potencia fija, y así se lee. El error estándar de ΔFP con 84 y 42 negativos ronda 0,02 a 0,03, bien bajo
la tolerancia de 0,08 que da la brecha del A/B.

Por qué esas cotas: el ideal de fidelidad es publicar todas las alertas (R_L = 1) y ningún negativo limpio (MIROVA
no publicó ninguno, por definición). `max` en el nativo está en (0; 2,7 %) y `min` en (1; 35,7 %). El campo de
MIROVA confirma H1 si devuelve al menos la mitad de lo que `max` perdió entregando a cambio a lo más un cuarto de
lo que `max` ganó en falsos; la refuta si casi no recupera, o si devuelve más de la mitad de esos falsos. Son
cotas relativas a lo medido en la misma corrida, no números inventados en absoluto; su forma (½ y ¼) sí es una
elección, y está dicha antes de ver datos.

Se informa además, sin decidir: R_L con las 42; la mediana de σ(campo)/σ(nativo) por grupo (la SOSPECHA de S150
§5 era 0,63 a 0,65 en pérdidas y residual contra 0,84 a 0,88 en conservadas); el AUC del margen z entre pérdidas y
residual apagado en cada campo (en el nativo, los campos del record no separaban: AUC 0,48); y la recuperación en
**noches** sin otra publicación de F (A94; verificador D22 H5).

## 7. D22 y D26, por separado (ampliación pedida, punto 3)

**Qué decide la sonda sobre la σ y qué decide sobre la compuerta son preguntas distintas**, y se leen en campos
distintos:
- **σ del campo (H1)** se decide comparando campos con la compuerta puesta: nativo contra M (§6). Pregunta si el
  problema es el sustrato sobre el que se mide σ.
- **D22 y D26** se deciden dentro de un mismo campo, comparando variantes del Test. En el nativo (la pregunta que
  el A/B suspendido quería responder) y, si existe, también en M (por si el remedio de la compuerta depende del
  sustrato). Población: las **14 pérdidas confiables del camino D22** (B sin ningún píxel del primer pase y el
  píxel publicado a menos de 3 K del fondo) contra la **muestra uniforme de 80 de los 271 negativos del mismo
  camino**. Eso es la selectividad dentro del estrato que pidió el verificador (H4): si sin la compuerta vuelven
  las alertas pero también esos negativos, D22 no es el arreglo.

Variantes, todas con `max`:

| variante | qué cambia | nivel |
|---|---|---|
| **D22** | primer pase sin compuerta; segundo pase como hoy | predicado (corrida real `max_sin_compuerta`) y tests (offline) |
| **D26** | compuerta puesta; pozo de μ₂ y σ₂ con los filtros de no aptos del primer pase | sólo tests (no hay flag; offline) |
| **D22 + D26** | las dos | sólo tests (offline) |

- Una pérdida cuenta como **recuperada** si la variante la publica (o, a nivel de tests, deja activo un píxel del
  objetivo) **y** `max` de esta misma corrida no (verificador D22 H3 c). El denominador son las pérdidas D22
  **reproducidas** por el nativo (§5.4), igual que en H1. Un negativo cuenta como **reabierto** si
  la variante publica y `max` no (o, a nivel de tests, aparece un píxel de cumbre activo que `max` no tenía).
- **Gates de D22**: los de §5 (identidad, cobertura general y la propia de D22 contada sobre las pérdidas
  reproducidas, V2-6; σ contra el A/B, reproducción por grupo; la validación del TIF y la condición de V2-1, que M
  publique las conservadas como el nativo, sólo cuando D22 se lee en M, N3), más el control positivo y que la
  muestra sea la lista congelada. Si falla uno, ninguna variante tiene veredicto y sus tasas no se escriben (V2-3),
  y la tabla H3 omite las filas `<campo>|max_sin_compuerta` de ese campo; si la frenada es la del nativo, las de
  todos los campos (N1).
- Reglas, para cada variante:

| veredicto | condición |
|---|---|
| NO RECUPERA | recupera menos de 7 de las 14 (< 0,50) |
| **NO ES EL ARREGLO** | recupera ≥ 0,50 pero reabre ≥ 0,25 de la muestra de negativos del camino |
| **SELECTIVO** | recupera ≥ 0,50 y reabre < 0,25 |

  0,50 y 0,25 son las cotas que el verificador D22 escribió para la selectividad (H4: «recupera al menos la mitad
  de las 14 y reabre menos de una cuarta parte de los 271»).
- **Cómo se lee el par.** Si D22 sola y D26 sola dan lo mismo en las 14, la pérdida es de la conjunción (lo que
  predijo el verificador, H1: con el primer pase vacío el dNTI del píxel es idéntico en los dos pases y sólo cambia
  el umbral). Si D26 sola recupera con selectividad y D22 no, el arreglo es el pozo del segundo pase y la compuerta
  puede quedarse. **Techo:** en 2 de las 14 (Isluga 2026-04-14 06:00 y Tupungatito 2026-08-21 06:30) F ya detecta
  un píxel con magnitud nula (verificador D22 H1): a nivel de predicado el techo realista es 12 de 14; a nivel de
  tests pueden contar.
- **Control del nivel de tests:** en D22 existen los dos niveles; se informa su acuerdo. Si es bajo, D26 y D22 + D26
  (que sólo tienen nivel de tests) se leen como orientación, no como veredicto.
- **Control positivo** (A116): `nativo|min` tiene que publicar las 14 (B las publicó). **Frena** (hallazgo 9): si no
  publica una sola de las usables, D22 y D26 quedan INDETERMINADO POR INSTRUMENTO, aunque H1 siga (el gate general
  tolera 2 fallas en las 32; el de D22 ninguna, porque con 14 casos y cota 7 cada una pesa 7 puntos).
- **Potencia:** con 14 casos, una recuperación real del 50 % cruza 7 de 14 con probabilidad cercana a 0,6
  (verificador D22 H11). Con 80 negativos, una reapertura del 25 % se mide con un error estándar de unos 5 puntos.
- **Unidad del operador:** de las 14, sólo 4 caen en noches sin otra publicación de F (§2). Se informa
  `recupera_noches_nuevas`: aun recuperando todo, el operador gana como mucho 4 noches.

## 8. H3, la tabla de lectura

Para nativo, `utm_nn` y los tres `tif_*`: R_L, R_K, publicación por grupo y FP con `min`, con `max` y con `max` sin
compuerta. Se lee como dice S150 §6: si con `min` el residual pasa y con `max` las pérdidas no, en todos los campos,
ninguna lectura de la conectiva reproduce a MIROVA y falta otro paso; si con `max` en M se separan, la conectiva
estaba bien y el defecto es el campo. La descomposición nativo → `utm_nn` → `tif_nn` → `tif_lin` separa el efecto
de la grilla (y su centro, D17) del efecto de interpolar.

## 9. Lo que la sonda NO decide, y sus límites

- **El interpolador de MIROVA** sólo se infiere por parecido con el TIF; si es otro (vecino natural, un filtro
  previo), ningún `tif_*` lo reproduce y H1 queda indeterminada.
- **El TIF que validamos puede no tener la textura de la grilla donde MIROVA detecta (hallazgo 4).** Los papers
  (Aveni 2024, Campus 2024) dicen que MIROVA detecta en una grilla UTM; los TIF de mayo a agosto, con los que se
  valida, son EPSG:4326. En `textura_utm_vs_geo_salida.txt` la autocorrelación a una celda de dL es **menor en el
  geográfico en los 11 de 11 volcanes** (0,18 a 0,30 contra 0,24 a 0,47). Once de once en la misma dirección no es
  ruido, aunque está confundido con las noches (los UTM son sólo del 14 y 15 de septiembre). SOSPECHA: los dos
  productos no tienen la misma textura y no sabemos cuál corresponde a la detección. Si la detección es la del UTM
  (más suave), validar contra el geográfico elige un campo menos suave que el real y sesga hacia REFUTA. La sonda no
  lo resuelve; lo dice.
- **La validación es casi una prueba de registro de subcelda (hallazgo 4).** En P4 correr el TIF una celda baja
  r_dL de 1 a 0,25 con r_L = 0,95. Una diferencia de geolocalización entre nuestro gránulo estándar y el NRT que
  procesó MIROVA, o un TIF pareado a otra pasada (17 de los 135 son archivos `_lm` cuya hora puso el índice), baja
  r_dL en los tres candidatos y empuja a INDETERMINADO. Es una falla segura (no confirma de más), pero puede gastar
  el run; por eso el gate de r_L ≥ 0,90 por pasada (§5.5) y el piloto (§10 bis). No se implementó el diagnóstico de
  r_dL con el mejor desplazamiento de ±0,5 celda (hallazgo 4 c): queda pendiente si el piloto muestra r_dL bajo con
  r_L alto. Además, en el sintético `tif_nn` contra un TIF lineal dio r_dL = 0,800, justo el umbral: r_dL ≥ 0,80
  no separa vecino de lineal; lo separa sólo s_ratio.
- **El TIF sólo trae I04 (hallazgo 5).** I05 no se puede validar: el NTI de la sonda mezcla una I04 validada con una
  I05 interpolada igual pero sin control. Estimación de orden del verificador, SIN VERIFICAR con datos: de noche
  L(I05) ronda 3 a 5 W m⁻² sr⁻¹ µm⁻¹ y L(I04) 0,05 a 0,2, y con el ruido de I04 a 260 K (del orden de 1 K) el
  término de I04 domina la varianza de dNTI por un factor de 3 a 10. Para medirlo en vez de suponerlo, cada campo
  guarda L_i05 por píxel y la fracción de la varianza de dNTI del pozo que explica el término de I04
  (`frac_var_dnti_termino_i04`, linealización de primer orden; en el sintético de la prueba local, con ruido
  blanco igual en las dos bandas, da 0,91 y la linealización explica 0,999 de la varianza). Si en los datos reales
  esa fracción es baja, la validación con I04 no valida lo que fija σ y H1 se lee con esa reserva.
- **Los campos `tif_*` cambian también el centro, el radio y la referencia de distancia (hallazgo 10).** La escena
  se centra en `get_grid_center` con radio 26 km, y la distancia que define el ROI pasa a medirse desde ese centro.
  No contamina la clase `summit` de las pérdidas (su fuente es `ctx_cluster` y con el ancla honesta la distancia
  final es la del cúmulo medida desde el cráter, `anchor.py:82-84`; sólo el respaldo `eruption_loose` usa la del
  centro), pero sí cambia el pozo de σ; eso se separa leyendo nativo → `utm_nn` → `tif_nn` → M (§8). No se
  implementó el diagnóstico de R_L restringido a publicaciones cuyo cúmulo cae en la zona objetivo: una
  «recuperación» en M puede ser de otro píxel de la cumbre y no del mismo foco. Pendiente; no decide.
- **El TIF sale del mismo gránulo** (A109): valida la construcción del campo, no certifica detecciones.
- **Abril no tiene TIF**: sus campos `tif_*` usan la plantilla validada con los TIF de mayo a septiembre.
- **Versión del gránulo.** NASA pudo reprocesar desde septiembre; la sonda prefiere el mismo archivo que el A/B y
  lo informa. Versiones de paquetes: cada lote guarda `pip freeze` (verificador D22 H9).
- **No mide magnitud ni posición** contra MIROVA: sólo detección y publicación.
- **Muestra pareada**: FP describe los volcanes y meses de las pérdidas (§6).
- **Prueba local sobre un gránulo sintético**: probó el código de punta a punta, no el tamaño de ningún efecto. En
  el sintético (ruido blanco de 0,35 K) la σ dNTI lineal fue 0,607 veces la nativa (`prueba_local_salida.txt`);
  eso muestra que el instrumento puede dar campos distintos, no predice el resultado real. Lo mismo vale para las
  poblaciones de P6 y P7: prueban que el evaluador da cada veredicto sólo cuando corresponde, no qué va a dar.
- **Volumen de la salida (hallazgo 8), SIN MEDIR.** La tabla por píxel lleva unas 35 columnas por campo y hasta
  4.000 filas (más, si hay más píxeles activos que eso: el tope ya no los corta), en 5 campos por pasada; el job
  `evaluar` empuja todo a una rama que no caduca. El piloto lo mide (bytes por pasada, §10 bis); si es grande, antes
  del despacho completo se decide por escrito empujar sólo `evaluacion.*` y dejar el detalle en los artefactos.
- **Detalles del verificador que no se corrigieron (hallazgo 11).** Versiones de paquetes sin fijar en la sonda y en
  el A/B (con el contraste dentro de la corrida y el gate de σ, deja de importar para H1; cada lote guarda
  `pip freeze`). El job `evaluar` instala sólo `numpy pyyaml pandas` y `evaluar.py` importa `banco_paridad`, que
  arrastra `auto_audit_weekly`, `pipeline.store` y `referencia_mirova_unificada`: debería bastar, SIN VERIFICAR en
  un entorno limpio. El piloto lo comprueba porque, aun con `--piloto`, `main()` importa `banco_paridad` y corre
  los casos de control del predicado con node (`control_identidad_predicado`, que no mira datos de la sonda); la
  versión anterior decía que lo comprobaba y no lo hacía (V2-9).
- **Lo que el sello deja fuera (V2-11).** `scripts/auto_audit_weekly.py` y `scripts/referencia_mirova_unificada.py`
  (los importa `banco_paridad`, no entran al predicado ni a la detección), `prueba_local.py`, archivos sin versionar
  y cambios sólo de finales de línea no rompen el sello. Las versiones de numpy y scipy tampoco se fijan; las cubre el
  gate de σ en el nativo, no en los `tif_*`.
- **Re-sellar no está impedido (V2-8).** `sellar.py --verificar` imprime qué entradas cambiaron respecto del sello
  anterior distinto en la historia de git (en el runner, con `fetch-depth` 1, no hay historia y lo dice), y §10 bis
  dice qué puede cambiar entre el piloto y el despacho; pero nada impide re-sellar con otro criterio. La procedencia
  queda en git. En §2, «residual apagado 29 / muestra D22
  31» mezclaba grupo primario y pertenencia (por grupo primario son 29 y 28, por pertenencia la muestra es 31;
  recontado sobre `pasadas.json`); ya se dice en §2.
- **Contraste del objetivo en el TIF (hallazgo 9), no implementado.** En las 10 pérdidas con TIF se podría informar
  el contraste del objetivo en el TIF y en M (aquí el TIF sale del mismo gránulo y eso es lo que se quiere, A109 no
  aplica). Es diagnóstico, no decide; queda pendiente.

## 10. Para el verificador del pre-registro

1. Que la lista de `pasadas.json` sea la que dice §2 y que el sorteo no dependa de ningún resultado
   (`seleccionar_pasadas.py`, semillas 150 y 172; correr de nuevo debe dar el mismo archivo).
2. Que los campos `tif_*` sean una réplica razonable del paso de MIROVA: centro en `get_grid_center`, radio 26 km
   para cubrir su imagen, interpolación en radiancia, I05 sin validar (§3, §9).
3. Las cotas de §5 (0,80; 0,80 a 1,25) y de §6 (½ y ¼): son elecciones; revisar si son razonables o si hay un dato
   que las fije mejor (A115).
4. Que `evaluar.py` implemente exactamente §5 a §8 (P5 a P7 de la prueba local recorren sus ramas sobre clones
   sintéticos con la meta real; P6 y P7 muestran cada veredicto saliendo sólo cuando corresponde).
5. Que la variante «d26» de `campos._segundo_pase_replica` sea la lectura correcta del paper (pozo del segundo
   pase con los mismos no aptos del primero; D26).
6. Que la zona objetivo de 0,75 km no fabrique recuperaciones al cambiar de grilla (el nulo de §5 lo vigila).
7. Costo: 365 pasadas × (3 corridas sobre el gránulo entero + 12 sobre grillas) no está medido; 330 minutos por
   lote es un supuesto. Por eso el **piloto con el lote 1** es obligatorio (§10 bis).
8. Que el workflow autentique sólo por token, use `"on":` entre comillas, `ubuntu-24.04`, el candado y el sello, y
   que el checkout disperso del archivo de TIF nunca reciba una lista vacía (siempre incluye `README.md`).
9. (Segunda verificación.) Que las correcciones de esta versión cierren los hallazgos 1, 2, 3, 6 y 7, que los
   números de §5 bis sean razonables, y que P6 y P7 de la prueba local muestren cada veredicto saliendo sólo cuando
   corresponde.

## 10 bis. Piloto obligatorio y sello

**El piloto es obligatorio, no una recomendación** (hallazgos 2, 8 y 11). Se despacha con `piloto = si` y
`lotes = 1` (Chaitén, 12 pasadas, 2 pérdidas confiables, 10 con TIF). En el piloto:
- el evaluador corre con `--piloto`: **no** corre el predicado sobre datos de la sonda ni imprime ningún veredicto
  de detección (ni H1, ni D22, ni la tabla H3, ni la reproducción del A/B). Imprime sólo cobertura de los lotes que
  corrieron, identidad, la **σ del nativo contra el record del A/B y la fracción de pasadas con el mismo L1B que el
  A/B** (V2-4), tiempo y memoria por pasada (`segundos`, `rss_max_mb`), volumen de la salida en bytes y la validación
  contra el TIF (con el gate de r_L, por campo y por volcán). Corre además los casos de control del predicado con
  node, que no miran datos de la sonda (V2-9);
- **si en el piloto la σ o el gránulo difieren del A/B en más del 5 % de sus pasadas, no se despacha el resto**: ese
  gate tumbaría las 365 (por ejemplo, si NASA reprocesó los gránulos) y hay que resolverlo antes;
- el log de Actions no imprime ningún dato de detección por pasada (V2-7): sólo n del ROI, σ e identidad. Los json
  por pasada sí traen las decisiones, y nadie tiene por qué abrirlos en el piloto;
- no se crea la rama de datos (el job de guardado se salta); los artefactos quedan 90 días;
- se lee **sólo** para validación, cobertura, σ, tiempo y memoria. Con eso se ajustan, antes del despacho completo y
  por escrito en este documento, `max-parallel`, el timeout y, si hace falta, la geometría de la
  validación (hallazgo 4 e; esta última cambia `evaluar.py` o `campos.py`, así que exige un verificador nuevo). **Todo ajuste se justifica citando esos números** (V2-7). **No** se ajusta ningún
  umbral de H1 ni de D22;
- **lo único que puede cambiar entre el piloto y el despacho** sin un verificador nuevo es el yml (sólo
  `max-parallel` y `timeout-minutes`; el tamaño de lote vive en `pasadas.json`, que no cambia) y esta sección §10 bis
  del DISENO. El re-sello imprime
  qué entradas cambiaron (V2-8); si aparece cualquier otra, el despacho no se hace sin un verificador nuevo;
- **su lote se vuelve a correr en el despacho completo.** El piloto no aporta pasadas a la evaluación, y si su
  salida queda en la misma carpeta que la del despacho, el evaluador lo detecta como pasadas duplicadas (V2-5);
- el despacho completo exige `lotes` vacío: el yml rechaza `piloto = no` con una lista de lotes (V2-3). Y el piloto
  corre **exactamente un lote**: «Plan de lotes» limpia la lista y, si con `piloto = si` no queda exactamente uno
  (`" "`, `","` o `"1,2"`), falla (N5: antes `" "` pasaba el candado y corría los 35 lotes como piloto). Que la
  interfaz de GitHub o `gh workflow run` recorten espacios está SIN VERIFICAR; el plan no depende de eso.
Aun si alguien abriera los json por pasada del piloto, con 2 pérdidas no hay veredicto posible: el gate de
cobertura exige 30 de 32 sobre `pasadas.json` entero (P7 lo comprueba con el lote 1).

**El sello** (`sellar.py`, hallazgo 3) fija con sha256 (finales LF) los archivos de la sonda (este documento,
`evaluar.py`, `campos.py`, `sonda.py`, `seleccionar_pasadas.py`, `sellar.py` y las tres listas congeladas) **y** lo
que decide el resultado tanto como el criterio: cada archivo versionado de `pipeline/` (con los perfiles),
`frontend/index.html` (el predicado), `scripts/banco_paridad.py` (su arnés), `scripts/run_pipeline.py`
(`load_volcanoes`, `VOLCANIC_FEATURES`), `volcanoes.yaml` y el propio workflow. Un archivo agregado o borrado en
`pipeline/` también lo rompe. Se eligió la lista de hashes y no `git diff <sha> HEAD` porque no necesita la historia
en el runner y sobrevive a un squash merge. El sello guarda además la procedencia: el sha del commit sobre el que se
selló, quién aprobó y contra qué informe; sin esas tres líneas no verifica. Como `main` cambia casi a diario, entre
el sello y el despacho no puede entrar ningún cambio a esas rutas: si entra, se vuelve a verificar y a sellar.

## 11. Archivos

| archivo | qué es |
|---|---|
| `DISENO.md` | este documento |
| `seleccionar_pasadas.py`, `seleccionar_pasadas_salida.txt` | la lista y sus controles de reproducción |
| `pasadas.json` | 365 pasadas con grupo, lote, gránulo del A/B, record resumido de B y F, TIF pareado |
| `negativos_camino_d22.json` | las listas congeladas de 271 y 576 negativos y de las 15 / 14 pérdidas del camino D22 |
| `plantillas_tif.py`, `plantillas_tif_salida.txt`, `plantillas_tif.json` | la grilla de MIROVA por volcán |
| `textura_utm_vs_geo.py`, `textura_utm_vs_geo_salida.txt` | chequeo de diseño: TIF UTM contra geográfico |
| `campos.py` | funciones puras: interpolación, regrid a la grilla de MIROVA, evaluación por píxel, validación |
| `sonda.py` | el runner de CI (descarga, cinco campos, captura, persistencia, salida por pasada) |
| `evaluar.py` | el criterio de §5 a §8 |
| `prueba_local.py`, `prueba_local_salida.txt` | prueba sin NASA: P0 a P8 (con P7b y P7c), 124 comprobaciones, todas OK; los 12 casos de P7b fallan con el código de `5eda5b942` y los 4 de P7c con el de `aae4a4ed0` |
| `sellar.py` | escribe (con `--aprobo` y `--informe`) y verifica `SELLO_PREREGISTRO.txt` (lo corre quien aprueba, no esta sesión) |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s150\VERIFICADOR_SONDA_TRES_CAMPOS.md` | el informe del verificador de la primera versión |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s150\VERIFICADOR2_SONDA_TRES_CAMPOS.md` | el informe del segundo verificador, sobre `5eda5b942` |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s150\VERIFICADOR3_SONDA_TRES_CAMPOS.md` | el informe del tercer verificador, sobre `aae4a4ed0` |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\probe-s150-tres-campos.yml` | el workflow (no despachado) |
