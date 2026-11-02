# Pre-registro: prueba retrospectiva del paquete de las tres vías «código MIROVA» en los 11 Tier A

Estado: **BORRADOR, SIN SELLO.** Escrito el 2026-11-02 entre 01:00 y 02:30 UTC (hora del servidor de GitHub al
empezar: `Mon, 02 Nov 2026 01:36:17 GMT`) por un agente de S172, a pedido de la coordinadora, como paso 1 del plan
`docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` (rama `loop/activo`, `fa22f4b87`), Tarea 0.1. No se corrió
ningún brazo ni se miró ningún resultado de la vía fuera de lo que ya está publicado en el repo. Lo único que se contó
sobre datos fue la referencia de MIROVA sola (tabla del scraper y OSF v2.5), para estimar el poder; esos conteos son
aproximados y el pre-registro manda recalcularlos con `banco_paridad` antes del sello (§7).

Rutas de repo relativas a `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. Commits citados:
`origin/main` = `14fb62030` (2026-11-01 23:34 UTC), `loop/activo` = `fa22f4b87`.

---

## 0. En una pantalla (para Nicolás)

**Qué contesta.** Si el paquete (las tres vías encendidas a la vez, el mismo perfil que la sombra prospectiva) se
comporta como MIROVA **en pasadas que ninguna regla miró al escribirse**: febrero y marzo de 2026 contra la tabla de
MIROVA, y febrero a diciembre de 2025 contra el OSF v2.5. Es la respuesta más rápida posible a «¿funcionamos igual que
MIROVA?», unas tres semanas antes de que las sombras prospectivas lleguen a su parada.

**Qué no contesta.** No prueba el sistema que va a publicar (LANCE, cortes de NASA, cron atrasado) ni el régimen sin
Suomi NPP: eso lo prueba sólo la sombra (plan §1). No prueba nada en Chillán en erupción: toda su erupción cae dentro de
muestra. Y en MODIS y VIIRS 750 tiene poco poder fuera de muestra (§7).

**Lo que la vuelve honesta.** (1) Decide sólo fuera de muestra; la ventana de octubre se corre como control de montaje,
no como evidencia. (2) Aplica a cada sensor su propia regla de adopción ya escrita, sin tocarla, y agrega una lectura
absoluta contra MIROVA que informa. (3) Ningún veredicto se llama «igual a MIROVA»: el nombre dice lo que la regla
prueba (§8).

**Cuándo y cuánto.** Después del despacho de V750-B (2026-11-03) y del merge de `roi_v750` (~11-04 a 11-06). Entre 180 y
220 h de runner de la vía más unas 10 h de control de K; pared de 32 a 40 h repartida en cuatro despachos, el grueso
en el de 2025 (§10).
Evidencia leída y verificada hacia el **2026-11-10 a 11-12**.

**Lo que tienes que decidir** está en el §12 (diez preguntas, cada una con recomendación).

---

## 1. Pregunta y unidad, como geólogo

**El fenómeno.** Un cráter activo de noche es una fracción mínima de un píxel de 375 m, 750 m o 1 km. MIROVA lo ve
interpolando el gránulo a una grilla fija alrededor del volcán, comparando cada celda con su entorno por NTI y ETI,
midiendo el fondo bajo un halo y sumando la radiancia de todas las celdas alertadas. Las tres vías hacen eso mismo con
el código de MIROVA, y dentro de muestra se equivocan menos que K y miden la magnitud cerca de la de MIROVA (MOD-D:
razón 0,983, `experiments/_s168/modd_f4_candado/lectura_ab2/leer_f4_salida.txt` en `e0bb1b150`; V375-E: 0,9996,
`experiments/_s172_chillan/auditor/v375e_lectura_salida.txt` en `loop/activo`; port de V750 0,994 a 0,998 en Chillán,
`experiments/_s172_chillan/verificador/INFORME.md`).

**La sospecha que esta prueba busca refutar.** Las reglas se eligieron mirando abril a octubre de 2026: la caja C13 de
375, la ROI de 750, la posición. Abril a octubre es otoño, invierno y primavera: cumbres nevadas, fondos fríos,
gradiente topográfico nocturno fuerte (A69). Febrero y marzo son verano (sin nieve en casi todos los conos) y 2025
trae las cuatro estaciones. Si las reglas se ajustaron a una estación, aquí se ve.

**La pregunta.** En febrero y marzo de 2026 y en 2025, por sensor: ¿el paquete (a) no pierde alertas protegidas que
MIROVA publicó, (b) se equivoca menos que K, o igual, en lo débil (alertas bajo 1 MW perdidas más publicaciones donde
MIROVA calló), y (c) mide la magnitud como MIROVA, también cuando el satélite mira de lado?

**Unidad.** La **pasada** (un gránulo, un volcán, un sensor), que es donde se aplican las reglas selladas y donde se
parea con MIROVA a ±120 s. Y la **noche-volcán** para lo que vive el operador: una noche con alerta protegida de
MIROVA en cualquier sensor, ¿la ve el tablero en algún sensor? Una noche en que MIROVA miró y calló en todos los
sensores, ¿el tablero calla? (§5.5). La noche informa; decide la pasada, porque así lo dicen las reglas selladas y el
criterio de victoria (`docs/MISSION.md` l. 115: «por sensor y por tramo»).

---

## 2. Qué se prueba: el paquete y los brazos

| brazo | qué es | papel |
|---|---|---|
| **VIA** | `run_pipeline.py` con el perfil aislado `_s172_retro_paquete` (§10.1): K de producción con las tres vías encendidas, MxD03 apagado, en el commit del tag del despacho; `store.append_record` como en producción | lo que se mide |
| VIA-radiante, VIA-cercano, VIA-pico | el record de VIA con la distancia al cráter de cada regla de posición (`variante_posicion` de MOD-D fase 4 y `distancias_desde_record` del lector de V375-E) | brazos de posición; decide el que eligió cada pre-registro (§5.1) |
| **K** | los records de `data/mirova_equivalent/` en el commit del tag (escritos por el reproceso #883 con K, cada uno con su `codigo_sha`) | control y vara de las reglas selladas |
| **K-gemelo** | el mismo código del tag con el perfil `_s172_retro_k` (vías apagadas), corrido en el runner sobre DM entero y sobre Láscar en F26 | control: que K de disco sea K de hoy, y ruido entre runners (S152) |
| **PLACEBO** | el record de K con toda magnitud × 1,2 | programa §2, obligatorio |

**Por qué K de disco y no un K re-corrido entero.** Correr K en todo el histórico duplica el costo (§10.4), y ya hay
dos mediciones de que K re-corrido publica igual que lo publicado: V375-E 2.342 de 2.342
(`v375e_lectura_salida.txt`) y el control `k_produccion` OK de MOD-D fase 4 (`leer_f4_salida.txt`). El K-gemelo sobre
DM y Láscar-F26 vuelve a medirlo con el código del tag; si falla, K de disco no sirve y la lectura queda INDECIDIBLE
hasta correr K entero (§6, C-K).

**Por qué el paquete entero y no cada vía por separado.** Es lo que va a correr la sombra y lo que se publicaría. Las
tres vías no se tocan entre sí (cada una cambia sólo el procesador de su sensor; comentario de
`pipeline/profiles/sombra_codigo_mirova.yaml`), así que el veredicto se lee por sensor igual.

---

## 3. Población por tramo y qué está dentro de muestra

Una ventana está **dentro de muestra** si alguien la miró para escribir una regla de las vías o la de K. Medir ahí
reproduce lo ya sabido. Evidencia de cada regla (archivo y línea en el ref donde está la versión vigente; ojo con el
§13, hay copias viejas en `main`):

| regla | ventana que usó | evidencia |
|---|---|---|
| K (adopción, #848) | V1 2026-08-29 a 10-08; V2 2026-03-01 a 06-12, VIIRS decide desde 04-01 | `experiments/_s151_prereg_fk_11/PREREGISTRO.md` l. 90 a 102 (`loop/activo`) |
| MOD-D censo (D-48) | 2026-03-01 a 10-16 | `experiments/_s162_modis_paquete/PREREGISTRO.md` l. 56 a 58 (`loop/activo`) |
| MOD-D fase 4 (sellado) | tramo C 2026-03-01 a 10-16; tramo E 2026-10-17 a 10-26 | `experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` l. 92 a 121 (`25e3cc3ba`, tag `s168-modd-f4-sellado`) |
| V375-E (sellado) y C13 (V375-C, PD1) | marco S159, 2026-04-01 a 10-21 sin el 12, 13 y 17 a 20 de octubre | `experiments/_s162_v375/PREREGISTRO_E.md` l. 70 y §9.2 l. 550 a 556 (tag `s170-v375e-lector`) |
| V750-B (sellado; elige la ROI) | T 2026-04-01 a 06-12; O 2026-06-13 a 11-02 12:59 UTC, sin el 12, 13 y 17 a 20 de octubre | `experiments/_s162_v750b/PREREGISTRO_V750B.md` l. 97 a 106 (tag `s167-v750b-adenda3-sellada`) |
| V750-A (borrador) | la de V750-B | `experiments/_s162_v750a/PREREGISTRO_V750A.md` l. 130 a 137 (rama `claude/s162-viirs750-2-918174`, `aa5583646`) |
| Regla de posición (S165) | ventana O | plan §1 punto 5; `experiments/_s165_regla_posicion/INFORME.md` |
| `WOOSTER_COEFF` de MODIS y VIIRS 375 (S14) | todo el OSF v2.5 de Chile, 2001 a 2025 (48.360 filas) | `CLAUDE.md` del proyecto, «Reglas científicas»; ver §4.3 sobre por qué no contamina la razón |

**Tramos de esta prueba:**

| tramo | fechas (UTC, pasadas nocturnas) | volcán-día | rol | por qué |
|---|---|---|---|---|
| **F26-V** | 2026-02-01 a 2026-03-31, VIIRS 375 y 750 | 649 | **decide** | ninguna regla de las vías lo miró; K lo procesó en V2 sólo en MODIS (VIIRS decidía desde 04-01) |
| **F26-M** | 2026-02-01 a 2026-02-28, MODIS | 308 | **decide** | MOD-D empieza el 03-01 |
| F26-M3 | 2026-03-01 a 2026-03-31, MODIS | 341 | control (dentro de muestra) | tramo C de MOD-D; tiene que reproducir el sentido de MOD-D |
| **R25** | 2025-02-15 a 2025-12-31, los tres sensores | 3.520 | **decide sólo P1-OSF; magnitud informa** | ninguna regla lo miró; la referencia es el OSF filtrado (§4.2) |
| DM | 2026-10-01 a 2026-10-16 (VIIRS sin el 12 ni el 13) | 176 | **control de montaje**, no evidencia | se solapan MOD-D C, V375-E y V750-B |
| E26 | 2026-01 | 0 | fuera | A119: enero no se usa (y no hay serie continua en la tabla antes del 10-ene) |

Restricciones dentro de los tramos que deciden:
- **Tupungatito**: en F26 entra desde el **2026-02-23** (la tabla no tiene filas antes del 02-14 y hasta el 02-23 el
  scraper rotulaba ALERTA con 5 km y no 7: hitos de `scripts/calidad_referencia_mirova.py`). En R25 no tiene filas en
  el OSF: **SIN DATO**.
- **NOAA-21**: no hay ninguna pasada de NOAA-21 en la tabla antes del **2026-04-09** (hito de
  `calidad_referencia_mirova.py`) ni en el OSF de 2025 (las filas de 375 y 750 traen dos códigos de satélite, 3 y 4;
  conteo propio, la tabla de códigos SIN VERIFICAR). Sus pasadas de F26 y R25 quedan `sin_info`: no entran a ninguna
  prueba que decide; se cuentan y se listan.
- **Sólo noche**, como todos los pre-registros de las vías (el pipeline filtra el día por elevación solar). El día es
  #813, otro frente.

**Por qué la población no está condicionada (GUIA §3b, fila 4).** No se eligen pasadas porque el sistema las marcó:
entra toda pasada nocturna de los 11 volcanes en el tramo con fila de la referencia a ±120 s (F26) o con gránulo (R25),
y la etiqueta sale de la referencia, no de K ni de la vía. La única selección es la de la tabla misma: en F26 la tabla
expone menos gránulos VIIRS por noche que desde abril (1,6 a 1,8 contra 2,3 a 3,4, hito del 04-01), así que hay
pasadas nuestras sin fila (`sin_info`). Eso baja el denominador, no lo sesga hacia la vía ni hacia K, porque la tabla no
mira lo que publicamos. Se declara: **una tasa por pasada de VIIRS en F26 no se compara con una de abril en adelante**
(A119 b), sólo vía contra K sobre las mismas pasadas.

**Régimen (GUIA §3b, fila 10).** F26 y R25 son anteriores a #535 (2026-08-28) y a la adopción de K (2026-10-18), pero
los dos brazos se calculan hoy con un mismo código en todas las fechas, así que ninguna frontera de producción los
separa. K de disco se escribió con el reproceso #883 (octubre), ya con #535 y con K: consistente. Lo que sí cambia entre
tramos es la referencia (§4), y por eso todo se lee **por tramo**.

---

## 4. La referencia por tramo y su calidad

### 4.1 F26: la tabla de MIROVA, sola

- **Decide la tabla sola** (`calidad_referencia_mirova.etiqueta_que_decide("2026-02-01")`: antes del 2026-06-13 «SOLO
  la tabla; el OCR se informa aparte»). El OCR en F26 está en su peor tramo (siete versiones hasta el 03-01, geometría
  mal calibrada hasta el 06-11, sin distancia hasta el 06-13): una protegida sólo del OCR **no veta y no decide**; se
  lista por nombre con la cabecera de la imagen revisada (A61) y, si la vía la pierde y K la publica, lleva el veredicto
  a DECIDE NICOLÁS (como MOD-D fase 4 §5 y §7 fila 5). N-3 (Suomi NPP sólo OCR antes del 10-09) queda subsumida.
- Cobertura de la tabla en febrero: 98,2 a 99,6 % de las noches; desde marzo 99 a 100 % (hito del 03-01). No hay
  reparo de MODIS.
- **Referencia congelada** por sha256 antes del despacho: la unión histórica que carga
  `scripts/referencia_mirova_unificada.cargar_referencia_unificada` (consolidado de Mirova-v1 en un commit fijo, más el
  respaldo y la unión que conserva las filas que el consolidado remoto perdió; A119, D5 y D6 de S150). Recomendación:
  la misma que congeló MOD-D fase 4 (consolidado `cb91eb506c37cff0b83164dd602d8a5340277637`, OCR
  `cfc57c4d8bc57c5ccd5219ff3a91749dae167b97`, `PREREGISTRO_MODD_F4.md` l. 124 a 128), porque cubre F26 y DM y ya pasó
  por un verificador; si se toma una más nueva, se lista qué filas de F26 cambian.
- **Etiquetas** (las de `banco_paridad` y `scripts/clase_mirova.py`, sin cambio): `protegida` (lectura A: alerta de la
  tabla, VRP de la pasada de 1 MW o más recalculado del VRP, nunca de `Clasificacion Mirova`; `docs/MISSION.md` l. 92 a
  113), `bajo1`, `neg_limpio` (MIROVA miró y todas sus filas de la pasada son RUTINA), `far_ref` (MIROVA publicó la
  fuente como `FALSO_POSITIVO` y ninguna ALERTA), `sin_info`.
- **Regla D-9 (SN)** en VIIRS 375: una pasada cuyas alertas del scraper tienen todas 0,05 MW o menos, sin otra alerta
  mayor a menos de 120 s, cuenta como «MIROVA no vio nada» (`docs/MISSION.md` l. 119 a 131;
  `clase_mirova.aplicar_regla_minimas`). Decide SN; se informan SE, la regla original y el umbral 0,04, y se dice si
  algún veredicto cambia.

### 4.2 R25: el OSF v2.5 de MIROVA

**Qué es y qué no es (A105).** El OSF es la base reprocesada y filtrada de MIROVA: clase automática DBSCAN y umbrales de
VRP por sensor (Coppola et al. 2026, Scientific Data, Tabla 1 p. 8 y «Data aggregation» p. 7). **Sirve para sus alertas
y su magnitud; no sirve para contar publicaciones de más**, porque una pasada ausente del OSF puede ser una pasada que
el filtro sacó, no una en que MIROVA calló. Por eso en R25 no hay negativos limpios ni P2.

Hechos medidos para este borrador (archivo local `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, fuera de git,
sha256 `0863c2407eadd09722ccd98fd50c48eefdc871a4b68f843bd8478f94f5eb29da`; ojo: pese al nombre trae 2001 a 2025, 615.470
filas; conteo propio con pandas, sin el pareo sellado):
- 2.577 filas de los volcanes chilenos entre el 2025-02-15 y el 2025-12-31, de 10 volcanes (Tupungatito 0).
- **El piso de VRP del OSF depende del sensor**: el VRP mínimo de 2025 es 0,011 MW en 375 m, 0,176 MW en 1 km y
  **5,05 MW en 750 m**. O sea que en VIIRS 750 el OSF sólo trae pasadas de 5 MW o más: una «protegida OSF» de 750 es en
  la práctica de 5 MW o más, y las alertas de 1 a 5 MW de 750 son invisibles en R25. El plan no lo anotaba.
