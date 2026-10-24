# Verificador con contexto limpio, S162 MODIS: MOD-C (lote de negativos), MOD-E (bow tie) y MOD-D (paquete)

## 1. Encabezado

- **Fecha y hora del servidor** (GitHub, header `Date`): inicio `Sat, 24 Oct 2026 16:05:03 GMT`; cierre del informe
  `Sat, 24 Oct 2026 16:31:33 GMT`.
- **Commit sobre el que medí**: `045d6f8adbb0e678f8e3384cf06ebea17934a46b` (rama `claude/s162-modis-774bb0`). Durante la
  sesión la rama avanzó a `90bd30612` (dos commits, sólo `tasks/LOOP_MODIS.md`); los diez archivos auditados tienen el
  mismo blob en `045d6f8a`, en `HEAD` y en disco (comprobado con `git rev-parse <commit>:<ruta>` y `git hash-object`).
- **Modelo y esfuerzo**: Claude Fable 5.1, esfuerzo medio, autónomo (sin preguntas a Nicolás).
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0\experiments\_s162_modis_verif_cde\`
  - `caminos.md` (sellado antes de abrir nada; sha256 del contenido `a32f4907…3088f49d`, hora `16:07:55 GMT`).
  - `arbol\`: árbol de lectura armado con `git archive` del commit base `0e18e1053` (`pipeline`, `scripts`, `frontend`,
    `volcanoes.yaml`, `experiments/_s158_audit_r2/oraculo`, `experiments/_s159/portes`) más `04_analizar.py`,
    `01_poblacion.py`, `verificador/`, `chillan_modis/`, `m/` y `mxd03_prereg/` de `origin/s159-pruebas`, y los JSON de
    resultados del run 39712862945. Los blobs de la copia del scratchpad coinciden con `origin/s159-pruebas`
    (`probe_portes.py 8ec50e7b`, `mirova_port.py 96769a89`, `04_analizar.py 6560b927`, `objetivos 7455d89c`,
    `poblacion cb48ddd4`, `oraculo 07da7010`).
  - `copias\`: copias de los scripts del auditor que escriben al lado de sí mismos (para no escribir fuera de CARPETA) y
    `evaluar_d25_s159-evaluador-d25.py` (`origin/s159-evaluador-d25` = `ded217af4`).
  - `verif_*.py` (mis instrumentos) y `salidas\` (toda salida cruda, mía y de las re-corridas).
- **Lo que NO miré** (que mi silencio no se lea como «todo bien»): no leí el informe del auditor de ningún frente ni
  `tasks/LOOP_MODIS.md`; no leí HDF reales (sin pyhdf en Windows) ni corrí red; no verifiqué el predicado del tablero ni
  `record_port` (vara de este plan, no mi eje); no medí «43 de 44 noches con protegida MODIS ya publican VIIRS» (MOD-D
  §4); no abrí la rama `s162-mxd03-codigo` porque no existe en `origin`; no verifiqué el método real de MIROVA para el
  bow tie (D28, SOSPECHA declarada por el auditor); no despaché nada ni usé credenciales.

## 2. En una pantalla

1. **MOD-C se sostiene**: los siete scripts reproducen sus salidas byte a byte en esta máquina (el sorteo da el mismo blob
   `02ee29f8`), la regla de decisión es monótona y sus fronteras (CONFIRMA sólo con x = 0, INDECIDIBLE 1 a 7, REFUTA
   desde 8) no se mueven con 10 semillas ni con N = 5.093; el workflow es válido, de sólo lectura y por token. Dos
   grietas chicas: la prueba del envoltorio es ciega a `sensor_zenith` y `sensor_azimuth` (dos mutaciones mías pasan), y
   los 8 controles protegidos son todos de Láscar bajo 41° de cenit.
2. **MOD-E: los números se reproducen, la lectura no se sigue de ellos.** El brazo SIN_DUP («filas de borde») no elimina
   duplicados: deja huecos de cobertura (10,7 % del eje a 25° de barrido, 9,9 % a 45°, 19,7 % a 55°) y conserva
   duplicados (8,9 % a 40°). La caída de 25 % a 50° aparece igual en focos vistos UNA sola vez (S/T 0,754, n 7): es
   efecto del remuestreo, no de quitar la copia del foco. Y el «efecto nulo hasta 45°» se mide donde el bow tie no actúa:
   a 40 y 45° los focos duplicados casi no se detectan en TODOS (0 de 11, 2 de 22) y quedan fuera de la mediana.
3. **MOD-D no es despachable y tiene reglas que obligan a decidir después de mirar**: P2 = BLOQUEA no tiene fila en §6;
   la salida «RESUELTO POR EL PAQUETE» de Chillán exige un d′ que, importado «sin copiar», pide dos volcanes con 3 pares
   (Chillán solo nunca cumple); el placebo «d′ = 0 o M INVALIDO» no puede fallar y contradice la D-28 sellada; M decide
   sólo en Chillán en §4 y en todo en §6; la población citada vive en una rama que no está en `origin`; el 0,485 de
   Chillán no es el de la población congelada (0,635, n 7); el costo doble-cuenta la descarga.
4. Lo que cada despacho decide sigue en pie: MOD-C puede correr tal cual (con las dos grietas anotadas); MOD-E no debe
   leerse como «D28 descartado hasta 52° y 1,3× sobre 55°»; MOD-D necesita evaluador, candado y reglas cerradas antes del
   sello.

## 3. Veredicto por afirmación

| afirmación | veredicto | evidencia (esta sesión) |
|---|---|---|
| C1 | **CONFIRMADO** | `salidas/01_seleccion_rerun.txt`: 5.093, 38 ya sorteadas, marco 5.055, n 400 proporcional en 22 estratos (semilla 162), 10 controles; blob del JSON escrito = `02ee29f8edc269aefa65874e6a834ff1fb41ec75`, idéntico al commiteado. Insumos con blob esperado (`cb48ddd4`, `7455d89c`). Grieta: VCD-10. |
| C2 | **CONFIRMADO** | `02` reproduce `filas_lote_s159_modis_fisica.json` byte a byte (ΔE −44,0; 8 cuentas de S159 IGUAL); `03` salida idéntica; `verif_c2_regla_salida.txt`: fronteras (1, 8) en las 10 semillas 163 a 172 y con N 5.093; monótona para n 300 a 400; con 0 eventos confirma desde n 310. Nota de lectura en §6. |
| C3 | **CONFIRMADO EN PARTE** | `04` salida idéntica; `jobs_39712862945.json` completo (`total_count` 15 = 15 jobs); 410 × 9,1 s + 8 × 104 s = 1,27 h. Parte no dicha: los 9,1 s INCLUYEN la búsqueda y descarga del par (VCD-09); para MOD-C no cambia la cifra, para MOD-D sí. |
| C4 | **CONFIRMADO EN PARTE** | `05` salida idéntica (85 s): control sin mutación PASA, 6 de 6 atrapadas por `AssertionError` (el código cuenta sólo esa excepción, l. 217-221). Parte que cae: la prueba no mira `sensor_zenith` ni `sensor_azimuth` (VCD-08: 2 de 4 mutaciones mías NO ATRAPADAS, control de mi arnés OK). Tamaño: estimado con modelo, declarado SIN DATO por el auditor. |
| C5 | **CONFIRMADO** | `c5_yaml.txt`: claves `name, on, concurrency, env, jobs` (`"on"` es string, A43); `permissions: contents: read` en los dos jobs; sin `git push`, `commit`, `continue-on-error`, usuario ni clave; `Token presente` es el primer paso del job `probe` y sale 1 si está vacío; `probe_portes.main` l. 421 vuelve a exigirlo y `fetch.auth` prefiere el token (l. 269-270, 318). Blobs del paso `Instrumento` = `origin/s159-pruebas` y = `0e18e1053`; el commit base es alcanzable desde `origin/s159-portes-disparo`. `07` ensayo en seco idéntico (38, 36, 36 de 36, x 0, INDECIDIBLE) e importa la regla de `03`. |
| E1 | **CONFIRMADO** | `e1_claves_grilla.txt`: 149 `grilla_*.npz` MODIS en D:, un solo conjunto de claves: `mir, tir, mir_b21, mir_geo5, tir_geo5`, float32 51 × 51; `probe_portes.py` l. 347-352 guarda sólo eso. |
| E2 | **CONFIRMADO EN PARTE** | Los dos scripts reproducen su salida; scipy da ρ 0,291 p 0,0057 (n 89) y Láscar ρ 0,294. Parte que el informe no dice (VCD-07): la subida está en las alertas bajo 1 MW (ρ 0,381, p 0,018, n 38) y no en las protegidas (ρ 0,194, p 0,23, n 40); en las bajo 1 MW baja el VRP de MIROVA con el cenit (ρ −0,321) y el cenit está confundido con la fecha (ρ −0,515); parcial | fecha ρ 0,277 (p 0,09). |
| E3 | **REFUTADO en la lectura, CONFIRMADO en los números** | Las dos corridas reproducen la salida byte a byte (3 m 27 s y 2 m 54 s). `verif_e3_bowtie_modelo_salida.txt`: SIN_DUP deja huecos y conserva duplicados según el ángulo (VCD-03); la caída de 25 % a 50° ocurre en focos no duplicados (VCD-03); el «nulo hasta 45°» se mide sobre focos donde los dos brazos usan los mismos píxeles, porque los duplicados no se detectan en TODOS (VCD-04). |
| D1 | **CONFIRMADO EN PARTE** | Respaldado: D33 existe (`origin/main:docs/MIROVA_DIVERGENCES.md:3310`), oráculo l. 96 es `temperatura_a_radiancia(bt15, LAMBDA_M13)`, 0 de 149 pasadas con B22 NaN y B21 válida (0 píxeles, campo `saturados.b22_nan_con_b21`), Chillán 0,837 y 1,734 a 58° (reproducido), `prueba_signos_p2` y `comparar_con_ganancia` con `N_CALIB_DPRIMA = 1000` en `ded217af`, 9,1 / 1,69 / 104 s, 32,8 s en `tiempo_proceso_vs_descarga_m_salida.txt:3`, `80b819828` existe y tiene el flag K33, (b) (c) (e) de `extra_verif_salida.txt`. Sin respaldo o distinto: población en rama inexistente (VCD-05), 0,485 contra 0,635 (VCD-11), costo doble (VCD-09), `record_port` «con la corrección V-5» no existe (VCD-12), «43 de 44 noches» SIN DATO. |
| D2 | **REFUTADO** (las reglas no cierran) | VCD-01 (BLOQUEA sin fila), VCD-02 (Chillán 1 inalcanzable con el d′ importado), VCD-06 (placebo que no puede fallar y contradice D-28 §2.5), VCD-07 bis (M local en §4, global en §6; P1b en dos filas; sin precedencia), VCD-13 (criterios sin número). |
| D3 | lista en §5 | |

## 4. Hallazgos (orden: lo peor primero)

### VCD-01. P2 = BLOQUEA no tiene fila en el veredicto del censo
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:97` (P2 por `prueba_signos_p2`, «importada sin
  copiar») y `:124-130` (tabla §6); `copias/evaluar_d25_s159-evaluador-d25.py`, `regla_signos_p2` (TEXTO: «SIN SUSTRATO
  con B de 4 o menos …; GANA …; PIERDE …; BLOQUEA si el neto es positivo sin llegar …; EMPATE si el neto es 0 o
  negativo sin llegar»).
