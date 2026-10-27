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
no las pudo mirar en VIIRS (19 en VIIRS 750, `experiments/_s165_regla_posicion/INFORME.md`, en `loop/activo`).

## 3. Qué agrega (nada de lo sellado cambia)

1. **Lista suplementaria** (`adenda2/objetivos_supl_v750b.py`). Corre la misma población (`01_poblacion.py` de main,
   la misma lógica) cambiando sólo el filtro de etiquetas de la l. 106 para dejar pasar también `far_ref` (fila
   FALSO_POSITIVO y ninguna ALERTA a ±120 s, etiqueta de `banco_paridad`). Aplica los mismos cortes del generador
   sellado (días excluidos, cese de Suomi NPP, sin gránulo afuera y declarado). Escribe aparte
   `objetivos_supl_v750b.json` (ids desde 100000), `sin_granulo_supl_v750b.json` (atado por sha256) y
   `objetivos_run_v750b.json` (la sellada seguida de la suplementaria). **Control**: las `pos` y `neg_limpio` de esa
   corrida, con los mismos cortes, tienen que ser exactamente las de la lista sellada del mismo día; si no, sale 1 y no
   escribe la lista del run.
2. **El run lee `objetivos_run_v750b.json`.** Es el único cambio del despacho: en la copia del workflow de la rama de
   disparo, `OBJETIVOS: "experiments/_s162_v750b/adenda2/objetivos_run_v750b.json"`. El probe, el workflow y el tag no
   cambian en nada más; las pasadas suplementarias corren en los mismos 32 trozos.
3. **Separación antes de la lectura sellada** (`adenda2/separar_resultados_v750b.py`). Escribe `sellado/` (ids menores
   que 100000) y `supl/`. La lectura sellada (adenda 1, `leer_v750b.py`) corre sobre `sellado/` y ve exactamente lo
   que habría visto sin la suplementaria: la batería lo comprueba byte a byte (P8), y comprueba también el testigo, que
   sin separar la salida sellada sí cambia (cuenta los resultados de más).
4. **Diagnóstico de posición** (`adenda2/leer_posicion_v750b.py`). No decide V750-B: es insumo de V750-A.

## 4. El diagnóstico

- **Brazos**, sobre la misma detección de cada caja (B0 a B5; sólo cambia el punto desde donde se mide la distancia,
  y con ella la clase `summit` o `far`; el VRP, que es el de la unión de los alertados, y el tamaño del cúmulo quedan
  como los arma el analizador sellado):
  - **radiante**: `record_cumulo` del analizador sellado, sin tocar;
  - **cercano**: el alertado más cercano al cráter (`pos_crater`, como mide producción);
  - **pico**: el alertado de mayor M13, el mismo que siembra el cúmulo, con el mismo desempate.
- **Publica**: el predicado del tablero ejecutado con node (A97).
- **Vara 1, alertas y negativos limpios** (la población sellada): P1 y E del §5 con el canal que decide y con la tabla
  sola, en T y O juntas, y la prueba de signos de P2 contra radiante de la misma caja. Las funciones (`etiqueta`,
  `metricas`, `p2`) se extraen con ast del `main()` del analizador sellado y se ejecutan sin copiar a mano; el
  analizador se identifica por sha256 con fin de línea LF (`83b7159b...`, el del tag). Además, las pasadas que cambian
  de publicación contra radiante, por nombre.
- **Vara 2, pasadas lejanas de MIROVA**: cuántas publica cada brazo en cada caja (lo correcto es cero), por nombre.
- **Vara 3, distancia**: la distancia de cada brazo desde el **centro** de la grilla (desde donde mide MIROVA)
  contra la `Distancia_km` de MIROVA, en alertas y en pasadas lejanas: mediana de la diferencia y fracción a 1 km o
  menos. Es diferencia de radios, no de posiciones (A93): sirve para descartar un brazo, no para afirmar que ve el
  mismo objeto que MIROVA. S165 encontró que la distancia de MIROVA calza mejor con el píxel pico que con el
  centroide; esto lo mide en VIIRS 750 con el código de MIROVA.
- **Controles** (si uno cae, sale 3 y dice DIAGNÓSTICO NO LEGIBLE): C1, en las cajas con un solo alertado los tres
  brazos coinciden; C2, nulo del predicado (un record radiante publicado, pasado a lejano, deja de publicar); C3, las
  listas (ids sin choque, todas `far_ref`, archivo sin gránulo atado por sha256); C4, el analizador es el sellado (si
  no lo es, ni se carga).
- **SIN DATO** de la suplementaria: se lista por nombre y no frena nada (es diagnóstico).