- `timeUTC` viene **truncado al minuto** (`dd/mm/aaaa hh:mm`). El pareo a ±120 s lo tolera si MIROVA usa la misma hora
  de gránulo; se mide la distribución de Δt de los pares antes de leer (control C-pareo, §6).
- `Dayflag` 0 en 47.907 de las 48.360 filas chilenas del archivo y con horas UTC de 01 a 07: muy probablemente 0 =
  noche, **SIN VERIFICAR** hasta leer la definición.
- Columnas según el esquema v2.5 (`experiments/_s172_chillan/auditor/schema_osf_v25_texto.txt`): `VRP` en **watts**;
  `LAT`/`LON` = píxel alertado más caliente; `Max_Dist` = distancia de la cumbre al píxel alertado **más lejano**, en
  **metros**; `class` 1 = detección volcánica, 0 = no volcánica; `SatZen` = cenit del satélite (lo usa §5.3).

**Regla del plan que se mantiene (A95):** ninguna columna se usa antes de leer su definición en Coppola et al. 2026
renderizando la página a imagen (`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`). El
esquema de texto ya da unidades y semántica de casi todas; falta confirmar `Dayflag` y la tabla de `Satellite`.

**Definiciones de R25** (se fijan aquí, antes de leer):
- **Pareo**: misma resolución (375 a VIIRS 375, 750 a VIIRS 750, 1000 a MODIS), ±120 s, mismo volcán.
- **Protegida OSF**: fila nocturna, `class` = 1, `VRP` ≥ 1e6 W, y el píxel más caliente (`LAT`, `LON`) a una distancia
  del cráter de `volcanoes.yaml` menor o igual que su `inner_radius_km` (decisión R-1 del §12: alternativa, `Max_Dist`).
  Conteo propio aproximado (distancia a las coordenadas de cumbre del OSF, no a las nuestras): **317 en 375 m** (273
  Láscar, 28 PCC, 14 Planchón-Peteroa, 2 Isluga), **17 en 750 m** (las 17 de Láscar, todas de 5 MW o más) y **162 en
  1 km** (155 Láscar, 6 Planchón-Peteroa, 1 Villarrica).
