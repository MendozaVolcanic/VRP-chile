# Pre-registro S159 (tarea 1.30, decisión D-19): geolocalización MODIS desde MxD03, sobre K

**BORRADOR v2 PARA EL SELLO DE NICOLÁS.** La v1 la escribió una sesión lateral del loop el 2026-10-21, antes de correr
ningún brazo y antes de escribir una línea en `pipeline/`. Un verificador con contexto limpio la revisó y dio LISTO
CON CAMBIOS (`verificador/INFORME.md`, commit `464152853`, hallazgos H1 a H9). Esta v2 incorpora los nueve, más el
informe del verificador del frente de pareo (`experiments/_s159/pareo_modis/verificador/INFORME.md`). Nada se despacha
sin el «sí» escrito de Nicolás, sin el candado del §8 y sin el tag del §9. Todos los números salen de scripts de esta
carpeta o de los del verificador, con su salida al lado (regla S91). Lo que queda abierto está en el §11, con una
recomendación en cada punto.

## 0. Registro de cambios de la v1 a la v2

| punto del verificador | qué cambió | dónde |
|---|---|---|
| H1, P2 con un nulo muerto (obligatorio) | El ruido de P2 ya no sale de K2 (mismo proceso, 0 por construcción). Sale de 20 semillas del comparador R (un corrimiento del mismo módulo en km, rumbo al azar), corridas en todas las pasadas con cenit ≤ 35°. P2 decide ahí. Sobre 35° se informa. P2 se informa también sin Cordón Caulle (31 de los 39 negativos limpios que K publica son de ese volcán). K2 queda como control de identidad | §3, §6 |
| H2, M bloquea por un 3 % (obligatorio) | **M sólo informa.** La alternativa (juzgar EMPEORA con el comparador de D-28) va al §11 | §6, §11 punto 6 |
| H3, `evaluar_d25.py` no sirve para MODIS (obligatorio) | Diseño de un evaluador MODIS nuevo: formato de entrada, estratos, funciones que importa sin copiar, y pruebas que fallan antes y pasan después. No implementado | §8 |
| H4, cita de Coppola 2016a mal localizada (obligatorio) | La p. 197 sólo da «>30°», y para la detección en cráteres hondos. La frase sobre la geolocalización no trae ángulo. Los cortes de 35° y 50° se declaran propios | §2, §7, §10 |
| H5, pareo | Fijo a ±120 s, sin la rama de 300 s, con el verificador del pareo citado. Se informan aparte las 222 mitades de pasada partida, los `sin_info` y los `far_ref` | §5, §6 |
| H6, qué significa CUMPLE | El veredicto pasa a llamarse **CUMPLE SIN DAÑO**. Se escribe que el veto tiene 4 protegidas expuestas y qué parte del §1 no decide nada | §1, §6, §10 |
| H7, costo | Partes por gránulo (1.232 gránulos). Horas recalculadas, separando descarga de proceso con un script nuevo | §9 |
| H8, afirmaciones heredadas | 0 alertas MODIS que dependan del OCR en esta ventana; «EPSG:4326» medido en 10 TIF; en Coppola 2026, LANCE está en la oración de VIIRS; bajo 40°, M tenía «casi» sin dato | §2, §5, §7, §10 |
| H9, control 3 | Sin tolerancia en los casos que deciden. Se midió que 5.449 de los 5.465 records fueron escritos con código cuyo `pipeline/` difiere del de hoy, así que el control separa deriva de versión de arnés roto | §8 |

**Dónde discrepo del verificador** (lo demás lo acepto entero):
- H1 dice que los negativos de Cordón Caulle están «muchos» con el cúmulo entre 18 y 19,8 km de un inner de 20. Contado
  sobre su propia salida (`verificador/extra_negpub_salida.txt`): 7 de 31 tienen el cúmulo a 17 km o más y 13 a 3 km
  o menos del cráter. La masa de P2 sí está en Cordón Caulle, pero sólo una parte está en el borde. No cambia el
  arreglo (el nulo medido con R ve los dos tipos), cambia la lectura.
- H9 dice «al menos 16 `codigo_sha`». En la ventana de este A/B son **12** (`censo_granulos_salida.txt`). Los 16
  probablemente cuentan el corpus entero desde 2025.

