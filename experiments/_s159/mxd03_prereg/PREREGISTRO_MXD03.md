# Pre-registro S159 (tarea 1.30, decisión D-19): geolocalización MODIS desde MxD03, sobre K

**BORRADOR PARA EL SELLO DE NICOLÁS.** Escrito el 2026-10-21 por una sesión lateral del loop, antes de correr ningún
brazo y antes de escribir una sola línea en `pipeline/`. Nada de esto se despacha sin su «sí» escrito, sin el candado
del §8 (evaluador con pruebas que fallan por la razón correcta y verificador con contexto limpio) y sin el tag del §9.
Todos los números de este documento salen de scripts de esta carpeta, con su salida al lado (regla S91); los del
frente M, de `experiments/_s159/m/` y su verificador. Las decisiones que quedan abiertas están en el §11, con una
recomendación en cada una.

Evidencia de esta carpeta (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\mxd03_prereg\`):

| script | salida | qué mide |
|---|---|---|
| `sustrato_modis.py` | `sustrato_modis_salida.txt` | con qué detector están escritos los records MODIS y cuántos hay por cenit y lado |
| `sustrato_mirova_modis.py` | `sustrato_mirova_modis_salida.txt` (marzo a 16-oct), `sustrato_mirova_modis_feb_salida.txt` (desde febrero, para los controles), `sustrato_mirova_modis.json` | población contra MIROVA, no condicionada a lo que publica K |
| `tif_modis_cobertura.py` | `tif_modis_cobertura_salida.txt`, `tif_modis_14sep_crs_salida.txt` | GeoTIFF MODIS de MIROVA: cuántos, de cuándo, en qué grilla |
| `tif_modis_para_alertas.py` | `tif_modis_para_alertas_salida.txt` | cuántas alertas MODIS de la ventana tienen TIF de su pasada |
| `tiempo_modis_probe_m.py` | `tiempo_modis_probe_m_salida.txt` | segundos por record MODIS en el runner (log del probe M) |
| `tiempo_por_dia_reproc.py` | `tiempo_por_dia_reproc_salida.txt` | minutos por día-volcán de un reproceso real, separados en descarga y proceso |

## 1. La pregunta, y por qué ahora

**La pregunta en una frase.** Si el pipeline ubica cada píxel MODIS con la geolocalización con corrección de terreno
de MxD03 (lo que declara MIROVA) en vez de interpolar la grilla de 5 km del propio L1B, ¿cambia lo que la réplica
publica, sin perder ninguna alerta protegida, sin publicar más donde MIROVA calló, y poniendo el calor donde lo ve
MIROVA?

**El fenómeno.** Un volcán visto de lado por MODIS (cenit sobre 40°) cae en un píxel de varios kilómetros, y el L1B sólo
trae la latitud y longitud cada 5 píxeles. El pipeline estira esa grilla gruesa a 1 km con una interpolación lineal
(`pipeline/process_modis.py:265-266` lee la grilla, `:292-295` la interpola, `:385-396` es `_interp_geo`), y no usa el
MxD03 que baja y exige: `calculate_vrp` lo recibe y lo ignora (`process_modis.py:513`, «accepted for API compatibility
but not used»), y `scripts/run_pipeline.py:223-230` salta el gránulo si el MxD03 falta. El frente M midió que así el
píxel del cráter queda corrido hacia el lado del sensor: mediana **2,82 km** con cenit de 40 a 50° y **5,04 km** sobre
50° del lado del frame 0 (1,10 y 2,48 del lado contrario; 1,10 y 0,79 cerca del nadir con n = 4 cada uno), y que en
Láscar, con los mismos píxeles detectados, el cúmulo pasa de 2,54 a 0,59 km del cráter (`experiments/_s159/m/INFORME.md`
H2 y H3, confirmados por el verificador).

**Por qué ahora.** La decisión D-19 dejó este pre-registro para cuando K estuviera en producción (las dos protegidas
que MxD03 perdía bajo C0 caían por el Test 1 integrado, que K apagó; `tasks/LOOP_OBJETIVOS.md` D-19 en `loop/activo`).
K está en producción desde el 2026-10-18 09:57:30 UTC y el histórico MODIS entero está escrito con K: los 14.565
records MODIS de los 11 Tier A, de 2025-02 a 2026-10, tienen `regimen.perfil` igual a `_s154_reproc_k_historico` o
`mirova_equivalent` (`sustrato_modis_salida.txt`). No hay frontera de régimen (A104, A85) dentro de la ventana de este
A/B.

**Lo que el frente M dejó en pie y lo que el verificador corrigió, y que este diseño absorbe.**
1. La población de M estaba condicionada a lo que K publica (records `summit`): cualquier perturbación de la posición
   apaga más de lo que enciende (A109). Aquí la población es el **censo** de las pasadas MODIS de la ventana, con la
   etiqueta de MIROVA, publique K o no (§5).
2. 4 de los 12 cambios de M fueron de **fondo** (`t_bg_k` se mueve 0,2 a 0,4 K y la magnitud cruza cero), no de
   posición, y 1 apagado ocurrió sin que el píxel saliera del círculo. Aquí la posición y el fondo se atribuyen por
   separado en las pasadas que cambian (§3, atribución), y cada pieza se mide en el estrato donde puede actuar (A114, §5).
3. Bajo 40° de cenit M no tenía dato. Aquí entran todos los tramos: ≤ 25°, 25 a 40°, 40 a 50° y sobre 50°, por lado
   del barrido. Es justo bajo 40° donde está el poder del veto: 44 de las 50 protegidas de la ventana (§5).
4. El pareo con MIROVA a la hora exacta pierde pasadas en el borde entre gránulos (verificador de M, 121 de 5.815).
   Aquí el pareo es una **dependencia declarada** del trabajo de `experiments/_s159/pareo_modis/`, con regla por defecto
   (§6).

**Lo que este A/B NO pregunta.** Si el remuestreo a la grilla UTM de MIROVA (D17, D28) explica el resto de la diferencia
de posición o de magnitud; si D25 (fondo por vecinos) debe escribirse en MODIS; por qué las dos protegidas de Chillán
del 12 y el 15 de octubre (cenit 58°) no tienen detección en ningún brazo (M H4: la geolocalización no es la causa).

## 2. Las tres preguntas de `docs/MISSION.md`

**1. ¿Está en los papers de MIROVA?** **Sí, con dos matices.** Coppola et al. 2026 (Scientific Data,
`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`, p. 4, primer párrafo; leído
renderizando la página a imagen, A95): para MODIS «Level 1B calibrated radiance products (MOD021KM and MYD021KM) were
used [...] together with the corresponding MOD03 and MYD03 Terrain-Corrected Geolocation products», y lo mismo para
VIIRS con VNP03 y VJ103, «accessed via the NASA LANCE/LAADS distribution systems». Matices:
- **Voz pasiva y producto de archivo.** La frase describe la cadena con que se armó el conjunto global 2000 a 2025, no
  dice con verbo activo que el sistema NRT lo aplique (regla S99 de MISSION). A favor de que es la misma cadena: nombra
  LANCE, que es la distribución de tiempo casi real. Se declara como respaldo fuerte, no como cita del NRT.
- **Coppola 2026 no está en la lista de 11 papers de MISSION**, aunque es del grupo MIROVA (Torino) y A105 ya lo usa
  como autoridad. Agregarlo es decisión de Nicolás (§11, punto 9).
- Coppola 2016a (`sp426.5.pdf`, p. 183, «Data extraction from MODIS Level 1B granules») dice que se extraen «pixel(s)
  geolocation (latitude and longitude)» de los gránulos de nivel 1, sin nombrar MOD03; y en p. 197 («Satellite viewing
  geometry») que con ángulos de barrido altos baja la precisión de la geolocalización y los errores pueden ser «up to
  several kilometres». O sea: **ni MIROVA espera una posición exacta sobre ~50°**, y eso acota lo que la vara espacial
  puede decidir en ese tramo (§7). Además MIROVA remuestrea a su grilla (p. 183, paso ii), cosa que nosotros no hacemos
  (`ENABLE_UTM_REGRID = False`, leído de `pipeline.profile`): MxD03 es necesario para la paridad de posición, no
  suficiente (D17 sigue abierta).

**2. ¿Cierra una divergencia documentada?** **En parte.** No hay una entrada numerada en `docs/MIROVA_DIVERGENCES.md`;
el corrimiento está anotado en la marca S151 de D18 («El cierre vale con la geolocalización MODIS de hoy [...] Si se
corrige, la caja se vuelve a medir») y como abierto en `docs/SINTOMAS.md` §3 (D-19). Recomendación: registrarla como
divergencia propia (D34) en el mismo PR que selle este documento (A113).

**3. ¿Alineación interna?** No aplica: es un cambio de método de posición.

**Uniformidad.** MIROVA corre un algoritmo por sensor, igual para todos los volcanes (MISSION, «Hecho canónico»). Lo que
se evalúa es MxD03 **en todo el cenit y en los 11 volcanes**; una adopción por tramo de cenit o por volcán queda excluida
de antemano.

## 3. Brazos

| brazo | qué es | por qué está |
|---|---|---|
| **K** | producción de hoy: `calculate_vrp` y `store.append_record` del tag, con `_interp_geo` | control |
| **K2** | K otra vez, en el mismo proceso | determinismo dentro del job; es el ruido de la regla de suma (§6) |
| **X** | K con la lat/lon por píxel de MxD03, todo lo demás igual (ángulos, bandas, perfil) | la palanca. Es exactamente el brazo B de M, que el verificador confirmó que sólo cambia lat/lon |
| **R** (opcional, §11 punto 7) | K con la grilla trasladada en bloque el mismo módulo en km que el corrimiento real de ese gránulo, en un rumbo al azar fijo por gránulo (sal declarada) | **comparador, no compuerta** (como D-28): ¿X cambia lo que publica más o mejor que un corrimiento sin información del mismo tamaño? Sólo comparable bajo 35° (sobre 35° la forma del campo con bow tie no es una traslación, `experiments/_s151_mxd03_sola_123/README.md`, versión 3) |

**Cómo se implementa X para el A/B: en el arnés, no en `pipeline/`** (recomendación, §11 punto 2). El arnés reemplaza
`process_modis.read_modis_l1b` por un lector que devuelve la lat/lon de MxD03, igual que `experiments/_s159/m/probe_m.py`
(l. 181 a 201). Así el A/B no toca `pipeline/` (A45) y se escribe el flag sólo si el veredicto lo justifica. El costo es
una condición más en el ciclo de adopción: el flag escrito tiene que reproducir el brazo X **record por record** en una
muestra fija de gránulos (§10).

**Ángulos.** En X los ángulos siguen saliendo de `_interp_geo`: no entran a la detección ni a la magnitud (comentario de
`process_modis.py:268-271`; su único consumidor es `observation_geometry`, `:1624-1625`). Los estratos de cenit y lado
se fijan con el record de **K**, igual para todos los brazos, para que la población no se mueva entre brazos.

**Atribución por pieza (A114, A75), sólo en las pasadas que cambian.** En el código, la posición entra por dos caminos
separables: el **fondo** (la distancia al centro del volcán, `dist`, `process_modis.py:560`, que arma el anillo de 5 a
25 km en `:582` y de ahí `t_bg`, `std_bg` y el NTI de fondo) y la **detección** (todo lo demás, §4). Para cada pasada
cuya publicación difiera entre K y X, el arnés corre dos brazos más: **X_fondo** (posiciones de K salvo el anillo, con
MxD03) y **X_det** (MxD03 salvo el anillo, con las posiciones de K). Controles de identidad que tienen que dar exacto:
X_fondo con las dos grillas iguales es K; X_fondo y X_det combinados son X. Atribuye, no decide. Correrlos en todo el
censo duplicaría el costo sin cambiar el veredicto.

## 4. Dónde llega la posición (A118): consumidores en MODIS

Leído en `pipeline/process_modis.py` de `origin/main` (`7689c487a`). Si el brazo X cambia `lat` y `lon`, cambian todos:

| consumidor | línea | qué puede cambiar | cómo lo ve el evaluador |
|---|---|---|---|
| distancia al centro, anillo de fondo 5 a 25 km | `:560`, `:582` | `t_bg`, `std_bg`, umbrales, NTI de fondo; magnitud que cruza cero | P2 y M; atribución X_fondo |
| distancia al ancla por píxel | `:564` | máscara de cumbre (`roi1_summit_mask`, `:838`, `:977`), umbrales duales de los Tests 2 y 3 (`:698`, `:741`, `:924`, `:1019`), `n_first_pass_summit` (`:959`) | P1, P2; atribución X_det |
| ROI de escena por caja de `radius_km` | `:581` | si un píxel entra a la escena; en el borde del barrido, si `calculate_vrp` devuelve record o `None` | control de cobertura (§8): se cuentan los `None` por brazo |
| máscara del p95 local | `:657` | el umbral local | P2 |
| zonas excluidas y cuerpos de agua (Villarrica, Láscar, Copahue, Llaima, Tupungatito) | `:1046` | qué píxeles se borran | P1, P2 |
| posición de cada píxel anómalo | `:1141-1142` | el filtro de distancia de `store.py` | P1, P2 |
| cúmulo anclado al cráter y su distancia | `:1168` | selección del primario, `distance_class` (que en MODIS sale del hotspot final, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`) | P1, P2, vara espacial |
| camino del vent y Test 1 | `:1287`, `:791` | nada en K (`ENABLE_VENT_PATH_MODIS = False`, `ENABLE_TEST1_PATH = False`, leídos de `pipeline.profile`) | huella: 0 `triggered_test1` |
| kernel local 3x3 y vecinos del dNTI | por índice de arreglo | nada: usan vecinos en la matriz, no distancias | no se mide |