- **Bajo 1 MW OSF** (sólo 375 y 1 km, por el piso): informa, con la regla SN aplicada por analogía en 375.
- Las filas `class` = 0 de 1 MW o más (105 en 375 m, 9 en 1 km) son lo más parecido a un `FALSO_POSITIVO`: se listan
  aparte y, si la vía las publica como cumbre, se informa (análogo de E_lejana), sin decidir.

### 4.3 Independencia de la razón de magnitud contra el OSF

El plan dejaba la duda de si `WOOSTER_COEFF`, calibrado contra el OSF en S14, contamina la razón. Leído en
`pipeline/mirova_v750_codigo.py` (`origin/main`) l. 70 a 85: la vía de 750 usa el coeficiente del `.m` de MIROVA
(1,97e7 × 0,5625 km²); la de MODIS 1,89e7 × 1 km² y la de 375 1,80e7 × 0,140625 km², que son los de S14. Pero S14 no
ajustó ese número a nuestras detecciones: lo recuperó como la constante k·A que MIROVA usa, de `VRP / ΔL` en las propias
filas del OSF (el auditor de Chillán lo midió constante por sensor con error relativo 1,1e-8). Es la misma constante de
MIROVA, no un parámetro libre ajustado a la razón. Conclusión: **la razón vía/OSF es independiente de esa calibración en
el sentido que importa**; se declara y no se trata como contaminación.

