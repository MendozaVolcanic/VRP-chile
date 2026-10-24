# Pre-registro S162 MOD-D: el paquete MODIS del código de MIROVA contra K (censo retrospectivo en el arnés)

> **BORRADOR para el verificador y para el sello.** Escrito el 2026-10-24 por la sesión hija de MODIS (loop
> `tasks/LOOP_MODIS.md`), antes de correr ningún brazo. Nicolás autorizó el programa por sensor con la decisión D-48
> («sobre las decisiones mías haz lo que tú recomiendes», 2026-10-24); la recomendación 3 del programa
> (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §9) es validar cada paquete con **equivalencia +
> censo + sombra prospectiva** en vez de tres A/B retrospectivos. Este documento pre-registra la primera pata (el
> censo) y fija las otras dos para cuando existan. Nada se despacha sin el verificador con contexto limpio, sin el
> candado del §8 y sin el pedido a la coordinadora. Nada toca `pipeline/` (A45).

## 0. Por qué este A/B y por qué ahora

**El fenómeno.** De noche, el cráter de Láscar o de Chillán ocupa una fracción mínima de un píxel MODIS de 1 km (más
de 2 × 5 km a 58° de cenit). MIROVA lo detecta por contraste local del NTI y del ETI sobre una grilla fija de 1 km,
mide el fondo interpolando por debajo de un halo, sin recortar, y suma la radiancia de todos los píxeles alertados.
Producción (K) hace otra cosa: umbrales duales sobre el píxel nativo, fondo de anillo de 5 a 25 km con recorte a cero
(D25) y el cúmulo anclado al cráter. En la muestra de 150 pasadas MODIS de S159, el código de MIROVA portado
(B22 primaria, MxD03, grilla 51 × 51) dio 50 de 50 protegidas y razón de magnitud 1,006 contra 0,516 de K
(`experiments/_s159/portes/INFORME.md` P-1, rama `s159-pruebas`); el verificador confirmó la detección y dejó el
«GANA» contra K NO RESUELTO por el estrato de negativos sin publicar (V-1), que es lo que mide MOD-C.

**La pregunta.** Sobre el **censo** de las pasadas MODIS nocturnas con referencia de MIROVA, ¿el paquete (PM) publica
lo que MIROVA publica y calla donde MIROVA calla mejor que K, sin perder una sola protegida? Y, dentro de lo mismo,
¿el déficit de magnitud de Chillán (K/MIROVA 0,485, n 7; MOD-D es donde el programa lo juzga) es del detector o del
sensor visto de lado?

**Lo que este censo decide y lo que no.** Decide si el paquete es **candidato** a pasar a la fase 3 del programa (la
vía de proceso «código MIROVA» en `pipeline/` detrás de flag). **No adopta nada**: la adopción es la fase 4 y pide
además la equivalencia pasada por pasada de esa vía contra este mismo PM y la sombra prospectiva (§7), con tag
defensivo y el sí de Nicolás (A45).

**Dependencias, en orden.** MOD-C (si el port enciende de más en `neg_resto`, este censo lo va a ver entero y su P2
tiene que poder darlo); MOD-B (si MxD03 sobre K da NO CUMPLE, el brazo PM-geo5 de aquí dice cuánto pesa MxD03 dentro
del paquete); MOD-E (si quitar los duplicados del bow tie cambia la magnitud, entra un brazo PM-sin_dup; ver §3).

## 1. Las tres preguntas de `docs/MISSION.md`

1. **¿Está en los papers?** El paquete es el **código operacional publicado por MIROVA** para VIIRS 750 (OSF zm62w, MIT,
   D34 del catálogo), con sólo las bandas, la grilla y el coeficiente cambiados por sensor. Para MODIS no hay código
   publicado: se traslada la estructura, no los números (programa §5). Que MIROVA use MxD03 en MODIS está en disputa
   hasta MOD-A (Coppola et al. 2026, p. 4: la tarea la hace la sesión del instrumento; este pre-registro la usa cuando
   llegue y, mientras tanto, la trata como inferencia por los datos: P-2 de PORTES).
2. **¿Cierra una divergencia documentada?** Sí, varias a la vez: D25 (fondo), D32 (suma), D17 (remuestreo), D21
   (B22, ya en K), D28 (bow tie, si MOD-E lo pide), y la geolocalización (D35 propuesta en el sello de MxD03).
3. **¿Alineación interna?** No aplica.

**Uniformidad.** Un algoritmo por sensor, igual para los 11 volcanes; la caja por volcán (V750-B) se hereda sólo si
V750-B la establece en el código de MIROVA, y entonces entra como brazo propio, no como ajuste de este.

## 2. Población y ventanas