- **QUÉ PASA**: físicamente, un paquete que publica un poco de más en negativos y no llega a significancia es el caso
  más probable de un port que «casi» reproduce. La regla vigente del proyecto devuelve BLOQUEA para eso; §6 sólo nombra
  GANA, EMPATE, PIERDE y SIN SUSTRATO, así que ese resultado no tiene etiqueta y se decide después de verlo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (pre-registro).
- **CÓMO REPRODUCIRLO**: `git show origin/s159-evaluador-d25:experiments/_s157_prereg_d25/evaluar_d25.py | grep -n BLOQUEA`
  y leer §6 del pre-registro.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 4.

### VCD-02. «RESUELTO POR EL PAQUETE» para Chillán exige un d′ que la función importada no puede dar con un solo volcán
- **ARCHIVO:LÍNEA**: `PREREGISTRO.md:98` («d′ contra la ganancia pareja … `comparar_con_ganancia` y su calibración de
  1.000 repeticiones»; «MEJORA sólo si d′ queda entero bajo 0») y `:114-115` (regla 1 de Chillán);
  `copias/evaluar_d25_s159-evaluador-d25.py` l. 295-340, docstring TEXTO: «Regla de D-27 sobre d′: intervalo al 95 %
  entero bajo 0; calibración simétrica de d′ … con tope de 5 % en la cola de MEJORA …; y mediana de d′ negativa en al
  menos dos volcanes con 3 pares o más (opción A). … `dprima_da_mejora` es la conjunción de las tres condiciones».
