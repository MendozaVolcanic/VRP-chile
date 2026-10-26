# Pre-registro S162 MOD-D: el paquete MODIS del código de MIROVA contra K (censo retrospectivo en el arnés), v2

## SELLO DE LAS REGLAS (2026-10-24, decisión D-48)

**Reglas de la v2 SELLADAS** por la decisión D-48 de Nicolás, 2026-10-24: «sobre las decisiones mías haz lo que tú
recomiendes». La aplicó la coordinadora S162 (sesión «Retomar») sobre la recomendación de esta sesión (§11, cinco
puntos, todos «sí») e informó a Nicolás para que pueda revertirla. Quedan selladas la población, los brazos, las pruebas
del §4, la prueba de Chillán del §5 con sus casos borde, la precedencia del §6 y los controles del §8. **No queda
sellado el despacho**: el candado del §10 (evaluador, arnés, workflow) y su verificador con contexto limpio siguen siendo
requisito antes de pedirlo. Todo cambio desde aquí va como adenda fechada.


> **v2, reglas selladas el 2026-10-24 (arriba). Texto previo del encabezado:** BORRADOR v2 para el sello. Escrito el 2026-10-24 por la sesión hija de MODIS (loop `tasks/LOOP_MODIS.md`) antes
> de correr ningún brazo. La v1 (commit `e4feb6f57` de la rama `claude/s162-modis-774bb0`) la revisó un verificador con
> contexto limpio (Fable alto, `experiments/_s162_modis_verif_cde/INFORME.md`, VCD-01, 02, 05, 06, 09, 11, 12 y 13, y
> la lista D3 de su §5); esta v2 cierra cada regla que obligaba a decidir después de mirar. Nicolás autorizó el programa
> por sensor con D-48 («sobre las decisiones mías haz lo que tú recomiendes», 2026-10-24); la recomendación 3 del
> programa (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §9) es validar cada paquete con
> **equivalencia + censo + sombra prospectiva**. Esto pre-registra el censo. **No es despachable todavía**: le faltan el
> evaluador, el candado y el workflow (§10), que se construyen después de que MOD-B y MOD-C entreguen, porque los dos
> cambian el diseño (MxD03 dentro o fuera; si el port enciende en `neg_resto`). Nada toca `pipeline/` (A45).

## 0. Registro de cambios de la v1 a la v2

| hallazgo | qué cambió |
|---|---|
| VCD-01, P2 = BLOQUEA sin fila | el veredicto (§6) tiene una fila para cada salida de `regla_signos_p2`, con precedencia escrita |
| VCD-02, Chillán exigía un d′ de dos volcanes | Chillán se juzga con una prueba propia, escrita aquí (§5): prueba de signos exacta por pasada, no `comparar_con_ganancia` |
| VCD-06, el placebo no podía fallar | el placebo K × 1,2 queda como control de cableado (d′ = 0 por construcción) e informa, como manda D-28 §2.5; no invalida M |
| VCD-13, alcances sin fijar | M decide sólo «EMPEORA sobre d» en el agregado (manda a Nicolás), y nada más; P1b tiene una sola regla; `sin_info` y `far_ref` informan; precedencia en §6 |
| VCD-11, el 0,485 de Chillán | en la población congelada de este censo K/MIROVA de Chillán es **0,635** (n 7; `experiments/_s162_mxd03/chillan_k_mirova_salida.txt`, rama `s162-mxd03-codigo`); 0,64 a 0,85 con cenit bajo 30° y 0,14 a 0,21 con cenit de 35 a 51° |
| VCD-12, `record_port` «con la corrección V-5» | se usa `record_port` de `04_analizar.py` sin cambios; la distancia del alertado más cercano es una función nueva, informativa |
| VCD-03 (MOD-E), PM-sin_dup | sale de los brazos: la regla de «filas de borde» dejaba huecos y conservaba copias. Queda una clasificación informativa por costura de barrido (§3) y la ablación real con los recortes nativos de MOD-C |
| VCD-05, población en rama local | la rama `s162-mxd03-codigo` está en el remoto (commit `34f8ca391`) |
| VCD-09, costo con descarga doble | recalculado (§9) |

## 1. Por qué, y qué decide

