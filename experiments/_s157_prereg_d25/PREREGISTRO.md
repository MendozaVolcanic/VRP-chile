# Pre-registro S157 (tarea 1.29): D25, fondo por vecinos, sobre K, con Nevados de Chillán como caso

Estado: **BORRADOR PARA EL SELLO DE NICOLÁS.** Nada de esto se despacha sin su «sí» escrito y sin el candado del §7
(evaluador con sus pruebas y verificador limpio). Escrito el 2026-10-20 por una sesión lateral del loop, antes de
correr ningún brazo. Los números de sustrato salen de `sustrato_k.py` (`sustrato_k_salida.txt`, regla S91); los de
Chillán, del PR #869 (`experiments/_s157_magnitud_chillan/`, rama `s157-magnitud-chillan`, verificador PARCIAL) y de
la tarea 1.14 (`experiments/_s151_presupuesto_magnitud/README.md` §3.2 y §3.4). El resumen para sellar está en
`RESUMEN_SELLO.md`. El probe del L1B que informa las decisiones de §8 está en `probe_l1b/`.

## 1. La pregunta, y por qué ahora

**El fenómeno.** De noche, en un cono nevado, el anillo de 5 a 25 km alrededor del volcán es sobre todo valle más
tibio que la cumbre. Nuestro pipeline resta como fondo la **mediana de ese anillo**; MIROVA (Coppola 2016a, p. 8,
ec. 6, y siete textos más del grupo, D25) resta la **media de los vecinos no alertados** del píxel caliente. Cuando el
entorno inmediato del cráter está más frío que el anillo, restamos de más: la magnitud sale baja y, si el foco es
débil, el exceso queda negativo y se recorta a 0,0 MW. Cuando el entorno está más tibio (glaciar de Tupungatito al
revés, Lastarria con su campo fumarólico), restamos de menos.

