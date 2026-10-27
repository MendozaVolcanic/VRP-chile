# Adenda 2 de V750-B (propuesta 2026-10-27): posición del record como diagnóstico y pasadas lejanas de MIROVA

Estado: **PROPUESTA, SIN SELLAR.** V750-B está sellado: esta adenda entra sólo si Nicolás la sella (decisión
relayada por la coordinadora S165 el 2026-10-27). Si no está sellada el día del despacho (2026-11-03), V750-B se
despacha tal como está sellado y las pasadas lejanas quedan para una corrida aparte. Escrita antes de ver los datos
del run, que no existen todavía. Al sellarse se agrega al final de `PREREGISTRO_V750B.md`, con un aviso arriba, igual
que la adenda 1. Autor: sesión VIIRS 750 2 (`tasks/LOOP_VIIRS750.md`, R9).

## 1. Qué pidió Nicolás y por qué toca a V750-B

Nicolás, 2026-10-27 (programa §7, rama `loop/activo`, `72928820b`): «Sí: no fijes la regla todavía; mídela como brazo
(radiante, cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA». El programa agrega que la vara
incluye las pasadas en que MIROVA publicó una fuente lejana (`FALSO_POSITIVO` de la tabla), y que si un pre-registro
está sellado los brazos entran por adenda, antes de ver los datos.

En VIIRS 750 los tres brazos de posición pertenecen a V750-A (el A/B de fase 4), que sigue en borrador y los recibe en
su texto. V750-B no decide nada sobre la posición. Pero es la única corrida que baja los gránulos antes de V750-A, y
guarda lo necesario para medir los tres brazos: por cada pasada y cada caja, todos los alertados con su fila, columna
y radiancia M13, y la grilla entera. Si V750-B corre sin las pasadas lejanas, V750-A tendría que volver a bajarlas
de NASA.

## 2. El fenómeno, como geólogo

La regla de posición sólo importa en una escena: un píxel débil junto al cráter y una fuente más radiante lejos (otro
foco del complejo, un borde de nube, un incendio). El analizador sellado ubica el record en el centroide del cúmulo
del alertado más radiante (**radiante**). Si ese cúmulo cae fuera del radio interior, el record queda lejano y el
tablero calla. Con **cercano**, el mismo record queda en la cumbre y el tablero publica la suma de todos los alertados,
que en esa escena viene sobre todo de la fuente lejana. Con **pico**, manda el píxel más radiante solo, sin promediar
su cúmulo: en un cúmulo que cruza el borde del radio interior, el centroide puede quedar adentro y el pico afuera.

Las pasadas en que MIROVA publicó una fuente lejana son justo esa escena vista desde MIROVA: vio calor y lo ubicó lejos
del cráter. Ahí lo correcto es no publicar como cumbre, y es donde «cercano» puede publicar de más. La medición de S165
no las pudo mirar en VIIRS (el programa §7, `72928820b`, dice «19 en VIIRS 750»; el informe de S165 no trae esa cifra,
VAD2-13, y el generador de esta adenda da 20 sobre su propia ventana, §6).

## 3. Qué agrega (nada de lo sellado cambia)

1. **Lista suplementaria** (`adenda2/objetivos_supl_v750b.py`). Corre la misma población (`01_poblacion.py` de main,
   la misma lógica) cambiando sólo el filtro de etiquetas de la l. 106 para dejar pasar también `far_ref` (fila
   FALSO_POSITIVO y ninguna ALERTA a ±120 s, etiqueta de `banco_paridad`). Aplica los mismos cortes del generador
   sellado (días excluidos, cese de Suomi NPP, sin gránulo afuera y declarado). Escribe aparte
   `objetivos_supl_v750b.json` (ids desde 100000), `sin_granulo_supl_v750b.json` (atado por sha256),
   `objetivos_run_v750b.json` (la sellada, sin tocar, seguida de la suplementaria) y `poblacion_supl.json`.
   **Control**: las `pos` y `neg_limpio` de esa corrida, con los mismos cortes, tienen que ser exactamente las de la
   lista sellada del mismo día, campo por campo (volcán, hora, gránulo, etiqueta, protegida, alerta de la tabla y si
   decide; VAD2-08). Si no, sale 1 sin escribir ninguna lista y deja la población como
   `poblacion_supl_CONTROL_FALLIDO.json`. Se niega a escribir en la carpeta sellada o encima de salidas de otra corrida
   (sale 2; no borra nada; VAD2-03 y VAD2-09).
2. **El run lee `objetivos_run_v750b.json`.** En la rama de disparo, además de lo que ya manda el §9 sellado, van los
   cuatro archivos de `adenda2/` del punto 1 (el tag `s162-v750b-sellado` no tiene esa carpeta: se commitean en la
   rama de disparo junto a la lista sellada) y la copia del workflow con
   `OBJETIVOS: "experiments/_s162_v750b/adenda2/objetivos_run_v750b.json"`. El probe y su lógica no cambian; las
   pasadas suplementarias corren en los mismos 32 trozos. Según el verificador, 19 de las 20 del ensayo caen en
   gránulos que ya se bajan, y 301 de 1.319 gránulos sellados cambian de trozo (cosmético, VAD2-10).
3. **Relanzamiento** (VAD2-06). Un relanzamiento de faltantes con `SOLO` tiene que leer la **misma** lista del run: si
   lee la sellada, el probe descarta sin error los ids desde 100000, imprime «0 granulos, 0 pasadas» y el trozo sale
   verde sin haber hecho nada (A108; lectura del código, no ejecutado). Antes de dar por bueno un relanzamiento se
   cuenta, en su log, que procesó tantas pasadas como ids pidió `SOLO`.
4. **Separación antes de la lectura sellada** (`adenda2/separar_resultados_v750b.py`). Escribe `sellado/` (ids menores
   que 100000) y `supl/`, cada carpeta de artefactos con su índice delante, para que la corrida y su relanzamiento no
   se pisen aunque se llamen igual (VAD2-01, que con la primera versión perdía resultados); cuenta releyendo lo escrito
   y sale 1 si las partes no suman lo leído. El verificador mostró que sin separar sólo cambia la línea informativa
   «con resultado N» del analizador; se separa igual para que la lectura sellada vea **exactamente** lo que habría visto
   sin la suplementaria (byte a byte, escenario P8, con su testigo).
5. **Diagnóstico de posición** (`adenda2/leer_posicion_v750b.py`). No decide V750-B: es insumo de V750-A.

## 4. El diagnóstico

- **Brazos**, sobre la misma detección de cada caja (B0 a B5; sólo cambia el punto desde donde se mide la distancia,
  y con ella la clase `summit` o `far`; el VRP, que es el de la unión de los alertados, y el tamaño del cúmulo quedan
  como los arma el analizador sellado):
  - **radiante**: `record_cumulo` del analizador sellado, sin tocar;
  - **cercano**: el alertado más cercano al cráter (`pos_crater`, como mide producción);
  - **pico**: el alertado de mayor M13, el mismo que siembra el cúmulo, con el mismo desempate.
- **Población**: la del analizador sellado, con su misma exclusión de las pasadas en que el K del probe no reproduce a
  producción (§7; VAD2-02). Así la fila «radiante» de cada caja es la del veredicto sellado: el verificador lo comprobó
  contra el analizador, con el cráter en el centro y corrido del centro.
- **Publica**: el predicado del tablero ejecutado con node (A97).
- **Vara 1, alertas y negativos limpios** (la población sellada): P1 y E del §5 con el canal que decide y con la tabla
  sola, en T y O juntas, y la prueba de signos de P2 contra radiante de la misma caja. Las funciones (`etiqueta`,
  `metricas`, `p2`) se extraen con ast del `main()` del analizador sellado y se ejecutan sin copiar a mano; el
  analizador se identifica por sha256 con fin de línea LF (`83b7159b...`, el del tag). Además, las pasadas que cambian
  de publicación contra radiante, por nombre.
- **Vara 2, pasadas lejanas de MIROVA**: cuántas tienen algún alertado en cada caja (VAD2-07: sin eso, un cero de
  «publica» no distingue «la escena no ocurrió» de «el brazo no publica de más») y cuántas publica cada brazo (lo
  correcto es cero), por nombre.
- **Vara 3, distancia**: la distancia de cada brazo desde la celda central de la grilla (33, 33; el punto de
  referencia de MIROVA queda a hasta 0,35 km de ella, VAD2-12) contra la `Distancia_km` de MIROVA, en alertas y en
  pasadas lejanas: mediana de la diferencia y fracción a 1 km o menos. Del OCR sólo entran las filas desde el
  2026-06-13 (A119; VAD2-05). Es diferencia de radios, no de posiciones (A93): sirve para descartar un brazo, no para
  afirmar que ve el mismo objeto que MIROVA. S165 encontró que la distancia de MIROVA calza mejor con el píxel pico que
  con el centroide; esto lo mide en VIIRS 750 con el código de MIROVA.
- **Controles** (si uno cae, sale 3 y dice DIAGNÓSTICO NO LEGIBLE): C1, en las cajas con un solo alertado los tres
  brazos coinciden, con al menos un caso; C2, nulo del predicado (un record radiante publicado, pasado a lejano, deja
  de publicar); C3, las listas (ids sellados bajo 100000, suplementarios desde 100000, sin choque, todas `far_ref`,
  archivo sin gránulo atado por sha256); C4, el analizador es el sellado (si no lo es, ni se carga).
- **SIN DATO** de la suplementaria: las procesadas que fallaron se listan por nombre; las sin gránulo, también. No frena
  nada (es diagnóstico).
- Orden de lectura: primero la sellada (§8). Si su compuerta queda cerrada, el diagnóstico se informa igual pero con
  esa marca, porque mide sobre la misma población.

## 5. Lo que esta adenda NO hace

- No toca la ROI, las métricas, la regla del §6 ni los controles del §7 de V750-B, ni su analizador.
- No elige regla de posición. Eso lo decide V750-A, con su propia regla escrita antes del sello.
- No cubre los `FALSO_POSITIVO` que en la misma pasada conviven con una ALERTA (esa pasada es `pos` y ya está en la
  población sellada), ni las 8 pasadas `sin_geometria` del ensayo (MIROVA vio calor sin saber dónde, V31.1), que
  quedan fuera de las dos listas por construcción (VAD2-13).
- «Lo correcto es no publicar» en las pasadas lejanas es una premisa de la réplica (A115): vale para
  `mirova_equivalent`, no para el perfil `experimental`.

## 6. Ensayo (2026-10-27, sobre main `bd711db63`, ventana hasta 2026-10-26)

`objetivos_v750b.py` da 5.841 objetivos (0 sin gránulo). `objetivos_supl_v750b.py` con la misma ventana: control
IGUALES (5.841 contra 5.841), **20 pasadas `far_ref` con gránulo, 0 sin gránulo**: Lastarria 5, Tupungatito 4,
Nevados de Chillán 3, Láscar 2, Planchón-Peteroa 2, Isluga 2, Llaima 1, Villarrica 1; distancias de MIROVA de 6,4 a
29,6 km; 6 antes del 2026-06-13. Las 20 traen una fila `FALSO_POSITIVO` de la tabla (una trae además una del OCR), y su
distancia sale de la de la tabla en las 20, así que no depende del OCR mal calibrado de antes de junio (A119).
Producción no publica ninguna de las 20. Costo: 20 pasadas más sobre unas 6.000 (0,3 %). El verificador reprodujo el
ensayo (5.841 IGUALES, 20, 0 sin gránulo, archivo suplementario idéntico byte a byte) con la versión anterior del
generador; la versión corregida ordena las suplementarias también por hora, así que su sha256 ya no es el del ensayo.
Los archivos del ensayo no son los definitivos y no se commitean.

## 7. Despacho del 2026-11-03 (sólo si Nicolás selló esta adenda)

Sobre el main de ese día, en este orden (la carpeta `adenda2/` no debe tener salidas de antes):

    python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02
    python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json

Se commitean `objetivos_v750b.json`, `sin_granulo_v750b.json` y `poblacion_completa.json` (sellados) y
`adenda2/objetivos_supl_v750b.json`, `adenda2/sin_granulo_supl_v750b.json`, `adenda2/objetivos_run_v750b.json` y
`adenda2/poblacion_supl.json`, con los tres sha256 que imprime el segundo comando. La coordinadora despacha desde el tag,
en la rama de disparo con esos archivos, con `OBJETIVOS` apuntando a `objetivos_run_v750b.json` (§3, puntos 2 y 3).

## 8. Lectura

    python <repo>/experiments/_s162_v750b/adenda2/separar_resultados_v750b.py --art <artefactos> [<relanzamiento>] --dest <carpeta nueva>
    python <repo>/experiments/_s162_v750b/adenda1/leer_v750b.py --art <carpeta nueva>/sellado <resto de argumentos de la adenda 1>
    python <repo>/experiments/_s162_v750b/adenda2/leer_posicion_v750b.py --art <artefactos> [<relanzamiento>] --objetivos <repo>/experiments/_s162_v750b/objetivos_v750b.json --objetivos-supl <repo>/experiments/_s162_v750b/adenda2/objetivos_supl_v750b.json --sin-granulo-supl <repo>/experiments/_s162_v750b/adenda2/sin_granulo_supl_v750b.json --evaluador <evaluar_d25.py del tag s161-d25-lectura>

El veredicto de V750-B es el del segundo comando y sólo ése. El tercero informa.

## 9. Pruebas

- `adenda2/probar_adenda2.py` (`probar_adenda2_salida.txt`): **35 de 35** como se espera, con escenas sintéticas en el
  formato del probe: LEJANA (alertado débil junto al cráter y cúmulo brillante a 13 km), BORDE (cúmulo que cruza el
  radio interior con el pico afuera), UNO (un solo alertado), PICOCERCA (el más radiante junto al cráter y un cúmulo
  más débil lejos) y una pasada con el cráter 7,5 km al W del centro. Comprueba P1 y E por brazo en los dos canales,
  los cambios contra radiante con su etiqueta (exactos, sin las suplementarias), P2, la pasada lejana (sólo cercano
  publica, con alertado), la distancia desde el centro con el cráter corrido, la exclusión de K distinto y de la
  diurna, la alerta sólo del OCR (cuenta en el canal que decide y no en la tabla sola; antes del 13-jun no entra a la
  vara 3), los controles C1 (con y sin casos), C3 (tres roturas) y C4, el SIN DATO por lista, la separación (P8 y su
  testigo, carpetas del mismo nombre, carpeta ocupada) y las funciones del generador (filtro, cortes, control,
  selección, numeración y orden de la lista del run).
- Nulo: `adenda2/mutar_adenda2.py` (`mutar_adenda2_salida.txt`): **27 de 27 mutaciones de una línea atrapadas por
  aserción** (19 del lector, 2 del separador, 6 del generador), la copia sin mutar PASA y la mutación que sólo hace caer
  al lector sale CAÍDA. Incluye las 14 del verificador que la primera versión de la batería dejaba pasar (VAD2-04).
  Quedan sin atrapar, declaradas: el predicado leyendo la columna del VRP de display en vez de la de publicación (en
  todas las escenas probadas las dos coinciden: un record lejano da display 0), el desempate del pico y el cruce de
  filas y columnas del centroide (equivalentes en las escenas, sólo importan con empates o en la diagonal), y la
  primera de las dos defensas del separador contra una carpeta ocupada (la segunda la ataja).
- Límite declarado: apagar C2 no lo atrapa ninguna escena (con datos sanos el control ya da verde); se prueba por las
  mutaciones que rompen lo que vigila (L5 lo hace caer).

## 10. Estado y verificador

- Batería: 35 de 35. Nulo: 27 de 27 atrapadas por aserción; identidad PASA; control CAÍDA.
- Verificador limpio (Sonnet 5.5, `adenda2/verificador/INFORME.md`, sobre `83405c557`): **LISTO CON CAMBIOS**, ningún
  hallazgo de gravedad 4 o 5; la lectura sellada no se contamina y los tres brazos miden lo que dicen. Hechos todos sus
  cambios: VAD2-01 (separador), VAD2-02 (exclusión de K distinto), VAD2-03 y VAD2-09 (el generador no escribe encima ni
  en la carpeta sellada), VAD2-04 (escenarios y 14 mutaciones suyas al nulo), VAD2-05 (OCR de antes del 13-jun fuera de
  la vara 3), VAD2-06 (relanzamiento, §3.3), VAD2-07 (pasadas lejanas con alertado), VAD2-08 (control campo por campo),
  VAD2-10 (declarado), VAD2-11 (sin gránulo por nombre), VAD2-12 (celda central) y VAD2-13 (cifra 19 y `sin_geometria`).
  Seguimiento suyo que no es de la adenda: `01_poblacion.py` escribe en el meta un commit fijo (`533398f8f`) aunque los
  records sean de otro.