**El fenómeno.** De noche, el cráter de Láscar o de Chillán ocupa una fracción mínima de un píxel MODIS de 1 km (más
de 2 × 5 km a 58° de cenit). MIROVA lo detecta por contraste local del NTI y del ETI sobre una grilla fija de 1 km,
mide el fondo interpolando por debajo de un halo, sin recortar, y suma la radiancia de todos los píxeles alertados.
Producción (K) usa umbrales duales sobre el píxel nativo, un fondo de anillo de 5 a 25 km con recorte a cero (D25) y el
cúmulo anclado al cráter. En la muestra de 150 pasadas MODIS de S159, el código de MIROVA portado dio 50 de 50
protegidas y razón 1,006 contra 0,516 de K (`experiments/_s159/portes/INFORME.md` P-1, rama `s159-pruebas`); el
verificador dejó el «gana contra K» NO RESUELTO (V-1), que es lo que mide MOD-C.

**La pregunta.** Sobre el censo de las pasadas MODIS nocturnas con referencia de MIROVA, ¿el paquete (PM) publica lo
que MIROVA publica y calla donde MIROVA calla mejor que K, sin perder una protegida? Y en Chillán, ¿el déficit de
magnitud (K/MIROVA 0,635, que cae de 0,64-0,85 bajo 30° de cenit a 0,14-0,21 de 35 a 51°) es del detector de K o del sensor visto de lado?

**Lo que decide**: si el paquete es CANDIDATO a la fase 3 (la vía «código MIROVA» en `pipeline/` detrás de flag). **No
adopta nada** (§7).

## 2. Población y ventanas

- **Censo**: las 5.465 pasadas MODIS nocturnas en 1.232 gránulos de MOD-B (`experiments/_s162_mxd03/poblacion.json`,
  rama `s162-mxd03-codigo`, main congelado `80b819828`, referencia con sha256 en `MANIFIESTO.json`), del 2026-03-01 al
  2026-10-16. Etiquetas: protegida 50, bajo 1 MW 42, negativo limpio 5.110, `sin_info` 253, `far_ref` 10.
- **Ventana T** (tabla sola decide, A119): toda la ventana; ninguna alerta MODIS depende del OCR (92 de 92 con fila del
  consolidado). El canal de cada alerta se informa igual.
- **Cortes informados por tramo** (no separan brazos): #535 (2026-08-28 23:00 UTC) y el reproceso de K (2026-09-18).
- **`sin_info` y `far_ref`**: no entran a ninguna prueba que decide; sus cambios de publicación se listan.

## 3. Brazos

| brazo | qué es | papel |
|---|---|---|
| **K** | producción del main congelado (`calculate_vrp` + `store.append_record`) | control |
| **K33** | K con `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA` encendido en memoria (D33) | informa: separa el sesgo de λ del de detector en M |
| **PM** | `experiments/_s159/portes/mirova_port.py` variante `fisica`, sin cambios (blob `96769a89`): B22 primaria con B21 donde B22 satura, MxD03, grilla UTM 51 × 51 de 1 km con la esquina de GEO, remuestreo lineal y el `.m` entero (Test 1 como alerta, 3 × 3 con central, umbrales, segundo pase con regresión, fondo `fillmissing2` sin recorte, suma de todos los alertados, sin modo de un píxel ni tope D9) | **la palanca** |
| **PM-geo5** | PM con la lat/lon de `_interp_geo` | informa: cuánto pesa MxD03 dentro del paquete |
| **PM-sens** | PM con todo el ROI1 en umbrales de cumbre | informa: la caja |
| **placebo** | K × 1,2 en magnitud | control de cableado de M (d′ = 0 por construcción); informa (D-28 §2.5) |

**D33 dentro del PM**: el port trabaja en radiancia, así que la ida y vuelta temperatura-radiancia no existe; queda la
cara de los píxeles donde B22 satura y entra B21 (3,929 µm tratado como 3,959). En S159, 0 de 149 pasadas. Se cuentan
por pasada; una pasada con alguno se marca y se informa con y sin ella.

**Record sintético del PM**: `record_port` de `experiments/_s159/portes/04_analizar.py`, sin cambios (distancia del
centroide de los alertados). Aparte, informativa, la distancia del alertado más cercano (función nueva del evaluador).