---

## 5. Lecturas y criterios

Todo por pasada nocturna. «Publica» y «magnitud mostrada» = el predicado de `frontend/index.html` del tag, ejecutado
con node sobre el record que dejó `store.append_record` (`banco_paridad.correr_node`, A97). Bloque = noche-volcán.

### 5.1 Lectura A: la regla de adopción de cada sensor, aplicada fuera de muestra (decide)

Se reusa la regla escrita de cada sensor, en el ref donde está la versión vigente, **con un solo cambio declarado
para los tres: censo en vez de muestra**. Donde la regla usaba pesos de muestreo (V375-E §9.2, pesos `N_h / n_ok_h`),
aquí todo pesa 1, porque se corre la población entera. Ningún umbral cambia.

| sensor | regla | tramo que decide | brazo de posición que decide |
|---|---|---|---|
| MODIS | tabla de veredicto del §7 de `PREREGISTRO_MODD_F4.md` (l. 209 a 241, `25e3cc3ba`), con P1, P1b, P2, P2', M; sin las piezas que no aplican (identidad contra las grillas del censo, tramo E) | F26-M | VIA-radiante: es el que eligió la lectura de MOD-D («posición: V (ninguno gana contra V)», `leer_f4_salida.txt`); los otros dos informan |
| VIIRS 375 | §5.4 (a) a (d) de `PREREGISTRO_E.md` (l. 134 a 151 del tag `s170-v375e-lector`), con la regla N-3 del §8.13 (l. 503) y el código del §9.7 | F26-V | **VIA-cercano**: «cercano decide», decisión de Nicolás del 2026-10-30 (§10 del mismo archivo, l. 703 a 714); radiante y P-sinfiltro informan |
| VIIRS 750 | §6 punto 2 de `PREREGISTRO_V750A.md` (l. 217 a 242 de `aa5583646`), con §6 bis y §6 ter, si está sellado el día del sello de este documento; si no, ese texto copiado tal cual y sellado aquí, con la ROI que eligió V750-B ya en `pipeline/grillas_mirova.yaml` | F26-V | el que elija el §6 bis de V750-A en su censo si ya corrió; si no, **VIA-radiante** (lo que hace hoy `procesar_grilla`) y los otros dos informan |

Particularidades que se declaran antes de leer:
- **F26 decide con la tabla sola** en los tres. Donde la regla original pide además «tabla más OCR» (V750-A §6.2,
  «con la tabla sola **y** con tabla más OCR»), la rama con OCR se calcula e **informa**; una pérdida sólo OCR va a
  DECIDE NICOLÁS, no veta. Es la regla de A119 y la misma excepción de MOD-D fase 4 §5. Es una desviación de V750-A y se
  dice así.
- **V375-E §5.4 (d) (curva de cenit)** se lee con el nulo y los controles de su §4 (pares con menos de 5° de diferencia,
  ganancia pareja, ganancia que crece con el cenit). Si F26 no tiene 8 noches con pares, (d) queda SIN SUSTRATO y no
  bloquea por sí sola (la regla dice «o al menos»; la falta de sustrato se informa).
- **V750-A §6.2 M**: la banda [0,9; 1,1] de la razón sobre todas las protegidas que la vía publica **decide** en F26-V,
  porque así lo escribió V750-A (L4, D-48). En MODIS la banda informa (MOD-D §12 decisión 4). No se uniforma: cada
  sensor con su regla.
- **R25** sólo aporta **P1-OSF** (§5.2) y la magnitud (§5.3). Las reglas selladas no se aplican a R25 porque todas
  necesitan negativos limpios.

### 5.2 P1-OSF en R25 (decide sólo en una dirección)

Para cada protegida OSF (§4.2): ¿la vía la publica? ¿K la publica?
- La vía no y K sí: **candidata a veto**. Se diagnostica con el record (píxeles alertados, distancia, `via_codigo_mirova`)
  y la cabecera de la imagen si existe. Como el OSF no es el NRT, **no veta sola: lleva el sensor a DECIDE NICOLÁS**
  con la lista (plan §5, paso 4).
- Ni la vía ni K: se lista (informa).
- La vía sí y K no: se lista como recuperada (informa).
- Se informa el recall de protegidas OSF de la vía y de K por sensor, por volcán y **sin Láscar** (Simpson, GUIA §3b
  fila 13: Láscar es el 86 % de las protegidas OSF de 375 y el 96 % de las de 1 km).

### 5.3 Magnitud partida por cenit (informa; en F26-V y F26-M es además la M de cada regla)

**Por qué.** Hoy está medido, en Chillán, que la razón de K contra MIROVA cae con el cenit en los tres sensores
(Spearman −0,87 MODIS n 12, −0,50 VIIRS 375 n 53, −0,81 VIIRS 750 n 39, los tres fuera del rango barajado; cerca del
nadir 0,75 / 0,74 / 0,85, sobre 60° 0,08 / 0,33 / 0,11), confirmado por un verificador limpio con réplica fuera de
muestra del 27-oct al 1-nov (`experiments/_s172_chillan/auditor/INFORME.md` §2 y `verificador/INFORME.md` §2). Las vías
llevan Chillán cerca de 1 sin dependencia del cenit (MOD-D: Spearman +0,50 sobre los mismos 12, VCH172-05), pero eso es
dentro de muestra y sólo en Chillán. Y la caída no es toda nuestra: MIROVA también baja con el cenit (en 750, 0,503 de
la pasada más oblicua sobre la menos oblicua de la misma noche; programa §1 punto 6). **La meta es caer como MIROVA, no
aplanar la curva.**

**Qué se mide, por sensor y tramo (F26, R25):**
1. Razón vía/MIROVA y K/MIROVA por pasada pareada en que los dos publican con VRP mayor que 0: mediana con IC por
   bootstrap de noches, por tramo de 10° de cenit (cenit del record nuestro; en R25 se compara con `SatZen` del OSF,
   control C-cenit) y por volcán.
2. Spearman de la razón contra el cenit, con su rango de 200 barajados del cenit dentro de cada sensor (semilla 172),
   el mismo instrumento de `s03_estratos.py` del auditor de Chillán.
3. La razón doble dentro de la noche (pasada más oblicua sobre menos oblicua, la nuestra sobre la de MIROVA), con el
   veredicto del §5.3 de V375-E aplicado a los tres sensores: REPRODUCE LA CURVA si el IC de la mediana contiene 1 y la
   mediana está en [0,8; 1,25]; CAE MÁS QUE MIROVA si el IC queda entero bajo 1; CAE MENOS si queda entero sobre 1; NO
   RESUELTO en otro caso; SIN SUSTRATO con menos de 8 noches.