## 5. Ventana y población

**Ventana: 2026-03-01 a 2026-10-16.** MODIS es completo y plano en la tabla desde marzo (A119 b;
`scripts/calidad_referencia_mirova.py`, que además avisó los ocho hitos de la ventana, todos de VIIRS o del OCR salvo el
del 2026-10-10, `ALERTA_SIN_GEOMETRIA_OCR`, que va a estrato aparte). Termina el 16-oct porque **del 17 al 20 de octubre
CMR no sirve MOD021KM** (`experiments/_s159/cob/INFORME.md` H2; MODIS NRT hasta el 10-21 01:35): esos días se declaran
fuera, no se reponen (mismo criterio que D-29 para D25). El 13-oct, que D-29 excluye en VIIRS, en MODIS tiene sus
records (COB: los 46 del día son MODIS y NOAA-20) y queda dentro. Enero no se usa (A119); febrero sólo para los
controles positivos (§8). 2025 no sirve: la tabla del scraper parte en 2026-01-10 y el OSF es filtrado, sin negativos
(A105).

**Población: el censo de las pasadas MODIS nocturnas de la ventana con record nuestro, con la etiqueta de MIROVA**
(`banco_paridad.etiquetar`, lectura A; la regla SN de D-9 no toca MODIS, `clase_mirova.SENSORES_MINIMA = ("VIIRS375",)`).
Medido sobre los JSON de `origin/main` `7689c487a` y la referencia remota (consolidado `c110787a`, OCR `4ddd5481`):

