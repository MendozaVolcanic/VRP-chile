# Verificación limpia v2 del pre-registro del A/B diurno de VIIRS sobre K (tarea 1.32)

- Hora del servidor (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date`): inicio Mon, 26 Oct 2026 13:01:01 GMT; cierre 13:42:28 GMT.
- Commit medido (`git rev-parse HEAD`): `bf8e24dd571aaccbe3bae3cfaecc24cd1c83e517` (objetos de la v2 en `81e6588dd9ee45485b7cbd65dfd52caf95c9a560`).
- Modelo: Sonnet 5.5. Esfuerzo: bajo (el que fijó quien me lanzó; no lo elegí yo).
- Lista de caminos de ruptura escrita ANTES de abrir `verificador/INFORME.md` y el §12: `verificador_v2/CAMINOS.md`,
  sha256 `93600b30a5f2c7b1fe9b772444800477b4f2a39856145e64fa17529984985f85`, hora del servidor 13:02:49 GMT. Antes de
  escribirla sólo había leído PREREGISTRO.md §0 a §11. No abrí `verificador/` en ningún momento.
- Todo lo que se cita salió de una herramienta de esta sesión. Mis scripts y salidas están en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44\experiments\_s163_diurno_k\verificador_v2\`
  (`esc1.py`, `esc2.py`, `medidas1..6.py` con su `_salida.txt`, `specx.json`/`salidax.txt`, `salida0/1.txt`,
  `nulo_v2_reproducido.txt`). No toqué ningún archivo del repo fuera de esa carpeta. La referencia congelada y la copia
  para mutar viven en mi carpeta temporal (borrada al final).

## Respuesta corta

La regla v2 **no tiene un camino por el que un brazo aleatorio o callado salga ADOPTAR** (medido, ver VERIFICADO LIMPIO) y
los arreglos de la v1 hacen lo que dicen. Pero tiene **un camino real por el que sale ADOPTAR con publicaciones de más
que ninguna regla mira** (V-N4), **el predicado que decide "publica" no está sellado** (V-N1), **la parte de
`main()` que implementa la robustez del §6.4 y la vara de cobertura no tiene ninguna prueba que la cuide** (V-N2) y **I6
(c) está mal calibrada: falla sola 16 a 23 % de las veces con un brazo ruidoso** (V-N3). Ninguno de los cuatro produce por
sí solo un ADOPTAR equivocado con un brazo razonable; los dos primeros pueden hacerlo si alguien toca algo después del
sello sin que ningún sha256 lo note.

## Hallazgos nuevos (ordenados por gravedad)

### V-N1 · El predicado «publica» y otras dependencias del evaluador quedan fuera de lo sellado · GRAVEDAD 3 · CONFIRMADO
- ARCHIVO:LÍNEA: `experiments/_s163_diurno_k/objetivos_sha256.txt` (16 rutas; ninguna es `frontend/index.html`);
  `scripts/banco_paridad.py:71` (`HTML = ROOT / "frontend" / "index.html"`) y `:109-135` (el JS que corre con node:
  `isSummitDetection`, `isValidDetection`, `isThermalArtifact`, `mirovaEqVrpDisplay`); `PREREGISTRO.md:412-414` (el
  `git diff` de §8 sólo mira `experiments/_s163_diurno_k/`, los dos perfiles y el workflow).
- QUÉ PASA: «publica» es el predicado del tablero ejecutado sobre el `frontend/index.html` del árbol donde se corre el
  evaluador, no el del tag ni el del sello. Tampoco están sellados `experiments/_s151_alertas_diurnas/real_o_reflejo_filas.json`
  (variante de reflejo, `evaluar_diurno_k.py:667-669`), `pipeline/store.py::_solar_elevation` (define día) ni
  `experiments/_s162_instrumento/mutar.py`. `frontend/index.html` cambió 5 veces desde el merge de K
  (`git log --oneline -5 -- frontend/index.html`: 3489e55c3, f101d7304, c8fbe5b3a, 34cea39e4, 60c45833f) y
  `pipeline/diurno.py` dice que hay que corregirlo antes de cualquier flip por los records diurnos.
- CÓMO SE VERÍA: si el frontend cambia entre el sello y la evaluación (cosa que el propio plan prevé), `pub` y `disp`
  cambian para los mismos records y el veredicto cambia en cualquier dirección sin que falle un sha256 ni el `git diff` del §8.
- CÓMO REPRODUCIRLO: comparar la lista de `objetivos_sha256.txt` con los imports del evaluador (`banco_paridad`, `HTML`);
  `git log --oneline -5 -- frontend/index.html`.
- Arreglo sugerido (no lo hago): sellar el sha256 del blob de `frontend/index.html` y de `real_o_reflejo_filas.json`, o
  evaluar siempre desde un `git archive` del tag de despacho.

### V-N2 · La robustez del §6.4, la vara de cobertura y la carga real no tienen ninguna prueba que las cuide · GRAVEDAD 3 · CONFIRMADO (que sobreviven mutaciones); lectura del código CORRECTA
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:535-538` (p_sup con `beta.ppf(1 - ALFA, ...)`), `:566-576` (las tres variantes del §6.4),
  `:431-474` (`cargar_brazo`: dedupe, descarte de MODIS diurno), `:67-71` (`es_dia_vol`, `> 0`).
- QUÉ PASA: las 48 mutaciones de `mutaciones.json` caen todas sobre `evaluar()` y las reglas puras; ninguna toca `main()`
  ni `cargar_brazo()`. Escribí 7 mutaciones propias sobre esas líneas (`verificador_v2/specx.json`): variante «tabla»
  usando la unión, variante «sin W2» sin excluir W2, p_sup al 85 % en vez de 95 %, variante «sin reflejo» sin excluir
  nada, records MODIS diurnos entrando, sin deduplicar records, día = elevación > 25°. **Las 7 sobreviven con la batería
  en verde** (`verificador_v2/salidax.txt`: «atrapadas por asercion: 0 de 7»). Leí esas líneas y hoy están bien escritas;
  el problema es que ninguna prueba lo demuestra, y que la única corrida de `main()` sobre datos reales (la prueba de
  humo) dio INVÁLIDO por I1 en todas las variantes, así que ni el cableado de las variantes ni el de p_sup ha producido
  nunca un veredicto distinto de INVÁLIDO.
- CÓMO SE VERÍA: un error de cableado en `main()` pasaría a una evaluación de 39 horas de reloj sin que nadie lo vea hasta
  leer el resultado. Dado que el archivo queda sellado por sha, el riesgo no es una edición futura sino un defecto que ya
  esté ahí y yo no haya visto leyendo.
- CÓMO REPRODUCIRLO: `git archive bf8e24dd… experiments/_s163_diurno_k experiments/_s162_instrumento scripts pipeline
  frontend/index.html experiments/_s151_alertas_diurnas/real_o_reflejo_filas.json volcanoes.yaml | tar -x -C <temporal>`;
  desde ahí `python -I experiments/_s162_instrumento/mutar.py specx.json salidax.txt` (el `specx.json` está en mi carpeta).

### V-N3 · I6 (c) está calibrada para 5 % y la tasa real de falsos de la prueba de signos con placebo simétrico es 7 a 8 % · GRAVEDAD 2 · CONFIRMADO
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:47-48` (`MAX_FALSOS_C = 4`, «P(Bin(40; 0,05) >= 5) = 0,048»), `:345-348`;
  `PREREGISTRO.md:224-225`.
- QUÉ PASA: el placebo c cuenta como «falso» tanto GANA como PIERDE. Cada una es una prueba de una cola al 5 %, así que la
  tasa conjunta de falsos es del orden de 8 %, no 5 %. Medí con la estructura real de bloques de W2 a W6 y un brazo
  ruidoso (q = 5, 20 y 50 %), 400 semillas (161 a 560) por sensor y q (`verificador_v2/medidas4_salida.txt`): tasa de GANA o
  PIERDE entre **0,072 y 0,083** en las seis combinaciones. Con esa tasa, P(5 o más de 40) = 0,16 a 0,23. Con las 40
  semillas oficiales dio 4, 2, 3, 1, 2 y 1 falsos (el primero justo en el límite).
- CÓMO SE VERÍA: un brazo ruidoso (el resultado más probable según la prueba de humo sobre C0) sale INDECIDIBLE por I6 en
  16 a 23 % de los casos en vez de NO ADOPTAR. No es reparable repitiendo jobs (semillas fijas, datos iguales). Dirección
  segura (no adopta), pero «INDECIDIBLE» tapa un NO ADOPTAR claro y la afirmación «0,048» del pre-registro es falsa para
  la unión de las dos colas. De paso: el nulo del §5.1 (i) «GANA en 0 de 200» no prueba nada del tamaño de la prueba de
  signos, porque un brazo aleatorio suma +1 casi siempre y nunca puede dar GANA; el tamaño sólo lo mide este placebo.
- CÓMO REPRODUCIRLO: `python -I verificador_v2/medidas4.py <referencia congelada>`.

### V-N4 · El caso b ADOPTA con publicaciones de más en pasadas «otra», que ninguna regla ni compuerta mira · GRAVEDAD 2 · CONFIRMADO
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:82-86` (casos a y b no miran `pub_otra`), `:320` (`pub_otra` sólo se informa);
  `PREREGISTRO.md:160-162` («lo que el brazo publique ahí queda a la vista en M4, no en la regla»).
- QUÉ PASA: escenario propio `verificador_v2/esc1.py` E1: 1 protegida recuperada, 0 publicaciones en negativos, 60
  publicaciones en pasadas FALSO_POSITIVO diurnas. Resultado: VIIRS375 **ADOPTAR caso b**, global **ADOPTAR**, con las
  dos opciones e-i y e-ii. La población «otra» real es de 265 pasadas (V375) y 60 (V750).
- CÓMO SE VERÍA: ADOPTAR de un brazo que publica en hasta 325 pasadas donde MIROVA no calló del todo (el mismo periodo
  tuvo una alerta o un FALSO_POSITIVO). Es improbable que un brazo callado en 2.246 negativos sea ruidoso justo en «otra»,
  por eso gravedad 2; pero la regla no lo excluye, y la variante e-ii no lo ataja (sólo el caso e pasa a Nicolás).
- Matiz de acotación: el negativo por periodo ya sacó 759 y 210 pasadas de «otra» (V2 de la v1), así que lo que queda es poco.

### V-N5 · I5 es más débil que la G3 que dice reemplazar · GRAVEDAD 2 · CONFIRMADO
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:216-233` (compara sólo `pub` y `disp`); `PREREGISTRO.md:215-220` («la G3 de la adenda»);
  `experiments/_s151_ab_diurno/PREREGISTRO.md:174` y `:296-305` (G3 = nulo 2 sin diferencias, record entero salvo campos volátiles).
- QUÉ PASA: un record nocturno que cambie de posición, de cúmulo, de distancia, de `final_hotspot_*` o de cualquier campo
  `diag_*` sin cambiar la publicación ni la magnitud publicada pasa I5. La G3 original lo marcaba. Para el criterio (publica
  y magnitud) puede bastar; para «la rama diurna no toca la noche» (A116/A118) es una protección menor que la sellada.
- CÓMO REPRODUCIRLO: leer ambos pasajes; un test con dos records nocturnos que difieran sólo en `sha` o en un campo no
  copiado pasa I5 porque `cargar_brazo` ni siquiera conserva esos campos (`:460-465`).

### V-N6 · I3 («días vacíos») queda anulada por un solo record diurno del brazo ese día · GRAVEDAD 2 · CONFIRMADO
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:123-127` y `:149-155` (`con_rec` cuenta records de cualquier hora);
  `evaluar_diurno_k.py:384-389`.
- QUÉ PASA: `Escena` con una pasada nocturna con alerta protegida y sin record en ningún brazo
  (`verificador_v2/esc2.py`): sin record diurno del brazo ese día, I3 da INVÁLIDO («días vacíos 1»); con un record diurno
  del brazo el mismo día, I3 da verde y el global NO ADOPTAR. O sea que un hueco nocturno común a los dos brazos (corte de
  NASA) deja de detectarse justo en los días en que el brazo diurno tiene algo.
- CÓMO SE VERÍA: no cambia el veredicto diurno (la noche de los dos brazos es igual por construcción); sí vuelve falsa la
  frase «I3, cobertura nocturna contra la referencia» en esos días. Hoy el único amparo es I5 (records en un solo brazo).

### V-N7 · V750 se mide con valores de la Tabla 1 donde el MISSION manda el código de MIROVA · GRAVEDAD 2 · CONFIRMADO (la divergencia); su efecto es SOSPECHA
- ARCHIVO:LÍNEA: `docs/MISSION.md:142-145` (TEXTO: «Para VIIRS 750, cuando el paper y el código difieren, manda el código»);
  `PREREGISTRO.md:87-100` y `:428`; código de MIROVA `MIROVA_VIIRS750_hotspot_detection.m:87-89` (filtro de reflejo, aplica a
  todas las escenas) y `:189` (K1 diurno -0,5).
- QUÉ PASA: el brazo usa K1 = -0,6 (Tabla 1) y no tiene filtro de reflejo; MIROVA usa -0,5 y descarta la escena con
  reflejo < 12°. El pre-registro lo declara y lo deja fuera (§9). Pero el veredicto de VIIRS 750 que sale del A/B es el de
  una configuración que el MISSION dice que no es la de MIROVA para ese sensor, y un ADOPTAR global llevaría esos valores
  al ciclo de adopción. Dirección esperable: K1 -0,6 es más permisivo que -0,5, o sea sesgo hacia más publicaciones (SOSPECHA,
  no medido).
- CÓMO REPRODUCIRLO: leer los tres pasajes.

### V-N8 · La variante de reflejo de 12° probablemente no puede cambiar nada · GRAVEDAD 1 · CONFIRMADO en la muestra; generalización SOSPECHA
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:280-288`; `humo_c0_W6b_salida.txt` («apaga 0 publicaciones diurnas del brazo; 0 publicaciones
  diurnas sin ángulos»); CLAUDE.md del proyecto (TEXTO, marca S158): «en 17.859 pasadas diurnas del OSF ninguna tiene glint
  bajo 10°».
- QUÉ PASA: sobre ~250 publicaciones diurnas reales de C0 el filtro apaga cero, y la marca S158 dice que ninguna pasada
  diurna está bajo 10°. Las pasadas de la referencia están todas a 17 a 20 UTC con elevación solar 23 a 61° (medido,
  `medidas1_salida.txt`). La variante informativa entonces repetirá el veredicto principal, y §2.2 («el primer candidato a
  probar es el filtro de 12°») apunta a un candidato que casi seguro no explica nada. No es un defecto de la regla.

### V-N9 · Pequeños · GRAVEDAD 1 · CONFIRMADO
- `PREREGISTRO.md:337-339` dice que la salida «dice si alguna» variante de mínimas «cambia el veredicto»; el evaluador sólo
  imprime el diccionario (`evaluar_diurno_k.py:579-589`), sin compararlo con el principal.
- Costo del §8: la aritmética sale (11 × 83 × 7,7 min = 117,2 h; /3 = 39,1 h; /6 = 19,5 h), pero los 2,2 y 5,5 min por
  volcán-día no se derivan de las cifras del propio §8 (15 a 24 y 40 a 58 min por media ventana, sin los días de cada mitad).
  Con medias ventanas de 8,3 días de promedio, los extremos darían 1,8 a 2,9 y 4,8 a 7,0. La evidencia de C0 vive en
  `loop/activo`, no en `main`: SIN DATO.
- §5.1 (ii): 10 de 200 (5,0 %) con e-i en V750 está «justo en el límite», pero con 200 repeticiones el intervalo es
  aproximadamente 2,4 a 9 %: no certifica «no más de 5 %». e-i ya no es la recomendada; sin consecuencia.

## Veredictos de las afirmaciones centrales (lo pedido en el punto 4)

| afirmación | veredicto | evidencia |
|---|---|---|
| Cifras del §3 (por ventana y totales) contra `sustrato_k_salida.txt` | CONFIRMADO | sumé a mano W2 a W6: V375 protegidas 26, mb 10, negativos 2.246, diurnas 2.547; V750 6, 0, 2.433, 2.499; tabla sola 6/7/2.271 y 2/0/2.439; «otra» 265 y 60 (el nulo reimprime 2.246/265/10/26 y 2.433/60/6) |
| Tabla 1 de Coppola 2016a (K1 -0,6, C1 0,02, C2 15 de día; noche -0,8, 0,003/0,01, 5/10) | CONFIRMADO | RENDER de PDF p. 7 (índice 6) a 130 dpi: columna «Daytime» ROI1 = ROI2 = (-0,6; 0,02; 15). Ojo: el texto de Test 2 y 3 de esa página lleva «or» (la conectiva `min`); no afecta este A/B |
| Dos diferencias del código MIROVA V750 (§2.2) | CONFIRMADO | `.m` l. 87 (`sunglint < 12`, l. 83-89 el bloque), l. 189 (K1 -0,5 día), l. 191-192 (σ 15), l. 194-198 (0,02); README l. 32-36 = fórmula del evaluador (`:265-274`) |
| I1 a I6 (cada compuerta implementa lo escrito) | CONFIRMADO (leídas) con V-N5 y V-N6 como debilidades; I6 con V-N3 | `evaluar_diurno_k.py:159-233, 341-351` |
| Casos a a e de §6.2 | CONFIRMADO | `:75-91`; escenarios E1 a E5 de `esc1.py` |
| §6.3 veredicto global | CONFIRMADO | `:106-124`, prioridad INVÁLIDO > INDECIDIBLE > R1 > DECIDE_M4 > mezcla |
| §6.4 robustez | CONFIRMADO EN PARTE | el cálculo de `veredicto_final` (`:127-133`) y el cableado leen bien, pero sin ninguna prueba (V-N2) |
| Lectura de R1 en §6.1 (inalcanzable con compuertas verdes) | CONFIRMADO | `:354-356` + control sintético `:250-256`; mutación M10/M38 |
| Prueba D y su necesidad | CONFIRMADO | 1-0,995^26 = 0,122; región de e-i (D cumple hasta 55 negativos publicados en V375 con 4 de 36, hasta 20 en V750 con 1 de 6, falla en 22); simulé el caso b con brazo aleatorio de q = 0,01 % a 0,5 %: ADOPTAR máximo 0,42 % (V375) y 0,09 % (V750) (`medidas5_salida.txt`) |
| Lo que dice §5.1 contra la salida del nulo | CONFIRMADO | corrí `congelar_referencia.py --commit 047bd5692` (los 4 sha256 OK) y `nulo_estructural.py`: salida idéntica a `nulo_estructural_salida.txt` salvo el banner de stderr (`diff` en la sesión) |
| Cuentas de costo del §8 | CONFIRMADO EN PARTE | aritmética sí; insumos SIN DATO (V-N9) |
| I4c: «falla desde 7 y desde 22» | CONFIRMADO | `scipy`: p_sup 0,0011 y 0,0059; umbral 7 y 22 con N = 2.547 y 2.499 |
| Batería 65 pruebas, perfiles 3 pruebas | CONFIRMADO | 65 passed en 8,7 s; 3 passed |
| Mutaciones «48 de 48» | CONFIRMADO, con alcance limitado | re-corrí en copia temporal (`git archive`): 25 de 25 + 23 de 23 atrapadas por aserción, control C-CAIDA como CAÍDA; pero ver V-N2 |
| sha256 de `objetivos_sha256.txt` | CONFIRMADO | 16 de 16 coinciden con `git show 81e6588dd…:<ruta> \| sha256sum`; pero ver V-N1 |

## Revisión de los arreglos del §12 (V1 a V13 de la primera verificación)

| ID | veredicto | ¿camino nuevo? |
|---|---|---|
| V1 e-i da ADOPTAR con PIERDE → e-ii recomendada | CONFIRMADO: sólo e-ii devuelve DECIDE en el caso e (`:87-91`); la región numérica de e-i se reproduce | Sí: el caso b no mira «otra» (V-N4) |
| V2 negativo por periodo | CONFIRMADO: `banderas_por_periodo` `:236-247`; 759 pasadas V375 y 210 V750 pasan de «otra» a negativo (= 1.024 a 265 y 270 a 60); M43/M49 | Los «nuevos» negativos caen en volcanes activos (Isluga 151, Láscar 108, PCC 99, Lastarria 84, Tupungatito 83): son errores si el brazo publica calor persistente real. Dirección conservadora (hacia NO ADOPTAR), consistente con el criterio («MIROVA miró y no vio nada»). Sin problema de día UTC partido: todas las diurnas caen entre 17 y 20 UTC y las nocturnas entre 04 y 07 UTC |
| V3 variantes de mínimas, M4 por ventana, elevación, 1.13 | CONFIRMADO EN PARTE: están (`:579-596`, `:328-337`, `desproporcion`), pero sin la comparación contra el principal | V-N9 |
| V4 geometría de reflejo existe en los records | CONFIRMADO: `process_viirs.py:475-479`, `process_viirs_mod.py:338-342`; fórmula igual a README | variante inerte (V-N8) |
| V5 excluir después de marcar | CONFIRMADO: `:381-383`, M44 | No |
| V6 I5 exige los mismos records | CONFIRMADO: `:228-232`, M46 | I5 sigue más débil que G3 (V-N5) |
| V7 días parciales | CONFIRMADO EN PARTE: declarado en §3; no re-medí los conteos de días parciales (SIN DATO); la tabla termina el 2026-10-19 (medido) | No |
| V8 recuperar es publicar con cualquier magnitud | CONFIRMADO: `:303` y `P_1mw` en `:327` | No |
| V9 límite de I6 e I2 | CONFIRMADO (declarado en §5) | I6 (c) además mal calibrada (V-N3) |
| V10 I4a toda alerta | CONFIRMADO: `:198-203`, M22/M45; tolerancias 7 y 22 reproducidas | No |
| V11 D con independencia falsa | CONFIRMADO: 36 alertas V375 en 30 volcán-días (medido); Láscar 7 + Lastarria 6 = 13 de 26 protegidas | No |
| V12 líneas y conteos | CONFIRMADO: `.m` l. 189, 191-192, 194-198, 83-89, 87; 13 positivos de W2 = 12 + 1 | No |
| V13 defaults de C0 y sha de blobs | CONFIRMADO: workflow l. 62 y 66 son C0; sha de blobs OK | No |

## VERIFICADO LIMPIO (qué miré y está sano, contra qué vara)

- **Frontera día/noche (mi camino C1)**: contra los datos de la referencia, todas las pasadas diurnas de W2 a W6 están a
  elevación solar ≥ 5° (3 entre 5 y 10°, ninguna ≤ 5°) y a 17 a 20 UTC; las alertas diurnas, a 23 a 61°; las nocturnas a
  04 a 07 UTC. Que MIROVA corte día y noche con otro ángulo no cambia ninguna clase (`medidas1_salida.txt`).
- **Periodo por día UTC (C2a, C2b)**: con esas horas ninguna noche ni ningún día cruza 00 UTC.
- **Brazo aleatorio o callado no adopta**: nulo reproducido idéntico; más allá de su grilla (q desde 0,5 %), la probabilidad
  máxima de ADOPTAR caso b con q entre 0,01 % y 0,5 % es 0,42 % (V375) y 0,09 % (V750) (`medidas5.py`, 200.000 repeticiones).
- **Aritmética**: 1-0,995^26 = 12,2 %; P(Bin(40; 0,05) ≥ 5) = 0,048 (la cuenta es correcta; lo que falla es qué mide, V-N3);
  p_sup y umbrales de I4c; costos 117,2 h / 39,1 h / 19,5 h.
- **Control sintético «observado, no publica»** (C6): solo se asigna si el brazo tiene record y después de I2
  (`:250-256`, `:394-395`); mutación M26; no inventa errores del control (el control nunca es error en un negativo y sólo
  «falla» en alertas bajo 1 MW, que es lo que el criterio pide).
- **Cobertura por pasada (C3)**: los records existen para pasadas sin detección (producción nocturna: 59 de 1.606 publican,
  0 de 2.715 pasadas sin record en V375; en V750 9 de 2.650, todas RUTINA, `medidas2_salida.txt`), así que «observado» no es
  igual a «publicado».
- **Alertas sin record (C14)**: en V375 ninguna de las 459 alertas nocturnas carece de record de producción; en V750 0 de
  96. Las alertas sólo OCR (23 de 36 en V375, 4 de 6 en V750) tienen instante que cae sobre un gránulo en la noche, así
  que I4a no debería disparar por eso.
- **Reflejo probable (1.13)**: 17 pasadas (13 V375, 4 V750), todas dentro de W2 a W6 y todas sólo OCR; cada fila del
  estudio encuentra su pasada (0 sin pasada) (`medidas3_salida.txt`).
- **Sello**: 16 de 16 sha256 de blobs reproducidos; referencia congelada con los 4 sha256 OK.
- **Perfiles y workflow** (parcial): control = producción salvo nombre y directorio; el diurno añade sólo
  `enable_daytime_viirs: true` (diff de los dos YAML); workflow con `"on":` entre comillas (l. 40), sólo `EARTHDATA_TOKEN`
  con falla si viene vacío (l. 102-106), candado `preregistro_aprobado` (l. 79), concurrencia propia (l. 70-71), `max-parallel: 3`
  (l. 87), timeout de paso 300 (l. 149), FLAGS_BRAZO con `ENABLE_DAYTIME_VIIRS` (l. 157), sin `--no-night-filter`.

## SIN DATO

- Cómo se comporta K de día sobre datos reales: no hay records de los brazos. La prueba de humo es de C0 y sale INVÁLIDO.
- Si MIROVA define `dayflag` por elevación > 0 (no se puede leer del código; los datos lo vuelven irrelevante, ver arriba).
- Que los 2,2 y 5,5 min por volcán-día del §8 salgan de la corrida sobre C0 (la evidencia está en `loop/activo`).
- Los conteos de días parciales de V7 y los de «sin noche» de W6 (no los re-medí).
- Si el instante de las alertas sólo OCR de día coincide con un gránulo que el brazo procese (el análogo nocturno da 0 de 459).
- Que `process_viirs*.py` escriba `diag_umbrales_diurnos` en todos los caminos de salida del record (leí el camino principal).

## QUÉ NO MIRÉ

- `pipeline/store.py` (rechazo diurno), `fetch.py`, `run_pipeline.py`, `process_viirs*.py` más allá de las líneas citadas,
  `scan_geometry.py`; ni que la rama diurna aplique de verdad la Tabla 1 (eso es de otra revisión).
- `scripts/unir_ventana.py`, `contar_pasadas_noche.py`, el cableado del job `merge` y `cobertura.txt` del workflow
  (sólo leí encabezado, defaults y los puntos listados).
- La validez del estudio 1.13 y de la regla SN (D-9); la calidad del OCR de Mirova-v1 (A119) más allá de lo que usan las variantes.
- El resto de `docs/MISSION.md` y la ADENDA_K entera (leí los pasajes citados).
- No corrí `evaluar_diurno_k.py main()` de punta a punta sobre datos propios (no armé raíces sintéticas), ni la prueba de
  humo; la leí.
- Mis escenarios sintéticos usan la `Escena` de la batería, así que heredan sus convenciones (una pasada diurna a las 17:00
  UTC en Láscar, etc.).
- Re-corrí las 49 mutaciones en una copia temporal (`git archive` de `bf8e24dd`), no sobre el worktree.