- **Predicción** (§9): la vía REPRODUCE LA CURVA o NO RESUELTO; K CAE MÁS QUE MIROVA en 375 y 750.
- **Límite declarado**: Chillán no erupcionaba en F26 ni en R25 (en R25 el OSF tiene 1 fila a menos de 5 km de su
  cráter, auditor de Chillán §4); la curva fuera de muestra es sobre todo la de Láscar. **La curva de Chillán no se
  puede probar fuera de muestra con este diseño.**

### 5.4 Lectura B: paridad absoluta contra MIROVA (informa, no decide)

Lo que Nicolás preguntó en sus palabras. Por sensor y tramo, de la vía y de K al lado, con numerador, denominador y
ventana:
- recall de protegidas (tabla en F26, OSF en R25) y lista nominal de las perdidas;
- recall bajo 1 MW (F26, con SN);
- tasa de publicación en negativos limpios con cota de Wilson (F26; no comparable con la de abril en adelante, §3);
- razón de magnitud (§5.3).

**No decide** porque no existe un umbral absoluto de «igual a MIROVA» que salga de los datos de MIROVA (MISSION punto 4,
A115): el criterio de victoria es relativo («ningún cambio que pierda una protegida»). Recomendación de lectura para
Nicolás (decisión R-6): llamar «a la par de MIROVA en ese sensor» sólo si la vía no pierde ninguna protegida que K
publica, su tasa en negativos limpios no supera la de K (cotas solapadas o menor) y su razón cumple la banda [0,8; 1,25]
de V375-E §5.3 (el único número sellado que ya existe para «se parece a MIROVA» en magnitud).

### 5.5 La noche del operador (informa)

- Noche protegida: noche-volcán con al menos una protegida de MIROVA en cualquier sensor. ¿El tablero publica algo en
  esa noche (algún sensor)? Vía contra K.
- Noche limpia: noche-volcán en que MIROVA miró en todos los sensores con dato y todas sus filas son RUTINA (con SN).
  ¿El tablero calla? Vía contra K.
- **Mismo número de oportunidades** (GUIA §3b fila 12): se compara la vía con K sobre las mismas pasadas de la noche;
  una noche con más pasadas no le da más chances a un brazo que al otro.

---

## 6. Controles (si uno cae, no se lee el veredicto de ese sensor)

| control | qué tiene que dar | si falla |
|---|---|---|
| **C-via** | en cada sensor y tramo, al menos 99 % de los records de VIA con `via_codigo_mirova` True; `sin_grilla`, `sin_mxd03` y `geo_distinta` contados aparte; un record sin la marca no entra al brazo VIA (V375-E adenda 1 punto 4) | INDECIDIBLE en ese sensor; se arregla el workflow y se repite el trozo |
| **C-cobertura** (A108) | pasadas de VIA contra K por volcán, día y sensor, antes de mirar nada. Las que faltan en VIA por la regla de cobertura de la vía (menos de 100 píxeles a 45 km o el más cercano a más de 5 km: `mirova_v750_codigo.py` l. 799 a 808, hallazgo 171-01, descarte sin record) se rotulan SIN DATO y salen del denominador de los dos brazos. **Una protegida SIN DATO que K publica veta** (como `leer_sombra_v375e.py` l. 573, tag `s170-v375e-lector`). Más de 10 % SIN DATO en una clase que decide: cae (como su `UMBRAL_COBERTURA`, l. 85). Toda alerta o bajo 1 MW de la tabla sin pasada nuestra a ±120 s se lista | trozos cortados por NASA (`SEARCH_CMR_TIMEOUT`, A64) se repiten una vez con la misma ventana; si sigue, SIN DATO en la primera línea |
| **C-K** | K-gemelo contra K de disco en DM y en Láscar-F26: misma publicación y `pc.vrp_mw` a 0,001 MW en al menos 99 % de las pasadas y en todas las protegidas (la tolerancia de V750-A §7, L18) | K de disco no sirve: INDECIDIBLE hasta correr K entero con el código del tag |
| **C-montaje** | en DM la vía reproduce, pasada por pasada, lo que midieron los A/B dentro de muestra donde el código es el mismo: V de MOD-D fase 4 (máscara, VRP a 0,001 MW, clase), la vía de V375-E (lectura lejana) y el brazo de V750-B con la ROI elegida (banda de triangulación de V750-A §4.1). Antes de correr se lista `git diff` del código de la vía entre cada tag y el del despacho, y las diferencias esperadas se escriben **antes** | se explica cada diferencia antes de leer F26 y R25; una no explicada deja todo INDECIDIBLE |
| **C-pareo** | Δt de los pares de R25 (OSF truncado al minuto): ninguno fuera de ±120 s y ninguna protegida OSF pareada a dos pasadas nuestras | se revisa el pareo; no se ensancha la ventana después de ver |
| **C-cenit** | en R25, \|cenit nuestro − `SatZen`\| ≤ 2° en los pares (el auditor de Chillán midió 1,6° máximo) | la curva de R25 no se lee |
| **PLACEBO** | K × 1,2: P1 y P2 sin discordancias salvo las que explican los filtros del tablero que miran la magnitud (`isCirrusArtifact`, `isDiffuseFieldArtifact`, tope de 50.000 MW; nota L7 de V750-A §7); M no puede dar MEJORA | el instrumento está roto |
| **Nulo de runner** | K-gemelo contra K de disco: P2 EMPATE o SIN SUSTRATO, M sin separación (mide la inestabilidad de `argsort` entre CPU de S152) | idem |
| **Nulo del lector** | el lector corrido sobre K contra K da 0 diferencias; una mutación que pierde una protegida da veto; 50 negativos con un cúmulo de cumbre inyectado suben P2 en 50 (contador de MOD-D §8.5) | el lector no sale |
| **Controles de cenit** | los de V375-E §4: nulo de pares a menos de 5° que contiene 1; ganancia pareja que no mueve la razón doble; ganancia que crece con el cenit que la sube | la curva no se lee |
| **Candado** | sha256 de cada archivo del lector, de las dos referencias y de `frontend/index.html` contra el manifiesto del sello, comprobado **antes** de correr (lección S171) | no se corre |

Preguntas del instrumento (GUIA §3): (1) si la vía no corriera, C-via da 0 % y lo ve; si el lector estuviera roto, el
nulo del lector y el placebo lo ven. (2) Si los artefactos estuvieran vacíos, C-cobertura da 0 pasadas contra miles de
K y cae. **Un vigilante ciego da verde**: por eso C-via y C-cobertura se imprimen por trozo en el log del runner (paso
de `controles_via.py`, plan Tarea 0.2 paso 7) y otra vez en la lectura.

---

## 7. Poder (antes de leer)

