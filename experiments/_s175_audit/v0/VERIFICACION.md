# VERIFICACION del frente F0 (S175)

CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v0\`
Caminos escritos antes de abrir ningún archivo citado: `...\v0\caminos.md` (sha256 del cuerpo `e312188e090dd5a86b000fb06aace01e267ba11fa4578c457f54e276ac55422b`, hora del servidor GitHub 2026-11-07 16:40:59 GMT; no se editó después).

## Encabezado

- Fecha y hora del servidor: sábado 2026-11-07, 16:40:59 GMT al escribir caminos.md (header `Date` de la API de GitHub); el reloj local marcaba 16:50:02 UTC al cerrar la medición de los últimos puntos.
- Base de medición: `752d348bc67190e53b610989877e2405d238a1bc`, leída con `git show` (no el árbol de trabajo). Las copias de la referencia en `insumos` coinciden con la vara: `snapshot_consolidado_base.csv` f833bfde..., `snapshot_ocr_base.csv` 577a336e..., `latest_consolidado_base.csv` dee76837... (comprobado con sha256sum).
- Modelo: Claude Sonnet 5.5 (`claude-sonnet-5-5`). Esfuerzo real con que corro: SIN DATO (la sesión no me lo informa).
- Llamadas a la API de GitHub usadas: 3 de 5 (`rate_limit` para la hora del servidor, fecha del secret EARTHDATA_TOKEN, lectura del issue #936). Sin escritura en el repo: no hice add, commit, stash, checkout ni pull. Sólo escribí en la carpeta v0 y en `C:\Users\nmend\vrp-temporales\s175_audit\v0\` (copias de la base por `git show`, unos 2 MB).
- No miré: `experiments\_s175_audit\f0\INFORME.md` ni las columnas de razonamiento (por encargo). No abrí los PDF de los papers (las citas de Campus 2024 y Coppola 2026 dentro de D32 las leo sólo como TEXTO del Markdown del repo, no las verifiqué en RENDER). No verifiqué contra GitHub el estado remoto de ramas ni la existencia de PR posteriores a la base. No pude comprobar la causa de las pasadas MODIS ausentes (necesita red a CMR/LANCE).

## En una pantalla

Los 12 veredictos: 5 CONFIRMADO (102, 103, 107, 110, 113), 7 CONFIRMADO EN PARTE (101, 104, 105, 106, 109, 114, 115), 0 REFUTADO, 0 SIN DATO. Las partes que no se sostienen son frases de contexto, no los números ni las citas: «quedó sin camino» (101), «caería en silencio» (109), «git ls-files no tiene ningún hallazgos.csv» (114, ya falso en HEAD) y «MIROVA usa 7 × 7 píxeles» (106). Los números de los scripts del auditor se reproducen bit a bit (101, 109, 110, 113) y por un camino independiente (101 y 109). Gravedades mías: ninguna en 4 o 5; la mayor es 3.

## Resumen de veredictos

| ID | Veredicto | Gravedad mía (auditor) |
|---|---|---|
| 101 | CONFIRMADO EN PARTE | 3 (4) |
| 102 | CONFIRMADO | 3 (4) |
| 103 | CONFIRMADO | 3 (3) |
| 104 | CONFIRMADO EN PARTE | 2 (3) |
| 105 | CONFIRMADO EN PARTE | 2 (3) |
| 106 | CONFIRMADO EN PARTE | 2 (3) |
| 107 | CONFIRMADO | 3 (3) |
| 109 | CONFIRMADO EN PARTE | 2 (2) |
| 110 | CONFIRMADO | 1 (2) |
| 113 | CONFIRMADO | 2 (2) |
| 114 | CONFIRMADO EN PARTE | 2 (2) |
| 115 | CONFIRMADO EN PARTE | 2 (2) |


## Veredictos por afirmación

### 101: cúmulos de cumbre de VIIRS 750 en 0,0 MW; 203 «sin camino». CONFIRMADO EN PARTE, gravedad 3

Pregunta 1 (¿lo vería si estuviera roto?): sí, el conteo de `pc.vrp_mw == 0` sería 0 sin el recorte a cero. Pregunta 2 (¿se vería distinto con el instrumento muerto?): sí, el mismo script imprime antes `CONTROL identidad del predicado: ([0, 1, 1, 1, 0], [1, 0])` y el total de cúmulos de cumbre (97, 58, 19), que serían 0 con el instrumento muerto.

- Re-corrí `f0_203_cumbre_cero.py`: salida idéntica a la del auditor (`v0\rerun_203_salida.txt`). Ventana 2026-09-18 a 2026-10-21: 30 de 97 cúmulos de cumbre de VIIRS 750 con 0,0 MW (30,9 %), 0 publicados; 7 con alerta de MIROVA, de 0,09 a 0,36 MW, ninguna protegida; entre ellas Láscar NOAA20 2026-10-08 05:42 con 0,36 MW. Control: los publicados entre los 0 MW son 0, consistente con «el tablero no publica 0 MW».
- Camino independiente (`v0_101_conteo_independiente.py` → `v0_101_conteo_independiente_salida.txt`): leí `data/mirova_equivalent/*.json` de la base con `git show`, sin pasar por `banco_paridad`, con la nocturnidad por `solar_zenith_deg >= 90`. Da 30/97, 11/58 y 6/19 en las tres ventanas del auditor, igual que él. Último dato de la base: 2026-11-06 05:42.
- Cita D25: `docs/MIROVA_DIVERGENCES.md` l. 2863 en la base (TEXTO): «D25 tal como está NO SE ADOPTA». La cita `docs/AUDIT_S160.md` §5 decisión 4, TEXTO: «Es la divergencia D25, abierta y con su A/B en #890» (l. 116 del archivo). Ambas existen.
- Lo que no se sostiene: «quedó sin camino». El mismo bloque de D25, l. 2874 a 2875, dice (TEXTO, paráfrasis mía: el camino que queda es el fondo del programa dentro del paquete del código por sensor, V750-A, V375-E, MOD-D). V750-A, según `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` l. 83 a 86 (TEXTO: «sin modo de un píxel ni tope D9»), reemplaza el fondo por el del código de MIROVA, que no recorta a cero. V750-A no está adoptado (pide A45 y sello), así que el fenómeno sigue en producción, pero la afirmación «sin camino» es falsa tal como está escrita: tiene un camino nombrado, pendiente de decisión.
- Lo que está sesgado: «la fracción bajó a 19 %». Es la ventana 2026-10-22 a 2026-11-02 (11 de 58). La ventana siguiente, 2026-11-03 a 2026-11-07, vuelve a 6 de 19 (31,6 %), igual a la ventana K de S160. Las dos ventanas posteriores juntas: 17 de 77 (22,1 %). No hay evidencia de que haya bajado de verdad (n de 19 a 58).
- Gravedad: las alertas de MIROVA que se pierden son débiles (0,09 a 0,36 MW) y no protegidas, y en las dos ventanas nuevas hay 0 con alerta de MIROVA entre los 0 MW (etiquetas sin_info y neg_limpio). Pero la misión pide capturar también lo débil en VIIRS. Pongo 3.

### 102: D32 abierta, publicamos el cúmulo y MIROVA suma. CONFIRMADO, gravedad 3

- `docs/MIROVA_DIVERGENCES.md` l. 3284 en la base (TEXTO): «**ABIERTA (registrada S147, verificada con contexto limpio, gravedad 4; prioridad MEDIA, no es la palanca del 0,7)**». Existe, con ese texto, en `git show 752d348bc:docs/MIROVA_DIVERGENCES.md` (copia en `C:\Users\nmend\vrp-temporales\s175_audit\v0\MD_base.md`).
- La sección no tiene marca posterior que la cierre: sólo la marca S158 que dice «Confirma D32».
- Mi gravedad es 3, no 4: la propia sección mide que sumar cierra el 26 % de la brecha en VIIRS 375 y en VIIRS 750 «la pasa de largo» (razón agregada hasta 1,153, 7,3 % de los pares superaría 10 veces a MIROVA), y dice que «no toca la sobre-publicación» porque la puerta de publicación no usa la magnitud mostrada. Es decir, cambia la magnitud mostrada, no abre ni cierra detecciones. Las citas de Campus 2024 y Coppola 2026 dentro de D32 no las re-verifiqué en RENDER.
- No re-medí la tabla de razones de S147 (es la del auditor y del documento).

### 103: Decisión 6 de S160 y C-10 abiertas. CONFIRMADO, gravedad 3

- `docs/COLA_CAMPO.md` l. 21 de la base: fila C-10, estado «abierto».
- `latest_consolidado_base.csv` l. 37438 (comprobado con `sed -n 37438p`): `2026-03-27 07:10:00,...,Lascar,MODIS,1.0,1.41,ALERTA_TERMICA`; y la misma fila está en el snapshot de la base y en `latest_consolidado.csv` de la raíz de la base.
- `tasks/LOOP_OBJETIVOS.md` l. 522 de `395af8034a3146ffd1d20575f290d7313a71707a` (leído con `git show`): fila D-43, TEXTO: «abiertas 6 (mirar C-10, Láscar MODIS 2026-03-27, antes de dar D18 por vetada)». Cita textual exacta. Es una marca del 2026-10-31 (S171); no encontré cierre posterior en la base.
- El veto: `docs/MIROVA_DIVERGENCES.md` D18 (l. 2427 y siguientes): el A/B de caja dio NO CUMPLE por perder esta protegida; la marca S162 dice que con MxD03 la alerta pasa de 3,20 a 0,89 km y que «el veto sigue valiendo» porque producción sigue con `_interp_geo`. Que la caja deje de perder esa alerta «es SOSPECHA hasta esa medición».
- Dato propio: el record de la base `data/mirova_equivalent/Lascar.json`, MODIS_AQUA 2026-03-27 07:10, publica `vrp 0,14 MW`, `final_hotspot_dist_km 3,38`, clase `summit`, perfil `_s154_reproc_k_historico` (contra 1,00 MW de MIROVA). «Exactamente 1,00 MW» es correcto en la referencia (valor de la tabla, no un redondeo del auditor).

### 104: Decisión 9, V0b-01 y C-07; K1 en -0,8 y tope D9 acoplado. CONFIRMADO EN PARTE, gravedad 2

- Las líneas citadas coinciden en la base: `pipeline/process_viirs_mod.py` l. 1040 a 1045 (`_path_d_cap_active = (` ... `and n_nti_path == 0`) y `pipeline/process_viirs.py` l. 1472 a 1477 (misma expresión con `t_bg_i04`); `pipeline/profiles/mirova_equivalent.yaml` l. 60 `nti_k1_night: -0.8`.
- Valor efectivo (no sólo el texto): con `VRP_PROFILE=mirova_equivalent`, `python -I` sobre `pipeline/profile.py` de la base da `NTI_K1_NIGHT -0.8`, `PATH_D_ONLY_CAP_MW 5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K 270.0` (el yaml l. 525 y 526 fija el tope). El tope está encendido.
- El acople es real: `nti_path_hot` se arma con `nti > NTI_K1_NIGHT` (`process_viirs_mod.py` l. 700 a 706; `process_viirs.py` l. 1062 a 1066) y el tope sólo actúa con `n_nti_path == 0`. Subir K1 a -0,7 deja menos píxeles en la vía NTI, hace más probable `n_nti_path == 0` y por tanto más probable el tope. `docs/COLA_CAMPO.md` l. 18 (C-07) y `docs/AUDIT_S160.md` decisión 9 (l. 121 de la copia): «no adoptar el K1 de -0,7 sin resolver antes que no tope una protegida». Ambas abiertas.
- Lo que no es como suena: el ejemplo de Nevados de Chillán VIIRS_SNPP_750 2026-10-01 06:00 UTC es un contrafactual. El record de producción publica `pc.vrp_mw 11,084` (no 5,0). La salida de `experiments/_s160_audit/f0b/v0b_02_ndc_tope_k1.out` muestra 11,084 contra el 5,0 que daría el tope. Hoy no se pierde nada por esto: es un bloqueo para una decisión futura (adoptar el K1 del código de MIROVA). Por eso 2.

### 105: C-09, fila OCR de Lastarria 2026-04-18 04:42 UTC. CONFIRMADO EN PARTE, gravedad 2

- `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` l. 931 de la base: `Lastarria,VIIRS375,1.29,0.0,ALERTA_TERMICA_OCR,...,1.56,20.04,ambiguo`. Existe y es esa fila.
- Ejecuté el cargador y la regla de la base (`v0_105_c09.py` → `v0_105_c09_salida.txt`, con la referencia de los `insumos` y las capas históricas sacadas de la base): la pasada VIIRS375 Lastarria 2026-04-18 04:42:01 sale `estado alerta, 1,29 MW, solo_ocr True`, y `es_protegida(lectura A) = True`. Control positivo: hay 567 pasadas protegidas de 47.124 en total, así que el instrumento puede dar True y False.
- Matiz que el auditor no dice: la tabla no contradice a esa fila. La pasada que la tabla lista como RUTINA 0,0 es del bucket VIIRS750, no del VIIRS375; en el canal tabla no hay ninguna fila VIIRS375 a esa hora, así que decide el OCR (`solo_ocr`). Y el propio marco ya la separa del lado: `protegida_de_crater(p, 3.0)` devuelve `(False, ('ocr_sin_distancia_medida', 'plataforma_desconocida_antes_del_hito'))`. Cuenta como protegida sólo en la lectura A que decide, no como «de cráter».
- Una alerta de 567 protegidas (0,2 %). Gravedad 2.

### 106: V2-09, umbrales de cumbre hasta inner_radius vs caja de MIROVA. CONFIRMADO EN PARTE, gravedad 2

- `pipeline/profile.py` l. 610 de la base: `ENABLE_ROI1_BOX_PAPER: bool = bool(_p.get("enable_roi1_box_paper", False))`. Valor efectivo medido con `VRP_PROFILE=mirova_equivalent`: `ENABLE_ROI1_BOX_PAPER = False`, semilado 2,5 km. El perfil operacional no lo menciona; sólo los perfiles de A/B `_s130_d18_caja.yaml`, `_s147_*` y `_s151_*` lo encienden.
- El comentario sobre la l. 606 (TEXTO): «DEFAULT OFF y OFF en el operacional». Está apagado a propósito: D18 está «ABIERTA (A/B corrido S130 → NO ADOPTAR ...; prioridad baja)» y el A/B de S151 sobre K dio NO CUMPLE por el veto de C-10 (ver 103). No es un olvido abierto sino una decisión con una condición pendiente.
- «MIROVA los usa en una caja de 7 × 7 píxeles» no tiene sustento en lo que leí. `docs/MIROVA_DIVERGENCES.md` l. 1117 (TEXTO) dice «la cumbre es `BOX == 2`, 7 × 7 celdas en la matriz de ejemplo», es decir, el tamaño de la matriz de un ejemplo del código, no la caja real de cada volcán. El título de D18 y el parámetro del código hablan de una caja de 5 km (semilado 2,5). La marca S160 de D18 agrega que el código de MIROVA permite ROI desplazables y reformables por volcán, de modo que ni 7 × 7 ni 5 km son un número fijo. Dejo esa parte como SOSPECHA.
- Gravedad 2: divergencia de fidelidad de prioridad baja, medida y vetada.

### 107: rotación de EARTHDATA_TOKEN antes del 2026-11-27. CONFIRMADO, gravedad 3

- `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` l. 28 (TEXTO): «vence **2026-12-07 18:03 UTC**» y «**Rotar antes del 2026-11-27.**». Textual.
- `insumos\secretos_nombres_fechas.txt`: `EARTHDATA_TOKEN 2026-10-08T18:07:05Z`. Re-consulté en vivo con `gh api repos/MendozaVolcanic/VRP-chile/actions/secrets/EARTHDATA_TOKEN --jq .updated_at`: `2026-10-08T18:07:05Z`, es decir, no se ha rotado desde el insumo. Aritmética: 2026-10-08 + 50 días = 2026-11-27 y + 60 días = 2026-12-07, consistente con «vida 60 días, rotar a los 50».
- `scripts/token_edad.py` l. 27 de la base: `DIAS_AVISO = 10   # vida 60 días, rotar a los 50`. Y el `nrt-healthcheck` abre issue con 10 días o menos de vida, o sea el 2026-11-27, la misma fecha: hay una segunda red automática.
- No es un defecto de código: es una fecha futura, a 20 días de hoy. Gravedad 3 por el antecedente (el token anterior venció el 2026-10-03 y el NRT estuvo caído hasta el 2026-10-08, según el mismo registro), reducida por la alerta automática del healthcheck. No pude verificar el `exp` del JWT (necesita el valor del secret; no lo toqué).

### 109: pasadas MODIS nocturnas que MIROVA lista y nosotros no bajamos. CONFIRMADO EN PARTE, gravedad 2

Pregunta 1: si bajáramos todas las pasadas, la lista sería vacía; el conteo lo vería. Pregunta 2: el control positivo es que 1.177 filas MIROVA sí tienen record nuestro a ±120 s (un instrumento muerto daría 0 y 0).

- Re-corrí `f0_pasadas_por_satelite.py`: salida idéntica a la del auditor (`diff` sin diferencias; `v0\rerun_pasadas_salida.txt`). Sección 4c: 58 filas MIROVA nocturnas sin record nuestro desde el 2026-09-14, 49 MODIS y 9 VIIRS, todas `RUTINA 0,0` de la tabla.
- Camino independiente (`v0_109_modis_horas.py` → `v0_109_modis_horas_salida.txt`): releí los records con `git show` de la base (comprobé que `base_data` del auditor es idéntica a la base en los 11 volcanes) y las filas de `latest_consolidado_base.csv`. Resultado: 1.177 filas MIROVA MODIS nocturnas con record y 49 sin él (4,0 %). Las 49 son todas `RUTINA` con 0,0 MW. Hay 3 pasadas enteras que falta: 2026-09-28 01:25 a 01:30 UTC (11 volcanes), 2026-10-10 01:05 a 01:10 UTC (11) y 2026-10-02 00:50 (4). En esas tres fechas sólo tenemos records MODIS a las 07:30 a 08:20 UTC (los de las otras pasadas).
- Las horas de las pasadas ausentes (00 a 02 y 07 a 08 UTC) son las mismas horas en que hay records en el resto de la historia, así que no son pasadas diurnas ni de otra naturaleza colada por el filtro `hora < 12`. Desde el 2026-03-01 la proporción es de 108 ausentes en 4.815 filas nocturnas (2,2 %); el 4,0 % de la ventana nueva es mayor, pero la muestra de pasadas enteras (3 eventos) lo explica casi todo.
- Lo que no se sostiene: «invisibles para el recall / caería igual en silencio». `banco_paridad.alertas_sin_record` (def en `scripts/banco_paridad.py` de la base) cuenta justamente las pasadas con alerta de MIROVA sin record nuestro a ±2 min. La corrí (`v0_109b_alertas_sin_record.py` → `v0_109b_alertas_sin_record_salida.txt`): desde el 2026-09-14, 0 de 532 filas-alerta sin record; desde el 2026-03-01, 16 de 2.495 (todas VIIRS, ninguna MODIS). Control positivo: quitar un record que sí aparea una alerta sube la cuenta de 0 a 1 y de 16 a 17. O sea que el banco sí ve las pasadas con alerta que nunca bajamos; la parte de «invisible» vale para las RUTINA (sin alerta) y para el audit semanal, que mide por noche.
- Causa de las pasadas ausentes: SIN DATO (requiere consultar CMR o LANCE; no lo hice). «Nunca bajamos» es una inferencia: sólo sé que no hay record nuestro.
- Gravedad 2.

### 110: noches_sin_datos y el recall ciegos a un satélite callado. CONFIRMADO, gravedad 1

- `scripts/auto_audit_weekly.py` l. 363 a 380 en la base: `recall_por_sensor` y `if (vol, b, fecha) not in vistos: sin_datos += 1` (l. 373 a 375). Coincide.
- Re-corrida de la sección 5 del script del auditor (idéntica): con NOAA-21 quitado de los últimos 14 días, los volcán-sensor-noche con algún record son 464 antes y 464 después, mientras los records NOAA-21 caen de 445 a 0. La métrica por sensor y noche no ve al satélite callado. Control positivo: los records NOAA-21 sí caen a 0 (445 a 0), así que la mutación se aplica.
- Pero es por diseño y está dicho: el docstring de `recall_por_sensor` (TEXTO): «Las noches sin ningún record nuestro del mismo sensor (apagón, gránulo no bajado) se informan aparte: no miramos != no vimos». Y el vigilante por plataforma que el auditor menciona existe y es otra cosa: `.github/workflows/nrt-healthcheck.yml` l. 281 a 301 y `scripts/vigilar_plataformas.py` (ventana de 72 h, ceses esperados en `scripts/ceses_esperados.json`). Cubrió el cese de Suomi NPP del 2026-11-02.
- Gravedad 1: el hueco es de latencia (hasta 72 h) y no de pérdida, y mientras otro satélite del sensor pasa, el sensor sigue cubierto.

### 113: V3-02, el medidor de cadencia ignora el disparador externo. CONFIRMADO, gravedad 2

- `scripts/medir_cadencia_cron.py` l. 69 de la base: `if r.get("event") != "schedule":`. Coincide. `.github/workflows/nrt-healthcheck.yml` l. 327: `--ventana-h 24 --json-out cadencia.json \`. `git grep cadencia.json` en la base sólo encuentra esa línea, logs viejos de `experiments/_s150_audit` y el INFORME de S160 (v3). Nadie lee el JSON; el reporte útil es el `tee` al resumen del job.
- Re-corrí `f0_cadencias.py`: igual a la salida del auditor salvo una advertencia de sintaxis (ver V0-02). `runs_nrt.json`: 50 corridas en 3,12 días, 40 `workflow_dispatch` y 10 `schedule`; 16,0 corridas por día, 12,8 por dispatch y 3,2 por schedule. El «12,8 de las 16» es exacto, pero la ventana es de sólo 3 días y de las últimas 50 corridas.
- Qué implica: `ESPERADO_POR_DIA` declara 12 para el NRT, `CRITICO` alerta sólo con cero corridas `schedule` en 24 h. Si el disparador externo muriera, el dispatch (lo que alimenta ~80 % del NRT) cae a 0 y el medidor no lo ve (siguen 3,2 `schedule` por día); si muriera el `schedule` de GitHub, el medidor alertaría aunque el NRT siga vivo. El docstring de la función dice que se ignora todo lo que no sea `schedule` porque «un dispatch manual no dice nada sobre la puntualidad del cron»: la premisa es de cuando el dispatch era manual. Otros monitores (staleness de 48 h y de 72 h) cubren el apagón de datos. S160 ya lo había registrado en `experiments/_s160_audit/v3/INFORME.md` l. 91 y 116 (dato del propio repo, no de este auditor).
- Gravedad 2.

### 114: los hallazgos.csv no entran a git. CONFIRMADO EN PARTE, gravedad 2

- Confirmado: `git check-ignore -v --no-index experiments/_s175_audit/f0/hallazgos.csv` devuelve `.gitignore:40:*.csv`; `.gitignore` l. 38 a 40 de la base: `# Local CSV data files (reference only, not part of pipeline)` y `*.csv`. No hay una negación `!` que reincluya los CSV de auditoría.
- Ya no es cierto el estado que el auditor describe: `git ls-files experiments/_s175_audit` en HEAD (`ff34b782d`, «informe F0 y hallazgos.csv de todos los frentes (forzados: .gitignore excluye *.csv, hallazgo 114)») sí contiene `f0/hallazgos.csv`, `f2/`, `f3/`, `f5/hallazgos.csv`, `v5/hallazgos_v5.csv`. Los forzaron con `git add -f`. Por eso `git check-ignore -v` sin `--no-index` ya no imprime nada (rc=1 en mi corrida).
- Confirmado con la base: `git ls-tree -r --name-only 752d348bc experiments/_s1*_audit*` da un solo `hallazgos.csv`. Pero en toda la base hay 16 rutas `hallazgos*.csv` forzadas (`_s159/...`, `_s160_espacial/...`, `_s161_verif_ve01/...`, `_s162_*/...`), de modo que el mecanismo de forzar ya se usaba; lo que falta es una regla que no dependa de acordarse. Para S160, `experiments/_s160_audit/` no tiene ningún CSV ni en la base ni en el disco (`ls` falla), que confirma «los de S160 ya no existen» para ese directorio (no para `_s160_espacial`, que sí tiene su `hallazgos.csv` en la base).
- «V2-13 no se puede clasificar»: V2-13 sólo aparece nombrado en la lista de pendientes sin verificador de `docs/AUDIT_S160.md` l. 47; sin el CSV no pude comprobar su contenido. SIN DATO sobre ese punto.
- Seguimiento sin código: la raíz sigue en pie (`*.csv`); el próximo CSV nuevo volverá a ser ignorado. Gravedad 2.

### 115: 166 abierto, bandas RECALL_MIN calibradas sobre C0. CONFIRMADO EN PARTE, gravedad 2

- `scripts/auto_audit_weekly.py` l. 120 de la base: `RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}`. Es la única definición; se usa en l. 925 y 927 (`flags_de_evaluacion`). La misma función dice (l. 918, TEXTO): «El recall sigue juzgando «cráter» porque RECALL_MIN se calibró sobre cráter (S119) y no hay bandas para publicación (A115: no inventar un umbral).» Es decir, el código dice que se calibraron en S119 (anterior a K de S153); la etiqueta «C0» es del auditor, coherente con el calendario, pero el código no la usa. Y el recall sí juzga a K y a la vía: el mensaje lleva `detector {det}`.
- Evidencia viva: el issue abierto #936 (2026-11-02) lista «recall MODIS 72.7% < banda 95.0% (n=22, detector K)» y «recall VIIRS750 79.2% < banda 79.5% (n=53, detector K)», más cuatro «alerta protegida sin publicar» de Nevados de Chillán MODIS. Es decir, las bandas viejas están disparando hoy contra K. Eso no prueba que las bandas estén mal (puede que el recall esté realmente bajo), sólo que ya no tienen una calibración propia del detector que juzgan.
- Tampoco es un olvido: l. 402 (TEXTO) «Las bandas NO se recalibran antes de ver datos (A115).» Es una decisión explícita con una condición.
- Gravedad 2: el aviso semanal rojo permanente (#915 y #936) pierde fuerza para cualquier lector (lección que el propio script anota en el comentario de `UNDER_BAND_KNOWN`: «un aviso que repite lo sabido deja de leerse»).

## Hallazgos nuevos (rango V0-01 en adelante)

### V0-01: la «fracción 19 %» de 101 depende de la ventana elegida
- TÍTULO: la baja a 19 % de los cúmulos de cumbre V750 en 0,0 MW es de una sola ventana; la siguiente vuelve a 31,6 %
- SCRIPT:SALIDA `v0\rerun_203_salida.txt` (ventanas 2 y 3) y `v0\v0_101_conteo_independiente_salida.txt`
- QUÉ PASA: el cúmulo de cumbre cae a 0,0 MW cuando el píxel del cráter está a la temperatura del anillo regional o más frío; con 58 y 19 cúmulos por ventana, 19,0 % y 31,6 % no se distinguen entre sí. Mismo recorte a cero de D25.
- CÓMO SE VE EN EL DASHBOARD: invisible (el cúmulo no se publica).
- CÓMO REPRODUCIRLO: `python -I C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v0\v0_101_conteo_independiente.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1 (afina la gravedad de 101; no es un defecto nuevo)