Evidencia de esta carpeta (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\mxd03_prereg\`):

| script | salida | qué mide |
|---|---|---|
| `sustrato_modis.py` | `sustrato_modis_salida.txt` | con qué detector están escritos los records MODIS, por cenit y lado |
| `sustrato_mirova_modis.py` | `sustrato_mirova_modis_salida.txt`, `sustrato_mirova_modis_feb_salida.txt` (controles), `.json` | población contra MIROVA, no condicionada a lo que publica K |
| `censo_granulos.py` (v2) | `censo_granulos_salida.txt` | records, gránulos, records con cenit ≤ 35° y `codigo_sha` del censo |
| `shas_vs_main` (v2, en línea en la sesión; salida guardada) | `shas_vs_main_salida.txt` | si el `pipeline/` de cada `codigo_sha` difiere del de hoy |
| `tif_modis_cobertura.py` | `tif_modis_cobertura_salida.txt`, `tif_modis_14sep_crs_salida.txt` | GeoTIFF MODIS de MIROVA |
| `tif_modis_para_alertas.py` | `tif_modis_para_alertas_salida.txt` | alertas MODIS con TIF de su pasada |
| `tiempo_modis_probe_m.py` | `tiempo_modis_probe_m_salida.txt` | segundos por record en el log del probe M |
| `tiempo_proceso_vs_descarga_m.py` (v2) | `tiempo_proceso_vs_descarga_m_salida.txt` | cuánto de cada record es proceso y cuánto es buscar y bajar |
| `tiempo_por_dia_reproc.py` | `tiempo_por_dia_reproc_salida.txt` | minutos por día-volcán de un reproceso real |
| del verificador | `verificador/extra_verif_salida.txt`, `extra_negpub_salida.txt`, `m_sensibilidad_salida.txt` | pasadas partidas, OCR, gránulos, negativos publicados, sensibilidad de M |

(`shas_vs_main_salida.txt` lo produjo un bloque de Python corrido en la sesión, no un archivo `.py`: lee los JSON de
`origin/main` `7689c487a` y corre `git diff --quiet <sha> 7689c487a -- pipeline/ volcanoes.yaml` por cada `codigo_sha`.
Si el sello lo pide, se pasa a script.)

## 1. La pregunta, y por qué ahora

**La pregunta en una frase.** Si el pipeline ubica cada píxel MODIS con la geolocalización con corrección de terreno
de MxD03 (lo que declara el conjunto de datos de MIROVA) en vez de interpolar la grilla de 5 km del propio L1B,
**¿daña la réplica?** Es decir, ¿pierde alguna alerta protegida o publica más donde MIROVA calló?

**Lo que el A/B decide y lo que no (H6).** Decide si el cambio es **inocuo para la réplica** (CUMPLE SIN DAÑO) o
**dañino** (NO CUMPLE). **No decide** si X pone el calor «donde lo ve MIROVA»: eso se informa con dos varas (§7), y
ninguna tiene poder para decidir en la ventana. Tampoco decide la magnitud (§6, M sólo informa). La razón para adoptar
X, si el A/B da sin daño, es la fidelidad literal (§2) más lo que el frente M ya midió de la posición. No hay una
mejora demostrada por este A/B, y un CUMPLE SIN DAÑO no debe leerse como «mejora».

**El fenómeno.** Un volcán visto de lado por MODIS (cenit sobre 40°) cae en un píxel de varios kilómetros, y el L1B sólo
trae la latitud y longitud cada 5 píxeles. El pipeline estira esa grilla gruesa a 1 km con una interpolación lineal
(`pipeline/process_modis.py:265-266` lee la grilla, `:292-295` la interpola, `:385-396` es `_interp_geo`), y no usa el
MxD03 que baja y exige: `calculate_vrp` lo recibe y lo ignora (`process_modis.py:513`, «accepted for API compatibility
but not used»), y `scripts/run_pipeline.py:223-230` salta el gránulo si el MxD03 falta. El frente M midió que así el
píxel del cráter queda corrido hacia el lado del sensor: mediana **2,82 km** con cenit de 40 a 50° y **5,04 km** sobre
50° del lado del frame 0 (1,10 y 2,48 del lado contrario; 1,10 y 0,79 cerca del nadir con n = 4 cada uno). Y en
Láscar, con los mismos píxeles detectados, el cúmulo pasa de 2,54 a 0,59 km del cráter (`experiments/_s159/m/INFORME.md`
H2 y H3, confirmados por su verificador).

**Por qué ahora.** La decisión D-19 dejó este pre-registro para cuando K estuviera en producción. Las dos protegidas que
MxD03 perdía bajo C0 caían por el Test 1 integrado, que K apagó (`tasks/LOOP_OBJETIVOS.md` D-19, en `loop/activo`). K
está en producción desde el 2026-10-18 09:57:30 UTC, y el histórico MODIS entero está escrito con el perfil K. Los
14.565 records MODIS de los 11 Tier A, de 2025-02 a 2026-10, tienen `regimen.perfil` igual a `_s154_reproc_k_historico`
o `mirova_equivalent` (`sustrato_modis_salida.txt`). No hay frontera de detector (A104, A85) dentro de la ventana, pero
sí deriva de código entre versiones (§8, control 3).

**Lo que dejó el frente M y que este diseño absorbe.**
1. La población de M estaba condicionada a lo que K publica (A109). Aquí es el **censo** de las pasadas MODIS de la
   ventana con la etiqueta de MIROVA (§5).
2. 4 de los 12 cambios de M fueron de **fondo**, no de posición, y uno se apagó sin que el píxel saliera del círculo.
   Aquí la posición y el fondo se atribuyen por separado en las pasadas que cambian (§3).
3. Bajo 40° de cenit M **casi** no tenía dato (n = 4 por lado cerca del nadir, sin cambios de clase). Aquí entran
   todos los tramos, y bajo 40° está el poder del veto: 44 de las 50 protegidas (§5).

**Lo que este A/B NO pregunta.** Si el remuestreo a la grilla UTM de MIROVA (D17, D28) explica el resto de la
diferencia; si D25 debe escribirse en MODIS; por qué las protegidas de Chillán del 12 y 15 de octubre (cenit 58°) no
tienen detección en ningún brazo (M H4: no es la geolocalización).

## 2. Las tres preguntas de `docs/MISSION.md`

> ⚠️ **S162, cita de MOD-A agregada después del sello y del resultado** (A113; no cambia ninguna regla ni el veredicto).
> (1) **Sobre el matiz «Voz pasiva, producto de archivo» del punto 1**: la tarea MOD-A (PR #902,
> `experiments/_s162_instrumento/MOD_A_CITA_MOD03.md` en la rama `instrumento/mod-a-cita`, `70208beb7`; páginas leídas
> renderizadas a imagen, verificador de contexto limpio: CONFIRMADO CON MATIZ) confirmó la cita de la p. 4 como insumo
> y mostró que el NRT corre el mismo procedimiento: en la p. 3 del PDF los insumos son productos NRT de LANCE o de
> archivo de LAADS, y en la p. 6 los volcanes de la lista NRT se procesan con LANCE desde su inclusión con el
> procedimiento ya descrito. El paper no separa dos cadenas, así que «no dice que el NRT lo aplique» ya no vale: el
> insumo queda **CONFIRMADO también en el NRT**. Lo que sigue **SIN LOCALIZAR** es el método: si cada píxel se ubica con
> MOD03 o se interpola, y cómo se remuestrea a la grilla UTM de la p. 5; el código del remuestreo no se publica (p. 21).
> Usar MxD03 por píxel, como hace el brazo X, sigue siendo una elección nuestra. (2) **Sobre el «registrarlo como D34»
> del punto 2** (y el «D34» del §11, punto 9): D34 está tomada desde S158 por el código de MIROVA para VIIRS 750; la
> divergencia quedó registrada como **D35** en `docs/MIROVA_DIVERGENCES.md`, con el veredicto del A/B (CUMPLE SIN
> DAÑO, verificado; `experiments/_s162_mxd03/resultado/INFORME.md`, rama `s162-mxd03-codigo`, `afb3fcdea`). Texto de
> abajo conservado tal como se selló.

**1. ¿Está en los papers de MIROVA?** **Sí, con matices.** Coppola et al. 2026 (Scientific Data,
`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`, p. 4, primer párrafo, leído renderizando
la página a imagen, A95): «For the MODIS period (2000-2025), Level 1B calibrated radiance products (MOD021KM and
MYD021KM) were used [...] together with the corresponding MOD03 and MYD03 Terrain-Corrected Geolocation products.»
Matices:
- **Voz pasiva, producto de archivo.** La oración describe con qué se armó el conjunto 2000 a 2025. No dice con verbo
  activo que el sistema NRT lo aplique (regla S99). La frase «accessed via the NASA LANCE/LAADS distribution systems»
  pertenece a la oración siguiente, la de VIIRS (H8). Para MODIS, la pista de que es la misma cadena que la NRT es
  indirecta. Respaldo fuerte, no cita del NRT.
- **Coppola 2026 no está en la lista de 11 papers de MISSION**, aunque es del grupo MIROVA (Torino) y A105 ya lo usa
  como autoridad (§11, punto 9).
- Coppola 2016a (`sp426.5.pdf`, p. 183, «Data extraction from MODIS Level 1B granules») dice que de los gránulos de
  nivel 1 se extraen «pixel(s) geolocation (latitude and longitude)», sin nombrar MOD03.
- La p. 197 (índice 16 del PDF, «Satellite viewing geometry»), corregida según H4, dice dos cosas separadas:
  - «c. 69% of the data have a satellite zenith >30°». Ese número se usa sólo para decir que con cenit alto pueden no
    verse focos en cráteres hondos.
  - Luego, **sin ángulo**: «high scan angles [...] decrease [...] the accuracy of the pixel(s) geolocation», con errores
    «up to several kilometres».

  La v1 le atribuía «~50°» y «~55°»; el paper no los dice. Los cortes de 35° y 50° de este documento son **propios**:
  el de 35° viene de la tarea 1.23 (sobre 35° el bow tie hace que una traslación rígida no sea comparable) y el de 50°
  es el tramo de M. Si se toma el único número del paper, su aviso empieza en 30° y cubre el tramo de 25 a 40° donde
  están las 4 protegidas expuestas.
- MIROVA además remuestrea a su grilla (p. 183, paso ii) y nosotros no (`ENABLE_UTM_REGRID = False`). MxD03 es necesario
  para la paridad de posición, no suficiente (D17 sigue abierta).

**2. ¿Cierra una divergencia documentada?** **En parte.** No hay entrada numerada en `docs/MIROVA_DIVERGENCES.md`. El
corrimiento está anotado en la marca S151 de D18 («El cierre vale con la geolocalización MODIS de hoy [...] Si se
corrige, la caja se vuelve a medir») y como abierto en `docs/SINTOMAS.md` §3 (D-19). Recomendación: registrarlo como D34
en el mismo PR del sello (A113).

**3. ¿Alineación interna?** No aplica.

**Uniformidad.** MIROVA corre un algoritmo por sensor, igual para todos los volcanes (MISSION, «Hecho canónico»). Se
evalúa MxD03 en todo el cenit y en los 11 volcanes. Una adopción por tramo o por volcán queda excluida.

## 3. Brazos

| brazo | qué es | papel |
|---|---|---|
| **K** | producción del tag: `calculate_vrp` + `store.append_record`, con `_interp_geo` | control |
| **K2** | K otra vez, en el mismo proceso | **control de identidad** (tiene que dar K exacto). No es ruido: no puede discrepar por construcción (H1) |
| **X** | K con la lat/lon por píxel de MxD03; ángulos, bandas y perfil iguales | la palanca. Es el brazo B de M |
| **R0 a R19** | K con la grilla trasladada en bloque el mismo módulo en km que el corrimiento real del gránulo (el de X en el píxel del cráter), en 20 rumbos equiespaciados cada 18° con fase al azar fija por gránulo (sal `s159-mxd03-r`), como en `experiments/_s151_mxd03_sola_123/README.md`. **Sólo en los records con cenit ≤ 35° (2.046, en 511 gránulos)** | **nulo de P2** (§6) y nulo de la vara VIIRS (§7). Es el mismo juego de semillas para las dos cosas. Sobre 35° no se corre: con bow tie una traslación rígida no imita a MxD03 (1.23, versión 3) |

**X en el arnés, no en `pipeline/`** (§11, punto 2). El arnés reemplaza `process_modis.read_modis_l1b` por un lector que
devuelve la lat/lon de MxD03, igual que `experiments/_s159/m/probe_m.py` (l. 181 a 201). R reemplaza la lat/lon por la
de `_interp_geo` trasladada. Así el A/B no toca `pipeline/` (A45). El flag se escribe sólo si el veredicto lo justifica,
y tiene que reproducir X record por record en una muestra fija (§10).

**Ángulos.** En X y en R los ángulos siguen saliendo de `_interp_geo`. No entran a la detección ni a la magnitud
(`process_modis.py:268-271`; único consumidor `observation_geometry`, `:1624-1625`). Los estratos de cenit y lado se
fijan con el record de **K**, iguales para todos los brazos.

**Atribución por pieza (A114, A75), sólo en las pasadas que cambian.** La posición entra por dos caminos: el **fondo**
(`dist` al centro del volcán, `process_modis.py:560`, que arma el anillo de 5 a 25 km en `:582` y de ahí `t_bg`,
`std_bg` y el NTI de fondo) y la **detección** (todo lo demás, §4). En cada pasada cuya publicación difiera entre K y X
el arnés corre dos brazos más:
- **X_fondo**: posiciones de K, salvo el anillo, que usa MxD03;
- **X_det**: MxD03, salvo el anillo, que usa las posiciones de K.

Controles de identidad que tienen que dar exactos: X_fondo con las dos grillas iguales da K, y X_fondo y X_det
combinados dan X. Atribuye, no decide.

## 4. Dónde llega la posición (A118): consumidores en MODIS

Leído en `pipeline/process_modis.py` de `origin/main` (`7689c487a`). El verificador comprobó cada línea.

| consumidor | línea | qué puede cambiar | cómo lo ve el evaluador |
|---|---|---|---|
| distancia al centro, anillo de fondo de 5 a 25 km | `:560`, `:582` | `t_bg`, `std_bg`, umbrales, NTI de fondo; magnitud que cruza cero | P2, M; X_fondo |
| distancia al ancla por píxel | `:564` | máscara de cumbre (`:838`, `:977`), umbrales duales de los Tests 2 y 3 (`:698`, `:741`, `:924`, `:1019`), `n_first_pass_summit` (`:959`) | P1, P2; X_det |
| ROI de escena por caja de `radius_km` | `:581` | si un píxel entra a la escena; en el borde del barrido, si hay record | control 4 (§8): los `None` por brazo |
| máscara del p95 local | `:657` | el umbral local | P2 |
| zonas excluidas y cuerpos de agua (Villarrica, Láscar, Copahue, Llaima, Tupungatito) | `:1046` | qué píxeles se borran | P1, P2 |
| posición de cada píxel anómalo | `:1141-1142` | el filtro de distancia de `store.py` | P1, P2 |
| cúmulo anclado al cráter | `:1168` | selección del primario, `distance_class` (sale del hotspot final, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`) | P1, P2, P4, varas |
| camino del vent y Test 1 | `:1287`, `:791` | nada en K (`ENABLE_VENT_PATH_MODIS` y `ENABLE_TEST1_PATH` en False) | huella: 0 `triggered_test1` |
| kernel local 3x3 y vecinos del dNTI | índice de arreglo | nada | no se mide |

