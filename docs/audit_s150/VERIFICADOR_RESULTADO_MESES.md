# Verificador con contexto limpio: `docs/S150_RESULTADO_MESES.md`

> Rama `s150-meses`, commit `c652d8f9f`. Verificado el 2026-10-03 por un agente que no produjo el resultado.
> Leí el pre-registro v3 (secciones 3 a 7 y la enmienda del recall), el documento y los ocho scripts. Todos los
> números de abajo los saqué corriendo cosas yo, no de los `.txt` de `resultados/`. Mis scripts están en
> `experiments/_s150_verificador/`; las extracciones y tablas, en el scratchpad de la sesión (no en el repo).

## Veredicto global

**El núcleo se sostiene: todos los números del documento se reproducen** (salvo un rango redondeado mal), las
reglas P1, P2, P5 y C8b están aplicadas como están escritas, el arreglo del gemelo es correcto y la separación
MODIS con banda 22 en Láscar es real. **Pero la lectura tiene tres huecos que cambian cómo se usa el resultado**:

1. Las dos pérdidas de agosto **no son un caso aislado**: las cinco alertas de 0,5 MW o más que `max` pierde en
   VIIRS 375 de mayo a agosto son todas del mismo tipo (Suomi NPP, sólo OCR, borde del barrido, B ya al 1 a 4 %
   de MIROVA). Mayo trae dos y junio una; la de junio cae después del 2026-06-13, en el tramo en que el OCR ya es
   confiable. La regla A119 las saca del veredicto en mayo y junio, y esa misma regla deja la etiqueta que decide
   casi ciega a Suomi NPP (H1).
2. `max` también recorta **alertas reales del borde**, nueve veces más que en el nadir (H2). El documento sólo
   cuenta la mitad buena de la selectividad por zona.
3. La comparación MODIS contra producción mezcla peras con manzanas: **en Láscar** producción publica 1 de 96
   negativos limpios, no 11,5 %. Con banda 22 sola (J) los falsos de Láscar suben de 1 a 11,5 % (H3).

Además, la columna "regla del pre-registro" del §0 dice MERECE SEGUIR en mayo, junio y julio aplicando la letra
anterior a la enmienda, mientras que para agosto invoca la enmienda como posible salida; la enmienda dice de sí
misma que "endurece el criterio, no lo afloja" (H4).

## 1. Afirmaciones revisadas

Comandos de base (desde la raíz del repo; `T` es una carpeta en el scratchpad):

```
python experiments/_s149_prereg_invierno/evaluar_ventana.py --nombre <mes> --desde ... --hasta ... \
  --control _s146_ab_sin_test1 --brazo _s147_ab_sin_test1_max --runs <run> \
  --gemelo _s149_ab_sin_test1_gemelo --runs-gemelo <run_gemelo> --tmp $T
```

con mayo 35599902448 y gemelo 35599941522, junio 35675490175 y 35679063864, julio 35728617326 y 35728872410,
agosto 35759688167 y 35766187578, abril 35639417826 sin gemelo. Para Láscar MODIS, `--control
_s149_ab_sin_test1_b22 --brazo _s149_ab_sin_test1_b22_max --sensor MODIS --control-gemelo _s146_ab_sin_test1`
con los runs de `despachos.log`.

