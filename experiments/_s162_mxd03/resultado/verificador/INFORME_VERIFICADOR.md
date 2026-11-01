# Verificador con contexto limpio: resultado del A/B de MxD03 sobre K (S162, MOD-B, tarea 1.30, D-48)

## 1. Encabezado

- **Fecha y hora del servidor** (GitHub, header `Date`, A86): sábado 24 de octubre de 2026, 20:31:18 GMT al empezar;
  caminos.md sellado a las 20:33:02 GMT (sha256 `ad03b0a0796955393c1d21182f1b9a9dd23946e3667561933234d4d538937ff2`).
- **Commit sobre el que medí**: worktree `D:\vrp-trabajo\s162-mxd03`, rama `s162-mxd03-codigo`, HEAD `1aaaf709c`.
  Tag `s162-mxd03-tag` resuelve al commit `ffbb36248` (`git rev-parse s162-mxd03-tag^{commit}`). `git diff ffbb36248 HEAD`
  sobre `pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` está vacío, y también contra `80b819828`
  (el `main` congelado, `merge-base HEAD origin/main`). `origin/main` al medir: `9c2ca6f95`. Los scripts del evaluador y
  la vara son byte a byte los del tag (`git diff --stat ffbb36248 HEAD -- experiments/_s162_mxd03/{evaluar_mxd03.py,
  vara_mxd03.py,poblacion.json,poblacion_mxd03.py,vara_viirs_mxd03.json,probe_mxd03_ab.py}` vacío; `poblacion.json`
  con sha256 LF `8c5b8113…` igual en HEAD y en el tag).