- **QUÉ PASA**: el déficit de Chillán se juzga sobre las alertas de Chillán que K y PM publican (K publica 7 de 10 en la
  población congelada). Si se importa `comparar_con_ganancia` «sin copiar», MEJORA exige dos volcanes: con uno solo la
  conjunción es falsa por construcción y la regla 1 nunca se cumple (todo cae en SIN RESOLVER). Si en cambio se usa sólo
  el intervalo de d′, eso no está escrito, y con ≤ 7 pares la calibración de 1.000 repeticiones probablemente no tenga
  poder (`MIN_PARES_PODER = 20`). En los dos casos el resultado de §5 queda predeterminado o a elección posterior.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: leer `comparar_con_ganancia` en el archivo citado; contar con
  `arbol/experiments/_s159/portes/poblacion_completa.json` las alertas de Chillán con `pub_prod` (7 de 10).
- **CONFIANZA**: CONFIRMADO (lectura del código); que la salida sea inalcanzable es SOSPECHA hasta correr. **GRAVEDAD**: 4.

### VCD-03. El brazo SIN_DUP del sintético no elimina duplicados: abre huecos y conserva duplicados según el ángulo; la caída de 25 % a 50° ocurre también en focos vistos una sola vez
- **SCRIPT:SALIDA**: `verif_e3_bowtie_modelo.py` → `salidas/verif_e3_bowtie_modelo_salida.txt` (misma geometría declarada
  en `experiments/_s162_modis_bowtie/ablacion_sintetica.py` l. 20-28 y 123: `sin_dup = |y − 10 s| < 5`).