| etiqueta | pareo 120 s | pareo 300 s | K publica (120 s) |
|---|---|---|---|
| alerta protegida (1 MW o más) | 50 | 50 | 48 |
| alerta bajo 1 MW | 42 | 43 | 32 |
| negativo limpio | 5.110 | 5.229 | 39 |
| `sin_info` | 253 | 133 | |
| `far_ref` | 10 | 10 | |
| **total** | **5.465** | **5.465** | |

Por tramo de cenit (record de K) y lado del barrido, con el pareo de 120 s:

| tramo | lado | protegidas (K publica) | bajo 1 MW (K publica) | negativos limpios (K publica) |
|---|---|---|---|---|
| ≤ 25° | frame 0 | 9 (9) | 11 (10) | 608 (9) |
| ≤ 25° | contrario | 20 (20) | 16 (12) | 632 (12) |
| 25 a 40° | frame 0 | 12 (12) | 4 (3) | 479 (5) |
| 25 a 40° | contrario | 3 (3) | 4 (3) | 456 (5) |
| 40 a 50° | frame 0 | 1 (1) | 2 (2) | 444 (0) |
| 40 a 50° | contrario | 2 (2) | 4 (2) | 401 (2) |
| > 50° | frame 0 | 1 (0) | 1 (0) | 1.052 (2) |
| > 50° | contrario | 2 (1) | 0 | 1.038 (4) |