## 5. Lo que esta adenda NO hace

- No toca la ROI, las métricas, la regla del §6 ni los controles del §7 de V750-B, ni su analizador.
- No elige regla de posición. Eso lo decide V750-A, con su propia regla escrita antes del sello.
- No cubre los `FALSO_POSITIVO` que en la misma pasada conviven con una ALERTA (esa pasada es `pos` y ya está en la
  población sellada).

## 6. Ensayo (2026-10-27, sobre main `bd711db63`, ventana hasta 2026-10-26)

`objetivos_v750b.py` da 5.841 objetivos (0 sin gránulo). `objetivos_supl_v750b.py` con la misma ventana: control
IGUALES (5.841 contra 5.841), **20 pasadas `far_ref` con gránulo, 0 sin gránulo**: Lastarria 5, Tupungatito 4,
Nevados de Chillán 3, Láscar 2, Planchón-Peteroa 2, Isluga 2, Llaima 1, Villarrica 1; distancias de MIROVA de 6,4 a
29,6 km; 6 antes del 2026-06-13. Las 20 traen una fila `FALSO_POSITIVO` de la tabla (una trae además una del OCR), así
que su distancia no depende del OCR mal calibrado de antes de junio (A119). Producción no publica ninguna de las 20.
Costo: 20 pasadas más sobre unas 6.000 (0,3 %). Los archivos del ensayo no son los definitivos y no se commitean.

## 7. Despacho del 2026-11-03 (sólo si Nicolás selló esta adenda)

Sobre el main de ese día, en este orden:

    python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02
    python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json

Se commitean `objetivos_v750b.json`, `sin_granulo_v750b.json` y `poblacion_completa.json` (sellados) y
`adenda2/objetivos_supl_v750b.json`, `adenda2/sin_granulo_supl_v750b.json`, `adenda2/objetivos_run_v750b.json` y
`adenda2/poblacion_supl.json`, con los tres sha256 que imprime el segundo comando. La coordinadora despacha desde el tag
con `OBJETIVOS` apuntando a `objetivos_run_v750b.json`.

## 8. Lectura

    python <repo>/experiments/_s162_v750b/adenda2/separar_resultados_v750b.py --art <artefactos> --dest <carpeta nueva>
    python <repo>/experiments/_s162_v750b/adenda1/leer_v750b.py --art <carpeta nueva>/sellado <resto de argumentos de la adenda 1>
    python <repo>/experiments/_s162_v750b/adenda2/leer_posicion_v750b.py --art <artefactos> --objetivos <repo>/experiments/_s162_v750b/objetivos_v750b.json --objetivos-supl <repo>/experiments/_s162_v750b/adenda2/objetivos_supl_v750b.json --sin-granulo-supl <repo>/experiments/_s162_v750b/adenda2/sin_granulo_supl_v750b.json --evaluador <evaluar_d25.py del tag s161-d25-lectura>

El veredicto de V750-B es el del segundo comando y sólo ése. El tercero informa.

## 9. Pruebas

- `adenda2/probar_adenda2.py` (`probar_adenda2_salida.txt`): 18 de 18 como se espera, con escenas sintéticas en el
  formato del probe: LEJANA (alertado débil junto al cráter y cúmulo brillante a 13 km), BORDE (cúmulo que cruza el
  radio interior con el pico afuera) y UNO (un solo alertado). Comprueba P1 y E por brazo, los cambios contra radiante
  con su etiqueta, la pasada lejana (sólo cercano publica), la distancia desde el centro con el cráter corrido del
  centro, los controles C3 y C4, la separación (P8 y su testigo) y el filtro del generador (P9).
- Nulo: `adenda2/mutar_adenda2.py` (`mutar_adenda2_salida.txt`): **13 de 13 mutaciones de una línea atrapadas por
  aserción** (diez del lector, una del separador, dos del generador), la copia sin mutar PASA y la mutación que sólo
  hace caer al lector sale CAÍDA. La primera corrida dejó una como CAÍDA y no atrapada (L9, C4 que acepta cualquier
  analizador): la copia del analizador de P7 vivía fuera de su carpeta y se caía al cargar; ahora vive al lado del
  sellado y la falla es por aserción.
- Límite declarado: apagar C1 o C2 no lo atrapa ninguna escena (con datos sanos el control ya da verde); esos controles
  se prueban por las mutaciones que rompen lo que vigilan.

## 10. Estado

- Batería: 18 de 18.
- Nulo: 13 de 13 atrapadas por aserción; identidad PASA; control CAÍDA.
- Verificador limpio: PENDIENTE.
