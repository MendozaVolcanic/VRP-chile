# Frente D: veredictos viejos bajo lo que hoy sabemos (auditoría S149)

> Auditor del frente D, 2026-09-21. Sólo lectura sobre el repo. Scripts y salidas en
> `experiments/_s149_audit/frente_d/` (`d1` a `d5`, cada uno con su `*_salida.txt`). Los datos del A/B
> sin Test 1 se extrajeron con `git archive origin/s146-ab/35521542153 <ruta>` al directorio temporal
> de la sesión (50 MB, fuera del repo). No se corrió pytest, no se despachó nada, no se tocó git.
>
> **Cómo leer la confianza.** Lo que dice "medido" sale de un script mío de esta sesión. Lo que dice
> "leído" lo leí yo en el archivo y línea citados. Lo que dice "censo delegado" lo leyó un subagente de
> esta sesión con cita de archivo y línea y yo no lo releí: vale como puntero, no como verificación.
> El tramo S124 a S133 lo cubrí yo por búsqueda dirigida (el subagente de ese tramo no entregó): su
> cobertura es PARCIAL y está declarada al final.

## 0. En una pantalla

1. **El A/B sin Test 1 (S147) CAE como veredicto.** De sus tres criterios fallados, C7 ya estaba caído
   (S148). Los otros dos, C2 y C4, son **el mismo fenómeno y no es de detección**: al apagar el Test 1
   desaparece el recómputo de magnitud que el Test 1 hace con su propio fondo, y la magnitud vuelve a
   calcularse contra el anillo regional (D25), que en cumbres frías da exceso cero. Medido: de las 6
   alertas "perdidas", **4 siguen detectadas en el cráter, en el mismo píxel, con 0,0 MW**; sólo 2 son
   pérdida de detección (0,06 y 0,05 MW). Y en los 44 pares donde baja la magnitud, el cúmulo tiene los
   mismos píxeles o más, en el mismo lugar.
2. **Con los criterios corregidos**, el brazo sin Test 1 da en VIIRS 375: negativos limpios 86,1 a
   28,7 %; negativos de pasada en noche con alerta (el estrato que el negativo limpio esconde) 90,6 a
   50,9 %; C8b cumplido (0,624 contra 0,398); recall por tramo: pierde 5 de 38 entre 0,05 y 0,10 MW,
   1 de 41 entre 0,10 y 0,20 MW y ninguna sobre 0,20 MW. El "100 % de recall" del control es el recall
   de un detector que publica el 86 % de todo: no es un mérito (A114 por el lado del recall).
3. **La palanca que sale de esto es D25 (fondo por vecinos), y sus dos veredictos viejos caen**: el de
   VIIRS 375 (S143) se midió con el Test 1 encendido, que es justo el que tapa el efecto; el de VIIRS
   750 (S145) se decidió en noches de volcán, unidad que el proyecto abandonó en S146. Medido en
   septiembre: **las 5 alertas de VIIRS 750 que no publicamos (13 de 18) son todas cúmulo en el cráter
   con 0,0 MW**. El riesgo simétrico también está medido: hay 56 a 62 negativos limpios de VIIRS 750 y
   29 de VIIRS 375 en la misma condición, que un fondo nuevo podría volver a publicar.
4. **Ningún A/B de S124 a S143 se corrió con el Test 1 apagado** (medido resolviendo 30 perfiles): todos
   los veredictos de magnitud y de sobre-publicación de ese tramo heredan A114.
5. **La causa (e) está sobre-aplicada**: el cambio de régimen de #535 es del código, no de la fecha del
   gránulo. El A/B de la caja de S130 corrió el 2026-09-01 con código posterior a #535 y a #571, y aun así
   `docs/AUDIT_S146.md:89` lo declara "medido entero antes de #535: SIN DATO". Cae igual, pero por (d) y (g).

## 1. Re-evaluación del A/B "sin el Test 1 integrado" (run 35521542153)

### 1.1 Instrumento y controles

`d1_reevaluar_sin_test1.py` usa el cargador, el predicado de node y el etiquetador del propio evaluador
(`experiments/_s146_ab_sin_test1/evaluar.py`, `scripts/banco_paridad.py`), la referencia congelada de
S146 y la ventana 2026-09-01 a 2026-09-20 (efectiva hasta el 19, `docs/S149_COSTO_OCULTO_MAX.md:94`).
Control = `_s146_ab_control` (Test 1 encendido), brazo = `_s146_ab_sin_test1`.

- ¿Vería un brazo roto? Sí: reproduce lo publicado. 2.362 pasadas en cada brazo, 2.362 comunes; VIIRS
  375 negativos limpios 86,1 a 28,7 % (n 366); recall 141 a 135 de 141; Láscar 0,655 a 0,477 (n 18).
  Coincide con `docs/S147_RESULTADO_AB_SIN_TEST1.md:34,48,76`.
