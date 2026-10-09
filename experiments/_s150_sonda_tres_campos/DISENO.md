# Sonda S150 de los tres campos: diseño (escrito y probado en local, SIN despachar)

> **Estado.** Diseño de un agente, sin verificador con contexto limpio todavía. No se bajó ningún gránulo
> de NASA ni se usaron credenciales. Nada de `pipeline/`, perfiles ni `data/` se tocó. El despacho exige
> (1) que un verificador apruebe este documento, (2) que quien lo aprueba corra `python sellar.py` para
> sellar los ocho archivos que fijan el criterio y la lista, y (3) el input `preregistro_aprobado = si` del
> workflow `.github/workflows/probe-s150-tres-campos.yml`. Sin el sello el workflow no corre.

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
  apagado 29, sobrevive 17, B no publica 15, muestra D22 31. Abril no tiene ningún TIF (el archivo empieza el
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
combinación; tope 4.000 por campo): fila, columna, lat, lon, distancia al ancla, cumbre, objetivo, BT de I04,
**BT − t_bg**, radiancia I04, NTI, dNTI, dETI, si pasa la compuerta, y por cada conectiva × compuerta: dNTI₂, dETI₂,
activo en el primer pase, final con el pozo real y final con el pozo «d26». Con eso y los μ, σ, μ₂, σ₂ guardados
se rehace offline cualquier decisión sin volver a bajar el gránulo (pedido 1 de la ampliación).

**Validación contra el TIF** (`campos.validar_contra_tif`), en las pasadas con TIF usable, para cada campo `tif_*`:
correlación de la radiancia (r_L), diferencia relativa mediana, correlación del contraste de 8 vecinos dL (r_dL),
razón de desviaciones sd(dL campo)/sd(dL TIF) (s_ratio) y autocorrelación a una celda de dL en el campo y en el TIF.
El borde de una celda se excluye. r_L dice si es la misma escena bien georreferenciada; r_dL y s_ratio dicen si la
**textura** que fija σ es la de MIROVA, que es lo que importa para H1.

## 5. Las dos preguntas del instrumento, y los controles

**¿Si estuviera roto, se vería?**
1. **Identidad con el pipeline, en cada pasada y campo.** μ y σ recalculados contra el diag que devolvió la
   función real (diferencia relativa < 1e-9), mismo tamaño de pozo, la máscara del primer pase recalculada contra
   `first_pass_tests_2_and_3` real con la misma conectiva y compuerta (4 combinaciones), y la réplica del segundo
   pase contra `second_pass_adjacent` real. Un par pasada-campo que falle se excluye y se cuenta; si fallan más del
   5 %, todo el run es INDETERMINADO POR INSTRUMENTO.
2. **Reproducción del A/B.** `nativo|max` tiene que publicar lo que F publicó y `nativo|min` lo que B publicó
   (acuerdo ≥ 95 % cada uno). Además se informa cuántas pasadas usaron el mismo archivo L1B que el A/B (la sonda lo
   prefiere al bajar) y cuánto difiere la σ dNTI nativa de la del record del A/B. Si no se reproduce, los
   veredictos llevan la salvedad (la comparación entre campos de la misma corrida sigue valiendo).
3. **Validación del campo contra el TIF de MIROVA** (§4). Un campo `tif_*` es **válido** si la mediana de r_dL es
   0,80 o más y la mediana de s_ratio está entre 0,80 y 1,25. Entre los válidos, el **campo MIROVA (M)** es el de
   mayor r_dL (empate: s_ratio más cerca de 1). Se elige mirando sólo el TIF, nunca los resultados de H1. Si ningún
   campo es válido, H1 es INDETERMINADO POR INSTRUMENTO. Los umbrales 0,80 y [0,80; 1,25] no salen de un dato
   medido: son la cota de «misma textura» que se fija antes de ver datos (el verificador debe revisarlos, §10).
4. **Cobertura (A108).** Cada lote sale en rojo si alguna pasada no completó sus 15 corridas; el evaluador informa
   esperadas, con salida y completas por grupo antes de cualquier tasa.

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

## 6. Criterio de H1 (σ del campo), pre-registrado

Unidad: publicación por el predicado del tablero. Tasas sobre la muestra de la sonda:
- **R_L(c, k)**: fracción de las 32 pérdidas confiables publicadas en el campo c con la conectiva k.
- **R_K(c, k)**: ídem sobre las conservadas débiles.
- **FP(c, k)**: tasa de publicación en negativos limpios, ponderada por estrato con los totales de la ventana
  (residual apagado 766, sobrevive 63, B no publica 1.495). Como la muestra está pareada al volcán y mes de las
  pérdidas, FP describe los negativos de esos volcanes y meses, no la tasa global. En el A/B, F publica 2,7 % y B
  35,7 % de los 2.324 negativos limpios (S150 §6; verificador D22 H4): la brecha que `max` compró.