- **Censo**: las mismas 5.465 pasadas MODIS nocturnas en 1.232 gránulos de MOD-B
  (`experiments/_s162_mxd03/poblacion.json`, rama `s162-mxd03-codigo`, main congelado `80b819828`, referencia congelada
  con sha256 en `MANIFIESTO.json`), del 2026-03-01 al 2026-10-16, con sus etiquetas (protegida 50, bajo 1 MW 42,
  negativo limpio 5.110, `sin_info` 253, `far_ref` 10). Usar la misma población hace los dos A/B comparables pasada por
  pasada y permite reusar su censo y sus controles.
- **Ventana T** (tabla sola decide, A119): en MODIS es toda la ventana, porque ninguna alerta MODIS depende del OCR
  (92 de 92 con fila del consolidado; verificador del pre-registro de MxD03, `extra_verif_salida.txt` (b)). Se informa
  igual el canal de cada alerta.
- **Cortes que se informan por tramo** (no separan brazos): #535 (2026-08-28 23:00 UTC), el reproceso de K
  (2026-09-18), la adopción de K (2026-10-18 09:57 UTC, fuera de la ventana), TIF congelados desde el 2026-09-22.
- **Prospectiva P** (§7): desde el 2026-11-03, en sombra.

## 3. Brazos

| brazo | qué es | papel |
|---|---|---|
| **K** | producción del main congelado (`calculate_vrp` + `store.append_record`), con `_interp_geo` | control |
| **K33** | K con `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA` encendido en memoria (D33: la vuelta a radiancia con la λ de la banda que dio la temperatura; ~+5,8 % de magnitud, `experiments/_s157_lambda_b22/`) | diagnóstico de M: separa el sesgo de λ del de detector |
| **PM** | el port del código de MIROVA (`experiments/_s159/portes/mirova_port.py`, variante `fisica`, sin un cambio): B22 primaria con B21 donde B22 satura, lat/lon de MxD03, grilla UTM 51 × 51 de 1 km con la esquina de GEO, remuestreo lineal, Test 1 como alerta, ventana 3 × 3 con central, umbrales del `.m`, segundo pase con regresión, fondo por `fillmissing2` sin recorte, suma de todos los alertados, sin modo de un píxel ni tope D9 | **la palanca** |
| **PM-geo5** | PM con la lat/lon de `_interp_geo` (la de producción) en vez de MxD03 | aísla MxD03 dentro del paquete (PD2 del programa: «MxD03 sola o en el paquete») |
| **PM-sens** | PM con todo el ROI1 en umbrales de cumbre (variante `sensible` de S159) | diagnóstico de la caja; en la muestra de S159 dio el mismo recall y silencio que `fisica` |
| **PM-sin_dup** | PM con los duplicados del bow tie quitados antes de remuestrear | **sólo si MOD-E lo pide** (adenda fechada antes del despacho); si no, no corre |
| **placebo** | K × 1,2 en magnitud, sin tocar detección | obligatorio para M (programa §2, D-28) |

**D33 en el PM.** El port trabaja en radiancia: detecta sobre la radiancia MIR y suma la radiancia, así que la ida y
vuelta temperatura-radiancia de D33 no existe ahí (`mirova_v750_r2.py` l. 96: la única conversión es el modelo espectral
`temperatura_a_radiancia(bt15, LAMBDA_M13)` con λ = 3,959 µm de B22). Queda una sola cara: los píxeles donde B22 satura
y entra B21 (3,929 µm) se tratan con la λ de B22. En S159 fueron 0 de 149 pasadas (`B22 en NaN con B21 válida`); se
cuentan por pasada, y si aparece alguno la pasada se marca y se informa con y sin ella. «PM con D33 corregido» del
programa queda así cumplido por construcción, salvo esa cara declarada.

**El record sintético del PM** (lo que lee el predicado del tablero) es `record_port` de
`experiments/_s159/portes/04_analizar.py` sin cambios, con la corrección que el verificador de PORTES pidió para la
distancia: centroide de los alertados **y** distancia del alertado más cercano, las dos informadas; decide la del
centroide (la pre-registrada en S159), la otra informa (V-5 de ese verificador).

## 4. Métricas (las del §2 del programa, con el código de D25 donde ya existe)

Todo por pasada MODIS, lectura A, «publica» = el predicado de `frontend/index.html` ejecutado con node
(`banco_paridad.correr_node`), contra K.