## 5. Ventana y población

**Ventana: 2026-03-01 a 2026-10-16.**
- MODIS es completo y plano en la tabla desde marzo (A119 b, `scripts/calidad_referencia_mirova.py`).
- Termina el 16-oct porque **del 17 al 20 de octubre CMR no sirve MOD021KM** (`experiments/_s159/cob/INFORME.md` H2).
  Esos días se declaran fuera y no se reponen (criterio de D-29).
- El 13-oct, que D-29 excluye en VIIRS, en MODIS tiene sus records (COB: los 46 del día son MODIS y NOAA-20) y queda
  dentro.
- Enero no se usa (A119). Febrero sólo para controles. 2025 no sirve: la tabla del scraper parte el 2026-01-10 y el OSF
  es filtrado (A105).

**Las etiquetas que deciden salen sólo de la tabla (H8).** En esta ventana ninguna alerta MODIS depende del OCR: las 92
alertas tienen fila del consolidado (`verificador/extra_verif_salida.txt` (b)). La frase de la v1 sobre «5 alertas de
Láscar que dependen del OCR» venía de la marca S151 de A119, de otra ventana, y se retira. Ninguna alerta MODIS nocturna
de MIROVA de la ventana queda sin record nuestro a ±120 s (`extra_verif_salida.txt` (a)).

