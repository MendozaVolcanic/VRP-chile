# S150: la conectiva `max` y la banda 22, leídas mes a mes (marzo a agosto de 2026)

> Evaluación de la cola del pre-registro v3 (`experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`,
> aprobado por Nicolás el 2026-09-21). Los diez despachos terminaron el 2026-09-22; mayo ya estaba evaluado
> y verificado (`docs/S149_RESULTADO_CONECTIVA_MAYO.md`). Acá se evalúan junio, julio y agosto en VIIRS, y
> marzo a junio de MODIS en Láscar. **Abril queda INDECIDIBLE** (cobertura despareja, ver §1).
> Todos los números salen de los archivos de `experiments/_s149_prereg_invierno/resultados/`; ninguno está
> transcrito a mano desde otro lado.
>
> **Estado: SIN VERIFICADOR con contexto limpio todavía.** La mejora en negativos limpios supera el 30 %,
> así que la regla del proyecto exige el verificador antes de que esto se use para decidir.

## 0. En una pantalla

**El fenómeno.** De noche, el píxel caliente de un cráter destaca contra su entorno por dos caminos: por
cuánto se aparta de la temperatura de fondo (el dNTI) y por cuánto se aparta de la variabilidad de ese
fondo. La conectiva decide si basta uno de los dos caminos (`min`, lo de hoy) o si hacen falta los dos
(`max`, lo que Coppola 2014 escribe como AND). Con `min`, un píxel al borde del barrido, sobre un fondo frío
y ruidoso, pasa por el camino más fácil. Por eso publicamos tanto en las noches en que MIROVA no vio nada.

**Lo que dicen los meses (VIIRS 375, brazo B sin Test 1 contra brazo F, que agrega `max`):**

| mes | negativos limpios: B, F | borde/nadir de F | recall por pasada (etiqueta que decide) | P5 | C8b | regla del pre-registro |
|---|---|---|---|---|---|---|
| mayo | 30,1 % a 2,3 % | 0,58 | tabla sola: 187 de 195, 0 pérdidas de 0,5 MW o más | cumple | cumple | MERECE SEGUIR |
| junio | 32,8 % a 1,5 % | 0,27 | tabla sola: 157 de 160, 0 pérdidas de 0,5 MW o más | cumple | cumple | MERECE SEGUIR |
| julio | 46,5 % a 2,4 % | 0,09 | tabla y OCR: 150 de 153, 0 pérdidas de 0,5 MW o más | **falla** (0,40 contra nulo 0,35) | cumple | MERECE SEGUIR |
| agosto | 34,7 % a 3,7 % | 0,04 | tabla y OCR: 110 de 120, **2 pérdidas de 0,5 MW o más** | cumple | cumple | **NO ADOPTAR por la letra de P4** (ver §3) |
| abril | sin evaluar | | | | | INDECIDIBLE (cobertura) |

**Agregado de mayo a agosto** (`agregado_mayo_agosto.txt`): en negativos limpios B publica 692 de 1.895
(36,5 %) y F 48 (2,5 %). De las alertas que B publica, F conserva 757 de 792 (95,6 %) con la etiqueta
completa y 542 de 560 (96,8 %) con la tabla sola.

**MODIS, Láscar, marzo a junio** (`modis_lascar_B_J_K.txt`), intervalos de Wilson al 95 %:

| brazo | publica cuando MIROVA alerta | publica en negativos limpios | ¿separa? |
|---|---|---|---|
| B (banda 21, sin Test 1) | 0 de 73 (0,0 %) | 0 de 96 (0,0 %) | no: no ve nada |
| J (banda 22) | 68 de 73 (93,2 %) [84,9 a 97,0] | 11 de 96 (11,5 %) [6,5 a 19,4] | **sí** |
| K (banda 22 y `max`) | 67 de 73 (91,8 %) [83,2 a 96,2] | 2 de 96 (2,1 %) [0,6 a 7,3] | **sí** |

Hoy MODIS en producción publica 11,7 % de las alertas contra 11,5 % de los negativos (AUDIT_S149): no
discrimina. Con banda 22, en Láscar, sí. **La salvedad pesa**: sólo se corrió Láscar, que es el único
volcán con alertas MODIS en esos meses; la tasa de falsos de J y K en los otros diez volcanes **no está
medida** (ver §5).

## 1. Cobertura y determinismo, antes de mirar nada

- **Junio, julio y agosto (11 volcanes)**: cobertura pareja, mismas pasadas en los dos brazos (3.520,
  3.497 y 3.135).
