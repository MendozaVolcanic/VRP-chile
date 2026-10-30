# Verificador corto de la ronda 2 del lector de la sombra V375-E (S169)

## 1. Encabezado
- Fecha y hora del servidor (`date -u`): inicio 2026-10-30 07:04 UTC, cierre 2026-10-30 07:30 UTC aprox.
- Commit medido: `9d76af91b` (árbol exportado en `arbol/`, sin `data/`). Para git real usé `repo_t/` (copia del árbol con un commit propio, sin remoto) y contrasté con el repositorio con `git show 9d76af91b:ruta` y `git diff 983f6f28d 9d76af91b -- experiments/`.
- Modelo y esfuerzo: Sonnet 5.5 (claude-sonnet-5-5), esfuerzo bajo.
- CARPETA: `D:/vrp-trabajo/temporales/s169_ver_lector_r2/`. El `caminos.md` se fijó a las 07:04:32 UTC antes de abrir el INFORME de la ronda y el código; sha256 del texto fijado `10e2504f339241cc47e9de8d283d96d3cdf21f4e8e6a693fc117aeb922fc1ba2` (después le agregué dos líneas al pie con ese sha y la hora, sin tocar el texto anterior).
- NO miré: `data/sombra_codigo_mirova/` ni `data/mirova_equivalent/` (prohibido); no corrí la batería completa (7 a 20 min) ni el nulo; no leí `ver_en_rojo.py` salvo su línea de timeout; no revisé la estadística de `evaluar.py` ni el PREREGISTRO §1 a §10; no verifiqué el cenit del record de K ni el perfil de la vía en un record real; no probé dos corridas simultáneas.

## 2. En una pantalla
- Veredicto: **LISTO PARA EL NULO CON CAMBIOS, y los cambios son en `mutar_sombra.py`, no en el lector.** L1 a L6 se sostienen, con los matices de abajo.
- Obliga a tocar antes del nulo: `mutar_sombra.py` pierde TODO el nulo si UNA corrida pasa de 1800 s (TimeoutExpired sin capturar y resultados impresos solo al final); R20 es la candidata (VL2-01). Además no se detiene si la identidad falla, así que un árbol equivocado da 138 "ATRAPADA" falsas (VL2-02).
- L1: en la misma carpeta, en otra carpeta del mismo checkout y con `origin/loop/activo` que ya tiene el registro, la segunda lectura sale rc 2 sin escribir. Queda abierto (procedimiento, no código) leer desde otro checkout si el registro aún no se commiteó, empujó y bajó con `git fetch` (VL2-03), y la lectura sale por stdout antes de poder commitear el registro (VL2-04).
- L3 y L4: S8 se comporta como dice (25 casos con git real y 17 de control_s8); los 16 sha de S0 coinciden con los bytes LF del objeto git. S8 marca de más (VL2-05).
- L2, L5 y L6 comprobados; V04 es equivalente de verdad.

## 3. Hallazgos (por gravedad)

### VL2-01
- TÍTULO: Un solo TimeoutExpired en una mutación aborta el nulo entero y se pierden los resultados de las 138.
- ARCHIVO:LÍNEA: `experiments/_s168/v375e_sombra/mutar_sombra.py:213` (timeout=1800), `:225-231` (`una()` sin `except`), `:266-270` (`resultados = list(ex.map(...))`; recién después se imprime cada mutación), `:275-276` (el `finally` escribe solo `L`). SCRIPT:SALIDA `l2_nulo.py:l2_nulo_salida.txt`, bloque (C).
- QUÉ PASA: es un fallo del instrumento, no del volcán. El nulo corre la batería una vez por mutación y anota los resultados solo cuando terminaron todas. Si una mutación hace que la batería tarde más de 30 min (sola tarda 7 min con el equipo libre y 15 a 20 con carga; cada lectura completa que R20 deja pasar en vez de rechazar tardó 37 a 78 s en mi `probe_l1`), `subprocess.run` lanza `TimeoutExpired`, nadie lo captura, `list(ex.map)` lo relanza y el `finally` guarda solo la identidad y los dos controles. El INFORME de la ronda dice que el grupo I superó los 30 min por R20 y que R20 pasó a K con tope de 5400 s (`ver_en_rojo.py:103`), mientras el nulo conserva 1800 s. R20 está cerca del final de la lista.
- CÓMO SE VE EN EL DASHBOARD: invisible. Se pierden 16 a 47 h de corrida sin tiempo para repetirla antes del 2026-11-03 15:00 UTC.
- CÓMO REPRODUCIRLO: `C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I D:/vrp-trabajo/temporales/s169_ver_lector_r2/l2_nulo.py` (parcha `subprocess.run` para lanzar TimeoutExpired solo en R20; M01 y M02 devuelven ATRAPADA). Salida: `main LEVANTO: TimeoutExpired` y el archivo de salida con 3 líneas (identidad y controles), sin M01 ni M02.
- CONFIANZA: CONFIRMADO el mecanismo. SOSPECHA que R20 (u otra) supere 1800 s en el nulo real (depende de la carga del equipo).
- GRAVEDAD: 4 (no tuerce una alerta; hunde el control que se pidió antes del sello).
- Arreglo propuesto (no aplicado): capturar `subprocess.TimeoutExpired` en `correr()` y devolver CAIDA; subir el timeout a 5400; escribir cada línea al disco al terminar cada mutación; no toca el lector ni obliga a repetir la batería.

