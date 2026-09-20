# Nulo por píxel alertado de la batería del Apéndice A: criterio escrito antes de ver salidas (S146)

> Escrito el 2026-09-20 cerca de las 11:00 UTC, ANTES de escribir el evaluador por píxel y ANTES de
> que exista ninguna salida con píxeles alertados (no existe ninguna: la batería nunca los guardó).
> El sha256 de este archivo queda en `experiments/_s146_bateria/HASH_CRITERIO_NULO.txt`. El
> evaluador lo recalcula en cada corrida y lo imprime; si no coincide, lo dice en la primera línea y
> el resultado de los nulos deja de valer como pre-registrado.
>
> Este criterio COMPLEMENTA a `docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md`, que está sellado y
> no se toca. El veredicto de cada caso (ACIERTO, FALLO, INDECIDIBLE, 9 de 9) lo sigue dando ese
> documento con su predicado del cúmulo primario. Acá se define sólo el nulo con poder que a ese
> documento le faltó (su propia sección 4, "Límite de N1 y N2").

## 0. Contaminación declarada

No es ciego. Antes de escribirlo leí `docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md` entero, o sea
que conozco, para los ocho brazos ya corridos, dónde cayó el cúmulo PRIMARIO de cada pasada y que
los nulos por cúmulo primario salieron vacíos. Leí también la sección V-16 del verificador, que hizo
un barrido fino de rumbos con el primario del mejor brazo (lleno a 60, 90 y 120 grados, vacío en el
resto).

Lo que NO conozco, porque no existe en ningún archivo: qué píxeles alertó cada brazo fuera del
cúmulo primario. La selección del pipeline está anclada al cráter, así que un brazo puede tener
alertas a 10 km que nunca quedaron guardadas. Eso es exactamente lo que mide este nulo, y es
genuinamente incierto para mí: no tengo idea de si las cajas rotadas van a salir vacías.

## 1. El fenómeno que se quiere distinguir

Una vara "regala aciertos" cuando el brazo siembra alertas por toda la escena (ruido de
cuantización, bordes de nube, línea de costa, gradiente topográfico) y entonces cualquier caja de
5 km, puesta donde sea, termina con algo adentro. En ese caso, encontrar algo en la caja de la
fisura de Fimmvörðuháls no dice que el brazo vio la lava: dice que el brazo alerta en todas partes.
Si en cambio el brazo alerta sólo donde hay calor, la misma caja puesta a la misma distancia de la
cumbre, en rumbos donde no hay nada volcánico, queda vacía.

## 2. La unidad: qué es un "píxel alertado"

Por cada pasada nocturna procesada, el probe guarda TODOS los píxeles de la máscara final de
alerta que el procesador MODIS le entrega a `cluster_hotspots` (la máscara que sale de los Tests 2
y 3, la recaptura del segundo pase y los filtros posteriores), más los píxeles del Test 1 cuando el
procesador agrupa por ese camino. Cada píxel lleva lat, lon, su magnitud individual en MW y los
caminos que lo marcaron.

**Píxel que cuenta para el nulo (decisorio): píxel alertado con `vrp_mw > 0`.** La razón es de
simetría con el predicado de acierto, que exige magnitud mayor que cero: un píxel alertado cuyo
exceso de radiancia se recorta a cero no puede producir un acierto en la caja de la fisura, así que
tampoco debe contar como regalo en una caja nula. El conteo de TODOS los píxeles alertados,
con o sin magnitud, se reporta al lado como dato informativo y no decide nada.

Un píxel está "en la caja" si su centro (lat, lon) queda a 5,0 km o menos del centro de la caja
(haversine, la misma función de la batería). El radio es el de toda la batería; no se agrega ningún
parámetro.

Universo de pasadas: todas las pasadas nocturnas MODIS procesadas de la fecha del caso, por brazo,
SIN el filtro de validez por NTI de A5, A6 y A8. Más pasadas son más oportunidades de llenar una
caja nula, así que es la elección que juega en contra del resultado cómodo.

## 3. Las cajas

Distancia y rumbo de referencia: los del pre-registro sellado, 9,53 km y 88,6 grados (la fisura del
GVP respecto de la cumbre del catálogo). El evaluador los recalcula, no los copia.