Lo que esto dice antes de correr nada:
- **El poder del veto es de Láscar y Chillán, y está bajo 40°.** Las alertas MODIS de la ventana son Láscar 80 (40
  protegidas), Chillán 10 (9) y Villarrica 2; los otros ocho volcanes tienen 0. 44 de las 50 protegidas tienen cenit de
  40° o menos, donde M no midió nada.
- **En noches, MODIS casi no decide.** De las 44 noches-volcán con protegida MODIS, 43 ya tienen una publicación VIIRS
  de K esa noche; de las 39 con alerta bajo 1 MW, 38 (A94). Un cambio MODIS mueve la paridad **del sensor MODIS** (la
  métrica 3 de MISSION es por sensor), casi nunca lo que el operador ve por noche.
- **Exposición de la pieza de posición** (techo, no predicción): pasadas cuyo cúmulo de K cae a menos del corrimiento
  mediano de M del borde de `inner_radius_km`: **4 protegidas**, las cuatro con cenit de 25 a 40° del lado del frame 0
  (Láscar 2026-03-09 07:10, 2026-03-27 07:10, 2026-04-08 01:50 y Chillán 2026-10-10 07:40; la del 03-27 es la que vetó
  la caja de D18), 3 bajo 1 MW y 10 negativos limpios. Para 25 a 40° no hay corrimiento medido y se usó el de 40 a 50°
  como cota (declarado en el script). En Láscar la fuente está en el cráter y M midió que X la acerca: la predicción es
  que esas protegidas se muevan **hacia adentro**.
- **Exposición de la pieza de fondo**: cúmulos `summit` con 0,1 MW o menos, donde un cambio de 0,2 a 0,4 K en el fondo
  cruza cero: Láscar 10 alertas bajo 1 MW (6 de ellas con el cúmulo del cráter en 0,0 MW que K no publica), 6 negativos
  limpios y 5 `sin_info`; Chillán 1 negativo. La pieza de fondo sólo actúa ahí, y ahí se informa aparte.
- **Lo que X no puede recuperar**: dentro de la ventana K deja sin publicar 2 protegidas, las de Chillán del 12 y del 15
  de octubre, que M ya probó que no vuelven con MxD03 (H4).

## 6. Métricas y reglas

Todo por **pasada MODIS**, contra K, con la lectura A (D-4), informando además la regla original (en MODIS coinciden).
«Publica» es el predicado de `frontend/index.html` ejecutado con node (A97); el evaluador imprime su sha256. Se informa
también por noche-volcán (A94) y por tramo de cenit y lado, que **no deciden** (§2, uniformidad).