- **Modelo y esfuerzo**: Claude Fable 5.1 (`claude-fable-5-1`); el encargo no declaró esfuerzo, corrí con el del agente.
- **CARPETA**: `D:\vrp-trabajo\s162-mxd03\experiments\_s162_mxd03\resultado\verificador\`. Copia de los artefactos en
  `copias\tandas\` (sha256 de los 48 jsonl en `copias\sha256_tandas_jsonl.txt`; los archivos de resultado del autor que
  venían en esa carpeta están apartados en `copias\tandas_autor_resultado\`, sha256 en `copias\sha256_resultado_autor.txt`).
- **Qué NO miré** (para que mi silencio no se lea como «todo bien»): no corrí el arnés sobre ningún HDF (sin pyhdf en
  Windows); no abrí los CSV congelados más allá de su sha256; tomé `vara_viirs_mxd03.json` como dado (su `meta` cita el
  `main` congelado y la referencia del MANIFIESTO, pero no reconstruí la tabla desde `data/`); no verifiqué la salida del
  predicado de node más allá del sha256 de `frontend/index.html`; no leí los logs de los jobs en GitHub, sólo la metadata
  de los tres runs (3 llamadas a la API de 10 permitidas); no revisé `k_en_sha.py` (no se ejecutó en ningún run).
  INFORME.md del autor lo leí **después** de sellar caminos.md y de correr mi censo.

## 2. En una pantalla

1. **R1 CONFIRMADO. R3 CONFIRMADO. R4 CONFIRMADO. R2 CONFIRMADO EN PARTE** (12 de los 13 «controles» pueden fallar y
   están en verde con recuento propio; «vara cruda» no es un control, es una anotación que siempre da OK).
2. El **CUMPLE SIN DAÑO se sostiene** con código independiente del evaluador: 5.465 de 5.465 pasadas, 0 errores, 0
   duplicados, K igual a `data/` y K2 igual a K en las 5.465; P1 0 perdidas (48 de 48 protegidas en K y en X); P2 ≤ 35°
   ΔX = −1 con ΔR entre −4 y +2 (ruido 4, EMPATE para cualquier ruido ≥ 1); vara MXD03 MAS CERCA por cinco caminos
   distintos del del autor; la tabla del §10 recompuesta a mano da el mismo veredicto. La re-corrida de los scripts del
   autor sobre mi copia reproduce `resultado_mxd03.json` y `vara_resultado.json` byte a byte.
3. **Ningún hallazgo mueve el veredicto.** Los que hay son de instrumento o de lectura: el módulo del nulo llega a
   103.470 km en 2 gránulos con relleno de MxD03 y el control lo da por bueno (VRB-01); la vara VIIRS da lo mismo con la
   referencia de **otra** noche (placebo), así que mide «más cerca del cráter de Láscar», no «del calor de esa noche»
   (VRB-02); «M NEUTRO, mediana 0,000» esconde que 17 de 79 alertas cambian la magnitud más de 10 % y 6 más de 30 %
   (VRB-03).
4. **Lo que condiciona (R4) es más fuerte de lo que dice el resumen**: las 48 protegidas con cúmulo se mueven TODAS hacia
   el cráter (mediana 1,46 km, máximo 2,49 km); el signo de P2 sin Cordón Caulle (+1) es una sola alerta bajo 1 MW de
   Láscar que X apaga por el fondo, no por la posición.
5. Instrumentos propios y salidas en CARPETA: `censo_verificador.py`, `anomalias_desplazamiento.py`, `vara_alternativas.py`,
   `detalles_extra.py`, `rerun_autor.sh`, `poblacion_regenerada_salida.txt`, `probar_evaluar_rerun_salida.txt`.

## 3. Veredicto por afirmación

### R1. Censo completo y sellado. **CONFIRMADO** (gravedad si fallara: 5; no falla)

Medido con `censo_verificador.py` (`censo_verificador_salida.txt`), código propio sin importar el evaluador:
- 24 archivos `ab_parte00..23.jsonl` con 24 cabeceras, **5.465 records**, 24 pies; `cabecera.parte` igual al nombre del
  archivo en las 24; pies con `errores` 0 en las 24 (minutos 24,2 a 52,2); los 24 `probe_N.log` terminan en «0 records
  con error»; ningún «CMR/descarga fallo» en los logs.
- **Clave por clave** (camino 1 de caminos.md): 5.465 pares (volcán, hora UTC) únicos en los artefactos, 0 repetidos,
  0 de la población sin artefacto, 0 artefactos fuera de la población; cada record está en la parte que
  `poblacion.partes` le asigna (0 fuera de lugar) y con la clave de gránulo de la población (0 distintas).
- **Commit** (caminos 3, 9, 34, 35): las 24 cabeceras declaran `commit ffbb36248` (= tag), `poblacion_checkout
  80b819828`, los sha256 LF de la referencia del MANIFIESTO (`8ec5d918…`, `fd7a7098…`), sal `s159-mxd03-r`, 20 nulos,
  flags `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False` y `ENABLE_MODIS_B22_PRIMARY = True`, sha256 de
  `frontend/index.html` `260b4a19…` (igual al local). Los 24 `procedencia_N.txt` dicen lo mismo (8 por rama t1, t2, t3).
  GitHub: runs 40112510038 (t1), 40122029477 (t2), 40126381034 (t3), los tres `completed / success`, `head_sha
  ffbb36248`, entre 16:38 y 20:28 UTC del 2026-10-24.
- **Población = sellada** (camino 2): `poblacion.json` LF idéntico al del tag; regenerada desde la referencia congelada
  con `poblacion_mxd03.py --sin-bajar --salida` (`poblacion_regenerada_salida.txt`): 5.465 records, mismas claves,
  **0 campos distintos** en todos los campos de cada record, mismas 24 partes. Los sha256 de los dos CSV de
  `D:\vrp-trabajo\temporales\s162_mxd03\ref\` coinciden con el MANIFIESTO.
- **K2 = K** (caminos 6, 7): `k2_igual` True en 5.465 (compara el record entero salvo marcas de hora,
  `probe_etiquetas.py:150-156`); además comparé a mano el resumen (pc_vrp, pc_lat, dc, n_anom, vrp_mw): 0 distintos, y
  `pub K != pub K2`: 0.
- **K = data/** (camino 5): recalculado por mi cuenta contra `pub_guardada`, `pc_vrp_guardada` (a 0,001 MW) y
  `dc_guardada` de la población: **0 de 5.465** difieren; `retenido_para_sha` 0, los 24 `recorridos_parteNN.jsonl` vacíos
  (sha256 de la cadena vacía) y los 24 `recorrer_N.log` dicen «0 records re-corridos». Los records vienen de 12
  `codigo_sha` (3695f6758: 4.614; 34cea39e4: 652; 57d18ad78: 144; e0c90caa7: 38; 8 más con 1 a 3), todos reproducidos.
- **Todos los brazos presentes**: K, K2, X en los 5.465; R00 a R19 en los 2.046 con `r_nulos` (= los 2.046 con cenit
  ≤ 35°, 0 inconsistencias); ningún brazo faltante; `None` sólo en brazos R (1 a 3 por R, ver VRB-01 y SEGUIMIENTOS).
- **Re-corrida de los scripts del autor** sobre mi copia (`rerun_autor_salida.txt`): `vara_mxd03.py --evaluar` y
  `evaluar_mxd03.py --art --vara --ref` dan `resultado_mxd03.json` sha256 `7d1e4c13…` y `vara_resultado.json`
  `521d55ee…`, **idénticos** a los del autor (`copias\sha256_resultado_autor.txt`).

Las dos preguntas: (1) un record faltante, repetido, en otra parte, de otro commit o con K ≠ data/ lo habría visto el
cruce clave por clave y los recuentos; (2) si los jsonl estuvieran vacíos o rotos el recuento daría 0 o reventaría al
parsear, no 5.465.

### R2. Los 13 controles en verde. **CONFIRMADO EN PARTE** (gravedad propia 1)

Cada control, qué input lo pondría en rojo, y mi medición propia:

| control | puede fallar? | mi medición (censo propio) |
|---|---|---|
| cobertura | sí (`faltan` o estado ≠ ok) | 5.465 ok, 0 faltan; `None` sólo en R |
| k2 | sí | 5.465 iguales |
| arnés (control 4) | sí (`no_reproduce`, `resto_frac` < 0,98, sha bajo umbral) | 0 difieren; la rama de re-corrida no se ejercitó (VRB-05) |
| r_modulo | sí (20 nulos, módulo a 10 m, rumbos cada 18°) | 0 malos, **pero acepta un módulo de 25.742 km** (VRB-01) |
| referencia | sí (sha256) | iguales al MANIFIESTO |
| reetiquetado | sí (regenera y compara lab, z, partida, vrp_mirova) | regenerada por mí: 0 campos distintos en TODOS los campos |
| duplicados | sí | 0 repetidas |
| predicado | sí (sha256 de index.html local ≠ jobs) | iguales (`260b4a19…`) |
| procedencia | sí (más de un commit) | 1 commit, = tag. No comprueba que ese commit sea el del tag ni que `pipeline/` sea el `main` congelado: eso lo hace el paso del workflow (`probe-s162-mxd03.yml:67-78`) y lo verifiqué con `git diff` |
| unión | sí | 0 distintas, 0 sin población; mi cruce de lab/z/r_nulos/sensor/tramo/lado/inner: 0 |
| geometría | sí (2,581 ± 0,05; nulo > 1e-6) | `obs_hacia_sensor_km` 2,581 exacto en `MYD021KM.A2026073.0705`; nulo máximo 0,0 |
| cableado | sí (hash X = K con corrimiento > 10 m; hashes de R repetidos) | hash X ≠ K en 5.465 de 5.465; 0 repetidos |
| **vara cruda** | **no** (`evaluar_mxd03.py:471` escribe `"estado": "OK"` sin condición) | anotación, no control (VRB-04) |

Control positivo del conjunto: 17 pasadas cambian de publicación entre K y X, 158 cúmulos se mueven, 97 records tienen
alguna Rk publicada con el cúmulo a más de 0,5 km de K (control 2 del §8 vivo). El instrumento ve cambios.

### R3. CUMPLE SIN DAÑO según el §10. **CONFIRMADO** (gravedad si fallara: 5; no falla)

Recompuesto pieza por pieza con código propio (`censo_verificador_salida.txt`, `vara_alternativas_salida.txt`):
- **Umbrales leídos del código, iguales al sello** (camino 19, 21, 23): protegida = alerta pareada a ±120 s con VRP de
  MIROVA ≥ 1,0 (`poblacion_mxd03.py:171-174`, `TOL_S = 120` l. 56; `vrp_mirova` mínimo en protegidas 1,0, máximo en bajo1
  0,99); pareo `banco_paridad.parear` a 120 s (`evaluar_mxd03.py:44, 65-68`); corte 35° (`CENIT_P2 = 35.0`, l. 45);
  ruido = segundo mayor |ΔR| de 20 (`ruido_p2`, l. 121-123); dirección ΔX = S(X) − S(K) (l. 155-157); SN sólo VIIRS375
  (`clase_mirova.py:108`).
- **P1**: 50 protegidas; K publica 48, X publica 48; «K sí y X no» = ∅; «K no y X sí» = ∅. Las 2 que K no publica son
  Chillán 2026-10-12 07:20 y 2026-10-15 01:05 (cenit 58°, `n_anom` 0 en K y en X, MIROVA 2,18 y 1,72 MW), lo que el §1
  ya declaraba fuera (M H4). **P1b** = ∅ (ninguna K ≥ 1 MW baja de 1 MW en X). Las 4 «expuestas» del §5 publican en K y X
  y su cúmulo pasa de 2,2 a 3,2 km a 0,3 a 0,9 km del cráter.
- **P2 ≤ 35°**: n 1.861 (2.046 menos protegidas, sin_info, far_ref y 106 negativos partidos con hermana sin_info; 0 de
  esos 106 cambian). S(K) 34, S(X) 33, **ΔX = −1**; ΔR = [−2, −2, −2, −3, −4, −3, −1, 0, 0, −2, −4, −1, 0, 2, 1, 0, 1, 0,
  −2, −2]; **ruido 4** (dos −4); 10 de 20 ΔR por debajo de ΔX; **EMPATE**, y sería EMPATE para cualquier ruido ≥ 1. Las
  7 pasadas que cambian: 6 negativos limpios de Cordón Caulle (4 que X apaga, 2 que X prende) y 1 bajo 1 MW de Láscar
  (2026-04-02 07:45) que X apaga **por el fondo**: el cúmulo pasa de 2,01 a 0,25 km del cráter pero su VRP cae de 0,011 a
  0,000 MW (X_fondo no publica, X_det sí).
- **Vara** (`vara_alternativas_salida.txt`): el camino del autor (pico 3×3, estricta, pos, ≤ 35°) da MXD03 MAS CERCA con
  n 65 (61 Láscar, 4 Chillán), 57 noches, dd mediana 0,733 km, IC 0,487 a 1,097, 51 de 65, nulo de pares máximo 0,295,
  Aqua y Terra del mismo signo. Por **otros caminos**: centro del píxel 0,579 (50 de 65); centroide del cúmulo
  publicado 1,082 (65 de 65); nivel amplio 0,858 (n 71); sólo Láscar 0,680. Todos MXD03 MAS CERCA. Sólo Chillán: SIN
  VARA (n 4). Sobre 35°: INDECIDIBLE (n 18, dd −0,86, IC cruza 0), coincide con la descriptiva del autor. El estadístico
  no está construido a favor de MxD03: la selección del píxel es la unión simétrica de los que caen a menos de 5 km del
  cráter con cualquiera de las dos grillas (`probe_sola.py:176-215`), los pesos y el índice son los mismos en todos los
  brazos, y los 20 pares de nulos tienen mediana 0 por construcción y se midieron (máximo 0,295 km). Lo que sí encontré
  es el placebo de VRB-02.
- **M**: 79 pares, 38 con X más cerca de MIROVA y 39 más lejos, 2 iguales; X/K mediana 1,000; `regla_m` NEUTRO. En
  agregado es neutro de verdad; por pasada no (VRB-03). Sólo informa.
- **P2 sobre 35°**: ΔX = −4 (S(K) 15, S(X) 11, n 3.185): 5 negativos que X apaga (Cordón Caulle 03-08, 06-19, 06-30;
  Chaitén 03-13; Chillán 06-01, cenit 47 a 65°), 2 que prende (Chaitén 04-21, Láscar 04-01) y 1 bajo 1 MW de Láscar que X
  recupera (05-06 08:00, cenit 47°). No es positivo, así que no manda a Nicolás.
- **Tabla del §10 recompuesta**: controles sin INDECIDIBLE ni INCOMPLETO; P1 SIN PÉRDIDA; P2 EMPATE (no PIERDE, no
  INDECIDIBLE: R vivo); vara no DETIENE; P1b vacío; saldo sobre 35° no positivo; vara con control de sesgo (dos
  satélites con n ≥ 5). Fila 1 de la tabla: **CUMPLE SIN DAÑO**. El código (`evaluar_mxd03.py:374-392`) sigue ese orden.

Las dos preguntas: (1) si X dañara, una protegida con pub K 1 y X 0, o un ΔX > 4, lo habría visto mi recuento, que no
pasa por el evaluador; (2) si X no se hubiera aplicado, el hash de X sería el de K (es distinto en 5.465) y los 17
cambios y 158 movimientos no existirían.

### R4. Lo que condiciona y no cambia el veredicto. **CONFIRMADO** (gravedad propia 2, por lo que agrega)

- **158 cúmulos movidos** más de 0,01 km = **todos** los 158 records que tienen cúmulo primario en K y en X (0 quedan
  quietos: la posición entra a la selección y al centroide); mediana 1,55 km, máximo 8,84 km. Además 10 records tienen
  cúmulo sólo en K y 6 sólo en X. 19 cambios de `distance_class` (17 negativos limpios, 1 sin_info, 1 bajo 1 MW; 0
  protegidas).
- **48 protegidas** = todas las que tienen cúmulo (las 48 que K publica). **Las 48 quedan MÁS CERCA del cráter en X**
  (`pc_dist` X < K en 48 de 48), mediana del movimiento 1,46 km, máximo 2,49 km; ninguna cambia de clase. Es un
  resultado espacial fuerte y en la misma dirección que la vara (VRB-02) y que M H3 del frente anterior. La auditoría
  A61 que el §6 exige tiene su insumo en estos mismos jsonl (`pc_lat`, `pc_lon`, `pc_dist` por brazo).
- **Signo distinto sin Cordón Caulle**: ΔX = +1 (ruido 2, EMPATE) contra −1. El +1 es la sola bajo 1 MW de Láscar
  2026-04-02 07:45 descrita en R3 (pérdida por fondo, no por posición). El §6 pide decirlo en la primera línea: el
  evaluador lo imprime («ATENCION (§6)») y el INFORME.md del autor lo pone en el punto 5 de su pantalla.

## 4. Hallazgos propios (ordenados por gravedad)

### VRB-01. El módulo del nulo llega a 103.470 km en gránulos con relleno de MxD03 y el control de módulo lo da por bueno
- **ARCHIVO:LÍNEA**: `experiments/_s151_mxd03_etiquetas/probe_etiquetas.py:141-147` (`desplazamiento_crater`);
  `experiments/_s162_mxd03/probe_mxd03_ab.py:189, 197-205` (usa `desp["km"]` como módulo de los 20 R);
  `experiments/_s162_mxd03/evaluar_mxd03.py:324-334` (`control_r_modulo` sólo exige aplicado = pedido a 10 m, sin tope
  físico). SCRIPT: `anomalias_desplazamiento.py` → `anomalias_desplazamiento_salida.txt` §1 y §3.
- **QUÉ PASA**: cuando el MxD03 trae un bloque de píxeles sin geolocalización (relleno −999, que el lector pasa a NaN),
  la grilla de 5 km del L1B también lo trae, y `_interp_geo` (`pipeline/process_modis.py:385-392`, `zoom` de orden 1
  sin enmascarar) reparte el −999 a los vecinos: el píxel más cercano al cráter según MxD03 queda con una posición
  interpolada absurda, y la «distancia interp menos MxD03» sale en decenas de miles de km. Dos records:
  PlanchónPeteroa 2026-03-18 08:05 (Aqua, cenit 50°, 54.190 píxeles de relleno, 103.470 km) y Lastarria 2026-04-23 01:50
  (Terra, cenit 17°, 203.100 de relleno, 25.742 km). El de Lastarria tiene `r_nulos`: sus 20 R trasladaron la grilla
  25.742 km, los 20 brazos dieron `None` (sin escena) y el control los aceptó porque el módulo aplicado (25.741,9082)
  es igual al pedido (25.741,908). De los 3 records con R `None` (`anomalias_desplazamiento_salida.txt` §3), éste es el
  único con los 20; los otros dos (Chaitén 2026-09-21 01:45, 10 R; Láscar 2026-09-23 01:35, 7 R) tienen módulos de 2,1 y
  2,5 km y sus `None` son el borde de la escena que el §4 ya prevé.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (A/B de sólo lectura; los dos records son negativos limpios que ningún brazo
  publica y ninguno es alerta, así que no entran a P1, a la vara ni al saldo de P2: un neg_limpio con pub 0 suma 0).
- **CÓMO REPRODUCIRLO**: `python -I anomalias_desplazamiento.py copias/tandas ../../poblacion.json` (sección 1);
  gránulos `MYD021KM.A2026077.0805` y `MOD021KM.A2026113.0150`.
- **CONFIANZA**: CONFIRMADO (medido en los artefactos). La causa (fill interpolado por `_interp_geo`) es SOSPECHA:
  encaja con los números, pero no abrí el HDF.
- **GRAVEDAD**: 2. No tuerce ninguna decisión de este A/B (1 de 2.046 nulos muerto, en un record que no decide), pero
  el control 2 del §8 («módulo aplicado igual al pedido») no distingue un módulo físico de uno absurdo, y en otro censo
  un gránulo así podría caer en una alerta. Un tope (p. ej. módulo ≤ 20 km, el doble del máximo real de 16,2 km) lo
  habría marcado.

### VRB-02. La vara VIIRS da MXD03 MAS CERCA también con la referencia de OTRA noche: mide «más cerca del cráter de Láscar»
- **SCRIPT:SALIDA**: `vara_alternativas.py` → `vara_alternativas_salida.txt` §e y §f; `experiments/_s151_mxd03_sola_123/
  evaluar_sola.py:125-224` (`vara`), `construir_vara_viirs.py:66-74` (`resumir_noche`).
- **QUÉ PASA**: el objeto caliente de Láscar está siempre en el cráter, y la referencia VIIRS de cada noche cae a 0,12 km
  del ancla (mediana sobre los 65). Barajando la referencia VIIRS entre alertas del mismo volcán (5 semillas), la vara da
  **lo mismo**: MXD03 MAS CERCA, dd 0,83 a 0,95 km, 51 de 65 en las cinco. Es decir, la vara no distingue «MxD03 pone el
  píxel donde VIIRS vio el calor esa noche» de «MxD03 pone el píxel en el cráter». Para una fuente permanente en el
  cráter las dos cosas coinciden y la lectura es correcta; pero la frase del autor («la posición mejora contra un sensor
  independiente», INFORME.md punto 3) suena a una medición por noche que la vara no puede hacer aquí. A110 ya anotaba
  que «el mismo punto en otras noches» es ciego a las fuentes permanentes: esto es el mismo punto ciego visto desde la
  vara. El estadístico en sí no está sesgado por construcción (selección simétrica, nulos de pares centrados y medidos,
  cinco caminos alternativos de acuerdo).
- **CÓMO SE VE EN EL DASHBOARD**: invisible (la vara sólo detiene).
- **CÓMO REPRODUCIRLO**: `VRP_PROFILE=mirova_equivalent python -I vara_alternativas.py copias/tandas` desde la raíz del
  worktree (sección e).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2. No cambia el veredicto; cambia cuánto se puede decir con la vara al justificar la adopción. La prueba
  de posición que sí tiene contenido por noche aquí es P4 (48 de 48 protegidas más cerca del cráter) y la A61 pendiente.

### VRB-03. «M NEUTRO, mediana de d 0,000, ĝ 1,00» esconde cambios de magnitud de hasta 50 % por pasada
- **SCRIPT:SALIDA**: `anomalias_desplazamiento_salida.txt` §4; `detalles_extra_salida.txt` §M; `evaluar_mxd03.py:221-243`.
- **QUÉ PASA**: X cambia `pc_vrp` en 77 de los 79 pares (la posición mueve el anillo de fondo y la selección de píxeles).
  X/K va de 0,887 (p10) a 1,076 (p90); 17 pares cambian más de 10 % y 6 más de 30 % (Láscar 2026-05-29 07:55: 0,050 a
  0,024 MW con MIROVA 0,24, X/K 0,48, X más lejos de MIROVA; Láscar 2026-03-27 07:10: 0,140 a 0,207 con MIROVA 1,00, X
  más cerca). La mediana de d es exactamente 0 porque hay 38 pares con d < 0, 39 con d > 0 y 2 con d = 0: el elemento 40
  de 79 es uno de los dos ceros. En agregado M es neutro de verdad (38 contra 39, suma de d +0,225); el «0,000» no
  significa «la magnitud no cambia».
- **CÓMO SE VE EN EL DASHBOARD**: si X se adopta, el operador vería en noches sueltas de Láscar una magnitud MODIS hasta
  ±50 % distinta de la de hoy, sin que cambie la alerta. Hoy: invisible.
- **CÓMO REPRODUCIRLO**: `python -I detalles_extra.py copias/tandas ../../poblacion.json` (sección M).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2. M sólo informa (§6, H2) y el veredicto no cambia; pero el aviso a OVDAS y la marca visible de la
  adopción (§10) deberían decir «la magnitud de alertas individuales se mueve hasta ±50 %», no «neutro».

### VRB-04. El control «vara cruda» no puede fallar: son 12 controles y una anotación
- **ARCHIVO:LÍNEA**: `experiments/_s162_mxd03/evaluar_mxd03.py:467-471`: `externos["vara_cruda"] = {"estado": "OK",
  "estado_evaluar_sola": v["estado"]}` siempre que se pase `--vara`.
- **QUÉ PASA**: ningún valor de `vara_resultado.json` lo pone en rojo; su único papel es registrar el estado crudo. El
  efecto de la vara sobre el veredicto entra por `res["vara"]` (DETIENE etc.), no por este control. «13 controles en
  verde» cuenta uno que es verde por construcción (A110).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: leer la línea; o pasar un `vara_resultado.json` con `"estado": "INTERP MAS CERCA"`: el veredicto
  pasa a DETENIDO POR LA VARA y el control sigue en OK.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### VRB-05. La rama de re-corrida en el `codigo_sha` (control 4) no se ejercitó en ningún run real, humo incluido
- **ARCHIVO:LÍNEA**: `experiments/_s162_mxd03/recorrer_en_sha.py:40` (`pend` vacío en las 24 partes); logs
  `recorrer_N.log` de las 24 partes y `humo_40111997157/recorrer_0.log`: «0 records re-corridos en su codigo_sha».
  `RESPUESTA_VERIFICADOR.md`, punto A3: «el humo lo ejercita» no se cumplió (el humo tampoco tuvo nada que re-correr).
- **QUÉ PASA**: K reprodujo `data/` en 5.465 de 5.465 (verificado por mi cuenta: publicación, `pc_vrp` a 0,001 MW y
  `distance_class`), así que no hubo nada que re-correr. Buena noticia para el arnés, pero «control 4 en verde» no
  dice que la re-corrida en un worktree viejo funcione en runner: su única cobertura es la prueba unitaria 8 y el paso
  del workflow que prueba el fetch por sha. La predicción del §8 («5.449 records escritos con un `pipeline/` distinto»
  podían dar deriva) no se materializó: la deriva de código entre esos sha no toca ninguno de estos records.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `for f in copias/tandas/*/*/recorrer_*.log; do tail -1 $f; done`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### VRB-06. El nulo de P2 no está centrado: casi cualquier traslación baja la sobre-publicación de Cordón Caulle igual que X
- **SCRIPT:SALIDA**: `censo_verificador_salida.txt` §P2 («ruido por volcan»).
- **QUÉ PASA**: ΔR tiene mediana −2 y 16 de 20 valores ≤ 0; todo el saldo viene de Cordón Caulle (S(K) 21 de 34; ΔR del
  volcán entre −4 y 0, 0 positivos). El lacolito difuso (A20) está parado en el borde del inner de 20 km: mover la
  grilla 1 a 3 km en cualquier rumbo saca cúmulos del círculo. X (ΔX de Cordón Caulle −2) hace lo mismo que una
  traslación al azar (10 de 20 ΔR por debajo de ΔX). La regla sellada usa |ΔR|, así que el EMPATE es correcto y robusto;
  lo que agrega es que P2 ≤ 35° no tiene poder para decir nada sobre la geolocalización en sí: su saldo es ruido de
  borde de Cordón Caulle, como el §5 predijo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -I censo_verificador.py copias/tandas ../../poblacion.json | grep "ruido por volcan"`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (lectura; el pre-registro ya lo esperaba).