| prueba | qué cuenta | regla | decide |
|---|---|---|---|
| **P1 veto** | protegidas que K publica y el brazo no | una sola: NO CANDIDATO | sí |
| **P1b, dos direcciones** | protegidas que cruzan 1 MW en la magnitud mostrada (K ≥ 1 y brazo < 1, y K < 1 y brazo ≥ 1) | se listan; con una o más de la primera dirección decide Nicolás | lista |
| **P2 suma bajo 1 MW** | S = alertas bajo 1 MW sin publicar + publicaciones en negativos limpios; por bloque noche-volcán | **prueba de signos por bloque noche-volcán (D-45)**, exacta hasta 20 bloques, una cola por dirección al 5 %; SIN SUSTRATO con 4 bloques discordantes o menos (D-44). Función `prueba_signos_p2` de `experiments/_s157_prereg_d25/evaluar_d25.py` (rama `s159-evaluador-d25`), importada sin copiar | sí |
| **M magnitud** | en alertas que los dos publican: d = abs(log10(B/MIROVA)) − abs(log10(K/MIROVA)), y d′ contra la ganancia pareja ĝ = mediana de B/K (D-28/D-30/D-32: `comparar_con_ganancia` y su calibración de 1.000 repeticiones) | MEJORA sólo si d′ queda entero bajo 0; EMPEORA contra K sobre d; el placebo K × 1,2 tiene que dar d′ = 0 (si no, el instrumento no sirve y M queda INVALIDO) | sí, para Chillán (§5) e informa en el resto |
| **Curva de cenit** | razón brazo/MIROVA por tramo de 10° de cenit, y la razón «más oblicua sobre menos oblicua de la misma noche» del brazo contra la de MIROVA | se compara contra la curva de MIROVA, **no contra 1** (programa §1 punto 6: MIROVA también cae con el cenit) | informa; condiciona Chillán |
| **Estratos** | todo lo anterior por tramo de 10° de cenit, por volcán, por canal (tabla / OCR) y por tramo de régimen | se informa | no |

**Unidad del operador (A94).** Se informa también por noche-volcán: cuántas noches con protegida MODIS cambian de
«publicada» a «no publicada» en el tablero considerando VIIRS de la misma noche (en la ventana, 43 de 44 noches con
protegida MODIS ya publican VIIRS).

## 5. El déficit de Chillán (se juzga aquí)

Chillán es el único volcán con alertas MODIS fuertes y oblicuas en la ventana (10 alertas, 9 protegidas). Las 2 del
12 y 15 de octubre a 58° no tienen detección en K ni en K con MxD03 (M H4; la cumbre fría vista de lado:
`experiments/_s159/chillan_modis/INFORME.md` H1), pero **el port de S159 sí las detecta** (razón contra MIROVA 0,837 y
1,734: `experiments/_s162_modis_bowtie/razon_por_cenit_volcan_salida.txt`, MOD-E). O sea que esas dos pérdidas son del
detector de K, no del sensor, y este censo tiene que confirmarlo sobre la población entera. Reglas, escritas antes de
correr:
1. **RESUELTO POR EL PAQUETE** si PM/MIROVA en las alertas de Chillán que PM publica tiene mediana en [0,8; 1,25] y su
   d′ contra K queda entero bajo 0 (con el placebo en d′ = 0).
2. **ES DEL SENSOR** si PM/MIROVA en Chillán sigue la misma caída con el cenit que MIROVA contra sí misma (la curva del
   §4) y la mediana queda bajo 0,8: el déficit es la cumbre fría a 58°, y lo que hace MIROVA ahí no lo reproduce el
   código trasladado.
3. **SIN RESOLVER** en cualquier otro caso, con la lista pasada por pasada.
Las 2 protegidas a 58° sin detección se informan aparte (no entran a la mediana: no hay magnitud que dividir).

## 6. Veredicto del censo

| resultado | etiqueta |
|---|---|
| PM: 0 protegidas perdidas, P2 GANA o EMPATE (signos), M sin EMPEORA sobre d, controles en verde | **CANDIDATO** a la fase 3 |
| PM pierde alguna protegida | **NO CANDIDATO** (con atribución: ¿PM-geo5 también la pierde? ¿PM-sens?) |
| P2 PIERDE (signos) | **NO CANDIDATO** |
| P1b con alguna, o M EMPEORA | **DECIDE NICOLÁS** con la lista |
| control rojo, o P2 SIN SUSTRATO | **INDECIDIBLE** (se busca el defecto; no se repite a ciegas) |

PM-geo5 y PM-sens tienen el mismo veredicto calculado, informativo: dicen qué pieza sostiene el resultado del PM.

## 7. Las otras dos patas (fijadas aquí, pre-registradas cuando existan)

- **Equivalencia (fase 3)**: la vía «código MIROVA» en `pipeline/` (detrás de flag, tag y sí de Nicolás; V750
  primero) tiene que reproducir el PM de este censo pasada por pasada: misma publicación en el 100 % de las alertas y
  de los negativos que el PM publica, y `pc.vrp_mw` a 0,001 MW; en el resto, 99 % o más (elegido). Muestra fija: los 85
  gránulos de M, más 3 noches de Láscar y 3 de Chillán, más todas las pasadas donde PM y K difieren.