| prueba | qué cuenta | regla | decide |
|---|---|---|---|
| **P1 veto** | protegidas que K publica y X no | VETADO con una sola pérdida que no esté también en K2 (K2 discorda de K por ruido). Es la regla de MISSION 1, sin umbral | sí |
| **P1b cruce de 1 MW** | protegidas que K muestra con 1 MW o más y X bajo 1 MW | se listan; con una o más decide Nicolás | lista |
| **P2 suma bajo 1 MW** | alertas bajo 1 MW que el brazo no publica + publicaciones en negativos limpios | GANA si la suma de X es menor que la de K menos el ruido; PIERDE si es mayor que la de K más el ruido; si no, EMPATE. Ruido = pasadas en que K y K2 discrepan en publicar (se espera 0: M dio A = A2 en 85 de 85). Hoy la suma de K es 10 + 39 = **49** | sí |
| **P3 vara espacial** | §7 | X no puede quedar **más lejos** de la referencia que K (INTERP MAS CERCA con control de sesgo bloquea, como inconsistencia que hay que explicar) | sólo bloquea (§11 punto 5) |
| **M magnitud** | en alertas que K y X publican, con VRP de MIROVA: d = abs(log10(X/MIROVA)) - abs(log10(K/MIROVA)) | la regla sellada de D25 (bootstrap por bloques noche-volcán, calibración simétrica D-27, opción A de dos volcanes con 3 pares o más, comparador D-28) | sólo bloquea: un EMPEORA impide CUMPLE, un MEJORA no cuenta (M midió X/K mediano 1,029 y 1,00) |
| **P4 el cúmulo se mueve** | pasadas con el centroide publicado movido más de 0,01 km, y las que cambian de `distance_class` | se informan; si alguna es protegida, la auditoría espacial A61 de todas las movidas va antes de adoptar | no |
| **P5 atribución** | por cada pasada que cambia de publicación: X_fondo, X_det (§3), `t_bg_k`, `diag_n_first_pass_summit`, si el píxel cruzó `inner_radius_km` | se informan | no |
| **R comparador** (si se incluye) | P1 y P2 de R contra K, bajo 35° | se informan al lado de X: «X cambia como el azar» o «X cambia menos/más que el azar». No vuelve inválido nada (D-28) | no |

**El pareo es una dependencia.** El veredicto se calcula con la tolerancia que fije `experiments/_s159/pareo_modis/`
(hoy en curso). Si al sellar no está, rige el de producción (120 s, `banco_paridad.TOL_S`) y se informa también con 300
s; si P1 o P2 cambian de veredicto entre las dos, lo dice la primera línea y decide Nicolás. Medido: pasar de 120 a 300 s
no cambia el número de protegidas (50) y suma 1 alerta bajo 1 MW y 119 negativos limpios.

**Por qué estos umbrales no son de gusto (A115).** El veto y la suma son el criterio de victoria de MISSION, sin
números elegidos; la tolerancia del ruido es el propio gemelo; la magnitud usa la regla ya sellada de D25 con su
calibración; la vara espacial pregunta cuál de las dos posiciones queda más cerca de la de MIROVA o de otro instrumento,
sin corte de distancia. Lo elegido, y dicho como elegido: los tramos de cenit (25, 40 y 50°, que sólo informan), el 0,01
km de P4 y los mínimos de la vara (§7).

**Predicciones (escritas antes de correr; no deciden).**
1. P1: CUMPLE. Si cae algo, una de las 4 protegidas expuestas de 25 a 40° del frame 0.
2. P2: EMPATE o GANA por pocas pasadas, casi todas en Láscar; los 9 volcanes sin alertas no cambian o cambian en 1 o 2
   negativos (M S4: 0 de 12 `far` pasan a `summit`).
3. M: NEUTRO (M midió X/K de 1,00 a 1,03).
4. Vara VIIRS: MXD03 MAS CERCA bajo 35° (ya lo dio la tarea 1.23 con n = 76) y entre 35 y 50°; sobre 50°, sin poder.
5. En noches: 0 o 1 noche cambia.

## 7. La vara espacial: contra qué se mide la posición

Un radio no es una posición (A93, A107): la `Distancia_km` de MIROVA no trae acimut y está cuantizada a su grilla (D15
del catálogo, no re-medida aquí). Por eso la posición se mide contra dos referencias con dirección, y la distancia
escalar sólo sirve para descartar.

**Lo que no sirve, medido.** La sugerencia de usar los TIF UTM nativos de MIROVA del 14 y 15 de septiembre (A106)
**no aplica a MODIS**: esa grilla UTM fue sólo de VIIRS 375. Los GeoTIFF MODIS de MIROVA son **todos EPSG:4326**, de
51 × 51 celdas de ~1 km, también los del 14-sep (`tif_modis_cobertura_salida.txt`: 8 de 8 de una muestra repartida de mayo
a septiembre; `tif_modis_14sep_crs_salida.txt`: Llaima 02:10 y Láscar 07:35 del 14-sep).

