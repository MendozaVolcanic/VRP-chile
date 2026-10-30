# Verificador limpio del lector de la sombra de V375-E (arreglos de S169)

CARPETA: D:\vrp-trabajo\temporales\s169_ver_lector\ (scripts en la raíz, salidas en salidas\, hallazgos.csv, caminos.md)
- Fecha y hora del servidor: 2026-10-30, inicio 03:06 UTC, cierre 03:35 UTC (`date -u`).
- Commit medido: `983f6f28d` (rama claude/s169-v375e-lector), árbol en `arbol\` (git archive; más `experiments/_s159`, `_s165_v375_via`, `_s158_audit_r2/oraculo` y `volcanoes.yaml`, que el lector necesita y el árbol no traía; y un `.git` vacío con alternates al repo, sólo para que `git diff c42ee0eb7 ...` resuelva).
- Modelo: Sonnet 5.5 (claude-sonnet-5-5), esfuerzo bajo. Contexto limpio: `caminos.md` fijado antes de abrir nada citado (sha256 al final del archivo, 03:06:32 UTC). No abrí el INFORME.md del autor hasta después de fijarlo; lo leí para contrastar la comprobación en rojo.
- NO miré: datos de data/sombra_codigo_mirova/ ni de la ventana P (no hay); el nulo de 111 mutaciones (no se corre); el cenit del record de K contra datos reales; la red; los 4 .py de pipeline/ que no entran al cierre de imports.

## En una pantalla
- Veredicto global: **SELLABLE CON CAMBIOS**. Un hallazgo de gravedad 3 (VL169-01): "se lee una sola vez" vale por nombre de corte y por carpeta, no por ventana; con otra referencia N se mueve y sale una segunda lectura (reproducido).
- Gravedad 2: el nulo cuenta como ATRAPADA a una mutación que sólo hace caer una sección (VL169-02); S8 marca de más (todo `pipeline/`, 35 commits en octubre) y no mira `volcanoes.yaml` ni `scripts/run_pipeline.py` (VL169-03 y 04, respuesta a B7); S8 y la batería dependen de objetos git (VL169-05); la población depende de la variable VRP_PROFILE y de módulos sin sha (VL169-06); S9 mide la tabla de cualquier sensor (VL169-07).
- Batería: 189 de 190 en mi árbol; la única falla es ambiental (sin .git); con alternates las dos aserciones de `diff_git` pasan, o sea 190 de 190 equivalente.
- Nulo de 13 h: **conviene arreglar antes de correrlo** (los arreglos de VL169-01, 02, 03, 05 y 06 tocan lector o script y las mutaciones se escriben sobre esas líneas).
- B2: los desvíos de S8 y S0 son sanos. B6: perfil comprobado en código y test; cenit SIN DATO.

## Veredictos por afirmación
| afirmación | veredicto | gravedad |
|---|---|---|
| B1 VS168-01 cerrado | CONFIRMADO EN PARTE. `--desde` igual, corte = primera noche de la parada, recorte a N, antes de N sólo controles (rc 5), nombre `lectura_sombra_corte_<N>`: reproducido. NO se cumple "se escribe una sola vez y nunca se sobrescribe" a nivel de ventana (VL169-01); y con un control caído antes de la parada sale 3 sin contadores (VL169-08) | 3 |
| B2 VS168-02 a 08 | CONFIRMADO: cada uno tiene texto en §11 y código que coinciden. Desvíos S8 y S0: sanos | 1 |
| B3 texto y código | CONFIRMADO EN PARTE: coinciden salvo VL169-01, VL169-08 y §11.10 con cifras viejas (seguimiento 1) | 1 |
| B4 batería 190 de 190 | CONFIRMADO EN PARTE: 189 de 190 en mi árbol (falla ambiental, VL169-05); la comprobación en rojo es por grupos (VL169-09) | 1 |
| B5 nulo | CONFIRMADO EN PARTE: cubre las reglas nuevas (N01 a N39 una por una; 111 únicas, 0 no-op) pero el criterio de ATRAPADA no excluye la caída (VL169-02). V04 sí es equivalente y está declarada antes de correr, en §11.10 (no en el script, VL169-10) | 2 |
| B6 perfil y cenit | CONFIRMADO el perfil (código y test de punta a punta, sin correrlo); cenit SIN DATO | 1 |
| B7 (coordinadora) | CONFIRMADO: S8 marcaría régimen por un cambio de `roi_v750` que VIIRS 375 no lee; ver VL169-03 | 2 |

## Hallazgos (ordenados por gravedad)

### VL169-01: "una sola vez" es por nombre de corte y carpeta, no por ventana
- ARCHIVO:LÍNEA: experiments/_s168/v375e_sombra/leer_sombra_v375e.py, `main`, bloque `n_pre` y `ya = Path(a.dir_salida) / f"lectura_sombra_corte_{n_pre}.txt"`, y `base = f"lectura_sombra_corte_{corte}"`. SCRIPT:SALIDA probe_b1.py y probe_b1b.py: salidas\probe_b1_salida.txt, salidas\probe_b1b_salida.txt.
- QUÉ PASA: lo que decide es la noche N en que se juntan 30 noches y 40 alertas, y N depende de las etiquetas, que dependen de la referencia de MIROVA. El guardia sólo mira si existe el archivo de ese N en esa carpeta. Con los mismos insumos y otra `--dir-salida` sale una segunda lectura (T_c: rc 0 y segundo archivo; en la misma carpeta, T_c2: rc 2). Con una referencia distinta N se mueve y la segunda lectura se escribe al lado de la primera, en la misma carpeta (probe_b1b T_d0: corte 2026-11-11, rc 0; T_d1, 7 alertas bajas pasadas a RUTINA: aparece también `lectura_sombra_corte_2026-11-12`, rc 0).
- CÓMO SE VE EN EL DASHBOARD: invisible (es el protocolo de la decisión de adoptar la vía).
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -I probe_b1.py` y `probe_b1b.py` en esta carpeta (escena sintética de la batería, parada de prueba 8 noches y 12 alertas para T_d).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 3: es lo que VS168-01 quería cerrar (mirar un resultado y repetir con otro insumo hasta que guste). Quien corre tiene que cambiar un insumo a propósito y el sha de cada insumo queda escrito, así que es auditable; pero el lector no lo impide y el texto no lo prohíbe fuera de "se baja una sola vez" (§11.1).
- Arreglo propuesto: negarse (rc 2) si existe cualquier `lectura_sombra_corte_*` en la carpeta; registro append-only de la ventana (no de N) que se commitea; y decir en §11.8 que una segunda lectura con otra referencia exige pre-registro nuevo.