**Pareo: ±120 s, fijo (H5).** El frente de pareo y su verificador confirmaron ±120 s
(`experiments/_s159/pareo_modis/verificador/INFORME.md`, afirmación 1): ensanchar no rescata ninguna alerta en los tres
sensores (l. 136) y sólo duplica el conteo. También confirmaron que MIROVA lista el gránulo del sur de una pasada partida
(Aqua 70 de 70, Terra 57 de 60). **Matiz que hereda este A/B:** que MIROVA sólo alerte cuando el cráter está en ese
gránulo está probado casi entero con VIIRS 375. **En MODIS descansa en una sola alerta** (n = 1; matiz a de la
afirmación 2 y hallazgo 3 de ese informe). Los negativos limpios contaminados son 0,9 % en MODIS (54 de 6.156), 2,0 %
en VIIRS 375 y 1,4 % en VIIRS 750.

**Población: el censo de las pasadas MODIS nocturnas de la ventana con record nuestro**, etiquetadas con
`banco_paridad.etiquetar` (lectura A; la regla SN de D-9 no toca MODIS, `clase_mirova.SENSORES_MINIMA = ("VIIRS375",)`).
Son 5.465 records en **1.232 gránulos**. 2.046 records tienen cenit ≤ 35°, en 511 gránulos (`censo_granulos_salida.txt`).
Medido sobre los JSON de `origin/main` `7689c487a` y la referencia remota (consolidado `c110787a`, OCR `4ddd5481`). El
verificador reprodujo estos números exactos.

| etiqueta | n | K publica |
|---|---|---|
| alerta protegida (1 MW o más) | 50 | 48 |
| alerta bajo 1 MW | 42 | 32 |
| negativo limpio | 5.110 | 39 |
| `sin_info` | 253 | 6 |
| `far_ref` | 10 | 0 |

Por tramo de cenit (record de K) y lado del barrido:

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

**Fuera de P1 y P2, informado aparte (A118 c):**
- Las **222** mitades de pasada partida (`extra_verif_salida.txt` (d)). 112 son negativos limpios, y 104 de ésos tienen a
  su hermano en `sin_info`. Cuando MIROVA lista el gránulo sin cráter, un cambio de X en la mitad que sí lo tiene es
  invisible para P2. Se lista cada cambio de publicación de X en esas mitades.
- Los `sin_info` (253, K publica 6) y los `far_ref` (10).

**Lo que esto dice antes de correr nada.**
- **El poder del veto es de Láscar y Chillán, y está bajo 40°.** Las alertas MODIS son Láscar 80 (40 protegidas),
  Chillán 10 (9) y Villarrica 2; los otros ocho volcanes no tienen ninguna. 44 de las 50 protegidas tienen cenit de 40° o
  menos.
- **El poder efectivo del veto son 4 protegidas (H6).** Son las que tienen el cúmulo de K a menos del corrimiento
  mediano de M del borde de `inner_radius_km`: Láscar 2026-03-09 07:10, 2026-03-27 07:10 (la que vetó la caja de D18) y
  2026-04-08 01:50, y Chillán 2026-10-10 07:40. Las cuatro tienen cenit de 25 a 40° del lado del frame 0. Para ese tramo
  no hay corrimiento medido, así que se usó el de 40 a 50° como cota. Las otras 44 que K publica tienen el cúmulo lejos
  del borde: perderlas exigiría un cambio por otra vía (fondo, selección).
- **En noches, MODIS casi no decide (A94).** De 44 noches-volcán con protegida MODIS, 43 ya tienen una publicación VIIRS
  de K; de 39 con alerta bajo 1 MW, 38. Este A/B es sobre la paridad del sensor MODIS.
