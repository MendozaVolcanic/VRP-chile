# Estudio D (tarea 1.12 del loop): las alertas de 0,05 MW o menos, ¿MIROVA las considera anomalía?

> Escrito el 2026-10-14 por el loop autónomo, en `loop/1.12-alertas-minimas`. Todo número sale de un script de
> esta carpeta con su salida guardada al lado: `censo_salida.txt`, `frontera_salida.txt`, `suma_salida.txt`,
> `extraer_salida.txt`, `cotejar_salida.txt`. Ningún número está transcrito a mano desde otro documento.
> **Estado: revisado por un verificador con contexto limpio** (números CONFIRMADOS; presentación PARCIAL). Sus
> cinco puntos se corrigieron en esta versión: pasadas distintas en vez de muestras sumadas (§2), redondeo o
> truncado no identificable (§2), refuerzo del control (§2), SN como lectura tan literal como SE y poco poder del
> "ningún veredicto cambia" (§3 y §4), y cotejo del CSV contra su fuente (§3).
>
> ⚠️ **Decidido el 2026-10-15 (D-9, issue #811): SN**, con 0,05 exacto contado como "MIROVA no vio nada" y la
> variante con 0,05 como alerta informada al lado. Ya está cableado: `scripts/clase_mirova.py::aplicar_regla_minimas`
> (modos SN, SE y original), en el etiquetador por `banco_paridad.indexar_referencia(regla_minimas=...)`. Los
> veredictos publicados, re-contados con las cinco variantes: `veredictos_tres_reglas.md`. Lo que §4 y §5 dicen
> como "no cableado" y "decisiones para Nicolás" se conserva como historia.

## 0. En una pantalla

**El fenómeno.** Un píxel VIIRS de 375 m que mira una fumarola, un domo tibio o un borde de lago de lava
recibe una fracción mínima de su superficie caliente. La señal que eso deja, convertida a potencia radiativa,
cae en centésimas de MW: 0,02, 0,03, 0,04 MW. A ese nivel la diferencia entre "hay algo" y "ruido del fondo"
es tan fina que MIROVA mismo la trata aparte: publica el número en su tabla y lo dibuja en su gráfico, pero con
**estrella gris** y con el banner de la imagen en **"Thermal anomaly: NONE"**. El scraper de Mirova-v1, en
cambio, llama ALERTA a todo VRP mayor que cero dentro de su radio. La réplica se mide contra esa etiqueta.

**Lo que se midió.**

1. **Cuántas son.** 155 de las 2.281 pasadas con alerta de la referencia unificada (6,8 %) tienen VRP de
   0,05 MW o menos; nocturnas, 155 de 2.156 (7,2 %). **Todas son VIIRS 375** (9,1 % de sus alertas
   nocturnas): la alerta más baja de VIIRS 750 es de 0,09 MW y la de MODIS de 0,13. Se concentran en
   Lastarria (55, el 22 % de sus alertas nocturnas), Tupungatito (26) y Planchón Peteroa (18).
2. **Dónde está la frontera.** En VIIRS 375, contando cada pasada una vez y con dos instrumentos (el OCR de
   Mirova-v1 y una lectura propia de las imágenes de mayo), hay **14 pasadas distintas NONE con 0,04 MW o
   menos y ninguna VERY LOW**, y **20 VERY LOW con 0,06 exacto y ninguna NONE** (283 VERY LOW con 0,06 o
   más). Con 14 casos y cero excepciones, la probabilidad de que una pasada de 0,04 o menos sea VERY LOW
   todavía puede llegar al 19,3 % (cota superior al 95 %). En 0,05 exacto salen los dos lados, 5 NONE y 5
   VERY LOW. Calza con un corte en el VRP verdadero entre 0,045 y 0,06 MW, con el valor publicado redondeado
   o truncado a dos decimales: **cuál de los dos no es identificable** con estos datos. La distancia al
   cráter y el ángulo de vista no explican el borde. **En VIIRS 750 la frontera no está resuelta** (una
   imagen NONE con 0,15 MW, una VERY LOW con 0,18).
3. **Cuánto cambia la suma de errores.** **Ningún veredicto cambia** en los tres resultados ya medidos (meses
   de S150, VIIRS 750, Chillán), pero esa frase **tiene poco poder**: B y F difieren de 6 a 8 veces, así que
   ningún tratamiento de 155 pasadas podía darlas vuelta, y F, K, KE y KET empatan en los tres escenarios.
   Lo que sí cambia es el **techo del A/B de D22**: de 14 pérdidas recuperables quedan 5 (entre 5 y 8 si
   las de 0,05 se dan por dudosas).
4. **Dos lecturas literales (§4), las dos para Nicolás.** "MIROVA no vio nada" (SN: la pasada mínima cuenta
   como negativo) y "estrato aparte" (SE: no cuenta para ningún lado). SN calza con la letra de MISSION
   (negativo limpio es "MIROVA miró y no vio nada", y eso dice un banner NONE); SE crea una tercera categoría
   que MISSION no tiene. Aparte va el tratamiento de 0,05 exacto (65 pasadas; en la muestra con banner, 5 de 10 NONE). Nada está
   cableado.

## 1. Cuántas son (`censo.py`, `censo_salida.txt`)

Pasada = (volcán, sensor, minuto), igual que `scripts/clase_mirova.py`. Su VRP es el de la fila de alerta del
consolidado si existe, si no el del OCR: el mismo orden que usa el evaluador del A/B
(`experiments/_s146_ab_sin_test1/evaluar.py::anotar_vrp_mirova`), para que el umbral corte las mismas pasadas
que el evaluador ve.

| | mínimas (VRP <= 0,05) | de todas las alertas |
|---|---|---|
| todas las pasadas | 155 de 2.281 | 6,8 % |
| nocturnas (las que miran los evaluadores) | 155 de 2.156 | 7,2 % |
| de ellas, con VRP 0,05 exacto | 65 | |
| de ellas, con VRP 0,04 o menos | 90 | |
| de ellas, sólo del OCR | 31 | |

Por tramo de calidad de la referencia (A119), nocturnas: hasta febrero 17 de 243 (7,0 %); marzo a 12 de junio
57 de 1.049 (5,4 %); 13 de junio a 5 de agosto 34 de 368 (9,2 %); desde el 6 de agosto 47 de 496 (9,5 %). La
fracción sube en el invierno y la primavera (12,0 % en septiembre); el detalle por mes y volcán está en la
salida.

## 2. Dónde está la frontera NONE / VERY LOW (`frontera_banner.py`, `frontera_salida.txt`)

### Tres muestras, dos instrumentos

A y B salen del **mismo** OCR y comparten 96 pasadas de VIIRS 375; no son observaciones independientes. Por
eso las cifras que deciden (más abajo, "pasadas distintas") cuentan cada pasada una vez.

- **A. Banner leído por el OCR de Mirova-v1** (`Nivel_Anomalia_MIROVA`, versión 30, agosto a octubre): 137
  pasadas. Bajo 1 MW sólo hay VIIRS 375.
- **B. Color de la estrella del gráfico de distancias**, que el OCR anota en la nota de validación desde la
  versión 29 (`ocr_utils.py` V29 la documenta como "detección débil sub-umbral del banner"). Donde una fila
  tiene las dos lecturas, estrella y banner coinciden en las 107 (7 gris con NONE, 100 verde con VERY LOW o LOW).
- **C. Banner leído por nosotros** en las 2.702 imágenes VRP de mayo del archivo local `mirova-tif-archive`
  (lectura local, sin pull; esa copia llega al 2026-05-20). `leer_png_mirova.py` lee la hora de adquisición
  (texto rojo "Last Update", UTC) y el banner sin OCR externo: MIROVA dibuja siempre con la misma fuente, así
  que cada glifo se identifica por el hash de su máscara (27 glifos, etiquetados mirando la hoja de contacto
  que el propio script regenera) y el banner se clasifica dos veces, por máscara y por color de fondo. Las
  imágenes se parean a la pasada de la referencia por volcán, sensor y hora (más o menos 120 s). Es la única
  muestra de otro mes y la única con MODIS y VIIRS 750 bajo 1 MW. Controles del instrumento: la hora leída
  nunca es posterior a la fecha de modificación del archivo (0 de 2.702; desfase mediano 4,5 h); las dos
  lecturas del banner coinciden en 2.702 de 2.702 (la primera versión del clasificador por color medía el
  ancho del texto con el borde del recuadro y discrepó en 60; se corrigió); ninguna pasada con dos copias
  trae dos banners distintos.

### VIIRS 375: la hipótesis y el control que puede fallar

**H**: el banner dice NONE si el VRP verdadero está bajo un umbral, y el VRP publicado es el verdadero con dos
decimales. Si se publica redondeado, el umbral está entre 0,045 y 0,055 MW; si se publica truncado (MIROVA
trunca el VRP que dibuja en la imagen), entre 0,05 y 0,06. Las dos versiones predicen lo mismo sobre el valor
publicado: cero NONE con 0,06 o más, cero VERY LOW con 0,04 o menos, y los dos lados en 0,05. **No se pueden
distinguir con estos datos**; lo único que se puede decir es que el umbral está entre 0,045 y 0,06 MW.

| muestra | NONE con <= 0,04 | VERY LOW con <= 0,04 | 0,05: NONE / VERY LOW | NONE con >= 0,06 | violaciones de H fuera de 0,05 |
|---|---|---|---|---|---|
| A (OCR, banner) | 7 | 0 | 2 / 3 | 0 | **0** |
| B (estrella), sólo pasadas también en el consolidado con el mismo VRP | 9 | 0 | 2 / 4 | 0 | **0** |
| C (mayo, lectura propia) | 3 | 0 | 3 / 0 | 0 | **0** |
| B, filas sin par en el consolidado | 0 | 5 | 1 / 1 | 8 | **13** |

El control falla donde tiene que fallar. Las filas de la estrella **sin par en el consolidado** son las que
pueden llevar la imagen de otra pasada (defecto de Suomi NPP, A119, arreglado en Mirova-v1#20): el VRP es de
la suya y la estrella sale del gráfico de otra. Ahí H se viola 13 veces. En las muestras limpias, cero. Y las
reglas desplazadas fallan en cada muestra limpia: "NONE si VRP <= 0,03" da 6, 7 y 4 violaciones; "NONE si
VRP <= 0,06" da 11, 17 y 6. La muestra tiene poder para distinguir la frontera (A110).

**Refuerzo del control.** Si las 13 violaciones vienen de que la estrella es de otra pasada, en el consolidado
tiene que aparecer, cerca, una pasada del mismo volcán y sensor cuyo VRP cuadre con el color (gris con más de 0
y hasta 0,05; verde con 0,05 o más). Pasa en **11 de 13**, y en las 11 es justamente **la pasada siguiente**
con VRP mayor que 0 (por ejemplo, Láscar 2026-08-30 05:54 con 0,17 MW y estrella gris: la siguiente, 06:18,
tiene 0,04). Nulo: la pasada siguiente cuadra con el color contrario en 1 de 13. Las dos que no cuadran son
pasadas de la tarde (Nevados de Chillán 2026-08-25 17:36 en VIIRS 375 y Planchón Peteroa 2026-08-14 17:42 en
VIIRS 750, que es la única violación fuera de VIIRS 375).

**Pasadas distintas de VIIRS 375** (A, B con par en el consolidado y C juntas, cada pasada una vez; 307
pasadas, ninguna con etiquetas distintas entre muestras):

| VRP publicado | NONE | VERY LOW o más |
|---|---|---|
| 0,04 o menos | 14 | 0 |
| 0,05 | 5 | 5 |
| 0,06 | 0 | 20 |
| más de 0,06 | 0 | 263 |

Cota superior al 95 % (cero casos en n, exacta) de que una pasada de 0,04 o menos sea VERY LOW: **19,3 %**
(n = 14); de que una de 0,06 exacto sea NONE: 13,9 % (n = 20). De las 44 pasadas de 0,06 MW o menos, 32 vienen
del OCR y 12 de la lectura propia.

El borde de 0,05 no lo separa otra variable: en A los dos NONE de 0,05 son de Tupungatito a 5,3 y 5,4 km, pero
en C los tres NONE de 0,05 están a 1,55 km (Lastarria), 4,8 km (Tupungatito) y 0,0 km (Chaitén), y Tupungatito
tiene VERY LOW de 0,06 a 0,10 MW a 5,27 y 5,41 km. El ángulo cenital tampoco (NONE de 0,04 con 3° y con 63°).

**Conclusión para VIIRS 375**: con 0,04 MW o menos MIROVA no ve anomalía en ninguna de las 14 pasadas
observadas; con 0,06 o más sí, en todas; en 0,05 es una moneda (5 NONE y 5 VERY LOW). Ese 0,05 mixto lo
explica el paso de dos decimales del valor publicado, sea redondeo o truncado, sin necesidad de una regla
distinta; cuál de los dos, no se sabe.

### VIIRS 750 y MODIS

- **El corte de 1 MW entre VERY LOW y LOW vale también en MODIS y VIIRS 750** en mayo: 0 pasadas del lado
  equivocado (7 de MODIS, 19 de VIIRS 750, además de las 120 de VIIRS 375). Hasta hoy el corte de las
  alertas protegidas estaba observado sólo en VIIRS 375 (`docs/S151_CRITERIO_CLASE_MIROVA.md` §5).
- **La frontera NONE de VIIRS 750 no está resuelta.** Isluga 2026-05-15 05:24, 0,15 MW, banner NONE con
  estrella gris; Planchón Peteroa 2026-05-09 05:42, 0,18 MW, VERY LOW con estrella verde (las dos imágenes
  revisadas a ojo además de la lectura automática). Si la frontera de 750 estuviera cerca de 0,15 a 0,18 MW
  (el píxel de 750 m tiene cuatro veces el área del de 375 m), las alertas de VIIRS 750 de 0,15 MW o menos
  serían NONE: son 6 en toda la referencia, y otras 7 de 0,16 a 0,17. Con una imagen por lado no se puede
  afirmar nada; va como sensibilidad en §3.
- **MODIS**: la alerta más baja es de 0,13 MW, y entre las imágenes de mayo con VRP mayor que cero la de
  menor VRP tiene 0,34 MW (VERY LOW). No hay datos bajo eso; la regla no lo toca.

## 3. Cuánto cambia la suma de errores (`suma_errores.py`, `suma_salida.txt`)

Suma de errores del criterio bajo 1 MW: alertas Muy Bajo sin publicar más publicaciones en negativos limpios,
pasada por pasada, con las etiquetas del evaluador. Tres escenarios sobre las **mismas** publicaciones de cada
brazo (no se re-corre nada):

- **S0**: la etiqueta original (control: reproduce los totales publicados);
- **SE, estrato aparte**: la pasada mínima sale de la suma; la noche no cambia;
- **SN, MIROVA no vio nada**: las filas de alerta de la pasada mínima pasan a RUTINA con VRP 0 y se
  re-etiqueta con `banco_paridad.etiquetar`, así que la pasada y las otras de esa noche pueden volverse
  negativos limpios.

Controles: el re-etiquetado sobre la referencia congelada (sha256 contra cada manifiesto) reproduce la etiqueta
de la tabla en el 100 % de las pasadas de cada mes y de Chillán; S0 reproduce los números publicados (meses
VIIRS 375: B publica 829 de 2.324 negativos limpios y F 63, como `docs/S150_RESULTADO_MESES.md`; VIIRS 750: 400
y 90, como la tarea 1.10; Chillán: C0 52, B 17, J 23, F, K, KE y KET 7, como el verificador de Chillán); y lo
que SE excluye coincide en cada brazo con las alertas que la etiqueta original marca con VRP de 0,05 o menos.
Ese último control encontró un defecto propio: la primera versión guardaba un índice por `id()` y en julio y
agosto excluía con el índice de otro mes.

Cotejo del CSV contra su fuente (`cotejar_tablas.py`, `cotejar_salida.txt`): `pasadas_meses_B_F.csv` coincide
campo por campo (clave, etiqueta, VRP de MIROVA, publicación de B y de F, ventana) con las tablas por pasada de
S150 en **VIIRS 375 y VIIRS 750: 13.677 pasadas, 0 diferencias**. La fuente es una sola: las tres copias de cada
mes que hay en los scratchpads de S150 tienen el mismo sha256. Que esas tablas sean las del resultado publicado
lo respalda que S0 reproduce sus totales exactos.

| resultado | brazos | S0 | SE | SN | ¿cambia el veredicto? |
|---|---|---|---|---|---|
| meses abril a agosto, VIIRS 375 | B / F | 860 / 134 | 852 / 109 | 904 / 138 | no: F gana en los tres |
| meses abril a agosto, VIIRS 750, sensibilidad 0,15 MW | B / F | 400 / 90 | 397 / 87 | 398 / 88 | no |
| Chillán, tres sensores | C0 / B / J / F=K=KE=KET | 52 / 17 / 23 / 7 | 52 / 15 / 21 / 5 | 55 / 17 / 23 / 6 | no |
| techo del A/B de D22 (pérdidas recuperables) | | 14 | 5 | 5 | **el techo cae** (5 a 8 con 0,05 dudoso) |

Por qué se mueve así, en términos físicos. B (sin la conectiva `max`) publica casi todo lo débil, incluidas
las mínimas; F las pierde más seguido (abril a agosto: B pierde 31 alertas Muy Bajo, F 71; de esas, 8 y 25
son mínimas). Tratarlas como estrato aparte le quita a F más errores que a B. Tratarlas como "MIROVA no vio
nada" convierte las que B publicó en falsas alarmas (B sube de 860 a 904). En los dos casos F se aleja de B.
En Chillán el efecto es de 1 a 3 errores por brazo.

**Cuánto vale "ningún veredicto cambia".** Poco. B y F difieren de 6 a 8 veces (860 contra 134, 852 contra
109, 904 contra 138): ningún tratamiento de las mínimas podía darlos vuelta, así que el resultado no pone a
prueba la regla. En Chillán F, K, KE y KET empatan en los tres escenarios (7, 5 y 6), y C0, B y J quedan lejos.
Una comparación entre brazos parecidos, como la del A/B de F y K que corre ahora, es donde la regla puede
decidir algo.

**El A/B de F y K que corre ahora (D-7)** compara contra C0, que es producción con el Test 1 encendido y
publica casi todo lo débil. Con SE o SN su P2 se vuelve algo más favorable a los candidatos que callan las
mínimas; no se puede cuantificar hasta que el run termine. El pre-registro ya dejó el borde de 0,05 MW como
límite declarado (§8).

**Lo que sí cambia de lectura.** En `docs/S150_RESULTADO_MESES.md` el costo de `max` en recall "está abajo de
0,10 MW" y el tramo "bajo 0,05 MW" (F pierde 25 a 44 % de lo que B publica ahí) quedó para la decisión de
Nicolás. Ese tramo es exactamente el que MIROVA llama NONE: lo que pesa en la decisión de recall es el tramo de
0,05 (dudoso) a 0,10 MW, que MIROVA sí llama VERY LOW.

## 4. Qué hacer con las mínimas en el evaluador (no cableado)

Lo que los datos de MIROVA fijan (A115): en VIIRS 375, una alerta del scraper con VRP de **0,04 MW o menos**
(VRP de la pasada, consolidado antes que OCR) es una pasada que MIROVA llama **NONE**. Ninguna de las 14
observadas salió VERY LOW. MODIS y VIIRS 750 no tienen alertas en ese rango. Lo que **no** fijan es cómo
contarlas, y hay dos lecturas, las dos literales:

- **SN, "MIROVA no vio nada": la pasada cuenta como negativo.** La regla 3 del criterio de victoria
  (`docs/MISSION.md`) define negativo limpio como "pasadas donde MIROVA miró y no vio nada", y un banner
  NONE es MIROVA diciendo, en su propia imagen, que no ve anomalía. La regla 2 define "Muy Bajo" como alertas
  "VERY LOW en el banner de MIROVA", así que una pasada NONE tampoco es Muy Bajo. En esta lectura, un brazo
  que la publica comete una falsa alarma. Costo: re-etiqueta noches enteras (otras pasadas de esa noche pueden
  volverse negativo limpio) y trata como silencio una señal que MIROVA sí registró en su tabla y dibujó con
  estrella gris.
- **SE, estrato aparte: la pasada no cuenta para ningún lado** (ni alerta perdida, ni acierto, ni negativo
  limpio) y se informa sola, con cuántas publica cada brazo. Es el escenario que no afirma de qué lado cae el
  error. Pero **crea una tercera categoría que MISSION no tiene**: hoy toda pasada es alerta, negativo limpio
  u "otra" sin etiqueta (`sin_info`, `far_ref`), y agregar una cuarta es cambiar el criterio, no aplicarlo.

Las dos dejan los veredictos ya medidos donde estaban (§3, con el poder escaso que allí se dice). Las cifras del
§3 usan el corte con 0,05 incluido, el más amplio; con el corte en 0,04 el efecto es menor. La elección entre
SN y SE es de Nicolás.

**Sub-decisión aparte: 0,05 exacto.** Son 65 pasadas de las 155, y en la muestra con banner MIROVA las llama
VERY LOW en 5 de 10. Meterlas en el tratamiento de las mínimas trata como NONE a una mitad que MIROVA llama
VERY LOW; dejarlas como alerta hace lo contrario con la otra mitad. Cualquier lado afirma algo que el dato no
sabe (el tercer decimal no se publica). Las opciones son: igual que las de 0,04 o menos, como alerta (lo de
hoy), o en un estrato aparte aunque las de 0,04 vayan como negativo.

**Por qué no se cableó.** Mueve la vara de todas las pruebas y cambia la lectura de un resultado ya publicado:
el techo del A/B de D22 baja de 14 a 5 (5 a 8 según lo que se decida para 0,05).

## 5. Decisiones para Nicolás

1. **Las de 0,04 MW o menos en VIIRS 375: ¿SN (negativo, la letra de la regla 3 de MISSION) o SE (estrato
   aparte, categoría nueva)?** El loop se inclinaba por SE porque no afirma el lado del error; la letra de
   MISSION favorece SN. Las dos son defendibles.
2. **Las de 0,05 exacto: ¿igual que las de 0,04, como alerta, o aparte?**

Lo que se decida va a la definición del criterio en `docs/MISSION.md` y a `scripts/clase_mirova.py`, con su
test, y obliga a re-leer el techo de D22.

## 6. Lo que no se pudo resolver

- **La frontera de VIIRS 750**: una imagen por lado (0,15 NONE, 0,18 VERY LOW). Las imágenes de agosto en
  adelante, donde el banner se puede leer, viven en el archivo remoto (`mirova-tif-archive`), que esta tarea no
  puede bajar; el `leer_png_mirova.py` sirve tal cual sobre ellas.
- **El tercer decimal de 0,05**: ni la tabla `latest.php` ni la imagen lo traen (las imágenes de mayo incluso
  muestran el VRP como entero). Sin él, 0,05 queda dudoso por construcción.
- **Si el corte depende de otra cosa además del VRP** (por ejemplo el número de píxeles alertados): en las
  muestras el VRP basta para explicar todo salvo 0,05, pero 0,05 es justo donde una segunda variable podría
  esconderse.
- **El A/B de F y K en curso**: el efecto de la regla en su P2 se mide cuando termine.
- **El TIF** no se usó: A24 dice que no es VRP sumable, y la copia local termina en mayo, donde ya alcanzó con
  el banner de la imagen VRP.

## Archivos

- `comun.py`: pasadas de alerta de la referencia unificada y tramos A119.
- `censo.py`, `censo_salida.txt`: §1.
- `leer_png_mirova.py`: lector del banner y la hora de las imágenes VRP; `python leer_png_mirova.py <dir>`
  regenera las hojas de contacto para re-verificar las etiquetas a ojo.
- `frontera_banner.py`, `frontera_salida.txt`: §2.
- `extraer_tablas.py`, `extraer_salida.txt`, `pasadas_meses_B_F.csv`, `pasadas_ndc.csv`: copia en el repo de
  las tablas por pasada de los meses de S150 y de Chillán, que vivían sólo en scratchpads (la parte de VIIRS
  750 es idéntica a `experiments/_s151_max_v750/pasadas_viirs750_B_F.csv`, comprobado).
- `cotejar_tablas.py`, `cotejar_salida.txt`: cotejo del CSV de los meses contra las tablas fuente (§3).
- `suma_errores.py`, `suma_salida.txt`: §3. Necesita la referencia congelada de los meses
  (`experiments/_s149_prereg_invierno/_congelado/<mes>/`, en `.gitignore`; se verifica contra el manifiesto).