**V-VIIRS, la vara física (recomendada como principal).** El instrumento de la tarea 1.23 sin cambios
(`experiments/_s151_mxd03_sola_123/construir_vara_viirs.py` y `evaluar_sola.py`, lectura 3): la posición del objeto
caliente de esa noche según VIIRS 375 (otro sensor, otro satélite, geolocalización por píxel VNP03IMG/VJ103IMG, píxel de
375 m), con pasadas publicadas cuyo cúmulo no viene del Test 1 y, en el nivel estricto, con alerta de MIROVA.
Estadístico dd = |K - v| - |X - v| en el píxel MODIS más caliente elegido por índice (el mismo píxel físico en los dos
brazos), intervalo por bootstrap de noches, nulo medido con pares de traslaciones al azar (los brazos R00 a R19 **sólo
en los gránulos con vara**, como en 1.23), y control de sesgo: Terra y Aqua corren la grilla en sentidos opuestos, así
que un veredicto exige el mismo signo en los dos. Estados y mínimos (10 gránulos, 5 noches) los de 1.23. Sobre 35° el
nulo no es comparable (bow tie) y la lectura es descriptiva; sobre ~50° además Coppola 2016a p. 197 avisa errores de
varios kilómetros, así que ahí no se exige nada.

**V-TIF, la vara de paridad (informa).** Dónde puso MIROVA el calor de **esa misma pasada** en su grilla: el GeoTIFF
MODIS de MIROVA (`MendozaVolcanic/mirova-tif-archive`, índice en el commit `3660cdfa`). Hay 5.540 imágenes MODIS
distintas, del 2026-05-09 al 2026-09-22 (el índice no tiene filas MODIS posteriores). De las filas de alerta MODIS de la ventana
que caen en ese tramo, 26 de 33 tienen TIF de su pasada a ±5 min, todas con md5 nuevo (`tif_modis_para_alertas_salida.txt`;
filas sin deduplicar, casi todas de Láscar). Antes de usarla:
- **georreferencia verificada** (A106): en las pasadas de Láscar con cenit ≤ 25° y alerta, la celda de máximo local del
  TIF tiene que caer a una celda o menos del cráter; si no, la vara es inválida;
- **máximo local, no global**: la celda de máximo del TIF de Láscar del 14-sep 07:35 está en el borde oeste de la caja, a
  unos 25 km del cráter (`tif_modis_14sep_crs_salida.txt`): el TIF es el campo, no el cúmulo (A24). La posición de MIROVA
  es la celda de máximo dentro de 5 km del cráter (la caja ROI1 de Coppola 2016a);
- **hora de adquisición del índice**, nunca la del nombre, y fuera las imágenes repetidas (A106);
- **no es independiente** (A109): sale del mismo gránulo. Para una comparación de posición entre dos brazos que
  comparten el píxel es aceptable, porque la selección es común a K y X; lo que mide es paridad con la geolocalización
  de MIROVA, no verdad física, y así se informa.
Con ~20 pasadas, casi todas de Láscar, informa y no decide (SIN PODER si quedan menos de 10 pasadas o 5 noches).

**`Distancia_km`, sólo para descartar.** Por alerta: si la distancia del cúmulo de X difiere de la de MIROVA en más de
una celda más medio píxel, X está viendo otro objeto; ídem K. Se informa la fracción compatible por brazo; no decide.

## 8. Controles, y el candado del evaluador

Si un control falla, lo que depende de él queda INDECIDIBLE y no se interpreta.
1. **Instrumento de geometría**: el control positivo de S151 (Láscar `MYD021KM.A2026073.0705`, componente hacia el
   sensor 2,581 km, ±0,05) y el nulo de geometría (`_interp_geo` contra sí misma, 0 en todos los gránulos), como M.
2. **Determinismo**: K y K2 publican lo mismo en el 100 % de las pasadas (M: 85 de 85). Si no, el ruido de P2 se mide
   con esa discordancia y se dice.
3. **El arnés reproduce producción**: K reproduce el record publicado en `data/` (mismo `primary_cluster.vrp_mw` a
   0,001 MW y misma decisión de publicar) en 98 de cada 100 pasadas o más; las excepciones se listan con su
   `codigo_sha`. El 98 % es el umbral heredado de F/K (elegido, no medido). M dio 84 de 85.
4. **Cobertura pareja** (A108): los mismos gránulos en todos los brazos; el arnés cubre el 100 % de las 5.465 pasadas
   del censo; los `None` de `calculate_vrp` se cuentan por brazo (X puede vaciar o llenar el ROI en el borde del
   barrido) y cada uno se lista. Faltante de CMR: reintento como en M; lo que siga faltando se informa como INCOMPLETO
   y se repite el trozo sobre el mismo código.
5. **La referencia es la congelada**: consolidado y OCR congelados al sellar (como `_congelado_v1/` de D25), sha256 LF
   en un `MANIFIESTO.json`. Medido: entre dos corridas de esta tarde el consolidado remoto cambió de `292e3782` a
   `c110787a`; sin congelar, el denominador se mueve solo.
6. **Controles positivos del etiquetado** (`sustrato_mirova_modis_feb_salida.txt`, todos en verde hoy): Láscar
   2026-02-11 07:00 `bajo1` (MIROVA 0,48 MW), Láscar 2026-03-27 07:10 `protegida` (1,0 MW), Chillán 2026-06-01 08:15 y
   Cordón Caulle 2026-06-19 01:15 negativos limpios.
7. **El cableado de X**: en X el `lat` que recibe `calculate_vrp` es el de MxD03 (el arnés guarda un hash de la grilla
   por brazo) y en K el de `_interp_geo`; los ángulos son iguales en los dos.

