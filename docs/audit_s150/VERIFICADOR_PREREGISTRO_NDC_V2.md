# Verificador del pre-registro S150 de Nevados de Chillán, versión 2

Verificador con contexto limpio. Objeto: `experiments/_s150_ndc/PREREGISTRO_NDC.md` versión 2, el evaluador
`experiments/_s150_ndc/medir_ndc.py`, su prueba `probar_medir_ndc.py`, los perfiles `pipeline/profiles/_s150_*.yaml`,
`diff_perfiles_ndc_salida.txt` y el cambio del workflow `reproc-s146-ab-sin-test1.yml`. Rama `s150-ndc`, commit
`b1cb2a00e` (comprobado con `git branch --show-current` y `git log -1`). No modifiqué nada del repo salvo este informe
(`git status` igual al de partida). Todo lo que corrí escribió en el scratchpad de la sesión.

## Veredicto

**No se puede despachar tal cual el 2026-10-13. Se puede con cambios acotados** (evaluador y texto de P5; ningún
brazo nuevo ni rediseño), seguidos de una nueva corrida de `probar_medir_ndc.py` con los controles que faltan.

La v2 corrige de verdad los dos defectos de diseño de la v1 (E ya no es candidato, P4 ya no culpa a la banda 22 de
una pérdida de etiqueta), el evaluador existe, reproduce el sustrato del §3 y sus seis controles pasan. Pero tiene
cuatro defectos de gravedad 3 que hacen que un verde o un rojo no signifique lo que el pre-registro dice:

1. P5 **sí puede fallar, pero por un mecanismo distinto del que el pre-registro anuncia** y en la dirección opuesta a
   la que sugiere su lectura: el tope D9 no toca `isSummitDetection`, toca el filtro de artefacto cirrus del tablero
   (N1). Y P5 compara dos jobs distintos con tolerancia cero y sin gemelo, así que el ruido del reproceso la hace
   fallar sola (N2).
2. **El evaluador da verde sobre un brazo que no aplicó su flag**, salvo E: el propio nulo lo muestra (T0 igual a
   producción da P5 CUMPLE; B igual a producción daría P2 CUMPLE) (N3).
3. **El control del cableado de E exige igualdad exacta de punto flotante entre dos jobs**, y el reproceso ya se midió
   no determinista bit a bit: lo más probable es que acuse "cableado roto" y deje E, KE y KET INDECIDIBLES por ruido (N4).
4. **El descuento por el gemelo hace desaparecer pérdidas en vez de volverlas indecidibles**, y el gemelo sólo mide el
   ruido de B, no el de C0 ni el de F (N5).

## 1. Lo que se verificó y está bien

- `diff_perfiles_ndc_salida.txt`: cada par difiere sólo en lo declarado (más `DATA_SUBDIR` y `PROFILE_NAME`).
  `PATH_D_ONLY_CAP_MW` resuelve a `None` en T0 y KET leído desde `pipeline.profile` (A89 no aplica), y los tres
  procesadores tratan `None` como tope apagado (`process_modis.py:1010`, `process_viirs.py:1415`,
  `process_viirs_mod.py:988`, `path_d_cap.py`).
- El workflow difiere de `origin/main` sólo en las dos líneas que imprimen `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`
  y `PATH_D_ONLY_CAP_MW` (`git diff origin/main`).
- Corrí `probar_medir_ndc.py` con un directorio mío: **rc 0, seis de seis OK**, igual que dice el §4. Corrí además
  `medir_ndc.py` directo sobre el nulo para ver las secciones 0 a 4 que la prueba trunca (imprime sólo los últimos
  6000 caracteres). El sustrato que imprime coincide con el §3: MODIS 3 alertas en actividad (2 de 1 MW o más), 28
  negativos limpios en reposo y 5 en actividad; VIIRS 375 11 (8); VIIRS 750 8 (6).
- Las claves de `crudos()` (`VOL|bucket|datetime_utc[:16]`) y de `armar_tabla` (`ev.clave`, `strftime('%Y-%m-%d
  %H:%M')`) coinciden en formato y usan el mismo `bp.bucket`. `crudos()` no filtra diurnas, pero eso sólo amplía la
  cobertura y la comprobación de versión; no produce falsos verdes.