| # | afirmación del documento | estado | cómo y qué obtuve |
|---|---|---|---|
| A1 | Negativos limpios V375, B a F: mayo 30,1 a 2,3; junio 32,8 a 1,5; julio 46,5 a 2,4; agosto 34,7 a 3,7 % | CONFIRMADO | `evaluar_ventana.py`, mismas cifras (n 349, 473, 505, 568) |
| A2 | Razón borde/nadir de F: 0,58; 0,27; 0,09; 0,04. Del control: 1,9 a 3,6 | CONFIRMADO | 0,58 / 0,27 / 0,09 / 0,04; control 2,33 / 2,94 / 3,57 / 1,87. Las cuatro zonas con 10 o más negativos |
| A3 | Recall que decide: mayo 187/195, junio 157/160 (tabla sola), julio 150/153 (tabla y OCR), agosto 110/120 con 2 pérdidas de 0,5 MW o más | CONFIRMADO | mismas cifras; pisos `ceil` 164, 134, 129, 101, todos superados. Ver H1 sobre lo que la etiqueta que decide deja fuera |
| A4 | P5: julio falla (0,40 contra 0,35); mayo, junio y agosto cumplen (0,36; 0,28; 0,21) | CONFIRMADO | 0,36 vs 0,62; 0,28 vs 0,49; 0,40 vs 0,35; 0,21 vs 0,34 |
| A5 | C8b cumple en los cuatro meses | CONFIRMADO | observado +0,88 / +0,91 / +0,93 / +0,81 contra p97,5 del nulo +0,49 / +0,50 / +0,50 / +0,41 (y la versión sin OCR también) |
| A6 | Veredictos de la columna "regla del pre-registro" | MATIZADO | Mecánicamente correctos con la letra de la sección 5 previa a la enmienda. Ver H4 |
| A7 | Agregado mayo a agosto: 692/1.895 (36,5 %) a 48 (2,5 %); F conserva 757/792 y 542/560 | CONFIRMADO | `agregado.py` sobre mis tablas: idéntico |
| A8 | Abril: cobertura despareja, falta Chaitén en B (3.082 contra 3.433) | CONFIRMADO | 74 + 139 + 138 = 351 pasadas de Chaitén sólo en F |
| A9 | Cobertura pareja junio, julio, agosto (3.520, 3.497, 3.135) | CONFIRMADO | idéntico |
| A10 | Determinismo 100 % en marzo, abril, junio, julio y agosto, en los tres sensores | CONFIRMADO, con dos matices | 285/285, 272/272, 275/275, 274/274, 253/253 en la decisión de publicar. Matices: mayo omitido (H5) y no es determinismo bit a bit (H6) |
| A11 | El defecto: comparar el gemelo contra J daba 90 % | CONFIRMADO | con el código viejo (sin `--control-gemelo`, control J) marzo da 257/285 = 90,2 %, FALLA |
| A12 | El arreglo es correcto y no cambia nada más | CONFIRMADO | diff de `c652d8f9f` sólo toca la referencia del gemelo; con `--control-gemelo` por defecto `dref` es el mismo perfil y runs que `dc`. Marzo con y sin el arreglo da predicciones idénticas línea por línea; agosto reproduce el `.txt` (generado con el código viejo) |
| A13 | MODIS Láscar, marzo a junio: B 0/73 y 0/96; J 68/73 y 11/96; K 67/73 y 2/96; Wilson [84,9; 97,0] contra [6,5; 19,4] para J y [83,2; 96,2] contra [0,6; 7,3] para K | CONFIRMADO, con salvedad de referencia | Reimplementación propia (`modis_lascar_independiente.py`: etiquetas escritas desde cero sobre los CSV, mi propio filtro de noche por elevación solar, mi propio Wilson; sólo reutilizo el predicado del tablero en node). Da exactamente esas cifras **si se incluye el respaldo del 2026-04-08**; con los CSV congelados solos da 71 positivas, J 66/71 y 12/96, K 65/71 y 3/96 (H8). Ninguna conclusión cambia |
| A14 | Regla de la sección 7: la única pérdida de K es 0,28 MW, Aqua, 2026-05-06; K no publica más que J; J publica más de la mitad | CONFIRMADO | pasada por pasada: K pierde sólo 2026-05-06 08:00 MODIS_AQUA 0,28 MW y no gana ninguna respecto de J; K ⊆ J |
| A15 | "Hoy MODIS en producción publica 11,7 % de las alertas contra 11,5 % de los negativos: no discrimina. Con banda 22, en Láscar, sí" | MATIZADO | Las dos cifras de AUDIT_S149 son reales, pero los negativos de producción son de los 11 volcanes (septiembre) y las positivas sólo de Láscar. En Láscar, marzo a junio, producción publica 8/73 alertas y **1/96 negativos** (H3) |
| A16 | §3, pasadas del 17 y 22 de agosto: cenit 63 y 59°, B 0,024 MW a 1,5 km y 0,018 MW a 0,3 km, F salta a 24,6 y 8,2 km; las otras pasadas de esas noches | CONFIRMADO | 63,4 y 59,2°; disp 0,024 y 0,018; F a 24,606 y 8,23 km. NOAA-20 05:18 (0,19 MW, cenit 40,6), NOAA-20 05:24 (0,23, 32,2), NOAA-21 06:12 (0,11, 49,5) publicadas por ambos; NOAA-21 06:06 del 17 es RUTINA. La tabla `latest.php` no tiene ninguna fila para las 05:00 del 17 ni para las 05:06 del 22 |
| A17 | §3, "En las otras tres ventanas, ninguna pérdida pasa de 0,5 MW con la etiqueta que decide" | MATIZADO | Cierto en la letra; esconde tres pérdidas del mismo tipo en mayo y junio (H1) |
| A18 | §3, "No es un problema general de Suomi NPP" (mediana B/MIROVA 0,56 a 1,00) | MATIZADO | Las medianas se reproducen (`magnitud_por_satelite.py`), pero miden la magnitud de B, no lo que `max` pierde. F pierde 23 % de las alertas de Suomi NPP sólo-OCR del borde (H1, H2) |
| A19 | Recall por tramo de magnitud (tabla del §2) | CONFIRMADO | `recall_por_magnitud.py` sobre mis tablas: las 20 celdas coinciden |
| A20 | "Los tramos bajo 0,10 MW son entre 21 y 33 % de las alertas de cada mes" | REFUTADO (menor) | 22,6 / 22,7 / 30,3 / 32,8 %: el rango es 23 a 33 |
| A21 | §4, VIIRS 750: P1 INDECIDIBLE los cuatro meses; 109/149 y 106/109; 8,6 a 1,1 %; pérdida de 0,5 MW o más en agosto; C8b falla en julio con 14 publicadas | CONFIRMADO | B en negativos 9,3 / 8,5 / 9,8 / 7,1 %; la pérdida de agosto es PuyehueCordonCaulle 2026-08-22 06:18, 0,65 MW, NOAA-21 750, **de la tabla** (falla P4 también sin OCR); julio C8b observado = p97,5 = +0,79 |
| A22 | La tabla de terminado pide 10 % focales y 15 % nevados | CONFIRMADO | AUDIT_S149 l. 167 |
| A23 | Pre-registro §5: "Los negativos limpios y el estrato de P5 salen siempre de la tabla, así que P1, P2 y P5 no cambian" | REFUTADO en el instrumento, sin efecto en veredictos | H7 |
| A24 | Perfiles: gemelo = B salvo nombre; J = B + banda 22; K = J + conectiva | CONFIRMADO (lo que se puede) | `diff_perfiles_s149_salida.txt` y `pipeline.profile` hoy dan eso; los registros MODIS de J y B difieren y los del gemelo y B no (salvo H6). Los flags impresos por el job de GitHub no están en los logs del repo: SIN VERIFICAR que el job los imprimió |