- **QUÉ PASA**: en el modelo los detectores de un barrido se centran en `10 s + (d − 4,5) a`; quitar los que caen fuera de
  la franja de 10 km deja sin ninguna huella conservada el 10,7 % del eje a 25° de barrido, el 5,9 % a 30°, el 9,9 % a
  45° y el 19,7 % a 55°, y a la vez conserva doble cobertura en el 8,9 % a 40° y el 2,1 % a 50°. Eso no es quitar el
  duplicado: es sacar filas enteras sin mirar si la otra copia existe. Y la razón S/T a 50° es 0,754 también en los 7
  focos que TODOS ve una sola vez (`cT 1 cS 1`, 0,61 a 1,39), igual que la mediana global del informe: el 25 % menos sale
  de remuestrear con 40 % menos de píxeles, no de quitar la copia del foco. La frase del informe «conservar los
  duplicados infla la suma del orden de 1,3 veces» (`INFORME.md:96-98`) no se sigue de lo medido, y MOD-D define
  PM-sin_dup con esta misma regla (`PREREGISTRO.md:73`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy; si PM-sin_dup entra al paquete con esta definición, un brazo que abre
  huecos de cobertura puede callar sobre un foco real en el hueco.
- **CÓMO REPRODUCIRLO**: `python -I verif_e3_bowtie_modelo.py --json ..\_s162_modis_bowtie\ablacion_sintetica_3MW.json`
  (tabla de cobertura y tabla por clase `cT, cS`). Control: en el nadir los dos brazos dan cobertura 1 en el 100 % (OK).
- **CONFIANZA**: CONFIRMADO (medición sobre el mismo modelo del auditor). **GRAVEDAD**: 3.

### VCD-04. El «efecto nulo hasta 45°» se mide donde el bow tie no actúa: los focos duplicados casi no se detectan en TODOS y quedan fuera de la mediana
- **SCRIPT:SALIDA**: `salidas/verif_e3_bowtie_modelo_salida.txt`, tabla por clase (3 MW): a 40° los focos con `cT 2`
  (duplicados en TODOS) se detectan 0 de 11, los `cT 1` 24 de 29; a 45°, 2 de 22 contra 18 de 18; a 50°, 17 de 32 contra
  7 de 7.
- **QUÉ PASA**: con las copias interleavadas (det 8 de un barrido y det 1 del siguiente a 0,5 km, con píxeles fríos entre
  medio), el remuestreo lineal reparte el foco entre vecinos fríos y el código no lo detecta. Así, S/T (que exige detección
  en los dos brazos) se calcula casi sólo sobre focos vistos una vez, donde los dos brazos comparten píxeles y S/T = 1 por
  construcción. En el modelo el bow tie se manifiesta como pérdida de DETECCIÓN del port, que la tabla del informe no
  desglosa, y la dispersión por realización ya es grande desde 30° (fuera de [0,95; 1,05]: 14 % a 30°, 54 % a 40°,
  25 % a 45°, 84 % a 50°) y sólo aparece en p10-p90. La conclusión «D28 no explica la subida de Láscar entre 25 y 48°»
  (`INFORME.md:20`) queda SIN EVIDENCIA, no refutada.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: mismo comando que VCD-03.
- **CONFIANZA**: CONFIRMADO (medido). **GRAVEDAD**: 3.

### VCD-05. La población y la referencia que MOD-D declara congelar viven en una rama que no está en `origin`
- **ARCHIVO:LÍNEA**: `PREREGISTRO.md:52-54` («`experiments/_s162_mxd03/poblacion.json`, rama `s162-mxd03-codigo`, main
  congelado `80b819828`, referencia congelada con sha256 en `MANIFIESTO.json`») y `:156`.
- **QUÉ PASA**: tras `git fetch origin --prune`, `origin/s162-mxd03-codigo` no es un objeto válido y ninguna rama remota
  contiene `experiments/_s162_mxd03/`. El commit `80b819828` sí existe (NRT 2026-10-24 14:21 UTC) y tiene el flag K33. Los
  conteos (5.465 pasadas, 1.232 gránulos, 50 / 42 / 5.110 / 253 / 10) se corroboran en
  `arbol/experiments/_s159/mxd03_prereg/verificador/extra_verif_salida.txt` (b), (c), (e) de `origin/s159-pruebas`, pero el
  archivo con el que el censo se ata no lo puede abrir un tercero ni el runner.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git fetch origin --prune && git rev-parse origin/s162-mxd03-codigo`; `for b in $(git branch -r);
  do git ls-tree $b experiments/_s162_mxd03/; done`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (bloquea el despacho; no tuerce un veredicto).

### VCD-06. El placebo «d′ = 0 o M INVALIDO» no puede fallar y contradice la D-28 sellada
- **ARCHIVO:LÍNEA**: `PREREGISTRO.md:74` («placebo K × 1,2 … obligatorio para M»), `:98` («el placebo K × 1,2 tiene que
  dar d′ = 0 (si no, el instrumento no sirve y M queda INVALIDO)»), `:150`; `copias/evaluar_d25_s159-evaluador-d25.py`
  l. 301 TEXTO: «Para una ganancia uniforme (el placebo) d′ es 0», y l. 884-885 TEXTO: «la compuerta del placebo se
  retiró; ningún placebo vuelve INVALIDO el veredicto».
- **QUÉ PASA**: con B = 1,2 K, ĝ = 1,2 y d′ = |log(1,2 K / 1,2 / M)| − |log(K / M)| = 0 en cada par, con cualquier dato y
  con el instrumento muerto: es un control que no puede fallar (A110), vale como prueba de humo del cableado y nada más.
  Además la regla sellada D-28 §2.5 dice que el placebo informa y no invalida; MOD-D vuelve a ponerle compuerta.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: leer las líneas citadas.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

### VCD-07. La razón port/MIROVA sube con el cenit en Láscar sólo en las alertas bajo 1 MW, donde el cenit va de la mano de la fecha
- **SCRIPT:SALIDA**: `verif_e2_confusores.py` → `salidas/verif_e2_confusores_salida.txt`; `salidas/verif_e2_parcial_bajo.txt`.
- **QUÉ PASA**: el agregado se reproduce (ρ 0,291, p 0,0057, n 89; Láscar ρ 0,294, p 0,009, n 78). Separado por clase:
  protegidas de Láscar ρ 0,194 (p 0,23, n 40); bajo 1 MW ρ 0,381 (p 0,018, n 38). En las bajo 1 MW el VRP de MIROVA
  cae con el cenit (ρ −0,321, p 0,049) y el del port no (ρ −0,047); y el cenit cae con la fecha (ρ −0,515, p 0,0009:
  cenit mediano 38,6° en marzo, 5,0° en septiembre), con la razón mediana bajando de 1,18 a 0,64 en el mismo lapso.
  Parcial | fecha en bajo 1 MW: ρ 0,277 (p 0,09); en Láscar entero la parcial no cambia (0,293). O sea que el informe
  tiene razón en que no es composición de volcanes, pero no estratificó por clase ni descontó la fecha, y el mecanismo
  compatible con lo medido (MIROVA pierde magnitud oblicua en las alertas débiles, el port no) no está dicho.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (el port no está en producción).
- **CÓMO REPRODUCIRLO**: `python -I verif_e2_confusores.py --art D:\vrp-trabajo\temporales\s159_portes\run_39712862945
  --objetivos arbol\experiments\_s159\portes\objetivos_portes.json`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### VCD-08. La prueba del envoltorio es ciega a `sensor_zenith` y `sensor_azimuth`
- **SCRIPT:SALIDA**: `verif_c4_mutacion_extra.py` → `salidas/verif_c4_mutacion_extra_salida.txt`: `m7_zenit_azimut_intercambiados`
  NO ATRAPADA, `m8_zenit_en_ceros` NO ATRAPADA; `m9` (lat/lon MxD03 intercambiadas) y `m10` (forma del gránulo)
  atrapadas; control (`b22 = b21`) atrapado por aserción. `05_prueba_envoltorio.py` l. 174-177 compara 7 capas; las dos de
  geometría no están en `pares`.
- **QUÉ PASA**: MOD-E necesita el cenit por píxel para estratificar la ablación real; un recorte con el cenit y el acimut
  cambiados, o en ceros, pasa la prueba y el job `prueba` queda verde. El 6 de 6 del auditor es cierto para sus 6
  mutaciones; el alcance de la prueba es 7 de las 9 capas con contenido.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: con `VRP_S159_PORTES` apuntando a `arbol\experiments\_s159\portes`,
  `python -I verif_c4_mutacion_extra.py --prueba ..\_s162_modis_negativos` (unos 2 min).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### VCD-09. Los «9,1 s por pasada» de S159 incluyen la descarga del gránulo; MOD-D suma la descarga otra vez
- **ARCHIVO:LÍNEA**: `arbol/experiments/_s159/portes/probe_portes.py:302` (`t0 = time.time()`), `:304` (`bajar_par`),
  `:368` (`r["segundos"] = round(time.time() - t0, 1)`); `experiments/_s162_modis_negativos/PREREGISTRO.md:138`;
  `experiments/_s162_modis_paquete/PREREGISTRO.md:160-164`.
- **QUÉ PASA**: el cronómetro arranca antes de buscar y bajar el par L1B + MxD03 (que se borra al terminar cada pasada,
  l. 362-366), así que 9,1 s es búsqueda + descarga + port + K. Para MOD-C la proyección vale tal cual (misma cadena).
  MOD-D suma 1.232 × 32,8 s de descarga más 5.465 × 9,1 s: la descarga entra dos veces y las «≈ 28 h» son cota alta
  (≈ 17 h con 9,1 s por pasada, menos si las pasadas comparten gránulo). El 32,8 s además es la media de «búsqueda CMR +
  descarga entre records» del probe de M (mediana 17,5, p90 72), no «un gránulo con L1B y MxD03» medido aparte.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `sed -n 299,305p arbol/experiments/_s159/portes/probe_portes.py; sed -n 366,369p …`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (sobrestima; no hace indecidible nada).

### VCD-10. Los 8 controles protegidos del lote son todos de Láscar y ninguno pasa de 41° de cenit
- **SCRIPT:SALIDA**: `salidas/01_seleccion_rerun.txt` (última línea: 8 `pos_prot` Láscar); `objetivos_portes.json`:
  `pos_prot` MODIS en S159 = Láscar 40, Chillán 9, Villarrica 1; cenit de los 8 elegidos 2,4° a 40,5°.
- **QUÉ PASA**: el control de instrumento (§6.3 del pre-registro) tiene que mostrar que la cadena enciende donde debe.
  Con la semilla 163 el sorteo de 8 entre 50 cayó en Láscar nadir-medio; si la cadena fallara sólo en pasadas oblicuas
  (el régimen de Chillán a 58°, que es justo el que MOD-E y MOD-D discuten), el control no lo vería.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -c "import json,collections;o=json.load(open('arbol/experiments/_s159/portes/objetivos_portes.json'));print(collections.Counter(x['volcan'] for x in o if x['b']=='MODIS' and x['clase']=='pos_prot'))"`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### VCD-11. El «K/MIROVA 0,485, n 7» de Chillán no cita fuente y no es el de la población congelada que MOD-C y MOD-D usan
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:24`; la cifra viene de
  `experiments/_s161_estado_864/INFORME.md:31` vía la tabla del programa (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md:26`).
  Sobre `arbol/experiments/_s159/portes/poblacion_completa.json` (blob `cb48ddd4`, la que MOD-C congela): Chillán 10
  alertas, 9 protegidas, K publica 7, `pc_vrp / mirova_vrp` = 0,137, 0,205, 0,209, 0,635, 0,747, 0,779, 0,847, mediana
  **0,635** (n 7).