- ¿Vería un instrumento muerto? Todos los n se imprimen; ninguno es cero salvo MODIS positivo (n 1).

### 1.2 Recall por tramo de la magnitud de MIROVA (VIIRS 375, `d1_salida.txt`)

| MIROVA publicó | n (tabla + OCR) | control | sin Test 1 | perdidas | n (tabla sola) | perdidas |
|---|---|---|---|---|---|---|
| 0,00 a 0,05 MW | 8 | 8 | 8 | 0 | 7 | 0 |
| 0,05 a 0,10 MW | 38 | 38 | 33 | **5** | 33 | **5** |
| 0,10 a 0,20 MW | 41 | 41 | 40 | **1** | 32 | **1** |
| 0,20 a 0,50 MW | 37 | 37 | 37 | 0 | 31 | 0 |
| 0,50 MW o más | 17 | 17 | 17 | 0 | 8 | 0 |
| todas | 141 | 141 | 135 | 6 | 111 | 6 |

Las 6 son de la tabla (ninguna depende del OCR). El 88 % de las alertas de la ventana está bajo 0,5 MW
(124 de 141): el corte de 0,5 MW del criterio C1 (`experiments/_s146_ab_sin_test1/parametros.json`,
clave `max_vrp_fn_aceptable_mw`, que cita "se aceptan falsos negativos sub-píxel bajo 0,5 MW") no
protegía nada en este sensor. VIIRS 750: 13 de 18 en los dos brazos, 0 pérdidas. MODIS: 1 de 1.

### 1.3 Las 6 pérdidas por dentro (`d3_salida.txt`)

| pasada | MIROVA | en el brazo sin Test 1 | clase |
|---|---|---|---|
| Nevados de Chillán 09-05 05:48 | 0,14 | `summit`, mismo cúmulo (0,407 km, 1 píxel, 3 anómalos), `pc.vrp_mw` 0,0 | **número** |
| Nevados de Chillán 09-14 05:42 | 0,09 | `summit`, mismo cúmulo (0,387 km), 0,0 MW | **número** |
| Isluga 09-13 05:12 | 0,07 | `summit`, cúmulo de 2 píxeles a 0,82 km (el control lo tenía a 3,0 km), 0,0 MW | **número** |
| Tupungatito 09-17 04:48 | 0,05 | `summit`, cúmulo a 0,23 km (el control a 2,5 km), 0,0 MW | **número** |
| Isluga 09-19 05:42 | 0,06 | `far`, gana un cúmulo contextual a 7,9 km | **detección** |
| Nevados de Chillán 09-18 05:24 | 0,05 | `far`, gana un cúmulo a 20,2 km | **detección** |

Fenómeno: un foco débil en una cumbre fría es más frío en el infrarrojo medio que la mediana de un
anillo regional lleno de valle tibio, así que su exceso sale negativo y se recorta a cero (D25,
`docs/MIROVA_DIVERGENCES.md:2602`). Mecanismo: con el Test 1 encendido y ganando la fuente interna, la
magnitud se recalcula contra el fondo propio del Test 1 (`pipeline/process_viirs.py:1858-1896` y
`1925-1943`; el comentario de la línea 1861 lo dice: "ΔL clip 0 → vrp=0 falsos negativos"). Al apagarlo
vuelve el fondo regional, la magnitud da 0,0 y el predicado del tablero no publica. **Las dos noches de
Nevados de Chillán que sostienen el fallo de C2 no son "un mecanismo que no entendemos" ni "un efecto de
segundo orden sobre la selección del cúmulo"** (`docs/S147_RESULTADO_AB_SIN_TEST1.md:65-69`): el cúmulo es
idéntico y lo único que cambia es el número. En Isluga 09-13 y Tupungatito 09-17 el cúmulo sí cambia, y
se acerca al cráter.

### 1.4 La magnitud pareada por dentro (`d1_salida.txt`, `d2_salida.txt`)

- 135 pares VIIRS 375 que los dos publican. En 91 la magnitud es idéntica. En 44 cambia: baja en 35,
  sube en 9. Control positivo: en los 91 que no cambian, el cúmulo tiene los mismos píxeles en los 91.
- En los 44 que cambian: los píxeles anómalos de la escena son idénticos en los 44; el cúmulo primario
  tiene **igual número de píxeles en 24 y más píxeles en 20, nunca menos**; se mueve 100 m o menos en 23,
  entre 100 y 500 m en 19 y más de 500 m en 2. O sea: el mismo objeto, con otro fondo restado.