**P1 con «cero perdidas».** Que la vía no pierda ninguna de n protegidas sólo descarta tasas de pérdida altas. Cota
superior al 95 % de la tasa de pérdida compatible con 0 de n (regla del tres, 3/n), con conteos propios aproximados de
la referencia (sin pareo, sin SN, noche aproximada como 00 a 11 UTC en la tabla):

| tramo y sensor | protegidas (aprox.) | volcanes | cota de pérdida con 0 perdidas |
|---|---|---|---|
| F26-M (febrero) | 7 | Láscar 7 | 43 % |
| F26-V, VIIRS 375 | 25 | Láscar 25 | 12 % |
| F26-V, VIIRS 750 | 30 | Láscar 29, Isluga 1 | 10 % |
| R25, 1 km | 162 | Láscar 155 | 1,9 % |
| R25, 375 m | 317 | Láscar 273 | 0,9 % |
| R25, 750 m (sólo 5 MW o más) | 17 | Láscar 17 | 18 % |

Consecuencias que se escriben ahora: **MODIS tiene casi todo su poder en R25** (contra el OSF, que no veta solo), y
**VIIRS 750 tiene poco en los dos tramos**. Casi toda la evidencia de P1 fuera de muestra es de Láscar: un «sin
pérdidas» dice poco de los volcanes de señal débil. (El plan citaba 34 y 30 alertas de 1 MW o más en VIIRS 375 y 750
para febrero y marzo; eran filas de día y noche. De noche son 25 y 30.)

**P2 (signos por bloque).** Bajo 1 MW de la tabla, de noche y aprox.: VIIRS 375 174 alertas en febrero y marzo (antes de
SN, que saca las de 0,05 MW o menos), VIIRS 750 23, MODIS de febrero 5; negativos limpios del orden de 370 a 640 pasadas
RUTINA por sensor y mes. El número que importa es el de **bloques noche-volcán donde los errores de la vía y de K
difieren**, y ése sólo se conoce con los datos. Se declara: con 4 bloques o menos, SIN SUSTRATO (D-45); el sorteo de
etiquetas dentro de cada estrato (volcán × tramo de cenit) se corre sobre K contra K antes de leer, para saber qué
fracción de barajados cumple «GANA o EMPATE» por azar (GUIA §3b fila 7).

**Antes del sello**, con la referencia congelada y `banco_paridad` (sin mirar la vía, que no existe todavía): se
recalculan todos estos conteos por tramo, sensor y volcán, con pareo a ±120 s, SN y N-3, y se escriben en el §7 del
documento sellado. Si F26-M queda con 4 bloques o menos, MODIS sólo puede salir con P1 y con R25.

---

## 8. Veredictos y sus nombres (por sensor)

Primera fila que se cumpla, sobre el brazo de posición que decide (§5.1):

| orden | condición | nombre del veredicto | qué promete |
|---|---|---|---|
| 1 | algún control del §6 en rojo para ese sensor | **INDECIDIBLE (CONTROLES)** | nada |
| 2 | en F26 la vía pierde una protegida de la tabla que K publica (incluida una SIN DATO que K publica) | **NO SE SOSTIENE FUERA DE MUESTRA: PIERDE PROTEGIDA** | que la regla de adopción falla en pasadas nuevas |
| 3 | la regla sellada del sensor da NO ADOPTAR o «no cumple» por P2 PIERDE (o, en 750, por M fuera de banda) en F26 | **NO SE SOSTIENE FUERA DE MUESTRA: PEOR QUE K** | idem, en lo débil o en magnitud |
| 4 | la regla da SIN SUSTRATO en F26 y R25 no tiene candidatas a veto | **SIN PODER FUERA DE MUESTRA** | que la retrospectiva no alcanza para ese sensor; no dice que falle |
| 5 | la regla da DECIDE NICOLÁS, o hay candidatas a veto en P1-OSF, o una pérdida sólo OCR, o la curva da CAE MÁS QUE MIROVA en la vía | **DECIDE NICOLÁS** (con la lista) | nada por sí solo |
| 6 | la regla da PROPONER ADOPCIÓN / cumple, y P1-OSF sin candidatas a veto | **LA ADOPCIÓN SE SOSTIENE FUERA DE MUESTRA** | que en febrero y marzo de 2026 y en 2025 la vía no pierde protegidas que K publica, no se equivoca más que K en lo débil y su magnitud pasa la regla de su sensor; **no** que el sistema publique igual que MIROVA en noviembre (eso es la sombra) ni nada fuera de los 11 volcanes |

**Qué abre cada uno** (plan §5, Compuerta A, que decide Nicolás): con LA ADOPCIÓN SE SOSTIENE FUERA DE MUESTRA en los
tres sensores y controles en verde, la recomendación es abrir la sombra de los 34. Con NO SE SOSTIENE en cualquier
sensor, no se abre para ninguno (plan: los 34 van con los tres sensores o con ninguno) y el sensor vuelve a su A/B con
la lista de pasadas en la mano. Con SIN PODER o DECIDE NICOLÁS, decide Nicolás con la lectura B (§5.4) delante. Ningún
resultado de esta prueba cambia lo que publica producción ni reemplaza la parada de una sombra.

---

## 9. Predicciones (para poder fallar)

Escritas con lo que se sabe dentro de muestra; si F26 o R25 las contradicen, esa es la información:
1. VIIRS 375 (cercano): P1 0 pérdidas que vetan en F26; P2 GANA o EMPATE; razón vía/MIROVA en [0,9; 1,1]; curva
   REPRODUCE o NO RESUELTO; K/MIROVA alrededor de 0,6 a 0,7.
2. VIIRS 750: P1 0 en F26; razón de la vía en [0,9; 1,1]; K bajo 0,8. Poco poder para P2.
3. MODIS (febrero): P1 0; P2 GANA o SIN SUSTRATO; R25 sin candidatas a veto en 1 km; razón vía/OSF cerca de 1 y K/OSF
   cerca de 0,5 en Láscar (MOD-D llevó Láscar de la mitad de MIROVA a la de MIROVA).
4. Verano: menos publicaciones de K en negativos limpios de volcanes nevados que en invierno (menos gradiente
   topográfico, A69); si la vía gana menos en F26 que dentro de muestra, eso es esperable y no es falla.
5. En R25, la razón de K por cenit cae como en Chillán (Spearman negativo fuera del barajado) y la de la vía no cae más
   que la de MIROVA.

---

## 10. Perfil aislado, workflow, trozos y costo

### 10.1 Perfiles

**`extends` resuelve un solo nivel**: `pipeline/profile.py` l. 51 a 67 (`origin/main` `14fb62030`) saca la clave
`extends` del hijo, lee el YAML del padre y mezcla; si el padre tiene a su vez `extends`, esa clave queda como dato y no
se resuelve. Por eso los dos perfiles extienden `mirova_equivalent` directamente y repiten los flags.