- Todos los pares que el código usa están en `PARES` y se calculan. Sobra uno: `(K, KE)` se calcula y no lo usa nadie
  (ver N3).
- La fórmula esperada del control 4 (`summit` si el centroide del cúmulo está a 5 km o menos) coincide con lo que hace
  el pipeline: `derivar_distance_class` (`process_modis.py:300`) más el rescate F47 y el guard A46 de `store.py:347 a
  485`; la regla D no entra porque el camino vent está apagado en `mirova_equivalent` (`vent_path=off`). El inner de
  `volcanoes.yaml` (5 km) y el del HTML son el mismo.
- Diez jobs caben: matrix de 1 volcán por 10 perfiles, `max-parallel: 6` (dos tandas), `timeout-minutes` 330 por job y
  300 por paso, `recolectar` cuenta la cobertura contra el control que se pase por entrada y publica la rama antes del
  guard final.

## 2. Hallazgos de la v1

| hallazgo v1 | estado | evidencia |
|---|---|---|
| H1 (4): E no podía fallar | **CORREGIDO** para E; **PARCIAL** para KE | E pasa a control de cableado y su costo medido está en el §1 (la sección 7 del evaluador lo reproduce: 22 de 28 en reposo, 5 topadas). KE sigue siendo candidato sin criterio de costo: puede "seguir a 11 volcanes" publicando lo mismo que E en reposo. Es una decisión defendible para una prueba de estrés, pero hay que escribirla como tal. |
| H2 (3): P4 culpaba a la banda 22 | **CORREGIDO** en la atribución; sustrato casi vacío | P3 por pares, P4 sólo KE y KET. Pero las pérdidas MODIS exigen que el control publique, y con la etiqueta histórica B publica **una sola** alerta MODIS de 1 MW o más (2026-10-01 01:45; la de 08:35 está `far` en B, J y K). P3 mide la banda 22 y `max` sobre n = 1 (N8). La reetiqueta offline que proponía la v1 no se hizo. |
| H3 (3): sustrato | **CORREGIDO** | Lo cuenta el evaluador con `banco_paridad`; las cifras del §3 se reproducen. |
| H4 (3): no había evaluador | **CORREGIDO, con reservas** | Existe y está probado, pero sólo con un positivo de P1 y uno de cableado: no hay positivo para P2, P3, P4 ni P5, ni el caso "brazo que no aplicó el flag" (N3, N9). |
| H5 (3): NRT y estándar | **PARCIAL** | Fecha de despacho desde el 10-13 y control 2. El control sólo bloquea las alertas de 1 MW o más; una mezcla en cualquier otra pasada entra igual a P5 y al determinismo, que no tienen tolerancia (N2). |
| H6 (3): cadena y ruido | **PARCIAL** | P1 se compara también contra C0. El descuento por el gemelo esconde pérdidas en vez de declararlas indecidibles, y no dice si un brazo construido sobre uno vetado hereda el veto (N5). |
| H7 (2): control positivo | **PARCIAL** | Se implementó la identidad E igual a C0 reetiquetado, pasada por pasada, como pedía la v1. Pero con igualdad exacta de `pc.vrp_mw` entre dos jobs (N4), y sólo para E, no para KE (N3). |
| H8 (2): perfiles y flag | **PARCIAL** | Despacho desde `main` y el workflow imprime los dos flags. No se agregaron al `assert`, y el evaluador no lee ese log. |
| H9 (2): "13 alertas" | **CORREGIDO** | El §1 dice 11 y el evaluador da 11. No dice qué script produce las cifras del §1 (las de MODIS y del tope vienen de los auditores). |
| H10 (2): P7 censurada | **PARCIAL** | La sección 8 no separa las pasadas topadas. Y la promesa "T0 y KET dan la magnitud sin tope" no se cumple: la sección 8 sólo mira positivos publicados, y ninguna pasada topada de producción es positiva (N6). |
| H11 (2): cobertura de alertas fuertes | **PARCIAL** | El control 1 sólo mira las alertas que C0 tiene. Una alerta sin record en C0 (como la MODIS del 2026-10-05 07:50, que no está en producción) no aparece en ninguna parte: en el nulo, P4 cuenta "2 de 2" sin avisar que falta la tercera. No se listaron las alertas esperadas. |
| H12 (1): insumos que se mueven | **PARCIAL** | Referencia congelada desde el remoto con sha (bien). No se guarda el sha de `index.html` ni del `NevadosDeChillan.json` usado en el §1, y el control 5 del §4 ("identidad del predicado") **no lo corre nadie**: `medir_ndc.py` no llama a `control_identidad_predicado` y `armar_tabla.py` tampoco (N7). |
| H13 (1): "una hora" | **NO CORREGIDO** | El §2 sigue diciendo "del orden de una hora cada uno"; el workflow estima 1,5 a 3 h y con dos tandas son del orden de 3 a 6 h. |
| H14 (3): tope D9 | **PARCIAL** | Brazos T0 y KET, P5 y columna de topadas en P6. Pero P5 está mal razonada (N1), es frágil al ruido (N2) y T0 casi no puede informar nada (N6). |
| H15 (2): `final_hotspot` descartado | **CORREGIDO** | Salvedad en el §6 y la sección 9 informa la distancia del cúmulo, no la del `final_hotspot`. |