- Razón contra MIROVA, mediana de los 135: 0,823 a 0,772. Los tres estratos que fallan C4 (Láscar, Isluga,
  Tupungatito) ya estaban bajo 1 en el control. En los 44 que cambian el brazo queda más lejos de MIROVA
  en 30 y más cerca en 14.
- La etiqueta persistida `final_hotspot_source` dice `ctx_cluster` en los 135 pares de los dos brazos: no
  sirve para saber quién puso la magnitud. La explicación del documento ("recómputo gateado por
  `source == 'test1'`", línea 82) es correcta para la variable interna, no para el campo del record.

**Respuesta a la pregunta del encargo.** El costo real que queda en pie es la **magnitud**, y es un costo
**del número que se publica, no de la detección**, en 4 de las 6 alertas perdidas y en los 35 pares que
bajan. Costo de detección propiamente tal: **2 pasadas de 141** (0,06 y 0,05 MW), donde el Test 1 era lo
único que veía el cráter. SOSPECHA razonada, no medida: un fondo de magnitud literal (D25) devolvería las 4
y parte de la caída de C4; ver el riesgo simétrico en 1.6.

### 1.5 Selectividad y el estrato que el negativo limpio esconde

| VIIRS 375 | control | sin Test 1 |
|---|---|---|
| negativos limpios (n 366) | 86,1 % | 28,7 % |
| RUTINA con VRP 0 en noche con alerta del sensor (n 106) | 90,6 % | 50,9 % |
| negativos de pasada, los dos juntos (n 472) | 87,1 % | 33,7 % |
| C8b, supervivencia de positivas menos la de negativos | | 0,624 contra p97,5 del nulo 0,398: **cumple** |

Supervivencia de lo que publica el control: positivas 96 %, RUTINA en noche con alerta 56 %, negativos
limpios 33 %. El orden es el físicamente esperable y el mismo que dio `max` (99, 37 y 9 %,
`experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md:136-138`). VIIRS 750: negativos limpios 21,4 a
5,9 % (n 613), RUTINA en noche con alerta 26,7 a 10,0 % (n 30), C8b cumple (0,725 contra 0,556). MODIS: una
sola positiva, C8b sin poder.

### 1.6 Detectado con magnitud cero, en los dos sentidos (`d4_salida.txt`)

Pasadas que NO se publican teniendo cúmulo `summit` dentro del radio con `pc.vrp_mw` igual a 0:

| | positivas | RUTINA en noche con alerta | negativos limpios |
|---|---|---|---|
| VIIRS 375, control | 0 de 141 | 2 de 106 | 4 de 366 |
| VIIRS 375, sin Test 1 | **4 de 141** | 15 de 106 | 29 de 366 |
| VIIRS 750, control | **5 de 18** | 6 de 30 | 62 de 613 |
| VIIRS 750, sin Test 1 | **5 de 18** | 7 de 30 | 56 de 613 |

Un arreglo del fondo no es gratis: en VIIRS 750 recuperaría hasta 5 de 18 positivas (28 puntos de recall
por pasada) y expondría hasta 56 de 613 negativos (9 puntos). Es un techo de exposición, no una predicción.

### 1.7 Qué diría hoy el veredicto

| criterio de S147 | resultado | estado del criterio hoy |
|---|---|---|
| C1 recall por pasada (piso 118, corte 0,5 MW) | cumple, 135 | el corte de 0,5 MW cayó para VIIRS (causa a); por tramo: 6 pérdidas, todas bajo 0,2 MW, 4 de ellas de número |
| C2 noches fuera de lista | falla, 2 noches de Chillán | vara que "el azar cumple" según su propio texto; las 2 noches son detección intacta con 0,0 MW |
| C3 publicación en negativos | cumple | se sostiene, y el estrato escondido (h) lo refuerza |
| C4 magnitud pareada | falla en 3 estratos | se sostiene como hecho; es el costo real, y es del fondo de la magnitud |
| C7 posición | falla, 96 de 532 | caído (causa b), informativo desde #729 |
| C8 | cumple | caído (causa c); su reemplazo C8b también cumple |

Clasificación: **CAE (hay que volver a medir)**. No porque apagar el Test 1 sea gratis, sino porque el
"NO ADOPTAR" atribuye a la selección del cúmulo un costo que es del fondo de la magnitud, y ese costo tiene
una palanca propia ya implementada y apagada (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` y `_VIIRS750`). El
brazo que falta es "sin Test 1 más fondo por vecinos", con "sin Test 1" como control.

## 2. Hallazgos, por gravedad

### H1. El "NO ADOPTAR" del A/B sin Test 1 atribuye a la detección un costo que es del número publicado
- ARCHIVO: `docs/S147_RESULTADO_AB_SIN_TEST1.md:9, 65-69, 92-94`. SCRIPT: `d3_salida.txt`, `d2_salida.txt`.
- QUÉ PASA: el foco débil sigue detectado en el cráter; sin el recómputo del Test 1 su exceso sobre el
  anillo regional se recorta a cero y no se publica. El documento lo lee como "se elige otro cúmulo".
- CÓMO SE VE EN EL DASHBOARD: invisible; la pasada no aparece porque la magnitud es 0,0 MW.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_d/d3_las_seis_perdidas.py <dir de salidas>`;
  Nevados de Chillán 2026-09-05 05:48 y 2026-09-14 05:42 UTC, VIIRS 375.
- CONFIANZA: CONFIRMADO (medido y código leído). GRAVEDAD 5: es el veredicto que mantiene encendida la
  palanca que explica 57 puntos de publicación falsa en VIIRS 375.

### H2. Los dos veredictos que apagaron D25 (fondo por vecinos) caen, y D25 es lo que el hallazgo H1 pide
- ARCHIVO: `docs/MIROVA_DIVERGENCES.md:2602-2650` (S145, VIIRS 750: "en noches el premio es cero");
  `experiments/_s143_evaluador/VERIFICADOR_VEREDICTO.md:36-37` (S143, VIIRS 375: D25 +0,052 en negativos,
  medido con el Test 1 encendido, `d5_salida.txt` fila `_s142_ab_control`); `tasks/BLOQUE_ARRANQUE_S144.md`
  tabla a ("Pérdidas de VIIRS 750: 5 de 5 son D25"). SCRIPT: `d4_salida.txt`.
- QUÉ PASA: en VIIRS 750 el cráter se detecta y se publica en 0,0 MW; en septiembre son 5 de 18 alertas
  de MIROVA por pasada. S143 ya lo sabía; S145 lo archivó contando noches de volcán (ventana 2026-03-01 a
  2026-09-20, que además pisa el tramo de OCR defectuoso y mezcla el régimen de producción previo a #535),
  y S146 declaró que la noche "NO DISCRIMINA" y que decide la pasada (`parametros.json`,
  `_piso_recall_por_que`). Nadie volvió a D25 con la unidad nueva.
- CÓMO SE VE: VIIRS 750 no muestra alertas que MIROVA sí publica (13 de 18 por pasada).
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_d/d4_detectado_con_cero.py <dir>`.
- CONFIANZA: CONFIRMADO el hecho (5 de 5 con cúmulo summit y 0,0 MW, en los dos brazos); SOSPECHA que el
  fondo por vecinos las recupere sin republicar los 56 negativos en la misma condición. GRAVEDAD 4.

### H3. Todo A/B de S124 a S143 corrió con el Test 1 encendido en el control y en los brazos
- SCRIPT: `d5_salida.txt` (30 perfiles resueltos por `pipeline.profile`; control positivo:
  `_s146_ab_sin_test1` da False). Límite: resuelve con el código de hoy.
- QUÉ PASA: con el Test 1 encendido la publicación en negativos está saturada (A114) y además, en
  septiembre, **50 de 141 positivas de VIIRS 375 (35 %) reciben su número del recómputo del Test 1**
  (inferido: son las 44 cuya magnitud cambia al apagarlo más las 6 que dejan de publicarse). Un A/B de
  magnitud con el Test 1 encendido mide una mezcla de dos fondos.
- Afecta a: F70 brazos B y C (S124), A/B de magnitud (S125), corona (S126 y S127), caja (S130), área
  geolocalizada (S133), banda 22 (S133), 5 brazos de S135, D22/D25 (S143).
- CONFIANZA: CONFIRMADO el estado del flag; SOSPECHA el tamaño del efecto en cada A/B viejo. GRAVEDAD 4.

### H4. `keep_peak` y la prioridad por rival débil sólo existen dentro del Test 1: sus veredictos quedan sin objeto si el Test 1 se apaga
- ARCHIVO: `pipeline/process_viirs.py:1850-1857` (`keep_peak` actúa sobre `test1_hot_filtered`) y
  `1767-1775` (la prioridad decide si el Test 1 gana la fuente).
- QUÉ PASA: S135 (5 brazos), S143 (brazo `lit_keep_peak`), S144 (cierre sin correr) y el brazo C de S147
  gastaron cuatro sesiones en perillas internas de un detector propio (D30). No caen: quedan SIN OBJETO
  bajo la rama "sin Test 1", y vuelven a importar sólo si se elige el estadístico corregido.
- CONFIANZA: CONFIRMADO por lectura de código; no medí que el brazo sin Test 1 sea insensible al flag
  (SIN VERIFICAR: `_s146_ab_sin_test1` tiene `keep_peak` en True, `d5_salida.txt`). GRAVEDAD 3.

### H5. La causa (e) se aplica por fecha de gránulo cuando es del código: `AUDIT_S146` A-13 está mal fundado para D18
- ARCHIVO: `docs/AUDIT_S146.md:89`; `docs/MIROVA_DIVERGENCES.md` nota S146 dentro de D18 ("entero anterior
  a #535: SIN DATO"). Evidencia: `gh run view 33456630043` da `createdAt 2026-09-01T00:54:21Z`, sha
  `d6d9b8e0`, y `git merge-base --is-ancestor` confirma que #571 (2026-08-31) es ancestro de ese sha.
- QUÉ PASA: el régimen de #535 es la máscara de nube apagada en el código. Un reproceso posterior corre
  en el régimen nuevo aunque los gránulos sean de junio. A104 vale para métricas sobre records persistidos
  de producción. Consecuencia práctica: el pre-registro de invierno corta agosto el día 27 "para no cruzar"
  (`PREREGISTRO_INVIERNO.md:66`) cuando todos sus brazos se reprocesan con el código de hoy: pierde 4 días
  sin necesidad (menor).
- CONFIANZA: CONFIRMADO para el run de D18; SOSPECHA como regla general. GRAVEDAD 2.

### H6. El campo `final_hotspot_source` no dice quién puso la magnitud
- SCRIPT: `d1_salida.txt` (135 de 135 pares con `ctx_cluster` en los dos brazos, 44 con magnitud distinta).
- QUÉ PASA: cualquier análisis que separe "records del Test 1" por ese campo (lo hace
  `docs/S147_RESULTADO_AB_SIN_TEST1.md:61-68`) subcuenta la influencia del Test 1 en la magnitud.
- CONFIANZA: CONFIRMADO. GRAVEDAD 3 (es del frente E o G; ver "Para otros frentes").

### H7. El recall de 100 % del control es saturación, y así entró como vara en tres pre-registros
- ARCHIVO: `parametros.json` (`min_pasadas_positivas_publicadas`, 118 de 143);
  `experiments/_s147_ab_conectiva/PREREGISTRO.md:106-113`; `PREREGISTRO_INVIERNO.md:129`.
- QUÉ PASA: un control que publica 86 % de los negativos publica 141 de 141 positivas casi por
  construcción. Medir a un brazo contra ese 100 % castiga cualquier selectividad. La vara correcta es la
  suma de los dos errores (definición del dueño en `docs/PLAN_AUDITORIA_S149.md:26-27`): control 0 de 141
  perdidas más 315 de 366 falsas; sin Test 1, 6 de 141 más 105 de 366.
- CONFIANZA: CONFIRMADO (números de `d1_salida.txt`). GRAVEDAD 3.

## 3. Censo de veredictos S124 a S148

Causas: (a) corte 0,5 MW en VIIRS; (b) C7; (c) C8; (d) Test 1 encendido; (e) cruza #535; (f) referencia en
tramo defectuoso; (g) flag que no llega a sus consumidores; (h) negativo limpio por noche. Agrego dos que
aparecieron: **(i) unidad noche en vez de pasada**; **(j) sin negativos: sólo mide sobre noches que MIROVA
confirmó** (A98). Clasificación: SOSTIENE / OTRA RAZÓN / CAE / NO SE SABE.

| # | sesión | qué se probó | ventana y criterio que decidió | veredicto | causas | clase | fuente |
|---|---|---|---|---|---|---|---|
| 1 | S124 | F70 brazo B, grilla UTM y kernel global | 2026-06-25 a 08-24, V375, razón de magnitud en noches cruzadas | NO ADOPTAR | d, j; corrida con el código previo a #535 (SIN VERIFICAR la fecha del run) | NO SE SABE | leído `docs/S124_F70_VEREDICTO.md:3, 112`; `d5` |
| 2 | S124 | F70 brazo C, kernel-bg | ídem, 6 volcanes | NO ADOPTAR | d, j | NO SE SABE | leído `docs/S124_F70_BRAZO_C_RESULTADO.md:4, 38-42` |
| 3 | S124 | Villarrica OP A/B | 2026-04-01 a 08-24, recall y magnitud en noches pareadas | informe, no adopción | d, f (parte antes del 06-13; qué canal usó, SIN VERIFICAR), i, j | NO SE SABE | leído `docs/S124_VILLARRICA_OP_AB_RESULTS.md:4, 21-35` |
| 4 | S125 | A/B de magnitud, brazos A, B, C | 2026-06-25 a 08-24, volcanes en banda de razón | NO ADOPTAR todavía | d (H3: parte de los pares recibe el número del Test 1), j; el brazo A no llegaba a VIIRS: es (g), ya declarado en `docs/S125_AB_MAGNITUD_RESULTADO.md:104-112` | CAE | leído |
| 5 | S126 | apagar la máscara de nube (#535) | jun a ago, noches ciegas recuperadas | sostener el apagado | j en parte (sólo 21 de 286 nuevas en noches confirmadas, `:63`) | SOSTIENE; su costo (sobre-publicación) es lo que hoy se mide | leído `docs/S126_CLOUDMASK_RESULTADO.md:15, 63-84` |
| 6 | S126/S127 | corona Ec. 6, 2 x 2 | 2026-06-25 a 08-24, 5 volcanes, un par por noche; "cero detecciones perdidas" y "Villarrica baja" | NO ADOPTAR | d, i, j; n de 3 a 36 por volcán | CAE: es el antecesor de D25 y se juzgó sin negativos y con el Test 1 poniendo parte de los números | leído `docs/S127_CORONA_RESULTADO.md:7-8, 26-45` |
| 7 | S126, S130 | piso de VRP | producción 2026-05-01 a 08-28 | quitado en S130 (#571) | ninguna de la lista | SOSTIENE | leído `docs/S126_PISO_VRP_ES_UN_NO_OP.md:4`; censo parcial |
| 8 | S129/S130 | A/B de fondos (GAP #A) | sin sustrato: los brazos no difieren | sin veredicto | g en su forma original (no hay píxeles K1 que retirar) | SOSTIENE como "no medible hoy" | leído `docs/s130/AB_FONDOS_SIN_SUSTRATO.md:4, 35-52` |
| 9 | S130 | caja de 5 x 5 km (D18) | gránulos 2026-05-29 a 08-24, run del 09-01; offset de cúmulo, pérdidas en noches confirmadas | NO ADOPTAR, "redistribuye, no recorta" | **g** (la caja no llegaba al segundo pase), **d**, j; (e) NO aplica (H5) | **CAE**, ya marcado en `docs/MIROVA_DIVERGENCES.md:2254-2265` | leído |
| 10 | S132 | re-etiquetar `distance_class` MODIS | corpus 2025-02-15 a 2026-09-02, records | NO ADOPTAR (falla C2) | e (producción, cruza), f (enero y febrero), i | NO SE SABE; A94 dice además que rinde 1 noche de 946 | leído `docs/s132/AB_DISTANCE_CLASS_MODIS.md:3, 9` |
| 11 | S133 | área geolocalizada, chunk 1 | 2026-04-01 a 05-31, 643 pares V375; "0 noches perdidas", bins de razón | NO ADOPTAR los tres | d, f (todo antes del 06-13; canal SIN VERIFICAR), j | NO SE SABE | leído `docs/s133/AB_AREA_VEREDICTO_CHUNK1.md:8, 28-34, 74` |
| 12 | S133 | banda 22 primaria | agosto de 2026, n 70, 2 volcanes; invariancia de fondo y magnitud | NO ADOPTAR, "no archivar" | d; criterio de invariancia que el propio doc cuestiona; S140 lo resumió como "descartado" (`tasks/BLOQUE_ARRANQUE_S140.md:89`, censo delegado): conocimiento deformado al resumir | CAE; en vuelo como brazos J y K de S149 | leído `docs/s133/AB_B22_VEREDICTO.md:10-20, 47-75` |
| 13 | S134 | ley de área intermedia (F4) | 2026-04-01 a 05-31, análisis sobre JSON de S133 | NO ADOPTAR | d, f, j | NO SE SABE | censo delegado `docs/AUDIT_S134.md:243, 263` |
| 14 | S135 | 5 brazos: `keep_peak`, segundo pase condicionado | 2026-06-01 a 08-31, 6 volcanes, cero noches perdidas, artefacto definido por noche | ningún brazo cumple | d, h, i; paridad accidental (A100) | OTRA RAZÓN / sin objeto si se apaga el Test 1 (H4) | censo delegado `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:22, 58` |
| 15 | S136 | conectiva `min` contra `max`, 9 escenas MODIS con banda 21 | batería del Apéndice A | NO ADOPTAR `max`, "cierra la conectiva" | criterio propio caído (S138, S146); banda 21 | **CAE**, ya revertido por S148 y S149 | censo delegado `experiments/_s136/VEREDICTO_CONECTIVA.md:1, 45` |
| 16 | S136 | corolario "el piso manda" (pool, retiro K1, C2) | sin medición | cerrado | derivado bajo `min` | **CAE** (A95, D26) y más ahora que `max` está confirmada: bajo `max` la desviación gobierna siempre | censo delegado; `CLAUDE.md` A95 leído |
| 17 | S136 | filtro de intensidad de Laiolo | 1.952 alertas, sin ventana | descartado | f posible | NO SE SABE | censo delegado |
| 18 | S136 | etiqueta `far` a `summit` | toda la serie, noches | no rentable, 4 de 946 | e, f, i | SOSTIENE por otra razón (S146 D-07 lo reproduce) | censo delegado |
| 19 | S137/S138 | D21 y D22 en batería de 8 brazos | 9 escenas MODIS | ningún brazo cumple, frente pausado | criterio caído (S146: 9 de 9) | **CAE**, ya marcado en `docs/MIROVA_DIVERGENCES.md:2526` | leído el encabezado |
| 20 | S138 | D25 como recall | 2026-01-11 a 09-07, noches de volcán | "no priorizar D25 como recall" | e, f (enero), i | **CAE** (H2) | censo delegado `docs/AUDIT_S138.md:144-160`; `tasks/BLOQUE_ARRANQUE_S139.md:121` |
| 21 | S141 | probe v1 de vecinos | 40 pasadas del OSF de 2025 | INDETERMINADO | d; referencia OSF filtrada (A105) | NO SE SABE | censo delegado |
| 22 | S142 | probe v2 de vecinos | 38 pasadas del OSF de 2025 | no justifica A/B | d; frágil (cambia sin un volcán) | NO SE SABE | censo delegado |
| 23 | S143 | D22 y D25, 6 brazos | gránulos 2026-06-01 a 08-31 reprocesados; cero pérdidas con cota de 0,55 km, negativos por pasada | NO ADOPTAR | **d** (todo el descenso venía de `keep_peak`, o sea del Test 1), cota escalar (A107), pérdidas de borde de cota (H5 de su verificador) | **CAE para D25 y D22**: no se han medido nunca sin el Test 1 | leído `experiments/_s143_evaluador/VERIFICADOR_VEREDICTO.md:11-15, 35-44` |
| 24 | S144 | `keep_peak` con dirección | cerrado sin correr | cerrado | sin objeto bajo "sin Test 1" | OTRA RAZÓN (H4) | censo delegado |
| 25 | S145 | D25 en VIIRS 750 | 2026-03-01 a 09-20, noches de volcán | "no ahora" | d, e (producción), f, **i** | **CAE** (H2) | leído `docs/MIROVA_DIVERGENCES.md:2621-2637` |
| 26 | S145 | cerca del frontend (D13) | septiembre, y jun a ago aparte | no es palanca | ninguna fuerte | SOSTIENE | censo delegado |
| 27 | S147 | **sin Test 1 (brazo B)** | 2026-09-01 a 09-20 | NO ADOPTAR por C2, C4, C7 | a, b, c, h | **CAE** (sección 1) | medido |
| 28 | S147 | sin prioridad por rival débil (brazo C) | ídem | NO ADOPTAR, "no es la palanca" | b, d (medido contra control saturado) | OTRA RAZÓN: sin objeto si se apaga el Test 1 | leído `docs/S147_RESULTADO_AB_SIN_TEST1.md:156-160` |
| 29 | S147 | descartes: remuestreo, cuantización, corte en MW | mayo y septiembre, TIF de la misma pasada | descartados | f en la parte de mayo; A109 (mismo gránulo) declarado; mide identidad de imagen, no el remuestreo a grilla (D17) | SOSTIENE lo medido; NO cierra D17 | censo delegado |
| 30 | S147 | estadístico corregido del Test 1 | no corrido | sin veredicto | | abierto | leído `:168-169` |
| 31 | S148 | conectiva `max` (brazo F) | septiembre, control sin Test 1 | CONFIRMADA en V375 | a en P4 (enmendado en S149), c (reemplazado), h (medido en S149) | SOSTIENE, con los criterios ya corregidos | leído `docs/S149_COSTO_OCULTO_MAX.md`; mayo en `docs/S149_RESULTADO_CONECTIVA_MAYO.md` (no releído) |
| 32 | S148 | caja (brazos G y H) | septiembre | no medible | g | sin veredicto; cableado arreglado en #738 | leído `tasks/BLOQUE_ARRANQUE_S150.md` |

## 4. Palancas que vuelven a estar vivas, en orden de cuánto moverían la paridad

1. **Apagar el Test 1 integrado (o su estadístico corregido).** VIIRS 375: negativos limpios 86,1 a
   28,7 %, negativos de pasada en noche con alerta 90,6 a 50,9 %; VIIRS 750: 21,4 a 5,9 %. Costo de
   detección medido: 2 pasadas de 141, las dos bajo 0,1 MW. Es la mayor de todas por un orden de magnitud.
2. **Conectiva `max` encima de lo anterior.** 29,8 a 2,7 % en septiembre, recall 137 a 135 de 143
   (`PREREGISTRO_INVIERNO.md:111-113`); ya es el frente activo.
3. **Fondo de la magnitud por vecinos (D25), con "sin Test 1" como control.** Es la pieza que falta para
   que 1 y 2 no cuesten número: 4 de las 6 pérdidas de VIIRS 375, los 35 pares que bajan, y 5 de 18
   alertas de VIIRS 750 (la mayor brecha de recall por pasada que queda en VIIRS). Riesgo medido en la
   misma tabla: 29 y 56 negativos limpios con cúmulo en 0,0 MW. Nunca medido sin el Test 1.
4. **Caja de 5 x 5 km (D18).** Nunca medida; cableado listo (#738). Tamaño desconocido.
5. **Compuerta de 3 K (D22).** Sólo medida con el Test 1 encendido, donde sube la publicación 0,20 con
   `keep_peak` apagado. Dirección desconocida bajo `max` y sin Test 1.
6. **Banda 22 más `max` en MODIS.** En vuelo (S149). Es la única palanca con sustrato para las alertas de
   Láscar en MODIS.
7. **Levers de magnitud de S124 a S133** (corona, área geolocalizada, kernel): re-mirar sólo después de 3,
   porque la corona es el mismo concepto que D25 y el resto se midió con dos fondos mezclados.

Sin objeto si se apaga el Test 1: `keep_peak`, prioridad por rival débil, segundo pase condicionado al Test 1.

## 5. Lo que cambiaría el plan

- El brazo siguiente no es "estadístico corregido contra control de producción", es una matriz chica con
  **"sin Test 1" como control**: más fondo por vecinos (V375 y V750), y los dos con `max`. Los datos de
  septiembre ya alcanzan para pre-registrar el tamaño esperado (sección 1.6).
- Todo pre-registro nuevo debería separar **pérdida de detección** de **pérdida por magnitud cero**; hoy el
  evaluador las suma (publicar exige VRP mayor que cero).
- La vara de recall no puede ser "lo que publica el control" mientras el control tenga el Test 1 encendido.

## 6. Para otros frentes

- Frente E: `pipeline/process_viirs.py:1858-1896`, el recómputo del Test 1 usa otro fondo que el bloque
  contextual; el mismo píxel vale distinto según quién gane la fuente interna.
- Frente G: `final_hotspot_source` persistido no refleja quién puso la magnitud (H6).
- Frente C: VIIRS 750, 5 de 18 alertas de septiembre son cúmulo summit con 0,0 MW (`d4_salida.txt`).
- Frente B: `docs/AUDIT_S146.md:89` aplica A104 por fecha de gránulo a un reproceso (H5).
- Frente A: el resumen "Banda 22 sola: descartado" (`tasks/BLOQUE_ARRANQUE_S140.md:89`) contra el original
  "no adoptar por ahora, y no archivar el frente" (`docs/s133/AB_B22_VEREDICTO.md:71`).

## 7. SIN VERIFICAR y límites

- Tramo S124 a S133: cobertura parcial. No leí `docs/AUDIT_S124.md`, `AUDIT_S125_PROFUNDA`, `AUDIT_S127`,
  `AUDIT_S128`, `AUDIT_S131` ni los README de `experiments/_s129_*` a `_s133*`. Pueden faltar veredictos.
- Las filas "censo delegado" no las releí.
- Que el fondo por vecinos recupere las 4 y las 5 pasadas es SOSPECHA: no corrí el pipeline.
- La fecha y el sha de los runs de F70, S125, corona y S133 no los consulté; sólo el de D18.
- `d5` resuelve los perfiles con el código de hoy.
- Una sola ventana (septiembre, 19 días efectivos). Nada de esto está medido en invierno ni en mayo.
- El canal de referencia (tabla u OCR) de las filas 3, 11 y 13 no lo verifiqué.

## 8. VERIFICADO LIMPIO

- El resultado publicado de S147 se reproduce exacto desde la rama del run: 2.362 pasadas por brazo,
  86,1 a 28,7 %, 135 de 141, Láscar 0,655 a 0,477 (`d1_reevaluar_sin_test1.py`).
- Las 6 pérdidas son de la tabla de MIROVA, ninguna depende del OCR; septiembre es posterior al OCR 30.0:
  la causa (f) no toca este A/B.
- La ventana de S147 y S148 es entera posterior a #535: (e) no las toca.
- C8b se cumple para el brazo sin Test 1 en VIIRS 375 y 750 (`evaluar.selectividad_supervivencia`).
- D18 ya lleva su marca de caída donde se lee primero (`docs/MIROVA_DIVERGENCES.md:2254`); D21 también
  (`:2526`). D13 y el piso de VRP no tienen ninguna de las causas.
- `_s146_ab_sin_test1` difiere de producción sólo en `ENABLE_TEST1_PATH` entre los seis flags que miré
  (`d5_salida.txt`); el diff completo es el de `experiments/_s146_ab_sin_test1/diff_perfiles_salida.txt`, no releído.
