# AUDIT S158, segunda ronda: replicación independiente, segundo oráculo y prueba con gránulos chilenos

> S158 R2, 2026-10-21. Brief: `experiments/_s158_audit/BRIEF_SEGUNDA_RONDA.md`. Rama `claude/s158-audit-r2-0eeee2`,
> cortada de `s158-d17-diseno` (PR #885). Todo el material (scripts, salidas crudas, informes por frente) está en
> `experiments/_s158_audit_r2/`. Nada de `pipeline/`, `data/` ni `frontend/` se tocó; el único workflow despachado es de
> sólo lectura (rama de disparo `s158-r2-granulos-disparo`, no se mergea). El correo a Coppola no se envió.
>
> **Cómo se aseguró la independencia.** Los veredictos propios quedaron escritos y commiteados en
> `experiments/_s158_audit_r2/VEREDICTOS_ANTES_DE_COMPARAR.md` (commit `26c9d078a`) **antes** de abrir
> `docs/AUDIT_S158.md`, los informes `f*/` y `v*/` de la primera ronda y las ramas hermanas. Los auditores de esta
> ronda escribieron sus scripts desde cero y tenían prohibido leer la primera ronda (salvo M1, cuyo objeto era el método
> de la primera ronda, y A113, que leyó sólo la tabla del §3 de F2). Seis de los nueve agentes de la primera ronda
> eran Opus; los auditores que replicaron hallazgos de Opus fueron Fable, el meta-auditor fue Sonnet, y los dos
> verificadores finales (Opus) no habían encontrado nada de lo que verifican.

## 0. La respuesta corta: ¿qué falta para la paridad con MIROVA?

**Lo que falta ya no es una incógnita: son cinco cambios con nombre, y el más grande está probado sobre gránulos
chilenos.** Por primera vez se corrió el código de MIROVA (en un port propio) sobre los mismos gránulos de VIIRS 750
que usó nuestro pipeline. Donde ese código detecta, da la magnitud de MIROVA a menos de 10 %; producción, sobre el
mismo gránulo, da entre 0 y la mitad. Ordenado por cuánto acerca cada pieza:

1. **El fondo del VRP y la suma (VIIRS 750 con código; VIIRS 375 y MODIS trasladado).** De noche la cumbre es más fría
   que las laderas y los valles del anillo de 5 a 25 km. Nosotros restamos la mediana de ese anillo, que es más tibia
   que el entorno del cráter, y recortamos a cero lo que queda bajo ella; MIROVA aparta los píxeles alertados con un
   halo, interpola el fondo con los que quedan alrededor y no recorta; además suma todos los alertados, y nosotros en
   cúmulos de hasta 3 píxeles publicamos el máximo. Medido: en Láscar 2026-10-08 05:42 el código da 0,33 MW, MIROVA
   0,36 y producción 0,0; en Villarrica 2026-09-19 05:48, 0,47 / 0,45 / 0,23; en Chillán 2026-10-10 05:54, 12,4 / 13,1 /
   10,5 (el de Láscar es frágil: con otras triangulaciones del fondo el código da 0,19 a 0,33). En el corpus, 595 de
   2.359 cúmulos de cumbre de VIIRS 750 (25 %) publican 0,0 MW y el tablero los oculta; en la misma pasada, 64 de ellos
   son alertas de MIROVA, todas bajo 1 MW (pareo por pasada a 8 min desde el 2026-01-10; un pareo a 60 min, que mezcla
   satélites, había dado 96 y 11 protegidas, y el verificador lo corrigió). El mismo cero sale también en MODIS (37) y
   en VIIRS 375 (271), y en los tres sensores casi siempre de un píxel que sólo encontró el segundo pase. **Ojo con la
   otra cara**: el mismo cambio despegaría del cero también pasadas donde MIROVA no
   vio nada (la investigación hermana de #887 las cuenta: 68 negativos limpios), así que se adopta sólo con A/B.
2. **La geometría: el remuestreo a la grilla UTM de MIROVA (D17) y su interpolador.** Nuestra razón de magnitud cae con
   el ángulo de observación. En VIIRS 375 es porque **nuestro** conteo de píxeles alertados cae mientras el de MIROVA
   queda plano; en MODIS, porque el de MIROVA **sube** con el ángulo (su grilla fija reparte el píxel grande en más
   celdas) y el nuestro no lo acompaña. Las dos caras son la misma pieza: área nadir fija sin remuestreo. En
   los gránulos, dos alertas débiles de cumbre (Láscar 2026-09-26, Chaitén 2026-10-06) aparecen o desaparecen según se
   mueva la grilla media celda o se cambie el interpolador. Falta identificar el interpolador y el origen exacto de la
   grilla de 750 m antes de implementar D17.
3. **La detección de VIIRS 750 igualada al código, en un solo paquete.** Sin la compuerta `bt > t_bg + 3 K` del primer
   pase, con el segundo pase sobre toda la escena rehaciendo la regresión del ETI, con el mínimo de dNTI de 0,02 fuera de
   la cumbre (nosotros 0,010), con la ventana de 3 × 3 que incluye al píxel central, y con la rama diurna del código
   (K1 de -0,5, 15 σ, rechazo por reflejo solar bajo 12°) en vez del rechazo de todo lo diurno. El K1 nocturno (-0,7
   en el código, -0,8 en el perfil `mirova_equivalent`, leído de `pipeline.profile`) casi no decide qué se publica.
4. **La ROI de cada volcán.** El código dice que MIROVA mueve y redimensiona sus ROI por volcán. En Cordón Caulle las
   dos alertas probadas (7,7 y 7,8 km del centro) sólo aparecen si el anillo usa los umbrales de cumbre: MIROVA tiene
   ahí una caja propia que no conocemos. En Tupungatito, la alerta a 5 km no aparece con ninguna variante.
5. **MODIS: geolocalización y fondo.** La interpolación de la geolocalización de MODIS ignora el desfase de su grilla de
   5 km y corre los píxeles de un lado del barrido hacia el nadir (2 a 3,6 km sobre 25° de cenit; del otro lado, casi
   nada), y el producto MOD03 que lo evitaría se baja y se ignora; el fondo de anillo con recorte deja en 0 MW 37
   cúmulos de cumbre MODIS, uno de ellos alerta de MIROVA de 1,04 MW (Láscar 2026-02-16 01:20, Terra).

Y **antes de creerle a cualquier A/B**, tres arreglos de instrumento: (a) cero gránulos (o un L1B sin su
geolocalización) se registra como «Cobertura: completa»; (b) la métrica M del A/B de D25 da MEJORA a un placebo que
multiplica la magnitud por 1,2 con la calibración simétrica de la adenda, **que está sellada desde el 2026-10-20
(D-27) y es la que rige**, mientras el evaluador sigue usando la calibración original por defecto; (c) hoy (21-oct,
17:33 a 17:41 UTC) CMR no devuelve **ningún** gránulo de VIIRS (bandas I y M, los tres satélites) ni de MODIS para todo
el 2026-10-18, ni de VIIRS para el 19-oct, aunque producción procesó los del 18 ese mismo día: ningún reproceso puede
reponer esos días mientras NASA no los vuelva a servir.

**Sobre #864** (auto-audit fuera de banda, insumo de S159): el recall de VIIRS 750 de 73,3 % se explica casi entero por
la pieza 1 (cráter detectado y publicado en 0 MW, oculto) y en parte por la 4 (Cordón Caulle 2026-10-10, sin detección
nuestra, alerta a 7,8 km); las dos protegidas de Chillán MODIS (2026-10-12 07:20 y 10-15 01:05, cenit 58°) no tienen
ningún píxel detectado nuestro, lo que apunta a la pieza 2 y a la 5 (SOSPECHA, sin gránulo); y las dos de Tupungatito
VIIRS 375 no son del cráter (nuestro cúmulo está a 21,6 y 9,4 km; la investigación hermana de #886 lo confirma en la
imagen de MIROVA). Las magnitudes bajas de Chillán (0,49 a 0,69) son compatibles con las piezas 1 y 2.

## 1. Las doce afirmaciones del brief, con veredicto propio

| # | afirmación | veredicto R2 | evidencia R2 (script o archivo) |
|---|---|---|---|
| 1 | El fondo V750 de producción es un escalar del anillo de 5 a 25 km con recorte a cero, y con los mismos píxeles de Etna da otra magnitud que el código | **CONFIRMADA** | `ra1/fondo_produccion_etna.py`: mediana del anillo pasada por Planck (`pipeline/process_viirs_mod.py:1041`), recorte por píxel `np.maximum(L_hot - L_bg, 0)` (`:1056`); Etna, mismos 5 píxeles: 2,75 MW contra 9,89 del OSF (0,28). Gránulos chilenos: §3 |
| 2 | Ese fondo deja en 0 MW cúmulos de cumbre V750 que el tablero oculta | **CONFIRMADA** (cruce con MIROVA CON MATIZ) | `ra1/contar_ceros_v750.py`, predicado real del tablero con node (`ra1/predicado_tablero.js`): 595 de 2.359 cúmulos de cumbre (corpus completo, observaciones 2025-02-15 a 2026-10-21), los 595 ocultos; reproducido exacto por el verificador (`verificador/va/v01_*`). En la misma pasada (8 min, desde 2026-01-10) 64 son alertas de MIROVA, **ninguna de 1 MW o más** (`verificador/va/v02_*`); el «96 y 11 protegidas» del auditor salía de un pareo a 60 min que juntaba la pasada siguiente. La división «pre-K / K» que hizo el auditor por fecha de observación **no es de régimen**: ver §4, R2-12 |
| 3 | Con el fondo por píxel de MIROVA del OSF sobre nuestros píxeles cambia la razón en VIIRS 375 | **CONFIRMADA CON MATIZ** | `ra2/02_magnitud_pares_osf.py` (OSF 2025, 2.139 pares a dt = 0): razón 0,830 → 0,885. Sube en los volcanes con fondo de anillo (Isluga 0,59 → 0,87, Copahue 0,64 → 1,02) y baja 5 a 14 % en los cinco con kernel local. El fondo explica una mediana de ~12 % de la brecha en VIIRS 375; el resto es conteo |
| 4 | La razón cae con el cenit y la caída es de conteo de píxeles | **CONFIRMADA** en VIIRS 375; **CON MATIZ** en MODIS; VIIRS 750 SIN DATO contra el OSF (n 45) | `ra2/02_*`: VIIRS 375, 1,02 a nadir → 0,62 sobre 60°; cae **nuestro** conteo (mediana 2,78 → 1,92 píxeles), el Npix de MIROVA es plano. En MODIS el verificador midió lo contrario en el lado de MIROVA: su Npix **sube** con el cenit (rho +0,30 en 12.938 filas chilenas del OSF, mediana 3 a 8) y el nuestro baja poco (`verificador/va/v04_*`): sigue siendo conteo, pero el que se mueve es el de MIROVA. Contra la tabla NRT (`ra2/04_nrt_cenit.py`, abril a octubre de 2026, 1.128 pares) la razón cae en los tres sensores |
| 5 | La compuerta `bt > t_bg + 3 K` del primer pase y el segundo pase están acoplados en V750 | **CON MATIZ** | `rb/01_sintetico_compuerta_segundo_pase.py`: el segundo pase no depende del primero (corre siempre), pero recaptura sin compuerta lo que la compuerta rechazó. `rb/01_sustrato_v750.py`: 1.257 de 28.581 records V750 existen sólo por el segundo pase. Que la compuerta sea la causa en esos records: SIN DATO (el record no guarda la BT del recapturado) |
| 6 | El código de MIROVA corre el segundo pase siempre y sobre toda la escena | **CONFIRMADA** | Lectura propia de `MIROVA_VIIRS750_hotspot_detection.m` l. 228-235 (sin condición) y l. 102-103 (dominio 67 × 67 menos el marco de 1 píxel, los tres BOX). En el oráculo, quitar el segundo pase cambia la máscara en 25 de 129 escenas sintéticas con alerta (`oraculo/comparar_oraculos_salida.txt`) |
| 7 | Cero gránulos en una búsqueda se registra como «Cobertura: completa» | **CONFIRMADA** | `rb/03_cero_granulos_cobertura.py`, sin red: 0 gránulos en 18 consultas → 0 fallas y código 0, aun con `--estricto-cobertura`; control: ReadTimeout → 6 fallas, código 3 |
| 8 | Al A/B de D25 le falta el 2026-10-18 | **CONFIRMADA, y falta más** | `rb/04_fechas_ab_d25.py`, `rb/04b_control_vs_produccion.py`, reproducido por `verificador/vb/`: faltan el 10-13 y el 10-18 completos y 44 pasadas del 10-12; 152 de 4.762 pasadas VIIRS de V1 (3,19 %), 0 pasadas del A/B que producción no tenga. El `cobertura.txt` del run dice «PAREJA» porque compara brazos entre sí y no puede ver un día que falta en todos. Sólo fechas y conteos; el veredicto del A/B no se leyó |
| 9 | La métrica M del evaluador de D25 da MEJORA con un brazo placebo de ganancia constante | **CONFIRMADA** | `rb/05_placebo_metrica_m.py` (pares de producción contra MIROVA, nunca el A/B): g = 1,2 da MEJORA en 4 de 4 estratos, g = 0,8 EMPEORA, g = 1,0 NEUTRO. La calibración original lo frena (INDECIDIBLE), pero frena **cualquier** brazo que cambie la magnitud; la **simétrica de la adenda** lo deja pasar, y esa adenda está **sellada** desde el 2026-10-20 (D-27, `experiments/_s157_prereg_d25/ADENDA_CALIBRACION.md:3`). El auditor la creyó sin sello; el verificador lo corrigió (`verificador/vb/`). Además `evaluar_d25.py:79` sigue con la original por defecto |
| 10 | Sobre 50° de cenit el VRP V750 del OSF no cumple la fórmula del código en parte de las filas | **CONFIRMADA** | `ra2/03_identidad_vrp_osf.py`: 8.239 de 34.250 filas V750 sobre 50° (24,1 %) no cumplen VRP = ΔL × 1,97e7 × 0,5625; bajo 50° cumple el 100 %; MODIS y VIIRS 375 cumplen el 100 % a todo cenit. Qué fórmula usan las que no cumplen: SIN DATO |
| 11 | Rechazamos todo VIIRS 750 diurno y se perdieron alertas protegidas de Chillán | **CONFIRMADA** | `rb/06_chillan_v750_diurno.py`: tres compuertas solares (`pipeline/store.py:188-223`, `pipeline/fetch.py:1018`, `scripts/run_pipeline.py:192`); el código de día cambia umbrales y sólo rechaza reflejo solar bajo 12°. Chillán V750: 3 de 3 protegidas diurnas sin record (2026-10-01 18:42 3,71 MW; 10-10 18:18 3,33; 10-18 19:06 2,49). Que sean señal y no reflejo solar: SOSPECHA |
| 12 | MIROVA cuenta píxeles, no regiones | **CONFIRMADA, y al revés de lo que decía el glosario** | `npix = numel(alert)` (`MIROVA_VIIRS750_VRP.m` l. 61). `ra2/`: el Npix del OSF se comporta como conteo; **nuestro** conteo es menor que el de MIROVA (mediana 0,67 en VIIRS 375, 0,50 en MODIS y VIIRS 750), no mayor |

## 2. El segundo oráculo (`experiments/_s158_audit_r2/oraculo/`)

Port de los dos `.m` escrito sin ver el primero. Lo que mostró:

- **Detección exacta.** En la pasada de Etna de la matriz de ejemplo (NOAA-20, 2023-05-19 00:54) da los mismos 5
  píxeles y el mismo Tot_Lmir_hot del OSF v2.5 (1,965342180), todos en la caja central de 7 × 7 (el comentario del `.m`
  la llama ROI 1, pero en la matriz es `BOX == 2`).
- **El fondo de `fillmissing2` es interpolación lineal sobre una triangulación de Delaunay, y la triangulación no es
  única.** En una grilla regular cuatro puntos de cada celda son cocirculares. Probando triangulaciones distintas sobre
  los mismos 5 píxeles salen 67 fondos posibles (VRP de 9,75 a 10,03 MW, ±1,3 %), y **uno coincide con el Tot_Lmir_bk
  del OSF a 3e-10**; por azar eso tendría una probabilidad del orden de 5e-6 (`oraculo/firma_fillmissing2.py`). Las
  alternativas (por filas, por columnas, relleno armónico) quedan a 1 a 18 %.
- **El primer oráculo usó otra de esas 67** (fondo 1,073661545): su «VRP a 0,09 %» fue una triangulación cercana, no
  una reproducción del interpolador. El meta-auditor llegó a lo mismo por su cuenta (±1,4 %, `m1/t19_oraculo_empates.py`).
- **Los dos oráculos coinciden en la detección**: máscaras idénticas en 600 escenas sintéticas (378 con alerta), con
  tres mutaciones de control que sí se ven (mínimo de cumbre, σ intercambiados, sin segundo pase). Una cuarta (K1 de
  -0,7 a -0,8) no cambia ninguna máscara: en esas escenas todo píxel con NTI entre -0,8 y -0,7 también pasa el test
  contextual. El VRP difiere entre ellos en más de 5 % en 23 de 378 escenas (máximo 82 %, foco junto al borde): la
  misma ambigüedad de triangulación más la extrapolación en el borde, que el `.m` no fija.

**Consecuencia práctica**: un oráculo en Python es vara exacta de la detección y vara del VRP dentro de unos pocos por
ciento, no al 0,1 %. Para decidir el fondo basta, porque la diferencia que se discute es de 2 a 4 veces.

## 3. La prueba con gránulos chilenos (`experiments/_s158_audit_r2/granulos/`)

Workflow de sólo lectura (runs 39641637298 y 39642919404, autenticado sólo con `EARTHDATA_TOKEN`). Para cada pasada
baja el mismo gránulo VIIRS 750 que usó nuestro record, remuestrea M13 y M15 por interpolación lineal a una grilla de
67 × 67 celdas de 750 m con la esquina de la grilla de 375 m que MIROVA usa en sus TIF (hipótesis del §4.1 de
`docs/DISENO_D17_REMUESTREO_UTM.md`), corre el oráculo con una caja por defecto (cumbre 7 × 7, anillo 21 × 21) y corre
también la función de producción sobre el mismo gránulo. 10 de 14 pasadas procesadas; las 4 restantes quedan SIN DATO: las 3 del 2026-10-18
porque CMR ya no las sirve (§4, R2-13), y la de Isluga del 2026-10-12 porque el probe no la encontró aunque, según el
verificador, CMR sí la tiene (causa sin explicar).

| pasada (UTC) | MIROVA NRT | oráculo (grilla y caja por defecto) | producción, mismo gránulo | lectura |
|---|---|---|---|---|
| Láscar 2026-10-08 05:42 | 0,36 MW a 0,75 km | 1 px, 0,33 MW | 1 px, **0,0 MW** | el fondo; reproduce |
| Chillán 2026-10-10 05:54 | 13,13 MW a 1,06 km | 5 px, 12,37 MW | 2 px, 10,48 MW | fondo y conteo; reproduce |
| Villarrica 2026-09-19 05:48 | 0,45 MW a 1,06 km | 2 px, 0,47 MW | 1 px, 0,23 MW | fondo y suma; reproduce |
| Láscar 2026-09-26 05:48 | 0,74 MW a 1,5 km | 0 px (1 px 0,82 MW con vecino más cercano o grilla movida media celda) | 1 px, 0,49 MW | grilla e interpolador |
| Chaitén 2026-10-06 05:30 | 0,18 MW a 0,0 km | 0 px (1 px 0,21 MW con vecino más cercano o grilla movida) | 1 px, 0,21 MW | grilla e interpolador |
| Cordón Caulle 2026-10-10 05:54 | 1,19 MW a 7,83 km | 0 px (1 px 0,79 MW a 7,8 km si el anillo usa umbrales de cumbre) | 0 px | ROI propia del volcán |
| Cordón Caulle 2026-10-16 05:42 | 0,61 MW a 7,65 km | 0 px (1 px 0,67 MW a 7,8 km con anillo sensible) | 2 px, 0,02 MW (otro objeto, junto al centro) | ROI propia del volcán |
| Tupungatito 2026-08-21 05:48 | 0,19 MW a 5,03 km | 0 px en todas las variantes | 1 px, 0,0 MW | no explicado |
| Tupungatito 2026-03-01 05:36 (sin alerta de MIROVA; caso brief) | sin fila V750 | 0 px | 1 px, 0,0 MW | coherente |
| Llaima 2026-10-10 05:54 (RUTINA, control negativo) | 0 | 0 px en todas las variantes | 0 px | control limpio |

Variantes: `granulos/analizar_variantes.py` (interpolador lineal, vecino más cercano y cúbico; grilla movida ±375 m en x
e y; anillo con umbrales de cumbre). Figuras para revisar a ojo: `granulos/figuras/*.png`.

**Lo que decide**: de las 8 pasadas con alerta de MIROVA y gránulo, el código con la configuración por defecto detecta 3,
y en las tres su magnitud cae a menos de 10 % de la de MIROVA, y la de producción no. El verificador lo reprodujo con
un port, una reproyección y un remuestreo propios (0,328, 12,367 y 0,474 MW, `verificador/va/`), y advirtió que
el acierto de Láscar 10-08 es frágil: con otras triangulaciones del fondo va de 0,19 a 0,33 MW (0,54 a 0,91 de MIROVA).
En dos de las cinco no reproducidas (Láscar 09-26, Chaitén 10-06) producción sí publica y el código no: la detección
débil no está resuelta por ninguno de los dos lados. **Lo que no decide**: la grilla de 750 m es una hipótesis; las alertas débiles dependen de ella al
nivel de media celda, así que esta prueba no identifica el remuestreo. Dos limitaciones más: la caja por defecto no es
la de MIROVA en todos los volcanes, y el fondo del oráculo lleva la banda de triangulación del §2 (en Láscar 10-08,
de 0,19 a 0,33 MW según la triangulación, porque es un solo píxel).

## 4. Hallazgos nuevos de esta ronda

Gravedad del auditor; el veredicto del verificador con contexto limpio va en la columna V (§5).

| id | hallazgo | dónde | G | V |
|---|---|---|---|---|
| R2-1 | El fondo de anillo con recorte deja en 0 MW y oculta 595 cúmulos de cumbre V750, 64 de ellos alertas de MIROVA de la misma pasada (todas bajo 1 MW) | `ra1/` | 5 | VER §5 |
| R2-2 | La geolocalización MODIS corre los píxeles hacia el nadir: `scipy.ndimage.zoom` ignora el desfase de la grilla de 5 km (promedio +0,94 km a 20-40° y +1,66 km a 40-55° en los records, 2 a 3,6 km de un solo lado del barrido; ~0 en VIIRS). Afecta la clase cumbre o escena, el fondo y la distancia | `pipeline/process_modis.py:385-396`; `m2/02_*`, `m2/03_*` | 4 | VER §5 |
| R2-3 | `single_pixel_mode` publica el máximo por píxel en cúmulos de hasta 3 píxeles; el código suma todos los alertados | `pipeline/single_pixel_mode.py:94-133`; `ra1/spm_razon.py` | 3 | VER §5 |
| R2-4 | Nuestro conteo de píxeles cae con el ángulo y el de MIROVA no: la magnitud publicada cae hasta 0,5 veces | `ra2/02_*` | 3 | VER §5 |
| R2-5 | El fondo de anillo es 7 a 19 % más caliente que el fondo por píxel de MIROVA en Isluga, Láscar y Copahue | `ra2/` | 3 | VER §5 |
| R2-6 | MODIS publica 0 MW con cúmulo de cumbre por el mismo fondo de anillo y recorte (37 de 619 records con píxeles; 9 con alerta de MIROVA) | `m2/04_*` | 3 | VER §5 |
| R2-7 | El tope de cordura de `store.py` se aplica antes de normalizar `t_max_i04_k` a `t_max_k`: en VIIRS 375 anula sin mirar la temperatura (hoy 0 casos; es el escenario de la erupción más grande) | `pipeline/store.py:551-557` | 3 | VER §5 |
| R2-8 | La métrica M aprueba un placebo de ganancia 1,2 con la calibración de la adenda | `rb/05_*` | 3 | VER §5 |
| R2-9 | Cero gránulos = «Cobertura: completa» | `rb/03_*` | 3 | VER §5 |
| R2-10 | VIIRS 750 diurno rechazado entero; 3 de 3 protegidas diurnas de Chillán sin record | `rb/06_*` | 3 | VER §5 |
| R2-11 | `fillmissing2` = lineal sobre Delaunay; ningún port en Python es vara del VRP al 1 % | `oraculo/` | 2 | VER §5 |
| R2-12 | Todo el corpus fechado se procesó después del merge de K: 0 de 71.968 records con `processed_utc` anterior al 2026-10-18 09:57 UTC (2.843 records sin sello). Una división «antes y después de K» por fecha de observación no separa detectores | medido en esta sesión; `ra2/07_regimen_records.py` | 3 | VER §5 |
| R2-13 | Hoy CMR devuelve 0 gránulos de todo el día 2026-10-18 (todo VIIRS y MODIS) y del 19-oct (VIIRS), en Standard y NRT; producción procesó los del 18 ese día. El 10-12, que el probe dio vacío, sí está en CMR | `granulos/run_39642919404/`; `verificador/vb/` | 3 | VER §5 |
| R2-14 | El segundo pase V750 recaptura sin compuerta lo que la compuerta rechazó; 1.257 records V750 sólo por el segundo pase | `rb/01_*` | 2 | VER §5 |
| R2-15 | La cita «Coppola 2024 L1129 literal» que sostiene el kernel local de fondo (D8) es del modelo de dos componentes, no del fondo del VRP | `a113/` H-R2-1 | 2 | marcado |
| R2-16 | 411 de 2.934 pasadas nocturnas 2025 del OSF (14 %) sin record nuestro a menos de 30 min (Cordón Caulle 84 de 436) | `ra2/` H4 | 2 | sin verificar |
| R2-17 | Las tres vistas del tablero coinciden hoy en efecto (0 diferencias sobre 74.811 records), con divergencias latentes en el texto | `m2/05_tres_vistas.js` | 1 | sin verificar |

## 5. Verificación con contexto limpio

Dos verificadores (Opus) que no encontraron nada de lo que verifican; recibieron sólo título, ubicación y gravedad, y
cada veredicto se apoya en una medición propia por otro camino. Informes: `experiments/_s158_audit_r2/verificador/va/`
y `vb/`. La columna V del §4 se lee aquí; G es la gravedad del verificador.

| hallazgo | veredicto | G | qué cambió |
|---|---|---|---|
| R2-1 (fondo y recorte, 595 ceros) | CONFIRMADO; cruce con MIROVA CON MATIZ | 3 | 64 alertas de la misma pasada, 0 protegidas (no 96 y 11); bajó de 5 a 3 por eso |
| R2-2 (geolocalización MODIS) | CONFIRMADO CON MATIZ | 3 | cuatro caminos (diccionario L1B C7 p. 100 renderizado, código, pareo con VIIRS 375 de la misma noche, lado del barrido): el corrimiento es **asimétrico**, 2 a 3,6 km de un lado del barrido sobre 25° y casi nulo del otro; el +0,94/+1,66 era el promedio de los dos lados |
| R2-3 (`single_pixel_mode`) | CONFIRMADO | 3 | también en VIIRS 375 (2.364 de 7.225) y MODIS (153 de 512), suma/publicado mediana 1,35 y 1,37 |
| R2-4 (conteo con el ángulo) | CON MATIZ | 3 | vale para VIIRS 375; en MODIS el Npix de MIROVA sube con el ángulo |
| R2-5 (anillo más caliente) | CON MATIZ | 2 | no es uniforme: Llaima 0,95 y Chillán 0,89 salen más fríos |
| R2-6 (MODIS en 0 MW) | CONFIRMADO | 3 | 9 alertas de MIROVA en la misma pasada, una de 1,04 MW |
| R2-7 (tope de cordura) | CONFIRMADO, latente | 2 | probado con `append_record` real en carpeta temporal; 0 de 74.811 records tocados hoy |
| R2-8 (placebo) | CONFIRMADO CON MATIZ | 3 | la adenda **está** sellada (D-27); rige la simétrica, que deja pasar al placebo |
| R2-9 (cero gránulos) | CONFIRMADO | 3 | variante propia: geolocalización vacía o día parcial también dan «completa» |
| R2-10 (diurno) | CONFIRMADO CON MATIZ | 3 | medición propia en los 11 Tier A: 3 alertas diurnas protegidas sin record, las 3 de Chillán; las nocturnas tienen record en 94 de 94. Es la decisión D-10 con flag, no un defecto silencioso |
| R2-11 (`fillmissing2`) | CONFIRMADO, matiz menor | 2 | port propio: 65 fondos en 300 triangulaciones, uno igual al OSF; «ningún port» vale mientras no se conozca la regla de MATLAB |
| R2-12 (todo el corpus es K) | CONFIRMADO | 2 | los 38 `codigo_sha` descienden de `34cea39e`; marca A113 puesta en CLAUDE.md |
| R2-13 (CMR sin gránulos) | CON MATIZ | 3 | el 18-oct, más amplio (todo VIIRS y MODIS 6.1) y también el 19-oct en VIIRS; el **12-oct no se reproduce**: CMR público sí devuelve los gránulos de Chaitén e Isluga de producción. Por qué el probe no los encontró queda sin explicar |
| R2-14 (segundo pase sin compuerta) | CONFIRMADO | 3 | la divergencia con MIROVA es la compuerta del primer pase (D22): el `.m` no tiene compuerta de temperatura en ningún pase |
| prueba con gránulos | CON MATIZ | 3 | reproducido con port, reproyección y remuestreo propios; son 8 alertas, no 7; Láscar 10-08 frágil al fondo |

**Hallazgos propios de los verificadores**

- **VA-1 (G3)**: los cúmulos de cumbre en 0 MW salen del segundo pase en los tres sensores (VIIRS 750 594 de 595, MODIS
  37 de 37, VIIRS 375 270 de 271). El efecto de cambiar el fondo y de quitar la compuerta hay que medirlo junto.
- **VA-2 (G2)**: VIIRS 375 también tiene 271 cúmulos de cumbre en 0 MW ocultos; no se parearon con MIROVA.
- **VA-4 (G1)**: en la matriz, `BOX == 1` es un bloque de 21 × 19, no 21 × 21; en la prueba con gránulos no cambia nada.
- **VB-1 (G2)**: un L1B sin su geolocalización se descarta en silencio y la cobertura dice «completa»; pasa: el 20-oct
  CMR tenía 72 MOD021KM NRT contra 68 MOD03 y 67 VNP02MOD_NRT contra 64 VNP03MOD_NRT.
- **VB-2 (G2)**: `experiments/_s157_prereg_d25/evaluar_d25.py:79` deja la calibración original por defecto y las líneas
  492-493 dicen que la simétrica «requiere el sello», que ya existe.
- **VB-3 (G2, latente)**: la rama diurna apagada no tiene rechazo por reflejo solar y usa K1 diurno de -0,6 contra -0,5
  del código.
- **VB-4 (G2)**: huecos de producción el 13-oct (11 records VIIRS 375) y el 20-oct (25 contra ~50 de un día normal); el
  13-oct MIROVA tampoco tiene la noche.

## 6. Comparación con la primera ronda

**Dónde coinciden.** Las doce afirmaciones del brief se sostienen en lo esencial: el fondo de anillo con recorte, los
cúmulos de cumbre en 0 MW, la caída con el cenit por conteo, el segundo pase siempre y en toda la escena, cero
gránulos como cobertura completa, el hueco del A/B de D25, el placebo, el escalón del OSF sobre 50° (los mismos 8.239
de 34.250), el rechazo diurno con las mismas 3 protegidas de Chillán, y que MIROVA cuenta píxeles. El meta-auditor
reconstruyó por camino propio los números centrales de la primera ronda y los reprodujo exactos (`m1/INFORME.md` §1).
También coincide que K1 casi no decide (la primera ronda lo midió en datos; esta, con mutaciones sintéticas).

**Dónde no coinciden, y por qué.**

| tema | primera ronda | segunda ronda | por qué difieren |
|---|---|---|---|
| precisión del oráculo | «VRP a 0,09 %» | ±1,3 a 1,4 % según la triangulación | la primera usó una triangulación cercana sin saber que había 67; ninguna de las dos rondas puede reproducir la de MATLAB sin MATLAB |
| «la brecha entera es el fondo» | dicho de Etna (N = 1) | cierto en Etna; en VIIRS 375 el fondo explica ~12 % y el resto es conteo; en los gránulos chilenos explica la mayor parte donde el código detecta | la primera convirtió una necesidad en causa general (M1 H4) |
| cúmulos en 0 MW | 235 de 855 nocturnos | 595 de 2.359 | ventanas y denominadores distintos (la primera, una ventana; la segunda, el corpus completo); M1 reprodujo el 235 de 855 con la definición de la primera. Las dos dicen 25 a 27 % |
| «0 noches perdidas» | F3-H1 | 55 de 266 noches con alerta V750 de MIROVA quedan sin ningún V750 visible; la investigación hermana #887 cuenta 1 noche sin ninguna publicación en todos los sensores | unidad distinta: noche sin el sensor contra noche sin nada. Las tres cuentas son compatibles |
| la compuerta de 3 K | «vacía el primer pase; 19 de 67 salen sólo del segundo pase» como causa | el acople existe (sintético), pero atribuir los records a la compuerta es SIN DATO | el record no guarda la BT del píxel recapturado (M1 H4 dice lo mismo) |
| el placebo | D = 1,10·K da MEJORA con la calibración que rige | lo mismo con g = 1,2 | coinciden; el auditor de esta ronda creyó la adenda sin sello y el verificador lo corrigió: **aquí la primera ronda tenía razón** |
| causa del hueco del 18-oct | «el Standard todavía no los traía y el NRT ya no» | los records del 18-oct son Standard procesados ese mismo día (M1 H2) y hoy CMR no devuelve ningún gránulo de ese día ni del 19 (R2-13) | la primera escribió una hipótesis como hecho de NASA; la causa sigue sin identificar (NASA retiró o no reindexó esos días) |
| régimen «antes y después de K» | ventana K desde el 2026-09-18 | todo el corpus se procesó con K (R2-12); M1 H7 dice además que la ventana K es innecesariamente estrecha | la frontera de datos de S155 dejó de ser frontera de régimen cuando se reprocesó el histórico (#852, #883) |
| geolocalización MODIS | no se miró | corrida hacia el nadir 1 a 1,7 km (R2-2) | ningún frente de la primera ronda tenía MODIS |
| prueba con gránulos | pendiente | hecha en 10 pasadas | |

**Con las investigaciones hermanas.** #886 (Tupungatito VIIRS 375) llega por su cuenta a que el déficit es sobre todo
el fondo de anillo y a que las dos protegidas de #864 son objetos lejanos; esta ronda ve lo mismo en los records (21,6
y 9,4 km, clase `far`). #887 (recall VIIRS 750) descompone las 75 pérdidas en 55 de cráter en 0 MW y 20 sin
detección, la misma partición que R2-1 y la tabla del §3; su frase «MIROVA toma como fondo la media de los vecinos del
píxel (D25)» no coincide con el código de VIIRS 750, que aparta a los vecinos con un halo y los reemplaza por una
interpolación desde fuera del halo. #887 cierra Cordón Caulle 2026-10-10 como #865 «ya explicado»; la prueba con
gránulos agrega que con la caja por defecto el código de MIROVA tampoco lo detecta, y que sí lo detecta con umbrales
de cumbre en el anillo: el mecanismo es la ROI de MIROVA en ese volcán.

## 7. Informe del meta-auditor (resumen; completo en `experiments/_s158_audit_r2/m1/INFORME.md`)

- **Los números de la primera ronda aguantan; fallan la lectura de causa y la propagación.** Reprodujo exactos el
  pareo OSF de F3-H2, el escalón de 50°, el corte de 30 km del OSF, los 235 de 855 y las fracciones del mínimo de
  escena.
- **Instrumentos que no podían fallar**: el control de Etna para K1, mínimos, 3 × 3 y recorte (5 de 8 mutaciones dan
  igual); «k y área iguales, toda la brecha es el fondo» (cierto por construcción); el control «0 de 48» de la compuerta
  de 3 K; «todos los píxeles con bt ≤ t_bg» en los cúmulos en cero (identidad del recorte).
- **Propagación A113 incompleta**: los límites del código (repositorio compacto, escalón de 50°, Etna que no ejercita
  los umbrales) no bajaron a los documentos que dicen «el código manda en VIIRS 750» (CLAUDE.md, MISSION.md, D34); D18,
  D8, D27 y dos memorias sin marca. Lista con archivo:línea en su §3 (U1 a U14).
- **Cuatro definiciones de «alerta de MIROVA»** entre frentes, y pareos de 20, 8, 5 minutos y minuto exacto; sin
  efecto en VIIRS 750, latente en los demás.

## 8. Marcas A113 de esta ronda

El auditor A113 verificó por su cuenta las 22 afirmaciones y las 10 pruebas de la tabla de F2 contra los `.m`, la
matriz, el OSF y el paper renderizado (`experiments/_s158_audit_r2/a113/INFORME.md`). Marcas puestas (formato
«⚠️ **S158 R2**», texto viejo conservado): `CLAUDE.md` (tabla de BIBLIOGRAPHY_SYNTHESIS, kernel de 8 vecinos, A4, A12,
A23), `docs/MISSION.md` (`exclude_zones`, D8 y D9), `docs/MIROVA_DIVERGENCES.md` (D8, D9 S45, D9 S71, D27),
`docs/HYPOTHESIS_LOG.md`, `docs/PREREGISTRO_AB_D1_D2_S135.md`, `docs/MIROVA_DETAILED_CITATIONS.md`, y comentarios en 10
archivos de `tests/` sin tocar ninguna aserción. Quien orquesta agregó una (R2-12, verificada por VA): en `CLAUDE.md`,
la frase «los datos cambian de detector en la observación del 2026-09-18» ya no separa detectores, porque todo el corpus
fechado se procesó con K; las pruebas que leen `CLAUDE.md` siguen verdes (111 de 111). Suite completa después de las marcas: 2.347 pasan, 29 omitidas,
1 xfail, 0 fallas.

Marcas pendientes, con dueño:

- **Bajo A45 (requieren tag y tu sí)**: comentarios en `pipeline/process_viirs_mod.py:481, 881, 1055`,
  `pipeline/detection_context.py:883-898, 974-984`, `pipeline/diurno.py:128`, `pipeline/vrp_regimes.py:39-55` y
  `pipeline/profiles/mirova_equivalent.yaml` (varias líneas).
- **Fuera de git**: `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:142, 248, 249` (los 12 σ / 8 σ de Di Bella como canónicos
  de VIIRS 750).
- **De la lista de M1 sin marcar todavía**: U1 a U4 y U8 a U13 (D34 «Alcance», los límites de F6 en CLAUDE.md y
  MISSION.md, D18, D27 en su segunda mención, la memoria del agente).

## 9. Guía para revisar con tus ojos

Para cada caso: qué abrir, qué debería verse si el hallazgo es cierto y qué si no. Las láminas de MIROVA están en el
repositorio Mirova-v1 (`monitoreo_satelital/imagenes_satelitales/<volcán>/<fecha>/`); las figuras del oráculo, en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_audit_r2\granulos\figuras\`.

1. **Láscar, 2026-10-08 05:42 UTC, VIIRS 750 (el fondo).** Abre en el tablero Láscar, sensor VIIRS 750, esa noche;
   después la lámina de MIROVA
   https://github.com/MendozaVolcanic/Mirova-v1/blob/main/monitoreo_satelital/imagenes_satelitales/Lascar/2026-10-08/05-42-01_Lascar_VIIRS750_Latest.png
   y la figura `Lascar_2026-10-08_0542.png`. **Si el hallazgo es cierto**: MIROVA marca un píxel en el cráter con 0,36
   MW; el tablero no muestra ningún punto VIIRS 750 en esa pasada (está en 0 MW y oculto); la figura del oráculo
   marca el mismo píxel, a 0,75 km, con 0,33 MW. **Si no**: el tablero muestra un punto con magnitud, o la lámina de
   MIROVA pone el píxel en otro lugar.
2. **Nevados de Chillán, 2026-10-10 05:54 UTC, VIIRS 750 (conteo y fondo).** Lámina
   https://github.com/MendozaVolcanic/Mirova-v1/blob/main/monitoreo_satelital/imagenes_satelitales/Nevados_de_Chillan/2026-10-10/05-54-02_Nevados_de_Chillan_VIIRS750_Latest.png
   y figura `NevadosDeChillan_2026-10-10_0554.png`. **Si es cierto**: la mancha caliente de MIROVA abarca varios
   píxeles (el oráculo marca 5 y da 12,4 MW contra 13,1); el tablero muestra 10,5 MW con 2 píxeles. **Si no**: la
   lámina muestra uno o dos píxeles, y la diferencia de magnitud no vendría del conteo.
3. **Cordón Caulle, 2026-10-10 05:54 UTC, VIIRS 750 (la ROI de MIROVA).** Lámina
   https://github.com/MendozaVolcanic/Mirova-v1/blob/main/monitoreo_satelital/imagenes_satelitales/Puyehue_Cordon_Caulle/2026-10-10/05-54-02_Puyehue_Cordon_Caulle_VIIRS750_Latest.png
   (y la de VIIRS 375 de la misma hora) y figura `PuyehueCordonCaulle_2026-10-10_0554.png`. **Si es cierto**: MIROVA
   marca un píxel a ~7,8 km al norte de su centro, que en la figura del oráculo es el punto caliente del borde norte del
   recuadro blanco; nosotros no publicamos nada en VIIRS 750 esa pasada. **Si no**: el píxel de MIROVA está en otro
   rumbo, y la explicación por la ROI cae.
4. **Tupungatito, 2026-09-28 05:18 UTC, VIIRS 375 (#864).** En el tablero, el record de esa pasada es `far` a 21,6 km.
   **Si es cierto** que no es del cráter: la serie «Last Month» de MIROVA de esos días tiene un marcador gris lejano
   esa noche (la investigación hermana #886 lo leyó a 22,6 km). **Si no**: el marcador está bajo 7 km y la alerta sí era
   del cráter.
5. **MODIS a cenit alto (la geolocalización).** En el mapa del tablero, elige una noche de Láscar o Isluga con un punto
   MODIS de cumbre a más de 40° de cenit (el popup y el campo `sensor_zenith_deg` lo dicen) y compáralo con el punto
   VIIRS 375 de la misma noche. **Si es cierto**: el punto MODIS queda corrido 1 a 2 km respecto del cráter hacia el
   lado desde donde miraba el satélite (`sensor_azimuth_deg`), y el VIIRS no. **Si no**: los dos caen sobre el cráter,
   o el MODIS se corre en cualquier dirección.

## 10. Decisiones para Nicolás

Todas tocan `pipeline/` o el evaluador y van, cada una, con tag defensivo, A/B pre-registrado y tu «sí» (A45).

| # | decisión | recomendación |
|---|---|---|
| 1 | Arreglar los instrumentos antes de cualquier A/B: cero gránulos y L1B sin geolocalización como falla (R2-9, VB-1); la calibración por defecto del evaluador de D25 (VB-2); y un control placebo obligatorio en la métrica M (R2-8) | **primero**, en un PR chico; sin esto un A/B puede dar «completo» y «MEJORA» sin medir nada |
| 2 | El A/B de D25 | no leer su veredicto; los días 18 y 19 de octubre no se pueden reponer mientras NASA no los sirva (R2-13); decidir si se evalúa sin ellos o se repite en otra ventana, y agregarle un brazo con el fondo del código |
| 3 | El fondo y la suma del código en VIIRS 750 (interpolado bajo los alertados, sin recorte, suma de todos, sin `single_pixel_mode`), **junto** con quitar la compuerta de 3 K del primer pase (VA-1) | A/B pre-registrado que cuente las dos caras: alertas de MIROVA recuperadas y negativos limpios despegados del cero. Es la pieza que más acerca, según la prueba con gránulos |
| 4 | D17, fase 0: identificar la grilla de 750 m y el interpolador | extender la prueba con gránulos a unas 40 pasadas (alertas débiles y RUTINA), con las variantes de grilla e interpolador pre-registradas, antes de escribir código de remuestreo |
| 5 | La ROI de MIROVA en Cordón Caulle y Tupungatito | medirla en sus TIF y en la `Distancia_km` (cuantizada a la celda, D15) antes de adoptar umbrales de cumbre fuera del cráter; es también una buena pregunta para el correo a Coppola cuando decidas enviarlo |
| 6 | Geolocalización MODIS (R2-2) | leer la geolocalización de MOD03, que ya se baja; arreglo de bajo riesgo pero cambia posiciones y clases, así que con A/B |
| 7 | VIIRS diurno (D-10) | sigue tuya; el código trae la rama diurna (K1 -0,5, 15 σ, reflejo solar bajo 12°) y nuestra rama apagada usa -0,6 y no tiene filtro de reflejo (VB-3) |
| 8 | Marcas A113 bajo A45 (§8) | ponerlas en el mismo PR que toque cada archivo |

## 11. Lo que esta ronda no pudo medir

- Las 3 pasadas del 2026-10-18 (CMR no las sirve hoy, R2-13) y la de Isluga del 2026-10-12 (el probe no la encontró).
- La grilla de 750 m y el interpolador del remuestreo de MIROVA: la prueba con gránulos los usa como hipótesis.
- La ROI de MIROVA en cada volcán chileno (en especial Cordón Caulle y Tupungatito).
- El efecto de despegar del cero en los negativos limpios con el fondo del código sobre gránulos reales (hace falta un
  conjunto de pasadas RUTINA más grande que el control de esta prueba).
- La triangulación exacta que usa MATLAB (no hay MATLAB ni Octave en la máquina).
- La geolocalización MODIS record a record (requiere reprocesar con MOD03).