- **QUÉ PASA**: dos medianas distintas con el mismo «n 7» para el mismo volcán y la misma ventana: otra referencia u otro
  pareo. El pre-registro juzga ese déficit (§5) sin fijar sobre qué población y referencia lo mide.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -I verif_d1_numeros.py --pob arbol/experiments/_s159/portes/poblacion_completa.json --art D:/vrp-trabajo/temporales/s159_portes/run_39712862945` → `salidas/verif_d1_numeros_salida.txt` (la
  cuenta es sobre `pasadas` con `b == MODIS`, `lab == pos`, `volcan == NevadosDeChillan`, sin el 17 al 20 de octubre).
- **CONFIANZA**: CONFIRMADO EN PARTE (la fuente existe pero no está citada; el número difiere del de la población congelada).
  **GRAVEDAD**: 2.

### VCD-12. El `record_port` «sin cambios, con la corrección V-5» no existe: `04_analizar.py` sólo tiene la distancia del centroide
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:83-86`; `arbol/experiments/_s159/portes/04_analizar.py:59-72`
  (`origin/s159-pruebas`, blob `6560b927`): `distance_class` sale de `dcen` (centroide) y no hay distancia del alertado
  más cercano.
- **QUÉ PASA**: MOD-D dice usar la función sin cambios y a la vez con una corrección que no está en ella. Alguien tendrá
  que escribirla, y entonces el «sin cambios» y la cadena «PM = port de S159» del control 2 dejan de ser literales.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git show origin/s159-pruebas:experiments/_s159/portes/04_analizar.py | sed -n 59,72p`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### VCD-13. Reglas de MOD-D con alcance o umbral sin fijar (obligan a decidir después de mirar)
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:96` (P1b «primera dirección» decide) contra `:129`
  («P1b con alguna»); `:98` (M «decide sí, para Chillán e informa en el resto») contra `:126` («M sin EMPEORA sobre d»
  como condición global de CANDIDATO) y `:129`; `:116-118` (Chillán regla 2: «sigue la misma caída con el cenit que
  MIROVA contra sí misma», sin número); `:99` («condiciona Chillán», sin decir cómo); `:52` (`sin_info` 253, `far_ref` 10
  sin decir si entran a P2); `:126-130` (sin precedencia: control rojo más protegida perdida cae en NO CANDIDATO y en
  INDECIDIBLE; fila CANDIDATO sin mencionar P1b).