**Costura de barrido (informa, por MOD-E)**: cada alerta se marca según si el píxel nativo del cráter cae en las dos
filas de borde de un barrido de 10 líneas (`linea % 10` en 0 o 9). En el sintético de MOD-E la costura es donde el
remuestreo lineal pierde un foco sub-píxel; aquí se cuenta cuántas alertas de MIROVA caen ahí y qué hace cada brazo con
ellas. La eliminación de duplicados (D28) **no** entra como brazo hasta que se localice el método de MIROVA (Coppola
2010 o Liu et al. 2008, SOSPECHA) y se pruebe un método sin huecos sobre los recortes nativos de MOD-C.

## 4. Pruebas

Todo por pasada MODIS, lectura A, «publica» = el predicado de `frontend/index.html` ejecutado con node
(`banco_paridad.correr_node`), contra K. Funciones importadas sin copiar de
`experiments/_s157_prereg_d25/evaluar_d25.py` en el commit `ded217af43911e9afadfbf77caf7e6741890b008` (rama
`s159-evaluador-d25`): `prueba_signos_p2` y `regla_signos_p2` (D-45), `pesos_bloque` y `regla_m`.

| prueba | qué cuenta | regla |
|---|---|---|
| **P1 veto** | protegidas que K publica y el brazo no | una sola: NO CANDIDATO (§6) |
| **P1b** | protegidas que los dos publican con K ≥ 1 MW y el brazo < 1 MW en la magnitud mostrada | una o más: DECIDE NICOLÁS. La dirección contraria (K < 1 y brazo ≥ 1) se lista y no decide |
| **P2** | S = alertas bajo 1 MW sin publicar + publicaciones en negativos limpios, sumado por bloque noche-volcán | `regla_signos_p2` (D-45): GANA, PIERDE, BLOQUEA, EMPATE o SIN SUSTRATO (con 4 bloques discordantes o menos) |
| **M** | en las alertas (protegida o bajo 1 MW) que K y el brazo publican: d = abs(log10(B/MIROVA)) − abs(log10(K/MIROVA)), bloques noche-volcán | `regla_m` sobre d en el agregado: sólo **EMPEORA** decide (manda a Nicolás); MEJORA y NEUTRO informan. d′ contra ĝ (D-28) y por volcán se informan |
| **Curva de cenit** | razón brazo/MIROVA por tramo de 10° de cenit | informa |
| **Noches** (A94) | noches con protegida MODIS que cambian de publicada a no publicada en el tablero contando VIIRS de la misma noche | informa |

## 5. Chillán (prueba propia, informa al lado del veredicto)

Población: las 10 alertas MODIS de Chillán del censo (9 protegidas, 1 bajo 1 MW; `chillan_k_mirova_salida.txt`).
1. **Recuperadas**: alertas que K no publica y PM sí (hoy K no publica 3: 2026-09-29 07:20, 2026-10-12 07:20 y
   2026-10-15 01:05). Se cuentan y se listan con su razón PM/MIROVA.
2. **Pares**: alertas que K y PM publican. En cada una, PM queda más cerca de MIROVA que K si
   abs(log10(PM/MIROVA)) < abs(log10(K/MIROVA)).
3. **RESUELTO POR EL PAQUETE** si (a) la mediana de PM/MIROVA en los pares está en [0,8; 1,25] **y** (b) la prueba de
   signos exacta de una cola sobre los pares da p ≤ 0,05 a favor de PM (con 7 pares exige 7 de 7, p = 1/128; con 6 de 7
   da p = 0,0625 y no alcanza; el número exacto de pares lo fija el censo, la regla no cambia).
4. **ES DEL SENSOR** si la mediana de PM/MIROVA en los pares con cenit sobre 30° (el corte que separa en K: 0,14 a 0,21
   de 35 a 51°, contra 0,64 a 0,85 bajo 30°) queda bajo 0,8 **y** la de los pares con cenit de 30° o menos queda en
   [0,8; 1,25]: el código trasladado reproduce a MIROVA de frente y no de lado.
5. **SIN SUSTRATO** si hay menos de 5 pares (con 4 la prueba de signos no puede bajar de p = 1/16 = 0,0625: la regla 3
   sería inalcanzable). Un par con las dos distancias iguales (empate exacto) sale de la prueba y se lista. Si el grupo
   de cenit de 30° o menos o el de más de 30° queda vacío, la regla 4 no se cumple (verificador, ronda 2, VCD-16).
6. **SIN RESOLVER** en cualquier otro caso, con la lista pasada por pasada.
Nota (VCD-17): el corte de 30° se eligió mirando a K en estos mismos 7 pares; es pre-registrado respecto de PM, y
cualquier corte entre 23,6° y 35,1° da la misma partición (4 pares bajo, 3 sobre).
Precedencia: 5 (SIN SUSTRATO) primero, después 3 y luego 4. Esta prueba no entra al veredicto del §6: lo acompaña.