**Candado, antes del tag** (como en D25):
- `evaluar_mxd03.py` reutiliza sin tocar el evaluador de D25 (`evaluar_d25.py`, P1, P2, M con sus dos adendas) con el
  sensor fijado a MODIS, más P3 (el `evaluar_sola.py` de 1.23 para la vara), P4, P5 y el comparador R.
- Pruebas en `probar_evaluar_mxd03.py` que fallen por la razón que dicen (S140): una protegida que X apaga da VETADO; una
  que también discorda en K2 no veta; un negativo que X publica de más cuenta en P2; P2 con ruido; una vara con X más
  lejos y el mismo signo en Terra y Aqua bloquea; con signos opuestos da SESGO POR SATELITE y no bloquea; M EMPEORA
  bloquea y M MEJORA no gana; R no invalida nada; el pareo de 300 s se aplica a los dos lados.
- Mutaciones del evaluador contadas sólo si las atrapa una aserción, con control de caída (S156).
- Verificador con contexto limpio sobre el evaluador y sobre el arnés.

## 9. Despacho y costo (no despachar sin el sello)

**Orden.** (a) Sello de Nicolás sobre este documento y el §11. (b) Candado del §8 mergeado y verificado. (c) Cupo: el
NRT ocupa 11 jobs cada 2 h y el tope de la cuenta es 20; nunca más de dos A/B vivos. (d) Referencia congelada. (e) Tag
sobre `main`, empujado, y su commit anotado:

```bash
git tag -a s159-mxd03-codigo -m "codigo del A/B de MxD03 sobre K" origin/main
git push origin s159-mxd03-codigo
git rev-parse s159-mxd03-codigo^{commit}
```

(f) Cada despacho **desde el tag** (A108, S152), el siguiente recién cuando el anterior terminó:

```bash
gh workflow run probe-mxd03-ab.yml --ref s159-mxd03-codigo -f preregistro_aprobado=si -f desde=2026-03-01 -f hasta=2026-10-16 -f parte_ini=0 -f parte_fin=7 -f partes=24
```

(y lo mismo con `parte_ini=8 parte_fin=15` y `16 23`). El workflow es el de M (`experiments/_s159/m/probe-s159-m.yml`)
pasado a `workflow_dispatch` con `"on":` entre comillas (A43), autenticación sólo por `EARTHDATA_TOKEN` y falla al
instante si viene vacío (A71), `ubuntu-24.04` fijado, y la lista de gránulos armada desde los records de K de la ventana
(cada record trae `granule`; los records de un mismo gránulo de dos volcanes, como Láscar y Lastarria, se bajan una vez).

**Costo, medido** (no adivinado):
- Por record en el arnés (bajar L1B y MxD03 con reintento, y tres corridas de `calculate_vrp` + `append_record`): mediana
  **23,9 s**, media **38 s** (51,6 min en 81 intervalos), p90 77 s, máximo 300 s, en el log del probe M (run
  39681481914, `tiempo_modis_probe_m_salida.txt`).
- Censo: 5.465 records × 38 s ≈ **58 h de runner** para K, K2 y X. R agrega una corrida por record: la parte de proceso
  de esos 38 s no está separada de la descarga, así que la cota es un tercio más (≈ 19 h, SIN MEDIR). Los R00 a R19 de la
  vara corren sólo en los gránulos con vara (en 1.23 eran 166 de 471; aquí no está contado). Atribución: sólo las
  pasadas que cambian.
- En 24 partes de ~230 records: ~2,4 h por job en media (el peor, con reintentos de CMR, cabe con margen bajo el tope de
  6 h; 1,3 × 2,4 = 3,1 h, A15), en tres tandas de 8: **~8 a 10 h de pared**.
- **La alternativa, un reproceso por brazo con `reproc-s146-ab-sin-test1.yml`**, cuesta al menos 4 veces más: en un job
  real (run 39467050396, Chillán 2026-07-13 a 22, `tiempo_por_dia_reproc_salida.txt`) cada día-volcán tomó 2,57 min, de
  los cuales **1,86 son búsqueda y descarga** de los tres sensores, que se bajan aunque el perfil apague VIIRS
  (`scripts/run_pipeline.py:213-218` filtra el sensor después de `fetch`). Con 2.530 días-volcán por brazo, sólo la
  descarga da ≥ 78 h por brazo, ≥ 235 h los tres. Y cada brazo correría en otro runner, con el ruido de desempate entre
  CPU (S152) metido en la comparación; en el arnés K y X comparten proceso y ese ruido no existe.

## 10. Riesgos, y lo que este A/B no puede decidir

**Riesgos del diseño.**
- **El arnés no es `run_pipeline`.** Reproduce sus argumentos (verificador de M: `append_record` con los mismos de
  `scripts/run_pipeline.py:247-254`), pero un cambio futuro de `run_pipeline` no lo vería. Mitigación: control 3 y, en la
  adopción, el flag escrito tiene que reproducir X record por record en una muestra fija (los 85 gránulos de M más 40 del
  censo, tres días de Láscar y tres de Chillán), como el paso 5 de la regla de K.