## 3. Hallazgos nuevos

### N1. P5 puede fallar, pero por el filtro de artefacto cirrus, no por `isSummitDetection`, y su falla significa lo contrario de lo que sugiere el texto. Gravedad 3

**El fenómeno.** El tope recorta a 5 MW la magnitud de un cúmulo contextual sobre fondo frío. El tablero tiene, aparte,
un filtro que esconde como "artefacto cirrus" todo cúmulo cuyo píxel más caliente está bajo 0 °C y cuya magnitud pasa de
10 MW (`isCirrusArtifact`, `frontend/index.html:1207`; y el de campo difuso, 50 MW). Con el tope puesto, ningún cúmulo
topado puede pasar de 10 MW, así que **el tope desactiva el filtro cirrus**: deja ver como "5,00" lo que sin tope el
tablero escondería como artefacto.

**Evidencia.**
- El predicado que usa el evaluador es `summit && valid && !art && disp > 0` (`scripts/banco_paridad.py:125 a 129`).
  `isSummitDetection` (`index.html:1480`) sólo mira `vrp_mw === 0`, y el tope nunca lleva a cero. El camino real es `art`.
- En la ventana hay 11 records MODIS topados en producción; **ninguno es una alerta de MIROVA**: 10 son negativos
  limpios y 1 `sin_info` (cruce con la tabla de C0 contra E del nulo). Sus `t_max_k` van de 252 a 279 K; 9 de 11 están
  bajo 273,15 K. Sus sumas de escena antes del tope (`vrp_mir_mw`) van de 40 a 74 MW.
- Pasé esos records por el predicado de node con la etiqueta desde el cúmulo y la magnitud del cúmulo en 5,0, 9,9 y
  12 MW: con 5,0 publican 9; con 12 MW, **7 de esos 9 pasan a `art = 1` y dejan de publicarse** (todos los de `t_max`
  bajo 0 °C). La magnitud real sin tope no la conozco (SIN VERIFICAR), pero las sumas de escena sugieren que pasa de 10.
- Consecuencia: en el par KE contra KET, P5 probablemente falla, y la falla quiere decir "el tope está haciendo visibles
  falsos positivos en reposo", no "el tope recorta una erupción". El texto del §5 ("afecta `isSummitDetection`, que lee
  `vrp_mw`") daría la lectura equivocada. En el par C0 contra T0, en cambio, los 11 topados de producción están `far`,
  así que P5 sólo puede fallar por ruido (N2): es casi vacía.

**Corrección.** Reescribir P5 como predicción con dirección y mecanismo: "en las pasadas donde el control está topado,
quitar el tope no cambia la decisión de publicar; si la cambia, se informa en qué dirección, en qué etiqueta (alerta,
negativo limpio, `sin_info`) y por cuál de los tres términos del predicado (`summit`, `valid`, `art`)". Que el
evaluador imprima esos tres términos (ya los devuelve `correr_node`) en cada cambio. Decir en el §1 que el tope no
recortó ninguna alerta de MIROVA en producción (ver N6).

### N2. P5 y el determinismo MODIS no toleran ni una diferencia, y el reproceso no es determinista bit a bit. Gravedad 3