## 2. Hallazgos propios

### H1. Las pérdidas fuertes de `max` en VIIRS 375 son un patrón, no un caso de agosto. Gravedad 4

`experiments/_s150_verificador/perdidas_por_satelite.py` sobre las tablas de mayo a agosto. Todas las alertas de
0,5 MW o más que B publica y F pierde:

| pasada | MIROVA | canal | cenit | B | cúmulo de F |
|---|---|---|---|---|---|
| Lastarria 2026-05-02 05:06, Suomi NPP | 2,36 MW | sólo OCR | 59,5° | 0,033 MW a 1,0 km | 19,5 km |
| Isluga 2026-05-29 04:54, Suomi NPP | 0,86 MW | sólo OCR | 69,0° | 0,013 MW a 4,9 km | 18,6 km |
| Láscar 2026-06-25 04:54, Suomi NPP | 0,51 MW | sólo OCR | 66,9° | 0,014 MW a 0,2 km | 21,3 km |
| Láscar 2026-08-17 05:00, Suomi NPP | 0,60 MW | sólo OCR | 63,4° | 0,024 MW a 1,5 km | 24,6 km |
| Láscar 2026-08-22 05:06, Suomi NPP | 1,65 MW | sólo OCR | 59,2° | 0,018 MW a 0,3 km | 8,2 km |

Cinco de cinco con la misma firma. Con la etiqueta completa, mayo y junio **también fallan P4 por la letra** (2 y
1 pérdidas); sólo pasan porque la regla A119 hace decidir a la tabla sola en ventanas que empiezan antes del
2026-06-13. Y la de junio es del 25, **después** del 2026-06-13, en el tramo en que el OCR ya mide distancia y
geometría: la regla la saca del veredicto por la fecha de inicio de la ventana, no por la calidad de esa fila.