## 6. Veredicto del censo (primera fila que se cumpla, en este orden)

| orden | condición | etiqueta |
|---|---|---|
| 1 | algún control del §8 en rojo | **INDECIDIBLE** (se busca el defecto; no se repite a ciegas) |
| 2 | PM pierde alguna protegida (P1) | **NO CANDIDATO**, con atribución (¿PM-geo5 y PM-sens también la pierden?) |
| 3 | P2 da PIERDE | **NO CANDIDATO** |
| 4 | P2 da SIN SUSTRATO | **INDECIDIBLE** |
| 5 | P2 da BLOQUEA, o P1b con alguna, o M da EMPEORA | **DECIDE NICOLÁS**, con la lista |
| 6 | P2 da GANA o EMPATE | **CANDIDATO** a la fase 3 |

PM-geo5 y PM-sens reciben el mismo cálculo como información.

## 7. Las otras dos patas (fijadas aquí, pre-registradas aparte)

- **Equivalencia (fase 3)**: la vía «código MIROVA» en `pipeline/` (flag, tag y sí de Nicolás; V750 primero) tiene que
  reproducir el PM de este censo pasada por pasada: misma publicación en el 100 % de las alertas y de los negativos que
  el PM publica, y `pc.vrp_mw` a 0,001 MW; en el resto, 99 % o más (elegido).
- **Sombra prospectiva**: la vía en un perfil de sombra con su `data_subdir` (A47) desde el 2026-11-03, con las reglas
  del §4 sobre la ventana P; su tamaño y su fecha de lectura se fijan en su propio pre-registro antes de mirar.

## 8. Controles (antes del resultado)

1. **K = producción**: en toda pasada, publicación y `pc.vrp_mw` a 0,001 MW; las diferencias en las que deciden se
   re-corren en su `codigo_sha` (como en MOD-B, `recorrer_en_sha.py`).
2. **PM = port de S159** en las pasadas del lote 39712862945 que están en la población (npix y VRP a 1e-6 MW).
3. **Cableado de M**: el placebo da d′ = 0 en todo par (si no, el cálculo de M está mal conectado).
4. **Nulo del contador** (fuera de línea): records del PM que publican, con `vrp_mw` = 0, dejan de publicar; 50
   negativos que no publican (semilla 162), con un cúmulo de cumbre de 0,3 MW a 0,5 km inyectado, pasan a publicar.
5. **Cobertura** (A108): los mismos 1.232 gránulos en todos los brazos; «volcán fuera del gránulo» y «escena inválida»
   fuera del denominador y contados aparte; sin pasadas repetidas.
6. **Referencia y población**: sha256 del `MANIFIESTO.json` y re-etiquetado desde la referencia congelada, como en MOD-B.

## 9. Costo (estimado; se mide en el humo)

Los 9,1 s por pasada MODIS de S159 incluyen búsqueda, descarga, port con sus 5 variantes y K
(`experiments/_s162_modis_negativos/04_costo_salida.txt`). Con K33 (+1,7 s) y sin repetir la descarga: 5.465 × 10,8 s
≈ **16,4 h** de runner como cota alta (las pasadas de un mismo gránulo comparten la descarga), más el arranque de 24 jobs
(~0,7 h). Despacho aparte de MOD-B, por la coordinadora, desde un tag, después del humo.

## 10. Lo que falta antes del sello (no es despachable sin esto)

1. **Evaluador** `evaluar_paquete.py` con pruebas que fallan contra un vacío y mutaciones con control de caída (S156),
   y ensayo en seco sobre el lote de S159.
2. **Arnés** del censo: el probe de PORTES envuelto (como MOD-C) para correr K, K33, PM, PM-geo5 y PM-sens sobre la
   población de MOD-B, guardando la fila y el frame del cráter para la costura.
3. **Candado**: blobs del port (`mirova_port.py 96769a89`, `probe_portes.py 8ec50e7b`, oráculo `07da7010`), de
   `evaluar_d25.py` en `ded217af4`, del arnés y del evaluador, y la referencia; tag defensivo.