### VL169-02: el nulo cuenta una caída como ATRAPADA
- ARCHIVO:LÍNEA: experiments/_s168/v375e_sombra/mutar_sombra.py `correr` (la función que devuelve "ATRAPADA" si exit 1 y línea RESULTADO) y probar_sombra.py `seccion` (l. 77 a 83). SCRIPT:SALIDA crash_vs_asercion.py: salidas\crash_vs_asercion_salida.txt; datos reales: experiments/_s169/v375e_lector_arreglos/rojo_D.txt (líneas «sección ... sin excepción TypeError(...)» y «KeyError(('VIA', 'radiante'))»).
- QUÉ PASA: `seccion()` convierte cualquier excepción en una aserción FALLA ("sección «x» sin excepción") para que la batería no se caiga. `correr()` declara ATRAPADA toda corrida con exit 1 y línea RESULTADO. Una mutación que sólo rompe el lector con una excepción sale ATRAPADA, contra la definición del proyecto (al menos una aserción por valor y ninguna caída) y contra el docstring del script ("una que hace caer la batería con una excepción es CAÍDA y no cuenta"). Sólo la caída en la importación sigue siendo CAÍDA.
- CÓMO SE VE EN EL DASHBOARD: invisible; infla la cifra del nulo.
- CÓMO REPRODUCIRLO: `python -I crash_vs_asercion.py` (crash en sección: exit 1; aserción falsa: exit 1, idéntico).
- CONFIANZA: CONFIRMADO. GRAVEDAD 2 (el nulo es la prueba de que las aserciones ven las reglas; con este criterio no lo prueba).
- Arreglo: en `correr`, ATRAPADA sólo si hay al menos un FALLA que no empiece con "sección «"; si todos son de sección, CAÍDA. Hacerlo antes de correr las 13 horas.