- **Sombra prospectiva**: la vía corre en el perfil `experimental` (o un perfil de sombra con su `data_subdir`, A47)
  desde el 2026-11-03, y se evalúa con las mismas reglas del §4 sobre la ventana P, sin Suomi NPP (no afecta a MODIS,
  pero es otro régimen del proyecto). Tamaño y fecha de lectura: se fijan en su propio pre-registro, antes de mirar.

## 8. Controles (se leen antes del resultado)

1. **K = producción** en toda pasada ok (publicación y `pc.vrp_mw` a 0,001 MW); las diferencias en las que deciden se
   re-corren en su `codigo_sha` (el mismo control 4 de MxD03; misma pieza `recorrer_en_sha.py`).
2. **PM = port de S159** en las 150 pasadas MODIS del lote 39712862945 que están en la población (npix y VRP a 1e-6
   MW): misma cadena.
3. **Placebo** K × 1,2: d′ = 0 por construcción; si no, M INVALIDO.
4. **Nulo del contador** (fuera de línea): a los records del PM que publican se les pone `vrp_mw` = 0 y dejan de
   publicar; a 50 negativos que no publican (semilla 162) se les inyecta un cúmulo de cumbre de 0,3 MW a 0,5 km y
   pasan a publicar (el del censo del oráculo de V750, §5.3).
5. **Cobertura** (A108): los mismos 1.232 gránulos en todos los brazos; «volcán fuera del gránulo» y «escena inválida»
   fuera del denominador y contadas aparte (estado propio «no observado», §8 punto 2 del programa).
6. **Referencia congelada**: la de MOD-B (sha256 del `MANIFIESTO.json`).

## 9. Costo y despacho

- **Medido en S159** (`experiments/_s162_modis_negativos/04_costo_salida.txt`): 9,1 s por pasada MODIS con K y las 5
  variantes del port (K 1,69 s), 104 s fijos por job; búsqueda y descarga de un gránulo con L1B y MxD03: media 32,8 s
  (MxD03 v2, `tiempo_proceso_vs_descarga_m_salida.txt`).
- **Estimado** para el censo: 1.232 gránulos × 32,8 s = 11,2 h de descarga; 5.465 pasadas × (9,1 s + K33 1,7 s +
  placebo 0) ≈ 16,4 h; arranque 0,7 h: **≈ 28 h de runner**, en 24 partes de ~1,2 h.
- **Alternativa con ahorro**: correr los brazos de este censo dentro de los jobs de MOD-B, sobre los mismos gránulos
  ya bajados (ahorra las 11,2 h de descarga). **No la recomiendo**: MOD-B ya está sellado y verificado con su arnés, y
  acoplarlo le cambia el código y el tiempo por parte (de ~2 h a ~2,7 h). Decide la coordinadora.
- Despacho: lo pide esta sesión a la coordinadora, desde un tag, con el pre-registro sellado y verificado, cuando MOD-C
  haya entregado (si MOD-C da REFUTA, este censo se corre igual: es el que lo mide entero).

## 10. Lo que no decide, y riesgos

- La adopción (fase 4). El día (D-10). VIIRS.
- **Concentración en Láscar**: 80 de 92 alertas MODIS son de Láscar; fuera de Láscar, Chillán y Villarrica no hay
  alertas MODIS en la ventana. Para los otros ocho volcanes sólo cuentan los negativos (P2).
- **El port no es la vía de pipeline**: un CANDIDATO aquí es del código en el arnés; la equivalencia de la fase 3 es la
  que ata la vía a este resultado.
- **La grilla 51 × 51 con la esquina de GEO** es la regla de los TIF de MIROVA en VIIRS 750 (`experiments/_s159/geo/`);
  que MODIS use la misma regla es SOSPECHA (TIF MODIS en EPSG:4326, `tif_modis_cobertura_salida.txt` de MxD03).

## 11. Decisiones para sellar (con recomendación)

1. ¿Censo en el arnés con brazos K, K33, PM, PM-geo5, PM-sens y placebo? **Sí.**
2. ¿Misma población y referencia que MOD-B? **Sí.**
3. ¿P2 por prueba de signos por bloque (D-45) en vez del nulo R de MOD-B? **Sí**: aquí no hay un corrimiento que
   imitar, y D-45 es la regla vigente del proyecto para P2.
4. ¿Chillán con las tres salidas del §5? **Sí.**
5. ¿Despacho aparte de MOD-B (no acoplado)? **Sí.**
6. ¿PM-sin_dup sólo si MOD-E lo pide? **Sí.**
