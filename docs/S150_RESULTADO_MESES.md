# S150: la conectiva `max` y la banda 22, leídas mes a mes (marzo a agosto de 2026)

> Evaluación de la cola del pre-registro v3 (`experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`,
> aprobado por Nicolás el 2026-09-21). Los diez despachos terminaron el 2026-09-22; mayo ya estaba evaluado
> y verificado (`docs/S149_RESULTADO_CONECTIVA_MAYO.md`). Acá se evalúan junio, julio y agosto en VIIRS, y
> marzo a junio de MODIS en Láscar. **Abril queda INDECIDIBLE** (cobertura despareja, ver §1).
> Todos los números salen de los archivos de `experiments/_s149_prereg_invierno/resultados/`; ninguno está
> transcrito a mano desde otro lado.
>
> **Estado: VERIFICADO con contexto limpio** (`docs/audit_s150/VERIFICADOR_RESULTADO_MESES.md`). Todos los
> números se reprodujeron; el arreglo del gemelo es correcto. El verificador encontró cuatro hallazgos de
> gravedad 3 o más, ya incorporados abajo: las pérdidas fuertes de `max` son un **patrón** de cinco casos
> (§3), `max` también recorta alertas reales del borde (§2), la comparación MODIS contra producción mezclaba
> poblaciones (§5), y la enmienda del recall se usaba en una sola dirección (§0).

## 0. En una pantalla

**El fenómeno.** De noche, el píxel caliente de un cráter destaca contra su entorno por dos caminos: por
cuánto se aparta de la temperatura de fondo (el dNTI) y por cuánto se aparta de la variabilidad de ese
fondo. La conectiva decide si basta uno de los dos caminos (`min`, lo de hoy) o si hacen falta los dos
(`max`, lo que Coppola 2014 escribe como AND). Con `min`, un píxel al borde del barrido, sobre un fondo frío
y ruidoso, pasa por el camino más fácil. Por eso publicamos tanto en las noches en que MIROVA no vio nada.

**Lo que dicen los meses (VIIRS 375, brazo B sin Test 1 contra brazo F, que agrega `max`):**

| mes | negativos limpios: B, F | borde/nadir de F | recall por pasada (etiqueta que decide) | pérdidas de 0,5 MW o más con la etiqueta completa | P5 | C8b | letra de la sección 5 |
|---|---|---|---|---|---|---|---|
| mayo | 30,1 % a 2,3 % | 0,58 | tabla sola: 187 de 195 | 2 | cumple | cumple | MERECE SEGUIR (decide la tabla sola) |
| junio | 32,8 % a 1,5 % | 0,27 | tabla sola: 157 de 160 | 1 (del 25, ya con OCR confiable) | cumple | cumple | MERECE SEGUIR (decide la tabla sola) |
| julio | 46,5 % a 2,4 % | 0,09 | tabla y OCR: 150 de 153 | 0 | **falla** (0,40 contra nulo 0,35) | cumple | MERECE SEGUIR |
| agosto | 34,7 % a 3,7 % | 0,04 | tabla y OCR: 110 de 120 | 2 | cumple | cumple | **NO ADOPTAR** |
| abril | sin evaluar | | | | | | INDECIDIBLE (cobertura) |

**Cómo leer la última columna (hallazgo H4 del verificador).** Esa columna aplica la letra de la sección 5,
escrita antes de mayo. La enmienda del recall (2026-09-21, posterior a mayo) dice que en VIIRS el veredicto
de recall lo da Nicolás mirando la tabla por tramo, y que la enmienda "endurece, no afloja". Aplicada en las
dos direcciones, **el recall de los cuatro meses queda pendiente de Nicolás**, no sólo el de agosto: los
"MERECE SEGUIR" de mayo a julio valen para P1, P2 y C8b, no para el recall. Y lo que pesa en esa decisión
es doble: el tramo bajo 0,05 MW (F pierde entre 25 y 44 % de lo que B publica ahí) y las cinco pérdidas
fuertes del §3, que en mayo y junio la regla A119 deja fuera del veredicto sólo por la fecha de inicio de la
ventana.

**Agregado de mayo a agosto** (`agregado_mayo_agosto.txt`): en negativos limpios B publica 692 de 1.895
(36,5 %) y F 48 (2,5 %). De las alertas que B publica, F conserva 757 de 792 (95,6 %) con la etiqueta
completa y 542 de 560 (96,8 %) con la tabla sola.

**MODIS, Láscar, marzo a junio** (`modis_lascar_B_J_K.txt`), intervalos de Wilson al 95 %:

| brazo | publica cuando MIROVA alerta | publica en negativos limpios | ¿separa? |
|---|---|---|---|
| B (banda 21, sin Test 1) | 0 de 73 (0,0 %) | 0 de 96 (0,0 %) | no: no ve nada |
| J (banda 22) | 68 de 73 (93,2 %) [84,9 a 97,0] | 11 de 96 (11,5 %) [6,5 a 19,4] | **sí** |
| K (banda 22 y `max`) | 67 de 73 (91,8 %) [83,2 a 96,2] | 2 de 96 (2,1 %) [0,6 a 7,3] | **sí** |