### VRB-07. En el borde del barrido el corrimiento de `_interp_geo` llega a 10 a 16 km, por encima de los «several kilometres» del paper
- **SCRIPT:SALIDA**: `anomalias_desplazamiento_salida.txt` §1; `detalles_extra_salida.txt` §corrimiento.
- **QUÉ PASA**: 15 records con cenit 63 a 75° y frame 0 a 70 (borde del lado del frame 0) tienen el píxel del cráter
  corrido 10,0 a 16,2 km; sobre 50° del frame 0 la mediana es 5,53 km y el p90 8,41 (n 1.107). Ninguno es alerta, ninguno
  publica en ningún brazo. Es la magnitud del defecto de producción que el A/B mide, no un defecto del A/B.
- **CÓMO SE VE EN EL DASHBOARD**: hoy, en producción, un píxel MODIS visto a más de 60° del frame 0 puede estar dibujado
  5 a 16 km fuera de su lugar; con X desaparece.
- **CÓMO REPRODUCIRLO**: sección 1 de `anomalias_desplazamiento.py`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 para este A/B (informa); para producción es el fenómeno que D35 registra.

## 5. SEGUIMIENTOS (fuera de mi eje, reproducibles)

- **S-1 (SOSPECHA, gravedad 2)**: `pipeline/process_modis.py:385-392`, `_interp_geo` interpola con `zoom` de orden 1
  sin enmascarar el relleno (−999) de la grilla de 5 km: los píxeles de 1 km vecinos a un bloque sin geolocalización
  quedan con posiciones absurdas en producción. Inferido de VRB-01 (dos gránulos con 54.190 y 203.100 píxeles de relleno
  en MxD03); no medido sobre el HDF. En K esos píxeles caen lejos de todo y se pierden; en X son NaN y se pierden. El
  efecto en detección es probablemente nulo, pero conviene medirlo antes de la adopción.