**N1px, la caja rotada en la escena de A2.** Centro a 9,53 km de la cumbre de Eyjafjallajökull,
rumbos 178,6, 268,6 y 358,6 grados (la fisura girada 90, 180 y 270). Tres cajas por brazo,
disjuntas entre sí y con la de la fisura. En ninguna hay nada volcánico activo el 7 de abril de
2010. La del sur mira hacia la planicie costera, el confusor que el propio autor nombra en el caso.

**N2px, la caja desplazada en los otros ocho casos.** El mismo desplazamiento (9,53 km; rumbos
88,6, 178,6, 268,6 y 358,6) aplicado a la cumbre de cada uno de los otros ocho volcanes. 32 cajas
por brazo.

**Una exclusión, fijada acá y con su razón: A1 Bezymianny, rumbo 358,6.** Esa caja NO es un lugar
"donde no hay nada que detectar": contiene la cumbre de Klyuchevskoy (56,057 N, 160,638 E según
`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`), que queda a 9,79 km y rumbo 17,3 grados de
Bezymianny y a 3,16 km del centro de esa caja (calculado en esta sesión). El mismo archivo trae
detecciones MODIS de MIROVA en Klyuchevskoy el 05-11-2011 y el 30-01-2012, del orden de 0,1 MW, o
sea que en enero de 2012 había ahí una fuente térmica débil y plausible. Un píxel alertado en esa
caja puede ser calor real de otro volcán y no un regalo. La caja se evalúa y se reporta aparte,
rotulada "fuente volcánica conocida", y NO entra ni al numerador ni al denominador de la tasa.
Revisé con el mismo cálculo el vecino de Erta Ale (Hayli Gubbi, a 5,86 km del centro de la caja más
cercana: fuera) y no conozco otra fuente activa a menos de 15 km de las otras siete cumbres en sus
fechas; eso último es de memoria y queda como SOSPECHA. Si el resultado llena una caja y alguien
quiere explicarla después con una fuente real que acá no nombré, esa explicación es post hoc y se
rotula así: la caja cuenta como ocupada.

Total de cajas nulas por brazo que entran a la tasa: 3 (N1px) + 31 (N2px) = **34**.

**NEGpx, la caja de cumbre en los casos negativos.** En A4 Dubbi, A7 Tolbachik y A9 Stromboli, la
caja de 5 km centrada en la cumbre. Tres cajas por brazo. El autor no detecta nada ahí.

## 4. Qué cuenta como vacío y qué resultado diría que la vara regala aciertos

Una caja está **VACÍA** si, sumando todas las pasadas del caso para ese brazo, tiene CERO píxeles
alertados con magnitud. Con uno o más está **OCUPADA**. No hay umbral de magnitud ni de número de
píxeles: un solo píxel de 0,01 MW ocupa la caja, porque un solo píxel de 0,01 MW en la caja de la
fisura bastaría para que un cúmulo primario diera "acierto".

Reglas, por brazo:

- **R1 (A2, decisoria sobre el acierto).** Si alguna de las tres cajas N1px está OCUPADA, el
  acierto de ese brazo en A2 pasa a **INDECIDIBLE**, igual que fija la sección 4 del pre-registro
  sellado para N1. En esa escena la vara no distingue.
- **R2 (tasa de regalo, sobre las 34 cajas).**
  - 0 de 34 ocupadas: **la vara no regala aciertos a este brazo**, con la salvedad de R4. Cero de
    34 acota la tasa real por debajo de 9 % aproximadamente (regla de tres, 3/34), no la prueba
    nula.
  - 1 a 3 de 34: **regalo marginal**. Se reporta caja por caja con sus píxeles y magnitudes. La
    vara no queda declarada limpia para ese brazo. El acierto de A2 se sostiene sólo si las
    ocupadas no son de N1px (R1).
  - 4 o más de 34 (más de 10 %): **la vara regala aciertos a este brazo**. El acierto de A2 de ese
    brazo deja de contar como evidencia, aunque las tres cajas de N1px estén vacías, y su 9 de 9,
    si lo tiene, se informa como "9 de 9 sin valor discriminante".
  Los cortes 1 y 4 los fijo acá sin más base que ésta: con 34 cajas, 4 ocupadas es el primer valor
  cuya cota inferior de 95 % para la tasa (cerca de 3 %) es incompatible con "casi nunca". Son
  arbitrarios y están escritos antes de medir; no se mueven después.