Con banda 22, en Láscar, MODIS separa alertas de negativos; con banda 21 y sin el Test 1 no ve nada.
**Las salvedades pesan** (§5): sólo se corrió Láscar, que es el único volcán con alertas MODIS en esos meses,
así que la tasa de falsos de J y K en los otros diez volcanes **no está medida**; y contra la producción de
Láscar en esa misma población (8 de 73 alertas y 1 de 96 negativos publicados), J multiplica por once los
falsos de Láscar y K por dos. Lo que cambia es que pasa a ver casi todas las alertas.

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
  y la línea DETERMINISMO de cada resultado). En mayo el gemelo no tiene la noche del 2026-05-03 (corte de
  NASA, `SEARCH_CMR_TIMEOUT`), así que el script lo marca FALLA por cobertura; en las 282 pasadas comunes
  coincide 282 (verificador, H5). **No es determinista bit a bit** (H6): en junio y agosto hay diferencias de
  punto flotante y algunos records MODIS cambian uno o dos píxeles; la decisión de publicar no cambió, y el
  100 % está medido sólo en Láscar.

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

**La otra cara, que `max` también corta en el borde (H2 del verificador).** Al borde el píxel crece y una
fuente chica queda diluida, así que una alerta real llega con la misma debilidad que un falso. `max` pierde
el 10,9 % de las alertas del borde que B publica, contra el 1,2 % en el nadir (agregado de mayo a agosto,
`experiments/_s150_verificador/perdidas_por_satelite.py`). O sea que el recorte por zona no distingue del
todo lo falso de lo real: separa por cuán diluido llega el píxel.

**Recall por tramo de magnitud** (`recall_por_magnitud_jun_jul_ago.txt` y `..._sept_mayo.txt`). El costo
de `max` está abajo de 0,10 MW:

| tramo de MIROVA | mayo: B, F | junio: B, F | julio: B, F | agosto: B, F |
|---|---|---|---|---|
| bajo 0,05 MW | 87 %, 73 % | 94 %, 75 % | 100 %, 70 % | 89 %, 56 % |
| 0,05 a 0,10 | 96 %, 85 % | 89 %, 82 % | 97 %, 97 % | 91 %, 81 % |
| 0,10 a 0,20 | 100 %, 98 % | 100 %, 96 % | 100 %, 100 % | 100 %, 96 % |
| 0,20 a 0,50 | 98 %, 97 % | 99 %, 97 % | 100 %, 100 % | 100 %, 98 % |
| 0,50 o más | 96 %, 93 % | 98 %, 97 % | 91 %, 91 % | 94 %, 83 % |

Los tramos bajo 0,10 MW son entre 23 y 33 % de las alertas de cada mes. Esta tabla es la que la enmienda
del pre-registro pone en manos de Nicolás para el veredicto de recall en VIIRS.

**P5, julio, falla.** Entre las pasadas que MIROVA lista con VRP 0 en una noche en que sí alertó, F recorta
a 0,40 de lo que publica B, y un apagado parejo daría 0,35. O sea que en julio `max` no es más selectivo que
el azar en ese estrato. Es informativa: P5 no decide. Los otros tres meses cumplen (0,36, 0,28 y 0,21).

## 3. Las alertas de 0,5 MW o más que `max` pierde: un patrón de cinco casos

El primer borrador hablaba de "dos pérdidas de agosto". El verificador (H1) mostró que con la etiqueta
completa son **cinco de mayo a agosto, todas con la misma firma**: **Suomi NPP**, **sólo por el OCR** (la
tabla `latest.php` no las trae), **al borde del barrido** (cenit de 59 a 69 grados), B publicándolas con el
1 a 4 % de la magnitud de MIROVA, y el cúmulo de F saltando lejos del cráter. Reproducido con mis tablas
(`experiments/_s150_verificador/perdidas_por_satelite.py`):

| pasada | MIROVA | cenit | lo que publicaba B | cúmulo de F |
|---|---|---|---|---|
| Lastarria 2026-05-02 05:06 | 2,36 MW | 59,5° | 0,033 MW a 1,0 km | 19,5 km; no publica |
| Isluga 2026-05-29 04:54 | 0,86 MW | 69,0° | 0,013 MW a 4,9 km | 18,6 km; no publica |
| Láscar 2026-06-25 04:54 | 0,51 MW | 66,9° | 0,014 MW a 0,2 km | 21,3 km; no publica |
| Láscar 2026-08-17 05:00 | 0,60 MW a 3,24 km | 63,4° | 0,024 MW a 1,5 km | 24,6 km; no publica |
| Láscar 2026-08-22 05:06 | 1,65 MW a 1,22 km | 59,2° | 0,018 MW a 0,3 km | 8,2 km; no publica |

Mayo y junio no las cuentan en su veredicto porque ahí decide la tabla sola (A119), y la tabla casi no lista
Suomi NPP: entre las alertas de Suomi NPP que B publica, 18 y 13 vienen de la tabla contra 55 y 44 sólo del
OCR, en mayo y junio. La de junio es del 25, posterior al 2026-06-13, cuando el OCR ya mide distancia: queda
fuera del veredicto por la fecha de inicio de la ventana, no por la calidad de esa fila.