- **S-2 (SOSPECHA, gravedad 2, para la adopción)**: donde MxD03 no tiene lat/lon, X pierde el píxel y K no. En esta
  ventana son 36 records en 8 gránulos (27 negativos, 7 sin_info, 1 far_ref y 1 protegida: Láscar 2026-04-23 01:50, que
  publica en K y en X con 0,786 y 0,762 MW). El flag `enable_modis_geo_mxd03` tendrá que declarar qué hace con un píxel
  sin geolocalización (descartarlo, como hace X, es lo honesto) y la FICHA SDA decirlo.
- **S-3 (CONFIRMADO, gravedad 1)**: `RESPUESTA_VERIFICADOR.md` A3 dice que el humo ejercita el control 4; el log del
  humo dice «0 records re-corridos». La afirmación es falsa tal como está escrita (ver VRB-05).
- **S-4 (CONFIRMADO, gravedad 1, lectura)**: la protegida Láscar 2026-03-12 07:25 (cenit 3,6°, 2,19 MW, cúmulo a 2,69 km
  en K y 0,55 km en X, inner 5 km) se apaga en 5 de las 20 traslaciones R de 2,15 km. Una protegida fuerte y lejos del
  borde del inner que se apaga con un corrimiento chico muestra que la publicación depende de la posición también por
  el fondo o las zonas excluidas de Láscar, no sólo por el borde. Insumo para la A61.
