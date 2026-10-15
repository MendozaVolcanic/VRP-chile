# Pre-registro S151 (tarea 1.6 del loop): F y K contra producción en los 11 Tier A

> **VERSIÓN 2, SIN APROBAR, SIN DESPACHAR.** Escrito y commiteado antes de correr ningún brazo sobre estas
> ventanas. La versión 1 la revisó un verificador con contexto limpio ("sellable con arreglos"); la 2 aplica sus
> siete puntos (§9). Falta el "sí" de Nicolás (el candado `preregistro_aprobado` del workflow es suyo). Todos los números de este documento salen de los scripts de esta carpeta, con su
> salida guardada al lado: `sustrato_salida.txt`, `duracion_runs_salida.txt`, `diff_perfiles_salida.txt` y
> `probar_salida.txt`.

## 1. La pregunta, y por qué ahora

**El fenómeno.** De noche, el píxel de un cráter con calor se despega de su entorno por dos caminos: por cuánto
se aparta del fondo (el dNTI) y por cuánto se aparta de la variabilidad de ese fondo. Producción acepta el píxel
si cumple **uno** de los dos (`min`) y además suma el exceso de infrarrojo medio de todo un disco de 3 km contra
un anillo (el Test 1 integrado, que no está en el paper). En una noche sin nada, con un fondo frío y ruidoso al
borde del barrido, el camino fácil y la suma del disco publican calor que MIROVA no ve: en la ventana de este
pre-registro producción publica en **734 de 832** negativos limpios de VIIRS 375 (`sustrato_salida.txt`, V1).
La familia candidata hace lo que escribe el paper: sin el Test 1 y con la conectiva `max` (los dos caminos).
**F** es eso; **K** es F más la banda 22 como primaria en MODIS, que es lo que el paper pide (D21) y lo único
que distingue a K de F (`diff_perfiles_salida.txt`: la banda 22 sólo la lee `process_modis.py`).

**Lo que ya se sabe, y lo que no.**
- Contra el brazo sin Test 1 (B), `max` baja la publicación en negativos limpios de VIIRS 375 de 35,7 a 2,7 %
  de abril a agosto y conserva 946 de 988 alertas (`experiments/_s149_prereg_invierno/resultados/agregado_abril_agosto.txt`).
  En VIIRS 750 la suma de errores baja de 400 a 90 (`experiments/_s151_max_v750/salida.txt`). **Pero todo eso
  es contra B, no contra producción.** Contra producción (C0) sólo se midió un volcán: Nevados de Chillán en
  erupción, donde ningún candidato perdió una alerta de 1 MW o más y la suma de errores bajo 1 MW fue C0 52,
  F y K 7 (`docs/S151_RESULTADO_NDC.md`).
- En MODIS, K se midió sólo en Láscar (S150): publica 67 de 73 alertas contra 8 de producción, y en negativos
  limpios 2 de 96 contra 1. **Fuera de Láscar, la tasa de falsos de K no está medida.**
- S147 descartó "sin Test 1" porque **apagarlo mueve el cúmulo publicado**: el Test 1 compite por el ancla, y
  sin él se elige otro cúmulo contextual (96 de 532 pasadas publicadas por los dos se movieron más de 500 m;
  2 de 149 donde MIROVA alertó, 41 de 180 donde no vio nada; `experiments/_s147_pos/estabilidad_salida.txt`).
  Aquí eso deja de ser una objeción recordada y pasa a ser una predicción medida (P4).