Lo que esto le hace a la lectura: (a) la frase "en las otras tres ventanas ninguna pérdida pasa de 0,5 MW" es
cierta en la letra y engañosa en el fondo; (b) la etiqueta "tabla sola" que decide mayo y junio es **casi ciega a
Suomi NPP**, justo el satélite donde está la pérdida: entre las alertas que B publica, Suomi NPP tiene 18 y 13 de
la tabla contra 55 y 44 sólo del OCR en mayo y junio; (c) el "SIN VERIFICAR" del §3 sobre si MIROVA da valores
raros en Suomi NPP al borde ahora tiene cinco casos para mirar, no dos, y define si el NO ADOPTAR de agosto
descansa en una clase de artefacto del OCR o de MIROVA. Un dato que apunta en esa dirección, sin probar nada: en
las dos filas OCR de agosto la distancia coincide con la de la pasada vecina (3,24 contra 3,23 km el 17; 1,22
contra 1,22 km el 22), y una hora después, en la misma geometría de Suomi NPP al borde, la tabla lista la pasada
como RUTINA con VRP 0 (06:42 del 17 y 06:48 del 22).

### H2. `max` también recorta alertas reales del borde, nueve veces más que en el nadir. Gravedad 3

Mismo script, agregando mayo a agosto, alertas V375 que B publica:

| zona (cenit del control) | B publica | F pierde |
|---|---|---|
| nadir (menos de 36°) | 410 | 5 (1,2 %) |
| medio (36 a 52°) | 190 | 9 (4,7 %) |
| borde (52° o más) | 192 | 21 (10,9 %) |

El §2 dice que con `max` "lo que queda está cerca del nadir, que es donde el píxel es chico y una anomalía tiene
más chance de ser real". Es la mitad de la historia: el recorte del borde también se lleva alertas reales que
MIROVA publicó, y para una réplica eso es pérdida de fidelidad. P2 mide la selectividad sólo en negativos
limpios; la cara en positivas no la mide ninguna predicción y debería ir al lado de P2 cuando Nicolás decida.

### H3. MODIS: la comparación con producción no es la misma población. Gravedad 3

`modis_lascar_independiente.py ... --produccion` sobre `data/mirova_equivalent/Lascar.json` (el de esta rama),
mismas 228 pasadas y mismas etiquetas:

| Láscar MODIS, marzo a junio | publica con alerta | publica en negativos limpios |
|---|---|---|
| producción hoy (banda 21 con Test 1) | 8 de 73 (11,0 %) [5,7; 20,2] | **1 de 96 (1,0 %)** [0,2; 5,7] |
| J (banda 22, sin Test 1) | 68 de 73 (93,2 %) | 11 de 96 (11,5 %) |
| K (banda 22 y `max`) | 67 de 73 (91,8 %) | 2 de 96 (2,1 %) |

El "11,5 % de negativos" de producción que cita el §0 es de los once volcanes en septiembre; en Láscar producción
casi no publica falsos. Leído contra la misma población: **J multiplica por once los falsos de Láscar** respecto de
producción y K por dos, a cambio de pasar de 11 a 92 % de recall. El argumento sigue a favor de K, pero "con banda
22 discrimina, hoy no" no es la comparación correcta, y J sola no sería una mejora en falsos. Salvedades que faltan
en el §5: (a) los records de producción de marzo a junio los escribió el código de esa época, no el de hoy; (b) 55
de las 73 positivas son de 0,5 MW o más y J publica las 55; en las 18 más débiles publica 13 (72 %), así que el
93 % es sobre todo detección de señal fuerte; (c) la sección 7 del pre-registro pide informar la **magnitud
pareada** y el documento no la da: la mediana de nuestro VRP sobre el de MIROVA es 0,50 en J (n 68, p25 0,31, p75
0,70) y 0,53 en K; (d) las 73 positivas caen en 62 noches y los 96 negativos en 56: Wilson supone independencia,
pero la separación es tan grande que no cambia.

### H4. La enmienda del recall se aplica en una sola dirección. Gravedad 3

La enmienda dice que en VIIRS el veredicto de recall lo da Nicolás mirando la tabla por tramo y que "endurece el
criterio, no lo afloja". El §0 marca MERECE SEGUIR en mayo, junio y julio con la letra anterior (que sólo mira el
corte de 0,5 MW y el piso `ceil`), y en agosto presenta la enmienda como lectura alternativa que podría salvarlo.
Bajo la propia cláusula de la enmienda, agosto no puede salir del NO ADOPTAR por ella, y mayo a julio no son MERECE
SEGUIR hasta que Nicolás vea la tabla por tramo, que muestra que F pierde entre 25 y 44 % de las alertas de menos
de 0,05 MW (B publica 87 a 100 %). Sugerencia: cambiar la columna a "P1, P2, C8b cumplen; recall: pendiente de
Nicolás (por la letra: cumple, cumple, cumple, falla)".