4. **Workflow** con el molde de MOD-C (`"on":`, token, sólo lectura, blobs).
5. **Verificador limpio** del candado antes del despacho, y otro del resultado.
6. **Insumos que pueden cambiar el diseño**: el resultado de MOD-B (si MxD03 daña sobre K, el PM-geo5 pasa a decidir) y
   el de MOD-C (si el port refuta en `neg_resto`, este censo lo mide entero igual).

## 11. Decisiones para sellar (con recomendación)

1. ¿Censo con K, K33, PM, PM-geo5, PM-sens y placebo, sobre la población de MOD-B? **Sí.**
2. ¿P2 por `regla_signos_p2` (D-45) y M decidiendo sólo EMPEORA en el agregado? **Sí.**
3. ¿Chillán con su prueba propia (§5), al lado del veredicto? **Sí.**
4. ¿D28 fuera de los brazos hasta localizar el método y probarlo sin huecos? **Sí.**
5. ¿Construir el candado después de MOD-B y MOD-C? **Sí.**

## Adenda 1 (2026-10-24, informativa; aplicada por la coordinadora con D-48 sobre la recomendación de esta sesión)

Origen: el diagnóstico de las dos publicaciones del port que dejan INDECIDIBLE a MOD-C
(`experiments/_s162_modis_negativos/diagnostico/INFORME.md`): una era calor real del cráter (Láscar 2026-05-11 07:55,
visto esa noche por VIIRS de los tres satélites y alertado por MIROVA en VIIRS) y la otra un artefacto de gradiente a 63°
(Llaima 2026-07-24 01:05). **No cambia ninguna regla sellada**: P2 sigue contando toda publicación en un negativo limpio
como costo para la réplica.

Estrato informativo nuevo, para cada brazo y cada publicación en un negativo limpio o en `neg_resto`:
- **soporte independiente**: si otro sensor la ve la misma noche en otro gránulo (A109: la pasada del mismo gránulo no
  cuenta). Definición: un record nuestro de VIIRS 375 o VIIRS 750 (de cualquier satélite), o del otro MODIS, con cúmulo
  `summit` publicado por el predicado del tablero, a 6 h o menos de la pasada MODIS (la ventana de la vara VIIRS de la
  tarea 1.23 y de MOD-B), en el mismo volcán; y aparte, si MIROVA alertó en cualquier canal en esa ventana.
- **candidata a experimental**: la publicación con soporte independiente. Se lista con volcán, hora, cenit, VRP y los
  soportes; va al perfil experimental (valor agregado, se valida contra OVDAS y SWIR, A115), no a la réplica.
- Se informa la cuenta: publicaciones en negativos con soporte, sin soporte, y su reparto por cenit (≤ 40°, > 40°).

Láscar 2026-05-11 07:55 queda anotada desde ya como candidata a experimental (señal real que MIROVA calla en MODIS).
Esta adenda entra al evaluador del candado del §10 y pasa por el mismo verificador limpio antes del despacho.

## Adenda 2 (2026-10-24, informativa): la ablación real del bow tie

`experiments/_s162_modis_bowtie/real/INFORME.md` y su verificador: con datos reales, el método A (quitar los centros que
el barrido anterior ya cubre) no abre huecos y deja las 11 protegidas del lote de MOD-C intactas; la regla de filas de
borde (B) mataría una protegida de Chillán de 5,18 MW. El efecto no queda confinado al foco duplicado (pasa por la sigma
global del umbral de cumbre del oráculo) y los cambios de publicación ocurren al filo del umbral. Consecuencia para este
censo, sin cambiar ninguna regla sellada: si se agrega un brazo sin duplicados, es **PM-sin_dup con el método A**,
**informativo** (como PM-geo5 y PM-sens), y **nunca la regla B**. Agregarlo exige una adenda fechada antes del candado,
con el método A tal como está en `experiments/_s162_modis_bowtie/real/comun.py` y su blob.

## Adenda 3 (2026-10-25, informativa): lo que fija el candado al implementar

Escrita por la sesión de relevo de MODIS antes de despachar nada. **No cambia ninguna regla sellada** (población,
brazos, pruebas del §4, Chillán del §5, precedencia del §6, controles del §8). Fija lo que el texto sellado dejaba
abierto y que el evaluador tuvo que decidir para poder correr; cada punto pasa por el verificador limpio del candado.