**Por qué ahora.** Con K la réplica ya calla donde MIROVA calla (adopción de S153, #850), y lo que falta es la
magnitud, sobre todo con el sensor oblicuo. En Chillán en erupción nuestra razón contra MIROVA cae con el cenit del
sensor: VIIRS 375 0,73 bajo 30°, 0,58 entre 30 y 50°, 0,45 sobre 50°; VIIRS 750 0,84, 0,41 y 0,16 (PR #869, §2.2).
De las palancas ya construidas, D25 es la que más mueve la magnitud hacia MIROVA (×1,28 [1,21; 1,35] en 468 pasadas
de VIIRS 375) y su efecto crece con el ángulo (×1,18 a nadir, ×1,41 en el borde; tarea 1.14, Tabla C2), pero se
midió dentro del brazo `literal` y sobre la detección anterior a K. Nunca se midió aislado ni sobre K.

**Lo que ya se sabe y acota la pregunta** (PR #869, verificado PARCIAL): en VIIRS 375 oblicuo D25 **no puede**
cerrar el déficit de Chillán por construcción, porque ni restando un fondo cero se llega a MIROVA (techo 0,64 a
0,68 sobre 40°). En VIIRS 750 y MODIS sí podría (techo 0,96 a 1,48). Por eso el criterio de magnitud no se pone en
VIIRS 375 oblicuo (§5).

**Lo que este A/B NO pregunta.** Si el resto del déficit angular es área del píxel (D17, tarea 1.36), selección de
vecinos (A99, A103) o el recorte del tablero en VIIRS 750 (tarea 1.8). D17 va después, sólo si queda dependencia con
el cenit.

## 2. Brazos, y por qué cada uno

| brazo | perfil | qué es | por qué está |
|---|---|---|---|
| K | `_s157_ab_d25_k_control` | la réplica K tal cual, sin MODIS | control: las pérdidas y la magnitud se cuentan contra lo que hoy se publica |
| K' | `_s157_ab_d25_k_gemelo` | K corrido otra vez | el ruido del runner (desempates que dependen de la CPU, S152): sin gemelo no se separa un efecto de D25 de una pasada que cambia sola |
| D | `_s157_ab_d25_k_on` | K más `enable_vrp_bg_neighbor_mean_viirs375` y `_viirs750`, ventana hasta 7x7 | la palanca, con el valor del perfil |
| D1 (opcional, §8 b) | `_s157_ab_d25_k_on_h1` | D con sólo los 8 vecinos | la mitad abierta de la decisión de S142 (1 contra 3) |

`tests/test_perfiles_d25_k_s157.py` resuelve todas las constantes de `pipeline.profile` (A89) y comprueba: K es
producción salvo nombre, directorio y MODIS apagado; K' es K salvo nombre y directorio; D es K salvo los dos flags de
D25; D1 es D salvo la ventana. Las dos mutaciones probadas al escribirla (sacar el flag de VIIRS 750 de D, sacar
`SENSOR_MODIS` de la línea `FLAGS_BRAZO`) hacen fallar la prueba por la aserción que corresponde.

**MODIS va apagado en los cuatro brazos, y queda FUERA del A/B.** D25 no existe en `process_modis`: ningún flag lo
lee (`grep` de `ENABLE_VRP_BG_NEIGHBOR` en `pipeline/process_modis.py`: 0). MODIS sólo tiene el kernel local 3x3 en
temperatura, opt-in para 5 volcanes (Chillán no está). El PR #869 pedía el criterio de magnitud «en VIIRS 750 y
MODIS»; en MODIS no hay palanca que medir sin tocar `pipeline/` con su ciclo A45. Lo que sí se mide sin tocar el
código es el análogo en el probe del L1B (`probe_l1b/`, brazos `kernel3` y `d25_rad` sobre las dos pasadas MODIS de
Chillán del 18-oct), y eso informa si vale la pena escribir el flag (decisión §8 c).

## 3. Dónde llega el flag (A118): consumidores del fondo y de la magnitud

D25 cambia el VRP de cada píxel alertado **después** de que la máscara de alertados quedó fija, así que no cambia qué
píxeles se detectan. Pero la magnitud por píxel tiene más consumidores que la suma, y cada uno puede mover lo que el
tablero publica. Leído en el código de `origin/main` 8c94c847b:

| consumidor | recibe el fondo de D25 | qué puede cambiar | cómo lo ve el evaluador |
|---|---|---|---|
| VRP por píxel del bloque contextual (`process_viirs.py:1492`, `process_viirs_mod.py:1047`) | sí | la magnitud | métrica M |
| selección del cúmulo (`cluster_hotspots(..., vrp_per_pixel=...)`) | sí | **qué cúmulo es el primario** si hay más de uno en el inner | P4 (el cúmulo se mueve) |
| keep_peak y núcleo F5' (store.py desde `anomaly_pixels`) | sí | el píxel ancla del núcleo de VIIRS 375 | M y P4 |
| modo de un píxel (`apply_single_pixel_mode`, umbral de magnitud del cúmulo) | sí | si el cúmulo se informa como suma o como su píxel mayor: un salto no lineal | M; se cuenta aparte cuántas pasadas cambian de modo |
| tope D9 de 5 MW (camino D solo, fondo bajo 270 K) | sí, se aplica después | **esconde** el alza de D25 en escenas frías | se cuenta `d9_capped` en D contra K |
| filtros del tablero `isCirrusArtifact` (más de 10 MW con píxel bajo 0 °C) e `isDiffuseFieldArtifact` | sí (leen la magnitud) | **apagan** una publicación que D25 subió sobre su umbral, calibrado con el fondo del anillo | P1 y P2 vía el predicado con node (A97); se listan las apagadas por filtro |
| recomputes del Test 1 (`process_viirs.py:1958`, `:1989`; `process_viirs_mod.py:1278`, `:1302`) | sí | nada: el Test 1 está apagado en K | huella: 0 `triggered_test1` |
| `vrp_vent_mw` (camino del vent) | **no** (anillo) | nada en el tablero bajo K | no se mide |
| MODIS | **no existe** | nada | fuera del A/B (§2) |

## 4. Ventanas, por tramo de calidad de la referencia (A119)

Los tres brazos corren el mismo código desde un tag (§6), así que la frontera de #535 (A104) no separa regímenes de
código entre brazos; lo que sí manda es la calidad de la referencia. Se reusan las ventanas de F/K, con V1 estirada
hasta el 18-oct para meter la mañana de Chillán que motivó esto.

- **V1, 2026-08-29 a 2026-10-18** (51 días). Decide la tabla y el OCR. Trae a Chillán en erupción desde el 28-sep.
  Pisa los hitos del OCR de Suomi NPP (hasta el 2026-10-09 la distancia y la clase de una fila sólo OCR pueden ser de
  otra pasada): esas pasadas no deciden con la lectura A, se listan; y el del 2026-10-10 (`ALERTA_SIN_GEOMETRIA_OCR`):
  estrato aparte, no son alerta de la lectura A, sí sirven para magnitud y se informan aparte. Referencia congelada
  en `_congelado_v1/` (Mirova-v1@`35a5ea86`, 2026-10-20 10:29 UTC, con las dos capas del repo; `congelar.py`, copia
  sin cambios del de F/K). **Con gemelo.**
- **V2, 2026-04-01 a 2026-06-12** (73 días, el poder del veto, sobre todo Láscar). Decide **la tabla sola**: el
  evaluador reetiqueta de verdad sacando las filas del OCR (S150, H7). VIIRS por pasada desde abril (A119 b). Pisa el
  hito de NOAA-21 del 2026-04-09 (inocuo: `sin_info` igual en todos los brazos, como en F/K). Referencia: la
  congelada de F/K (`experiments/_s151_prereg_fk_11/_congelado_v2/`), misma ventana. Se despacha en dos mitades,
  **V2a 04-01 a 05-07** y **V2b 05-08 a 06-12**. Sin gemelo: las pérdidas que caigan acá se resuelven con la
  repetición dirigida de F/K (§5 de su pre-registro).
- **Chillán** no tiene K en disco antes del 2026-09-18 (su histórico con K se está rearmando), así que en el sustrato
  entra sólo desde esa fecha. En el A/B los brazos lo reprocesan entero, en las dos ventanas.

**Sustrato con K, medido en disco** (`sustrato_k_salida.txt`; controles C1, C2, C3 y CK en verde):

| | V1 VIIRS 375 | V1 VIIRS 750 | V2 VIIRS 375 | V2 VIIRS 750 |
|---|---|---|---|---|
| protegidas A que K publica (veto) | 38 | 31 | 38 | 42 |
| fracción de pérdida detectable al 80 % | 4,1 % | 5,1 % | 4,1 % | 3,8 % |
| alertas bajo 1 MW / las que K publica | 279 / 259 | 38 / 21 | 385 / 362 | 75 / 49 |
| negativos limpios / los que K publica | 945 / 23 | 1.497 / 14 | 871 / 36 | 1.635 / 20 |
| **cúmulos del cráter en 0,0 MW en negativos (lo que D25 puede ENCENDER)** | **0** | **17** | **2** | **21** |
| ídem en alertas (lo que D25 puede RECUPERAR) | 4 | 11 | 6 | 23 |
| pares publicados con VRP de MIROVA, cenit ≤ 40° / > 40° | 166 / 131 | 29 / 23 | 211 / 189 | 64 / 27 |
| razón mediana con K, cenit ≤ 40° / > 40° | 0,72 / 0,52 | 0,66 / 0,35 | 0,73 / 0,56 | 0,54 / 0,51 |

**La lectura que cambia respecto de S151.** Con la detección vieja (C0), D25 en VIIRS 750 encendía 268 de 268
negativos limpios con el cráter en cero (`experiments/_s151_d25_v750_disco/README.md`), y su cierre quedó condicionado
a la detección. Con K esa población es de **17 y 21 pasadas en VIIRS 750 y de 0 y 2 en VIIRS 375**: K ya no deja
cúmulos mudos en el cráter donde MIROVA no vio nada. El riesgo de sobre-publicación de D25 sobre K es, como mucho, de
ese tamaño, y del mismo orden que lo que puede recuperar (11 y 23 alertas en VIIRS 750). Es un techo de exposición, no
una predicción: el script clasifica, no corre el pipeline.

## 5. Métricas y reglas, por sensor, por tramo de cenit y por ventana

Todo se cuenta por pasada, contra K, con la **lectura A** (D-4) y la **regla SN** de D-9 (MISSION), informando
también la regla original; si discrepan, manda la más estricta (como en F/K). «Publica» es el predicado de
`frontend/index.html` ejecutado con node (A97). Tramos de cenit del sensor: **≤ 40° y > 40°** (el corte de D17,
nota S141), y además los tres tramos de #869 (< 30°, 30 a 50°, ≥ 50°) como información.

| prueba | qué cuenta | regla | dónde decide |
|---|---|---|---|
| **P1 veto** | protegidas A que K publica y D no | VETADO con una pérdida neta; ruidosa (K' también cambia) deja INDECIDIBLE; en V2, PENDIENTE DE REPETICIÓN (repetición dirigida de F/K, tope dos) | VIIRS 375 y 750, las dos ventanas |
| **P1b cruce de 1 MW** | protegidas A que K muestra con 1 MW o más y D bajo 1 MW | se listan; con una o más, decide Nicolás (regla de F/K §5) | ídem |
| **P2 suma bajo 1 MW** | alertas Muy Bajo que el brazo no publica + publicaciones en negativos limpios | GANA si la suma de D es menor que la de K menos el ruido; PIERDE si es mayor que la de K más el ruido; si no, EMPATE. Ruido = pasadas discordantes entre K y K' (en V2, la fracción medida en V1) | VIIRS 375 y 750, las dos ventanas |
| **M magnitud** | en las alertas que K y D publican y tienen VRP de MIROVA: d = abs(log10(D/MIROVA)) − abs(log10(K/MIROVA)) | **MEJORA** si el intervalo bootstrap al 95 % (pasadas, 10.000 remuestreos, semilla fija) de la mediana de d queda entero bajo 0 **y** la mediana pasa el ruido (mediana de abs(d) entre K' y K); **EMPEORA** si queda entero sobre 0 y pasa el ruido; si no, **NEUTRO**; con menos de 5 pares, **SIN SUSTRATO** | **VIIRS 750 en los dos tramos de cenit; VIIRS 375 sólo con cenit ≤ 40°** |
| M375 oblicuo (informa) | lo mismo en VIIRS 375 con cenit > 40° | se informa, no decide: ahí D25 no puede cerrar por construcción (#869) | no decide |
| P4 el cúmulo se mueve (informa, condiciona) | pasadas donde el centroide del cúmulo publicado de D se aleja más de 0,01 km del de K, o cambia el modo de un píxel | se informan con su volcán; si alguna es protegida, la auditoría espacial A61 de todas las movidas va antes de cualquier adopción | no decide |
| P5 consumidores (informa) | `d9_capped` en D contra K; publicaciones de D apagadas por los filtros del tablero; `diag_bg_vecinos_n_sin_vecinos` (píxeles que cayeron al respaldo) | se informan | no decide |

**Por qué este criterio de magnitud sale de los datos de MIROVA (A115).** No hay un umbral elegido: la vara es el VRP
que MIROVA publicó en cada pasada, la pregunta es si D queda **más cerca** de ese valor que K, en la escala
logarítmica (que castiga igual pasarse que quedarse corto: el probe de S151 dio razón mediana 1,19 en los rescates de
VIIRS 750, o sea que D25 también puede pasarse), y el ruido contra el que se compara es el **gemelo medido**, no un
número fijado. El corte de 40° no es un umbral de la métrica: es dónde #869 mostró que D25 puede actuar.

**Predicciones (escritas antes de correr; no deciden).**
1. VIIRS 375 cenit ≤ 40°: M MEJORA (la razón sube desde ~0,72; 1.14 midió ×1,18 a nadir en `literal`).
2. VIIRS 375 cenit > 40°: la razón sube pero queda bajo 0,7; en Chillán bajo 0,6 (techo de #869).
3. VIIRS 750: M MEJORA en los dos tramos; en Chillán con cenit ≥ 50° la razón publicada queda bajo 0,5, porque el
   recorte del tablero (F_rec 0,57 en ese tramo) no depende del fondo.
4. P2: EMPATE en VIIRS 375 (0 y 2 cúmulos que encender); en VIIRS 750 el signo no lo predigo (17 y 21 que encender
   contra 11 y 23 que recuperar).
5. P1: CUMPLE; si cae alguna, en Lastarria o Tupungatito (vecinos más tibios que el anillo; 1.14 midió 0,91 en
   Lastarria).

## 6. Despacho (no despachar sin el sello)

**Antes del primer despacho**, en este orden: (a) el sello de Nicolás sobre este documento y las decisiones del §8;
(b) el candado del §7 mergeado y verificado; (c) el reproceso de Chillán y el histórico con K terminados o con cupo:
con el NRT (11 jobs) y otro reproceso vivo no queda margen en el tope de 20 jobs; nunca más de dos A/B vivos; (d) el
tag sobre `main` y su commit completo:

```bash
git tag -a s157-d25-k-codigo -m "codigo del A/B de D25 sobre K" origin/main
git push origin s157-d25-k-codigo
git rev-parse s157-d25-k-codigo^{commit}
```

**Cada despacho desde el tag**, nunca desde `main` a secas (A108; S152), y el siguiente recién cuando el anterior
empezó (grupo `s146-ab-sin-test1`, un solo pendiente; antes de cada despacho `gh run list --workflow
reproc-s146-ab-sin-test1.yml --json status -q '[.[]|select(.status!="completed")]|length'` tiene que dar 0):

```bash
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-08-29 -f end=2026-10-18 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_gemelo","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-04-01 -f end=2026-05-07 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-05-08 -f end=2026-06-12 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
```

Con la opción §8 b, se agrega `"_s157_ab_d25_k_on_h1"` a `brazos` en los tres. Autentica sólo con `EARTHDATA_TOKEN`
(A71); `ubuntu-24.04` está fijado en el workflow.

**Costo, estimado** desde la tasa de F/K (`experiments/_s151_prereg_fk_11/duracion_runs.py --estimar`: 2,20 min por
día de ventana en un job sin Test 1 con los tres sensores, el job más lento 1,42 veces la mediana; sin MODIS debería
ser menos, no está medido): V1, 33 jobs de ~112 min (peor ~159), ~10 a 15 h de pared con 6 en paralelo; V2a y V2b, 22
jobs de ~80 min (peor ~115) cada uno, ~6 a 8 h cada uno. En serie, **~22 a 31 h de grupo ocupado**; con D1, un tercio
más. El peor job (159 min) queda bajo el tope de 300 con el margen de A15 (1,3 × 159 = 207).

## 7. Controles antes de mirar ningún resultado, y el candado del evaluador

**Controles del A/B** (si uno falla, lo que depende de él queda INDECIDIBLE y no se interpreta):
1. **Cobertura pareja** (A108): las mismas pasadas en los brazos de cada despacho, por volcán y sensor; contar las de
   cada brazo contra el control ANTES de mirar el veredicto. Y el control contra lo que hay en disco con K (producción
   desde el 2026-09-18, histórico con K antes): si en algún volcán y sensor al control le falta más del 5 % de las
   pasadas, cobertura corta (el 5 % es del instrumento, heredado de F/K, elegido y no medido). Chillán antes del
   2026-09-18 se compara contra producción (C0): las pasadas no dependen del detector.
2. **Versión de producto** igual entre brazos en toda pasada protegida.
3. **Cableado** (A118): la línea `FLAGS_BRAZO` de cada job trae los dos flags de D25, su ventana y `SENSOR_MODIS`
   con el valor declarado (agregados al workflow en este PR); y la **huella en los records**: D tiene
   `diag_bg_vecinos_n_sin_vecinos` en sus records con cúmulo, K y K' en ninguno; 0 `triggered_test1` en todos.
4. **Determinismo**: K' contra K, misma decisión de publicar en 98 de cada 100 pasadas o más (umbral heredado de S149
   a F/K, elegido).
5. **Nulo de la palanca medido, no razonado (A110, A116)**: el evaluador corrido con K' en el lugar de D tiene que dar
   P1 CUMPLE, P2 EMPATE y M NEUTRO en todos los estratos. Si da otra cosa, el instrumento inventa efectos y nada se
   interpreta.
6. **La referencia es la congelada, entera**: sha256 LF de los CSV y de las dos capas contra el `MANIFIESTO.json`.
7. **El predicado del tablero** es el de `frontend/index.html` con node; el evaluador imprime su sha256.

**Candado, a implementar y verificar ANTES de despachar** (como el de la adenda K del diurno):
- `evaluar_d25.py`: el evaluador de F/K (`experiments/_s151_prereg_fk_11/evaluar_fk.py`, P1, P2, ruido, repetición,
  lectura A y SN) con los brazos parametrizados (K, K', D, D1) **sin tocar el archivo de F/K**, más la métrica M por
  tramo de cenit, P1b, P4 y P5 de este documento.
- Sus pruebas, en `probar_evaluar_d25.py`, cada una tiene que **fallar por la razón que dice** (S140): nulo (cuatro
  brazos idénticos dan CUMPLE, EMPATE, NEUTRO); positivo de M (magnitud de VIIRS 750 de D llevada hacia MIROVA a la
  mitad de distancia en log: MEJORA); negativo de M (dividida por 20: EMPEORA); una protegida oculta en D: VETADO; una
  protegida que cruza 1 MW: P1b la lista; un negativo publicado de más en D: P2 lo cuenta; un VIIRS 375 oblicuo
  mejorado NO decide; mutación del corte de 40° a 50° cae por una prueba con nombre.
- Mutaciones del evaluador contadas sólo si las atrapa una aserción, con control de caída (memoria S156).
- Verificador con contexto limpio sobre el evaluador.

## 8. Decisiones para el sello

**a) El criterio de magnitud.** Recomendado: **M como está en §5** (decide VIIRS 750 en los dos tramos y VIIRS 375
con cenit ≤ 40°). Alternativa: que M decida también VIIRS 375 oblicuo. No lo recomiendo: ahí D25 no puede cerrar por
construcción, y un NEUTRO o un MEJORA chico no dirían nada de D25.

**b) La ventana de D25 (1 contra 3).** Recomendado: **sólo D con hasta 7x7** (el valor del perfil), salvo que el probe
muestre que la mitad de los píxeles de los cúmulos de Chillán cae al interior y cambia más de 5 % entre `h3` y `h1`;
en ese caso agregar D1 en V1 (un tercio más de costo en V1). Esta decisión se toma con el resultado del probe a la
vista, antes de despachar, y se anota acá.

**c) MODIS.** Recomendado: **fuera de este A/B**, y decidir si se escribe el flag de D25 en MODIS (ciclo A45) con el
resultado del probe (`kernel3` y `d25_rad` en las dos pasadas MODIS de Chillán). Alternativa: escribir el flag antes y
meter MODIS en este A/B; retrasa todo y su sustrato de alertas MODIS es chico (14 protegidas en V1, 16 en V2).

**d) Qué hacer con cada veredicto.**

| resultado | qué se hace |
|---|---|
| P1 CUMPLE, P2 sin PIERDE en ningún sensor, M MEJORA en algún estrato que decide y EMPEORA en ninguno | **CUMPLE**: se abre el ciclo de adopción (tag defensivo, R2 por píxel, verificador independiente, «sí» de Nicolás; A45, S33) |
| ídem pero M NEUTRO en todo | **SIN EFECTO**: D25 es fidelidad literal (siete textos del grupo), pero no mueve la magnitud sobre K. Decide Nicolás |
| M MEJORA en un estrato y EMPEORA en otro | decide Nicolás con la tabla por estrato |
| P1 VETADO, o P2 PIERDE en algún sensor | **NO CUMPLE**: no se adopta; cada pérdida se diagnostica (cabecera de la imagen de MIROVA, A61) |
| P1b con alguna protegida bajo 1 MW | decide Nicolás con la lista |
| INDECIDIBLE o PENDIENTE | repetición dirigida (tope dos, F/K §5); un INDECIDIBLE de controles no se repite, se busca el defecto |

## 9. Lo que este A/B no puede decir

- **MODIS** (§2). Ni la inconsistencia de longitud de onda de MODIS con K (banda 22 para la temperatura, banda 21 para
  volver a radiancia; hallazgo lateral de #869, ×1,05 a 1,06).
- **D17**: si después de D25 la razón sigue cayendo con el cenit, D17 queda como hipótesis (tarea 1.36), con el
  contraste por zona de agregación que propuso #869.
- **Selección**: D25 no agrega píxeles. Si MIROVA suma vecinos tibios que no alertamos, eso no se mueve; el probe del
  L1B mide cuánto podría ser en Chillán.
- **El poder del veto fuera de Láscar y Chillán**: como en F/K, en los otros volcanes hay 3 protegidas o menos por
  sensor y ventana (`sustrato_k_salida.txt`, tablas por volcán).
- **El día**: los brazos son nocturnos; el A/B diurno sobre K es otra tarea (1.32).
