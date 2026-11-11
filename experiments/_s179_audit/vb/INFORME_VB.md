# Verificación del frente B, auditoría S179 (VIIRS 375 y 750: encendido preparado y regla de reversión)

## 1. Encabezado

- Hora del servidor al empezar: Wed, 11 Nov 2026 01:53:57 GMT (cabecera Date de GitHub). Informe cerrado a las 02:09:54 GMT del 2026-11-11 (cabecera Date).
- Código medido: main 438a60a1e. La instantánea D:\vrp-trabajo\temporales\s179-audit\main\ coincide con `git show 438a60a1e` en los 9 archivos citados (sha256). origin/main ya va en 16d78e3e0, pero entre los dos commits sólo cambiaron datos (ningún archivo de código, workflow ni regla). Documentos del loop: 0472cd95e (D:\vrp-trabajo\temporales\s179-audit\loop\).
- Modelo: Claude Opus 5.5, con el esfuerzo que fijó la sesión que me lanzó (bajo).
- CARPETA: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\
- Caminos escritos antes de abrir los archivos citados: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\caminos.md (sha256 707c836b7a3ca689..., sellado a las 01:54:31 UTC). No lo volví a editar.
- Temporal: D:\vrp-trabajo\temporales\s179-audit\vb\ (unos 178 MB: datos de 16d78e3e0 para medir una noche más, y un almacén de objetos git privado de 152 KB para simular merges sin escribir en el .git compartido).
- Llamadas a la API de GitHub: 5 de 5 (tres cabeceras Date, `gh pr view 984`, `gh run view 42742205624`).
- Qué NO miré: el informe y el hallazgos.csv del auditor (obstáculo deliberado); docs/PLAN_AUDITORIA_S179.md y otras carpetas experiments/_s179_*; el navegador (no abrí el tablero); los logs de los runs de Actions (sólo el resumen de pasos de un run); el código de `pipeline/mirova_v750_codigo.py` (no verifiqué por qué la vía calla las tres Muy Bajo, sólo que las calla); la retrospectiva de MODIS; cualquier cosa de MODIS fuera de lo que comparte el vigilante.

## 2. En una pantalla

1. De las 15 afirmaciones del frente B, ninguna queda refutada. 8 se confirman enteras y 7 en parte. Las correcciones son de cifra o de alcance; ninguna invierte el sentido.
2. Lo más serio (gravedad 3): con Chillán en erupción, el plazo de la reversión pre-autorizada se agota en 11 a 13 días, y casi todo lo que prueba es Chillán (451). Además, el paso de `nrt.yml` que pone rojo un error de la vía en VIIRS sigue sin hacer, y se pasó a «después del merge» sin una frase de Nicolás (454 y DEC-15). Por último, el día del encendido el tablero sólo mostrará una línea, aunque la magnitud cambie mucho entre volcanes (456).
3. Correcciones: revertir B1 con B2 ya adentro choca en 11 archivos, no en 9 (457). El salto de magnitud medido pasada a pasada va de 0,44 a 4,09 veces según el volcán, no de 1,3 a 3,2 (456). La razón «4,9 veces» de la cota (i) baja a 3,7 a 4,3 con otro denominador u otra ventana, y descansa en 3 casos (452).
4. Hallazgo nuevo VB-01: todos los datos de la guardia K de VIIRS anteriores al 11-11 salen de una sola ejecución manual. Esa ejecución terminó en falla, y la primera corrida programada también falló en los 11 volcanes. La primera corrida programada en verde es la del 2026-11-11 a las 00:12 UTC. La condición «tres noches de guardia» todavía no se cumple si se cuentan corridas.
5. Los tres scripts del auditor se reprodujeron idénticos desde mi carpeta (salvo fin de línea). Los controles nulo y positivo dieron lo esperado.

## 3. Veredicto por afirmación, ordenado por mi gravedad

Notación: «re-corrido» quiere decir que copié el script del auditor a mi carpeta, lo corrí y la salida dio idéntica a la suya (`diff --strip-trailing-cr`). Las cifras de una ventana van con su denominador. Las ventanas son las noches del 2026-11-03 al 11-09 (datos de 438a60a1e) y del 11-03 al 11-10 (datos de 16d78e3e0).

### 451. Plazo de 29 protegidas: unos 11 días, casi sólo Chillán. CONFIRMADO EN PARTE. Mi gravedad: 3

