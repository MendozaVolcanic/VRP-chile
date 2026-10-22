# Auditoría S160: los instrumentos, las unidades, lo que vence y los cierres con número

> 2026-10-22, orquestador Opus 5.5. Código auditado: `origin/main` = `d516b9d8c` (instantánea en
> `D:\vrp-trabajo\temporales\s160_audit\main\`). Plan: `docs/PLAN_AUDITORIA_S160.md`, sellado en `06e0fad3b` y, para
> F1a y F1b, en `60762a939` (R7 fijada por Nicolás: 5 %, 1.000 barajados, intervalo de 95 %). Todo lo que sigue sale
> de veredictos de verificador con contexto limpio; lo que sólo vio un auditor está marcado así. Informes, scripts y
> salidas: `experiments/_s160_audit/<agente>/`. Registro de modelo, duración y consumo:
> `experiments/_s160_audit/REGISTRO_AGENTES.md`.

## 0. En una pantalla

1. **Lo que está en producción se sostiene.** La regla con que se adoptó K es débil (aprueba un placebo que apaga al
   azar el 1 % de las publicaciones, porque P2 tiene tolerancia 0), pero K supera ese margen por mucho y no pierde
   ninguna protegida que decida: la probabilidad de lograrlo apagando al azar lo mismo va de 3e-4 a 6e-39 (V1a). La
   debilidad sí importa hacia adelante: `evaluar_d25.py` hereda la misma P2 y D25 es un A/B pendiente.
2. **El riesgo más cercano es una plataforma callada.** Cuando la búsqueda de NASA deja de servir una plataforma o
   MODIS entero, el NRT dice «Cobertura: completa» y sale con 0, también en modo estricto, y el auto-audit no levanta
   bandera cuando falta el record de una pasada con alerta protegida (241 en parte, gravedad 4; V3-01, gravedad 4).
   Suomi NPP cesa el 2026-11-02 13:00 UTC; el PR #892 cubre la vigilancia por plataforma, no el mensaje del NRT.
3. **Lo más grave de detector: 30 de 97 cúmulos de cumbre de VIIRS 750** en la ventana K quedan en 0,0 MW por el
   recorte a cero del fondo y desaparecen del tablero; 7 tenían alerta de MIROVA (203, gravedad 5, V2).
4. **Los documentos que cada sesión lee primero describen datos que ya no están**: el reemplazo del histórico con K
   (#883) no llegó a `MISSION.md`, `CLAUDE.md` ni `SINTOMAS.md`, y nada de S157 ni S158 está en `main` (281 en parte,
   V4-01, V4-02, V0a-01).
5. Pendientes de S158: los 16 verificados (11 confirmados, 4 en parte, 1 refutado en parte); dos suben de gravedad
   (F1-H6 a 4, F6-3 a 3) y uno abre un riesgo nuevo: con el K1 del código de MIROVA, una alerta protegida de Chillán
   quedaría topada en 5 MW (V0b-01).

6. Los «NO ADOPTAR» viejos aguantan: ningún evaluador de prioridad B con código aprueba un placebo (F1b), y los tres
   frentes que F1b creyó cerrados sobre instrumentos ciegos (D18, D22, la conectiva `max`) ya no dependen de esos
   instrumentos (V1b: los tres bajan de 4 a 2). Lo nuevo es V1b-01: el veto que hoy mantiene cerrada D18 depende de una
   sola alerta MODIS de Láscar de exactamente 1,00 MW, el umbral de protegida.

## 1. Los tres números de la regla C

| | confirmados | en parte | refutados | sin dato |
|---|---|---|---|---|
| F1a (V1a: 3 hallazgos y 3 celdas) | 161, 163, R6 | 162, R11 | R17 | |
| F1b (V1b: 5 hallazgos y 45 celdas) | celdas: 25 confirmadas o en parte | 180, 181, 182, 188, 189 (los tres primeros bajan de 4 a 2) | celdas: 11 refutadas, no aplican o literales sin efecto | celdas: 9 |
| F2 (V2: 11) | 202, 203, 205, 206, 207, 208, 213 | 201, 204, 209 | 211 | |
| F3 (V3: 9) | 243, 244, 246, 247, 248 | 241, 242, 245, 252 | | |
| F4 (V4: 12) | 285, 288, 289, 290, 291 | 281, 282, 283, 286, 287, 293 | 284 | |
| Pendientes S158 por F0a (10) | F1-H4, H6, H9, F6-3, F6-5, F6-6, F6-7 | F1-H8, F6-4, F6-8 | | |
| Pendientes S158 por F0b (6) | F4-H5, F4-H7, F4-H8, R2-17 | F4-H2, F4-H3 (refutado en parte) | | |

Hallazgos propios de los verificadores (entran a la puerta de S161 como verificados una vez, por quien los
encontró, y necesitan su propio verificador): V1a-01 a V1a-0n, V2-09 a V2-13, V3-01 a V3-04, V4-01 a V4-03, V0a-01,
V0b-01 a V0b-03. Sin verificar (gravedad 1 y 2 fuera de F1; regla C, son la puerta de S161): F1a 3, F2 9, F3 6, F4 5,
F1b 12 (sus celdas FALLA sí pasaron por V1b).

## 2. Confirmados de gravedad 3 o más, con la guarda que los cerraría

Gravedad del verificador, no del auditor. «Guarda» es la prueba que lo mediría y cómo se vería en rojo (regla B del
protocolo).

| ID | qué pasa (fenómeno primero) | gravedad | guarda y su rojo |
|---|---|---|---|
| 203 | Un cúmulo de cumbre de VIIRS 750 cuyo píxel está a la temperatura del anillo regional o más frío queda en 0,0 MW, y el tablero no publica nada con 0 MW: 30 de 97 en la ventana K, 7 con alerta de MIROVA, 11 negativos limpios, ninguna protegida. El código de MIROVA no recorta ahí. Arreglarlo movería la publicación en los dos sentidos | 5 | contar cúmulos `summit` con `pc.vrp_mw == 0` por sensor en cada auto-audit; rojo: la fracción supera la de la ventana K (31 %) o una protegida cae en el conjunto. Decide Nicolás si entra al A/B del detector del código (§5) |
| 241 | Una plataforma o colección que la búsqueda de NASA deja de servir se lee como «no hubo pasada»: «Cobertura: completa», código 0, también con `--estricto-cobertura`. Las otras plataformas siguen, así que el tablero no queda vacío: se pierden en silencio las pasadas de esa | 4 | el vigilante por plataforma de #892, más un test que simule Suomi NPP vacío y exija un aviso distinto de «completa»; rojo: el mensaje sigue diciendo «completa» |
| V3-01 | Si MIROVA tiene una alerta protegida y nosotros no tenemos ningún record de esa pasada (`sin_record`), el auto-audit no levanta bandera (`scripts/auto_audit_weekly.py:796` y `:827`) | 4 (V3, sin segundo verificador) | caso sintético con una protegida sin record; rojo: el auto-audit no la cuenta |
| 281 | #883 reemplazó todo el histórico por datos de K (68.072 records anteriores al 18-sep son de K) y los documentos rectores siguen diciendo «C0 antes del 2026-09-18» | 4 | test que lea la frontera de `cambio_detector.js` y exija que `MISSION.md` y `CLAUDE.md` la nombren; rojo: la fecha escrita no coincide |
| F1-H6 | Publicamos un cúmulo cuyo modo es de un píxel donde MIROVA suma todos los alertados de la escena: cambia la magnitud de 1 de cada 5 VIIRS 750 publicados (14 de 67 en K) | 4 (F0a) | ya catalogado como D32; guarda: comparación por pasada contra el oráculo del código |
| 202, 205, 206, 213 | Cambios de espacio: el mínimo de cumbre 0,003 y el piso -0,1 quedan 12,5 % más laxos al pasar de 3 × 3 con central a 8 vecinos (202); el C2 del segundo pase usa una sigma de otro pool que MIROVA (205); el anillo de fondo está centrado en el centro del volcán y en PCC el cráter cae dentro del anillo (206); las bandas del auto-audit se calibraron con C0 y juzgan a K (213) | 4 (efecto de 202, 205 y 206 SIN DATO) | 202 y 205: test de equivalencia contra el port del `.m`; 206: test que exija que el cráter quede fuera del anillo en los 11 Tier A; 213: recalibrar y fechar las bandas por detector |
| 285, 286, 289, 293 | Rebajas que no bajaron a sus hijos: A118 dice que D18 nunca se midió (285); marcas de S158 ausentes en `CLAUDE.md` y U1, U3, U10, U12, U13 (286, 293); `README.md` describe el Test 1 integrado vivo (289) | 3 | §4 (marcas aplicadas en esta rama) |
| 282, 283, 290, 291 | Números de cierres que se reproducen en el corpus de su fecha y no hoy, por corpus vivo y por #883 (A90): tope D9, D-4, D27, D33. La marca de D-4 no declara su ventana | 3 y 2 | marca con ventana (§4) |
| 243 | MODIS 6.1 tiene decomiso anunciado (2026-09-30) y no ejecutado; cuando ocurra, el Standard cae al NRT en silencio y nadie mide la proporción de records NRT | 3 | contar por corrida la fracción MODIS `product_version == "nrt"`; rojo: sube de 0 % en dos semanas |
| 245 | La copia horaria de la tabla de MIROVA acepta copias que se encogen (7 en 64 días, 1.948 filas que no volvieron, 14 protegidas) y las propaga al tablero | 3 | validar en el workflow un mínimo de líneas y la cabecera, como ya se hace con el OCR; rojo: una copia con menos filas pasa |
| 247 | `EARTHDATA_TOKEN` vence el 2026-12-07 18:03 UTC (aviso desde el 2026-11-27); un secret ausente da «desconocido» sin issue, y `nrt.yml` no tiene la guarda de token vacío que sí tiene `experimental-diario.yml`: con token vacío, hasta 88 logins por corrida y bloqueo de la cuenta (A71) | 3 | la guarda de `experimental-diario.yml` copiada a `nrt.yml`; rojo: un job con token vacío llega a `auth()` |
| 288 | La memoria del agente conserva cinco cierres rebajados sin marca (`MEMORY.md:50-51`) | 3 | propuesta en `experiments/_s160_audit/marcas/MARCAS_APLICADAS.md` |
| V0b-01 | K1 no decide la detección en producción, pero sí el tope D9 de 5 MW (`_path_d_cap_active` exige `n_nti_path == 0`): con K1 = -0,7, el valor del código de MIROVA para VIIRS 750, la protegida de Chillán del 2026-10-01 06:00 bajaría de 11,08 a 5,0 MW (MIROVA dio 10,0) | 3 (F0b, sin segundo verificador) | antes de adoptar el K1 del código, test de que una protegida no queda topada; C-07 de la cola de campo |
| F6-3 | La decisión «manda el código de MIROVA» para VIIRS 750 se apoya en Etna, único caso con resultado publicado, que no ejercita K1 -0,7, el 0,02 de fuera de la cumbre ni la rama diurna | 3 (F0a) | se cierra con más casos con resultado de MIROVA; no tiene guarda de código |
| V1b-01 | El veto de S151 que mantiene cerrada D18 (la caja de 5 × 5 km) depende de una sola alerta MODIS de Láscar (2026-03-27 07:10) de 1,00 MW, justo el umbral de protegida (`clase_mirova.py` l. 46 y 72), con MIROVA a 1,41 km y nosotros a 3,2 km. Un redondeo de MIROVA decide si la caja se puede adoptar. Que el veto sea frágil es SOSPECHA (no se corrió con la alerta en 0,99 MW) | 3 (V1b, sin segundo verificador) | antes de cerrar un frente por una sola protegida, exigir que el veredicto se sostenga con su VRP en 0,99 y 1,01 MW; C-10 de la cola de campo |

## 3. Refutados y rebajados (lo que no hay que perseguir)

- **211** (VRE del tablero integra 62,5 h por día): REFUTADO por V2; el auditor contó todos los records y la VRE sólo
  suma las válidas (6,2 h por día y volcán). Queda que 15 de 147 días-volcán integran más de 24 h (gravedad baja).
- **284** (D-9 «14 pasadas NONE» sin instrumento): REFUTADO por V4; las 14 y el «5 y 5» salen enteros del script.
- **201** rebajado de 5 a 3: la conversión de unidades es exacta, pero el C1 de escena casi no toca lo publicado (4 de
  2.452 publicaciones V375, 8 de 485 V750, 1 de 129 MODIS).
- **161** rebajado de 5 a 3: el instrumento de K es débil, pero la adopción no se explica por esa debilidad.
- **R17** de F1a: REFUTADO como defecto que toque el veredicto (el cruce de canales de `alerta_protegida` da 0 casos).
- **242** «sin push»: cierto a las 03:08, falso a las 03:33 (PR #892). Un estado externo se fecha.
- **180, 181, 182** (F1b, gravedad 4): bajan a 2 en V1b. D18 la cierra hoy el veto de S151, no S130; la `max` en
  producción no depende de S148 (`REGLA_ADOPCION.md` l. 37 a 39) y el 133 de 143 sale de un control sin su reparación
  (con ella, 137 de 143 y C4 se cumple); dentro de los brazos de S143 no existe el régimen de #535 (0 de 3.400 records
  con máscara de nube) y D22 sigue ABIERTA en el catálogo.
- **F4-H3**: el mínimo de cumbre 0,003 es inerte en el dNTI pero gobierna el umbral del dETI en 6 a 17 % de las
  pasadas (efecto en lo publicado SIN DATO).

## 4. Marcas A113

Aplicadas en esta rama (`s160-auditoria`) **27 marcas**, sólo donde V4 sostiene el hallazgo, con el texto de F4
ajustado a su veredicto (por ejemplo, un número que se reproduce en el corpus de su fecha lleva la ventana, no «no se
reproduce»): 281 en `MISSION.md`, `CLAUDE.md`, `SINTOMAS.md` y D10, D11 y D11-bis del catálogo (9); 282 en A23, D9 y
`MISSION.md` (4); 283 en el criterio de victoria, el glosario e `INDEX.md` (3); 285 en A118; 286 y 293 (U1, U3, U8,
`CLAUDE.md:147-153`); 289 en `README.md` (4); 290 en D27 con el hash de las dos tablas; 291 en D33; V4-02 en el hueco
de nov-2025 a ene-2026 de `CLAUDE.md`. Detalle, una fila por marca: `experiments/_s160_audit/marcas/MARCAS_APLICADAS.md`.

**Sin aplicar (12)**, con su razón en ese archivo: 284 (refutado); U4 (borde que V4 no decide); U10, U13, H8, un YAML y
`BIBLIOGRAPHY_SYNTHESIS.md` (fuera de los documentos permitidos); 287, 288 y U12 (memoria del agente: queda la
propuesta escrita, la aplica la sesión que haga el cierre); V4-01 (es integración de ramas, decisión 5); 292 y 294 a
297 (sin verificador). SIN DATO: si la frontera de #535 sigue separando los datos después de #883.

Tests que leen los documentos tocados: los dos que de verdad abren uno (`test_guard_libro_de_pruebas_s146.py`,
`test_guard_declarado_vs_efectivo_s131.py`) pasan (26 de 26) después de agregar esta auditoría a `INDEX.md`, que la
guarda G6 exige.

## 5. Decisiones de Nicolás, con recomendación

| # | decisión | recomendación |
|---|---|---|
| 1 | Mergear el PR del preámbulo (MendozaVolcanic/VRP-chile#891) | sí; ningún test lo lee y la suite pasa entera |
| 2 | Antes de leer el veredicto de D25 (#890): ¿P2 con tolerancia 0 sirve para decidir D25? | no leer #890 hasta comprobar que su evaluador rechaza el placebo que apaga al azar el 1 % (V1a-01); si no lo rechaza, fijar el margen de P2 contra ese placebo antes de abrir el resultado |
| 3 | Suomi NPP: #892 y el mensaje del NRT | mergear #892 antes del 2-nov y agregar que «sin gránulos de una plataforma esperada» no se llame «completa»; C-06 de la cola de campo lo comprueba el mismo día |
| 4 | El recorte a cero de VIIRS 750 (203) | no arreglarlo aislado (mueve publicación en los dos sentidos): que entre al A/B del detector del código como una de sus diferencias, con C-08 mirado antes |
| 5 | Llevar a `main` lo de S157 y S158 (V0a-01, V4-01) | sí, y pronto: hoy el `CLAUDE.md` que carga cada sesión desde OneDrive no tiene ninguna marca de S157 ni S158 |
| 6 | Reabrir D18 y D22 (180, 182) | no reabrirlos por S160 (los tres hallazgos de F1b bajaron a gravedad 2); sí mirar C-10 antes de dar D18 por vetada, porque el veto cuelga de una alerta de 1,00 MW |
| 7 | Guardas de la referencia (245) y del token en `nrt.yml` (247) | sí; son workflows, no pipeline, pero tocan producción: con tag y tu sí (A45) |
| 8 | Dónde vive la cola de campo | `docs/COLA_CAMPO.md`, abierta en esta rama con 10 casos; la mantiene la síntesis de cada auditoría |
| 9 | K1 del código de MIROVA y el tope D9 (V0b-01) | no adoptar el K1 de -0,7 sin resolver antes que no tope una protegida |

## 6. Cola de campo

Abierta en `docs/COLA_CAMPO.md` con 10 casos: los 5 de `docs/AUDIT_S158_R2.md` §9 y 5 de esta auditoría (C-06 el
cese de Suomi NPP el 2-nov, C-07 Chillán con K1 -0,7, C-08 un cúmulo VIIRS 750 en 0 MW con alerta de MIROVA, C-09 la
alerta OCR de Lastarria del 18-abr que todo evaluador con el combinado cuenta como protegida, C-10 la alerta de Láscar de 1,00 MW que sostiene el veto de D18).

## 7. Lo que la guía no dio (actualiza el §10 del plan)

Los 19 puntos del plan entraron 18 a la guía (`workspace-guias` `f570abd`). Lo que apareció al correr:

1. **El CSV de hallazgos se rompe en silencio.** F2 escribió `hallazgos.csv` a mano y dos filas quedaron con comas sin
   comillas: los campos se corrieron y la gravedad de 203, la más alta del frente, quedó ilegible para el script que
   arma la lista del verificador. Agregado al preámbulo (#891): escribirlo con el módulo csv.
2. **El esfuerzo del subagente no se controla desde el prompt.** V1a declaró haber corrido con esfuerzo bajo aunque
   la tarea pedía `high`. La tabla de modelo y esfuerzo de la guía supone un control que el harness no siempre da: el
   registro tiene que anotar el esfuerzo declarado por el agente, no el pedido.
3. **Los topes de disco se pasan.** F1a llegó a 3 GB con un tope de 2; lo vio el orquestador mirando `du`, no el
   agente. El tope necesita a alguien que lo mida durante la corrida.
4. **La instantánea tiene que traer la configuración de la raíz.** Faltaban `volcanoes.yaml` y `README.md`; F2 extrajo
   el primero fuera de su carpeta (lo declaró) y F4 tuvo que leer el segundo con `git show`.
5. **Un worktree compartido con otra sesión es un riesgo real.** La sesión coordinadora hizo un merge por error en el
   worktree de la auditoría (lo deshizo; el merge no tocaba nada que leyeran los auditores). El plan debe declarar el
   worktree exclusivo y la otra sesión, no tocarlo.
6. **Un estado externo envejece en minutos.** 242 era cierto a las 03:08 y falso a las 03:33. Todo estado de GitHub o
   de NASA que entra a un hallazgo va con su hora del servidor, y el verificador lo vuelve a mirar.
7. **«La rama» no es una sola.** V4 encontró que F4 atribuyó a `loop/activo` lo que vive en el linaje `s160-auditoria`.
   Con tres linajes vivos, el plan tiene que decir qué documentos se auditan en cuál, igual que fija el commit del código.
8. **La lista del verificador no lleva el razonamiento del auditor.** Las celdas de la matriz traían la explicación de
   la FALLA; se quitaron antes de entregar la lista. `armar_lista.py` lo hace para los hallazgos; para las celdas hay
   que hacerlo a propósito.

## 8. Lo que esta auditoría no hizo

Ningún arreglo, A/B, reproceso ni descarga de L1B; no leyó el veredicto de D25; no mergeó nada; no auditó el código
del scraper Mirova-v1 (lo audita la sesión `audit-mirova-v1`); no corrió el frente por uso ni el de prueba de campo.