**La pregunta.** ¿F (en VIIRS) y K (en los tres sensores), contra C0, sobre los 11 Tier A, cumplen el criterio
de victoria de `docs/MISSION.md`: ninguna alerta protegida perdida; bajo 1 MW, menor suma de alertas perdidas y
publicaciones de más; medido en las dos direcciones, por sensor y por tramo A119, con recall, publicación en
negativos limpios y razón de magnitud? Con las dos lecturas de "alerta protegida" de
`docs/S151_CRITERIO_CLASE_MIROVA.md` (A, la de por defecto; B, pendiente en el issue #782).

**Lo que esta prueba no decide.** No adopta nada: la adopción es el ciclo A45 (tag defensivo y confirmación de
Nicolás) y pasa antes por el verificador con contexto limpio sobre el resultado.

## 2. Brazos, y por qué cada uno

| brazo | perfil | qué es | por qué está |
|---|---|---|---|
| C0 | `_s146_ab_control` | producción (difiere de `mirova_equivalent` sólo en el nombre y el directorio) | es el control: las pérdidas se cuentan contra lo que hoy se publica |
| F | `_s147_ab_sin_test1_max` | sin Test 1, conectiva `max` | el candidato VIIRS que nombra la pregunta; y como en VIIRS corre el mismo código que K, **el par F y K es un gemelo gratis del candidato en VIIRS** |
| K | `_s149_ab_sin_test1_b22_max` | F con banda 22 primaria en MODIS | el candidato completo: los flags son globales, así que lo adoptable es K (su VIIRS es el de F) |
| G | `_s151_ab_control_gemelo` (nuevo, YAML de experimento) | C0 corrido otra vez | el ruido del control nunca se midió. El de la familia sin Test 1 sí (S149 y S150, gemelo de B, 100 % de la decisión) y en VIIRS lo da F contra K. G mide el del brazo contra el que se cuentan las pérdidas, que lleva el Test 1 y suma un disco: un píxel que cambia entre dos jobs puede mover esa suma |

`diff_perfiles_salida.txt` resuelve cada perfil como lo resuelve el código (A89): C0 contra producción, 2
atributos distintos (nombre y directorio); C0 contra G, los mismos 2; C0 contra F, además `ENABLE_TEST1_PATH` y
`ENABLE_TESTS_23_PROSE_BRANCH`; F contra K, sólo `ENABLE_MODIS_B22_PRIMARY`.

**Brazos que no están, a propósito.** B y J (sin `max`): ya se midieron (S150) y no son candidatos. KE y KET
(etiqueta desde el cúmulo, sin tope): en Chillán KE decidió igual que K en todas las pasadas y el tope quedó sin
probar; ese es otro frente. La caja de 5 × 5 km es la tarea 1.7. **Los flags de compuerta y de fondo que la
tarea 1.6 pide para MODIS no existen** (`docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:285`): escribirlos es
tocar `pipeline/` con su ciclo A45, así que K se prueba como está y lo que falte queda dicho en §8.

**F no es adoptable solo.** Sus flags también corren en MODIS, con la banda 21, donde `max` apaga el detector
(S147; S150: B con banda 21 no publica ninguna de las 73 alertas de Láscar). Por eso F se juzga en VIIRS, que es
lo que la pregunta le pide, y su MODIS se imprime sólo para que nadie lo adopte sin K.

## 3. Ventanas: dos, ninguna cruza #535

**Por qué dos.** El veto ("ninguna alerta protegida perdida") sólo puede fallar donde hay alertas protegidas
que C0 publica, y `sustrato.py` mide que en el régimen de hoy casi no hay:

| ventana | MODIS | VIIRS 375 | VIIRS 750 |
|---|---|---|---|
| V1, protegidas A que producción publica (sin las del OCR de Suomi NPP) | 3 | 12 | 10 |
| V1, fracción de pérdida que el veto detecta con 80 % de probabilidad | 41,5 % | 12,6 % | 14,9 % |
| V2 (VIIRS desde abril), protegidas A que producción publica | 6 | 37 | 42 |
| V2, fracción detectable al 80 % | 23,5 % | 4,3 % | 3,8 % |

Con sólo V1, un candidato podría perder una de cada ocho protegidas de VIIRS 375 y el veto saldría limpio. Las
protegidas de este año están en marzo a junio, sobre todo en Láscar. Por eso hay una segunda ventana.

**Ojo: el veto con poder es un veto de Láscar, no de los once** (verificador, 6a; tablas "POR SENSOR Y VOLCÁN" y
"LO QUE DECIDE, POR SENSOR Y VOLCÁN" de `sustrato_salida.txt`). En V2, de las protegidas A que deciden, Láscar
tiene 36 de 38 en VIIRS 375, 39 de 42 en VIIRS 750 y 39 de 39 en MODIS. En V1, las 12 de VIIRS 375 que deciden
son 10 de Nevados de Chillán (la erupción, ya probada en #796), 1 de Planchón Peteroa y 1 de Láscar. Los otros
nueve volcanes tienen 3 protegidas o menos en cada sensor y ventana. El 4,3 % detectable vale para lo que pasa en
Láscar; en los demás volcanes el veto casi no puede fallar, y un CUMPLE ahí no dice que no se pierda nada.

- **V1, 2026-08-29 a 2026-10-08** (41 días; régimen actual). Empieza después del 2026-08-28 23:00 UTC (#535,
  A104), así que no mezcla regímenes. Es posterior al 2026-06-13: **decide la etiqueta con tabla y OCR** (A119).
  Pisa el hito del 2026-10-09: hasta esa fecha, en las filas sólo del OCR de **Suomi NPP**, la distancia y la
  clase ALERTA pueden ser de otra pasada (el VRP sí es el suyo; Mirova-v1#20, `docs/S150_IMAGENES_SNPP.md`).
  Esas pasadas (9 protegidas en VIIRS 375 y 2 en VIIRS 750) **no deciden con la lectura A**: se listan y se
  revisa la cabecera de la imagen antes de proponer nada. Con la lectura B sí deciden, porque B no usa ni la
  clase ni la distancia. Trae a Chillán en erupción desde el 2026-09-28 y es la que aporta el costo: 906
  negativos limpios MODIS (836 fuera de Láscar), 832 de VIIRS 375 y 1.303 de VIIRS 750. Termina el 2026-10-08
  para que el producto estándar de NASA (3 a 5 días) esté publicado en todos los brazos al despachar.
- **V2, 2026-03-01 a 2026-06-12** (104 días; poder del veto). Entera antes de #535 y antes del 2026-06-13, así
  que **decide la tabla sola**: el evaluador reetiqueta de verdad, sacando las filas del OCR (una alerta sólo
  del OCR no es positiva ni saca a la pasada de los negativos; S150, hallazgo H7). **VIIRS decide desde el
  2026-04-01** (A119 b: antes la tabla exponía menos gránulos VIIRS por noche); MODIS, toda la ventana (A119:
  MODIS completo desde marzo). Enero no se usa. Se despacha en dos mitades, V2a del 03-01 al 04-20 y V2b del
  04-21 al 06-12, porque un job de 104 días con el Test 1 no cabe en el tope de 300 minutos con el margen de A15.
  En V2 corren sólo C0 y K: en VIIRS, K es F (§2), y el gemelo se reemplaza por la repetición dirigida de §5.
  **El VIIRS de F en V2 se deriva de K** (verificador, punto 3): el evaluador escribe el veredicto de F de V2 con
  los veredictos VIIRS de K, marcado "derivado de K". Sin eso, el "peor de las dos ventanas" de F sería sólo V1,
  con el poder de V1.
  Pisa además el hito de **NOAA-21 del 2026-04-09** (verificador, 6f): antes de esa fecha la tabla no lista
  ninguna pasada de NOAA-21. Es inocuo para el veredicto: esas pasadas nuestras de NOAA-21 del 1 al 8 de abril no
  tienen fila de MIROVA, quedan como `sin_info` en todos los brazos por igual, y `sin_info` no entra ni al veto, ni
  a la suma, ni a la magnitud. Sólo achica un poco el sustrato de esos ocho días.

**Referencias congeladas** desde el remoto del dueño (Mirova-v1@`c5944c6`, 2026-10-14 14:30 UTC), con recorte
[desde − 1 día, hasta + 2 días] y sha256 con fin de línea LF en `MANIFIESTO.json` (`congelar.py`; LF porque
autocrlf deja los CSV en CRLF en Windows y un sha crudo mediría la máquina: pasaba con el congelado de #796).
**La referencia se congela entera** (verificador, punto 2): `cargar_referencia_unificada` suma por defecto dos
capas que viven en el repo y no en el remoto, la histórica de la unión (`data/mirova_reference/union_historica/
consolidado_filas_perdidas.csv`, que `audit-weekly.yml` reescribe cada semana) y el respaldo del 2026-04-08. En V2
aportan 4 de 39 protegidas MODIS, 3 de 42 de VIIRS 750 y 73 negativos MODIS. `congelar.py capas` las copia
recortadas a la ventana dentro de cada `_congelado_v*` (V1: 22 y 0 filas; V2: 383 y 5.312), con su sha256 en el
manifiesto; el evaluador y `sustrato.py` se las pasan explícitas al cargador (`historico_path=`, `respaldo_path=`;
`armar_tabla.py` ganó `--historico` y `--respaldo`, opcionales, sin cambiar los usos anteriores), y cualquier
diferencia de sha, o un congelado sin capas, pone `referencia_ok` en falso y todo queda INDECIDIBLE. La copia de
la histórica es idéntica a la que se usó al congelar los CSV principales (mismo sha de la fuente entera). Los CSV
van a git forzados (`*.csv` está en `.gitignore`), como en #796.

## 4. Despacho (no despachar sin el "sí" de Nicolás)

Desde `main`, con este PR mergeado (el perfil del gemelo tiene que estar en `main`). El grupo de concurrencia
`s146-ab-sin-test1` corre uno a la vez y GitHub guarda **un solo run pendiente por grupo**: un tercer despacho
desplaza al que espera. Regla: antes de cada despacho, `gh run list --workflow reproc-s146-ab-sin-test1.yml
--json status -q '[.[]|select(.status!="completed")]|length'` tiene que dar 0 (o 1, si ese 1 es el V1 de este
mismo pre-registro corriendo y no hay nadie esperando); nunca más de dos A/B vivos.

```
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-08-29 -f end=2026-10-08 -f vols="$ONCE" -f brazos='["_s146_ab_control","_s147_ab_sin_test1_max","_s149_ab_sin_test1_b22_max","_s151_ab_control_gemelo"]' -f control=_s146_ab_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-03-01 -f end=2026-04-20 -f vols="$ONCE" -f brazos='["_s146_ab_control","_s149_ab_sin_test1_b22_max"]' -f control=_s146_ab_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-04-21 -f end=2026-06-12 -f vols="$ONCE" -f brazos='["_s146_ab_control","_s149_ab_sin_test1_b22_max"]' -f control=_s146_ab_control
```

Orden: V1, V2a, V2b (V1 primero porque su gemelo da el ruido de la suma de V2). Autentica sólo con
`EARTHDATA_TOKEN` (vence el 2026-12-07); `ubuntu-24.04` está fijado en el workflow.

**Duración, desde runs pasados** (`duracion_runs.py --estimar`: 95 jobs sin Test 1 de los runs de mayo a agosto
y de Chillán, 2,20 minutos por día de ventana; 3 jobs con Test 1 de Chillán, 2,79; el job más lento de un run
llega a 1,42 veces la mediana):

| despacho | jobs | job con Test 1 (peor) | job sin Test 1 | pared con 6 en paralelo |
|---|---|---|---|---|
| V1 | 44 | 114 min (163) | 90 min | ~12,5 h |
| V2a | 22 | 142 min (202) | 112 min | ~7,8 h |
| V2b | 22 | 148 min (210) | 116 min | ~8,1 h |

En serie, ~28 h de grupo ocupado. El peor job estimado (210 min) queda bajo el tope de 300 con el margen de A15
(1,3 × 210 = 273). La estimación con Test 1 sale de 3 jobs: es la parte menos firme.

## 5. Controles, antes de mirar ningún resultado (secciones 1 a 4 de `evaluar_fk.py`)

1. **Cobertura pareja** (A108): las mismas pasadas en todos los brazos de cada despacho, y toda pasada protegida
   (A o B) con record en todos. Si no, INDECIDIBLE: se repite el job corto con el mismo código y no se interpreta.
   **Y C0 contra producción** (verificador, 6b): la paridad entre brazos no ve un job verde sin datos que les pase
   a todos por igual (S141). Se comparan las pasadas de C0 con las de `data/mirova_equivalent/` en la misma
   ventana; si en algún volcán y sensor a C0 le falta más del 5 % de las pasadas que producción sí tiene, la
   cobertura es corta e INDECIDIBLE. El 5 % es un umbral del instrumento, elegido, no medido.
2. **Versión de producto por pasada**: ninguna pasada protegida con versión distinta entre brazos.
3. **Cableado de cada brazo, cada volcán y cada despacho**: la línea `FLAGS_BRAZO` del log de cada job (en V2,
   el de V2a **y** el de V2b; la versión 1 leía sólo el primero que encontraba, verificador punto 1) tiene que traer el perfil y el
   directorio del brazo y exactamente los flags declarados (Test 1, conectiva, banda 22, etiqueta, tope), y
   `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` y `ENABLE_VENT_ANCHORED_CLUSTERING` con su valor de producción; y la
   huella en los records: un brazo sin Test 1 no tiene ningún `triggered_test1`. Un brazo mal cableado deja
   INDECIDIBLE todo lo que lo usa.
4. **Determinismo**: G contra C0 en los tres sensores y K contra F en VIIRS, misma decisión de publicar en 98 de
   cada 100 pasadas o más (umbral heredado de S149 y S150).
5. **La referencia es la congelada, entera**: sha256 LF de los dos CSV principales y de las dos capas contra el
   manifiesto (§3).
6. **El predicado del tablero** es el de `frontend/index.html` ejecutado con node (A97); el evaluador imprime su
   sha256.

**Ruido en las pérdidas, y cómo se resuelve** (verificador, punto 4). Una pérdida es una protegida que C0 publica
y el candidato no. Se clasifica así, en este orden:
- En una pasada donde G también cambia respecto de C0 (ruido del control), o, en VIIRS, donde F y K deciden
  distinto (ruido del candidato), es **ruidosa** y deja ese veto INDECIDIBLE. No se descuenta.
- En una ventana sin gemelo (V2), es **PENDIENTE DE REPETICIÓN**: el evaluador no la da por neta ni por ruido.
- Si no, es **neta**: VETADO.

**El camino de resolución es el mismo para las ruidosas de V1 y las pendientes de V2**: se repiten los jobs de
C0 y del candidato de ese volcán, con la misma ventana (o la misma mitad) y el mismo código, y se vuelve a evaluar
con `--repeticion <salidas de la repetición>`. Si en la repetición C0 la vuelve a publicar y el candidato la
vuelve a perder, es neta y VETADO; si no, es ruido confirmado y no cuenta (se lista igual). Una sola repetición;
si la repetición misma es despareja (A108), se repite de nuevo, no se interpreta.

**Ruido en la suma (P2)** (verificador, 6d): no es la diferencia neta de las sumas de G y C0, que deja cancelarse
dos pasadas que cambian en sentidos opuestos, sino el número de **pasadas discordantes**, donde C0 y G no
coinciden en si hay error; es una cota superior de la neta. En V2, sin gemelo, el ruido es la fracción
discordantes / suma de C0 medida en V1, por sensor y lectura (`--ruido-de`).

## 6. Predicciones y reglas (secciones 5 a 8 de `evaluar_fk.py`, que las implementa tal cual)

Todo se cuenta **por pasada**, por sensor, por lectura (A y B) y por ventana, contra C0. "Publica" es el
predicado del tablero. Una alerta protegida es la de `scripts/clase_mirova.alerta_protegida` (VRP de la pasada
de 1 MW o más, recalculado del VRP; A: alerta del scraper; B: cualquier fila que no sea RUTINA).

| # | qué | regla (decide) | predicción, y de dónde sale |
|---|---|---|---|
| **P1** veto | pérdidas: protegidas que C0 publica y el candidato no | VETADO con una pérdida neta; INDECIDIBLE si las únicas son ruidosas; PENDIENTE DE REPETICIÓN si las únicas están en una ventana sin gemelo; CUMPLE con cero (o con todas descartadas por la repetición); SIN SUSTRATO si C0 no publica ninguna | **Lectura A: CUMPLE** en VIIRS (Chillán: 13 de 13 y 11 de 11; las cinco pérdidas fuertes de `max` en meses eran filas del OCR con la imagen de otra pasada) y en MODIS (en Láscar K publica 67 de 73, C0 8). **Lectura B: al menos una pérdida en VIIRS** (tarea 1.10: con B, F perdió en Chillán un calor lejano de 1,52 MW que B publicaba como otro objeto) |
| **P2** suma bajo 1 MW | alertas Muy Bajo que el brazo no publica + publicaciones en negativos limpios; ruido = pasadas discordantes entre G y C0 (§5). En V1, las pasadas cuya alerta descansa sólo en el OCR de Suomi NPP salen de la suma que decide (su etiqueta depende de la clase) y se imprime también la suma con ellas | GANA si la suma del candidato es menor que la de C0 menos el ruido; PIERDE si es mayor que la de C0 más el ruido; si no, EMPATE | **GANA en VIIRS 375 y VIIRS 750 en las dos ventanas** (producción publica 734 de 832 negativos de VIIRS 375 en V1; en Chillán la suma fue 37 contra 4 y 14 contra 2). **GANA en MODIS** en V2 (producción pierde 25 de 26 alertas Muy Bajo, todas de Láscar, y publica 252 negativos) y en V1 (producción publica 110 negativos MODIS; 61 en Puyehue Cordón Caulle), con menos confianza: fuera de Láscar el costo de K es lo que esta prueba mide por primera vez |
| **P3** magnitud | d = abs(log10(brazo/MIROVA)) − abs(log10(C0/MIROVA)), en las alertas que publican los dos; ruido = mediana de d del gemelo | FALLA si el intervalo bootstrap al 95 % de la mediana de d queda entero sobre 0 **y** la mediana supera el ruido; con menos de 5 pares, SIN SUSTRATO | CUMPLE en los tres sensores (Chillán: 0,563 contra 0,548 en VIIRS 375 y 0,385 igual en VIIRS 750). Riesgo declarado: S147 midió que sin Test 1 la razón baja 0,10 a 0,18 en VIIRS 375 de Láscar, Isluga y Tupungatito |
| P3b (informa) | mediana de log10(brazo/C0) en VIIRS 375 de esos tres volcanes | se informa | **negativa en los tres** (S147: donde el Test 1 recompone la magnitud, apagarlo la achica) |
| **P4** el cúmulo se mueve | fracción de alertas publicadas por C0 y el candidato en que el cúmulo se corre más de 0,5 km. **Los 0,5 km son elegidos, no medidos** (verificador, 6c; A115): los puso S147 y aquí se heredan para que el tope sea comparable con lo que S147 midió; ningún dato de MIROVA dice que 0,5 km sea el umbral que importa | CUMPLE si no supera el límite superior de Wilson al 95 % de lo que midió S147 en alertas, 2 de 149, que es **0,048**; FALLA si lo supera. FALLA no veta: obliga a una auditoría espacial (A61) de las pasadas movidas antes de proponer nada | **CUMPLE en el agregado**, con el movimiento concentrado donde MIROVA no vio nada (S147: 22,8 % contra 1,3 %). En MODIS de la erupción **sí se mueve** (Chillán: 2 de 2 alertas MODIS movidas) |
| P5 (informa) | MODIS fuera de Láscar: negativos limpios publicados por K y por C0, por volcán | se informa; ya pesa en P2 | K publica menos que C0 (producción en V1: 107 de 836; 61 de 96 en Puyehue Cordón Caulle) |
| P6 (informa) | publicación de C0 en negativos limpios de VIIRS 375 (implementada en la sección 9 de `evaluar_fk.py`; la versión 1 la anunciaba y ningún script la calculaba, verificador 6b) | se informa: DENTRO o FUERA de la banda | entre 80 y 92 %, la banda de A114 con el Test 1 encendido (producción en V1: 88,2 %). Fuera de esa banda, el reproceso no se parece a producción y hay que saber por qué antes de leer lo demás |

**Veredicto por ventana y candidato** (`global_ventana`), en este orden: controles fallidos o brazo mal cableado,
INDECIDIBLE; un P1 VETADO, NO CUMPLE (veto); un P1, P2 o P3 INDECIDIBLE, INDECIDIBLE; un P1 PENDIENTE DE
REPETICIÓN, PENDIENTE DE REPETICIÓN (se resuelve con §5 y se vuelve a evaluar); un P2 PIERDE, NO CUMPLE
(suma); ningún P2 GANA, NO CUMPLE (no gana en ningún sensor); si no, CUMPLE, que se degrada a "CUMPLE EN
DETECCIÓN, FALLA EN MAGNITUD (decide Nicolás)" con un P3 FALLA, y se anota "veto sin sustrato" y "auditoría
espacial pendiente" cuando corresponde. F se juzga en VIIRS 375 y VIIRS 750 (en V2, con los veredictos VIIRS de
K, §3); K en los tres. **El veredicto final es el peor de las dos ventanas** (`--combinar`), por lectura, con este
orden de gravedad: NO CUMPLE, INDECIDIBLE, PENDIENTE DE REPETICIÓN, CUMPLE EN DETECCIÓN, CUMPLE (un NO CUMPLE en
una ventana es definitivo aunque la otra esté pendiente). Mientras D-4 (#782) no se decida, se informan las
dos lecturas y ninguna se elige.

## 7. La prueba del evaluador (`probar_evaluar_fk.py`, salida en `probar_salida.txt`)

Brazos fabricados desde los records de producción de V1 (11 volcanes) con la referencia congelada de V1 y su
línea `FLAGS_BRAZO`, más el run real de Chillán. Cada veredicto puede salir y cada uno tiene su caso que no lo
da:

- **Nulo**: cuatro brazos idénticos dan controles OK, cero pérdidas, EMPATE en las seis sumas, P3 y P4 CUMPLE, y
  el candidato **NO CUMPLE (no gana en ningún sensor)**: un brazo igual al control no gana.
- **P1**: una protegida oculta en F y K da VETADO (A y B); si también la oculta el gemelo, INDECIDIBLE; si sólo K
  la oculta, K INDECIDIBLE y F CUMPLE; una protegida sólo del OCR de Suomi NPP da CUMPLE con A (y se lista) y
  VETADO con B; una sólo de la lectura B da A CUMPLE y B VETADO; con la tabla sola, la del OCR no es positiva.
- **P2**: sin publicar en negativos, GANA y global CUMPLE; sin publicar las Muy Bajo, PIERDE; diez menos donde el
  gemelo tiene veinte, EMPATE.
- **P3**: magnitud de VIIRS 750 dividida por 20, FALLA y el global lo dice. **La primera versión del caso
  multiplicaba por 4 y no falló, con razón**: en VIIRS 750 C0 subestima (mediana 0,46) y 4 veces deja la razón
  en 1,85, más cerca de 1 en logaritmo. La métrica es simétrica en log; queda dicho en §8.
- **P4**: el cúmulo corrido 2 km, FALLA.
- **Controles**: un log de K con banda 21, K mal cableado y todo lo de K INDECIDIBLE; una pasada de menos,
  cobertura despareja; VIIRS 375 de Copahue ausente en los cuatro brazos (la paridad no lo ve), C0 contra
  producción lo ve; el gemelo distinto en 100 pasadas, determinismo FALLA; la capa histórica congelada alterada, o
  un congelado sin capas, referencia_ok falso.
- **Repetición**: sin gemelo ni repetición, PENDIENTE DE REPETICIÓN; la repetición que no la pierde, ruido
  confirmado y CUMPLE; la que la vuelve a perder, VETADO; una ruidosa de V1 que la repetición confirma, VETADO.
- **V2 de verdad** (verificador, punto 5): dos despachos fusionados (dos `--raiz`), dos `--logs`, `--ruido-de`
  con la salida del nulo de V1, tabla sola y VIIRS desde abril. Nulo: controles OK, F derivado de K. Un log de K
  con banda 21 **sólo en V2b**: K mal cableado; ese caso es el que la versión 1 no veía (defecto 1). Una protegida
  VIIRS 375 de marzo oculta en K no decide; una de V2b, PENDIENTE DE REPETICIÓN.
- **Run real de Chillán** (38560317428, gemelo igual a C0): reproduce la suma de su verificador, **C0 52, F 7,
  K 7**, controles OK, P1 VIIRS CUMPLE, y K recupera la alerta MODIS del 2026-10-01 08:35 (5,18 MW).
- **Combinar** nulo y veto: K NO CUMPLE.

> ⚠️ **Nota del 2026-10-15 (D-9, issue #811), posterior al sello; no cambia ninguna regla de este documento.**
> `evaluar_fk.py` ganó una sección 10 que INFORMA P2 y el veredicto con las reglas de las alertas mínimas (SN,
> SE, original y las variantes con 0,04); decide la etiqueta original, como se escribió aquí (`README.md`). La
> autoprueba ganó 4 comprobaciones de esa sección y hoy da **41 de 41** (`probar_salida.txt`): las 37 de abajo
> siguen todas OK. Texto original:

Resultado: **37 de 37** comprobaciones (`probar_salida.txt`), sobre el evaluador tal como queda commiteado. El
caso `v2_cable`, corrido con el evaluador de la versión 1 (`git show` del commit anterior), da "K OK" en el
cableado: es el defecto 1, y la versión 2 lo atrapa. Uso:
`python probar_evaluar_fk.py <TMP> <DIR_NDC>`, con `<DIR_NDC>` bajado de la rama `s146-ab/38560317428` (C0, F, K y
sus logs).

## 8. Lo que este A/B no puede decir

- **Si adoptar.** Eso es A45: tag defensivo, verificador limpio sobre el resultado y el "sí" de Nicolás.
- **El recall MODIS fuera de Láscar**: hay 4 protegidas MODIS fuera de Láscar en V1 (3 de Chillán en erupción,
  ya probadas en #796, y 1 de Villarrica) y ninguna en V2. Lo que sí mide fuera de Láscar es el **costo** (836
  negativos limpios MODIS en V1, 2.173 en V2).
- **El paquete MODIS completo** de la tarea 1.6: compuerta y fondo por vecinos no existen como flag.
- **El tope D9** en un régimen donde actúe: sigue sin probar (#796).
- **Si el cúmulo está donde MIROVA lo ve.** P4 mide cuánto se mueve entre dos configuraciones, no cuál acierta:
  `Distancia_km` no trae acimut (A93) y sólo informa si el movido queda más cerca o más lejos del cráter en radio.
- **Ciego no es.** F ya se miró contra B de abril a septiembre y en Chillán; lo nuevo es C0 como control, los 11
  volcanes y K fuera de Láscar.
- **V2 con los records de hoy.** El sustrato de V2 se estimó con records de producción que escribió el código de
  esa época (antes de #535): da el orden de magnitud del poder, no el resultado.
- **Las pasadas `sin_info` y `far_ref`** no entran en la suma (no son negativos limpios); se informan como
  "otras publicadas" (en V1, producción publica 742 de 852 en VIIRS 375).
- ⚠️ **Decidido después del sello, D-9 (2026-10-15, issue #811): regla SN, las alertas de 0,05 MW o menos cuentan
  como "MIROVA no vio nada".** Este A/B sigue decidiendo con la regla original y la sección 10 de `evaluar_fk.py`
  informa SN, SE y las variantes con 0,04 (`README.md`). Texto original:
  **El borde de 0,05 MW**: MIROVA dice NONE en pasadas que el scraper registra como alerta Muy Bajo
  (`docs/S151_CRITERIO_CLASE_MIROVA.md` §5); de qué lado cae el error en señales mínimas queda abierto.
- **La métrica de magnitud es simétrica en logaritmo**: no dice si subestimar es preferible a sobrestimar. Que el
  caso de 4 veces no fallara no es un defecto del criterio (acercarse a 1 en log es acercarse a MIROVA), pero
  dice que P3 tiene **poco poder** contra cambios que mueven la razón a través de 1 (verificador, 6g). Y P3 sólo
  compara las alertas que publican los dos: **no mide la magnitud de las alertas recuperadas** (las que el
  candidato publica y C0 no, como la MODIS del 1-oct en Chillán); esas se listan en P1, sin vara de magnitud.
- **C3 de `sustrato.py` no decide nada** (verificador, 6e): su umbral de 25 % lo elegí yo, sin nulo medido; sólo
  dice que el conteo del sustrato pareaba por hora.
- **Los otros 34 volcanes** no corren.

## 9. Qué cambió de la versión 1 a la 2 (verificador con contexto limpio del PR #797)

| punto del verificador | cambio | caso de prueba que lo atrapa |
|---|---|---|
| 1. `flags_leidos` leía sólo el primer log | lee el log de cada directorio de `--logs` y cada uno tiene que estar | `v2_cable` |
| 2. capas de la referencia sin congelar | `congelar.py capas`; capas pasadas explícitas a `armar_tabla.py` (`--historico`, `--respaldo`), a la protección y a `sustrato.py`; sha en el manifiesto | `capa_mod`, `sin_capas` |
| 3. F en V2 sin veredicto | el VIIRS de F en V2 se deriva de K | `v2_nulo` |
| 4. pérdida de V2 sin repetición salía VETADO; ruidosa de V1 sin salida | PENDIENTE DE REPETICIÓN; camino de resolución común en §5 | `sin_rep`, `v2_abril`, `rep_no`, `rep_si`, `gem_rep` |
| 5. faltaba un caso V2 completo | casos `v2_*` con fusión, dos logs, `--ruido-de`, tabla sola y VIIRS desde abril | `v2_*` |
| 6a. el veto con poder es de Láscar | dicho en §3, con los conteos por volcán de `sustrato.py` | (documento) |
| 6b. P6 sin script; job vacío común a todos | P6 en la sección 9 del evaluador; C0 contra producción en la cobertura | `nulo` (P6), `vacio` |
| 6c. 0,5 km elegidos | dicho en P4 | (documento) |
| 6d. ruido neto de P2 | pasadas discordantes | `empate` |
| 6e. C3 | dicho en §8 y en `sustrato.py` | (documento) |
| 6f. NOAA-21 antes del 2026-04-09 | dicho en §3 | (documento) |
| 6g. P3 con poco poder, sin las recuperadas | dicho en §8 | (documento) |