### V0-02: `f0_cadencias.py` emite una advertencia de sintaxis
- TÍTULO: `f"{I}\{nombre}"` en el script del auditor es un escape inválido
- ARCHIVO:LÍNEA `experiments\_s175_audit\f0\f0_cadencias.py:12`
- QUÉ PASA: Python 3.12 da `SyntaxWarning: invalid escape sequence '\{'` y la advertencia se coló en la primera línea de la salida guardada (`f0_cadencias_salida.txt`). Hoy corre; en una versión futura de Python será un error.
- CÓMO SE VE EN EL DASHBOARD: invisible (es un instrumento de auditoría)
- CÓMO REPRODUCIRLO: `python -I C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\f0_cadencias.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

## SEGUIMIENTOS (fuera de mi eje, sin perseguir)

- Issue #936: cuatro alertas protegidas de Nevados de Chillán MODIS (2026-10-12 07:20, 10-15 01:05, 10-25 07:20, 10-30 07:15) sin publicar con detector K. Es el objeto de otro frente, y yo no lo abrí más allá de leer el título y la lista.
- `data/mirova_equivalent/Lascar.json` tiene 7 de 1.080 records V750 con `pc.vrp_mw` exactamente 5,0 (vs 1 de 172 en Chillán, 0 en Villarrica y Llaima). Puede ser el tope de D9 o coincidencia; no lo investigué. Confianza SOSPECHA.

## VERIFICADO LIMPIO

- Las líneas citadas por el auditor en 102, 103, 104, 106, 107, 110, 113 y 115 existen en la base con el texto citado (comprobadas con `git show 752d348bc...:<ruta> | sed -n`). La vara es la base, no el árbol de trabajo.
- Reproducibilidad: `f0_203_cumbre_cero.py`, `f0_pasadas_por_satelite.py` y `f0_cadencias.py` se re-ejecutan y dan la salida del auditor (salvo la advertencia de V0-02). Los conteos de 101 y 109 se obtienen de nuevo por un camino que no usa el banco (`v0_101_conteo_independiente.py`, `v0_109_modis_horas.py`).

## SIN DATO

- Esfuerzo real con que corro: SIN DATO.
- Causa de las 49 pasadas MODIS ausentes (109): requiere CMR o LANCE.
- Estado remoto posterior a la base (PR, ramas): no consultado salvo el secret (107) y el issue #936 (115).
- Contenido de V2-13 y de los hallazgos.csv de S160: no recuperable (114).
- Si la caja de MIROVA es 7 × 7 píxeles (106): SOSPECHA, no verificada contra el código `.m` ni contra el paper en RENDER.

## FUERA DE ALCANCE

No toqué `pipeline/`, `data/`, `frontend/`, workflows ni credenciales; no hice commit. No abrí `INFORME.md` del auditor.

## Archivos de esta verificación

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v0\`: `caminos.md`, `VERIFICACION.md`, `v0_105_c09.py` y `_salida.txt`, `v0_101_conteo_independiente.py` y `_salida.txt`, `v0_109_modis_horas.py` y `_salida.txt`, `v0_109b_alertas_sin_record.py` y `_salida.txt`, `rerun_203_salida.txt`, `rerun_pasadas_salida.txt`, `rerun_cadencias_salida.txt` (más sus `stderr`).