**Evidencia.** P5 cuenta "decisiones de publicar distintas" sobre **todas** las pasadas de dos jobs distintos, con
umbral cero y sin descuento (`medir_ndc.py:198 a 204`). El verificador de resultados de S150 (H6,
`docs/audit_s150/VERIFICADOR_RESULTADO_MESES.md:156 a 165`) midió que dos gemelos cambian el conjunto de píxeles MODIS
en 2 a 5 records por mes en Láscar, por aritmética del runner. En NdC con cúmulos de decenas a cientos de píxeles, un
solo cambio de decisión basta para declarar "el tope decide publicación". Lo mismo con el determinismo MODIS: con 39
pasadas, 98 % exige 39 de 39 (`medir_ndc.py:142`), o sea tolerancia cero, cosa que el pre-registro no dice.

**Corrección.** Evaluar P5 **sólo en las pasadas donde el control tiene `d9_capped`** (las únicas donde el tope actuó) y
usar las demás como control de determinismo del par: ahí C0 y T0 tienen que coincidir, y si no coinciden P5 es
INDECIDIBLE, no FALLA. Lo mismo para KE contra KET. Para el determinismo MODIS, escribir en el §4 que 98 % sobre 39
pasadas es cero diferencias, o fijar el umbral en pasadas y no en porcentaje.

### N3. El evaluador da verde sobre un brazo que no aplicó su flag (salvo E). Gravedad 3

**Evidencia.** El control 4 sólo existe para E. En el nulo de `probar_medir_ndc.py`, T0, B, F, J, K, KE y KET son copias
de producción, es decir, **exactamente lo que se vería si ninguno hubiera leído su flag**, y la salida da `CONTROLES:
OK`, P1, P2, P3 CUMPLE y `P5_T0` CUMPLE. O sea que un T0 que no quitó el tope cumple P5, y un B que no apagó el Test 1
cumple P2, en verde. El caso de KE es el más serio: si el flag de etiqueta no llegara, P4 fallaría (en el nulo, KE sin
reetiquetar da "1 de 2", sección 6) y el veredicto culparía al candidato completo de un defecto de cableado. El par
`(K, KE)` se calcula y no se usa. El workflow imprime los flags pero no los afirma, y el evaluador no lee el log.

**Corrección.** Controles de cableado baratos, desde los records, para cada brazo que pueda darse vuelta:
- **T0 y KET**: cero records con `d9_capped`, y al menos una pasada donde el control está topado y el brazo da
  `pc.vrp_mw` mayor que 5.
- **KE**: la misma identidad que E, pero contra K.
- **B, F, J, K**: cero records con `triggered_test1`, o el contador de diagnóstico del camino Test 1 en cero (el que
  corresponda; SIN VERIFICAR cuál persiste el pipeline hoy).
- Y que el evaluador lea la línea "El brazo LEE" de cada log del run (están en `salidas/logs`) y la compare con el perfil.
Agregar a `probar_medir_ndc.py` un positivo con T0 igual a producción, que tiene que dar "cableado roto" y no CUMPLE.

### N4. El control de cableado de E exige igualdad exacta entre dos jobs, y lo más probable es que acuse "roto" por ruido. Gravedad 3

**Evidencia.** `medir_ndc.py:158`: `e["pc_vrp"] != c["pc_vrp"]` y `e["d9"] != c["d9"]` sobre **todos** los records,
incluidos VIIRS. E y C0 son reprocesos independientes; con el no determinismo medido (N2) basta un píxel de diferencia en
un cúmulo para que `malE` no quede vacío. Entonces el evaluador declara "CABLEADO ROTO: INDECIDIBLE para E y KE" (y KET
por el §4.4), es decir, **todo el candidato MODIS indecidible por ruido de punto flotante**. La prueba no lo detecta
porque su E es una copia reetiquetada de producción, idéntica por construcción.

**Corrección.** La identidad se exige sobre la **etiqueta**, en las pasadas donde E y C0 tienen el mismo cúmulo (mismo
centroide a la precisión guardada); las diferencias de magnitud se informan como determinismo, con tolerancia declarada.
Que la falla del cableado exija una pasada con mismo cúmulo y etiqueta distinta de la esperada, que es lo único que un
cableado roto produce.