1. **Árbol del censo**: rama `s162-modd-candado`, cortada de `s162-mxd03-codigo` (main congelado `80b819828`, el de
   MOD-B). Se le copiaron sin cambios los blobs sellados del port (`probe_portes.py 8ec50e7b`, `mirova_port.py
   96769a89`; el oráculo `07da7010` ya estaba igual en main) y `04_analizar.py` de S159. `evaluar_d25.py` de main es
   OTRA versión (blob `d26e215f`, sin `comparar_con_ganancia`): la del commit `ded217af4` (blob `1dbabf65`) va como
   `evaluar_d25_ded217af4.py` y el evaluador y el workflow comprueban su hash.
2. **Grilla por volcán**: `grillas.json`, la de los objetivos de S159 (igual a la de MOD-C), 11 volcanes.
3. **K**: el brazo de MOD-B (`probe_mxd03_ab.brazo`, misma función de producción y mismo main). Control 1 = el de MOD-B
   (`control_arnes` con la re-corrida en el `codigo_sha`, `recorrer_en_sha.py` sin cambios), más que el predicado del
   evaluador dé para K la misma publicación que el del runner. **K33**: el mismo brazo con
   `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA` parchado en `pipeline.process_modis` (lo lee al llamarse, `:600`).
4. **PM, PM-geo5, PM-sens**: `probe_portes.procesar` sin cambios, con `sin_k=True`, sobre los mismos archivos ya
   bajados (sólo `bajar_par` se reemplaza por enlaces duros: no hay descarga doble). Las variantes `pixel` y
   `fisica_b21` que el probe corre igual se guardan e informan.
5. **«Magnitud mostrada»** = la de `mirovaEqVrpDisplay` del predicado con node, en P1b (como dice el §4) y también en M
   (el §4 no lo dice para M; se elige lo mismo para medir lo que el operador ve; `pc.vrp_mw` de K va en el record).
6. **Pasadas no evaluables por el port** (estado del probe distinto de «ok», escena inválida o grilla con más de la
   mitad vacía) salen del denominador de TODOS los brazos (§8 control 5) y se cuentan por motivo. Una **protegida**
   que caiga ahí se lista junto al veredicto (informa; no la cuenta P1 porque el §8 la saca del denominador).
7. **P2**: las mitades de pasada partida cuya hermana es `sin_info` se cuentan (el §4 no las excluye, a diferencia de
   MOD-B); cuántas discordantes son de ese tipo se informa.
8. **Chillán, regla 5**: «pares» = pares sin empate exacto (la razón de la regla es la prueba de signos).
9. **Adenda 1**: «el otro MODIS» = el otro satélite; ventana ±6 h; «MIROVA alertó en cualquier canal» = una fila de
   alerta de la referencia congelada (regla SN), de cualquier sensor, del mismo volcán.
10. **Control 4**: además de (a) y (b), P2 del PM tiene que contar exactamente 50 errores más con la inyección.
11. **Control 2**: hay 149 pasadas del lote 39712862945 en la población; 148 evaluables (una con escena inválida sale
    del denominador, §8 control 5), 91 de ellas con píxeles del port; si ninguna común tiene píxeles, INDECIDIBLE.
12. **Informativos nuevos**: diagnóstico S-1 (`diagnostico_s1.py`: umbral de cumbre con la sigma de toda la grilla y
    con la de la ROI1, con identidad contra el oráculo en cada pasada); estrato «borde del gránulo» (VA61-01 del
    verificador de la A61: píxel MxD03 más cercano al cráter en la primera o última línea o frame); K33 igual a K; cruce
    del K de este censo con el de MOD-B.
13. **PM-sin_dup no se agrega**: pediría guardar el recorte nativo de cada pasada (0,3 a 0,7 MB, 1,6 a 3,7 GB en el
    censo, medido en MOD-C) y el método de MIROVA para D28 sigue SIN DATO. Queda para un lote propio.
14. **Humo** (rama `s162-modd-humo`, 5 gránulos): Láscar 2026-03-14 07:05 y Chillán 2026-10-16 01:40 (comunes con S159:
    el PM tiene que dar el npix y el VRP de S159), Láscar 2026-03-27 07:10 (protegida), Chillán 2026-10-10 07:40
    (expuesta) y Villarrica 2026-04-30 03:00 (cráter en el frame 0, VA61-01). El humo pasa si el job de pruebas sin red
    sale verde, las 5 pasadas tienen fila «ok», K reproduce data/ en las que deciden y el PM reproduce a S159 en las
    dos comunes. Recién entonces se piden las tres tandas.