- **La base de P2 es Cordón Caulle.** Hoy la suma de K es 10 alertas bajo 1 MW sin publicar más 39 negativos limpios
  publicados, o sea 49. 31 de esos 39 negativos son de Cordón Caulle (Láscar 5; Isluga, Chillán y Chaitén 1 cada uno).
  De los 31, 7 tienen el cúmulo a 17 km o más del cráter (inner 20), 13 a 3 km o menos y 6 tienen cenit sobre 40°
  (`verificador/extra_negpub_salida.txt`). Es el lacolito difuso (A20). Corrimientos de 1 a 5 km pueden meterlo o sacarlo
  del círculo por razones que nada tienen que ver con la geolocalización correcta. Por eso P2 necesita un nulo medido
  y se informa también sin Cordón Caulle.
- **Pieza de fondo:** cúmulos `summit` de 0,1 MW o menos, donde un cambio de 0,2 a 0,4 K en el fondo cruza cero. Hay en
  Láscar 10 alertas bajo 1 MW (6 con el cúmulo del cráter en 0,0 MW, que K no publica), 6 negativos y 5 `sin_info`, y
  en Chillán 1 negativo.
- **Lo que X no puede recuperar:** las protegidas de Chillán del 12 y del 15 de octubre (M H4).

## 6. Métricas y reglas

Todo por **pasada MODIS**, contra K, lectura A (la regla original da lo mismo en MODIS). «Publica» es el predicado de
`frontend/index.html` ejecutado con node (A97), con su sha256 impreso. Por noche-volcán, por tramo y por lado se informa
y no decide.

| prueba | qué cuenta | regla | decide |
|---|---|---|---|
| **P1 veto** | protegidas que K publica y X no | VETADO con una sola. Es la regla 1 de MISSION, sin ruido que la absuelva. Por cada protegida perdida se informa en cuántas de las R0 a R19 también se pierde (su fragilidad, como en 1.23), sin cambiar el veto | sí, todo el cenit |
| **P2 suma bajo 1 MW** | S = alertas bajo 1 MW que el brazo no publica + publicaciones en negativos limpios; Δ_X = S(X) - S(K) y Δ_Rk = S(Rk) - S(K) | **En las pasadas con cenit ≤ 35°**: ruido = el segundo mayor de los 20 valores de abs(Δ_Rk), o sea el percentil 95 de una muestra de 20 (elegido). GANA si Δ_X < -ruido, PIERDE si Δ_X > ruido, EMPATE si no. Se informa además el rango de Δ_X entre los Δ_Rk (comparador, como D-28) | sí, sólo ≤ 35° |
| **P2 sobre 35°** | Δ_X en las pasadas con cenit sobre 35° | se informa con la lista pasada por pasada; sin nulo comparable | no (§11, punto 4) |
| **P2 sin Cordón Caulle** | lo mismo sin ese volcán, ≤ 35° y sobre 35° | se informa; si su signo difiere del de P2, la primera línea lo dice | no |
| **P1b cruce de 1 MW** | protegidas que K muestra con 1 MW o más y X bajo 1 MW | se listan; con una o más decide Nicolás | lista |
| **P3 vara VIIRS** | §7 | INTERP MAS CERCA con control de sesgo **detiene** el ciclo hasta explicarlo | sólo detiene |
| **M magnitud** | en alertas que K y X publican con VRP de MIROVA: d = abs(log10(X/MIROVA)) - abs(log10(K/MIROVA)), más d′ contra la ganancia uniforme ĝ = mediana de X/K (D-28) | **sólo informa** (H2): mediana, intervalo por bloques noche-volcán, ĝ y d por volcán | no (§11, punto 6) |
| **P4 el cúmulo se mueve** | centroide movido más de 0,01 km, y cambios de `distance_class` | si alguna es protegida, auditoría espacial A61 de todas antes de adoptar | condiciona |
| **P5 atribución** | X_fondo y X_det, `t_bg_k`, `diag_n_first_pass_summit`, cruce de `inner_radius_km`, en cada pasada que cambia | se informa | no |
| **P6 fuera del censo decisor** | cambios de publicación de X en las 222 mitades partidas, en `sin_info` y en `far_ref` | se listan | no |

**Por qué M sólo informa (H2).** K queda bajo MIROVA en 77 de 80 pares (K/MIROVA mediana 0,532,
`verificador/m_sensibilidad_salida.txt`). Con un X uniforme igual a 0,97·K, la regla sellada de D25 da EMPEORA con un
intervalo de ancho cero ([+0,0132; +0,0132]). Bloquearía por una diferencia que el operador no distingue, en un sensor
que ya está a la mitad de MIROVA por otras causas (D25, D33, D17). Y M midió X/K mediano de 1,00 a 1,03. La alternativa,
juzgar EMPEORA con el comparador de D-28 (d′), ya no bloquea por una ganancia uniforme, pero se aparta del texto
sellado de D-28 («EMPEORA se sigue juzgando sobre d»). Eso sería una regla nueva sin pruebas propias en un A/B que no
es de magnitud. Queda como alternativa en el §11.

**Por qué el nulo de P2 es R y no K2 (H1).** P2 no mide ruido de máquina sino cuánto se mueven los casos de borde ante
cualquier corrimiento del tamaño del de X. R es justo eso: el mismo módulo en km, sin información de dirección. Si el
saldo de X no sale del vaivén que produce un corrimiento sin información, X no daña ni ayuda más que el azar del borde.
El nulo puede dar distinto de cero: el control 2 del §8 exige que R mueva la grilla y al menos un cúmulo antes de
usarlo.

**Umbrales (A115).** El veto y la suma son el criterio de MISSION. Elegido y dicho como elegido: el percentil 95 de 20
semillas, los cortes de 35° y 50°, el 0,01 km de P4, los mínimos de la vara y el corrimiento usado para «expuesta».

**Predicciones (escritas antes de correr; no deciden).**
1. P1: CUMPLE. Si cae algo, una de las 4 protegidas expuestas (25 a 40° del frame 0). En Láscar la fuente está en el
   cráter y X la acerca, así que se espera que se muevan hacia adentro.
2. P2 ≤ 35°: EMPATE. Lo que se mueva, mayormente en Cordón Caulle, y dentro del vaivén de R.
3. M: X/K cerca de 1.
4. Vara VIIRS: MXD03 MAS CERCA bajo 35° (ya lo dio 1.23, n = 76); entre 35 y 50°, descriptivo.
5. En noches: 0 o 1 noche cambia.

## 7. Contra qué se mide la posición (informa o detiene; no adopta)