### VL2-02
- TÍTULO: El nulo sigue aunque la identidad falle, y ATRAPADA no se compara contra la identidad.
- ARCHIVO:LÍNEA: `mutar_sombra.py:216-219` (rc 1 con línea RESULTADO es ATRAPADA sin más), `:259-264` (identidad y controles solo se imprimen), `:277` (`return 0` siempre). SCRIPT:SALIDA `l2_nulo_salida.txt` (A) y (C): "IDENTIDAD (copia sin mutar): FALLA ATRAPADA" y el nulo continúa.
- QUÉ PASA: si el árbol donde se corre no es el correcto (un sha de S0 distinto, el commit `c42ee0eb7` ausente, árbol sucio, o el worktree principal en `loop/activo`, que hoy no contiene el lector: `git merge-base --is-ancestor 9d76af91b HEAD` dio NO), la batería ya falla sin mutar. Entonces las 138 mutaciones salen rc 1 con RESULTADO, o sea ATRAPADA, y el nulo informa "138 atrapadas" 16 a 47 h después sin haber medido nada. Lo mismo si CONTROL o CONTROL_SECCION no dan CAIDA: la línea dice "(tiene que ser CAIDA)" pero nadie lo exige.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: ídem VL2-01, líneas "IDENTIDAD ... FALLA" y a continuación CONTROL y el resto.
- CONFIANZA: CONFIRMADO (código y salida del parche).
- GRAVEDAD: 3.
- Arreglo propuesto: abortar con rc 2 si la identidad no es SOBREVIVE o si CONTROL y CONTROL_SECCION no son CAIDA; opcionalmente contar ATRAPADA solo si las FALLA de la mutación difieren de las de la identidad.

