# Pre-registro S151 (tarea 1.6 del loop): F y K contra producción en los 11 Tier A

> **VERSIÓN 1, SIN APROBAR, SIN DESPACHAR.** Escrito y commiteado antes de correr ningún brazo sobre estas
> ventanas. Falta el verificador con contexto limpio y el "sí" de Nicolás (el candado `preregistro_aprobado`
> del workflow es suyo). Todos los números de este documento salen de los scripts de esta carpeta, con su
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

**Referencias congeladas** desde el remoto del dueño (Mirova-v1@`c5944c6`, 2026-10-14 14:30 UTC), con recorte
[desde − 1 día, hasta + 2 días] y sha256 con fin de línea LF en `MANIFIESTO.json` (`congelar.py`; LF porque
autocrlf deja los CSV en CRLF en Windows y un sha crudo mediría la máquina: pasaba con el congelado de #796). El
manifiesto anota además el sha de la capa histórica de la unión (`data/mirova_reference/union_historica/`), que
el cargador agrega por defecto; el evaluador avisa si cambió. Los CSV van a git forzados (`*.csv` está en
`.gitignore`), como en #796.

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
2. **Versión de producto por pasada**: ninguna pasada protegida con versión distinta entre brazos.
3. **Cableado de cada brazo y cada volcán**: la línea `FLAGS_BRAZO` de cada log tiene que traer el perfil y el
   directorio del brazo y exactamente los flags declarados (Test 1, conectiva, banda 22, etiqueta, tope), y
   `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` y `ENABLE_VENT_ANCHORED_CLUSTERING` con su valor de producción; y la
   huella en los records: un brazo sin Test 1 no tiene ningún `triggered_test1`. Un brazo mal cableado deja
   INDECIDIBLE todo lo que lo usa.
4. **Determinismo**: G contra C0 en los tres sensores y K contra F en VIIRS, misma decisión de publicar en 98 de
   cada 100 pasadas o más (umbral heredado de S149 y S150).
5. **La referencia es la congelada**: sha256 LF de los dos CSV contra el manifiesto.
6. **El predicado del tablero** es el de `frontend/index.html` ejecutado con node (A97); el evaluador imprime su
   sha256.

**Ruido en las pérdidas.** Una pérdida en una pasada donde G también cambia respecto de C0 (ruido del control),
o, en VIIRS, donde F y K deciden distinto (ruido del candidato), no se descuenta: deja ese veto INDECIDIBLE. En
V2 no hay gemelo: **toda pérdida neta de V2 se confirma repitiendo los jobs de C0 y K de ese volcán y esa mitad**,
y se evalúa con `--repeticion`; si en la repetición no se pierde, queda INDECIDIBLE. Para la suma de V2 el ruido
es la fracción medida por el gemelo en V1, por sensor (`--ruido-de`).

## 6. Predicciones y reglas (secciones 5 a 8 de `evaluar_fk.py`, que las implementa tal cual)

Todo se cuenta **por pasada**, por sensor, por lectura (A y B) y por ventana, contra C0. "Publica" es el
predicado del tablero. Una alerta protegida es la de `scripts/clase_mirova.alerta_protegida` (VRP de la pasada
de 1 MW o más, recalculado del VRP; A: alerta del scraper; B: cualquier fila que no sea RUTINA).

| # | qué | regla (decide) | predicción, y de dónde sale |
|---|---|---|---|
| **P1** veto | pérdidas: protegidas que C0 publica y el candidato no | VETADO con una pérdida neta; INDECIDIBLE si las únicas son ruidosas; CUMPLE con cero; SIN SUSTRATO si C0 no publica ninguna | **Lectura A: CUMPLE** en VIIRS (Chillán: 13 de 13 y 11 de 11; las cinco pérdidas fuertes de `max` en meses eran filas del OCR con la imagen de otra pasada) y en MODIS (en Láscar K publica 67 de 73, C0 8). **Lectura B: al menos una pérdida en VIIRS** (tarea 1.10: con B, F perdió en Chillán un calor lejano de 1,52 MW que B publicaba como otro objeto) |
| **P2** suma bajo 1 MW | alertas Muy Bajo que el brazo no publica + publicaciones en negativos limpios; ruido = diferencia de la suma entre G y C0. En V1, las pasadas cuya alerta descansa sólo en el OCR de Suomi NPP salen de la suma que decide (su etiqueta depende de la clase) y se imprime también la suma con ellas | GANA si la suma del candidato es menor que la de C0 menos el ruido; PIERDE si es mayor que la de C0 más el ruido; si no, EMPATE | **GANA en VIIRS 375 y VIIRS 750 en las dos ventanas** (producción publica 734 de 832 negativos de VIIRS 375 en V1; en Chillán la suma fue 37 contra 4 y 14 contra 2). **GANA en MODIS** en V2 (producción pierde 25 de 26 alertas Muy Bajo, todas de Láscar, y publica 252 negativos) y en V1 (producción publica 110 negativos MODIS; 61 en Puyehue Cordón Caulle), con menos confianza: fuera de Láscar el costo de K es lo que esta prueba mide por primera vez |
| **P3** magnitud | d = abs(log10(brazo/MIROVA)) − abs(log10(C0/MIROVA)), en las alertas que publican los dos; ruido = mediana de d del gemelo | FALLA si el intervalo bootstrap al 95 % de la mediana de d queda entero sobre 0 **y** la mediana supera el ruido; con menos de 5 pares, SIN SUSTRATO | CUMPLE en los tres sensores (Chillán: 0,563 contra 0,548 en VIIRS 375 y 0,385 igual en VIIRS 750). Riesgo declarado: S147 midió que sin Test 1 la razón baja 0,10 a 0,18 en VIIRS 375 de Láscar, Isluga y Tupungatito |
| P3b (informa) | mediana de log10(brazo/C0) en VIIRS 375 de esos tres volcanes | se informa | **negativa en los tres** (S147: donde el Test 1 recompone la magnitud, apagarlo la achica) |
| **P4** el cúmulo se mueve | fracción de alertas publicadas por C0 y el candidato en que el cúmulo se corre más de 0,5 km | CUMPLE si no supera el límite superior de Wilson al 95 % de lo que midió S147 en alertas, 2 de 149, que es **0,048**; FALLA si lo supera. FALLA no veta: obliga a una auditoría espacial (A61) de las pasadas movidas antes de proponer nada | **CUMPLE en el agregado**, con el movimiento concentrado donde MIROVA no vio nada (S147: 22,8 % contra 1,3 %). En MODIS de la erupción **sí se mueve** (Chillán: 2 de 2 alertas MODIS movidas) |
| P5 (informa) | MODIS fuera de Láscar: negativos limpios publicados por K y por C0, por volcán | se informa; ya pesa en P2 | K publica menos que C0 (producción en V1: 107 de 836; 61 de 96 en Puyehue Cordón Caulle) |
| P6 (informa) | publicación de C0 en negativos limpios de VIIRS 375 | se informa | entre 80 y 92 %, la banda de A114 con el Test 1 encendido (producción en V1: 88,2 %). Fuera de esa banda, el reproceso no se parece a producción y hay que saber por qué antes de leer lo demás |

**Veredicto por ventana y candidato** (`global_ventana`), en este orden: controles fallidos o brazo mal cableado,
INDECIDIBLE; un P1 VETADO, NO CUMPLE (veto); un P1, P2 o P3 INDECIDIBLE, INDECIDIBLE; un P2 PIERDE, NO CUMPLE
(suma); ningún P2 GANA, NO CUMPLE (no gana en ningún sensor); si no, CUMPLE, que se degrada a "CUMPLE EN
DETECCIÓN, FALLA EN MAGNITUD (decide Nicolás)" con un P3 FALLA, y se anota "veto sin sustrato" y "auditoría
espacial pendiente" cuando corresponde. F se juzga en VIIRS 375 y VIIRS 750; K en los tres. **El veredicto final
es el peor de las dos ventanas** (`--combinar`), por lectura. Mientras D-4 (#782) no se decida, se informan las
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
  cobertura despareja; el gemelo distinto en 100 pasadas, determinismo FALLA.
- **Repetición** (V2): la pérdida que no se repite da INDECIDIBLE; la que se repite, VETADO.
- **Run real de Chillán** (38560317428, gemelo igual a C0): reproduce la suma de su verificador, **C0 52, F 7,
  K 7**, controles OK, P1 VIIRS CUMPLE, y K recupera la alerta MODIS del 2026-10-01 08:35 (5,18 MW).
- **Combinar** nulo y veto: K NO CUMPLE.

Resultado: **26 de 26** comprobaciones (`probar_salida.txt`), sobre el evaluador tal como queda commiteado. Uso:
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
- **El borde de 0,05 MW**: MIROVA dice NONE en pasadas que el scraper registra como alerta Muy Bajo
  (`docs/S151_CRITERIO_CLASE_MIROVA.md` §5); de qué lado cae el error en señales mínimas queda abierto.
- **La métrica de magnitud es simétrica en logaritmo**: no dice si subestimar es preferible a sobrestimar.
- **Los otros 34 volcanes** no corren.