Un radio no es una posición (A93, A107). La `Distancia_km` de MIROVA no trae acimut (D15 del catálogo, no re-medida
aquí). La posición se mide con dirección, y la distancia escalar sólo descarta.

**Lo que no sirve.** Los TIF UTM nativos del 14 y 15 de septiembre (A106) fueron sólo de VIIRS 375. Los GeoTIFF MODIS
de MIROVA que leí están en EPSG:4326, en 51 × 51 celdas de ~1 km. Eso está medido en **una muestra de 10** de las 5.540
imágenes distintas (8 repartidas de mayo a septiembre y 2 del 14-sep: `tif_modis_cobertura_salida.txt`,
`tif_modis_14sep_crs_salida.txt`), no en todas (H8). Medirlas todas se puede hacer bajando sólo la cabecera de cada TIF
(unos 20 KB por archivo), y se recomienda hacerlo antes del candado si la vara V-TIF entra.

**V-VIIRS, la vara física (detiene).** El instrumento de la tarea 1.23 sin cambios
(`experiments/_s151_mxd03_sola_123/construir_vara_viirs.py`, lectura 3 de `evaluar_sola.py`):
- la posición del objeto caliente según VIIRS 375 esa misma noche (otro sensor, geolocalización VNP03IMG/VJ103IMG,
  píxel de 375 m), en el nivel estricto (alerta de MIROVA, cúmulo que no viene del Test 1);
- dd = |K - v| - |X - v| en el píxel MODIS más caliente, elegido por índice;
- bootstrap de noches;
- nulo con los pares de traslaciones R (las mismas R0 a R19 del §3);
- control de sesgo por satélite (Terra y Aqua corren la grilla en sentidos opuestos).

Bajo 35° decide si **detiene** (INTERP MAS CERCA con el mismo signo en los dos satélites). Sobre 35° es descriptiva: el
nulo no es comparable por el bow tie, que es un corte propio. Coppola 2016a avisa la pérdida de precisión con ángulos
altos sin dar un número. Sesgo declarado: bajo 35° la vara de 1.23 fue 70 de 76 gránulos de Láscar.

**V-TIF, la vara de paridad (informa).** Dónde puso MIROVA el calor de esa misma pasada: su GeoTIFF MODIS
(`MendozaVolcanic/mirova-tif-archive`, índice en `3660cdfa`), con 5.540 imágenes distintas del 2026-05-09 al 2026-09-22.
De las filas de alerta MODIS de la ventana en ese tramo, 26 de 33 tienen TIF de su pasada a ±5 min, todas con md5
nuevo (`tif_modis_para_alertas_salida.txt`; filas sin deduplicar, casi todas de Láscar). Antes de usarla:
- **Georreferencia verificada** (A106): en Láscar, con cenit ≤ 25° y alerta, la celda de máximo local tiene que caer a
  una celda o menos del cráter.
- **Máximo local, no global**: el máximo global del TIF de Láscar del 14-sep 07:35 está en el borde oeste, a unos 25 km
  del cráter (A24). La posición de MIROVA es la celda de máximo dentro de 5 km del cráter.
- **Hora de adquisición del índice** y fuera las imágenes repetidas (A106).
- **No es independiente** (A109): sale del mismo gránulo. Mide paridad con la geolocalización de MIROVA, no verdad
  física.

Con unas 20 pasadas, SIN PODER si quedan menos de 10 pasadas o 5 noches.

**`Distancia_km`, sólo para descartar**: la fracción de alertas compatible por brazo (diferencia de hasta una celda más
medio píxel).

## 8. Controles, y el diseño del evaluador

**Controles** (si uno falla, lo que depende de él queda INDECIDIBLE):
1. **Instrumento de geometría**: control positivo de S151 (Láscar `MYD021KM.A2026073.0705`, 2,581 km ±0,05) y nulo
   `_interp_geo` contra sí misma (0 en todos los gránulos).
2. **R vivo**: en cada gránulo, el módulo aplicado es igual al pedido (10 m) y los rumbos quedan cada 18°. En el censo
   ≤ 35°, al menos un cúmulo publicado de alguna Rk se mueve más de 0,5 km respecto de K. Si no, el nulo no puede ver un
   borde y P2 queda INDECIDIBLE.
3. **K2 = K exacto** en el 100 % de los records (identidad, no ruido).
4. **El arnés reproduce producción, sin tolerancia donde decide (H9).** 5.449 de los 5.465 records de la ventana fueron
   escritos por 5 `codigo_sha` cuyo `pipeline/` difiere del de `7689c487a`, y 16 por 7 que no difieren
   (`shas_vs_main_salida.txt`; 12 shas en total). Una diferencia entre el K del arnés y el record de `data/` puede ser
   deriva de versión y no un arnés roto. Por eso:
   - En las **92 alertas, los 39 negativos publicados y las pasadas expuestas** se exige igualdad exacta (decisión de
     publicar y `primary_cluster.vrp_mw` a 0,001 MW). Cada diferencia se re-corre con K **en el `codigo_sha` del record**
     (checkout de ese sha en el job). Si así reproduce, es deriva de versión: se lista y la base del veredicto es el K
     del tag. Si no reproduce, el arnés está roto y todo queda INDECIDIBLE.
   - En el resto, 98 % o más (umbral heredado de F/K, elegido), estratificado por `codigo_sha`.
5. **Cobertura** (A108): los mismos gránulos en todos los brazos; el 100 % de los 1.232 gránulos. Los `None` de
   `calculate_vrp` se cuentan por brazo y se listan. Lo que falte por CMR tras el reintento queda INCOMPLETO y se repite
   la parte sobre el mismo código.
6. **Referencia congelada**: consolidado y OCR congelados al sellar, sha256 LF en un `MANIFIESTO.json`. Entre dos
   corridas de esta tarde el consolidado remoto cambió de `292e3782` a `c110787a`.
7. **Controles positivos del etiquetado** (en verde hoy, `sustrato_mirova_modis_feb_salida.txt`): Láscar 2026-02-11
   07:00 `bajo1`; Láscar 2026-03-27 07:10 `protegida`; Chillán 2026-06-01 08:15 y Cordón Caulle 2026-06-19 01:15
   negativos limpios.
8. **Cableado**: hash de la grilla lat/lon por brazo (X = MxD03, K = `_interp_geo`, Rk = trasladada); ángulos iguales
   en todos.