- **QUÉ PASA**: cada una de estas lecturas deja dos etiquetas posibles para el mismo dato.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: leer las líneas citadas.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### VCD-14. El lector `07_leer_lote.py` sólo reconoce dos motivos de «no evaluable»; un `motivo_vacio = sunglint` contaría como silencio del port
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_negativos/07_leer_lote.py:57-64`; el oráculo tiene dos motivos:
  `arbol/experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py:136` (`sunglint`) y `:155` (`escena_invalida`).
- **QUÉ PASA**: en S159 los 149 ok sólo tuvieron `None` (148) y `escena_invalida` (1) (`salidas/c5_motivos_s159.txt`), y
  de noche el reflejo solar no debería aparecer; si apareciera, la pasada entraría a n con x = 0 y empujaría hacia
  CONFIRMA. Riesgo bajo, pero el lector debería listar el motivo y excluirlo o declarar por qué no.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n motivo arbol/experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`.
- **CONFIANZA**: SOSPECHA (no hay caso en los datos). **GRAVEDAD**: 1.

## 5. D3: lo que falta para que MOD-D sea despachable

1. **Evaluador propio**: no existe ningún script en `experiments/_s162_modis_paquete/` (sólo `PREREGISTRO.md`). Falta el
   que arme bloques noche-volcán, llame a `prueba_signos_p2` / `regla_signos_p2` y a `comparar_con_ganancia` del commit
   fijado, calcule P1, P1b, la curva de cenit y las tres salidas de Chillán, con pruebas de mutación y control de caída
   (S156) y ensayo en seco sobre el lote de S159 (como hizo MOD-C con `07`).