- ARCHIVO:LÍNEA: scripts/vigilancia_guardia_modis.py:228-237 (en `vistas` entran todas las protegidas con record en la guardia, de todos los volcanes juntos; `dentro_de_plazo` exige orden 29 o menos) y :327 (el plazo se cumple con 29 vistas o a los 120 días). La regla lo dice en l. 106 (§4.6) y l. 27 (D3). Leído en 438a60a1e.
- SCRIPT:SALIDA: re_sim_vigilancia_salida.txt (re-corrido): VIIRS 375, 20 protegidas en 7,79 días (18 de Chillán y 2 de Cordón Caulle). VIIRS 750, 19 protegidas (16 y 3). Con otra ventana (sim_ventana_16d78_salida.txt, datos de 16d78e3e0, 8,79 días): VIIRS 375 tiene 21 (19 y 2), es decir 2,39 por día, y llega a 29 en 12,1 días. VIIRS 750 tiene 20 (17 y 3) y llega a 29 en 12,7 días.
- QUÉ PASA: mientras Chillán siga en erupción, junta 2 a 3 alertas protegidas por noche. A ese ritmo, la ventana en que la reversión está pre-autorizada se cierra en 11 a 13 días. Desde entonces, una protegida callada queda como `CANDIDATA_FUERA_DE_PLAZO` y decide Nicolás. La potencia que cita D3 (1 menos 0,9 elevado a 29, igual a 0,953) supone 29 pruebas independientes. Aquí son unas 26 alertas fuertes de un mismo volcán (2 a 37 MW en VIIRS 375), y casi ninguna es débil ni de otro volcán.
- Corrección: no es «un solo volcán». Cordón Caulle aporta 2 protegidas en VIIRS 375 y 3 en VIIRS 750. Además, el plazo corto depende de la erupción: en la ventana O (junio a octubre, NOAA-20 y NOAA-21) hubo 0,22 protegidas por día (re_cotas_poder_salida.txt, parte 2). A ese ritmo, 29 protegidas tardarían unos 131 días y mandaría el tope de 120 días.
- CÓMO SE VE EN EL DASHBOARD: invisible. El operador no ve el plazo. Pasado el plazo, una protegida callada abre igual el aviso de la vigilancia, pero ya no está pre-autorizada.
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\sim_ventana_16d78.py"`, con datos de 16d78e3e0 extraídos a D:\vrp-trabajo\temporales\s179-audit\vb\datos_16d78e3e0\. Mira «protegidas posteriores al encendido» en el escenario A.
- Por qué baja de 4 a 3: la vigilancia sigue detectando y avisando después del plazo. Lo que se pierde es la reversión automática, no la detección.

### 454 y DEC-15 (los fundo: son el mismo hecho). Condiciones previas al merge no hechas; el paso de `nrt.yml` pasó a «después del merge» sin frase de Nicolás. CONFIRMADO. Mi gravedad: 3