### N5. El descuento por el gemelo hace desaparecer pérdidas en vez de declararlas indecidibles, y el gemelo no es pertinente para todos los pares. Gravedad 3

**Evidencia.** `difiere_gb` son las pasadas donde B y G deciden distinto, y se descuentan en **todos** los pares
(`medir_ndc.py:170 a 178`), incluidos C0 contra F, C0 contra B, B contra J y J contra K. El veredicto sólo mira las
netas, así que una pérdida descontada da CUMPLE. El gemelo mide el ruido de B; no dice nada del ruido de C0, ni del de F
(`max` actúa justo sobre píxeles en el borde del umbral), ni del de J y K (otra banda primaria). Respuesta a la pregunta
3: **sí puede esconder una pérdida real de F contra C0**. Si en una alerta fuerte B publica y G no, la pasada está en el
borde para el detector sin Test 1; si F también la pierde, la pérdida se descuenta aunque `max` pueda ser la causa, y
aunque contra C0 (producción, lo que el operador ve hoy) sea una alerta de 1 MW o más que se deja de publicar. Con unas
24 alertas fuertes en VIIRS y un veto de cero, una sola pérdida escondida cambia el veredicto.

**Corrección.** Una pérdida en una pasada donde el gemelo cambia no es CUMPLE: es **INDECIDIBLE para esa predicción**,
listada con la pasada. Aplicar el descuento sólo a los pares cuyo brazo comparte el detector con B (C0 contra B, B contra
F para la parte de B), nunca a pares MODIS con banda 22. Escribir en el §5 que un brazo construido sobre uno vetado
hereda el veto (o por qué no).

### N6. El tope no recortó ninguna alerta de MIROVA en producción, y T0 no puede informar la magnitud sin tope que promete. Gravedad 2

**Evidencia.** De los 11 MODIS topados (09-20 a 10-02), ninguno coincide con una alerta de MIROVA (N1). Las tres alertas
MODIS de la ventana (09-29 07:20, 10-01 01:45 y 08:35) no están topadas. La sección 8 del evaluador sólo calcula la
razón de magnitud sobre positivos publicados, así que T0 da exactamente la misma razón que C0 (en el nulo, idénticas) y
las magnitudes sin tope de las pasadas topadas no aparecen en ninguna parte. El comentario de
`_s150_sin_tope_d9.yaml` ("una erupción real de más de 5 MW sobre un fondo frío se publica como 5,00") y el §1 sugieren
lo contrario de lo que muestran los datos.

**Corrección.** En el §1 decir que el tope actuó sólo en pasadas sin alerta. En P7, agregar una tabla cruda (sin
predicado) con `pc.vrp_mw` de C0 y T0 en cada pasada topada, su etiqueta de MIROVA y `t_max_k`; y separar las topadas
en la razón de magnitud, como pedía H10.

### N7. El control 5 del §4 no existe en el código, y el veredicto JSON no respeta el control 4. Gravedad 2

**Evidencia.** El §4.5 lista la identidad del predicado como control, pero ni `medir_ndc.py` ni `armar_tabla.py` llaman a
`bp.control_identidad_predicado` ni registran el sha de `frontend/index.html`. Y `controles` (`medir_ndc.py:167`) no
incluye `cableado_etiqueta_ok`: con el cableado roto, `veredicto["P4_KE"]`, `P4_KET` y `P5_KET` se escriben igual como
CUMPLE o FALLA en el JSON, aunque el texto impreso diga INDECIDIBLE.

**Corrección.** Llamar a `control_identidad_predicado` al inicio, guardar el sha de `index.html` y del JSON de
referencia en la salida, y escribir INDECIDIBLE en el JSON para toda predicción cuyo control no pasó.

### N8. P3 y P4 se deciden sobre una o dos alertas, y el pre-registro promete atribuir. Gravedad 2

**Evidencia.** Sección 6 del nulo: P4 sobre 2 alertas MODIS de 1 MW o más (la del 10-05 07:50 no tiene record en
producción). P3 compara pérdidas donde el control publica, y con la etiqueta histórica B publica sólo la de 01:45. El §1
dice que la prueba "responde qué parte del MODIS falla en una erupción: el detector, el tope o la etiqueta".