### VL169-03: S8 compara todo `pipeline/` y marca por cambios que VIIRS 375 no lee (respuesta a B7)
- ARCHIVO:LÍNEA: leer_sombra_v375e.py `diff_git` (git diff --name-only BASE sha -- pipeline/) y `control_s8`. SCRIPT:SALIDA cierre_imports.py: salidas\cierre_imports_salida.txt.
- QUÉ PASA (B7): sí, un cambio de `roi_v750` en pipeline/grillas_mirova.yaml hace que S8 marque régimen y lleve (b), (c), (d) a DECIDE NICOLAS, y VIIRS 375 no lo lee. `FAMILIAS["VIIRS375"]` tiene `roi1_half_m`, así que `calcular_vrp_granulo` arma la caja con `caja_v375` (mirova_v750_codigo.py, la rama `caja_roi(tipo_roi or g.get("roi", ...))` sólo corre sin `roi1_half_m`); su `clave_roi` es "roi_v375", que el yaml no trae; y `roi_v750` y `roi_modis` no aparecen en ningún otro .py de pipeline/ ni de scripts/ (grep). En cambio el yaml SÍ lo lee la vía de VIIRS 375 por `epsg, x0, y0, centro_lat, centro_lon` (`grilla_del_volcan`), así que excluir el archivo entero abriría un hueco real.
  Por archivo .py no hay nada que excluir: el cierre estático de imports desde process_viirs.py, store.py y run_pipeline.py alcanza todos los .py de pipeline/ salvo `audit_metrics.py`, `detect_tirvolch.py`, `mirova_csv_loader.py` y `__init__.py`. Lo que sobra son los ~100 YAML de `pipeline/profiles/` (sólo cuentan `mirova_equivalent.yaml` y `sombra_codigo_mirova.yaml`, que hereda del primero), los comentarios y docstrings, y las claves ROI. Tasa base: 35 commits que tocan `pipeline/` en origin/main desde 2026-10-01 (20 desde el 15-oct), casi todos de otra vía o con banderas apagadas; en una ventana de 30 noches la marca es casi segura.
- CÓMO SE VE EN EL DASHBOARD: invisible; el paquete no saldría CUMPLE y todo iría a Nicolás con una lista de archivos.
- CÓMO REPRODUCIRLO: `git -C <repo> log origin/main --since=2026-10-01 --format=%h -- pipeline/ | wc -l` (35); `python -I cierre_imports.py`.
- CONFIANZA: CONFIRMADO (lecturas y conteos); no medí el efecto de cada commit.
- GRAVEDAD 2 (sobre-marca: no puede producir un CUMPLE falso, sí volver casi inalcanzable el CUMPLE automático).
- Cómo debería comparar S8 sin abrir hueco (propuesta; la decide quien orquesta): (1) .py de pipeline/: igualdad de AST (ast.dump sin docstrings) entre base y sha, de modo que comentarios y FICHA no marquen; cualquier otra diferencia marca. No intentar función por función: mirova_v750_codigo.py comparte `procesar_grilla` y helpers con V750 y MODIS; un cambio ahí puede ser de la vía de 375 y descartarlo sería el hueco. (2) `pipeline/profiles/`: sólo `mirova_equivalent.yaml` y `sombra_codigo_mirova.yaml` (y la cadena `extends`); los demás no los carga ni K ni la vía. (3) `pipeline/grillas_mirova.yaml`: parsear base y sha, borrar solamente `roi_v750` y `roi_modis` de cada volcán y comparar el resto por igualdad; archivo ilegible, volcán nuevo o clave nueva marcan (falla cerrada). (4) Excluir `audit_metrics.py`, `detect_tirvolch.py` y `mirova_csv_loader.py` sólo si Nicolás acepta el cierre estático (una importación dinámica no queda cubierta). (5) Agregar lo que hoy falta (VL169-04). Lo que no se abre: un cambio real de la vía de 375 en un .py, en x0/y0/centro/epsg o en el perfil sigue marcando; si el código pasara a leer `roi_v750` para 375, sería un cambio de .py y marcaría. Residuo honesto: un cambio en código compartido pero ajeno (MODIS o V750 dentro de mirova_v750_codigo.py) seguirá marcando y Nicolás lo descarta mirando el diff.