- ARCHIVO:LÍNEA: la regla, en l. 116 a 126 (§5, «PR B1 y B2, cada uno aparte, antes del merge»), con su l. 122: «Un paso en `nrt.yml` que deje el job en rojo si el log trae `ERROR processing` en un gránulo de ese sensor». En 438a60a1e, `.github/workflows/nrt.yml` l. 373 a 384 sólo mira MODIS. El comentario de ese bloque dice, TEXTO: «Los errores de VIIRS se informan y no hacen fallar». `scripts/revisar_errores_modis_nrt.py` l. 12 y 13 dice lo mismo, TEXTO: «Los `ERROR processing` de VIIRS (375 m y 750 m) se cuentan y se informan, pero NO hacen fallar el job». tasks/LOOP_OBJETIVOS.md l. 645 (0472cd95e), TEXTO: «Pendiente tras el merge (fuera de los PR): paso de `nrt.yml` que ponga rojo `ERROR processing` en VIIRS». La entrada no trae ninguna frase de Nicolás.
- Estado de cada condición de la regla §5, para B1:
  - Hechas: el sello y `COTAS` (vigilancia_guardia_viirs.py:73-74); #965 en main (commit 7e0cc55da); el flag y su prueba en la rama de #974 (cuerpo del PR, tabla de archivos); la prueba de que el revert no choca, sólo en perfiles.
  - No hechas:
    - (1) Probar en navegador con records de la vía (LOOP_OBJETIVOS.md:645, «probar en navegador sigue pendiente»).
    - (2) El paso de `nrt.yml`.
    - (3) Medir el tiempo del NRT con la vía (cuerpo de #974, «Condiciones pendientes», punto 4).
    - (4) La excepción al congelamiento §12.6 para B1 y B2: `grep 12.6` en la bitácora sólo encuentra la de `fetch.py` (l. 841) y la de MODIS (l. 1704).
    - (5) El aviso a consumidores para VIIRS: hay un precedente de MODIS que lo dio por cumplido porque no hay consumidores (l. 1359 a 1363), pero no está anotado para VIIRS.
  - Parciales: las marcas por divergencia en `MIROVA_DIVERGENCES.md` (#974 sólo pone la marca general); la guardia «tres noches» (ver VB-01).
- QUÉ PASA: con la vía encendida, una falla del código de la vía en un gránulo VIIRS no cae a K. La pasada queda sin record y el job del NRT sale verde. El primer aviso llega a las 24 horas, y sólo si había una protegida (§4.4 (a)). Si la vía se detiene en un volcán, el aviso llega a los 3 días por frescura. Una alerta débil en esa pasada no la ve nadie (ver 460).
- CÓMO SE VE EN EL DASHBOARD: una pasada que no aparece. Para el operador es silencio.
- CÓMO REPRODUCIRLO: `sed -n 373,384p .github/workflows/nrt.yml` y `sed -n 640,646p tasks/LOOP_OBJETIVOS.md` en las instantáneas de main y de loop.

### 456. Salto de magnitud el día del encendido y el tablero sólo lo marca con una línea. CONFIRMADO EN PARTE. Mi gravedad: 3

- ARCHIVO:LÍNEA: frontend/cambio_detector.js:284-293 (438a60a1e). Por cada familia, `notarRecords` sólo guarda la fecha. El comentario de l. 288 a 290 dice, TEXTO: «la vía ya no pone aviso de texto arriba del tablero; la marca queda sólo como línea vertical en los gráficos». La línea lleva el rótulo «VIIRS 375: vía MIROVA» (l. 170, l. 337) y no explica el cambio. El diseño, docs/superpowers/specs/2026-11-08-encendido-v375e-design.md l. 60 (0472cd95e), TEXTO: «La magnitud sube cerca del doble en esa fecha y el operador debe leer que **no es que el volcán crezca**».
- SCRIPT:SALIDA: re_detalle_sombra_salida.txt (re-corrido) da la razón de medianas contra MIROVA, de 1,32 a 3,16 por volcán en VIIRS 375 y de 1,27 a 2,91 en VIIRS 750. Medido por otro camino (magnitud_via_k_438a60a1e_salida.txt): la razón vía/K pasada a pasada, en todas las pasadas que los dos publican. En VIIRS 375 la mediana total es 1,94 (n 57). Por volcán la mediana va de 0,44 (Chaitén, n 2) y 1,03 (Lastarria, n 4) a 4,09 (Isluga, n 6), con un máximo de 25,8 en una pasada de Chillán. En VIIRS 750 la mediana total es 2,08 (n 23). Con una noche más (magnitud_via_k_16d78e3e0_salida.txt) las cifras casi no cambian, y Lastarria baja a 0,75. Control nulo: K de la guardia contra K de producción da 1,0000 exacto (n 84 y n 28).
- QUÉ PASA: el cambio de detector no es «el doble parejo». En Isluga y Tupungatito la magnitud mostrada sube 3 a 4 veces en la mediana. En Chaitén y Lastarria la vía puede mostrar menos que K. Una línea con un rótulo no le dice al operador nada de eso.
- Corrección: el rango 1,3 a 3,2 sale de medianas contra MIROVA, sólo en pasadas con alerta. Pasada a pasada, el rango por volcán es más ancho (0,44 a 4,09), con n de 2 a 18 por volcán.
- CÓMO SE VE EN EL DASHBOARD: un escalón en la serie de VIIRS en la fecha de una línea punteada rosada (375) o celeste (750), sin texto. En Chillán, con el domo activo, puede leerse como «la erupción crece».
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\magnitud_via_k.py" D:\vrp-trabajo\temporales\s179-audit\b\datos 2026-11-03 2026-11-09`.

### 452. La cota (i) de VIIRS 375 (más de 14) está muy por debajo de lo que la vía calló en la semana de la sombra. CONFIRMADO EN PARTE. Mi gravedad: 2

- ARCHIVO:LÍNEA: scripts/vigilancia_guardia_viirs.py:73 (`"VIIRS375": {"muy_bajo": 14, ...}`) y la regla l. 92 («se esperan 9,48 en 120 días»), en 438a60a1e.
- SCRIPT:SALIDA: re_sim_vigilancia_salida.txt (re-corrido): 3 de 36 en 7,79 días (Planchón-Peteroa 0,06 MW el 11-05 05:24; Cordón Caulle 0,09 MW el 11-04 05:42 y 0,36 MW el 11-07 06:30). Proyectado a 120 días son 46,21, que es 4,87 veces 9,48. Con la guardia real (escenario A2) dan los mismos 3. Con una noche más (sim_ventana_16d78_salida.txt) son 3 de 38 en 8,79 días: 40,96, o 4,32 veces. Por pasada en vez de por día (tasa_por_pasada_452_salida.txt): 3 de 36 es 0,083, 3,9 veces la tasa por pasada de la calibración C-rad (0,0213). La probabilidad de ver 3 o más con la tasa calibrada es 0,041, y 0,047 con la ventana larga. Comprobé a mano una de las tres: Cordón Caulle 2026-11-07 06:30 UTC. MIROVA dice 0,36 MW, ALERTA_TERMICA, Muy Bajo, a 8,19 km (latest_consolidado.csv). La vía tiene 0 píxeles alertados. K tiene 4 píxeles, muestra 0,26 MW a 0,58 km y lo clasifica como cumbre.
- QUÉ PASA: en la primera semana, la vía calló alertas débiles unas 4 veces más seguido de lo que supone la calibración. Si ese ritmo sigue, la cota (i) dispara INVESTIGAR hacia el día 39 (re_cotas_poder_salida.txt, parte 4). Pero son 3 casos. Con ellos, el intervalo de 95 % de la tasa a 120 días va de 9,5 a 135 (la misma salida), y su borde inferior toca la tasa calibrada.
- Corrección: «4,9 veces» es la estimación puntual de la ventana más corta medida por día. Por pasada o con una noche más da entre 3,7 y 4,3. La evidencia de que la calibración se queda corta es marginal (p entre 0,02 y 0,05).
- Por qué gravedad 2: si la cota dispara, abre una investigación. No revierte ni cambia lo publicado.
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\tasa_por_pasada_452.py"`. Cordón Caulle, VIIRS NOAA-20, 2026-11-07 06:30 UTC.

### 453 y DEC-6 (los fundo en lo estadístico). Falsa alarma de las cotas con la incertidumbre de la tasa; la cota (ii) de VIIRS 750 sale de un caso. CONFIRMADO EN PARTE. Mi gravedad: 2

- ARCHIVO:LÍNEA: la regla, l. 88 a 98. La falsa alarma declarada coincide con experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt l. 84 y 85 (C-rad 0,059 y 0,056) y con experiments/_s176_v375e_adopcion/cotas_retrospectiva_v750_salida.txt, última línea (0,045 y 0,053). La cota (ii) de VIIRS 750 sale de «1 de 3218» (misma salida; la regla lo dice en l. 94: «1 de 3.218; se esperan 0,84»).
- SCRIPT:SALIDA: re_cotas_poder_salida.txt (re-corrido; Jeffreys): 0,282; 0,195; 0,122; 0,169. Por otro camino (cotas_sensibilidad_salida.txt), con tres distribuciones de la tasa y un camino sin prior:
  - VIIRS 375 (i): Gamma(k) 0,179; Jeffreys 0,282; Gamma(k+1) 0,396.
  - VIIRS 375 (ii): 0,140; 0,194; 0,259.
  - VIIRS 750 (i): 0,100; 0,123; 0,147.
  - VIIRS 750 (ii): 0,094; 0,168; 0,249.
  - Con la tasa en el borde superior de 80 % de Garwood: 0,877; 0,598; 0,259; 0,459.
  - Controles: con la tasa puntual, mi cuenta da lo que publica la regla (0,058; 0,057; 0,045; 0,053). En los estratos de un solo sumando, la binomial negativa exacta coincide con el Monte Carlo (0,101 contra 0,100; 0,168 contra 0,168).
- QUÉ PASA: las cuatro cotas salen de 1 a 9 casos crudos. Si la tasa no se toma como exacta, la falsa alarma en 120 días está entre 9 y 40 % según el modelo, no entre 4,5 y 5,9 %. El sentido es el mismo en todos los modelos: la falsa alarma queda sobre el 8 % que pide el método. La cota (ii) de VIIRS 750 descansa en 1 sola pasada (Isluga, 2026-07-15 05:36) y tiene poco poder: con el triple de la tasa calibrada dispara con probabilidad 0,46 (re_cotas_poder_salida.txt).
- Corrección: el «12 a 28 %» es el modelo de Jeffreys. Con otro modelo es 9 a 18 % o 15 a 40 %. Además, la regla ya avisa que no incluye esta incertidumbre (l. 98, TEXTO: «su Poisson no incluye la incertidumbre de esa tasa»). El defecto está declarado pero no cuantificado, y Nicolás selló D1 y D2 con esa frase a la vista.
- DEC-6, juzgada DEBILITADA: la confirmo como juicio (cota de un caso, poco poder, falsa alarma real de 9 a 25 %). Nicolás la aceptó («Sí a D2 a D7», regla l. 26) con «1 de 3.218» escrito en la tabla.
- CÓMO SE VE EN EL DASHBOARD: invisible. Una falsa alarma abre un aviso INVESTIGAR y no toca el tablero.
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\cotas_sensibilidad.py"`.

### 455. «Ninguna protegida perdida» en VIIRS descansa en Láscar y Chillán; seis volcanes sin ninguna protegida probada con la vía real. CONFIRMADO EN PARTE. Mi gravedad: 2

- SCRIPT:SALIDA: protegidas_por_volcan_salida.txt, que lee experiments/_s178_lectura/lectura.json en ff8a39972 (campos `sensores.<S>.lectura_b` y `osf.por_sensor`) y la semana de la sombra.
  - VIIRS 375: Láscar tiene 299 protegidas (26 de la retrospectiva F26-V y 273 de OSF). Cordón Caulle tiene 30 (28 de OSF y 2 de la sombra), Chillán 18 (todas de la sombra), Planchón-Peteroa 14 (OSF) e Isluga 2 (OSF). Sin ninguna: Lastarria, Tupungatito, Llaima, Villarrica, Copahue y Chaitén (6).
  - VIIRS 750: sin ninguna 7 volcanes, porque se suma Planchón-Peteroa.
  - Control: Láscar sale con protegidas en los dos campos, como debía.
- QUÉ PASA: lo probado son focos fuertes y persistentes (Láscar, Chillán) y algo de Cordón Caulle y Planchón-Peteroa. En Villarrica y Tupungatito, K de producción sí tuvo protegidas en la ventana O (4 y 4 en VIIRS 375 con tres plataformas; re_cotas_poder_salida.txt, parte 2), pero la vía real nunca corrió sobre ellas.
- Corrección: en VIIRS 750 son 7 volcanes, no 6. «Descansa en Láscar y Chillán» deja fuera a Cordón Caulle (30) y Planchón-Peteroa (14) en VIIRS 375.
- Por qué gravedad 2: después del encendido, la guardia vigila los 11 volcanes. Una pérdida en Villarrica dispara la reversión si cae dentro del plazo de 451.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\protegidas_por_volcan.py"`.

### 457. Revertir B1 con B2 ya adentro choca, y nadie ensayó esa resolución. CONFIRMADO EN PARTE: choca en 11 archivos, no en 9. Mi gravedad: 2

- SCRIPT:SALIDA: D:\vrp-trabajo\temporales\s179-audit\vb\mt_paso2_revert_B1_tras_B2.txt. Simulé el revert con `git merge-tree --write-tree` y un almacén de objetos privado (`GIT_OBJECT_DIRECTORY` en mi temporal, con el .git del repo como alternativo; no escribe en el repo). Pasos: (1) B1 (bbbe2068d) sobre el main donde mergea limpio (1028c78f8), lo que da el árbol f0eb9bbe; (2) revert de B1 = merge con base f0eb9bbe, «nuestro» = e68819484 (B2 sobre B1, la rama de #983) y «suyo» = 1028c78f8.
- Resultado: choca en 11 archivos: CLAUDE.md, docs/FICHA_SDA_VRP_CHILE.md, docs/MISSION.md y las 8 pruebas que nombra el cuerpo de #974. Los 5 perfiles mergean limpio. En el árbol resultante, `mirova_equivalent.yaml` queda sin la línea `enable_v375_codigo_mirova` (el flag vuelve a su valor por defecto) y conserva `enable_v750_codigo_mirova: true`.
- QUÉ PASA: lo que apaga la vía (el perfil) revierte limpio. Lo que choca son pruebas y documentos que #983 ajustó a mano: las 8 pruebas, más las marcas de CLAUDE.md y MISSION.md que #983 corrigió «sin conflicto pero a mano» (cuerpo de #983). Ese mismo día, la sesión tiene que resolver 11 archivos a mano, dejando VIIRS 375 apagado y VIIRS 750 encendido en las pruebas. La única prueba de revert que existe es la de perfiles (`test_revert_flag_v375_no_choca_s177.py` en la rama: `test_revertir_b1_con_b2_ya_en_main_no_choca` compara sólo `.yaml`).
- Corrección: 11 archivos, no 9. La cifra 9 viene del cuerpo de #974 y #983, escrito antes de corregir CLAUDE.md y MISSION.md. Mi simulación usa 1028c78f8 como main y no el main que habrá ese día.
- Por qué gravedad 2: la parte que protege al operador (apagar la vía) no choca.
- CÓMO SE VE EN EL DASHBOARD: invisible. Retrasa la reversión si la sesión se traba.
- CÓMO REPRODUCIRLO: los comandos están en la sección 6 de este informe.

### 460. La vía no escribe record en cerca del 5 % de las pasadas de VIIRS 375, y una alerta débil ahí no entra a ninguna cota. CONFIRMADO. Mi gravedad: 2

- ARCHIVO:LÍNEA: pipeline/process_viirs.py:773-774 y 781-782 (`if _rad is None: return None` e `if _rec is None: return None`: sin record). scripts/vigilancia_guardia_modis.py:252-254: (i) Muy Bajo exige `p["prod_pub"] is not None`. :318: sin record sólo cuenta protegidas. :280-294: (iii) cuenta las pasadas y no mira si MIROVA alertó. La regla dice que (iii) «Se informa y no dispara» (l. 84). Leído en 438a60a1e.
- SCRIPT:SALIDA: re_detalle_sombra_salida.txt (re-corrido): 11 de 223 (4,9 %). Casi todas son de borde de barrido (cenit de 56 a 70 grados, salvo dos de 11 y 32 grados). Por etiqueta de MIROVA: 4 negativos limpios y 7 sin información; ninguna con alerta de MIROVA. K publicó en 1 (Cordón Caulle 11-08 06:06, 0,58 MW, sin información de MIROVA). Con una noche más: 11 de 254 (4,3 %) y ninguna pasada con alerta y sin record de la vía (sim_ventana_16d78_salida.txt, detalle de A).
- QUÉ PASA: el hueco existe en el código, y la regla lo deja sin disparo a sabiendas. En 8 noches no se observó ningún caso real.
- CÓMO SE VE EN EL DASHBOARD: una pasada que falta.
- CÓMO REPRODUCIRLO: `python re_detalle_sombra.py` en la carpeta del verificador, parte (a).

### 463. D5 dice que los lectores sellados se conservan y se corren, pero el de V375-E no está en main, nadie lo corre y al encender B1 pierde su brazo K. CONFIRMADO. Mi gravedad: 2

- ARCHIVO:LÍNEA: la regla, l. 29 (D5, «Los lectores se conservan y se corren») y l. 44. docs/AUDIT_S175.md (37670d910) l. 216 (F2-209) y l. 272 (decisión 20). El lector es experiments/_s168/v375e_sombra/leer_sombra_v375e.py y no existe en 438a60a1e (`git cat-file -e` falla). El tag `s172-v375e-lector-resellado` no es ancestro de main. Ningún workflow de main lo nombra (grep en .github/workflows). Su uso (l. 25 del lector en el tag) pide `--data-k <carpeta de data/mirova_equivalent>`, y fija PERFIL_K = "mirova_equivalent" (l. 93) y el sha256 de `mirova_equivalent.yaml` (l. 76), archivo que B1 cambia.
- QUÉ PASA: con B1, `data/mirova_equivalent` de VIIRS 375 pasa a ser de la vía, y el lector se queda sin el lado K. Además, el cambio del perfil hace fallar su control de sello. Que le apunte a `data/guardia_k_viirs` sin romper sus controles es SOSPECHA (no lo probé).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git cat-file -e 438a60a1e:experiments/_s168/v375e_sombra/leer_sombra_v375e.py`; `git merge-base --is-ancestor s172-v375e-lector-resellado 438a60a1e`.

### 461. La regla pide revertir el mismo día UTC, pero la guardia corre en la práctica pasada la medianoche UTC. CONFIRMADO EN PARTE. Mi gravedad: 1

- ARCHIVO:LÍNEA: la regla, l. 68, TEXTO: «**Quién y cuándo**: la sesión que lee el issue, el mismo día UTC». .github/workflows/guardia-k-viirs.yml l. 16 a 19 (hora 19:35 UTC) y l. 7, TEXTO: «se revierte el encendido de ese sensor el mismo dia».
- Datos: D:\vrp-trabajo\temporales\s179-audit\insumos\runs_guardia-k-viirs.json y la salida del auditor api_guardia_runs_salida.txt (solo leída). Corridas programadas: creadas el 2026-11-10 02:21:36 UTC (6 h 47 min de atraso) y el 2026-11-11 00:12:12 UTC (4 h 37 min); n 2. El respaldo de la vigilancia a las 22:55 UTC también corrió tarde: 02:18 y 04:27 UTC (3,4 y 5,5 h; runs_vigilancia-guardia-viirs.json).
- QUÉ PASA: los atrasos son ciertos. Pero la l. 68 ata el plazo a la sesión que lee el aviso, no al día de la pasada, y eso se puede cumplir aunque la guardia corra a las 00:30 UTC. Lo que sí queda inconsistente es el comentario del workflow (l. 7) y el diseño (l. 52, «Revert de B el mismo día»): una pasada de las 05:00 UTC del día D se compara recién el día D+1.
- CÓMO SE VE EN EL DASHBOARD: la vía mostraría la pasada callada unas 20 horas más antes de que alguien lo sepa.

### 458. #974 y #983 chocan hoy con main en la ficha; su CI verde es anterior a #982 y #984; la numeración de la ficha está escrita de distintas maneras. CONFIRMADO. Mi gravedad: 1

- SCRIPT:SALIDA: D:\vrp-trabajo\temporales\s179-audit\vb\mt_*_sobre_438a60a1e.txt y mt_*_sobre_origin_main.txt. Las tres puntas (bbbe2068d, e68819484, 9d3e63015) chocan sólo en docs/FICHA_SDA_VRP_CHILE.md, contra 438a60a1e y contra 16d78e3e0.
- CI: #974 pasó a las 02:55 UTC y #983 a las 10:31 UTC del 2026-11-10 (insumos pr_974.json y pr_983.json). #982 entró a las 11:25:49 UTC y #984 a las 17:00:23 UTC (`git log -1 --format=%cI a9bd0313b 438a60a1e`).
- Numeración: la ficha de main (438a60a1e) va en v1.22 (#984). La de #974 dice v1.21. La de #983 dice v1.22 (B1) y v1.23 (B2). La bitácora en l. 582 dice v1.22 y v1.23, y en l. 576, que es más nueva, dice v1.23 y v1.24. Son tres numeraciones.
- CÓMO SE VE EN EL DASHBOARD: invisible. Es la ficha pública de transparencia (CPLT), no una decisión de alerta.

### DEC-14. «Quita los 3» se aplicó más ancho que lo pedido. CONFIRMADO EN PARTE. Mi gravedad: 1

- ARCHIVO:LÍNEA: tasks/LOOP_OBJETIVOS.md l. 593 (0472cd95e): «quita los 3» se refiere al aviso K (#976), al aviso de la vía de MODIS y al del cese de Suomi NPP. frontend/cambio_detector.js:284-293 quita el aviso de texto de las tres vías (MODIS, VIIRS 375 y VIIRS 750); los dos de VIIRS todavía no se mostraban.
- Matiz: el cuerpo de #984 lo dijo antes del merge, TEXTO: «`notarRecords` ya no llama a `insertarAvisoVia` (avisos `aviso-cambio-via-modis`, `-v375`, `-v750`)». Nicolás contestó «Mergea #984» (l. 576). La ampliación quedó a la vista, pero no hubo una decisión expresa sobre los avisos de VIIRS. Eso choca con la decisión 4 del diseño (l. 60) y alimenta 456.

### DEC-19. El veredicto de la retrospectiva para VIIRS 750 (fila 4, DECIDE NICOLÁS) no tiene frase de Nicolás. CONFIRMADO. Mi gravedad: 2

- ARCHIVO:LÍNEA: lectura.json (ff8a39972) en `sensores.VIIRS750` tiene fila 4, veredicto «DECIDE NICOLÁS» y motivos `["v750a_no_sellado", "regla del sensor"]`. tasks/BLOQUE_ARRANQUE_S179.md l. 19 y l. 39 (0472cd95e) la siguen dando como pendiente («después de #974 / esperar más evidencia»). En las entradas de S178 de la bitácora (l. 570 a 680) no hay ninguna frase de Nicolás sobre esa fila.
- Matiz: con D5 sellado, V750-A deja de decidir. Así cae uno de los dos motivos, pero el otro («regla del sensor») sigue.

## 4. Hallazgos propios

### VB-01. La condición «guardia K de VIIRS al menos tres noches» descansa en una sola ejecución, y esa ejecución terminó en falla

- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `git log origin/main -- data/guardia_k_viirs` muestra que todo lo anterior al 11-11 son 11 commits entre las 01:25 y las 01:49 UTC del 2026-11-10. Son de la ejecución manual 42734558894 (creada a las 01:16, conclusión «failure»; insumos runs_guardia-k-viirs.json). La corrida programada 42742205624 (02:21 UTC) falló en los 11 trabajos, todos en el paso «Revisar que salio K de los dos VIIRS» (D:\vrp-trabajo\temporales\s179-audit\vb\run_42742205624.json), y no escribió datos. La primera programada en verde es la 42929475700, del 2026-11-11 a las 00:12 UTC. La regla, l. 132, da el nulo por comprobado («223 y 220 pares, 0 distintos, guardia del 11-03 al 11-09»), y la bitácora (S178) dice «La guardia K de VIIRS cuenta noches desde su corrida de hoy».
- QUÉ PASA: los datos de la guardia del 11-03 al 11-09 salen de una sola ejecución que procesó 8 fechas hacia atrás. Eso mide bien el nulo de una corrida, pero no muestra que el workflow corra sano noche a noche. Al cierre de 438a60a1e había 0 corridas programadas en verde. Hoy hay 1.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `gh run view 42742205624 --repo MendozaVolcanic/VRP-chile --json jobs`.
- CONFIANZA: CONFIRMADO en los hechos. La causa de la falla es SOSPECHA: puede ser el «falso rojo» al cruzar la medianoche UTC que #977 corrigió (#977 entró a las 09:26 UTC del 11-10, después de la corrida fallida). No leí el log.
- GRAVEDAD: 2.

## 5. SEGUIMIENTOS (fuera de mi eje)

- El vigilante de la guardia K de VIIRS carga la referencia sin respaldo ni histórico (`vigilancia_guardia_viirs.py:152`), y los scripts del auditor la cargan con los dos. En ventanas posteriores a abril no cambia nada, porque mis re-corridas dan lo mismo. Confianza: SOSPECHA de que no importa. Gravedad 1.
- La vía de VIIRS 375 calla Cordón Caulle 2026-11-07 06:30 (MIROVA 0,36 MW a 8,19 km según la tabla y a 3,78 km según el OCR), mientras K lo ve a 0,58 km como cumbre. Que MIROVA y K ubiquen el foco tan distinto merece mirarse en el eje de posición. Confianza: CONFIRMADO el dato, SOSPECHA la causa.

## 6. VERIFICADO LIMPIO

- Las cotas del vigilante son las de la regla sellada: `COTAS` = 14/17 y 12/2 (vigilancia_guardia_viirs.py:73-74) contra la regla l. 92 a 94. Vara: la tabla de la regla en 438a60a1e.
- El nulo de la guardia contra producción da 0 publicaciones distintas en 223 y 220 pares, con VRP mostrado idéntico (re_cotas_poder_salida.txt, parte 3; y magnitud_via_k: 1,0000 exacto en n 84 y n 28). Vara: el predicado del tablero con node (`banco_paridad.cargar_nuestros`).
- Los controles del simulacro: el brazo mudo da 20 y 19 candidatas a reversión; el que siempre publica da sobre-publicación 93 de 98 y 161 de 164; el de K contra K da 0 y 0 con n mayor que 0 (re_sim_vigilancia_salida.txt). Mi ventana larga reproduce lo mismo.
- La falsa alarma declarada en la regla (5,9; 5,6; 4,5; 5,3 %) es la de las salidas selladas (cotas_v375_con_retro_salida.txt l. 84 y 85; cotas_retrospectiva_v750_salida.txt, última línea), y mi Poisson la reproduce.
- Los perfiles: en mi simulación, el revert de B1 tras B2 mergea limpio en los 5 perfiles.
- Comandos de la simulación de merges, con objetos privados:
  `export GIT_OBJECT_DIRECTORY=D:/vrp-trabajo/temporales/s179-audit/vb/objs GIT_ALTERNATE_OBJECT_DIRECTORIES="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.git/objects"; git merge-tree --write-tree --name-only 1028c78f8 bbbe2068d` (árbol f0eb9bbe), y después `git merge-tree --write-tree --name-only --merge-base=f0eb9bbe e68819484 1028c78f8`.

## 7. SIN DATO

- La causa de las dos corridas fallidas de la guardia (no leí sus logs).
- Si el lector de V375-E aceptaría `data/guardia_k_viirs` como brazo K sin romper sus controles.
- La resolución real de los 11 conflictos del revert: no la ensayé, sólo conté los conflictos.
- El tablero en el navegador con records de la vía: no lo abrí.

## 8. FUERA DE ALCANCE

MODIS (salvo el código que comparte el vigilante); la retrospectiva de MODIS; la vara MATLAB de B2 (#980); el reemplazo de la historia (#981); el porqué físico de las tres Muy Bajo calladas.

## Archivos de esta verificación (todos en C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb\)

caminos.md; re_sim_vigilancia.py y su salida; re_cotas_poder.py y su salida; re_detalle_sombra.py y su salida (copias del auditor que escriben aquí); sim_ventana_16d78.py y su salida; magnitud_via_k.py y sus dos salidas; cotas_sensibilidad.py y su salida; tasa_por_pasada_452.py y su salida; protegidas_por_volcan.py y su salida; hallazgos.csv; este INFORME_VB.md.