### VL2-03
- TÍTULO: La "una sola lectura por ventana" se sostiene en el mismo checkout; desde otro checkout depende de commit, push y fetch, y el lector no lo exige.
- ARCHIVO:LÍNEA: `leer_sombra_v375e.py:767-790` (`registro_local`, `registro_remoto`, `ventana_ya_leida`), `:824-827`. SCRIPT:SALIDA `probe_l1.py:probe_l1_salida.txt`.
- QUÉ PASA: medido con `main()` real y git real. T0 primera lectura: rc 0 y registro con N, sha de la referencia y de los records, hora, `--commit`, sha del lector (`registro_ejemplo.txt`). T1 (otra referencia, otra carpeta) y T2 (misma referencia, otra carpeta) en el mismo checkout: rc 2 en 0 s, nada escrito. T4 (registro local ausente, `origin/loop/activo` con el registro): rc 2. **T3** (registro local ausente, `origin/loop/activo` sin el registro todavía) y **T5** (el registro sí está en el remoto pero la referencia local quedó vieja, sin `git fetch`): rc 0 y una segunda lectura con su archivo. El lector lee el remoto con `git show origin/loop/activo:...` sobre la referencia LOCAL; no hace fetch y solo avisa "haz git fetch" cuando la referencia no existe, no cuando está vieja. §11.8 dice "Una segunda lectura no puede pasar en silencio": cierto solo si se cumplió el procedimiento; sobreafirma.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `probe_l1.py` (unos 4 min; escribe en `tmp_l1/` y `repo_t/`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (la original era 3: el camino que queda exige no tener el registro local y una referencia vieja, y deja una línea visible al commitear).
- Mitigaciones baratas: (a) solo procedimiento: `git fetch origin` y comprobar que `origin/loop/activo` es la punta antes de leer; (b) cambio del lector (exige repetir batería y nulo, va ANTES del nulo): imprimir y guardar en el registro el sha de `origin/loop/activo` y la hora de su commit, y escribir el registro además en una ruta fuera del checkout que compartan todos los checkouts del computador.

### VL2-04
- TÍTULO: La lectura que decide sale por stdout antes de que el registro pueda estar commiteado.
- ARCHIVO:LÍNEA: `leer_sombra_v375e.py:119-121` (`pr` hace `print(..., flush=True)`), `:885` (`anotar_registro`, solo local), `:894` (`reporte(...)` imprime la lectura). PREREGISTRO_E.md §11.8: el registro "se commitea a `loop/activo` antes de mostrar la lectura a nadie (ni a la coordinadora ni a Nicolás)" (TEXTO).
- QUÉ PASA: quien corre el lector ve la lectura en la terminal en el mismo instante en que se escribe el registro local; el commit es posterior y ninguna guarda de código lo impide. La frase de §11.8 solo se cumple si quien lo corre redirige la salida a un archivo y no lo abre hasta commitear.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las líneas citadas; `pr` imprime siempre. No corrí el lector con consola visible.
- CONFIANZA: CONFIRMADO por lectura del código.
- GRAVEDAD: 2. Se cierra sin tocar el lector: el comando del §11 lleva `> salida_consola.txt 2>&1` y no se abre hasta commitear.

### VL2-05
- TÍTULO: S8 marca de más: bytes en volcanoes.yaml, el workflow y los perfiles, y AST de cualquier `.py` de `pipeline/`, aunque no sea de la vía de VIIRS 375.
- ARCHIVO:LÍNEA: `leer_sombra_v375e.py:399-415` (`cambio_significativo`), `:95-96` (`RUTAS_REGIMEN`, `PERFILES_REGIMEN`). SCRIPT:SALIDA `l3_s8.py:l3_s8_salida.txt`.
- QUÉ PASA: con git real y un commit por caso. NO marcan: solo `roi_v750` (un volcán y los 11), docstring de módulo o de función, comentario en un `.py`, CRLF en un `.py`, comentario en la grilla, un tercer perfil, un archivo de `scripts/` fuera de las rutas, comentario en `run_pipeline.py`. SÍ marcan: `x0`, clave o volcán nuevo, grilla ilegible, cambio de valor en un `.py`, `.py` nuevo, borrado o ilegible, los dos perfiles (aun un comentario), `run_pipeline.py` con código, un archivo no `.py` en `pipeline/`. Y también marcan, sin efecto físico: un comentario en `volcanoes.yaml`, en el workflow de la sombra o en `mirova_equivalent.yaml`, y cualquier cambio de AST en `process_modis.py`, `mirova_v750_codigo.py` u otro `.py` que la vía de VIIRS 375 no usa. En `origin/main` hubo 23 commits sobre `pipeline/*.py` solo desde el 2026-10-01.
- CÓMO SE VE EN EL DASHBOARD: la lectura sale con "CAMBIO: los CUMPLE de (b), (c) y (d) pasan a DECIDE NICOLAS" sin que haya cambiado el detector de VIIRS 375.
- CÓMO REPRODUCIRLO: `l3_s8.py` (casos 16, 18, 19 difieren de lo ideal).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (falla cerrada: nunca oculta un cambio real; cuesta que Nicolás juzgue a mano la lista de archivos que imprime el lector).

### VL2-06
- TÍTULO: S9 usa la fila más nueva de VIIRS 375 de cualquier volcán, no la del volcán que se lee.
- ARCHIVO:LÍNEA: `leer_sombra_v375e.py:842` (el `max` sobre `source == "CONS"` y `sensor_bucket == "VIIRS375"`), `:469-474` (`control_s9`). SCRIPT:SALIDA `l5_ligero.py:l5_ligero_salida.txt`.
- QUÉ PASA: el filtro por sensor funciona (una fila MODIS del 2026-11-20 y una de VIIRS 750 del 2026-12-30 no mueven `ultima_tabla`, que da 2026-11-12 de VIIRS 375). Pero el máximo es global: si la tabla de un volcán se atrasa y la de otro no, S9 pasa.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `l5_ligero.py`.
- CONFIANZA: CONFIRMADO el comportamiento; SOSPECHA que una tabla se atrase solo por volcán.
- GRAVEDAD: 1.

## 4. SEGUIMIENTOS (fuera del eje; no los perseguí)
1. Una mutación que sale CAIDA (aparte de los dos controles) queda sin evaluar; el informe del nulo debería listarlas una a una (`mutar_sombra.py:221-222`). SOSPECHA, gravedad 1.
2. `.github/workflows/sombra-codigo-mirova.yml` instala `numpy`, `scipy` y `pyproj` sin versión (`pip install ... numpy h5py scipy pyyaml pyproj`, hacia las líneas 86-91, leído del árbol): un cambio de versión entre noches no lo ve S8. Leído (CONFIRMADO); consecuencia SOSPECHA. Gravedad 2.
3. La batería imprime a stderr `probar_sombra.py: error: the following arguments are required: --commit` en una prueba que espera ese SystemExit (también aparece en `rojo_F.txt`): es ruido esperado, no una falla.
4. Tiempo del nulo: 141 corridas a 7 min son 16,4 h; a 15-20 min son 35 a 47 h. Quedan unas 103 h hasta 2026-11-03 15:00 UTC, así que cabe una sola vez.
5. `mutar_sombra.py` crea `_mut_sombra_*` dentro de `experiments/_s168/` del repositorio mientras corre; si el proceso muere por kill quedan sin borrar (el `finally` de `una` cubre excepciones, no un kill).

## 5. VERIFICADO LIMPIO
(Vara: PREREGISTRO_E.md §11.4, §11.8 y §11.12 del árbol `9d76af91b` y mi `caminos.md`. Cada script lleva en su encabezado las dos preguntas del instrumento y un control positivo.)
- **L4, S0 y los sha**: `l4_sha.py` da 16 de 16 `OK`: sha del lector (extraído por regex del propio `SHA_DEPS` y `SHA_SELLO_LECTOR`) = sha256 LF del archivo del árbol = sha256 del objeto `git show 9d76af91b:ruta`, sin pasar por el sistema de archivos de Windows; 0 CRLF en los 16. Control: el mismo texto con CRLF da otro sha (`58055bdc…` frente a `911169dd…`). `c42ee0eb7` es ancestro de `dcec35a8c` (merge, padres `983f6f28d` y `cc388729`) y de `9d76af91b`. Entre `c42ee0eb7` y `9d76af91b` los 17 archivos de S0 y de las rutas de S8 tienen el mismo sha y `git diff --stat` sobre `pipeline/`, `volcanoes.yaml`, `run_pipeline.py` y el workflow sale vacío. Contra `983f6f28d`, el lector cambia solo el sha de `auto_audit_weekly.py` (3afd3e65 a 9c4da61e) y suma `store.py`, `profile.py`, `f5_core.py` y `mirova_equivalent.yaml` (diff de las líneas de sha).
- **L3, S8**: `l3_s8.py` (25 casos) y `l3_control_s8.py` (`control_s8` real con records y commits reales). Un cambio solo en `roi_v750` NO marca; `x0` marca; un `.py` de la vía marca y un comentario o docstring no; CRLF no. Un record sin `codigo_sha` marca ("sin sha"), sin `regimen` marca, la primera noche sin `codigo_sha` marca por la base, sin records de la vía marca, un sha no resoluble marca. El hueco declarado se comporta como dice: un cambio ANTES de la base queda coherente, no marca, y `informa_c42ee0eb7_contra_base` trae `['pipeline/constants.py']` (o "git no lo resuelve"), que `reporte` imprime (`:693-694`). Controles: el caso sin cambio no marca y el de `x0` sí.
- **L5**: `l5_ligero.py`: `VRP_PROFILE` = `experimental`, vacío o `sombra_codigo_mirova` hace que S0 caiga y no cargue nada; ausente carga y fija `mirova_equivalent`. S9 con 2 días pasa y con 1 día cae. `l5_contadores.py`: `main()` real, 2 noches, umbrales 30/40: rc 3, "S6 CAE", "LECTURA NO LEGIBLE" y "noches 2 de 30, alertas 5 de 40: NO ALCANZADA".
- **L2**: `l2_nulo.py` (A), tabla de verdad de `correr()`: rc 1 + RESULTADO es ATRAPADA; rc 2 + RESULTADO es CAIDA; rc 1 sin RESULTADO (excepción no capturada) es CAIDA; rc 0 es SOBREVIVE; rc 3 es CAIDA. `l2_seccion.py`: `seccion()` real deja `CAIDAS = ['lanza']` y la regla del final (`return 2 if CAIDAS else (0 if all(RES) else 1)`) da 2 aunque todo RES sea True. Control del autor, `rojo_F.txt`: CONTROL_SECCION sale exit 2 con la sección "borde" como CAE; `return frozenset(out)` está en `borde_mixto`, llamada dentro de esa sección (`probar_sombra.py:673-693`).
- **L6, nulo estático**: `l6_nulo_estatico.py`: 138 mutaciones (M 55, V 17, N 39, R 27), ids sin repetir, `comprobar_unicas()` = `[]`, viejo distinto de nuevo en todas, 0 con SyntaxError, 0 con el mismo AST del original; control: una mutación inventada aparece como `('INVENTADA', 0)`. Corridas = 138 + identidad + 2 controles = 141. V04 está en `EQUIVALENTES`. Equivalencia de V04 en el código: `regla_signos` (`evaluar.py:129-141`) devuelve exactamente SIN SUSTRATO, GANA, PIERDE, BLOQUEA o EMPATE y `p2_con` también la usa (`leer_posicion_v375e.py:275`); (b) acepta {GANA, EMPATE, SIN SUSTRATO} para P2 y rechaza {PIERDE, BLOQUEA} para P2-L, que es el complemento, así que cruzarlos no cambia (b) (`criterios_sombra`, `:536-547`).
- **Batería**: `probar_sombra_salida.txt` de `9d76af91b` tiene 227 líneas PASA, 0 FALLA, 0 CAE y la línea `RESULTADO: 227 de 227`; no la re-corrí. Commits: lector 03:37:31 (-03:00), batería 03:37:33, salida 03:37:38; sin cambio posterior. Toda llamada a `LS.main` de la batería pasa antes por `nuevo_reg()` o `correr`, que mandan `REGISTRO` a un temporal; el repositorio real no tiene `lecturas/` (la batería no ensucia el registro real).
- `lecturas/REGISTRO_VENTANA_P.jsonl` no está ignorado por git (`git check-ignore -v` rc 1 en el repo real), así que `git add` normal lo toma.

## 6. SIN DATO
- Batería 227 de 227 sobre el árbol final: no la corrí (7 a 20 min, sobre el límite de 10). La identidad del nulo la repetirá primero; por eso VL2-02 importa.
- Que la batería necesite git presente: lo deduzco del código (usa `REF_REGISTRO = "HEAD"` y resuelve `c42ee0eb7` en el checkout), no lo medí en un árbol sin `.git`.
- Perfil de la vía y `regimen.perfil` en un record real: no hay records que abrir; igual que la ronda.
- El instante exacto en que aparece la lectura en una consola (VL2-04 es por lectura del código).

## 7. FUERA DE ALCANCE
La estadística de `evaluar.py` y de la regla del paquete, el PREREGISTRO §1 a §10, `ver_en_rojo.py` (salvo su timeout), los workflows de la sombra y su cadencia.

## 8. Veredicto
**LISTO PARA EL NULO CON CAMBIOS.** Antes de lanzarlo: (1) `mutar_sombra.py`: capturar TimeoutExpired, subir el timeout, guardar cada resultado al terminar y abortar si la identidad no pasa o si los dos controles no son CAIDA (VL2-01 y VL2-02); no toca el lector ni repite la batería. (2) Decidir si VL2-03 y VL2-04 se cierran con el procedimiento (fetch explícito, salida a archivo) o con un cambio del lector, que iría ANTES del nulo.