### VL169-04: S8 no compara lo que la vía y K también leen fuera de `pipeline/`
- ARCHIVO:LÍNEA: pipeline/mirova_v750_codigo.py (`_volcanes_yaml`, `parents[1] / "volcanoes.yaml"`), scripts/run_pipeline.py l. 92 (VOLCANOES_FILE) y .github/workflows/sombra-codigo-mirova.yml l. 122 (argumentos de run_pipeline.py). SCRIPT:SALIDA cierre_imports.py, sección "lecturas de archivos".
- QUÉ PASA: S8 sólo diferencia `pipeline/`. `volcanoes.yaml` (radio interior, coordenadas, radio) alimenta la clase summit/far de K y de la vía, y `scripts/run_pipeline.py` es el llamador que arma los argumentos de los procesadores (A6). Un cambio ahí cambia lo que la ventana mide sin marca. VS168-04 pidió cubrir pipeline/, profiles/ e index.html; el autor cubrió pipeline/ y index.html (S0).
- CÓMO SE VE EN EL DASHBOARD: una pasada pasaría de summit a far, o al revés, y la lectura mezclaría dos detectores sin aviso.
- CÓMO REPRODUCIRLO: `git -C <repo> diff --name-only c42ee0eb7 <sha> -- volcanoes.yaml scripts/run_pipeline.py .github/workflows/sombra-codigo-mirova.yml`.
- CONFIANZA: CONFIRMADO que se leen; SOSPECHA el efecto (no medí un cambio real). GRAVEDAD 2.
- Arreglo: agregarlos al pathspec de `diff_git` (con igualdad de AST para el .py).