- **Poder concentrado.** El veto es de Láscar (40) y Chillán (9); un CUMPLE no dice nada de los otros nueve volcanes en
  alertas, sólo en negativos (5.110, donde K publica 39).
- **Sesgo de la vara VIIRS por volcán.** Bajo 35° la vara de 1.23 fue 70 de 76 gránulos de Láscar. El control Terra
  contra Aqua cancela un sesgo constante, no uno que dependa del volcán.
- **El pareo** (§6) y **el OCR**: 5 alertas MODIS de Láscar dependen del OCR (A119, marca S151); se listan aparte.

**Lo que no decide.**
- La magnitud MODIS (D25 en MODIS, D33 longitud de onda, D17 remuestreo): M ya dio que la geolocalización no la mueve.
- Las protegidas de Chillán a 58° (M H4) y todo lo que pase sobre ~55°: ni MIROVA promete posición ahí (Coppola 2016a
  p. 197).
- D18 (la caja de 5 × 5 km): su veto cayó en una protegida de Láscar con el píxel a 3,2 km, corrido por esta misma
  geolocalización. **Si X se adopta, la caja se vuelve a medir sobre X**, no antes.
- VIIRS: no se toca.
- La noche del operador: en 43 de 44 noches con protegida MODIS ya publica VIIRS. Este A/B decide la paridad del sensor
  MODIS, no un cambio de lo que el operador ve por noche, y así se le dice al operador.

**Qué se hace con cada veredicto.**

| resultado | qué se hace |
|---|---|
| P1 CUMPLE, P2 sin PIERDE, P3 no bloquea, M no EMPEORA | **CUMPLE**: ciclo de adopción. Tag defensivo, flag `enable_modis_geo_mxd03` en `process_modis` con TDD y su prueba de reproducción contra X, el «sí» de Nicolás (A45), FICHA SDA, D34 en el catálogo con marcas A113, marca visible de la fecha en las tres vistas (el marcador MODIS se corre 2 a 5 km), aviso a OVDAS |
| P1 VETADO o P2 PIERDE | **NO CUMPLE**: no se adopta; cada pérdida con atribución (P5) y auditoría espacial A61 |
| P3 bloquea (INTERP MAS CERCA con control) | se busca el error en la vara o en el arnés antes que nada (sería raro, MxD03 es el producto oficial) |
| M EMPEORA | decide Nicolás con la tabla por volcán |
| P1b con alguna | decide Nicolás con la lista |
| INDECIDIBLE o INCOMPLETO | repetición del trozo sobre el mismo código, tope dos; un INDECIDIBLE de controles no se repite, se busca el defecto |

## 11. Lo que tiene que decidir Nicolás para sellar

1. **¿La pregunta y los brazos K, K2, X tal como están?** Recomendado: sí.
2. **¿X en el arnés (sin tocar `pipeline/` hasta el veredicto) o un flag escrito antes?** Recomendado: **en el arnés**.
   Es el brazo B de M, ya verificado; el flag se escribe sólo si CUMPLE y tiene que reproducir X record por record.
3. **¿Arnés por gránulo o reproceso por brazo?** Recomendado: **arnés**, ~58 h de runner y ~8 a 10 h de pared, contra
   ≥ 235 h, y sin ruido entre CPU en la comparación.
4. **¿Ventana 2026-03-01 a 2026-10-16, con 17 al 20 de octubre fuera por CMR?** Recomendado: sí. Alternativa: agregar
   15 a 28 de febrero sólo como información.
5. **¿Qué papel tiene la vara espacial?** Recomendado: **sólo bloquea** (si X queda más lejos que K con control de
   sesgo, se para todo). Alternativas: exigir MXD03 MAS CERCA para adoptar (bajo 35° ya se sabe que da eso); o sólo
   informar.
6. **¿Magnitud sólo bloquea?** Recomendado: sí, con la regla sellada de D25.
7. **¿Comparador R (un corrimiento al azar del mismo tamaño), como comparador y no compuerta, bajo 35°?** Recomendado:
   **sí**; cuesta hasta un tercio más y responde «¿X cambia más que el azar?», que fue la pregunta abierta de 1.21.
8. **¿Atribución posición contra fondo sólo en las pasadas que cambian?** Recomendado: sí.
9. **Documentos que acompañan el sello**: registrar el corrimiento como D34 en `docs/MIROVA_DIVERGENCES.md` con marca
   A113 en D18 y en `docs/SINTOMAS.md` §3, y agregar Coppola 2026 (Scientific Data) a la lista de papers de MISSION.
   Recomendado: sí, en el mismo PR.
10. **El pareo**: si `pareo_modis` no terminó al sellar, rige 120 s con 300 s informado (§6). Recomendado: sí.
11. **Orden con D18**: re-medir la caja sólo después de este veredicto, sobre X si se adopta. Recomendado: sí.
