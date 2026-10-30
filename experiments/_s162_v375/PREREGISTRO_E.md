# Pre-registro V375-E (S162): el paquete del código de MIROVA en VIIRS 375 contra producción (K)

> ⚠️ **Cuerpo y adenda 3 SELLADOS (S168, 2026-10-29)** sobre `e6675da85` más el commit del sello (tag
> `s168-v375e-cuerpo-sellado`), con la condición que puso Nicolás (ningún hallazgo de gravedad 3 en el verificador limpio
> de la adenda 3), cumplida: §9.12. Texto de la marca antes del sello:
>
> ⚠️ **Adenda 3 (S167, §9), SIN SELLAR**: cierra el cuerpo (§1 a §7) para el sello que aprobó Nicolás tras el
> verificador corto del cuerpo, escrita antes de abrir el run de las lejanas o de leer el marco. **Donde una adenda
> contradice al cuerpo o a una adenda anterior, rige la más reciente (§9.1).** El «BORRADOR, sin sellar» y las
> dependencias de la cabecera que sigue describen el estado de S162: PD1 y PD3 están cumplidas (§7.1, §8.3) y el
> evaluador común se conecta en §9.5. Cabecera original:
>
> Escrito antes de que exista el paquete en `pipeline/` y antes de ver ningún resultado suyo. Lo que cambie después del
> sello va en una adenda fechada al final. Es el pre-registro de una ADOPCIÓN posible: la implementación, el sello, el
> tag defensivo y el despacho pasan por A45 (el sí de Nicolás, cada uno). Estado: **BORRADOR, sin sellar**; depende de
> PD1 (la ROI, V375-C), de PD3 (la vía de proceso en `pipeline/` detrás de flag) y del evaluador común de la sesión del
> instrumento (programa §8.3: placebo y comparador d′ fuera de `evaluar_d25.py`). Pasó por el verificador limpio junto
> con B y C (`verificador/INFORME.md`); sus correcciones a E están en §3, §4 y §5.4.
>
> ⚠️ **Adenda 2 (S166, §8), SELLADA por Nicolás el 2026-10-28 sobre `349409880`** («continua con todo lo que
> recomiendes», en el chat de la coordinadora S166, con las dos sub-decisiones recomendadas: la vara nueva del paso 1,
> §8.6 b, y la regla N-3, §8.13). Lo que no es la adenda 2 sigue en borrador (superado: el cuerpo se cierra con la
> adenda 3, §9). Texto de la marca antes del sello (tras §8.13 el veto (a) con radiante cae por 2 protegidas, no 4): la vía ya está en `main` (#921, apagada) y Nicolás decidió medir la regla de
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

⚠️ En la retrospectiva P-def no se corre, P-sinfiltro informa y PLACEBO son los controles C8 y C9: §9.4 (VA168-05).

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

1. **Equivalencia (PD3)**. (⚠️ Población, vara y compuerta precisadas por §8.6 y §9.3: se mide en todas las pasadas con
   grilla de los cuatro lotes, no sólo en las 859 de B y C, y NO EQUIVALENTE corta la lectura con exit 4.) La vía de `pipeline/`, corrida sobre los gránulos del lote de B y C (859 pasadas con grilla
   guardada), reproduce al port de `brazos.py` pasada por pasada: misma cantidad de alertados y VRP a 1e-3 MW en el
   99 % o más, **la publicación idéntica en el 100 % de las pasadas** y las 80 protegidas idénticas. Si no, el paquete
   no es el código y no se sigue. (El verificador mostró que tolerar 1 % de pasadas distintas, ~8 de 859, es del tamaño
   del efecto que B mide en negativos: por eso la publicación no tiene tolerancia.)
2. **Lectura retrospectiva** (⚠️ población y pesos: §9.2, la unión de S159, S162 y S162b con pesos N_h / n_ok_h, y no
   los de B §3) sobre la unión de B y C (marco de S159, del 2026-04-01 al 2026-10-21, sin el 12, 13 y 17 a
   20 de octubre), con los pesos de `PREREGISTRO_B.md` §3. Ventanas T y O por separado, O1 y O2 (#535) por separado.
3. **Sombra prospectiva confirmatoria** (⚠️ qué lee y cuándo se escribe su lector: §9.8) desde el **2026-11-03** (ventana P del programa, sin Suomi NPP: otro régimen),
   como perfil aparte con su `data_subdir`, sin tocar la vista operacional, hasta 30 noches o 40 alertas de MIROVA que
   decidan, lo que llegue último. La referencia se congela por hash en cada corte de lectura.

## 4. Controles (antes de leer)

⚠️ Cuáles corre el lector de la retrospectiva y cuáles no (y por qué): §9.4; los de la curva informan en la
retrospectiva (§9.6). Texto original:

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

⚠️ Qué lote decide y con qué pesos: §9.2 (las reglas de qué lote decide de B §5.5 y de B2 no rigen aquí). MISSION
informa y no decide (§9.7). Texto original:

Las de `PREREGISTRO_C.md` §5 y `PREREGISTRO_B.md` §5, de P contra K: P1 veto (ninguna protegida que K publica puede
perderse; lectura A, regla SN; la protegida de cráter de V375-A al lado), P1b en las dos direcciones, P2 por la prueba
de signos por bloque noche-volcán (D-45), silencio en negativos limpios con la cota de Wilson sobre n efectivo, MISSION
con la cota honesta del estrato de cero eventos.

### 5.2 Magnitud (M)

⚠️ Qué corte decide, en qué modo y con qué pares: §9.5 (decide la unión del marco en modo «decide»; los cortes por
cenit, volcán y canal informan). Texto original:

La regla sellada de D-27 sobre d = |log10(P / MIROVA)| − |log10(K / MIROVA)| y el comparador de ganancia pareja de
D-28 (d′ con ĝ = mediana de log10(P / K)), con la calibración de D-30 y D-32, **tomados del evaluador común de la
sesión del instrumento** (no se reimplementan aquí). Por tramo de 10° de cenit, por volcán y por canal. El placebo da
d′ = 0 por construcción; si no, el instrumento está roto.

### 5.3 La curva de cenit

⚠️ En la retrospectiva la curva informa y no decide: el marco no da las 8 noches de nulo (§9.6). El criterio (d) se
decide en la sombra. Texto original:

Razón doble D por noche (`curva_cenit.py`), condicionada (las dos pasadas publicadas, DECIDE) y sin condicionar (no
publicar = 0, informa). Veredicto: SIN SUSTRATO con menos de 8 noches en la lectura o en el nulo; NULO SESGADO si el
nulo no contiene 1; **CAE MAS QUE MIROVA** si el IC de la mediana de D queda entero bajo 1; CAE MENOS QUE MIROVA si
queda entero sobre 1; **REPRODUCE LA CURVA** si lo contiene y la mediana está en [0,8; 1,25]; NO RESUELTO en otro caso.
Se informa al lado si la curva de MIROVA misma se separa del nulo (en la ventana O no se separa: 0,857 [0,707; 1,077]
contra un nulo de MIROVA de 0,947); esa marca no bloquea, porque D compara las dos caídas en los mismos pares. Por tramo de la
pasada oblicua (menos de 50°, 50° o más) y por volcán (Chillán aparte, V375-F).
Vara de K, medida antes: **CAE MAS QUE MIROVA**, 0,766 [0,722; 0,861].

### 5.4 Regla de adopción del paquete (para PD4, decide Nicolás con A45)

⚠️ Precisada por §8.5 (el paquete es la vía con el brazo de la regla de posición), §8.13 (las protegidas sólo del OCR
de Suomi NPP anteriores al 2026-10-09 no vetan en (a)) y §9.7 (cada salida posible de cada criterio y de la regla de
posición, mapeada a CUMPLE, NO CUMPLE o DECIDE NICOLÁS, en código). Texto original:

El paquete P **cumple** si, en la lectura retrospectiva Y en la sombra prospectiva: (a) P1 no pierde ninguna protegida
que K publica (lectura A, todos los canales: decisión 4 del programa, «decide la lectura A»); (b) P2 contra K da GANA o EMPATE (no PIERDE ni BLOQUEA) y el silencio no da ENCIENDE DE MAS; (c) M da
MEJORA con d′ dando MEJORA (no sólo una ganancia) o, si d no mejora, no EMPEORA; (d) la curva da REPRODUCE LA CURVA,
o al menos el IC de D del paquete queda entero sobre el de K. Si (a) falla en cualquiera de las dos, **no cumple**.
Si la retrospectiva cumple y la sombra no tiene sustrato a las 30 noches, la decisión es de Nicolás con lo que haya.

**Riesgo conocido para (a), dicho antes de medir.** (⚠️ Resuelto por §8.13: Nicolás decidió que esas protegidas, sólo
del OCR de Suomi NPP antes del 2026-10-09, se informan aparte y no vetan.) En el lote de S159 el port pierde 3 protegidas que K publica, las
tres sólo OCR (dos de Tupungatito y una de Isluga), y las pierden los diez brazos de ROI por igual. V375-C las saca de
la elección de caja (no las causa la caja), pero aquí siguen siendo veto. Si en el lote nuevo aparecen más del mismo
tipo, (a) falla por ellas aunque la etiqueta de protegida de cráter de V375-A diga que son fuentes lejanas: cambiar la
vara para esas filas es una decisión de Nicolás, con la etiqueta de V375-A delante, no de este pre-registro.

## 6. Lo que este pre-registro no hace

No implementa nada (PD3 es otra tarea con su propio pre-registro de implementación y A45). No mide el día. No mide
Chillán sobre 3 MW como pregunta propia (V375-F, después de esto). No mezcla la ventana P con la O: son regímenes
distintos (cese de Suomi NPP).

## 7. Adenda 1 (2026-10-26, S164): PD1, dependencias cumplidas y la vara de la equivalencia

Escrita antes de que exista la vía de 375 y antes de ver ningún resultado del paquete. Sigue en **BORRADOR, sin sellar**
(superado: se sella con el cuerpo, §9).

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
   (Superado por §8.13: Nicolás lo decidió al sellar la adenda 2; no vetan.)

## 8. Adenda 2 (2026-10-28, S166): los tres brazos de posición y las pasadas lejanas de MIROVA

Estado: **SELLADA** por Nicolás el 2026-10-28 sobre el commit `349409880` (rama `claude/adoring-wright-dc0404`). Sus
palabras, relayadas por la coordinadora S166: «continua con todo lo que recomiendes», con las dos sub-decisiones que
ella recomendó: aceptar la vara nueva del paso 1 (§8.6 b) con las dos cifras a la vista, y aplicar la regla N-3 (§8.13).
El commit del sello las aplica sin cambiar nada más (tag `s166-v375e-adenda2-sellada`). Estado antes del sello:
BORRADOR, SIN SELLAR. Autor: sesión hija de VIIRS 375 de la coordinadora S166. Código, listas y pruebas en
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
familia `VIIRS375` (docstring y cuerpo, l. 687 a 745). Dos cosas más de la vía, que la tabla no decía (verificador,
pregunta 1): el corte de 5 km al centro de la grilla (`FAMILIAS["VIIRS375"]["dist_max_centro_km"]`, un gránulo que no
cubre el volcán no da record), y que el relabel A46 del almacén y `geo_class` leen `pc.centroid_dist_km`, por eso las
variantes de §8.4 reescriben ese campo.

### 8.4 Qué agrega

1. **Tres brazos de posición sobre la misma detección.** La máscara, el VRP y el tamaño del cúmulo son los de
   `procesar_grilla`; sólo cambia la distancia desde el cráter (`posicion_de`, el mismo ancla que producción) y con ella
   `distance_class`, `primary_cluster.centroid_dist_km` y `final_hotspot_dist_km`. Frontera inclusiva (`summit` si la
   distancia es `inner_radius_km` o menos), igual que la vía.
   - **radiante**: el record de la vía sin tocar (centroide del cúmulo 8-conexo de la alertada más radiante);
   - **cercano** (al cráter; no es el «cercano» de `evaluar.py`, que mide desde el punto X0, Y0 de MIROVA: VC167-08):
     el alertado más cercano al cráter; a igual distancia, el de menor (fila, columna);
   - **pico**: el alertado de mayor radiancia I4, el mismo que siembra el cúmulo, con el mismo desempate que la vía.
   Cada variante pasa por `store.append_record` y por el predicado del tablero con node, como un record de producción.
   La variante no es un record completo (VE2-08): no mueve `centroid_lat/lon`, `final_hotspot_lat/lon` ni `n_pixels`.
   El predicado no los lee (lee `distance_class` y `pc.centroid_dist_km`, `frontend/index.html` l. 1175 y 1179, según el
   verificador), así que la publicación medida es la que tendría la regla; un PR que la implemente tiene que mover
   también el marcador.
2. **Las pasadas lejanas de MIROVA** (`e_adenda2/objetivos_far_v375.py`). Corre la población de S159
   (`experiments/_s159/portes/01_poblacion.py`) con los **mismos insumos congelados** que el marco de B y C (records de
   `533398f8f`, comprobados blob por blob; referencia de Mirova-v1 en los commits `fe2d0a57` y `4ddd5481`, bajada de esos
   commits y no del remoto de hoy; más las dos capas locales que `cargar_referencia_unificada` suma por defecto,
   fijadas por sha256 LF en el meta de la lista: `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv`
   `2613e7cc…bf59e7` y `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv`
   `183aff7f…aa93568`; de la primera sacan su fila FALSO_POSITIVO 15 de las 330, VE2-02 del verificador), cambiando sólo
   el filtro de etiquetas para dejar pasar `far_ref`. Control: las
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
   sha256 (fin de línea LF): `objetivos_far_v375.json` `a8528424…11ca1b`, `objetivos_run_far_v375.json` (lo que lee
   el run) `28468a14…22db26`, población `aff8822a…cd0a7d` (regenerable, no se commitea; copia en
   `D:\vrp-trabajo\temporales\s166_v375e_adenda2\poblacion_far_v2.json`). La primera versión de la lista (sin las
   capas en el meta, `d968aafe…` y `4abc0630…`) traía las mismas 330 pasadas, campo por campo. Salida: `e_adenda2/objetivos_far_v375_salida.txt`.
3. **Un run de sólo lectura** (`e_adenda2/probe-s166-v375e-far.yml`): el mismo `probe_v375.py` de B y C, sin cambios,
   sobre esas 350 pasadas en 14 trozos de 25, que guarda la grilla de cada una. Lo despacha la coordinadora, desde un
   tag, en una rama de disparo que no se mergea (§8.8).
4. **Un lector** (`e_adenda2/leer_posicion_v375e.py`): la vía de `pipeline/` sobre las grillas de los lotes S159, S162,
   S162b y FAR, los tres brazos, y las tres varas del §8.5.

### 8.5 Las varas y la regla de posición (RP)

- **Vara 1, alertas y negativos limpios del marco** (los pesos de `PREREGISTRO_B.md` §3; ⚠️ superado por §9.2: la
  unión de los tres lotes con pesos N_h / n_ok_h; MISSION y la mediana de magnitud de `evaluar.py` informan, la M que
  decide es la de §9.5): las lecturas de `evaluar.py`
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
  1. **Veto de la posición**: queda fuera todo brazo que calle una protegida (lectura A) que K publica **y que otro
     brazo sí publica**, salvo las protegidas sólo del OCR de Suomi NPP anteriores al 2026-10-09, que se informan aparte
     (§8.13, sellada). La protegida que K publica y callan los tres brazos no la arregla ninguna regla de posición:
     se informa aparte como «pérdida común» y sigue siendo veto del paquete en el §5.4 (a), no de esta elección.
     (Corregido por VE2-01 del verificador: con el veto entero, las 3 protegidas de Suomi NPP sólo del OCR que pierden
     los diez brazos de V375-C, `resultado_run40116289866/verificador/INFORME.md` l. 43, habrían sacado a los tres
     brazos sin medir nada de posición.)
  2. Si queda uno solo, ése. Si no queda ninguno: «NINGÚN BRAZO PASA EL VETO».
     Un ciclo (radiante vence a cercano, cercano a pico y pico a radiante) da NO RESUELTO entre los tres (VE2-09).
  3. Si quedan varios: el que **GANA** a cada uno de los otros en la prueba de signos por bloque del error de posición
     (D-45: exacta con 20 bloques o menos, si no 10.000 sorteos con semilla 162; GANA con valor-p 5 % o menos).
  4. Si ninguno gana a todos: el único que nadie vence; si nadie vence a radiante, **se queda radiante** (cambiar el
     código compartido exige una mejora medida); si no, **NO RESUELTO** entre los no vencidos, y decide Nicolás con la
     vara 3 al lado.
  5. **Sin cobertura de las lejanas** (sin run FAR, sin control de vida, o más del 10 % de las `far_tabla` SIN DATO), la
     regla **no decide**: «NO DECIDE: LAS LEJANAS SIN COBERTURA». (⚠️ Superado por §9.3 a: con el control de vida
     caído no se lee nada, LECTURA NO LEGIBLE, como dice §8.7; «sin run FAR» no se alcanza desde la línea de
     comandos; NO DECIDE queda sólo para más del 10 % de `far_tabla` SIN DATO.)
  6. **Por tramo (A104, VE2-06 y N-2)**: la misma regla se corre dentro de T, O1 y O2. Si O1 u O2 por separado no da
     el mismo resultado que la unión (otro brazo, o SE QUEDA RADIANTE frente a un elegido, o NO RESUELTO, o NINGUNO), el
     veredicto lleva la marca «A104: en O1 (u O2) el resultado es otro (…); decide Nicolás». Un tramo sin pasadas no
     cuenta como discordancia. Dicho antes de medir: en un tramo chico lo más probable es SE QUEDA RADIANTE por falta de
     bloques, así que esta marca puede saltar seguido; cuando salta, decide Nicolás.
  Se informan al lado, sin decidir: la misma regla con el veto contado sólo sobre protegidas de la tabla (las cuatro de
  §8.1 son del OCR, y dos de ellas de Suomi NPP: VE2-07 pide leerlas con cautela por A119, aunque desde el
  2026-06-13 el OCR ya tiene distancia), cuántos bloques discordantes aporta cada tramo, y cuántas `far_tabla` tienen
  algún alertado en la caja (si son menos de 5, las lejanas no tienen sustrato para pesar en la elección y se dice:
  VE2-13).
  Dicho antes de medir (VE2-12): cada pasada pesa lo que representa en la población. Una alerta bajo 1 MW sorteada pesa
  unas 5 (`pos_bajo` es muestra de 200 en 949), una protegida y una lejana pesan 1 (son censo), un negativo limpio
  sorteado unas 2. Las protegidas no dependen de ese peso porque las cuida el veto.
- **El paquete P del §5.4 es la vía con el brazo que elige la RP.** Si la RP da NO RESUELTO, el §5.4 se lee con cada
  brazo empatado y decide Nicolás. (⚠️ Las demás salidas de la RP, NINGÚN, NO DECIDE y la marca A104: §9.7.) Al criterio (b) del §5.4 se le agrega: **P2-L del brazo elegido contra K no da
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
   las pasadas FAR (en `equivalencia_v375e.py` sólo estaba el marco). El lector imprime también, al lado y sin decidir,
   la cifra con la vara vieja del §7.3 (N-1 del verificador corto), para que el efecto de este cambio se vea en la
   lectura (en #921 eran 289 de 329 contra 329 de 329). Dicho con la
   cautela de V165-04: sobre 4 píxeles no hay salida de MATLAB para 375, así que esto prueba que la vía y el port
   coinciden con la misma regla, no que la vía iguale a MATLAB. **Escrita después de ver el resultado de #921** (40 de
   329 fuera de tolerancia con la vara vieja, las 40 a 0,0 con la nueva): la decide Nicolás. **Aceptada por Nicolás al
   sellar (2026-10-28)**; la lectura sigue mostrando también la cifra con la vara vieja (N-1).
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
pasadas como ids pidió (A108). Costo: 350 pasadas, unas 2,5 h de runner. (⚠️ Lo que sigue sobre la sombra queda
superado por §9.8: la RP no se corre en la sombra.) La sombra prospectiva del §3.3 lee los tres
brazos desde los records (`distancias_desde_record`: radiante = `centroid_dist_km`, pico = `hotspot_dist_km`, cercano
= el menor `dist_km` de `anomaly_pixels`, redondeado a 0,01 km por la vía), con la misma RP; si elige otro brazo que la
retrospectiva, decide Nicolás.

### 8.9 Lectura

    python -I experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py --art-far <artefactos del run FAR> --art-s159 D:\vrp-trabajo\temporales\s159_portes\run_39712862945 --art-s162 C:\vrp-trabajo\temporales\s162_v375\run_40116289866 --art-s162b C:\vrp-trabajo\temporales\s162_v375\run_40131572769 --salida <archivo> --json <archivo>

(las cuatro rutas son obligatorias y no tienen valor por defecto, para que leer el marco sea siempre explícito: VE2-10).
El orden de lectura: primero los controles, después la equivalencia por brazo (§8.6), después la RP, y recién
entonces las lecturas del §5 con el brazo elegido. (⚠️ Esas lecturas del §5 ya están escritas y probadas en el
lector, §9.5 a §9.7; no se agregan después de ver la salida de la RP. Salidas: 0, 3 control caído, 4 no equivalente.)

### 8.10 Lo que esta adenda no hace

No elige la regla de posición: la elige la RP con los datos, o Nicolás si no resuelve. No toca `pipeline/` (si la RP
elige otro brazo que radiante, cambiar la vía es un PR aparte con su A45, y afecta también a VIIRS 750 y MODIS, que
comparten `procesar_grilla`). No cubre las `FALSO_POSITIVO` que conviven con una ALERTA en la misma pasada (esas son
`pos` y ya están en el marco) ni las `sin_geometria`. «Lo correcto es no publicar» en las lejanas es una premisa de la
réplica (A115): vale para `mirova_equivalent`, no para `experimental`.

### 8.11 Pruebas y estado

⚠️ Cifras del sello de la adenda 2; las vigentes (batería 165 de 165, nulo 113 de 114 con el repaso) están en §9.11
(VA168-05).

- **Batería** (`e_adenda2/probar_adenda2.py`, salida `probar_adenda2_salida.txt`): **140 de 140**, con escenas
  sintéticas (LEJANA, BORDE, UNO, PICOCERCA, ANILLO, cráter corrido de X0, Y0), el predicado del tablero con node, el
  almacén real y `evaluar.py` real. Cubre las tres distancias y sus desempates, la variante, cada control (C1 a C7, en
  verde y en rojo, C7 también con un port que calla igual que la referencia), la equivalencia por brazo (máscara, VRP a
  1e-3 MW y publicación), la elección de la vara del VRP, la regla de posición con escenas y con veredictos fabricados
  (todas las ramas de `decidir_brazo`, ciclo incluido), el veto que sólo cuenta lo que depende de la posición y la
  pérdida común, la regla por tramo con la marca A104 ante cualquier resultado distinto (N-2), la cifra con la vara vieja (N-1), la regla N-3 (no veta la protegida
  sólo OCR de Suomi NPP anterior al hito; sí vetan NOAA-21, la de la tabla y la del 2026-10-09), la regla del 10 % de lejanas SIN DATO, pesos distintos de 1, el
  veto con la tabla sola, las tres varas, el K re-corrido, el ancla de la vía en el cráter, las funciones del generador
  y `generar()` entero con dependencias sintéticas (control caído, segundo intento, carpeta del marco, records de otro
  commit, CRLF, capas locales en el meta). Sobre grillas reales sin leer el marco: la identidad de radiante y pico con
  `procesar_grilla` en las 6 grillas con alertados de `tests/datos_s165_v375/`, y `main()` de punta a punta sobre un
  artefacto falso armado con 5 de esas grillas rotuladas como control de vida (máscara de la vía igual a la del port
  C13 en 5 de 5, VRP contra la vara en 5 de 5, publicación por brazo igual, C5 en 5 de 5, C6 sin cambios; sale 3 por C7,
  como debe con 5 de 20 re-medidas; con un almacén que cambia la clase, C6 cae).
- **Nulo por mutaciones** (`e_adenda2/mutar_adenda2.py`, salida `mutar_adenda2_salida.txt`): **83 de 84 mutaciones
  de una línea atrapadas por aserción**, 0 caídas (65 del lector, 19 del generador; en el checkout de Windows con
  CRLF: en un árbol LF L42 sobrevive y quedan 82 de 84, N-5); la copia sin mutar PASA y la que
  rompe la importación sale CAÍDA. Sobrevive una, declarada equivalente: L20 pasa a la regla de posición también las
  `far_ocr`, pero el error de posición no las cuenta y el veto sólo mira el marco, así que no puede cambiar nada. Las
  sobrevivientes del verificador que no eran equivalentes entran como L50 a L58, las ramas nuevas de los arreglos
  como L46 a L49 y G19, las del verificador corto como L59 a L62, y las que deshacen la regla N-3 del sello como L63 a L65.
  Quedan declaradas equivalentes o débiles, sin mutación propia: el pico sobre toda la máscara en vez del cúmulo (la
  semilla del cúmulo es el máximo de toda la máscara: es el mismo píxel), la tolerancia de C1 y el inner del tablero en
  `publicar` (la variante ya fija la clase con el inner de `volcanoes.yaml`, que coincide con el del tablero en los 11).

### 8.12 Verificador limpio y arreglos

Sonnet 5.5 con contexto limpio (`e_adenda2/verificador/INFORME.md`; sus caminos escritos antes de abrir la adenda,
sha256 `bcf60fd0…be8bcf9`; servidor 2026-10-28 04:51 a 05:19 UTC; commit medido `6c80ce7c0`). El verificador declaró
que corrió a esfuerzo bajo, aunque se le pidió alto. Veredicto: **SELLABLE CON CAMBIOS**. Reprodujo todas las cifras,
regeneró la lista con los mismos sha256 (byte a byte), re-corrió la batería (112 de 112) y el nulo (62 de 63), confirmó
que la §8.3 describe la vía de #921, que los tres brazos son los del programa medidos desde el ancla de producción
(`get_detection_anchor`, 11 de 11) y que el almacén no cambia clase, VRP ni publicación de las variantes (18 de 18), y
midió que ninguna `far_tabla` tiene `Distancia_km` de MIROVA dentro del radio del tablero (0 de 329).

| hallazgo | gravedad | qué se hizo |
|---|---|---|
| VE2-01 el veto lo decidían pérdidas comunes a los tres brazos | 4 | el veto de la posición cuenta sólo la protegida que otro brazo publica; las comunes se informan y siguen siendo veto del §5.4 (a) (§8.5 paso 1) |
| VE2-02 15 lejanas sacan su fila de una capa local no fijada | 2 | sha256 de las dos capas en el meta de la lista y en §8.4; lista regenerada (mismas 330 pasadas) |
| VE2-03 una aserción de `main()` dentro de un `else` muerto | 2 | error mío al insertar el bloque CRLF; movida, y se agregó la de C5 y C6 |
| VE2-04 16 de sus 23 mutaciones sobrevivían | 3 | pruebas nuevas para pesos distintos de 1, negativos en la regla, regla del 10 %, C7 sin píxeles, rango CTLF, ancla, ejes de `pos_ref`, borde del OCR y ciclo; sus mutaciones entran al nulo |
| VE2-05 cableado de `main()` sin prueba | 2 | aserciones sobre C5 y C6 en `main()`, y un almacén que voltea la clase hace caer C6 |
| VE2-06 sin veredicto por tramo | 2 | la regla corre en T, O1 y O2, con la marca A104 (§8.5 paso 6) |
| VE2-07 las 4 protegidas motivadoras son sólo del OCR | 3, SOSPECHA | dicho en §8.5; deciden igual (lectura A, todos los canales, como el §5.4) |
| VE2-08 la variante no mueve lat/lon | 1 | declarado en §8.4 |
| VE2-09 un ciclo daba texto vacío | 1 | NO RESUELTO entre los tres |
| VE2-10 el lector leía el marco por defecto | 2 | las cuatro rutas son obligatorias |
| VE2-11 referencias internas erradas | 1 | corregidas (§8.12 existe; el yml cita §8.8) |
| VE2-12 una alerta bajo 1 MW pesa unas 5 veces una protegida | 1 | declarado en §8.5 (es el peso de la población; las protegidas las cuida el veto) |
| VE2-13 la regla no exige sustrato en las lejanas | 1 | el lector dice cuántas `far_tabla` tienen alertado y avisa bajo 5 |

**Verificador corto sobre el delta** (lanzado por la coordinadora S166; Sonnet con contexto limpio sobre
`6c80ce7c0..e037b8326`; informe en `D:\vrp-trabajo\temporales\s166_ver_v375e\INFORME.md`): **SELLABLE CON CAMBIOS
MENORES**. Lo ya fijado sigue intacto; batería 130 de 130; nulo 75 de 77 en un árbol LF (L42 se atrapa sólo con el
checkout en CRLF: el 76 de 77 vale en Windows); L20 es equivalente. Su juicio sobre el §8.6 b: corrección de
instrumento con base previa (la contingencia «se mira primero el relleno» estaba escrita en S164), escrita después de ver
el resultado, que sobre 4 píxeles prueba que dos implementaciones de la misma regla coinciden y no que coincidan con
MATLAB, y que sólo puede cambiar el veredicto de E por la puerta del paso 1. Arreglos de esta versión:

| hallazgo | qué se hizo |
|---|---|
| N-1 el efecto del §8.6 b no se veía en la lectura | el lector imprime la cifra con la vara vieja, informativa (§8.6 b) |
| N-2 la marca A104 sólo saltaba entre dos ELEGIDO distintos | salta con cualquier resultado distinto en O1 u O2 (§8.5 paso 6), con pruebas |
| N-3 dos de las cuatro protegidas son sólo OCR de Suomi NPP antes del 2026-10-09 | opción explícita en §8.13, a decidir por Nicolás, sin aplicar (aplicada al sellar, §8.13) |
| N-4 la batería no es autocontenida | dicho en su encabezado: necesita el repo git (o `GIT_DIR`) y la copia de D: |
| N-5 el nulo depende del fin de línea del checkout | dicho en el encabezado de la batería y aquí |
| N-6 y VE2-11 el yml decía «sellada» | dice «SIN SELLAR al escribir este archivo; se despacha sólo cuando Nicolás la selle» |

**VE2-07 y VE2-13 quedan abiertos, y por qué.** (⚠️ Estado anterior al sello: VE2-07 quedó resuelto por la regla
N-3, que Nicolás aplicó al sellar (§8.13); VE2-13 sigue abierto por diseño, sin cambio.) VE2-07 (las protegidas motivadoras son sólo del OCR) no se cierra sin
cambiar quién veta, y eso es la opción N-3: lo decide Nicolás. VE2-13 (la regla no exige sustrato en las lejanas) se
cerraría agregando un mínimo de `far_tabla` con alertado como condición para decidir; no lo agregué porque cambiaría la
regla después del primer verificador sin que nadie lo haya pedido, y porque las lejanas son un censo: si pocas tienen
un alertado en la caja, la escena que separa los brazos es rara en ese marco, no está sin medir. El lector lo dice
(`far_tabla con algún alertado`, con aviso bajo 5), y si Nicolás quiere que bloquee, es un cambio de una línea antes
del sello.

Esta versión (N-1 a N-6) no pasó por un tercer verificador. Batería y nulo: §8.11.

### 8.13 Regla N-3, aplicada (sellada por Nicolás el 2026-10-28)

Para el auto-audit, Nicolás decidió que las alertas sólo del OCR de Suomi NPP anteriores al 2026-10-09 se informan
aparte y no deciden (PR #924, abierto al 2026-10-28). Al sellar esta adenda eligió lo mismo para E: **las protegidas
sólo del OCR (sin alerta de la tabla) de Suomi NPP (`VIIRS_SNPP`) anteriores al 2026-10-09 se informan aparte y no
vetan, ni en la regla de posición (§8.5 paso 1) ni en el criterio (a) del §5.4.** La de la tabla, la de otra
plataforma o la de ese día en adelante siguen vetando. El lector la aplica con `no_veta_n3`: la regla de posición las
lista como «informadas aparte» y no las cuenta en el veto, y por cada brazo imprime el «P1 que veta» del §5.4 (a) sin
ellas, al lado del P1 de `evaluar.py`, que las cuenta todas.

Qué toca, dicho antes de medir:
- de las cuatro del §8.1, dos dejan de vetar a radiante: Isluga 2026-09-28 05:12 y 2026-10-03 05:18 (las dos
  `VIIRS_SNPP`). Las otras dos (Isluga 2026-06-17 05:06 y Láscar 2026-10-01 05:18) son de NOAA-21 y siguen vetando,
  así que con la regla de hoy (radiante) el veto (a) sigue cayendo por ellas;
- las tres protegidas de S159 que pierden los diez brazos de V375-C y K publica (Tupungatito 2026-08-01 y 2026-09-14,
  Isluga 2026-09-09; todas de Suomi NPP y sólo del OCR) dejan de vetar el paquete en el §5.4 (a), que es el riesgo que
  §5.4 y §7.5 dejaban a su decisión.

Texto anterior al sello, conservado: era una opción «a decidir por Nicolás, no aplicada», con el mismo contenido.

## 9. Adenda 3 (2026-10-29, S167): cierre del cuerpo antes del sello

Estado: **SELLADA** el 2026-10-29 (S168) sobre `e6675da85` más el commit del sello, tag `s168-v375e-cuerpo-sellado`,
junto con el cuerpo §1 a §7: Nicolás aprobó el sello con la condición de que el verificador limpio de esta adenda no
trajera hallazgos de gravedad 3 (relayado por la coordinadora S167), y no trajo ninguno (§9.12). Estado antes del sello:
SIN SELLAR. Autor: sesión hija de VIIRS 375, a pedido de la coordinadora S167. Nicolás aprobó el 2026-10-29
(«Sí a todo», programa §12.5 punto 3, relayado por la coordinadora) sellar el cuerpo (§1 a §7) después de un verificador
corto que comprobara que no choca con la adenda 2. Ese verificador (Sonnet con contexto limpio,
`experiments/_s167/v375e_cuerpo_verificador/INFORME.md` en `loop/activo`) dio **SELLABLE CON CAMBIOS MENORES**, con un
hallazgo de gravedad 3 (VC167-04: el lector no calculaba el §5.2 ni el §5.3, ni los brazos P-def, P-sinfiltro y PLACEBO)
y cuatro de gravedad 2. Esta adenda los cierra por texto y en el código del lector, con pruebas y mutaciones.

**Qué se sabía al escribirla.** El run de las lejanas existe (run 40773794395, 14 de 14 trabajos en verde y 350 de 350
pasadas según su log, dato de la coordinadora) y **no se abrió**. Nada del marco se leyó. El único número nuevo es un
conteo de diseño sobre la lista de objetivos, sin grillas, sin resultados y sin ninguna publicación
(`e_adenda2/contar_pares_curva.py`, salida `contar_pares_curva_salida.txt`): el marco tiene 280 alertas con VRP de
MIROVA (80 protegidas y 200 bajo 1 MW), en 34 noches-volcán con dos o más; 28 noches con 15° o más de cenit entre la
pasada menos oblicua y la más oblicua, y 5 con un par a menos de 5° (T 7 y 2; O 21 y 3).

### 9.1 Precedencia y marcas (VC167-06)

Donde una adenda contradice al cuerpo o a una adenda anterior, **rige la más reciente**. Las marcas «⚠️» quedaron al
inicio de cada pasaje superado (cabecera, marca de la adenda 2, §3.1 a §3.3, §4, §5.1 a §5.4 y su riesgo conocido,
§7 y §7.5, y dentro de §8 los puntos 8.4, 8.5, 8.8, 8.9 y 8.12); el texto viejo se conserva. Sobre «todos los canales»
del §5.4 (a): la protegida es la que decide según la ventana (`seleccion.py` l. 14 y 98: las alertas sólo del OCR
anteriores al 2026-06-13 no entran al marco, A119), y entre ellas cuentan la tabla y el OCR, salvo las de §8.13.

### 9.2 Población y pesos (VC167-01)

La retrospectiva lee la **unión de los tres lotes del marco**: S159 (149 pasadas de 375), S162 (709) y S162b (1.200
negativos limpios restantes, el lote de B2), 2.058 en total, más las 330 lejanas y las 20 de control de vida del run
de las lejanas. El peso de cada pasada es **N_h / n_ok_h** por clase y estrato (volcán x cenit) sobre todo lo cargado
con dato (las SIN DATO no cuentan en n_ok_h); las lejanas pesan 1 (censo). **Decide la unión, no un lote**: las reglas
de qué lote decide de `PREREGISTRO_B.md` §5.5 y de B2 no rigen aquí. Con B2 dentro, el peso de un negativo limpio baja
(Chaitén z ≤ 40: de 143/19 = 7,5 con los pesos de B §3 a 143/71 = 2,0; cálculo del verificador). Es lo que hacía el
lector desde la adenda 2; esta sección lo escribe. El «859» del §3.1 era el lote de B y C: la equivalencia se mide en
todas las pasadas con grilla de los cuatro lotes.

### 9.3 Compuertas (VC167-02 y VC167-05)

a. **Controles**: si cae cualquiera de C1 a C9 (el control de vida C7 incluido), sale 3, «LECTURA NO LEGIBLE», y no se
   lee nada, ni el marco. Así lo hacía el código y así queda escrito, en lugar del «no decide» del §8.5 paso 5, que
   vale ahora sólo para más del 10 % de `far_tabla` SIN DATO (la RP da NO DECIDE y el resto se lee). «Sin run FAR» no
   se alcanza desde la línea de comandos (`--art-far` es obligatorio); la rama queda en el código sólo para la batería.
b. **Equivalencia**: si da NO EQUIVALENTE (máscara, VRP o publicación de cualquier brazo), sale **4**, «PAQUETE NO ES EL
   CODIGO», con los controles, la cobertura y la equivalencia impresos, y **no se lee la RP ni el §5**. Corta todo y no
   sólo ese brazo: la máscara y el VRP son los mismos en los tres, así que una publicación distinta en uno viene de un
   VRP distinto, que toca a los tres. Qué hacer entonces lo decide Nicolás.

### 9.4 Brazos y controles del §2 y del §4 en esta lectura (VC167-04)

- **PLACEBO** (K x 1,2): **C8**, el record de K re-corrido con el VRP x 1,2 (en `vrp_mw`, `f5_core_vrp_mw` y el VRP del
  cúmulo) pasa por el predicado del tablero y tiene que publicar donde K re-corrido publica en todas las pasadas (0
  discordantes en P1 y P2); **C9**, el placebo de M con el comparador (x 1,2 y x 0,8,
  `evaluador_comun.placebo_ganancia` sobre los pares de K consigo mismo) no puede dar MEJORA (d′ = 0). Si cae
  cualquiera, sale 3.
- **P-sinfiltro**: la vía publicando toda pasada con algún alertado en la caja, sin el predicado de cumbre, con su VRP.
  Se lee con las lecturas de `evaluar.py` y la prueba de signos contra K. **Informa, no decide.**
- **P-def** (caja M14): **no se corre aquí.** Su papel era separar el efecto de la ROI; eso ya lo midió V375-C sobre los
  mismos lotes (`resultado_run40116289866/INFORME.md`) y la caja quedó decidida en PD1 (§7.1).
- **Controles de B §4**: la cobertura contra la referencia (A108, por lote y clase, con las SIN DATO por nombre) y K
  re-corrido contra K publicado (0,95) ya los corría el lector. El control positivo, el nulo y NUNCA de B §4 prueban a
  `evaluar.py`, que aquí se usa sin cambios e identificado por sha256 (C4): no se repiten. El control positivo de la
  vía son C1, C5 y la equivalencia.
- **Controles de la curva** (§4: nulo de cenit parecido, sesgo de plataforma, ganancias): van con la curva, y en la
  retrospectiva informan (§9.6).

### 9.5 Magnitud M (§5.2; VC167-04 y VC167-03)

**Pares**: las alertas de MIROVA del marco con VRP (protegidas y bajo 1 MW) que el brazo y K publican con magnitud mayor
que 0; la magnitud de K es la de K re-corrido que muestra el predicado del tablero. Una pasada que publica uno solo sale
de M y se cuenta aparte (la ven P1 y P2). **Regla**: `evaluador_comun.decidir_estrato` en modo **«decide»**, con la
calibración simétrica (D-27, D-30, D-32) y el comparador d′ (D-28), **sobre la unión del marco: es el único corte que
decide (c)**. Sin peso de población: el evaluador común remuestrea por bloque noche-volcán, así que las protegidas
(censo) pesan más que en la población; dicho antes de medir, y por eso se informa también por clase. **Informan**, en
modo «informa»: por tramo de 10° de cenit, por volcán, por canal (alerta de la tabla o sólo del OCR) y por clase.
**A104**: la misma regla en T, O1 y O2; si O1 u O2, con sustrato, da otro estado de (c) que la unión, en cualquier
dirección, (c) pasa a DECIDE NICOLÁS. La mediana de VRP/MIROVA de `evaluar.py` se sigue imprimiendo y sólo informa.

### 9.6 La curva de cenit (§5.3) en la retrospectiva

Se calcula con `curva_cenit.py` para K y para cada brazo, condicionada y sin condicionar, sobre las alertas del marco,
y **sólo informa**. Con el conteo de diseño, el marco tiene a lo más 5 noches para el nulo de cenit parecido (con el
cenit de la lista; el lector usa el del run, que puede diferir algo), bajo el mínimo de 8 del §5.3: da SIN SUSTRATO por
construcción. Además las alertas bajo 1 MW son muestra (200 de 949), así que una noche entra sólo si sus dos pasadas
salieron sorteadas. **El criterio (d) se decide sólo en la sombra** (§9.8), donde están todas las pasadas.

### 9.7 La regla del §5.4 en código (VC167-03)

`criterios_retro` y `regla_adopcion` del lector. Lo que no es explícitamente favorable no cumple; las salidas que el
§5.4 no previó pasan a Nicolás.

| criterio | CUMPLE | NO CUMPLE | DECIDE NICOLÁS |
|---|---|---|---|
| (a) | ninguna protegida que K publica y el brazo calla, fuera de las de §8.13 (las pérdidas comunes cuentan) | una o más | nunca |
| (b) | P2 contra K GANA, EMPATE o SIN SUSTRATO, el silencio no da ENCIENDE DE MAS y P2-L no da PIERDE ni BLOQUEA | P2 PIERDE o BLOQUEA, o ENCIENDE DE MAS, o P2-L PIERDE o BLOQUEA | nunca |
| (c) | M MEJORA (en modo «decide» ya exige d′ MEJORA) o NEUTRO | EMPEORA, INDECIDIBLE o SIN SUSTRATO | marca A104 en M |
| (d), retrospectiva | informa, no decide | nunca | nunca |
| (d), sombra | REPRODUCE LA CURVA; o el extremo inferior del IC de D del paquete sobre el extremo superior del IC de D de K (cada uno con sus pares condicionados, como los arma `curva_cenit`) sin CAER MENOS QUE MIROVA | CAE MENOS QUE MIROVA, o CAE MAS o NO RESUELTO sin superar a K | SIN SUSTRATO o NULO SESGADO |

Por qué SIN SUSTRATO cumple en (b): con 4 bloques discordantes o menos, el brazo y K casi no difieren en errores, y el
texto pide «no PIERDE ni BLOQUEA». Por qué INDECIDIBLE y SIN SUSTRATO no cumplen en (c): el texto pide que no EMPEORE, y
el instrumento no lo certifica. Por qué CAE MENOS no cumple en (d): la meta es caer igual que MIROVA (§1), no menos. Así
queda fijado el «sobre el de K» del §5.4 (d).

**Retrospectiva de un brazo**: NO CUMPLE si algún criterio no cumple; si no, DECIDE NICOLÁS si alguno lo pide; si no,
«CUMPLE (falta la sombra)».

| salida de la RP | estado del paquete en la retrospectiva |
|---|---|
| ELEGIDO x, o SE QUEDA RADIANTE, sin marca A104 | el del brazo |
| NINGÚN BRAZO PASA EL VETO | NO CUMPLE (cada brazo calla una protegida que K publica) |
| NO RESUELTO (el ciclo incluido) | DECIDE NICOLÁS entre los no vencidos (en el ciclo, los tres), salvo que ninguno cumpla: NO CUMPLE |
| NO DECIDE (lejanas sin cobertura) | DECIDE NICOLÁS entre los tres, salvo que ninguno cumpla |
| con marca A104 | DECIDE NICOLÁS con el brazo de la unión, salvo que no cumpla |

**MISSION** (VC167-07) informa y no decide; se imprime contando también las protegidas de §8.13, rotulado así.

### 9.8 La sombra (VC167-09)

**La RP no se corre en la sombra.** La sombra lee el brazo que eligió la retrospectiva (o el que elija Nicolás si no
resolvió); las tres distancias desde los records (§8.8) sólo informan. Su lector (la vara 1, la M de §9.5, la curva y
el (d) de §9.7, con las mismas funciones de este lector) se escribe y se prueba con mutaciones antes del primer corte
de lectura de la ventana P, y pasa por Nicolás antes de leer.

### 9.9 Nombre (VC167-08)

En §8 y en el reporte del lector, «cercano» es el alertado más cercano **al cráter**; el «cercano» de `evaluar.py` y de B
y C es el más cercano al punto X0, Y0 de MIROVA. El reporte lo dice en el encabezado de la vara 1.

### 9.10 Qué cambió en el código y pruebas

`e_adenda2/leer_posicion_v375e.py`: C8 y C9; la compuerta de equivalencia con salida 4 (`codigo_salida`); P-sinfiltro;
`pares_magnitud`, `magnitud`, `estado_c`, `pares_k`, `control_placebo_m`, `placebo_k`, `curva`, `estado_d_sombra`,
`criterios_retro` y `regla_adopcion`; los rótulos de MISSION y de «cercano». `evaluar.py`, `curva_cenit.py` y
`scripts/evaluador_comun.py` no cambian. Batería y nulo: §9.11.

### 9.11 Batería y nulo

**Batería**: `e_adenda2/probar_adenda2.py`, 165 de 165 (`e_adenda2/probar_adenda2_salida.txt`), sobre datos sintéticos;
ninguna corrida sobre el marco ni sobre el run FAR.

**Nulo por mutaciones** (`e_adenda2/mutar_adenda2.py`, 114 mutaciones, dos a la vez, `e_adenda2/mutar_adenda2_salida.txt`):
identidad PASA, control de caída CAIDA; 111 atrapadas por aserción, 2 sobreviven y 1 cae. Lo que no quedó atrapado:

| mutación | en el nulo completo | qué se hizo | repaso |
|---|---|---|---|
| L20 | sobrevive | equivalente, como en las adendas anteriores | sin cambio |
| L85 (`NINGUN` deja de dar NO CUMPLE) | cae con `KeyError: 'ningun'` (caída no es atrapada) | se reescribió para que no caiga: `NINGUN` da DECIDE NICOLÁS | ATRAPADA |
| L94 (la curva toma toda pasada como publicada) | sobrevive | prueba nueva: si el brazo calla en el cenit alto, la curva condicionada pierde esas noches y la de K no | ATRAPADA |

El repaso (`e_adenda2/repasar_mutaciones.py L85 L94`, `e_adenda2/repasar_mutaciones_salida.txt`) corre la identidad, el
control de caída y esas dos mutaciones con la batería de 165: identidad PASA, control CAIDA, L85 y L94 ATRAPADA. Las
otras 111 no se volvieron a correr: el arreglo sólo agregó una prueba y cambió el texto de L85, así que con la batería
nueva sólo podrían dejar de ser atrapadas por aserción si bajo alguna de ellas la prueba nueva lanzara y la batería
cayera; eso no se midió (en la identidad no lanza). Con el repaso: 113 de 114 atrapadas por aserción, sobrevive L20
(equivalente).

### 9.12 Verificador limpio de la adenda 3 y el sello (S168)

Sonnet 5.5 con contexto limpio sobre `e6675da85` (`experiments/_s168/v375e_adenda3_verificador/INFORME.md`; servidor
2026-10-29 19:35 a 19:55 UTC), sin abrir el run de las lejanas ni el marco. Veredicto: **SELLABLE CON CAMBIOS MENORES,
ningún hallazgo de gravedad 3**. VC167-01, 02, 03, 05, 06, 07 y 08 cerrados; VC167-04 y 09 en parte. Re-corrió la batería
(165 de 165) y seis mutaciones con la batería nueva (L85, L94, L70, L77, L89 y L93: las seis ATRAPADA); no re-corrió el
nulo completo, y confirmó que §9.11 lo dice. Juzgó L20 equivalente.

**El código del lector no se tocó al sellar**: el sellado es el que midió el verificador. Los hallazgos se tratan así, por
texto:

| hallazgo | gravedad | tratamiento al sellar |
|---|---|---|
| VA168-01 si cae C3 (las listas), el lector sale 3 pero imprime igual todo el marco | 2 | lo que rige: con C3 caído la salida es 3, LECTURA NO LEGIBLE, y quien lee la salida no mira nada más allá de los controles; si se lee el marco por ese camino, la lectura queda contaminada y se dice. El arreglo en el código (pasar las fallas de C3 a `analizar`) va al lector de la sombra |
| VA168-02 sesgo de plataforma, ganancia pareja y ganancia que crece con el cenit (§4) no están en el lector | 2 | en la retrospectiva no se calculan (la curva informa y da SIN SUSTRATO, §9.6), y el «van con la curva» de §9.4 vale sólo para la sombra. Su consecuencia en (d) se fija en el pre-registro del lector de la sombra, que pasa por Nicolás antes de leer (§9.8) |
| VA168-03 `estado_d_sombra` exige además que la curva de K no sea SIN SUSTRATO ni NULO SESGADO | 1 | rige el código: esa condición es parte del CUMPLE de (d) en la sombra |
| VA168-04 marca A104 junto con EMPEORA en (c) | 1 | rige el código: manda la marca A104 (DECIDE NICOLÁS); «otro estado de (c)» es CUMPLE contra NO CUMPLE, no el veredicto crudo |
| VA168-05 marcas que faltaban (§2, §8.11) | 1 | agregadas al sellar; la mención de §8.4 en §9.1 es la aclaración de «cercano», no una marca de superado |
| VA168-06 V375-C midió la ROI sólo en detección y una mediana de magnitud | 1 | dicho: se renuncia a atribuir a la ROI la M de §9.5 y la curva |
| VA168-07 C8 pasa con 0 de 0; «por construcción» usa el cenit de la lista | 1 | en la lectura se informa cuántas pasadas con K entraron a C8; si son 0, C8 no prueba nada y se dice |
| VA168-08 redondeo de 0,01 km del cercano en la sombra | 1 | va al pre-registro del lector de la sombra |

## 10. Nota posterior a la lectura (S168, 2026-10-30): decisión de Nicolás sobre el brazo de la sombra

**Escrita después de la lectura retrospectiva** (`experiments/_s168/v375e_lectura_lejana/INFORME.md`, commit
`92b3b4208`). No cambia nada de lo sellado (§1 a §9): la regla de posición sellada eligió **cercano** (único brazo que
pasa el veto) y §9.8 ya decía que la sombra lee el brazo que eligió la retrospectiva.

Decisión de Nicolás (2026-10-30, ~00:20 UTC, en el chat de la coordinadora S169, relayada por ella), frase textual:
**«Cercano decide»**, en respuesta a «¿Qué brazo de posición lleva V375-E a la sombra?», con la opción «cercano decide
en la sombra, como dice la regla sellada, y radiante se informa al lado, rotulado como posterior a la lectura».

Queda así:
- En la sombra, **cercano decide** el §5.4 (a) a (d), con el lector de la sombra (§9.8), que se escribe, se prueba con
  mutaciones y pasa por un verificador limpio y por Nicolás antes de abrir datos de la ventana P.
- **Radiante se informa al lado** con el rótulo «posterior a la lectura»: la vía de `pipeline/` hoy publica con radiante,
  y el costo de cercano en las pasadas lejanas (104 de 329 contra 13 de radiante en la retrospectiva, VL168-01 y 04) se
  sigue mirando. La línea de radiante no decide nada.
- Pico no se lee en la sombra (en la retrospectiva dio lo mismo que radiante en todas las lecturas).

Lo que la sombra guarda para calcular cercano sin tocar `pipeline/` (comprobado contra `origin/main` `c42ee0eb7`): cada
record de la vía trae en `anomaly_pixels` todos los alertados con `fila`, `col` y `dist_km` desde el cráter, redondeada a
0,01 km (`pipeline/mirova_v750_codigo.py` l. 726 a 732), y el almacén no los filtra, ni los borra, ni les aplica el tope por cúmulo a un record con
`via_codigo_mirova` (`pipeline/store.py` l. 362, 401 y 455). Cercano es el menor `dist_km`; el redondeo sólo puede cambiar la
clase cuando ese mínimo queda a menos de 0,005 km del radio interior (VA168-08), y el lector de la sombra tiene que
contar esos casos y decir cómo los trata antes de leer (lo hace §11.5).

## 11. El lector de la sombra (S168, 2026-10-30)

Estado: **BORRADOR, SIN SELLAR**. Escrito antes de que exista ningún dato de la ventana P (la primera corrida de la
sombra con ventana es el 2026-11-03 a las 15:00 UTC). Cumple lo que pide §9.8 con la decisión de §10. Código:
`experiments/_s168/v375e_sombra/leer_sombra_v375e.py`; batería y nulo en la misma carpeta. Ningún dato de la ventana P
se abre hasta que la coordinadora se lo lleve a Nicolás con el verificador.

**Arreglos de S169** (verificador limpio de S168, `experiments/_s168/v375e_sombra/verificador/INFORME.md`, hallazgos
VS168-01 a 14): las reglas de abajo ya los incluyen, escritos antes que el código; la tabla de §11.11 dice qué hallazgo
cerró cada regla y dónde. Donde el texto y el código difieran, **manda el texto**.

### 11.1 Qué lee

- **Records de K**: los VIIRS 375 nocturnos de `data/mirova_equivalent/` de los 11 Tier A (lo que publica producción).
  **Records de la vía**: los VIIRS 375 de `data/sombra_codigo_mirova/` con `via_codigo_mirova` igual a `True`, pareados
  con el de K por volcán, sensor y `datetime_utc`. Las dos carpetas se leen de un commit de `origin/main` que el lector
  recibe por `--commit` (**obligatorio**, VS168-14) y escribe en su salida, junto con el sha256 de cada JSON.
- **Referencia de MIROVA**: el consolidado y el OCR de Mirova-v1, **pasados por ruta** (`--cons` y `--ocr`; el lector no
  baja nada, VS168-14), **congelados por sha256** en la salida (§3.3), sin las capas locales (la historia recuperada y el
  respaldo del 2026-04-08 son anteriores a la ventana P y no aportan filas en ella). Pareo a 120 s, regla D-9 en modo SN
  y protegida en lectura A, igual que la retrospectiva (`experiments/_s159/portes/01_poblacion.py`,
  `scripts/banco_paridad.py`). **Para el corte que decide la referencia se baja una sola vez**, después del rezago de S9
  (§11.4), y su sha256 queda en la lectura; filas que el scraper pierda o agregue después no cambian esa lectura, porque
  no se vuelve a escribir (§11.8, VS168-05).
- **Ventana P**: empieza **exactamente** el 2026-11-03. El argumento `--desde` existe sólo para que la batería pruebe que
  cualquier otro valor cae: S1 exige igualdad, así que un inicio posterior también cae (VS168-01). Termina en la noche de
  la parada (§11.8): si `--hasta` es posterior, el lector lee sólo hasta esa noche y lo dice. Sin Suomi NPP (§3.3): si
  aparece un record de `VIIRS_SNPP` se cuenta y se deja fuera.

### 11.2 Población, clases y pesos

Las etiquetas de `banco_paridad.etiquetar` sobre los records de K: `pos` con protegida (lectura A, 1 MW o más) es
`pos_prot`; el resto de `pos` es `pos_bajo` (en la ventana P toda alerta decide: es posterior al 2026-06-13, A119);
`neg_limpio` es `neg_pub` si K publica y `neg_resto` si no; `far_ref` con una fila `FALSO_POSITIVO` de la tabla es
`far_tabla`, y la que sólo trae filas del OCR es `far_ocr` (informa). `minima`, `sin_geometria` y `sin_info` se cuentan y
quedan fuera, como en la retrospectiva. **No hay muestreo: toda pasada pesa 1** (censo). La regla N-3 (§8.13) no puede
aplicar en la ventana P (es para antes del 2026-10-09); el lector la conserva y cuenta cuántas filas toca, que deberían ser 0.
Las pasadas **partidas** de la retrospectiva (`01_poblacion.py`, una pasada repartida en dos gránulos) no se marcan en la
sombra: la marca salía del run de la retrospectiva, que la sombra no tiene, y en los records no hay con qué
reconstruirla. Se acepta (VS168-12): la retrospectiva las informaba aparte, no decidían.

### 11.3 Brazos

- **Cercano decide** (§10): la vía con la distancia del alertado más cercano al cráter (`distancias_desde_record` y
  `variante` del lector sellado), por el predicado del tablero con node.
- **Radiante informa**, rotulado «posterior a la lectura»: el record de la vía tal como se guardó.
- **P-sinfiltro informa**: la vía publicando toda pasada con algún alertado.
- **K** es el control: lo que publica el tablero con el record de producción, con su magnitud mostrada.
- Pico no se lee.

### 11.4 Controles (si cae uno: sale 3, «LECTURA NO LEGIBLE», y no se imprime ni se escribe nada de la población)

Arreglo de VA168-01: todos los controles se calculan antes de imprimir nada de la población, y la salida con controles
caídos lleva sólo procedencia y controles.

**Qué se imprime de los controles (VS168-02).** Con un control caído, o antes de la parada (§11.8), de cada control se
imprime y se escribe sólo su nombre, OK o CAE, y un motivo genérico fijo (por ejemplo «S7 CAE: más del 10 % sin dato
en una clase de las que deciden»): ningún conteo por clase, ninguna lista y ningún nombre de pasada. El detalle de los
controles (conteos, listas, distancias) sale sólo en la lectura que decide, con todos los controles en OK. Los
conteos por clase, las horas y los nombres de pasadas son composición del marco. **Antes de la parada, los dos
contadores de la parada (noches y alertas acumuladas) se imprimen siempre, también con un control caído** (VL169-08,
ronda 2): son lo único que dice cuánto falta, no son una lectura, y sin ellos las primeras noches (en que S6 cae por
falta de sustrato) se leerían sólo como «LECTURA NO LEGIBLE». Con la parada alcanzada y un control caído no se
imprimen.

Los controles son:

- **S0 procedencia**: el sha256 (con fin de línea LF) del lector sellado `leer_posicion_v375e.py`, de `evaluar.py`, de
  `curva_cenit.py` y de `scripts/evaluador_comun.py` son los del tag `s168-v375e-cuerpo-sellado`. Si no, ni se cargan.
  **Además (VS168-04)**, los módulos que etiquetan y publican tienen que ser los del sello de este lector:
  `scripts/banco_paridad.py`, `scripts/clase_mirova.py`, `scripts/referencia_mirova_unificada.py`,
  `scripts/auto_audit_weekly.py` (pasadas diurnas y coordenadas), `scripts/calidad_referencia_mirova.py`,
  `pipeline/mirova_csv_loader.py`, `pipeline/diurno.py` y `frontend/index.html` (el predicado del tablero y los radios
  interiores). Sus sha256 quedan fijos en el código del lector al sellarlo; si uno no calza, no se carga nada. Por eso la
  lectura se corre **desde un checkout del tag del lector** (los records y la referencia se pasan por ruta desde donde
  estén). El sha256 del propio lector y el `git rev-parse HEAD` del checkout donde corre se imprimen (un archivo no puede
  llevar su propio sha256; lo fija el tag).
  **Ronda 2 (VL169-06)**: S0 fija también `pipeline/store.py` (qué pasada es diurna), `pipeline/profile.py`,
  `pipeline/f5_core.py` y `pipeline/profiles/mirova_equivalent.yaml` (los flags que esos módulos leen). Y el perfil no
  puede venir de afuera: si la variable de entorno `VRP_PROFILE` está puesta con un valor distinto de
  `mirova_equivalent`, S0 cae y no se carga nada; si no está puesta, el lector la fija en `mirova_equivalent` antes de
  importar nada (`banco_paridad` y `evaluador_comun` sólo la ponen si falta, así que un valor del shell ganaba). Es la
  única variable de entorno que cambia flags en los módulos que el lector carga (`grep` de `os.environ` en esos
  módulos: `VRP_PROFILE` y `GITHUB_SHA`, que sólo escribe la marca de régimen de un record nuevo).
  **Ronda 2 (VL169-05), linaje y checkout**: la rama del lector tiene `origin/main` mezclado (merge `dcec35a8c`), así que
  `c42ee0eb7` es ancestro y los sha de S0 son los del linaje de `main` en ese merge; **el tag del lector se corta sobre
  un commit que desciende de ese merge**. El checkout donde se lee tiene que haber hecho `git fetch origin` y tener
  `c42ee0eb7` y los `codigo_sha` de los records (S8 los compara con git; un sha que git no resuelve marca régimen, así
  que un checkout incompleto marcaría la lectura por una causa de procedimiento).
- **S1 ventana**: el corte empieza **exactamente** el 2026-11-03 (igualdad, VS168-01), termina en la noche del corte
  (§11.8), ningún record usado queda fuera de esa ventana y las claves de pasada (volcán, sensor y hora) no se repiten.
- **S2 predicado**: el control de identidad del predicado de `banco_paridad` (`control_identidad_predicado`) pasa, y en
  una pasada real de la vía con publicación el predicado responde a `distance_class` en las dos direcciones (summit
  publica, far no, de vuelta a summit publica). Sin ninguna pasada así, S2 no se puede comprobar y cae.
- **S3 un alertado**: en las pasadas con un solo alertado, radiante y cercano difieren en 0,0051 km o menos (el redondeo
  de las dos distancias), con al menos un caso.
- **S4 radiante es el record**: la variante radiante tiene la misma `distance_class` que el record guardado en todas las
  pasadas con alertados, **salvo** las que tienen `centroid_dist_km` a 0,0005 km o menos del radio interior (más el
  error de coma flotante): la vía guarda esa distancia redondeada a 0,001 km y la clase la calculó sin redondear, así
  que ahí el redondeo puede dar vuelta la clase sin que nada esté mal. Esas pasadas se excluyen de S4 y se cuentan
  (VS168-10).
- **S5 PLACEBO** (C8): K con el VRP x 1,2 publica igual que K en todas las pasadas, **con al menos una** pasada con
  record de K (VA168-07).
- **S6 placebo de M** (C9): K x 1,2 y x 0,8 con el comparador no da MEJORA, **y el comparador tiene que haber corrido**:
  si los pares de K consigo mismo no llegan al sustrato del evaluador común (5 pares en 3 noches), S6 cae, como S5 con
  0 de 0 (VS168-08). La lectura informa cuántos pares usó.
- **S7 cobertura** (A108): las pasadas sin record de la vía (o con la vía en `"sin_grilla"`) son SIN DATO y se listan
  por nombre en la lectura; si en alguna clase de las que deciden (`pos_prot`, `pos_bajo`, `neg_pub`, `neg_resto`,
  `far_tabla`) pasan del 10 %, cae. Una protegida SIN DATO que K publica, además, veta en (a) (§11.6, VS168-03).
- **S9 rezago de la referencia** (VS168-05, sólo con la parada alcanzada): la fila más nueva **de VIIRS 375** del
  consolidado (la tabla; ronda 2, VL169-07: no la de cualquier sensor, porque el scraper puede seguir escribiendo MODIS
  con VIIRS 375 atrasado) es de al menos **2 días** después de la noche del corte. Si no, la tabla y el OCR pueden no haber traído todavía
  las alertas de las últimas noches (una pasada quedaría `neg_limpio` porque su alerta no llegó): cae, y hay que volver a
  bajar la referencia más tarde.
- **S10 distancias completas** (VS168-11): ninguna pasada de la vía con alertados queda sin las distancias de
  `distancias_desde_record` (cúmulo, pico o algún `dist_km` faltante). Si hay alguna, cae: tratarla como «no publica»
  sería una pérdida silenciosa. La lectura lista cuántas hubo (deben ser 0).

**S8, marca de régimen (VS168-04; no hace caer la lectura, la marca).** Cada record trae `regimen.codigo_sha`, el commit
de `main` que lo escribió, y `regimen.perfil`. Para todas las pasadas del corte, los `codigo_sha` distintos de los
records de K y de la vía, y el de `--commit`, se comparan con git contra **la base de la ventana**. Además el perfil de
los records de K tiene que ser `mirova_equivalent` y el de la vía `sombra_codigo_mirova`. Un sha ausente, que git no
resuelve, o un perfil distinto cuentan como cambio.

**La base de la ventana (ronda 2, precisión de la coordinadora de S169).** No es un commit escrito a mano: es el
`codigo_sha` de los records **de la vía** de la primera noche de la ventana con records de la vía (el 2026-11-03 si la
sombra corrió ese día), o sea el commit de `main` del que corrió la primera sombra con datos. Si esa noche trae más de
un `codigo_sha`, la base es el del record más temprano y los otros se comparan contra ella como cualquier otro. Si el
record más temprano no trae `codigo_sha`, no hay base y la lectura se marca. La regla es que **todas las noches tienen
que tener el mismo régimen que la primera**, con la comparación de abajo. Por qué no `c42ee0eb7`: antes del 2026-11-03
pueden entrar a `main` arreglos en `scripts/`, en el workflow de la sombra o en `scripts/run_pipeline.py` (una auditoría
del 2026-10-30 encontró defectos ahí), y como esos archivos están en lo que se compara, contra `c42ee0eb7` todas las
noches saldrían marcadas.

**El hueco que esto abre, y cómo queda a la vista.** Con la base tomada de los datos, el lector ya no comprueba que la
primera noche haya corrido con el código que se pre-registró: si antes del 2026-11-03 entra a `main` un cambio que
altera la vía o K (no sólo un arreglo del workflow), la ventana entera sería coherente consigo misma y no marcaría. Para
que eso no pase en silencio, el lector **informa** (sin marcar) la misma comparación entre `c42ee0eb7` y la base, con la
lista de archivos que cambian; la lectura la imprime en la línea del régimen. Juzgar si esos cambios tocan lo que la
sombra mide es de Nicolás, con esa lista delante.

**Qué se compara (ronda 2, VL169-03 y VL169-04; regla adoptada por la coordinadora de S169).** Los archivos que cambian
entre la base de la ventana y el sha en `pipeline/`, `volcanoes.yaml`, `scripts/run_pipeline.py` y
`.github/workflows/sombra-codigo-mirova.yml` (`git diff --name-only`), y de cada uno:
- un `.py` (los de `pipeline/` y `scripts/run_pipeline.py`) cuenta como cambio si su **árbol sintáctico sin docstrings**
  difiere (`ast.dump` de las dos versiones, quitando el docstring de módulo, clases y funciones): un comentario, un
  docstring o la cabecera FICHA no marcan; cualquier otra diferencia sí, también en código que comparten la vía de
  VIIRS 375, VIIRS 750 y MODIS (separar por función abriría el hueco de A89). Un `.py` que aparece, desaparece o no se
  puede leer marca;
- en `pipeline/profiles/` cuentan sólo `mirova_equivalent.yaml` y `sombra_codigo_mirova.yaml` (el segundo hereda del
  primero); los demás perfiles no los carga ni K ni la vía, y un cambio ahí no marca. Un cambio en esos dos marca;
- `pipeline/grillas_mirova.yaml` se lee en las dos versiones y de cada volcán se quitan **sólo** `roi_v750` y
  `roi_modis` (que la vía de VIIRS 375 no lee: arma su caja con `roi1_half_m`); el resto (`epsg`, `x0`, `y0`,
  `centro_lat`, `centro_lon` y cualquier otra clave) se compara por igualdad. Un archivo que no se puede leer, un volcán
  nuevo o una clave nueva marcan;
- cualquier otro archivo de esas rutas que cambie (`volcanoes.yaml`, el workflow, un `.json` o `.yaml` de `pipeline/`)
  marca.
Por qué así: con `pipeline/` entero la marca era casi segura en 30 noches (35 commits tocaron `pipeline/` en `main`
desde el 2026-10-01, casi todos de otra vía o con banderas apagadas, verificador de S169) y el CUMPLE automático
quedaba inalcanzable; y faltaban `volcanoes.yaml` (radio interior y coordenadas que deciden summit o far) y el llamador
`scripts/run_pipeline.py` (A6). Lo que esta regla no abre: un cambio real de la vía en un `.py`, en `x0`, `y0`, centro o
`epsg`, o en el perfil, sigue marcando. Lo que deja: un cambio en código compartido pero ajeno (MODIS o VIIRS 750 dentro
de `mirova_v750_codigo.py`) sigue marcando, y Nicolás lo descarta mirando el diff. Si hay cambio, la
lectura se imprime igual, rotulada con los commits y los archivos que cambiaron, y **un CUMPLE de (b), (c) o (d) pasa a
DECIDE NICOLÁS** (§11.7). Por qué marca y no cae: no es el instrumento el que falla sino la ventana la que mezcla dos
detectores (A104); Nicolás tiene que ver la lectura para decidir. Por qué un NO CUMPLE se queda: con dos regímenes
mezclados no se puede certificar que la vía cumpla, pero una protegida perdida o un empeoramiento medido siguen siendo
razones para no adoptar; dejarlo en NO CUMPLE es lo conservador. (La propuesta del traspaso decía «LECTURA NO LEGIBLE
y decide Nicolás»; se eligió la variante del verificador, que deja ver la lectura. La primera versión comparaba
`pipeline/` entero por nombre de archivo; la ronda 2 la reemplazó por la regla de arriba.)

### 11.5 El borde del radio (VA168-08)

Una pasada es **de borde** si el cercano queda a menos de 0,005 km del `inner_radius_km` del volcán, porque ahí el
redondeo a 0,01 km puede cambiar la clase. Se tratan con la regla inclusiva sobre el valor redondeado (summit si es igual
o menor), como la prueba de la sombra, y se listan por nombre. El lector repite todo el §11.7 con la clase de esas
pasadas dada vuelta; **si el estado del paquete cambia, el paquete pasa a DECIDE NICOLÁS**.

**Escenario mixto adverso (VS168-09).** Además de la vuelta conjunta, el lector repite el §11.7 con la vuelta que más
perjudica a cercano: las pasadas de borde que son alertas (`pos_prot`, `pos_bajo`) y hoy quedan en summit pasan a far
(callan), y las que no son alertas (negativos y lejanas) y hoy quedan en far pasan a summit (publican). Si ese conjunto no
está vacío y es distinto del de la vuelta conjunta, se calcula aparte; si cualquiera de las dos vueltas cambia el estado,
DECIDE NICOLÁS. La salida dice qué vuelta lo cambió.

### 11.6 Lecturas

Cada una para cercano (decide), radiante (informa) y P-sinfiltro (informa), contra K, con las funciones sin cambios de
`evaluar.py` y del lector sellado:

- **(a)** P1: protegidas que K publica y el brazo calla, por nombre. No se corre la regla de posición (§9.8), así que no
  hay «pérdidas comunes»: toda protegida perdida que K publica veta. **Una protegida SIN DATO** (sin record de la vía, o
  con la vía en `"sin_grilla"`) **que K publica cuenta como perdida y veta** (lo conservador: no se sabe si la vía la
  habría publicado, y §5.4 (a) no admite pérdidas de protegidas que K publica). Todas las protegidas SIN DATO se listan
  por nombre, con K publica o no (VS168-03).
- **(b)** P2 contra K por la prueba de signos por bloque noche-volcán, silencio en negativos limpios, y P2-L (sólo
  `far_tabla`, error = publicar). Si falta una de las dos clases de negativos (`neg_pub` o `neg_resto`), el silencio
  queda «SIN SUSTRATO» y (b) se lee sin él, y la salida lo dice; con la parada alcanzada eso no debería pasar. Si
  además P2 contra K da SIN SUSTRATO, el CUMPLE de (b) es **por falta de evidencia** y la salida lo rotula así (no cambia
  el estado: la tabla de §9.7 ya lo prevé).
- **(c)** M de §9.5: `evaluador_comun.decidir_estrato` en modo «decide» sobre toda la ventana, con los cortes por cenit,
  volcán, canal y clase en modo «informa». **En la sombra, M en SIN SUSTRATO da DECIDE NICOLÁS, no NO CUMPLE**
  (VS168-06): la última frase del §5.4 prevé el caso («si la sombra no tiene sustrato a las 30 noches, la decisión es de
  Nicolás con lo que haya») y la lectura sólo existe con la parada alcanzada. INDECIDIBLE y EMPEORA siguen sin cumplir.
- **(d)** la curva de §9.6 con `curva_cenit` (condicionada decide, sin condicionar informa) y su estado con
  `estado_d_sombra`, más los controles de la curva del §4 (VA168-02, abajo), **corridos para el brazo y para K**.
- **Lejanas** (VL168-01 y 04, informa): cuántas `far_tabla` publica cada brazo y K, por nombre. Lo correcto es no
  publicar; no decide nada. También se informan las `far_ocr` de cada brazo y de K (VS168-12).
- **Cobertura de K** (VS168-12, informa): cuántas alertas nocturnas de MIROVA de VIIRS 375 de la ventana no tienen record
  de K a 120 s (`banco_paridad.alertas_sin_record`), por volcán. Son invisibles para P1 y para la parada.
- **MISSION** informa (§9.7).

**A104 en una ventana sin tramos**: la ventana P es un solo régimen (sin Suomi NPP, después de #535 y del hito del OCR),
así que la marca A104 de §8.5 y §9.5 no aplica. En su lugar se informa, sin decidir, la M y el P2 de la primera mitad de
las noches contra la segunda (mitad por fecha de noche: la noche de la mediana va a la primera).

**Controles de la curva del §4 (VA168-02)**, sobre las pasadas con alerta de MIROVA, **una vez para el brazo y otra
para K** (VS168-07: `estado_d_sombra` compara la curva del brazo con la de K, así que un sesgo en la de K invalida la
comparación igual que uno en la del brazo):
- nulo de cenit parecido: ya está dentro de `curva_cenit.veredicto` (NULO SESGADO);
- sesgo de plataforma (`curva_cenit.sesgo_plataforma`): si da SESGADO para el brazo o para K, (d) pasa a DECIDE NICOLÁS;
- ganancia pareja (x 1,2 a todas las pasadas): la mediana de D no se mueve más de 0,01 en log10; si se mueve, para el
  brazo o para K, el instrumento está roto y (d) pasa a DECIDE NICOLÁS;
- ganancia que crece con el cenit (1 + 0,01 por grado sobre 20°): la mediana de D tiene que subir; si no sube, para el
  brazo o para K, la curva no ve el cenit y (d) pasa a DECIDE NICOLÁS.
Con la curva en SIN SUSTRATO estos controles se informan y no cambian nada (el estado ya es DECIDE NICOLÁS).

### 11.7 Regla del paquete en la sombra

Para cercano: (a) CUMPLE si no hay ninguna protegida que K publica y cercano calla (las SIN DATO que K publica incluidas,
§11.6), si no NO CUMPLE; (b) como en la tabla de §9.7; (c) como en la tabla de §9.7, salvo que SIN SUSTRATO da DECIDE
NICOLÁS (§11.6); (d) el `estado_d_sombra` de §9.7 con la curva condicionada, llevado a DECIDE NICOLÁS por los controles
de la curva del brazo o de K (§11.6). **Con la marca de régimen de S8, un CUMPLE de (b), (c) o (d) pasa a DECIDE
NICOLÁS** (§11.4). **Estado**: NO CUMPLE si algún criterio no cumple; si no, DECIDE NICOLÁS si alguno lo pide (o si lo
pide el borde, §11.5); si no, CUMPLE. Junto con la retrospectiva (CUMPLE, falta la sombra, con cercano), un CUMPLE de la
sombra es «el paquete cumple» del §5.4, y la adopción (PD4) sigue siendo decisión de Nicolás con A45.

**Lo que informa no decide, y no se imprime como si decidiera** (VS168-13 y VS168-14): de radiante y de P-sinfiltro se
imprimen sólo las lecturas, sin criterios ni estado (ni en pantalla ni en el JSON); el estado del paquete es sólo el de
cercano. Las mitades (§11.6, en lugar de A104) informan: si discrepan entre sí no cambian ningún criterio ni el estado.

### 11.8 Parada (§3.3) y el corte que decide

El lector cuenta las **noches** (fechas de noche con al menos una pasada de la población con dato, o sea con record de
la vía) y las **alertas que deciden** (pasadas `pos_prot` y `pos_bajo` con dato), acumuladas noche por noche desde el
2026-11-03. La parada se alcanza en la **primera noche N** en que hay 30 noches **y** 40 alertas acumuladas («lo que
llegue último»).

**El corte que decide (VS168-01) es la lectura que termina en N.** El lector calcula N con todo lo que tiene hasta
`--hasta` y:
- si N existe y `--hasta` es N o posterior, **lee sólo hasta N** (la población, los controles y la lectura se recalculan
  sobre las noches del 2026-11-03 a N) e imprime que recortó; las pasadas posteriores a N no entran a nada;
- si no hay N todavía, **no hay lectura**: imprime sólo procedencia, los controles (con la regla de impresión de §11.4) y
  los dos contadores de la parada (noches y alertas). No hay cortes provisionales con criterios, estado ni lecturas que
  mirar: lo que no existe no se puede usar para parar antes ni para seguir esperando un resultado.
Si a las 30 noches no hay 40 alertas, la decisión de seguir o de leer con lo que haya es de Nicolás (§5.4); leer con lo
que haya exige un pre-registro nuevo, porque este lector no lee antes de N.

**Salidas** (`--dir-salida`, obligatorio): nunca se sobrescribe un archivo. La lectura que decide se escribe como
`lectura_sombra_corte_<N>.txt` y `.json`. Toda otra corrida (antes de la parada, o con un control caído) se escribe como
`controles_sombra_<corte>_<hora UTC>.txt` y `.json`, con `<corte>` igual a N si ya existe o a `--hasta` si no. Cada
salida lleva el sha256 de la referencia y de los records.

**Una sola lectura por ventana, no por nombre ni por carpeta (ronda 2, VL169-01; decisión de la coordinadora de S169).**
N depende de las etiquetas, y las etiquetas de la referencia: con otra referencia N se mueve y el nombre del archivo
cambia, y con otra carpeta el nombre no choca (el verificador de S169 lo reprodujo con `probe_b1b.py`: dos lecturas,
de los cortes 11-11 y 11-12, en la misma carpeta). Así que la regla es por ventana:
- **Registro de la ventana.** Cada lectura que decide agrega, **antes de imprimir la lectura**, una línea a
  `experiments/_s168/v375e_sombra/lecturas/REGISTRO_VENTANA_P.jsonl` (en el checkout del lector; sólo se agrega, nunca
  se reescribe) con N, la hora del servidor, el sha256 de la referencia y de cada JSON de records, `--commit`, el sha256
  del lector y la carpeta de salida. No lleva el estado del paquete. **Ese registro se commitea a `loop/activo` antes de
  mostrar la lectura a nadie** (ni a la coordinadora ni a Nicolás).
- **El lector se niega (sale 2, sin escribir nada y sin imprimir ninguna lectura)** si: en la carpeta de salida existe
  cualquier `lectura_sombra_corte_*`; o el registro local ya tiene una lectura; o el registro de `origin/loop/activo` ya
  tiene una lectura (lo lee con `git show`); o `origin/loop/activo` no se puede resolver (falla cerrada: hay que hacer
  `git fetch origin`). Se comprueba antes de calcular nada.
- **Una segunda lectura no puede pasar en silencio.** Con otra carpeta o con otra referencia en el mismo checkout, la
  rechaza el registro local; desde otro checkout, la rechaza el de `loop/activo`; y si dos lecturas se hicieran antes de
  que el registro llegara a `loop/activo`, al commitearlo quedan dos líneas, visibles. Una segunda lectura con otra
  referencia exige un pre-registro nuevo.

**Códigos de salida**: 0 lectura que decide escrita; 3 LECTURA NO LEGIBLE (cae un control, o `VRP_PROFILE` con otro
valor); 5 parada no alcanzada (sólo controles y contadores); 2 la ventana ya se leyó (o no se puede comprobar) o el
archivo de salida ya existe.

### 11.9 Lo que este lector no hace

No toca `pipeline/`, `data/` ni `frontend/`, no despacha nada y no corre la regla de posición. No lee MODIS ni VIIRS 750
(sus pre-registros tienen sus propios lectores). No lee el día.

### 11.10 Pruebas y estado

- **Batería y nulo, historia** (cifras de cada momento; las vigentes están en el punto siguiente): en S168 la batería
  daba 104 de 104 y el nulo tenía 55 mutaciones; en la primera ronda de S169, 190 de 190 y 111. Ninguna versión del nulo
  se ha corrido.
- **Vigente (S169, ronda 2)**: batería y nulo con las cifras de §11.12 y de
  `experiments/_s169/v375e_lector_arreglos/INFORME.md`, sección «Ronda 2». La batería cubre, sobre escenas sintéticas
  con el predicado del tablero con node, `banco_paridad` real y las dependencias del tag: clases, población (Suomi NPP
  fuera), `cargar_records`, brazos, borde y sus dos vueltas, los controles S0 a S10 en verde y en rojo, la marca S8, que
  con un control caído o antes de la parada no salga la población, el corte en la noche de la parada, el registro de la
  ventana, el cableado de `leer_brazo` y `main()` de punta a punta.
- **S169, primera ronda** (historia): con los arreglos de §11.11 la batería pasó a 190 aserciones y el nulo a 111
  mutaciones (las 55 de S168, seis reescritas; las 14 que el verificador creía sobrevivientes, en 17 mutaciones; y 39 de
  las reglas nuevas). Cada regla nueva se vio en rojo rompiéndola a mano en una copia
  (`experiments/_s169/v375e_lector_arreglos/ver_en_rojo.py`).
- **V04 es equivalente** y se espera que sobreviva al nulo: cruzar P2 contra K con P2-L en la llamada a
  `criterios_sombra` no cambia (b), porque en el alfabeto de `regla_signos` el conjunto que (b) acepta para P2 (GANA,
  EMPATE, SIN SUSTRATO) es el complemento exacto del que rechaza para P2-L (PIERDE, BLOQUEA). Desde la ronda 2 está
  declarada en `mutar_sombra.py` (`EQUIVALENTES`, VL169-10) y la salida la rotula.
- **Caídas (ronda 2, VL169-02)**: los resultados del lector se envuelven en un dict que devuelve vacío para una clave
  que falta (una clave quitada se ve como aserción fallida), y una excepción dentro de una sección se registra como
  **CAÍDA**, no como aserción fallida: la batería sale 2. El nulo cuenta ATRAPADA sólo con salida 1 (alguna aserción
  falló y ninguna sección se cayó); con salida 2, CAÍDA. Lo comprueban dos controles: `CONTROL` (rompe la importación)
  y `CONTROL_SECCION` (lanza dentro de una sección); los dos tienen que salir CAÍDA.

### 11.11 Arreglos del verificador limpio de S168 (S169, 2026-10-30)

Cada regla nueva quedó escrita en la sección que dice la tabla antes de tocar el código; cada una tiene una aserción en
`probar_sombra.py` que se vio en rojo rompiendo la regla a mano en una copia, y una mutación en `mutar_sombra.py`.

| hallazgo | gravedad | regla (sección) | tratamiento |
|---|---|---|---|
| VS168-01 el corte que decide queda libre | 3 | §11.1, §11.4 S1, §11.8 | `--desde` igual a 2026-11-03; el corte que decide termina en la primera noche de la parada; antes, sólo controles y contadores; salidas sin sobrescribir con la fecha del corte |
| VS168-02 con un control caído se imprime el detalle | 2 | §11.4 | sólo nombre, OK o CAE y un motivo fijo; el detalle sólo en la lectura que decide |
| VS168-03 protegida SIN DATO que K publica | 2 | §11.6 (a), §11.4 S7 | veta en (a) y se lista; S7 conserva su 10 % |
| VS168-04 régimen y módulos sin identificar | 2 | §11.4 S0 y S8, §11.1 | S0 fija ocho archivos más; `--commit` obligatorio; S8 marca el cambio de `pipeline/` contra `c42ee0eb7` y lleva los CUMPLE de (b), (c) y (d) a DECIDE NICOLÁS (variante del verificador, no la del traspaso: razón en S8) |
| VS168-05 la referencia pierde filas y tiene rezago | 2 | §11.1, §11.4 S9, §11.8 | rezago de 2 días sobre el corte; el corte que decide se escribe una sola vez |
| VS168-06 (c) SIN SUSTRATO da NO CUMPLE | 2 | §11.6 (c), §11.7 | DECIDE NICOLÁS |
| VS168-07 controles de la curva sólo del brazo | 2 | §11.6 | también para K |
| VS168-08 la batería no ataba (b), (c), (d) ni S6 | 2 | §11.4 S6 | S6 exige sustrato e informa sus pares; aserciones por valor de cada criterio y del estado, la rama sin `neg_pub` y S6 en verde y en rojo |
| VS168-09 sólo la vuelta conjunta del borde | 1 | §11.5 | se agrega el escenario mixto adverso |
| VS168-10 S4 puede caer por redondeo | 1 | §11.4 S4 | se excluyen las de radiante a 0,0005 km del radio |
| VS168-11 alertados sin distancias | 1 | §11.4 S10 | control nuevo, deben ser 0 |
| VS168-12 lo que la retrospectiva informaba | 1 | §11.2, §11.6 | se informan las alertas sin record de K y las `far_ocr`; las listas de la lectura van completas al JSON (las de `lecturas_far` del lector sellado se quedan en 40); la marca de partida se acepta sin reconstruir |
| VS168-13 los brazos que informan imprimen estado | 1 | §11.7 | sin criterios ni estado para radiante y P-sinfiltro |
| VS168-14 `--commit` opcional, referencia, mitades | 1 | §11.1, §11.7 | `--commit` obligatorio; la referencia se pasa por ruta; las mitades informan |

**Lo que quedó aceptado sin código** (gravedad 1, con su razón): la marca de partida (§11.2); las listas de
`lecturas_far` truncadas a 40 por el lector sellado, que no se toca (el número total sí sale entero); el cenit tomado de
`sensor_zenith_deg` del record de K en lugar del `geometria_centro` del run (la sombra no tiene run; el verificador lo
dejó SIN VERIFICAR y aquí también queda así); y el Wilson que `evaluar.lecturas` aplica a `neg_resto` como si fuera
muestra, que es más conservador que un conteo exacto para ver ENCIENDE DE MAS y es la función sellada sin cambios.

### 11.12 Ronda 2: verificador limpio de S169 (2026-10-30)

Verificador limpio (Sonnet) sobre `983f6f28d`: SELLABLE CON CAMBIOS, un hallazgo de gravedad 3 y seis de gravedad 2
(`experiments/_s169/v375e_lector_verificador/INFORME.md`, en la rama `loop/activo`). Las decisiones de cómo cerrarlos
son de la coordinadora de S169 y están escritas en la sección que dice la tabla, antes que el código.

| hallazgo | gravedad | regla (sección) | tratamiento |
|---|---|---|---|
| VL169-01 «una sola vez» era por nombre y carpeta, no por ventana | 3 | §11.8 | una sola lectura por ventana: rc 2 sin escribir nada si hay cualquier `lectura_sombra_corte_*` en la carpeta, si el registro local o el de `loop/activo` ya tiene una lectura, o si `loop/activo` no se resuelve; registro de la ventana que se commitea a `loop/activo` antes de mostrar la lectura; probado con el caso de `probe_b1b.py` |
| VL169-02 el nulo contaba una caída como ATRAPADA | 2 | §11.10 y esta sección | en la batería una excepción dentro de una sección es CAÍDA (sale 2), no FALLA; el nulo cuenta ATRAPADA sólo con salida 1 y ninguna sección caída; control nuevo `CONTROL_SECCION` (lanza dentro de una sección: tiene que salir CAÍDA) |
| VL169-03 S8 marcaba por todo `pipeline/` | 2 | §11.4 S8 | AST sin docstrings para los `.py`; sólo los dos perfiles que cargan K y la vía; `grillas_mirova.yaml` sin `roi_v750` ni `roi_modis` |
| VL169-04 S8 no miraba lo de fuera de `pipeline/` | 2 | §11.4 S8 | se suman `volcanoes.yaml`, `scripts/run_pipeline.py` y el workflow de la sombra |
| (precisión de la coordinadora) la base de S8 | 2 | §11.4 S8 | la base deja de ser `c42ee0eb7`: es el `codigo_sha` de los records de la vía de la primera noche; todas las noches tienen que tener su régimen; la comparación entre `c42ee0eb7` y la base se informa, sin marcar (el hueco que abre está escrito en S8) |
| VL169-05 S8 y la batería dependían de objetos git | 2 | §11.4 S0 | merge de `origin/main` en la rama (`dcec35a8c`): `c42ee0eb7` es ancestro; S0 recalculado sobre ese árbol (cambió `auto_audit_weekly.py`); el tag se corta sobre un descendiente de ese merge; el checkout de lectura hace `git fetch origin` |
| VL169-06 VRP_PROFILE y módulos sin sha | 2 | §11.4 S0 | S0 cae si `VRP_PROFILE` trae otro perfil y lo fija si falta; suma `store.py`, `profile.py`, `f5_core.py` y `profiles/mirova_equivalent.yaml` |
| VL169-07 S9 medía la tabla de cualquier sensor | 2 | §11.4 S9 | sólo filas de VIIRS 375 |
| VL169-08 sin contadores con un control caído antes de la parada | 1 | §11.4 | los contadores salen siempre antes de la parada |
| VL169-09 la comprobación en rojo es por grupos | 1 | (ninguna) | aceptado: la cierra el nulo, que rompe una regla por copia; los grupos se eligieron para no taparse y los que se taparon se repitieron |
| VL169-10 V04 equivalente sin marca en el script | 1 | §11.10 | `EQUIVALENTES` en `mutar_sombra.py`, declarada antes de correr y rotulada en la salida |

Seguimientos del verificador que quedan **aceptados sin código**: dos corridas simultáneas podrían pisar la lectura
(el registro de la ventana y el commit a `loop/activo` lo harían visible); no hay instantánea diaria de la referencia
(VS168-05 queda cerrado por S9 y por la lectura única, no por captura); con la parada alcanzada y un control caído el
nombre `controles_sombra_<N>_…` revela N, no la lectura; y `--hasta` sin ceros compara como texto (la parada manda).