**Evaluador nuevo, `evaluar_mxd03.py` (H3; se diseña aquí, no se implementa).** `evaluar_d25.py` no sirve: fija
`SENS = ("VIIRS375", "VIIRS750")` (l. 65, rama `s159-evaluador-d25`), descarta MODIS y lee directorios de reproceso por
perfil.
- **Entrada**: los jsonl del arnés, una fila por record y gránulo, con el record publicado de cada brazo (K, K2, X,
  R0 a R19 cuando corresponda, X_fondo y X_det cuando corresponda), el hash de grilla, el corrimiento pedido y aplicado,
  la versión del L1B y del MxD03, y la geometría del cráter. Más el `MANIFIESTO.json` de la referencia y la lista de
  gránulos pedidos.
- **Reglas propias**: P1, P2 con el nulo R, P2 sobre 35° y sin Cordón Caulle, P1b, P4, P5 y P6, los controles 1 a 8, y
  el etiquetado con `banco_paridad.etiquetar` a 120 s (importado, no copiado).
- **Reglas importadas sin copiar**: para M, que sólo informa, `regla_m`, `calibrar_simetrico` y `comparar_con_ganancia`
  de `evaluar_d25.py`. Requiere que esa rama esté en `main` antes del tag; si no lo está, M se informa sin intervalo.
  Para la vara, la lectura 3 de `experiments/_s151_mxd03_sola_123/evaluar_sola.py`.
- **Estratos de M** (informan): un estrato por volcán con 3 pares o más (Láscar 72 y Chillán 7 de 80, según el
  verificador), más cenit ≤ 35° y sobre 35°.

**Pruebas, en `probar_evaluar_mxd03.py`.** Cada una se escribe primero contra un evaluador vacío o mutado, tiene que
**fallar** ahí y **pasar** con el evaluador correcto (S140):
1. Una protegida que X apaga da VETADO, aunque 15 de las R también la apaguen.
2. P2: con Δ_X = +3 y Δ_R entre -1 y +1 da PIERDE; con Δ_X = +1 y Δ_R entre -3 y +3 da EMPATE; con Δ_X = -3 da GANA.
3. Con todas las Δ_R iguales a 0 y R sin mover ningún cúmulo, P2 da INDECIDIBLE (control 2), no GANA ni PIERDE.
4. Un cambio de X con cenit de 40° no entra a la decisión de P2 y sí a su informe.
5. Un negativo de Cordón Caulle publicado de más cambia P2 y no cambia P2 sin Cordón Caulle.
6. Un cambio en una mitad de pasada partida cuya hermana es `sin_info` sale en P6 y no en P2.
7. K2 distinto de K da INDECIDIBLE.
8. Una alerta donde el K del arnés difiere de `data/` y no reproduce en su sha da INDECIDIBLE; si reproduce, da «deriva
   de versión» y sigue.
9. X = 0,97·K en todas las alertas: M informa EMPEORA en d y ĝ = 0,97, y el veredicto no cambia (H2).
10. Vara: X más lejos con el mismo signo en Terra y Aqua detiene; con signos opuestos da SESGO POR SATELITE y no
    detiene.
11. Un `None` sólo en X se cuenta en cobertura y no rompe el evaluador.
12. Una alerta pareada a 150 s no entra (el pareo es 120 s).

Mutaciones del evaluador contadas sólo si las atrapa una aserción, con control de caída (S156): el ruido de P2 tomado
de K2; P2 decidido sobre todo el cenit; el veto absuelto por R; M bloqueando; pareo a 300 s. Después, verificador con
contexto limpio sobre el evaluador y el arnés.

## 9. Despacho y costo (no despachar sin el sello)

**Orden.**
1. Sello de Nicolás sobre este documento y el §11.
2. Candado del §8 mergeado y verificado, con `evaluar_d25.py` en `main` si M se informa con intervalo.
3. Cupo: el NRT ocupa 11 jobs cada 2 h, el tope de la cuenta es 20 y nunca hay más de dos A/B vivos.
4. Referencia congelada.
5. Tag sobre `main`:

```bash
git tag -a s159-mxd03-codigo -m "codigo del A/B de MxD03 sobre K" origin/main
git push origin s159-mxd03-codigo
git rev-parse s159-mxd03-codigo^{commit}
```

6. Cada despacho **desde el tag** (A108, S152), el siguiente recién cuando el anterior terminó:

```bash
gh workflow run probe-mxd03-ab.yml --ref s159-mxd03-codigo -f preregistro_aprobado=si -f desde=2026-03-01 -f hasta=2026-10-16 -f parte_ini=0 -f parte_fin=7 -f partes=24
```

Luego se repite con `8 15` y `16 23`.

El workflow es el de M (`experiments/_s159/m/probe-s159-m.yml`) con estos cambios:
- `workflow_dispatch` con `"on":` entre comillas (A43);
- autenticación sólo por `EARTHDATA_TOKEN`, que falla al instante si viene vacío (A71);
- `ubuntu-24.04` fijado;
- **partes armadas por gránulo**, no por record (H7): los 1.232 gránulos se reparten en 24 partes, y cada gránulo se
  baja una sola vez y sirve a todos sus records (4,4 en promedio; Láscar y Lastarria comparten).

**Costo, medido** (`tiempo_proceso_vs_descarga_m_salida.txt`, sobre el log del probe M, run 39681481914):
- Búsqueda en CMR más descarga de L1B y MxD03: media **32,8 s** por gránulo (mediana 17,5; p90 72; máximo 293 con
  reintentos).
- Proceso: la geometría de S151 más tres corridas de `calculate_vrp` + `append_record` toman mediana 6,4 s. Por corrida
  son **≤ 2,15 s** (cota alta, porque incluye la geometría).

| componente | cuenta | horas de runner |
|---|---|---|
| bajar 1.232 gránulos | 1.232 × 32,8 s | 11,2 |
| K, K2 y X en 5.465 records | 5.465 × 3 × 2,15 s | 9,8 |
| R0 a R19 en los 2.046 records con cenit ≤ 35° | 2.046 × 20 × 2,15 s | 24,4 |
| X_fondo y X_det en las pasadas que cambian | M dio 12 de 63 sobre 40°; aun con 500 pasadas, 500 × 2 × 2,15 s | ≤ 0,6 |
| arranque de 24 jobs (~1,8 min cada uno, `tiempo_por_dia_reproc_salida.txt`) | | 0,7 |
| **total** | | **≈ 47 h** |