### VL169-05: S8 y la batería dependen de que git tenga los objetos; el texto no lo dice
- ARCHIVO:LÍNEA: leer_sombra_v375e.py `diff_git` y `BASE_REGIMEN`; probar_sombra.py l. 403 a 405. SCRIPT:SALIDA salidas\bateria_190.txt (FALLA "diff_git ve que c42ee0eb7 contra sí mismo..."), salidas\git_check_salida.txt.
- QUÉ PASA: `c42ee0eb7` (#926) no es ancestro de `983f6f28d` (`git merge-base --is-ancestor`: no; el perfil sombra_codigo_mirova.yaml y el test s167 no están en el árbol medido y sí en origin/main). En un checkout sin esos objetos `git diff` falla, S8 trata todo sha como "git no lo resuelve" y la lectura sale marcada siempre. Sin .git mi corrida dio 189 de 190; con alternates, `diff_git(base, base) == []` y `diff_git(base, "0"*40) is None` pasan. Además `scripts/auto_audit_weekly.py` ya difiere entre el sha sellado en S0 (3afd3e65...) y origin/main (9c4da61e...; commits 25fcb9c8e y b2ae7d40f del 2026-10-28): si el tag se corta sobre main, S0 cae (falla cerrada, bien); si se corta sobre el linaje del lector, el checkout no tiene los objetos de main hasta hacer `git fetch`.
- CÓMO SE VE EN EL DASHBOARD: invisible; la lectura saldría marcada o no legible por una causa de procedimiento.
- CÓMO REPRODUCIRLO: correr probar_sombra.py en un árbol sin .git (189 de 190).
- CONFIANZA: CONFIRMADO. GRAVEDAD 2 (puede llevar a "arreglar" el procedimiento después de ver).
- Arreglo: escribir en §11.4 que el checkout del tag haya hecho `git fetch origin` y contenga c42ee0eb7 y los sha de los records, y decidir ahora el linaje del tag (y re-sellar el sha de auto_audit_weekly.py si es sobre main).

### VL169-06: la población depende de módulos y de una variable de entorno que S0 no identifica
- ARCHIVO:LÍNEA: scripts/banco_paridad.py l. 60 (`os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")`), scripts/auto_audit_weekly.py l. 45 a 47 y 295 a 300 (`_reject_daytime`, `ENABLE_DAYTIME_MODIS`, `flag_viirs_diurno()`), pipeline/store.py l. 203 a 224, pipeline/diurno.py. SCRIPT:SALIDA imports_check.py: imports_check_salida.txt; env_check.py: salidas\env_check_salida.txt.
- QUÉ PASA: al ejecutar el lector se cargan, sin sha en S0, `pipeline/store.py`, `pipeline/profile.py`, `pipeline/f5_core.py`, `brazos.py`, `mirova_port.py` y `mirova_v750_r2.py`. Qué es de día y qué de noche lo decide `store._reject_daytime` con el flag que lee `pipeline.profile`, y `setdefault` deja ganar a la variable VRP_PROFILE del shell. Con `VRP_PROFILE=_s151_ab_diurno_on`, S0 sale OK y `ENABLE_DAYTIME_VIIRS` pasa de False a True.
- CÓMO SE VE EN EL DASHBOARD: no se vería; cambiaría qué filas diurnas de la referencia o de los records entran a la población.
- CÓMO REPRODUCIRLO: `VRP_PROFILE=_s151_ab_diurno_on python -I env_check.py` y la misma sin la variable.
- CONFIANZA: CONFIRMADO el mecanismo; SOSPECHA el efecto en datos (los records de K de producción no traen filas diurnas; la referencia sí podría). SOSPECHA que `brazos`, `mirova_port` y `mirova_v750_r2` no influyan en la ruta de la sombra. GRAVEDAD 2 (es el camino "variable de entorno" que pidió B1; A89).
- Arreglo: que `main` falle si VRP_PROFILE está definida y no es `mirova_equivalent`, y agregar a S0 el sha de store.py, profile.py y profiles/mirova_equivalent.yaml.

### VL169-07: S9 mide la tabla de cualquier sensor y volcán
- ARCHIVO:LÍNEA: leer_sombra_v375e.py `main`: `ultima_tabla = max((f["fecha_utc"] for f in filas_ref if f.get("source") == "CONS"), default=None)`. SCRIPT:SALIDA probe_b1b.py, T_s9a: salidas\probe_b1b_salida.txt.
- QUÉ PASA: el rezago de 2 días se mide con la fila más nueva de toda la tabla (MODIS, VIIRS 750, otros volcanes). Si el scraper sigue escribiendo MODIS pero atrasó VIIRS 375, S9 pasa y una pasada puede quedar `neg_limpio` porque su alerta no llegó. En T_s9a `ultima_tabla` salió "2026-12-08 05:00:10", una fila de MODIS. Mi control T_s9b no fue válido (había filas de VIIRS 375 posteriores al corte): vale como prueba del código, no del efecto.
- CÓMO SE VE: invisible. CONFIANZA: CONFIRMADO (código y valor); SOSPECHA que ocurra en la ventana. GRAVEDAD 2.
- Arreglo: filtrar `ultima_tabla` por sensor VIIRS 375 y por los volcanes con record.

### VL169-08: antes de la parada, con un control caído, sale 3 y sin contadores
- ARCHIVO:LÍNEA: leer_sombra_v375e.py `analizar` (`if fallas: return {...}` antes de `out["parada"] = cont`) y `main` (`cod = {"decide": 0, "provisional": 5, "no_legible": 3}`). SCRIPT:SALIDA probe_b1b.py, T_i: salidas\probe_b1b_salida.txt.
- QUÉ PASA: con 2 noches y umbrales reales sale rc 3, "S6 CAE...", sin los contadores de noches y alertas que §11.8 promete antes de la parada. S6 exige 5 pares en 3 noches, así que las primeras noches de la ventana saldrán siempre "LECTURA NO LEGIBLE", que se lee como falla del instrumento. B1 esperaba rc 5 antes de la parada.
- CÓMO SE VE: el operador ve "no legible" los primeros días y presión por "arreglar". CONFIANZA: CONFIRMADO. GRAVEDAD 1.
- Arreglo: imprimir los contadores también cuando cae un control antes de la parada, o escribir en §11.8 que rc 3 puede preceder a rc 5.

### VL169-09: la comprobación en rojo es por grupos
- ARCHIVO:LÍNEA: experiments/_s169/v375e_lector_arreglos/ver_en_rojo.py (GRUPOS, ESPERA) y rojo_A.txt a rojo_E.txt.
- QUÉ PASA: cada grupo rompe 2 a 17 reglas a la vez y da EN ROJO si alguna aserción con el prefijo esperado falla. Las aserciones de `main()` se comparten entre roturas (rojo_D: N04 sola descompone unas 20 aserciones de main; esa corrida terminó en 134 de 180 por secciones abortadas) y una rotura puede encender la aserción de otra. El autor ya halló dos casos así (N16, V06). Lo cierra el nulo, no este script; hasta que corra, "cada regla nueva tiene una aserción que la ve en rojo" está probado sólo en sentido débil.
- CONFIANZA: CONFIRMADO (lectura de las salidas). GRAVEDAD 1.

### VL169-10: V04 equivalente sin marca en el script
- ARCHIVO:LÍNEA: mutar_sombra.py, entrada ("V04", ...); declaración en PREREGISTRO_E.md §11.10 y en el INFORME del autor.
- QUÉ PASA: la equivalencia es correcta (evaluar.py l. 129 a 141 devuelve sólo SIN SUSTRATO, GANA, PIERDE, BLOQUEA, EMPATE; el conjunto que (b) acepta para P2, {GANA, EMPATE, SIN SUSTRATO}, es el complemento del que rechaza para P2-L, {PIERDE, BLOQUEA}; cruzarlos da lo mismo) y está declarada antes de correr, en el texto. El script no la marca, así que la línea final dirá "110 de 111" sin explicarlo. CONFIANZA: CONFIRMADO. GRAVEDAD 1.

## SEGUIMIENTOS (fuera de mi eje o menores)
1. PREREGISTRO_E.md §11.10, primeras viñetas: siguen diciendo "104 de 104" y "55 mutaciones... pendiente"; la viñeta de S169 dice 190 y 111 (confianza alta).
2. `main()` no tiene guardia al escribir la lectura que decide (sólo el chequeo de `ya` antes de analizar): dos corridas simultáneas podrían pisar el archivo (SOSPECHA, gravedad 1).
3. No hay instantánea diaria de la referencia dentro de la ventana: filas que el scraper pierda antes de la única descarga no se ven (VS168-05 queda cerrado por S9 y por "una vez", no por captura). SOSPECHA, gravedad 1.
4. Con la parada alcanzada y un control caído, el nombre del archivo `controles_sombra_<N>_...` revela N (no la lectura). Gravedad 1.
5. `--hasta` con fecha sin ceros ("2026-11-5") compara como texto y abarca meses completos; inocuo para la decisión (la parada manda), confuso. Gravedad 1.
6. El tag del lector se corta desde el linaje de `983f6f28d`, que no contiene `pipeline/profiles/sombra_codigo_mirova.yaml` ni el test s167: el checkout del lector no es un checkout de la sombra. Bien para el lector; hay que tenerlo presente al decir "desde un checkout del tag".

## VERIFICADO LIMPIO (comando y vara)
- Los 12 sha de S0 coinciden con los archivos del árbol, y los 4 de SHA_DEPS con el tag `s168-v375e-cuerpo-sellado` (`sha_check.py`; control positivo: probar_sombra.py no coincide). Vara: el tag y el árbol.
- §1 a §10 intactos: las primeras 701 líneas de PREREGISTRO_E.md del tag sellado son idénticas a las de 983f6f28d (diff vacío salvo una línea en blanco) y las primeras 727 sin CR tienen el mismo sha256 (5af76cd5...) en 3f7e8814c y 983f6f28d. Vara: el tag.
- Camino a una lectura antes de la parada: no encontré ninguno. `--hasta` anterior a N da rc 5 (T_h); umbrales reales con 25 noches dan rc 5 sin lectura (T_a, control: T_b con parada de prueba sí escribe lectura); `--desde` distinto de 2026-11-03 da rc 3 sin población (T_e y batería); no hay `--json`, `--modo` ni argumento de prueba en la CLI; `PARADA_NOCHES` y `PARADA_ALERTAS` sólo se tocan desde la batería y una aserción fija 30 y 40. Las variables de entorno afectan sólo por VL169-06. Vara: texto §11.8 y código de salida.
- Recorte a N: con la parada de prueba el lector lee sólo hasta N y lo dice (T_b y batería). Las pasadas posteriores a N no entran a población, controles ni lecturas (leí `analizar`, `main` y `alertas_sin_record`).
- `noche_parada`: primera noche con 30 noches y 40 alertas, lo que llegue último (aserciones de la batería con los umbrales reales; leí la función). Noche = fecha UTC (`banco_paridad.py` l. 284), coherente con el filtro de la referencia por fecha.
- B2 uno por uno: VS168-02 (MOTIVO, `reporte_controles(detalle)`, `para_json`), 03 (`veta` suma `sin_dato_prot` con K publica), 04 (S0 con 8 archivos, S8, `--commit` obligatorio), 05 (S9 y una vez), 06 (`estado_c_sombra`), 07 (`controles_curva(..., "K")` vía `paquete` y `cae_k`), 08 (S6 exige sustrato; aserciones por valor): texto y código coinciden. VS168-09 a 14 también coinciden (borde mixto, `TOL_S4_KM`, S10, informes, brazos que informan sin estado, `--commit`).
- Desvío S8 (CUMPLE de (b), (c), (d) a DECIDE NICOLAS): sano frente al §5.4 y al §9.7 sellados. Un CUMPLE nunca se vuelve NO CUMPLE ni al revés; sólo pasa a DECIDE NICOLAS, que es lo que §9.7 manda para "las salidas que el §5.4 no previó" y el mismo trato que la marca A104 sobre (c). Un NO CUMPLE con régimen mezclado se mantiene (conservador). Matiz: con la sobre-marca de VL169-03 el CUMPLE automático casi no será alcanzable.
- Desvío S0 (sha de frontend/index.html): sano; es el predicado que define "publica" (`banco_paridad.HTML`). Hoy index.html es idéntico en origin/main y en el lector.
- (c) SIN SUSTRATO a DECIDE NICOLAS en la sombra: sano; la última frase del §5.4 lo prevé.
- Nulo estático (`nulo_estatico.py`): 111 mutaciones, 111 ids únicos, `comprobar_unicas()` vacío (control positivo: una mutación falsa aparece), 0 no-op. Cubre N01 a N39 (VS168-01 a 14), V01 a V14 y las 55 previas. Vara: una por regla de §11.11.
- B6: `pipeline/profiles/sombra_codigo_mirova.yaml` en origin/main declara `profile: sombra_codigo_mirova`; `pipeline/profile.py` l. 69 y 76 fijan `PROFILE_NAME`; `pipeline/store.py` l. 89 a 94 y 549 escriben `regimen.perfil`; el workflow l. 122 corre `run_pipeline.py --profile sombra_codigo_mirova`; tests/test_sombra_codigo_mirova_s167.py l. 299 aserta `r["regimen"]["perfil"] == PERFIL` de punta a punta (no corrí ese test). K: `mirova_equivalent`. Vara: código de origin/main.

## SIN DATO
- Cenit: el record de K trae `sensor_zenith_deg` (`scan_geometry.observation_geometry`, píxel más cercano al punto reportado; `evaluar.armar` lo toma con `o.get("z")`), pero no puedo medir sin datos de la ventana P si coincide con el `geometria_centro` del run de la retrospectiva.
- Efecto en datos reales de VL169-03, 04, 06 y 07.
- Que `brazos.py`, `mirova_port.py` y `mirova_v750_r2.py` no influyan en la ruta de la sombra (sólo vi que se cargan).
- El test s167 de punta a punta no lo corrí.

## FUERA DE ALCANCE
Retrospectiva, lectores de MODIS y VIIRS 750, contenido de data/, la decisión de adoptar (A45).

## ¿Se puede correr ya el nulo de 13 h?
No. Arreglar antes: VL169-02 (criterio de ATRAPADA, en el script del nulo), y VL169-01, 03, 05 y 06 (cambian líneas del lector sobre las que las 111 mutaciones están escritas; volver a pasar `comprobar_unicas` y agregar mutaciones para las reglas nuevas). Quedan cuatro días hasta el 2026-11-03 15:00 UTC y el nulo toma 13 h, así que hay margen para un ciclo de arreglo. Marcar V04 como equivalente en el script antes de correr.