- **S-5 (CONFIRMADO, gravedad 1)**: los 15 records de VRB-07 y los 2 de VRB-01 muestran que `desplazamiento_crater`
  mide bien el fenómeno pero no tiene control de plausibilidad; cualquier reutilización del arnés debería declarar un tope.

## 6. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

| qué | comando | vara |
|---|---|---|
| 5.465 records, 24 partes, 0 errores, 0 duplicados, claves = población | `python -I censo_verificador.py copias/tandas ../../poblacion.json` | `poblacion.json` del tag (LF idéntico a `git show ffbb36248:…`) |
| commit único ffbb36248 = tag; `pipeline/` = `main` congelado | `git rev-parse s162-mxd03-tag^{commit}`; `git diff --stat ffbb36248 80b819828 -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` (vacío) | tag y `merge-base HEAD origin/main` |
| runs t1, t2, t3 success con head_sha ffbb36248 | `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/<id>` | GitHub |
| referencia congelada | `sha256sum D:/vrp-trabajo/temporales/s162_mxd03/ref/*` | `MANIFIESTO.json` |
| población regenerada = sellada en todos los campos | `python -I experiments/_s162_mxd03/poblacion_mxd03.py --ref … --sin-bajar --salida copias/poblacion_regenerada.json` + cruce campo a campo | `poblacion.json` del tag |
| K2 = K (record entero y resumen), K = data/ (pub, pc_vrp, dc) | censo propio | `pub_guardada`, `pc_vrp_guardada`, `dc_guardada` de la población |
| X aplicado: hash X ≠ K en 5.465; corrimiento > 0 en 5.465; 158 de 158 cúmulos se mueven | censo propio | control positivo |
| nulos R: 20 por record, módulo a 10 m, rumbos cada 18°, 21 hashes distintos, control 2 vivo (97 records) | censo propio | §8 controles 2 y 8 |
| control de geometría 2,581 km; nulo interp contra interp 0 | censo propio | §8 control 1 |
| P1, P1b, P2 (≤ 35, > 35, sin CC), P4, P5 identidades, P6, M | censo propio | §6 del pre-registro, leído en TEXTO |
| vara por 5 caminos + placebo | `vara_alternativas.py` | `evaluar_sola.vara` (instrumento de 1.23), tabla congelada |
| scripts del autor reproducen byte a byte | `bash rerun_autor.sh` | sha256 de `resultado/` |
| 22 pruebas del evaluador pasan en HEAD | `python -I experiments/_s162_mxd03/probar_evaluar_mxd03.py` (`probar_evaluar_rerun_salida.txt`) | la suite del autor (no la mía) |
| umbrales del código = sello (1 MW, 120 s, 35°, p95 de 20) | lectura `poblacion_mxd03.py:56,171-174`, `evaluar_mxd03.py:44-47,121-130` | §5 y §6 |