**Riesgo de herencia (VR172-02, `tasks/LOOP_OBJETIVOS.md` entrada del 2026-11-02 00:03):** si producción enciende la vía
de MODIS (PR de S172 en preparación) o los flags de MxD03, los perfiles que extienden `mirova_equivalent` los heredan
en silencio. Por eso aquí **todo flag que define los brazos va escrito**, también los que hoy coinciden con producción:

- `_s172_retro_paquete.yaml`: el de la Tarea 0.2 del plan, más `enable_modis_geo_mxd03: false`,
  `enable_modis_crater_sin_dato: false` y `enable_modis_dist_desde_crater: false` en `thresholds:` (la vía de MODIS
  sellada lee su propio MxD03 con esos tres apagados, MOD-D fase 4 §2). Carpeta `_s172_retro_paquete`.
- `_s172_retro_k.yaml`: lo mismo con las tres vías en `false`. Carpeta `_s172_retro_k`.
- Prueba (además de la del plan, que compara contra la sombra): que los dos perfiles resuelven los tres flags de las
  vías y los tres de MxD03 al valor escrito aquí **aunque `mirova_equivalent` los cambie** (se prueba con un padre
  mutado en un directorio temporal). Roja antes, verde después.
- Ninguno de los dos marca régimen en el lector de V375-E (perfiles nuevos, plan H9); el re-sellado por claves de S172
  no los lista. Comprobarlo con su batería antes del merge.

### 10.2 Workflow

`reproc-retro-paquete.yml` según el plan (Tarea 0.2 paso 6: `pyproj` instalado, sólo `EARTHDATA_TOKEN` con corte
inmediato si viene vacío, sin job `merge`, artifacts con `retention-days: 30`, `"on":` entre comillas, `ubuntu-24.04`,
grupo propio, `controles_via.py` por trozo), con dos cambios a lo que el plan proponía:
- **`max_days` de 20, no el 37 por defecto.** En el precedente del reproceso de K (run 39125546355, 2025-02-15 a
  2026-09-17, 176 trozos de ~36 días) el trozo tuvo mediana 80 min, **p95 160 min y máximo 172 min** contra un paso de
  170 min, y 6 de 176 jobs fallaron (conteo propio con la API, 2026-11-02). Con la vía a 1,06 a 1,25 veces K el p95
  pasaría el límite. Con 20 días: p95 estimado de 95 a 115 min.
- El nombre del perfil va en el input; el workflow rehúsa cualquier perfil que no empiece por `_s172_retro_`.

### 10.3 Despachos (de a uno, cada uno desde un tag, después de V750-B)

| despacho | perfil | volcanes | ventanas | trozos de 20 días | jobs | cuándo |
|---|---|---|---|---|---|---|
| D1 humo | `_s172_retro_paquete` | Láscar | 2025-06-15, 2026-02-10, 2026-10-05 (un día cada uno) | 3 | 3 | tras el merge del perfil y el workflow |
| D2 tanda 1 | `_s172_retro_paquete` | 11 | F26 (59 días) y DM (16 días) | 3 + 1 | 44 | el día del merge de `roi_v750` o el siguiente |
| D3 control K | `_s172_retro_k` | 11 en DM; Láscar en F26 | DM y F26 | 1 por volcán en DM, 3 en Láscar | 14 | justo después de D2 |
| D4 tanda 2 | `_s172_retro_paquete` | 11 | R25 (320 días) | 16 | 176 | justo después de D3 |

Matriz de 176 jobs: bajo el tope de 256 de GitHub. Cada despacho desde un tag puesto sobre el `main` que contiene el
perfil, el workflow y `roi_v750` (`s172-retro-d2`, etc.; lección S152: dos pipelines distintos en un A/B). MODIS sólo
corre en Linux: todo va en el runner, nada local. `max-parallel: 6` (en la franja del NRT, 01 a 12 UTC: NRT 8 + 6 = 14
jobs; si coinciden la sombra y la experimental, 22, sobre el tope de 20 si el plan es Free, SIN DATO: preferir
despachar D4 fuera de 01 a 12 UTC o bajar a 4 si coinciden).

### 10.4 Costo

Tasa medida de K: **2,39 min de runner por volcán-día** con sobrecarga incluida (run 39125546355: 254,2 h de runner en
176 jobs para 580 días × 11 volcanes; pared 32,3 h con `max-parallel: 8`). Factor de la vía: **1,06 a 1,25** (SIN DATO;
cota de `experiments/_s172_capacidad_nrt/INFORME.md` §4, que el humo D1 y la sombra del 11-03 miden). O sea 2,5 a 3,0
min por volcán-día.

| despacho | volcán-día | horas de runner | pared con 6 en paralelo |
|---|---|---|---|
| D1 | 3 | < 0,5 | < 1 h |
| D2 | 825 | 35 a 41 | 6 a 7,5 h |
| D3 | 235 | 9 a 10 (K, sin factor) | 1,5 a 2 h |
| D4 | 3.520 | 147 a 176 | 24 a 29 h (18 a 22 h con 8) |
| total | 4.583 | 191 a 228 | 32 a 40 h |

Descargas a LAADS: el grueso es D4 (2025 sólo en el producto estándar). Ninguna tanda puede cruzar la rotación del
token del **2026-11-27** (vence 2026-12-07 18:03): con el calendario de abajo no la cruza.

**Calendario (UTC, estimado):** 11-02 a 11-05 sello de este documento, lector, perfiles y workflow (PR con tag y
frase de merge); 11-03 V750-B (solo, ~2 h); ~11-04 a 11-06 lectura de V750-B y merge de `roi_v750`; D1 el mismo día;
D2 y D3 ~11-06 a 11-07; D4 ~11-07 a 11-09; lectura, verificador limpio de otro modelo e informe ~11-10 a 11-12.

**Alternativa para adelantar MODIS y VIIRS 375 tres o cuatro días (decisión R-4):** un perfil con
`sensors: {viirs_750: false}` despachado sobre F26 y DM apenas termine V750-B, y VIIRS 750 sobre F26 y DM tras el merge
de `roi_v750`. Costo: el apagado de un sensor salta su proceso pero **no su descarga** (`scripts/run_pipeline.py` l. 217
a 235: `fetch_for_volcano` baja todas las plataformas antes de filtrar), así que la segunda pasada vuelve a bajar todo:
+30 a 40 h de runner. R25 iría siempre en un solo despacho con los tres.

---

## 11. Candado (antes del despacho; sin esto no se despacha)

- Manifiesto con sha256 de: el lector `leer_retro.py` y lo que importa (funciones de `evaluar_f4.py` del candado de
  MOD-D, `evaluar.py` de V375-E con sha256 LF `2126b743…`, el analizador de V750-A, `evaluar_d25.py` blob `1dbabf65`,
  `scripts/clase_mirova.py`, `scripts/banco_paridad.py`, `scripts/referencia_mirova_unificada.py`), las dos referencias
  congeladas, el OSF (`0863c240…`), `frontend/index.html` del tag y los dos perfiles.