Con `brecha = FP(nativo, min) − FP(nativo, max)` y `ΔFP = FP(M, max) − FP(nativo, max)`, ambas medidas en la sonda:

| veredicto | condición |
|---|---|
| **CONFIRMA** | R_L(M, max) ≥ 0,50 **y** ΔFP ≤ 0,25 · brecha **y** R_K(M, max) ≥ R_K(nativo, max) − 0,10 **y** zonas nulas sanas |
| **REFUTA** | R_L(M, max) < 0,25, **o** ΔFP > 0,50 · brecha (el campo mueve pérdidas y falsos juntos, como bajar C2) |
| INDETERMINADO | el resto |

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
  objetivo) **y** `max` de esta misma corrida no (verificador D22 H3 c). Un negativo cuenta como **reabierto** si
  la variante publica y `max` no (o, a nivel de tests, aparece un píxel de cumbre activo que `max` no tenía).
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
- **Control positivo** (A116): `nativo|min` tiene que publicar las 14 (B las publicó); se informa.
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
- **El TIF sólo trae I04.** I05 no se puede validar: el NTI de la sonda mezcla una I04 validada con una I05
  interpolada igual pero sin control.
- **El TIF sale del mismo gránulo** (A109): valida la construcción del campo, no certifica detecciones.
- **Abril no tiene TIF**: sus campos `tif_*` usan la plantilla validada con los TIF de mayo a septiembre.
- **Versión del gránulo.** NASA pudo reprocesar desde septiembre; la sonda prefiere el mismo archivo que el A/B y
  lo informa. Versiones de paquetes: cada lote guarda `pip freeze` (verificador D22 H9).
- **No mide magnitud ni posición** contra MIROVA: sólo detección y publicación.
- **Muestra pareada**: FP describe los volcanes y meses de las pérdidas (§6).
- **Prueba local sobre un gránulo sintético**: probó el código de punta a punta, no el tamaño de ningún efecto. En
  el sintético (ruido blanco de 0,35 K) la σ dNTI lineal fue 0,607 veces la nativa (`prueba_local_salida.txt`);
  eso muestra que el instrumento puede dar campos distintos, no predice el resultado real.

## 10. Para el verificador del pre-registro

1. Que la lista de `pasadas.json` sea la que dice §2 y que el sorteo no dependa de ningún resultado
   (`seleccionar_pasadas.py`, semillas 150 y 172; correr de nuevo debe dar el mismo archivo).
2. Que los campos `tif_*` sean una réplica razonable del paso de MIROVA: centro en `get_grid_center`, radio 26 km
   para cubrir su imagen, interpolación en radiancia, I05 sin validar (§3, §9).
3. Las cotas de §5 (0,80; 0,80 a 1,25) y de §6 (½ y ¼): son elecciones; revisar si son razonables o si hay un dato
   que las fije mejor (A115).
4. Que `evaluar.py` implemente exactamente §5 a §8 (P5 y P6 de la prueba local recorren sus ramas sobre clones
   sintéticos, con veredictos degenerados a propósito).
5. Que la variante «d26» de `campos._segundo_pase_replica` sea la lectura correcta del paper (pozo del segundo
   pase con los mismos no aptos del primero; D26).
6. Que la zona objetivo de 0,75 km no fabrique recuperaciones al cambiar de grilla (el nulo de §5 lo vigila).
7. Costo: 365 pasadas × (3 corridas sobre el gránulo entero + 12 sobre grillas) no está medido. Se recomienda un
   **piloto con el lote 1** (Chaitén, 12 pasadas, 2 pérdidas, 10 con TIF) antes del despacho completo, para medir
   tiempo y memoria por pasada y ajustar `max-parallel` y el tamaño de lote.
8. Que el workflow autentique sólo por token, use `"on":` entre comillas, `ubuntu-24.04`, el candado y el sello, y
   que el checkout disperso del archivo de TIF nunca reciba una lista vacía (siempre incluye `README.md`).

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
| `prueba_local.py`, `prueba_local_salida.txt` | prueba sin NASA: P0 a P6, 61 comprobaciones, todas OK |
| `sellar.py` | escribe y verifica `SELLO_PREREGISTRO.txt` (lo corre quien aprueba, no esta sesión) |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\probe-s150-tres-campos.yml` | el workflow (no despachado) |