Lectura física. **Sospecha**, no medido: en estas pasadas B ya veía el cráter apenas, con el 1 a 4 % de
la energía que reporta MIROVA. El píxel caliente estaba en el límite del umbral y `max`, que le exige
pasar por los dos caminos, lo apagó. Las otras pasadas de esas noches que MIROVA da como alerta (NOAA-20
a las 05:18 del 17, con 0,19 MW; NOAA-20 a las 05:24 y NOAA-21 a las 06:12 del 22, con 0,23 y 0,11 MW;
cenit de 32 a 50 grados) los dos brazos las publican; la de NOAA-21 de las 06:06 del 17 MIROVA la lista
con VRP 0. No es un problema general de Suomi NPP: la mediana mensual de la magnitud de B sobre la de
MIROVA en Suomi NPP va de 0,56 a 1,00 entre mayo y agosto, dentro del rango de los otros dos satélites
(`magnitud_por_satelite.txt`). Lo raro es que MIROVA dé 0,60 y 1,65 MW en Suomi NPP al borde del barrido,
de tres a quince veces lo que da en las pasadas de menor ángulo de esas mismas noches. Un dato que apunta en
esa dirección, sin probar nada (verificador): en las dos filas OCR de agosto la distancia coincide con la de
la pasada vecina (3,24 contra 3,23 km el 17; 1,22 contra 1,22 km el 22), y una hora después, en la misma
geometría de Suomi NPP al borde, la tabla lista la pasada como RUTINA con VRP 0 (06:42 del 17 y 06:48 del
22). Que sea un artefacto del OCR o de MIROVA queda **SIN VERIFICAR**: pide mirar las cinco imágenes de
MIROVA en el repo Mirova-v1 (`imagenes_satelitales/<volcán>/<fecha>/<hora>_..._VIIRS375_VRP.png`) y los
gránulos. Y decide si el NO ADOPTAR de agosto descansa en una alerta real o en una fila mal leída.

**Qué dice la regla.** Por la letra de P4 (sección 5 del pre-registro), "ninguna pérdida de 0,5 MW o más"
falla en agosto, y con la etiqueta completa fallaría también en mayo y junio. Por la enmienda del recall, el
corte de 0,5 MW queda sólo para MODIS y el veredicto de recall de VIIRS, en los cuatro meses, lo da Nicolás
mirando la tabla por tramo y estos cinco casos (ver §0).

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

**Lo que no se puede decir todavía**: que la banda 22 arregla MODIS en la réplica. Salvedades (las tres
últimas, del verificador, H3):
- Estos 96 negativos limpios son todos de Láscar. La brecha de MODIS en producción viene sobre todo de los
  otros volcanes. Hace falta un despacho de J y K sobre los 11 volcanes, con la misma ventana, para medir la
  tasa de falsos donde importa. No se pudo despachar hoy (§6).
- Contra la producción de Láscar en esta misma población (8 de 73 alertas y 1 de 96 negativos publicados),
  J multiplica por once los falsos y K por dos. La comparación con el 11,5 % de AUDIT_S149 mezclaba
  poblaciones. Y esos records de producción los escribió el código de esa época, no el de hoy.
- 55 de las 73 positivas son fuertes (0,5 MW o más): es un sustrato fácil.
- La magnitud pareada que la sección 7 pide informar no estaba: mediana de J sobre MIROVA **0,50**.
- Los conteos usan el respaldo de la referencia del 2026-04-08 que `armar_tabla` carga sin figurar en el
  manifiesto del congelado; con los CSV congelados solos dan 66 de 71 y 12 de 96 para J, 65 de 71 y 3 de 96
  para K. No cambia la conclusión.

**Informativo, D21**: con banda 21 y sin el Test 1, B no publica ni una de las 73 alertas MODIS de Láscar.
Hoy, lo que MODIS publica en producción en Láscar lo publica el Test 1 integrado, no los Tests 2 y 3.

## 6. Lo que quedó sin hacer, y por qué

- **Abril**: repetir el job de Chaitén del brazo B (run 35639417826) con el mismo código. **Bloqueado**: el
  token de Earthdata venció el 2026-10-03. El NRT falla desde las 07:36 UTC de ese día
  (`EARTHDATA_CREDENTIAL_INVALID`, "Token ... has expired"). Rotarlo es de Nicolás.
- **MODIS J y K en los 11 volcanes**: mismo bloqueo.
- **Las cinco imágenes de MIROVA del §3**: pendiente. Es lo primero que conviene mirar, porque decide si la
  pérdida fuerte de `max` es real.
- **Que el job de GitHub haya aplicado los flags declarados**: los logs guardados en el repo no los imprimen
  (SIN VERIFICAR, verificador).
- Hallazgo menor del verificador sin corregir (H7): la versión "tabla sola" no reetiqueta de verdad, porque
  el OCR sigue sacando pasadas de los negativos limpios y del estrato de P5. Reetiquetado de verdad, ningún
  veredicto cambia.
