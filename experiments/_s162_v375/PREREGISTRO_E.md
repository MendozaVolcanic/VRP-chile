# Pre-registro V375-E (S162): el paquete del código de MIROVA en VIIRS 375 contra producción (K)

> Escrito antes de que exista el paquete en `pipeline/` y antes de ver ningún resultado suyo. Lo que cambie después del
> sello va en una adenda fechada al final. Es el pre-registro de una ADOPCIÓN posible: la implementación, el sello, el
> tag defensivo y el despacho pasan por A45 (el sí de Nicolás, cada uno). Estado: **BORRADOR, sin sellar**; depende de
> PD1 (la ROI, V375-C), de PD3 (la vía de proceso en `pipeline/` detrás de flag) y del evaluador común de la sesión del
> instrumento (programa §8.3: placebo y comparador d′ fuera de `evaluar_d25.py`). Pasó por el verificador limpio junto
> con B y C (`verificador/INFORME.md`); sus correcciones a E están en §3, §4 y §5.4.
>
> ⚠️ **Adenda 2 (S166, §8, SIN SELLAR)**: la vía ya está en `main` (#921, apagada) y Nicolás decidió medir la regla de
> posición como tres brazos (radiante, cercano y pico). La adenda agrega esos brazos, las 330 pasadas en que MIROVA
> publicó una fuente lejana, una regla de posición escrita antes de ver los datos, y corrige el paso 1 donde ya no
> describía la vía de #921. Con la regla de hoy (radiante) el veto (a) del §5.4 caería por 4 protegidas que K publica.

## 1. Pregunta

Si VIIRS 375 pasa a calcularse con el código de MIROVA (el mismo que en 750, con bandas I, la grilla de 134 x 134 y la
caja que salga de PD1), ¿el tablero se parece más a MIROVA que hoy, en las dos direcciones, sin perder ninguna alerta
protegida?

**Por qué.** Producción ve casi todo lo que MIROVA ve en 375 (recall 96,8 %), pero muestra la magnitud a dos tercios
(0,651 [0,436; 0,848] en la muestra de S159) y publica en 3,85 % de las noches limpias. El port, sobre las mismas
pasadas, dio la magnitud al centésimo (1,000 [0,966; 1,019], n 61) y apagó dos de cada tres puntos de cumbre en noches
sin nada. Y en las pasadas oblicuas el problema es doble: MIROVA también pierde magnitud cuando mira de lado, pero K
pierde más. Medido de antemano sobre la población congelada de S159 (`linea_base_curva_salida.txt`, pares de la misma
noche y volcán con 15° o más de diferencia de cenit, las dos pasadas publicadas): la pasada más oblicua sobre la menos
oblicua da **0,778** en MIROVA y **0,573** en K; la razón doble K / MIROVA es **0,766 [0,722; 0,861]** (215 noches), y
sobre 50° de cenit **0,733 [0,608; 0,861]** (153). La meta del paquete no es aplanar la curva (MIROVA no es plana) sino
**caer igual que MIROVA**: razón doble 1.

## 2. Brazos

| brazo | qué es |
|---|---|
| **K** | producción (detector K, #850), lo publicado; control |
| **P** | el paquete: vía de proceso «código MIROVA» de VIIRS 375 con la caja de PD1, el predicado de cumbre del tablero |
| P-def | el paquete con la caja M14 (la de S159), para separar el efecto de la ROI |
| P-sinfiltro | el paquete publicando todo lo que detecta (decisión 5 del programa: medir sin el predicado de cumbre) |
| PLACEBO | K con el VRP x 1,2 (programa §2, obligatorio): tiene que dar 0 discordantes en P1 y P2, y d′ = 0 |

Lo que el paquete acopla y se prueba junto (programa §7): remuestreo a la grilla fija (D17), Test 1 como alerta, ventana
de 3 x 3 con la celda central, umbrales del `.m`, sin compuerta de 3 K, segundo pase con la regresión recalculada,
fondo por `fillmissing2` bajo el halo, sin recorte, suma de todos los alertados, sin modo de un píxel ni tope D9.
La atribución pieza a pieza no es de aquí: va en ablaciones locales sobre las grillas guardadas.

## 3. Tres pasos, en orden (decisión 3 del programa)

1. **Equivalencia (PD3)**. La vía de `pipeline/`, corrida sobre los gránulos del lote de B y C (859 pasadas con grilla
   guardada), reproduce al port de `brazos.py` pasada por pasada: misma cantidad de alertados y VRP a 1e-3 MW en el
   99 % o más, **la publicación idéntica en el 100 % de las pasadas** y las 80 protegidas idénticas. Si no, el paquete
   no es el código y no se sigue. (El verificador mostró que tolerar 1 % de pasadas distintas, ~8 de 859, es del tamaño
   del efecto que B mide en negativos: por eso la publicación no tiene tolerancia.)
2. **Lectura retrospectiva** sobre la unión de B y C (marco de S159, del 2026-04-01 al 2026-10-21, sin el 12, 13 y 17 a
   20 de octubre), con los pesos de `PREREGISTRO_B.md` §3. Ventanas T y O por separado, O1 y O2 (#535) por separado.
3. **Sombra prospectiva confirmatoria** desde el **2026-11-03** (ventana P del programa, sin Suomi NPP: otro régimen),
   como perfil aparte con su `data_subdir`, sin tocar la vista operacional, hasta 30 noches o 40 alertas de MIROVA que
   decidan, lo que llegue último. La referencia se congela por hash en cada corte de lectura.

## 4. Controles (antes de leer)

Los de `PREREGISTRO_B.md` §4 (cobertura contra la referencia de MIROVA del instrumento, SIN DATO fuera del
denominador, K re-corrido, control positivo, nulo, NUNCA, PLACEBO), y para la curva de cenit (`curva_cenit.py`,
probados sobre K en `linea_base_curva_salida.txt`):

- **Nulo de cenit parecido**: en la misma noche y volcán, el par de pasadas con alerta de MIROVA que difieren en menos
  de 5° de cenit, **ordenado con la misma regla que la lectura** (la de menor cenit primero). La razón doble de ese nulo
  tiene que contener 1 (en K: 1,162 [0,940; 1,626], 37 noches); si no, NULO SESGADO y la curva no se lee. En el borrador
  el orden del nulo se sorteaba y el verificador mostró que así no puede fallar (d y 1/d equiprobables).
- **Sesgo de plataforma** (que ningún nulo de pares ve): mediana de nuestro VRP sobre el de MIROVA por plataforma; SESGADO
  si dos difieren en más de un factor 1,25 con los IC sin solaparse. En K: NOAA-20 0,66, NOAA-21 0,64, Suomi NPP 0,61, sin
  sesgo. Casi todos los pares oblicuo y menos oblicuo son de plataformas distintas (214 de 215). El nulo de 750 (los mismos pares ordenados por hora) **no sirve en
  375**: el VRP de MIROVA baja de una pasada a la siguiente de la misma noche (mediana 0,818, n 365), y el orden por
  hora cae casi igual que el orden por cenit (0,786 contra 0,778).
- **Ganancia pareja** (x 1,2 a todas las pasadas): la razón doble no se mueve (en K: 0,766 → 0,766).
- **Ganancia que crece con el cenit** (1 + 0,01 por grado sobre 20°): la razón doble tiene que subir (en K: 0,766 →
  0,988). Si no se mueve, el instrumento no ve el cenit.

## 5. Lecturas y regla de adopción

### 5.1 Detección (P1, P1b, P2, silencio, MISSION)

Las de `PREREGISTRO_C.md` §5 y `PREREGISTRO_B.md` §5, de P contra K: P1 veto (ninguna protegida que K publica puede
perderse; lectura A, regla SN; la protegida de cráter de V375-A al lado), P1b en las dos direcciones, P2 por la prueba
de signos por bloque noche-volcán (D-45), silencio en negativos limpios con la cota de Wilson sobre n efectivo, MISSION
con la cota honesta del estrato de cero eventos.

### 5.2 Magnitud (M)

La regla sellada de D-27 sobre d = |log10(P / MIROVA)| − |log10(K / MIROVA)| y el comparador de ganancia pareja de
D-28 (d′ con ĝ = mediana de log10(P / K)), con la calibración de D-30 y D-32, **tomados del evaluador común de la
sesión del instrumento** (no se reimplementan aquí). Por tramo de 10° de cenit, por volcán y por canal. El placebo da
d′ = 0 por construcción; si no, el instrumento está roto.

### 5.3 La curva de cenit

Razón doble D por noche (`curva_cenit.py`), condicionada (las dos pasadas publicadas, DECIDE) y sin condicionar (no
publicar = 0, informa). Veredicto: SIN SUSTRATO con menos de 8 noches en la lectura o en el nulo; NULO SESGADO si el
nulo no contiene 1; **CAE MAS QUE MIROVA** si el IC de la mediana de D queda entero bajo 1; CAE MENOS QUE MIROVA si
queda entero sobre 1; **REPRODUCE LA CURVA** si lo contiene y la mediana está en [0,8; 1,25]; NO RESUELTO en otro caso.
Se informa al lado si la curva de MIROVA misma se separa del nulo (en la ventana O no se separa: 0,857 [0,707; 1,077]
contra un nulo de MIROVA de 0,947); esa marca no bloquea, porque D compara las dos caídas en los mismos pares. Por tramo de la
pasada oblicua (menos de 50°, 50° o más) y por volcán (Chillán aparte, V375-F).
Vara de K, medida antes: **CAE MAS QUE MIROVA**, 0,766 [0,722; 0,861].

### 5.4 Regla de adopción del paquete (para PD4, decide Nicolás con A45)

El paquete P **cumple** si, en la lectura retrospectiva Y en la sombra prospectiva: (a) P1 no pierde ninguna protegida
que K publica (lectura A, todos los canales: decisión 4 del programa, «decide la lectura A»); (b) P2 contra K da GANA o EMPATE (no PIERDE ni BLOQUEA) y el silencio no da ENCIENDE DE MAS; (c) M da
MEJORA con d′ dando MEJORA (no sólo una ganancia) o, si d no mejora, no EMPEORA; (d) la curva da REPRODUCE LA CURVA,
o al menos el IC de D del paquete queda entero sobre el de K. Si (a) falla en cualquiera de las dos, **no cumple**.
Si la retrospectiva cumple y la sombra no tiene sustrato a las 30 noches, la decisión es de Nicolás con lo que haya.

**Riesgo conocido para (a), dicho antes de medir.** En el lote de S159 el port pierde 3 protegidas que K publica, las
tres sólo OCR (dos de Tupungatito y una de Isluga), y las pierden los diez brazos de ROI por igual. V375-C las saca de
la elección de caja (no las causa la caja), pero aquí siguen siendo veto. Si en el lote nuevo aparecen más del mismo
tipo, (a) falla por ellas aunque la etiqueta de protegida de cráter de V375-A diga que son fuentes lejanas: cambiar la
vara para esas filas es una decisión de Nicolás, con la etiqueta de V375-A delante, no de este pre-registro.

## 6. Lo que este pre-registro no hace

No implementa nada (PD3 es otra tarea con su propio pre-registro de implementación y A45). No mide el día. No mide
Chillán sobre 3 MW como pregunta propia (V375-F, después de esto). No mezcla la ventana P con la O: son regímenes
distintos (cese de Suomi NPP).

## 7. Adenda 1 (2026-10-26, S164): PD1, dependencias cumplidas y la vara de la equivalencia

Escrita antes de que exista la vía de 375 y antes de ver ningún resultado del paquete. Sigue en **BORRADOR, sin sellar**.

1. **PD1 decidida**: caja **C13 en todos los volcanes**, centrada en el cráter de `volcanoes.yaml` (coordinadora S164,
   bajo D-48). El brazo P usa C13; P-def sigue con M14 para separar el efecto de la ROI. Base: V375-C
   (`resultado_run40116289866/INFORME.md`) y la etiqueta de cráter (`evaluar_con_crater_salida.txt`): las 6 protegidas
   que C13 pierde, igual que M14, son sólo OCR de Suomi NPP antes del hito y ninguna es de cráter.
2. **Dependencias que ya están en main**: evaluador común con placebo y d′ (#904 y #905), alerta y protegida por pasada
   y protegida de cráter (#903), y la vía «código MIROVA» (#907, merge cff07d173, `pipeline/mirova_v750_codigo.py`, con el
   flag apagado). Esa vía trae el detector del `.m` de 750 m y **no** los números de 375. Llevarla a 375 es la tarea de
   implementación (PD3) y tiene su propio pre-registro y A45.
3. **La vara del paso 1 (equivalencia) cambia en el fondo de 1 a 4 píxeles.** La vía de main rellena con el
   `fillmissing2` de MATLAB y `brazos.py` con el port viejo, que en las escenas de 1 a 4 píxeles da otro fondo en 137 de
   422 (hasta 0,83 relativo; `o2_375/comparar_matlab_375_salida.txt`). Por eso la equivalencia del VRP se mide contra
   `brazos.py` con el fondo de MATLAB en esas escenas: `o2_375/matlab_v375.json`, la salida de MATLAB, que coincide con
   la regla de relleno en 422 de 422 (`o2_375/verificador_matlab/INFORME.md`, CONFIRMADO). Sobre 4 píxeles se mide
   contra `brazos.py` tal cual. Si ahí no calza, se mira primero el relleno. La exigencia de **publicación idéntica en
   el 100 %** no cambia. Con ese fondo la publicación de los diez brazos ya resultó idéntica
   (`o2_375/evaluar_con_matlab_salida.txt`: P1, P2, recall y VEREDICTO B iguales).
4. Cada record de la vía lleva `via_codigo_mirova: True` (store.py le salta la geocerca, el filtro por distancia y el
   tope por cúmulo). Un record sin esa marca no entra en la lectura del brazo P.
5. Lo que el riesgo de §5.4 dejaba abierto ya tiene etiqueta: las 3 protegidas de S159 que el port pierde y K publica
   son `ocr_snpp_antes_del_hito`. Igual siguen siendo veto. Cambiar la vara para esas filas lo decide Nicolás.

## 8. Adenda 2 (2026-10-28, S166): los tres brazos de posición y las pasadas lejanas de MIROVA

Estado: **BORRADOR, SIN SELLAR.** Autor: sesión hija de VIIRS 375 de la coordinadora S166. Código, listas y pruebas en
`experiments/_s162_v375/e_adenda2/`.

**Qué se sabía al escribirla (dicho para que se pueda descontar).** El resultado de la equivalencia de #921
(`experiments/_s165_v375_via/equivalencia_v375e_salida.txt`: NO EQUIVALENTE, 8 pasadas de publicación distinta, 4 de
ellas protegidas, todas por la regla de posición), la medición de la regla en los tres sensores
(`experiments/_s165_regla_posicion/INFORME.md` y su `verificador/INFORME.md`, rama `loop/activo`) y, del generador de
la lista suplementaria, cuántas de las pasadas lejanas publica K (122 de 330; es un dato de K, el control). **Qué no se
había visto**: ninguna lectura de P sobre el marco (la retrospectiva del §3.2), nada del run de las pasadas lejanas
(no existe todavía) y nada de la sombra. El lector se corrió sólo sobre escenas sintéticas y, para la identidad con la
vía, sobre las 7 grillas de `tests/datos_s165_v375/` midiendo distancias, sin ninguna lectura.

### 8.1 Qué pidió Nicolás y por qué toca a E

Nicolás, 2026-10-27 (programa §7, `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` en `loop/activo`):
«Sí: no fijes la regla todavía; mídela como brazo (radiante, cercano y pico) en los A/B de cada sensor contra lo que
publica MIROVA». El programa agrega que la vara incluye las pasadas en que MIROVA publicó una fuente lejana
(`FALSO_POSITIVO` de la tabla) y que, si un pre-registro está sellado, los brazos entran por adenda antes de ver los
datos. E no está sellado, pero la adenda se escribe igual, separada y fechada, para que se vea qué cambió y cuándo.

En 375 la pregunta no es cosmética: con la regla que tiene hoy la vía (radiante), las protegidas Isluga 2026-06-17
05:06, 2026-09-28 05:12 y 2026-10-03 05:18 y Láscar 2026-10-01 05:18 quedan lejanas y el tablero no las publica; K
publica las cuatro (`pub_prod` 1 en `objetivos_v375_bc.json` y `experiments/_s159/portes/objetivos_portes.json`). O
sea que, sin brazos, el veto (a) del §5.4 caería por ellas antes de medir nada más.

### 8.2 El fenómeno, como geólogo

La regla de posición sólo importa en una escena: un píxel débil junto al cráter y una fuente más radiante lejos (otro
foco del complejo, un borde de nube, un incendio, un salar tibio). La vía ubica el record en el centroide del cúmulo de
la alertada más radiante (**radiante**): si ese cúmulo está fuera del radio interior, el record es lejano y el tablero
calla. Con **cercano** (el alertado más cercano al cráter) el mismo record queda en la cumbre y el tablero publica la
suma de todos los alertados, que en esa escena viene sobre todo de la fuente lejana. Con **pico** (el alertado de
mayor radiancia MIR) manda un píxel solo; difiere de radiante cuando el cúmulo cruza el borde del radio interior (el
centroide adentro y el pico afuera, o al revés).

Lo que MIROVA hace en esa escena no está escrito: el `.m` de VIIRS 750 devuelve la lista de alertados y el VRP sumado,
sin elegir un píxel ni medir una distancia (`MIROVA_VIIRS750_hotspot_detection.m` l. 1; `MIROVA_VIIRS750_VRP.m` l. 1).
La `Distancia_km` que publica sale de una parte del sistema que no está publicada. Por eso se mide (A115): las
alertas que MIROVA publicó a distancia de cráter con una fuente lejana en la escena dicen «cercano»; las pasadas en que
MIROVA publicó la fuente lejana como lejana (`FALSO_POSITIVO` de la tabla) son la misma escena vista al revés, y ahí
lo correcto es no publicar en la cumbre. S165 encontró tres filas de la tabla en esa configuración, dos a favor de
cercano y una a favor de radiante: no alcanza para decidir, y en 375 las pasadas lejanas no se habían mirado (H1 del
verificador de S165).

### 8.3 La vía tal como quedó en #921, contra lo que este pre-registro decía

Comprobado contra `origin/main` (`bd711db63` y `55c95c705`, mismo `pipeline/mirova_v750_codigo.py`, blob
`a9c00eaf`):

| tema | lo que decía E | lo que hace la vía de #921 | consecuencia |
|---|---|---|---|
| dónde vive | §7.2: «llevarla a 375 es la tarea de PD3» | `FAMILIAS["VIIRS375"]` en `pipeline/mirova_v750_codigo.py`, flag `ENABLE_V375_CODIGO_MIROVA` (`thresholds:`, apagado en los tres perfiles), bloque al inicio de `calculate_vrp` de `pipeline/process_viirs.py` | PD3 cumplida |
| caja | §7.1: C13 en el cráter | `caja_v375`: C13 en la celda más cercana al cráter dentro de la ROI1 física de S159; igual a `brazos.caja(..., "C13", ...)` en 2.012 de 2.012 | sin cambio |
| volcán sin grilla | no lo decía | sigue K y el record lleva `via_codigo_mirova: "sin_grilla"` | un record así no entra al brazo P (ya lo decía §7.4 para la marca) |
| almacén | §7.4: le salta geocerca, filtro por distancia y tope por cúmulo | además no calcula `f5_core_vrp_mw` (#921, V165-01) | el tablero publica `pc.vrp_mw`, la suma de todos los alertados (D32) |
| posición | §2: «el predicado de cumbre del tablero»; §3.1 compara la publicación contra `brazos.py` | la vía mide el centroide del cúmulo de la alertada más radiante **desde el cráter**; `evaluar.py` decide con el alertado más cercano **a X0, Y0** | son dos reglas distintas: por eso la equivalencia salió NO EQUIVALENTE en 8 pasadas con máscara idéntica. Lo resuelve §8.6 a |
| fondo sobre 4 píxeles | §7.3: contra `brazos.py` tal cual; «si ahí no calza, se mira primero el relleno» | la vía rellena con la regla de MATLAB en todos los tamaños; `brazos.py` con el port viejo | 40 de 329 fuera de 1e-3 MW, y las 40 calzan a 0,0 con `brazos.py` usando la regla de MATLAB (código independiente de S163). Lo resuelve §8.6 b |

El resto del §2 (bandas I04 e I05, grilla de 134 x 134 a 375 m, coeficiente, umbrales del `.m`, sin compuerta de 3 K,
segundo pase, suma de todos los alertados, sin modo de un píxel ni tope D9) es lo que hace `procesar_grilla` con la
familia `VIIRS375` (docstring y cuerpo, l. 687 a 745).

### 8.4 Qué agrega

1. **Tres brazos de posición sobre la misma detección.** La máscara, el VRP y el tamaño del cúmulo son los de
   `procesar_grilla`; sólo cambia la distancia desde el cráter (`posicion_de`, el mismo ancla que producción) y con ella
   `distance_class`, `primary_cluster.centroid_dist_km` y `final_hotspot_dist_km`. Frontera inclusiva (`summit` si la
   distancia es `inner_radius_km` o menos), igual que la vía.
   - **radiante**: el record de la vía sin tocar (centroide del cúmulo 8-conexo de la alertada más radiante);
   - **cercano**: el alertado más cercano al cráter; a igual distancia, el de menor (fila, columna);
   - **pico**: el alertado de mayor radiancia I4, el mismo que siembra el cúmulo, con el mismo desempate que la vía.
   Cada variante pasa por `store.append_record` y por el predicado del tablero con node, como un record de producción.
2. **Las pasadas lejanas de MIROVA** (`e_adenda2/objetivos_far_v375.py`). Corre la población de S159
   (`experiments/_s159/portes/01_poblacion.py`) con los **mismos insumos congelados** que el marco de B y C (records de
   `533398f8f`, comprobados blob por blob; referencia de Mirova-v1 en los commits `fe2d0a57` y `4ddd5481`, bajada de esos
   commits y no del remoto de hoy), cambiando sólo el filtro de etiquetas para dejar pasar `far_ref`. Control: las
   `pos` y `neg_limpio` de esa corrida son las del marco entrada por entrada (10.087 contra 10.087, todos los campos,
   los dos sensores). Resultado: **330 pasadas VIIRS 375 con gránulo, 0 sin gránulo**, del 2026-04-01 al 2026-10-21
   sin los días excluidos: T 117, O1 131, O2 82 (A104). Dos subclases, porque `banco_paridad.es_fp` cuenta también
   `FALSO_POSITIVO_OCR`, que es etiqueta del scraper (A11), no una publicación de MIROVA:
   - **far_tabla** (329): la pasada trae una fila `FALSO_POSITIVO` del consolidado. Decide.
   - **far_ocr** (1): sólo filas del OCR. Se corre e informa; no decide.
   El 338 del verificador de S165 (`05_far_ref_fuera_del_universo.py`) contaba filas de la tabla sobre la copia de hoy
   de la referencia, sin quitar los días excluidos ni las pasadas con una ALERTA en la misma pasada y sin exigir un
   record nuestro; la etiqueta `far_ref` sobre la copia del marco da 330. No separé cuánto aporta cada diferencia. La lista lleva además las 20
   pasadas del control de vida de B2 (re-mediciones de S162 con su M14 de referencia), con ids desde 29000.
   sha256 (fin de línea LF): `objetivos_far_v375.json` `d968aafe…c46c7d`, `objetivos_run_far_v375.json` (lo que lee
   el run) `4abc0630…51ad47`, población `aff8822a…cd0a7d` (regenerable, no se commitea; copia en
   `D:\vrp-trabajo\temporales\s166_v375e_adenda2\poblacion_far.json`). Salida: `e_adenda2/objetivos_far_v375_salida.txt`.
3. **Un run de sólo lectura** (`e_adenda2/probe-s166-v375e-far.yml`): el mismo `probe_v375.py` de B y C, sin cambios,
   sobre esas 350 pasadas en 14 trozos de 25, que guarda la grilla de cada una. Lo despacha la coordinadora, desde un
   tag, en una rama de disparo que no se mergea (§8.8).
4. **Un lector** (`e_adenda2/leer_posicion_v375e.py`): la vía de `pipeline/` sobre las grillas de los lotes S159, S162,
   S162b y FAR, los tres brazos, y las tres varas del §8.5.

### 8.5 Las varas y la regla de posición (RP)

- **Vara 1, alertas y negativos limpios del marco** (los pesos de `PREREGISTRO_B.md` §3): las lecturas de `evaluar.py`
  (P1, P1b, recall, silencio, MISSION, magnitud) y la prueba de signos contra K, **para cada brazo**, tomadas de
  `evaluar.py` sin copiarlas (el lector lo identifica por sha256 LF, `2126b743…`, y no lo carga si es otro). Además,
  las pasadas que cambian de publicación contra radiante, por nombre.
- **Vara 2, pasadas lejanas** (`far_tabla`, censo, peso 1): cuántas tienen algún alertado en la caja (sin eso, un cero
  no distingue «la escena no ocurrió» de «el brazo no publica de más») y cuántas publica cada brazo y K, por tramo y
  por nombre. Lo correcto es no publicar. **P2-L**: prueba de signos por bloque noche-volcán (D-45) de cada brazo
  contra K, contando como error sólo publicar en una `far_tabla`. `far_ocr` se informa aparte.
- **Vara 3, distancia** (informa): cada brazo medido desde X0, Y0 (el punto de referencia de MIROVA, con el mismo
  objeto elegido desde el cráter) contra la `Distancia_km` de MIROVA, en las alertas de la tabla, en las del OCR desde el
  2026-06-13 (A119) y en las `far_tabla`: mediana de la diferencia y cuántas a una celda (0,375 km) y a 1 km o menos.
  Es diferencia de radios, no de posiciones (A93): sirve para descartar un brazo, no para afirmar que ve lo mismo.
- **Regla de posición (RP), decide**, sobre el marco más las `far_tabla`, con el error de posición = protegida sin
  publicar, alerta bajo 1 MW sin publicar, publicación en un negativo limpio o publicación en una `far_tabla`, cada
  pasada con su peso:
  1. **Veto**: queda fuera todo brazo que calle una protegida (lectura A) que K publica (el mismo veto del §5.4 a).
  2. Si queda uno solo, ése. Si no queda ninguno: «NINGÚN BRAZO PASA EL VETO» y P no cumple (a) con ninguna regla.
  3. Si quedan varios: el que **GANA** a cada uno de los otros en la prueba de signos por bloque del error de posición
     (D-45: exacta con 20 bloques o menos, si no 10.000 sorteos con semilla 162; GANA con valor-p 5 % o menos).
  4. Si ninguno gana a todos: el único que nadie vence; si nadie vence a radiante, **se queda radiante** (cambiar el
     código compartido exige una mejora medida); si no, **NO RESUELTO** entre los no vencidos, y decide Nicolás con la
     vara 3 al lado.
  5. **Sin cobertura de las lejanas** (sin run FAR, sin control de vida, o más del 10 % de las `far_tabla` SIN DATO), la
     regla **no decide**: «NO DECIDE: LAS LEJANAS SIN COBERTURA».
  Se informan al lado, sin decidir: la misma regla con el veto contado sólo sobre protegidas de la tabla (las cuatro de
  §8.1 son del OCR), y cuántos bloques discordantes aporta cada tramo (T, O1, O2; A104). Si la elección se apoya en un
  solo tramo, se dice.
- **El paquete P del §5.4 es la vía con el brazo que elige la RP.** Si la RP da NO RESUELTO, el §5.4 se lee con cada
  brazo empatado y decide Nicolás. Al criterio (b) del §5.4 se le agrega: **P2-L del brazo elegido contra K no da
  PIERDE ni BLOQUEA** (publicar en la cumbre donde MIROVA ubicó el calor lejos es un error que K puede no cometer: K
  publica en 122 de las 330).

### 8.6 Cambios al paso 1 (equivalencia, §3.1)

a. **La publicación se compara brazo por brazo, con la misma regla de posición a los dos lados.** Con la máscara y la
   grilla idénticas, la distancia de cada brazo es idéntica por construcción; lo único que puede separar la publicación
   de la vía y la del port es el VRP. El lector arma, para cada brazo, el record de la vía y el mismo record con el VRP
   del port (con la vara del §7.3 y del punto b), y exige publicación idéntica en el 100 %, en el marco y en las
   lejanas.
   (Escrita después de ver la equivalencia de #921: es la razón de la adenda, no un ajuste para que calce.)
b. **La vara del VRP sobre 4 píxeles es `brazos.py` con la regla de relleno de MATLAB por código independiente**
   (`delaunay_perturbado.py` de S163, la función `vrp_port_con_regla_matlab` de `equivalencia_v375e.py`), en vez de
   `brazos.py` tal cual. De 1 a 4 píxeles sigue la salida de MATLAB donde la hay; en las pasadas FAR, que MATLAB no
   corrió, la misma regla por código independiente. La exigencia del 99 % no cambia, y el lector la mide también en
   las pasadas FAR (en `equivalencia_v375e.py` sólo estaba el marco). Dicho con la
   cautela de V165-04: sobre 4 píxeles no hay salida de MATLAB para 375, así que esto prueba que la vía y el port
   coinciden con la misma regla, no que la vía iguale a MATLAB. **Escrita después de ver el resultado de #921** (40 de
   329 fuera de tolerancia con la vara vieja, las 40 a 0,0 con la nueva): la decide Nicolás.
c. Máscara idéntica índice por índice y grilla y caja idénticas: sin cambio.

### 8.7 Controles del lector (si uno cae: sale 3, «LECTURA NO LEGIBLE», y no se lee nada)

C1, en las pasadas con un solo alertado los tres brazos dan la misma distancia, con al menos un caso. C2, el predicado
responde a `distance_class` en las dos direcciones (summit publica, far no, de vuelta a summit publica). C3, las
listas: ids FAR en [20000, 29000), control de vida en [29000, 30000), ningún id del marco en esos rangos, toda FAR con
clase `far_tabla` o `far_ocr`, el archivo sin gránulo atado por sha256 a la lista. C4, `evaluar.py` es el del
pre-registro (si no, ni se carga). C5, radiante y pico recalculados desde la máscara son el `centroid_dist_km` y el
`hotspot_dist_km` del record de la vía, y su clase la de la vía, en todas las pasadas con alertados. C6, el almacén no
cambia la `distance_class` de ninguna variante. C7, control de vida del run FAR: las 20 re-medidas dan el M14 de S162
(npix y VRP a 1e-6 MW) en el 90 % o más, ninguna distinta, alguna con píxeles. Además, antes de cualquier número:
cobertura por lote y clase (A108), las SIN DATO por nombre, y K re-corrido contra K publicado con la regla de
`evaluar.py` (0,95). Si `pipeline/mirova_v750_codigo.py` el día de la lectura no es el blob de #921 (comparado con
fin de línea LF, como lo guarda git), se avisa; C5 vigila que la regla del record no haya cambiado.

### 8.8 Despacho (sólo con la adenda sellada)

La coordinadora, desde un tag sobre el commit sellado: copia `e_adenda2/probe-s166-v375e-far.yml` a
`.github/workflows/` en la rama `s166-v375e-far-disparo` (no se mergea) y empuja. Autentica sólo por `EARTHDATA_TOKEN`
(A71). Un relanzamiento con `SOLO` lee la misma lista; antes de darlo por bueno se cuenta en su log que procesó tantas
pasadas como ids pidió (A108). Costo: 350 pasadas, unas 2,5 h de runner. La sombra prospectiva del §3.3 lee los tres
brazos desde los records (`distancias_desde_record`: radiante = `centroid_dist_km`, pico = `hotspot_dist_km`, cercano
= el menor `dist_km` de `anomaly_pixels`, redondeado a 0,01 km por la vía), con la misma RP; si elige otro brazo que la
retrospectiva, decide Nicolás.

### 8.9 Lectura

    python -I experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py --art-far <artefactos del run FAR> --salida <archivo> --json <archivo>

(los artefactos de S159, S162 y S162b se leen de sus rutas de siempre; `--art-s159`, `--art-s162` y `--art-s162b` las
cambian). El orden de lectura: primero los controles, después la equivalencia por brazo (§8.6), después la RP, y recién
entonces las lecturas del §5 con el brazo elegido.

### 8.10 Lo que esta adenda no hace

No elige la regla de posición: la elige la RP con los datos, o Nicolás si no resuelve. No toca `pipeline/` (si la RP
elige otro brazo que radiante, cambiar la vía es un PR aparte con su A45, y afecta también a VIIRS 750 y MODIS, que
comparten `procesar_grilla`). No cubre las `FALSO_POSITIVO` que conviven con una ALERTA en la misma pasada (esas son
`pos` y ya están en el marco) ni las `sin_geometria`. «Lo correcto es no publicar» en las lejanas es una premisa de la
réplica (A115): vale para `mirova_equivalent`, no para `experimental`.

### 8.11 Pruebas y estado

- **Batería** (`e_adenda2/probar_adenda2.py`, salida `probar_adenda2_salida.txt`): **112 de 112**, con escenas
  sintéticas (LEJANA, BORDE, UNO, PICOCERCA, ANILLO, cráter corrido de X0, Y0), el predicado del tablero con node, el
  almacén real y `evaluar.py` real. Cubre las tres distancias y sus desempates, la variante, cada control (C1 a C7, en
  verde y en rojo), la equivalencia por brazo (máscara, VRP a 1e-3 MW y publicación), la elección de la vara del VRP,
  la regla de posición con escenas y con veredictos fabricados (todas las ramas de `decidir_brazo`), el veto con la
  tabla sola, los bloques por tramo, las tres varas, el K re-corrido, las funciones del generador y `generar()` entero
  con dependencias sintéticas (control caído, segundo intento, carpeta del marco, records de otro commit, CRLF).
  Además, sobre grillas reales sin leer el marco: la identidad de radiante y pico con `procesar_grilla` en las 6
  grillas con alertados de `tests/datos_s165_v375/`, y `main()` de punta a punta sobre un artefacto falso armado con 5
  de esas grillas rotuladas como control de vida (máscara de la vía igual a la del port C13 en 5 de 5, VRP contra la
  vara en 5 de 5, publicación por brazo igual; sale 3 por C7, como debe con 5 de 20 re-medidas).
- **Nulo por mutaciones** (`e_adenda2/mutar_adenda2.py`, salida `mutar_adenda2_salida.txt`): **62 de 63 mutaciones
  de una línea atrapadas por aserción**, 0 caídas (45 del lector, 18 del generador); la copia sin mutar PASA y la que
  rompe la importación sale CAÍDA. Sobrevive una, declarada equivalente: L20 pasa a la regla de posición también las
  `far_ocr`, pero el error de posición no las cuenta y el veto sólo mira el marco, así que no puede cambiar nada. En
  la primera corrida sobrevivían tres más y caían tres (una lectura faltante tras un control caído, un volcán sin
  grilla en la escena del generador, una guarda que lanza en vez de devolver 2): se arreglaron en la batería, no en el
  código medido, y la elección de la vara pasó a una función propia (`elegir_vara`) para poder probarla.
- **Verificador limpio**: pendiente (§8.12).