- **Abril: COBERTURA DESPAREJA.** Al brazo B le falta Chaitén (3.082 pasadas contra 3.433). Hay que
  repetir ese job con el mismo código antes de evaluar (A108). **No se pudo repetir hoy**: el token de
  Earthdata venció el 2026-10-03 y todo workflow que baja gránulos falla con 401 (§6).
- **Ventanas de Láscar sólo**: el recolector del workflow las marca en rojo porque espera 11 volcanes; es
  el defecto conocido. Dentro de Láscar la cobertura es pareja en los cuatro meses.
- **Determinismo**: el gemelo de B coincide con B en la decisión de publicar en el **100 %** de las
  pasadas, en marzo, abril, junio, julio y agosto, y en los tres sensores (`determinismo_lascar_contra_B.txt`
  y la línea DETERMINISMO de cada resultado).

**Defecto de instrumento encontrado y corregido.** `evaluar_ventana.py` comparaba el gemelo contra el
`--control` de la ventana. En las ventanas de Láscar el control es J (banda 22), así que la primera
corrida dio "90 % de coincidencia, INDECIDIBLE": eso medía cuánto se parecen B y J, no si el código es
determinista. Se agregó `--control-gemelo` (por defecto, el control, así que julio y agosto no cambian:
comprobado, predicciones idénticas) y `--runs-control-gemelo`, y la línea imprime contra qué perfil
compara. Con B como referencia, 100 %.

## 2. VIIRS 375: lo que `max` apaga y lo que deja

**Negativos limpios.** En los cuatro meses B publica entre 30 y 47 % de las pasadas en que MIROVA miró y no
vio nada, y F entre 1,5 y 3,7 %. La tabla de terminado congelada pide 10 % en focales y 15 % en nevados.

**Dónde estaba lo falso.** En el control la tasa falsa del borde del barrido es 1,9 a 3,6 veces la del
nadir. Con `max` se invierte (0,04 a 0,58): lo que queda está cerca del nadir, que es donde el píxel es
chico y una anomalía tiene más chance de ser real. Es el mismo patrón de septiembre y mayo.

**Recall por tramo de magnitud** (`recall_por_magnitud_jun_jul_ago.txt` y `..._sept_mayo.txt`). El costo
de `max` está abajo de 0,10 MW:

| tramo de MIROVA | mayo: B, F | junio: B, F | julio: B, F | agosto: B, F |
|---|---|---|---|---|
| bajo 0,05 MW | 87 %, 73 % | 94 %, 75 % | 100 %, 70 % | 89 %, 56 % |
| 0,05 a 0,10 | 96 %, 85 % | 89 %, 82 % | 97 %, 97 % | 91 %, 81 % |
| 0,10 a 0,20 | 100 %, 98 % | 100 %, 96 % | 100 %, 100 % | 100 %, 96 % |
| 0,20 a 0,50 | 98 %, 97 % | 99 %, 97 % | 100 %, 100 % | 100 %, 98 % |
| 0,50 o más | 96 %, 93 % | 98 %, 97 % | 91 %, 91 % | 94 %, 83 % |

Los tramos bajo 0,10 MW son entre 21 y 33 % de las alertas de cada mes. Esta tabla es la que la enmienda
del pre-registro pone en manos de Nicolás para el veredicto de recall en VIIRS.

**P5, julio, falla.** Entre las pasadas que MIROVA lista con VRP 0 en una noche en que sí alertó, F recorta
a 0,40 de lo que publica B, y un apagado parejo daría 0,35. O sea que en julio `max` no es más selectivo que
el azar en ese estrato. Es informativa: P5 no decide. Los otros tres meses cumplen (0,36, 0,28 y 0,21).

## 3. Agosto: las dos alertas de 0,5 MW o más que `max` pierde

Las dos son de Láscar, de **Suomi NPP**, llegan **sólo por el OCR** (la tabla `latest.php` no las trae) y
caen **al borde del barrido** (cenit del satélite de 63 y 59 grados):

| pasada | MIROVA | lo que publicaba B | qué hace F |
|---|---|---|---|
| 2026-08-17 05:00 | 0,60 MW a 3,24 km | 0,024 MW, cúmulo a 1,5 km del cráter | el cúmulo salta a 24,6 km; no publica |
| 2026-08-22 05:06 | 1,65 MW a 1,22 km | 0,018 MW, cúmulo a 0,3 km del cráter | el cúmulo salta a 8,2 km; no publica |

