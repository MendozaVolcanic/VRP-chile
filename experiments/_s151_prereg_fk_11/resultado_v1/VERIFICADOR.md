# Verificador con contexto limpio: A/B F/K, ventana V1 (2026-08-29 a 2026-10-08)

Verificador independiente del resultado de `experiments/_s151_prereg_fk_11/resultado_v1/v1.log` y `v1.json`
(regla R3: una mejora de más de 30 % exige auditoría independiente). No se tocó el repo. Todo lo de este informe
sale de scripts y salidas guardados en `C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v1\`.

## Veredicto: PARCIAL

Lo que decide se sostiene: con la lectura A, F y K CUMPLEN en V1, y la caída de la suma de errores bajo 1 MW es
real, reproducible, no depende de cómo se unieron los intentos, y el instrumento sí sabe dar VETADO, PIERDE y
FALLA sobre estos mismos datos. Dos partes del resultado, en cambio, no dicen lo que parecen decir:

1. **P3 (magnitud) está anulado por construcción en VIIRS 375.** Su CUMPLE es letra del pre-registro, no
   medición: sin el Test 1, la magnitud sí empeora contra MIROVA, y la métrica no lo puede ver.
2. **El veto de la lectura B no mide pérdidas del objeto que MIROVA vio.** En las 12 «pérdidas», C0 publicaba
   una señal minúscula en el cráter (0,012 a 0,10 MW, sólo por el Test 1) mientras el objeto de MIROVA está a
   11 a 28 km; F ve un objeto lejano a una distancia parecida y lo calla como `far`. Además, la frase del
   encargo «10 objetos lejanos **sin VRP** en MIROVA» es falsa: tienen 1,07 a 3,98 MW (FALSO_POSITIVO).

## 1. Reproducción

`python experiments/_s151_prereg_fk_11/evaluar_fk.py --ventana V1 --raiz ...\union_d16 --logs ...\i3\logs
--out rep_d16\v1.json --tmp rep_d16\tmp` (14 s). Resultado: **0 diferencias** en todas las claves del JSON contra
`resultado_v1\v1.json`; el log es idéntico salvo el orden en que se intercalan las líneas de stderr
(`rep_d16\v1.log`).

## 2. ¿El evaluador mide lo que dice?

**Definiciones leídas en el código.**
- *Protegida* (`scripts/clase_mirova.py:65`): A = fila del scraper de tipo alerta con VRP de 1 MW o más; B =
  cualquier fila no RUTINA con 1 MW o más (incluye FALSO_POSITIVO). Se arma sobre las filas pareadas a la
  pasada (`banco_paridad.parear`), la misma referencia congelada que la tabla (sha256 verificado).
- *Negativo limpio* (`scripts/banco_paridad.py:317`): la tabla de MIROVA lista ESTA pasada como RUTINA con VRP 0
  y en la noche de ese sensor no hay ni alerta ni FALSO_POSITIVO. Es conservador.
- *Pérdida* (P1, `evaluar_fk.py` §5): protegida que C0 publica y el candidato no, por pasada.
- *Exclusión Suomi NPP* (`ocr_snpp`): pasadas cuya alerta descansa sólo en filas del OCR y cuyo record es de
  Suomi NPP. Salen del P1 y del P2 con la lectura A (se listan); con la B deciden. V1 entera es anterior al
  hito del 2026-10-09, así que aplica en toda la ventana. Correcto según el pre-registro (l. 91 a 94).
- *Regla SN de D-9*: sección 10, informa y no decide; el autocontrol (la regla original reproduce la sección 6)
  da OK y la etiqueta recalculada coincide en 4.820 de 4.820 pasadas. Con SN, SE y las variantes de 0,04 el
  veredicto de la ventana no cambia.

**Las 21 alertas de VIIRS 375 que F y K dejan de publicar** (`perdidas_F.txt`; K es idéntico en VIIRS):
- 11 de 0,05 MW o menos (las que MIROVA llama NONE en su banner, D-9);
- 8 entre 0,06 y 0,21 MW (Muy Bajo);
- 2 de 1 MW o más, ambas protegidas A y ambas sólo del OCR de Suomi NPP: Tupungatito 2026-09-28 05:18
  (2,51 MW) y 2026-09-29 04:54 (1,86 MW).
- En VIIRS 750 se dejan de publicar 4, todas Muy Bajo (0,16 a 0,38 MW). En MODIS, ninguna; K recupera la
  protegida de Chillán del 2026-10-01 08:35 (5,18 MW).

**Conciliación «protegidas A 19 de 21» (§9) contra «pérdidas netas 0» (§5).** La §9 cuenta las 21 protegidas
A, incluidas las 9 que descansan sólo en el OCR de Suomi NPP; la §5 las aparta. Las 2 que faltan en la §9 son
exactamente las 2 de Tupungatito que la §5 lista como «solo OCR Suomi NPP (no decide)». No hay contradicción.
Lo que falta es la revisión de la cabecera de la imagen que el pre-registro manda antes de proponer nada. Dos
evidencias independientes apuntan a que no son pérdidas reales con la lectura A:
- el estudio `experiments/_s151_distancia_ocr/verificador/cambios_salida.txt` (filas 49 y 52) marca las dos
  como «lejos», con distancias candidatas de 9,73 y 22,7 km en la imagen (no lo verifiqué yo);
- F, sin saber nada de MIROVA, pone su cúmulo en esas dos pasadas a **9,40 km (1,11 MW)** y a **21,57 km
  (0,15 MW)**, mientras C0 publicaba 0,059 y 0,050 MW de un solo píxel en el cráter por el Test 1
  (`b_objetos.txt`). Es una coincidencia de radios, no de posición (A93, A107): sugiere, no prueba.

**Poder del veto con la lectura A.** En VIIRS 375 deciden 12 protegidas (21 menos 9 de Suomi NPP), y 10 son de
Chillán en erupción; las otras son 1 de Láscar y 1 de Planchón Peteroa. En VIIRS 750 deciden 10 de 12, todas
de Chillán salvo 1 de Puyehue. En MODIS, 4 (3 de Chillán y 1 de Villarrica). El CUMPLE de V1 dice «no se pierde
nada de Chillán en erupción», no «no se pierde nada»; el pre-registro ya lo declara y por eso existe V2.

**Lo que queda fuera de la suma (A118 c)** (`estratos.txt`). En VIIRS, F publica un subconjunto estricto de lo
que publica C0 (0 pasadas donde F publique y C0 no, en todas las etiquetas). Fuera de la suma, C0 publica 413
pasadas `sin_info` de VIIRS 375 sin fila de MIROVA, 265 `sin_info` donde MIROVA lista la pasada con VRP 0 en una
noche con alerta, y 64 `far_ref`; F publica 54, 37 y 22. Ninguno de esos estratos contiene alertas, así que no
esconde pérdidas; sí esconde más publicaciones de C0 que F apaga.

## 3. Que la unión no contamine

Construí la unión de los intentos 1 y 3 con la versión de `unir_intentos.py` del PR #843 (rama
`loop/unir-intentos-hotspot-escena`, commit 5a1ddae93) en los dos órdenes (`union_13`, `union_31`; 44 archivos
cada una, ningún «NO SE UNE»; los 2 records `hotspot_escena` son de Llaima control, MODIS_TERRA 2026-09-24
02:05 y 2026-10-06 01:45). Evaluadas: **0 claves distintas** del JSON contra la evaluación de `union_d16` en
los dos órdenes. La unión vieja `...\union\` (sin D-16) le deja a C0 dos pasadas de menos (Llaima VIIRS 750
2026-09-16 05:06 y 06:48) y el evaluador da **INDECIDIBLE** por cobertura, que es lo correcto.

Nota aparte: en Llaima MODIS_TERRA 2026-10-06 01:45 el mismo código de control da `vrp_mw` 4,281 en un intento y
3,568 en el otro (cambia `final_hotspot_source`, test1 contra cluster_rescue). La decisión de publicar es la
misma (lo comprueba el predicado del tablero), pero la magnitud MODIS no es determinista en ese caso.

## 4. P3: la métrica pareada se anula por construcción

`p3_salida.txt`. En VIIRS 375, de 239 pares, **124 (51,9 %) tienen d exactamente 0** porque F publica el mismo
cúmulo que C0. La mediana de una distribución con más de la mitad de su masa en cero es cero, y el bootstrap
de la mediana da [0, 0]: el criterio «FALLA si el intervalo queda sobre 0» no puede dispararse mientras más de
la mitad de los pares no cambie, cualquiera sea el tamaño del efecto en el resto.

En los 115 pares que sí cambian, F queda más bajo que C0 en 98 (mediana de log10(F/C0) = -0,142, unos 28 %
menos), d es positivo en 77 y negativo en 38 (prueba de signos, p = 0,00035), y la media de d es +0,048 con
intervalo bootstrap [+0,026, +0,074]. O sea: **sin el Test 1 la magnitud de VIIRS 375 se aleja de la de
MIROVA, de forma significativa**, y es lo que el pre-registro declaró como riesgo (S147: baja 0,10 a 0,18 en
Láscar, Isluga y Tupungatito; la P3b lo confirma en Láscar y Tupungatito). Las razones medianas marginales
(C0 0,748, F 0,620) lo muestran; la d mediana no. En VIIRS 750 los 28 pares son idénticos (d = 0 en el 100 %),
y ahí el cero sí es real. En MODIS (K) hay 3 pares, SIN SUSTRATO, y en los 3 K queda más cerca de MIROVA.

Con la regla sellada el veredicto es CUMPLE, y no se cambia después de mirar. Pero no hay que leerlo como
«la magnitud no empeora».

## 5. Prueba independiente del instrumento (A110, A116)

Siembras sobre los datos REALES de V1 (copia de `union_d16`), script `scripts/sembrar.py`, salidas
`siembra_*.log` y `siembra_*_resumen.txt`:

| caso | siembra | esperado | obtenido |
|---|---|---|---|
| veto_a | F y K ocultan la protegida A que decide Chillán VIIRS 375 2026-10-01 05:24 (`distance_class` far) | VETADO A y B | P1 VIIRS 375 VETADO en A y B para F y K; global NO CUMPLE (veto) |
| veto_modis | K pierde la protegida MODIS Chillán 2026-10-05 07:50 por otro mecanismo (sin cúmulo, VRP 0, `discarded_reason`) | K vetado, F no | P1 K MODIS VETADO; F lectura A sigue CUMPLE (MODIS sólo informa en F) |
| pierde | F y K reciben el record de C0, sin Test 1, en las pasadas negativas que C0 publica (1.426 records) | PIERDE | suma F 750 contra C0 734 -> P2 PIERDE; global NO CUMPLE (suma de errores); cableado sigue OK |
| magnitud | F y K publican VIIRS 375 con 1/20 de la magnitud | P3 FALLA | d mediana +1,301 [+1,301, +1,301] -> FALLA; global CUMPLE EN DETECCIÓN, FALLA EN MAGNITUD |

El instrumento puede dar VETADO, PIERDE, FALLA e INDECIDIBLE (esta última, con la unión sin D-16) sobre estos
datos. Su único punto ciego encontrado es el de P3 (sección 4), que no es un defecto de código sino de la
métrica sellada.

## 6. Lo que Nicolás debe saber antes de mirar V2

1. **La mejora en detección es real y se sostiene**: VIIRS 375 baja de 734 a 37 errores (88,2 % a 2,5 % en
   negativos limpios), VIIRS 750 de 331 a 26, MODIS de 114 a 4 (F) o 10 (K); el gemelo dio 0 pasadas
   discordantes en los tres sensores y C0 cae dentro de la banda de A114 (P6). El costo son 21 alertas de
   VIIRS 375, 19 de ellas bajo 1 MW y 11 de 0,05 MW o menos.
2. **El CUMPLE de la lectura A en V1 descansa sobre Chillán en erupción** (10 de 12 protegidas que deciden en
   VIIRS 375). V2 es la que puede vetar, sobre todo con Láscar.
3. **Las 2 protegidas de Tupungatito** siguen sin la revisión de cabecera que pide el pre-registro. Todo indica
   que son objetos lejanos (distancias candidatas del OCR y posición del cúmulo de F coinciden en radio), pero
   hay que mirarlas antes de adoptar.
4. **El veto de la lectura B es un artefacto del pareo por pasada**: en las 12 pérdidas, C0 nunca publicó el
   objeto de MIROVA, sino un píxel del cráter de 0,012 a 0,10 MW por el Test 1. Si la lectura B importa,
   habría que contarla por objeto, no por pasada.
5. **P3 no protege la magnitud**: en V2 seguirá ciega mientras más de la mitad de los pares no cambie. Si la
   magnitud importa para la adopción, conviene informar al lado, como dato y sin cambiar la regla sellada, la
   media de d con su intervalo y la prueba de signos sobre los pares que cambian.