### H5. El determinismo de mayo quedó sin cerrar y se omitió. Gravedad 2

Mayo estaba "pendiente" en `docs/S149_RESULTADO_CONECTIVA_MAYO.md` y en su verificador. El S150 lista el
determinismo de los otros cinco meses y no menciona mayo. Corrido: el gemelo 35599941522 coincide 282 de 282, pero
**le falta la noche del 2026-05-03** (10 pasadas; su log muestra `SEARCH_CMR_TIMEOUT` en esa fecha), así que
`evaluar_ventana.py` lo marca "FALLA: INDECIDIBLE" por cobertura. No es falta de determinismo, es A108; pero por la
regla de la sección 5 mayo queda INDECIDIBLE hasta repetir ese job corto o hasta que se declare que la cobertura
del gemelo no cuenta.

### H6. El reproceso no es determinista bit a bit. Gravedad 2

`determinismo_crudo.py`, record por record, ignorando `processed_utc` (que difiere en todos: los gemelos son
reprocesos de verdad, no copias). Marzo, abril, mayo y julio: idénticos. **Junio y agosto no**: `diag_mu_deti`
difiere en 268 de 275 y 246 de 253 records (error relativo del orden de 1e-13), y en 2 y 5 records MODIS cambia el
conjunto de píxeles anómalos en 1 o 2 píxeles y `vrp_mir_mw` en 1 a 2 %. No hubo cambios de código en `main` entre
los despachos, así que es aritmética de punto flotante del runner. La decisión de publicar no cambió en Láscar,
pero el 100 % se midió sólo en Láscar, que es fuerte; en un volcán débil, donde `max` actúa justo sobre píxeles al
borde del umbral, un píxel puede cambiar de lado entre corridas. No invalida nada; conviene decir "determinista en
la decisión, en Láscar" y no "el código es determinista".

### H7. La "tabla sola" del instrumento no es una reetiquetación con la tabla sola. Gravedad 2

En `banco_paridad.etiquetar`, un negativo limpio exige que la noche no tenga alerta **de ninguna fuente**, y el
estrato de P5 usa `noche_con_alerta_sensor` con OCR incluido. La variante "tabla sola" de `medir_predicciones.py`
sólo quita las positivas sólo-OCR. Reetiqueté de verdad pasando a `armar_tabla.py` un OCR vacío (sólo cabecera):
mayo F en negativos 2,3 a 3,7 % y P2 0,58 a 0,82; junio 1,5 a 2,2 % y 0,27 a 0,40; julio P5 0,35 contra 0,35, sigue
fallando; agosto igual. **Ningún veredicto cambia**, pero la frase del pre-registro "los negativos limpios y el
estrato de P5 salen siempre de la tabla" es falsa tal como está implementada.

### H8. La referencia "congelada" no es la única entrada. Gravedad 1

`armar_tabla.py` llama a `cargar_referencia_unificada` con el respaldo por defecto
(`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv`), que no está en el
manifiesto de `_congelado/`. En marzo y abril aporta filas que la congelada perdió (por ejemplo, ALERTA de Láscar
MODIS del 2026-03-04 07:15, 03-14 07:05, 03-19 01:55 y 04-05 01:35) y cambia el sustrato MODIS de 71 a 73
positivas y un negativo de abril pasa a positiva. El respaldo es un archivo histórico fijo, así que el resultado es
reproducible, pero el manifiesto debería nombrarlo.

### H9. Rango mal redondeado. Gravedad 1

A20: "entre 21 y 33 %" es "entre 23 y 33 %".

## 3. Lo que no verifiqué

- Que el job de GitHub imprimiera `conectiva_prosa`, `caja_roi1` y `modis_b22` (requisito de despacho): los logs
  guardados en las ramas `s146-ab/*` no traen esas líneas. SIN VERIFICAR.
- Las imágenes de MIROVA de las cinco pasadas de H1: no toqué el repo Mirova-v1. SIN VERIFICAR.
- MODIS J y K en los otros diez volcanes: no existe el despacho. SIN VERIFICAR (el documento ya lo dice).
- Septiembre y el agregado con septiembre: fuera del alcance de este documento.

## 4. Scripts

- `experiments/_s150_verificador/perdidas_por_satelite.py`: H1 y H2.
- `experiments/_s150_verificador/modis_lascar_independiente.py`: A13, A14, H3, H8 (etiquetas propias; sólo el
  predicado del tablero en node es compartido).
- `experiments/_s150_verificador/determinismo_crudo.py`: H6.