- El lector se escribe con TDD (rojo antes de verde, anotado en el commit), batería de escenarios sintéticos, mutaciones
  atrapadas **por aserción** con control de caída (GUIA §3), y verificador limpio de otro modelo sobre el lector y sobre
  este documento.
- `git diff <commit del sello> -- PREREGISTRO_RETRO_PAQUETE.md` vacío al leer; todo lo agregado después va rotulado
  *post hoc*.
- Los conteos del §7 recalculados y escritos.

---

## 12. Qué decide Nicolás (con recomendación)

| # | pregunta | recomendación | por qué |
|---|---|---|---|
| R-1 | Protegida OSF: ¿distancia del píxel más caliente (`LAT`/`LON`) o `Max_Dist`? | **Píxel más caliente**; `Max_Dist` se informa | `Max_Dist` mide al píxel más lejano: un cúmulo de cráter con una cola larga quedaría fuera; el más caliente es lo más parecido a la distancia que MIROVA publica en el NRT |
| R-2 | K: ¿de disco con control (K-gemelo en DM y Láscar-F26) o re-corrido entero? | **De disco con control** (D3, ~10 h) | ya hay dos mediciones de K re-corrido = publicado; correr K entero suma ~180 h |
| R-3 | Posición de VIIRS 750 si V750-A no ha elegido al sellar | **Radiante decide**, cercano y pico informan | es lo que hace hoy la vía; a igual evidencia no se cambia (V750-A §6 bis) |
| R-4 | ¿Partir la tanda 1 por sensor para adelantar MODIS y VIIRS 375? | **No**, salvo que quieras esos dos sensores antes del 11-06 | ahorra 3 a 4 días en dos sensores a cambio de 30 a 40 h de runner y un despacho más que vigilar |
| R-5 | ¿El OSF puede vetar solo? | **No: lleva a DECIDE NICOLÁS** | no es el NRT y está filtrado (A105) |
| R-6 | ¿Con qué lectura B se dice «a la par de MIROVA» en un sensor? | la del §5.4 | es la única forma de decirlo con números que ya existen (V375-E §5.3) sin inventar umbrales (A115) |
| R-7 | Banda de magnitud de V750-A [0,9; 1,1]: ¿decide en F26-V como en V750-A? | **Sí** (no se toca la regla) | cambiarla al leer otra ventana sería el error de A95 |
| R-8 | ¿Febrero y marzo de MODIS? | **Febrero decide, marzo control** | marzo es tramo C de MOD-D |
| R-9 | Tupungatito en F26 | **desde el 2026-02-23** | antes la tabla no lo tiene o rotula con 5 km |
| R-10 | ¿La lectura de la noche (§5.5) decide? | **No, informa** | las reglas y el criterio de victoria son por pasada y sensor; si quieres que decida, hay que escribirlo antes del sello |

---

## 13. Premisas del encargo y del plan que no se sostienen al leer (con archivo:línea)

1. **Las copias de los pre-registros que hay en `main` y en `loop/activo` son viejas.** `experiments/_s162_v375/PREREGISTRO_E.md`
   tiene 143 líneas y dice «BORRADOR, sin sellar» en `origin/main` y `loop/activo`; la versión sellada (cuerpo y
   adendas, con el §5.4 en l. 134 y «cercano decide» en l. 703 a 714) vive sólo en los tags `s168-v375e-cuerpo-sellado`
   y `s170-v375e-lector` y en la rama `claude/s172-v375e-relector`. Lo mismo con V750-B (277 líneas en `main`, 660 en
   el tag `s167-v750b-adenda3-sellada`) y V750-A (182 en `main`, 341 en `aa5583646` de `claude/s162-viirs750-2-918174`,
   todavía BORRADOR). El plan cita «§5.4 de `experiments/_s162_v375/PREREGISTRO_E.md`» sin ref: hay que citar el tag.
2. **El OSF de 750 tiene piso de 5,05 MW** (§4.2): «protegida OSF» de 750 no es «1 MW o más» sino «5 MW o más». El
   plan (H3, Tarea 0.1 paso 4) no lo dice.
3. **NOAA-21 no está en la tabla antes del 2026-04-09** ni en el OSF de 2025: sus pasadas de F26 y R25 no se pueden
   juzgar. El plan no lo menciona.
4. **Conteos de poder de F26** del plan (34 y 30 alertas de 1 MW o más en VIIRS 375 y 750) mezclan día y noche; de noche
   son unas 25 y 30, casi todas de Láscar (§7).
5. **El tamaño de trozo por defecto (37 días) no alcanza** con la vía: el precedente de K ya tuvo p95 de 160 min contra
   170 (§10.2). El plan estimaba la tanda 1 en 4 a 7 h con 1,8 a 3,2 min por volcán-día; la tasa medida de K con
   sobrecarga es 2,39, y con la vía 2,5 a 3,0.
6. **La prueba del perfil del plan no ve la herencia de MxD03**: compara contra la sombra, que tampoco los fija; si
   producción enciende MxD03, los dos cambian juntos y la prueba sigue verde (§10.1).
7. **Los records VIIRS que la vía descarta sin record** (171-01) no aparecen en C-via, que cuenta records: los atrapa
   sólo C-cobertura contra K (§6).

---

## 14. Lo que este pre-registro no hace

No corre nada, no crea perfiles ni workflow (eso es la Tarea 0.2 del plan, con tag `pre-s172-retro-paquete` y frase de
merge), no toca `pipeline/`, `nrt.yml`, `volcanoes.yaml`, `grillas_mirova.yaml` ni la sombra. No mide el día. No mide
Chillán en erupción. No mide los 34. No adopta nada: cualquier encendido sigue pidiendo su A45.

---

## Dudas abiertas (cortas)

1. ¿`Dayflag` 0 = noche y qué satélite es cada código de `Satellite` en el OSF? Leer Coppola et al. 2026 renderizado
   antes del sello.
2. ¿V750-A se sella antes que este documento? Si no, este documento copia su §6 y lo sella; conviene que lo diga la
   sesión de VIIRS 750 para no tener dos versiones selladas del mismo texto.
3. ¿El lector de la sombra de VIIRS 750 marca régimen con perfiles nuevos? (plan §14, SIN DATO).
4. ¿El fetch de 2025 encuentra NOAA-20 y Suomi NPP estándar completos y MxD03 en todos los días? Lo dice el humo D1 sólo
   para un día; C-cobertura lo dice entero.
5. ¿Qué referencia congelada se usa: la de MOD-D fase 4 (2026-10-27) o una más nueva? Para F26 no debería cambiar nada,
   pero hay que listarlo (A119, el consolidado pierde filas).
6. Plan de la cuenta de GitHub (tope de 20 jobs): SIN DATO; decide si D4 puede ir con 8 en paralelo.