Lectura física. **Sospecha**, no medido: en esas dos pasadas B ya veía el cráter apenas, con el 1 a 4 % de
la energía que reporta MIROVA. El píxel caliente estaba en el límite del umbral y `max`, que le exige
pasar por los dos caminos, lo apagó. Las otras pasadas de esas noches que MIROVA da como alerta (NOAA-20
a las 05:18 del 17, con 0,19 MW; NOAA-20 a las 05:24 y NOAA-21 a las 06:12 del 22, con 0,23 y 0,11 MW;
cenit de 32 a 50 grados) los dos brazos las publican; la de NOAA-21 de las 06:06 del 17 MIROVA la lista
con VRP 0. No es un problema general de Suomi NPP: la mediana mensual de la magnitud de B sobre la de
MIROVA en Suomi NPP va de 0,56 a 1,00 entre mayo y agosto, dentro del rango de los otros dos satélites
(`magnitud_por_satelite.txt`). Lo raro es que MIROVA dé 0,60 y 1,65 MW en Suomi NPP al borde del barrido,
de tres a quince veces lo que da en las pasadas de menor ángulo de esas mismas noches. Eso queda **SIN
VERIFICAR**: pide mirar las dos imágenes de MIROVA (`imagenes_satelitales/Lascar/2026-08-17/05-00-00_...`
y `.../2026-08-22/05-06-00_...` en el repo Mirova-v1) y el gránulo.

**Qué dice la regla.** Por la letra de P4 (sección 5 del pre-registro), "ninguna pérdida de 0,5 MW o más"
falla y agosto da NO ADOPTAR. La enmienda del 2026-09-21, escrita después de mayo, dejó el corte de
0,5 MW sólo para MODIS y el veredicto de recall en VIIRS en manos de Nicolás, mirando la tabla por tramo.
No corresponde que yo elija cuál de las dos lecturas manda: se dice así y lo decide Nicolás. En las otras
tres ventanas, ninguna pérdida pasa de 0,5 MW con la etiqueta que decide.

## 4. VIIRS 750: `max` casi no toca el recall, y el cero sigue ahí

Agregado de mayo a agosto: B publica 109 de las 149 alertas de MIROVA (73,2 %) y F conserva 106 de esas
109. En negativos limpios, 8,6 % a 1,1 %. P1 es INDECIDIBLE en los cuatro meses por la cláusula de
sustrato: B ya publica menos de 18 %. Lo que falta en VIIRS 750 no es la conectiva: es el 27 % de alertas
que ninguno de los dos brazos publica (la brecha del "cero" de AUDIT_S149, Fase 2). En agosto F pierde una
alerta de 0,5 MW o más en VIIRS 750 (`agosto_VIIRS750.txt`). En julio C8b falla en VIIRS 750
(observado igual al percentil del nulo, con 14 alertas publicadas: poco sustrato).

## 5. MODIS: lo que esto permite decir y lo que no

**Regla de la sección 7 del pre-registro, aplicada al agregado de los cuatro meses:**
- K no pierde ninguna positiva de 0,5 MW o más que J publique: **cumple** (su única pérdida es de 0,28 MW,
  Aqua, 2026-05-06).
- K no publica más que J en negativos limpios: **cumple** (2 contra 11).
- J publica al menos la mitad de las positivas: 68 de 73, **hay sustrato**.

**Lo que no se puede decir todavía**: que la banda 22 arregla MODIS en la réplica. Estos 96 negativos
limpios son todos de Láscar. La brecha de MODIS en producción viene sobre todo de los otros volcanes (11,5 %
de negativos publicados en los 11). Hace falta un despacho de J y K sobre los 11 volcanes, con la misma
ventana, para medir la tasa de falsos donde importa. No se pudo despachar hoy (§6).

**Informativo, D21**: con banda 21 y sin el Test 1, B no publica ni una de las 73 alertas MODIS de Láscar.
Hoy, lo que MODIS publica en producción en Láscar lo publica el Test 1 integrado, no los Tests 2 y 3.

## 6. Lo que quedó sin hacer, y por qué

- **Abril**: repetir el job de Chaitén del brazo B (run 35639417826) con el mismo código. **Bloqueado**: el
  token de Earthdata venció el 2026-10-03. El NRT falla desde las 07:36 UTC de ese día
  (`EARTHDATA_CREDENTIAL_INVALID`, "Token ... has expired"). Rotarlo es de Nicolás.
- **MODIS J y K en los 11 volcanes**: mismo bloqueo.
- **Verificador con contexto limpio** sobre este resultado: pendiente; lo exige la mejora mayor que 30 %.
- **Las dos imágenes de MIROVA de agosto** (§3): pendiente.