**Corrección.** Declarar el n esperado de P3 y P4 en el §5. Para separar detector de etiqueta con más sustrato, medir
P3 con la etiqueta neutralizada (cúmulo con magnitud dentro del inner, o reetiqueta offline de B, J y K, que es exacta
porque la etiqueta no entra aguas arriba). Rebajar la frase del §1 a "aporta evidencia".

### N9. La prueba del evaluador no cubre lo que el §4 afirma, y su salida oculta los controles. Gravedad 2

**Evidencia.** `probar_medir_ndc.py:48` imprime sólo los últimos 6000 caracteres, así que las secciones 0 a 4 (los
controles) no se ven en la salida de la prueba. En su "nulo", KE y KET son producción sin reetiquetar y dan P4 FALLA, un
veredicto que el resumen no revisa. No hay positivos para P2, P3, P4, P5, para la mezcla de versión de producto, ni para
una alerta sin record en C0.

**Corrección.** Imprimir la salida completa (o escribirla a archivo), construir KE y KET del nulo como K reetiquetado, y
agregar un positivo por predicción y por control (incluidos los de N3 y N4), cada uno con su resultado esperado
escrito antes de correrlo.

### N10. Insumos que no se pueden verificar desde aquí. Gravedad 1

- El token "rotado el 2026-10-08, vence el 2026-12-07" (§7): SIN VERIFICAR. A las 18:47 UTC del 10-08 el NRT tenía
  cuatro corridas seguidas en `failure` (07-oct 19:44 a 08-oct 17:11) y una en curso desde las 18:08. Antes de despachar,
  comprobar que esa corrida o una siguiente terminó verde.
- Que el producto estándar cubra hasta el 10-07 el 10-13: plausible por la latencia que documenta `fetch.py:167`, SIN
  VERIFICAR. Ojo con un caso que el control 2 no ve: si el estándar de un día está **parcialmente** publicado,
  `search_granules` devuelve lo parcial y no cae al NRT (`fetch.py:505 a 538`), y el brazo queda con pasadas de menos;
  lo atrapa el control 1, no el 2.
- H13 sigue: corregir la duración en el §2.

## 4. Respuestas a las cinco preguntas

1. **Prueba y caminos a un verde falso.** La prueba pasa seis de seis y sus dos positivos prueban lo que dicen (P1 veta
   la pasada sembrada; E sin reetiquetar acusa cableado). Caminos a verde sobre un brazo roto: cualquier brazo distinto
   de E que no haya aplicado su flag (N3, demostrado por el propio nulo); una alerta fuerte sin record en C0 (H11); una
   pérdida descontada por el gemelo (N5). Las claves de `crudos()` y `armar_tabla` coinciden y todos los pares usados
   se calculan.
2. **P5 con el sustrato que hay.** Puede fallar de verdad en KE contra KET, por el filtro cirrus del tablero
   (`isCirrusArtifact`, magnitud del cúmulo sobre 10 MW con `t_max` bajo 0 °C), no por `isSummitDetection`; en C0
   contra T0 sólo puede fallar por ruido, porque todos los topados están `far` (N1, N2).
3. **Gemelo.** Sí, puede esconder una pérdida real de F contra C0 (N5).
4. **NRT y estándar.** La fecha y el control 2 resuelven la mezcla en las alertas fuertes. Dentro de un brazo no hay
   mezcla: el directorio del brazo arranca vacío y `store.py:620` sólo reemplaza NRT por estándar dentro del mismo
   archivo. Entre brazos, la mezcla en pasadas no fuertes sigue entrando a P5 y al determinismo (N2).
5. **Lo que falta.** Controles de cableado para T0, KET, KE y B (N3); P5 restringida a las pasadas topadas con dirección
   y mecanismo (N1, N2); tabla cruda de magnitud sin tope (N6); el control 5 implementado (N7). Diez jobs caben en el
   workflow, en dos tandas de 6 y 4.

## 5. Scripts y salidas de este informe (en el scratchpad, no en el repo)

- `probe_salida.txt`: salida cruda de `probar_medir_ndc.py`.
- Salida de `medir_ndc.py` corrido directo sobre el nulo (secciones 0 a 4).
- Cruce de los 11 records topados con la tabla C0 contra E del nulo, y el paso de esos records por `bp.correr_node` con
  magnitud 5,0, 9,9 y 12 MW (N1).