2. **Candado**: §8 se llama «Controles»; el «candado del §8» que el encabezado invoca no está escrito. Faltan los blobs del
   port (`mirova_port.py 96769a89`, `probe_portes.py 8ec50e7b`, `oraculo 07da7010`), del evaluador (`evaluar_d25.py` en
   `ded217af4`, hoy sin commit fijado en el texto), del `record_port` que se use, del arnés y de la referencia (sha256),
   más el tag defensivo.
3. **Población alcanzable** (VCD-05): la rama `s162-mxd03-codigo` y `experiments/_s162_mxd03/` tienen que estar en `origin`
   o la población se vuelve a congelar en una rama que exista.
4. **Reglas cerradas** (VCD-01, 02, 06, 13): fila para BLOQUEA; decir si d′ se toma entero o sólo su intervalo, y qué pasa
   con un solo volcán y ≤ 7 pares; placebo como humo (sin INVALIDO) o justificar apartarse de D-28 §2.5; alcance de M; una
   sola regla para P1b; precedencia entre filas; criterio numérico de «sigue la misma caída»; destino de `sin_info` y
   `far_ref`.
5. **PM-sin_dup**: redefinir la eliminación de duplicados (VCD-03) antes de gastar runner en ese brazo, y decir de dónde
   sale el índice de línea en el arnés del censo (el arnés de MOD-B no está en `origin`).
6. **`record_port`** (VCD-12): escribir la corrección V-5 o quitar la frase; fijar su blob.
7. **Costo** (VCD-09): recalcular sin doble conteo y medir el costo del `prueba` equivalente.
8. **Workflow**: no hay yml para MOD-D; el de MOD-C sirve de molde (token, sólo lectura, blobs, `"on"`).
9. **Verificador limpio después del resultado**, previsto por el programa §2; dejarlo en el pre-registro.

## 6. Notas de lectura (no son hallazgos)

- **C2, qué quiere decir «CONFIRMA con x = 0»**: el límite superior de Jeffreys al 97,5 % con 0 de 400 es 0,63 % (+31,6
  pasadas sobre 5.055); sumado réplica a réplica con ΔE_otros da IC [−56,5; −9,4]. La suma de cotas (Wilson, +18,6) nunca
  confirma y el auditor lo declara. El veredicto depende de esa convención declarada; con n = 310 ya confirma, con 300 no.
  Tratar `pos_bajo` (censo) como fijo angosta a [−55,4; −10,1] y tampoco cambia la frontera.
- **E2, pseudorreplicación**: 31 de las 89 pasadas tienen más de una fila de MIROVA pareada a ±120 s; qué fila da
  `mirova_vrp` no es mi eje (SEGUIMIENTO).

## 7. SEGUIMIENTOS (fuera de mi eje)

- **La rama de trabajo está 708 commits detrás de `origin/main`** (`git log --oneline HEAD..origin/main | wc -l`;
  merge-base `2ca366cdc`). `pipeline/profile.py` de este worktree no tiene `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA`
  (`origin/main:pipeline/profile.py:645` sí). Cualquier lectura de `pipeline/` hecha desde este worktree describe un
  pipeline viejo. CONFIRMADO, gravedad 2 para quien audite desde aquí.