En 24 partes son ~2 h por job (1,3 × 2 = 2,6 h, bajo el tope de 6 h, A15). En tres tandas de 8 son **~6 a 8 h de
pared**. La alternativa de un reproceso por brazo sigue costando 235 h o más sólo en descarga (1,86 min de búsqueda y
descarga por día-volcán, `tiempo_por_dia_reproc_salida.txt`, porque `scripts/run_pipeline.py:213-218` filtra el sensor
después de `fetch`). Además mete el ruido entre CPU (S152) en la comparación, y con 20 semillas de R sería impagable.

## 10. Riesgos, y lo que no decide

**Riesgos del diseño.**
- **El arnés no es `run_pipeline`.** Reproduce sus argumentos (verificador de M), y el control 4 lo ata a `data/`. En la
  adopción, el flag escrito tiene que reproducir X record por record en una muestra fija: los 85 gránulos de M más tres
  días de Láscar y tres de Chillán.
- **Poder concentrado.** El veto real son 4 protegidas de Láscar y Chillán. Un CUMPLE SIN DAÑO no dice nada de las
  alertas de los otros nueve volcanes, que no tienen ninguna. Para ellos sólo cuentan los negativos (5.110; K publica
  39, 31 de Cordón Caulle).
- **R sólo bajo 35°.** Sobre 35° no hay nulo para P2, y ahí está el corrimiento mayor (5 km sobre 50° del frame 0) y 6
  de los 31 negativos publicados de Cordón Caulle. Lo que pase ahí se lista pasada por pasada (§11, punto 4).
- **La regla del gránulo sur en MODIS descansa en n = 1** (verificador del pareo). Si fuera falsa en MODIS, algunas
  RUTINA del gránulo sur serían «no miré» y no negativos. El efecto está acotado por el 0,9 % de negativos contaminados.

**Lo que no decide.**
- **Que X mejore algo.** CUMPLE SIN DAÑO significa «no daña la réplica».
- **La paridad de posición con MIROVA del §1 de la v1** («poniendo el calor donde lo ve MIROVA»): ninguna prueba la
  decide. V-VIIRS sólo puede detener y V-TIF sólo informa.
- La magnitud MODIS (D25, D33, D17): M sólo informa.
- Las protegidas de Chillán a 58° (M H4).
- D18: su veto cayó en una protegida de Láscar con el píxel a 3,2 km, corrido por esta misma geolocalización. Si X se
  adopta, la caja se vuelve a medir sobre X.
- VIIRS, y la noche del operador (43 de 44 noches con protegida ya publican VIIRS).

**Qué se hace con cada veredicto.**

| resultado | qué se hace |
|---|---|
| P1 sin pérdida, P2 ≤ 35° GANA o EMPATE, la vara VIIRS no detiene, controles en verde | **CUMPLE SIN DAÑO**. Se abre el ciclo de adopción **si Nicolás lo pide por fidelidad literal**: tag defensivo, flag `enable_modis_geo_mxd03` con TDD y reproducción de X, su «sí» (A45), FICHA SDA, D34 con marcas A113, marca visible de la fecha en las tres vistas (el marcador MODIS se corre 2 a 5 km) y aviso a OVDAS |
| P1 VETADO o P2 ≤ 35° PIERDE | **NO CUMPLE**: no se adopta. Cada pérdida con atribución (P5) y auditoría espacial A61 |
| la vara VIIRS detiene | se busca primero el error en la vara o en el arnés |
| P1b con alguna, o P2 sobre 35° con un saldo positivo que la primera línea marque | decide Nicolás con la lista |
| INDECIDIBLE o INCOMPLETO | repetir la parte sobre el mismo código, tope dos; un INDECIDIBLE de controles no se repite, se busca el defecto |

## 11. Lo que tiene que decidir Nicolás para sellar

1. **¿La pregunta («¿daña la réplica?») y los brazos K, K2 (identidad), X y R0 a R19?** Recomendado: sí.
2. **¿X en el arnés, sin tocar `pipeline/` hasta el veredicto?** Recomendado: sí. Es el brazo B de M, ya verificado.
3. **¿Arnés partido por gránulo (~47 h de runner, ~6 a 8 h de pared) en vez de un reproceso por brazo (≥ 235 h)?**
   Recomendado: sí.
4. **P2 sobre 35°**, donde no hay nulo comparable. Recomendado: **que informe**, con la lista y una línea en la cabecera
   si su saldo es positivo. Alternativa: que decida con el saldo crudo (sin nulo), y entonces un borde de Cordón Caulle
   puede vetar.
5. **¿Nulo de P2 con el percentil 95 de 20 semillas?** Recomendado: sí (elegido; con 20 semillas el mínimo p nominal es
   1/21). Alternativa: 40 semillas, que duplican la fila de R (~24 h más).
6. **M.** Recomendado: **sólo informa** (§6). Alternativa: EMPEORA juzgado con el comparador de D-28 (d′ contra ĝ) que
   bloquea. No bloquearía por un 3 % uniforme, pero es una regla nueva respecto de lo sellado en D-28.
7. **¿Ventana 2026-03-01 a 2026-10-16, sin el 17 al 20 de octubre?** Recomendado: sí.
8. **¿La vara VIIRS sólo detiene y V-TIF sólo informa?** Recomendado: sí. Alternativa: exigir MXD03 MAS CERCA para
   adoptar (bajo 35° ya se sabe que da eso).
9. **Documentos del sello**: D34 en `docs/MIROVA_DIVERGENCES.md`, marcas A113 en D18 y en `docs/SINTOMAS.md` §3, y
   Coppola 2026 a la lista de papers de MISSION. Recomendado: sí, en el mismo PR.
10. **¿Medir el CRS de los 5.540 TIF MODIS (sólo cabeceras) antes del candado?** Recomendado: sí, si V-TIF entra.
11. **Orden con D18**: re-medir la caja sólo después de este veredicto, sobre X si se adopta. Recomendado: sí.
12. **Qué hace un CUMPLE SIN DAÑO.** Recomendado: abrir la adopción por fidelidad literal (Coppola 2026) y por la
    posición que ya midió M. Alternativa: no adoptar hasta que una vara con poder (más TIF, o una ventana con más
    alertas fuera de Láscar) muestre paridad de posición.