## 7. SIN DATO

- Vara sólo Chillán: SIN VARA (n 4, 3 noches); no se puede decir nada de la posición fuera de Láscar con esta vara.
- Vara sobre 35°: INDECIDIBLE (n 18, IC cruza 0), como el autor.
- No medí sobre HDF si `_interp_geo` reparte el relleno (S-1): inferido, no observado.
- No reconstruí `vara_viirs_mxd03.json` desde `data/`: su `meta` cita el `main` congelado y la referencia, y el
  verificador previo la reprodujo byte a byte (`verificador/rerun_vara_construir_salida.txt`, no releído aquí).
- Esfuerzo del modelo: no declarado por el orquestador.

## 8. FUERA DE ALCANCE

Si MxD03 debe adoptarse; D17 (remuestreo UTM), D25, D33; las protegidas de Chillán a 58°; la paridad de posición con
MIROVA (V-TIF no entró); el contenido de las notas del verificador previo (ronda 1 y 2), salvo A3 que cité porque mi
dato lo contradice.

## 9. Archivos de esta carpeta

`caminos.md` (sellado), `INFORME_VERIFICADOR.md` (este), `hallazgos.csv`, `censo_verificador.py` + `_salida.txt`,
`anomalias_desplazamiento.py` + `_salida.txt`, `vara_alternativas.py` + `_salida.txt`, `detalles_extra.py` + `_salida.txt`,
`rerun_autor.sh` + `rerun_autor_salida.txt`, `poblacion_regenerada_salida.txt`, `probar_evaluar_rerun_salida.txt`,
`copias/` (tandas, sha256, población regenerada, resultados del autor apartados).