- `probe_portes.py:41-42` mete `RAIZ` y `RAIZ/scripts` en `sys.path`: si el árbol base no trae `scripts/`, el import de
  `banco_paridad` en `04_analizar.py:33` falla en silencio de otra forma. En el runner el árbol es completo; anotado por si
  alguien lee los artefactos en otra máquina. SOSPECHA, gravedad 1.
- `mirova_vrp` con varias filas de MIROVA por pasada (31 de 89): confirmar que es la fila de la alerta. SOSPECHA, gravedad 1.
- Mi primer control del nadir en `verif_e3_bowtie_modelo.py` dio FALLA por empates exactos en los bordes de huella
  (intervalos cerrados por los dos lados); corregido a semiabierto, da OK. Lo dejo escrito porque es el mismo modo de falla
  que el proyecto llama «el instrumento mide otra cosa».

## 8. VERIFICADO LIMPIO (comando y vara)

- `01_seleccion.py` reproduce el blob `02ee29f8` del JSON de objetivos en esta máquina (Windows, Python 3.12): vara = el
  archivo commiteado. `salidas/01_seleccion_rerun.txt`.
- `02_filas_lote_s159.py` reproduce `filas_lote_s159_modis_fisica.json` byte a byte (`cmp`), con node y el predicado del
  tablero del árbol base: vara = las 8 cuentas de `04_analizar_salida.txt` de S159 (IGUAL las 8). `salidas/02_filas_rerun.txt`.
- `03_regla_decision.py`: salida idéntica (`diff`); controles (a) INDECIDIBLE (b) REFUTA (c) CONFIRMA; `verif_c2_regla.py`:
  fronteras (1, 8) con 10 semillas y con N 5.093, monótona n 300 a 400. Vara = la tabla del pre-registro §3.
- `04_costo.py`: salida idéntica; `jobs_39712862945.json` `total_count` 15 = 15 (sin paginación perdida).
- `05_prueba_envoltorio.py`: salida idéntica salvo el tiempo (85,2 s); el conteo exige `AssertionError` (l. 217-221); la
  identidad compara el JSON entero del port en las 5 variantes y la grilla guardada (l. 152-161).
- `probe-s162-negmodis.yml`: `yaml.safe_load` da claves string, `"on"` quoted; permisos lectura; sin push ni usuario/clave;
  token primero; `--solo ""` es inocuo (`probe_portes.py:433 if a.solo`); blobs del `Instrumento` = `0e18e1053` =
  `origin/s159-pruebas`; `0e18e1053` alcanzable desde `origin/s159-portes-disparo`; dependencias del job `prueba` cubren
  los imports no estándar del camino (`scipy`, `yaml`, `numpy`, `pyproj`; pyhdf falso en 05). `salidas/c5_yaml.txt`.
- `07_leer_lote.py` ensayo en seco idéntico (`diff`), e importa `03` para el veredicto. `salidas/07_ensayo_rerun.txt`.
- E1: 149 `grilla_*.npz`, un conjunto de claves (`salidas/e1_claves_grilla.txt`).
- E2: `razon_por_cenit.py` y `_volcan.py` idénticos; scipy ρ 0,291 (p 0,0057). `salidas/razon_por_cenit*_rerun.txt`.
- E3: `ablacion_sintetica.py` 1 y 3 MW idénticos; control negativo del nadir OK en las dos. `salidas/ablacion_*_rerun.txt`.
- D1 respaldado: D33 (`origin/main:docs/MIROVA_DIVERGENCES.md:3310`); oráculo l. 96; `saturados.b22_nan_con_b21` = 0 en
  149 pasadas y 0 píxeles; Chillán 0,837 y 1,734 (`salidas/razon_por_cenit_volcan_rerun.txt`); `prueba_signos_p2` (l. 509),
  `comparar_con_ganancia` (l. 295), `N_CALIB_DPRIMA = 1000` (l. 126) en `ded217af4`; `m/INFORME.md:97` H4;
  `chillan_modis/INFORME.md:39` H1; `extra_verif_salida.txt` (b) 92 filas CONS, (c) 1.232 / 5.465, (e) 5.110 / 253 / 10;
  `80b819828` existe y tiene el flag K33; 32,8 s en `tiempo_proceso_vs_descarga_m_salida.txt:3`.

## 9. SIN DATO

- «43 de 44 noches con protegida MODIS ya publican VIIRS» (MOD-D §4): sin fuente citada y no lo medí.
- El bow tie real (sin HDF ni pyhdf en Windows); el costo del job `prueba` en el runner; el método de MIROVA para los
  duplicados (D28).
- Si la salida «RESUELTO POR EL PAQUETE» es alcanzable con ≤ 7 pares (VCD-02): depende de cómo se importe d′.

## 10. FUERA DE ALCANCE

El predicado del tablero y `record_port` como vara; el pareo de la referencia; MOD-A y MOD-B; cualquier arreglo.