- **R3 (negativos).** Si alguna caja NEGpx está OCUPADA en un brazo cuyo veredicto por cúmulo
  primario para ese caso fue CONFORME, el caso se informa como **"conforme con reserva: hay píxeles
  alertados con magnitud a 5 km o menos de la cumbre que el cúmulo primario no mostró"** y el total
  del brazo se escribe con la reserva (por ejemplo "9 de 9 con 1 reserva"). No cambia el veredicto
  sellado, que es por cúmulo primario; lo califica. Si la caja está vacía, el negativo queda
  confirmado también por píxel.
- **R4 (sustrato, para no leer un nulo muerto como limpio).** Por brazo se cuenta cuántos píxeles
  alertados con magnitud hay en el anillo de 4,53 a 14,53 km de la cumbre, en cualquier rumbo,
  sumando los nueve casos. Si ese número es cero y a la vez el brazo tiene un acierto en A2 por
  cúmulo primario, la captura está rota (el cúmulo primario de A2 está hecho de píxeles que deberían
  aparecer ahí) y el evaluador TERMINA CON ERROR. Si es mayor que cero, un nulo vacío significa de
  verdad "el brazo alertó fuera de la cumbre y no cayó en las cajas nulas".

## 5. Controles del instrumento, con su nulo medido (A110)

- **Cpx-a, integridad de la captura.** En cada pasada, la suma de `n_pixels` de los cúmulos de cada
  llamada debe ser igual al número de píxeles listados de esa llamada, y el cúmulo primario
  capturado debe coincidir en posición con el `primary_cluster` del record. Si no, error.
- **Cpx-b, contraste en la caja de la fisura.** Para cada brazo con acierto en A2 por cúmulo
  primario, la caja de la fisura debe tener al menos un píxel con magnitud (el centroide del
  primario está adentro y tiene magnitud, así que alguno de sus píxeles tiene que estar cerca). Si
  tiene cero, error (captura muerta). Se reporta además el conteo y los MW de la caja de la fisura
  al lado de los de las cajas nulas, para que el contraste se lea en las mismas unidades.
- **Cpx-c, control sintético, corrido en local antes de despachar.** Una salida fabricada con un
  píxel plantado en una caja rotada debe dar OCUPADA y cambiar el acierto a INDECIDIBLE; la misma
  salida sin ese píxel debe dar VACÍA; un píxel plantado con magnitud cero no debe ocupar la caja
  decisoria pero sí aparecer en el conteo informativo; y un píxel plantado a 5,2 km del centro debe
  quedar fuera. Si alguno de los cuatro falla, el evaluador no sirve.
- **Cpx-d, identidad del predicado sellado.** Con el cúmulo primario de las salidas nuevas y la
  vara vieja, el evaluador debe reproducir los veredictos commiteados de S136 y S137 en los ocho
  brazos ya corridos (72 celdas). Una diferencia no es error del nulo, pero se reporta como DERIVA:
  el pipeline o los gránulos de NASA cambiaron desde el 13-09-2026 y la comparación con los informes
  viejos deja de ser directa.

## 6. Las dos preguntas del instrumento

1. Si lo que mide estuviera roto (la vara regala aciertos), ¿fallaría? Sí: R1 y R2 cuentan alertas
   reales por píxel en cajas donde no hay nada, y ya no dependen de qué cúmulo eligió el pipeline.
   Cpx-c lo demuestra con un píxel plantado.
2. Si el instrumento estuviera muerto (la captura no engancha, o el evaluador no mira posiciones),
   ¿se vería distinto? Sí: R4 y Cpx-b terminan con error si un brazo acierta A2 sin píxeles en la
   caja de la fisura, Cpx-a compara captura contra record, y el probe se niega a correr si alguna
   de las funciones que envuelve no existe con ese nombre en `pipeline.process_modis`.

## 7. Qué NO decide este criterio

No adopta nada, no cambia el veredicto sellado de ningún caso salvo por R1 (que el sellado ya
preveía), no mide paridad con MIROVA y no arregla los otros defectos del instrumento que S138
documentó (mezcla de pasadas de dos noches, cúmulos con tope de 5 MW contados como aciertos).
